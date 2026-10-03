# STATE

> Rewritten at the end of every work block. Written for someone returning after **three weeks**.

**Last updated:** 2026-10-03
**Current milestone:** M2 — Watch blues learn to eat (status: review)
**Current spec:** `docs/specs/002-m2-watch-blues.md` (built; evidence in its "Result" section)
**Branch:** `feat/m2-watch-blues` (pushed, PR open)

## HUMAN TASK 2 — watch the blues learn (5 min)
1. In a normal terminal (not Claude Code), go to the project folder:
   `cd ~/Personal\ projects/RLEcosystem`
2. Type `.venv/bin/python -m rlecosystem` and press Enter. The browser opens by itself; if not,
   open `http://127.0.0.1:8000/` in it.
3. Watch for about 1 minute: blues wander, the top line says around 10 food/min per blue.
4. Click **Speed: watch** once (it becomes "fast-forward"). Wait 2–3 minutes.
5. Click it again to go back to watch. Click **Vision: off** to see the 16 slices; coloured slices
   are the ones that see something.
6. Stop the server in the terminal with Ctrl+C.
- **Pass:** the blues visibly head for food more than at the start, and the food/min number went
  up (in Claude's headless run: 12 → about 50).
- **Fail:** anything else, or the page shows "disconnected". Tell Claude what you saw.
- **What Claude does with it:** pass → you merge the PR, M2 is done. Fail → bug fix with a failing
  test first.

## Where we are
M2 is built: one command opens a live browser view of 5 blues learning to eat with one shared
brain, plus 15 hidden worlds training the same brain. Code in `src/rlecosystem/`:
- `world.py`: the vectorised world (wheels, wrap-around, 16-slice vision, food respawn, rewards).
- `ppo.py`: the in-house PPO brain (policy + value nets, GAE, update).
- `trainer.py`: 16 worlds × 5 blues → one brain; `snapshot()` of world 0 for the browser;
  `evaluate()` for fixed-seed scores.
- `server.py`: FastAPI; the simulation thread (watch = 30 steps/s, fast = as fast as possible),
  `GET /` and `WS /ws`.
- `__main__.py`: the start command. `static/`: the canvas page (plain JS).
Tests: `test_world.py` (physics, vision, eating), `test_ppo.py`, `test_learning.py` (tiny world,
trained ≥ 2× random, ~25 s), `test_server.py` (real uvicorn + websockets client). DoD ~40 s.

## Next step
1. The PO does HUMAN TASK 2, then merges the PR (squash).
2. M3 (live controls, charts, save / load): plan mode → spec 003.

## Why the current approach
- Hidden worlds: with only the 5 visible blues learning, watch speed would need ~75 min before they
  look good; with 16 worlds it takes a few minutes (PO decision).
- The simulation runs in its own thread and publishes a ready-made JSON frame under a lock; the
  WebSocket just sends the latest one ~30×/s. The trainer is only touched by that one thread.
- CI reads `.claude/dod-commands` instead of repeating the commands, so the Stop hook and CI can't
  drift apart. Ruff only looks at `src tests`.

## In progress / committed but unfinished
- Nothing besides the open M2 PR.

## Blocked on the human
- HUMAN TASK 2, then merge the M2 PR.

## Decisions made since last review
- M2 (PO, 2026-10-03): added `websockets==17.2`; 15 hidden worlds train the shared brain.
- World fixed at 1600×900, scaled to fit the window (letterboxed). Server only on 127.0.0.1:8000.
- PPO also uses gradient clipping 0.5 and value-loss weight 0.5 (standard values).
- Watch mode skips, instead of catching up, the steps lost to a PPO update: ~28–31 steps/s.
- Learning test settings: 400×300, 10 food, 8 worlds × 2 blues, 64-step rollouts, 40 updates,
  bar ≥ 2× the best of three baselines (seeds 0/1/2 gave 3.6–4.1×).
- Still from M0: vision 150 px, vmax 150 px/s, ≤ 1 turn/s, dt 1/30 s, PPO MLP 80→64→64 tanh,
  log_std −0.5, γ 0.99, λ 0.95, clip 0.2, lr 3e-4, 4 epochs × 4 minibatches, entropy 0.001,
  128-step rollouts, 4 torch threads.

## Tried and rejected — don't retry
- "Drive at the nearest food" as an efficiency ceiling with several blues: they all chase the same
  food (89.7/min alone, 26.4 with 5 blues). The M3 efficiency chart needs a per-blue definition
  that doesn't assume blues compete with nobody.
- `ruff ... .` on the whole repo inside Claude's sandbox fails with "Permission denied" on masked
  `.claude/` files. Use `src tests`.

## Known debt
- Each PPO update (~0.3 s) runs in the simulation thread, so the picture may pause briefly every
  ~4 s at watch speed. Fix in M3 if it bothers the PO.
- Food sitting on an edge is drawn cut in half (blues are drawn wrapped, food isn't). Cosmetic.
- Learning wobbled at 10 min in M0 (eval 60 → 46 → 61). Consider learning-rate decay if the live
  view shows blues getting worse for a while.
- `gh` inside Claude's sandbox isn't logged in (anonymous limit 60 API calls/hour, can't read CI
  logs). `git push` works. Run `gh run view` sparingly.
- The repo root has untracked empty dotfiles (`.bashrc`, `.idea`, `.mcp.json`, …) created by
  Claude's sandbox. Not ours; never commit them.
- Python in `.venv` is 3.14.7 (PRODUCT says 3.12+; fine).
