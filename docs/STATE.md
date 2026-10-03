# STATE

> Rewritten at the end of every work block. Written for someone returning after **three weeks**.

**Last updated:** 2026-10-03
**Current milestone:** M1 — Setup (status: review)
**Current spec:** `docs/specs/001-m1-setup.md` (done; evidence in its "Result" section)
**Branch:** `chore/m1-setup` (pushed)

## Where we are
M1 is built. The repo is a Python project with no features yet:
- `pyproject.toml`: pinned dependencies, plus the ruff and pytest settings.
- `src/rlecosystem/`: an empty package.
- `tests/test_smoke.py`: checks the imports, that torch is the CPU build, and fixed-seed determinism.
- `.claude/dod-commands`: ruff check, ruff format --check and pytest, all run on `src tests`.
- `.github/workflows/ci.yml`: runs every line of `.claude/dod-commands` on every push.

Each check was shown red once on purpose, locally and in CI (run 37128486560). The package is
installed editable in `.venv`.

## Next step
1. Claude confirms the CI run for the branch's last commit is green and opens the PR. If `gh` can't
   create the PR from the sandbox, the PO opens it from the link Claude gives.
2. The PO merges the PR (squash).
3. M2 (watch blues learn to eat): plan mode → spec 002.

## Why the current approach
CI reads `.claude/dod-commands` instead of repeating the commands, so the Stop hook and CI can't
drift apart. Ruff only looks at `src tests`. The code lives there, and inside Claude's sandbox some
`.claude/` files can't be read.

## In progress / committed but unfinished
- Nothing besides the open M1 PR.

## Blocked on the human
- Merge the M1 PR.

## Decisions made since last review
- `src/` layout, a single `pyproject.toml`, and exact `==` pins of the versions already in `.venv`.
- CI: GitHub Actions (PO approved; free tier), Ubuntu, Python 3.14, torch from the PyTorch CPU index,
  checkout@v5 / setup-python@v6. One run takes about 45 s.
- No type checker for now, because it would be a new dependency.
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
