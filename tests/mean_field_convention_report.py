"""Run with MPLBACKEND=Agg python3 tests/mean_field_convention_report.py."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_mean_field_conventions import (
    ATOL, RTOL, COORDINATE_ATOL, COORDINATES, BASELINE, FIXTURES, METADATA,
    make_process, snapshot, response_structure, old_over_new,
)
import torch

report = {'rtol': RTOL, 'atol': ATOL, 'coordinate_atol': COORDINATE_ATOL,
          'max_absolute_difference_by_quantity': {}, 'ranks_and_truncation_identical': True}
for index, config in enumerate(METADATA['configs']):
    process = make_process(config)
    process.compute_trajectory()
    new = snapshot(process)
    old = dict(BASELINE[index])
    old.update(response_structure(old))
    new.update(response_structure(new))
    for name, old_values in old.items():
        new_values = new[name]
        if not isinstance(old_values, list):
            old_values, new_values = [old_values], [new_values]
        for left, right in zip(old_values, new_values):
            if isinstance(left, (bool, int)):
                assert left == right, (index, name)
                continue
            left, right = torch.as_tensor(left), torch.as_tensor(right) * old_over_new(name, config)
            torch.testing.assert_close(left, right, rtol=RTOL,
                                       atol=COORDINATE_ATOL if name in COORDINATES else ATOL)
            difference = (left - right).abs().max().item() if left.numel() else 0.
            report['max_absolute_difference_by_quantity'][name] = max(
                difference, report['max_absolute_difference_by_quantity'].get(name, 0.))
(FIXTURES / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
