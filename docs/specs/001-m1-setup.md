# Spec 001 — M1 setup: an empty project where every check runs green

**Milestone:** M1 · **Status:** approved · **Date:** 2026-10-03

## Goal
After this, the repo is a real Python project with no features yet: one package, one test folder,
lint + format + tests that run with one command each, the same commands wired into the Stop hook
(`.claude/dod-commands`) and into GitHub CI on every push. Each check is shown going red once on
purpose, so we know it can catch something.

## Not doing
- Any feature code (world, brain, server, browser page) — that starts in M2.
- A type checker (mypy/pyright): it would be a new dependency the PO hasn't approved. Can be
  proposed later if bugs show it's needed.
- A `README.md` (M-last), a Makefile, pre-commit hooks, coverage reports.
- Changing the dependencies already installed in `.venv` (approved list in PRODUCT.md).

## Approach
- **Layout:** `src/` layout — package `src/rlecosystem/`, tests in `tests/`. Installed into the
  existing `.venv` as editable (`pip install -e .`, no new packages), so tests import it like the app will.
- **One config file:** `pyproject.toml` holds the project metadata, the pinned dependencies (exact
  versions already in `.venv`: numpy, torch CPU, fastapi, uvicorn; dev: pytest, ruff), and the
  ruff and pytest settings. `requires-python = ">=3.12"`.
- **torch CPU build:** installed from PyTorch's CPU wheel index (`download.pytorch.org/whl/cpu`) both
  locally and in CI, so CI never pulls the multi-GB CUDA build.
- **Skeleton content (no features):** `rlecosystem/__init__.py` with `__version__`; one smoke test
  that imports the package and checks the toolchain the later milestones rely on: numpy and torch
  import, torch is the CPU build, and a fixed seed gives the same random numbers twice
  (determinism is the base of every learning test later).
- **DoD = three commands**, run from the repo root against `.venv`:
  `ruff check src tests` (lint) · `ruff format --check src tests` (formatting) · `pytest -q` (tests).
- **CI:** GitHub Actions, one workflow, Ubuntu, Python 3.14 (matches `.venv`). It creates `.venv`
  the same way as locally, installs, then runs **every line of `.claude/dod-commands`** — CI reads
  that file, so the Stop hook and CI can never drift apart.
- **.gitignore:** add `runs/` (saved brains / chart history, per PRODUCT), `.pytest_cache/`,
  `.ruff_cache/`, `*.egg-info/`.
- **Proving each check can fail** (evidence in the PR): break lint (unused import), formatting
  (badly spaced line), a test (wrong assert) — each run shown red, then fixed and green. For CI:
  push one deliberately failing commit on this branch, show the red run, then a revert commit and
  the green run. No force-push; the red commit stays in branch history and is squashed away on merge.

## Files and interfaces
| File / interface | New / changed | What |
|---|---|---|
| `pyproject.toml` | new | metadata, pinned deps, ruff + pytest config |
| `src/rlecosystem/__init__.py` | new | empty package with `__version__` |
| `tests/test_smoke.py` | new | toolchain smoke test (imports, CPU torch, seeded determinism) |
| `.claude/dod-commands` | changed | the three real commands |
| `.github/workflows/ci.yml` | new | runs `.claude/dod-commands` on every push |
| `.gitignore` | changed | `runs/`, tool caches, egg-info |
| `docs/ROADMAP.md` | changed | M0 → done, M1 status |
| `docs/STATE.md` | changed | rewritten at the end |

## Touches existing code
No product code exists. The Stop hook starts running real commands from this milestone on, so every
later turn that changes files must keep lint, format and tests green.

## Test plan
| Case | Type | Expected |
|---|---|---|
| happy path | DoD | all three commands exit 0 locally; CI run on the branch is green |
| lint can fail | manual break | unused import → `ruff check` exits 1, names the file |
| format can fail | manual break | misformatted line → `ruff format --check` exits 1 |
| test can fail | manual break | wrong assert in smoke test → `pytest` exits 1 |
| CI can fail | pushed break | red CI run on the branch, then green after the revert |
| hook uses the file | Stop hook | with a broken check, the Stop hook blocks the turn (seen during the breaks above) |

## Definition of Done (commands)
```
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
.venv/bin/pytest -q
```
End-to-end check: the CI run for the PR's last commit is green, and the PR lists the four red runs.

## Assumptions made
- `src/` layout + editable install (prevents tests accidentally importing from the wrong place).
- Python 3.14 in CI because `.venv` is 3.14.7; `requires-python >=3.12` as PRODUCT says.
- Exact version pins (`==`) for reproducible results; upgrades are deliberate commits.
- No type checker in the DoD (see "Not doing").

## Risks
- `gh` is not logged in inside Claude's sandbox; if pushing or reading CI status fails, it becomes
  a short HUMAN TASK (`gh auth login`) or the PO opens the Actions page.
- Python 3.14 + torch 2.14 CPU wheels must exist on the CPU index for Linux — they do locally; if CI
  can't find them, fall back to Python 3.13 in CI and note it here.

## Needs a decision from the Product Owner
- [ ] Use **GitHub Actions** for CI on this private repo. It is free up to 2,000 minutes/month on a
      private repo; one run here is ≈ 2–4 min (mostly downloading torch), so ~500 pushes/month
      before the free allowance runs out. With GitHub's default $0 spending limit, runs stop
      instead of costing money.
