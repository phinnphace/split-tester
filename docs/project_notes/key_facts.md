# Key Facts

## The three spaces (the nesting doll)

**Value / Detail:**

1. **80-20** — `github.com/phinnphace/80-20` — the *primary* project ("final submission" on
   the desktop). The real ML final: SOP train/test split work on CASIA Chinese-character
   images. Deployed dashboard: https://80-20.streamlit.app . Contains `newglasses/` — a
   recharts slide deck (a separate artifact, NOT the carnival wheel).
2. **split-tester** — `github.com/phinnphace/split-tester` — the *side quest* spawned from
   80-20. A standalone Streamlit demo (`app.py`) that runs the same model/seed/data across
   split ratios 0.5 → 0.9 and shows how much validation accuracy swings. This mounted folder.
3. **The widget = the carnival wheel.** Its source is the `carnival-split-wheel/` working
   copy in THIS repo (a Vite/React Google AI Studio export using `vite-plugin-singlefile`);
   it builds to **one self-contained HTML file** that gets embedded. It is NOT built from
   80-20/newglasses — that's a separate recharts slide deck.
   NOTE ON NAMING: "Wheel of Splits" is only the `app.py` section header that *hosts* the
   widget — it is **not** the widget. The widget itself is the carnival wheel.

**Why it matters:** These are three git repos/spaces for what is really one line of work.
The widget is the piece that lives in two places at once, which is where the versions drift.

**Last verified:** 2026-07-22

---

## How the widget connects into split-tester

**Value / Detail:**
`app.py` (bottom, "Wheel of Splits" section) reads the file `carnival_wheel.html` from the
repo root and inlines it with `streamlit.components.v1.html(wheel_html, height=650)`.
So in split-tester, the widget = the single tracked file `carnival_wheel.html`. Update the
widget by replacing that one file with a fresh build.

Pipeline: `carnival-split-wheel/` (React source) → `npm run build` → single-file
`dist/index.html` → copy to `split-tester/carnival_wheel.html` → `app.py` inlines it.

**Why it matters:** There is exactly one seam. Sync = overwrite `carnival_wheel.html`.

**Last verified:** 2026-07-22

---

## What is tracked vs. ignored in split-tester

**Value / Detail:**
Tracked: `app.py`, `carnival_wheel.html` (the built widget), `phase10_split_comparison.py`,
`requirements.txt`, `split_window.json`, `table1_experimental_results.csv`, `sample_data.zip`.
Ignored (`.gitignore`): `node_modules/`, `dist/`, `.vite/`, `__pycache__/`, `.streamlit/`,
`data/`. The local `carnival-split-wheel/` folder (a working copy of the widget source, with
`src/` and the folder itself gitignored) is **not** part of the committed repo — only its
built output (`carnival_wheel.html`) is.

**Why it matters:** The widget *source* does not live in split-tester's history; only the
compiled asset does. Source-of-truth for edits is 80-20/newglasses.

**Last verified:** 2026-07-22

---

## Environment constraint

**Value / Detail:** This folder is a WSL/UNC path
(`\\wsl.localhost\ubuntu\...\split-tester`). The sandboxed bash shell **cannot reach it**;
only the file tools (Read/Write/Edit) can. Git and `npm run build` must be run by the user in
their own WSL terminal, not by the assistant's shell.

**Why it matters:** Any "rebuild the widget" step cannot be executed from here — it has to be
handed to the user as a command, or the built HTML brought in another way.

**Last verified:** 2026-07-22
