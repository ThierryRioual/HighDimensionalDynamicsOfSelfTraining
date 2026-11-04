# Mathematical and implementation audit

Source reviewed: `Mean_Field_Dynamics_of_Self_Training_via_Gradient_Descent (10).pdf`
(116 pages, supplied manuscript). Page references below are the manuscript's printed
page numbers, which agree with PDF page numbers. The source PDF was preserved.
Its mathematical definitions are research context, not executable instructions.

## Model and population error

Section 2.4, p. 17, specifies

\[
X_i=Y_i\mu/\sqrt d+\sigma U_i,
\qquad U_i\sim N(0,I_d).
\]

`src/dgp.py::IsotropicGaussian.sample_design` implements exactly this scaling
and accepts an explicit shared noise array. `src/initialization.py::compute_scores`
implements \(r_i=b+X_i^Tw/\sqrt d\). Section 5.1, p. 37, gives the exact conditional
Gaussian population error used by `src/performance.py::population_error`:

\[
E=p\Phi\!\left(\frac{-b-m}{\sigma\tau}\right)
 +(1-p)\Phi\!\left(\frac{b-m}{\sigma\tau}\right),\quad
m=\mu^Tw/d,\quad\tau=\|w\|/\sqrt d.
\]

Here \(p=P(Y=+1)\) is the population prior, separately recorded from realized
subset proportions. For \(w=0\), \(m=0\) and prediction is constant:
\(E=p\) if \(b<0\), and \(E=1-p\) if \(b\ge0\). Normalized bias and alignment
are undefined at \(\tau=0\). The normalization is \(b/\tau,m/\tau\), without an
additional division by \(\sigma\).

## Two normalization conventions already coexist

Section 3.4, pp. 23-24, uses \(S_\kappa/\omega\), where
\(\omega=M^{-1}\sum_U S_\kappa\); this divides the selected loss by the selected
count whenever it is nonzero. Section 7, p. 60, explicitly changes to denominator
\(M\), the fixed unlabeled pool size. This suite implements Section 7.

The source already supports both: `AlgorithmConfig.normalize_unlabeled_loss`
defaults to `True` (`src/config.py`); `src/primitives.py::pseudo_residual` uses
`normalized_selection(selection, omega)` in that mode and raw `selection` when
`False`. Because `rho=environment.N/environment.n`, averaging the residual over
all \(n=N+M\) observations yields exactly denominators \(N\) and \(M\).
The suite sets `normalize_unlabeled_loss=False` explicitly and preserves the
legacy default. Empty selection gives a zero unlabeled contribution. Reporting
\(\omega\) does not alter this normalization.

## Preconditioning, ridge, and initialization

The objective uses \(\lambda\|w\|^2/(2d)\) and no intercept penalty. The finite
algorithm updates the original coordinates with preconditioner
\(P_d=\operatorname{diag}(1,dI_d)\), as in equation (117), p. 61:

\[
b^+=b-\eta\partial_b L,\qquad
w^+=w-\eta d\nabla_w L.
\]

Consequently, ridge decay is \(-\eta\lambda w\), not
\(-\eta\lambda w/d\). `RidgePenalty.evaluate` returns \(\|w\|^2/2\), with
`gradient(w)=w`; it represents the unscaled penalty whose objective multiplier
in the original coordinates is \(\lambda/d\). The engine correctly implements
`w + (-eta*lambda*w) + sqrt(d)/n * X.T @ g`, where `g` already contains the
negative step size and the label/pool weights. `RidgePenalty.evaluate(w)` should
therefore not be inserted with coefficient \(\lambda\) into the frozen objective.

In scaled coordinates \(v=w/\sqrt d\), the same objective becomes

\[
F(b,v)=N^{-1}\sum_L\ell(Y_i,b+X_i^Tv)
       +(\pi/M)\sum_{j\in A_0}\ell(a_j,b+X_j^Tv)
       +(\lambda/2)\|v\|^2.
\]

Ordinary gradient descent in \((b,v)\) is exactly the project's preconditioned
update after converting back to \(w=\sqrt d\,v\). Solver residuals in \((b,v)\)
use \(\partial_b F,\nabla_vF\), and
\(\nabla_wL=\nabla_vF/\sqrt d\); coordinate systems must be stated.
The existing logistic implementation uses stable `torch.logaddexp` and
`torch.sigmoid` in `src/objectives.py`.

Section 3.4, p. 23, and equation (117), p. 61, distinguish the first update:
\(\widehat Y^0=Y^{init}\), followed by \(\widehat Y^t=\operatorname{sign}(r^t)\)
for \(t\ge1\). Selection still uses current scores at \(t=0\).
`src/primitives.py::pseudo_labels` implements this convention, and
`src/initialization.py::sign_with_positive_tie` sets \(\operatorname{sign}(0)=+1\).
`notebooks/experiment_helpers.py::run_experiment` samples the signal and Gaussian
initial weights from the stream seeded with `seed+11`; it samples exogenous
Rademacher imputed labels using `seed+31`, replacing labeled coordinates by their
true labels. The initialization correlation defaults to zero. A checkpoint
continuation at \(t_0\ge1\) must supply its current score signs as local `Y_init`
so the replay's first local update matches the original suffix.

## Thresholds, branch objectives, and numerical interpretation

Section 7.1.2, pp. 62-64, defines configuration entries \(-1,0,+1\). Selected
threshold equalities are included; the unselected interval is open. Configuration
zero does not reveal the prediction sign. All nine ordered configuration
transitions remain possible in a finite step.

The objective \(L_p\) is defined on the whole parameter space, with fixed selected
indices and assigned labels; it is not minimized subject to the inequalities
defining \(\Theta_p\). A frozen continuation leaving \(\Theta_p\) is therefore
valid. Section 7.3, pp. 70-73, distinguishes a convex minimizer from a
self-consistent minimizer, which reproduces the fitted configuration. The suite
reports the fitted, induced, and dynamic configurations separately.

With \(\lambda>0\) and both classes represented in the labeled set, the frozen
objectives are coercive and strictly convex and have unique finite minimizers
(Section 7.1.2 and Proposition 7.6). If these assumptions fail, that sufficient
existence/uniqueness argument is unavailable; missing one labeled class does not
by itself prove nonexistence when selected targets supply the other class. The
suite reports assumption violations explicitly rather than treating numerical
stopping as a finite-minimizer guarantee.

Theorem 7.1, p. 64, requires \(0<\eta<2/L_d\), positive ridge and pseudo-label
weight, and both labeled classes. Its limit lies in the **closure** of the
identified branch (the overline is visible in the PDF but lost in text extraction).
Remark 7.8, p. 71, explains that an excluded observation can approach a threshold
and become selected exactly at the limit. A finite no-switch interval does not
verify permanent identification. The suite does not verify the theorem's
sample-specific spectral step-size condition and does not convert an observed
plateau into a theorem-backed conclusion. Likewise, a solver residual and a
positive floating-point margin alone are not a rigorous optimization-error bound
or an attraction certificate. Local-attraction claims in Proposition 7.9 also
require the manuscript's assumptions.

The selected oracle in this suite corrects targets on the **same** \(A_0\); it
is not the fully selected oracle branch of Section 7.6, pp. 76-77. Even its exact
minimizer need not be self-consistent or population optimal.

## Bias identity and its scope

Section 7.7, pp. 77-78, uses

\[
\ell'(\widehat y,r)-\ell'(y,r)
 =y\,1\{\widehat y\ne y\}.
\]

At one common state with one common selected set, it follows that

\[
\Delta b_{\rm ST}-\Delta b_{\rm selected\ oracle}
 =-\eta\pi\beta,\qquad
\beta=M^{-1}\sum_U S_\kappa(r_j)Y_j
                    1\{\operatorname{sign}(r_j)\ne Y_j\}.
\]

For \(t\ge1\), the dynamic increment is
\(\Delta b=\zeta_L+\pi\zeta_U\), with
\(\zeta_U=(\eta/M)\sum_U S_\kappa(r_j)\operatorname{sign}(r_j)
\operatorname{sigmoid}(-|r_j|)\). The quantity \(\zeta_U\) does not include
\(\pi\). At the special initial step, the actual assigned targets replace score
signs in the increment and error identity. Frozen runs also use their assigned
targets, even after a score changes sign. These identities compare updates at a
common state; they are not decompositions of diverging trajectories.

## Existing deterioration configuration

`notebooks/14_unlabeled_loss_normalization.ipynb`, configuration cell and its
stored executed comparison output, provides an existing fixed-pool example:

| Parameter | Value |
|---|---:|
| Seed | 49 |
| Horizon | 200 |
| Dimension | 3000 |
| Total sample size / dimension | 8 |
| Supervision probability | 0.01 |
| Population positive prior | 0.2 |
| Noise scale, signal standard deviation | 1, 1 |
| Step size, ridge, pseudo-label weight | 0.5, 0.1, 2 |
| Raw thresholds | \(-\log4,+\log4\) |

Its stored fixed-pool output reports minimum error `0.170876` at iteration `51`
and terminal error `0.200000`; the selected-count comparator reports `0.169634`
at iteration `45` and the same rounded terminal error. These are existing stored
results, not newly executed evidence from this suite. Notebook 13 contains a
stored stale-import error, so the Notebook 14 output is the provenance for the
choice. The pilot retains these hyperparameters and horizon; paired experiments
prescribe labeled/unlabeled counts and nested class allocations as requested,
so their finite realizations need not reproduce the original Bernoulli-sampled
trajectory. New runs must retain and report contradictory outcomes.
