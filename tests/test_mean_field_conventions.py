"""Compare manuscript units with immutable outputs captured before the refactor."""
import json
from pathlib import Path

import pytest
import torch

from src.asymptotics import MacroscopicStateEvolution
from src.config import AlgorithmConfig, DataConfig

FIXTURES = Path(__file__).parent / 'fixtures' / 'mean_field_conventions'
METADATA = json.loads((FIXTURES / 'metadata.json').read_text())
BASELINE = torch.load(FIXTURES / 'baseline.pt', weights_only=True)
RTOL, ATOL = 2e-9, 2e-10
# Coordinates and raw phi become ill-conditioned at small eta; predictions
# retain the tighter tolerance above. These are absolute coordinate tolerances.
COORDINATE_ATOL = 1e-7
COORDINATES = {'B_w', 'B_g', 'Q_w', 'P_g', 'phi_w', 'phi_g', 'alpha_w', 'alpha_g', 'gamma_w', 'gamma_g'}


def make_process(config):
    eta, mode = config['eta'], config['mode']
    algo = AlgorithmConfig(
        n_iterations=5, step_size=eta, penalty_param=.1,
        pseudo_label_param=0. if mode == 'supervised' else .7,
        margin_threshold=.4, initial_bias=.2,
        bias_step_size=.07 if mode == 'truncated' else None,
        bias_pseudo_label_param=.2 if mode == 'truncated' else None,
    )
    return MacroscopicStateEvolution(
        DataConfig(scale=1.3, label_prior=.4, supervision_ratio=.3,
                   data_to_dimension_ratio=2.3, signal_law=lambda: 1.),
        algo, K_w=53, K_g=71, mc_seed=123,
        eps_rank=.1 if mode == 'truncated' else 1e-10, lstsq_driver='gelsd',
    )


def snapshot(process):
    result = {name: getattr(process, name) for name in METADATA['histories']}
    result.update(phi_w=[process.compute_weight_memory(t) for t in range(process.T + 1)],
                  phi_g=[process.compute_residual_memory(t) for t in range(process.T + 1)])
    for name in ('B_w', 'B_g', 'Theta_w', 'Theta_g', 'Q_w', 'P_g',
                 'W_ring', 'G_ring', 'Q_ring', 'P_ring', 'z_g', 'z_w'):
        result[name] = getattr(process, name)
    result['C_w'] = process.W_ring.T @ process.W_ring / process.K_w
    result['C_g'] = process.G_ring.T @ process.G_ring / process.K_g
    return result


def response_structure(values):
    """Projection/cumulative responses reconstructed in the maintained basis.

    No additional rank cutoff is introduced: gelsd uses the same default rcond
    as the recorded production solves. This also covers truncated histories.
    """
    responses = {}
    for side in ('w', 'g'):
        theta = values['Theta_' + side]
        ranks = values['weight_rank' if side == 'w' else 'residual_rank']
        alphas, gammas = [], []
        for t in range(theta.shape[1]):
            rank_before = ranks[t-1] if t else 0
            alpha = (torch.linalg.lstsq(theta[:rank_before, :t],
                                       theta[:rank_before, t], driver='gelsd').solution
                     if rank_before else theta.new_zeros(t))
            gamma = values['phi_' + side][t].clone()
            for u in range(t):
                gamma[:gammas[u].numel()] += alpha[u] * gammas[u]
            alphas.append(alpha)
            gammas.append(gamma)
        responses['alpha_' + side] = alphas
        responses['gamma_' + side] = gammas
        target = 'g' if side == 'w' else 'w'
        scales = values['forward_innovation_scale' if side == 'w' else 'backward_innovation_scale']
        gaussian = []
        for t, alpha in enumerate(alphas):
            xi = scales[t] * values['z_' + target][t]
            for u in range(t):
                xi = xi + alpha[u] * gaussian[u]
            gaussian.append(xi)
        responses['xi_' + target] = gaussian
        xi_matrix = torch.stack(gaussian, dim=1)
        responses['C_xi_' + target] = xi_matrix.T @ xi_matrix / xi_matrix.shape[0]
    return responses


def old_over_new(name, config):
    eta = config['eta']
    if name in ('residual', 'backward_noise', 'label_residual_alignments',
                'mean_residual', 'residual_memory_coordinates', 'phi_g', 'gamma_g', 'G_ring', 'P_ring', 'xi_w'):
        return -eta
    if name in ('bias_residual', 'mean_bias_residual'):
        return -(.07 if config['mode'] == 'truncated' else eta)
    if name in ('backward_innovation_scale', 'Theta_g'):
        return eta
    if name in ('C_g', 'C_xi_w'):
        return eta ** 2
    if name in ('phi_w', 'gamma_w'):
        return -1 / eta
    if name in ('B_g', 'P_g', 'weight_memory_coordinates', 'z_w'):
        return -1
    return 1


@pytest.mark.parametrize('index', range(len(BASELINE)))
def test_seeded_pre_refactor_equivalence(index):
    config = METADATA['configs'][index]
    process = make_process(config)
    process.compute_trajectory()
    current = snapshot(process)
    old_snapshot = dict(BASELINE[index])
    old_snapshot.update(response_structure(old_snapshot))
    current.update(response_structure(current))
    for name, old_values in old_snapshot.items():
        new_values = current[name]
        if not isinstance(old_values, list):
            old_values, new_values = [old_values], [new_values]
        for old, new in zip(old_values, new_values):
            if isinstance(old, (bool, int)):
                assert old == new, name
            else:
                torch.testing.assert_close(
                    torch.as_tensor(new) * old_over_new(name, config),
                    torch.as_tensor(old), rtol=RTOL, atol=COORDINATE_ATOL if name in COORDINATES else ATOL, msg=name,
                )
    if config['mode'] == 'truncated':
        assert any(process.weight_rank_truncated) or any(process.residual_rank_truncated)

    for t in range(process.T + 1):
        r = process.preactivation[t]
        labels = torch.where(r >= 0, 1., -1.)
        cfg = process.algo_cfg
        expected_g = process.indicator / process.rho * cfg.loss_function.gradient(r, process.label)
        expected_g += ((1-process.indicator) / (1-process.rho) * cfg.pseudo_label_param
                       * cfg.selection_mask(r) * cfg.loss_function.gradient(r, labels))
        torch.testing.assert_close(process.residual[t], expected_g)
        if t < process.T:
            torch.testing.assert_close(process.weight[t+1], process.weight[t] - process.eta * (
                cfg.penalty_param * cfg.penalty_function.gradient(process.weight[t])
                + process.label_residual_alignments[t] * process.signal
                + process.sigma / process.delta**.5 * process.backward_noise[t]))
            torch.testing.assert_close(process.bias[t+1], process.bias[t]
                                      - cfg.get_bias_step_size() * process.mean_bias_residual[t])


@pytest.mark.parametrize('eta_b', [0., .07])
def test_bias_gradient_is_independent_of_rate(eta_b):
    process = make_process({'eta': .3, 'mode': 'self_training'})
    from dataclasses import replace
    process.algo_cfg = replace(process.algo_cfg, bias_step_size=eta_b)
    process.step(0)
    torch.testing.assert_close(process.bias_residual[0], process.residual[0])
    torch.testing.assert_close(process.bias[1], process.bias[0]
                              - eta_b * process.residual[0].mean())


@pytest.mark.parametrize('eta', [.1, .2, .7])
def test_maintained_figure_runner_against_original_predictions(eta):
    import math
    import numpy as np
    from figures.experiments import MonteCarloConfig, run_monte_carlo_experiment
    config = MonteCarloConfig(
        data=DataConfig(scale=1., label_prior=.4, supervision_ratio=.1,
                        data_to_dimension_ratio=2., signal_law=lambda: float(torch.randn(()))),
        algorithm=AlgorithmConfig(n_iterations=8, step_size=eta, penalty_param=.1,
                                  pseudo_label_param=2., margin_threshold=math.log(4)),
        d=128, k=512, runs=2, seed=49,
    )
    current = run_monte_carlo_experiment(config)
    with np.load(FIXTURES / 'workflow_baseline.npz') as old:
        for side in ('self_training', 'effective_process'):
            for name, values in current[side].items():
                np.testing.assert_allclose(values, old[f'{eta}/{side}/{name}'],
                                           rtol=RTOL, atol=ATOL)


@pytest.mark.parametrize('dtype', [torch.float32, torch.float64])
@pytest.mark.parametrize('scale', [.001, .3, 2., 1000.])
@pytest.mark.parametrize('rcond', [None, 1e-4])
def test_rank_and_transport_cutoffs_are_scale_invariant(dtype, scale, rcond):
    from src.orthogonal import EmpiricalOrthogonalBasis, solve_transported_history
    # Independent, dependent, and deliberately truncated directions.
    history = torch.tensor([[1., 2., 1., 0.], [0., 0., .001, 1.],
                            [0., 0., 0., .3], [0., 0., 0., .1]], dtype=dtype)
    original = EmpiricalOrthogonalBasis(4, eps_rank=.01, dtype=dtype)
    rescaled = EmpiricalOrthogonalBasis(4, eps_rank=.01, dtype=dtype)
    for column in history.T:
        left = original.project_and_update(column)
        right = rescaled.project_and_update(-column / scale)
        assert left.rank_after == right.rank_after
        assert left.truncated == right.truncated
    tolerance = 2e-5 if dtype == torch.float32 else 1e-12
    torch.testing.assert_close(original.B, -rescaled.B, rtol=tolerance, atol=tolerance)
    torch.testing.assert_close(original.Theta, scale * rescaled.Theta,
                               rtol=tolerance, atol=tolerance)
    transported = torch.arange(12, dtype=dtype).reshape(3, 4)
    before = solve_transported_history(transported, original.Theta,
                                       rcond=rcond, driver='gelsd')
    after = solve_transported_history(-transported / scale, rescaled.Theta,
                                      rcond=rcond, driver='gelsd')
    torch.testing.assert_close(before, -after, rtol=tolerance, atol=tolerance)
