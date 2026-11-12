# Mathematical architecture

## Dependency flow

`figures/experiments.py` provides the experiment configurations, the statistical
and Monte Carlo runners, and their plotting functions. The two notebooks import
these definitions and retain the paper parameter choices and execution cells.
The module does not run experiments or create figures when imported.

`DataConfig` describes the population. `dgp` draws a feature matrix and an
`environment` containing the realized sample vectors. `initialization` validates
the initial condition against the design and observed labels. `algorithms.fit`
runs the finite updates using `X` and `y_observed`, where `0` marks unlabeled
observations. `callbacks` receives evaluation inputs separately and records
the resulting diagnostics.

Both finite GD and `asymptotics` use `primitives` for scores, sign conventions,
selection weights, and pseudo-residuals, and `performance` for population risks.
The effective-process recursion delegates its numerical factorizations to
`orthogonal`. Pure primitives do not depend on initialization or finite-data
containers.

## Quenched finite model

`QuenchedEnvironment(mu, Y, Delta)` in `src/environment.py` is the canonical
finite object.  It clones and validates the realised vectors and derives
`d,n,delta=n/d,I_L,I_U,N,M,rho=N/n`.  It is held fixed while GD runs.
`FourCellSampleTypeLaw` samples a general categorical law on
`(+1,1),(+1,0),(-1,1),(-1,0)`; `DataConfig(label_prior, supervision_ratio)`
remains the product/MCAR convenience model.

`IsotropicGaussian` in `src/dgp.py` generates the conditional design

$$
X_i=Y_i\mu/\sqrt d+\sigma U_i,\qquad U_i\stackrel{\rm iid}{\sim}N(0,I_d),
$$

so `Delta` controls observation, not feature generation.

## Finite self-training

`SelfTrainingInitialization(b_init,w_init,Y_init=None)` uses the initial score
signs by default. An optional full-index `Y_init` overrides only the first step
and requires `Y_init[I_L]=Y[I_L]`. At a finite update `t`, the default is

$$
\widehat Y^t=\mathrm{sign}(r^t) \quad (t\ge0),
\qquad \mathrm{sign}(0)=1.
$$

`SelfTrainedGradientDescent.fit(X, y_observed, initialization)` is the
single mathematical implementation. It derives `Delta = (y_observed != 0)`
and `rho = N/n`, using only the observed labels. It freezes the pseudo-labels and
raw confidence mask before forming

$$
g_i^t=-\eta_w\left\{\frac{\Delta_i}{\rho}\ell'(Y_i,r_i^t)+
\frac{(1-\Delta_i)\pi}{1-\rho}S_i^t
\ell'(\widehat Y_i^t,r_i^t)\right\},
$$

with a zero unlabeled term when no observations are selected. The selection
fraction `omega` remains a diagnostic and does not rescale the loss. The
weight-vector update always uses this residual with pseudo-label coefficient `pseudo_label_param`.  The
bias uses the companion residual

$$
g_{b,i}^t=-\eta_b\left\{\frac{\Delta_i}{\rho}\ell'(Y_i,r_i^t)+
\frac{(1-\Delta_i)\pi_b}{1-\rho}S_i^t
\ell'(\widehat Y_i^t,r_i^t)\right\},
$$

If `bias_pseudo_label_param` is omitted, $\pi_b=\pi$.
The weight rate is `step_size`; the bias rate is `bias_step_size`, defaulting
to the weight rate when unspecified. With trainable bias, the updates are

$$
b^{t+1}=b^t+n^{-1}{\bf1}^Tg_b^t,\quad
w^{t+1}=w^t-\eta_w\lambda\nabla J(w^t)+\sqrt d\,X^Tg^t/n.
$$

`AlgorithmConfig.initial_bias` defaults to zero.  The value $b^0$ is included
in every logit regardless of `train_bias`; that flag controls only whether
the bias update is applied.  Thus `train_bias=False` defines a fixed
intercept, which may be nonzero.  Explicit initialization arguments in the
low-level finite and state-evolution APIs override the configuration default.

Both retained notebook runners use `sample` and `fit`. `sample` returns
`(environment, X, X_test, Y_test)`; the runners construct
`y_observed = environment.Y * environment.Delta`. `fit` requires this observed
label vector and explicit initialization and returns the fitted estimator. The
approximation notebook groups labeled rows before unlabeled rows to preserve
the numerical reduction order of its former split-data path.

There is no split-data adapter or implicit random initialization. Users can
explicitly call `primitives.compute_scores` and
`primitives.sign_with_positive_tie` to construct an explicit score-based
initialization. Algorithm 3.2's score-sign rule is already the default of both
retained runners and the numerical kernels. Explicit alternative first-step
pseudo-labels remain available through `Y_init`. True unlabeled labels and the signal vector
in the environment affect diagnostics only, not the training updates.

`macroscopic_observables(t, environment=...)` and
`finite_decomposition(X, U, t, sigma=..., environment=...)` receive the
environment explicitly for post-training analysis. In particular, signal
alignment `m` and true-label/residual alignment `chi` are evaluated there from
the recorded weights and residuals, rather than inside the training loop.

`FiniteStep` stores the exact frozen `g`, `omega`, labels, and observables used
in each update.  Callback residual metrics read this record rather than
reconstructing a different residual after the update.

Finite GD records and callback residual diagnostics retain increment units:
`u = -eta_w * g`, where `g` is the frozen score gradient. The existing
`FiniteStep.g` field stores `u` for API compatibility. Effective histories
use manuscript units `g`; the descent rates appear in the parameter updates.
See [the convention audit](mean_field_convention_refactor.md).

Callback score diagnostics (`population_error`, bias, norm, alignment,
selected-error fraction, and `unl_usage`) refer to the current state
`t=0,...,T`. Residual diagnostics refer to the preceding update, with zero
entries at `t=0`. The comparison runner uses `se.selection_rate[:T+1]` for
current-state selection fractions, including initialization.

## Effective dynamics

`src/asymptotics.py` keeps the projection-based orthogonal-coordinate core:
separate `K_w,K_g`, CGS2 bases with `B.T @ B/K=I`, transported `Q^[w],P^[g]`,
and small least-squares solves.  Its Gaussian convention is
`z_g` in sample space driving `q`, and `z_w` in parameter space driving `p`.
No production Gram inverse or autograd response is used.

The class separates initialization/validation, independent random streams,
trajectory views, numerical helpers, the core recursion, observables, and
compatibility accessors. Rank and truncation histories are retained in the
effective-process records. Basis quality diagnostics are available on demand
from the orthogonal basis, without storing unused quality histories or running
an extra diagnostic SVD at each step. The basis returns each update's information
in `OrthogonalizationResult`.

`state_evolution_sample_base_sampler(law, ...)` adapts a joint sample-type law
to its existing low-level sampler.  `theorem_trajectory` presents
`(W_T,Q_T,R_T,G_{T-1},P_{T-1})`; internally retained `g^T,p^T` remain auxiliary
diagnostics.

Finite GD and state evolution also record a common, non-recursive oracle-bias
diagnostic.  For their shared test-score convention
$R^t=b^t+m^tY+\sigma\tau^tZ$, it evaluates

$$
b_{\rm oracle}^t=\frac{\sigma^2(\tau^t)^2}{2m^t}
\log\frac{p}{1-p}
$$

and the population error obtained by replacing only the evaluation intercept
$b^t$ with $b_{\rm oracle}^t$.  The actual $b^t$ remains in every finite and
effective-process update.  The oracle quantities are recorded as `NaN` when
$m^t$ is numerically zero.

## Reproducibility and extensions

The retained entry points are `figures/statistical_behavior.ipynb` and
`figures/approximation_accuracy.ipynb`. Their logic is implemented in
`figures/experiments.py`. Its `ExperimentConfig` packages `DataConfig`,
`AlgorithmConfig`, dimension, and seed; `MonteCarloConfig` extends these common
fields with particle count, repetition count, and tracked metrics. Sample size
is derived from dimension and the configured data-to-dimension ratio. Simulation
functions accept configurations explicitly, and plotting functions consume
their returned results. The notebooks retain the paper configurations.

The statistical experiment uses separate seed streams for signal/weight
initialization and design generation. The approximation
experiment additionally seeds the effective process independently for each
repetition. No artificial initial-label draws are made. The two runners retain
their established observation order and callback timing. All numerical validation, including the independent
coordinate-reference and ill-conditioned CGS2 checks, is in `tests/`;
historical outputs and reference PDFs are not runtime dependencies.

The notebooks explicitly select float64. `config.py` also retains its existing
Torch default-dtype setting for compatibility; changing that import side effect
would require a separate precision and random-draw audit. The approximation
runner validates its supported comparison metrics before simulation, while
the finite callback retains its broader existing metric interface.

Pseudo-label weights are fixed scalars. Confidence selection uses only the
inclusive hard rule on raw scores with independently configurable margins.
There are no schedule, selector-strategy, threshold-normalization or
selected-fraction loss-normalization options. Custom loss functions and
penalties, explicit initial conditions, and independent weight/bias learning
rates remain supported.

The November 3 draft's equation (8) uses this total-pool unlabeled denominator.
Its Algorithm 3.2 uses score-sign pseudo-labels at iteration zero, which is now
the default of the finite algorithm, effective process, and both notebooks. The separate bias learning
rate and optional bias-specific pseudo-label coefficient are extensions beyond
that draft's shared rate and coefficient; the defaults recover the shared
values. Dated audit documents preserve the earlier implementation's state.
