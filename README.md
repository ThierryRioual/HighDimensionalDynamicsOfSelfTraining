# High-dimensional dynamics of self-training

## Overview

Research code for confidence-based self-training in a binary Gaussian mixture
and Monte Carlo simulation of its high-dimensional effective process. The
experiments compare finite-dimensional gradient descent with effective-process
predictions and study the population classification error and its decomposition.

The model uses $X_i=Y_i\mu/\sqrt d+\sigma U_i$ and scores
$r_i^t=b^t+X_i^\top w^t/\sqrt d$. The training pool is reused at every iteration.
Pseudo-labels default to score signs from iteration zero, with $\mathrm{sign}(0)=+1$.
Selection includes both boundaries: $r_i^t\geq\kappa_+$ or $r_i^t\leq\kappa_-$.
The unlabeled loss is averaged over the **entire unlabeled pool**, without
rescaling by the selected fraction. Effective-process predictions are estimated
using finite Monte Carlo particle populations.

## Installation

Tested with **CPython 3.9.6 on macOS arm64**, using CPU tensors and float64.
The numerical, notebook, and test package versions are pinned in
[requirements.txt](requirements.txt).
The commands below use a macOS/Linux shell and a `python3` interpreter
compatible with the pinned package versions.

```sh
git clone https://github.com/ThierryRioual/HighDimensionalDynamicsOfSelfTraining.git
cd HighDimensionalDynamicsOfSelfTraining
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip==26.0.1
python -m pip install -r requirements.txt
python -m ipykernel install --sys-prefix --name self-training --display-name "Self-training (.venv)"
python -m jupyterlab
```

In JupyterLab, select the **Self-training (.venv)** kernel for each notebook.
This matters when an existing kernel named `python3` points to another Python
installation. Launch JupyterLab from the repository root. The notebooks also
resolve imports when opened from a directory within the project checkout.

The tested Apple Python build uses LibreSSL 2.8.3. JupyterLab's HTTP dependency
may emit `NotOpenSSLWarning`; this did not prevent the numerical tests or local
notebook execution. HTTPS-dependent Jupyter features were not validated.

## Repository structure

| Path | Purpose |
| --- | --- |
| [src/](src/) | Finite GD, effective-process recursion, configuration, data generation, initialization, objectives, callbacks, and numerical linear algebra. |
| [experiments/experiments.py](experiments/experiments.py) | Shared configuration and simulation runners for the paper experiments. |
| [experiments/plotting.py](experiments/plotting.py) | Plotting, scoped styles, and figure export for recorded results. |
| [experiments/notebooks/](experiments/notebooks/) | Paper and dataset experiment notebooks with editable settings. |
| [experiments/](experiments/) | Importable experiment modules, including the dataset loaders and DINOv2 embedding pipeline. |
| [tests/](tests/) | Numerical identities, independent coordinate references, CGS2 checks, RNG checks, callback/initialization tests, and reduced experiment tests. |
| [docs/](docs/) | Implementation architecture, effective-process mathematics, and repository organization. |
| [manuscript/](manuscript/) | LaTeX sources, bibliography, and versioned figure PDFs. |
| `outputs/` | Generated plots, simulation records, and diagnostics; excluded from Git. |

Folder roles and naming conventions are
documented in [repository organization](docs/repository_organization.md).

## Reproducing the figures

Open the notebooks below, select the project kernel, and run their cells in order.
Parameters are defined in their configuration cells; both import reusable code
from `experiments/experiments.py` and `experiments/plotting.py`.

| Notebook | Experiment and output | Current full configuration |
| --- | --- | --- |
| [statistical_behavior.ipynb](experiments/notebooks/statistical_behavior.ipynb) | Population-error decomposition into the optimal linear/Bayes error, alignment regret, and intercept regret; balanced and imbalanced panels in one side-by-side figure. | `d=5000`, `n=40000`, `n_iterations=400`, `seed=49`; `label_prior=0.5` then `0.2`. Edit `config_balanced`; `config_unbalanced` derives from it with `dataclasses.replace`. |
| [approximation_accuracy.ipynb](experiments/notebooks/approximation_accuracy.ipynb) | One six-panel finite-GD/effective-process comparison: population error, selected fraction, selected-error fraction, bias, alignment, and weight norm. | `d=2000`, `n=16000`, `n_iterations=300`, `k=10000`, `runs=20`, `seed=42`. Edit `config`. |

The paper notebooks save vector PDFs to `manuscript/figures/`, which the
manuscript includes directly. The dataset notebooks save standalone PDFs to
`outputs/figures/`.

The [dataset notebooks](experiments/notebooks/) use the same pattern. Their
loading, fitting, and plotting code is in `experiments/mnist.py`,
`experiments/fashion_mnist.py`, `experiments/isolet.py`, and
`experiments/cifar_dinov2.py`. The MNIST loader also requires scikit-learn
(tested with version 1.6.1).

Build the paper from the repository root with:

```sh
cd manuscript
latexmk -pdf -outdir=build -interaction=nonstopmode -halt-on-error main.tex
```

The compiled paper is `manuscript/build/main.pdf`. For Overleaf, upload the
contents of `manuscript/`, including its `figures/` subdirectory, and select
`main.tex` as the main document. Exclude the local `build/` folder. Incorporate
any independent Overleaf edits before replacing existing files.

Full configurations require substantial CPU time and memory. The statistical
notebook's dense float64 design matrix alone occupies 1.6 GB, before Gaussian
noise arrays, subsets, and trajectory histories. The comparison notebook runs
20 repetitions, each including finite GD and the effective process. Reduce
`d`, `k`, `runs`, and `algorithm.n_iterations` before executing a quick check;
the testing section below provides a small standalone example. No runtime or
peak-memory benchmark is claimed.

## Experimental configuration

`ExperimentConfig(data, algorithm, d, seed)` packages a `DataConfig` and an
`AlgorithmConfig`. `MonteCarloConfig` adds particle count, repetitions, and metrics.
The sample size is derived as `n=round(data_to_dimension_ratio*d)`; realized
labeled and unlabeled counts are recorded by the sampled environment.

| Parameters | Meaning |
| --- | --- |
| `d`; `data_to_dimension_ratio` | Feature dimension; aspect ratio $\delta=n/d$. |
| `scale`; `label_prior`; `supervision_ratio` | Gaussian noise scale $\sigma$; probability $P(Y=+1)$; labeling probability $\rho$. |
| `signal_law` | Callable generating the signal-vector coordinates; notebook defaults are standard Gaussian. |
| `positive_margin`; `negative_margin` | Independent raw-score confidence margins, with $\kappa_-<0<\kappa_+$. `margin_threshold` is a symmetric-margin shortcut. |
| `pseudo_label_param`; `penalty_param` | Fixed unlabeled-loss coefficient $\pi$ and regularization coefficient $\lambda$. |
| `step_size`; `bias_step_size` | Weight and bias learning rates. `bias_step_size=None` follows `step_size`. |
| `train_bias`; `initial_bias` | Train or freeze the intercept; prescribed initial value. A fixed nonzero bias still enters every score and selection decision. |
| `loss_function`; `penalty_function` | Objects implementing `evaluate` and `gradient`; defaults are logistic loss and ridge penalty. |
| `n_iterations`; `k`; `runs` | Number of GD updates; particle count in each effective-process population; Monte Carlo repetitions. |
| `seed`; optional runner `seeds` | Nonnegative integer base seed; an explicit iterable of distinct integer `seeds` in `run_monte_carlo_experiment` overrides the configured repetition seeds and count. |
| `metrics` | Comparison metrics to record; supported names are the six principal keys listed below. |

The runners sample the finite signal and Gaussian initial weights on CPU in
float64. They seed and restore the global Torch CPU, Python, and NumPy random
streams used by scalar signal laws. A callable that uses its own generator
must manage that generator itself.
For explicit weights and bias, use the finite API:

```python
from src.initialization import SelfTrainingInitialization

initialization = SelfTrainingInitialization(b_init, w_init)
algorithm.fit(X, y_observed, initialization)
```

`y_observed` has entries `-1` or `+1` for observed labels and `0` for unlabeled
observations. An explicitly supplied `b_init` overrides `AlgorithmConfig.initial_bias`.
Optional `Y_init` overrides only the first-step pseudo-labels; omitting it uses
the paper's score-sign convention. Hidden true labels and the signal vector
are evaluation inputs, not inputs to `fit`.

The optional `bias_pseudo_label_param` gives the bias a separate unlabeled-loss
coefficient; by default it shares `pseudo_label_param`. Independent bias rates
and explicit first-step label overrides are supported extensions, not requirements
for the shared-rate, score-sign algorithm used by the notebooks.

## Recorded observables

Score diagnostics are recorded at $t=0,\ldots,T$, including initialization.
`population_error` is the analytic Gaussian-mixture risk, not an empirical
held-out error estimate. The two Gaussian paper runners sample training data only.

| Result key | Implemented quantity |
| --- | --- |
| `population_error` | Population classification error $P(\mathrm{sign}_+(r^t)\ne Y)$, with a positive prediction at zero scores. |
| `bias_term` | Intercept $b^t$. |
| `weight_vector_norm` | Dimension-normalized norm $\tau^t=\lVert w^t\rVert/\sqrt d$. |
| `weight_signal_alignment` | Alignment $m^t=\mu^\top w^t/d$. |
| `unl_usage` | Selected fraction at the **current scores**: entry $t$ contains $\omega^t$, including initialization and the terminal state. Requires `X_unl`, but no labels. |
| `unl_selected_error` | Current fraction of **all unlabeled observations** that are selected and have an incorrect score-sign label, $e^t$. It is not error conditional on selection. |

The Monte Carlo result has keys `config`, `iterations`, `seeds`,
`self_training`, and `effective_process`. Each method contains arrays of shape
`(repetitions, T+1)`, for example `results["self_training"]["population_error"]`.
Plots summarize repetitions along axis zero: blue for finite GD, orange for
the effective process, solid median, dotted mean, and shaded interquartile range.

The two selection fractions divide by the realized unlabeled count in each
method and use zero when that count is zero. In particular the effective
comparison records the empirical fraction, while the core state evolution
also keeps its population-normalized selection diagnostic.

`plot_monte_carlo_experiment(results, metrics=None)` plots the shared recorded
metrics and the derived `normalized_alignment=m/tau` when available. At each
iteration it summarizes finite repetitions only and leaves a gap when all
values are undefined. The comparison runner returns the requested metrics
only. The core callback and state evolution still compute their auxiliary
stationary-intercept diagnostics separately from the comparison.

Statistical results contain one-dimensional arrays of length `T+1`:
`population_error`, `optimal_linear_error`, `alignment_regret`, and `bias_regret`.
The decomposition uses the optimal error over intercept choices for the current
weight direction: alignment regret is its excess over the realized-signal Bayes
benchmark, and bias regret is the remaining population error. Undefined
zero-norm regrets are `NaN`. The statistical plot currently uses an error-axis
range of `[0, 0.5]`; returned arrays retain their full values. Both plotting
functions consume results without rerunning simulation.
`plot_statistical_behavior(results, names)` accepts equally sized nonempty lists
of recorded experiments and panel titles and returns `(figure, axes)` with
`axes.shape == (1, len(results))`. Each panel uses its own recorded iteration grid;
axes are shared and the four-entry legend appears once above the figure.

Both plotters accept keyword-only `save_image=False` and `image_path=None`.
With `save_image=True`, the plotters write a vector PDF by default to
`outputs/figures/statistical_behavior_comparison.pdf` or
`outputs/figures/approximation_accuracy.pdf` relative to the repository root.
For a custom `image_path`, use `.pdf` for vector output or `.png` for a
600 dpi raster preview. Relative custom paths use the current working
directory. Output directories are created only when saving is enabled.
For a matching notebook figure and paper PDF, pass `manuscript=True` when
plotting and save the returned figure with `save_figure(fig, path)`. The
optional `legend_font_size` sets the legend size in source-figure points.
Export preserves the figure's typography.

## Running tests

From the repository root with the environment activated:

```sh
python -m pip check
PYTHONPATH=. MPLBACKEND=Agg python -m pytest -q
```

The configuration in `.github/workflows/tests.yml` runs the same pytest suite
automatically on GitHub pushes and pull requests. The numerical reference checks
are part of this suite; full paper-scale simulations are run separately.

The suite uses pytest and runs reduced simulations rather than the full paper
experiments. It includes independent numerical reference checks and tests that
plotters use the recorded Monte Carlo data.

A small standalone simulation-and-plot smoke test is:

```sh
MPLBACKEND=Agg python - <<'PY'
from matplotlib import pyplot as plt
from src.config import DataConfig, AlgorithmConfig
from experiments.experiments import (
    ExperimentConfig, MonteCarloConfig,
    run_statistical_experiment, run_monte_carlo_experiment,
)
from experiments.plotting import plot_statistical_behavior, plot_monte_carlo_experiment

data = DataConfig(1.0, 0.2, 0.4, 3.0, lambda: 1.0)
algorithm = AlgorithmConfig(3, 0.1, 0.1, 0.4, positive_margin=0.5, negative_margin=-0.5)
stat = run_statistical_experiment(ExperimentConfig(data, algorithm, d=24, seed=49))
comparison = run_monte_carlo_experiment(
    MonteCarloConfig(data, algorithm, d=24, seed=42, k=64, runs=2)
)
for figure, _ in (plot_statistical_behavior([stat], ["Statistical behavior"]), plot_monte_carlo_experiment(comparison)):
    figure.canvas.draw()
    plt.close(figure)
assert stat["population_error"].shape == (4,)
assert comparison["self_training"]["population_error"].shape == (2, 4)
print("Smoke test passed")
PY
```

## License

No license has been adopted for this repository.

## Citation

When reporting results, include the
[repository URL](https://github.com/ThierryRioual/HighDimensionalDynamicsOfSelfTraining)
and the release tag or commit used. A confirmed paper citation is not currently
recorded here; no author list, publication venue, or DOI is inferred.
