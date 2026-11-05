"""Raw, inclusive confidence margins shared by finite GD and state evolution."""

import pytest
import torch

from src.algorithms import SelfTrainedGradientDescent
from src.asymptotics import MacroscopicStateEvolution
from src.config import AlgorithmConfig, DataConfig
from src.dgp import IsotropicGaussian
from src.environment import FourCellSampleTypeLaw, state_evolution_sample_base_sampler
from src.initialization import SelfTrainingInitialization
from src.objectives import LogisticLoss
from src.primitives import pseudo_residual


def test_default_particle_sampler_does_not_draw_initial_pseudo_labels():
    law = FourCellSampleTypeLaw.product(label_prior=.4, supervision_ratio=.5)
    generator = torch.Generator().manual_seed(19)
    reference = torch.Generator().manual_seed(19)
    label, indicator, initial = state_evolution_sample_base_sampler(law)(
        32, generator, torch.float64, torch.device("cpu"),
    )
    expected_label, expected_indicator = law.sample(
        32, generator=reference, dtype=torch.float64, device=torch.device("cpu"),
    )
    assert initial is None
    torch.testing.assert_close(label, expected_label, rtol=0, atol=0)
    torch.testing.assert_close(indicator, expected_indicator, rtol=0, atol=0)
    assert torch.equal(generator.get_state(), reference.get_state())


def test_selected_fraction_does_not_rescale_unlabeled_loss():
    scores = torch.tensor([2., 2.])
    arguments = dict(scores=scores, Y=torch.ones(2), Delta=torch.zeros(2),
                     Yhat=torch.ones(2), pi=.7, eta=.1, rho=.5, loss_function=LogisticLoss())
    one_selected = pseudo_residual(selection=torch.tensor([1., 0.]), **arguments)
    both_selected = pseudo_residual(selection=torch.ones(2), **arguments)
    torch.testing.assert_close(one_selected[0], both_selected[0], rtol=0, atol=0)
    assert one_selected[1] == 0


@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_asymmetric_confidence_boundaries_are_inclusive(dtype):
    cfg = AlgorithmConfig(1, .1, 0., .4, positive_margin=.8, negative_margin=-.3)
    scores = torch.tensor([-.31, -.3, -.29, 0., .79, .8, .81], dtype=dtype)
    selected = cfg.selection_mask(scores)
    torch.testing.assert_close(selected, torch.tensor([1., 1., 0., 0., 0., 1., 1.], dtype=dtype))
    assert selected.device == scores.device
    assert not torch.equal(cfg.selection_mask(scores), cfg.selection_mask(3 * scores))


def test_small_finite_and_particle_experiment_uses_raw_margins():
    cfg = AlgorithmConfig(2, .1, .1, .4, positive_margin=.7, negative_margin=-.3)
    data = DataConfig(1.7, .4, .4, 3., lambda: 1.)
    dgp = IsotropicGaussian(data, n_train=72, dimensions=24, seed=17)
    env, X, _, _ = dgp.sample()
    init = SelfTrainingInitialization(0., torch.ones(24), env.Y.clone())
    learner = SelfTrainedGradientDescent(cfg).fit(X, env.Y * env.Delta, init)
    for step in learner.update_records_:
        expected = ((step.scores <= -.3) | (step.scores >= .7)).double() * (1 - env.Delta)
        assert torch.equal(step.selection, expected)
        assert torch.isfinite(step.g).all()
    process = MacroscopicStateEvolution(
        data, cfg, K_w=64, K_g=96, mc_seed=17,
        sample_base_sampler=state_evolution_sample_base_sampler(dgp.law),
    )
    process.compute_trajectory()
    for t, scores in enumerate(process.preactivation):
        expected = ((scores <= -.3) | (scores >= .7)).double()
        assert torch.equal(process.selection_mask(scores), expected)
        torch.testing.assert_close(process.selection_rate[t],
                                   ((1 - process.indicator) * expected).mean() / (1 - process.rho))


@pytest.mark.parametrize("bias_pi", [None, .2])
def test_effective_process_freezes_one_selection_mask_per_step(monkeypatch, bias_pi):
    calls = []
    selection_mask = AlgorithmConfig.selection_mask

    def counted(config, scores):
        calls.append(scores)
        return selection_mask(config, scores)

    monkeypatch.setattr(AlgorithmConfig, "selection_mask", counted)
    cfg = AlgorithmConfig(2, .1, .1, .4, positive_margin=.7, negative_margin=-.3,
                          bias_pseudo_label_param=bias_pi)
    data = DataConfig(.8, .5, .5, 2., lambda: 1.)
    dgp = IsotropicGaussian(data, n_train=8, dimensions=4)
    process = MacroscopicStateEvolution(
        data, cfg, K_w=24, K_g=32,
        sample_base_sampler=state_evolution_sample_base_sampler(dgp.law),
    )
    process.compute_trajectory()
    assert len(calls) == cfg.n_iterations + 1
