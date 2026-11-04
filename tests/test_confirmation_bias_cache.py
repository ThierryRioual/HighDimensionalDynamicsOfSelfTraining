"""Cache persistence and compatibility, independent of numerical training."""
import numpy as np
import pytest

from experiments.confirmation_bias.runner import load_result, save_result, validate_resume_runtime


def test_result_round_trip_and_no_overwrite(tmp_path):
    result = {'status':'complete','scalars':{'undefined':float('nan'),'value':.2},
              'checkpoints':[{'w':np.array([1.,2.]),'counts':np.arange(9).reshape(3,3)}]}
    save_result(tmp_path,result)
    restored=load_result(tmp_path)
    assert np.isnan(restored['scalars']['undefined'])
    np.testing.assert_array_equal(restored['checkpoints'][0]['counts'],result['checkpoints'][0]['counts'])
    np.testing.assert_array_equal(restored['checkpoints'][0]['w'],result['checkpoints'][0]['w'])
    with pytest.raises(FileExistsError): save_result(tmp_path,{'status':'different'})
    assert load_result(tmp_path)['status']=='complete'


def test_resume_rejects_mixed_runtime():
    recorded=dict(python='3.x',platform='cpu',numpy='a',scipy='b',torch='c',torch_threads=2)
    validate_resume_runtime(recorded,dict(recorded))
    for key in recorded:
        changed={**recorded,key:'different'}
        with pytest.raises(RuntimeError,match='separate --output-root'):
            validate_resume_runtime(recorded,changed)


def test_notebook_runs_exact_overridden_config(monkeypatch, tmp_path):
    from dataclasses import replace
    import torch
    from experiments.confirmation_bias import runner
    from experiments.confirmation_bias.config import SuiteConfig
    cfg = replace(SuiteConfig(), d=17, n_labeled=6, n_unlabeled=31, T=9)
    def missing(*args, **kwargs):
        raise FileNotFoundError('new configuration')
    monkeypatch.setattr(runner, 'load_suite', missing)
    calls = []
    def run(actual, output_root):
        calls.append((actual, output_root, torch.get_num_threads()))
        return {'config': actual.to_dict()}
    monkeypatch.setattr(runner, 'run_suite', run)
    before = torch.get_num_threads()
    with pytest.raises(RuntimeError, match='ALLOW_RUN=True'):
        runner.load_or_run_suite(cfg, tmp_path)
    assert not calls
    result = runner.load_or_run_suite(cfg, tmp_path, allow_run=True)
    assert calls == [(cfg, tmp_path, 2)]
    assert calls[0][0] is cfg
    assert result['config']['d'] == 17
    assert torch.get_num_threads() == before


def test_complete_notebook_cache_never_retrains(monkeypatch, tmp_path):
    from experiments.confirmation_bias import runner
    from experiments.confirmation_bias.config import SuiteConfig
    cached = {'runs': ['cached']}
    monkeypatch.setattr(runner, 'load_suite', lambda *a, **kw: cached)
    def forbidden(*args, **kwargs):
        raise AssertionError('complete cache must not train')
    monkeypatch.setattr(runner, 'run_suite', forbidden)
    for allow in [False, True]:
        assert runner.load_or_run_suite(SuiteConfig(), tmp_path, allow_run=allow) is cached
