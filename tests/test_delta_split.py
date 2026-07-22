"""Tests for delta_split. Runnable with plain numpy + pytest (no sklearn needed).

Run from the repo root:  pytest -q
"""
import numpy as np
import pytest

# `delta_split` doesn't start with `test_`, so pytest won't try to collect it as a test.
from delta_split import delta_split, SplitDelta, DEFAULT_SPLITS


class Majority:
    """Tiny deterministic estimator: predicts the most common training label."""

    def fit(self, X, y):
        vals, counts = np.unique(y, return_counts=True)
        self.label_ = vals[int(np.argmax(counts))]
        return self

    def predict(self, X):
        return np.full(len(X), self.label_)


def make_data(n=100):
    rng = np.random.RandomState(0)
    X = rng.rand(n, 4)
    y = np.array([1] * (n * 6 // 10) + [0] * (n - n * 6 // 10))
    return X, y


def test_keys_and_order():
    X, y = make_data()
    d = delta_split(Majority(), X, y, verbose=False)
    assert list(d.keys()) == [
        "train_50_val_50",
        "train_60_val_40",
        "train_70_val_30",
        "train_80_val_20",
        "train_90_val_10",
    ]


def test_is_splitdelta_and_plain_dict():
    X, y = make_data()
    d = delta_split(Majority(), X, y, verbose=False)
    assert isinstance(d, SplitDelta)
    assert isinstance(d, dict)
    import json

    assert set(json.loads(json.dumps(d))) == set(d)


def test_values_are_fractions():
    X, y = make_data()
    d = delta_split(Majority(), X, y, verbose=False)
    assert all(0.0 <= v <= 1.0 for v in d.values())


def test_summary_readouts():
    X, y = make_data()
    d = delta_split(Majority(), X, y, verbose=False)
    lo, hi = d.range
    assert lo == min(d.values())
    assert hi == max(d.values())
    assert d.spread == pytest.approx(hi - lo)
    assert d[d.high] == hi
    assert d[d.low] == lo


def test_deterministic():
    X, y = make_data()
    a = delta_split(Majority(), X, y, verbose=False)
    b = delta_split(Majority(), X, y, verbose=False)
    assert a == b


def test_custom_metric():
    X, y = make_data()
    d = delta_split(Majority(), X, y, metric=lambda yt, yp: 0.5, verbose=False)
    assert set(d.values()) == {0.5}
    assert d.spread == 0.0


def test_model_factory_path():
    X, y = make_data()
    d = delta_split(model_factory=Majority, X=X, y=y, verbose=False)
    assert len(d) == len(DEFAULT_SPLITS)


def test_predict_hook_and_fit_returning_model():
    X, y = make_data()
    d = delta_split(
        Majority(),
        X,
        y,
        fit=lambda m, xt, yt: m.fit(xt, yt),  # returns the fitted model
        predict=lambda m, xv: m.predict(xv),
        verbose=False,
    )
    assert len(d) == len(DEFAULT_SPLITS)


def test_custom_splits():
    X, y = make_data()
    d = delta_split(Majority(), X, y, splits=(0.7, 0.8), verbose=False)
    assert list(d.keys()) == ["train_70_val_30", "train_80_val_20"]


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(model=Majority(), model_factory=Majority),  # both
        dict(),  # neither model nor factory
    ],
)
def test_bad_model_args(kwargs):
    X, y = make_data()
    kwargs.setdefault("X", X)
    kwargs.setdefault("y", y)
    with pytest.raises(ValueError):
        delta_split(**kwargs)


def test_missing_xy():
    with pytest.raises(ValueError):
        delta_split(Majority(), None, None)


def test_length_mismatch():
    X, y = make_data()
    with pytest.raises(ValueError):
        delta_split(Majority(), X, y[:-1])


def test_too_few_samples():
    X = np.zeros((3, 2))
    y = np.array([0, 1, 0])
    with pytest.raises(ValueError):
        delta_split(Majority(), X, y)


def test_bad_split_fraction():
    X, y = make_data()
    with pytest.raises(ValueError):
        delta_split(Majority(), X, y, splits=(0.5, 1.5), verbose=False)
