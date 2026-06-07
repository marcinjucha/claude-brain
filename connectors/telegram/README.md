# Telegram capture

Bot Telegram → zapisuje każdą wiadomość jako notatkę markdown w `00-Inbox` vaultu.
Lekki poller w Node (zero zależności, bez n8n). Tekst i podpisy zdjęć trafiają do treści;
załączniki (zdjęcia/pliki/voice) na razie tylko oznaczane do ręcznego dograania.

## Setup (jednorazowo)

1. **Utwórz bota.** W Telegramie napisz do [@BotFather](https://t.me/BotFather) → `/newbot`
   → nadaj nazwę → dostaniesz **token** (`123456:ABC-...`).

2. **Poznaj swoje chat_id** (do allowlisty). Napisz cokolwiek do swojego nowego bota, potem:
   ```bash
   curl -s "https://api.telegram.org/bot<TOKEN>/getUpdates" | grep -o '"chat":{"id":[0-9-]*'
   ```
   Zapisz liczbę po `"id":`.

3. **Ustaw zmienne środowiskowe** (skopiuj `.env.example` → `.env` i uzupełnij, albo eksportuj):
   ```bash
   export TELEGRAM_BOT_TOKEN="123456:ABC-..."
   export TELEGRAM_ALLOWED_CHATS="<twoje_chat_id>"   # CSV; puste = każdy (NIEzalecane)
   ```

4. **Uruchom:**
   ```bash
   node connectors/telegram/capture.mjs
   ```
   Wyślij wiadomość do bota → powinna pojawić się jako plik w `00-Inbox`, a bot odpowie `✅ Zapisane`.

## Format zapisanej notatki

```markdown
---
source: telegram
captured: 2026-06-07T14:32:00.000Z
from: "Marcin"
chat_id: 123456789
message_id: 42
status: inbox
tags: [inbox, telegram]
---

treść wiadomości
```

`status: inbox` + tag `inbox` ułatwiają późniejszą klasyfikację do PARA przez Claude Code.

## Uruchamianie w tle (launchd — zainstalowane)

Agent `com.mjucha.brain.telegram` jest zainstalowany w `~/Library/LaunchAgents/`
(autostart przy logowaniu + restart przy padzie). Źródło: `scripts/`.

```bash
# status
launchctl list | grep brain
# logi
tail -f /tmp/brain-telegram.log /tmp/brain-telegram.err.log
# restart po zmianie kodu/.env
launchctl unload ~/Library/LaunchAgents/com.mjucha.brain.telegram.plist
launchctl load   ~/Library/LaunchAgents/com.mjucha.brain.telegram.plist
# wyłączenie na stałe
launchctl unload ~/Library/LaunchAgents/com.mjucha.brain.telegram.plist
rm ~/Library/LaunchAgents/com.mjucha.brain.telegram.plist
```

> Po zmianie wersji node (nvm) zaktualizuj ścieżkę PATH w `scripts/run-telegram-capture.sh`.

Alternatywa na później: workflow n8n z Telegram Trigger → zapis pliku (gdy postawisz n8n).

## Stan

Offset przetworzonych wiadomości trzymany w `.state.json` (gitignored) — restart nie duplikuje notatek.
