# STATE

> Rewritten at the end of every work block. Written for someone returning after **three weeks**.

**Last updated:** 2026-10-03
**Current milestone:** M0 — Can wheeled blues learn to eat fast enough? (status: review, PR open)
**Current spec:** `docs/specs/000-m0-wheeled-blues-probe.md` (done)
**Branch:** `feat/m0-probe`

## Where we are
M0 passed. A throwaway headless probe showed that wheel-steered blues with 16-slice vision and one
shared PPO brain eat 58.9 food/min each after 20 min of CPU training, vs 5.3 for random blues (11.2×).
They were already at 9× after 1 minute. Full table is in the spec. No product code exists yet.

## Next step
PO merges the M0 PR. Then M1 (setup): plan mode → spec 001 → skeleton, pytest, ruff,
`.claude/dod-commands`, CI. Every check must be shown failing once.

## Why the current approach
The riskiest assumption (wheels too hard to learn fast on CPU) is settled, so the ROADMAP is unchanged.

## In progress / committed but unfinished
- Nothing besides the open M0 PR.

## Blocked on the human
- Merge the M0 PR on GitHub (PR link is in the session hand-back).

## Decisions made since last review
- Probe world, the starting point for M2: 1600×900, 50 food (r 5), 5 blues (r 10), vmax 150 px/s,
  wheelbase gives 1 turn/s max, dt 1/30 s, vision radius 150 px (answers PRODUCT's open question for now).
- PPO settings that worked: MLP 80→64→64 tanh, separate value net, log_std init −0.5, γ 0.99,
  λ 0.95, clip 0.2, lr 3e-4, 16 worlds × 5 blues, 128-step rollouts, 4 epochs × 4 minibatches,
  entropy 0.001, 4 torch threads. Actions: Gaussian, mapped (x+1)/2 and clipped to [0,1] wheel speed.
- The success bar compares against the *better* of two random baselines (uniform random wheels,
  untrained brain).

## Tried and rejected — don't retry
- "Drive at the nearest food" as an efficiency ceiling with several blues: they all chase the same
  food (89.7/min alone, 26.4 with 5 blues). The M3 efficiency chart needs a per-blue definition
  that doesn't assume blues compete with nobody.

## Known debt
- Learning wobbled at 10 min (eval 60 → 46 → 61). Consider learning-rate decay or a smaller lr in M2
  if the live view shows blues getting worse for a while.
- Python in `.venv` is 3.14.7 (PRODUCT says 3.12+; fine).
