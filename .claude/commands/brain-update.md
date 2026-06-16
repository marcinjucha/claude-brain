---
description: Update the brain's project memory after working in a folder (status, done, connections)
argument-hint: [context] [note]
allowed-tools: Read, Edit, Write, Bash, Grep
---

# /brain-update — zapisz sesję do pamięci projektu

Po pracy w folderze aktualizuje **górny poziom** pamięci — plik projektu w vaulcie (status,
co zrobione, nowe połączenia). Para z `/brain-load`. Globalna.

Repo mózgu (config/ścieżki): `/Users/marcinjucha/Prywatne/projects/claude-brain`.

## Faza 0 — wykryj projekt + ticket
`pwd` → dopasuj do `config.json` → `paths` (najdłuższy prefiks). Ustal `<vault>` i `<memory>`.
Brak trafienia → użyj `$1` / zapytaj. Ticket z gałęzi (jeśli kontekst JIRA):
`git -C <cwd> branch --show-current` → regex `SHELF-[0-9]+` (jeden z możliwych kluczy
notatki w Fazie 2b; kontekst Notion używa klucza encji).

## Faza 1 — zbierz co się zmieniło (źródło: TA sesja/konwersacja + dodatki)
**Główne źródło: ta sesja/konwersacja** — uniwersalne, działa wszędzie (np. dla Notion/marketingu
nie ma SESSION.md, a praca żyje w rozmowie: „przeanalizowałem Call 2 Kacpra, oto decyzje").
Z niej wyciągnij: co zrobione, decyzje (z WHY), dead-endy, otwarte pytania, „co dalej",
dotknięte pliki/encje, zmiany statusu. Dodatkowo: **+ SESSION.md jeśli istnieje** (bonus dla
iOS worktree — ulotny scratchpad gałęzi) **+ `git log` od ostatniej aktualizacji** (wsparcie).
SESSION.md NIE jest wymagany. **Tylko jednokierunkowo: sesja → mózg.** NIGDY nie zapisuj
z powrotem do SESSION.md (pozostaje pasywny — „sesja nie wie o mózgu").
Daty względne (np. „wczoraj", „dziś") zamień na bezwzględne (`YYYY-MM-DD`).

## Faza 2a — pamięć projektu / wysoka półka (status + połączenia)
W `<vault>/<memory>` (np. `_scandit.md`): odśwież sekcje **Status**, **W toku**,
**Jak się łączy**. Ustaw `updated` na dziś. Zwięźle — to mapa, nie dziennik.
Jeśli plik nie istnieje → utwórz z analogicznej struktury co `_scandit.md`.
Tu idzie TYLKO wysoki poziom (status/postęp/połączenia), NIE detal techniczny.

## Faza 2b — notatka robocza / working detail (detal z sesji)
Roboczy detal z sesji (decyzje, dead-endy, „co dalej", dotknięte pliki/encje) wpłyń do
**notatki roboczej**. Jednostka notatki: per-TICKET dla kontekstów JIRA, per-ENCJA
(klient/twórca/prospect) dla kontekstów Notion.

**Ustal klucz notatki (target):**
- Da się wywieść ticket z gałęzi (`SHELF-[0-9]+`) → target `<vault>/<TICKET>*.md`.
- W przeciwnym razie (Notion/inny kontekst) → target notatki **encji, nad którą pracowano**
  (twórca/prospect/klient). Rozwiąż z: jawnego argumentu `$2` jeśli podany; inaczej wywnioskuj
  z konwersacji (która encja była w centrum); inaczej dopasuj istniejącą notatkę w `<vault>`
  po nazwie. (np. praca nad Kacprem → `kacper-snela.md`.)

**Zapisz detal:**
- Notatka istnieje → dopisz/zaktualizuj sekcje **Detal techniczny / jak to robimy** i
  **Decyzje i pytania otwarte**. `updated`=dziś.
- Notatka nie istnieje, ale encja/ticket jednoznacznie zidentyfikowane → utwórz z
  `_system/templates/working-note.md` (frontmatter jak w `/brain-load` Faza 2.5), wypełnij
  detalem i **zaznacz w raporcie, że powstała nowa notatka**.
- Target niejednoznaczny / nie da się ustalić → **NIE zgaduj i nie twórz złej notatki**:
  zaktualizuj TYLKO wysoką półkę (Faza 2a) i napisz w raporcie, że working detail nie został
  zrzucony (brak jasnego targetu).
- Daty bezwzględne. Dalej jednokierunkowo — do SESSION.md nic nie wraca.

## Faza 3 — rozdziel poziomy (WAŻNE)
- **Wysoka półka (Faza 2a):** status, postęp, połączenia, „co dalej". → pamięć projektu `<memory>`.
- **Working detail (Faza 2b):** decyzje, dead-endy, dotknięte pliki, proces. → notatka robocza
  (ticketu dla JIRA / encji dla Notion).
- **Trwałe lekcje repo (NIE tu):** reguły kodu, pułapki architektury. → ścieżką
  `/ai-extract-memory` (do `memory.md`, bufor sesji) → `/ai-curate-memory` (promocja do CLAUDE.md/skilli).
  Jeśli w sesji pojawiła się taka lekcja — **zasugeruj** użytkownikowi ten zapis, nie wpisuj jej do mózgu.

## Faza 4 — raport
Co zaktualizowano: (a) pamięć projektu (`<memory>` — status/połączenia), (b) notatka robocza
(ticketu lub encji — detal; zaznacz jeśli powstała nowa LUB jeśli detalu nie zrzucono przez
niejednoznaczny target) + ewentualne sugestie lekcji do repo `memory.md`. SESSION.md nietknięty.
