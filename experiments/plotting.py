"""Plot recorded experiments and save figures without changing their typography."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from contextlib import AbstractContextManager
from pathlib import Path

from matplotlib import pyplot as plt
from matplotlib.figure import Figure
import numpy as np
from scipy.stats import gaussian_kde


def experiment_plot_style() -> AbstractContextManager[None]:
    """Scope the dataset plotting defaults to the current figure or cell."""
    return plt.rc_context({
        "figure.dpi": 110,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def _figure_format(path: Path) -> str:
    file_format = path.suffix.lower().lstrip(".")
    if file_format not in ("pdf", "png"):
        raise ValueError("Figure path must have a .pdf or .png extension.")
    return file_format


def save_figure(fig: Figure, path: str | Path, *, pad_inches: float = 0.2) -> None:
    """Save a vector PDF or 600 dpi PNG without changing the figure's style."""
    destination = Path(path)
    file_format = _figure_format(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, format=file_format, dpi=600, facecolor="white",
                transparent=False, bbox_inches="tight", pad_inches=pad_inches)


def _export_destination(
    enabled: bool, image_path: str | Path | None, default_name: str,
) -> Path | None:
    if not enabled:
        return None
    destination = (Path(__file__).resolve().parents[1] / "outputs" / "figures" / default_name
                   if image_path is None else Path(image_path))
    _figure_format(destination)
    return destination


def _style_axes(fig: Figure, manuscript: bool) -> float | None:
    """Set the print typography and return the recommended legend size."""
    if not manuscript:
        return None
    # Convert target point sizes at manuscript width to source-figure points.
    scale = fig.get_figwidth() / 6.27
    for ax in fig.axes:
        ax.title.set_fontsize(6.0 * scale)
        ax.xaxis.label.set_fontsize(5.0 * scale)
        ax.yaxis.label.set_fontsize(5.0 * scale)
        ax.tick_params(axis="both", labelsize=4.0 * scale)
    return 6.0 * scale



def _style_comparison(
    fig: Figure, axes: np.ndarray, legend_columns: int,
    manuscript: bool, legend_font_size: float | None,
) -> float | None:
    """Apply the shared comparison grid and typography, with the legend below."""
    for ax in axes.flat:
        ax.grid(alpha=0.25, linewidth=0.6)
    font_size = _style_axes(fig, manuscript)
    fig.legend(*axes.flat[0].get_legend_handles_labels(), loc="outside lower center",
               ncol=legend_columns, frameon=False,
               fontsize=legend_font_size if legend_font_size is not None else (font_size or 9))
    return font_size


def _summarize_trajectories(values: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return Q1, median, Q3, and mean without letting one missing run erase a time."""
    finite = np.isfinite(values)
    if finite.all():
        q1, median, q3 = np.percentile(values, [25, 50, 75], axis=0)
        return q1, median, q3, values.mean(axis=0)
    has_data = finite.any(axis=0)
    summary = np.full((4, values.shape[1]), np.nan)
    if has_data.any():
        observed = np.where(finite[:, has_data], values[:, has_data], np.nan)
        summary[:3, has_data] = np.nanpercentile(observed, [25, 50, 75], axis=0)
        summary[3, has_data] = np.nanmean(observed, axis=0)
    return summary[0], summary[1], summary[2], summary[3]


def plot_statistical_behavior(
    results: list[dict],
    names: list[str],
    *,
    save_image: bool = False,
    image_path: str | Path | None = None,
    manuscript: bool = False,
    legend_font_size: float | None = None,
):
    """Plot recorded decompositions; optionally save a vector PDF.

    Set manuscript=True for paper typography. legend_font_size overrides the
    chosen preset in source-figure points. Return (figure, 2D axes).
    The default image path is
    outputs/figures/statistical_behavior_comparison.pdf relative to the repository root.
    """
    if not results:
        raise ValueError("results must be a nonempty list.")
    if not names:
        raise ValueError("names must be a nonempty list.")
    if len(results) != len(names):
        raise ValueError("results and names must have the same length.")

    destination = _export_destination(save_image, image_path, "statistical_behavior_comparison.pdf")
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
    font_size = _style_axes(fig, manuscript)
    fig.legend(*axes[0, 0].get_legend_handles_labels(), loc="outside lower center",
               ncol=min(4, 2 * ncols), frameon=False,
               fontsize=legend_font_size if legend_font_size is not None else (font_size or 9))
    if destination is not None:
        save_figure(fig, destination)
    return fig, axes


_TRAJECTORY_TITLES = {
    "population_error": r"Population error $\mathcal{E}^t$",
    "test_error": r"Test error $\mathcal{E}^t$",
    "bias_term": r"Intercept $b^t$",
    "weight_vector_norm": r"Weight vector norm $\tau^t$",
    "weight_signal_alignment": r"Signal alignment $m^t$",
    "normalized_alignment": r"Normalized alignment $m^t/\tau^t$",
    "unl_usage": r"Selected fraction $\omega^t$",
    "unl_selected_error": r"Selected-error fraction $e^t$",
    "oracle_bias": r"Stationary intercept $b_{\mathrm{stat}}^t$",
    "oracle_error": r"Population error at stationary intercept",
}


def plot_trajectory_comparison(
    results: dict,
    metrics: list[str],
    methods: Sequence[tuple[str, str, str]],
    *,
    manuscript: bool = False,
    legend_font_size: float | None = None,
    median_only: bool = False,
    line_styles: Mapping[str, str] | None = None,
):
    """Draw a comparison of up to three columns with median, mean and IQR.

    Aggregate finite repetitions separately at each iteration. Leave gaps
    where no finite values remain. Set median_only for a line-only comparison.
    The optional line_styles mapping controls each method's median line.
    """
    if not metrics or not methods:
        raise ValueError("At least one metric and method are required.")
    time = np.asarray(results["iterations"])
    if time.ndim != 1 or not time.size or not np.isfinite(time).all():
        raise ValueError("iterations must be a nonempty finite one-dimensional array.")
    summaries = {}
    for metric in metrics:
        for method, _, _ in methods:
            values = np.asarray(results[method][metric], dtype=float)
            if values.ndim != 2 or not values.shape[0] or values.shape[1] != time.size:
                raise ValueError(f"{method}/{metric} must have shape (repetitions, {time.size}).")
            summaries[method, metric] = _summarize_trajectories(values)
    ncols = min(3, len(metrics))
    nrows = (len(metrics) + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.8 * ncols, 3.4 * nrows + 1.8 / ncols),
                             squeeze=False, layout="constrained")
    for ax, metric in zip(axes.flat, metrics):
        for method, label, color in methods:
            q1, median, q3, mean = summaries[method, metric]
            if not median_only:
                ax.fill_between(time, q1, q3, color=color,
                                alpha=0.18, linewidth=0, label=f"{label}: IQR")
            ax.plot(time, median, color=color, linewidth=1.6,
                    linestyle=(line_styles or {}).get(method, "-"),
                    label=f"{label}: median" if not median_only else label)
            if not median_only:
                ax.plot(time, mean, color=color,
                        linestyle=":", linewidth=1.6, label=f"{label}: mean")
        ax.set(title=_TRAJECTORY_TITLES.get(metric, metric.replace("_", " ").capitalize()),
               xlabel=r"Iteration $t$")
    for ax in list(axes.flat)[len(metrics):]:
        ax.set_visible(False)
    _style_comparison(fig, axes, ncols, manuscript, legend_font_size)
    return fig, axes


def plot_monte_carlo_experiment(
    results: dict, metrics: str | Iterable[str] | None = None,
    *,
    save_image: bool = False,
    image_path: str | Path | None = None,
    manuscript: bool = False,
    legend_font_size: float | None = None,
):
    """Plot per-iteration Monte Carlo medians, means, and interquartile bands.

    Select existing result keys or ``normalized_alignment`` (m / tau).
    ``weight_vector_norm`` already stores the normalized norm tau=||w||/sqrt(d).
    By default, plot shared metrics and m / tau when available. Historical
    stationary-intercept diagnostics require explicit selection.
    Set manuscript=True for paper typography, or supply legend_font_size in
    source-figure points to override only the legend.
    Selection metrics use the scores at each recorded iteration.
    Return (figure, axes); no simulation is run and results are not modified.
    With save_image=True, save a vector PDF to image_path or the repository's
    outputs/figures/approximation_accuracy.pdf by default.
    """
    methods = (("self_training", "Algorithm", "tab:blue"),
               ("effective_process", "Effective process", "tab:orange"))
    available = [key for key in results["self_training"]
                 if key in results["effective_process"]]
    if all("weight_vector_norm" in results[method] and
           "weight_signal_alignment" in results[method] for method, _, _ in methods):
        if "normalized_alignment" not in available:
            available.append("normalized_alignment")
    if metrics is None:
        metrics = [name for name in available if name not in ("oracle_bias", "oracle_error")]
    elif isinstance(metrics, str):
        metrics = [metrics]
    else:
        metrics = list(metrics)
    if not metrics or any(metric not in available for metric in metrics):
        raise ValueError(f"Select at least one available metric: {available}")

    destination = _export_destination(save_image, image_path, "approximation_accuracy.pdf")
    if "normalized_alignment" in metrics:
        results = results.copy()
        for method, _, _ in methods:
            history = results[method]
            if "normalized_alignment" not in history:
                norm = np.asarray(history["weight_vector_norm"], dtype=float)
                normalized = np.divide(
                    history["weight_signal_alignment"], norm,
                    out=np.full_like(norm, np.nan), where=np.isfinite(norm) & (norm > 0),
                )
                results[method] = {**history, "normalized_alignment": normalized}
    fig, axes = plot_trajectory_comparison(
        results, metrics, methods, manuscript=manuscript, legend_font_size=legend_font_size,
    )
    if destination is not None:
        save_figure(fig, destination)
    return fig, axes


def plot_checkpoint_distributions(
    rows: Sequence[tuple[Mapping[int, tuple[np.ndarray, np.ndarray]], str, Sequence[float]]],
    *,
    manuscript: bool = False,
    labels: tuple[str, str] = ("Real self-training", "Effective process"),
) -> Figure:
    """Draw density panels with shared scales within each row and one legend.

    Each row supplies checkpoint samples, an x-axis label, and optional score thresholds.
    """
    if not rows or not rows[0][0]:
        raise ValueError("At least one checkpoint is required.")
    times = sorted(rows[0][0])
    if any(sorted(samples) != times for samples, _, _ in rows):
        raise ValueError("All rows must have the same checkpoints.")
    fig, axes = plt.subplots(
        len(rows), len(times), figsize=(3.4 * len(times) + 0.6, 2.8 * len(rows) + 0.6),
        sharex="row", sharey="row", squeeze=False, layout="constrained",
    )
    for row_index, (row, (samples_by_iteration, xlabel, thresholds)) in enumerate(zip(axes, rows)):
        samples = [samples_by_iteration[t] for t in times]
        low = min(values.min() for pair in samples for values in pair)
        high = max(values.max() for pair in samples for values in pair)
        if thresholds:
            low, high = min(low, min(thresholds)), max(high, max(thresholds))
        padding = 0.05 * (high - low) if high > low else 0.05
        bins = np.linspace(low - padding, high + padding, 81)
        grid = np.linspace(bins[0], bins[-1], 400)
        for ax, t, (real, effective) in zip(row, times, samples):
            ax.hist(real, bins=bins, density=True, color="tab:blue", alpha=0.35, label=labels[0])
            if np.ptp(effective) == 0:
                ax.axvline(effective[0], color="tab:orange", label=labels[1])
            else:
                ax.plot(grid, gaussian_kde(effective)(grid), color="tab:orange", label=labels[1])
            for i, threshold in enumerate(thresholds):
                ax.axvline(
                    threshold, color="tab:gray", linestyle="--", linewidth=1,
                    label=r"Selection thresholds $\kappa$" if i == 0 else None,
                )
            ax.set(title=f"Iteration $t={t}$" if row_index == 0 else "", xlabel=xlabel, xlim=(bins[0], bins[-1]))

        row[0].set_ylabel("Probability density")
    _style_comparison(fig, axes, 3, manuscript, None)
    return fig
