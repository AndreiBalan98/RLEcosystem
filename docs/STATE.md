# STATE

> Rewritten at the end of every work block. Written for someone returning after **three weeks**.

**Last updated:** 2026-10-03
**Current milestone:** M1 — Setup (status: building, blocked on a HUMAN TASK)
**Current spec:** `docs/specs/001-m1-setup.md` (approved)
**Branch:** `chore/m1-setup` (3 commits, **not pushed yet**)

## Where we are
M0 is merged and done. M1 is built locally: `pyproject.toml` (pinned deps, ruff + pytest config),
`src/rlecosystem/` (empty package), `tests/test_smoke.py` (imports, CPU torch, fixed-seed
determinism), `.claude/dod-commands` (ruff check · ruff format --check · pytest), and
`.github/workflows/ci.yml`, which runs every line of `.claude/dod-commands`. All three DoD commands
are green and each was shown red once on purpose (unused import, bad formatting, wrong assert); the
Stop hook was shown blocking on a broken lint. The package is installed editable in `.venv`
(`pip install --no-deps --no-build-isolation -e .`, nothing new downloaded).

## Next step
1. PO does HUMAN TASK 1 below.
2. Claude pushes the branch, shows CI green, pushes one deliberately failing commit to show CI red,
   reverts it, shows green again, runs the `spec-reviewer`, opens the PR with all the evidence.
3. PO merges. Then M2 (watch blues learn to eat): plan mode → spec 002.

## Why the current approach
CI reads `.claude/dod-commands` instead of repeating the commands, so the Stop hook and CI can't
drift apart. Ruff only looks at `src tests`: the code is there, and inside Claude's sandbox some
`.claude/` files can't be read.

## In progress / committed but unfinished
- Branch `chore/m1-setup`: everything committed; missing only the CI proof (push blocked).

## Blocked on the human
**HUMAN TASK 1 — let your GitHub token add CI files (≈ 2 min).**
Why: `git push` failed with *"refusing to allow a Personal Access Token to create or update workflow
`.github/workflows/ci.yml` without `workflow` scope"*. GitHub requires an extra permission to add a CI
file. You add it to the token you already have, so nothing changes on your laptop.
1. In a browser open https://github.com/settings/tokens
2. Find the token git uses on this laptop. It is under **"Personal access tokens (classic)"** or
   **"Fine-grained tokens"**. If there are several, it's the one that has `repo` access (classic)
   or access to `RLEcosystem` (fine-grained).
3. Click its name to edit it.
   - Classic: tick the **`workflow`** checkbox, scroll down, click **Update token**.
   - Fine-grained: under *Repository permissions*, set **Workflows** to **Read and write**, click **Update**.
4. Do **not** click "Regenerate token": that would make a new token and stop git from logging in.
5. Done looks like: back in Claude Code, type `continue M1`. Claude retries
   `git push -u origin chore/m1-setup`, and it should no longer say "refusing to allow".

## Decisions made since last review
- `src/` layout, single `pyproject.toml`, exact `==` pins of the versions already in `.venv`.
- CI: GitHub Actions (PO approved, free tier), Ubuntu, Python 3.14, torch from the PyTorch CPU index.
- No type checker for now (it would be a new dependency).
- From M0 (still the starting point for M2): world 1600×900, 50 food (r 5), 5 blues (r 10),
  vmax 150 px/s, 1 turn/s max, dt 1/30 s, vision radius 150 px. PPO: MLP 80→64→64 tanh, separate
  value net, log_std init −0.5, γ 0.99, λ 0.95, clip 0.2, lr 3e-4, 16 worlds × 5 blues, 128-step
  rollouts, 4 epochs × 4 minibatches, entropy 0.001, 4 torch threads; actions Gaussian, mapped
  (x+1)/2 and clipped to [0,1]. Success bar compares against the *better* of two random baselines.

## Tried and rejected — don't retry
- "Drive at the nearest food" as an efficiency ceiling with several blues: they all chase the same
  food (89.7/min alone, 26.4 with 5 blues). The M3 efficiency chart needs a per-blue definition
  that doesn't assume blues compete with nobody.
- `ruff ... .` (whole repo) inside Claude's sandbox: fails with "Permission denied" on masked
  `.claude/` files. Use `src tests`.

## Known debt
- Learning wobbled at 10 min in M0 (eval 60 → 46 → 61). Consider learning-rate decay or a smaller lr
  in M2 if the live view shows blues getting worse for a while.
- Python in `.venv` is 3.14.7 (PRODUCT says 3.12+; fine).
