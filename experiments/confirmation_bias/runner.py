"""Reproducible, resumable targeted experiments; no import-time training.

Run: python3 -m experiments.confirmation_bias.runner --profile smoke
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

import numpy as np
import scipy
import torch

from .config import preset
from .core import run_checkpoint_experiment
from .data import make_paired_base

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / 'outputs' / 'confirmation_bias'
SCHEMA_VERSION = 1


def source_fingerprints():
    files = sorted((ROOT/'src').glob('*.py')) + [Path(__file__).with_name(n+'.py')
        for n in ['config','core','data','optimization']]
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def configuration_id(cfg):
    payload = {'schema':SCHEMA_VERSION,'config':cfg.to_dict(),'sources':source_fingerprints()}
    return cfg.profile+'-'+hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()[:16]


def output_directory(cfg, output_root=DEFAULT_OUTPUT):
    return Path(output_root)/configuration_id(cfg)


def _git(*args):
    try:
        return subprocess.check_output(['git',*args],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
    except (OSError,subprocess.CalledProcessError):
        return None


def software_metadata():
    return dict(python=sys.version,platform=platform.platform(),numpy=np.__version__,scipy=scipy.__version__,
        torch=torch.__version__,git_commit=_git('rev-parse','HEAD'),git_status=_git('status','--short'),
        torch_threads=torch.get_num_threads(),source_fingerprints=source_fingerprints())


def save_result(directory, result):
    """JSON structure plus non-pickled compressed arrays, written atomically."""
    directory = Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    if (directory/'result.json').exists():
        raise FileExistsError(f'Refusing to overwrite {directory}')
    arrays = {}
    def encode(obj):
        if isinstance(obj,np.ndarray):
            key = f'a{len(arrays)}'
            arrays[key] = obj
            return {'__array__':key}
        if isinstance(obj,torch.Tensor): return encode(obj.detach().cpu().numpy())
        if isinstance(obj,dict): return {str(k):encode(v) for k,v in obj.items()}
        if isinstance(obj,(list,tuple)): return [encode(v) for v in obj]
        if isinstance(obj,np.generic): return encode(obj.item())
        if isinstance(obj,float) and not np.isfinite(obj): return {'__float__':str(obj)}
        return obj
    encoded = encode(result)
    temporary = directory/'arrays.partial.npz'
    np.savez_compressed(temporary,**arrays)
    temporary.replace(directory/'arrays.npz')
    temporary_json = directory/'result.partial.json'
    temporary_json.write_text(json.dumps(encoded,indent=2,allow_nan=False)+'\n')
    temporary_json.replace(directory/'result.json')


def load_result(directory):
    directory=Path(directory)
    with np.load(directory/'arrays.npz',allow_pickle=False) as archive:
        def decode(obj):
            if isinstance(obj,dict):
                if set(obj)=={'__array__'}: return archive[obj['__array__']].copy()
                if set(obj)=={'__float__'}: return float(obj['__float__'])
                return {k:decode(v) for k,v in obj.items()}
            if isinstance(obj,list): return [decode(v) for v in obj]
            return obj
        return decode(json.loads((directory/'result.json').read_text()))


def run_name(seed,p):
    return f'seed_{seed}_p_{p:.8g}'.replace('.','p')


def load_suite(cfg,output_root=DEFAULT_OUTPUT):
    directory=output_directory(cfg,output_root)
    if not (directory/'suite.json').exists():
        raise FileNotFoundError(f'No compatible cache at {directory}. Run python3 -m experiments.confirmation_bias.runner --profile {cfg.profile}')
    metadata=json.loads((directory/'suite.json').read_text())
    runs=[load_result(directory/run_name(seed,p)) for seed in cfg.seeds for p in cfg.imbalance_levels]
    if any(r.get('status')!='complete' for r in runs): raise RuntimeError('Incomplete suite cache')
    return dict(config=cfg.to_dict(),runs=runs,metadata=metadata,output_dir=str(directory))


def load_or_run_suite(cfg, output_root=DEFAULT_OUTPUT, allow_run=False, threads=2):
    """Load first; optionally train the exact supplied notebook configuration.

    Do not reconstruct cfg from its profile name: notebook overrides must reach
    both the trainer and cache lookup unchanged. Complete caches never retrain.
    """
    try:
        return load_suite(cfg, output_root)
    except FileNotFoundError as exc:
        if not allow_run:
            raise RuntimeError(
                f'No complete cache for the current CONFIG at {output_directory(cfg, output_root)}. '
                'Set ALLOW_RUN=True in the notebook configuration cell and rerun '
                'that cell and the load/run cell to generate these exact settings.'
            ) from exc
    if threads < 1:
        raise ValueError('threads must be positive')
    previous_threads = torch.get_num_threads()
    try:
        torch.set_num_threads(threads)
        return run_suite(cfg, output_root)
    finally:
        torch.set_num_threads(previous_threads)


def validate_resume_runtime(recorded, current):
    """Avoid silently mixing newly trained runs from different runtimes.

    Reading an old cache is allowed. Extending it requires matching numerical
    software/platform/thread metadata; an alternative output root separates a
    deliberately different runtime without modifying the old results.
    """
    keys = ('python','platform','numpy','scipy','torch','torch_threads')
    changed = [key for key in keys if recorded.get(key) != current.get(key)]
    if changed:
        raise RuntimeError('Refusing to mix cached runs across runtime changes: '
                           + ', '.join(changed)
                           + '. Load the existing cache, or use a separate --output-root for new runs.')


def run_suite(cfg,output_root=DEFAULT_OUTPUT):
    directory=output_directory(cfg,output_root)
    directory.mkdir(parents=True,exist_ok=True)
    manifest=directory/'suite.json'
    if manifest.exists():
        recorded = json.loads(manifest.read_text())
        validate_resume_runtime(recorded['software'], software_metadata())
    if not manifest.exists():
        manifest.write_text(json.dumps(dict(configuration_id=configuration_id(cfg),schema_version=SCHEMA_VERSION,
            config=cfg.to_dict(),software=software_metadata(),created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
            normalization='fixed total unlabeled pool M',
            initial_step='exogenous Rademacher Y_init at t=0, score signs at t>=1',
            purpose='software validation only' if cfg.profile=='smoke' else 'targeted diagnostic experiment'),indent=2)+'\n')
    for seed in cfg.seeds:
        base=None
        for p in cfg.imbalance_levels:
            dest=directory/run_name(seed,p)
            if (dest/'result.json').exists():
                cached=load_result(dest)
                if cached.get('status')!='complete': raise RuntimeError(f'Incomplete cached result: {dest}')
                print(f'Cache: seed={seed}, p={p}',flush=True)
                continue
            if base is None: base=make_paired_base(cfg,seed)
            dest.mkdir(parents=True,exist_ok=True)
            started=time.monotonic()
            status=dict(seed=seed,p=p,status='running',started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
            (dest/'status.json').write_text(json.dumps(status,indent=2)+'\n')
            print(f'Running {cfg.profile}: seed={seed}, p={p}',flush=True)
            try:
                dataset=base.dataset(p)
                result=run_checkpoint_experiment(dataset,cfg,seed)
                result.update(status='complete',elapsed_seconds=time.monotonic()-started,
                    config=cfg.to_dict(),configuration_id=configuration_id(cfg))
                save_result(dest,result)
                status.update(status='complete',elapsed_seconds=result['elapsed_seconds'])
                s=result['summary']
                print(f'  best={s["best_error"]:.6f}, final={s["terminal_error"]:.6f}, t_best={result["t_best"]}, {result["elapsed_seconds"]:.1f}s',flush=True)
                del dataset,result
            except Exception as error:
                status.update(status='failed',error=repr(error),traceback=traceback.format_exc(),elapsed_seconds=time.monotonic()-started)
                raise
            finally:
                (dest/'status.json').write_text(json.dumps(status,indent=2)+'\n')
        del base
    print(f'Results: {directory}',flush=True)
    return load_suite(cfg,output_root)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',choices=['smoke','pilot','expanded'],default='smoke')
    parser.add_argument('--output-root',type=Path,default=DEFAULT_OUTPUT)
    parser.add_argument('--seeds',type=int,nargs='+',help='Optional explicit seed list; creates a distinct configuration ID')
    parser.add_argument('--threads',type=int,default=2,help='Torch CPU threads (metadata recorded)')
    args=parser.parse_args()
    if args.threads<1: parser.error('--threads must be positive')
    torch.set_num_threads(args.threads)
    cfg=preset(args.profile)
    if args.seeds: cfg=replace(cfg,seeds=tuple(args.seeds))
    run_suite(cfg,args.output_root)


if __name__=='__main__': main()
