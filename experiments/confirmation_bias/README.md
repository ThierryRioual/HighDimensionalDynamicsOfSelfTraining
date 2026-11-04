# Confirmation bias, imbalance, and branch stability

This additive finite-dimensional suite studies two distinct changes: fitting an
already chosen configuration, and changing that configuration along training.
It calls `SelfTrainedGradientDescent.fit_full`; it introduces no replacement
training recursion and changes no existing source defaults or notebooks.

## Source configuration and mathematical audit

The pilot reuses Notebook 14's first configuration: seed 49, d=3000, n=24000,
supervision ratio .01, T=200, p=.2, sigma=signal_std=1, eta=.5, lambda=.1,
pi=2, raw thresholds ±log(4). Its stored fixed-M run reaches error .170876 at
iteration 51 and ends at .2. Seeds 50 and 51 are reproducible additional
replicates; the expanded profile uses 49–58. No settings were tuned to produce
these outcomes. The smoke profile (d=32,N=8,M=120,T=12,seed49) tests software
only and is not evidence for the scientific hypothesis.

The new paired designs prescribe N=240,M=23760 and class counts; the legacy
notebook sampled membership/classes independently, so realized counts and
seed-specific trajectories differ. The suite preserves the population settings
and initialization procedure, not the legacy dataset. See
[MATHEMATICAL_AUDIT.md](MATHEMATICAL_AUDIT.md) for manuscript page/equation references.

For X_i=Y_i mu/sqrt(d)+sigma U_i and r_i=b+X_i^T w/sqrt(d), the suite minimizes
logistic loss plus lambda ||w||²/(2d), with no intercept penalty. With v=w/sqrt(d),
the original preconditioned update is ordinary GD in (b,v):

    b_next = b - eta * dL/db
    v_next = v - eta * dL/dv

The engine's RidgePenalty.gradient(w)=w gives the correct -eta*lambda*w decay
because its weight update is preconditioned by d. The loss and sigmoid are
stable logaddexp/sigmoid evaluations. Selected thresholds include equality;
sign(0)=+1. At t=0 only, exogenous Rademacher Y_init supplies pseudo-targets.
At t>=1 they are score signs. Initial b=0 and iid Gaussian w are independent
of data; labeled Y_init entries equal observed labels.

**Normalization:** `normalize_unlabeled_loss=False` explicitly uses pi/M times
the selected sum, even when the selected set is empty. The existing default
`True` uses pi/|A_t| when nonempty. Neither default nor legacy results change.
Raw thresholds are used throughout this suite.

## Run and reproduce

From the repository root (Python with numpy, scipy, torch, pandas, matplotlib,
pytest, nbformat, nbclient, and ipykernel installed):

```sh
PYTHONPATH=. python3 -m experiments.confirmation_bias.runner --profile smoke
PYTHONPATH=. python3 -m experiments.confirmation_bias.runner --profile pilot
PYTHONPATH=. python3 -m experiments.confirmation_bias.runner --profile expanded
PYTHONPATH=. MPLBACKEND=Agg MPLCONFIGDIR=/private/tmp/codex-mplconfig python3 scripts/run_confirmation_bias_notebooks.py --profile smoke
PYTHONPATH=. MPLBACKEND=Agg MPLCONFIGDIR=/private/tmp/codex-mplconfig python3 scripts/run_confirmation_bias_notebooks.py --profile pilot
PYTHONPATH=. MPLBACKEND=Agg MPLCONFIGDIR=/private/tmp/codex-mplconfig python3 -m pytest tests -q
```

The runner accepts `--seeds 49 50 51`, `--threads 2`, and `--output-root PATH`.
An overridden seed list creates a separate configuration ID. Each profile runs
Experiment A within every seed/prior pair required by Experiment B, at
p in {.5,.35,.2}. There is no parameter sweep. Notebook execution only loads
compatible caches; missing results raise an actionable error. The notebooks
also support explicit `ALLOW_RUN=True` for a deliberate requested run.

Outputs live under `outputs/confirmation_bias/<profile>-<hash>/`. The identifier
hashes configuration, solver settings, and numerical source files. Run results
are JSON plus compressed NPZ (no pickle); a manifest records software versions,
git commit/status, source hashes, streams, dataset hashes, timestamps, and run
status. Existing complete runs are loaded, never overwritten. Extending a cache across
a change in Python, numerical libraries, platform, or thread count is rejected;
use a separate output root for that runtime. Read-only loading remains supported. Failed attempts
retain status/traceback; a retry can complete a partial run. Scalar trajectories,
full 3-by-3 transition counts, threshold-crossing summaries, checkpoint states,
endpoints, frozen configurations, minimizer parameters and raw margins are
saved. Full trajectories of weight vectors/design matrices are not saved.
Designs can be regenerated from recorded streams and checked against hashes.

A source change intentionally creates a new cache ID. Prior directories remain
available and are never deleted. Figures, CSV tables, and clean-kernel executed
notebook copies are saved within the corresponding suite directory.

## Paired design and counterfactuals

Independent local RNG streams produce signal/initial weights (seed+11), Gaussian
noise, membership, and class ranks (distinct namespaced SeedSequence streams),
and exogenous initial labels (seed+31). The exact seed derivation and actual
64-bit seeds are recorded; namespacing prevents cross-replicate stream collisions. Across priors, all these draws are shared. Within each
subset, the smallest ranks receive +1, with counts round(p*subset_size), ties
to even. Labeled counts are clipped to [1,N-1]. Changed labels reconstruct X
through the existing IsotropicGaussian generator. Global RNG state is untouched.
Population p and both realized proportions are saved separately.

For each baseline, t_best is the earliest argmin over t>=1. Checkpoints are the
deduplicated {max(1,floor(t_best/2)),t_best}, including terminal checkpoints.
Population-error checkpoint choice is retrospective and unavailable as a
practical stopping rule. Runs without deterioration remain in every table. The flag uses
max_{t>=t_best} E_t-E_t_best > 1e-8; the separate signed terminal deterioration
summary is E_T-E_t_best.

Dynamic, frozen-pseudo, and frozen-selected-oracle continuations start at the
same exact (b,w), use the same remaining horizon, and keep all hyperparameters
fixed. Dynamic replay resets its local initial targets to the current signs
because the absolute checkpoint is >=1; every replay is checked against all
baseline suffix weight vectors and intercepts. Frozen wrappers fix both mask
and targets while retaining the original engine updates. Oracle targets use
truth only on that same mask. Ordinary self-training never consults unlabeled
truth for its targets; diagnostic summaries may consult it.

## Diagnostics and interpretation

Population error is exact conditional on the fitted classifier under the
Gaussian mixture. At tau=0 the actual constant predictor and positive tie
convention determine error; b/tau and m/tau are NaN. Configuration proportions
are score-induced -1/0/+1; prediction proportions use the zero decision boundary.
They are not interchangeable. Separate fitted-configuration fractions and
assigned-target error fractions preserve the objective assignments (including
the special first step), while score-induced fractions may change in a frozen
run. Selected false-negative/positive fractions use
M as denominator; `selected_false_negative_rate` divides by the number with induced p=-1,
and `selected_false_positive_rate` divides by the number with induced p=+1.
These are selected-sign error proportions, not errors conditional on the true
class; an empty denominator returns NaN.
All nine configuration transitions are counted, including direct sign switches.
The last observed switch and first fully negative-selected state are empirical
finite-horizon observations, never certified identification times.

For t>=1 dynamic updates record zeta_L, zeta_U (without pi), and beta. The bias
update is zeta_L+pi*zeta_U. The same-state, same-mask oracle increment difference
is -eta*pi*beta. At the special t=0 and in frozen continuations, zeta_U uses
actual assigned targets, and beta_assigned verifies the analogous identity;
the dynamic self-label expression is explicitly undefined there. This identity
does not give the difference between diverging trajectories. Threshold crossing
summaries report Delta b and X_j^T Delta w/sqrt(d), including both thresholds
for a direct sign switch. These are descriptive one-step coordinate summaries.

Frozen minimization uses unconstrained L-BFGS-B in (b,v), analytic derivatives,
no intercept penalty, and no projection onto branch inequalities. Results report
solver status, tolerances, iterations, objective, infinity/L2 gradient residuals
in those coordinates. Positive ridge and both active target signs ensure a
finite unique minimizer; missing labeled classes and zero ridge are handled
explicitly. A small gradient residual is a convergence diagnostic, not a
validated bound on score error.

Consistency is evaluated for every unlabeled observation against the original
pseudo-label configuration. Positive/negative selected entries have inclusive
inequalities, zeros have strict interior inequalities. A margin above 1e-7 is
numerically strictly consistent; below -1e-7 is inconsistent; otherwise the
result is unresolved. Failed/insufficiently converged solvers take precedence.
Raw margins, all four inequality violation types, induced configuration, and
residuals are retained. None of these labels is a rigorous certificate. Oracle
minimizers need not be self-training equilibria, and frozen continuations may
leave the original branch.

Frozen deterioration measures what can happen while fitting fixed assignments;
dynamic-minus-frozen compares allowing those assignments to change;
frozen-minus-oracle compares target correction on a fixed selected set. Poor
oracle outcomes can remain because coverage, direction, finite samples, or
regularization remain limiting. These contrasts are not a complete causal
decomposition. Seed averages and paired differences are descriptive; three
seeds cannot support a general theorem or a reliable claim about all datasets.
Balanced classes are never assumed immune to collapse. No attraction theorem
is invoked without verifying its hypotheses, including a sufficient step bound.

For developers inspecting returned learner objects: in a frozen wrapper,
`FiniteStep.pseudo_labels` still contains the engine's candidate labels. The
fixed loss provider overrides those candidates on unlabeled coordinates.
The saved `p0`, fitted-configuration summaries, and assigned-target increments
represent the actual objective; tests independently verify the stored residuals
against those fixed targets after threshold/sign crossings.

See [RESULTS.md](RESULTS.md) for executed validation and pilot findings.

## Editing notebook configurations

The configuration cell reloads edited presets from config.py. Run that cell
after changing a preset; notebook-specific changes can be made with
`CONFIG = dataclasses.replace(CONFIG, ...)` after construction.
The load/run cell passes this exact object to `load_or_run_suite`, rather than
starting a separate process that reconstructs the profile defaults.
Complete caches load without retraining. For a new or incomplete configuration,
set `ALLOW_RUN=True` and rerun the configuration and load/run cells.
The default remains `False` so opening/executing a notebook does not silently
start an expensive experiment. Changing dimensions or the horizon requires
new results; previous caches are preserved.
