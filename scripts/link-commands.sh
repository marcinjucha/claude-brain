#!/usr/bin/env bash
# Symlink every brain command into the global ~/.claude/commands so it is available from ANY repo.
# Idempotent: re-creates only missing/wrong links, leaves correct ones, refuses to clobber a real file.
#
# Why: brain-* commands live in claude-brain/.claude/commands but Claude Code discovers global
# commands from ~/.claude/commands. New command files were being created without the symlink, so
# they were invisible outside this repo (e.g. from the scandit repo). Run this after adding a command.
#
# Usage: link-commands.sh [--dry-run]
set -euo pipefail

SRC_DIR="/Users/marcinjucha/Prywatne/projects/claude-brain/.claude/commands"
DST_DIR="$HOME/.claude/commands"
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1

[ -d "$SRC_DIR" ] || { echo "✗ brak $SRC_DIR"; exit 1; }
mkdir -p "$DST_DIR"

linked=0; ok=0; skipped=0
for src in "$SRC_DIR"/*.md; do
  [ -e "$src" ] || continue
  name="$(basename "$src")"
  dst="$DST_DIR/$name"
  if [ -L "$dst" ]; then
    if [ "$(readlink "$dst")" = "$src" ]; then ok=$((ok+1)); continue; fi
    # symlink pointing elsewhere → re-point
    [ $DRY -eq 1 ] && { echo "  RE-LINK $name (→ $(readlink "$dst"))"; linked=$((linked+1)); continue; }
    ln -sf "$src" "$dst"; echo "  ↻ re-linked $name"; linked=$((linked+1))
  elif [ -e "$dst" ]; then
    echo "  ⚠ pominięto $name — istnieje ZWYKŁY plik w $DST_DIR (nie nadpisuję)"; skipped=$((skipped+1))
  else
    [ $DRY -eq 1 ] && { echo "  LINK $name"; linked=$((linked+1)); continue; }
    ln -s "$src" "$dst"; echo "  + $name"; linked=$((linked+1))
  fi
done

echo "── $linked nowych/poprawionych · $ok już-OK · $skipped pominięto (zwykły plik)"
[ $DRY -eq 1 ] && echo "(dry-run — nic nie zmieniono)"
exit 0
