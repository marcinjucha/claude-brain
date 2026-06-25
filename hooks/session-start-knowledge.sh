#!/usr/bin/env bash
# SessionStart hook: keep the current context's skill knowledge snapshots in sync with the brain.
# Regenerates references/knowledge/ from the vault notes (one-way) when they've drifted.
# OFFLINE-SAFE, never fails a session. Companion to the brain context-injection hook.
set -uo pipefail
trap 'exit 0' ERR

CONFIG="/Users/marcinjucha/Prywatne/projects/claude-brain/config.json"
SCRIPT="/Users/marcinjucha/Prywatne/projects/claude-brain/scripts/sync-knowledge.py"

INPUT="$(cat 2>/dev/null || true)"
command -v jq >/dev/null 2>&1 || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
[ -f "$CONFIG" ] || exit 0
[ -f "$SCRIPT" ] || exit 0

CWD="$(printf '%s' "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)"
[ -n "$CWD" ] || CWD="$PWD"

# longest-prefix match cwd → context (same logic as the brain context hook)
MATCH=""
while IFS= read -r key; do
  [ -n "$key" ] || continue
  case "$CWD/" in
    "$key"/*|"$key"/) [ "${#key}" -gt "${#MATCH}" ] && MATCH="$key" ;;
  esac
done < <(jq -r '.paths | keys[]' "$CONFIG" 2>/dev/null)
[ -n "$MATCH" ] || exit 0

CTX="$(jq -r --arg k "$MATCH" '.paths[$k].context // empty' "$CONFIG" 2>/dev/null)"
[ -n "$CTX" ] || exit 0
# only sync contexts marked active in the knowledge config
ACTIVE="$(jq -r --arg c "$CTX" '.knowledge[$c].active // false' "$CONFIG" 2>/dev/null)"
[ "$ACTIVE" = "true" ] || exit 0

SUMMARY="$(python3 "$SCRIPT" --context "$CTX" --quiet 2>/dev/null || true)"
if [ -n "$SUMMARY" ]; then
  jq -n --arg c "knowledge-sync: $SUMMARY (źródło: brain → snapshot w references/)" \
    '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $c}}'
fi
exit 0
