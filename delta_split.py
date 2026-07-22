"""
delta_split -- calibrate how sensitive your reported metric is to the train/val split ratio.

Perturb one knob almost everyone treats as neutral -- the split ratio -- and measure the
delta it produces in internal validation. Same model, same seed, same data; only the split
moves.

This is a CALIBRATION / sensitivity check, not a result generator. What it returns are
internal-validation measurements at each split ratio and the spread (delta) across them.
They are preliminary diagnostics -- not results, findings, benchmarks, or external
validation -- and it deliberately does NOT crown an "optimal" split, because optimality is
contextual. The point is to stop a single split's number from being mistaken for truth.

    from delta_split import delta_split

    d = delta_split(my_model, X, y)
    # {'train_50_val_50': 0.555, 'train_60_val_40': 0.648,
    #  'train_70_val_30': 0.673, 'train_80_val_20': 0.735,
    #  'train_90_val_10': 0.816}

    d.spread   # the delta across ratios (max - min) -- the calibration signal
    d.range    # (min, max)
    d.high     # the ratio with the highest internal-val number (NOT "best")
    d.low      # the ratio with the lowest

`my_model` is anything with sklearn-style ``.fit(X, y)`` / ``.predict(X)`` (scikit-learn,
XGBoost, LightGBM, CatBoost, ...). It sticks into other stacks through optional hooks:

    fit           callable(model, X_train, y_train) -> (optionally) fitted model
    predict       callable(model, X_val) -> predictions
    metric        callable(y_true, y_pred) -> float   (default: accuracy)
    model_factory callable() -> a fresh model   (use instead of `model` when the
                  estimator can't be cloned, e.g. a PyTorch/Keras network)

Only dependency is numpy (scikit-learn is used if present, just for cleaner cloning).
"""
from __future__ import annotations

import copy

import numpy as np

try:  # only used to get a clean unfitted copy of an sklearn-style estimator
    from sklearn.base import clone as _sk_clone
except Exception:  # pragma: no cover
    _sk_clone = None

__all__ = ["delta_split", "SplitDelta", "DEFAULT_SPLITS"]
__version__ = "0.1.0"

DEFAULT_SPLITS = (0.5, 0.6, 0.7, 0.8, 0.9)


class SplitDelta(dict):
    """A plain ``{split_name: internal_val}`` dict, plus readouts of the swing.

    Iterating/serializing yields only the split entries, so it prints and
    ``json.dumps`` cleanly. The calibration summary lives on attributes:

        .range   (min, max) of the internal-validation numbers
        .spread  max - min  (the delta across split ratios -- the signal)
        .high    the split ratio sitting at the highest number  (NOT "best")
        .low     the split ratio sitting at the lowest number
    """

    @property
    def range(self) -> tuple:
        v = list(self.values())
        return (min(v), max(v))

    @property
    def spread(self) -> float:
        v = list(self.values())
        return max(v) - min(v)

    @property
    def high(self) -> str:
        return max(self, key=self.get)

    @property
    def low(self) -> str:
        return min(self, key=self.get)


def _accuracy(y_true, y_pred) -> float:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    return float((y_true == y_pred).mean())


def _fresh(model):
    """Return an unfitted copy of ``model`` with the same hyperparameters."""
    if _sk_clone is not None:
        try:
            return _sk_clone(model)
        except Exception:
            pass
    return copy.deepcopy(model)


def delta_split(
    model=None,
    X=None,
    y=None,
    *,
    model_factory=None,
    splits=DEFAULT_SPLITS,
    seed=42,
    fit=None,
    predict=None,
    metric=None,
    verbose=True,
):
    """Perturb the train/val split ratio and measure the delta in internal validation.

    A calibration / sensitivity check: it fits a fresh copy of the model at each split
    ratio (same seed, same data, only the cut point moves) and reports the internal-
    validation number at each ratio plus the spread across them. These are preliminary
    diagnostics, not results/benchmarks, and it does not identify an "optimal" split.

    Parameters
    ----------
    model : estimator with ``.fit`` / ``.predict``. A fresh copy is fitted per split
        (via ``sklearn.clone``, falling back to ``deepcopy``). Pass this OR ``model_factory``.
    X, y : array-likes of equal length.
    model_factory : callable() -> a brand-new model, called once per split. Use instead of
        ``model`` when the estimator can't be copied cleanly (e.g. a PyTorch/Keras network).
    splits : iterable of train fractions in (0, 1). Default 0.5 .. 0.9.
    seed : int. Fixes the single shuffle reused for every split, so the split ratio is the
        only thing that changes between runs.
    fit : callable(model, X_train, y_train). Defaults to ``model.fit``. May return the
        fitted model (used if not None) or mutate in place.
    predict : callable(model, X_val) -> predictions. Defaults to ``model.predict``.
    metric : callable(y_true, y_pred) -> float. Defaults to accuracy. Swap in R^2, F1, MAE,
        or anything else to make this stick to your problem.
    verbose : bool. Print a per-split line and a delta summary.

    Returns
    -------
    SplitDelta : ``{'train_50_val_50': internal_val, ...}`` plus
        ``.spread`` / ``.range`` / ``.high`` / ``.low``.
    """
    if (model is None) == (model_factory is None):
        raise ValueError("pass exactly one of `model` or `model_factory`")
    if X is None or y is None:
        raise ValueError("X and y are required")

    splits = tuple(splits)  # allow generators; we iterate more than once
    X = np.asarray(X)
    y = np.asarray(y)
    n = len(X)
    if n != len(y):
        raise ValueError(f"X and y length mismatch: {n} vs {len(y)}")
    if n < len(splits) + 1:
        raise ValueError(f"not enough samples (n={n}) for these splits")

    do_fit = fit or (lambda m, xt, yt: m.fit(xt, yt))
    do_predict = predict or (lambda m, xv: m.predict(xv))
    do_metric = metric or _accuracy

    # One fixed shuffle for ALL splits -> the split ratio is the only variable.
    order = np.random.RandomState(seed).permutation(n)

    out = SplitDelta()
    for s in splits:
        if not 0.0 < s < 1.0:
            raise ValueError(f"split fractions must be in (0, 1); got {s}")
        name = f"train_{int(round(s * 100))}_val_{int(round((1 - s) * 100))}"
        cut = int(n * s)
        train_idx, val_idx = order[:cut], order[cut:]
        if len(train_idx) == 0 or len(val_idx) == 0:
            raise ValueError(f"split {s} leaves an empty set (n={n})")

        est = model_factory() if model_factory is not None else _fresh(model)
        fitted = do_fit(est, X[train_idx], y[train_idx])
        if fitted is not None:  # support fit hooks that return a new model
            est = fitted
        preds = do_predict(est, X[val_idx])
        internal_val = float(do_metric(y[val_idx], preds))
        out[name] = internal_val

        if verbose:
            print(f"  {name}: train={len(train_idx)}, val={len(val_idx)}, internal-val={internal_val:.3f}")

    if verbose:
        lo, hi = out.range
        print(
            f"delta (spread) across splits: {out.spread:.3f}  "
            f"[high {out.high}={hi:.3f}, low {out.low}={lo:.3f}]  "
            f"-- calibration only; not a result or an 'optimal' split"
        )
    return out


if __name__ == "__main__":
    # Tiny self-check on a synthetic dataset (needs scikit-learn).
    from sklearn.datasets import make_classification
    from sklearn.ensemble import RandomForestClassifier

    Xs, ys = make_classification(n_samples=300, n_features=20, random_state=0)
    delta_split(RandomForestClassifier(n_estimators=50, random_state=42), Xs, ys)
