#!/usr/bin/env bash
# Symlink every brain artifact (command, skill, agent) into the global ~/.claude so it is
# available from ANY repo.
# Idempotent: re-creates only missing/wrong links, leaves correct ones, refuses to clobber a real file.
#
# Why: brain-* commands + the brain-conventions skill + the brain-manager agent live in
# claude-brain/.claude/{commands,skills,agents} but Claude Code discovers GLOBAL artifacts from
# ~/.claude/{commands,skills,agents}. New files were being created without the symlink, so they
# were invisible outside this repo (e.g. from the scandit repo). Run this after adding any of them.
#
# Usage: link-commands.sh [--dry-run]
set -euo pipefail

BASE="/Users/marcinjucha/Prywatne/projects/claude-brain/.claude"
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1

linked=0; ok=0; skipped=0

# link_item <src> <dst>: idempotent symlink; re-points a wrong symlink; refuses to clobber a real file.
link_item() {
  local src="$1" dst="$2" name; name="$(basename "$src")"
  if [ -L "$dst" ]; then
    if [ "$(readlink "$dst")" = "$src" ]; then ok=$((ok+1)); return; fi
    [ $DRY -eq 1 ] && { echo "  RE-LINK $name (→ $(readlink "$dst"))"; linked=$((linked+1)); return; }
    ln -sfn "$src" "$dst"; echo "  ↻ re-linked $name"; linked=$((linked+1))
  elif [ -e "$dst" ]; then
    echo "  ⚠ pominięto $name — istnieje ZWYKŁY plik/katalog w $(dirname "$dst") (nie nadpisuję)"; skipped=$((skipped+1))
  else
    [ $DRY -eq 1 ] && { echo "  LINK $name"; linked=$((linked+1)); return; }
    ln -s "$src" "$dst"; echo "  + $name"; linked=$((linked+1))
  fi
}

# link_group <src_dir> <dst_dir> <mode>: mode=files → *.md files; mode=dirs → immediate subdirs.
link_group() {
  local src_dir="$1" dst_dir="$2" mode="$3"
  [ -d "$src_dir" ] || { echo "  (brak $src_dir — pomijam)"; return; }
  mkdir -p "$dst_dir"
  if [ "$mode" = "files" ]; then
    for src in "$src_dir"/*.md; do
      [ -e "$src" ] || continue
      link_item "$src" "$dst_dir/$(basename "$src")"
    done
  else
    for src in "$src_dir"/*/; do
      [ -d "$src" ] || continue
      src="${src%/}"                         # strip trailing slash
      link_item "$src" "$dst_dir/$(basename "$src")"
    done
  fi
}

echo "commands:"; link_group "$BASE/commands" "$HOME/.claude/commands" files
echo "skills:";   link_group "$BASE/skills"   "$HOME/.claude/skills"   dirs
echo "agents:";   link_group "$BASE/agents"   "$HOME/.claude/agents"   files

echo "── $linked nowych/poprawionych · $ok już-OK · $skipped pominięto (zwykły plik)"
[ $DRY -eq 1 ] && echo "(dry-run — nic nie zmieniono)"
exit 0
