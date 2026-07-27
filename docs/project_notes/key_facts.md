# Key Facts

## The three spaces (the nesting doll)

**Value / Detail:**

1. **80-20** — `github.com/phinnphace/80-20` — the *primary* project: train/test split work
   on CASIA Chinese-character images. Deployed dashboard: https://80-20.streamlit.app .
   Contains `newglasses/` — a recharts slide deck (a separate artifact, NOT the carnival
   wheel). NOTE (phinn's decree, 2026-07-26): do not reference "the final" anywhere — it is
   not on git (only component parts are) and mentioning it only causes confusion.
2. **split-tester** — `github.com/phinnphace/split-tester` — the *side quest* spawned from
   80-20. A standalone Streamlit demo (`app.py`) that runs the same model/seed/data across
   split ratios 0.5 → 0.9 and shows how much validation accuracy swings. This mounted folder.
3. **The carnival wheel** — a widget housed under 80-20: deployed at
   go.dataacorns.com/80-20/carnival-wheel. The artifact of record is the built single-file
   `carnival_wheel.html` tracked in split-tester (per phinn, 2026-07-26 — supersedes the
   earlier "own separate space/repo" note). The local `carnival-split-wheel/` Vite/React
   working copy (`vite-plugin-singlefile`, gitignored) is what rebuilds it. It is NOT
   80-20/newglasses (a separate recharts slide deck). NOTE ON NAMING: "Wheel of Splits" is
   only the `app.py` section header that *hosts* the widget — not the widget itself.

**Why it matters:** One line of work across two repos plus a deployment. The widget lives
in two places at once (split-tester's tracked HTML + the 80-20 deployment), which is where
versions drift.

**Last verified:** 2026-07-26

---

## How the widget connects into split-tester

**Value / Detail:**
`app.py` (bottom, "Wheel of Splits" section) reads the file `carnival_wheel.html` from the
repo root and inlines it with `streamlit.components.v1.html(wheel_html, height=650)`.
So in split-tester, the widget = the single tracked file `carnival_wheel.html`. Update the
widget by replacing that one file with a fresh build.

Pipeline: `carnival-split-wheel/` working copy → `npm run build` → single-file HTML →
copy to `split-tester/carnival_wheel.html` (the artifact of record) → `app.py` inlines it.

**Why it matters:** There is exactly one seam. Sync = overwrite `carnival_wheel.html`.

**Last verified:** 2026-07-22

---

## What is tracked vs. ignored in split-tester

**Value / Detail:**
Tracked: `app.py`, `delta_split.py` (+ `tests/`, `conftest.py`), `carnival_wheel.html` (the
built widget), `phase10_split_comparison.py`, `requirements.txt`, `split_window.json`,
`table1_experimental_results.csv` (real experimental results — keep tracked), `sample_data.zip`,
`README.md`, `CLAUDE.md`, `docs/`.
Ignored (`.gitignore`): `node_modules/`, `dist/`, `.vite/`, `__pycache__/`, `.streamlit/`,
`data/`, `*:Zone.Identifier` (Windows junk), and `carnival-split-wheel/` + `.zip` (the wheel
source working copy — redundant here since the wheel has its own home).

**Why it matters:** The wheel *source* does not live in split-tester; only the compiled
`carnival_wheel.html` does. Source-of-truth for wheel edits is the wheel's own home (NOT
80-20/newglasses, NOT here).

**Last verified:** 2026-07-22

---

## The delta_split calibration tool

**Value / Detail:** `delta_split.py` (repo root) is a numpy-only drop-in:
`delta_split(model, X, y)` perturbs the train/val split ratio (0.5 → 0.9) and returns a
`SplitDelta` (`.spread` / `.range` / `.high` / `.low`) — the *delta* in internal validation.
Framework-sticky via `fit` / `predict` / `metric` / `model_factory` hooks. Framed as
**calibration** (preliminary diagnostics), not results/benchmarks, and it does not name an
"optimal" split. Tests: `tests/test_delta_split.py` (+ `conftest.py`). Renamed from
`test_splits` / `SplitResults` (the `test_` prefix collided with pytest; "results"/"best"
carried the wrong framing).

**Last verified:** 2026-07-22

---

## Result artifacts and their provenance

**Value / Detail:**

- `split_window.json` (root) — verbatim output of the Phase 10 run; the source of the
  README's headline table (64.5 / 60.2 / 67.3 / 73.5 / 81.6). Keys corrected to
  `..._val_20` / `..._val_10` on 2026-07-26 (label-only fix).
- `phase10_split_comparison.py` — the PyTorch script that produced it. Seed 42 covers
  model init/training; the shuffle is drawn per run (unseeded `SystemRandom`) and held
  fixed across the five splits. Needs `data/isolated/…` (gitignored) to actually run.
- `table1_experimental_results.csv` — Table 1 of the 80-20 experimental results; separate run
  (different shuffle), includes Condition B + CASIA/CalliBench transfer. Its Condition-A
  numbers legitimately differ from split_window.json — README now explains this.
- `sample_data.zip` — 40-image CASIA sample; what `app.py` actually trains on.

**Why it matters:** Three overlapping result sets exist; without this map a public reader
sees "contradictory" numbers. (This repo is for the world — beyond the coursework scope.)

**Last verified:** 2026-07-26

---

## CalliReader locations (parked)

**Value / Detail:** The downloaded CalliReader project lives at `~/CalliReader` (WSL home,
i.e. `\\wsl.localhost\Ubuntu\home\pmark\CalliReader`); related attempts (or lack thereof)
sit under `~/character_context_project`. phinn couldn't get it to run; parked for a later
stab — not now. Neither path is reachable from this session (UNC mount rejection).
phinn's chosen route (2026-07-26): full transparency — a session with broad folder access
rather than copying bits around. NOTE: `CalliReader` sits in `~/pmark` HOME, as a SIBLING of
`character_context_project` — mounting the latter alone does not include it.

**Why it matters:** CalliBench transfer work (`phase10_callibench_transfer.py`, on standby)
eventually connects to this.

**Last verified:** 2026-07-26

---

## Environment constraint

**Value / Detail:** This folder is a WSL/UNC path
(`\\wsl.localhost\ubuntu\...\split-tester`). The sandboxed bash shell **cannot reach it**;
only the file tools (Read/Write/Edit) can. Git and `npm run build` must be run by the user in
their own WSL terminal, not by the assistant's shell.

**Why it matters:** Any "rebuild the widget" step cannot be executed from here — it has to be
handed to the user as a command, or the built HTML brought in another way.

**Last verified:** 2026-07-22
