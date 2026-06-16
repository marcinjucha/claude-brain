#!/usr/bin/env bash
# Register the brain SessionStart hook into ~/.claude/settings.json.
# Idempotent: re-running never duplicates the entry. Merges into existing settings
# (other hooks/keys preserved). Resolves the hook path from this script's location,
# so it works wherever claude-brain is cloned.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$SCRIPT_DIR/session-start-brain.sh"
SETTINGS="${HOME}/.claude/settings.json"

command -v jq >/dev/null 2>&1 || { echo "✗ jq required"; exit 1; }
[ -f "$HOOK" ] || { echo "✗ hook not found: $HOOK"; exit 1; }
chmod +x "$HOOK"

mkdir -p "$(dirname "$SETTINGS")"
[ -f "$SETTINGS" ] || echo '{}' > "$SETTINGS"
jq empty "$SETTINGS" 2>/dev/null || { echo "✗ $SETTINGS is not valid JSON"; exit 1; }

if jq -e --arg cmd "$HOOK" 'any(.hooks.SessionStart[]?.hooks[]?; .command == $cmd)' "$SETTINGS" >/dev/null 2>&1; then
  echo "✓ already registered: $HOOK"
  exit 0
fi

cp "$SETTINGS" "$SETTINGS.bak"
TMP="$(mktemp)"
jq --arg cmd "$HOOK" '
  .hooks //= {} |
  .hooks.SessionStart //= [] |
  .hooks.SessionStart += [{ "hooks": [ { "type": "command", "command": $cmd } ] }]
' "$SETTINGS" > "$TMP"
jq empty "$TMP" 2>/dev/null || { echo "✗ produced invalid JSON, aborting (backup: $SETTINGS.bak)"; rm -f "$TMP"; exit 1; }
mv "$TMP" "$SETTINGS"
echo "✓ registered SessionStart hook → $HOOK (backup: $SETTINGS.bak)"
