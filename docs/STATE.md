# STATE

> Rewritten at the end of every work block. Written for someone returning after **three weeks**.

**Last updated:** 2026-10-03
**Current milestone:** M2 — Watch blues learn to eat (status: building)
**Current spec:** `docs/specs/002-m2-watch-blues.md` (approved 2026-10-03)
**Branch:** `feat/m2-watch-blues`

## HUMAN TASK 1 — install websockets (1 min, blocks M2's server)
1. In the terminal where Claude Code runs, type exactly:
   `! .venv/bin/pip install websockets==17.2` and press Enter.
2. Done looks like: the last line says `Successfully installed websockets-17.2`.
3. What Claude does next: pins it in `pyproject.toml` and builds the live server on it.

## Where we are
M1 is merged. M2's spec is approved; building has not started. The repo is a Python project with no
features yet:
- `pyproject.toml`: pinned dependencies, plus the ruff and pytest settings.
- `src/rlecosystem/`: an empty package.
- `tests/test_smoke.py`: checks the imports, that torch is the CPU build, and fixed-seed determinism.
- `.claude/dod-commands`: ruff check, ruff format --check and pytest, all run on `src tests`.
- `.github/workflows/ci.yml`: runs every line of `.claude/dod-commands` on every push.

Each check was shown red once on purpose, locally and in CI (run 37128486560). The package is
installed editable in `.venv`.

## Next step
1. The PO does HUMAN TASK 1.
2. Claude builds M2 as spec 002 describes: world → brain → trainer → server → page, tests first.

## Why the current approach
CI reads `.claude/dod-commands` instead of repeating the commands, so the Stop hook and CI can't
drift apart. Ruff only looks at `src tests`. The code lives there, and inside Claude's sandbox some
`.claude/` files can't be read.

## In progress / committed but unfinished
- Nothing.

## Blocked on the human
- HUMAN TASK 1 (install websockets).

## Decisions made since last review
- `src/` layout, a single `pyproject.toml`, and exact `==` pins of the versions already in `.venv`.
- CI: GitHub Actions (PO approved; free tier), Ubuntu, Python 3.14, torch from the PyTorch CPU index,
  checkout@v5 / setup-python@v6. One run takes about 45 s.
- No type checker for now, because it would be a new dependency.
- M2 (PO, 2026-10-03): add `websockets==17.2`; 15 hidden worlds train the shared brain next to the
  visible one.
- Carried over from M0 as the starting point for M2:
  - World: 1600×900, 50 food (r 5), 5 blues (r 10), vmax 150 px/s, at most 1 turn/s, dt 1/30 s,
    vision radius 150 px.
  - PPO: MLP 80→64→64 tanh, separate value net, log_std init −0.5, γ 0.99, λ 0.95, clip 0.2,
    lr 3e-4, 16 worlds × 5 blues, 128-step rollouts, 4 epochs × 4 minibatches, entropy 0.001,
    4 torch threads.
  - Actions: Gaussian, mapped (x+1)/2 and clipped to [0,1].
  - The success bar compares against the *better* of two random baselines.

## Tried and rejected — don't retry
- "Drive at the nearest food" as an efficiency ceiling with several blues: they all chase the same
  food (89.7/min alone, 26.4 with 5 blues). The M3 efficiency chart needs a per-blue definition
  that doesn't assume blues compete with nobody.
- `ruff ... .` on the whole repo inside Claude's sandbox fails with "Permission denied" on masked
  `.claude/` files. Use `src tests`.

## Known debt
- `gh` inside Claude's sandbox isn't logged in. It shares GitHub's anonymous limit of 60 API calls
  an hour and can't read CI logs. `git push` works because it uses the stored token. Run
  `gh run view` sparingly.
- Learning wobbled at 10 min in M0 (eval 60 → 46 → 61). Consider learning-rate decay or a smaller lr
  in M2 if the live view shows blues getting worse for a while.
- Python in `.venv` is 3.14.7 (PRODUCT says 3.12+; fine).
