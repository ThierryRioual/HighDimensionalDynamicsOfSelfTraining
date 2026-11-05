import torch
torch.set_default_dtype(torch.float64)

import math
from dataclasses import dataclass, field
from typing import Callable, Optional

from src.objectives import (
    LossFunction, Penalty, LogisticLoss, RidgePenalty, HardSelection
)


@dataclass(frozen=True)
class DataConfig:
    """
    Population-level data generating process parameters.
    These define the macroscopic quantities that characterize the data distribution
    in the high-dimensional limit — the 'Laws of the Universe'.
    """
    scale: float                        # noise scale (σ)
    label_prior: float                  # class balance
    supervision_ratio: float            # probability a sample's label is observed ρ 
    data_to_dimension_ratio: float      # δ = n/d
    signal_law: Callable[[], float]   # distribution of signal vector entries

    def __post_init__(self):
        """Validates population-level parameters."""
        if not (0 < self.supervision_ratio <= 1):
            raise ValueError(
                f"supervision_ratio must be in (0, 1], got {self.supervision_ratio}"
            )
        if not (0 < self.label_prior < 1):
            raise ValueError(
                f"label_prior must be in (0, 1), got {self.label_prior}"
            )
        if self.data_to_dimension_ratio <= 0:
            raise ValueError(
                f"data_to_dimension_ratio must be positive, got {self.data_to_dimension_ratio}"
            )


@dataclass(frozen=True)
class AlgorithmConfig:
    """Fixed pseudo-label coefficients and independent gradient-descent rates."""

    n_iterations: int
    step_size: float
    penalty_param: float
    pseudo_label_param: float
    margin_threshold: Optional[float] = None
    positive_margin: Optional[float] = None
    negative_margin: Optional[float] = None
    train_bias: bool = True
    loss_function: LossFunction = field(default_factory=LogisticLoss)
    penalty_function: Penalty = field(default_factory=RidgePenalty)
    initial_bias: float = 0.0
    bias_step_size: Optional[float] = None
    bias_pseudo_label_param: Optional[float] = None

    def __post_init__(self):
        if self.n_iterations < 0:
            raise ValueError("n_iterations must be nonnegative")
        if not math.isfinite(float(self.step_size)) or self.step_size <= 0:
            raise ValueError("step_size must be finite and positive")
        if self.bias_step_size is not None and (
            not math.isfinite(float(self.bias_step_size)) or self.bias_step_size < 0
        ):
            raise ValueError("bias_step_size must be finite and nonnegative")
        if not isinstance(self.train_bias, bool):
            raise TypeError("train_bias must be a bool")
        if self.penalty_param < 0:
            raise ValueError("penalty_param must be nonnegative")
        if self.pseudo_label_param < 0:
            raise ValueError("pseudo_label_param must be nonnegative")
        if not math.isfinite(float(self.initial_bias)):
            raise ValueError("initial_bias must be finite")
        if self.bias_pseudo_label_param is not None and (
            not math.isfinite(float(self.bias_pseudo_label_param))
            or self.bias_pseudo_label_param < 0
        ):
            raise ValueError("bias_pseudo_label_param must be finite and nonnegative")

        if self.margin_threshold is not None:
            if self.positive_margin is None:
                object.__setattr__(self, "positive_margin", self.margin_threshold)
            if self.negative_margin is None:
                object.__setattr__(self, "negative_margin", -self.margin_threshold)
        if self.positive_margin is None or self.negative_margin is None:
            raise ValueError(
                "must specify either margin_threshold, or both positive_margin and negative_margin"
            )
        if not (self.negative_margin < 0 < self.positive_margin):
            # Preserve the existing all-selected, zero-threshold experiment.
            if not (self.negative_margin == 0.0 and self.positive_margin == 0.0):
                raise ValueError("require negative_margin < 0 < positive_margin")

    def selection_mask(self, scores: torch.Tensor) -> torch.Tensor:
        """Select raw scores at or beyond either confidence margin."""
        return HardSelection()(scores, self.positive_margin, self.negative_margin)

    def get_bias_step_size(self) -> float:
        """Use the weight learning rate unless a bias rate is prescribed."""
        return float(self.step_size if self.bias_step_size is None else self.bias_step_size)

    def get_bias_pseudo_label_weight(self) -> float:
        """Use the ordinary pseudo-label coefficient unless overridden for bias."""
        return float(
            self.pseudo_label_param
            if self.bias_pseudo_label_param is None else self.bias_pseudo_label_param
        )
