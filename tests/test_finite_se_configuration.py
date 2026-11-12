"""A matching finite/SE configuration smoke test, without a false finite-K equality claim."""

import torch

from src.algorithms import SelfTrainedGradientDescent
from src.asymptotics import MacroscopicStateEvolution
from src.config import AlgorithmConfig, DataConfig
from src.dgp import IsotropicGaussian
from src.environment import (
    FourCellSampleTypeLaw,
    state_evolution_sample_base_sampler,
)
from src.initialization import SelfTrainingInitialization


def test_finite_and_se_share_a_fixed_pi_joint_law_configuration():
    d, n = 20, 80
    law = FourCellSampleTypeLaw((.15, .25, .05, .55))
    data = DataConfig(scale=.8, label_prior=law.label_prior, supervision_ratio=law.supervision_ratio, data_to_dimension_ratio=n/d, signal_law=lambda: .3)
    cfg = AlgorithmConfig(n_iterations=1, step_size=.1, penalty_param=.1, pseudo_label_param=.7, margin_threshold=.5,
                          bias_pseudo_label_param=.3)
    dgp = IsotropicGaussian(cfg=data, n_train=n, dimensions=d, n_test=0, signal_vector=torch.full((d,), .3), sample_type_law=law, seed=4)
    env = dgp.sample_environment()
    assert env.delta == data.data_to_dimension_ratio
    X, _ = dgp.sample_design(env)
    y_init = env.Y.clone()
    y_init[env.I_U] = 1.
    finite = SelfTrainedGradientDescent(cfg).fit(X, env.Y * env.Delta, SelfTrainingInitialization(0., torch.ones(d), y_init))
    assert torch.isfinite(finite.weights).all()
    se = MacroscopicStateEvolution(data, cfg, K_w=37, K_g=41, sample_base_sampler=state_evolution_sample_base_sampler(law), mc_seed=4,
                                  initial_weight=torch.ones(37))
    se.compute_trajectory()
    assert torch.isfinite(se.weight[1]).all()
    assert len(se.theorem_trajectory.G) == 1

    step = finite.update_records_[0]
    torch.testing.assert_close(step.omega, step.selection[env.I_U].mean())
    se_mask = se.selection_mask(se.preactivation[0])
    torch.testing.assert_close(se.selection_rate[0], ((1 - se.indicator) * se_mask).mean() / (1 - se.rho))
    for factor, scores, Y, Delta, Yhat, selection, omega, rho, g, bias_g in [
        (-cfg.step_size, step.scores, env.Y, env.Delta, y_init, step.selection, step.omega, env.rho, step.g, step.bias_residual),
        (1., se.preactivation[0], se.label, se.indicator, torch.where(se.preactivation[0] >= 0, 1., -1.),
         se_mask, se.selection_rate[0], se.rho, se.residual[0], se.bias_residual[0]),
    ]:
        assert 0 < omega < 1
        labeled = Delta / rho * cfg.loss_function.gradient(scores, Y)
        for pi, actual in [(cfg.pseudo_label_param, g), (cfg.bias_pseudo_label_param, bias_g)]:
            unlabeled = (1 - Delta) * pi / (1 - rho) * selection * cfg.loss_function.gradient(scores, Yhat)
            assert torch.count_nonzero(unlabeled) > 0
            torch.testing.assert_close(actual, factor * (labeled + unlabeled))
