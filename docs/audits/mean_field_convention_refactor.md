# Manuscript convention alignment

The authoritative reference is
[`mean-field.tex`](../../manuscript/mean-field.tex),
Definition `def:mean-field-recursion`, specifically `eq:g-U-definition`,
`eq:phi-w-definition`, `eq:phi-g-definition`, and `eq:w-update-definition`.
The manuscript was not edited.

`src/primitives.py` now exposes the frozen score gradient independently of
learning rates. `src/asymptotics.py` uses that gradient throughout projections,
transported histories, empirical moments, and diagnostic memory solves. Its
updates explicitly multiply the gradient contributions by the descent rates.
`get_decay_from` continues to return the penalty increment
`-eta * lambda * j'(w)`; it is not a manuscript residual.

All mean-field public field names, shapes, and method signatures are retained.
The optional `eta` argument of `compute_pseudo_residual_from` is retained but
has no effect: a manuscript residual is independent of the step size.
The separate bias residual uses its configured pseudo-label coefficient and
its learning rate is applied in the intercept update. At zero bias rate,
that residual is now the gradient rather than an identically zero increment.
With `train_bias=False`, the existing diagnostic convention `g_b=g` remains.

## Old and new quantities

Here `old = factor * new`, for the positive constant weight rate `eta`.
These identities couple parameter-side standard normals by sign reversal.

| Quantity | Factor |
| --- | ---: |
| `g`, `p`, `chi`, `zeta`, residual orthogonal component | `-eta` |
| Residual Gram matrix `C_g` | `eta**2` |
| `alpha_w`, `alpha_g` | `1` |
| `phi_w`, cumulative `gamma_w` | `-1/eta` |
| `phi_g`, cumulative `gamma_g` | `-eta` |
| Residual innovation scale `v_g` | `eta` |
| Parameter Gaussian process `xi_w` | `-eta` |
| Parameter Gaussian process Gram matrix | `eta**2` |
| `B_g`, `P_g`, `psi_w`, primitive `z_w` | `-1` |
| `Theta_g`, residual projection coordinates `beta_g` | `eta` |
| `psi_g` | `-eta` |
| `w`, `b`, `q`, `r`, `C_w`, `v_w`, `xi_g`, predictions | `1` |

The companion bias-gradient factor is `-eta_b` when bias training is enabled;
this also covers its separate pseudo-label coefficient. At `eta_b=0`, the
old zero increment cannot be inverted to recover the new gradient.

Finite GD update records, finite decomposition, and callback residual metrics
retain increment units for API compatibility. Their adapter still computes
`u=-eta*g`. They are outside the standardized mean-field histories; the
statistical training algorithm and finite predictions are unchanged.

The sign reversal of the parameter Gaussian generator output preserves its
standard normal law and independence, consumes exactly the same draws, and
preserves seeded effective trajectories. The backward recursion still uses
`+v_g*z_w` with a nonnegative innovation scale, exactly as in the manuscript.

## Numerical rank audit

No rank cutoff or solver was changed. Production CGS2 accepts a direction iff
`rho > eps_rank * input_norm`. Both sides scale by `1/eta` for residual
histories. The residual basis reverses sign while its coordinate matrix scales
by `1/eta`, leaving its singular-value ratios unchanged. Transport and raw
memory solves use `torch.linalg.lstsq` with the existing `rcond` and driver;
the default cutoff is relative to the largest singular value. There are no
production Gram pseudoinverses, eigendecompositions, or covariance square-root
factorizations in this recursion. The optional diagnostic SVD computes
coordinate singular values and introduces no rank decision.

Regression coverage includes default and explicit `rcond`, float32/float64,
rescalings from .001 to 1000, and dependent and deliberately truncated
histories. As usual, floating-point decisions arbitrarily close to a cutoff
cannot be guaranteed identical under every possible input rescaling.

## Numerical evidence

The immutable pre-edit fixture records 12 float64 runs with unequal particle
budgets `K_w=53,K_g=71`, seed 123, five updates plus terminal diagnostics,
`eta=.03,.3,1,2`, and three regimes: supervised, active self-training, and
active self-training with deliberate truncation and separate bias controls.
Metadata includes the original source SHA256 and Torch version. Tests also
reconstruct projection coefficients, cumulative responses, Gaussian processes,
and their empirical Gram matrices from these recorded histories.

After converting the new results into the old units, maximum absolute errors
were:

| Quantity | Maximum absolute difference |
| --- | ---: |
| Weight trajectory | `1.34e-15` |
| Intercept trajectory | `2.78e-17` |
| Scores | `5.78e-15` |
| Classification error | `1.12e-16` |
| Selection fraction | `0` |
| Residual Gram matrix | `2.78e-17` |
| Raw memory coefficients | `7.77e-9` |
| Projection coefficients | `5.48e-10` |
| Cumulative memory coefficients | `7.58e-9` |
| Bases and transported histories | `3.96e-8` |

All rank and truncation histories agree exactly. Predictions and ordinary
histories use `rtol=2e-9, atol=2e-10`. Raw responses, bases, and transported
coordinates use the same relative tolerance and `atol=1e-7`: small-step
supervised trajectories are nearly dependent, so their coordinate
representations are more sensitive than their represented vectors.
The unrounded per-quantity results are in
[`comparison.json`](../../tests/fixtures/mean_field_conventions/comparison.json).

The maintained `run_monte_carlo_experiment` workflow was additionally compared
against the original class for `eta=.1,.2,.7`, two seeds, eight updates,
`d=128`, and 512 particles. Every returned finite and effective metric passed
the tighter tolerance; the maximum discrepancy was `1.78e-15`. These saved
workflow outputs are covered by regression tests. Full publication-size
notebooks were not rerun; retained-notebook, plotting, and PNG-saving tests
exercise their interfaces.

The original suite passed 154 tests. The final suite passed **187 tests**
in 22.15 seconds, including 33 new regression cases. The suite includes
finite simulation, retained-notebook configuration, plotting, and PNG-saving
checks. The final suite and independent comparison report can be run using:

```sh
MPLBACKEND=Agg python3 -m pytest -q
MPLBACKEND=Agg python3 tests/mean_field_convention_report.py
```

The macOS interactive Matplotlib backend aborted the initial test run;
headless Agg resolves that environment issue. Equivalence is established for
the tested configurations and tolerances, not for arbitrary horizons or
particle-limit accuracy. No ambiguous manuscript normalization remained.
