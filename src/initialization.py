"""Validated initial conditions for the full finite dataset."""

from __future__ import annotations

from dataclasses import dataclass

import torch


@dataclass(frozen=True)
class SelfTrainingInitialization:
    """Initial bias/weights and optional first-step pseudo-label override."""

    b_init: float | torch.Tensor
    w_init: torch.Tensor
    Y_init: torch.Tensor | None = None

    def for_data(self, X: torch.Tensor, y_observed: torch.Tensor) -> "SelfTrainingInitialization":
        """Validate initial conditions against the design and observed labels."""
        w = torch.as_tensor(self.w_init, dtype=torch.float64, device=X.device).detach().clone()
        b = torch.as_tensor(self.b_init, dtype=torch.float64, device=X.device).detach().clone()
        if w.shape != (X.shape[1],):
            raise ValueError(f"w_init must have shape ({X.shape[1]},)")
        if b.numel() != 1 or not torch.isfinite(b).all() or not torch.isfinite(w).all():
            raise ValueError("b_init and w_init must be finite")
        if y_observed.shape != (X.shape[0],):
            raise ValueError("y_observed must have shape (n,)")
        y_init = None
        if self.Y_init is not None:
            y_init = torch.as_tensor(self.Y_init, dtype=torch.float64, device=X.device).detach().clone()
            if y_init.shape != (X.shape[0],):
                raise ValueError(f"Y_init must have shape ({X.shape[0]},)")
            if not torch.all((y_init == -1) | (y_init == 1)):
                raise ValueError("Y_init entries must belong to {-1,+1}")
            labeled = y_observed != 0
            if torch.any(y_init[labeled] != y_observed[labeled]):
                raise ValueError("Y_init must equal Y on labelled coordinates")
        return SelfTrainingInitialization(b.reshape(()), w, y_init)
