#!/usr/bin/env bash
# Register the knowledge-sync SessionStart hook into ~/.claude/settings.json (idempotent).
# Mirrors hooks/install.sh (the brain context hook installer).
set -euo pipefail

HOOK="/Users/marcinjucha/Prywatne/projects/claude-brain/hooks/session-start-knowledge.sh"
SETTINGS="${HOME}/.claude/settings.json"

command -v jq >/dev/null 2>&1 || { echo "jq required"; exit 1; }
chmod +x "$HOOK" 2>/dev/null || true
[ -f "$SETTINGS" ] || { echo "no $SETTINGS"; exit 1; }

if jq -e --arg cmd "$HOOK" 'any(.hooks.SessionStart[]?.hooks[]?; .command == $cmd)' "$SETTINGS" >/dev/null 2>&1; then
  echo "✓ knowledge SessionStart hook already registered"
  exit 0
fi

cp "$SETTINGS" "$SETTINGS.bak"
jq --arg cmd "$HOOK" '
  .hooks //= {} |
  .hooks.SessionStart //= [] |
  .hooks.SessionStart += [{ "hooks": [ { "type": "command", "command": $cmd } ] }]
' "$SETTINGS.bak" > "$SETTINGS"
echo "✓ registered knowledge SessionStart hook → $HOOK (backup: $SETTINGS.bak)"
