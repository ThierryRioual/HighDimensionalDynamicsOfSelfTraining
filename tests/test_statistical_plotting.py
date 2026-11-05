"""Synthetic checks for comparisons of recorded error decompositions."""

from copy import deepcopy

from matplotlib import pyplot as plt
from matplotlib.colors import to_rgba
from matplotlib.figure import Figure
import numpy as np
import pytest

from figures import experiments


def _recorded_result(iterations, offset=0.):
    time = np.asarray(iterations, dtype=float)
    return {
        "iterations": time,
        "optimal_linear_error": np.full(time.size, .08 + offset),
        "alignment_regret": np.linspace(.09, .05, time.size),
        "bias_regret": np.linspace(.04, .02, time.size),
        "population_error": np.linspace(.21 + offset, .15 + offset, time.size),
    }


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


@pytest.mark.parametrize("count", [1, 2, 3])
def test_statistical_panels_follow_supplied_order_and_iteration_grids(count):
    grids = ([0., 1., 2.], [-2., 1., 7.], [3., 4., 10.])
    results = [_recorded_result(grid, .01 * index)
               for index, grid in enumerate(grids[:count])]
    names = [f"Recorded experiment {index}" for index in range(count)]
    fig, axes = experiments.plot_statistical_behavior(results, names)

    assert axes.shape == (1, count)
    assert len(fig.axes) == count
    assert fig.get_constrained_layout()
    first = axes[0, 0]
    for ax, result, name in zip(axes.flat, results, names):
        assert ax.get_title() == name
        assert ax.get_xlabel() == r"Iteration $t$"
        assert ax.get_ylabel() == ""
        assert ax.get_ylim() == (0., .5)
        assert ax.get_legend() is None
        if count > 1:
            assert ax.get_shared_x_axes().joined(first, ax)
            assert ax.get_shared_y_axes().joined(first, ax)
        assert ax.get_xlim() == first.get_xlim()
        np.testing.assert_array_equal(ax.lines[0].get_xdata(), result["iterations"])
        np.testing.assert_array_equal(ax.lines[0].get_ydata(), result["population_error"])
        assert ax.lines[0].get_color() == "black"
        assert ax.lines[0].get_linestyle() == "-"
        assert ax.lines[0].get_linewidth() == 1.
        assert ax.lines[0].get_zorder() > max(area.get_zorder() for area in ax.collections)

    xmin, xmax = first.get_xlim()
    assert xmin <= min(np.min(result["iterations"]) for result in results)
    assert xmax >= max(np.max(result["iterations"]) for result in results)
    assert len(fig.legends) == 1
    labels = [text.get_text() for text in fig.legends[0].get_texts()]
    assert labels == [
        r"Bayes error $\mathcal{E}_{\mathrm{B}}$",
        r"Alignment regret $\mathcal{R}_{\mathrm{align}}^t$",
        r"Intercept regret $\mathcal{R}_{\mathrm{int}}^t$",
        r"Total error $\mathcal{E}^t$",
    ]
    assert len(labels) == len(set(labels)) == 4


def test_statistical_layers_keep_recorded_decomposition_and_colors():
    result = _recorded_result([0., 1., 2.])
    _, axes = experiments.plot_statistical_behavior([result], ["Example"])
    ax = axes[0, 0]
    assert len(ax.collections) == 3
    lower = np.zeros(3)
    for area, key, color in zip(
        ax.collections,
        ("optimal_linear_error", "alignment_regret", "bias_regret"),
        ("#5fae5fff", "tab:blue", "tab:orange"),
    ):
        np.testing.assert_allclose(area.get_facecolor(), [to_rgba(color, alpha=.5)])
        upper = lower + result[key]
        vertices = np.concatenate([path.vertices for path in area.get_paths()])
        for index, time in enumerate(result["iterations"]):
            heights = vertices[vertices[:, 0] == time, 1]
            np.testing.assert_allclose([heights.min(), heights.max()],
                                       [lower[index], upper[index]])
        lower = upper


def test_statistical_plot_preserves_nan_gaps_and_inputs_without_simulating(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("plotting must only consume recorded results")

    monkeypatch.setattr(experiments, "run_statistical_experiment", forbidden)
    monkeypatch.setattr(experiments, "run_monte_carlo_experiment", forbidden)
    monkeypatch.setattr(plt, "savefig", forbidden)
    monkeypatch.setattr(Figure, "savefig", forbidden)
    result = _recorded_result([0., 1., 2., 3., 4.])
    result["alignment_regret"][2] = np.nan
    result["bias_regret"][2] = np.nan
    results = [result]
    names = ["Recorded NaNs"]
    original = deepcopy(results)
    original_names = names.copy()

    _, axes = experiments.plot_statistical_behavior(results, names)

    assert names == original_names
    assert len(results) == len(original)
    for actual, before in zip(results, original):
        assert actual.keys() == before.keys()
        for key in actual:
            np.testing.assert_array_equal(actual[key], before[key])
    ax = axes[0, 0]
    np.testing.assert_array_equal(ax.lines[0].get_ydata(), result["population_error"])
    for area in ax.collections[1:]:
        paths = area.get_paths()
        assert len(paths) == 2
        assert all(np.all(path.vertices[:, 0] < 2.) or
                   np.all(path.vertices[:, 0] > 2.) for path in paths)


@pytest.mark.parametrize("names", [[], ["One", "Two"]])
def test_statistical_plot_rejects_mismatched_lists(names):
    with pytest.raises(ValueError, match="(?i)((same|equal).*length|non.?empty)"):
        experiments.plot_statistical_behavior([_recorded_result([0., 1.])], names)


@pytest.mark.parametrize("names", [[], ["Unexpected"]])
def test_statistical_plot_rejects_empty_results(names):
    with pytest.raises(ValueError, match="(?i)(non.?empty|at least one|empty)"):
        experiments.plot_statistical_behavior([], names)
