# split-tester

Side-quest repo spawned from the primary **80-20** project. A standalone Streamlit demo that
shows how the train/val split ratio (0.5 → 0.9) swings validation accuracy on CASIA
Chinese-character images. Includes the "Wheel of Splits" carnival widget.

## Big picture — the nesting doll

```
80-20  (github.com/phinnphace/80-20)  ← PRIMARY: the "final submission" ML project
│                                        deployed at 80-20.streamlit.app
│   NOTE: 80-20's `newglasses/` folder is a recharts SLIDE DECK — a DIFFERENT artifact,
│   NOT the carnival wheel (see 80-20's own CLAUDE.md).
│
split-tester  (github.com/phinnphace/split-tester)  ← THIS repo, the side quest
├── app.py                ← Streamlit demo; inlines the wheel via components.html()
├── carnival_wheel.html   ← the built carnival-wheel widget (ARTIFACT tracked here)
└── carnival-split-wheel/ ← the wheel's SOURCE working copy (Vite/React, Google AI Studio
                            export; `npm run build` → single-file HTML → carnival_wheel.html).
                            gitignored; canonical home TBD/confirm.
```

The one seam: `app.py` reads `carnival_wheel.html` and embeds it with
`streamlit.components.v1.html(wheel_html, height=650)`. To update the widget, replace that
single file with a fresh build. Do **not** try to serve the HTML as a Streamlit static file —
that path has been a dead end.

## Constraints

- This folder is a WSL/UNC path; the assistant's sandboxed shell can't reach it. Run `git`
  and `npm run build` in your own WSL terminal. The assistant edits files directly.
- `carnival_wheel.html` is a **generated** artifact — edit the wheel source
  (`carnival-split-wheel/`, a Vite/React single-file build), rebuild, then re-copy here.
  It is NOT built from 80-20/newglasses (that's a separate slide deck).

## Project Memory System

Project notes live in `docs/project_notes/` — see `key_facts.md` · `decisions.md` ·
`bugs.md` · `issues.md`.

**Before proposing architectural changes:** check `decisions.md` for existing choices.
**When hitting errors/bugs:** search `bugs.md` first; document new ones when resolved.
**When looking up config/paths/URLs:** check `key_facts.md` before assuming.
