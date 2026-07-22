# Split Ratio Tester

## Where this comes from

This tool emerged from a side quest in a larger experiment on contextual visual learning. I was training small CNNs (93K parameters) to recognize the Chinese character 打 (dǎ) against five visually similar distractors, using real handwriting from the [CASIA database](http://www.nlpr.ia.ac.cn/databases/handwriting/Home.html).

While testing different train/validation splits on identical models—same architecture, same seed, same data—I noticed the standard 80/20 default was not neutral. Validation accuracy swung by over 21 percentage points depending only on where the split boundary fell.

That finding had nothing to do with Chinese characters specifically. It was about a default everyone inherits and nobody tests.

## What this demonstrates

|Split|Validation Accuracy|
|-|-|
|50/50|64.5%|
|60/40|60.2%|
|70/30|67.3%|
|80/20|73.5%|
|90/10|81.6%|

Same model. Same seed. Same data. The only variable is the train/val ratio. If I'd stopped at 60/40, I'd report 60.2%. At 90/10, I'd report 81.6%. Both numbers are "correct." Neither tells the whole story.

## Try it yourself

A 40-image sample of the actual dataset is included in `sample\_data.zip`.
Each image is a 100×100 grayscale PNG: isolated characters (Condition A)
or two-character bigrams (Condition B), labeled as 打 (positive) or a
visually similar distractor (negative).

The full dataset (489 Condition A + 298 Condition B images) is available
from the CASIA-HWDB database via HuggingFace. See the main project repo
for extraction scripts.

## The tool

`delta_split.py` is a single function you drop onto your existing model. It **calibrates**
one design choice — the train/val split ratio — by perturbing it across 50/50 → 90/10 and
reporting the *delta* in internal validation. Same model, same seed, same data; only the
split moves. The numbers it returns are preliminary diagnostics — not results, findings, or
benchmarks — and it does not pick an "optimal" split. Only dependency is `numpy`.

Anything with scikit-learn-style `.fit()` / `.predict()` works with zero config
(scikit-learn, XGBoost, LightGBM, CatBoost, ...):

```python
from delta_split import delta_split
from sklearn.ensemble import RandomForestClassifier

d = delta_split(RandomForestClassifier(), X, y)
# train_50_val_50: train=150, val=150, internal-val=0.555
# ...
# delta (spread) across splits: 0.261  [high train_90_val_10=0.816, low train_50_val_50=0.555]

d.spread   # 0.261  -> the delta; how much a single split could swing your number
d.range    # (0.555, 0.816)
d.high     # 'train_90_val_10'  (highest internal-val -- NOT "best")
d.low      # 'train_50_val_50'
dict(d)    # plain dict, JSON-serializable
```

### Technique-sticky, not framework-agnostic
Where Ml goes (an ever increasing expanse of domains, this goes with)
It sticks into *your* workflow through optional hooks — the headline call stays a one-liner:

| hook | what it is | default |
|------|------------|---------|
| `metric` | `callable(y_true, y_pred) -> float` | accuracy |
| `predict` | `callable(model, X_val) -> preds` | `model.predict` |
| `fit` | `callable(model, X_train, y_train)` (may return the fitted model) | `model.fit` |
| `model_factory` | `callable() -> a fresh model` (use instead of `model`) | clone `model` |

**Regression / custom metric**

```python
from sklearn.metrics import r2_score
from sklearn.linear_model import Ridge

d = delta_split(Ridge(), X, y, metric=r2_score)
```

**Keras** — `predict` returns probabilities, so adapt it, and hand over a factory so each
split starts from fresh weights:

```python
import numpy as np

d = delta_split(
    model_factory=build_model,
    X=X, y=y,
    fit=lambda m, xt, yt: m.fit(xt, yt, epochs=20, verbose=0),
    predict=lambda m, xv: np.argmax(m.predict(xv, verbose=0), axis=1),
)
```

**PyTorch** — wrap your own train/eval loop in the hooks:

```python
def train(model, X_tr, y_tr):
    # ... your loop; mutates model or returns a model
    return model

def infer(model, X_val):
    model.eval()
    with torch.no_grad():
        return model(to_tensor(X_val)).argmax(1).cpu().numpy()

d = delta_split(model_factory=build_net, X=X, y=y, fit=train, predict=infer)
```

**Why one fixed shuffle:** every split reuses a single shuffle drawn from `seed`; only the
cut point moves. So the split ratio is the *only* thing changing between runs — the delta
you see is attributable to the ratio, not to a different random draw.

## Tests

```bash
pip install pytest scikit-learn
pytest -q
```

