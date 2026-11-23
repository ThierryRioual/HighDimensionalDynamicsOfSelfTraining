"""Data and experiment routines for MNIST."""

import csv

from IPython.display import Markdown, display
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, PercentFormatter
import numpy as np
import torch

from experiments.plotting import save_figure

from src.algorithms import SelfTrainedGradientDescent
from src.asymptotics import MacroscopicStateEvolution
from src.config import AlgorithmConfig, DataConfig
from src.dgp import IsotropicGaussian
from src.environment import QuenchedEnvironment
from src.initialization import SelfTrainingInitialization
from src.performance import population_error
from src.primitives import compute_scores, selection_rate, sign_with_positive_tie


def load_mnist(data_dir):
    from sklearn.datasets import fetch_openml

    X, y = fetch_openml(
        "mnist_784", version=1, return_X_y=True, as_frame=False,
        data_home=str(data_dir),
    )
    X = np.asarray(X, dtype=np.float32) / 255.0
    y = np.asarray(y, dtype=np.int64)

    X_train, X_test = X[:60000], X[60000:]
    y_train, y_test = y[:60000], y[60000:]
    return X_train, y_train, X_test, y_test


def describe_mnist(data, data_dir):
    X_train, y_train, X_test, y_test = data
    images_train = X_train.reshape(-1, 28, 28)

    print(f"Cache: {data_dir}")
    print(f"Training: {len(X_train):,} | Test: {len(X_test):,}")
    print(f"Features: shape={X_train.shape}, dtype={X_train.dtype}")
    print(f"Image shape: {images_train.shape[1:]}")


def round_count(n, p):
    return int(np.floor(n * p + 0.5))


def mnist_diagnostics(learner, data):
    y_test_binary = data["y_test"]
    neg = y_test_binary == -1
    pos = y_test_binary == +1
    unlabeled = data["observed"] == 0
    d = data["X_train"].shape[1]
    biases = [step.bias for step in learner.update_records_] + [learner.bias]
    rows = []
    for t, (bias, weight) in enumerate(zip(biases, learner.weight_history_)):
        test_scores = compute_scores(data["X_test"], bias, weight)
        test_mistakes = sign_with_positive_tie(test_scores) != y_test_binary
        scores = (learner.update_records_[t].scores if t < len(learner.update_records_)
                  else learner.decision_function(data["X_train"]))[unlabeled]
        selected = learner.selection_mask(scores)
        coverage = selection_rate(selected).item()
        pseudo = sign_with_positive_tie(scores)
        wrong = selected.bool() & (pseudo != data["hidden"])
        selected_error_fraction = wrong.double().mean().item()
        rows.append({
            "iteration": t,
            "test_error": test_mistakes.double().mean().item(),
            "negative_error": test_mistakes[neg].double().mean().item(),
            "positive_error": test_mistakes[pos].double().mean().item(),
            "coverage": coverage,
            "selected_error_fraction": selected_error_fraction,
            "pseudo_accuracy": 1 - selected_error_fraction / coverage if coverage else np.nan,
            "intercept": bias.item(),
            "test_score_gap": ((test_scores[pos].mean() - test_scores[neg].mean()) / 2).item(),
            "weight_norm": (torch.linalg.vector_norm(weight) / d**0.5).item(),
        })
    return rows




def calibrate_mnist_gaussian(pixels, labels):
    """Fit the centered isotropic model using scaled training pixels only."""
    n, d = pixels.shape
    negative, positive = pixels[labels == -1], pixels[labels == 1]
    if n <= 2 or min(len(negative), len(positive)) == 0:
        raise ValueError("Gaussian calibration requires both classes and more than two training rows.")
    m_minus, m_plus = negative.mean(0), positive.mean(0)
    center = (m_plus + m_minus) / 2
    v = (m_plus - m_minus) / 2
    rss = (negative - m_minus).square().sum() + (positive - m_plus).square().sum()
    sigma = float(torch.sqrt(rss / (d * (n - 2))))
    if not np.isfinite(sigma) or sigma <= 0:
        raise ValueError("The fitted isotropic noise scale must be finite and positive.")
    return center, d**0.5 * v, sigma


def finite_mnist_gaussian(p, seed, data, labels, mu, sigma, cfg, initialization, *, midpoint=0.0):
    observed = data["observed"]
    labeled = observed != 0
    n, d = data["X_train"].shape
    population = DataConfig(
        scale=sigma, label_prior=p, supervision_ratio=float(labeled.double().mean()),
        data_to_dimension_ratio=n / d, signal_law=lambda: 0.0,
    )  # The supplied joint parameter sampler provides the signal.
    environment = QuenchedEnvironment(mu, labels, labeled)
    gaussian = IsotropicGaussian(
        cfg=population, n_train=n, dimensions=d, seed=seed + 23, environment=environment,
    )
    test_labels = data["y_test"]
    test_environment = QuenchedEnvironment(mu, test_labels, torch.zeros_like(test_labels))
    X_gaussian, _ = gaussian.sample_design(environment)
    X_gaussian_test, _ = gaussian.sample_design(test_environment)
    # The from-scratch figures use pool-mean centering, so preserve their fitted offset.
    gaussian_data = {**data, "X_train": X_gaussian + midpoint, "X_test": X_gaussian_test + midpoint}
    learner = SelfTrainedGradientDescent(cfg).fit(gaussian_data["X_train"], observed, initialization)
    return mnist_diagnostics(learner, gaussian_data), population


def regularized_zca(eigenvalues, eigenvectors, ridge):
    inverse_roots = (eigenvalues + ridge).rsqrt()
    whitener = (eigenvectors * inverse_roots) @ eigenvectors.T
    return whitener, eigenvalues / (eigenvalues + ridge)


def fit_mnist_whitener(train, labels, ridge_fraction):
    """Fit regularized ZCA from the pooled within-class training covariance."""
    if not np.isfinite(ridge_fraction) or ridge_fraction <= 0:
        raise ValueError("The whitening ridge fraction must be finite and positive.")
    residuals = torch.cat([
        group - group.mean(dim=0)
        for group in (train[labels == -1], train[labels == 1])
    ])
    covariance = residuals.T @ residuals / (len(train) - 2)
    eigenvalues, eigenvectors = torch.linalg.eigh(covariance)
    eigenvalues = eigenvalues.clamp_min(0)
    ridge = float(ridge_fraction * eigenvalues.mean())
    whitener, spectrum = regularized_zca(eigenvalues, eigenvectors, ridge)
    return whitener, ridge, spectrum


def whiten_mnist_by_class(data, labels, pooled_whitener, ridge):
    """Whiten each class's residuals and preserve its pooled-whitened training mean."""
    train, test = data["X_train"], data["X_test"]
    train_whitened, test_whitened = torch.empty_like(train), torch.empty_like(test)
    pooled_covariances, separate_covariances = [], []
    for y in (-1, 1):
        train_mask, test_mask = labels == y, data["y_test"] == y
        group = train[train_mask]
        if len(group) < 2:
            raise ValueError("Class-specific whitening requires at least two training rows per class.")
        mean = group.mean(dim=0)
        residuals = group - mean
        covariance = residuals.T @ residuals / (len(group) - 1)
        eigenvalues, eigenvectors = torch.linalg.eigh(covariance)
        whitener, spectrum = regularized_zca(eigenvalues.clamp_min(0), eigenvectors, ridge)

        target_mean = mean @ pooled_whitener
        train_whitened[train_mask] = residuals @ whitener + target_mean
        test_whitened[test_mask] = (test[test_mask] - mean) @ whitener + target_mean

        pooled_covariances.append(pooled_whitener @ covariance @ pooled_whitener)
        separate_covariances.append((eigenvectors * spectrum) @ eigenvectors.T)

    def relative_covariance_gap(pair):
        negative, positive = pair
        return float(torch.linalg.matrix_norm(positive - negative)
                     / torch.linalg.matrix_norm((positive + negative) / 2))

    return train_whitened, test_whitened, {
        "ridge": ridge,
        "pooled_covariance_gap": relative_covariance_gap(pooled_covariances),
        "class_specific_covariance_gap": relative_covariance_gap(separate_covariances),
    }

class MNISTExperiment:
    """Run the MNIST baseline, Gaussian comparison, and whitening experiments."""

    def __init__(
        self, root, data, *,
        negative_digit, positive_digit, class_proportions, labeling_rate,
        n_train, n_test, seeds, training_steps,
        eta, reg_lambda, pi, tau,
        sample_particles, particle_seed,
    ):
        self.root = root
        self.figures_dir = root / "outputs" / "figures"
        self.negative_digit = negative_digit
        self.positive_digit = positive_digit
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
        self.sample_particles = sample_particles
        self.particle_seed = particle_seed
        self.X_train, self.y_train, self.X_test, self.y_test = data

        if (any(not isinstance(digit, int) or isinstance(digit, bool) or digit not in range(10)
                for digit in (negative_digit, positive_digit)) or negative_digit == positive_digit):
            raise ValueError("Choose two distinct integer digits from 0 to 9.")
        if len(class_proportions) != 2 or not all(0 < p < 1 for p in class_proportions):
            raise ValueError("Provide two positive-class proportions strictly between 0 and 1.")
        if not 0 < labeling_rate < 1:
            raise ValueError("labeling_rate must be strictly between 0 and 1.")
        if not 0.5 < tau < 1:
            raise ValueError("tau must be strictly between 0.5 and 1.")
        if not seeds or any(not isinstance(seed, int) or seed < 0 for seed in seeds):
            raise ValueError("Provide at least one nonnegative integer seed.")
        if not isinstance(training_steps, int) or training_steps < 0:
            raise ValueError("training_steps must be a nonnegative integer.")
        if not np.isfinite([eta, reg_lambda, pi]).all() or eta <= 0 or min(reg_lambda, pi) < 0:
            raise ValueError("eta must be finite and positive; reg_lambda and pi must be finite and nonnegative.")

    def mnist_split(self, p, seed, sizes):
        train_size, test_size = sizes
        names = ("Training", "Test")
        for name, size in zip(names, sizes):
            if not isinstance(size, int) or size < 2:
                raise ValueError(f"{name} size must be an integer of at least 2.")
        n_pos = [round_count(size, p) for size in sizes]
        n_neg = [size - pos for size, pos in zip(sizes, n_pos)]
        for name, neg, pos in zip(names, n_neg, n_pos):
            if min(neg, pos) == 0:
                raise ValueError(f"{name} needs both classes after rounding at p={p:g}.")
        n_labeled = round_count(train_size, self.labeling_rate)
        if not 0 < n_labeled < train_size:
            raise ValueError(f"labeling_rate gives {n_labeled} labels for {train_size} training rows; "
                             "need at least one labeled and one unlabeled row.")

        rng = np.random.default_rng(seed)
        train_parts, test_parts = [], []
        for digit, counts in zip((self.negative_digit, self.positive_digit), (n_neg, n_pos)):
            train_pool = np.flatnonzero(self.y_train == digit)
            test_pool = np.flatnonzero(self.y_test == digit)
            train_count, test_count = counts
            if train_count > len(train_pool) or test_count > len(test_pool):
                raise ValueError(
                    f"At p={p:g}, digit {digit} needs {train_count} official training and "
                    f"{test_count} official test rows; only {len(train_pool)} and "
                    f"{len(test_pool)} are available."
                )
            train_parts.append(rng.choice(train_pool, size=train_count, replace=False))
            test_parts.append(rng.choice(test_pool, size=test_count, replace=False))

        train_ids = rng.permutation(np.concatenate(train_parts))
        test_ids = rng.permutation(np.concatenate(test_parts))
        train_labels = np.where(self.y_train[train_ids] == self.positive_digit, 1, -1)
        # Use the exact integer ratio for half-up rounding of the labeled positives.
        labeled_pos = (2 * n_labeled * n_pos[0] + train_size) // (2 * train_size)
        labeled = np.concatenate([
            rng.choice(np.flatnonzero(train_labels == -1), n_labeled - labeled_pos, replace=False),
            rng.choice(np.flatnonzero(train_labels == +1), labeled_pos, replace=False),
        ])
        observed = np.zeros(train_size, dtype=np.int64)
        observed[labeled] = train_labels[labeled]
        unlabeled = observed == 0

        train_pixels = self.X_train[train_ids].astype(np.float64)
        center = train_pixels.mean(axis=0)
        return {
            "X_train": torch.from_numpy(train_pixels - center),
            "observed": torch.from_numpy(observed),
            "hidden": torch.from_numpy(train_labels[unlabeled]),
            "X_test": torch.from_numpy(self.X_test[test_ids].astype(np.float64) - center),
            "y_test": torch.from_numpy(np.where(self.y_test[test_ids] == self.positive_digit, 1, -1)),
            "ids": (train_ids, test_ids + len(self.y_train)),
        }

    def fit_mnist(self, design, observed, initialization, steps, pseudo_weight):
        cfg = AlgorithmConfig(
            n_iterations=steps, step_size=self.eta, penalty_param=self.reg_lambda,
            pseudo_label_param=pseudo_weight, margin_threshold=float(np.log(self.tau / (1 - self.tau))),
        )
        return SelfTrainedGradientDescent(cfg).fit(design, observed, initialization)

    def run_mnist_repetition(self, p, seed, sizes, steps):
        data = self.mnist_split(p, seed, sizes)
        design, observed = data["X_train"], data["observed"]
        labeled = observed != 0

        generator = torch.Generator().manual_seed(seed + 11)
        w_init = torch.randn(design.shape[1], generator=generator, dtype=design.dtype)
        initialization = SelfTrainingInitialization(0.0, w_init)
        supervised = self.fit_mnist(design, observed, initialization, steps, 0.0)
        self_trained = self.fit_mnist(design, observed, initialization, steps, self.pi)
        labels = observed.clone()
        labels[~labeled] = data["hidden"]
        midpoint, mu, sigma = calibrate_mnist_gaussian(design, labels)
        finite, _ = finite_mnist_gaussian(
            p, seed, data, labels, mu, sigma, self_trained.cfg, initialization, midpoint=midpoint,
        )
        trajectories = {
            "supervised_only": mnist_diagnostics(supervised, data),
            "self_training": mnist_diagnostics(self_trained, data),
            "finite_gaussian": finite,
        }
        counts = {
            "Train": (len(observed), int((observed == 1).sum() + (data["hidden"] == 1).sum())),
            "Labeled": (int(labeled.sum()), int((observed == 1).sum())),
            "Unlabeled": (len(data["hidden"]), int((data["hidden"] == 1).sum())),
            "Test": (len(data["y_test"]), int((data["y_test"] == 1).sum())),
        }


        return {"p": p, "seed": seed, "counts": counts, "trajectories": trajectories}

    def plot_mnist_trajectories(self, runs):
        pi = self.pi
        fig, axes = plt.subplots(2, 3, figsize=(11, 6.3), sharex=True, layout="constrained")
        methods = [
            ("supervised_only", r"Supervised only ($\pi=0$)", "tab:blue"),
            ("self_training", rf"Self-training ($\pi={pi:g}$)", "tab:orange"),
            ("finite_gaussian", "Finite fitted Gaussian self-training", "tab:green"),
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
        fig.legend(handles, labels, loc="outside lower center", ncol=len(methods), frameon=False)
        fig.suptitle(f"MNIST digits {self.negative_digit} and {self.positive_digit} | Positive proportion = {runs[0]['p']:g}")
        return fig

    def compare_mnist_gaussian(
        self, p, seed, steps, *, whitening_ridge_fraction=None, class_specific=False,
    ):
        if class_specific and whitening_ridge_fraction is None:
            raise ValueError("Class-specific whitening requires a whitening ridge fraction.")
        data = self.mnist_split(p, seed, (self.n_train, self.n_test))
        observed = data["observed"]
        labeled = observed != 0
        train_ids, test_ids = data["ids"]
        pixels = torch.as_tensor(self.X_train[train_ids], dtype=torch.float64)
        labels = observed.clone()
        labels[~labeled] = data["hidden"]
        c, mu, sigma = calibrate_mnist_gaussian(pixels, labels)
        n, d = pixels.shape
        data["X_train"] = pixels - c
        data["X_test"] = torch.as_tensor(self.X_test[test_ids - len(self.y_train)], dtype=pixels.dtype) - c
        whitening_stats = None
        if whitening_ridge_fraction is not None:
            whitener, ridge, whitened_eigenvalues = fit_mnist_whitener(
                data["X_train"], labels, whitening_ridge_fraction,
            )
            if class_specific:
                data["X_train"], data["X_test"], whitening_stats = whiten_mnist_by_class(
                    data, labels, whitener, ridge,
                )
            else:
                for key in ("X_train", "X_test"):
                    data[key] = data[key] @ whitener
                whitening_stats = {
                    "ridge": ridge,
                    "directions_with_variance_ge_0_9": int((whitened_eigenvalues >= 0.9).sum()),
                }
            _, mu, sigma = calibrate_mnist_gaussian(data["X_train"], labels)

        generator = torch.Generator().manual_seed(seed + 11)
        w0 = torch.randn(d, generator=generator, dtype=pixels.dtype)
        initialization = SelfTrainingInitialization(0.0, w0)
        learner = self.fit_mnist(data["X_train"], observed, initialization, steps, self.pi)
        real = mnist_diagnostics(learner, data)
        finite, population = finite_mnist_gaussian(
            p, seed, data, labels, mu, sigma, learner.cfg, initialization,
        )
        for rows in (real, finite):
            for row in rows:
                row["test_error"] = (1 - p) * row["negative_error"] + p * row["positive_error"]

        if not isinstance(self.sample_particles, int) or self.sample_particles <= 0 or steps <= 0:
            raise ValueError("The effective process requires positive sample_particles and training_steps.")
        # Group equal sample types, then map equally spaced midpoints to their empirical law.
        types = 2 * labeled.to(torch.int64) + (labels == 1).to(torch.int64)
        order = torch.argsort(types)
        grid = ((2 * torch.arange(self.sample_particles) + 1) * n) // (2 * self.sample_particles)
        idx = order[grid]
        if not torch.equal(torch.unique(types[idx]), torch.unique(types)):
            raise ValueError("Increase sample_particles so every present (label, revelation) type is represented.")

        def parameter_base(count, generator, dtype, device):
            return mu.to(device=device, dtype=dtype), w0.to(device=device, dtype=dtype)

        def sample_base(count, generator, dtype, device):
            return (labels[idx].to(device=device, dtype=dtype),
                    labeled[idx].to(device=device, dtype=dtype), None)

        process = MacroscopicStateEvolution(
            data_cfg=population, algo_cfg=learner.cfg,
            K_w=d, K_g=self.sample_particles, mc_seed=self.particle_seed + seed,
            parameter_base_sampler=parameter_base, sample_base_sampler=sample_base,
        )
        process.compute_trajectory()
        unlabeled_particles = process.indicator == 0
        effective = []
        for t, scores in enumerate(process.preactivation):
            scores = scores[unlabeled_particles]
            selected = process.selection_mask(scores) > 0
            wrong = sign_with_positive_tie(scores) != process.label[unlabeled_particles]
            effective.append({
                "iteration": t,
                "test_error": float(process.error[t]),
                "coverage": selected.double().mean().item(),
                "selected_error_fraction": (selected & wrong).double().mean().item(),
                "intercept": process.bias[t].item(),
                "test_score_gap": process.weight_signal_alignments[t].item(),
                "weight_norm": float(process.weight_norm[t]),
            })


        return {
            "p": p, "seed": seed, "n": n, "d": d,
            "class_counts": (int((labels == -1).sum()), int((labels == 1).sum())),
            "revealed_counts": (int((observed == -1).sum()), int((observed == 1).sum())),
            "sigma": sigma, "signal_energy": mu.square().mean().item(),
            "whitening": whitening_stats,
            "trajectories": {"mnist": real, "finite_gaussian": finite, "effective_process": effective},
        }

    def plot_mnist_gaussian_comparison(
        self, runs, *, preprocessing="oracle midpoint", mnist_label="Real MNIST self-training",
    ):
        fig, axes = plt.subplots(2, 3, figsize=(11, 6.3), sharex=True, layout="constrained")
        methods = [
            ("mnist", mnist_label, "tab:blue"),
            ("finite_gaussian", "Finite fitted Gaussian self-training", "tab:green"),
            ("effective_process", "Fitted-Gaussian effective process", "tab:orange"),
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
                # Whole-percent formatting needs at least one percentage point between ticks.
                ticks = ax.get_yticks()
                if len(ticks) > 1 and ticks[1] - ticks[0] < 0.01 - 1e-12:
                    ax.yaxis.set_major_locator(MultipleLocator(0.01))
            else:
                ax.set_xlabel("Iteration")
            ax.grid(alpha=0.2, linewidth=0.6)
        handles, labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="outside lower center", ncol=len(methods), frameon=False)
        fig.suptitle(f"MNIST {self.negative_digit} vs. {self.positive_digit}, {preprocessing} | Positive proportion = {runs[0]['p']:g}")
        return fig


    def run_from_scratch(self):
        full_sizes = (self.n_train, self.n_test)
        runs_by_scenario = []
        count_table = [
            "| Requested p | Seed | Train | Labeled | Unlabeled  | Test |",
            "|---:|---:|---:|---:|---:|---:|",
        ]
        for p in self.class_proportions:
            runs = []
            for seed in self.seeds:
                run = self.run_mnist_repetition(
                    p, seed, full_sizes, self.training_steps,
                )
                runs.append(run)
                cells = [f"{pos:,} / {n:,} ({pos / n:.1%})" for n, pos in run["counts"].values()]
                count_table.append(f"| {p:g} | {seed} | " + " | ".join(cells) + " |")
            runs_by_scenario.append(runs)
        display(Markdown("\n".join(count_table)))
        return runs_by_scenario

    def show_from_scratch_figures(self, runs_by_scenario):
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        for runs in runs_by_scenario:
            fig = self.plot_mnist_trajectories(runs)
            figure_path = self.figures_dir / f"mnist_from_scratch_p{runs[0]['p']:g}.pdf"
            save_figure(fig, figure_path)
            plt.show()

    def save_from_scratch_measurements(self, runs_by_scenario, *, save_csv=False):
        summary = [
            "| Requested p | Pseudo-label weight | Initial test error | Final test error | "
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
                        "negative_digit": self.negative_digit, "positive_digit": self.positive_digit,
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
            measurements_path = self.root / "outputs" / "mnist_self_training" / "from_scratch_trajectories.csv"
            measurements_path.parent.mkdir(parents=True, exist_ok=True)
            with measurements_path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=list(measurements[0]))
                writer.writeheader()
                writer.writerows(measurements)
            print(f"Per-iteration measurements saved to {measurements_path}")



    def run_gaussian_comparison(self):
        gaussian_comparison_runs = []
        calibration_table = [
            "| Target p | Seed | d | n | Classes (− / +) | Revealed (− / +) | Sigma | ‖μ‖²/d | Initialization | Centering |",
            "|---:|---:|---:|---:|:---:|:---:|---:|---:|:---|:---|",
        ]
        for p in self.class_proportions:
            runs = []
            for seed in self.seeds:
                run = self.compare_mnist_gaussian(p, seed, self.training_steps)
                runs.append(run)
                neg, pos = run["class_counts"]
                lab_neg, lab_pos = run["revealed_counts"]
                calibration_table.append(
                    f"| {p:g} | {seed} | {run['d']} | {run['n']} | {neg} / {pos} | "
                    f"{lab_neg} / {lab_pos} | {run['sigma']:.4f} | {run['signal_energy']:.4f} | "
                    "Seeded Gaussian weights, zero intercept | Oracle midpoint |"
                )
            gaussian_comparison_runs.append(runs)
        display(Markdown("\n".join(calibration_table)))
        return gaussian_comparison_runs

    def show_gaussian_figures(self, gaussian_comparison_runs):
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        for runs in gaussian_comparison_runs:
            fig = self.plot_mnist_gaussian_comparison(runs)
            figure_path = self.figures_dir / f"mnist_gaussian_midpoint_p{runs[0]['p']:g}.pdf"
            save_figure(fig, figure_path)
            plt.show()


    def run_pooled_whitening(self, whitening_ridge_fraction):
        whitened_gaussian_runs = [
            [
                self.compare_mnist_gaussian(p, seed, self.training_steps,
                                       whitening_ridge_fraction=whitening_ridge_fraction)
                for seed in self.seeds
            ]
            for p in self.class_proportions
        ]
        whitening_table = [
            "| Target p | Seed | Whitening ridge | Directions with variance ≥ 0.9 | Fitted σ | ‖μ‖²/d |",
            "|---:|---:|---:|---:|---:|---:|",
        ]
        for runs in whitened_gaussian_runs:
            for run in runs:
                stats = run["whitening"]
                near_unit = stats["directions_with_variance_ge_0_9"]
                whitening_table.append(
                    f"| {run['p']:g} | {run['seed']} | {stats['ridge']:.3g} | {near_unit} / {run['d']} | "
                    f"{run['sigma']:.3f} | {run['signal_energy']:.3f} |"
                )
        display(Markdown("\n".join(whitening_table)))
        return whitened_gaussian_runs

    def show_pooled_whitening_figures(self, whitened_gaussian_runs):
        for runs in whitened_gaussian_runs:
            fig = self.plot_mnist_gaussian_comparison(
                runs, preprocessing="regularized whitening", mnist_label="Whitened MNIST self-training",
            )
            figure_path = self.figures_dir / f"mnist_gaussian_whitened_p{runs[0]['p']:g}.pdf"
            save_figure(fig, figure_path)
            plt.show()


    def run_class_whitening(self, whitening_ridge_fraction):
        class_whitened_gaussian_runs = [
            [
                self.compare_mnist_gaussian(
                    p, seed, self.training_steps,
                    whitening_ridge_fraction=whitening_ridge_fraction, class_specific=True,
                )
                for seed in self.seeds
            ]
            for p in self.class_proportions
        ]
        class_whitening_table = [
            "| Target p | Seed | Covariance gap, pooled | Covariance gap, class-specific | Fitted σ |",
            "|---:|---:|---:|---:|---:|",
        ]
        for runs in class_whitened_gaussian_runs:
            for run in runs:
                stats = run["whitening"]
                class_whitening_table.append(
                    f"| {run['p']:g} | {run['seed']} | {stats['pooled_covariance_gap']:.3f} | "
                    f"{stats['class_specific_covariance_gap']:.3f} | {run['sigma']:.3f} |"
                )
        display(Markdown("\n".join(class_whitening_table)))
        return class_whitened_gaussian_runs

    def show_class_whitening_figures(self, class_whitened_gaussian_runs):
        for runs in class_whitened_gaussian_runs:
            fig = self.plot_mnist_gaussian_comparison(
                runs, preprocessing="oracle class-specific whitening",
                mnist_label="Class-whitened MNIST self-training",
            )
            figure_path = self.figures_dir / f"mnist_gaussian_class_whitened_p{runs[0]['p']:g}.pdf"
            save_figure(fig, figure_path)
            plt.show()
