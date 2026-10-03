#!/usr/bin/env bash
# Stop hook — Definition of Done gate.
# Blocks Claude from ending its turn while:
#   1. any command in .claude/dod-commands fails, or
#   2. a new commit message signals unverified work (?, untested, try, maybe, idk, should work).
# Exit 2 = block (stderr is fed back to Claude). Exit 0 = allow.
# Skips work when nothing changed since the last passing check, so chat-only turns stay cheap.
# After 3 consecutive blocks it lets the turn end, and Claude must escalate to the human.

cat >/dev/null  # consume hook JSON on stdin (not needed)

ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$ROOT" || exit 0
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

GITDIR="$(git rev-parse --git-dir)"
PASS_FILE="$GITDIR/dod-last-pass"      # fingerprint of the last state that passed
HEAD_FILE="$GITDIR/dod-last-head"      # HEAD at the last pass (for commit-message range)
FAIL_FILE="$GITDIR/dod-fail-count"
MAX_BLOCKS=3

HEAD_SHA="$(git rev-parse -q --verify HEAD 2>/dev/null || echo none)"
FINGERPRINT="$( { echo "$HEAD_SHA"; git status --porcelain; git diff; } | cksum | cut -d' ' -f1 )"

if [ -f "$PASS_FILE" ] && [ "$(cat "$PASS_FILE")" = "$FINGERPRINT" ]; then
  exit 0   # nothing changed since the last green check
fi

FAILURES=""

# --- 1. Commit-message honesty check (new commits only) ---------------------------------
if [ "$HEAD_SHA" != "none" ]; then
  LAST_HEAD="$(cat "$HEAD_FILE" 2>/dev/null)"
  if [ -n "$LAST_HEAD" ] && git merge-base --is-ancestor "$LAST_HEAD" HEAD 2>/dev/null; then
    RANGE="$LAST_HEAD..HEAD"
  else
    RANGE="-n 1 HEAD"   # first run, or history was rewritten: check only the newest commit
  fi
  # shellcheck disable=SC2086
  BAD="$(git log --format='%h %s' $RANGE 2>/dev/null \
        | grep -Ei '\?|untested|(^|[^a-z])try([^a-z]|$)|(^|[^a-z])maybe([^a-z]|$)|(^|[^a-z])idk([^a-z]|$)|should work')"
  if [ -n "$BAD" ]; then
    FAILURES+=$'\n'"## Commit messages signal unverified work"$'\n'"$BAD"$'\n'
    FAILURES+="Verify the work, then amend/reword these commits (unpushed only), or use a 'wip:' commit that states exactly what is missing."$'\n'
  fi
fi

# --- 2. DoD commands -------------------------------------------------------------------
DOD_FILE="$ROOT/.claude/dod-commands"
if [ -f "$DOD_FILE" ]; then
  while IFS= read -r CMD || [ -n "$CMD" ]; do
    CMD="$(echo "$CMD" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    case "$CMD" in ""|"#"*) continue ;; esac            # whole-line comments only:
    # a '#' inside a command (a regex, a URL fragment) is part of the command, not a comment.
    OUT="$(bash -c "$CMD" 2>&1 </dev/null)"
    CODE=$?
    if [ $CODE -ne 0 ]; then
      FAILURES+=$'\n'"## FAILED (exit $CODE): $CMD"$'\n'"$(echo "$OUT" | tail -n 40)"$'\n'
    fi
  done < "$DOD_FILE"
fi

# --- Verdict ---------------------------------------------------------------------------
if [ -z "$FAILURES" ]; then
  echo "$FINGERPRINT" > "$PASS_FILE"
  echo "$HEAD_SHA" > "$HEAD_FILE"
  rm -f "$FAIL_FILE"
  exit 0
fi

COUNT=$(( $(cat "$FAIL_FILE" 2>/dev/null || echo 0) + 1 ))
echo "$COUNT" > "$FAIL_FILE"

if [ "$COUNT" -gt "$MAX_BLOCKS" ]; then
  rm -f "$FAIL_FILE"
  exit 0   # stop looping; Claude was told on the previous block to escalate
fi

{
  echo "Definition of Done is NOT met (block $COUNT of $MAX_BLOCKS). Do not end the turn yet."
  echo "$FAILURES"
  if [ "$COUNT" -ge "$MAX_BLOCKS" ]; then
    echo "This is the last block. If you cannot fix it now: stop, commit as 'wip:' on the branch,"
    echo "update docs/STATE.md, and escalate to the human — what fails, what you tried, 2-3 options, your recommendation."
  else
    echo "Fix the cause (not the check), re-run the failing command, and show the output as evidence."
  fi
} >&2
exit 2
