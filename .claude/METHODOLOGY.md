# Agentic Development Methodology — v0.4

One person is Product Owner + Project Manager. Claude is the whole engineering team.
This file is the working guide. Attach it to the brainstorm chat; the repo carries the rest.

> **Core rule: Claude decides *how*. The human decides *what* and *whether*.**
> Anything that changes cost, scope, data, security or user-visible behaviour is a human
> decision. Everything else is Claude's to make — and to report.

The goal: **maximum control, minimum effort.** The human's involvement is concentrated at a few
high-leverage gates (approve a spec, review a finished PR). Everywhere else: zero involvement,
protected by an escalation list and automated checks.

---

## 1. Pipeline

```
Phase 0  BRAINSTORM  chat      idea → understood problem
Phase 1  SPEC        chat      → PRODUCT.md, ROADMAP.md (+ CONSTITUTION.md tweaks)
Phase 2  SETUP       terminal  install kit, scaffold, checks green
Phase 3  BUILD LOOP  terminal  one milestone at a time: Gate A → autonomous run → Gate B
Phase 4  SHIP        terminal  merge, tag, deploy
Phase 5  EVOLVE      both      raise maturity level, loop back
```

## 2. The document set — CLOSED

| File | Contains | Changes |
|---|---|---|
| `CLAUDE.md` | commands, rules, stop-and-ask list. < 50 lines (+ a pack's short section). | rarely |
| `docs/PRODUCT.md` | problem, users, scope, non-goals, decisions, **involvement level**, **maturity level** | rarely |
| `docs/CONSTITUTION.md` | non-negotiable engineering rules | almost never (PO decision) |
| `docs/ROADMAP.md` | milestones, each with DoD as runnable checks | per milestone |
| `docs/STATE.md` | live handoff, written for someone away 3 weeks | every session |
| `docs/specs/NNN-name.md` | one per milestone — **the unit the human approves** | per milestone |
| `docs/decisions/ADR-NNN.md` | architecture decisions | when made |
| `README.md` | how to run the project | rarely |
| *pack files* | only what a domain pack declares (§10) — e.g. trading: `RESEARCH-LOG.md`, `experiments/NNN-*.md` | per pack |

**Nothing else exists.** No summaries, guides, completion reports, quick-starts. Creating any other
markdown file is an escalation — and a hook blocks it.

## 3. Phase 0 — Brainstorm protocol (Claude in chat)

0. **Walk him through the method first** — ≤6 plain bullets, the two loops, which steps are his.
   He finished the first trading project without understanding the method until a picture
   explained it; the picture belongs at the start, not the end.
1. **Never ask what can be inferred or researched.** Decide, state the assumption.
2. **One decision area per turn.** Max 3 tappable questions, 2–4 options each.
3. **Ask only what is his to decide** (what / whether). How-decisions are stated, not asked.
   **Always arrive with a recommendation:** *Recommendation: X, because … Alternatives: Y (if…),
   Z (if…).* His job is yes / no / show me more.
4. **Low-stakes details: state the default and move on.** He can override.
5. **Unknowns become `OPEN QUESTION` in PRODUCT.md.** Never assume silently.
6. **Push back once**, clearly, then follow his call.
7. He may write in Romanian (often dictated). **Always reply and write artifacts in English.**

**Cover before writing the spec:** problem and user · the one core loop · MVP scope · non-goals ·
success criteria · delivery target (web/PWA/mobile/CLI) · stack · data + storage · auth · external
services · hosting · monolith (default) · **involvement level** · **maturity level** · budget ·
deadline. A domain pack adds its own checklist.

**Output of Phases 0–1:** filled `PRODUCT.md` and `ROADMAP.md` (M0 = feasibility probe, M1 = setup).
Exit test: he reads them and finds nothing surprising and nothing missing.

## 4. The involvement dial

One word in `PRODUCT.md`. `install.sh` generates `.claude/settings.json` from it.

| | **I0 Throwaway** | **I1 Milestone** (default) | **I2 Close control** |
|---|---|---|---|
| Mode | auto | auto, sandboxed | plan → acceptEdits |
| Git | Claude commits and pushes | Claude commits, pushes feature branches, opens PRs. Human merges. | Claude proposes commit messages. Human runs all git. |
| Infra / DB | Claude creates + migrates | Human owns credentials + schema changes | Claude writes `.sql`, explains; human runs |
| Gates | one, at the end | spec + PR per milestone | spec per task, every PR, ADR per architectural choice |
| Escalate on | money, secrets | full list (§6) | full list + anything ambiguous |
| Maturity | L0 | L1–L2 | L2–L3 |

**Promotion I0 → I1** (a throwaway that turned out to matter): add tests on core paths, CI,
`.gitignore` audit, backfill a spec for what exists, then continue with gates.

## 5. M0 — prove it is possible, before building anything

**The first milestone is not scaffolding. It is the smallest throwaway probe that settles the
riskiest assumption in `PRODUCT.md`** — can the data be read, does the API return what we need,
does the device expose that signal. Phase 0 ends by naming that assumption; M0 kills or confirms it.

- If settling it needs something only the human can fetch (a page's HTML, an export, an account,
  a sample file), **that HUMAN TASK is step one of the project**, before any repo work. Sequence
  the human's tasks by how much they could invalidate, not by how convenient they are.
- The probe is deleted afterwards. It is evidence, not product.
- If the assumption fails, the project stops or changes target here — with the finding written into
  `STATE.md`. **A cheap, honest "no" is a successful outcome**, not a failure.

## 5b. Phase 2 — Setup (M1)

1. Create repo, clone. Run `install.sh <I0|I1|I2> <repo> [pack]`. **Confirm repo visibility with the PO.**
2. Put the brainstorm output into `docs/PRODUCT.md` and `docs/ROADMAP.md`.
3. `.gitignore` is in place **before the first dependency install**.
4. `gh auth login` (I0/I1).
5. Claude scaffolds skeleton + test runner + linter (+ CI at L1+) **before any feature code**, and
   fills `.claude/dod-commands` with the real commands.
6. All DoD commands run green on the empty project, **and each one is proven able to fail** — break
   the thing on purpose once, show it red, put that in the evidence. **Nothing autonomous happens
   before this.**
7. Started from a generator (Lovable, template)? The next milestone is *"understand what we were
   given"*: read it, write the findings into `docs/decisions/ADR-001.md` (keep / replace / delete).

## 6. Phase 3 — The build loop

**Milestone size:** 1–3 days of agent work, demonstrable, with a machine-checkable DoD.

**Gate A — spec.** Claude, in plan mode, reads the code and writes `docs/specs/NNN-name.md`
from the template. Human approves / edits / rejects. **The spec is committed before any code.**
Every approval request opens with three plain lines — **you're approving** · **if this is wrong** ·
**check** — because a yes given without understanding is not a gate.

**Autonomous run.** Implement against the spec, write and run tests, fix own failures, small
conventional commits, update `STATE.md`. The Stop hook refuses to end the turn while DoD fails.

**Escalation — stop immediately, even mid-milestone:**
- new dependency, framework or external service
- credentials, keys, secrets, billing — anything that costs money
- DB schema change or destructive migration
- deleting/rewriting code outside the spec's scope
- changing a public API, URL or data contract
- a design decision the spec doesn't cover · discovering the spec is wrong
- **two failed attempts at the same problem**
- creating a file outside the closed document set
- anything on the pack's own stop-and-ask list

On stopping: what was found · 2–3 options with tradeoffs · recommendation.

**Gate B — PR.** Before the human looks: the `spec-reviewer` subagent (fresh context) checks the
diff against the spec, correctness gaps only. Claude fixes real gaps, then opens the PR with
**evidence** — commands run and their output — and a 5-line summary: what shipped, what changed,
what Claude decided, what needs a ruling.

## 6b. Human tasks — the expensive part

Anything only the human can do (install something, click through a UI, copy from DevTools, create
an account or key, confirm something on screen) is written in `docs/STATE.md` as a **HUMAN TASK**:

- numbered steps with **exact keystrokes**, assuming no mouse and no prior knowledge of the tool
- what "done" looks like, in one sentence he can check against
- what Claude does with the result, and what happens if it comes back different
- the **riskiest one first** — never after work that it could invalidate

Claude does everything around it: prepares the exact command to run afterwards, and verifies the
result rather than trusting it ("32 bytes" is not an HTML capture).

## 6c. Session archive

At the end of a milestone worth learning from, copy the Claude Code transcript into
`sessions/<date>-<slug>/` (`archive-session.sh` does it). Before committing: check it for emails,
absolute paths, keys and scraped third-party content, and confirm the repo's visibility. The
archive is append-only evidence and the only reliable input for improving the method.

## 7. Change and edge cases

- **Mid-milestone pivot:** stop → update the spec → human approves → only then touch code.
- **Direction change between milestones:** edit `ROADMAP.md` in a `docs:` commit. Never decide in
  chat only.
- **Bug (not a feature):** no spec. Write a failing test that reproduces it → fix → green → commit
  `fix:`. Two failed fixes → escalate.
- **New feature after v1:** same loop; the spec's "Touches existing code" section is mandatory.
- **Session death (limit / full context):** never end a block with uncommitted broken work. Commit
  to the branch with `wip:`, update `STATE.md`. Offer this early when a limit looks close.
- **Stuck:** after two failures, `/clear`, restart with a better prompt; still stuck → escalate
  with what was tried and what would be tried next.
- **Disagreement:** object once, briefly, with the reason — then comply.
- **Human-only tasks** (accounts, keys, DNS, payments): a *Blocked on human* item in `STATE.md`
  with exact click-by-click instructions.
- **Abandoned work:** delete the branch, note it in `STATE.md` under "Tried and rejected".
- **Cancelling a milestone or a project:** set the milestone's status to `cancelled` in
  `ROADMAP.md` with the reason and where the finding lives; rewrite `STATE.md` so the first
  paragraph says it is stopped and why. Do not delete the reasoning — a closed project is a record.
- **A stop rule, written before the last round.** When the work keeps failing, don't drift: agree a
  capped final round (budget + pass bar + "if nothing passes, we stop") *before* it runs, as its own
  spec. TradingWithAI ended exactly this way (spec 009) — cleanly, with no argument afterwards.
- **Closing a project:** `STATE.md` becomes the conclusion — the answer, exactly what it covers,
  what it does not cover, and what new evidence would justify reopening. `README.md` tells the same
  story for a visitor, with a chart. Archive the last sessions.
- **A rule stops the work:** that is the rule doing its job. Say which rule, in the PO's own words
  from `PRODUCT.md`, then offer 2–3 ways forward that keep the rule.

## 8. Maturity ladder

Set in `PRODUCT.md`. No skipping, no gold-plating beyond it. Raising it is its own milestone.

- **L0 Prototype** — manual testing, commits to main. Is the idea any good?
- **L1 Working** — tests on core paths, lint + format, CI on push, branches + PRs, conventional
  commits, `.env.example`, basic error handling.
- **L2 Reliable** — business-logic coverage, integration tests, typed end to end, staging,
  versioned migrations, input validation, error tracking, backups, ADRs.
- **L3 Production** — E2E, perf budgets, security + dependency scanning, observability, rate
  limits, feature flags, rollback procedure, runbook.

## 9. Session ritual (Claude Code)

```
# start of block
claude --permission-mode plan
> read CLAUDE.md and docs/STATE.md. where are we and what's next?

# start of milestone (Gate A)
> write the spec for ROADMAP milestone N to docs/specs/NNN-name.md using
> .claude/templates/SPEC.md. no implementation code.

# after approval
Shift+Tab to auto
> implement docs/specs/NNN-name.md. run the DoD. iterate until green.
> run the spec-reviewer. update docs/STATE.md. commit and open a PR with evidence.

# end of block
> update docs/STATE.md for someone returning in three weeks.
```

**Context hygiene (it is also the budget on Pro):** `/clear` between unrelated tasks · one session
per milestone, `/rename` it · name files, don't paste them · research via subagents ·
`/compact` deliberately · after two failed corrections, `/clear` and re-prompt.

## 10. Domain packs

The kernel above is domain-neutral. A **pack** adds what one kind of project needs, and nothing
else: `install.sh <level> <repo> <pack>`. A pack answers six questions — what is the artifact, what
is the unit of work, what can a machine check, what needs human taste, what is costly or
irreversible, what are the maturity rungs — and ships:

- `PACK.md` → installed as `.claude/PACK-<name>.md`, read before any milestone
- a short section appended to `CLAUDE.md` (the rules that must never be forgotten)
- its own `PRODUCT.md` / `ROADMAP.md` templates, which replace the kernel's
- any extra documents it declares (the only additions allowed to the closed set)
- extra permissions and network domains, merged into `.claude/settings.json`

**Where a pack is stricter than the kernel, the pack wins.** Packs available: `trading`.
