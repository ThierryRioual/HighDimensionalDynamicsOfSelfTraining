"""Data and experiment routines for ISOLET."""

import csv
import io
from pathlib import Path
import re
from string import ascii_uppercase
import subprocess
from tempfile import NamedTemporaryFile
from urllib.request import urlopen
from zipfile import ZipFile

from IPython.display import Markdown, display
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import torch

from experiments.plotting import save_figure

from src.algorithms import SelfTrainedGradientDescent
from src.config import AlgorithmConfig
from src.initialization import SelfTrainingInitialization
from src.primitives import compute_scores, selection_rate, sign_with_positive_tie


def read_isolet_member(archive, filename):
    try:
        raw = subprocess.run(
            ["gzip", "-dc"], input=archive.read(filename), capture_output=True, check=True,
        ).stdout
    except FileNotFoundError as exc:
        raise RuntimeError("ISOLET's .Z files require a system gzip command.") from exc
    values = np.loadtxt(io.BytesIO(raw), delimiter=",")
    if values.shape[1] != 618 or not np.isfinite(values).all():
        raise ValueError(f"Expected 617 finite features and a class code in {filename}.")
    labels = values[:, -1].astype(np.int64)
    if not np.array_equal(values[:, -1], labels) or not np.isin(labels, np.arange(1, 27)).all():
        raise ValueError(f"Invalid ISOLET label codes in {filename}.")
    return values[:, :-1], labels


def load_isolet(archive_path):
    archive_url = "https://archive.ics.uci.edu/static/public/54/isolet.zip"
    if not archive_path.exists():
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        with urlopen(archive_url, timeout=90) as response:
            archive_bytes = response.read()
        # Check the ZIP before moving it to the cache path.
        with ZipFile(io.BytesIO(archive_bytes)) as archive:
            if archive.testzip() is not None:
                raise ValueError("The downloaded ISOLET archive failed its integrity check.")
        with NamedTemporaryFile(dir=archive_path.parent, delete=False) as temp:
            temp.write(archive_bytes)
        Path(temp.name).replace(archive_path)

    with ZipFile(archive_path) as archive:
        info = archive.read("isolet.info").decode("ascii")
        table = re.findall(r"^\s*(\d+)\s+([A-Z])\s+(\d+)\s+(\d+)\s*$", info, re.M)
        letter_codes = {letter: int(label) for label, letter, _, _ in table}
        if letter_codes != dict(zip(ascii_uppercase, range(1, 27))):
            raise ValueError("Unexpected class mapping in the official ISOLET documentation.")
        X_train, y_train = read_isolet_member(archive, "isolet1+2+3+4.data.Z")
        X_test, y_test = read_isolet_member(archive, "isolet5.data.Z")

    for column, labels in [(2, y_train), (3, y_test)]:
        expected = [int(row[column]) for row in table]
        if not np.array_equal(np.bincount(labels, minlength=27)[1:], expected):
            raise ValueError("ISOLET label counts differ from those in isolet.info.")
    return X_train, y_train, X_test, y_test, letter_codes


def round_count(n, p):
    return int(np.floor(n * p + 0.5))


def isolet_diagnostics(learner, data, p):
    y_test_binary = data["y_test"]
    neg = y_test_binary == -1
    pos = y_test_binary == 1
    unlabeled = data["observed"] == 0
    d = data["X_train"].shape[1]
    biases = [step.bias for step in learner.update_records_] + [learner.bias]
    rows = []
    for t, (bias, weight) in enumerate(zip(biases, learner.weight_history_)):
        test_scores = compute_scores(data["X_test"], bias, weight)
        mistakes = sign_with_positive_tie(test_scores) != y_test_binary
        negative_error = mistakes[neg].double().mean().item()
        positive_error = mistakes[pos].double().mean().item()
        scores = (learner.update_records_[t].scores if t < len(learner.update_records_)
                  else learner.decision_function(data["X_train"]))[unlabeled]
        selected = learner.selection_mask(scores)
        coverage = selection_rate(selected).item()
        predictions = sign_with_positive_tie(scores)
        wrong = selected.bool() & (predictions != data["hidden"])
        selected_error = wrong.double().mean().item()
        rows.append({
            "iteration": t,
            "test_error": (1 - p) * negative_error + p * positive_error,
            "negative_error": negative_error,
            "positive_error": positive_error,
            "coverage": coverage,
            "selected_error_fraction": selected_error,
            "pseudo_accuracy": 1 - selected_error / coverage if coverage else np.nan,
            "intercept": bias.item(),
            "test_score_gap": ((test_scores[pos].mean() - test_scores[neg].mean()) / 2).item(),
            "weight_norm": (torch.linalg.vector_norm(weight) / d**0.5).item(),
            "predicted_positive_fraction": (predictions == 1).double().mean().item(),
        })
    return rows



class ISOLETExperiment:
    """Compare supervised and self-training trajectories on ISOLET."""

    def __init__(
        self, root, *,
        negative_letter, positive_letter, class_proportions, labeling_rate,
        n_train, n_test, seeds, training_steps,
        eta, reg_lambda, pi, tau,
    ):
        self.root = root
        self.figures_dir = root / "outputs" / "figures"
        self.negative_letter = negative_letter
        self.positive_letter = positive_letter
        self.class_proportions = class_proportions
        self.labeling_rate = labeling_rate
        self.n_train = n_train
        self.n_test = n_test
        self.seeds = seeds
        self.training_steps = training_steps
        self.eta = eta
        self.reg_lambda = reg_lambda
        self.pi = pi
        self.tau = tau

        if (negative_letter not in tuple(ascii_uppercase) or positive_letter not in tuple(ascii_uppercase)
                or negative_letter == positive_letter):
            raise ValueError("Choose two distinct uppercase letters A through Z.")
        if len(class_proportions) != 2 or not all(0 < p < 1 for p in class_proportions):
            raise ValueError("Supply two positive-class proportions strictly between 0 and 1.")
        if not 0 < labeling_rate < 1 or not 0.5 < tau < 1:
            raise ValueError("Require 0 < labeling_rate < 1 and 0.5 < tau < 1.")
        if not seeds or any(not isinstance(seed, int) or seed < 0 for seed in seeds):
            raise ValueError("Supply at least one nonnegative integer seed.")
        if not isinstance(training_steps, int) or training_steps < 0:
            raise ValueError("training_steps must be a nonnegative integer.")
        if not isinstance(n_train, int) or n_train < 2:
            raise ValueError("n_train must be an integer of at least 2.")
        if n_test is not None and (not isinstance(n_test, int) or n_test < 2):
            raise ValueError("n_test must be None or an integer of at least 2.")
        if not np.isfinite([eta, reg_lambda, pi]).all() or eta <= 0 or min(reg_lambda, pi) < 0:
            raise ValueError("Require finite eta > 0, reg_lambda >= 0, and pi >= 0.")

    def isolet_split(self, p, seed, sizes):
        train_size, test_size = sizes
        n_pos = round_count(train_size, p)
        train_counts = (train_size - n_pos, n_pos)
        n_labeled = round_count(train_size, self.labeling_rate)
        labeled_pos = (2 * n_labeled * n_pos + train_size) // (2 * train_size)
        if min(labeled_pos, n_labeled - labeled_pos) < 1 or n_labeled >= train_size:
            raise ValueError(f"p={p:g}, n_train={train_size}: rounding gives "
                             f"{n_labeled - labeled_pos} negative and {labeled_pos} positive labels "
                             f"and {train_size - n_labeled} unlabeled rows. Need both revealed classes "
                             "and some unlabeled rows.")

        rng = np.random.default_rng(seed)
        train_parts = []
        for letter, label, count in zip((self.negative_letter, self.positive_letter), self.codes, train_counts):
            pool = np.flatnonzero(self.y_train == label)
            if count > len(pool):
                raise ValueError(f"p={p:g}, {letter}: requested {count} training rows, "
                                 f"but ISOLET 1–4 has only {len(pool)}.")
            train_parts.append(rng.choice(pool, count, replace=False))
        train_ids = rng.permutation(np.concatenate(train_parts))
        train_labels = np.where(self.y_train[train_ids] == self.codes[1], 1, -1)
        observed = np.zeros(train_size, dtype=np.int64)
        for label, count in [(-1, n_labeled - labeled_pos), (1, labeled_pos)]:
            ids = rng.choice(np.flatnonzero(train_labels == label), count, replace=False)
            observed[ids] = label

        heldout_ids = self.test_ids
        if test_size is not None:
            if test_size > len(self.test_ids):
                raise ValueError(f"Requested {test_size} test rows; only {len(self.test_ids)} official "
                                 f"rows are available for {self.negative_letter} and {self.positive_letter}.")
            negative_test = self.test_ids[self.y_test[self.test_ids] == self.codes[0]]
            positive_test = self.test_ids[self.y_test[self.test_ids] == self.codes[1]]
            test_pos = round_count(test_size, len(positive_test) / len(self.test_ids))
            if not 0 < test_pos < test_size:
                raise ValueError("n_test must leave at least one row for each letter.")
            test_rng = np.random.default_rng([seed, 1])
            heldout_ids = np.concatenate([
                test_rng.choice(negative_test, test_size - test_pos, replace=False),
                test_rng.choice(positive_test, test_pos, replace=False),
            ])

        X_pool = self.X_train[train_ids]
        center = X_pool.mean(axis=0)
        return {
            "X_train": torch.from_numpy(X_pool - center),
            "observed": torch.from_numpy(observed),
            "hidden": torch.from_numpy(train_labels[observed == 0]),
            "X_test": torch.from_numpy(self.X_test[heldout_ids] - center),
            "y_test": torch.from_numpy(np.where(self.y_test[heldout_ids] == self.codes[1], 1, -1)),
            "ids": (train_ids, heldout_ids + len(self.y_train)),
        }

    def fit_isolet(self, design, observed, initialization, steps, pseudo_weight):
        cfg = AlgorithmConfig(
            n_iterations=steps, step_size=self.eta, penalty_param=self.reg_lambda,
            pseudo_label_param=pseudo_weight, margin_threshold=float(np.log(self.tau / (1 - self.tau))),
        )
        return SelfTrainedGradientDescent(cfg).fit(design, observed, initialization)

    def run_isolet_repetition(self, p, seed, sizes, steps):
        data = self.isolet_split(p, seed, sizes)
        design, observed = data["X_train"], data["observed"]
        labeled = observed != 0

        generator = torch.Generator().manual_seed(seed + 11)
        w_init = torch.randn(design.shape[1], generator=generator, dtype=design.dtype)
        initialization = SelfTrainingInitialization(0.0, w_init)
        supervised = self.fit_isolet(design, observed, initialization, steps, 0.0)
        self_trained = self.fit_isolet(design, observed, initialization, steps, self.pi)
        trajectories = {
            "supervised_only": isolet_diagnostics(supervised, data, p),
            "self_training": isolet_diagnostics(self_trained, data, p),
        }
        n_labeled_pos = int((observed == 1).sum())
        n_unlabeled_pos = int((data["hidden"] == 1).sum())
        counts = {
            "Train": (len(observed), n_labeled_pos + n_unlabeled_pos),
            "Labeled": (int(labeled.sum()), n_labeled_pos),
            "Unlabeled": (len(data["hidden"]), n_unlabeled_pos),
            "Test": (len(data["y_test"]), int((data["y_test"] == 1).sum())),
        }

        return {"p": p, "seed": seed, "counts": counts, "trajectories": trajectories}

    def plot_isolet_trajectories(self, runs):
        pi = self.pi
        fig, axes = plt.subplots(2, 3, figsize=(11, 6.3), sharex=True, layout="constrained")
        methods = [
            ("supervised_only", r"Supervised only ($\pi=0$)", "tab:blue"),
            ("self_training", rf"Self-training ($\pi={pi:g}$)", "tab:orange"),
        ]
        panels = [
            ("test_error", "Test classification error"),
            ("coverage", "Selected fraction"),
            ("selected_error_fraction", "Incorrect and selected fraction"),
            ("intercept", "Intercept"),
            ("test_score_gap", "Half the test class mean score gap"),
            ("weight_norm", r"Weight norm $\|w\|/\sqrt{d}$"),
        ]
        for index, (ax, (key, title)) in enumerate(zip(axes.flat, panels)):
            for method, label, color in methods:
                values = np.array([[row[key] for row in run["trajectories"][method]] for run in runs])
                t = np.arange(values.shape[1])
                mean, sd = values.mean(axis=0), values.std(axis=0)
                ax.plot(t, mean, label=label, color=color)
                ax.fill_between(t, mean - sd, mean + sd, color=color, alpha=0.16, linewidth=0)
            ax.set_title(title)
            if index < 3:
                ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
            else:
                ax.set_xlabel("Iteration")
            ax.grid(alpha=0.2, linewidth=0.6)
        handles, labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="outside lower center", ncol=2, frameon=False)
        fig.suptitle(f"ISOLET letters {self.negative_letter} and {self.positive_letter} | Target positive proportion = {runs[0]['p']:g}")
        return fig

    def load_data(self):
        archive_path = self.root / "data" / "isolet" / "isolet.zip"
        X_train, y_train, X_test, y_test, letter_codes = load_isolet(archive_path)
        codes = tuple(letter_codes[letter] for letter in (self.negative_letter, self.positive_letter))
        test_ids = np.flatnonzero(np.isin(y_test, codes))
        print(f"Official train/test: {len(y_train):,} / {len(y_test):,} rows, {X_train.shape[1]} features")
        print(f"{self.negative_letter} (code {codes[0]}) → −1; {self.positive_letter} (code {codes[1]}) → +1")
        print(f"Cache: {archive_path}")
        self.X_train = X_train
        self.y_train = y_train
        self.X_test = X_test
        self.y_test = y_test
        self.codes = codes
        self.test_ids = test_ids


    def run_comparison(self):
        full_sizes = (self.n_train, self.n_test)
        runs_by_scenario = []
        count_table = [
            "| Requested p | Seed | Train | Labeled | Unlabeled  | Test |",
            "|---:|---:|---:|---:|---:|---:|",
        ]
        for p in self.class_proportions:
            runs = []
            for seed in self.seeds:
                run = self.run_isolet_repetition(
                    p, seed, full_sizes, self.training_steps,
                )
                runs.append(run)
                cells = [f"{pos:,} / {n:,} ({pos / n:.1%})" for n, pos in run["counts"].values()]
                count_table.append(f"| {p:g} | {seed} | " + " | ".join(cells) + " |")
            runs_by_scenario.append(runs)
        display(Markdown("\n".join(count_table)))
        return runs_by_scenario

    def show_trajectories(self, runs_by_scenario):
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        for runs in runs_by_scenario:
            fig = self.plot_isolet_trajectories(runs)
            figure_path = self.figures_dir / f"isolet_from_scratch_p{runs[0]['p']:g}.pdf"
            save_figure(fig, figure_path)
            plt.show()

    def save_measurements(self, runs_by_scenario, *, save_csv=False):
        summary = [
            "| Requested p | Pseudo-label weight | Initial weighted test error | Final weighted test error | "
            "Final selected fraction |",
            "|---:|---:|---:|---:|---:|",
        ]
        measurements = []
        for runs in runs_by_scenario:
            for method, pseudo_weight in (("supervised_only", 0.0), ("self_training", self.pi)):
                trajectories = [run["trajectories"][method] for run in runs]
                initial_error = np.mean([rows[0]["test_error"] for rows in trajectories])
                final_error = np.mean([rows[-1]["test_error"] for rows in trajectories])
                final_coverage = np.mean([rows[-1]["coverage"] for rows in trajectories])
                summary.append(
                    f"| {runs[0]['p']:g} | {pseudo_weight:g} | {initial_error:.2%} | "
                    f"{final_error:.2%} | {final_coverage:.2%} |"
                )
                for run, rows in zip(runs, trajectories):
                    settings = {
                        "negative_letter": self.negative_letter, "positive_letter": self.positive_letter,
                        "positive_proportion": run["p"], "seed": run["seed"], "method": method,
                        "labeling_rate": self.labeling_rate, "eta": self.eta, "reg_lambda": self.reg_lambda,
                        "pi": pseudo_weight, "tau": self.tau,
                    }
                    for split, (size, positives) in run["counts"].items():
                        settings[f"n_{split.lower()}"] = size
                        settings[f"n_positive_{split.lower()}"] = positives
                    measurements.extend({**settings, **row} for row in rows)
        display(Markdown("\n".join(summary)))

        if save_csv:
            measurements_path = self.root / "outputs" / "isolet_self_training" / "from_scratch_trajectories.csv"
            measurements_path.parent.mkdir(parents=True, exist_ok=True)
            with measurements_path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=list(measurements[0]))
                writer.writeheader()
                writer.writerows(measurements)
            print(f"Per-iteration measurements saved to {measurements_path}")

