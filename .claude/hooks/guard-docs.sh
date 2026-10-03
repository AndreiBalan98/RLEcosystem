#!/usr/bin/env bash
# PreToolUse hook (Write) — enforces the closed document set.
# Blocks creation of any NEW markdown file outside the allowed set. Editing existing files is fine.
# Exit 2 = block (stderr is fed back to Claude).

INPUT="$(cat)"
ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"

if command -v python3 >/dev/null 2>&1; then
  FILE="$(printf '%s' "$INPUT" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))' 2>/dev/null)"
elif command -v jq >/dev/null 2>&1; then
  FILE="$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty')"
else
  FILE="$(printf '%s' "$INPUT" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
fi

[ -z "$FILE" ] && exit 0
case "$FILE" in *.md|*.MD|*.markdown) ;; *) exit 0 ;; esac
[ -e "$FILE" ] && exit 0                     # editing an existing file is allowed

REL="${FILE#"$ROOT"/}"
case "$REL" in
  CLAUDE.md|README.md) exit 0 ;;
  docs/PRODUCT.md|docs/CONSTITUTION.md|docs/ROADMAP.md|docs/STATE.md|docs/RESEARCH-LOG.md|docs/LITERATURE.md) exit 0 ;;
  docs/specs/[0-9][0-9][0-9]-*.md) exit 0 ;;
  docs/experiments/[0-9][0-9][0-9]-*.md) exit 0 ;;
  docs/decisions/ADR-[0-9][0-9][0-9]*.md) exit 0 ;;
  .claude/*|sessions/*) exit 0 ;;
  /*) exit 0 ;;                              # outside the project (e.g. scratch dirs) — not our concern
esac

cat >&2 <<EOF
Blocked: '$REL' is outside the closed document set (docs/CONSTITUTION.md §1).
Do not create summaries, guides, reports or quick-starts. Put the content in docs/STATE.md or the
current spec instead. If a new document is truly needed, stop and ask the Product Owner.
Allowed: CLAUDE.md, README.md, docs/{PRODUCT,CONSTITUTION,ROADMAP,STATE,RESEARCH-LOG,LITERATURE}.md,
docs/specs/NNN-name.md, docs/experiments/NNN-name.md, docs/decisions/ADR-NNN-name.md,
.claude/*, sessions/*
EOF
exit 2
