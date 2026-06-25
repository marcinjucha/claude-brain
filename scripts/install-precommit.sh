#!/usr/bin/env bash
# Install a pre-commit hook into a consuming repo that regenerates + stages knowledge snapshots
# and blocks the commit on a dangling reference. Idempotent.
#
# Usage: install-precommit.sh <repo-path> <context>
#   e.g. install-precommit.sh /Users/marcinjucha/Prywatne/projects/claude-marketing shadow-operator
set -euo pipefail

REPO="${1:?repo path required}"
CTX="${2:?context required}"
SCRIPT="/Users/marcinjucha/Prywatne/projects/claude-brain/scripts/sync-knowledge.py"
HOOKDIR="$REPO/.git/hooks"

[ -d "$REPO/.git" ] || { echo "✗ $REPO is not a git repo"; exit 1; }
mkdir -p "$HOOKDIR"
PRECOMMIT="$HOOKDIR/pre-commit"

# Guard: don't clobber an unrelated existing pre-commit
if [ -f "$PRECOMMIT" ] && ! grep -q "sync-knowledge.py" "$PRECOMMIT" 2>/dev/null; then
  echo "✗ $PRECOMMIT exists and is not ours — merge manually"; exit 1
fi

cat > "$PRECOMMIT" <<EOF
#!/usr/bin/env bash
# Auto-installed by claude-brain/scripts/install-precommit.sh — keeps knowledge snapshots fresh.
SCRIPT="$SCRIPT"
CTX="$CTX"
command -v python3 >/dev/null 2>&1 || exit 0
[ -f "\$SCRIPT" ] || exit 0
python3 "\$SCRIPT" --context "\$CTX"; code=\$?
if [ "\$code" -eq 2 ]; then
  echo "✗ knowledge-sync: dangling reference — fix the skill/note before committing." >&2
  exit 1
fi
# stage any regenerated snapshots so they land in this commit
git add -- skills/*/references/knowledge/ .claude/skills/*/references/knowledge/ 2>/dev/null || true
exit 0
EOF
chmod +x "$PRECOMMIT"
echo "✓ pre-commit installed → $PRECOMMIT (context: $CTX)"
