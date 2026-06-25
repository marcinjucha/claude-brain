#!/usr/bin/env bash
# Onboard a context to the knowledge-system (plumbing, deterministic):
#   1) create the vault knowledge dir + a starter _MOC.md
#   2) flip the context to active:true in config.json
#   3) install the pre-commit hook in each consumer repo
# Idempotent. The per-skill MIGRATION (extract knowledge → notes → thin the skill) is separate
# CONTENT work — see _system/knowledge-system.md for the contract.
#
# Usage: knowledge-init.sh <context>      e.g.  knowledge-init.sh scandit
set -euo pipefail

CTX="${1:?podaj kontekst, np: knowledge-init.sh scandit}"
BRAIN="/Users/marcinjucha/Prywatne/projects/claude-brain"
CONFIG="$BRAIN/config.json"
command -v jq >/dev/null 2>&1 || { echo "jq wymagane"; exit 1; }

# context must already be registered in config.knowledge
jq -e --arg c "$CTX" '.knowledge[$c]' "$CONFIG" >/dev/null 2>&1 || {
  echo "✗ kontekst '$CTX' nie jest w config.json .knowledge."
  echo "  Dodaj najpierw wpis: \"$CTX\": { \"dir\": \"03-Resources/$CTX/knowledge\", \"active\": false, \"consumers\": [\"<repo>/.claude/skills\"] }"
  exit 1
}

VAULT="$(jq -r '.vault.path' "$CONFIG")"
DIR="$(jq -r --arg c "$CTX" '.knowledge[$c].dir' "$CONFIG")"
KDIR="$VAULT/$DIR"
TODAY="$(date +%F)"

# 1) vault knowledge dir + starter MOC ---------------------------------------
mkdir -p "$KDIR"
MOC="$KDIR/_MOC.md"
if [ ! -f "$MOC" ]; then
  cat > "$MOC" <<EOF
---
type: moc
context: $CTX
title: MOC — Wiedza ($CTX)
updated: $TODAY
tags: [moc, knowledge, $CTX]
---

# 🗺️ MOC — Wiedza ($CTX)

> Mapa treści = punkt wejścia do wiedzy domenowej. Kontrakt: [[knowledge-system]] (\`_system/\`).
> Mózg = źródło; skille dostają snapshot do \`references/knowledge/\` przez \`sync-knowledge.py\`.

## (grupuj notatki po obszarze)

## Status notatek
- (brak — dodaj pierwsze notatki)
EOF
  echo "✓ utworzono $MOC"
else
  echo "· MOC już istnieje: $MOC"
fi

# 2) activate in config ------------------------------------------------------
if [ "$(jq -r --arg c "$CTX" '.knowledge[$c].active' "$CONFIG")" != "true" ]; then
  cp "$CONFIG" "$CONFIG.bak"
  jq --arg c "$CTX" '.knowledge[$c].active = true' "$CONFIG.bak" > "$CONFIG"
  echo "✓ aktywowano '$CTX' w config (backup: config.json.bak)"
else
  echo "· '$CTX' już aktywny w config"
fi

# 3) install pre-commit in each consumer repo --------------------------------
while IFS= read -r consumer; do
  [ -n "$consumer" ] || continue
  if [ ! -d "$consumer" ]; then echo "⚠ konsument nie istnieje: $consumer (pomijam)"; continue; fi
  root="$(git -C "$consumer" rev-parse --show-toplevel 2>/dev/null || true)"
  if [ -z "$root" ]; then echo "⚠ $consumer poza repo git (pomijam pre-commit)"; continue; fi
  bash "$BRAIN/scripts/install-precommit.sh" "$root" "$CTX" \
    || echo "⚠ pre-commit nie zainstalowany w $root — zmerguj ręcznie (istnieje już inny hook?)"
done < <(jq -r --arg c "$CTX" '.knowledge[$c].consumers[]?' "$CONFIG")

cat <<EOF

✅ Plumbing gotowy dla '$CTX'. Dalej (treść, per skill):
  1) napisz notatki wiedzy w: $KDIR
     (atomowe, tytuł=teza, wg _system/knowledge-system.md)
  2) w skillach tego kontekstu dodaj blok '## Knowledge' + wskaźniki @references/knowledge/<slug>.md
  3) sync zadzieje się sam (SessionStart + pre-commit); ręcznie:
     python3 $BRAIN/scripts/sync-knowledge.py --context $CTX
EOF
