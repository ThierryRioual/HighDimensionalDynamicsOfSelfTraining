"""Execute both diagnostic notebooks in separate clean kernels against a cache.

No training is launched. Run the suite runner first. Executed copies are saved
inside that configuration's output directory; source notebooks are preserved.
"""
import argparse
import os
import re
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

import nbformat
from nbclient import NotebookClient
from experiments.confirmation_bias.config import preset
from experiments.confirmation_bias.runner import load_suite


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',choices=['smoke','pilot','expanded'],default='smoke')
    parser.add_argument('--timeout',type=int,default=300)
    args=parser.parse_args()
    suite=load_suite(preset(args.profile))
    destination=Path(suite['output_dir'])/'notebooks'
    destination.mkdir(parents=True,exist_ok=True)
    os.environ['CONFIRMATION_PROFILE']=args.profile
    os.environ.setdefault('MPLBACKEND','Agg')
    for name in ['15_checkpoint_branch_consistency.ipynb','16_paired_imbalance_branch_outcomes.ipynb']:
        notebook=nbformat.read(ROOT/'notebooks'/name,as_version=4)
        # Preserve source links when an executed copy lives below outputs/.
        for cell in notebook.cells:
            if cell.cell_type == 'markdown':
                def relocated(match):
                    target = match.group(1)
                    if '://' in target or target.startswith('#'):
                        return match.group(0)
                    if target in ['15_checkpoint_branch_consistency.ipynb', '16_paired_imbalance_branch_outcomes.ipynb']:
                        return match.group(0)
                    resolved = (ROOT/'notebooks'/target).resolve()
                    return '](' + os.path.relpath(resolved, destination) + ')'
                cell.source = re.sub(r'\]\(([^)]+)\)', relocated, cell.source)
        client=NotebookClient(notebook,timeout=args.timeout,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}})
        client.execute()
        target=destination/name
        nbformat.write(notebook,target)
        print(f'Executed {target}',flush=True)


if __name__=='__main__': main()
