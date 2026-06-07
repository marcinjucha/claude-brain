---
description: Update the brain's project memory after working in a folder (status, done, connections)
argument-hint: [context] [note]
allowed-tools: Read, Edit, Write, Bash, Grep
---

# /brain-update — zapisz sesję do pamięci projektu

Po pracy w folderze aktualizuje **górny poziom** pamięci — plik projektu w vaulcie (status,
co zrobione, nowe połączenia). Para z `/brain-load`. Globalna.

Repo mózgu (config/ścieżki): `/Users/marcinjucha/Prywatne/projects/claude-brain`.

## Faza 0 — wykryj projekt
`pwd` → dopasuj do `config.json` → `paths` (najdłuższy prefiks). Ustal `<vault>` i `<memory>`.
Brak trafienia → użyj `$1` / zapytaj.

## Faza 1 — zbierz co się zmieniło
Z tej sesji/rozmowy + `git log` od ostatniej aktualizacji: co zrobione, jakie decyzje
(z WHY), nowe połączenia z innymi kontekstami, zmiany statusu zadań.

## Faza 2 — zaktualizuj pamięć projektu (górny poziom)
W `<vault>/<memory>` (np. `_scandit.md`): odśwież sekcje **Status**, **W toku**,
**Jak się łączy**. Ustaw `updated` na dziś. Zwięźle — to mapa, nie dziennik.
Jeśli plik nie istnieje → utwórz z analogicznej struktury co `_scandit.md`.

## Faza 3 — rozdziel poziomy (WAŻNE)
- **Górny (tu):** status, postęp, połączenia, wskaźniki "co dalej". → pamięć projektu w vaulcie.
- **Dolny (NIE tu):** głębokie lekcje techniczne, pułapki, reguły kodu. → repo, ścieżką:
  `/ai-extract-memory` (do `memory.md`, bufor sesji) → `/ai-curate-memory` (promocja do CLAUDE.md/skilli).
  Jeśli w sesji pojawiła się taka lekcja — **zasugeruj** użytkownikowi ten zapis, nie wpisuj jej
  do pamięci projektu w mózgu.

## Faza 4 — raport
Co zaktualizowano w pamięci projektu + ewentualne sugestie lekcji do repo `memory.md`.
