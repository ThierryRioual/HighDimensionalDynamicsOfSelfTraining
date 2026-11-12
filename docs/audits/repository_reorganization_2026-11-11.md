# Repository reorganization: November 11, 2026

Baseline commit: `0969477` (the remote-documentation integration).

## Changes

- Moved maintained experiment notebooks and their shared runner from `figures/`
  to `experiments/`; updated imports, tests, and current documentation.
- Simplified the paper directory to `manuscript/`, with required figure PDFs
  under `manuscript/figures/` and local build products under `manuscript/build/`.
- Collected historical audits under `docs/audits/`. The original Fable audit
  retains its exact contents.
- Preserved all 32 files from `pdfs/` under `archive/legacy_exports/`, including
  their original filenames and bytes. Earlier manuscript PNGs are also retained.
  The detailed move inventory records original checksums and sizes.
- Changed new PNG export destinations to `outputs/figures/`; notebook vector
  exports go directly to the manuscript's versioned figure directory.
- Moved the standalone convention check to `scripts/check_mean_field_conventions.py`.
  It now writes a fresh report under `outputs/verification/`, rather than
  rewriting regression fixtures.
- Added explicit ignore rules for outputs, local historical exports, and LaTeX
  build products, while allowing the manuscript's required PDF assets.
- Added a GitHub Actions workflow for the Python tests and convention check.
- Kept the existing `src` imports. Package renaming and license adoption are
  outside this folder migration.

## Validation

- Full existing test suite: **187 passed**.
- Independent numerical convention comparisons: passed; rank and truncation
  histories agree with the saved baselines.
- All numerical fixture data remain byte-identical to the baseline.
- Both maintained notebooks execute at reduced settings (`d=32`, three updates;
  the comparison uses 64 particles and two runs). Separate fresh IPython
  subprocesses exercised the repository-root and experiment-directory entry
  points, including PNG and PDF export to scratch directories.
- Original notebook configurations and recorded outputs are preserved.
- The numerical implementation is byte-identical except for its manuscript
  documentation path. The mathematical sources and bibliography are unchanged,
  except for the two figure paths and their trailing whitespace in `numerical.tex`.
- `latexmk -pdf -outdir=build -interaction=nonstopmode -halt-on-error main.tex`
  succeeds from `manuscript/` and produces 61 pages. Extracted text and rendered
  page images match the pre-move PDF on every page. The existing underfull
  paragraph warning remains; no undefined-reference or citation warnings occur.
- Maintained Markdown links resolve to existing local targets.
- Workflow YAML was parsed and reviewed. The workflow has not yet run on GitHub.
- A 16-file source bundle is available locally at `outputs/overleaf/manuscript.zip`;
  it excludes build products and has a valid ZIP integrity check.

No full paper-scale simulation was rerun for this path migration. Historical
scientific artifacts were preserved, and the source archive is not an assertion
that independent edits in a remote Overleaf project have already been merged.
