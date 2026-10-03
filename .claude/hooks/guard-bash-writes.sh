#!/usr/bin/env bash
# PreToolUse hook (Bash) — closes the two holes the QuizBot run exposed:
#   1. `cat > docs/FOO.md <<EOF` bypasses the closed-document-set guard, because that guard only
#      sees the Write tool.
#   2. `cat > existing-file` silently replaces a file nobody read first (this destroyed two thirds
#      of .gitignore in the QuizBot run).
# Exit 2 = block (stderr is fed back to Claude).

INPUT="$(cat)"
ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"

if command -v python3 >/dev/null 2>&1; then
  CMD="$(printf '%s' "$INPUT" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("tool_input",{}).get("command",""))' 2>/dev/null)"
elif command -v jq >/dev/null 2>&1; then
  CMD="$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')"
else
  exit 0
fi
[ -z "$CMD" ] && exit 0

# Every truncating redirect target: `> path` and `tee path` (not `>>`, not `2>`, not `>&`).
TARGETS="$(printf '%s\n' "$CMD" \
  | grep -oE '(^|[^0-9>&])>[[:space:]]*[^|&;><[:space:]]+|(^|[[:space:]])tee[[:space:]]+[^|&;><[:space:]]+' \
  | sed -E 's/.*(>|tee)[[:space:]]*//' )"
[ -z "$TARGETS" ] && exit 0

cd "$ROOT" 2>/dev/null || exit 0

for T in $TARGETS; do
  case "$T" in
    /dev/null|/tmp/*|/var/tmp/*|*/scratchpad/*|.git/*|"$ROOT"/.git/*) continue ;;
  esac
  REL="${T#"$ROOT"/}"
  case "$REL" in /*) continue ;; esac      # outside the project

  # 1. new markdown outside the closed document set
  case "$REL" in
    *.md|*.MD|*.markdown)
      if [ ! -e "$REL" ]; then
        case "$REL" in
          CLAUDE.md|README.md|docs/PRODUCT.md|docs/CONSTITUTION.md|docs/ROADMAP.md|docs/STATE.md|docs/RESEARCH-LOG.md|docs/LITERATURE.md) ;;
          docs/specs/[0-9][0-9][0-9]-*.md|docs/experiments/[0-9][0-9][0-9]-*.md) ;;
          docs/decisions/ADR-[0-9][0-9][0-9]*.md|.claude/*|sessions/*) ;;
          *)
            echo "Blocked: '$REL' is outside the closed document set (docs/CONSTITUTION.md 1)." >&2
            echo "Writing it through the shell does not make it allowed. Put the content in docs/STATE.md" >&2
            echo "or the current spec, or stop and ask the Product Owner." >&2
            exit 2 ;;
        esac
      fi ;;
  esac

  # 2. truncating an existing file through the shell
  if [ -f "$REL" ]; then
    echo "Blocked: '> $REL' would replace a file that already exists." >&2
    echo "Use the Edit tool for a change, or Write after reading the file — a heredoc rewrite drops" >&2
    echo "whatever you did not retype (this is how .gitignore lost two thirds of its entries)." >&2
    echo "Appending with '>>' is fine." >&2
    exit 2
  fi
done
exit 0
