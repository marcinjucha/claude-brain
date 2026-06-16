#!/usr/bin/env bash
# SessionStart hook: inject brain context (project memory + worktree SESSION.md) when cwd
# maps to a claude-brain context. READ-ONLY, OFFLINE-SAFE (no network/JIRA), never fails a session.
# Reads cwd from SessionStart hook JSON on stdin; emits additionalContext via hookSpecificOutput.
# Companion to /brain-load (which does the network-backed full orient + ticket backfill).
set -uo pipefail

# Never let an error abort the session: any failure path -> exit 0 silently.
fail_silent() { exit 0; }
trap fail_silent ERR

CONFIG="/Users/marcinjucha/Prywatne/projects/claude-brain/config.json"

# --- read stdin (hook JSON) -------------------------------------------------
INPUT="$(cat 2>/dev/null || true)"
command -v jq >/dev/null 2>&1 || exit 0
[ -f "$CONFIG" ] || exit 0

CWD="$(printf '%s' "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)"
[ -n "$CWD" ] || CWD="$PWD"
[ -d "$CWD" ] || exit 0

# --- longest-prefix match cwd against config .paths keys --------------------
VAULT_PATH="$(jq -r '.vault.path // empty' "$CONFIG" 2>/dev/null)"
[ -n "$VAULT_PATH" ] || exit 0

MATCH_PREFIX=""
while IFS= read -r key; do
  [ -n "$key" ] || continue
  case "$CWD/" in
    "$key"/*|"$key"/)
      if [ "${#key}" -gt "${#MATCH_PREFIX}" ]; then MATCH_PREFIX="$key"; fi ;;
  esac
done < <(jq -r '.paths | keys[]' "$CONFIG" 2>/dev/null)

# --- locate worktree SESSION.md: search cwd, walk up to matched prefix ------
find_session_md() {
  local dir="$1" stop="$2"
  while :; do
    [ -f "$dir/SESSION.md" ] && { printf '%s' "$dir/SESSION.md"; return 0; }
    [ -n "$stop" ] && [ "$dir" = "$stop" ] && break
    local parent; parent="$(dirname "$dir")"
    [ "$parent" = "$dir" ] && break
    dir="$parent"
  done
  return 1
}

# --- emit additionalContext via SessionStart hook output schema -------------
emit() {
  jq -n --arg ctx "$1" \
    '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $ctx}}'
}

# === NO MATCH: optionally surface SESSION.md, else exit silently ============
if [ -z "$MATCH_PREFIX" ]; then
  SESSION_FILE="$(find_session_md "$CWD" "" || true)"
  if [ -n "${SESSION_FILE:-}" ] && [ -f "$SESSION_FILE" ]; then
    emit "$(printf '## Worktree SESSION.md (%s)\n\n%s' "$SESSION_FILE" "$(cat "$SESSION_FILE")")"
  fi
  exit 0
fi

# === MATCH: assemble brain context ==========================================
CONTEXT="$(jq -r --arg k "$MATCH_PREFIX" '.paths[$k].context // empty' "$CONFIG" 2>/dev/null)"
VAULT_SUB="$(jq -r --arg k "$MATCH_PREFIX" '.paths[$k].vault // empty' "$CONFIG" 2>/dev/null)"
MEMORY="$(jq -r --arg k "$MATCH_PREFIX" '.paths[$k].memory // empty' "$CONFIG" 2>/dev/null)"
MEMORY_FILE="$VAULT_PATH/$VAULT_SUB/$MEMORY"

OUT=""
append() { OUT="${OUT}${1}"$'\n'; }

append "# Brain context loaded (read-only) — context: ${CONTEXT:-unknown}"
append ""

# high-shelf project memory (_scandit.md etc.)
if [ -n "$MEMORY" ] && [ -f "$MEMORY_FILE" ]; then
  append "## Brain project memory ($MEMORY_FILE)"
  append ""
  append "$(cat "$MEMORY_FILE" 2>/dev/null)"
  append ""
else
  append "## Brain project memory"
  append "(not found at $MEMORY_FILE — run /brain-load)"
  append ""
fi

# worktree SESSION.md (cwd up to the matched repo prefix)
SESSION_FILE="$(find_session_md "$CWD" "$MATCH_PREFIX" || true)"
if [ -n "${SESSION_FILE:-}" ] && [ -f "$SESSION_FILE" ]; then
  append "## Worktree SESSION.md ($SESSION_FILE)"
  append ""
  append "$(cat "$SESSION_FILE" 2>/dev/null)"
  append ""
fi

# infer current ticket from branch; check for a working-note in the vault
TICKET=""
if command -v git >/dev/null 2>&1; then
  BRANCH="$(git -C "$CWD" branch --show-current 2>/dev/null || true)"
  TICKET="$(printf '%s' "$BRANCH" | grep -oiE 'SHELF-[0-9]+' | head -1 || true)"
fi

NOTE_MISSING=0
if [ -n "$TICKET" ]; then
  # working-note convention: 01-Projects/work/<TICKET>*.md
  if ! ls "$VAULT_PATH/$VAULT_SUB/$TICKET"*.md >/dev/null 2>&1; then
    NOTE_MISSING=1
  fi
fi

# REMINDER — always present; explicit if the current ticket's note is missing.
append "---"
if [ -n "$TICKET" ] && [ "$NOTE_MISSING" -eq 1 ]; then
  append "REMINDER: brain context is available above. No working-note for $TICKET in the vault — run /brain-load to backfill it and fully orient."
elif [ -n "$TICKET" ]; then
  append "REMINDER: brain context is available above ($TICKET has a working-note). Run /brain-load for the full orient."
else
  append "REMINDER: brain context is available above. Run /brain-load for the full orient."
fi

emit "$OUT"
exit 0
