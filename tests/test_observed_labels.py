"""Estimator training needs observed labels, not a generative environment."""

from dataclasses import replace

import pytest
import torch

from src.algorithms import SelfTrainedGradientDescent
from src.callbacks import TestEvaluatorCallback as EvaluatorCallback
from src.config import AlgorithmConfig
from src.initialization import SelfTrainingInitialization
from src.objectives import LogisticLoss
from src.primitives import compute_scores, sign_with_positive_tie


def _problem():
    X = torch.tensor([[.3, -.2], [1., .5], [-.4, .2], [.1, -.7]])
    y_observed = torch.tensor([1., 0., -1., 0.])
    initialization = SelfTrainingInitialization(
        .1, torch.tensor([.4, -.3]), torch.tensor([1., -1., -1., 1.])
    )
    cfg = AlgorithmConfig(3, .2, .1, .7, margin_threshold=.1)
    return X, y_observed, initialization, cfg


def test_fit_without_environment_preserves_inputs_and_predicts():
    X, y_observed, initialization, cfg = _problem()
    original_X, original_y = X.clone(), y_observed.clone()
    original_w, original_init_y = initialization.w_init.clone(), initialization.Y_init.clone()
    learner = SelfTrainedGradientDescent(cfg)
    assert learner.fit(X, y_observed, initialization) is learner
    assert not hasattr(learner, "environment_")
    torch.testing.assert_close(X, original_X, rtol=0, atol=0)
    torch.testing.assert_close(y_observed, original_y, rtol=0, atol=0)
    torch.testing.assert_close(initialization.w_init, original_w, rtol=0, atol=0)
    torch.testing.assert_close(initialization.Y_init, original_init_y, rtol=0, atol=0)
    assert learner.y_observed_.data_ptr() != y_observed.data_ptr()
    assert learner.predict(X).shape == y_observed.shape
    assert torch.all(learner.predict(X).abs() == 1)
    for step in learner.update_records_:
        assert torch.all(step.selection[y_observed != 0] == 0)


@pytest.mark.parametrize("train_bias", [False, True])
@pytest.mark.parametrize("bias", [0., .4])
def test_default_initialization_matches_explicit_initial_score_signs(train_bias, bias):
    X, observed, init, config = _problem()
    config = replace(config, train_bias=train_bias)
    initial = SelfTrainingInitialization(bias, init.w_init)
    expected = sign_with_positive_tie(compute_scores(X, bias, init.w_init))
    explicit = expected.clone()
    explicit[observed != 0] = observed[observed != 0]
    actual = SelfTrainedGradientDescent(config).fit(X, observed, initial)
    reference = SelfTrainedGradientDescent(config).fit(
        X, observed, SelfTrainingInitialization(bias, init.w_init, explicit),
    )
    assert actual.initialization_.Y_init is None
    torch.testing.assert_close(actual.update_records_[0].pseudo_labels, expected, rtol=0, atol=0)
    for actual_w, expected_w in zip(actual.weight_history_, reference.weight_history_):
        torch.testing.assert_close(actual_w, expected_w, rtol=0, atol=0)
    torch.testing.assert_close(actual.bias, reference.bias, rtol=0, atol=0)


@pytest.mark.parametrize("labels, message", [
    ([1., 0., -1.], "shape"),
    ([[1.], [0.], [-1.], [0.]], "shape"),
    ([1., 2., -1., 0.], "entries"),
    ([1., float("nan"), -1., 0.], "entries"),
    ([1., float("inf"), -1., 0.], "entries"),
    ([0., 0., 0., 0.], "labelled"),
])
def test_fit_rejects_invalid_observed_labels(labels, message):
    X, _, initialization, cfg = _problem()
    with pytest.raises(ValueError, match=message):
        SelfTrainedGradientDescent(cfg).fit(X, labels, initialization)


def test_fit_requires_initial_labels_to_match_observed_labels():
    X, y_observed, initialization, cfg = _problem()
    inconsistent = initialization.Y_init.clone()
    inconsistent[0] *= -1
    with pytest.raises(ValueError, match="labelled"):
        SelfTrainedGradientDescent(cfg).fit(
            X, y_observed,
            SelfTrainingInitialization(initialization.b_init, initialization.w_init, inconsistent),
        )


def test_callbacks_use_interleaved_observed_mask_for_frozen_residuals():
    X, y_observed, initialization, cfg = _problem()
    labeled = y_observed != 0
    Y = torch.tensor([1., 1., -1., -1.])
    callback = EvaluatorCallback(
        X_lab=X[labeled], Y_lab=Y[labeled],
        X_unl=X[~labeled], Y_unl=Y[~labeled],
        metrics={"train_mean_residual", "train_label_residual_alignment"},
    )
    learner = SelfTrainedGradientDescent(cfg, callback).fit(X, y_observed, initialization)
    for metric in callback.history_.values():
        assert len(metric) == cfg.n_iterations + 1 and metric[0] == 0.
    for t, step in enumerate(learner.update_records_, 1):
        for name, mask in [("lab", labeled), ("unl", ~labeled)]:
            assert callback.history_[f"{name}_mean_residual"][t] == pytest.approx(float(step.g[mask].mean()))
            assert callback.history_[f"{name}_label_residual_alignment"][t] == pytest.approx(
                float((Y[mask] * step.g[mask]).mean()))


def test_binary_loss_receives_only_binary_labels_and_all_labeled_fit_works():
    class BinaryLoss(LogisticLoss):
        def gradient(self, scores, labels):
            assert torch.all(labels.abs() == 1)
            return super().gradient(scores, labels)

    X, y_observed, initialization, _ = _problem()
    cfg = AlgorithmConfig(2, .2, .1, .7, margin_threshold=.1, loss_function=BinaryLoss())
    assert torch.isfinite(SelfTrainedGradientDescent(cfg).fit(X, y_observed, initialization).weights).all()
    learner = SelfTrainedGradientDescent(cfg).fit(X, initialization.Y_init, initialization)
    assert all(float(step.omega) == 0. for step in learner.update_records_)
    assert torch.isfinite(learner.weights).all()
