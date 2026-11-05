"""Shared pure mathematical primitives for finite GD and effective dynamics."""

from __future__ import annotations

from typing import Optional

import torch


# Pure score and pseudo-label functions.

def sign_with_positive_tie(scores: torch.Tensor) -> torch.Tensor:
    """Return ``sign(scores)`` with the manuscript convention ``sign(0)=+1``."""

    return torch.where(scores >= 0, torch.ones_like(scores), -torch.ones_like(scores))


def compute_scores(X: torch.Tensor, b: float | torch.Tensor, w: torch.Tensor) -> torch.Tensor:
    """Compute ``r=b 1 + Xw/sqrt(d)`` without mutating inputs."""

    if X.ndim != 2 or w.ndim != 1 or X.shape[1] != w.numel():
        raise ValueError("require X.shape == (n, d) and w.shape == (d,)")
    if X.device != w.device:
        raise ValueError("X and w must share a device")
    return X @ w / (w.numel() ** 0.5) + torch.as_tensor(b, dtype=X.dtype, device=X.device)


def pseudo_labels(t: int, scores: torch.Tensor, Y_init: Optional[torch.Tensor] = None) -> torch.Tensor:
    """Use score signs at every step unless t=0 labels are explicitly supplied."""
    if t < 0:
        raise ValueError("t must be nonnegative")
    if t == 0 and Y_init is not None:
        if Y_init.shape != scores.shape:
            raise ValueError("Y_init and scores must have the same shape")
        return Y_init.to(dtype=scores.dtype, device=scores.device)
    return sign_with_positive_tie(scores)


# Selection weights and the shared frozen-score update residual.

def selection_rate(selection: torch.Tensor, Delta: Optional[torch.Tensor] = None) -> torch.Tensor:
    """Empirical ``omega`` over unlabeled observations (zero if ``M=0``)."""

    if Delta is None:
        return selection.mean() if selection.numel() else selection.new_zeros(())
    unlabeled = Delta == 0
    M = int(unlabeled.sum().item())
    if M == 0:
        return selection.new_zeros(())
    return selection[unlabeled].sum() / M


def pseudo_residual(
    *,
    scores: torch.Tensor,
    Y: torch.Tensor,
    Delta: torch.Tensor,
    Yhat: torch.Tensor,
    selection: torch.Tensor,
    pi: float,
    eta: float,
    rho: float,
    loss_function,
) -> torch.Tensor:
    """Finite/particle vector ``g=-eta`` times the frozen score gradient."""

    labelled = torch.zeros_like(scores) if rho == 0 else Delta / rho * loss_function.gradient(scores, Y)
    if pi == 0 or rho >= 1 or not torch.any((1 - Delta) * selection != 0):
        return -eta * labelled
    unlabeled = ((1 - Delta) * pi / (1 - rho) * selection
                 * loss_function.gradient(scores, Yhat))
    return -eta * (labelled + unlabeled)


def compute_abstract_pseudo_residual_from(
    preactivation: torch.Tensor,
    label: torch.Tensor,
    indicator: torch.Tensor,
    selection_mask: torch.Tensor,
    coef: float,
    rho: float,
    eta: float,
    loss_function,
    time_index: Optional[int] = None,
    initial_pseudo_label: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    """
    Validate and adapt particle score inputs to the shared pseudo-residual.

    Finite GD calls pseudo_residual directly; the effective process and optional
    callback residual diagnostics use this adapter. Both use g = -eta times
    the frozen score gradient.

    Score signs are used at every iteration by default. At ``time_index=0``,
    explicit ``initial_pseudo_label`` values optionally override that rule. The unlabeled term is normalized by
    the total unlabeled population, with no selected-fraction normalization.
    """
    if not isinstance(preactivation, torch.Tensor):
        raise TypeError("preactivation must be a torch.Tensor")
    if not isinstance(label, torch.Tensor):
        raise TypeError("label must be a torch.Tensor")
    if not isinstance(indicator, torch.Tensor):
        raise TypeError("indicator must be a torch.Tensor")
    if not isinstance(selection_mask, torch.Tensor):
        raise TypeError("selection_mask must be a torch.Tensor")
    if label.shape != preactivation.shape:
        raise ValueError(
            "label and preactivation must have the same shape, "
            f"got {tuple(label.shape)} and {tuple(preactivation.shape)}"
        )
    if selection_mask.shape != preactivation.shape:
        raise ValueError(
            "selection_mask and preactivation must have the same shape, "
            f"got {tuple(selection_mask.shape)} and {tuple(preactivation.shape)}"
        )
    try:
        indicator_shape = torch.broadcast_shapes(
            indicator.shape, preactivation.shape
        )
    except RuntimeError as error:
        raise ValueError(
            "indicator must be scalar or broadcastable to the preactivation "
            f"shape {tuple(preactivation.shape)}, got {tuple(indicator.shape)}"
        ) from error
    if indicator_shape != preactivation.shape:
        raise ValueError(
            "indicator must broadcast exactly to the preactivation shape, "
            f"got {tuple(indicator_shape)} instead of {tuple(preactivation.shape)}"
        )
    if label.device != preactivation.device:
        raise ValueError("label and preactivation must be on the same device")
    if indicator.device != preactivation.device:
        raise ValueError("indicator and preactivation must be on the same device")
    if selection_mask.device != preactivation.device:
        raise ValueError(
            "selection_mask and preactivation must be on the same device"
        )
    if not torch.all((label == 1) | (label == -1)):
        raise ValueError("label entries must belong to {-1, +1}")
    if time_index is not None:
        if isinstance(time_index, bool) or not isinstance(time_index, int):
            raise TypeError("time_index must be a nonnegative integer or None")
        if time_index < 0:
            raise ValueError("time_index must be nonnegative")

    indicator = indicator.to(dtype=preactivation.dtype)
    if coef == 0.0 or rho >= 1.0 or not torch.any((1 - indicator) * selection_mask != 0):
        # No pseudo-labelled term is active.
        return pseudo_residual(
            scores=preactivation,
            Y=label,
            Delta=indicator,
            Yhat=label,
            selection=torch.zeros_like(selection_mask),
            pi=0.0,
            eta=eta,
            rho=rho,
            loss_function=loss_function,
        )

    if time_index == 0 and initial_pseudo_label is not None:
        if not isinstance(initial_pseudo_label, torch.Tensor):
            raise TypeError("initial_pseudo_label must be a torch.Tensor")
        if initial_pseudo_label.shape != preactivation.shape:
            raise ValueError(
                "initial_pseudo_label and preactivation must have the same "
                f"shape, got {tuple(initial_pseudo_label.shape)} and "
                f"{tuple(preactivation.shape)}"
            )
        if initial_pseudo_label.device != preactivation.device:
            raise ValueError(
                "initial_pseudo_label and preactivation must be on the same device"
            )
        if not torch.all(
            (initial_pseudo_label == 1) | (initial_pseudo_label == -1)
        ):
            raise ValueError(
                "initial_pseudo_label entries must belong to {-1, +1}"
            )
        y_init = initial_pseudo_label.to(dtype=preactivation.dtype)
    else:
        y_init = None
    # ``time_index=None`` historically meant endogenous sign scores; map it to
    # a positive time while sharing the same pseudo-residual implementation.
    effective_time = 1 if time_index is None else time_index
    y_pseudo = pseudo_labels(effective_time, preactivation, y_init)
    return pseudo_residual(
        scores=preactivation,
        Y=label,
        Delta=indicator,
        Yhat=y_pseudo,
        selection=selection_mask,
        pi=coef,
        eta=eta,
        rho=rho,
        loss_function=loss_function,
    )
