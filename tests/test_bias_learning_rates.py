"""Independent weight/bias rates and fixed nonzero intercepts."""

from dataclasses import replace
import math

import pytest
import torch

from src.algorithms import SelfTrainedGradientDescent
from src.asymptotics import MacroscopicStateEvolution
from src.config import AlgorithmConfig, DataConfig
from src.environment import FourCellSampleTypeLaw, state_evolution_sample_base_sampler
from src.initialization import SelfTrainingInitialization
from src.objectives import LossFunction, Penalty


def _finite_problem():
    X = torch.tensor([[.3, -.2], [1., .5], [-.4, .2], [.1, -.7]])
    observed = torch.tensor([1., 0., -1., 0.])
    initialization = SelfTrainingInitialization(
        .2, torch.tensor([.4, -.3]), torch.tensor([1., -1., -1., 1.])
    )
    return X, observed, initialization


def _config(**kwargs):
    return AlgorithmConfig(1, .2, .1, .7, margin_threshold=.1, initial_bias=.2, **kwargs)


def _process(config):
    law = FourCellSampleTypeLaw.product(label_prior=.5, supervision_ratio=.5)
    return MacroscopicStateEvolution(
        DataConfig(.8, .5, .5, 2., lambda: 1.), config,
        K_w=12, K_g=16, mc_seed=17, initial_weight=torch.linspace(.2, .7, 12),
        sample_base_sampler=state_evolution_sample_base_sampler(law),
    )


def test_default_bias_rate_follows_weight_rate_after_replace():
    config = _config()
    assert config.bias_step_size is None
    assert config.get_bias_step_size() == config.step_size
    changed = replace(config, step_size=.07)
    assert changed.get_bias_step_size() == .07
    explicit = replace(config, bias_step_size=.03)
    assert replace(explicit, step_size=.07).get_bias_step_size() == .03
    assert replace(config, bias_step_size=0.).get_bias_step_size() == 0.


@pytest.mark.parametrize("rate", [-.1, float("inf"), float("nan")])
def test_invalid_bias_learning_rates_are_rejected(rate):
    with pytest.raises(ValueError, match="bias_step_size"):
        _config(bias_step_size=rate)


def test_finite_independent_bias_rate_leaves_the_first_weight_update_unchanged():
    X, observed, initialization = _finite_problem()
    default = SelfTrainedGradientDescent(_config()).fit(X, observed, initialization)
    equal = SelfTrainedGradientDescent(_config(bias_step_size=.2)).fit(X, observed, initialization)
    slower = SelfTrainedGradientDescent(_config(bias_step_size=.03)).fit(X, observed, initialization)
    torch.testing.assert_close(default.weights, equal.weights, rtol=0, atol=0)
    torch.testing.assert_close(default.bias, equal.bias, rtol=0, atol=0)
    torch.testing.assert_close(default.weights, slower.weights, rtol=0, atol=0)
    torch.testing.assert_close(slower.bias - initialization.b_init,
                               .03 / .2 * (default.bias - initialization.b_init))
    assert not torch.equal(default.bias, slower.bias)


def test_effective_independent_bias_rate_leaves_the_first_weight_update_unchanged():
    default, equal, slower = [_process(cfg) for cfg in
                              [_config(), _config(bias_step_size=.2), _config(bias_step_size=.03)]]
    for process in (default, equal, slower):
        process.step(0)
    torch.testing.assert_close(default.weight[1], equal.weight[1], rtol=0, atol=0)
    torch.testing.assert_close(default.bias[1], equal.bias[1], rtol=0, atol=0)
    torch.testing.assert_close(default.weight[1], slower.weight[1], rtol=0, atol=0)
    torch.testing.assert_close(slower.bias[1] - slower.bias[0],
                               .03 / .2 * (default.bias[1] - default.bias[0]))
    assert not torch.equal(default.bias[1], slower.bias[1])


@pytest.mark.parametrize("train_bias, rate", [(False, .9), (True, 0.)])
def test_fixed_nonzero_bias_affects_scores_selection_and_pseudo_labels(train_bias, rate):
    X = torch.tensor([[0.], [.5], [-.5], [1.], [-1.]])
    observed = torch.tensor([1., 0., 0., 0., 0.])
    init = SelfTrainingInitialization(.4, torch.ones(1), torch.tensor([1., 1., -1., 1., -1.]))
    config = AlgorithmConfig(3, .1, .1, .7, positive_margin=.8, negative_margin=-.3,
                             train_bias=train_bias, bias_step_size=rate, initial_bias=.4)
    learner = SelfTrainedGradientDescent(config).fit(X, observed, init)
    torch.testing.assert_close(learner.bias, torch.tensor(.4), rtol=0, atol=0)
    for step in learner.update_records_:
        torch.testing.assert_close(step.bias, torch.tensor(.4), rtol=0, atol=0)
        torch.testing.assert_close(step.scores, .4 + X @ step.weight)
        expected = ((step.scores >= .8) | (step.scores <= -.3)).double() * (observed == 0)
        torch.testing.assert_close(step.selection, expected)
        if step.t:
            torch.testing.assert_close(step.pseudo_labels, torch.where(step.scores >= 0, 1., -1.))
    assert not torch.equal(learner.update_records_[0].selection,
                           config.selection_mask(X[:, 0]) * (observed == 0))

    process = _process(replace(config, n_iterations=3))
    process.compute_trajectory()
    for t in range(4):
        torch.testing.assert_close(process.bias[t], torch.tensor(.4), rtol=0, atol=0)
        expected = .4 + process.weight_signal_alignments[t] * process.label + .8 * process.forward_noise[t]
        torch.testing.assert_close(process.preactivation[t], expected)


def test_zero_bias_rate_needs_no_initial_pseudo_labels_when_weight_pi_is_zero():
    config = AlgorithmConfig(2, .1, .1, 0., margin_threshold=.5, initial_bias=.4,
                             bias_pseudo_label_param=.7, bias_step_size=0.)
    process = MacroscopicStateEvolution(
        DataConfig(.8, .5, .5, 2., lambda: 1.), config, K_w=12, K_g=16,
    )
    assert process.initial_pseudo_label is None
    process.compute_trajectory()
    for bias in process.bias:
        torch.testing.assert_close(bias, torch.tensor(.4), rtol=0, atol=0)


def test_fixed_bias_ignores_the_unused_bias_pseudo_label_coefficient():
    config = AlgorithmConfig(2, .1, .1, 0., margin_threshold=.5, initial_bias=.4,
                             train_bias=False, bias_pseudo_label_param=.7, bias_step_size=.3)
    X, observed, initialization = _finite_problem()
    initialization = replace(initialization, b_init=.4)
    baseline = replace(config, bias_pseudo_label_param=0., bias_step_size=.01)
    actual = SelfTrainedGradientDescent(config).fit(X, observed, initialization)
    reference = SelfTrainedGradientDescent(baseline).fit(X, observed, initialization)
    torch.testing.assert_close(actual.weights, reference.weights, rtol=0, atol=0)
    torch.testing.assert_close(actual.bias, torch.tensor(.4), rtol=0, atol=0)

    data = DataConfig(.8, .5, .5, 2., lambda: 1.)
    actual_se = MacroscopicStateEvolution(data, config, K_w=12, K_g=16)
    reference_se = MacroscopicStateEvolution(data, baseline, K_w=12, K_g=16)
    assert actual_se.initial_pseudo_label is None
    actual_se.compute_trajectory()
    reference_se.compute_trajectory()
    for actual_w, expected_w in zip(actual_se.weight, reference_se.weight):
        torch.testing.assert_close(actual_w, expected_w, rtol=0, atol=0)
    for bias in actual_se.bias:
        torch.testing.assert_close(bias, torch.tensor(.4), rtol=0, atol=0)


def test_custom_loss_penalty_and_initialization_match_the_finite_objective():
    class SquaredLoss(LossFunction):
        def evaluate(self, scores, labels):
            return .5 * torch.sum((scores - labels).square())

        def gradient(self, scores, labels):
            return scores - labels

    class QuarticPenalty(Penalty):
        def evaluate(self, weights):
            return .25 * torch.sum(weights ** 4)

        def gradient(self, weights):
            return weights ** 3

    X, observed, init = _finite_problem()
    config = _config(bias_step_size=.03, bias_pseudo_label_param=.2,
                     loss_function=SquaredLoss(), penalty_function=QuarticPenalty())
    learner = SelfTrainedGradientDescent(config).fit(X, observed, init)
    step = learner.update_records_[0]
    labeled = observed != 0
    rho = float(labeled.double().mean())
    labeled_gradient = torch.zeros_like(observed)
    labeled_gradient[labeled] = (step.scores[labeled] - observed[labeled]) / rho
    pseudo_gradient = step.selection * (step.scores - init.Y_init) / (1 - rho)
    expected_g = -config.step_size * (labeled_gradient + .7 * pseudo_gradient)
    expected_bias_g = -.03 * (labeled_gradient + .2 * pseudo_gradient)
    torch.testing.assert_close(step.g, expected_g)
    torch.testing.assert_close(step.bias_residual, expected_bias_g)
    expected_weight = (init.w_init - .2 * .1 * init.w_init ** 3
                       + math.sqrt(X.shape[1]) / X.shape[0] * (X.T @ expected_g))
    torch.testing.assert_close(learner.weights, expected_weight)
    torch.testing.assert_close(learner.bias, init.b_init + expected_bias_g.mean())

    process = _process(config)
    process.step(0)
    scores = process.preactivation[0]
    selection = config.selection_mask(scores)
    lab = process.indicator / process.rho * (scores - process.label)
    pseudo = (1 - process.indicator) / (1 - process.rho) * selection * (scores - torch.where(scores >= 0, 1., -1.))
    torch.testing.assert_close(process.residual[0], -.2 * (lab + .7 * pseudo))
    torch.testing.assert_close(process.bias_residual[0], -.03 * (lab + .2 * pseudo))
    expected_weight = (process.weight[0] - .2 * .1 * process.weight[0] ** 3
                       + torch.mean(process.label * process.residual[0]) * process.signal
                       + .8 / math.sqrt(2.) * process.backward_noise[0])
    torch.testing.assert_close(process.weight[1], expected_weight)
    torch.testing.assert_close(process.bias[1], process.bias[0] + process.bias_residual[0].mean())
