# Particle simulation of the effective self-training process

This note describes the implementation in
[`MacroscopicStateEvolution`](../src/asymptotics.py) and
[`src/orthogonal.py`](../src/orthogonal.py).
The accompanying manuscript supplies the mathematical interpretation in
Definition 4.6 (the mean-field recursion) and Section 5.1. Statements about numerical operations
refer to the current source. Exact coordinate identities, particle
approximations, and numerical rank regularization are distinguished below.

The maintained comparison entry point is
[`experiments/approximation_accuracy.ipynb`](../experiments/approximation_accuracy.ipynb),
which calls `run_monte_carlo_experiment` in
[`experiments/experiments.py`](../experiments/experiments.py).
The statistical notebook,
[`experiments/statistical_behavior.ipynb`](../experiments/statistical_behavior.ipynb),
computes a finite-model error decomposition and does not run the particle
process.

## 1. Finite model, scaling, and residual convention

Let $d$ be the parameter dimension and $n$ the number of training observations.
The realized environment consists of a signal vector
$\mu\in\mathbb R^d$, labels $Y_i\in\{-1,+1\}$, and observation indicators
$\Delta_i\in\{0,1\}$. Write

$$
I_{\mathcal L}=\{i:\Delta_i=1\},\qquad
I_{\mathcal U}=\{i:\Delta_i=0\},\qquad
N=|I_{\mathcal L}|,\quad M=|I_{\mathcal U}|,
\quad \rho_n=N/n,\quad\delta_n=n/d.
$$

The Gaussian design and training scores are

$$
X_i=\frac{Y_i\mu}{\sqrt d}+\sigma U_i,
\qquad U_{ij}\stackrel{\mathrm{i.i.d.}}{\sim}\mathcal N(0,1),
\qquad
r_i^t=b^t+\frac{X_i^\top w^t}{\sqrt d}.
$$

Here $\sigma>0$ is the noise scale. The environment is fixed during training;
`IsotropicGaussian.sample_design` generates the design conditionally on it.
`SelfTrainedGradientDescent.fit` receives $X$, the observed-label vector
$y_i^{\mathrm{observed}}=\Delta_iY_i$, and explicit initial conditions.
Unobserved labels and $\mu$ are not inputs to the finite training update.
See [`src/dgp.py`](../src/dgp.py),
[`src/environment.py`](../src/environment.py), and
[`src/algorithms.py`](../src/algorithms.py).

### 1.1 Frozen selection and pseudo-labels

For $\kappa_-<0<\kappa_+$, define

$$
S_\kappa(r)=\mathbf 1_{\{r\geq\kappa_+\}\cup\{r\leq\kappa_-\}},
\qquad
\mathrm{sign}_+(r)=
\begin{cases}
+1,&r\geq0,\\
-1,&r<0.
\end{cases}
$$

Both threshold equalities are selected. The default pseudo-label is
$\widehat Y_i^t=\mathrm{sign}_+(r_i^t)$ at **every** iteration,
including $t=0$. An explicitly supplied $Y^{\mathrm{init}}$ can replace this
rule only at $t=0$. On labeled coordinates that override must agree with $Y$.
The selection mask and pseudo-labels are frozen before evaluating the score
gradient: neither the threshold map nor the pseudo-label map is differentiated.
These conventions are shared by `AlgorithmConfig.selection_mask`,
`HardSelection`, and the functions in [`src/primitives.py`](../src/primitives.py).
The supported special case $\kappa_-=\kappa_+=0$ selects every score and still
uses $\mathrm{sign}_+(0)=+1$.

Let $\ell(r,y)$ denote the per-observation loss and
$\ell_r(r,y)=\partial\ell(r,y)/\partial r$ its score derivative. Write
$\eta_w$ for `step_size`, $\pi$ for `pseudo_label_param`, and $\lambda$ for
`penalty_param`. For $0<\rho_n<1$, the code's weight residual is

$$
u_i^t=-\eta_w\left[
\frac{\Delta_i}{\rho_n}\ell_r(r_i^t,Y_i)
+\frac{(1-\Delta_i)\pi}{1-\rho_n}
 S_\kappa(r_i^t)\ell_r(r_i^t,\widehat Y_i^t)
\right].
$$

**The finite increment $u^t$ includes the learning rate and descent sign.**
The manuscript and effective implementation instead use the score gradient
$g^t=-u^t/\eta_w$ for positive $\eta_w$; at zero rate, $g^t$ is still
computed directly from the bracketed expression. The finite API retains
`FiniteStep.g` and callback residual names for these increments.
There is no division by the selected fraction. Thus the unlabeled part uses
the total unlabeled pool, rather than the selected pool, as its denominator.
For $\rho_n=1$ the unlabeled term is omitted; a finite fit requires $N>0$.
An empty selection or $\pi=0$ also gives a zero unlabeled contribution.

The default loss and penalty in [`src/objectives.py`](../src/objectives.py) are

$$
\ell(r,y)=\log(1+e^{-yr}),\qquad
\ell_r(r,y)=-y\,\mathrm{sigmoid}(-yr),\qquad
J(w)=\frac12\sum_{j=1}^d w_j^2.
$$

For a separable penalty $J(w)=\sum_j j(w_j)$, set
$h^t=-\eta_w\lambda j'(w^t)$ coordinatewise. The implemented finite update is

$$
w^{t+1}=w^t+h^t+\frac{\sqrt d}{n}X^\top u^t.
$$

Custom loss and penalty implementations can be supplied through the current
interfaces; the scalar effective-process interpretation assumes the relevant
derivatives act coordinatewise. In particular, ridge gives
$h^t=-\eta_w\lambda w^t$.

### 1.2 Bias controls

The defaults use the same residual for weights and intercept. The code also
supports a separate bias rate $\eta_b$ (`bias_step_size`) and pseudo-label
coefficient $\pi_b$ (`bias_pseudo_label_param`). When the bias is trainable,
define $u_b^t$ by the preceding residual formula with
$(\eta_w,\pi)$ replaced by $(\eta_b,\pi_b)$. Then

$$
b^{t+1}=b^t+\frac1n\sum_i u_{b,i}^t.
$$

The defaults are $\eta_b=\eta_w$ and $\pi_b=\pi$, hence $u_b^t=u^t$.
With `train_bias=False`, $b^{t+1}=b^t$; the fixed bias remains in every score.
In that case the implementation retains $u_b^t=u^t$ for diagnostics but does
not apply its mean. The bias is not penalized.

### 1.3 Exact finite decomposition and proportional regime

Introduce the finite observables and fluctuations

$$
m^t=\frac{\mu^\top w^t}{d},\qquad
\chi_u^t=\frac{Y^\top u^t}{n},\qquad
q^t=\frac{Uw^t}{\sqrt d},\qquad
p_u^t=\frac{U^\top u^t}{\sqrt n}.
$$

Substitution into the score and weight updates gives the exact identities

$$
r^t=b^t\mathbf 1_n+m^tY+\sigma q^t,
\qquad
w^{t+1}=w^t+h^t+\chi_u^t\mu+
\frac{\sigma}{\sqrt{\delta_n}}p_u^t.
$$

These are the identities evaluated by
`SelfTrainedGradientDescent.finite_decomposition`, whose existing `chi` and
`p` fields store $\chi_u^t$ and $p_u^t$. In manuscript units the corresponding
quantities are $\chi^t=Y^\top g^t/n$ and $p^t=U^\top g^t/\sqrt n$,
and the weight update subtracts
$\eta_w(\chi^t\mu+\sigma p^t/\sqrt{\delta_n})$.
These identities explain all powers of
$d,n,\delta_n$ used below. The effective recursion describes the proportional
regime $n,d\to\infty$ with $\delta_n\to\bar\delta\in(0,\infty)$,
$\rho_n\to\bar\rho$, and limiting coordinate laws for the environment and
initialization, over a fixed time horizon $T$. `DataConfig` supplies
$\bar\delta$, $\bar\rho$, the class prior $p=\mathbb P(Y=+1)$, $\sigma$, and
the signal-coordinate law. The particle algorithm is a numerical evaluation
of that recursion, not an additional proof of its high-dimensional limit.

## 2. Limiting scalar recursion and its memory structure

Use tildes for limiting random variables and
$\widetilde{\mathbb E}$ for their expectations. Parameter-coordinate variables
are $(\widetilde\mu,\widetilde w^t,\widetilde p^t,\widetilde h^t)$;
sample-coordinate variables are
$(\widetilde Y,\widetilde\Delta,\widetilde q^t,
\widetilde r^t,\widetilde g^t)$.
The scalar $\bar b^t$ and moment/projection coefficients are deterministic
in the limiting construction. The two base blocks have their prescribed
parameter and sample laws and are independent of each other and of the
primitive Gaussian innovations.

For $t\geq0$, let $\widetilde W_t$, $\widetilde P_t$,
$\widetilde G_t$, and $\widetilde Q_t$ be row vectors containing the
corresponding scalar histories from time $0$ through $t$. Define the
uncentered moment matrices

$$
\bar C_t^{[w]}=\widetilde{\mathbb E}
 [\widetilde W_t^\top\widetilde W_t],\qquad
\bar C_t^{[g]}=\widetilde{\mathbb E}
 [\widetilde G_t^\top\widetilde G_t].
$$

They are positive semidefinite Gram matrices, not centered covariances in
general. Means need not vanish. A dagger denotes the Moore–Penrose inverse.
Empty histories at $t=0$ contribute zero to every associated product.

The forward projection coefficients, orthogonal residual, innovation scale,
and memory coefficients are

$$
\begin{aligned}
\bar\alpha_t^{[w]}&=(\bar C_{t-1}^{[w]})^\dagger
 \widetilde{\mathbb E}[\widetilde W_{t-1}^\top\widetilde w^t],\\
\widetilde w_\perp^t&=\widetilde w^t-
 \widetilde W_{t-1}\bar\alpha_t^{[w]},\\
\bar v_t^{[w]}&=
 \sqrt{\widetilde{\mathbb E}[(\widetilde w_\perp^t)^2]},\\
\bar\phi_t^{[w]}&=(\bar C_{t-1}^{[g]})^\dagger
 \widetilde{\mathbb E}[\widetilde P_{t-1}^\top\widetilde w_\perp^t],\\
\widetilde q^t&=
 \widetilde Q_{t-1}\bar\alpha_t^{[w]}
 +\bar\delta^{-1/2}\widetilde G_{t-1}\bar\phi_t^{[w]}
 +\bar v_t^{[w]}Z_t^{[g]}.
\end{aligned}
$$

Here $Z_t^{[g]}$ is a new standard normal variable in sample-coordinate
space. Next compute

$$
\bar m^t=\widetilde{\mathbb E}[\widetilde\mu\widetilde w^t],
\qquad
\widetilde r^t=\bar b^t+\bar m^t\widetilde Y+\sigma\widetilde q^t,
$$

and evaluate $\widetilde g^t$ using the bracketed score gradient in Section 1
(without the factor $-\eta_w$), with
$\rho_n$ replaced by $\bar\rho$ and the effective score sign as default
pseudo-label. The backward quantities are

$$
\begin{aligned}
\bar\alpha_t^{[g]}&=(\bar C_{t-1}^{[g]})^\dagger
 \widetilde{\mathbb E}[\widetilde G_{t-1}^\top\widetilde g^t],\\
\widetilde g_\perp^t&=\widetilde g^t-
 \widetilde G_{t-1}\bar\alpha_t^{[g]},\\
\bar v_t^{[g]}&=
 \sqrt{\widetilde{\mathbb E}[(\widetilde g_\perp^t)^2]},\\
\bar\phi_t^{[g]}&=(\bar C_t^{[w]})^\dagger
 \widetilde{\mathbb E}[\widetilde Q_t^\top\widetilde g_\perp^t],\\
\widetilde p^t&=
 \widetilde P_{t-1}\bar\alpha_t^{[g]}
 +\sqrt{\bar\delta}\,\widetilde W_t\bar\phi_t^{[g]}
 +\bar v_t^{[g]}Z_t^{[w]}.
\end{aligned}
$$

$Z_t^{[w]}$ is a new standard normal variable in parameter-coordinate
space. The update is

$$
\begin{aligned}
\bar\chi^t&=\widetilde{\mathbb E}[\widetilde Y\widetilde g^t],
&\bar\zeta_b^t&=\widetilde{\mathbb E}[\widetilde g_b^t],\\
\widetilde h^t&=-\eta_w\lambda j'(\widetilde w^t),
&\widetilde w^{t+1}&=\widetilde w^t+\widetilde h^t-
 \eta_w\bar\chi^t\widetilde\mu-
 \eta_w\frac{\sigma}{\sqrt{\bar\delta}}\widetilde p^t.
\end{aligned}
$$

For trainable bias, $\bar b^{t+1}=\bar b^t-\eta_b\bar\zeta_b^t$;
otherwise it is unchanged. Here $\widetilde g_b^t$ uses the same raw gradient
formula with $\pi$ replaced by $\pi_b$; its rate is applied only in the
intercept update. With a fixed intercept, its diagnostic equals
$\widetilde g^t$. Under the default shared residual,
$\bar\zeta_b^t=\bar\zeta^t=
\widetilde{\mathbb E}[\widetilde g^t]$.

The historical projection terms retain the part explained by the past
trajectory. The $\phi$ terms describe the additional dependence created by
reusing the same Gaussian design in the forward and transpose operations.
Only the remaining orthogonal component is represented by a fresh Gaussian.
For example, writing
$a_t=\widetilde{\mathbb E}[\widetilde W_{t-1}^\top\widetilde w^t]$,
the forward innovation variance satisfies

$$
(\bar v_t^{[w]})^2=
\widetilde{\mathbb E}[(\widetilde w^t)^2]
-a_t^\top(\bar C_{t-1}^{[w]})^\dagger a_t.
$$

The particle code obtains the corresponding nonnegative quantity by taking
the norm of an orthogonal residual, rather than subtracting nearly equal
second moments. The variables $Z^{[g]}$ and $Z^{[w]}$ are independent
innovations; the complete $q,p$ trajectories also contain nonlinear memory
terms and should not be asserted jointly Gaussian.

## 3. Particle populations and initialization

On an auxiliary particle probability space, draw independent populations

$$
(\mathring\mu_k,\mathring w_k^0)_{k=1}^{K_w}
 \stackrel{\mathrm{i.i.d.}}{\sim}\bar\nu_{(\mu,w^0)},\qquad
(\mathring Y_i,\mathring\Delta_i)_{i=1}^{K_g}
 \stackrel{\mathrm{i.i.d.}}{\sim}\bar\nu_{(Y,\Delta)}.
$$

The circles distinguish particle variables from limiting scalar variables
and finite-model vectors. Hats below denote scalar particle estimates.
The particle budgets $K_w,K_g$ approximate two different coordinate laws;
they do not replace $d,n$ in $\bar\delta$. In particular,
$K_g/K_w=\bar\delta$ is **not** required. The class accepts independent
`K_w` and `K_g`; supplying only one copies it to the other. With neither
specified, `K` sets both budgets and defaults to $1000$.

The default parameter law draws signal coordinates from
`DataConfig.signal_law` and independent $\mathcal N(0,1)$ initial weights.
No normalization of the sampled vector is performed. The default sample
law is the product law

$$
\mathbb P(\mathring Y=+1)=p,\qquad
\mathbb P(\mathring\Delta=1)=\bar\rho,
\qquad\mathring Y\ \perp\ \mathring\Delta.
$$

`parameter_base_sampler(K_w, generator, dtype, device)` may instead return
the joint pair $(\mathring\mu,\mathring w^0)$, preserving dependence within
that pair. `initial_weight` permits an explicit parameter-particle vector
when no parameter-base sampler is supplied. Similarly,
`sample_base_sampler(K_g, generator, dtype, device)` returns
$(\mathring Y,\mathring\Delta,Y^{\mathrm{init}})$; its third output may be
`None`, which uses score-sign labels from time zero. A non-`None` output is
an exogenous first-step override, not the default initialization.
Supplied samplers define the intended laws; the code checks shapes, finite
values, and discrete-label constraints, not the samplers' i.i.d. property.

[`state_evolution_sample_base_sampler`](../src/environment.py) adapts a
joint sample-type law to this interface. `FourCellSampleTypeLaw` can encode
dependence between $Y$ and $\Delta$. For that use, the configured $p$ and
$\bar\rho$ must agree with the law's marginals: the effective residual still
uses the configured $\bar\rho$. The current notebooks use the consistent
product-law case. The initial bias is `AlgorithmConfig.initial_bias`,
defaulting to $0$, unless the low-level constructor's `initial_bias`
argument overrides it.

### 3.1 Random streams and primitive innovations

For every $t=0,\ldots,T$, initialization allocates

$$
z_t^{[g]}\sim\mathcal N(0,I_{K_g}),\qquad
z_t^{[w]}\sim\mathcal N(0,I_{K_w}),
$$

independently across time, families, and base populations. The superscript
on a primitive innovation denotes its **ambient space**: sample-space
$z^{[g]}$ drives the forward fluctuation $q$, and parameter-space
$z^{[w]}$ drives the backward fluctuation $p$. Superscripts on trajectory
coefficients instead identify the source weight or residual trajectory.

`MacroscopicStateEvolution` uses separate Torch generators for the parameter
base, sample base, sample innovations, and parameter innovations. Their
stream identifiers are $11,23,37,53$, with seeds

```math
s_a=(\texttt{mc\_seed}+1\,000\,003a)\bmod(2^{63}-1).
```

The scalar signal callback is sampled in an isolated global RNG
context with stream $83$. Custom-sampler calls also isolate and restore the
global Torch, NumPy, and Python states, using fallback streams $71$ and
$97$. Custom samplers should use their supplied generator. These mechanisms
separate streams; they cannot enforce independence if a custom sampler
introduces external shared state.

Once shared empirical quantities are evaluated, already at $t=0$, particles
interact through empirical averages, projection coefficients, and innovation
scales. They are therefore not
independent trajectory samples, even though their primitive inputs are
sampled independently.

## 4. Empirical trajectory coordinates

For vectors on the two sides, use the empirical inner products

$$
\langle x,y\rangle_{K_w}=K_w^{-1}x^\top y,
\qquad
\langle u,v\rangle_{K_g}=K_g^{-1}u^\top v,
\qquad \|x\|_K=\sqrt{K^{-1}x^\top x}.
$$

These replace $\widetilde{\mathbb E}[XY]$. They are not centered sample
covariances and have no $K-1$ correction.

Collect columns through time $t$ into matrices

$$
\begin{aligned}
\mathring W_t&=[\mathring w^0\ \cdots\ \mathring w^t]
 \in\mathbb R^{K_w\times(t+1)},\\
\mathring P_t&=[\mathring p^0\ \cdots\ \mathring p^t]
 \in\mathbb R^{K_w\times(t+1)},\\
\mathring G_t&=[\mathring g^0\ \cdots\ \mathring g^t]
 \in\mathbb R^{K_g\times(t+1)},\\
\mathring Q_t&=[\mathring q^0\ \cdots\ \mathring q^t]
 \in\mathbb R^{K_g\times(t+1)},\\
\mathring R_t&=[\mathring r^0\ \cdots\ \mathring r^t]
 \in\mathbb R^{K_g\times(t+1)}.
\end{aligned}
$$

The code stores individual vectors in lists of length $T+1$ and
stacks computed columns when required. Its maintained bases and coordinate
matrices have dimensions

$$
\begin{aligned}
B_t^{[w]}&\in\mathbb R^{K_w\times r_t^{[w]}},
&\Theta_t^{[w]}&\in\mathbb R^{r_t^{[w]}\times(t+1)},\\
B_t^{[g]}&\in\mathbb R^{K_g\times r_t^{[g]}},
&\Theta_t^{[g]}&\in\mathbb R^{r_t^{[g]}\times(t+1)}.
\end{aligned}
$$

Here $r_t^{[w]},r_t^{[g]}$ are maintained numerical ranks, each at most
$t+1$. In exact arithmetic their columns satisfy

$$
K_w^{-1}(B_t^{[w]})^\top B_t^{[w]}=I,
\qquad K_g^{-1}(B_t^{[g]})^\top B_t^{[g]}=I.
$$

A basis column thus has Euclidean norm $\sqrt{K_w}$ or $\sqrt{K_g}$,
rather than $1$.

### 4.1 Sequential CGS2 and rank acceptance

`EmpiricalOrthogonalBasis.project_and_update` processes one vector $x^s$
against the past basis $B_{s-1}\in\mathbb R^{K\times r_{s-1}}$.
The initial basis is empty, with rank zero. It performs two classical
Gram–Schmidt passes:

$$
\begin{aligned}
c_1&=K^{-1}B_{s-1}^\top x^s,&
u_1&=x^s-B_{s-1}c_1,\\
c_2&=K^{-1}B_{s-1}^\top u_1,&
u_2&=u_1-B_{s-1}c_2,\\
\beta_s&=c_1+c_2,&\rho_s&=\|u_2\|_K.
\end{aligned}
$$

For an empty basis, $\beta_s$ is empty and $u_2=x^s$.
The second pass reduces loss of orthogonality when cancellation leaves a
small component in the old span. A new direction is accepted precisely when

$$
\rho_s>\varepsilon_{\mathrm{rank}}\|x^s\|_K.
$$

The inequality is strict. The default `eps_rank` is $10^{-10}$; zero is
also allowed. On acceptance, append $u_2/\rho_s$ to the basis and set
$\theta_s=(\beta_s^\top,\rho_s)^\top$. Otherwise retain the old basis and
set $\theta_s=\beta_s$. Earlier columns of $\Theta$ are zero-padded when
a new basis row is added; their coordinates are not refitted. Every input
column is appended to $\Theta$, including dependent columns.

`OrthogonalizationResult` returns the past coordinates $\beta_s$, current
coordinates $\theta_s$, raw residual $u_2$, norm $\rho_s$, input norm,
rank information, and `truncated`. That flag means the direction was
rejected although $\rho_s>0$; floating-point residue on an otherwise
dependent column can also set it.

**Rejection does not set $u_2$ or $\rho_s$ to zero.** The residual and its
norm are still used in the current memory term and Gaussian innovation.
Only their representation as a new basis direction is omitted. Hence rank
truncation regularizes subsequent coordinate calculations, including the
same iteration's backward memory after a weight-basis rejection. It does not
remove the current innovation.

### 4.2 Exact identities and truncation errors

If no nonzero direction is discarded, exact arithmetic gives

$$
\mathring W_t=B_t^{[w]}\Theta_t^{[w]},\qquad
\mathring G_t=B_t^{[g]}\Theta_t^{[g]},
$$

and consequently

$$
K_w^{-1}\mathring W_t^\top\mathring W_t
 =(\Theta_t^{[w]})^\top\Theta_t^{[w]},\qquad
K_g^{-1}\mathring G_t^\top\mathring G_t
 =(\Theta_t^{[g]})^\top\Theta_t^{[g]}.
$$

With rejected nonzero residuals, define
$E_t^{[w]}=\mathring W_t-B_t^{[w]}\Theta_t^{[w]}$ and analogously
$E_t^{[g]}$. For a rejected column $s$, the corresponding reconstruction
error obeys

$$
\|E_t^{[w]}[:,s]\|_{K_w}
 \leq\varepsilon_{\mathrm{rank}}\|\mathring w^s\|_{K_w},
\qquad
\|E_t^{[g]}[:,s]\|_{K_g}
 \leq\varepsilon_{\mathrm{rank}}\|\mathring g^s\|_{K_g},
$$

up to floating-point error. Columns here use zero-based time indices.
These local bounds are not global error bounds for the recursively
coupled particle system.

## 5. Transported histories and stable least squares

Define the forward history transported into weight coordinates and the
backward history transported into residual coordinates by

$$
Q_t^{[w]}=\mathring Q_t(\Theta_t^{[w]})^\dagger
 \in\mathbb R^{K_g\times r_t^{[w]}},\qquad
P_t^{[g]}=\mathring P_t(\Theta_t^{[g]})^\dagger
 \in\mathbb R^{K_w\times r_t^{[g]}}.
$$

These formulas specify the exact least-squares quantities. The implementation
`solve_transported_history` computes them without forming a pseudoinverse:

$$
\begin{aligned}
(Q_t^{[w]})^\top&=
 \mathop{\mathrm{argmin}}\limits_{A\in\mathbb R^{r_t^{[w]}\times K_g}}
 \| (\Theta_t^{[w]})^\top A-\mathring Q_t^\top\|_F^2,\\
(P_t^{[g]})^\top&=
 \mathop{\mathrm{argmin}}\limits_{A\in\mathbb R^{r_t^{[g]}\times K_w}}
 \| (\Theta_t^{[g]})^\top A-\mathring P_t^\top\|_F^2.
\end{aligned}
$$

The minimizer is unique when the maintained coordinate matrix has full row
rank. If the solver identifies a smaller rank, the rank-aware least-squares
solution uses that smaller numerical space. The code returns the correctly
shaped empty matrix for rank zero. The left-hand matrices are small in
trajectory dimension, although there is one right-hand side per particle on
the opposite side.

### 5.1 Solver controls and conditioning

`torch.linalg.lstsq` receives `rcond=lstsq_rcond`, and receives a `driver`
only when `lstsq_driver` is specified. Both options default to `None`.
For the pinned PyTorch 2.8 version, the CPU default is pivoted QR (`gelsy`);
CUDA uses `gels`, which assumes full rank. CPU SVD drivers can be requested
explicitly. With the default `rcond`, the rank threshold is based on machine
precision and matrix dimensions. These are library semantics, not a
code-selected fixed SVD method or an automatic fallback policy.
See the [PyTorch 2.8 least-squares documentation](https://docs.pytorch.org/docs/2.8/generated/torch.linalg.lstsq.html).

The basis tolerance and the solver tolerance address different operations.
`eps_rank` decides whether to augment a trajectory basis; `lstsq_rcond`
affects the numerical rank resolved when transporting the history. The
production code uses the returned solution and does not record the solver's
reported rank. Thus exact Moore–Penrose equivalences require both faithful
trajectory coordinates and a solve that resolves the maintained rank.

For an exact factorization, the nonzero singular values of
$\mathring W_t/\sqrt{K_w}$ equal those of $\Theta_t^{[w]}$.
For a full-column-rank trajectory $A$,

$$
\kappa_2(A^\top A)=\kappa_2(A)^2,
$$

whereas the coordinate matrix retains the trajectory's nonzero-subspace
condition number. Working in coordinates avoids the squaring introduced by
normal equations; it does not eliminate intrinsic near-dependence.

The current solver recomputes each transported history from all available
columns at every half-step. There is no implemented block-inverse fast path.
In the special case of successive full-rank square coordinate matrices,
the identity

$$
Q_t^{[w]}=
\left[Q_{t-1}^{[w]}\quad
\frac{\mathring q^t-Q_{t-1}^{[w]}\beta_t^{[w]}}
 {\rho_t^{[w]}}\right]
$$

explains the manuscript's online formula, but it is not the production
algorithm. It is not a general pseudoinverse update after rank loss. Even
when a new column adds no direction, the Moore–Penrose transport must be
recomputed for the enlarged coordinate matrix and fluctuation history.

## 6. Implemented particle recursion

At the beginning of iteration $t$, the code has
$\mathring w^t,\hat b^t$, the histories through $t-1$, and their bases and
transported histories. For $t=0$ all past matrices are empty.

### 6.1 Forward half-step

First apply CGS2 to $\mathring w^t$ against $B_{t-1}^{[w]}$.
It returns the past projection coordinates
$\beta_t^{[w]}\in\mathbb R^{r_{t-1}^{[w]}}$, residual
$\mathring w_\perp^t\in\mathbb R^{K_w}$, and scale
$\hat v_t^{[w]}=\|\mathring w_\perp^t\|_{K_w}$,
while updating $B_t^{[w]},\Theta_t^{[w]}$. Set

$$
\psi_t^{[w]}=
\frac1{K_w}(P_{t-1}^{[g]})^\top\mathring w_\perp^t
 \in\mathbb R^{r_{t-1}^{[g]}}.
$$

Then evaluate

$$
\mathring q^t=
Q_{t-1}^{[w]}\beta_t^{[w]}
+\frac1{\sqrt{\bar\delta}}B_{t-1}^{[g]}\psi_t^{[w]}
+\hat v_t^{[w]}z_t^{[g]}
\quad\in\mathbb R^{K_g}.
$$

Both residual-side objects on the right are **past** objects. Append this
column to $\mathring Q_{t-1}$ and solve for $Q_t^{[w]}$ using the updated
weight coordinates. Next compute

$$
\hat m^t=\frac1{K_w}\mathring\mu^\top\mathring w^t,
\qquad
\hat\tau^t=\sqrt{\frac1{K_w}\|\mathring w^t\|_2^2},
\qquad
\mathring r^t=\hat b^t\mathbf 1_{K_g}
+\hat m^t\mathring Y+\sigma\mathring q^t.
$$

Compute the raw-score selection and record the population-denominator
selection estimate

$$
\hat\omega_{\mathrm{pop}}^t=
\frac{1}{K_g(1-\bar\rho)}
\sum_{i=1}^{K_g}(1-\mathring\Delta_i)S_\kappa(\mathring r_i^t).
$$

For $\bar\rho=1$, `compute_selection_rate` returns zero.
The residual is evaluated coordinatewise as

$$
\mathring g_i^t=\left[
\frac{\mathring\Delta_i}{\bar\rho}
 \ell_r(\mathring r_i^t,\mathring Y_i)
+\frac{(1-\mathring\Delta_i)\pi}{1-\bar\rho}
 S_\kappa(\mathring r_i^t)
 \ell_r(\mathring r_i^t,\mathrm{sign}_+(\mathring r_i^t))
\right].
$$

The same first-step override and zero-unlabeled-term conventions as in
Section 1 apply, without incorporating a learning rate into the residual. In particular, $\hat\omega_{\mathrm{pop}}^t$ is a
diagnostic and is **not** an argument that rescales this residual.
The companion bias residual is also computed when its settings differ.
This is the order in `MacroscopicStateEvolution.forward_pass`.

### 6.2 Backward half-step and parameter update

Apply CGS2 to $\mathring g^t$ against the past residual basis. It returns
$\beta_t^{[g]}\in\mathbb R^{r_{t-1}^{[g]}}$,
$\mathring g_\perp^t\in\mathbb R^{K_g}$, and
$\hat v_t^{[g]}=\|\mathring g_\perp^t\|_{K_g}$, while updating
$B_t^{[g]},\Theta_t^{[g]}$. Using the **already updated** forward transport,
compute

$$
\psi_t^{[g]}=
\frac1{K_g}(Q_t^{[w]})^\top\mathring g_\perp^t
 \in\mathbb R^{r_t^{[w]}},
$$

and

$$
\mathring p^t=
P_{t-1}^{[g]}\beta_t^{[g]}
+\sqrt{\bar\delta}\,B_t^{[w]}\psi_t^{[g]}
+\hat v_t^{[g]}z_t^{[w]}
\quad\in\mathbb R^{K_w}.
$$

Append $\mathring p^t$ and solve for $P_t^{[g]}$ with the updated residual
coordinates. The empirical drift coefficients and update are

$$
\begin{aligned}
\hat\chi^t&=\frac1{K_g}\mathring Y^\top\mathring g^t,
&\hat\zeta^t&=\frac1{K_g}\mathbf 1^\top\mathring g^t,
&\hat\zeta_b^t&=\frac1{K_g}\mathbf 1^\top\mathring g_b^t,\\
\mathring h^t&=-\eta_w\lambda j'(\mathring w^t),
&\mathring w^{t+1}&=\mathring w^t+\mathring h^t-
 \eta_w\hat\chi^t\mathring\mu-
 \eta_w\frac{\sigma}{\sqrt{\bar\delta}}\mathring p^t.
\end{aligned}
$$

If the bias is trainable, set $\hat b^{t+1}=\hat b^t-\eta_b\hat\zeta_b^t$;
otherwise retain $\hat b^t$. The code stores the weight and bias residual
means separately as `mean_residual` and `mean_bias_residual`.
`_backward_pass` performs these operations; the public `backward_pass`
permits a parameter update only for $t<T$.

The appearances of $\mathring\mu$ and $\mathring Y$ in the effective
description encode the conditional law of the finite design and its update.
They do not give hidden labels or a known signal to the finite estimator.

### 6.3 Projection equivalence and the role of the memory coordinates

Under an exact factorization and rank-resolving solves, the empirical raw
projection and memory coefficients are

$$
\begin{aligned}
\hat\alpha_t^{[w]}&=(\Theta_{t-1}^{[w]})^\dagger\beta_t^{[w]},
&\hat\phi_t^{[w]}&=(\Theta_{t-1}^{[g]})^\dagger\psi_t^{[w]},\\
\hat\alpha_t^{[g]}&=(\Theta_{t-1}^{[g]})^\dagger\beta_t^{[g]},
&\hat\phi_t^{[g]}&=(\Theta_t^{[w]})^\dagger\psi_t^{[g]}.
\end{aligned}
$$

Their represented vectors satisfy

$$
\begin{aligned}
\mathring Q_{t-1}\hat\alpha_t^{[w]}&=
 Q_{t-1}^{[w]}\beta_t^{[w]},
&\mathring G_{t-1}\hat\phi_t^{[w]}&=
 B_{t-1}^{[g]}\psi_t^{[w]},\\
\mathring P_{t-1}\hat\alpha_t^{[g]}&=
 P_{t-1}^{[g]}\beta_t^{[g]},
&\mathring W_t\hat\phi_t^{[g]}&=B_t^{[w]}\psi_t^{[g]}.
\end{aligned}
$$

These are equivalent formulations of the projection and memory terms in
Section 2 after replacing expectations by empirical averages. Production
updates use $\beta,\psi$ directly. `compute_weight_memory` and
`compute_residual_memory` reconstruct $\phi_t^{[w]}\in\mathbb R^t$
and $\phi_t^{[g]}\in\mathbb R^{t+1}$ lazily for diagnostics, using small
least-squares solves. They do not drive the recursion.

### 6.4 Gaussian conditioning and time zero

Conditional on the quantities available before each new innovation, the
fresh contributions have covariance

$$
\mathrm{Cov}(\hat v_t^{[w]}z_t^{[g]}\mid\text{forward history})
 =(\hat v_t^{[w]})^2I_{K_g},\qquad
\mathrm{Cov}(\hat v_t^{[g]}z_t^{[w]}\mid\text{backward history})
 =(\hat v_t^{[g]})^2I_{K_w}.
$$

The forward history here includes the current parameter vector; the backward
history includes the current scores and residual. Independence of the fresh
primitive vector makes these conditional identities exact for the particle
construction. The code does not sample a dense time-covariance matrix or
factor a trajectory covariance by Cholesky. Temporal dependence is generated
sequentially by the transported histories and memory terms.
`forward_innovation_scale` and `backward_innovation_scale` contain standard
deviations, not their squares.

At $t=0$ the forward projection and memory terms vanish, so

$$
\mathring q^0=\|\mathring w^0\|_{K_w}z_0^{[g]}.
$$

The backward memory generally does **not** vanish at time zero: it uses
the newly computed $Q_0^{[w]}$ and $B_0^{[w]}$. Thus

$$
\mathring p^0=
\sqrt{\bar\delta}\,B_0^{[w]}\psi_0^{[g]}
+\|\mathring g^0\|_{K_g}z_0^{[w]}.
$$

The empty-rank conventions also cover an exactly zero initial weight or
residual without a special inverse or a division by a zero basis norm.

## 7. Complete causal schedule and terminal evaluation

`n_iterations=T` means exactly $T$ parameter updates. The actual execution
order is the following; `CGS2` includes the rank decision and coordinate
update described above.

```text
Initialize base particles, b[0], w[0], and innovations for t = 0,...,T.
Initialize empty weight/residual bases and transported histories.

For t = 0,...,T:
    CGS2(w[t], past weight basis) -> beta_w, w_perp, v_w; update B_w, Theta_w.
    psi_w = P_g.T @ w_perp / K_w, using past P_g and residual basis.
    Form q[t] from past Q_w, past residual basis, psi_w, and v_w*z_g[t].
    Append q[t]; solve Theta_w.T @ Q_w.T ~= Q_history.T.
    Compute m[t], tau[t], scores r[t], selection, and selection_rate[t].
    Compute g[t] and the companion bias residual with frozen labels/mask.
    Compute population_error[t] and auxiliary oracle diagnostics.

    CGS2(g[t], past residual basis) -> beta_g, g_perp, v_g; update B_g, Theta_g.
    psi_g = Q_w.T @ g_perp / K_g, using the current Q_w.
    Form p[t] from past P_g, current weight basis, psi_g, and v_g*z_w[t].
    Append p[t]; solve Theta_g.T @ P_g.T ~= P_history.T.
    Compute chi[t], weight/bias residual means, and decay[t].
    If t < T:
        Update b[t+1] if trainable and update w[t+1].
```

`step(t)` performs one forward evaluation, error evaluation, and backward
update, then advances `_current_t`. `compute_trajectory` calls it for
$t=0,\ldots,T-1$, followed by the terminal evaluation at $T$ with
`update_parameters=False`. The terminal pass constructs $q^T,g^T,p^T$
and diagnostic coefficients, but creates neither $w^{T+1}$ nor $b^{T+1}$.

Consequently the internal raw histories have $T+1$ entries on both sides.
The theorem-facing `theorem_trajectory` deliberately returns

$$
(W_T,Q_T,R_T,G_{T-1},P_{T-1}),
$$

excluding the auxiliary terminal residual and backward fluctuation.
This separates the finite-update horizon from the desire to evaluate
diagnostics at all states $0,\ldots,T$.

## 8. Observables and finite-model comparison

### 8.1 Alignment, norm, bias, and population classification error

The finite-model and particle quantities correspond as follows.

| Observable | Finite model | Particle estimate | Recorded key |
|---|---|---|---|
| Bias | $b^t$ | $\hat b^t$ | `bias_term` |
| Signal alignment | $d^{-1}\mu^\top w^t$ | $K_w^{-1}\mathring\mu^\top\mathring w^t$ | `weight_signal_alignment` |
| Normalized norm | $\lVert w^t\rVert_2/\sqrt d$ | $\sqrt{K_w^{-1}\lVert\mathring w^t\rVert_2^2}$ | `weight_vector_norm` |

In particular, `weight_vector_norm` is already $\tau^t$, not an unnormalized
Euclidean norm. The plotter can also display $m^t/\tau^t$ as
`normalized_alignment`, with `NaN` when the norm is nonpositive.

For a fresh observation independent of training, the conditional score has
the form $b+mY+\sigma\tau Z$, where $Z\sim\mathcal N(0,1)$ is independent
of $Y$. Hence, for $s=\sigma\tau>0$,

$$
\mathcal E(b,m,\tau)
=p\,\Phi\!\left(\frac{-b-m}{s}\right)
+(1-p)\,\Phi\!\left(\frac{b-m}{s}\right).
$$

`population_error` in [`src/performance.py`](../src/performance.py) evaluates
this expression. The finite callback substitutes finite $b,m,\tau$; the
effective process substitutes their particle estimates. It is not empirical
misclassification on the training particles. At $s=0$, the code evaluates
the exact deterministic-score rule

$$
\mathcal E(b,m,\tau)
=p\,\mathbf1_{\{b+m<0\}}
+(1-p)\,\mathbf1_{\{b-m\geq0\}},
$$

including the positive-label tie convention.

### 8.2 Selected fraction and selected-error fraction

With separated nonzero margins, the active state is
$\mathfrak c^t=S_\kappa(r^t)\mathrm{sign}_+(r^t)$.
The limiting diagnostics are

$$
\bar\omega^t=\widetilde{\mathbb P}
 (\widetilde{\mathfrak c}^t\ne0\mid\widetilde\Delta=0),
\qquad
\bar e^t=\widetilde{\mathbb P}
 (\widetilde{\mathfrak c}^t=-\widetilde Y\mid\widetilde\Delta=0).
$$

The second is the fraction of the **entire unlabeled pool** that is selected
incorrectly, not the error conditional on selection. Define the random
unlabeled particle count $M_g=\sum_i(1-\mathring\Delta_i)$.
For $M_g>0$, the empirical conditional estimates would be

$$
\hat\omega_{\mathrm{emp}}^t=
\frac1{M_g}\sum_{\mathring\Delta_i=0}S_\kappa(\mathring r_i^t),
\qquad
\hat e_{\mathrm{emp}}^t=
\frac1{M_g}\sum_{\mathring\Delta_i=0}S_\kappa(\mathring r_i^t)
\mathbf1_{\{\mathrm{sign}_+(\mathring r_i^t)\ne\mathring Y_i\}}.
$$

The actual effective-process code uses **two denominator conventions**:

- `MacroscopicStateEvolution.selection_rate[t]` stores
  $\hat\omega_{\mathrm{pop}}^t$ from Section 6, with denominator
  $K_g(1-\bar\rho)$, exactly as in the supplied implementation section.
- `run_monte_carlo_experiment` computes `unl_selected_error[t]` from current
  scores using $\hat e_{\mathrm{emp}}^t$, with denominator $M_g$. It returns
  zero if $M_g=0$.

For $0<\bar\rho<1$ and $M_g>0$, the exact relation is

$$
\hat\omega_{\mathrm{pop}}^t=
\frac{M_g}{K_g(1-\bar\rho)}\hat\omega_{\mathrm{emp}}^t.
$$

Thus $\hat\omega_{\mathrm{pop}}^t$ can exceed $1$ at finite particle
budgets; it is not a bounded sample fraction. For instance, if every
particle is unlabeled and selected, it equals $1/(1-\bar\rho)$.
For the empirical estimates at the same time,
$0\leq\hat e_{\mathrm{emp}}^t\leq\hat\omega_{\mathrm{emp}}^t\leq1$.
The corresponding ordering need not hold between
$\hat e_{\mathrm{emp}}^t$ and $\hat\omega_{\mathrm{pop}}^t$.
These are distinct finite-particle estimates of the intended conditional
quantities; equivalence in a particle limit additionally requires
consistency of that limit. No change of estimator is made here.

The finite callback uses the realized total unlabeled count $M$ for both
diagnostics. Hidden finite labels enter the selected-error evaluation only,
and never enter training. For an explicit first-step pseudo-label override,
this diagnostic still evaluates the current **score-sign** label, as the
code does; it is not a diagnostic of the override's label errors.

### 8.3 Recorded time indices

The callback is called before any update and after each update. Bias, norm,
alignment, population error, selected-error fraction, and `unl_usage` refer
to the current state $t=0,\ldots,T$:

```math
\texttt{unl\_usage}[t]=\omega^t,\qquad 0\leq t\leq T.
```

Finite usage is evaluated directly from current unlabeled scores; it requires
`X_unl` but no diagnostic labels. The effective comparison uses
`se.selection_rate[:T+1]`, retaining its population denominator.
The finite selected-error fraction is bounded by usage at every common time.
For the effective particle estimates, their different empirical versus
population denominators can prevent that exact finite-particle inequality.
Residual callback diagnostics still describe the preceding update and start
at zero. See [`TestEvaluatorCallback`](../src/callbacks.py).

### 8.4 Auxiliary stationary-intercept diagnostic

Requesting population error also records `oracle_bias` and `oracle_error`.
The implementation evaluates the stationary-intercept expression

$$
b_{\mathrm{stationary}}=
\frac{\sigma^2\tau^2}{2m}\log\frac p{1-p},
$$

and the population error obtained by replacing only the evaluation bias
with this value. It returns `NaN` for both diagnostics when

$$
|m|\leq\sqrt{\epsilon_{\mathrm{mach}}}
 \max\{1,|\sigma\tau|\},
$$

or when $m$ or the computed intercept is nonfinite. State evolution uses the
epsilon of its configured dtype. These histories never affect the actual
bias, scores, or parameter updates.

The `oracle` name needs a qualification: for $\sigma\tau>0$ this stationary
intercept minimizes error when $m>0$, but maximizes it when $m<0$.
Indeed, at stationarity, with
$a=p\varphi((b+m)/(\sigma\tau))>0$,

$$
\frac{\partial^2\mathcal E}{\partial b^2}
=\frac{2ma}{(\sigma\tau)^3}.
$$

Here $\varphi$ is the standard normal density. The source does not reject
negative $m$ before computing the stationary expression. Thus these
auxiliary histories should not be interpreted as universally error-optimal
intercepts. This issue is separate from the six main comparison metrics.

## 9. Current experiment workflow and interpretation of discrepancies

The approximation notebook packages population and algorithm parameters in
`MonteCarloConfig`, then calls `run_monte_carlo_experiment(config)`.
At the version checked here, it uses

$$
\begin{gathered}
d=2000,\quad n=16000,\quad K_w=K_g=10000,\quad T=300,\\
\sigma=1,\quad p=0.2,\quad\bar\rho=0.1,\quad\bar\delta=8,\\
\eta_w=\eta_b=0.1,\quad\pi=\pi_b=5,\quad\lambda=0.1,
\quad\kappa_\pm=\pm\log4.
\end{gathered}
$$

It uses $20$ repetitions, with finite-experiment seeds $42,\ldots,61$.
For each repetition, the runner:

1. Samples a finite Gaussian signal and independent Gaussian initial weights
   with the isolated Torch seed `seed + 11`; the data generator has its own
   seed `seed + 23`. Both notebooks use $b^0=0$ and leave first-step
   pseudo-labels endogenous.
2. Samples the finite environment and design, groups labeled rows before
   unlabeled rows to preserve the established reduction order, and fits
   the finite algorithm with callbacks.
3. Constructs `MacroscopicStateEvolution` with `mc_seed=seed + 47`, the same
   population and algorithm configurations, `K=config.k`, and the joint
   sample-type-law adapter. It calls `compute_trajectory()` once.
4. Records finite and effective trajectories at the current score times,
   without substituting finite realized vectors into
   the particle system.

The initial effective parameter coordinates have the same law as the finite
coordinates; the runs do not share a sampled initial weight vector or a
sampled environment. Finite training uses the realized $\rho_n=N/n$;
state evolution uses configured $\bar\rho$. The finite sample size is
`round(data_to_dimension_ratio * d)`, whereas the effective aspect ratio is
the configured real value. These distinctions are intentional finite-size
versus limiting-population conventions.

For each method and metric, results are stored as
`results[method][metric]` with shape `(repetitions, T + 1)`;
`method` is `"self_training"` or `"effective_process"` and
`results["iterations"]` is $0,\ldots,T$.
`plot_monte_carlo_experiment` takes only those recorded results as its data
input. It computes the pointwise quartiles, median, and arithmetic mean
along axis $0$. Blue denotes finite GD, orange denotes the particle
approximation, the median is solid, the mean dotted, and the interquartile
region shaded. Plotting does not rerun simulations.

Three sources of discrepancy should be separated:

- **Finite-dimensional fluctuations:** the random finite environment,
  design, and initialization vary across repetitions at fixed $d,n$.
- **Particle approximation error:** finite $K_w,K_g$ replace expectations
  by interacting empirical averages and introduce random coefficients.
  Consequently the displayed effective trajectory is itself random.
- **Numerical error and regularization:** finite precision, basis-rank
  rejection, and least-squares rank decisions affect the numerical
  particle system independently of the original high-dimensional limit.

The interquartile regions summarize repetitions at these fixed budgets;
they are not confidence bands for an exact deterministic limiting curve.
No convergence rate in $K_w,K_g$ or uniform guarantee in $T$ is established
by the implementation or the numerical identity tests. Any consistency
argument must address threshold discontinuities, possible rank changes,
and stability of the recursive projections. Increasing the particle
budgets alone does not remove a fixed numerical-rank regularization.

## 10. Stabilization, derivative-free memory, and verification

The implemented numerical controls are CGS2 reorthogonalization, relative
basis-rank acceptance, and the chosen least-squares tolerances and driver.
The defaults are float64 on CPU. Float32 is supported by the effective
class, but the retained notebooks explicitly use float64. No covariance
jitter, eigenvalue clipping, adaptive rank tolerance, automatic SVD fallback,
or differentiation through the stochastic trajectory is implemented.

On-demand basis diagnostics are `orthogonality_error`,
`coordinate_singular_values`, and `coordinate_condition_number`.
The state-evolution histories record `weight_rank`, `residual_rank`,
`weight_rank_truncated`, `residual_rank_truncated`, and the two innovation
scales. These quantities support inspection; the recursion does not
automatically react to a large condition number or perform a sensitivity
study in `eps_rank` or `lstsq_rcond`. Such studies can assess numerical
robustness but are not a proved error certificate.

Memory is defined by inner products and least-squares projections. Although
the loss derivative $\ell_r$ and penalty derivative $j'$ are evaluated,
the implementation does not differentiate the selector or its stochastic
history to obtain response coefficients. In particular, a smooth
derivative-average representation should not be substituted for the hard
threshold without accounting for its jumps. The elementary example

$$
Z\sim\mathcal N(0,1),\qquad f(z)=\mathbf1_{\{z>a\}},\qquad
f'(z)=0\ \text{a.e.},\qquad
\mathbb E[Zf(Z)]=\int_a^\infty z\varphi(z)\,dz=\varphi(a)
$$

shows why an almost-everywhere derivative alone does not justify the
classical smooth Stein identity for this discontinuous function.
No derivative identity is needed for the projection construction in this
note; an identification with a smooth response formulation would require
its own hypotheses and argument.

The relevant existing checks are
[`test_empirical_orthogonal_basis.py`](../tests/test_empirical_orthogonal_basis.py),
[`test_orthogonal_coordinate_reference.py`](../tests/test_orthogonal_coordinate_reference.py),
and [`test_state_evolution_response.py`](../tests/test_state_evolution_response.py).
They cover basis normalization and rank handling, coordinate/Gram reference
identities with unequal populations and dependent columns, independent
streams, innovation dimensions, initialization, and terminal conventions.
The Gram pseudoinverses used in reference tests are not part of production
updates. Agreement on these fixtures verifies those identities and
conventions, not a particle-limit theorem or a long-horizon accuracy bound.
