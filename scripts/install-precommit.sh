#!/usr/bin/env bash
# Install a pre-commit hook into a consuming repo that regenerates + stages knowledge snapshots
# and blocks the commit on a dangling reference. Idempotent.
#
# Usage: install-precommit.sh <repo-path> <context>
#   e.g. install-precommit.sh /Users/marcinjucha/Prywatne/projects/claude-marketing shadow-operator
set -euo pipefail

REPO="${1:?repo path required}"
CTX="${2:?context required}"
CFG="${3:-}"   # optional config.json override (testing); empty = engine's default
SCRIPT="/Users/marcinjucha/Prywatne/projects/claude-brain/scripts/sync-knowledge.py"

# Worktree-safe: in a git worktree `.git` is a FILE, not a dir, and hooks live in the common dir.
git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1 || { echo "✗ $REPO nie jest repo/worktree git"; exit 1; }
HOOKDIR="$(git -C "$REPO" rev-parse --git-path hooks 2>/dev/null)"
case "$HOOKDIR" in /*) ;; *) HOOKDIR="$REPO/$HOOKDIR" ;; esac
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
CFG="$CFG"
command -v python3 >/dev/null 2>&1 || exit 0
[ -f "\$SCRIPT" ] || exit 0
python3 "\$SCRIPT" --context "\$CTX" \${CFG:+--config "\$CFG"}; code=\$?
if [ "\$code" -eq 2 ]; then
  echo "✗ knowledge-sync: dangling reference — fix the skill/note before committing." >&2
  exit 1
fi
# stage any regenerated snapshots so they land in this commit.
# Per-glob with a -d guard: a non-matching pattern must NOT poison the whole add step
# (a single combined add of two pathspecs aborts and stages NOTHING if one does not match).
for p in skills/*/references/knowledge/ .claude/skills/*/references/knowledge/; do
  [ -d "\$p" ] && git add -- "\$p" 2>/dev/null || true
done
exit 0
EOF
chmod +x "$PRECOMMIT"
echo "✓ pre-commit installed → $PRECOMMIT (context: $CTX)"
