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

`split\_tester.py` is a single function that wraps your existing model. It tests five split ratios (50/50 through 90/10) and reports the range. Drop it into any project.

```python
from split\_tester import test\_splits

results = test\_splits(my\_model, X\_train, y\_train)
# Output: train\_50\_val\_50: 0.555, train\_60\_val\_40: 0.648, ...

