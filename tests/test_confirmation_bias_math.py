"""Analytic and pairing checks for the additive confirmation-bias suite."""

from dataclasses import replace

import numpy as np
import pytest
import torch

from experiments.confirmation_bias.config import preset
from experiments.confirmation_bias.data import make_paired_base
from experiments.confirmation_bias.optimization import (
    branch_consistency, frozen_objective, minimize_frozen,
)
from src.environment import QuenchedEnvironment


def small_dataset():
    cfg = replace(preset("smoke"), d=4, n_labeled=6, n_unlabeled=10)
    data = make_paired_base(cfg, 49).dataset(0.2)
    return cfg, data


@pytest.mark.parametrize("oracle", [False, True])
def test_scaled_objective_gradient_and_fixed_denominator(oracle):
    cfg, data = small_dataset()
    p0 = np.array([-1, 0, 1, 0, 0, -1, 1, 0, 0, 0])
    z = np.array([0.4, 0.1, -0.3, 0.2, 0.5])
    value, gradient = frozen_objective(z, data.X, data.environment, p0, cfg, oracle)
    X, env = data.X, data.environment
    r = torch.as_tensor(z[0]) + X @ torch.as_tensor(z[1:])
    targets = env.Y[env.I_U] if oracle else torch.as_tensor(p0)
    expected = torch.nn.functional.softplus(-env.Y[env.I_L] * r[env.I_L]).mean()
    expected += cfg.pi / env.M * torch.nn.functional.softplus(-targets[p0 != 0] * r[env.I_U][p0 != 0]).sum()
    expected += cfg.penalty / 2 * np.dot(z[1:], z[1:])
    assert value == pytest.approx(float(expected), abs=1e-13)
    numerical = np.empty(z.size)
    for j in range(z.size):
        step = np.eye(z.size)[j] * 1e-6
        numerical[j] = (frozen_objective(z + step, X, env, p0, cfg, oracle)[0] - frozen_objective(z - step, X, env, p0, cfg, oracle)[0]) / 2e-6
    np.testing.assert_allclose(gradient, numerical, rtol=1e-7, atol=1e-9)


def test_empty_selection_has_no_unlabeled_term_or_intercept_penalty():
    cfg, data = small_dataset()
    p0 = np.zeros(data.environment.M)
    z = np.array([1000.0, 0.1, -0.3, 0.2, 0.5])
    value, gradient = frozen_objective(z, data.X, data.environment, p0, cfg)
    value_zero, gradient_zero = frozen_objective(z, data.X, data.environment, p0, replace(cfg, pi=0))
    assert np.isfinite(value)
    assert np.isfinite(gradient).all()
    assert value == value_zero
    np.testing.assert_array_equal(gradient, gradient_zero)
    _, gradient_no_ridge = frozen_objective(z, data.X, data.environment, p0, replace(cfg, penalty=0))
    assert gradient[0] == gradient_no_ridge[0]
    np.testing.assert_allclose(gradient[1:] - gradient_no_ridge[1:], cfg.penalty * z[1:])


def test_convex_solver_reports_coordinates_residual_and_failures():
    cfg, data = small_dataset()
    p0 = np.zeros(data.environment.M)
    result = minimize_frozen(data.X, data.environment, p0, 0.0, data.initialization.w_init, cfg)
    assert result["converged"]
    assert result["gradient_inf"] <= cfg.solver_residual_tolerance
    assert result["gradient_coordinates"] == "(b,v=w/sqrt(d))"
    z = np.r_[result["b"], result["w"] / np.sqrt(cfg.d)]
    assert frozen_objective(z, data.X, data.environment, p0, cfg)[0] == pytest.approx(result["objective"])
    no_ridge = minimize_frozen(data.X, data.environment, p0, 0.0, data.initialization.w_init, replace(cfg, penalty=0, solver_maxiter=5))
    assert not no_ridge["converged"]
    assert not no_ridge["assumptions"]["finite_unique_minimizer_guaranteed"]
    env = QuenchedEnvironment(data.environment.mu, torch.ones(data.environment.n), data.environment.Delta)
    degenerate = minimize_frozen(data.X, env, p0, 0.0, data.initialization.w_init, cfg)
    assert degenerate["status"] == "no_finite_minimizer"
    assert not degenerate["converged"]
    assert degenerate["nit"] == 0


def test_branch_margins_and_selected_versus_zero_boundary_equalities():
    p0 = np.array([1, -1, 0, 0])
    strict = branch_consistency([2, -2, 0, 0.5], p0, -1, 1)
    np.testing.assert_allclose(strict["margins"], [1, 1, 1, 0.5])
    assert strict["status"] == "numerically strictly self-consistent"
    assert strict["n_violated_inequalities"] == 0
    boundary = branch_consistency([1, -1, -1, 1], p0, -1, 1)
    assert boundary["status"] == "unresolved / near a boundary"
    assert boundary["violations"] == {
        "positive_below_upper": 0, "negative_above_lower": 0,
        "zero_at_or_below_lower": 1, "zero_at_or_above_upper": 1,
    }
    np.testing.assert_array_equal(boundary["induced_configuration"], [1, -1, -1, 1])
    inconsistent = branch_consistency([0, 0, -2, 2], p0, -1, 1)
    assert inconsistent["status"] == "numerically inconsistent"
    assert inconsistent["n_violated_inequalities"] == 4
    failed = branch_consistency([2, -2, 0, 0.5], p0, -1, 1, solver_converged=False)
    assert failed["status"] == "solver failed or insufficiently converged"


def test_paired_nested_counts_reconstruction_and_random_streams():
    cfg = preset("smoke")
    global_state = torch.random.get_rng_state().clone()
    base = make_paired_base(cfg, 49)
    assert torch.equal(torch.random.get_rng_state(), global_state)
    previous_positive = None
    for p in sorted(cfg.imbalance_levels):
        data = base.dataset(p)
        env = data.environment
        expected_labeled = min(cfg.n_labeled - 1, max(1, round(p * cfg.n_labeled)))
        assert int((env.Y[env.I_L] == 1).sum()) == expected_labeled
        assert int((env.Y[env.I_U] == 1).sum()) == round(p * cfg.n_unlabeled)
        positive = env.Y == 1
        if previous_positive is not None:
            assert torch.all(positive[previous_positive])
        previous_positive = positive
        torch.testing.assert_close(data.X, env.Y[:, None] * base.mu / cfg.d**0.5 + cfg.sigma * base.U)
        torch.testing.assert_close(env.Delta, base.Delta)
        torch.testing.assert_close(data.initialization.w_init, base.w_init)
        torch.testing.assert_close(data.initialization.Y_init[env.I_U], base.Y_init[env.I_U])
        torch.testing.assert_close(data.initialization.Y_init[env.I_L], env.Y[env.I_L])
        assert data.metadata["population_p"] == p
    repeated = make_paired_base(cfg, 49)
    assert base.metadata["hashes"] == repeated.metadata["hashes"]
    # Match the repository helper's exact seed+11 draw order and +31 Rademacher
    # convention, rather than merely matching the marginal initialization law.
    rng = torch.Generator().manual_seed(49 + 11)
    torch.testing.assert_close(base.mu, cfg.signal_std * torch.randn(cfg.d, generator=rng))
    torch.testing.assert_close(base.w_init, torch.randn(cfg.d, generator=rng))
    init_rng = torch.Generator().manual_seed(49 + 31)
    expected = torch.where(torch.rand(cfg.n, generator=init_rng) < .5, 1.0, -1.0)
    torch.testing.assert_close(base.Y_init, expected)


def test_shipped_expanded_replicates_have_distinct_random_stream_seeds():
    # Small dimensions suffice to inspect the exact stream recipes; these do
    # not depend on dimensions or sample counts.
    cfg = replace(preset("smoke"), d=1, n_labeled=2, n_unlabeled=1)
    all_streams = [value for seed in preset("expanded").seeds
                   for value in make_paired_base(cfg, seed).metadata["streams"].values()]
    assert len(all_streams) == len(set(all_streams))
