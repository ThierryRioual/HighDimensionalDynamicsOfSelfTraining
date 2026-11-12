"""Optional PNG exports use recorded results and the returned Figure directly."""

from copy import deepcopy
from inspect import Parameter, signature
from pathlib import Path
from struct import unpack_from

from matplotlib import pyplot as plt
from matplotlib.figure import Figure
import numpy as np
import pytest

from experiments import experiments


@pytest.fixture(autouse=True)
def _isolate_plotting(monkeypatch):
    # Resolve the backend before forbidding display operations in the functions.
    plt.get_backend()
    close = plt.close

    def forbidden(*args, **kwargs):
        raise AssertionError("plotting must not simulate, display, or close figures")

    for name in ("run_statistical_experiment", "run_monte_carlo_experiment"):
        monkeypatch.setattr(experiments, name, forbidden)
    for name in ("savefig", "show", "close"):
        monkeypatch.setattr(plt, name, forbidden)
    yield
    close("all")


@pytest.fixture(params=("statistical", "monte_carlo"))
def plot_case(request):
    iterations = np.array([0., 1., 2.])
    if request.param == "statistical":
        result = {
            "iterations": iterations,
            "optimal_linear_error": np.full(3, .08),
            "alignment_regret": np.array([.09, .07, .05]),
            "bias_regret": np.array([.04, .03, .02]),
            "population_error": np.array([.21, .18, .15]),
        }
        return (
            experiments.plot_statistical_behavior,
            ([result], ["Recorded experiment"]),
            "statistical_behavior_comparison.png",
            4,
        )
    result = {
        "iterations": iterations,
        "self_training": {
            "population_error": np.array([[.30, .24, .20], [.32, .26, .22]])
        },
        "effective_process": {
            "population_error": np.array([[.29, .23, .19], [.31, .25, .21]])
        },
    }
    return (
        experiments.plot_monte_carlo_experiment,
        (result,),
        "approximation_accuracy.png",
        6,
    )


def test_saving_options_are_optional_and_keyword_only(plot_case):
    plot, _, _, _ = plot_case
    parameters = signature(plot).parameters
    for name, default in (("save_image", False), ("image_path", None)):
        assert parameters[name].kind is Parameter.KEYWORD_ONLY
        assert parameters[name].default is default


def test_saving_disabled_has_no_filesystem_effects(plot_case, tmp_path, monkeypatch):
    plot, args, filename, _ = plot_case
    fake_repo = tmp_path / "repository"
    monkeypatch.setattr(experiments, "__file__", str(fake_repo / "experiments" / "experiments.py"))

    def forbidden(*args, **kwargs):
        raise AssertionError("saving disabled must not call Figure.savefig")

    monkeypatch.setattr(Figure, "savefig", forbidden)
    plot(*args)
    plot(*args, save_image=False, image_path=tmp_path / "custom" / filename)
    # An unused output path is not validated or created.
    plot(*args, save_image=False, image_path=tmp_path / "unused" / "figure.pdf")
    assert list(tmp_path.iterdir()) == []


def test_custom_png_is_high_resolution_white_and_keeps_shared_legend(
    plot_case, tmp_path, monkeypatch
):
    plot, args, filename, legend_count = plot_case
    original = deepcopy(args)
    path = tmp_path / "nested" / "figures" / filename
    original_rc = plt.rcParams.copy()
    _, unsaved_axes = plot(*args)
    calls = []
    savefig = Figure.savefig

    def record_savefig(fig, filename, **kwargs):
        calls.append((fig, Path(filename), kwargs.copy()))
        return savefig(fig, filename, **kwargs)

    monkeypatch.setattr(Figure, "savefig", record_savefig)
    fig, axes = plot(*args, save_image=True, image_path=path)

    assert len(calls) == 1
    assert calls[0][0] is fig
    assert calls[0][1] == path
    for key, value in {
        "format": "png", "dpi": 600, "facecolor": "white",
        "transparent": False, "bbox_inches": "tight", "pad_inches": .2,
    }.items():
        assert calls[0][2][key] == value
    assert axes.shape == (1, 1)
    assert plt.fignum_exists(fig.number)
    assert len(fig.legends) == 1
    assert len(fig.legends[0].get_texts()) == legend_count
    assert axes[0, 0].get_legend() is None
    np.testing.assert_equal(args, original)
    assert plt.rcParams == original_rc
    assert axes[0, 0].get_xlim() == unsaved_axes[0, 0].get_xlim()
    assert axes[0, 0].get_ylim() == unsaved_axes[0, 0].get_ylim()
    assert axes[0, 0].get_ylabel() == unsaved_axes[0, 0].get_ylabel()
    for actual, unsaved in zip(axes[0, 0].lines, unsaved_axes[0, 0].lines):
        np.testing.assert_array_equal(actual.get_xdata(), unsaved.get_xdata())
        np.testing.assert_array_equal(actual.get_ydata(), unsaved.get_ydata())
        assert actual.get_color() == unsaved.get_color()
        assert actual.get_linestyle() == unsaved.get_linestyle()

    png = path.read_bytes()
    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    offset = 8
    while offset < len(png):
        length, kind = unpack_from(">I4s", png, offset)
        if kind == b"pHYs":
            horizontal, vertical, unit = unpack_from(">IIB", png, offset + 8)
            assert unit == 1  # PNG stores pixel density in pixels per meter.
            np.testing.assert_allclose(
                np.array([horizontal, vertical]) * .0254, [600., 600.], atol=.01
            )
            break
        offset += length + 12
    else:
        pytest.fail("Saved PNG has no resolution metadata")
    image = plt.imread(path)
    np.testing.assert_array_equal(image[0, 0, :3], np.ones(3))
    np.testing.assert_array_equal(image[-1, -1, :3], np.ones(3))

    # The tight export region includes every title, axis label, and legend label.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    export_bbox = fig.get_tightbbox(renderer).padded(.2)
    labels = [*fig.legends[0].get_texts(), axes[0, 0].title,
              axes[0, 0].xaxis.label, axes[0, 0].yaxis.label]
    for label in labels:
        if not label.get_text():
            continue
        bounds = label.get_window_extent(renderer).transformed(fig.dpi_scale_trans.inverted())
        assert export_bbox.contains(bounds.x0, bounds.y0)
        assert export_bbox.contains(bounds.x1, bounds.y1)


def test_default_png_uses_repository_output_directory(plot_case, tmp_path, monkeypatch):
    plot, args, filename, _ = plot_case
    fake_repo = tmp_path / "repository"
    monkeypatch.setattr(experiments, "__file__", str(fake_repo / "experiments" / "experiments.py"))
    calls = []

    def record_savefig(fig, filename, **kwargs):
        calls.append((fig, Path(filename), kwargs))

    monkeypatch.setattr(Figure, "savefig", record_savefig)
    fig, _ = plot(*args, save_image=True)
    assert len(calls) == 1
    assert calls[0][0] is fig
    assert calls[0][1] == fake_repo / "outputs" / "figures" / filename
    assert calls[0][1].parent.is_dir()


def test_enabled_saving_rejects_pdf_paths(plot_case, tmp_path, monkeypatch):
    plot, args, _, _ = plot_case

    def forbidden(*args, **kwargs):
        raise AssertionError("invalid paths must not write a figure")

    monkeypatch.setattr(Figure, "savefig", forbidden)
    with pytest.raises(ValueError, match="(?i)png"):
        plot(*args, save_image=True, image_path=tmp_path / "unused" / "figure.pdf")
    assert list(tmp_path.iterdir()) == []
