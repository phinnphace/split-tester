# Bug Log

## split-tester's carnival_wheel.html is an outdated build

**Date:** 2026-07-22
**Status:** Open

**Issue:**
The `carnival_wheel.html` committed/present in split-tester is an older build of the wheel,
not the current functional widget (the newer version worked on in 80-20/newglasses).

**Root Cause:**
The wheel is built separately from its source (the `carnival-split-wheel/` Vite/React
export); split-tester only tracks the compiled `carnival_wheel.html`, so when the widget is
rebuilt the tracked copy isn't refreshed — the two drift. (Source is carnival-split-wheel,
NOT 80-20/newglasses.)

**Solution (planned):**
1. Confirm which build is authoritative (newglasses build vs. the local
   `carnival-split-wheel/` working copy vs. last night's artifact).
2. Rebuild the widget from that source (`npm run build`, single-file output).
3. Overwrite `split-tester/carnival_wheel.html` with the fresh single-file HTML.
4. Verify `app.py` still loads it (`components.html`, height 650) and commit/push.

**Prevention:**
Treat `carnival_wheel.html` as a generated artifact. When the widget changes upstream,
re-copy the build into split-tester in the same pass. Consider a short "sync" note/script.

**Constraint:** The build cannot be run from the assistant's bash shell (WSL/UNC path is
unreachable) — the user runs it in their own terminal.
