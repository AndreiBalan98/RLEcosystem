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

## Result
Built on branch `feat/m2-watch-blues`, Intel i7-1255U, 4 torch threads.

**DoD** (all three lines green; 30 tests, 40 s wall-clock):
```
$ .venv/bin/ruff check src tests && .venv/bin/ruff format --check src tests && .venv/bin/pytest -q
All checks passed!
11 files already formatted
30 passed in 37.98s
```

**Learning test** (tiny world 400×300, 10 food, 8 worlds × 2 blues, 40 updates of 64 steps):
```
baselines {'uniform random': 16.0, 'untrained (mean)': 9.5, 'untrained (sampled)': 10.0}
→ trained 57.5 food/min/blue (3.59×)          1 passed in 26.69s
```
Probe over seeds 0/1/2 before fixing the settings: 3.59× / 4.06× / 3.62×, so the ≥ 2× bar has margin.
Shown red once with `LR = 0.0`: `assert 9.5 >= (2 * 16.0)` → 1 failed.

**Server test** shown red once by making `Sim.set_speed` a no-op: `assert 31 > (2 * 31)` → 1 failed.
Green run: `ticks/s watch 30 fast 233` (tiny world).

**End-to-end** (full world 1600×900, 16 worlds × 5 blues, real uvicorn + websockets client):
```
GET / -> 200
frame keys: ['blues', 'food', 'slices', 'stats', 'world'] | food 50 | blues 5
blue 0: [964.3, 798.8, -0.469] | its slice 0: [3, 150.0]
frame size: 2149 bytes
watch: {'sim_seconds': 5.9, 'food_per_min': 12.2, 'updates': 1, 'speed': 'watch', 'ticks_per_s': 31}
fast : {'sim_seconds': 52.4, 'food_per_min': 12.6, 'updates': 12, 'speed': 'fast', 'ticks_per_s': 83}
fast : {'sim_seconds': 103.4, 'food_per_min': 28.6, 'updates': 24, 'speed': 'fast', 'ticks_per_s': 87}
fast : {'sim_seconds': 155.5, 'food_per_min': 39.0, 'updates': 36, 'speed': 'fast', 'ticks_per_s': 94}
fast : {'sim_seconds': 208.9, 'food_per_min': 44.0, 'updates': 48, 'speed': 'fast', 'ticks_per_s': 144}
fast : {'sim_seconds': 263.6, 'food_per_min': 40.6, 'updates': 61, 'speed': 'fast', 'ticks_per_s': 165}
fast : {'sim_seconds': 315.7, 'food_per_min': 44.4, 'updates': 73, 'speed': 'fast', 'ticks_per_s': 128}
fast : {'sim_seconds': 364.3, 'food_per_min': 49.0, 'updates': 85, 'speed': 'fast', 'ticks_per_s': 72}
fast : {'sim_seconds': 419.7, 'food_per_min': 50.6, 'updates': 98, 'speed': 'fast', 'ticks_per_s': 93}
```
Food per blue went 12 → 51 per minute in about 2 minutes of fast-forward. Fast-forward runs
70–165 steps/s on the full world (M0's probe: ~147).

**Differences from the plan, all small:** gradient clipping 0.5 and value-loss weight 0.5 were
added to PPO (standard values; M0's script no longer exists to compare). In watch mode, the steps
lost to a PPO update are skipped, not caught up, so the speed reads 28–31 steps/s.
`spec-reviewer`: no code bugs; it asked for this Result section and a fresh STATE.md (done). From
its optional notes, a binary or malformed WebSocket message is now ignored instead of logged as an
error. Food on an edge is drawn half-cut (blues wrap visually, food doesn't): cosmetic, left as is.

**Pending:** HUMAN TASK 2 in STATE.md (the PO watches it for 5 minutes).
