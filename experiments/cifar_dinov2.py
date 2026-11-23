"""Extract DINOv2 embeddings and run the CIFAR-100 comparisons."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from functools import cached_property, lru_cache
from hashlib import md5, sha256
import json
from pathlib import Path
import pickle
import tarfile
from typing import Any, Callable, Literal, Protocol, TypedDict, Union
from urllib.request import urlretrieve
from zipfile import ZipFile

from IPython.display import Markdown
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
from numpy.typing import NDArray
from PIL import Image
import torch
from torch import Tensor

from experiments.plotting import plot_checkpoint_distributions, plot_trajectory_comparison, save_figure

from src.algorithms import SelfTrainedGradientDescent
from src.asymptotics import MacroscopicStateEvolution
from src.config import AlgorithmConfig, DataConfig
from src.dgp import IsotropicGaussian
from src.environment import QuenchedEnvironment
from src.initialization import SelfTrainingInitialization
from src.performance import population_error
from src.primitives import compute_scores, sign_with_positive_tie


Split = Literal["train", "test"]
ImageArray = NDArray[np.uint8]
FeatureArray = NDArray[np.float32]
IdArray = NDArray[np.int64]
EmbeddingPool = tuple[FeatureArray, IdArray, IdArray]  # Features, coarse labels, image IDs.
SuperclassPair = tuple[tuple[int, ...], tuple[int, ...]]  # Negative group, positive group.
MetricRow = dict[str, float]  # Includes the integer iteration and scalar metrics.
Checkpoints = dict[int, dict[str, NDArray[np.float64]]]


class FileHash(Protocol):
    """Operations required of a streaming hash object."""

    def update(self, block: bytes, /) -> None:
        """Consume the next block of bytes."""

    def hexdigest(self) -> str:
        """Return the current digest as hexadecimal text."""


HashFactory = Callable[[], FileHash]


class ComparisonRun(TypedDict):
    """Results for one seed and one target positive-class proportion."""

    p: float
    seed: int
    n: int
    d: int
    class_counts: tuple[int, int]
    revealed_counts: tuple[int, int]
    sigma: float
    signal_energy: float
    whitening_ridge: float
    midpoint_bias_shift: float
    trajectories: dict[str, list[MetricRow]]
    distribution_snapshots: dict[str, Checkpoints]


CIFAR_URL = "https://cave.cs.toronto.edu/kriz/cifar-100-python.tar.gz"
CIFAR_MD5 = "eb9058c3a382ffc7106e4002c42a8d85"
DINO_REVISION = "e1277af2ba9496fbadf7aec6eba56e8d882d1e35"
DINO_SOURCE = f"https://codeload.github.com/facebookresearch/dinov2/zip/{DINO_REVISION}"
DINO_WEIGHTS = "https://dl.fbaipublicfiles.com/dinov2/dinov2_vitb14/dinov2_vitb14_pretrain.pth"
DINO_SOURCE_SHA256 = "209c4f04fb0d63a869f7ea5c18d61dc7d8196c88cb1cb4a53bf3b0607146685c"
DINO_WEIGHTS_SHA256 = "0b8b82f85de91b424aded121c7e1dcc2b7bc6d0adeea651bf73a13307fad8c73"

# Classification evaluation defaults in dinov2/data/transforms.py at DINO_REVISION.
RESIZE, CROP = 256, 224
RGB_MEAN, RGB_STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)
EMBEDDING_METADATA = {
    "dataset_md5": CIFAR_MD5,
    "checkpoint": "dinov2_vitb14",
    "source_revision": DINO_REVISION,
    "weights_sha256": DINO_WEIGHTS_SHA256,
    "embedding": "x_norm_clstoken",
    "resize": RESIZE, "crop": CROP, "resampling": "PIL bicubic",
    "mean": RGB_MEAN, "std": RGB_STD, "dtype": "float32",
}


def digest(path: Path, algorithm: HashFactory) -> str:
    """Compute the file hash in 1 MiB chunks and return its hexadecimal representation.

    The factory creates a fresh hash object, such as MD5 or SHA-256. Streaming
    keeps memory use independent of file size.
    """
    value = algorithm()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def prepare_image(pixels: ImageArray) -> ImageArray:
    """Resize one HWC uint8 RGB image with bicubic interpolation and center-crop it.

    Return a (224, 224, 3) array. The encoder applies channel normalization later.
    """
    image = Image.fromarray(pixels).resize((RESIZE, RESIZE), Image.Resampling.BICUBIC)
    border = (RESIZE - CROP) // 2
    return np.asarray(image.crop((border, border, border + CROP, border + CROP)))


class CIFAR100Embeddings:
    """Load frozen DINOv2 embeddings from disk or regenerate them on demand."""

    def __init__(self, cache_dir: Path, *, device: Union[str, torch.device], batch_size: int) -> None:
        """Store the cache directory, encoder device, and maximum inference batch size.

        Downloads and model loading are deferred until the corresponding data are needed.
        """
        self.cache_dir = cache_dir
        self.device = device
        self.batch_size = batch_size

    def cached_download(self, url: str, name: str, algorithm: HashFactory, expected: str) -> Path:
        """Reuse a file whose digest matches the expected value, or download it.

        Verify the temporary download before replacing the destination. Delete a
        checksum-mismatched download and raise ValueError.
        """
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path = self.cache_dir / name
        if path.is_file() and digest(path, algorithm) == expected:
            return path
        print(f"Downloading {name}", flush=True)
        temporary = path.with_suffix(path.suffix + ".part")
        urlretrieve(url, temporary)
        if digest(temporary, algorithm) != expected:
            temporary.unlink()
            raise ValueError(f"Checksum mismatch for {name}")
        temporary.replace(path)
        return path

    def read_cifar_member(self, name: str) -> dict[str, Any]:
        """Deserialize the named member of the verified CIFAR archive.

        The metadata and split files use the original Python pickle format.
        """
        # Only deserialize the checksum-verified official archive.
        with tarfile.open(self.cifar_path, "r:gz") as archive:
            with archive.extractfile(f"cifar-100-python/{name}") as member:
                return pickle.load(member, encoding="latin1")

    @lru_cache(maxsize=2)
    def read_cifar(self, split: Split) -> tuple[ImageArray, IdArray, IdArray]:
        """Read and memoize the official split as images, coarse labels, and image IDs.

        Images have shape (N, 32, 32, 3). Test IDs start at 50,000 so that train
        and test IDs can be compared directly for overlap.
        """
        expected_rows = {"train": 50_000, "test": 10_000}[split]
        record = self.read_cifar_member(split)
        images = record["data"].reshape(-1, 3, 32, 32).transpose(0, 2, 3, 1)
        labels = np.asarray(record["coarse_labels"], dtype=np.int64)
        assert len(images) == len(labels) == expected_rows
        np.testing.assert_array_equal(
            np.bincount(labels, minlength=len(self.coarse_names)),
            np.full(len(self.coarse_names), expected_rows // len(self.coarse_names)),
        )
        ids = np.arange(expected_rows, dtype=np.int64) + (50_000 if split == "test" else 0)
        return images, labels, ids

    @lru_cache(maxsize=1)
    def load_encoder(self) -> torch.nn.Module:
        """Build and memoize the frozen ViT-B/14 from pinned source and verified weights.

        Load the state dict on CPU, then move the float32 model to the inference
        device and switch it to evaluation mode.
        """
        source = self.cached_download(
            DINO_SOURCE, f"dinov2-{DINO_REVISION}.zip", sha256, DINO_SOURCE_SHA256
        )
        weights = self.cached_download(
            DINO_WEIGHTS, "dinov2_vitb14_pretrain.pth", sha256, DINO_WEIGHTS_SHA256
        )
        # Load the architecture from the pinned, checksum-verified Meta source.
        source_dir = self.cache_dir / f"dinov2-{DINO_REVISION}"
        if not (source_dir / "hubconf.py").is_file():
            with ZipFile(source) as archive:
                archive.extractall(self.cache_dir)
        model = torch.hub.load(str(source_dir), "dinov2_vitb14", source="local", pretrained=False).float()
        model.load_state_dict(torch.load(weights, map_location="cpu", weights_only=True), strict=True)
        return model.requires_grad_(False).eval().to(self.device)

    @torch.inference_mode()
    def extract_embeddings(self, images: ImageArray, split: Split, coarse_id: int) -> FeatureArray:
        """Encode images in order as float32 CLS-token features of shape (N, 768).

        Resize and crop the RGB images, transform the batch from NHWC to NCHW,
        scale pixels to [0, 1], and apply per-channel normalization. Run frozen
        inference on the selected device and copy the features back to NumPy.
        The split and coarse ID identify the batch in progress messages.
        """
        model = self.load_encoder()
        mean = torch.tensor(RGB_MEAN, device=self.device, dtype=torch.float32)[None, :, None, None]
        std = torch.tensor(RGB_STD, device=self.device, dtype=torch.float32)[None, :, None, None]
        features = np.empty((len(images), 768), dtype=np.float32)
        for start in range(0, len(images), self.batch_size):
            stop = min(start + self.batch_size, len(images))
            rgb = np.stack([prepare_image(image) for image in images[start:stop]])
            batch = torch.from_numpy(rgb).permute(0, 3, 1, 2).to(self.device, dtype=torch.float32)
            embedding = model.forward_features((batch / 255 - mean) / std)["x_norm_clstoken"]
            features[start:stop] = embedding.cpu().numpy()
            if stop == len(images) or (start // self.batch_size + 1) % 20 == 0:
                print(f"{split}, {self.coarse_names[coarse_id]}: {stop:,}/{len(images):,}", flush=True)
        assert np.isfinite(features).all()
        return features

    def load_embeddings(self, split: Split, coarse_ids: Iterable[int]) -> EmbeddingPool:
        """Return features, coarse labels, and IDs grouped in the requested class order.

        Cache entries are keyed by split, superclass, and preprocessing provenance.
        Reuse a cached matrix only if its metadata, ordered IDs, shape, dtype, and
        finite values pass validation. Otherwise extract and save that superclass.
        """
        images, labels, ids = self.read_cifar(split)
        splits, targets, image_ids = [], [], []
        for coarse_id in coarse_ids:
            mask = labels == coarse_id
            selected_ids = ids[mask]
            metadata = json.dumps(
                {**EMBEDDING_METADATA, "split": split, "coarse_id": int(coarse_id)}, sort_keys=True,
            )
            cache_key = sha256(metadata.encode()).hexdigest()[:16]
            path = self.cache_dir / f"embeddings_{split}_coarse{coarse_id}_{cache_key}.npz"
            features = None
            if path.is_file():
                with np.load(path, allow_pickle=False) as cached:
                    if (cached["metadata"].item() == metadata
                            and np.array_equal(cached["image_ids"], selected_ids)):
                        features = cached["features"]
                if features is not None and (
                    features.shape != (len(selected_ids), 768)
                    or features.dtype != np.float32 or not np.isfinite(features).all()
                ):
                    features = None
            if features is None:
                print(f"Encoding {split} {self.coarse_names[coarse_id]} on {self.device}", flush=True)
                features = self.extract_embeddings(images[mask], split, coarse_id)
                temporary = path.with_suffix(".part")
                with temporary.open("wb") as stream:
                    np.savez(stream, features=features, image_ids=selected_ids, metadata=metadata)
                temporary.replace(path)
            splits.append(features)
            targets.append(labels[mask])
            image_ids.append(selected_ids)
        return np.concatenate(splits), np.concatenate(targets), np.concatenate(image_ids)

    @cached_property
    def cifar_path(self) -> Path:
        """Resolve the verified dataset archive once per embedding loader."""
        cifar_path = self.cached_download(CIFAR_URL, "cifar-100-python.tar.gz", md5, CIFAR_MD5)
        return cifar_path

    @cached_property
    def coarse_names(self) -> dict[int, str]:
        """Map CIFAR coarse label IDs to readable names from the official metadata."""
        coarse_names = dict(enumerate(self.read_cifar_member("meta")["coarse_label_names"]))
        coarse_names = {label: name.replace("_", " ") for label, name in coarse_names.items()}
        return coarse_names


def describe_cifar_groups(
    embeddings: CIFAR100Embeddings,
    negative_superclasses: Sequence[int],
    positive_superclasses: Sequence[int],
) -> Markdown:
    """Show the configured binary labels and the official fine categories they contain."""
    fine_names = embeddings.read_cifar_member("meta")["fine_label_names"]
    record = embeddings.read_cifar_member("test")
    fine_ids = np.asarray(record["fine_labels"])
    coarse_ids = np.asarray(record["coarse_labels"])
    rows = [
        "| Binary label | Superclass (ID) | Fine categories |",
        "| --- | --- | --- |",
    ]
    for label, group in ((-1, negative_superclasses), (+1, positive_superclasses)):
        for coarse_id in group:
            categories = ", ".join(
                fine_names[i].replace("_", " ") for i in np.unique(fine_ids[coarse_ids == coarse_id])
            )
            name = embeddings.coarse_names[coarse_id]
            rows.append(f"| {label:+d} | {name} ({coarse_id}) | {categories} |")
    return Markdown("\n".join(rows))


def round_count(n: int, p: float) -> int:
    """Convert a fraction of n into a count by rounding half up."""
    return int(np.floor(n * p + 0.5))


def random_head(d: int, seed: int) -> SelfTrainingInitialization:
    """Draw a reproducible d-dimensional standard Gaussian weight vector with zero bias.

    Use a dedicated generator seeded with seed + 11.
    """
    generator = torch.Generator().manual_seed(seed + 11)
    w0 = torch.randn(d, generator=generator, dtype=torch.float64)
    return SelfTrainingInitialization(0.0, w0)


def classification_error(scores: Tensor, labels: Tensor, p: float) -> float:
    """Compute binary misclassification error under positive-class prior p.

    Weight the negative and positive conditional error rates by 1 - p and p.
    A zero score predicts the positive class.
    """
    mistakes = sign_with_positive_tie(scores) != labels
    return ((1 - p) * mistakes[labels == -1].double().mean()
            + p * mistakes[labels == 1].double().mean()).item()


def calibrate_gaussian(train: Tensor, labels: Tensor) -> tuple[Tensor, Tensor, float]:
    """Fit a two-class isotropic Gaussian model to the embedding rows and true labels.

    Return the midpoint of class means, their half-difference scaled by sqrt(d),
    and a common noise standard deviation. The pooled residual sum of squares
    is divided by d * (n - 2) to account for the two fitted class means.
    """
    n, d = train.shape
    negative, positive = train[labels == -1], train[labels == 1]
    m_minus, m_plus = negative.mean(0), positive.mean(0)
    midpoint = (m_plus + m_minus) / 2
    mu = d**0.5 * (m_plus - m_minus) / 2
    rss = (negative - m_minus).square().sum() + (positive - m_plus).square().sum()
    sigma = float(torch.sqrt(rss / (d * (n - 2))))
    if not np.isfinite(sigma) or sigma <= 0:
        raise ValueError("The fitted isotropic noise scale must be finite and positive.")
    return midpoint, mu, sigma


def evaluation_errors(
    bias: Tensor,
    weight: Tensor,
    real_test_centered: Tensor,
    y_test: Tensor,
    mu: Tensor,
    sigma: float,
    p: float,
) -> dict[str, float]:
    """Evaluate one head on the fitted Gaussian population and real test embeddings.

    The bias and real test features use coordinates centered at the fitted
    midpoint. Both metrics use the target positive-class prior p.
    """
    d = weight.numel()
    return {
        "gaussian_population_error": population_error(
            float(bias), float(mu @ weight / d),
            float(torch.linalg.vector_norm(weight) / d**0.5), sigma, p,
        ),
        "real_test_error": classification_error(
            compute_scores(real_test_centered, bias, weight), y_test, p,
        ),
    }


def selection_diagnostics(scores: Tensor, labels: Tensor, cfg: AlgorithmConfig) -> dict[str, float]:
    """Report selected and incorrectly selected counts as fractions of unlabeled rows."""
    selected = cfg.selection_mask(scores).bool()
    wrong = sign_with_positive_tie(scores) != labels
    return {
        "coverage": selected.double().mean().item(),
        "selected_error_fraction": (selected & wrong).double().mean().item(),
    }


def finite_diagnostics(
    learner: SelfTrainedGradientDescent,
    X: Tensor, X_test: Tensor, y_test: Tensor, hidden: Tensor,
    p: float, origin_shift: Tensor,
    real_test_centered: Tensor, midpoint: Tensor, mu: Tensor, sigma: float,
    checkpoints: Sequence[int],
) -> tuple[list[MetricRow], Checkpoints]:
    """Record native sample metrics and all-row score snapshots for a finite fit.

    X and X_test are in the learner’s coordinates. hidden holds the true labels
    of unrevealed training rows in their original order. origin_shift maps the
    learner’s feature origin into the whitened coordinates, while midpoint is
    the fitted Gaussian center in those coordinates. Coverage is the fraction
    of unrevealed rows selected. Selected error uses that same denominator.
    Stored scores describe states before updates. Recompute scores at state T.
    """
    unlabeled = learner.y_observed_ == 0
    sqrt_d = X.shape[1]**0.5
    biases = [step.bias for step in learner.update_records_] + [learner.bias]
    rows, snapshots = [], {}
    for t, (bias, weight) in enumerate(zip(biases, learner.weight_history_)):
        test_scores = compute_scores(X_test, bias, weight)
        scores = (learner.update_records_[t].scores if t < len(learner.update_records_)
                  else learner.decision_function(X))
        if t in checkpoints:
            snapshots[t] = {"scores": scores.cpu().numpy(), "weights": weight.cpu().numpy()}
        rows.append({
            "iteration": t,
            "test_error": classification_error(test_scores, y_test, p),
            **evaluation_errors(
                bias + (midpoint - origin_shift) @ weight / sqrt_d,
                weight, real_test_centered, y_test, mu, sigma, p,
            ),
            **selection_diagnostics(scores[unlabeled], hidden, learner.cfg),
            "intercept": (bias - origin_shift @ weight / sqrt_d).item(),
            "signal_alignment": float(mu @ weight / weight.numel()),
            "weight_norm": (torch.linalg.vector_norm(weight) / sqrt_d).item(),
        })
    return rows, snapshots


class DINOv2CIFAR100Experiment:
    """Compare CIFAR-100 embeddings with a fitted Gaussian and its effective process."""

    def __init__(
        self, embeddings: CIFAR100Embeddings, *,
        class_proportions: Sequence[float], labeling_rate: float, n_train: int, n_test: int,
        seeds: Sequence[int], training_steps: int, checkpoint_times: Sequence[int], eta: float,
        reg_lambda: float, pi: float, tau: float, negative_superclasses: tuple[int, ...],
        positive_superclasses: tuple[int, ...],
        pilot_holdout_per_class: int, pilot_seed: int,
        whitening_ridge_fraction: float, sample_particles: int, particle_seed: int,
    ) -> None:
        """Configure and validate an experiment without loading its data.

        Set the binary superclass groups, sample and revelation budgets, and
        repetition seeds. eta, reg_lambda, pi, and tau specify step size, penalty,
        pseudo-label weight, and confidence threshold. The holdout size and seed
        define which images are excluded from fitting. Whitening and particle settings
        control the Gaussian comparisons. Call prepare_training_pool() and load_test_embeddings()
        before running the comparisons.
        """
        self.class_proportions = class_proportions
        self.labeling_rate = labeling_rate
        self.n_train = n_train
        self.n_test = n_test
        self.seeds = seeds
        self.training_steps = training_steps
        self.checkpoint_times = checkpoint_times
        self.eta = eta
        self.reg_lambda = reg_lambda
        self.pi = pi
        self.tau = tau
        self.negative_superclasses = negative_superclasses
        self.positive_superclasses = positive_superclasses
        self.pilot_holdout_per_class = pilot_holdout_per_class
        self.pilot_seed = pilot_seed
        self.whitening_ridge_fraction = whitening_ridge_fraction
        self.sample_particles = sample_particles
        self.particle_seed = particle_seed
        self.embeddings = embeddings

        if len(class_proportions) != 2 or not all(0 < p < 1 for p in class_proportions):
            raise ValueError("Provide two positive-class proportions strictly between 0 and 1.")
        if not 0 < labeling_rate < 1 or not 0.5 < tau < 1:
            raise ValueError("Choose a labeling rate in (0, 1) and a confidence threshold in (0.5, 1).")
        if not seeds or any(not isinstance(seed, int) or seed < 0 for seed in seeds):
            raise ValueError("Provide at least one nonnegative integer seed.")
        if any(not isinstance(size, int) or size <= 0
               for size in (n_train, n_test, training_steps, sample_particles, pilot_holdout_per_class)):
            raise ValueError("Sample sizes, training steps, and particle count must be positive integers.")
        if (not np.isfinite([eta, reg_lambda, pi, whitening_ridge_fraction]).all()
                or min(eta, pi, whitening_ridge_fraction) <= 0 or reg_lambda < 0):
            raise ValueError("Choose finite positive eta, pi, whitening ridge fraction, and nonnegative reg_lambda.")

        if (not checkpoint_times
                or any(type(t) is not int or not 0 <= t <= training_steps for t in checkpoint_times)
                or len(set(checkpoint_times)) != len(checkpoint_times)):
            raise ValueError("Choose distinct integer checkpoint times between 0 and training_steps.")

    def sample_binary(
        self,
        pool: EmbeddingPool,
        pair: SuperclassPair,
        size: int,
        p: float,
        rng: np.random.Generator,
    ) -> tuple[Tensor, Tensor, IdArray]:
        """Sample size rows without replacement at target positive fraction p.

        Divide each binary class budget as evenly as possible across its constituent
        superclasses. Return float64 embeddings, labels in {-1, +1}, and source IDs
        under the same random permutation.
        """
        features, coarse, ids = pool
        n_pos = round_count(size, p)
        selected_rows, selected_labels = [], []
        for superclasses, count, label in zip(pair, (size - n_pos, n_pos), (-1, 1)):
            per_class, remainder = divmod(count, len(superclasses))
            for i, superclass in enumerate(superclasses):
                requested = per_class + (i < remainder)
                available = np.flatnonzero(coarse == superclass)
                if not 1 <= requested <= len(available):
                    raise ValueError(
                        f"Superclass {self.coarse_names[superclass]} needs {requested} rows "
                        f"but {len(available)} are available."
                    )
                selected_rows.append(rng.choice(available, size=requested, replace=False))
                selected_labels.append(np.full(requested, label, dtype=np.int64))
        order = rng.permutation(size)
        rows = np.concatenate(selected_rows)[order]
        return (
            torch.as_tensor(features[rows], dtype=torch.float64),
            torch.from_numpy(np.concatenate(selected_labels)[order]),
            ids[rows],
        )

    def reveal_labels(self, labels: Tensor, rng: np.random.Generator) -> Tensor:
        """Reveal the configured fraction of labels while approximately preserving class balance.

        Return a tensor in the original row order with 0 marking unrevealed labels.
        Require both revealed and hidden observations in each binary class.
        """
        n_labeled = round_count(len(labels), self.labeling_rate)
        n_pos = int((labels == 1).sum())
        labeled_pos = (2 * n_labeled * n_pos + len(labels)) // (2 * len(labels))
        observed = torch.zeros_like(labels)
        for label, count in ((-1, n_labeled - labeled_pos), (1, labeled_pos)):
            candidates = np.flatnonzero(labels.numpy() == label)
            if not 0 < count < len(candidates):
                raise ValueError(f"Class {label} needs both revealed and hidden labels.")
            observed[rng.choice(candidates, size=count, replace=False)] = label
        return observed

    def head_config(self, steps: int, pseudo_weight: float) -> AlgorithmConfig:
        """Build the head optimizer configuration for the given update and pseudo-label budgets.

        Convert the confidence threshold tau from probability to logit units.
        """
        return AlgorithmConfig(
            n_iterations=steps, step_size=self.eta, penalty_param=self.reg_lambda,
            pseudo_label_param=pseudo_weight, margin_threshold=float(np.log(self.tau / (1 - self.tau))),
        )

    def compare_dinov2_cifar100(
        self,
        p: float,
        seed: int,
        steps: int,
        *,
        checkpoints: Sequence[int]=(),
    ) -> ComparisonRun:
        """Run one seeded comparison at positive proportion p for the given update count.

        Use matched data budgets and initial weights for real self-training, finite
        Gaussian self-training, and state evolution.
        Fit the Gaussian from the preprocessed training embeddings. Report trajectories
        including initialization and optional score and weight snapshots at checkpoints.
        Evaluate selection both on each method's native sample and on shared CIFAR rows.
        The oracle whitening transform uses true training and test class labels.
        """
        rng = np.random.default_rng(seed)
        X, labels, training_ids = self.sample_binary(self.available_train, self.chosen_pair, self.n_train, p, rng)
        X_test, y_test, evaluation_ids = self.sample_binary(self.test_pool, self.chosen_pair, self.n_test, p, rng)
        assert len(np.unique(training_ids)) == self.n_train
        assert len(np.unique(evaluation_ids)) == self.n_test
        assert not np.intersect1d(training_ids, self.pilot_ids).size
        assert not np.intersect1d(training_ids, evaluation_ids).size
        assert not np.intersect1d(self.pilot_ids, evaluation_ids).size

        observed = self.reveal_labels(labels, rng)
        labeled = observed != 0
        hidden = labels[~labeled]
        X, X_test, ridge = self.whiten_embeddings_by_class(X, labels, X_test, y_test)
        n, d = X.shape
        assert d == 768
        initialization = random_head(d, seed)
        w0 = initialization.w_init
        cfg = self.head_config(steps, self.pi)
        midpoint, mu, sigma = calibrate_gaussian(X, labels)
        real_train_centered = X - midpoint
        real_test_centered = X_test - midpoint
        learner = SelfTrainedGradientDescent(cfg).fit(X, observed, initialization)
        assert torch.equal(learner.y_observed_, observed)
        torch.testing.assert_close(learner.weight_history_[0], w0)
        real, real_snapshots = finite_diagnostics(
            learner, X, X_test, y_test, hidden, p, torch.zeros_like(w0),
            real_test_centered, midpoint, mu, sigma, checkpoints,
        )

        sqrt_d = d**0.5
        bias_shift = float(midpoint @ w0 / sqrt_d)
        # Re-centering the features changes the intercept needed to preserve initial scores.
        gaussian_init = SelfTrainingInitialization(bias_shift, w0)
        torch.testing.assert_close(
            compute_scores(X, initialization.b_init, w0),
            compute_scores(real_train_centered, gaussian_init.b_init, w0),
        )
        population = DataConfig(
            scale=sigma, label_prior=p, supervision_ratio=float(labeled.double().mean()),
            data_to_dimension_ratio=n / d, signal_law=lambda: 0.0,
        )  # The joint parameter sampler supplies the fitted signal.
        train_environment = QuenchedEnvironment(mu, labels, labeled)
        gaussian = IsotropicGaussian(
            cfg=population, n_train=n, dimensions=d, seed=seed + 23, environment=train_environment,
        )
        test_environment = QuenchedEnvironment(mu, y_test, torch.zeros_like(y_test))
        X_gaussian, _ = gaussian.sample_design(train_environment)
        X_gaussian_test, _ = gaussian.sample_design(test_environment)
        gaussian_head = SelfTrainedGradientDescent(cfg).fit(X_gaussian, observed, gaussian_init)
        finite, finite_snapshots = finite_diagnostics(
            gaussian_head, X_gaussian, X_gaussian_test, y_test, hidden, p, midpoint,
            real_test_centered, midpoint, mu, sigma, checkpoints,
        )

        # Place equally spaced midpoints in the empirical law of (label, revelation).
        types = 2 * labeled.to(torch.int64) + (labels == 1).to(torch.int64)
        grid = ((2 * torch.arange(self.sample_particles) + 1) * n) // (2 * self.sample_particles)
        idx = torch.argsort(types)[grid]
        if not torch.equal(torch.unique(types[idx]), torch.unique(types)):
            raise ValueError("Increase sample_particles so every present label/revelation type is represented.")
        if self.sample_particles % n == 0:
            assert torch.equal(torch.bincount(types[idx]), torch.bincount(types) * (self.sample_particles // n))

        def parameter_base(
            count: int,
            generator: torch.Generator,
            dtype: torch.dtype,
            device: torch.device,
        ) -> tuple[Tensor, Tensor]:
            """Supply the fitted signal and initial weights in the process dtype and device."""
            return mu.to(device=device, dtype=dtype), w0.to(device=device, dtype=dtype)

        def sample_base(
            count: int,
            generator: torch.Generator,
            dtype: torch.dtype,
            device: torch.device,
        ) -> tuple[Tensor, Tensor, None]:
            """Supply paired labels and revelation indicators without initial pseudo-labels."""
            return (labels[idx].to(device=device, dtype=dtype),
                    labeled[idx].to(device=device, dtype=dtype), None)

        process = MacroscopicStateEvolution(
            data_cfg=population, algo_cfg=cfg, initial_bias=bias_shift,
            K_w=d, K_g=self.sample_particles, mc_seed=self.particle_seed + seed,
            parameter_base_sampler=parameter_base, sample_base_sampler=sample_base,
        )
        process.compute_trajectory()
        assert gaussian.cfg is process.data_cfg and gaussian_head.cfg is process.algo_cfg
        assert process.sigma == gaussian.cfg.scale
        torch.testing.assert_close(process.signal, train_environment.mu)
        torch.testing.assert_close(process.initial_bias, gaussian_head.update_records_[0].bias)
        torch.testing.assert_close(process.initial_weight, gaussian_head.weight_history_[0])
        unlabeled_particles = process.indicator == 0
        particle_labels = process.label[unlabeled_particles]
        effective = []
        for t, scores in enumerate(process.preactivation):
            effective.append({
                "iteration": t,
                "test_error": float(process.error[t]),
                **evaluation_errors(
                    process.bias[t], process.weight[t], real_test_centered, y_test, mu, sigma, p,
                ),
                **selection_diagnostics(scores[unlabeled_particles], particle_labels, cfg),
                "intercept": (process.bias[t] - midpoint @ process.weight[t] / sqrt_d).item(),
                "signal_alignment": process.weight_signal_alignments[t].item(),
                "weight_norm": float(process.weight_norm[t]),
            })

        effective_snapshots = {
            t: {
                "scores": process.preactivation[t].cpu().numpy(),
                "weights": process.weight[t].cpu().numpy(),
            }
            for t in checkpoints
        }
        for row in real:
            row["cifar_coverage"] = row["coverage"]
            row["cifar_selected_error_fraction"] = row["selected_error_fraction"]

        # Apply both Gaussian-derived head trajectories to the same real rows.
        # Their biases are in coordinates centered at the fitted Gaussian midpoint.
        gaussian_biases = [step.bias for step in gaussian_head.update_records_] + [gaussian_head.bias]
        for rows, snapshots, weights, biases in (
            (finite, finite_snapshots, gaussian_head.weight_history_, gaussian_biases),
            (effective, effective_snapshots, process.weight, process.bias),
        ):
            scores_by_state = (
                torch.stack(weights) @ real_train_centered.T / sqrt_d + torch.stack(biases)[:, None]
            )
            for t, (row, scores) in enumerate(zip(rows, scores_by_state)):
                metrics = selection_diagnostics(scores[~labeled], hidden, cfg)
                row.update({f"cifar_{name}": value for name, value in metrics.items()})
                if t in snapshots:
                    snapshots[t]["cifar_scores"] = scores.cpu().numpy().copy()

        trajectories = {"real_self_training": real, "finite_gaussian": finite, "effective_process": effective}
        for rows in trajectories.values():
            assert [row["iteration"] for row in rows] == list(range(steps + 1))
            assert np.isclose(rows[0]["intercept"], 0)
            assert np.isclose(rows[0]["weight_norm"], real[0]["weight_norm"])
            assert all(np.isfinite(list(row.values())).all() for row in rows)
            assert all(0 <= row["selected_error_fraction"] <= row["coverage"] <= 1 for row in rows)
            assert all(0 <= row["cifar_selected_error_fraction"] <= row["cifar_coverage"] <= 1 for row in rows)
        return {
            "p": p, "seed": seed, "n": n, "d": d,
            "class_counts": (int((labels == -1).sum()), int((labels == 1).sum())),
            "revealed_counts": (int((observed == -1).sum()), int((observed == 1).sum())),
            "sigma": sigma, "signal_energy": mu.square().mean().item(),
            "whitening_ridge": ridge, "midpoint_bias_shift": bias_shift,
            "trajectories": trajectories,
            "distribution_snapshots": {
                "real": real_snapshots,
                "finite_gaussian": finite_snapshots,
                "effective": effective_snapshots,
            },
        }

    def whiten_embeddings_by_class(
        self,
        train: Tensor,
        labels: Tensor,
        evaluation: Tensor,
        evaluation_labels: Tensor,
    ) -> tuple[Tensor, Tensor, float]:
        """Whiten within-class residuals while preserving the centered, pooled-whitened means.

        Fit all means and covariances on training data, then apply the appropriate
        transform according to each evaluation row’s true label. This is an oracle
        comparison. Return the transformed features and the shared ridge.
        """
        groups = [train[labels == y] for y in (-1, 1)]
        if any(len(group) < 2 for group in groups):
            raise ValueError("Class-specific whitening requires at least two training rows per class.")
        means = [group.mean(dim=0) for group in groups]
        midpoint = (means[0] + means[1]) / 2
        residuals = [group - mean for group, mean in zip(groups, means)]
        scatters = [group.T @ group for group in residuals]
        pooled_covariance = (scatters[0] + scatters[1]) / (len(train) - 2)
        eigenvalues, eigenvectors = torch.linalg.eigh(pooled_covariance)
        eigenvalues = eigenvalues.clamp_min(0)
        ridge = float(self.whitening_ridge_fraction * eigenvalues.mean())
        if not np.isfinite(ridge) or ridge <= 0:
            raise ValueError("The pooled within-class covariance must have positive finite trace.")
        pooled_whitener = (eigenvectors * (eigenvalues + ridge).rsqrt()) @ eigenvectors.T

        train_whitened, evaluation_whitened = torch.empty_like(train), torch.empty_like(evaluation)
        for y, mean, residual, scatter in zip((-1, 1), means, residuals, scatters):
            covariance = scatter / (len(residual) - 1)
            eigenvalues, eigenvectors = torch.linalg.eigh(covariance)
            eigenvalues = eigenvalues.clamp_min(0)
            whitener = (eigenvectors * (eigenvalues + ridge).rsqrt()) @ eigenvectors.T
            target_mean = (mean - midpoint) @ pooled_whitener
            train_mask, evaluation_mask = labels == y, evaluation_labels == y
            transformed = residual @ whitener + target_mean
            train_whitened[train_mask] = transformed
            evaluation_whitened[evaluation_mask] = (evaluation[evaluation_mask] - mean) @ whitener + target_mean

            torch.testing.assert_close(transformed.mean(dim=0), target_mean)
        return train_whitened, evaluation_whitened, ridge

    def prepare_training_pool(self) -> None:
        """Load selected superclasses and exclude the original seeded holdout.

        Preserve the original training pool and its row order for reproducibility.
        """
        chosen_pair = (self.negative_superclasses, self.positive_superclasses)
        candidate_labels = sorted(set(self.negative_superclasses + self.positive_superclasses))
        if (not all(chosen_pair)
                or len(candidate_labels) != len(self.negative_superclasses) + len(self.positive_superclasses)):
            raise ValueError("Provide two nonempty, disjoint superclass groups without duplicates.")
        self.coarse_names = self.embeddings.coarse_names
        train_embeddings, train_coarse, train_ids = self.embeddings.load_embeddings("train", candidate_labels)

        pilot_rng = np.random.default_rng(self.pilot_seed)
        pilot_ids = np.concatenate([
            pilot_rng.choice(train_ids[train_coarse == label], self.pilot_holdout_per_class, replace=False)
            for label in candidate_labels
        ])
        is_pilot = np.isin(train_ids, pilot_ids)
        available_train = (train_embeddings[~is_pilot], train_coarse[~is_pilot], train_ids[~is_pilot])
        self.chosen_pair = chosen_pair
        self.candidate_labels = candidate_labels
        self.available_train = available_train
        self.pilot_ids = pilot_ids

    def load_test_embeddings(self) -> None:
        """Load the chosen superclasses from the official test split after preparing the training pool."""
        self.test_pool = self.embeddings.load_embeddings("test", self.candidate_labels)

    def run_class_whitening(self) -> list[list[ComparisonRun]]:
        """Run one oracle-whitened comparison per proportion and seed.

        The outer list follows class_proportions. Each inner list follows seeds.
        """
        return [
            [
                self.compare_dinov2_cifar100(
                    p, seed, self.training_steps, checkpoints=self.checkpoint_times,
                )
                for seed in self.seeds
            ]
            for p in self.class_proportions
        ]


_DINO_METHODS = (
    ("real_self_training", "DINOv2 embedding ST", "tab:blue"),
    ("finite_gaussian", "Fitted Gaussian ST", "tab:green"),
    ("effective_process", "Effective process", "tab:orange"),
)
_SELECTION_FIELDS = {"unl_usage": "coverage", "unl_selected_error": "selected_error_fraction"}
_CIFAR_SELECTION_FIELDS = {metric: f"cifar_{field}" for metric, field in _SELECTION_FIELDS.items()}


def _trajectory_values(
    runs: Sequence[ComparisonRun], method: str, fields: dict[str, str],
) -> dict[str, list[list[float]]]:
    """Extract one scalar trajectory per seed for each requested plot metric."""
    return {
        metric: [[row[field] for row in run["trajectories"][method]] for run in runs]
        for metric, field in fields.items()
    }


def _trajectory_iterations(runs: Sequence[ComparisonRun]) -> list[float]:
    """Return the common state indices for all methods and seeds."""
    return [row["iteration"] for row in runs[0]["trajectories"]["real_self_training"]]


def plot_dinov2_cifar100_trajectories(
    runs: Sequence[ComparisonRun],
    *,
    manuscript: bool = False,
    legend_font_size: float | None = None,
) -> Figure:
    """Plot six dynamics metrics, with all sample-side evaluations on CIFAR."""
    fields = {
        "test_error": "real_test_error",
        **_CIFAR_SELECTION_FIELDS,
        "bias_term": "intercept",
        "weight_signal_alignment": "signal_alignment",
        "weight_vector_norm": "weight_norm",
    }
    results = {
        "iterations": _trajectory_iterations(runs),
        **{method: _trajectory_values(runs, method, fields) for method, _, _ in _DINO_METHODS},
    }
    paper_style = {
        key: plt.rcParamsDefault[key]
        for key in ("axes.spines.top", "axes.spines.right", "figure.dpi")
    }
    with plt.rc_context(paper_style):
        fig, _ = plot_trajectory_comparison(
            results, list(fields), _DINO_METHODS, manuscript=manuscript,
            legend_font_size=legend_font_size,
        )
    return fig


def plot_dinov2_cifar100_selection(
    runs: Sequence[ComparisonRun], *, manuscript: bool = False,
) -> Figure:
    """Plot mean, median, and IQR of paired native-minus-DINOv2 differences."""
    cifar_fields = {"test_error": "real_test_error", **_CIFAR_SELECTION_FIELDS}
    native_fields = {"test_error": "gaussian_population_error", **_SELECTION_FIELDS}
    baseline = _trajectory_values(runs, "real_self_training", cifar_fields)
    methods = _DINO_METHODS[1:]
    results = {"iterations": _trajectory_iterations(runs)}
    for method, _, _ in methods:
        native = _trajectory_values(runs, method, native_fields)
        results[method] = {
            metric: np.asarray(values) - np.asarray(baseline[metric])
            for metric, values in native.items()
        }
    fig, axes = plot_trajectory_comparison(
        results, list(cifar_fields), methods, manuscript=manuscript,
    )
    axes[0, 0].set_ylabel("Native minus DINOv2")
    for ax in axes.flat:
        ax.axhline(0, color="0.45", linestyle=":", linewidth=1, zorder=1)
    return fig


def save_dinov2_cifar100_figures(
    figures_dir: Path,
    runs_by_scenario: Sequence[Sequence[ComparisonRun]],
    filename_prefix: str = "dinov2_cifar100_mammal_groups",
) -> None:
    """Save and display a trajectory and a selection diagnostic PDF per proportion."""
    for plot, suffix in (
        (plot_dinov2_cifar100_trajectories, ""),
        (plot_dinov2_cifar100_selection, "_selection_evaluation"),
    ):
        for runs in runs_by_scenario:
            figure_path = figures_dir / f"{filename_prefix}{suffix}_p{runs[0]['p']:g}.pdf"
            fig = plot(runs, manuscript=True)
            save_figure(fig, figure_path, pad_inches=0.1)
            plt.show()


def save_checkpoint_distributions(
    figures_dir: Path,
    runs_by_scenario: Sequence[Sequence[ComparisonRun]],
    checkpoints: Sequence[int],
    *,
    score_thresholds: Sequence[float],
) -> None:
    """Save a combined score and weight density figure per class proportion."""
    figures_dir.mkdir(parents=True, exist_ok=True)
    for runs in runs_by_scenario:
        rows = []
        for observable, xlabel in (
            ("scores", f"Training score $r^t_i$"), ("weights", f"Weight coordinate $w^t_k$"),
        ):
            thresholds = score_thresholds if observable == "scores" else ()
            samples = {
                t: (
                    np.concatenate([run["distribution_snapshots"]["real"][t][observable] for run in runs]),
                    np.concatenate([run["distribution_snapshots"]["effective"][t][observable] for run in runs]),
                )
                for t in checkpoints
            }
            rows.append((samples, xlabel, thresholds))
        fig = plot_checkpoint_distributions(
            rows, manuscript=True, labels=(_DINO_METHODS[0][1], _DINO_METHODS[2][1]),
        )
        filename = f"dinov2_cifar100_mammal_groups_class_whitened_checkpoint_distributions_p{runs[0]['p']:g}.pdf"
        save_figure(fig, figures_dir / filename)
        plt.show()
