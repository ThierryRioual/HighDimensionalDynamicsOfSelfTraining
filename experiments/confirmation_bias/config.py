"""Small named configurations; the pilot retains Notebook 14's raw thresholds.

The only objective-normalization change from the legacy default is explicit:
``normalize_unlabeled_loss=False`` divides by the fixed pool size M, including
when no observations are selected. Population priors are varied only in the
prescribed paired comparison; no outcome-dependent tuning is performed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import math

from src.config import AlgorithmConfig


@dataclass(frozen=True)
class SuiteConfig:
    d: int = 3000
    n_labeled: int = 240
    n_unlabeled: int = 23760
    T: int = 200
    p_c: float = 0.2
    sigma: float = 1.0
    signal_std: float = 1.0
    eta: float = 0.5
    penalty: float = 0.1
    pi: float = 2.0
    kappa_minus: float = -math.log(4.0)
    kappa_plus: float = math.log(4.0)
    seeds: tuple[int, ...] = (49, 50, 51)
    profile: str = "pilot"
    solver_gtol: float = 1e-8
    solver_ftol: float = 1e-15
    solver_maxiter: int = 1500
    solver_maxls: int = 40
    solver_residual_tolerance: float = 1e-6
    consistency_tolerance: float = 1e-7
    deterioration_tolerance: float = 1e-8
    replay_tolerance: float = 1e-10

    def __post_init__(self):
        if self.d < 1 or self.n_labeled < 2 or self.n_unlabeled < 1 or self.T < 2:
            raise ValueError("require d>=1, N>=2, M>=1 and T>=2")
        if not 0 < self.p_c < 0.5:
            raise ValueError("p_c must be a negative-majority prior in (0,1/2)")
        if not self.kappa_minus < 0 < self.kappa_plus:
            raise ValueError("require kappa_minus < 0 < kappa_plus")
        for name in ("sigma", "eta", "solver_gtol", "solver_ftol", "solver_residual_tolerance", "consistency_tolerance", "deterioration_tolerance", "replay_tolerance"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
        for name in ("signal_std", "penalty", "pi"):
            value = getattr(self, name)
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and nonnegative")
        if self.solver_maxiter < 1 or self.solver_maxls < 1:
            raise ValueError("solver iteration limits must be positive")
        if not self.seeds or len(set(self.seeds)) != len(self.seeds):
            raise ValueError("seeds must be nonempty and distinct")

    @property
    def imbalance_levels(self) -> tuple[float, float, float]:
        return (0.5, (0.5 + self.p_c) / 2.0, self.p_c)

    @property
    def n(self) -> int:
        return self.n_labeled + self.n_unlabeled

    def algorithm_config(self, T: int | None = None) -> AlgorithmConfig:
        return AlgorithmConfig(
            n_iterations=self.T if T is None else T,
            step_size=self.eta,
            penalty_param=self.penalty,
            pseudo_label_param=self.pi,
            negative_margin=self.kappa_minus,
            positive_margin=self.kappa_plus,
            include_bias=True,
            initial_bias=0.0,
            normalized_threshold=False,
            normalize_unlabeled_loss=False,
        )

    def to_dict(self) -> dict:
        return asdict(self)

RHO = 0.02
DELTA = 8.0
D = 2_000
TOTAL = round(DELTA * D)
N = round(TOTAL * RHO)
M = TOTAL - N
T = 300

def preset(profile: str = "pilot") -> SuiteConfig:
    """Return smoke, three-seed pilot, or ten-seed expanded configuration."""
    cfg = SuiteConfig(profile=profile)
    if profile == "smoke":
        return replace(cfg, d=D, n_labeled=N, n_unlabeled=M, T=T, seeds=(49,))
    if profile == "pilot":
        return cfg
    if profile == "expanded":
        return replace(cfg, seeds=tuple(range(49, 59)))
    raise ValueError(f"unknown profile {profile!r}; choose smoke, pilot, expanded")
