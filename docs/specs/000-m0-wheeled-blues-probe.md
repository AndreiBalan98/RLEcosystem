# Spec 000 — M0 probe: can wheeled blues learn to eat fast enough?

**Milestone:** M0 · **Status:** done · **Date:** 2026-10-03

## Goal
Settle PRODUCT.md's riskiest assumption with numbers: do blues that steer with two wheels and see
through a 16-slice vision circle learn to eat ≥ 3× more food per minute than random blues within
20 minutes of training on the PO's laptop CPU?

## Not doing
- No graphics, no server, no reds, no tests / CI / DoD setup (that is M1).
- The probe script is never committed: it lives in the session scratchpad and is thrown away.
  Only docs change in the repo.

## Approach
- **World** (numpy, vectorised, many worlds in parallel): 1600×900 px, edges wrap, 50 food
  (radius 5) that respawn at once at a random spot, 5 blues per world (radius 10).
  Time step 1/30 s; "one minute" = 1800 steps of simulated time at normal watching speed.
- **Body:** two wheels, each speed in [0, vmax], vmax = 150 px/s. Forward speed = mean of the wheels;
  turn rate = difference ÷ wheelbase, wheelbase chosen so the max spin is ≈ 1 turn per second.
  A blue eats a food when centre distance < 15 px.
- **Vision:** radius 150 px, 16 slices relative to heading. Per slice, the nearest object →
  one-hot [food, blue, red, nothing] + distance ÷ radius (nothing → 1.0). 80 inputs.
- **Brain:** one shared PPO brain for all blues (in-house PPO, PyTorch CPU): policy MLP 80→64→64,
  Gaussian over 2 outputs, clipped and mapped to wheel speeds; separate value MLP. No episodes
  (infinite horizon), γ = 0.99, GAE λ = 0.95, 16 worlds × 5 blues, 128-step rollouts, 4 epochs,
  lr 3e-4. Reward: +1 per food eaten, nothing else.
- **Evaluation:** fixed seed, 1 world, 5 blues, 3 simulated minutes, same starting layout each
  time. Food per minute per blue for:
  uniform random wheel speeds · untrained brain · trained brain (mean action and sampled action)
  at 1, 2, 5, 10, 15, 20 min of training wall-clock · a hand-written "drive at the nearest food"
  controller (ceiling, for context only).

## Files and interfaces
| File / interface | New / changed | What |
|---|---|---|
| `docs/specs/000-m0-wheeled-blues-probe.md` | new | this spec, result appended at the end |
| `docs/ROADMAP.md` | changed | M0 result sentence + status |
| `docs/STATE.md` | changed | rewritten for the next session |
| scratchpad `m0_probe.py` | throwaway | the probe; not in the repo |

## Touches existing code
None — there is no code yet.

## Test plan
| Case | Type | Expected |
|---|---|---|
| success bar | probe run | trained (mean action) at 20 min ≥ 3× the **better** of the two baselines |
| metric can go red | probe run | random baseline is far below the nearest-food controller; if close, the metric is broken |
| learning curve | probe run | checkpoints at 1/2/5/10/15/20 min show when learning becomes visible |

## Definition of Done (commands)
```
.venv/bin/python <scratchpad>/m0_probe.py --minutes 20
```
End-to-end check: the printed table, pasted into the PR, plus one sentence in ROADMAP M0.

## Assumptions made
- World 1600×900 (a typical full browser window), 5 blues, vmax 150 px/s, vision radius 150 px.
- The success bar compares against the better of two baselines (uniform random, untrained brain).
- On failure: at most one retune of learning settings (not world rules), then the PO decides.

## Risks
- Training speed on a 12-thread laptop CPU limits how many samples 20 minutes buys.

## Needs a decision from the Product Owner
- [x] Only if the bar fails: which plan change — not needed, the bar passed.

## Result
Run: `.venv/bin/python m0_probe.py --checkpoints 1 2 5 10 15 20` on an Intel i7-1255U, 4 torch threads.
Food eaten per minute per blue, eval world seed 12345, 3 simulated minutes:
```
baseline  random wheels      :   4.20 food/min/blue
baseline  untrained (mean)   :   3.60
baseline  untrained (sampled):   5.27
ceiling   drive-at-nearest   :  26.40
training: 16 worlds x 5 blues, 128-step rollouts, 4 threads
train_min  sim_steps  steps/s train_food/min eval_mean eval_sampled
     1.01       8448      140          41.91     48.00        46.27
     2.00      17280      144          46.55     52.60        50.87
     5.01      43648      145          55.05     60.07        57.07
    10.00      87680      146          41.66     45.87        48.87
    15.01     132352      147          56.99     60.93        59.33
    20.01     176000      147          58.90     58.87        59.60
```
- **Bar:** 58.87 ÷ 5.27 = **11.2×** at 20 min (≥ 3× needed). Passed at 1 min already (9.1×).
- **"Ceiling" was mislabelled:** the nearest-food controller scores 89.7 with 1 blue but 26.4 with 5,
  because all blues chase the same food. It is a weak reference, not a ceiling. Random (4.2) is still
  far below it, so the metric does tell good from bad driving.
- **Dip at 10 min** (60 → 46 → 61): ordinary PPO wobble at a fixed learning rate. Recorded as debt.
- Training speed: ~147 world-steps/s × 80 blues ≈ 11,800 agent-steps/s. 1 training minute ≈ 4.9
  simulated minutes at watching speed.
- The probe script was deleted after the run (never committed).
