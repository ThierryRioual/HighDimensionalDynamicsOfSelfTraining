"""Behavioral checks for the additive suite's use of the existing engine."""
from dataclasses import replace

import numpy as np
import pytest
import torch

from experiments.confirmation_bias.config import SuiteConfig
from experiments.confirmation_bias.core import (
    checkpoint_initialization,
    configuration,
    fit_trajectory,
    terminal_configuration_type,
)
from experiments.confirmation_bias.data import PairedDataset, make_paired_base
from src.algorithms import SelfTrainedGradientDescent
from src.config import AlgorithmConfig
from src.environment import QuenchedEnvironment
from src.initialization import SelfTrainingInitialization, compute_scores, sign_with_positive_tie
from src.objectives import LogisticLoss


def example(T=4):
    cfg = SuiteConfig(d=3, n_labeled=4, n_unlabeled=9, T=T,
                      eta=.2, penalty=.3, pi=1.7, kappa_minus=-.4, kappa_plus=.6)
    return make_paired_base(cfg, 37).dataset(.2), cfg


def objective_gradient(dataset, cfg, b, w, selected, assigned):
    """Independent analytic-objective autograd check in scaled coordinates."""
    env, X = dataset.environment, dataset.X
    v = (w / env.d**.5).detach().clone().requires_grad_()
    intercept = b.detach().clone().requires_grad_()
    r = intercept + X @ v
    supervised = torch.logaddexp(torch.zeros(env.N, dtype=r.dtype), -env.Y[env.I_L]*r[env.I_L]).mean()
    unlabeled = (selected * torch.logaddexp(torch.zeros(env.M, dtype=r.dtype), -assigned*r[env.I_U])).sum() / env.M
    objective = supervised + cfg.pi*unlabeled + cfg.penalty*v.square().sum()/2
    gb, gv = torch.autograd.grad(objective, (intercept, v))
    return gb, gv


def test_suite_uses_legacy_engine_and_preserves_default():
    dataset, cfg = example()
    result, learner = fit_trajectory(dataset, cfg)
    plain = SelfTrainedGradientDescent(cfg.algorithm_config())
    plain.fit_full(dataset.X, dataset.environment, dataset.initialization)
    assert torch.equal(learner.weights, plain.weights)
    assert torch.equal(learner.bias, plain.bias)
    assert np.array_equal(result['endpoint']['w'], plain.weights.numpy())
    assert AlgorithmConfig(2, .1, .1, 1.0, margin_threshold=1.0).normalize_unlabeled_loss is True
    assert cfg.algorithm_config().normalize_unlabeled_loss is False
    assert type(learner) is SelfTrainedGradientDescent


def test_preconditioned_update_matches_scaled_objective_gradient():
    dataset, cfg = example()
    _, learner = fit_trajectory(dataset, cfg)
    env = dataset.environment
    for t, step in enumerate(learner.update_records_):
        selected = step.selection[env.I_U]
        assigned = step.pseudo_labels[env.I_U]
        gb, gv = objective_gradient(dataset, cfg, step.bias, step.weight, selected, assigned)
        next_b = learner.update_records_[t+1].bias if t+1<cfg.T else learner.bias
        torch.testing.assert_close(next_b, step.bias-cfg.eta*gb, atol=2e-14, rtol=2e-14)
        torch.testing.assert_close(learner.weight_history_[t+1], step.weight-cfg.eta*env.d**.5*gv, atol=2e-14, rtol=2e-14)


def test_bias_oracle_identity_and_special_initial_step():
    dataset, cfg = example()
    env = dataset.environment
    r0 = compute_scores(dataset.X, dataset.initialization.b_init, dataset.initialization.w_init)
    forced = dataset.initialization.Y_init.clone()
    forced[env.I_U] = -sign_with_positive_tie(r0[env.I_U])
    dataset = replace(dataset, initialization=SelfTrainingInitialization(0., dataset.initialization.w_init, forced))
    result, learner = fit_trajectory(dataset, cfg)
    updates = result['updates']
    assert np.isnan(updates['dynamic_self_label_zeta_U'][0])
    for t, record in enumerate(learner.update_records_):
        y, r = env.Y[env.I_U], record.scores[env.I_U]
        assigned, selected = record.pseudo_labels[env.I_U], record.selection[env.I_U]
        expected = cfg.eta * (selected*assigned*torch.sigmoid(-assigned*r)).sum()/env.M
        np.testing.assert_allclose(updates['zeta_U'][t], expected, atol=2e-15)
        if t:
            np.testing.assert_allclose(updates['zeta_U'][t], updates['dynamic_self_label_zeta_U'][t], atol=2e-15)
            np.testing.assert_allclose(updates['beta'][t], updates['beta_assigned'][t], atol=2e-15)
        direct_error = cfg.pi*(expected-cfg.eta*(selected*y*torch.sigmoid(-y*r)).sum()/env.M)
        target_error = -cfg.eta*cfg.pi*(selected*y*(assigned!=y)).sum()/env.M
        torch.testing.assert_close(direct_error, target_error, atol=2e-15, rtol=2e-14)
    np.testing.assert_allclose(updates['bias_update_residual'], 0., atol=2e-15)
    np.testing.assert_allclose(updates['oracle_identity_residual'], 0., atol=2e-15)
    np.testing.assert_allclose(updates['score_update_residual'], 0., atol=5e-15)
    np.testing.assert_allclose(updates['delta_b'], updates['zeta_L']+cfg.pi*updates['zeta_U'], atol=2e-15)


def crossing_example():
    cfg = SuiteConfig(d=1, n_labeled=2, n_unlabeled=3, T=2,
                      eta=.6, penalty=.1, pi=.7, kappa_minus=-1., kappa_plus=1.)
    env = QuenchedEnvironment(torch.ones(1, dtype=torch.float64),
        torch.tensor([1.,-1.,1.,1.,-1.], dtype=torch.float64),
        torch.tensor([1.,1.,0.,0.,0.], dtype=torch.float64))
    X = torch.tensor([[-10.],[10.],[2.],[.4],[-2.]], dtype=torch.float64)
    init = SelfTrainingInitialization(0., torch.ones(1, dtype=torch.float64), env.Y.clone())
    return PairedDataset(X, env, init, {}, .2), cfg


def test_frozen_targets_and_selection_survive_crossings_and_direct_switches():
    dataset, cfg = crossing_example()
    env = dataset.environment
    p0 = torch.tensor([1,0,-1])
    result, learner = fit_trajectory(dataset, cfg, p0=p0)
    first, second = learner.update_records_
    current_configuration = configuration(second.scores[env.I_U], -1., 1.)
    assert current_configuration.tolist() == [-1,-1,1]
    assert second.pseudo_labels[env.I_U].tolist() == [-1.,-1.,1.]
    assigned = torch.tensor([1.,1.,-1.], dtype=torch.float64)
    for record in learner.update_records_:
        assert record.selection[env.I_U].tolist() == [1.,0.,1.]
        expected = -cfg.eta*cfg.pi/(1-env.rho)*record.selection[env.I_U]*LogisticLoss().gradient(record.scores[env.I_U], assigned)
        torch.testing.assert_close(record.g[env.I_U], expected)
    # Direct +1 -> -1 and -1 -> +1 transitions must both remain visible.
    transitions = result['updates']['transition_counts'][0]
    assert transitions[2,0] == 1
    assert transitions[0,2] == 1
    assert transitions[1,0] == 1
    assert result['updates']['switches'][0] == 3
    for crossing in result['updates']['crossings'].values():
        observed = crossing['count'] > 0
        np.testing.assert_allclose(crossing['mean_bias'][observed]+crossing['mean_feature'][observed], crossing['mean_total'][observed], atol=2e-15)


@pytest.mark.parametrize('p0', [[0,0,0], [1,0,0], [1,0,-1]])
def test_frozen_unlabeled_term_uses_fixed_pool_M(p0):
    dataset, cfg = crossing_example()
    result, learner = fit_trajectory(dataset, cfg, p0=torch.tensor(p0))
    env = dataset.environment
    selected = torch.tensor(p0).ne(0).double()
    assigned = torch.tensor(p0, dtype=torch.float64)
    assigned[assigned==0] = 1.
    for t, record in enumerate(learner.update_records_):
        expected = cfg.eta*(selected*assigned*torch.sigmoid(-assigned*record.scores[env.I_U])).sum()/env.M
        np.testing.assert_allclose(result['updates']['zeta_U'][t], expected, atol=2e-15)
        gb, gv = objective_gradient(dataset, cfg, record.bias, record.weight, selected, assigned)
        torch.testing.assert_close(learner.weight_history_[t+1], record.weight-cfg.eta*env.d**.5*gv)
        assert torch.isfinite(record.g).all()
    if not selected.any():
        np.testing.assert_array_equal(result['updates']['zeta_U'], 0.)


def test_checkpoint_replay_exactly_matches_baseline_suffix():
    dataset, cfg = example(T=6)
    full, learner = fit_trajectory(dataset, cfg)
    for t0 in (1, 3, cfg.T):
        b = learner.update_records_[t0].bias if t0<cfg.T else learner.bias
        w = learner.weight_history_[t0]
        initial = checkpoint_initialization(dataset, b, w)
        suffix, replay = fit_trajectory(dataset, cfg, initial, start=t0)
        for expected, actual in zip(learner.weight_history_[t0:], replay.weight_history_):
            assert torch.equal(expected, actual)
        for key, values in full['states'].items():
            np.testing.assert_equal(suffix['states'][key], values[t0:])
        assert len(suffix['updates']['switches']) == cfg.T-t0


def test_ordinary_training_does_not_consult_true_unlabeled_labels():
    dataset, cfg = example()
    truth = dataset.environment.Y.clone()
    truth[dataset.environment.I_U] *= -1
    changed_env = QuenchedEnvironment(dataset.environment.mu, truth, dataset.environment.Delta)
    # Holding X fixed here is an intervention only to audit data leakage, not
    # the paired scientific design (which reconstructs X whenever labels change).
    changed = replace(dataset, environment=changed_env)
    _, first = fit_trajectory(dataset, cfg)
    _, second = fit_trajectory(changed, cfg)
    for a, b in zip(first.weight_history_, second.weight_history_):
        assert torch.equal(a, b)
    assert torch.equal(first.bias, second.bias)


def test_zero_norm_population_tie_and_threshold_conventions():
    dataset, cfg = example(T=2)
    cfg = replace(cfg, T=2)
    initial = SelfTrainingInitialization(0., torch.zeros(cfg.d, dtype=torch.float64), dataset.initialization.Y_init)
    result, _ = fit_trajectory(dataset, cfg, initial, start=cfg.T)
    state = result['states']
    assert state['tau'][0] == 0
    assert state['error'][0] == 1-dataset.p
    assert np.isnan(state['normalized_bias'][0])
    assert np.isnan(state['normalized_alignment'][0])
    np.testing.assert_array_equal(state['prediction_fractions'][0], [0,1])
    scores = torch.tensor([-1., -0., .2, 1.], dtype=torch.float64)
    assert configuration(scores, -1., 1.).tolist() == [-1,0,0,1]
    assert sign_with_positive_tie(scores).tolist() == [-1.,1.,1.,1.]
    assert terminal_configuration_type([-1,-1]) == 'fully negative selected'
    assert terminal_configuration_type([-1,0]) == 'negative selected plus zeros'
