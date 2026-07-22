# Architectural Decisions

## Embed the wheel as a compiled single-file asset, inlined via components.html

**Date:** 2026-07-22 (recorded; decision made over prior commits)
**Status:** Accepted

**Context:**
The wheel started as a "native" Streamlit widget that was laggy. Git history shows the move
"feat: replace laggy native widget with compiled asset."

**Decision:**
Build the React wheel to a single self-contained HTML file and inline it in `app.py` with
`streamlit.components.v1.html(...)`, reading `carnival_wheel.html` from the repo root.

**Alternatives Considered:**
- Native Streamlit widgets — rejected: laggy.
- Serving the HTML as a Streamlit static file — rejected / do NOT revisit: does not fit this
  setup and has been a dead end before.

**Consequences:**
- The widget must be rebuilt and the single file re-copied whenever it changes.
- Only `carnival_wheel.html` is version-controlled in split-tester; the source lives in 80-20.

---

## Wheel source = carnival-split-wheel (a Vite/React build); repo tracks only the build

**Date:** 2026-07-22 (corrected — earlier said 80-20/newglasses, which was wrong)
**Status:** Accepted

**Context:**
The carnival wheel is embedded in the split-tester demo (and could be reused elsewhere).

**Decision:**
Wheel source = the `carnival-split-wheel/` working copy (Vite/React Google AI Studio
export) — NOT 80-20/newglasses (that folder is a separate recharts slide deck).
split-tester tracks only the built artifact (`carnival_wheel.html`); rebuild the source and
copy the single-file HTML over.

**Consequences:**
- Prevents two diverging source trees, but means split-tester's copy can go stale (see
  bugs.md: outdated widget). Syncing = copy the fresh build over.

---

## Keep split_tester as a single "hey, use this" helper in the repo root

**Date:** 2026-07-22
**Status:** Accepted

**Context:**
`test_splits(model, X, y)` (the reusable extraction of the split-ratio loop) is meant to
be a low-friction drop-in that nudges people to check how much their train/val split
ratio swings results. The "80/20" reflex spans many frameworks and domains. It already
lives in the split-tester repo and is intended as a simple "use this" helper, not a
separate distribution project.

**Decision:**
Keep it as a single self-contained module at the repo root: `split_tester.py`
(numpy-only; scikit-learn used if present, just for cleaner cloning). Design is
**framework-sticky, not agnostic**: dead-simple sklearn-protocol call by default, with
optional `fit` / `predict` / `metric` / `model_factory` hooks so PyTorch, Keras, and
regression plug into the user's own workflow.

**Alternatives Considered:**
- Standalone `split-tester-pip/` package folder (own repo, pyproject/LICENSE/tests) —
  built briefly, then rejected: overkill for a "use this" helper, and it left a duplicate
  copy of the module. That folder is redundant and can be deleted. (Note: this was
  accidental duplication, not intentional branching — the deliberately nested
  80-20 → split-tester → wheel structure is fine and stays.)

**Consequences:**
- Canonical file = root `split_tester.py`. Do not keep a second copy.
- If pip-installability is wanted later, add a minimal root `pyproject.toml` with
  `py-modules = ["split_tester"]` — no need to relocate the file.
- Cannot be run/tested from the assistant shell (WSL/UNC) — user runs it in their own
  terminal.
