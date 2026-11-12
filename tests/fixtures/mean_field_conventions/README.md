# Effective-process numerical reference fixtures

`reference.pt` contains fixed tensor trajectories in manuscript units:
`g` is the frozen score gradient, and parameter updates apply the configured
descent rates. The fixture covers four weight rates (`.03`, `.3`, `1`, `2`)
and three configurations: supervised learning, active self-training, and
self-training with rank truncation and separate intercept controls.

`metadata.json` specifies the configurations, recorded histories, particle
counts, seed, dtype, and least-squares driver. Each trajectory uses five updates
and a terminal evaluation with `K_w=53`, `K_g=71`, and seed 123. The setup is
specified by `make_process` in `tests/test_mean_field_conventions.py`.

`experiment_metrics.npz` contains the finite and effective metrics used by the
experiment-runner reference test at weight rates `.1`, `.2`, and `.7`, with
two seeds, eight updates, dimension 128, and 512 particles.

The pytest suite checks trajectories, rank and truncation decisions, response
coefficients, Gaussian processes, gradient identities, and parameter updates.
Reference data are fixed test inputs; running the tests does not rewrite them.
