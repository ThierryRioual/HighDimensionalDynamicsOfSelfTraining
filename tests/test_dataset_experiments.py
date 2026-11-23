"""Scientific checks for the dataset experiment pipelines using synthetic data."""

from matplotlib import pyplot as plt
import numpy as np
import pytest
import torch

from experiments.cifar_dinov2 import (
    DINOv2CIFAR100Experiment,
    plot_dinov2_cifar100_selection,
    plot_dinov2_cifar100_trajectories,
)
from experiments.fashion_mnist import FashionMNISTExperiment, whiten_fashion_mnist_by_class
from experiments.isolet import ISOLETExperiment
from experiments.mnist import MNISTExperiment, whiten_mnist_by_class
from src.performance import population_error


@pytest.fixture
def image_data():
    rng = np.random.default_rng(7)
    labels = np.repeat([0, 1], 40)
    train = rng.normal(size=(80, 6)).astype(np.float64)
    test = rng.normal(size=(80, 6)).astype(np.float64)
    return train, labels, test, labels.copy()


def settings():
    return dict(class_proportions=[0.5, 0.25], labeling_rate=0.25,
                n_train=32, n_test=16, seeds=[42], training_steps=2,
                eta=0.05, reg_lambda=0.1, pi=2.0, tau=0.8)


@pytest.fixture(params=['mnist', 'fashion', 'isolet'])
def dataset_experiment(request, image_data, tmp_path):
    cfg = settings()
    if request.param == 'mnist':
        exp = MNISTExperiment(tmp_path, image_data, negative_digit=0, positive_digit=1,
                              sample_particles=64, particle_seed=47, **cfg)
        split = exp.mnist_split
    elif request.param == 'fashion':
        exp = FashionMNISTExperiment(tmp_path, image_data, negative_label=0, positive_label=1,
                                     sample_particles=64, particle_seed=47, **cfg)
        split = exp.fashion_mnist_split
    else:
        exp = ISOLETExperiment(tmp_path, negative_letter='A', positive_letter='B', **cfg)
        exp.X_train, exp.y_train, exp.X_test, exp.y_test = image_data
        exp.codes = (0, 1)
        exp.test_ids = np.arange(len(exp.y_test))
        split = exp.isolet_split
    return request.param, exp, split


@pytest.mark.parametrize('proportion', [0.5, 0.25])
def test_sample_split_and_revealed_labels(dataset_experiment, proportion):
    name, exp, split = dataset_experiment
    data = split(proportion, 42, (32, 16))
    if name == 'fashion':
        train_ids = np.array([np.flatnonzero(np.all(exp.X_train == row, axis=1))[0] for row in data['X_train'].numpy()])
        test_ids = np.array([np.flatnonzero(np.all(exp.X_test == row, axis=1))[0] for row in data['X_test'].numpy()]) + len(exp.y_train)
    else:
        train_ids, test_ids = data['ids']
    assert len(np.unique(train_ids)) == 32
    assert len(np.unique(test_ids)) == 16
    assert train_ids.max() < len(exp.y_train) <= test_ids.min()
    truth = np.where(exp.y_train[train_ids] == 1, 1, -1)
    observed = data['observed'].numpy()
    revealed = observed != 0
    assert revealed.sum() == 8
    np.testing.assert_array_equal(observed[revealed], truth[revealed])
    np.testing.assert_array_equal(data['hidden'].numpy(), truth[~revealed])
    assert (truth == 1).sum() == round(32 * proportion)
    if name != 'fashion':
        torch.testing.assert_close(data['X_train'].mean(0), torch.zeros(6, dtype=torch.float64), atol=1e-12, rtol=0)
    repeat = split(proportion, 42, (32, 16))
    torch.testing.assert_close(data['X_train'], repeat['X_train'])


@pytest.mark.parametrize('whiten', [whiten_mnist_by_class, whiten_fashion_mnist_by_class])
def test_class_whitening_preserves_pooled_means_and_expected_covariance(whiten):
    generator = torch.Generator().manual_seed(3)
    train = torch.randn(24, 4, generator=generator, dtype=torch.float64)
    labels = torch.tensor([-1] * 12 + [1] * 12)
    test = torch.randn(8, 4, generator=generator, dtype=torch.float64)
    test_labels = torch.tensor([-1] * 4 + [1] * 4)
    pooled = torch.diag(torch.tensor([1.0, 0.8, 1.2, 0.7], dtype=torch.float64))
    ridge = 0.1
    transformed, transformed_test, stats = whiten(
        {'X_train': train, 'X_test': test, 'y_test': test_labels}, labels, pooled, ridge,
    )
    for label in (-1, 1):
        group = train[labels == label]
        mean = group.mean(0)
        residual = group - mean
        covariance = residual.T @ residual / (len(group) - 1)
        eigenvalues, vectors = torch.linalg.eigh(covariance)
        whitening = (vectors * (eigenvalues.clamp_min(0) + ridge).rsqrt()) @ vectors.T
        expected_train = residual @ whitening + mean @ pooled
        expected_test = (test[test_labels == label] - mean) @ whitening + mean @ pooled
        torch.testing.assert_close(transformed[labels == label], expected_train)
        torch.testing.assert_close(transformed_test[test_labels == label], expected_test)
    assert all(np.isfinite(value) for value in stats.values())


def test_cifar_sampling_and_revelation():
    exp = DINOv2CIFAR100Experiment(
        object(), **settings(), checkpoint_times=[0, 1, 2],
        negative_superclasses=(0, 1), positive_superclasses=(2,), pilot_holdout_per_class=2,
        pilot_seed=2026, whitening_ridge_fraction=0.01,
        sample_particles=64, particle_seed=47,
    )
    exp.coarse_names = {0: 'a', 1: 'b', 2: 'c'}
    ids = np.arange(90)
    coarse = np.repeat([0, 1, 2], 30)
    pool = (np.arange(90 * 6).reshape(90, 6), coarse, ids)
    rng = np.random.default_rng(42)
    _, labels, chosen = exp.sample_binary(pool, ((0, 1), (2,)), 32, 0.25, rng)
    assert len(np.unique(chosen)) == 32
    np.testing.assert_array_equal(labels.numpy(), np.where(coarse[chosen] == 2, 1, -1))
    observed = exp.reveal_labels(labels, rng)
    assert (observed != 0).sum() == 8
    assert torch.equal(observed[observed != 0], labels[observed != 0])


def test_seeded_gaussian_trajectories(dataset_experiment):
    name, exp, _ = dataset_experiment
    if name == 'isolet':
        result = exp.run_isolet_repetition(.5, 42, (32, 16), 2)
        for row in result['trajectories']['self_training']:
            assert row['test_error'] == pytest.approx(.5 * (row['negative_error'] + row['positive_error']))
    else:
        runner = exp.compare_mnist_gaussian if name == 'mnist' else exp.compare_fashion_mnist_gaussian
        result = runner(.5, 42, 2)
        replay = runner(.5, 42, 2)
        assert result['trajectories'] == replay['trajectories']
        effective = result['trajectories']['effective_process']
        for row in effective:
            assert row['test_error'] == pytest.approx(population_error(
                row['intercept'], row['test_score_gap'], row['weight_norm'], result['sigma'], .5))
    for rows in result['trajectories'].values():
        assert [row['iteration'] for row in rows] == [0, 1, 2]
        for row in rows:
            assert 0 <= row['selected_error_fraction'] <= row['coverage'] <= 1


def test_shared_initialization_and_supervised_update(dataset_experiment, monkeypatch):
    name, exp, _ = dataset_experiment
    if name == 'fashion':
        pytest.skip('The Fashion comparison uses its own fitted-Gaussian initialization path.')
    method_name = 'fit_mnist' if name == 'mnist' else 'fit_isolet'
    original = getattr(exp, method_name)
    learners = []

    def capture(*args, **kwargs):
        learner = original(*args, **kwargs)
        learners.append(learner)
        return learner

    monkeypatch.setattr(exp, method_name, capture)
    runner = exp.run_mnist_repetition if name == 'mnist' else exp.run_isolet_repetition
    result = runner(.5, 42, (32, 16), 2)
    supervised, trained = learners
    torch.testing.assert_close(supervised.weight_history_[0], trained.weight_history_[0], rtol=0, atol=0)
    assert supervised.initialization_.b_init.item() == trained.initialization_.b_init.item() == 0
    assert torch.equal(supervised.y_observed_, trained.y_observed_)
    unlabeled = supervised.y_observed_ == 0
    assert all(torch.all(step.g[unlabeled] == 0) for step in supervised.update_records_)
    for key, value in result['trajectories']['supervised_only'][0].items():
        other = result['trajectories']['self_training'][0][key]
        assert value == other or (np.isnan(value) and np.isnan(other))


def test_mnist_plot_uses_recorded_trajectories(dataset_experiment):
    from matplotlib import pyplot as plt

    name, exp, _ = dataset_experiment
    if name != 'mnist':
        pytest.skip('This plot belongs to the MNIST experiment.')
    run = exp.run_mnist_repetition(.5, 42, (32, 16), 2)
    fig = exp.plot_mnist_trajectories([run])
    for line, method in zip(fig.axes[0].lines, ('supervised_only', 'self_training', 'finite_gaussian')):
        np.testing.assert_array_equal(line.get_ydata(), [row['test_error'] for row in run['trajectories'][method]])
    plt.close(fig)


def test_cifar_gaussian_comparison_on_synthetic_embeddings():
    cfg = settings()
    exp = DINOv2CIFAR100Experiment(
        object(), **cfg, checkpoint_times=[0, 1, 2],
        negative_superclasses=(0,), positive_superclasses=(1,), pilot_holdout_per_class=2,
        pilot_seed=2026, whitening_ridge_fraction=.01,
        sample_particles=64, particle_seed=47,
    )
    rng = np.random.default_rng(7)
    features = rng.normal(size=(100, 768)).astype(np.float32)
    coarse = np.repeat([0, 1], 50)
    ids = np.arange(100)
    exp.available_train = (features, coarse, ids)
    exp.test_pool = (features.copy(), coarse.copy(), ids + 100)
    exp.chosen_pair = ((0,), (1,))
    exp.pilot_ids = np.array([], dtype=np.int64)
    exp.coarse_names = {0: 'negative', 1: 'positive'}
    run = exp.compare_dinov2_cifar100(.5, 42, 2, checkpoints=[0, 2])
    assert run['class_counts'] == (16, 16)
    assert run['revealed_counts'] == (4, 4)
    snapshots = run["distribution_snapshots"]
    assert set(snapshots["real"]) == {0, 2}
    for t in (0, 2):
        assert snapshots["real"][t]["scores"].shape == (exp.n_train,)
        assert snapshots["effective"][t]["scores"].shape == (exp.sample_particles,)
    for rows in run['trajectories'].values():
        assert [row['iteration'] for row in rows] == [0, 1, 2]
        assert all(0 <= row['selected_error_fraction'] <= row['coverage'] <= 1 for row in rows)
        assert all(0 <= row['cifar_selected_error_fraction'] <= row['cifar_coverage'] <= 1 for row in rows)
    for row in run['trajectories']['effective_process']:
        assert row['test_error'] == pytest.approx(row['gaussian_population_error'])

    methods = ("real_self_training", "finite_gaussian", "effective_process")
    assert set(run["trajectories"]) == set(methods)
    # Reconstruct the sampled CIFAR rows and score the recorded heads in
    # whitened coordinates, using the intercept plotted for each head.
    rng = np.random.default_rng(42)
    X, labels, _ = exp.sample_binary(exp.available_train, exp.chosen_pair, exp.n_train, .5, rng)
    X_test, y_test, _ = exp.sample_binary(exp.test_pool, exp.chosen_pair, exp.n_test, .5, rng)
    hidden = exp.reveal_labels(labels, rng).numpy() == 0
    X, _, _ = exp.whiten_embeddings_by_class(X, labels, X_test, y_test)
    for method, snapshot_key in zip(methods, ("real", "finite_gaussian", "effective")):
        for t in (0, 2):
            row = run["trajectories"][method][t]
            snapshot = snapshots[snapshot_key][t]
            scores = (X.numpy() * snapshot["weights"]).sum(axis=1)
            scores = scores / np.sqrt(run["d"]) + row["intercept"]
            score_key = "scores" if snapshot_key == "real" else "cifar_scores"
            np.testing.assert_allclose(snapshot[score_key], scores, atol=1e-12)
            scores = scores[hidden]
            selected = np.abs(scores) >= np.log(exp.tau / (1 - exp.tau))
            wrong = np.where(scores >= 0, 1, -1) != labels.numpy()[hidden]
            assert row["cifar_coverage"] == selected.mean()
            assert row["cifar_selected_error_fraction"] == (selected & wrong).mean()

    fig = plot_dinov2_cifar100_trajectories([run])
    try:
        assert len(fig.axes) == 6
        assert fig.axes[0].get_title() == r"Test error $\mathcal{E}^t$"
        assert fig.axes[4].get_title() == r"Signal alignment $m^t$"
        fields = ("real_test_error", "cifar_coverage", "cifar_selected_error_fraction",
                  "intercept", "signal_alignment", "weight_norm")
        for ax, field in zip(fig.axes, fields):
            assert len(ax.lines) == 6 and len(ax.collections) == 3
            assert ax.get_xlabel() == r"Iteration $t$"
            for i, method in enumerate(methods):
                expected = [row[field] for row in run["trajectories"][method]]
                np.testing.assert_array_equal(ax.lines[2 * i].get_ydata(), expected)
                assert ax.lines[2 * i + 1].get_linestyle() == ":"
    finally:
        plt.close(fig)

    fig = plot_dinov2_cifar100_selection([run])
    try:
        assert len(fig.axes) == 3
        fields = (
            ("real_test_error", "gaussian_population_error"),
            ("cifar_coverage", "coverage"),
            ("cifar_selected_error_fraction", "selected_error_fraction"),
        )
        for ax, (cifar_field, native_field) in zip(fig.axes, fields):
            assert len(ax.lines) == 5 and len(ax.collections) == 2
            np.testing.assert_array_equal(ax.lines[-1].get_ydata(), [0, 0])
            baseline = run["trajectories"]["real_self_training"]
            for i, (method, color) in enumerate(zip(methods[1:], ("tab:green", "tab:orange"))):
                rows = run["trajectories"][method]
                for line, field, style in zip(
                    ax.lines[2 * i:2 * i + 2], (native_field, native_field), ("-", ":"),
                ):
                    differences = [row[field] - real[cifar_field] for row, real in zip(rows, baseline)]
                    np.testing.assert_array_equal(line.get_ydata(), differences)
                    assert line.get_color() == color
                    assert line.get_linestyle() == style
    finally:
        plt.close(fig)
