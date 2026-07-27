# Bug Log

## split-tester's carnival_wheel.html is an outdated build

**Date:** 2026-07-22
**Status:** Resolved 2026-07-26 — copied the working-copy build to repo root; phinn confirmed the wheel loads and spins in the app
**Update 2026-07-26 (phinn):** the tracked `carnival_wheel.html` in split-tester is the
wheel of record; the widget is deployed under 80-20 at
go.dataacorns.com/80-20/carnival-wheel. Phinn changed the widget in the Streamlit app and
it hasn't worked since — restoring a working build into the tracked file is the open work.

**Issue:**
The `carnival_wheel.html` committed/present in split-tester is an older build of the wheel,
not the current functional widget (the newer version worked on in 80-20/newglasses).

**Root Cause:**
The wheel is built separately from its source (the `carnival-split-wheel/` Vite/React
export); split-tester only tracks the compiled `carnival_wheel.html`, so when the widget is
rebuilt the tracked copy isn't refreshed — the two drift. (Source is carnival-split-wheel,
NOT 80-20/newglasses.)

**Update 2026-07-26 (diagnosed):** the root-level `carnival_wheel.html` is not merely
outdated — it is **absent from the repo root entirely**. The only copy on disk is
`carnival-split-wheel/carnival_wheel.html` (inside the gitignored working folder), which
carries the canonical accuracies (64.5/60.2/67.3/73.5/81.6). app.py's fallback error
("carnival_wheel.html not found next to app.py") is exactly what the broken widget was.

**Solution:**
1. `cp carnival-split-wheel/carnival_wheel.html carnival_wheel.html` (repo root).
2. Verify `app.py` loads it (`components.html`, height 650), run app, commit/push.

**Prevention:**
Treat `carnival_wheel.html` as a generated artifact. When the widget changes upstream,
re-copy the build into split-tester in the same pass. Consider a short "sync" note/script.

**Constraint:** The build cannot be run from the assistant's bash shell (WSL/UNC path is
unreachable) — the user runs it in their own terminal.

---

## split_window.json keys mislabeled "val_19" / "val_9" (float truncation)

**Date:** 2026-07-26
**Status:** Resolved

**Issue:**
Published artifact `split_window.json` had keys `train_80_val_19` and `train_90_val_9`.

**Root Cause:**
`phase10_split_comparison.py` built labels with `int((1-split)*100)`; `1-0.8` is
`0.19999…` so `int()` truncates to 19 (and 0.9 → 9).

**Solution:**
Changed the script to `round(...)`; renamed the two JSON keys to `train_80_val_20` /
`train_90_val_10` (label-only fix — sizes and accuracies untouched).

**Prevention:**
Use `round()` (never `int()`) when formatting percentages from floats.

---

## phase10 script wrote to models/ which doesn't exist in this repo

**Date:** 2026-07-26
**Status:** Resolved

**Issue:**
Script ends with `open('models/split_window.json', 'w')` — crashes with
FileNotFoundError here, where there is no `models/` dir (the tracked copy sits at root).

**Solution:**
Added `os.makedirs('models', exist_ok=True)` before the write.

**Prevention:**
Provenance scripts copied in from another repo should have their paths checked against
this repo's layout.

---

## Local README diverged from GitHub README

**Date:** 2026-07-26
**Status:** Open (needs a pull/merge by the user)

**Issue:**
The pushed README (github.com/phinnphace/split-tester) contains edits the local copy
lacked: heading "Technique-sticky, not framework-agnostic" plus an unfinished sentence
("Where Ml goes (an ever increasing expanse of domains, this goes with)"). These are
phinn's own edits made on GitHub directly, so local main is behind remote.

**Solution (in progress):**
Local README now folds in those edits (heading adopted; sentence polished) plus new
provenance section/typo/link fixes — local is the superset. User must merge before
pushing: `git add -A && git commit`, then `git pull --no-rebase -X ours`, then push.
(`-X ours` keeps the local side on conflicting hunks — safe because local README already
contains the remote edit. Skim `git log origin/main` first for any other web-only commits.)

**Prevention:**
After editing on GitHub directly, pull before the next local session touches the file.
