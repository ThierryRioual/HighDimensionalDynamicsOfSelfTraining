"""Load Fashion-MNIST and run the self-training comparisons."""

import csv
import gzip
from hashlib import md5
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

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
from src.primitives import compute_scores, selection_rate, sign_with_positive_tie


FASHION_MNIST_URL = "https://raw.githubusercontent.com/zalandoresearch/fashion-mnist/master/data/fashion/"
FASHION_MNIST_CHECKSUMS = {
    "train-images-idx3-ubyte.gz": "8d4fb7e6c68d591d4c3dfef9ec88bf0d",
    "train-labels-idx1-ubyte.gz": "25c81989df183df01b3e8a0aad5dffbe",
    "t10k-images-idx3-ubyte.gz": "bef4ecab320f06d8554ea6380940ec79",
    "t10k-labels-idx1-ubyte.gz": "bb300cfdad3c16e7a12a480ee83cd310",
}


def read_idx_file(filename, data_dir):
    path = data_dir / filename
    cached = path.exists()
    if cached:
        compressed = path.read_bytes()
    else:
        with urlopen(FASHION_MNIST_URL + filename, timeout=90) as response:
            compressed = response.read()
    if md5(compressed).hexdigest() != FASHION_MNIST_CHECKSUMS[filename]:
        raise ValueError(f"Fashion-MNIST checksum mismatch for {path}.")
    if not cached:
        data_dir.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=data_dir, delete=False) as temp:
            temp.write(compressed)
        Path(temp.name).replace(path)
    return gzip.decompress(compressed)


def load_fashion_mnist(split, size, data_dir):
    images = read_idx_file(f"{split}-images-idx3-ubyte.gz", data_dir)
    labels = read_idx_file(f"{split}-labels-idx1-ubyte.gz", data_dir)
    image_header = np.frombuffer(images, dtype=">u4", count=4)
    label_header = np.frombuffer(labels, dtype=">u4", count=2)
    if tuple(image_header) != (2051, size, 28, 28) or tuple(label_header) != (2049, size):
        raise ValueError(f"Unexpected Fashion-MNIST IDX headers for the {split} split.")
    X = np.frombuffer(images, dtype=np.uint8, offset=16).reshape(size, 784)
    y = np.frombuffer(labels, dtype=np.uint8, offset=8).astype(np.int64)
    if y.shape != (size,):
        raise ValueError(f"Unexpected Fashion-MNIST label count for the {split} split.")
    return np.asarray(X, dtype=np.float32) / 255.0, y


def describe_fashion_mnist(data, data_dir):
    X_train, y_train, X_test, y_test = data
    print(f"Cache: {data_dir}")
    print(f"Training: {len(X_train):,} | Test: {len(X_test):,}")
    print(f"Features: shape={X_train.shape}, dtype={X_train.dtype}")


def round_count(n, p):
    return int(np.floor(n * p + 0.5))


def fashion_mnist_diagnostics(learner, data, p):
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
            "test_error": ((1 - p) * test_mistakes[neg].double().mean()
                           + p * test_mistakes[pos].double().mean()).item(),
            "coverage": coverage,
            "selected_error_fraction": selected_error_fraction,
            "intercept": bias.item(),
            "test_score_gap": ((test_scores[pos].mean() - test_scores[neg].mean()) / 2).item(),
            "weight_norm": (torch.linalg.vector_norm(weight) / d**0.5).item(),
        })
    return rows


def calibrate_fashion_mnist_gaussian(pixels, labels):
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


def regularized_zca(eigenvalues, eigenvectors, ridge):
    inverse_roots = (eigenvalues + ridge).rsqrt()
    whitener = (eigenvectors * inverse_roots) @ eigenvectors.T
    return whitener, eigenvalues / (eigenvalues + ridge)


def fit_fashion_mnist_whitener(train, labels, ridge_fraction):
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


def whiten_fashion_mnist_by_class(data, labels, pooled_whitener, ridge):
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


def plot_fashion_mnist_gaussian_comparison(
    runs, *, preprocessing="oracle midpoint", fashion_label="Fashion-MNIST self-training",
):
    fig, axes = plt.subplots(2, 3, figsize=(11, 6.3), sharex=True, layout="constrained")
    methods = [
        ("fashion_mnist", fashion_label, "tab:blue"),
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
    fig.suptitle(f"Fashion-MNIST pullover vs. coat, {preprocessing} | Positive proportion = {runs[0]['p']:g}")
    return fig

class FashionMNISTExperiment:
    """Compare Fashion-MNIST with a fitted Gaussian and its effective process."""

    def __init__(
        self, root, data, *,
        negative_label, positive_label, class_proportions, labeling_rate,
        n_train, n_test, seeds, training_steps,
        eta, reg_lambda, pi, tau,
        sample_particles, particle_seed,
    ):
        self.root = root
        self.figures_dir = root / "outputs" / "figures"
        self.negative_label = negative_label
        self.positive_label = positive_label
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
                for digit in (negative_label, positive_label)) or negative_label == positive_label):
            raise ValueError("Choose two distinct integer labels from 0 to 9.")
        if len(class_proportions) != 2 or not all(0 < p < 1 for p in class_proportions):
            raise ValueError("Provide two positive-class proportions strictly between 0 and 1.")
        if not 0 < labeling_rate < 1:
            raise ValueError("labeling_rate must be strictly between 0 and 1.")
        if not 0.5 < tau < 1:
            raise ValueError("tau must be strictly between 0.5 and 1.")
        if not seeds or any(not isinstance(seed, int) or seed < 0 for seed in seeds):
            raise ValueError("Provide at least one nonnegative integer seed.")
        if not isinstance(training_steps, int) or training_steps <= 0:
            raise ValueError("training_steps must be a positive integer.")
        if not np.isfinite([eta, reg_lambda, pi]).all() or eta <= 0 or min(reg_lambda, pi) < 0:
            raise ValueError("eta must be finite and positive; reg_lambda and pi must be finite and nonnegative.")

    def fashion_mnist_split(self, p, seed, sizes):
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
        for label, counts in zip((self.negative_label, self.positive_label), (n_neg, n_pos)):
            train_pool = np.flatnonzero(self.y_train == label)
            test_pool = np.flatnonzero(self.y_test == label)
            train_count, test_count = counts
            if train_count > len(train_pool) or test_count > len(test_pool):
                raise ValueError(
                    f"At p={p:g}, label {label} needs {train_count} official training and "
                    f"{test_count} official test rows; only {len(train_pool)} and "
                    f"{len(test_pool)} are available."
                )
            train_parts.append(rng.choice(train_pool, size=train_count, replace=False))
            test_parts.append(rng.choice(test_pool, size=test_count, replace=False))

        train_ids = rng.permutation(np.concatenate(train_parts))
        test_ids = rng.permutation(np.concatenate(test_parts))
        train_labels = np.where(self.y_train[train_ids] == self.positive_label, 1, -1)
        # Use the exact integer ratio for half-up rounding of the labeled positives.
        labeled_pos = (2 * n_labeled * n_pos[0] + train_size) // (2 * train_size)
        labeled = np.concatenate([
            rng.choice(np.flatnonzero(train_labels == -1), n_labeled - labeled_pos, replace=False),
            rng.choice(np.flatnonzero(train_labels == +1), labeled_pos, replace=False),
        ])
        observed = np.zeros(train_size, dtype=np.int64)
        observed[labeled] = train_labels[labeled]
        unlabeled = observed == 0

        return {
            "X_train": torch.from_numpy(self.X_train[train_ids].astype(np.float64)),
            "observed": torch.from_numpy(observed),
            "hidden": torch.from_numpy(train_labels[unlabeled]),
            "X_test": torch.from_numpy(self.X_test[test_ids].astype(np.float64)),
            "y_test": torch.from_numpy(np.where(self.y_test[test_ids] == self.positive_label, 1, -1)),
        }

    def fit_fashion_mnist(self, design, observed, initialization, steps, pseudo_weight):
        cfg = AlgorithmConfig(
            n_iterations=steps, step_size=self.eta, penalty_param=self.reg_lambda,
            pseudo_label_param=pseudo_weight, margin_threshold=float(np.log(self.tau / (1 - self.tau))),
        )
        return SelfTrainedGradientDescent(cfg).fit(design, observed, initialization)

    def compare_fashion_mnist_gaussian(
        self, p, seed, steps, *, whitening_ridge_fraction=None,
    ):
        data = self.fashion_mnist_split(p, seed, (self.n_train, self.n_test))
        observed = data["observed"]
        labeled = observed != 0
        labels = observed.clone()
        labels[~labeled] = data["hidden"]
        pixels = data["X_train"]
        c, mu, sigma = calibrate_fashion_mnist_gaussian(pixels, labels)
        n, d = pixels.shape
        data["X_train"] = pixels - c
        data["X_test"] = data["X_test"] - c
        whitening_stats = None
        if whitening_ridge_fraction is not None:
            whitener, ridge, _ = fit_fashion_mnist_whitener(
                data["X_train"], labels, whitening_ridge_fraction,
            )
            data["X_train"], data["X_test"], whitening_stats = whiten_fashion_mnist_by_class(
                data, labels, whitener, ridge,
            )
            _, mu, sigma = calibrate_fashion_mnist_gaussian(data["X_train"], labels)

        generator = torch.Generator().manual_seed(seed + 11)
        w0 = torch.randn(d, generator=generator, dtype=pixels.dtype)
        initialization = SelfTrainingInitialization(0.0, w0)
        real_learner = self.fit_fashion_mnist(data["X_train"], observed, initialization, steps, self.pi)
        real = fashion_mnist_diagnostics(real_learner, data, p)

        population = DataConfig(
            scale=sigma, label_prior=p, supervision_ratio=float(labeled.double().mean()),
            data_to_dimension_ratio=n / d, signal_law=lambda: 0.0,
        )  # The supplied joint parameter sampler provides the signal.
        train_environment = QuenchedEnvironment(mu, labels, labeled)
        gaussian = IsotropicGaussian(
            cfg=population, n_train=n, dimensions=d, seed=seed + 23, environment=train_environment,
        )
        test_environment = QuenchedEnvironment(mu, data["y_test"], torch.zeros_like(data["y_test"]))
        X_gaussian, _ = gaussian.sample_design(train_environment)
        X_gaussian_test, _ = gaussian.sample_design(test_environment)
        gaussian_data = {**data, "X_train": X_gaussian, "X_test": X_gaussian_test}
        gaussian_learner = SelfTrainedGradientDescent(real_learner.cfg).fit(
            X_gaussian, observed, initialization,
        )
        finite = fashion_mnist_diagnostics(gaussian_learner, gaussian_data, p)

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
            data_cfg=population, algo_cfg=real_learner.cfg,
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

        trajectories = {"fashion_mnist": real, "finite_gaussian": finite, "effective_process": effective}

        return {
            "p": p, "seed": seed, "n": n, "d": d,
            "class_counts": (int((labels == -1).sum()), int((labels == 1).sum())),
            "revealed_counts": (int((observed == -1).sum()), int((observed == 1).sum())),
            "sigma": sigma, "signal_energy": mu.square().mean().item(),
            "whitening": whitening_stats,
            "trajectories": trajectories,
        }

    def save_fashion_mnist_trajectories(self, runs_by_scenario, measurements_path, *, save_csv=False):
        summary = [
            "| Requested p | Method | Initial test error | Final test error | "
            "Final selected fraction |",
            "|---:|---:|---:|---:|---:|",
        ]
        measurements = []
        for runs in runs_by_scenario:
            for method in ("fashion_mnist", "finite_gaussian", "effective_process"):
                trajectories = [run["trajectories"][method] for run in runs]
                initial_error = np.mean([rows[0]["test_error"] for rows in trajectories])
                final_error = np.mean([rows[-1]["test_error"] for rows in trajectories])
                final_coverage = np.mean([rows[-1]["coverage"] for rows in trajectories])
                summary.append(
                    f"| {runs[0]['p']:g} | {method.replace('_', ' ')} | {initial_error:.2%} | "
                    f"{final_error:.2%} | {final_coverage:.2%} |"
                )
                for run, rows in zip(runs, trajectories):
                    settings = {
                        "negative_label": self.negative_label, "positive_label": self.positive_label,
                        "positive_proportion": run["p"], "seed": run["seed"], "method": method,
                        "labeling_rate": self.labeling_rate, "eta": self.eta, "reg_lambda": self.reg_lambda,
                        "pi": self.pi, "tau": self.tau,
                        "n_train": run["n"], "n_test": self.n_test, "d": run["d"],
                        "sigma": run["sigma"], "signal_energy": run["signal_energy"],
                    }
                    for name in ("class_counts", "revealed_counts"):
                        negative, positive = run[name]
                        settings[f"{name}_negative"] = negative
                        settings[f"{name}_positive"] = positive
                    measurements.extend({**settings, **row} for row in rows)
        display(Markdown("\n".join(summary)))

        if save_csv:
            measurements_path.parent.mkdir(parents=True, exist_ok=True)
            with measurements_path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=list(measurements[0]))
                writer.writeheader()
                writer.writerows(measurements)
            print(f"Per-iteration measurements saved to {measurements_path}")
        return summary, measurements


    def run_gaussian_comparison(self):
        gaussian_comparison_runs = []
        calibration_table = [
            "| Target p | Seed | d | n | Classes (− / +) | Revealed (− / +) | Sigma | ‖μ‖²/d | Initialization | Centering |",
            "|---:|---:|---:|---:|:---:|:---:|---:|---:|:---|:---|",
        ]
        for p in self.class_proportions:
            runs = []
            for seed in self.seeds:
                run = self.compare_fashion_mnist_gaussian(p, seed, self.training_steps)
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
            fig = plot_fashion_mnist_gaussian_comparison(runs)
            figure_path = self.figures_dir / f"fashion_mnist_gaussian_midpoint_p{runs[0]['p']:g}.pdf"
            save_figure(fig, figure_path)
            plt.show()


    def run_class_whitening(self, whitening_ridge_fraction):
        class_whitened_gaussian_runs = [
            [
                self.compare_fashion_mnist_gaussian(
                    p, seed, self.training_steps,
                    whitening_ridge_fraction=whitening_ridge_fraction,
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
            fig = plot_fashion_mnist_gaussian_comparison(
                runs, preprocessing="oracle class-specific whitening",
                fashion_label="Class-whitened Fashion-MNIST self-training",
            )
            figure_path = self.figures_dir / f"fashion_mnist_gaussian_class_whitened_p{runs[0]['p']:g}.pdf"
            save_figure(fig, figure_path)
            plt.show()
