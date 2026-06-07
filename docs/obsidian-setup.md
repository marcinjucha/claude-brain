# Obsidian — setup (żywy + klikalny dashboard)

Pluginy instalujesz w Obsidianie: Settings → Community plugins → Browse. Z terminala się nie da.

## 1. Dataview (wymagany) — żywy dashboard
Install + Enable **Dataview**. Po włączeniu listy w `Home.md` i `_social-board.md`
wypełniają się same (zapytania o `type: working-note`, `project-memory`, `content`).
Nic więcej nie trzeba — to czyni dashboard żywym.

## 2. Klik → Claude w terminalu (opcjonalne)
Natywny link Obsidiana tylko nawiguje. Żeby **klik odpalał komendę `/brain-*`**, trzeba mostu:

Zainstaluj **Shell commands** + **Buttons**.

### a) Shell commands — zdefiniuj polecenia
Settings → Shell commands → New. Dodaj (podmień ścieżkę do `claude` jeśli inna):

```
# nazwa: brain-pull-social
cd "/Users/marcinjucha/Prywatne/projects/claude-brain" && /Users/marcinjucha/.nvm/versions/node/v23.7.0/bin/claude -p "/brain-pull social-media"
```
```
# nazwa: brain-digest
cd "/Users/marcinjucha/Prywatne/projects/claude-brain" && claude -p "/brain-digest"
```

Ustaw "Output channel" na Notification, żeby widzieć wynik w Obsidianie.

### b) Buttons — przycisk w notatce
W `Home.md` wstaw (działa po włączeniu Buttons):

````
```button
name ⬇️ Pull social-media
type command
action Shell commands: Execute: brain-pull-social
```
````

### Caveaty (uczciwie)
- **Headless (`claude -p`) działa dla operacji „do środka"** — pull, digest, load. Zweryfikuj raz,
  czy Twoja wersja Claude Code wykonuje slash-komendy w `-p` (jeśli nie: `claude -p "wykonaj /brain-pull social-media"`).
- **Publish/Update są interaktywne** (wymagają potwierdzenia) — nie odpalaj ich headless z przycisku.
  Dla nich zrób przycisk otwierający Terminal:
  ```
  osascript -e 'tell application "Terminal" to do script "cd /Users/marcinjucha/Prywatne/projects/claude-brain && claude"'
  ```
- Na **komórce** Shell commands nie zadziała (brak terminala) — tam dashboard jest do *czytania*;
  komendy odpalasz z laptopa.

## 3. (Opcjonalnie) Kanban plugin
Jeśli wolisz przeciągać karty contentu zamiast list Dataview — plugin **Kanban** na folderze
`01-Projects/agency/social-media/`. Dataview board (`_social-board.md`) i Kanban mogą współistnieć.
