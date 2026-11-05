import warnings

import numpy as np
import torch

from src.algorithms import SelfTrainedGradientDescent
from src.config import AlgorithmConfig
from src.environment import QuenchedEnvironment
from src.initialization import SelfTrainingInitialization
from src.objectives import LogisticLoss, RidgePenalty
from src.primitives import compute_scores


def _algorithm_config(n_iterations, step_size):
    return AlgorithmConfig(
        n_iterations=n_iterations,
        margin_threshold=1.0,
        step_size=step_size,
        penalty_param=0.01,
        pseudo_label_param=0.1,
        loss_function=LogisticLoss(),
        penalty_function=RidgePenalty(),
    )


def test_self_training_does_not_emit_runtime_warnings():
    rng = np.random.default_rng(0)
    X_lab = rng.normal(size=(40, 3))
    y_lab = np.where(X_lab[:, 0] + X_lab[:, 1] > 0, 1, -1)
    X_unl = rng.normal(size=(40, 3))

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        learner = SelfTrainedGradientDescent(
            cfg=_algorithm_config(
                n_iterations=20,
                step_size=0.5,
            )
        )
        X_lab = torch.as_tensor(X_lab)
        y_lab = torch.as_tensor(y_lab)
        X_unl = torch.as_tensor(X_unl)
        X = torch.cat((X_lab, X_unl))
        Y = torch.cat((y_lab, torch.ones(len(X_unl))))
        environment = QuenchedEnvironment(
            torch.zeros(X.shape[1]), Y,
            torch.cat((torch.ones(len(X_lab)), torch.zeros(len(X_unl)))),
        )
        initialization = SelfTrainingInitialization(
            learner.cfg.initial_bias, torch.randn(X.shape[1]), Y.clone()
        )
        learner.fit(X, environment.Y * environment.Delta, initialization)
        fields = learner.decision_function(X_unl)

    assert torch.isfinite(fields).all()
    assert torch.isfinite(learner.weights).all()


def test_field_is_safe_for_extreme_weights():
    fields = compute_scores(
        torch.tensor([[1.0, -2.0], [0.5, 1.5]]),
        1e300, torch.tensor([1e300, -1e300]),
    )

    assert torch.isfinite(fields).all()
