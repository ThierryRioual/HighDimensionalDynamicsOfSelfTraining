"""Tables, figures, and data-dependent commentary for cached experiment results.

This module only reads result dictionaries. It never trains a model or changes a
configuration. State and update times are kept separate throughout the plots.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BRANCHES = ("dynamic", "frozen", "oracle")
COLORS = {"dynamic": "#175da8", "frozen": "#df8323", "oracle": "#287d48"}
LABELS = {"dynamic": "Dynamic", "frozen": "Frozen targets + set", "oracle": "Frozen set, true targets"}
CONFIGURATIONS = (-1, 0, 1)


def _array(values):
    return np.asarray(values, dtype=float)


def _last(trajectory, key):
    return float(_array(trajectory["states"][key])[-1])


def select_runs(suite, p=None):
    """Return runs in reproducible seed/prior order, optionally selecting a prior."""
    runs = suite["runs"]
    if p is not None:
        runs = [run for run in runs if np.isclose(run["p"], p)]
    return sorted(runs, key=lambda run: (run["seed"], -run["p"]))


def baseline_table(suite):
    rows = []
    for run in select_runs(suite):
        trajectory = run["baseline"]
        fractions = _array(trajectory["states"]["configuration_fractions"])[-1]
        row = {"seed": run["seed"], "p": run["p"], "t_best": run["t_best"],
               **run["summary"], **trajectory.get("summary", {}),
               "terminal_minus_fraction": fractions[0], "terminal_zero_fraction": fractions[1],
               "terminal_plus_fraction": fractions[2]}
        for key, value in run.get("data_metadata", {}).items():
            if value is None or np.isscalar(value):
                row[f"data_{key}"] = value
        rows.append(row)
    return pd.DataFrame(rows)


def continuation_table(suite):
    rows = []
    for run in select_runs(suite):
        for checkpoint in run["checkpoints"]:
            for branch, trajectory in checkpoint["continuations"].items():
                error = _array(trajectory["states"]["error"])
                rows.append({"seed": run["seed"], "p": run["p"], "t0": checkpoint["t0"],
                             "branch": branch, "checkpoint_error": error[0],
                             "terminal_error": error[-1], "error_change_from_checkpoint": error[-1] - error[0],
                             "terminal_b": _last(trajectory, "b"),
                             "terminal_normalized_bias": _last(trajectory, "normalized_bias"),
                             "terminal_normalized_alignment": _last(trajectory, "normalized_alignment"),
                             "observed_switches": int(np.sum(trajectory["updates"]["switches"])),
                             "replay_max_abs": checkpoint["replay_max_abs"],
                             **trajectory.get("summary", {})})
    return pd.DataFrame(rows)


def minimizer_table(suite):
    rows = []
    for run in select_runs(suite):
        for checkpoint in run["checkpoints"]:
            for branch, result in checkpoint["minimizers"].items():
                consistency = result.get("consistency") or {}
                row = {"seed": run["seed"], "p": run["p"], "t0": checkpoint["t0"],
                       "branch": branch}
                for key in ("objective", "error", "gradient_inf", "gradient_l2", "gradient_coordinates",
                            "converged", "status", "solver_success", "solver_status_code", "message", "nit", "nfev",
                            "solver_settings", "assumptions", "warnings"):
                    row[key] = result.get(key)
                row.update(consistency_status=consistency.get("status", "not an equilibrium claim"),
                           margin_min=consistency.get("margin_min", np.nan))
                for key in ("n_violated_inequalities", "n_violated_observations", "n_near_boundary", "tolerance"):
                    row[key] = consistency.get(key)
                for key, value in result.get("solver_settings", {}).items():
                    row[f"solver_{key}"] = value
                for key, value in consistency.get("violations", {}).items():
                    row[f"violations_{key}"] = value
                rows.append(row)
    return pd.DataFrame(rows)


def margin_table(suite):
    """Long table retains every frozen configuration and raw consistency margin."""
    rows = []
    for run in select_runs(suite):
        for checkpoint in run["checkpoints"]:
            result = checkpoint["minimizers"]["frozen"]
            consistency = result.get("consistency") or {}
            margins = consistency.get("margins", [])
            induced = consistency.get("induced_configuration", [])
            dynamic = checkpoint["continuations"]["dynamic"]["endpoint"].get("configuration", [])
            for j, (target, margin) in enumerate(zip(checkpoint["p0"], margins)):
                rows.append({"seed": run["seed"], "p": run["p"], "t0": checkpoint["t0"],
                             "unlabeled_index": j, "frozen_configuration": int(target),
                             "induced_configuration": int(induced[j]) if len(induced) else None,
                             "dynamic_terminal_configuration": int(dynamic[j]) if len(dynamic) else None,
                             "margin": float(margin), "solver_gradient_inf": result.get("gradient_inf"),
                             "consistency_status": consistency.get("status")})
    return pd.DataFrame(rows)


def transition_table(suite):
    """All nine cells, including direct sign changes, at every baseline update."""
    rows = []
    for run in select_runs(suite):
        updates = run["baseline"]["updates"]
        for t, counts in zip(updates["iteration"], updates["transition_counts"]):
            for a, before in enumerate(CONFIGURATIONS):
                for b, after in enumerate(CONFIGURATIONS):
                    rows.append({"seed": run["seed"], "p": run["p"], "iteration": t,
                                 "from_configuration": before, "to_configuration": after,
                                 "count": int(counts[a][b])})
    return pd.DataFrame(rows)


def crossing_table(suite):
    """Count-weighted means over crossing events (an observation may occur twice)."""
    rows = []
    for run in select_runs(suite):
        for direction, summaries in run["baseline"]["updates"].get("crossings", {}).items():
            counts = _array(summaries["count"])
            total = int(counts.sum())
            row = {"seed": run["seed"], "p": run["p"], "crossing": direction, "count": total}
            for key in ("mean_bias", "mean_feature", "mean_total", "mean_abs_bias", "mean_abs_feature"):
                values = _array(summaries[key])
                active = counts > 0
                row[key] = float(np.sum(values[active] * counts[active]) / total) if total else np.nan
            row["mean_additivity_residual"] = row["mean_total"] - row["mean_bias"] - row["mean_feature"]
            rows.append(row)
    return pd.DataFrame(rows)


def identity_table(suite):
    rows = []
    pi = suite["config"]["pi"]
    for run in select_runs(suite):
        updates = run["baseline"]["updates"]
        residual = _array(updates["delta_b"]) - _array(updates["zeta_L"]) - pi * _array(updates["zeta_U"])
        oracle_residual = _array(updates["oracle_identity_residual"])
        valid = np.isfinite(oracle_residual)
        rows.append({"seed": run["seed"], "p": run["p"],
                     "max_bias_decomposition_residual": float(np.nanmax(np.abs(residual))) if len(residual) else np.nan,
                     "max_one_step_oracle_identity_residual": float(np.max(np.abs(oracle_residual[valid]))) if valid.any() else np.nan,
                     "oracle_identity_updates_checked": int(valid.sum())})
    return pd.DataFrame(rows)


def paired_table(suite, reference_p=0.5):
    """Seed-joined differences at a common absolute terminal iteration."""
    table = baseline_table(suite)
    metrics = ("terminal_error", "best_error", "deterioration")
    reference = table[np.isclose(table["p"], reference_p)].set_index("seed")
    rows = []
    for _, row in table[~np.isclose(table["p"], reference_p)].iterrows():
        if row["seed"] not in reference.index:
            continue
        paired = reference.loc[row["seed"]]
        result = {"seed": int(row["seed"]), "p": row["p"], "reference_p": reference_p}
        for metric in metrics:
            result[f"{metric}_minus_reference"] = row[metric] - paired[metric]
        rows.append(result)
    return pd.DataFrame(rows)


def aggregate_table(suite):
    """Descriptive seed summaries; no population-level uncertainty claim."""
    table = baseline_table(suite)
    return table.groupby("p", sort=False).agg(
        seeds=("seed", "count"), terminal_error_mean=("terminal_error", "mean"),
        terminal_error_min=("terminal_error", "min"), terminal_error_max=("terminal_error", "max"),
        deterioration_mean=("deterioration", "mean"), deteriorated_runs=("deteriorated", "sum"),
        terminal_zero_fraction_mean=("terminal_zero_fraction", "mean"),
    ).reset_index()


def export_tables(suite):
    directory = Path(suite["output_dir"]) / "tables"
    directory.mkdir(parents=True, exist_ok=True)
    makers = {"baselines": baseline_table, "continuations": continuation_table,
              "minimizers": minimizer_table, "raw_consistency_margins": margin_table,
              "baseline_transitions": transition_table, "threshold_crossings": crossing_table,
              "one_step_identities": identity_table, "paired_differences": paired_table,
              "imbalance_aggregates": aggregate_table}
    tables = {name: maker(suite) for name, maker in makers.items()}
    for name, table in tables.items():
        table.to_csv(directory / f"{name}.csv", index=False)
    return tables


def save_figure(suite, figure, name):
    directory = Path(suite["output_dir"]) / "figures"
    directory.mkdir(parents=True, exist_ok=True)
    figure.savefig(directory / f"{name}.png", dpi=160, bbox_inches="tight")
    figure.savefig(directory / f"{name}.pdf", bbox_inches="tight")
    return directory / f"{name}.pdf"


def _style(axes):
    for ax in np.asarray(axes).ravel():
        ax.grid(alpha=0.22)
        if ax.get_legend_handles_labels()[0]:
            ax.legend(fontsize=8)


def _line(ax, times, values, **kwargs):
    """A checkpoint at T has one state and must remain visible as a point."""
    if len(times) == 1:
        kwargs.setdefault("marker", "o")
    return ax.plot(times, values, **kwargs)


def plot_checkpoint_errors(runs):
    entries = [(run, cp) for run in runs for cp in run["checkpoints"]]
    fig, axes = plt.subplots(len(entries), 2, figsize=(11, 3.1 * len(entries)), squeeze=False,
                             constrained_layout=True)
    for (run, cp), row in zip(entries, axes):
        for branch in BRANCHES:
            states = cp["continuations"][branch]["states"]
            times, errors = _array(states["iteration"]), _array(states["error"])
            for ax, offset in zip(row, (0, cp["t0"])):
                _line(ax, times - offset, errors, color=COLORS[branch], label=LABELS[branch])
        row[0].set(title=f"Seed {run['seed']}, p={run['p']:g}, checkpoint {cp['t0']}",
                   xlabel="absolute iteration t", ylabel="population classification error", ylim=(0, 0.5))
        row[1].set(title="Same trajectories: checkpoint-relative view", xlabel=r"steps since checkpoint $t-t_0$",
                   ylabel="population classification error", ylim=(0, 0.5))
        if len(times) == 1:
            for ax in row:
                ax.text(0.04, 0.65, "Checkpoint equals T: no remaining updates.\nAll three initial states coincide.", transform=ax.transAxes)
    _style(axes)
    return fig


def plot_checkpoint_diagnostics(run, checkpoint):
    fig, axes = plt.subplots(4, 2, figsize=(12, 12), constrained_layout=True)
    for branch in BRANCHES:
        trajectory = checkpoint["continuations"][branch]
        states, updates = trajectory["states"], trajectory["updates"]
        t = _array(states["iteration"])
        color, label = COLORS[branch], LABELS[branch]
        for ax, key in zip(axes.ravel()[:3], ("b", "normalized_bias", "normalized_alignment")):
            _line(ax, t, states[key], color=color, label=label)
        fractions = _array(states["configuration_fractions"])
        for j, style in enumerate(("-", ":", "--")):
            _line(axes[1, 1], t, fractions[:, j], linestyle=style, color=color,
                  label=label if j == 0 else None)
        _line(axes[2, 0], t, _array(states["prediction_fractions"])[:, 1], color=color, label=label)
        axes[2, 1].plot(updates["iteration"], updates["switches"], color=color, label=label)
        _line(axes[3, 0], t, states["selected_false_negative_fraction"], color=color, label=label)
        _line(axes[3, 1], t, states["selected_false_positive_fraction"], color=color, label=label)
    titles = (r"Intercept $b$", r"Normalized bias $b/\tau$", r"Alignment $m/\tau$",
              "Score-induced configuration fractions", "Positive predictions (selection ignored)",
              "Score-induced configuration switches", "Induced false negatives / M", "Induced false positives / M")
    for ax, title in zip(axes.ravel(), titles):
        ax.set(title=title, xlabel="absolute iteration t")
    for i in (3, 4, 6, 7):
        axes.ravel()[i].set_ylim(0, 0.5)
    axes[2, 1].set_xlabel(r"update $t\to t+1$")
    axes[1, 1].set_title("Induced configurations: solid −1, dotted 0, dashed +1")
    if len(t) == 1:
        axes[2, 1].text(0.15, 0.5, "Checkpoint equals T: no updates.", transform=axes[2, 1].transAxes)
    fig.suptitle(f"Seed {run['seed']}, p={run['p']:g}, common checkpoint t₀={checkpoint['t0']}")
    _style(axes)
    return fig


def plot_update_decomposition(runs, pi):
    fig, axes = plt.subplots(len(runs), 2, figsize=(12, 3.5 * len(runs)), squeeze=False,
                             constrained_layout=True)
    for run, row in zip(runs, axes):
        updates = run["baseline"]["updates"]
        t = _array(updates["iteration"])
        row[0].plot(t, updates["zeta_L"], label=r"$\zeta_L$")
        row[0].plot(t, pi * _array(updates["zeta_U"]), label=r"$\pi\zeta_U$")
        row[0].plot(t, updates["delta_b"], color="black", linestyle="--", label=r"actual $\Delta b$")
        row[0].axhline(0, color="grey", linewidth=0.7)
        row[0].set(title=f"Seed {run['seed']}: actual intercept increments", xlabel=r"update $t\to t+1$")
        row[1].plot(t, updates["beta"], label=r"$\beta_t$ (no factor $\pi$)")
        row[1].axhline(0, color="grey", linewidth=0.7)
        row[1].set(title="Signed selected pseudo-label error", xlabel=r"update $t\to t+1$")
    _style(axes)
    return fig


def plot_imbalance_baselines(suite):
    ps = sorted({run["p"] for run in suite["runs"]}, reverse=True)
    fig, axes = plt.subplots(3, len(ps), figsize=(5 * len(ps), 10), squeeze=False,
                             constrained_layout=True)
    for col, p in enumerate(ps):
        runs = select_runs(suite, p)
        for row, metric in enumerate(("error", "normalized_bias", "normalized_alignment")):
            values = []
            for run in runs:
                states = run["baseline"]["states"]
                axes[row, col].plot(states["iteration"], states[metric], alpha=0.6, label=f"seed {run['seed']}")
                values.append(_array(states[metric]))
            if len(values) > 1:
                matrix = np.stack(values)
                valid = np.isfinite(matrix)
                mean = np.divide(np.nansum(matrix, axis=0), valid.sum(axis=0),
                                 out=np.full(matrix.shape[1], np.nan), where=valid.sum(axis=0) > 0)
                axes[row, col].plot(states["iteration"], mean, color="black", linewidth=2, label="seed mean")
            axes[row, col].set(title=f"p={p:g}: {metric.replace('_', ' ')}", xlabel="absolute iteration t")
        axes[0, col].set_ylim(0, 0.5)
    _style(axes)
    return fig


def plot_imbalance_continuations(suite):
    """Each trajectory is aligned to its own t_best; no across-run state matching."""
    ps = sorted({run["p"] for run in suite["runs"]}, reverse=True)
    fig, axes = plt.subplots(3, len(ps), figsize=(5 * len(ps), 10), squeeze=False,
                             constrained_layout=True)
    for col, p in enumerate(ps):
        for run in select_runs(suite, p):
            checkpoint = next(cp for cp in run["checkpoints"] if cp["t0"] == run["t_best"])
            for row, branch in enumerate(BRANCHES):
                states = checkpoint["continuations"][branch]["states"]
                _line(axes[row, col], _array(states["iteration"]) - checkpoint["t0"], states["error"],
                      label=f"seed {run['seed']}, t₀={checkpoint['t0']}")
                axes[row, col].set(title=f"p={p:g}: {LABELS[branch]}", xlabel="steps since this run's t_best",
                                   ylabel="population error", ylim=(0, 0.5))
    _style(axes)
    return fig


def plot_branch_outcomes(suite):
    baselines = baseline_table(suite)
    minimizers = minimizer_table(suite)
    frozen = minimizers[minimizers["branch"] == "frozen"]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)
    positions = np.arange(len(baselines))
    bottom = np.zeros(len(baselines))
    for column, label, color in (("terminal_minus_fraction", "−1 selected", "#506bad"),
                                  ("terminal_zero_fraction", "0 excluded", "#c9c9c9"),
                                  ("terminal_plus_fraction", "+1 selected", "#db9959")):
        values = baselines[column].to_numpy()
        axes[0].bar(positions, values, bottom=bottom, label=label, color=color)
        bottom += values
    axes[0].set_xticks(positions, [f"{int(row.seed)}\np={row.p:g}" for row in baselines.itertuples()], rotation=45)
    axes[0].set(title="Dynamic terminal configurations", ylabel="fraction of unlabeled pool", ylim=(0, 0.5))
    for index, row in enumerate(frozen.itertuples()):
        if np.isfinite(row.margin_min):
            axes[1].scatter(index, row.margin_min, marker="o" if row.converged else "x", color="#6b3f91")
    axes[1].axhline(0, color="black", linewidth=1)
    axes[1].set_xticks(np.arange(len(frozen)),
                       [f"{int(row.seed)}, p={row.p:g}\nt₀={row.t0}" for row in frozen.itertuples()], rotation=60)
    axes[1].set(title="Frozen minimizer: raw minimum consistency margin\n○ converged; × insufficient convergence (see status table)",
                ylabel=r"$\min_j\gamma_j$")
    _style(axes)
    return fig


def checkpoint_interpretation(suite, p=None):
    """Facts computed from actual trajectories, with signed contrasts defined."""
    lines = []
    if suite["config"].get("profile") == "smoke":
        lines.append("**Smoke validation only:** these reduced runs validate execution and numerical bookkeeping; they do not test the substantive collapse hypothesis.")
    for run in select_runs(suite, p):
        summary = run["summary"]
        lines.append(f"- Seed {run['seed']}, p={run['p']:g}: earliest best post-initial error {summary['best_error']:.6f} at t={run['t_best']}; terminal error {summary['terminal_error']:.6f}. Terminal minus best = {summary['deterioration']:+.6f}; deterioration flag = {summary['deteriorated']}.")
        for cp in run["checkpoints"]:
            trajectories = cp["continuations"]
            initial = float(trajectories["dynamic"]["states"]["error"][0])
            dynamic, frozen, oracle = [_last(trajectories[name], "error") for name in BRANCHES]
            fit = cp["minimizers"]["frozen"]
            consistency = fit.get("consistency") or {}
            lines.append(f"  At t₀={cp['t0']}: frozen fitting changes error by {frozen-initial:+.6f}; dynamic minus frozen terminal error is {dynamic-frozen:+.6f}; frozen minus oracle terminal error is {frozen-oracle:+.6f}. Correct selected labels leave terminal error {oracle:.6f}. Frozen minimizer status: {consistency.get('status', 'unavailable')}, raw minimum margin {consistency.get('margin_min', np.nan):.4g}, gradient infinity norm {fit.get('gradient_inf', np.nan):.3g}. Replay maximum discrepancy: {cp['replay_max_abs']:.3g}.")
    lines.append("Positive frozen-fitting changes indicate deterioration while holding both selection and assigned labels fixed. Positive dynamic-minus-frozen differences indicate additional terminal deterioration associated with allowing configuration changes. Positive frozen-minus-oracle differences indicate improvement after correcting targets on the identical initially selected set. Negative values are retained and oppose the corresponding directional hypothesis. These are conditional counterfactual comparisons, not an additive causal decomposition across trajectories.")
    return "\n\n".join(lines)


def imbalance_interpretation(suite):
    lines = []
    if suite["config"].get("profile") == "smoke":
        lines.append("**Smoke validation only.** No scientific conclusion about imbalance or collapse is warranted from the reduced dimensions/horizon.")
    baselines = baseline_table(suite)
    for row in aggregate_table(suite).itertuples():
        lines.append(f"- p={row.p:g}: {row.seeds} seeds; mean terminal error {row.terminal_error_mean:.6f} (observed range {row.terminal_error_min:.6f}–{row.terminal_error_max:.6f}); {int(row.deteriorated_runs)}/{row.seeds} runs deteriorate by the configured tolerance; mean terminal-minus-best error {row.deterioration_mean:+.6f}.")
    for row in paired_table(suite).itertuples():
        lines.append(f"- Paired seed {row.seed}, p={row.p:g} minus p={row.reference_p:g}: terminal-error difference {row.terminal_error_minus_reference:+.6f}; deterioration difference {row.deterioration_minus_reference:+.6f}.")
    types = baselines.groupby(["p", "terminal_configuration_type"]).size()
    lines.append("Observed dynamic terminal configuration types: " + "; ".join(f"p={p:g}, {kind}: {count}" for (p, kind), count in types.items()) + ".")
    minimizers = minimizer_table(suite)
    statuses = minimizers[minimizers["branch"] == "frozen"].groupby("consistency_status").size()
    lines.append("Frozen pseudo-label minimizer classifications: " + "; ".join(f"{status}: {count}" for status, count in statuses.items()) + ".")
    lines.append("Formation is described by the dynamic configuration transitions. Fitting is probed by fixed-target continuations and independent unconstrained minimization. Attraction is only probed by the observed finite continuations: numerical self-consistency and a switch-free interval do not prove convergence, local stability, or permanent identification. A balanced prior is not an exclusion criterion for collapse. Seed ranges and means are descriptive; this small paired sample does not establish a theorem or reliable population uncertainty interval.")
    return "\n\n".join(lines)
