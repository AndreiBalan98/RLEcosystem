# ROADMAP

Status: `todo` → `spec` → `building` → `review` → `done`, plus `cancelled` (decided against; say
why and where the finding is recorded). One milestone in progress at a time.
Direction changes are edits to this file in a `docs:` commit — never decided in chat only.

## M0 — Can wheeled blues learn to eat fast enough? · status: done
**Outcome:** a throwaway headless script (no graphics): wrap-around plane, 50 food, a few blues with
two-wheel steering and 16-slice vision, one shared PPO brain. Trains up to 20 minutes on the PO's CPU
and prints food eaten per minute: random vs trained, fixed seed. Delete the probe afterwards.
**Result (2026-10-03, Intel i7-1255U, 4 torch threads):** on a fixed seed (1600×900, 50 food, 5 blues,
vision 150 px), trained blues ate **58.9 food/min each after 20 min** vs **5.3** for the best random
baseline (**11.2×**), and were already at 48.0 (9×) after 1 min, so the assumption holds and the plan is unchanged.
**Definition of Done:**
- [x] the result is written here in one sentence, with the numbers and the CPU it ran on
- [x] if it fails (< 3× random after 20 min): change the plan here — not needed, it passed

## M1 — Setup · status: done
**Outcome:** empty project where every check runs green.
**Definition of Done:**
- [x] `.gitignore` committed before any dependency install (incl. `runs/`)
- [x] skeleton + pytest + ruff in place; `.claude/dod-commands` filled with real commands
- [x] every DoD command exits 0, and each was shown able to fail
- [x] CI runs the DoD commands on push and is green
**Out of scope:** any feature code.

## M2 — Watch blues learn to eat · status: building (spec 002)
**Outcome:** one command opens the browser: full-window wrap-around plane, 50 green food, several
blues learning live with a shared brain. Vision circle show/hide. Speed toggle (watch / fast-forward).
**Definition of Done (runnable):**
- [ ] learning test: fixed seed, tiny world, trained blues eat more than random (≤ 2 min)
- [ ] the world (wheels, wrap-around, vision slices, food respawn) is tested without the browser
- [ ] HUMAN TASK (2 min): PO runs the start command and confirms he sees blues getting better
**Out of scope:** live controls, charts, reds.

## M3 — Change the world live, see it in charts · status: todo
**Outcome:** live controls for food count, blue count (add one / several, joining with the current
brain) and blue speed. Charts: blue food per minute and blue eating efficiency. Save / load brain.
**Definition of Done (runnable):**
- [ ] a control change reaches the simulation within 1 s (automated test)
- [ ] the efficiency number is tested on a hand-made case (a blue driving straight at food ≈ 100%)
- [ ] save → load → same seed gives the same score (test)
- [ ] ≥ 20 agents at ≥ 30 frames/second in the browser (measured, number in the PR)

## M4 — Red predators, both learning · status: todo
**Outcome:** reds with their own shared brain, learning from the moment they appear; a caught blue
dies. Red controls identical to blue's (add, speed, constant / natural population); the blue
constant / natural switch. Chart: red catches per minute, on the same timeline as blue food.
**Definition of Done (runnable):**
- [ ] learning test: trained reds catch more than random reds; trained blues survive longer than
      untrained blues against the same reds (fixed seeds)
- [ ] population modes tested: constant keeps the count; natural lets blues die out

## M5 — Stamina · status: todo
**Outcome:** blues lose energy over time and starve if they eat too slowly. Then the PO picks what's
next (reproduction, reds starving, a bigger predator…), each its own spec.

## M6 — A classic game · status: todo
**Outcome:** an Atari-style game from the standard RL toolkit (OPEN QUESTION: which). The PO plays
it with the keyboard; then an agent trains on it; he watches it play and sees its score chart.

## M-last — Wrap up · status: todo
**Outcome:** `README.md` with a screenshot and charts, how to start it, and what each species learned.
