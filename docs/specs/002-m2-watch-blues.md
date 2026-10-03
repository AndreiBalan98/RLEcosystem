# Spec 002 — M2: watch blues learn to eat

**Milestone:** M2 · **Status:** approved · **Date:** 2026-10-03

## Goal
The PO runs one command, `.venv/bin/python -m rlecosystem`, and the browser opens on a full-window
wrap-around plane with 50 green food and 5 blues learning live with one shared brain. One button
shows/hides each blue's vision circle with its 16 slices; another toggles watch speed /
fast-forward. A small text line shows simulated time and food eaten per blue in the last simulated
minute, so he can see the blues getting better.

## Not doing
- Live controls (food count, blue count, speed), charts, save / load, reds, the efficiency metric.
  Those are M3 and M4.
- Fixing the short pause during each brain update (see Risks), unless the PO asks.

## Approach
M0's settings (STATE.md, "Carried over from M0") are reused unchanged.
- **World** (`world.py`, vectorised numpy): `World(n_worlds, n_blues, seed)`. 1600×900 px, edges
  wrap. 50 food (radius 5); an eaten one reappears at once at a random spot. Blues have radius 10
  and eat when centre distance < 15. Two wheels, each in [0, vmax = 150 px/s]: forward speed =
  mean of the wheels, turn rate = difference ÷ wheelbase, with the wheelbase set so the fastest spin
  is ≈ 1 turn/s. dt = 1/30 s. `observe()` → (worlds, blues, 80): per slice (16, relative to
  heading), the nearest thing inside the 150 px vision circle as one-hot [food, blue, red, nothing]
  plus distance ÷ 150 (nothing → 1.0). Distances account for the wrap. `step(wheels)` → rewards.
- **Brain** (`ppo.py`, in-house PPO, PyTorch CPU): policy MLP 80→64→64 tanh with a Gaussian over
  the 2 wheels (log_std init −0.5), separate value MLP. GAE γ 0.99, λ 0.95, clip 0.2, lr 3e-4,
  4 epochs × 4 minibatches, entropy 0.001. Actions mapped (x+1)/2, clipped to [0, 1], × vmax.
  No episodes (infinite horizon), as in M0.
- **Trainer** (`trainer.py`): owns a World of 16 worlds × 5 blues and the PPO brain. `tick()`
  advances every world one step and runs a PPO update every 128 steps. World 0 is shown; the other
  15 are hidden and train the same brain (PO decision, 2026-10-03). `snapshot()` returns world 0 as
  plain data: food positions, blue x / y / heading, per-slice nearest type and distance, stats
  (simulated time, food per blue in the last simulated minute, updates done).
- **Server** (`server.py`, FastAPI + uvicorn): the simulation loop runs in one background thread.
  Watch = 30 ticks/s real time (1 simulated second per second); fast = as fast as the CPU allows.
  `GET /` serves the page. `WS /ws` pushes the latest snapshot as JSON about 30 times a second and
  accepts `{"speed": "watch"}` / `{"speed": "fast"}`. Vision show/hide is a drawing switch in the
  browser only.
- **Start** (`__main__.py`): starts uvicorn on 127.0.0.1:8000 and opens the default browser.
- **Page** (`static/index.html`, `static/app.js`): plain JavaScript and canvas, no library. The
  world stays 1600×900 and is scaled to fit the window (letterboxed).
- Torch uses 4 threads, as in M0. New dependency: `websockets==17.2` (PO approved, 2026-10-03).
  It lets uvicorn serve WebSockets, and the tests use its client.

## Files and interfaces
| File / interface | New / changed | What |
|---|---|---|
| `src/rlecosystem/world.py` | new | `World`: wheels, wrap, vision, food respawn, rewards |
| `src/rlecosystem/ppo.py` | new | policy / value nets, GAE, PPO update, action mapping |
| `src/rlecosystem/trainer.py` | new | `Trainer`: worlds + brain, `tick()`, `snapshot()` |
| `src/rlecosystem/server.py` | new | FastAPI app, sim thread, `GET /`, `WS /ws` |
| `src/rlecosystem/__main__.py` | new | the one start command |
| `src/rlecosystem/static/index.html`, `app.js` | new | canvas view, two buttons, stats line |
| `WS /ws` messages | new | server → `{food, blues, slices, stats}`; client → `{speed}` |
| `tests/test_world.py`, `test_ppo.py`, `test_learning.py`, `test_server.py` | new | see Test plan |
| `pyproject.toml` | changed | `websockets==17.2`; ship `static/` as package data |
| `docs/ROADMAP.md`, `docs/STATE.md` | changed | status and handover |

## Touches existing code
Only `pyproject.toml` (one dependency line plus package data). Nothing else exists yet. CI
installs from `pyproject.toml`, so it picks up `websockets` with no workflow change.

## Test plan
| Case | Type | Expected |
|---|---|---|
| equal wheels → straight line, vmax·dt per step | unit | exact distance, heading unchanged |
| left wheel faster → turns right; full spin speed ≈ 1 turn/s | unit | sign and size of heading change |
| leaving through any edge comes back on the opposite side | unit | wrapped position |
| food in slice k at distance d → slice k one-hot food + d/150 | unit | exact values |
| empty slice → nothing, 1.0; two things in one slice → nearest wins; food across the wrap edge is seen | unit | exact values |
| blue on food → reward +1, still 50 food, eaten food moved | unit | exact |
| same seed → same trajectory; different seed → different | unit | equal / unequal arrays |
| GAE on a hand-made 3-step case | unit | hand-computed numbers |
| action mapping: any network output → wheel speeds in [0, vmax] | unit | bounds hold |
| **learning:** tiny world, fixed seed, fixed number of updates; trained (mean action) vs the better of uniform random and untrained | integration | ≥ 2× food/min, test runs < 60 s |
| learning test can go red | proof, once | with lr = 0 it fails (output in Result) |
| server: `GET /` → 200 HTML; a WS frame has food / blues / slices / stats; sending `fast` raises ticks/s | integration (real uvicorn in a thread + websockets client) | as stated |

## Definition of Done (commands)
```
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
.venv/bin/pytest -q
```
The whole DoD stays under about 2 minutes.
End-to-end check: Claude starts the server headless, connects with the websockets client, and prints
one frame plus ticks/s in watch vs fast. Then a HUMAN TASK (5 min): the PO runs
`.venv/bin/python -m rlecosystem`. Pass = "the blues visibly head for food more than at the start,
and the food/min number went up".

## Assumptions made
- The world is fixed at 1600×900 and scaled to fit any window. PRODUCT says window-sized, but a
  fixed size keeps the brain identical on every screen and matches M0.
- 5 visible blues (15 hidden worlds × 5 more train the same brain).
- The on-screen food/min text is orientation only, not the M3 chart.
- The brain starts fresh on every start (save / load is M3).
- Server only on 127.0.0.1 (not reachable from other machines).

## Risks
- Each PPO update (~0.3 s) runs in the sim thread, so the picture may pause briefly every ~4 s at
  watch speed. Accepted for M2; fix in M3 if it bothers the PO.
- M0 saw a dip at 10 min of training (fixed learning rate); it may show live. Known debt.
- The learning test must stay short and stable on both the laptop and CI; it uses a fixed seed and
  a fixed number of updates, not wall-clock time.

## Needs a decision from the Product Owner
- [x] New dependency `websockets` — approved 2026-10-03.
- [x] Hidden worlds train the shared brain — approved 2026-10-03.
- [x] Approve this spec — approved 2026-10-03.
