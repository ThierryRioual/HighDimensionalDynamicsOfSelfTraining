"""Low-cost finite/effective-process smoke tests.

These tests do not assert finite-sample agreement with state evolution.  The
finite data and Monte Carlo particles are different populations, so a precise
comparison would require a dedicated convergence experiment with uncertainty
quantification.  Here we check only matched initialization definitions and that
each implementation completes a supervised update with fixed ``pi=0``.
"""

import torch

from src.algorithms import SelfTrainedGradientDescent
from src.asymptotics import MacroscopicStateEvolution
from src.config import AlgorithmConfig, DataConfig
from src.dgp import IsotropicGaussian
from src.environment import QuenchedEnvironment
from src.initialization import SelfTrainingInitialization


def _algorithm_config(pseudo_label_param):
    return AlgorithmConfig(
        n_iterations=1,
        margin_threshold=1.0,
        step_size=0.1,
        penalty_param=0.1,
        pseudo_label_param=pseudo_label_param,
        train_bias=True,
    )


def _matched_setup():
    dimensions = 32
    n_train = 96
    signal = torch.linspace(-1.0, 1.0, dimensions, dtype=torch.float64)
    initial_weight = torch.linspace(
        1.0, -0.5, dimensions, dtype=torch.float64
    )
    initial_bias = 0.2
    data_cfg = DataConfig(
        scale=1.2,
        label_prior=0.4,
        supervision_ratio=0.25,
        data_to_dimension_ratio=n_train / dimensions,
        signal_law=lambda: 0.0,
    )
    return (
        dimensions,
        n_train,
        signal,
        initial_weight,
        initial_bias,
        data_cfg,
    )


def _fixed_parameter_sampler(signal, initial_weight):
    def sampler(size, generator, dtype, device):
        del generator
        assert size == signal.numel()
        return (
            signal.to(dtype=dtype, device=device),
            initial_weight.to(dtype=dtype, device=device),
        )

    return sampler


def test_matched_initialization_has_identical_macroscopic_definitions():
    (
        dimensions,
        _,
        signal,
        initial_weight,
        initial_bias,
        data_cfg,
    ) = _matched_setup()
    se = MacroscopicStateEvolution(
        data_cfg=data_cfg,
        algo_cfg=_algorithm_config(pseudo_label_param=0.0),
        K_w=dimensions,
        K_g=47,
        initial_bias=initial_bias,
        parameter_base_sampler=_fixed_parameter_sampler(signal, initial_weight),
        mc_seed=23,
    )

    finite_alignment = torch.mean(signal * initial_weight)
    finite_norm = torch.sqrt(torch.mean(initial_weight.square())).item()

    torch.testing.assert_close(se.signal, signal)
    torch.testing.assert_close(se.weight[0], initial_weight)
    torch.testing.assert_close(se.bias[0], torch.tensor(initial_bias))
    torch.testing.assert_close(
        se.compute_weight_signal_alignment(0), finite_alignment
    )
    assert se.compute_weight_norm(0) == finite_norm


def test_finite_and_effective_process_complete_one_supervised_smoke_step():
    (
        dimensions,
        n_train,
        signal,
        initial_weight,
        initial_bias,
        data_cfg,
    ) = _matched_setup()
    supervised_cfg = _algorithm_config(pseudo_label_param=0.0)

    dgp = IsotropicGaussian(
        cfg=data_cfg,
        n_train=n_train,
        n_test=0,
        dimensions=dimensions,
        seed=29,
        signal_vector=signal,
    )
    environment, X, _, _ = dgp.sample(stratified=True)
    # Use labeled-then-unlabeled row order and inactive t=0
    # pseudo-label placeholders without drawing additional random numbers.
    order = torch.cat((environment.I_L, environment.I_U))
    environment = QuenchedEnvironment(
        environment.mu, environment.Y[order], environment.Delta[order]
    )
    X = X[order]
    y_init = environment.Y.clone()
    y_init[environment.I_U] = 1.
    initialization = SelfTrainingInitialization(
        initial_bias, initial_weight, y_init
    )

    finite = SelfTrainedGradientDescent(cfg=supervised_cfg)
    finite.fit(X, environment.Y * environment.Delta, initialization)
    step = finite.update_records_[0]
    assert torch.count_nonzero(step.g[environment.I_U]) == 0
    expected_labeled = -supervised_cfg.step_size / environment.rho * supervised_cfg.loss_function.gradient(
        step.scores[environment.I_L], environment.Y[environment.I_L]
    )
    torch.testing.assert_close(step.g[environment.I_L], expected_labeled)
    assert torch.isfinite(finite.weights).all() and torch.isfinite(finite.bias)

    state_evolution = MacroscopicStateEvolution(
        data_cfg=data_cfg,
        algo_cfg=supervised_cfg,
        K_w=dimensions,
        K_g=53,
        initial_bias=initial_bias,
        parameter_base_sampler=_fixed_parameter_sampler(signal, initial_weight),
        mc_seed=31,
    )
    state_evolution.step(0)

    # This is a separate Monte Carlo smoke check, not an assertion that its
    # realized first iterate equals the finite-dimensional one.
    assert torch.isfinite(state_evolution.weight[1]).all()
    assert torch.isfinite(state_evolution.bias[1])
    assert torch.isfinite(state_evolution.preactivation[0]).all()
    assert torch.isfinite(state_evolution.residual[0]).all()
    assert state_evolution._current_t == 1
