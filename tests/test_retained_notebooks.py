"""Small simulations and numerical plot checks for the paper entry points."""

import ast
from dataclasses import replace
import importlib
import json
from pathlib import Path
from types import SimpleNamespace

from matplotlib import pyplot as plt
import numpy as np
import pytest
from scipy.special import ndtr
import torch

from figures import experiments
from src.algorithms import SelfTrainedGradientDescent
from src.config import AlgorithmConfig, DataConfig


def test_notebooks_import_shared_experiment_functions():
    root = Path(__file__).resolve().parents[1]
    for name, runner, plotter, config in [
        ("statistical_behavior", "run_statistical_experiment",
         "plot_statistical_behavior", "ExperimentConfig"),
        ("approximation_accuracy", "run_monte_carlo_experiment",
         "plot_monte_carlo_experiment", "MonteCarloConfig"),
    ]:
        notebook = json.loads((root / "figures" / f"{name}.ipynb").read_text())
        imported = set()
        for cell in notebook["cells"]:
            if cell["cell_type"] != "code":
                continue
            source = "\n".join(line for line in cell["source"]
                               if not line.lstrip().startswith("%"))
            for node in ast.parse(source).body:
                if isinstance(node, ast.ImportFrom) and node.module == "figures.experiments":
                    imported.update(alias.name for alias in node.names)
        for attribute in (runner, plotter, config):
            assert attribute in imported and callable(getattr(experiments, attribute))


def test_shared_module_import_does_not_simulate_or_create_figures(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("importing experiment definitions must not run an experiment")

    monkeypatch.setattr(experiments.IsotropicGaussian, "sample", forbidden)
    monkeypatch.setattr(experiments.SelfTrainedGradientDescent, "fit", forbidden)
    monkeypatch.setattr(experiments.MacroscopicStateEvolution, "compute_trajectory", forbidden)
    monkeypatch.setattr(plt, "subplots", forbidden)
    rng = torch.get_rng_state().clone()
    figures = plt.get_fignums()
    importlib.reload(experiments)
    assert torch.equal(torch.get_rng_state(), rng)
    assert plt.get_fignums() == figures


@pytest.mark.parametrize("prior", [.5, .2])
def test_statistical_runner_error_regrets_and_plot(monkeypatch, prior):
    learners = []

    def capture(*args, **kwargs):
        learner = SelfTrainedGradientDescent(*args, **kwargs)
        learners.append(learner)
        return learner

    monkeypatch.setattr(experiments, "SelfTrainedGradientDescent", capture)
    config = experiments.ExperimentConfig(
        DataConfig(.8, prior, .4, 3., lambda: 2.),
        AlgorithmConfig(4, .1, .2, .7, margin_threshold=.5,
                        initial_bias=.2, train_bias=False), d=24, seed=49)
    rng = torch.get_rng_state().clone()
    result = experiments.run_statistical_experiment(config)
    assert torch.equal(torch.get_rng_state(), rng)
    assert result["config"] is config
    np.testing.assert_array_equal(result["iterations"], np.arange(5))
    learner = learners[0]
    assert learner.cfg is config.algorithm and learner.y_observed_.shape == (config.n,)
    assert not hasattr(learner, "environment_")
    torch.testing.assert_close(learner.callback.mu, torch.full((24,), 2.))
    history = learner.callback.history_
    norm = np.asarray(history["weight_vector_norm"])
    alignment = np.asarray(history["weight_signal_alignment"]) / norm
    bias = np.asarray(history["bias_term"]) / norm
    expected_error = prior * ndtr((-bias-alignment)/.8) + (1-prior) * ndtr((bias-alignment)/.8)
    conditional_error = np.full_like(alignment, min(prior, 1-prior))
    positive = alignment > 0
    optimal_bias = .8**2 * np.log(prior/(1-prior)) / (2*alignment[positive])
    conditional_error[positive] = (
        prior * ndtr((-optimal_bias-alignment[positive])/.8)
        + (1-prior) * ndtr((optimal_bias-alignment[positive])/.8))
    bayes_bias = .8**2 * np.log(prior/(1-prior)) / 4
    optimal_error = prior * ndtr((-bayes_bias-2)/.8) + (1-prior) * ndtr((bayes_bias-2)/.8)
    np.testing.assert_allclose(result["population_error"], expected_error, atol=1e-14)
    np.testing.assert_allclose(result["optimal_linear_error"], optimal_error, atol=1e-14)
    np.testing.assert_allclose(result["alignment_regret"], conditional_error-optimal_error, atol=1e-14)
    np.testing.assert_allclose(result["bias_regret"], expected_error-conditional_error, atol=1e-14)
    replay = experiments.run_statistical_experiment(config)
    for metric in result:
        if metric != "config":
            np.testing.assert_array_equal(result[metric], replay[metric])
    fig, axes = experiments.plot_statistical_behavior([result], ["Recorded experiment"])
    ax = axes[0, 0]
    assert len(fig.axes) == 1 and len(ax.collections) == 3
    np.testing.assert_array_equal(ax.lines[0].get_ydata(), result["population_error"])
    plt.close(fig)


@pytest.mark.parametrize("prior", [.2, .5, .8])
def test_statistical_regret_domains(monkeypatch, prior):
    alignment = np.array([-1., 0., 1e-18, .5, 0.])
    norm = np.array([1., 1., 1., 1., 0.])
    bias = np.array([.1, .2, -.1, .3, 0.])
    error = prior * ndtr(-bias-alignment) + (1-prior) * ndtr(bias-alignment)
    error[-1] = 1-prior  # Zero score predicts +1 under the project's tie rule.

    def fake_learner(cfg, callback):
        callback.history_.update(population_error=error, weight_vector_norm=norm,
                                 weight_signal_alignment=alignment, bias_term=bias)
        return SimpleNamespace(fit=lambda *args: None)

    monkeypatch.setattr(experiments, "SelfTrainedGradientDescent", fake_learner)
    config = experiments.ExperimentConfig(
        DataConfig(1., prior, .4, 3., lambda: 1.),
        AlgorithmConfig(4, .1, .1, .4, margin_threshold=.5), d=24)
    result = experiments.run_statistical_experiment(config)
    conditional = result["alignment_regret"] + result["optimal_linear_error"]
    np.testing.assert_allclose(conditional[:2], min(prior, 1-prior), atol=1e-14)
    optimal_bias = np.log(prior/(1-prior)) / (2*alignment[2:4])
    expected = prior * ndtr(-optimal_bias-alignment[2:4]) + (1-prior) * ndtr(optimal_bias-alignment[2:4])
    np.testing.assert_allclose(conditional[2:4], expected, atol=1e-14)
    assert np.isnan(result["alignment_regret"][-1]) and np.isnan(result["bias_regret"][-1])
    fig, axes = experiments.plot_statistical_behavior([result], ["Recorded experiment"])
    ax = axes[0, 0]
    np.testing.assert_array_equal(ax.lines[0].get_ydata(), error)
    assert all(np.all(path.vertices[:, 0] < 4) for path in ax.collections[1].get_paths())
    plt.close(fig)


def test_statistical_zero_signal_benchmark():
    config = experiments.ExperimentConfig(
        DataConfig(1., .2, .4, 3., lambda: 0.),
        AlgorithmConfig(2, .1, .1, .4, margin_threshold=.5), d=24)
    result = experiments.run_statistical_experiment(config)
    np.testing.assert_array_equal(result["optimal_linear_error"], np.full(3, .2))
    np.testing.assert_allclose(result["alignment_regret"], 0, atol=1e-14)


@pytest.mark.parametrize("train_bias", [True, False])
def test_approximation_runner_config_replay_and_selection(monkeypatch, train_bias):
    finite, particles = [], []
    effective_class = experiments.MacroscopicStateEvolution

    def capture_finite(*args, **kwargs):
        learner = SelfTrainedGradientDescent(*args, **kwargs)
        finite.append(learner)
        return learner

    def capture_effective(*args, **kwargs):
        process = effective_class(*args, **kwargs)
        particles.append(process)
        return process

    monkeypatch.setattr(experiments, "SelfTrainedGradientDescent", capture_finite)
    monkeypatch.setattr(experiments, "MacroscopicStateEvolution", capture_effective)
    config = experiments.MonteCarloConfig(
        DataConfig(.7, .65, .4, 3., lambda: 2.),
        AlgorithmConfig(3, .07, .4, .9, positive_margin=.8, negative_margin=-.6,
                        initial_bias=.35, train_bias=train_bias, bias_step_size=.03),
        d=24, seed=42, k=128, runs=2)
    rng = torch.get_rng_state().clone()
    result = experiments.run_monte_carlo_experiment(config)
    assert torch.equal(torch.get_rng_state(), rng)
    assert result["config"] is config
    np.testing.assert_array_equal(result["seeds"], [42, 43])
    np.testing.assert_array_equal(result["iterations"], np.arange(4))
    for method in ("self_training", "effective_process"):
        assert set(result[method]) == set(config.metrics) | {"oracle_bias", "oracle_error"}
        for values in result[method].values():
            assert values.shape == (2, 4) and np.isfinite(values).all()
        assert not np.array_equal(result[method]["population_error"][0],
                                  result[method]["population_error"][1])
    for i, (learner, process) in enumerate(zip(finite, particles)):
        assert learner.cfg is process.algo_cfg is config.algorithm
        assert process.data_cfg is config.data and process.K_w == process.K_g == 128
        torch.testing.assert_close(learner.callback.mu, torch.full((24,), 2.))
        assert learner.y_observed_.shape == (config.n,)
        assert not hasattr(learner, "environment_")
        # Preserve the former adapter's L-then-U row order and observed labels.
        n_labeled = learner.callback.X_lab.shape[0]
        torch.testing.assert_close(learner.y_observed_[:n_labeled], learner.callback.Y_lab)
        assert torch.all(learner.y_observed_[n_labeled:] == 0)
        for step in learner.update_records_:
            alignment = torch.dot(learner.callback.mu, step.weight) / config.d
            assert learner.callback.history_["weight_signal_alignment"][step.t] == pytest.approx(float(alignment))
        torch.testing.assert_close(process.signal, torch.full((128,), 2.))
        if not train_bias:
            np.testing.assert_allclose(learner.callback.history_["bias_term"], .35)
            np.testing.assert_allclose([float(b) for b in process.bias], .35)
        for t, scores in enumerate(process.preactivation):
            selected = process.selection_mask(scores) > 0
            incorrect = selected & (torch.where(scores >= 0, 1, -1) != process.label)
            expected = incorrect[process.indicator == 0].double().mean().item()
            assert result["effective_process"]["unl_selected_error"][i, t] == pytest.approx(expected)
        np.testing.assert_array_equal(result["effective_process"]["unl_usage"][i],
                                      [float(v) for v in process.selection_rate[:4]])
        np.testing.assert_array_equal(result["self_training"]["unl_usage"][i],
                                      [float(step.omega) for step in learner.update_records_]
                                      + [learner.selection_mask(learner.decision_function(learner.callback.X_unl)).double().mean().item()])
    replay = experiments.run_monte_carlo_experiment(config)
    for method in ("self_training", "effective_process"):
        for metric in result[method]:
            np.testing.assert_array_equal(result[method][metric], replay[method][metric])
    short = replace(config, algorithm=replace(config.algorithm, n_iterations=1))
    overridden = experiments.run_monte_carlo_experiment(short, seeds=[101])
    np.testing.assert_array_equal(overridden["seeds"], [101])
    assert overridden["self_training"]["population_error"].shape == (1, 2)


def test_approximation_comparison_metric_contract():
    config = experiments.MonteCarloConfig(
        DataConfig(.8, .2, .4, 3., lambda: 1.),
        AlgorithmConfig(1, .1, .1, .4, margin_threshold=.5),
        d=24, k=64, runs=1, metrics=("test_error",))
    with pytest.raises(ValueError, match="Unsupported comparison metrics"):
        experiments.run_monte_carlo_experiment(config)
    result = experiments.run_monte_carlo_experiment(
        replace(config, metrics=("unl_selected_error",)))
    for method in ("self_training", "effective_process"):
        assert set(result[method]) == {"unl_selected_error"}
        assert result[method]["unl_selected_error"].shape == (1, 2)


def test_approximation_plot_statistics_and_independence(monkeypatch):
    sample = np.array([[1, 4, 2], [2, 6, 4], [3, 8, 8], [20, 10, 30]], dtype=float)
    result = {"iterations": np.arange(3), "self_training": {"population_error": sample},
              "effective_process": {"population_error": sample+2}}

    def forbidden(*args, **kwargs):
        raise AssertionError("plotting must not rerun simulation")

    monkeypatch.setattr(experiments, "run_monte_carlo_experiment", forbidden)
    fig, axes = experiments.plot_monte_carlo_experiment(result, metrics="population_error")
    ax = axes[0, 0]
    for i, values in enumerate((sample, sample+2)):
        q1, median, q3 = np.percentile(values, [25, 50, 75], axis=0)
        np.testing.assert_array_equal(ax.lines[2*i].get_ydata(), median)
        np.testing.assert_array_equal(ax.lines[2*i+1].get_ydata(), values.mean(axis=0))
        assert ax.lines[2*i].get_linestyle() == "-"
        assert ax.lines[2*i+1].get_linestyle() == ":"
        assert ax.lines[2*i].get_color() == ("tab:blue", "tab:orange")[i]
        vertices = ax.collections[i].get_paths()[0].vertices
        for t in range(3):
            y = vertices[vertices[:, 0] == t, 1]
            np.testing.assert_allclose([y.min(), y.max()], [q1[t], q3[t]])
    np.testing.assert_array_equal(result["self_training"]["population_error"], sample)
    plt.close(fig)
    norms = np.array([[1., 2., 4.], [2., 3., 5.]])
    alignments = np.array([[1., 4., 8.], [6., 9., 20.]])
    result = {"iterations": np.arange(3), "self_training": {
        "weight_vector_norm": norms, "weight_signal_alignment": alignments}}
    result["effective_process"] = dict(result["self_training"])
    fig, axes = experiments.plot_monte_carlo_experiment(result)
    assert sum(ax.get_visible() for ax in axes.flat) == 3
    np.testing.assert_allclose(axes.flat[2].lines[0].get_ydata(), np.median(alignments/norms, axis=0))
    np.testing.assert_allclose(axes.flat[2].lines[1].get_ydata(), np.mean(alignments/norms, axis=0))
    plt.close(fig)
