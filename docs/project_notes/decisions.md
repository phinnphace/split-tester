# Architectural Decisions

## Publish the paper audit as a sibling static route with a generated data snapshot

**Date:** 2026-08-12
**Status:** Superseded 2026-08-21 by the full corpus retirement below

**Context:**
An earlier Paper Trail corpus and its public evidence interface were published at this route.

**Decision:**
This decision is retained only as a pointer to repository history. Its active implementation
and derived data were retired under the 2026-08-21 decision below.

**Consequences:**
- No former corpus detail is carried forward in this active decision log.

## Retire the active Paper Trail corpus and rebuild from a corrected master

**Date:** 2026-08-21
**Status:** Accepted

**Context:**
A reference document was mistakenly included in the initial corpus. Although it was removed
and affected analyses were rerun, later work still descended from the original master input.

**Decision:**
Purge the active corpus and every inherited local and public output. Retain only the generic
schema and review protocol. Keep the public routes active as correction/rebuild notices, and
preserve ordinary Git history rather than rewriting it. Begin again only from the corrected
master citation CSV.

**Consequences:**
- No prior paper records, node memberships, summaries, or analytical outputs remain active.
- The generated browser data and its exporter are removed.
- Earlier public versions remain inspectable in Git history.
- Every citation in the corrected master will be registered before review begins.

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
- Only `carnival_wheel.html` is version-controlled in split-tester; the wheel's source lives
  in its own home (a separate space/repo), not here.

---

## The wheel has its own home; split-tester tracks only the built HTML

**Date:** 2026-07-22 (corrected twice — it is NOT 80-20/newglasses, and its source is NOT
kept in split-tester either)
**Status:** Amended 2026-07-26 — per phinn there is no separate wheel repo/space: the
artifact of record is `carnival_wheel.html` tracked in split-tester, the deployment is
housed under 80-20 (go.dataacorns.com/80-20/carnival-wheel), and the local
`carnival-split-wheel/` Vite working copy (gitignored) is what rebuilds it.

**Context:**
The carnival wheel (a Vite/React single-file build) is embedded in the split-tester demo,
but it is its own artifact with its own home (a separate space/repo).

**Decision:**
The wheel's source lives in its OWN home — not in split-tester, and NOT in 80-20/newglasses
(that folder is a separate recharts slide deck). split-tester tracks only the built artifact
(`carnival_wheel.html`); to update it, rebuild in the wheel's home and copy the single-file
HTML in. The local `carnival-split-wheel/` folder here is a redundant working copy —
gitignored, and safe to delete.

**Consequences:**
- One source of truth (the wheel's own home); split-tester's `carnival_wheel.html` can go
  stale (see bugs.md) and is refreshed by copying a fresh build over.

---

## The calibration drop-in is `delta_split` (single "hey, use this" file at the repo root)

**Date:** 2026-07-22
**Status:** Accepted

**Context:**
`delta_split(model, X, y)` (the reusable extraction of the split-ratio loop) is a
low-friction drop-in that nudges people to CALIBRATE how much their train/val split ratio
moves internal validation. The "80/20" reflex spans many frameworks and domains. It lives
in the split-tester repo as a simple "use this" helper, not a separate distribution project.

**Decision:**
Keep it as a single self-contained module at the repo root: `delta_split.py` (numpy-only;
scikit-learn used if present, just for cleaner cloning). Naming/framing is deliberate — it's
**calibration, not results**: the function is `delta_split`, the return type is `SplitDelta`,
the extremes are `.high` / `.low` (not "best"/"worst"), and it does not crown an "optimal"
split. Design is **framework-sticky**: dead-simple sklearn-protocol call by default, with
optional `fit` / `predict` / `metric` / `model_factory` hooks so PyTorch, Keras, and
regression plug into the user's own workflow.

**Alternatives Considered:**
- Standalone `split-tester-pip/` package folder — built briefly, then rejected: overkill for
  a "use this" helper, and it left a duplicate copy. Deleted. (Accidental duplication, not
  intentional branching — the nested 80-20 → split-tester → wheel structure stays.)
- Names `test_splits` / `SplitResults` — rejected: `test_` collided with pytest collection,
  and "results"/"best" smuggled in the exact conflation the project critiques.

**Consequences:**
- Canonical file = root `delta_split.py`. One copy only.
- Tests live in `tests/test_delta_split.py` (+ `conftest.py` so `import delta_split` works).
- Cannot be run/tested from the assistant shell (WSL/UNC) — user runs it in their terminal.
