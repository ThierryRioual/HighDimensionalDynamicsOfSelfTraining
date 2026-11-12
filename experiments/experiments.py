"""Configurations, simulation runners, and plots for the two paper experiments.

The notebooks choose parameters and call these functions. Importing this module
runs no experiments and creates no figures. Runners return results dictionaries;
plotters consume those dictionaries without rerunning simulations.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from matplotlib import pyplot as plt

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

def run_statistical_experiment(config: ExperimentConfig) -> dict:
    """Run finite GD and return its population-error decomposition.

    The result contains the configuration, iterations, population error, optimal
    linear error, alignment regret and bias regret. Arrays have length T + 1.
    """
    data_config, algorithm_config = config.data, config.algorithm
    sigma, p = data_config.scale, data_config.label_prior
    T = algorithm_config.n_iterations
    # Honor the configured signal law without changing the caller's RNG state.
    with torch.random.fork_rng():
        torch.manual_seed(config.seed + 11)
        dgp = IsotropicGaussian(
            cfg=data_config, n_train=config.n, dimensions=config.d,
            seed=config.seed + 23
        )
        w_init = torch.randn(config.d)
    environment, X, _, _ = dgp.sample()
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
    Both unl_usage and unl_selected_error use current scores at every
    recorded state, including initialization and the terminal state.
    """
    seeds = list(seeds) if seeds is not None else [config.seed + i for i in range(config.runs)]
    if not seeds:
        raise ValueError("seeds must contain at least one repetition")
    supported_metrics = _COMPARISON_METRICS
    unsupported = set(config.metrics).difference(supported_metrics)
    if unsupported:
        raise ValueError(f"Unsupported comparison metrics: {sorted(unsupported)}. "
                         f"Choose from {supported_metrics}.")
    data_config, algorithm_config = config.data, config.algorithm
    T = algorithm_config.n_iterations
    results = {
        "config": config,
        "iterations": np.arange(T + 1), "seeds": np.asarray(seeds),
        "self_training": {}, "effective_process": {}
    }

    for seed in seeds:

        print(f"Running seed {seed}...")

        seed = int(seed)
        with torch.random.fork_rng():
            torch.manual_seed(seed + 11)
            dgp = IsotropicGaussian(
                cfg=data_config, dimensions=config.d, n_train=config.n, seed=seed + 23
            )
            w_init = torch.randn(config.d)
        environment, X, _, _ = dgp.sample()
        # Retain the original split adapter's row order and reduction arithmetic.
        order = torch.cat((environment.I_L, environment.I_U))
        X = X[order]
        environment = QuenchedEnvironment(
            mu=environment.mu, Y=environment.Y[order], Delta=environment.Delta[order]
        )
        initialization = SelfTrainingInitialization(
            algorithm_config.initial_bias, w_init
        )
        callback = TestEvaluatorCallback(
            X_lab=X[environment.I_L], Y_lab=environment.Y[environment.I_L],
            X_unl=X[environment.I_U], Y_unl=environment.Y[environment.I_U],
            mu=environment.mu, sigma=data_config.scale,
            p=data_config.label_prior, metrics=config.metrics
        )
        algorithm = SelfTrainedGradientDescent(
            cfg=algorithm_config, callback=callback
        )
        y_observed = environment.Y * environment.Delta
        algorithm.fit(X, y_observed, initialization)

        effective_process = MacroscopicStateEvolution(
            data_cfg=data_config, algo_cfg=algorithm_config, K=config.k,
            mc_seed=seed + 47,
            sample_base_sampler=state_evolution_sample_base_sampler(dgp.law)
        )
        effective_process.compute_trajectory()
        se = effective_process
        unlabeled = se.indicator == 0
        selected_errors = []
        for scores in se.preactivation:
            selected = se.selection_mask(scores) > 0
            predictions = sign_with_positive_tie(scores)
            incorrect = selected & (predictions != se.label)
            selected_errors.append(
                float(incorrect[unlabeled].double().mean())
                if unlabeled.any() else 0.0
            )
        effective_history = {
            "population_error": se.error,
            "bias_term": se.bias,
            "weight_signal_alignment": se.weight_signal_alignments,
            "weight_vector_norm": se.weight_norm,
            "unl_usage": se.selection_rate[:T + 1],
            "unl_selected_error": selected_errors,
            "oracle_bias": se.oracle_bias,
            "oracle_error": se.oracle_error,
        }
        for metric, trajectory in callback.history_.items():
            results["self_training"].setdefault(metric, []).append(
                np.asarray(trajectory, dtype=float)
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


# Plotting: evaluation and presentation consume recorded results only.

def plot_statistical_behavior(
    results: list[dict],
    names: list[str],
    *,
    save_image: bool = False,
    image_path: str | Path | None = None,
):
    """Plot recorded decompositions; optionally save a 600 dpi PNG.

    Return (figure, 2D axes). The default image path is
    outputs/figures/statistical_behavior_comparison.png relative to the repository root.
    """
    if not results:
        raise ValueError("results must be a nonempty list.")
    if not names:
        raise ValueError("names must be a nonempty list.")
    if len(results) != len(names):
        raise ValueError("results and names must have the same length.")

    ncols = len(results)
    fig, axes = plt.subplots(
        1, ncols, figsize=(4.8 * ncols, 3.4 + 1.8 / ncols),
        sharex=True, sharey=True, squeeze=False, layout="constrained",
    )
    for ax, result, name in zip(axes.flat, results, names):
        time = result["iterations"]
        # NaN regrets create gaps; the recorded error curve remains visible.
        ax.stackplot(
            time, result["optimal_linear_error"], result["alignment_regret"],
            result["bias_regret"],
            labels=(
                r"Bayes error $\mathcal{E}_{\mathrm{B}}$",
                r"Alignment regret $\mathcal{R}_{\mathrm{align}}^t$",
                r"Intercept regret $\mathcal{R}_{\mathrm{int}}^t$",
            ),
            colors=("#5fae5fff", "tab:blue", "tab:orange"), alpha=0.5,
        )
        ax.plot(time, result["population_error"], color="black", linestyle="-",
                linewidth=1.0, label=r"Total error $\mathcal{E}^t$", zorder=3)
        ax.set(title=name, xlabel=r"Iteration $t$", ylim=(0, 0.5))
        ax.grid(alpha=0.25, linewidth=0.6)

    xmin = min(np.min(result["iterations"]) for result in results)
    xmax = max(np.max(result["iterations"]) for result in results)
    if xmin < xmax:
        axes[0, 0].set_xlim(xmin, xmax)
    fig.legend(*axes[0, 0].get_legend_handles_labels(), loc="outside upper center",
               ncol=min(4, 2 * ncols), frameon=False, fontsize=9)
    if save_image:
        destination = (
            Path(__file__).resolve().parents[1] / "outputs" / "figures" / "statistical_behavior_comparison.png"
            if image_path is None else Path(image_path)
        )
        if destination.suffix.lower() != ".png":
            raise ValueError("image_path must have a .png extension.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(destination, format="png", dpi=600, facecolor="white",
                    transparent=False, bbox_inches="tight", pad_inches=0.2)
    return fig, axes


def plot_monte_carlo_experiment(
    results: dict, metrics: str | Iterable[str] | None = None,
    *,
    save_image: bool = False,
    image_path: str | Path | None = None,
):
    """Plot per-iteration Monte Carlo medians, means, and interquartile bands.

    Select existing result keys or ``normalized_alignment`` (m / tau).
    ``weight_vector_norm`` already stores the normalized norm tau=||w||/sqrt(d).
    By default, plot all metrics shared by the methods, plus m / tau if available.
    Selection metrics use the scores at each recorded iteration.
    Return (figure, axes); no simulation is run and results are not modified.
    With save_image=True, save a 600 dpi PNG to image_path or the repository's
    outputs/figures/approximation_accuracy.png by default.
    """
    titles = {
        "population_error": r"Population error $\mathcal{E}^t$",
        "bias_term": r"Intercept $b^t$",
        "weight_vector_norm": r"Weight vector norm $\tau^t$",
        "weight_signal_alignment": r"Signal alignment $m^t$",
        "normalized_alignment": r"Normalized alignment $m^t/\tau^t$",
        "unl_usage": r"Selected fraction $\omega^t$",
        "unl_selected_error": r"Selected-error fraction $e^t$",
        "oracle_bias": r"Oracle intercept $b_{\mathrm{oracle}}^t$",
        "oracle_error": r"Oracle population error",
    }
    methods = (("self_training", "Algorithm", "tab:blue"),
               ("effective_process", "Effective process", "tab:orange"))
    available = [key for key in results["self_training"]
                 if key in results["effective_process"]]
    if all("weight_vector_norm" in results[method] and
           "weight_signal_alignment" in results[method] for method, _, _ in methods):
        available.append("normalized_alignment")
    if metrics is None:
        metrics = available
    elif isinstance(metrics, str):
        metrics = [metrics]
    else:
        metrics = list(metrics)
    if not metrics or any(metric not in available for metric in metrics):
        raise ValueError(f"Select at least one available metric: {available}")

    ncols = min(3, len(metrics))
    nrows = (len(metrics) + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.8 * ncols, 3.4 * nrows + 1.8 / ncols),
                             squeeze=False, layout="constrained")
    for ax, metric in zip(axes.flat, metrics):
        for method, label, color in methods:
            values = results[method]
            if metric == "normalized_alignment":
                norm = np.asarray(values["weight_vector_norm"], dtype=float)
                values = np.divide(values["weight_signal_alignment"], norm,
                                   out=np.full_like(norm, np.nan), where=norm > 0)
            else:
                values = np.asarray(values[metric], dtype=float)
            q1, median, q3 = np.percentile(values, [25, 50, 75], axis=0)
            ax.fill_between(results["iterations"], q1, q3, color=color,
                            alpha=0.18, linewidth=0, label=f"{label}: IQR")
            ax.plot(results["iterations"], median, color=color, linewidth=1.6,
                    label=f"{label}: median")
            ax.plot(results["iterations"], np.mean(values, axis=0), color=color,
                    linestyle=":", linewidth=1.6, label=f"{label}: mean")
        ax.set(title=titles.get(metric, metric.replace("_", " ").capitalize()),
               xlabel=r"Iteration $t$")
        ax.grid(alpha=0.25, linewidth=0.6)
    for ax in list(axes.flat)[len(metrics):]:
        ax.set_visible(False)
    fig.legend(*axes.flat[0].get_legend_handles_labels(), loc="outside upper center",
               ncol=ncols, frameon=False, fontsize=9)
    if save_image:
        destination = (
            Path(__file__).resolve().parents[1] / "outputs" / "figures" / "approximation_accuracy.png"
            if image_path is None else Path(image_path)
        )
        if destination.suffix.lower() != ".png":
            raise ValueError("image_path must have a .png extension.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(destination, format="png", dpi=600, facecolor="white",
                    transparent=False, bbox_inches="tight", pad_inches=0.2)
    return fig, axes
