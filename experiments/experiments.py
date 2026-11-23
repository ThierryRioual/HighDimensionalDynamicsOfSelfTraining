"""Configurations and simulation runners for the two paper experiments.

The notebooks choose parameters and call these functions. Importing this module
runs no experiments and creates no figures. Runners return results dictionaries;
plotters consume those dictionaries without rerunning simulations.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from numbers import Integral
import random

import numpy as np
import torch

from experiments.plotting import plot_monte_carlo_experiment, plot_statistical_behavior

from src.algorithms import SelfTrainedGradientDescent
from src.asymptotics import MacroscopicStateEvolution
from src.callbacks import TestEvaluatorCallback
from src.config import AlgorithmConfig, DataConfig
from src.dgp import IsotropicGaussian
from src.environment import QuenchedEnvironment, state_evolution_sample_base_sampler
from src.initialization import SelfTrainingInitialization
from src.performance import bayes_parameters, population_error
from src.primitives import sign_with_positive_tie

__all__ = [
    "ExperimentConfig",
    "MonteCarloConfig",
    "run_statistical_experiment",
    "run_monte_carlo_experiment",
    "plot_statistical_behavior",
    "plot_monte_carlo_experiment",
]

_COMPARISON_METRICS = (
    "population_error", "bias_term", "weight_signal_alignment",
    "weight_vector_norm", "unl_usage", "unl_selected_error",
)


# Configuration

@dataclass(frozen=True)
class ExperimentConfig:
    """Population, algorithm, dimension, and seed for a finite experiment."""

    data: DataConfig
    algorithm: AlgorithmConfig
    d: int = 500
    seed: int = 49

    @property
    def n(self) -> int:
        """Sample size implied by the configured aspect ratio."""
        return round(self.data.data_to_dimension_ratio * self.d)


@dataclass(frozen=True)
class MonteCarloConfig(ExperimentConfig):
    """Add particle count, repetition count, and finite/effective observables."""

    k: int = 1000
    runs: int = 5
    metrics: tuple[str, ...] = _COMPARISON_METRICS


# Simulation: retain each experiment's initialization and random streams.

@contextmanager
def _float64_defaults() -> Iterator[None]:
    """Give scalar signal laws a consistent Torch dtype during sampling."""
    previous_dtype = torch.get_default_dtype()
    torch.set_default_dtype(torch.float64)
    try:
        yield
    finally:
        torch.set_default_dtype(previous_dtype)


def _validate_seed(seed: int) -> int:
    """Check the base seed and leave room for the runner's stream offsets."""
    if isinstance(seed, bool) or not isinstance(seed, Integral) or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seeds must be nonnegative integers in the signed 64-bit range")
    return int(seed)


def _sample_finite_training(
    config: ExperimentConfig, seed: int,
) -> tuple[IsotropicGaussian, QuenchedEnvironment, torch.Tensor, torch.Tensor]:
    """Sample the training environment, design, and initial weights on CPU.

    Preserve the caller's global CPU Torch, Python, and NumPy random states.
    The signal law and initial weights use seed + 11. Labels and design
    noise use the DGP's separate generator at seed + 23.
    """
    if isinstance(config.d, bool) or not isinstance(config.d, Integral) or config.d < 1:
        raise ValueError("d must be a positive integer")
    if not np.isfinite(config.data.data_to_dimension_ratio) or config.n < 1:
        raise ValueError("the aspect ratio and dimension must give a positive sample size")
    if not np.isfinite(config.data.scale) or config.data.scale < 0:
        raise ValueError("the noise scale must be finite and nonnegative")
    python_state, numpy_state = random.getstate(), np.random.get_state()
    with torch.random.fork_rng(devices=[]), _float64_defaults():
        try:
            random.seed(seed + 11)
            np.random.seed((seed + 11) % 2**32)
            generator = torch.Generator(device="cpu").manual_seed(seed + 11)
            torch.set_rng_state(generator.get_state())
            dgp = IsotropicGaussian(
                cfg=config.data, n_train=config.n, dimensions=config.d, seed=seed + 23,
            )
            w_init = torch.randn(config.d, dtype=torch.float64, device="cpu")
        finally:
            random.setstate(python_state)
            np.random.set_state(numpy_state)
    environment = dgp.sample_environment()
    X, _ = dgp.sample_design(environment)
    return dgp, environment, X, w_init


def run_statistical_experiment(config: ExperimentConfig) -> dict:
    """Run finite GD and return its population-error decomposition.

    The result contains the configuration, iterations, population error, optimal
    linear error, alignment regret and bias regret. Arrays have length T + 1.
    """
    data_config, algorithm_config = config.data, config.algorithm
    sigma, p = data_config.scale, data_config.label_prior
    T = algorithm_config.n_iterations
    _, environment, X, w_init = _sample_finite_training(config, _validate_seed(config.seed))
    mu = environment.mu
    initialization = SelfTrainingInitialization(algorithm_config.initial_bias, w_init)
    callback = TestEvaluatorCallback(
        mu=mu, sigma=sigma, p=p, metrics={"population_error"}
    )
    algorithm = SelfTrainedGradientDescent(cfg=algorithm_config, callback=callback)
    y_observed = environment.Y * environment.Delta
    algorithm.fit(X, y_observed, initialization)

    history = callback.history_
    error = np.asarray(history["population_error"])
    norm = np.asarray(history["weight_vector_norm"])
    alignment = np.divide(history["weight_signal_alignment"], norm,
                          out=np.full_like(norm, np.nan), where=norm > 0)
    # The finite optimum applies to positive alignment. Otherwise use the
    # majority-class constant predictor (an extended-real intercept).
    optimal_bias = np.full_like(alignment, -np.inf if p <= 0.5 else np.inf)
    optimal_bias[~np.isfinite(alignment)] = np.nan
    positive = np.isfinite(alignment) & (alignment > 0)
    if p == 0.5:
        optimal_bias[np.isfinite(alignment) & (alignment >= 0)] = 0.0
    else:
        with np.errstate(over="ignore", divide="ignore"):
            optimal_bias[positive] = sigma**2 * np.log(p / (1 - p)) / 2 / alignment[positive]
    conditional_error = np.asarray([
        population_error(b, a, 1.0, sigma, p)
        for b, a in zip(optimal_bias, alignment)
    ])
    signal_scale = float(torch.linalg.vector_norm(mu) / config.d**0.5)
    optimal_error = (population_error(*bayes_parameters(signal_scale, sigma, p), sigma, p)
                     if signal_scale > 0 else min(p, 1 - p))
    return {
        "config": config,
        "iterations": np.arange(T + 1),
        "population_error": error,
        "optimal_linear_error": np.full(T + 1, optimal_error),
        "alignment_regret": conditional_error - optimal_error,
        "bias_regret": error - conditional_error,
    }


def run_monte_carlo_experiment(
    config: MonteCarloConfig, seeds: Iterable[int] | None = None,
) -> dict:
    """Run finite GD and effective-process comparisons for independent seeds.

    Optional seeds override the configuration's seed and repetition count.
    Results contain the configuration, iterations, seeds, and two method
    dictionaries (self_training and effective_process) keyed by metric name.
    Metric arrays have shape (len(seeds), config.algorithm.n_iterations + 1).
    Both selection metrics use current scores and the realized unlabeled count
    in each method, including initialization and the terminal state. A method
    with no unlabeled observations records zero for both fractions.
    """
    if seeds is None:
        if isinstance(config.runs, bool) or not isinstance(config.runs, Integral) or config.runs < 1:
            raise ValueError("runs must be a positive integer")
        base_seed = _validate_seed(config.seed)
        seeds = range(base_seed, base_seed + int(config.runs))
    seeds = [_validate_seed(seed) for seed in seeds]
    if not seeds or len(seeds) != len(set(seeds)):
        raise ValueError("seeds must contain at least one repetition and be distinct")
    if not config.metrics or len(config.metrics) != len(set(config.metrics)):
        raise ValueError("comparison metrics must be nonempty and distinct")
    unsupported = set(config.metrics).difference(_COMPARISON_METRICS)
    if unsupported:
        raise ValueError(f"Unsupported comparison metrics: {sorted(unsupported)}. "
                         f"Choose from {_COMPARISON_METRICS}.")
    data_config, algorithm_config = config.data, config.algorithm
    T = algorithm_config.n_iterations
    if isinstance(T, bool) or not isinstance(T, int) or T < 1:
        raise ValueError("Monte Carlo comparison requires a positive integer n_iterations")
    if isinstance(config.k, bool) or not isinstance(config.k, int) or config.k < 1:
        raise ValueError("k must be a positive integer")
    if not np.isfinite(data_config.scale) or data_config.scale <= 0:
        raise ValueError("Monte Carlo comparison requires a finite positive noise scale")
    track_usage = "unl_usage" in config.metrics
    track_selected_error = "unl_selected_error" in config.metrics
    results = {
        "config": config,
        "iterations": np.arange(T + 1), "seeds": np.asarray(seeds),
        "self_training": {}, "effective_process": {}
    }

    for seed in seeds:
        print(f"Running seed {seed}...")
        dgp, environment, X, w_init = _sample_finite_training(config, seed)
        # Retain the original split adapter's row order and reduction arithmetic.
        labeled_ids = environment.I_L
        order = torch.cat((labeled_ids, environment.I_U))
        X = X[order]
        environment = QuenchedEnvironment(
            mu=environment.mu, Y=environment.Y[order], Delta=environment.Delta[order]
        )
        initialization = SelfTrainingInitialization(
            algorithm_config.initial_bias, w_init
        )
        callback = TestEvaluatorCallback(
            X_unl=X[len(labeled_ids):] if track_usage or track_selected_error else None,
            Y_unl=environment.Y[len(labeled_ids):] if track_selected_error else None,
            mu=environment.mu, sigma=data_config.scale,
            p=data_config.label_prior, metrics=config.metrics,
        )
        algorithm = SelfTrainedGradientDescent(
            cfg=algorithm_config, callback=callback
        )
        y_observed = environment.Y * environment.Delta
        algorithm.fit(X, y_observed, initialization)

        with _float64_defaults():
            se = MacroscopicStateEvolution(
                data_cfg=data_config, algo_cfg=algorithm_config, K=config.k,
                mc_seed=seed + 47,
                sample_base_sampler=state_evolution_sample_base_sampler(dgp.law),
            )
        se.compute_trajectory()
        effective_history = {
            "population_error": se.error,
            "bias_term": se.bias,
            "weight_signal_alignment": se.weight_signal_alignments,
            "weight_vector_norm": se.weight_norm,
        }
        if track_usage or track_selected_error:
            unlabeled = se.indicator == 0
            truth = se.label[unlabeled] if track_selected_error else None
            usage, selected_errors = [], []
            for scores in se.preactivation:
                scores = scores[unlabeled]
                selected = se.selection_mask(scores) > 0
                if track_usage:
                    usage.append(selected.double().mean().item() if scores.numel() else 0.0)
                if track_selected_error:
                    wrong = selected & (sign_with_positive_tie(scores) != truth)
                    selected_errors.append(wrong.double().mean().item() if scores.numel() else 0.0)
            effective_history.update(unl_usage=usage, unl_selected_error=selected_errors)

        for metric in config.metrics:
            results["self_training"].setdefault(metric, []).append(
                np.asarray(callback.history_[metric], dtype=float)
            )
            results["effective_process"].setdefault(metric, []).append(
                np.asarray(effective_history[metric], dtype=float)
            )

    for method in ("self_training", "effective_process"):
        results[method] = {
            metric: np.stack(trajectories)
            for metric, trajectories in results[method].items()
        }
    return results
