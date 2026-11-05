"""Finite-dimensional self-training gradient descent.

The learning loop receives one design matrix and observed labels, with zero
marking unlabeled observations. Model-specific ground truth is used only by
explicit diagnostic methods and callbacks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import torch

from src.config import AlgorithmConfig
from src.environment import QuenchedEnvironment
from src.initialization import SelfTrainingInitialization
from src.primitives import (
    compute_scores, pseudo_labels, pseudo_residual, selection_rate,
    sign_with_positive_tie,
)


@dataclass(frozen=True)
class FiniteStep:
    """Frozen objects used by one finite objective/update."""

    t: int
    scores: torch.Tensor
    pseudo_labels: torch.Tensor
    selection: torch.Tensor
    omega: torch.Tensor
    g: torch.Tensor
    bias_residual: torch.Tensor
    zeta: torch.Tensor
    tau: torch.Tensor
    bias: torch.Tensor
    weight: torch.Tensor


@dataclass
class SelfTrainedGradientDescent:
    """Finite self-training gradient descent with frozen pseudo-label updates."""

    cfg: AlgorithmConfig
    callback: Optional[Callable[["SelfTrainedGradientDescent", int], None]] = None

    bias: Optional[torch.Tensor] = field(init=False, default=None)
    weights: Optional[torch.Tensor] = field(init=False, default=None)
    y_observed_: Optional[torch.Tensor] = field(init=False, default=None)
    initialization_: Optional[SelfTrainingInitialization] = field(init=False, default=None)
    update_records_: list[FiniteStep] = field(init=False, default_factory=list)
    weight_history_: list[torch.Tensor] = field(init=False, default_factory=list)
    prev_preactivations_: Optional[torch.Tensor] = field(init=False, default=None)

    def _validate_X(self, X: torch.Tensor) -> torch.Tensor:
        X = torch.as_tensor(X, dtype=torch.float64)
        if X.ndim != 2 or min(X.shape) == 0:
            raise ValueError("X must be a nonempty two-dimensional design matrix")
        if not torch.isfinite(X).all():
            raise ValueError("X must be finite")
        return X

    def selection_mask(self, scores: torch.Tensor) -> torch.Tensor:
        return self.cfg.selection_mask(scores)

    @torch.no_grad()
    def fit(
        self,
        X: torch.Tensor,
        y_observed: torch.Tensor,
        initialization: SelfTrainingInitialization,
    ) -> "SelfTrainedGradientDescent":
        """Fit with labels in ``{-1, 0, +1}``; zero means unlabeled.

        Initialization supplies the bias and weights. Pseudo-labels use score
        signs from t=0 unless Y_init explicitly overrides the first step.
        Hidden ground-truth labels and the signal vector are not training inputs.
        """

        X = self._validate_X(X)
        y_observed = torch.as_tensor(y_observed, dtype=X.dtype, device=X.device).detach().clone()
        if y_observed.shape != (X.shape[0],):
            raise ValueError("y_observed must have shape (n,)")
        if not torch.all((y_observed == -1) | (y_observed == 0) | (y_observed == 1)):
            raise ValueError("y_observed entries must belong to {-1, 0, +1}")
        labeled = y_observed != 0
        n_labeled = int(labeled.sum().item())
        if n_labeled == 0:
            raise ValueError("finite self-training requires at least one labelled observation")
        n, d = X.shape
        Delta = labeled.to(dtype=X.dtype)
        rho = n_labeled / n
        if not isinstance(initialization, SelfTrainingInitialization):
            raise ValueError(
                "fit requires an explicit SelfTrainingInitialization for bias and weights"
            )
        init = initialization.for_data(X, y_observed)
        # Loss gradients take binary labels even where Delta later zeros them.
        training_labels = torch.where(labeled, y_observed, torch.ones_like(y_observed))
        self.y_observed_ = y_observed
        self.initialization_ = init
        self.bias = torch.as_tensor(init.b_init, dtype=X.dtype, device=X.device).detach().clone().reshape(())
        self.weights = init.w_init.detach().clone()
        self.update_records_ = []
        self.weight_history_ = [self.weights.detach().clone()]
        self.prev_preactivations_ = None

        # Initial callback retains the historical T+1 callback convention.  No
        # pseudo-residual is attributed to this state until the first objective
        # has been frozen below.
        if self.callback is not None:
            self.callback(self, 0)

        for t in range(self.cfg.n_iterations):
            b_current = self.bias
            w_current = self.weights
            scores = compute_scores(X, b_current, w_current)
            Yhat = pseudo_labels(t, scores, init.Y_init)
            selection = self.selection_mask(scores)
            # Labeled selection is irrelevant, but setting it to zero makes the
            # stored weights exactly the finite manuscript convention.
            selection = selection * (1.0 - Delta)
            omega = selection_rate(selection, Delta)
            pi = self.cfg.pseudo_label_param
            g = pseudo_residual(
                scores=scores,
                Y=training_labels,
                Delta=Delta,
                Yhat=Yhat,
                selection=selection,
                pi=pi,
                eta=self.cfg.step_size,
                rho=rho,
                loss_function=self.cfg.loss_function,
            )
            bias_pi = self.cfg.get_bias_pseudo_label_weight()
            bias_eta = self.cfg.get_bias_step_size()
            reuse_residual = not self.cfg.train_bias or (
                bias_pi == pi and bias_eta == self.cfg.step_size
            )
            bias_residual = g if reuse_residual else pseudo_residual(
                scores=scores,
                Y=training_labels,
                Delta=Delta,
                Yhat=Yhat,
                selection=selection,
                pi=bias_pi,
                eta=bias_eta,
                rho=rho,
                loss_function=self.cfg.loss_function,
            )
            zeta = torch.mean(bias_residual)
            tau = torch.linalg.vector_norm(w_current) / (d ** 0.5)
            record = FiniteStep(
                t=t,
                scores=scores.detach().clone(),
                pseudo_labels=Yhat.detach().clone(),
                selection=selection.detach().clone(),
                omega=omega.detach().clone(),
                g=g.detach().clone(),
                bias_residual=bias_residual.detach().clone(),
                zeta=zeta.detach().clone(),
                tau=tau.detach().clone(),
                bias=b_current.detach().clone(),
                weight=w_current.detach().clone(),
            )
            self.update_records_.append(record)

            # g already contains -eta times the frozen score gradient.
            decay = -self.cfg.step_size * self.cfg.penalty_param * self.cfg.penalty_function.gradient(w_current)
            self.prev_preactivations_ = scores[~labeled].detach().clone()
            self.weights = (w_current + decay + (d ** 0.5 / n) * (X.T @ g)).detach()
            self.bias = (b_current + zeta).detach() if self.cfg.train_bias else b_current.detach().clone()
            self.weight_history_.append(self.weights.detach().clone())

            if self.callback is not None:
                self.callback(self, t + 1)
        return self

    def macroscopic_observables(self, t: int, *, environment: QuenchedEnvironment) -> dict[str, torch.Tensor]:
        """Finite observables attached to the exact objective at iteration ``t``."""

        if t < 0 or t >= len(self.update_records_):
            raise IndexError("t must index an executed update")
        step = self.update_records_[t]
        env = environment
        if (env.n, env.d) != (step.scores.numel(), step.weight.numel()):
            raise ValueError("environment must match the fitted data shape")
        return {
            "m": torch.dot(env.mu, step.weight) / env.d,
            "chi": torch.dot(env.Y, step.g) / env.n,
            "zeta": step.zeta,
            "tau": step.tau,
            "omega": step.omega,
            "C_w": torch.stack(self.weight_history_[: t + 1], dim=1).T @ step.weight / env.d,
            "C_g": torch.stack([record.g for record in self.update_records_[: t + 1]], dim=1).T @ step.g / env.n,
        }

    def finite_decomposition(self, X: torch.Tensor, U: torch.Tensor, t: int, *, sigma: float, environment: QuenchedEnvironment) -> dict[str, torch.Tensor]:
        """Return the finite forward/backward decomposition at an executed step."""

        if self.y_observed_ is None:
            raise RuntimeError("fit must be called first")
        env = environment
        step = self.update_records_[t]
        X = torch.as_tensor(X, dtype=torch.float64, device=env.mu.device)
        U = torch.as_tensor(U, dtype=torch.float64, device=env.mu.device)
        if X.shape != (env.n, env.d) or U.shape != X.shape:
            raise ValueError("X and U must both have shape (n,d)")
        q = U @ step.weight / (env.d ** 0.5)
        p = U.T @ step.g / (env.n ** 0.5)
        m = torch.dot(env.mu, step.weight) / env.d
        chi = torch.dot(env.Y, step.g) / env.n
        r = step.bias + m * env.Y + float(sigma) * q
        noise_update = float(sigma) / (env.delta ** 0.5) * p
        return {
            "q": q,
            "p": p,
            "r": r,
            "direct_score": step.scores,
            "noise_update": noise_update,
            "direct_update_noise": (env.d ** 0.5 / env.n) * (X.T @ step.g) - chi * env.mu,
        }

    def decision_function(self, X: torch.Tensor) -> torch.Tensor:
        if self.weights is None or self.bias is None:
            raise RuntimeError("fit must be called before prediction")
        return compute_scores(X, self.bias, self.weights)

    def predict(self, X: torch.Tensor) -> torch.Tensor:
        return sign_with_positive_tie(self.decision_function(X))
