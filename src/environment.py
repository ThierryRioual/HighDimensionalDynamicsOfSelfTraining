"""Quenched finite-dimensional environments and sample-type laws.

The finite mathematical model conditions on a realised triple
``(mu, Y, Delta)``.  Feature noise is deliberately absent from this object and
is generated conditionally by :mod:`src.dgp`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import torch


def _frozen_vector(name: str, value: torch.Tensor, *, dtype: torch.dtype | None = None) -> torch.Tensor:
    tensor = torch.as_tensor(value, dtype=dtype if dtype is not None else None).detach().clone()
    if tensor.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional, got {tuple(tensor.shape)}")
    if not torch.isfinite(tensor).all():
        raise ValueError(f"{name} must be finite")
    return tensor


@dataclass(frozen=True)
class QuenchedEnvironment:
    """Validated realised finite environment ``(mu, Y, Delta)``.

    Inputs are cloned and fields cannot be rebound. Tensor contents are treated
    as read-only by convention; a frozen dataclass does not freeze tensor data.
    ``I_L`` and ``I_U`` are derived properties, never independent mutable state.
    """

    mu: torch.Tensor
    Y: torch.Tensor
    Delta: torch.Tensor

    def __post_init__(self) -> None:
        mu = _frozen_vector("mu", self.mu, dtype=torch.float64)
        Y = _frozen_vector("Y", self.Y, dtype=torch.float64)
        Delta = _frozen_vector("Delta", self.Delta, dtype=torch.float64)
        if mu.numel() == 0:
            raise ValueError("the signal dimension must be positive")
        if Y.shape != Delta.shape:
            raise ValueError("Y and Delta must have the same shape")
        if Y.device != mu.device or Delta.device != mu.device:
            raise ValueError("mu, Y, and Delta must share a device")
        if not torch.all((Y == -1) | (Y == 1)):
            raise ValueError("Y entries must belong to {-1, +1}")
        if not torch.all((Delta == 0) | (Delta == 1)):
            raise ValueError("Delta entries must belong to {0, 1}")
        if Y.numel() == 0:
            raise ValueError("the environment must contain at least one sample")
        object.__setattr__(self, "mu", mu)
        object.__setattr__(self, "Y", Y)
        object.__setattr__(self, "Delta", Delta)

    @property
    def d(self) -> int:
        return int(self.mu.numel())

    @property
    def n(self) -> int:
        return int(self.Y.numel())

    @property
    def delta(self) -> float:
        return self.n / self.d

    @property
    def I_L(self) -> torch.Tensor:
        return torch.nonzero(self.Delta == 1, as_tuple=False).reshape(-1)

    @property
    def I_U(self) -> torch.Tensor:
        return torch.nonzero(self.Delta == 0, as_tuple=False).reshape(-1)

    @property
    def N(self) -> int:
        return int(self.I_L.numel())

    @property
    def M(self) -> int:
        return int(self.I_U.numel())

    @property
    def rho(self) -> float:
        return self.N / self.n


class SampleTypeLaw(Protocol):
    """Law for the joint sample type ``(Y, Delta)``."""

    def sample(self, n: int, *, generator: torch.Generator, dtype: torch.dtype, device: torch.device) -> tuple[torch.Tensor, torch.Tensor]: ...

    @property
    def label_prior(self) -> float: ...


@dataclass(frozen=True)
class FourCellSampleTypeLaw:
    """Categorical law for ``(Y, Delta)`` in order ``(+1,1),(+1,0),(-1,1),(-1,0)``."""

    probabilities: tuple[float, float, float, float]

    def __post_init__(self) -> None:
        probs = tuple(float(x) for x in self.probabilities)
        if any(x < 0 for x in probs) or not abs(sum(probs) - 1.0) <= 1e-12:
            raise ValueError("four-cell probabilities must be nonnegative and sum to one")
        object.__setattr__(self, "probabilities", probs)

    @classmethod
    def product(cls, *, label_prior: float, supervision_ratio: float) -> "FourCellSampleTypeLaw":
        p, rho = float(label_prior), float(supervision_ratio)
        return cls((p * rho, p * (1 - rho), (1 - p) * rho, (1 - p) * (1 - rho)))

    @property
    def label_prior(self) -> float:
        return self.probabilities[0] + self.probabilities[1]

    @property
    def supervision_ratio(self) -> float:
        return self.probabilities[0] + self.probabilities[2]

    def sample(self, n: int, *, generator: torch.Generator, dtype: torch.dtype, device: torch.device) -> tuple[torch.Tensor, torch.Tensor]:
        if n <= 0:
            raise ValueError("n must be positive")
        probs = torch.tensor(self.probabilities, dtype=dtype, device=device)
        category = torch.multinomial(probs, n, replacement=True, generator=generator)
        Y = torch.where(category < 2, 1.0, -1.0).to(dtype=dtype)
        Delta = torch.where((category == 0) | (category == 2), 1.0, 0.0).to(dtype=dtype)
        return Y, Delta


def state_evolution_sample_base_sampler(
    law: SampleTypeLaw,
    initial_label_sampler=None,
):
    """Adapt a joint sample-type law to ``MacroscopicStateEvolution``'s sampler.

    ``initial_label_sampler`` receives ``(Y, Delta, generator)`` and must
    return a full ``Y_init`` vector to override the first-step pseudo-labels.
    By default, return None so the process uses its own initial score signs.
    """

    def sampler(K: int, generator: torch.Generator, dtype: torch.dtype, device: torch.device):
        Y, Delta = law.sample(K, generator=generator, dtype=dtype, device=device)
        Y_init = None
        if initial_label_sampler is not None:
            Y_init = torch.as_tensor(initial_label_sampler(Y, Delta, generator), dtype=dtype, device=device).clone()
            Y_init[Delta == 1] = Y[Delta == 1]
        return Y, Delta, Y_init

    return sampler
