"""Unconstrained convex frozen-objective fits and numerical branch diagnostics.

Optimization uses z=(b,v), v=w/sqrt(d); ridge is lambda*||v||^2/2 and
the intercept is unpenalized. No branch inequalities enter the optimizer.
Consistency labels are floating-point diagnostics, not rigorous certificates.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize
import torch

from src.objectives import LogisticLoss

from .config import SuiteConfig


def _array(value):
    if isinstance(value, torch.Tensor):
        value = value.detach().cpu().numpy()
    return np.asarray(value, dtype=np.float64)


def _objective_arrays(X, environment, p0, cfg, oracle):
    X = _array(X)
    y = _array(environment.Y)
    labeled = _array(environment.Delta) == 1
    p0 = _array(p0)
    if X.shape != (environment.n, environment.d):
        raise ValueError("X shape differs from environment")
    if p0.shape != (environment.M,) or not np.isin(p0, (-1, 0, 1)).all():
        raise ValueError("p0 must have M entries in {-1,0,+1}")
    if environment.N < 1:
        raise ValueError("frozen objective requires at least one labeled observation")
    # Retain only observations with positive objective weight. Exclusion has no
    # effect on the denominator, which is always the original fixed pool M.
    unlabeled_indices = np.flatnonzero(~labeled)
    active_unlabeled = unlabeled_indices[p0 != 0] if cfg.pi > 0 else unlabeled_indices[:0]
    active = np.concatenate((np.flatnonzero(labeled), active_unlabeled))
    targets = np.concatenate((y[labeled], y[active_unlabeled] if oracle else p0[p0 != 0] if cfg.pi > 0 else p0[:0]))
    weights = np.concatenate((np.full(environment.N, 1.0 / environment.N), np.full(active_unlabeled.size, cfg.pi / environment.M if environment.M else 0.0)))
    return tuple(torch.from_numpy(array) for array in (np.ascontiguousarray(X[active]), targets, weights))


@torch.no_grad()
def _evaluate(z, X, targets, weights, penalty):
    # Use the same float64 Torch math as the finite engine, including its stable
    # logistic derivative. This also avoids spurious NumPy/Accelerate matmul
    # floating-point warnings observed on this macOS checkout for finite inputs.
    parameter = torch.as_tensor(z, dtype=torch.float64)
    b, v = parameter[0], parameter[1:]
    scores = b + X @ v
    margins = targets * scores
    value = torch.dot(weights, torch.logaddexp(torch.zeros_like(margins), -margins)) + 0.5 * penalty * torch.dot(v, v)
    score_gradient = weights * LogisticLoss().gradient(scores, targets)
    gradient = torch.cat((score_gradient.sum().reshape(1), X.T @ score_gradient + penalty * v))
    if not torch.isfinite(value) or not torch.isfinite(gradient).all():
        raise FloatingPointError("nonfinite frozen objective or analytic gradient in (b,v) coordinates")
    return float(value), gradient.numpy()


def frozen_objective(z, X, environment, p0, cfg: SuiteConfig, oracle=False):
    """Return objective and analytic gradient in z=(b,w/sqrt(d)) coordinates."""
    z = _array(z)
    if z.shape != (environment.d + 1,):
        raise ValueError("z must contain b followed by d scaled weights")
    arrays = _objective_arrays(X, environment, p0, cfg, oracle)
    return _evaluate(z, *arrays, cfg.penalty)


def minimize_frozen(X, environment, p0, b0, w0, cfg: SuiteConfig, oracle=False) -> dict:
    """Independently minimize one frozen objective using analytic L-BFGS-B.

    Positive ridge and both signs among positive-weight targets imply a finite,
    unique minimizer: ridge controls v and opposite target signs control b.
    Both labeled classes suffice, even with an empty selected set. If labeled
    support is missing we check the full active support explicitly. With zero
    ridge, existence/coercivity is not assumed even if a solver stops.
    """
    X_active, targets, weights = _objective_arrays(X, environment, p0, cfg, oracle)
    z0 = np.concatenate(([float(b0)], _array(w0) / np.sqrt(environment.d)))
    if z0.shape != (environment.d + 1,) or not np.isfinite(z0).all():
        raise ValueError("starting parameter must be finite with d weights")
    labeled_y = _array(environment.Y)[_array(environment.Delta) == 1]
    missing_labeled_class = np.unique(labeled_y).size < 2
    both_active_classes = np.unique(targets[weights > 0]).size == 2
    assumptions = {
        "positive_ridge": cfg.penalty > 0,
        "both_labeled_classes": not missing_labeled_class,
        "both_active_target_classes": both_active_classes,
        "finite_unique_minimizer_guaranteed": cfg.penalty > 0 and both_active_classes,
    }
    settings = {"method": "L-BFGS-B", "gtol": cfg.solver_gtol, "ftol": cfg.solver_ftol, "maxiter": cfg.solver_maxiter, "maxls": cfg.solver_maxls, "residual_tolerance": cfg.solver_residual_tolerance}
    warnings = []
    if missing_labeled_class:
        warnings.append("A labeled class is absent; finite-minimizer reasoning uses the full positive-weight target support.")
    if cfg.penalty <= 0:
        warnings.append("No positive ridge: existence of a finite minimizer has not been established (separation is possible).")
    if not both_active_classes:
        warnings.append("Only one sign has positive objective weight: the unpenalized intercept diverges, so there is no finite minimizer.")
        value, gradient = _evaluate(z0, X_active, targets, weights, cfg.penalty)
        return {
            "b": float(z0[0]), "w": z0[1:] * np.sqrt(environment.d),
            "objective": value, "gradient_inf": float(np.linalg.norm(gradient, ord=np.inf)), "gradient_l2": float(np.linalg.norm(gradient)),
            "gradient_coordinates": "(b,v=w/sqrt(d))", "converged": False,
            "status": "no_finite_minimizer", "solver_status_code": None, "solver_success": False,
            "message": warnings[-1], "nit": 0, "nfev": 1, "solver_settings": settings,
            "assumptions": assumptions, "warnings": warnings,
        }
    result = minimize(
        _evaluate, z0, args=(X_active, targets, weights, cfg.penalty), method="L-BFGS-B", jac=True,
        options={"gtol": cfg.solver_gtol, "ftol": cfg.solver_ftol, "maxiter": cfg.solver_maxiter, "maxls": cfg.solver_maxls},
    )
    value, gradient = _evaluate(result.x, X_active, targets, weights, cfg.penalty)
    gradient_inf = float(np.linalg.norm(gradient, ord=np.inf))
    converged = bool(result.success and np.isfinite(value) and np.isfinite(result.x).all() and gradient_inf <= cfg.solver_residual_tolerance and assumptions["finite_unique_minimizer_guaranteed"])
    return {
        "b": float(result.x[0]), "w": result.x[1:] * np.sqrt(environment.d),
        "objective": value, "gradient_inf": gradient_inf, "gradient_l2": float(np.linalg.norm(gradient)),
        "gradient_coordinates": "(b,v=w/sqrt(d))", "converged": converged,
        "status": "converged" if converged else "failed_or_insufficiently_converged",
        "solver_status_code": int(result.status), "solver_success": bool(result.success),
        "message": str(result.message), "nit": int(result.nit), "nfev": int(result.nfev),
        "solver_settings": settings, "assumptions": assumptions, "warnings": warnings,
    }


def branch_consistency(scores, p0, kminus, kplus, solver_converged=True, tolerance=1e-7) -> dict:
    """Signed branch margins with selected equality and strict zero intervals.

    Raw violation counts respect exact inequalities. Entries whose margin lies
    within +/-tolerance are considered unresolved, including zero configurations
    exactly on a boundary (which violate the strict zero interval). These labels
    do not include any optimization-error bound and are not certificates.
    """
    scores, p0 = _array(scores), _array(p0)
    if scores.ndim != 1 or scores.shape != p0.shape or not np.isin(p0, (-1, 0, 1)).all():
        raise ValueError("scores and p0 must be equal-length vectors; p0 in {-1,0,1}")
    if not kminus < 0 < kplus or tolerance <= 0:
        raise ValueError("require kminus<0<kplus and tolerance>0")
    positive, negative, zero = p0 == 1, p0 == -1, p0 == 0
    margins = np.where(positive, scores - kplus, np.where(negative, kminus - scores, np.minimum(scores - kminus, kplus - scores)))
    induced = np.where(scores <= kminus, -1, np.where(scores >= kplus, 1, 0)).astype(np.int8)
    violations = {
        "positive_below_upper": int(np.sum(positive & (scores < kplus))),
        "negative_above_lower": int(np.sum(negative & (scores > kminus))),
        "zero_at_or_below_lower": int(np.sum(zero & (scores <= kminus))),
        "zero_at_or_above_upper": int(np.sum(zero & (scores >= kplus))),
    }
    violated_observations = positive & (scores < kplus) | negative & (scores > kminus) | zero & ((scores <= kminus) | (scores >= kplus))
    margin_min = float(np.min(margins)) if margins.size else float("inf")
    if not solver_converged or not np.isfinite(scores).all():
        status = "solver failed or insufficiently converged"
    elif margin_min > tolerance:
        status = "numerically strictly self-consistent"
    elif margin_min < -tolerance:
        status = "numerically inconsistent"
    else:
        status = "unresolved / near a boundary"
    return {
        "margins": margins, "margin_min": margin_min,
        "violations": violations, "n_violated_inequalities": sum(violations.values()),
        "n_violated_observations": int(violated_observations.sum()),
        "n_near_boundary": int(np.sum(np.abs(margins) <= tolerance)),
        "induced_configuration": induced, "status": status,
        "tolerance": float(tolerance), "solver_converged": bool(solver_converged),
        "rigorous_certificate": False,
    }
