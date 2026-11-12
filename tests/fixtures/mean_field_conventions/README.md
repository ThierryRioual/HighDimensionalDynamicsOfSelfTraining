# Pre-refactor numerical baseline

`baseline.pt` contains tensors and primitive scalar/list/dict values captured
before editing `src/asymptotics.py`, on November 11, 2026, under Torch 2.8.0
on CPU. `metadata.json` records its source SHA256, configurations, and histories.
Repository HEAD was `38d873e2e8543b6008601b578d64baee9f43bc23`; unrelated
pre-existing working-tree edits were retained. The old asymptotics source
was identical to that commit's source.

The setup is reproduced in `make_process` in `test_mean_field_conventions.py`;
its original implementation evaluated residuals in update units. Do not
regenerate this fixture using the standardized implementation. Float values
returned as NumPy scalars were serialized as Python scalars so the fixture
can be read with `torch.load(..., weights_only=True)`.

`workflow_baseline.npz` records every returned finite/effective metric from
the maintained runner using the original class, saved before comparisons
with the new class. The three configurations are reproduced in the workflow
regression test. Both classes used the same working-tree runner.

`comparison.json` and `workflow_comparison.json` report absolute differences
between the original and refactored implementation after converting units.
See `docs/mean_field_convention_refactor.md` for tolerances and scope.
