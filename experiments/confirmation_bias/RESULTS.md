# Executed results and validation

Pilot cache: `outputs/confirmation_bias/pilot-36eab699ab9ca204/`. Smoke cache: `outputs/confirmation_bias/smoke-edce8d87002d52a9/`. All numbers below were read from completed caches; smoke is execution validation only.

## Validation completed

- Full existing and new test suite: **177 passed** (headless Matplotlib).
- Final smoke: all three priors for seed 49, six checkpoints and twelve unconstrained convex solves.
- Full pilot: seeds 49, 50, 51 at all three priors, nine baselines, eighteen checkpoints, fifty-four continuations, and thirty-six unconstrained convex solves. Summed run time was approximately 7.9 minutes on this environment (two Torch CPU threads).
- Every checkpoint dynamic replay matched every baseline suffix weight/intercept exactly: maximum discrepancy 0.
- Maximum baseline intercept decomposition residual: 4.43e-16; maximum same-state oracle identity residual: 1.12e-16.
- All 36 pilot solves converged under the recorded criterion; largest gradient infinity norm in (b,v=w/sqrt(d)) coordinates: 9.61226e-09. Solver gtol=1e-8, ftol=1e-15, acceptance residual tolerance=1e-6, maxiter=1500, maxls=40.
- Both notebooks were executed in clean local Jupyter kernels on the smoke cache. Both also executed on the completed pilot cache. The four executed notebook copies contain 18 embedded PNG figures in total and zero error outputs. Executed pilot copies, exported PNG/PDF figures, and CSV tables are in the pilot directory. Jupyter required local socket permissions outside the filesystem sandbox.
- Expanded ten-seed profile has not been executed.

## Individual baseline results

| Seed | Population p | Earliest best t >= 1 | Best error | Terminal error | Terminal minus best | Terminal configuration |
|---:|---:|---:|---:|---:|---:|---|
| 49 | 0.5 | 200 | 0.296595 | 0.296595 | 0.000000 | both selected signs plus zeros |
| 49 | 0.35 | 66 | 0.258798 | 0.349944 | 0.091146 | negative selected plus zeros |
| 49 | 0.2 | 49 | 0.169314 | 0.200000 | 0.030686 | negative selected plus zeros |
| 50 | 0.5 | 200 | 0.279968 | 0.279968 | 0.000000 | both selected signs plus zeros |
| 50 | 0.35 | 65 | 0.253865 | 0.349954 | 0.096089 | negative selected plus zeros |
| 50 | 0.2 | 48 | 0.163930 | 0.200000 | 0.036070 | negative selected plus zeros |
| 51 | 0.5 | 200 | 0.302423 | 0.302423 | 0.000000 | both selected signs plus zeros |
| 51 | 0.35 | 67 | 0.263796 | 0.349939 | 0.086143 | both selected signs plus zeros |
| 51 | 0.2 | 49 | 0.169202 | 0.200000 | 0.030797 | negative selected plus zeros |

All three balanced runs continue to their best observed error at T=200, so their best-checkpoint continuations have zero remaining steps. Their earlier checkpoint at t=100 supplies a nontrivial comparison. This does not establish that balanced runs cannot collapse at another horizon or on another dataset.

All six imbalanced runs deteriorate after their best states. Their terminal errors are close to the negative constant-prediction risk p. None ever reaches an entirely negative-selected configuration within this horizon: excluded entries remain. At p=.35, seed 51 also retains a positive-selected entry. Prediction collapse and an entirely selected single-sign branch are therefore not interchangeable.

## Within-run best-checkpoint comparisons

Each row averages three comparisons from the same state within each seed. Positive frozen change means deterioration despite keeping both targets and selection fixed. Positive dynamic-minus-frozen means a larger terminal error when configurations may change. Positive frozen-minus-oracle means correcting targets on that same initial selected set improves terminal error.

| p | Frozen terminal minus checkpoint | Dynamic minus frozen terminal | Frozen minus oracle terminal | Oracle terminal error |
|---:|---:|---:|---:|---:|
| 0.35 | 0.030030 | 0.061096 | 0.083250 | 0.205599 |
| 0.2 | 0.030304 | 0.002214 | 0.040800 | 0.156986 |

At p=.2, deterioration persists almost entirely under frozen fitting at these checkpoints; the mean dynamic-minus-frozen terminal difference is about .00221. At p=.35, the corresponding difference is about .06110, while frozen fitting still deteriorates by about .03003. Correcting selected labels improves every imbalanced best-checkpoint continuation, but leaves nonzero error. These conditional comparisons do not isolate all reasons for residual oracle error or yield an additive causal decomposition.

At the earlier checkpoints, frozen fitting can instead improve error from its starting value. At balanced t=100 checkpoints, changing configurations improves terminal error relative to freezing them. Thus the direction of the contrasts depends on the configuration, checkpoint, and prior; the suite retains these opposing cases.

## Numerical branch diagnostics

All eighteen frozen pseudo-label minimizers are numerically inconsistent with their original configurations, using a signed margin tolerance of 1e-7. Their minimum margins range from -3.647874 to -0.080014. All have converged solver status. No strictly consistent or near-boundary case was observed in this pilot; unit tests exercise those classifications and failure precedence.

This assesses the retrospectively chosen checkpoint branches. It does not prove that the dynamic terminal branch lacks a self-consistent minimizer, since terminal branch minimization was not added beyond the specified checkpoint rule. The oracle branch comparisons use the original pseudo-label inequalities for reference only; oracle minimizers are not asserted to be self-training equilibria.

## Limits and reproduction

Prescribed paired counts replace the legacy iid membership/class allocation, so the new seed-49 dataset differs from the historical notebook realization. Population p changes both training distribution and evaluation risk; paired risk differences do not share a fixed evaluation functional. Three seeds provide descriptive evidence only. Retrospective population-error checkpoints are not deployable stopping rules. No optimization-error bound, local stability spectrum, or sample-specific theorem step-size bound has been certified. Last observed switches are finite-horizon observations.

No existing training module, default, API, notebook, result, or user modification was changed. Added numerical modules are config.py, data.py, core.py, optimization.py, runner.py; reporting.py regenerates tables/plots. The two source notebooks, mathematical audit, runner documentation, notebook execution script, and focused engine/math/cache tests are additive.

Run from the repository root:

```sh
PYTHONPATH=. python3 -m experiments.confirmation_bias.runner --profile smoke
PYTHONPATH=. python3 -m experiments.confirmation_bias.runner --profile pilot
PYTHONPATH=. python3 -m experiments.confirmation_bias.runner --profile expanded
PYTHONPATH=. MPLBACKEND=Agg MPLCONFIGDIR=/private/tmp/codex-mplconfig python3 scripts/run_confirmation_bias_notebooks.py --profile smoke
PYTHONPATH=. MPLBACKEND=Agg MPLCONFIGDIR=/private/tmp/codex-mplconfig python3 scripts/run_confirmation_bias_notebooks.py --profile pilot
PYTHONPATH=. MPLBACKEND=Agg MPLCONFIGDIR=/private/tmp/codex-mplconfig python3 -m pytest tests -q
```
