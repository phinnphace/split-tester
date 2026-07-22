# Work Log

## Sort the nested project into separate spaces and connect them properly

**Date opened:** 2026-07-22
**Status:** In Progress

**Description:**
Untangle the "nesting doll": primary project 80-20 (final submission), side-quest repo
split-tester, and the carnival-wheel widget (newglasses). Establish a clear big-picture map
and make sure the pieces connect (the widget flows correctly into split-tester).

**Notes:**
- 2026-07-22: Mapped the architecture and set up project memory (docs/project_notes/ +
  CLAUDE.md). Confirmed the single seam: `carnival_wheel.html` inlined by `app.py`.
- Open question for the user: which widget build is authoritative before we sync split-tester?
- Blocker: assistant bash cannot reach this WSL folder, so builds/git are run by the user.
