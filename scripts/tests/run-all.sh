#!/usr/bin/env bash
# Regression suite for the knowledge-system (engine + pre-commit e2e). Run after any change to
# sync-knowledge.py / install-precommit.sh / hooks. Exits nonzero if any sub-suite fails.
set -uo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
rc=0
echo "######## ENGINE ########"; bash "$DIR/test-engine.sh" || rc=1
echo; echo "######## PRE-COMMIT E2E ########"; bash "$DIR/test-precommit-e2e.sh" || rc=1
echo; [ $rc -eq 0 ] && echo "✅✅ WSZYSTKO ZIELONE" || echo "❌ są błędy"
exit $rc
