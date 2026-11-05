# Feedback dynamics of self-training

## Overview

Research code for confidence-based self-training in a binary Gaussian mixture
and Monte Carlo simulation of its high-dimensional effective process. The
experiments compare finite-dimensional gradient descent with effective-process
predictions and study the population classification error and its decomposition.

The model uses $X_i=Y_i\mu/\sqrt d+\sigma U_i$ and scores
$r_i^t=b^t+X_i^\top w^t/\sqrt d$. The training pool is reused at every iteration.
Pseudo-labels default to score signs from iteration zero, with $\operatorname{sign}(0)=+1$.
Selection includes both boundaries: $r_i^t\geq\kappa_+$ or $r_i^t\leq\kappa_-$.
The unlabeled loss is averaged over the **entire unlabeled pool**, without
rescaling by the selected fraction. Effective-process predictions are estimated
using finite Monte Carlo particle populations.

## Installation

Tested with **CPython 3.9.6 on macOS arm64**, using CPU tensors and float64.
The numerical, notebook, and test package versions are pinned in
[requirements.txt](requirements.txt). Other Python/platform combinations have
not been validated. The commands below use a macOS/Linux shell and a
`python3` interpreter providing the tested Python version.

```sh
git clone https://github.com/ThierryRioual/FeedbackDynamicsOfSelfTraining.git
cd FeedbackDynamicsOfSelfTraining
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
resolve imports when opened with `figures/` as the working directory.

The tested Apple Python build uses LibreSSL 2.8.3. JupyterLab's HTTP dependency
may emit `NotOpenSSLWarning`; this did not prevent the numerical tests or local
notebook execution. HTTPS-dependent Jupyter features were not validated.

## Repository structure

| Path | Purpose |
| --- | --- |
| [src/](src/) | Finite GD, effective-process recursion, configuration, data generation, initialization, objectives, callbacks, and numerical linear algebra. |
| [figures/experiments.py](figures/experiments.py) | Shared experiment configurations, runners, and plotting functions; importing it runs no experiment. |
| [figures/](figures/) | The two maintained notebook entry points and their editable experiment settings. |
| [tests/](tests/) | Numerical identities, independent coordinate references, CGS2 checks, RNG checks, callback/initialization tests, and reduced experiment tests. |
| [docs/](docs/) | Architecture notes and dated mathematical audits. Dated audits describe historical snapshots. |
| [pdfs/](pdfs/), [outputs/](outputs/) | Reference material and historical research records; not runtime dependencies. Archived notebook copies are not maintained entry points. |

## Reproducing the figures

Open the notebooks below, select the project kernel, and run their cells in order.
Parameters are defined in their configuration cells; both import reusable code
from `figures/experiments.py`. Neither notebook imports the other.

| Notebook | Experiment and output | Current full configuration |
| --- | --- | --- |
| [statistical_behavior.ipynb](figures/statistical_behavior.ipynb) | Population-error decomposition into the optimal linear/Bayes error, alignment regret, and intercept regret; balanced and imbalanced panels in one side-by-side figure. | `d=5000`, `n=40000`, `n_iterations=500`, `seed=49`; `label_prior=0.5` then `0.2`. Edit `config_balanced`; `config_unbalanced` derives from it with `dataclasses.replace`. |
| [approximation_accuracy.ipynb](figures/approximation_accuracy.ipynb) | One six-panel finite-GD/effective-process comparison: population error, selected fraction, selected-error fraction, bias, alignment, and weight norm. | `d=2000`, `n=16000`, `n_iterations=300`, `k=10000`, `runs=20`, `seed=42`. Edit `config`. |

`effective_process.ipynb` has been retired; its finite/effective-process
comparison is covered by `approximation_accuracy.ipynb`. No paper figure
numbers are assigned here.

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
| `seed`; optional runner `seeds` | Base seed; an explicit `seeds` iterable in `run_monte_carlo_experiment` overrides the configured repetition seeds and count. |
| `metrics` | Comparison metrics to record; supported names are the six principal keys listed below. |

The notebook runners draw Gaussian initial weights using their seeded streams.
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
held-out error estimate. The notebook runners generate no held-out test sample.

| Result key | Implemented quantity |
| --- | --- |
| `population_error` | Population classification error $P(\operatorname{sign}_+(r^t)\ne Y)$, with a positive prediction at zero scores. |
| `bias_term` | Intercept $b^t$. |
| `weight_vector_norm` | Dimension-normalized norm $\tau^t=\lVert w^t\rVert/\sqrt d$. |
| `weight_signal_alignment` | Alignment $m^t=\mu^\top w^t/d$. |
| `unl_usage` | Selected fraction of the **preceding update**: entry $t+1$ contains $\omega^t$; entry zero is zero. |
| `unl_selected_error` | Current fraction of **all unlabeled observations** that are selected and have an incorrect score-sign label, $e^t$. It is not error conditional on selection. |

The Monte Carlo result has keys `config`, `iterations`, `seeds`,
`self_training`, and `effective_process`. Each method contains arrays of shape
`(repetitions, T+1)`, for example `results["self_training"]["population_error"]`.
Plots summarize repetitions along axis zero: blue for finite GD, orange for
the effective process, solid median, dotted mean, and shaded interquartile range.

`plot_monte_carlo_experiment(results, metrics=None)` plots all shared available
metrics by default. It additionally accepts the derived plotting quantity
`normalized_alignment=m/tau`; that name is not a configured recording metric.
Requesting `population_error` also records `oracle_bias` and `oracle_error`
from the prescribed intercept $\sigma^2\tau^2\log[p/(1-p)]/(2m)$, with `NaN`
near zero alignment. These are auxiliary evaluation diagnostics.

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
With `save_image=True`, the Figure saves a 600 dpi PNG on white with tight bounds
and padding. Defaults are `pdfs/statistical_behavior_comparison.png` and
`pdfs/approximation_accuracy.png`, resolved from the repository root. A custom
`image_path` must end in `.png`; relative custom paths use the current working
directory. Directories are created only when saving is enabled. The notebook
calls demonstrate saving with explicit paths based on `project_root`.

## Running tests

From the repository root with the environment activated:

```sh
python -m pip check
PYTHONPATH=. MPLBACKEND=Agg python -m pytest -q
```

The suite uses pytest and runs reduced simulations rather than the full paper
experiments. It includes independent numerical reference checks and tests that
plotters use the recorded Monte Carlo data.

Release preparation verified a clean installation of the pinned requirements,
`pip check`, the full test suite, and both notebooks in fresh kernels with reduced
settings (`d=32`, `n_iterations=5`, `k=160`, `runs=2` for the comparison).
The full configurations listed above were not run during this validation.

A small standalone simulation-and-plot smoke test is:

```sh
MPLBACKEND=Agg python - <<'PY'
from matplotlib import pyplot as plt
from src.config import DataConfig, AlgorithmConfig
from figures.experiments import (
    ExperimentConfig, MonteCarloConfig,
    run_statistical_experiment, run_monte_carlo_experiment,
    plot_statistical_behavior, plot_monte_carlo_experiment,
)

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

No license has been adopted yet. The proposed choice for code covered by the
maintainer's rights is the [MIT License](https://opensource.org/license/mit),
subject to explicit approval. It permits reuse with retention of the copyright
and permission notice. [BSD-3-Clause](https://opensource.org/license/bsd-3-clause)
is another conventional option and adds an explicit non-endorsement condition.
No `LICENSE` file is installed before that choice is approved. Reference PDFs
and third-party materials must retain their own applicable terms.

## Citation

When reporting results, include the
[repository URL](https://github.com/ThierryRioual/FeedbackDynamicsOfSelfTraining)
and the release tag or commit used. A confirmed paper citation is not currently
recorded here; no author list, publication venue, or DOI is inferred.
