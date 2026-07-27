# Work Log

## Sort the nested project into separate spaces and connect them properly

**Date opened:** 2026-07-22
**Status:** In Progress

**Description:**
Untangle the "nesting doll": primary project 80-20, side-quest repo
split-tester, and the carnival-wheel widget (newglasses). Establish a clear big-picture map
and make sure the pieces connect (the widget flows correctly into split-tester).

**Notes:**
- 2026-07-22: Mapped the architecture and set up project memory (docs/project_notes/ +
  CLAUDE.md). Confirmed the single seam: `carnival_wheel.html` inlined by `app.py`.
- Open question for the user: which widget build is authoritative before we sync split-tester?
- Blocker: assistant bash cannot reach this WSL folder, so builds/git are run by the user.

---

## Cross the T's on split-tester presentation (public-facing)

**Date opened:** 2026-07-26
**Status:** In Progress

**Description:**
split-tester is the side quest beyond the coursework scope — it's for the world, not a
grader. More eyes are expected, so results must be visible in the README, not just
derivable from code. Recently added provenance artifacts:
`phase10_split_comparison.py`, `split_window.json`, `table1_experimental_results.csv`,
`sample_data.zip`. The trained models live one layer up, in 80-20 (this repo links to it).

**Notes:**
- 2026-07-26: Reviewed the additions. Fixed JSON label truncation + script output path
  (see bugs.md); added README "Where the numbers live" provenance section explaining why
  table1 CSV Condition-A numbers differ from the README table (different shuffle draw —
  which is the repo's own point); fixed `sample\_data.zip` typo; linked 80-20 repo;
  folded in remote-only README edits (see bugs.md — user must pull/merge before push).
- Documented (not changed): phase10's shuffle uses unseeded `secrets.SystemRandom()` —
  fixed within a run, not reproducible across runs. Comment added in-script; user decides
  whether future runs should seed it.
- Remaining, user-side: (1) merge+push per bugs.md; (2) 80-20's README links only the
  dashboard tinyurl — add a line linking github.com/phinnphace/split-tester; (3) planned
  updated app with results surfaced (user building); (4) stale carnival_wheel.html
  (existing open bug).
- 2026-07-26 corrections from phinn (assistant had over-inferred): audience is the public,
  not a grader; all GitHub edits are phinn's own; the wheel of record is the tracked
  `carnival_wheel.html`, deployed under 80-20 at go.dataacorns.com/80-20/carnival-wheel.
  DECREE: do not reference "the final" anywhere — it is not on git (only component parts
  are); mentioning it only causes confusion. Scrubbed from README/notes/CLAUDE.md same day.
- 2026-07-26: phinn uploaded `phase10_callibench_transfer.py` (the shipped CalliBench
  transfer test — tests trained models on 19 calligraphy 打 crops). ON STANDBY per phinn —
  no integration yet. Related: callireader wouldn't run; he'll take another stab later,
  not now. Wheel live-link added to README "Try it yourself".
