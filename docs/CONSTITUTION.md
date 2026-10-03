# CONSTITUTION

Non-negotiable rules. Changing this file requires an explicit Product Owner decision.

## 1. Documents — the set is closed
The only markdown files in this repo are: `CLAUDE.md`, `README.md`, `docs/PRODUCT.md`,
`docs/CONSTITUTION.md`, `docs/ROADMAP.md`, `docs/STATE.md`, `docs/specs/NNN-*.md`,
`docs/decisions/ADR-NNN-*.md`, files under `.claude/`, and session archives under
`sessions/<date>-<slug>/`. A domain pack may add its own: the trading pack adds
`docs/RESEARCH-LOG.md`, `docs/experiments/NNN-*.md` and `docs/LITERATURE.md`.
- **Session archives** are raw Claude Code transcripts, kept so the way of working can be reviewed.
  Append-only evidence: never edited afterwards, never a substitute for `STATE.md` or a spec.
  Before committing one, check what it contains (emails, paths, scraped third-party content, keys)
  and confirm the repo's visibility — see §6.
- Claude never creates any other markdown file without asking. No summaries, guides, completion
  reports or quick-starts. Record things in `STATE.md` or the spec.
- Enforced by `.claude/hooks/guard-docs.sh` and `.claude/hooks/guard-bash-writes.sh`.

## 2. Specs
- Every milestone has a spec in `docs/specs/NNN-name.md`, **committed before the first line of
  implementation code**.
- If the approach changes mid-milestone: stop → update spec → approval → code.
- The spec is updated in the same PR as the code, or the PR doesn't merge.
- Bugs skip the spec: failing test that reproduces it first, then the fix.

## 3. Verification
- The Definition of Done is `.claude/dod-commands`: every line must exit 0.
  Typical: lint · typecheck · test · build · deploy-dry-run (what the host will run, run locally).
- The Stop hook blocks the turn from ending while any DoD command fails.
- Commit messages containing `?`, `untested`, `try`, `maybe`, `idk` or `should work` fail the DoD.
  If it isn't verified, it isn't committed as done — use `wip:` and say what's missing.
- At L1+: CI runs the same DoD commands on every push.
- Evidence over assertion: PRs include the commands run and their output.
- **Every check is proven able to fail.** When a DoD command is added, break the thing it guards on
  purpose once, show it go red, and put that in the milestone's evidence. A green check that cannot
  go red is worse than no check.
- Manual checks are allowed only when no command can do the job, and are written as a HUMAN TASK
  (§ CLAUDE.md) with an exact pass/fail sentence.

## 4. Code
- Simple over clever. Follow the existing patterns in the codebase.
- No new dependency without Product Owner approval.
- No dead code, no commented-out code, no TODO without a note in `STATE.md`.
- Secrets only in environment variables; `.env.example` lists every variable with a dummy value.

## 5. Git
- Trunk-based: short-lived branches off `main` (`feat/ fix/ chore/ docs/ refactor/` + slug).
  At L0 / I0, commits may go straight to `main`.
- Conventional Commits, one logical change per commit, English only.
- `main` is always green. Never force-push. Never rewrite shared history.
- Who runs which git command is set by the involvement level (see PRODUCT.md).

## 6. Hygiene
- **Repository visibility is a Product Owner decision, recorded in `PRODUCT.md`.** Never assume a
  repo is private. Before the first push, and before committing anything that quotes a third-party
  site or the PO's machine, state the visibility out loud and get it confirmed.
- `.gitignore` exists before the first dependency install. Never commit `node_modules/`, `venv/`,
  `__pycache__/`, `dist/`, `.env*` (except `.env.example`).
