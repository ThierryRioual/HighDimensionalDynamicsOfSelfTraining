# Repository organization

The manuscript and numerical implementation are versioned together. Python
imports use the `src` package, for example `from src.config import DataConfig`.

| Directory | Role |
| --- | --- |
| `src/` | Numerical implementation and model configuration. |
| `experiments/` | Figure notebooks and shared experiment runners. |
| `tests/` | Numerical tests, reference fixtures, and reduced experiment checks. |
| `manuscript/` | LaTeX sources, bibliography, and required figure PDFs. |
| `docs/` | Architecture, effective-process mathematics, and repository organization. |
| `.github/workflows/` | Automated checks run by GitHub Actions. |

## Naming and generated files

Use short lowercase directory names and `snake_case` for Python modules and
notebooks. LaTeX files and figures use descriptive names. The manuscript's
required figures are versioned under `manuscript/figures/`.

Generated simulation outputs and PNG previews go under the ignored `outputs/`
directory. LaTeX compilation products go under the ignored `manuscript/build/`
directory. Numerical reference fixtures are tracked under `tests/fixtures/`.

## Tests and automated checks

From the repository root, run:

```sh
MPLBACKEND=Agg python -m pytest -q
```

This includes the effective-process reference trajectories, coordinate and
gradient identities, random-stream isolation, and reduced figure experiments.
The YAML configuration in `.github/workflows/tests.yml` installs the pinned
dependencies and runs this command on GitHub pushes and pull requests.

## Manuscript and Overleaf

From `manuscript/`, run:

```sh
latexmk -pdf -outdir=build -interaction=nonstopmode -halt-on-error main.tex
```

The output is `manuscript/build/main.pdf`. For Overleaf, upload the manuscript
sources and the `figures/` subdirectory, select `main.tex` as the main document,
and exclude `build/`. Reconcile independent Overleaf edits before replacing files.
