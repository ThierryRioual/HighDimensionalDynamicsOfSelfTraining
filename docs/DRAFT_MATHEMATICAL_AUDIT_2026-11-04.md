# Audit of the November 3, 2026 mathematical draft

Audited November 4, 2026. Source: `High_Dimensional_Dynamics_of_Self_Training (1).pdf`, 54 pages. Printed page numbers coincide with PDF page numbers. This report concerns this version, rather than the older manuscript referenced by `experiments/confirmation_bias/MATHEMATICAL_AUDIT.md`.

## Assessment and scope

I read the statements and proofs in Sections 3–4 and Appendices A–D, checked the critical finite-dimensional and Gaussian-conditioning identities, visually inspected the branch-closure notation and switching estimates, and compared the algorithm and effective recursion with the current source. I did not identify a fatal mathematical gap in Theorems 4.4, 4.7, or 4.10 in this review. This is a substantive review, not a formal certification of the proofs or a complete verification of the literature and novelty claims.

The most consequential findings concern correspondence with the repository: the draft now studies a different normalization and first-step pseudo-label rule from the repository's defaults. There is also a reproducible failure in the current validation suite. No production code, tests, notebooks, or source PDF were changed by this audit.

## Findings requiring action

### 1. High priority: the default unlabeled objective differs from equation (8)

**Evidence:** pp. 6–7, equation (8), Algorithm 3.2; `src/config.py:99`; `src/primitives.py:66–85`; `src/algorithms.py:123–134`.

The draft uses the fixed pool denominator:

\[
L_U(\theta;\vartheta)=\frac{\pi}{M}\sum_{j\in I_U}S_j(\vartheta)\ell(\widehat Y_j(\vartheta),r_j(\theta)).
\]

The default code uses `normalize_unlabeled_loss=True`, and hence, when selection is nonempty,

\[
L_{U,\mathrm{code}}(\theta;\vartheta)
=\frac{\pi}{M\omega(\vartheta)}\sum_{j\in I_U}S_j(\vartheta)\ell(\widehat Y_j(\vartheta),r_j(\theta)),
\quad \omega=M^{-1}\sum_{I_U}S_j.
\]

The unlabeled coefficient is multiplied by `1/omega`. This is time-dependent and cannot generally be absorbed into a single fixed value of pi. Finite GD and the numerical effective process share this option, so agreement between them does not establish agreement with this draft.

**Mathematical consequence:** Proposition 4.1 and the descent argument prove a result for the unnormalized feedback. Their stated potential does not generate the normalized feedback. This distinction is structural. For example, in independent score coordinates with two positive unlabeled examples, let the second remain selected while the first crosses its positive threshold. The normalized unlabeled score gradient is `(0, pi*ell'_2)` before the crossing and `(pi*ell'_1/2, pi*ell'_2/2)` afterward. Any continuous potential with these smooth branch gradients would have to have matching tangential derivatives on the boundary, but the second component changes there and `ell'_2` is nonzero. Branchwise additive constants cannot repair this discrepancy.

**Correction:** explicitly set `normalize_unlabeled_loss=False` in every experiment presented as an implementation of this draft. Preserve the existing default if backward compatibility is desired, but distinguish the normalized extension in documentation and metadata. Do not transfer the finite- or long-time convergence theorems to that extension without a separate argument.

### 2. High priority: the first-step pseudo-label rule differs

**Evidence:** Algorithm 3.2, p. 7; Definition 4.6, equations (34)–(35); `src/primitives.py:13–20`; `src/asymptotics.py:470–525`; `src/utils.py:42–46`.

The draft refreshes pseudo-labels at every iteration, including zero:

\[
\widehat Y_j^0=\operatorname{sign}(b^0+X_j^\top w^0/\sqrt d).
\]

The code instead uses an explicit `Y_init` at zero, followed by score signs from time one onward. Its state-evolution base sampler returns `(Y, Delta, Y_init)` independently of the fresh Gaussian innovations; the default sampler refuses an active unlabeled coefficient at time zero without this exogenous input. This is not the first-step rule in the current draft.

**Correction for finite runs:** after constructing X, b0, and w0, supply

```python
r0 = b0 + X @ w0 / math.sqrt(environment.d)
Y_init = torch.where(environment.Delta == 1,
                     environment.Y,
                     torch.where(r0 >= 0, 1.0, -1.0))
```

The replacement on labeled coordinates satisfies the initialization validator and does not affect their supervised loss.

**Correction for numerical effective dynamics:** add an explicit mode that computes the initial pseudo-label from the constructed effective initial score. Sampling an independent initial label with the same marginal distribution is insufficient: its joint law with the initial score matters. A burn-in schedule with `pi_0=0` defines another algorithm and does not implement the stated fixed-positive-pi recursion.

**Scope nuance:** an arbitrary first update does not by itself invalidate eventual finite-dimensional convergence of the unnormalized code, because its tail from time one follows the draft's map. It does change the initial state of that tail, the trajectory laws, and potentially the final identified branch. The stated fixed-horizon theorem cannot simply be used for the alternate initialization.

### 3. Medium priority: validation currently fails because of positional constructor arguments

Full suite result: **175 passed, 4 failed**. All four failures occur while constructing the data generator, before their intended mathematical checks.

The current constructor order is

```python
IsotropicGaussian(cfg, n_train, dimensions, n_test=0, ...)
```

but `tests/test_finite_manuscript_model.py:53` calls `(cfg, 3, 0, 2, ...)`, and `tests/test_finite_se_configuration.py:27` calls `(data, n, 0, d, ...)`. Both therefore request dimension zero. The second call is parametrized over three normalization settings, giving three failures.

**Correction:** use keyword arguments, e.g. `IsotropicGaussian(cfg=cfg, n_train=3, dimensions=2, n_test=0, ...)`. The failing test named “manuscript” also explicitly verifies normalized loss and exogenous first-step labels. Even after repairing its constructor call, that test name does not establish correspondence with this new PDF.

### 4. Medium priority: document the residual convention before comparing diagnostics

**Evidence:** draft (35), (63)–(65); `src/primitives.py::pseudo_residual`; `src/algorithms.py:151–177`; `src/asymptotics.py:927–957`.

With the objective and labels matched, the conventions are related by

\[
g_{\rm code}^t=-\eta g_{\rm draft}^t,\quad
p_{\rm code}^t=-\eta p_{\rm draft}^t,\quad
\chi_{\rm code}^t=-\eta\chi_{\rm draft}^t.
\]

When the bias and weight pseudo-label coefficients coincide, also
`zeta_code = -eta*zeta_draft`. The code consequently adds these increments, while the draft subtracts eta times the corresponding derivatives. This is a consistent convention, not an update error.

Projection diagnostics must be converted too: alpha coefficients are unchanged, the residual Gram matrix is multiplied by eta squared, forward phi coefficients by `-1/eta`, and backward phi coefficients by `-eta`. Innovation standard deviations remain nonnegative, so identifying complete Gaussian realizations additionally requires a sign change in the corresponding parameter-side innovations. An explicit notation table would prevent incorrect comparisons of signed residual observables or memory coefficients.

### 5. Low priority: references and notation

- Definition 4.6, p. 11, refers to “Theorem B.1”; the result is **Lemma B.1**. There is also a doubled period after the atomlessness statement.
- The proof of Proposition 4.9, p. 43, defines the effective history `H^[g]_{t+1}` but subsequently conditions on `F^[g]_{t+1}`. Use the defined effective history consistently; the finite-dimensional filtrations use F elsewhere.
- In Lemma C.1, the Gaussian upper-tail estimate is valid. A direct citation is Vershynin's **Corollary 5.35**, obtained from Theorem 5.32 and Proposition 5.34. The current two-result citation is sufficient in substance; the corollary is easier to locate.
- `docs/ARCHITECTURE.md`, `src/utils.py`, and tests still describe the normalized/exogenous-initial-label model as manuscript-consistent. They need a version-specific correspondence statement.

## Proof audit

### A. Finite-dimensional potential and convergence: no blocking gap found

The sign assumptions and convexity imply that the selected loss derivative is bounded on each selected half-line and that its integral is bounded below. The explicit expression (49) is correct, including both threshold values. The derivative jumps downward at both thresholds, so `psi_kappa(r) - L_ell*r` is nonincreasing with the prescribed selected-boundary values. Consequently the global upper-quadratic bound (51) is valid across thresholds, not merely within a branch.

Coercivity uses both labeled classes to bound the unpenalized intercept; penalty coercivity bounds w. The positive Hessian argument is valid even without a positive dimension-independent lower bound on j'', because d is fixed here.

The key separation in Lemma A.2 is valid: two distinct branches whose closures intersect can differ only by selected/unselected transitions at a common threshold. Choosing points in the actual branches gives a direction on which every changed coordinate contributes with the same strict sign in (56). Cancellation between different feature vectors does not invalidate that scalar-product argument. Infinite changes would therefore give two distinct stationary branch gradients at a common limit point, a contradiction.

After identification, the smooth branch map is defined on the entire ambient space. Its local contraction argument does not require a ball contained in the branch. The closure bars in Theorem 4.4 and (57) were verified visually and are essential.

**Interpretation to preserve:** the limit need not be a fixed point of the actual threshold-assigned map, nor a local minimum of V. Remark 4.5 correctly allows this. A concrete example is d=1, all feature vectors zero, ridge penalty, two positive and one negative labeled observations, and at least one unlabeled observation. Take `kappa_+=log(2)`, `kappa_-=-1`, `pi=1`, `lambda=.1`, `eta=.1`, `w0=0`, and `0<b0<log(2)`. All unlabeled examples remain unselected at every finite time, and

\[
b^{t+1}=b^t-.1\{\operatorname{sigmoid}(b^t)-2/3\}\uparrow\log 2.
\]

The limit belongs to the closure of the unselected branch, but threshold equality selects all unlabeled examples. At the limit the intercept gradient is `-1/3`, so the actual update moves away. The right derivative of V is negative there, so it is not a local minimum either. The step-size condition is satisfied (`Lambda_d=.5`). This example is allowed because the finite-dimensional theorem permits arbitrary fixed features.

### B. Effective recursion and finite-horizon convergence: no blocking gap found

The forward and backward aspect-ratio factors in (31)–(32), (64)–(65), and (80), (89) agree. In particular,

\[
q^t=Uw^t/\sqrt d,\quad p^t=U^\top g^t/\sqrt n,
\]

give a forward memory multiplier `1/sqrt(delta)` and a backward one `sqrt(delta)`. The parameter update then has `sigma/sqrt(delta)`.

Lemma B.1 supplies a genuine nondegeneracy argument. Initial positive weight energy supplies a full-support Gaussian score. On a positive-probability labeled cell, the continuous nonconstant loss derivative has positive conditional variance under that score. This forces a positive residual innovation; the next fresh parameter-side Gaussian then forces a positive weight innovation. The induction avoids assuming nondegeneracy as an unexplained genericity condition.

The adaptive Gaussian conditioning in B.8 is justified by its sequential construction: each new multiplication direction is measurable before its corresponding observation. Conditioning on a direction chosen by the new, not-yet-observed product would not be justified, but that is not what the proof does. The remaining matrix subspace and its orthogonal projection have the stated forms, including rank-deficient histories.

The projected Gaussian errors have expected normalized squared norm of order `t/n` or `(t+1)/d`. Tightness, rather than uniform integrability of their random amplitudes, suffices through the conditional Markov argument given in the proof.

Lemma B.5 correctly combines W2 convergence, almost-everywhere continuity, and a local uniform linear-growth bound. In particular, bounded indicators with discontinuities only at the confidence thresholds can be appended because the limiting scores are atomless. No differentiation through hard selection is needed. Lemma B.6 uses conditional independence of the fresh Gaussian coordinates and transfers back through equality of joint laws with the measurable history. The population test-error formula (43) has the correct signs and noise scale.

**Scope to preserve:** the initialization in Theorem 4.7 is deterministic conditional on the quenched environment. A weight vector trained on the same Gaussian design is generally outside this assumption. Random initialization independent of the design may be covered by an additional conditioning argument once the required empirical limits are verified; design-dependent pretraining needs further work.

### C. Long-time convergence: no blocking gap found

The proof does more than infer convergence from square-summable increments. It establishes the additional switching and two-time stability estimates needed to make the effective process Cauchy.

The central estimate (119) is plausible and the stated proof verifies it. Projecting orthogonally to the deterministic signal leaves an iid Gaussian `(d-1) by M` matrix. For each fixed nonzero v, its image divided by the norm of v is a standard Gaussian vector. A small-ball estimate followed by a union bound over at most `7^M` vectors gives the simultaneous lower bound when `M/d` has a finite limit and epsilon is chosen sufficiently small. This is a bound on a finite alphabet, not a lower singular-value bound on all of R^M; it therefore does not conflict with a nontrivial kernel when M>d. Simultaneity allows the switch vector to depend on the data.

The approximation error in (121) is controlled by score displacement even for direct negative-to-positive transitions, because both thresholds then lie between the old and new scores. Combining this with the design upper bound and the two successive update norms gives (124). Its constants may be very poor as the aspect ratio grows, but remain positive and independent of time, which is what the theorem needs.

Uniform localization in C.4 is supported by strong penalty curvature and both labeled classes. The averaged lower bound on supervised loss curvature is sufficient: the mixed intercept/weight cancellation is explicitly handled on p. 49 rather than ignored. C.5 then uses bounded loss derivatives and the fraction of changed configurations to compare branch gradients. This yields a dimension-independent two-time parameter bound.

The argument passes inequalities to deterministic fixed-time limits, then sums the resulting effective-process inequalities. It does not interchange infinite time and dimension. Borel–Cantelli is correctly applied without any independence assumption on switching events.

**Scope to preserve:** the result is L2 convergence of effective weights and scores, and almost-sure eventual stabilization of the representative unlabeled configuration. It does not provide a uniform-in-d approximation for arbitrarily large times, a rate for identification times, commutation of limits, uniqueness of a global attractor, or global optimization. Finite-time atomlessness also does not establish atomlessness of the limiting score; Corollary 4.11 appropriately adds a boundary-mass assumption for identifying the terminal configuration directly from the terminal score.

## Numerical verification and limits

An independent eight-step implementation of Algorithm 3.2 with logistic loss, ridge penalty, asymmetric thresholds, and initial score-sign labels was compared to finite GD with `normalize_unlabeled_loss=False` and matching Y_init. Maximum weight-coordinate discrepancy across all eight steps was `2.220446049250313e-16`; final intercept discrepancy was `2.7755575615628914e-17`. This supports the update scaling and signs under matched conventions.

On the same deterministic seeded instance, the initial selected fraction was `.5`; enabling normalization changed the first weight update by Euclidean norm `0.03932045186772745`. Thus the normalization mismatch is observable, not merely notational.

The four initially selected test files produced 20 passes and one constructor failure. The full suite produced 175 passes and four constructor failures in 6.72 seconds, using:

```bash
PYTHONPATH=. MPLBACKEND=Agg MPLCONFIGDIR=/private/tmp/codex-mplconfig python3 -m pytest -q
```

These are finite computational checks, not proofs of the high-dimensional or long-time theorems. No new finite-size convergence experiment, full notebook execution, or complete literature-priority audit was performed.

## Recommended revision order

1. Define one explicit current-draft execution mode: unnormalized loss, endogenous initial score-sign labels, fixed pi, raw hard thresholds, updated intercept, and equal bias/weight pseudo-label coefficients.
2. Implement the corresponding initial-label mode in the numerical effective process and add an independent manuscript-reference comparison. Existing finite/SE agreement tests alone do not identify which manuscript they implement.
3. Repair the four constructor failures with keyword arguments and update the “manuscript-consistent” documentation and test descriptions.
4. Correct the minor references and add a notation table for residuals and memory coefficients.
5. Keep the boundary-limit caveat and the order-of-limits scope explicit when summarizing the convergence results.

## External sources checked

- Roman Vershynin, *Introduction to the non-asymptotic analysis of random matrices*, Theorem 5.32, Proposition 5.34, and Corollary 5.35: https://arxiv.org/pdf/1011.3027. This supports the Gaussian matrix estimate used in C.1; it is not a source for the draft's original convergence arguments.
- Gerbelot et al., *Rigorous Dynamical Mean-Field Theory for Stochastic Gradient Descent Methods*, SIAM Journal on Mathematics of Data Science 6(2), 400–427 (2024): https://doi.org/10.1137/23M1594388. Publication metadata and the general Gaussian-conditioning context were checked; no assertion is made here that this paper directly proves the discontinuous recursion in the draft.
