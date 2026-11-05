"""Selected-error diagnostics use score signs and the full unlabeled pool."""

import pytest
import torch

import src.callbacks as callbacks
from src.algorithms import SelfTrainedGradientDescent
from src.callbacks import TestEvaluatorCallback as EvaluatorCallback
from src.config import AlgorithmConfig
from src.environment import QuenchedEnvironment
from src.initialization import SelfTrainingInitialization


def _problem(T=0, threshold=1.0):
    # Positive/negative threshold equalities, selected tails, and unselected
    # scores (including zero). Four selected, two incorrect, six unlabeled.
    X = torch.tensor([[0.], [0.], [1.], [-1.], [2.], [-2.], [.5], [0.]])
    Y = torch.tensor([1., -1., 1., 1., -1., -1., -1., -1.])
    env = QuenchedEnvironment(torch.ones(1), Y, torch.tensor([1., 1., 0., 0., 0., 0., 0., 0.]))
    cfg = AlgorithmConfig(T, .1, .2, .7, margin_threshold=threshold)
    # Deliberately disagree with score signs at initialization: the diagnostic
    # is defined by c(r), rather than by the training update's exogenous labels.
    init = SelfTrainingInitialization(0., torch.ones(1), Y.clone())
    cb = EvaluatorCallback(X_unl=X[env.I_U], Y_unl=Y[env.I_U],
                           metrics={"unl_usage", "unl_selected_error", "unl_error"})
    return X, env, cfg, init, cb


@pytest.mark.parametrize("threshold, expected", [(1., 2/6), (3., 0.)])
def test_selected_error_boundaries_and_empty_selection(threshold, expected):
    X, env, cfg, init, cb = _problem(threshold=threshold)
    learner = SelfTrainedGradientDescent(cfg, callback=cb).fit(X, env.Y * env.Delta, init)
    assert cb.history_["unl_selected_error"] == pytest.approx([expected])
    scores = learner.decision_function(X[env.I_U])
    omega = learner.selection_mask(scores).double().mean().item()
    assert 0 <= expected <= omega <= 1
    assert omega == pytest.approx(4/6 if threshold == 1 else 0.)
    # Preserve legacy usage timing: its initial entry is zero.
    assert cb.history_["unl_usage"] == [0.]


def test_selected_error_tracks_current_scores_and_does_not_change_training():
    X, env, cfg, init, cb = _problem(T=3)
    learner = SelfTrainedGradientDescent(cfg, callback=cb).fit(X, env.Y * env.Delta, init)
    reference = SelfTrainedGradientDescent(cfg).fit(X, env.Y * env.Delta, init)
    assert len(cb.history_["unl_selected_error"]) == cfg.n_iterations + 1
    # d=1: stored weights and each callback bias reconstruct current scores.
    biases = [0.] + [float(step.bias + step.bias_residual.mean())
                     for step in learner.update_records_]
    for t, (w, b) in enumerate(zip(learner.weight_history_, biases)):
        scores = b + X[env.I_U] @ w
        c = (scores >= 1.).int() - (scores <= -1.).int()
        expected = (c == -env.Y[env.I_U]).double().mean().item()
        omega = (c != 0).double().mean().item()
        assert cb.history_["unl_selected_error"][t] == pytest.approx(expected)
        assert 0 <= expected <= omega <= 1
        torch.testing.assert_close(w, reference.weight_history_[t], rtol=0, atol=0)
    torch.testing.assert_close(learner.bias, reference.bias, rtol=0, atol=0)
    assert cb.history_["unl_usage"] == [0.] + [float(s.omega) for s in learner.update_records_]
    # Legacy usage entry t+1 belongs to scores at t.
    for error, omega in zip(cb.history_["unl_selected_error"][:-1],
                            cb.history_["unl_usage"][1:]):
        assert 0 <= error <= omega <= 1


def test_selected_error_requires_diagnostic_labels():
    with pytest.raises(AssertionError, match="X_unl and Y_unl"):
        EvaluatorCallback(X_unl=torch.ones(2, 1), metrics={"unl_selected_error"})


def test_score_diagnostics_reuse_cached_preactivations(monkeypatch):
    X, env, cfg, init, callback = _problem(T=2)
    callback = EvaluatorCallback(
        X_lab=X[env.I_L], Y_lab=env.Y[env.I_L],
        X_unl=callback.X_unl, Y_unl=callback.Y_unl,
        X_test=X.clone(), Y_test=env.Y.clone(),
        metrics={"lab_error", "unl_error", "unl_selected_error",
                 "test_error", "test_mean_residual"},
    )
    learner = SelfTrainedGradientDescent(cfg, callback=callback)
    decision_function = learner.decision_function
    calls = {"lab": 0, "unl": 0, "test": 0}

    def counted_preactivation(samples, *args, **kwargs):
        for name in calls:
            if samples is getattr(callback, f"X_{name}"):
                calls[name] += 1
        return decision_function(samples, *args, **kwargs)

    monkeypatch.setattr(learner, "decision_function", counted_preactivation)
    learner.fit(X, env.Y * env.Delta, init)
    # Error, selection, and held-out residual diagnostics share scores within
    # each callback; the cache is refreshed for every new model state.
    assert calls == {name: cfg.n_iterations + 1 for name in calls}


def test_callback_history_serializes_selected_error(tmp_path):
    X, env, cfg, init, callback = _problem(T=2)
    SelfTrainedGradientDescent(cfg, callback=callback).fit(X, env.Y * env.Delta, init)
    trajectory = torch.tensor(callback.history_["unl_selected_error"])
    assert trajectory.shape == (3,)
    assert torch.all((trajectory >= 0) & (trajectory <= 1))
    path = tmp_path / "results.pt"
    torch.save(callback.history_, path)
    restored = torch.load(path, weights_only=True)
    torch.testing.assert_close(torch.tensor(restored["unl_selected_error"]), trajectory)


def test_usage_requires_no_evaluation_data():
    X, env, cfg, init, _ = _problem(T=2)
    callback = EvaluatorCallback(metrics={"unl_usage"})
    learner = SelfTrainedGradientDescent(cfg, callback).fit(X, env.Y * env.Delta, init)
    assert callback.history_["unl_usage"] == [0.] + [float(s.omega) for s in learner.update_records_]


def test_callback_combines_training_data_only_for_training_error():
    X, env, _, _, _ = _problem()
    data = dict(X_lab=X[env.I_L], Y_lab=env.Y[env.I_L],
                X_unl=X[env.I_U], Y_unl=env.Y[env.I_U])
    callback = EvaluatorCallback(**data, metrics={"unl_selected_error"})
    assert callback.X_train is None and callback.Y_train is None
    callback = EvaluatorCallback(**data, metrics={"train_error"})
    assert callback.X_train.shape == X.shape and callback.Y_train.shape == env.Y.shape


def test_held_out_residual_is_cached_across_metrics(monkeypatch):
    X, env, cfg, init, _ = _problem(T=2)
    calls = []
    residual = callbacks.compute_abstract_pseudo_residual_from

    def counted(**kwargs):
        calls.append(kwargs)
        return residual(**kwargs)

    monkeypatch.setattr(callbacks, "compute_abstract_pseudo_residual_from", counted)
    callback = EvaluatorCallback(
        X_test=X, Y_test=env.Y,
        metrics={"test_mean_residual", "test_label_residual_alignment"},
    )
    SelfTrainedGradientDescent(cfg, callback).fit(X, env.Y * env.Delta, init)
    assert len(calls) == cfg.n_iterations + 1
