# PRODUCT

> Filled from the brainstorm chat (3 Oct 2026). Changes need the Product Owner.

## Operating settings
| Setting | Value |
|---|---|
| **Involvement level** | I1 <!-- I0 throwaway · I1 milestone · I2 close control --> |
| **Maturity level** | L1 <!-- L0 prototype · L1 working · L2 reliable · L3 production --> |
| Budget ceiling / month | 0 — everything runs on the PO's laptop, CPU only |
| Deadline | none |
| Who else touches this code | nobody |
| **Repository visibility** | private |

## Riskiest assumption
**Blue agents that steer with two wheels and see through a 16-slice vision circle visibly learn to
eat within 10–20 minutes of training on the PO's laptop CPU.** Steering with wheels is harder to learn
than "move towards the food". If it takes hours, live watching stops being fun and the plan changes.
Evidence that settles it: a throwaway headless script, fixed seed, prints food eaten per minute for
random blues vs trained blues after ≤ 20 min. Claude runs it; no human task needed.

## Problem
The PO wants to *see* reinforcement learning happen: agents start clueless, get better, and adapt
when he changes their world — with charts that show it, not just a final score.

## Users
The PO, watching and experimenting on his own machine. Nobody else.

## Core loop
Start the world → watch agents learn live → change something (more food, more blues, more reds,
faster reds) → watch behaviour and charts react.

## The world
| Item | Decision |
|---|---|
| Plane | 2D, top-down, the size of the browser window. **Edges wrap around** (leave right, come back left). Size is fixed when the run starts, so a brain behaves the same on any screen. |
| Food | **Green** circles. **50 by default**, count always constant: an eaten one reappears at a random spot at once. |
| Blue agents | Foragers. Eat food. Die when a red catches them. **All blues share one brain.** |
| Red agents | Predators. Same body and senses as blue. Catch blues. **All reds share one brain, learning from the moment they appear.** |
| Body | A circle. Moves with **two invisible wheels, left and right**: the brain sets each wheel's speed, **forward only** (0 → max). Turning comes from the speed difference — the agent has to learn to steer. Wheels are not drawn. |
| Vision | A circle around the agent (radius = a setting), cut into **16 slices**. Each slice reports the **nearest** thing in it: a **type code** (food · blue · red · nothing; more types can be added later) and its **distance**. |
| Rewards | Blue: **+1 per food eaten** (nothing else for now). Red: **+1 per blue caught**. |
| Death | A caught blue disappears. Reds don't die yet. |

## Live controls (while it runs, no restart)
- **Food:** number of food dots
- **Blues:** add one / add several; speed; population mode — **constant** (a dead blue respawns) or
  **natural** (dead blues stay dead; no reproduction yet, so the count only falls)
- **Reds:** the exact same controls as blues (add, speed, constant / natural); reds never fall yet
- **Vision circle:** show / hide (with its 16 slices)
- A new agent joins with its species' brain **as it is right then**
- **Speed toggle:** watch at normal speed / fast-forward training
- **Save / load** each species' brain

## Charts (live, one shared timeline)
1. **Blue food eaten per minute**
2. **Red catches per minute** — on the same timeline as 1, so the arms race is visible
3. **Blue eating efficiency** — one average line: actual eating rate ÷ the best rate possible given
   blue's max speed and how far the food is (100% = drives straight at the nearest food every time)

## Later (after the MVP, each its own milestone)
- **Stamina:** blues lose energy over time and starve if they eat too slowly
- reproduction; reds starving; a bigger predator that eats reds
- a classic game (Atari-style, e.g. Pong or Breakout, from the standard RL toolkit): the PO plays
  it with the keyboard, then an agent learns it and he watches

## Non-goals (explicitly NOT building)
- Mario, Miniclip/Flash or any game we'd need a ROM or pirated copy for
- anything that needs a GPU, a cloud server or money
- online hosting, accounts, mobile app, 3D
- evolution-based learning (may come later as a comparison, not now)
- drawing the wheels

## Success criteria
- **Learning, proven by a test:** on a fixed seed, trained blues eat ≥ 3× more food per minute than
  random blues, after ≤ 20 min of training on the PO's CPU
- **Arms race, proven by a test:** with fixed seeds, trained reds catch more than random reds, and
  trained blues survive longer than untrained blues against the same reds
- **Live:** a control change reaches the world within 1 second; charts update at least once a second
- **Watchable:** ≥ 30 frames/second in the browser with 50 food and ≥ 20 agents
- a saved brain, reloaded, behaves like before (same seed → same score)

## Technical decisions (Claude's, stated — the PO can overrule)
| Area | Decision | Why |
|---|---|---|
| Delivery target | local web page in the browser (`localhost`), full window | live view, controls and charts in one place |
| Stack | Python 3.12+, PyTorch (CPU build), numpy; small server (FastAPI + uvicorn) with a WebSocket; browser canvas + a small chart library | he knows Python and PyTorch from FlappyBirdDQN |
| RL algorithm | PPO, small in-house implementation | every line visible to tests; wheel speeds are continuous numbers, which PPO handles well |
| Brain inputs | per slice: the type as one-hot (food/blue/red/nothing) + distance scaled 0–1 | the PO's type codes, in the form a neural net reads best |
| Data & storage | saved brains and chart history under `runs/` (git-ignored) | no database needed |
| Auth / external services / hosting | none — runs on his laptop (Fedora) | |
| Architecture | monolith: simulation + learning + server in one process | default until proven otherwise |

**Dependencies (approved by the PO when he installs them in setup):** numpy, torch (CPU build),
fastapi, uvicorn, pytest, ruff. Chart and drawing code runs in the browser.

## Constraints
- **Every claim that something learns is a fixed-seed test**, not "it looks like it's learning".
  Learning tests use a tiny world so they run in under ~2 minutes in the DoD.
- **Every milestone ends with something the PO can watch** in the browser, with one exact command to start it.
- Training uses the laptop, not Claude: Claude writes code; long runs don't need Claude watching.

## Open questions
- OPEN QUESTION: vision radius default — M0 picks one that learns, the PO can change it live later.
- OPEN QUESTION: should blue get a penalty for being caught, or is losing its future food enough?
  Start with none; add one only if blues don't learn to flee (PO decides).
- OPEN QUESTION: which classic game first — decided when we get there.
