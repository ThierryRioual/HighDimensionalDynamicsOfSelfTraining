"""Paired Gaussian designs with nested prescribed-count class assignments.

This deliberately uses stratified, prescribed counts instead of the legacy
iid four-cell sample law. Noise, membership, ranks and initialization randomness
are paired across population priors; changed labels always reconstruct X.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

import numpy as np
import torch

from src.config import DataConfig
from src.dgp import IsotropicGaussian
from src.environment import QuenchedEnvironment
from src.initialization import SelfTrainingInitialization

from .config import SuiteConfig


def _hash(tensor: torch.Tensor) -> str:
    return hashlib.sha256(memoryview(tensor.detach().cpu().contiguous().numpy())).hexdigest()


@dataclass
class PairedDataset:
    X: torch.Tensor
    environment: QuenchedEnvironment
    initialization: SelfTrainingInitialization
    metadata: dict
    p: float


@dataclass
class PairedBase:
    config: SuiteConfig
    seed: int
    mu: torch.Tensor
    U: torch.Tensor
    Delta: torch.Tensor
    ranks: torch.Tensor
    Y_init: torch.Tensor
    w_init: torch.Tensor
    metadata: dict
    b_init: float = 0.0

    def dataset(self, p: float) -> PairedDataset:
        """Construct a dataset while retaining the same latent pairing objects.

        Within each subset the smallest ranks receive +1. Counts use Python's
        round-to-nearest (ties to even); labeled counts are clipped to [1,N-1].
        Thus both labeled classes are represented, and assignments are nested.
        """
        if not 0 < p < 1:
            raise ValueError("population p must lie in (0,1)")
        cfg = self.config
        Y = torch.full((cfg.n,), -1.0, dtype=torch.float64)
        counts = {}
        for name, mask, count in (("labeled", self.Delta == 1, cfg.n_labeled), ("unlabeled", self.Delta == 0, cfg.n_unlabeled)):
            indices = torch.nonzero(mask, as_tuple=False).flatten()
            positive_count = round(p * count)
            if name == "labeled":
                positive_count = min(count - 1, max(1, positive_count))
            order = indices[torch.argsort(self.ranks[indices], stable=True)]
            Y[order[:positive_count]] = 1.0
            counts[name] = {"positive": positive_count, "negative": count - positive_count, "positive_fraction": positive_count / count}
        env = QuenchedEnvironment(self.mu, Y, self.Delta)
        dgp = IsotropicGaussian(
            cfg=DataConfig(cfg.sigma, p, cfg.n_labeled / cfg.n, cfg.n / cfg.d, lambda: 0.0),
            n_train=cfg.n, n_test=0, dimensions=cfg.d,
            seed=self.seed + 23, signal_vector=self.mu, environment=env,
        )
        X, _ = dgp.sample_design(env, noise=self.U)
        y_init = self.Y_init.clone()
        y_init[env.I_L] = env.Y[env.I_L]
        initialization = SelfTrainingInitialization(self.b_init, self.w_init.clone(), y_init).for_environment(env)
        metadata = {
            **self.metadata,
            "population_p": p,
            "realized_labeled_p": counts["labeled"]["positive_fraction"],
            "realized_unlabeled_p": counts["unlabeled"]["positive_fraction"],
            "class_counts": counts,
            "label_sha256": _hash(Y),
            "initial_label_sha256": _hash(y_init),
            "count_rounding": "round to nearest, ties to even; labeled count clipped to [1,N-1]",
        }
        return PairedDataset(X, env, initialization, metadata, float(p))


def make_paired_base(config: SuiteConfig, seed: int) -> PairedBase:
    """Use independent local generators; leave global RNG state untouched."""
    # Namespace new random streams by (replicate seed, suite tag, stream tag).
    # Small additive offsets would otherwise collide across expanded replicates
    # (e.g. one seed's noise stream with another seed's initial-label stream).
    # Preserve the legacy parameter/initial-label streams exactly; their ranges
    # do not overlap in the supplied 49..58 expanded configuration.
    def namespaced_seed(tag):
        sequence = np.random.SeedSequence([seed, 0x43424941, tag])
        return int(sequence.generate_state(1, dtype=np.uint64)[0]) | (1 << 63)

    streams = {
        "signal_and_weights": seed + 11,
        "noise": namespaced_seed(23),
        "initial_labels": seed + 31,
        "membership": namespaced_seed(101),
        "class_ranks": namespaced_seed(103),
    }
    generator = lambda name: torch.Generator().manual_seed(streams[name])
    parameter_rng = generator("signal_and_weights")
    mu = config.signal_std * torch.randn(config.d, generator=parameter_rng, dtype=torch.float64)
    w_init = torch.randn(config.d, generator=parameter_rng, dtype=torch.float64)
    U = torch.randn((config.n, config.d), generator=generator("noise"), dtype=torch.float64)
    Delta = torch.zeros(config.n, dtype=torch.float64)
    Delta[torch.randperm(config.n, generator=generator("membership"))[:config.n_labeled]] = 1.0
    ranks = torch.rand(config.n, generator=generator("class_ranks"), dtype=torch.float64)
    Y_init = torch.where(torch.rand(config.n, generator=generator("initial_labels"), dtype=torch.float64) < 0.5, 1.0, -1.0)
    metadata = {
        "seed": seed,
        "streams": streams,
        "stream_recipe": "signal_and_weights=seed+11; initial_labels=seed+31; other seeds=uint64(SeedSequence([seed,0x43424941,tag]).generate_state(1)) | 2**63; tags noise=23,membership=101,class_ranks=103",
        "pairing": "shared mu,U,Delta,class ranks,w_init,and exogenous unlabeled Y_init",
        "sampling": "prescribed counts with nested rank assignment in each subset",
        "initialization": "b=0, iid N(0,1) w independent of mu; exogenous iid Rademacher Y_init on unlabeled coordinates; engine special t=0 step",
        "hashes": {name: _hash(value) for name, value in (("mu", mu), ("U", U), ("Delta", Delta), ("ranks", ranks), ("w_init", w_init), ("exogenous_labels", Y_init))},
    }
    return PairedBase(config, seed, mu, U, Delta, ranks, Y_init, w_init, metadata)
