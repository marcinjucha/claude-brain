#!/usr/bin/env bash
# Wrapper dla launchd: ładuje .env i odpala poller Telegrama.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
set -a
[ -f .env ] && . ./.env
set +a
# nvm node nie jest w PATH launchd — dopisz katalog node (zaktualizuj przy zmianie wersji node)
export PATH="/Users/marcinjucha/.nvm/versions/node/v23.7.0/bin:$PATH"
exec node connectors/telegram/capture.mjs
