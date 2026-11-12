import torch

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Literal

from src.algorithms import SelfTrainedGradientDescent
from src.performance import oracle_calibrated_bias_and_error, population_error
from src.primitives import compute_abstract_pseudo_residual_from, sign_with_positive_tie

MetricName = Literal[
    # Error terms
    "lab_error", 
    "unl_error", 
    "train_error",
    "test_error", 
    "population_error",
    # Label-Residual alignment terms
    "lab_label_residual_alignment",
    "unl_label_residual_alignment",
    "train_label_residual_alignment",
    "test_label_residual_alignment",
    # Mean Residual terms
    "lab_mean_residual",
    "unl_mean_residual",
    "train_mean_residual",
    "test_mean_residual",
    # Other Macroscopic terms
    "bias_term",
    "weight_vector_norm",
    "weight_signal_alignment",
    # Selection terms
    "unl_usage", 
    "unl_selected_error",
    "unl_flipping_rate"
]

@dataclass
class TestEvaluatorCallback:
    """
    Evaluates the model dynamically based on requested tracking metrics.
    Possible metrics include:
    ---- 1. Error terms ----
    - "lab_error": Error on labeled data
    - "unl_error": Error on unlabeled data (requires Y_unl)
    - "train_error": Error on train data (requires X_train and Y_train)
    - "test_error": Error on test data (requires X_test and Y_test)
    ---- 2. Label-Residual alignment terms ----
    - "lab_label_residual_alignment": Tracks E[Y * g(X)] on the labeled set
    - "unl_label_residual_alignment": Tracks E[Y * g(X)] on the unlabeled set
    - "train_label_residual_alignment": Tracks E[Y * g(X)] on the train set
    - "test_label_residual_alignment": Tracks E[Y * g(X)] on the test set
    ---- 3. Mean Residual terms ----
    - "lab_mean_residual": Tracks E[g(X)] on the labeled set (mean residual)
    - "unl_mean_residual": Tracks E[g(X)] on the unlabeled set
    - "train_mean_residual": Tracks E[g(X)] on the train set
    - "test_mean_residual": Tracks E[g(X)] on the test set
    ---- 4. Other Macroscopic terms ----
    - "bias_term": Tracks the value of the intercept (b)
    - "weight_vector_norm": Tracks tau = ||w|| / sqrt(d)
    - "weight_signal_alignment": Tracks the overlap between w and mu (requires mu)
    - Requesting "population_error" also records the auxiliary histories
      "oracle_bias" and "oracle_error" using the same weight observables.
    ---- 5. Selection terms ----
    - "unl_usage": Fraction selected by current unlabeled scores, including t=0
      (requires X_unl)
    - "unl_selected_error": Fraction of all unlabeled samples selected with an
      incorrect score-sign label, evaluated at the current scores (including t=0)
    - "unl_flipping_rate": Rate of label flipping in unlabeled data across iterations

    Score-based diagnostics use the current model state at t=0,...,T.
    Training residual diagnostics use the residual frozen in update t-1,
    with zero residuals at t=0.
    """

    X_lab: Optional[torch.Tensor] = None
    Y_lab: Optional[torch.Tensor] = None
    X_unl: Optional[torch.Tensor] = None
    Y_unl: Optional[torch.Tensor] = None
    X_test: Optional[torch.Tensor] = None
    Y_test: Optional[torch.Tensor] = None
    mu: Optional[torch.Tensor] = None  # Required for weight_signal_alignment
    sigma: Optional[float] = None # Required for population_error
    p: Optional[float] = None # Required for population_error

    X_train: Optional[torch.Tensor] = field(init=False, default=None)
    Y_train: Optional[torch.Tensor] = field(init=False, default=None)

    metrics: Set[MetricName] = field(
        default_factory=lambda: {"population_error"}
    )

    history_: Dict[str, List[float]] = field(init=False, default_factory=dict)

    def __post_init__(self):
        """Initialize history dictionary and validate data dependencies."""

        # A callback may add dependent metrics; never mutate the caller's set
        # (the runner uses that set to allocate result tensors).
        self.metrics = set(self.metrics)

        if "population_error" in self.metrics:
            self.metrics.update({"bias_term", "weight_vector_norm", "weight_signal_alignment"})

        if "train_mean_residual" in self.metrics:
            self.metrics.update({"lab_mean_residual", "unl_mean_residual"})

        if "train_label_residual_alignment" in self.metrics:
            self.metrics.update({"lab_label_residual_alignment", "unl_label_residual_alignment"})

        for metric in self.metrics:
            self.history_[metric] = []
        if "population_error" in self.metrics:
            self.history_["oracle_bias"] = []
            self.history_["oracle_error"] = []

        if "train_error" in self.metrics:
            if self.X_lab is not None and self.X_unl is not None:
                self.X_train = torch.cat([self.X_lab, self.X_unl])
            if self.Y_lab is not None and self.Y_unl is not None:
                self.Y_train = torch.cat([self.Y_lab, self.Y_unl])

        # Validate standard data dependencies
        if "lab_error" in self.metrics:
            assert self.X_lab is not None and self.Y_lab is not None, "X_lab and Y_lab required for lab_error."
        if {"unl_error", "unl_flipping_rate", "unl_usage"} & self.metrics:
            assert self.X_unl is not None, "X_unl required for unlabeled metrics."
        if "unl_error" in self.metrics:
            assert self.Y_unl is not None, "Y_unl required for unl_error."
        if "unl_selected_error" in self.metrics:
            assert self.X_unl is not None and self.Y_unl is not None, "X_unl and Y_unl required for unl_selected_error."
        if {"test_error", "test_label_residual_alignment", "test_mean_residual"} & self.metrics:
            assert self.X_test is not None and self.Y_test is not None, "X_test and Y_test required for test metrics."
        if "train_error" in self.metrics:
            assert self.X_train is not None and self.Y_train is not None, "X_train and Y_train required for train metrics."
            
        # Validate macroscopic tracking dependencies
        if "weight_signal_alignment" in self.metrics:
            assert self.mu is not None, "mu required for weight_signal_alignment."

    def __call__(self, learner: 'SelfTrainedGradientDescent', t: int):
        """
        Evaluate requested metrics initially and after each gradient step.
        """
        
        cache = {}
        y_observed = learner.y_observed_

        def get_actual_g_full():
            if t == 0 or not learner.update_records_:
                return torch.zeros_like(y_observed) if y_observed is not None else None
            # Callback t is emitted immediately after update t-1.  This is the
            # exact g frozen in that update, not a recomputation from current
            # post-update scores.
            return learner.update_records_[t - 1].g

        def get_actual_g_lab():
            g = get_actual_g_full()
            return g[y_observed != 0] if g is not None and y_observed is not None else None

        def get_actual_g_unl():
            g = get_actual_g_full()
            return g[y_observed == 0] if g is not None and y_observed is not None else None

        # --- Lazy Getters ---
        def get_preactivations_lab():
            if "preactivations_lab" not in cache:
                cache["preactivations_lab"] = learner.decision_function(self.X_lab)
            return cache["preactivations_lab"]

        def get_preactivations_unl():
            if "preactivations_unl" not in cache:
                cache["preactivations_unl"] = learner.decision_function(self.X_unl)
            return cache["preactivations_unl"]

        def get_preactivations_test():
            if "preactivations_test" not in cache:
                cache["preactivations_test"] = learner.decision_function(self.X_test)
            return cache["preactivations_test"]

        def get_test_residual():
            if "test_residual" not in cache:
                scores = get_preactivations_test()
                # Held-out residuals use true labels with no pseudo-label term.
                cache["test_residual"] = compute_abstract_pseudo_residual_from(
                    preactivation=scores, label=self.Y_test,
                    indicator=scores.new_tensor(1.0),
                    selection_mask=torch.zeros_like(scores),
                    coef=0.0, rho=1.0, eta=learner.cfg.step_size,
                    loss_function=learner.cfg.loss_function,
                )
            return cache["test_residual"]

        def get_preds_lab():
            if "preds_lab" not in cache:
                cache["preds_lab"] = sign_with_positive_tie(get_preactivations_lab())
            return cache["preds_lab"]

        def get_preds_unl():
            if "preds_unl" not in cache:
                cache["preds_unl"] = sign_with_positive_tie(get_preactivations_unl())
            return cache["preds_unl"]

        def get_preds_train():
            if "preds_train" not in cache:
                cache["preds_train"] = learner.predict(self.X_train)
            return cache["preds_train"]
        
        def get_preds_test():
            if "preds_test" not in cache:
                cache["preds_test"] = sign_with_positive_tie(get_preactivations_test())
            return cache["preds_test"]

        # --- 1. Labeled Metrics ---
        if "lab_error" in self.metrics:
            error = (get_preds_lab() != self.Y_lab).double().mean().item()
            self.history_["lab_error"].append(error)
        
        if "lab_label_residual_alignment" in self.metrics:
            g = get_actual_g_lab()
            self.history_["lab_label_residual_alignment"].append(torch.mean(self.Y_lab * g).item())

        if "lab_mean_residual" in self.metrics:
            g = get_actual_g_lab()
            self.history_["lab_mean_residual"].append(torch.mean(g).item())

        # --- 2. Unlabeled Metrics ---
        if "unl_error" in self.metrics:
            error = (get_preds_unl() != self.Y_unl).double().mean().item()
            self.history_["unl_error"].append(error)

        if "unl_label_residual_alignment" in self.metrics:
            g = get_actual_g_unl()
            self.history_["unl_label_residual_alignment"].append(torch.mean(self.Y_unl * g).item())

        if "unl_mean_residual" in self.metrics:
            g = get_actual_g_unl()
            self.history_["unl_mean_residual"].append(torch.mean(g).item())

        # --- 3. Train Metrics (Error Only!) ---
        if "train_error" in self.metrics:
            error = (get_preds_train() != self.Y_train).double().mean().item()
            self.history_["train_error"].append(error)

        n_lab = self.X_lab.shape[0] if self.X_lab is not None else 0
        n_unl = self.X_unl.shape[0] if self.X_unl is not None else 0
        rho = n_lab / (n_lab + n_unl) if (n_lab + n_unl) > 0 else 1.0

        if "train_mean_residual" in self.metrics:
            lab = self.history_["lab_mean_residual"][-1]
            unl = self.history_["unl_mean_residual"][-1]
            self.history_["train_mean_residual"].append(rho * lab + (1 - rho) * unl)

        if "train_label_residual_alignment" in self.metrics:
            lab = self.history_["lab_label_residual_alignment"][-1]
            unl = self.history_["unl_label_residual_alignment"][-1]
            self.history_["train_label_residual_alignment"].append(rho * lab + (1 - rho) * unl)

        # --- 4. Test Metrics ---
        if "test_error" in self.metrics:
            error = (get_preds_test() != self.Y_test).double().mean().item()
            self.history_["test_error"].append(error)
                
        if "test_label_residual_alignment" in self.metrics:
            g = get_test_residual()
            self.history_["test_label_residual_alignment"].append(torch.mean(self.Y_test * g).item())

        if "test_mean_residual" in self.metrics:
            g = get_test_residual()
            self.history_["test_mean_residual"].append(torch.mean(g).item())


        # --- 5. Pseudo-labeling Selection Metrics ---
        if "unl_selected_error" in self.metrics:
            scores = get_preactivations_unl()
            selected = learner.selection_mask(scores) > 0
            incorrect = selected & (get_preds_unl() != self.Y_unl)
            error = incorrect.double().mean().item() if scores.numel() else 0.0
            self.history_["unl_selected_error"].append(error)

        if "unl_usage" in self.metrics:
            scores = get_preactivations_unl()
            usage = (
                (learner.selection_mask(scores) > 0).double().mean().item()
                if scores.numel() else 0.0
            )
            self.history_["unl_usage"].append(usage)

        if "unl_flipping_rate" in self.metrics:
            if learner.prev_preactivations_ is not None:
                prev_preds = torch.where(learner.prev_preactivations_ >= 0, 1, -1)
                flipping_rate = (get_preds_unl() != prev_preds).double().mean().item()
                self.history_["unl_flipping_rate"].append(flipping_rate)
            else:
                self.history_["unl_flipping_rate"].append(0.0)


        # --- 6. Internal State Metrics ---
        if "bias_term" in self.metrics:
            bias_val = learner.bias.item() if isinstance(learner.bias, torch.Tensor) else float(learner.bias)
            self.history_["bias_term"].append(bias_val)
        
        if "weight_vector_norm" in self.metrics:
            # Dimension-normalized norm tau = ||w|| / sqrt(d).
            d = len(learner.weights)
            norm = (torch.linalg.norm(learner.weights) / (d**0.5)).item()
            self.history_["weight_vector_norm"].append(norm)
            
        if "weight_signal_alignment" in self.metrics:
            alignment = torch.mean(learner.weights * self.mu).item()
            self.history_["weight_signal_alignment"].append(alignment)

        if "population_error" in self.metrics:
            alignment = self.history_["weight_signal_alignment"][-1]
            weight_scale = self.history_["weight_vector_norm"][-1]
            pop_err = population_error(
                b=self.history_["bias_term"][-1],
                m=alignment,
                tau=weight_scale,
                sigma=self.sigma,
                p=self.p
            )
            self.history_["population_error"].append(pop_err)
            oracle_bias, oracle_error = oracle_calibrated_bias_and_error(
                alignment,
                weight_scale,
                self.sigma,
                self.p,
                machine_epsilon=torch.finfo(learner.weights.dtype).eps,
            )
            self.history_["oracle_bias"].append(oracle_bias)
            self.history_["oracle_error"].append(oracle_error)
