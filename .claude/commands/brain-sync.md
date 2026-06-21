---
description: Periodic brain audit — consolidate/clean/organize a context's vault (propose-then-confirm), regenerate the status layer (Home rollup + per-context + hubs), and report tracker→Brain (Notion/JIRA) migration gaps
argument-hint: [context] [--all|--status|--gap]
allowed-tools: Read, Edit, Write, Bash, Grep, mcp__notion__notion-fetch, mcp__notion__notion-search, mcp__claude_ai_Atlassian__searchJiraIssuesUsingJql
---

# /brain-sync — utrzymanie i optymalizacja mózgu

Okresowy audyt kontekstu w vaulcie: konsoliduje, czyści, lepiej organizuje, ODŚWIEŻA warstwę statusu
(`Home.md` rollup + `_<context>.md` + huby) i wskazuje luki tracker→Brain (Notion/JIRA). Para z `/brain-update`.
**Podział po osi czasu: brain-update = event-driven, wąski (po sesji); brain-sync = periodic-audit,
pełny przelicz.** Globalna. Repo (config/ścieżki): `/Users/marcinjucha/Prywatne/projects/claude-brain`.

## Domyślnie READ-ONLY + propose-then-confirm
brain-sync **najpierw raportuje plan, nie dotyka plików.** Jedna bramka zgody na całą partię (możesz
odznaczyć pozycje). Operacje nieodwracalne (usunięcie / scalenie / rename / przeniesienie) — ZAWSZE
pozycja-po-pozycji. **`rm` NIGDY** — „usuń" = przenieś do `04-Archive/` (wbudowany undo; vault to iCloud,
nie git).

### Strefy NIGDY-nie-rusza (auto)
- `SESSION.md` — jednokierunkowo (sesja→mózg), jak w brain-update. Nigdy nie zapisuj.
- Datowane wpisy `### YYYY-MM-DD` (sekcje Detal/Log) — wolno tylko **dopisać** „(superseded → X)", nie
  edytować treści wpisu. Nie przepisuj historii.
- Pliki-archiwa: nazwa `*-notion-archive`, ścieżka `04-Archive/*`, frontmatter `type: archive`.
- Jawne warianty (nagłówki „wariant/alternatywny", np. twarda vs złagodzona umowa) — near-duplicate
  to FLAGA do przeglądu, NIGDY auto-merge.

## Faza 0 — wykryj kontekst + zakres
`pwd` → `config.json` → `paths` (najdłuższy prefiks) → `<context>` + obszar vaultu. Brak trafienia →
użyj `$1` / zapytaj. Tryby (z `$2`):
- brak → bieżący kontekst + pełny audyt;
- `--all` → wszystkie konteksty, ale RAPORT zbiorczy; ZAPIS tylko per-kontekst, osobna zgoda na każdy;
- `--status` → sam refresh warstwy statusu (Faza 4), pomiń sprzątanie (realizuje „tylko odśwież widok");
- `--gap` → dołącz raport luk migracji (Faza 4.5).

## Faza 1 — inwentaryzacja + diagnostyka (READ-ONLY)
Zmapuj notatki kontekstu (pliki, rozmiary, frontmatter, linki `[[…]]`, otwarte `- [ ]`). Wykryj:

**Deterministyczne (grep/skrypt — pewne):**
- broken `[[wikilinks]]` (brak celu); osierocone notatki (0 linków przychodzących, nie-hub);
- puste/szablonowe scaffoldy (body = nietknięty template: „To jest serce notatki", „Treść gotowa…");
- `updated` < daty edycji pliku / starsze niż próg; braki we frontmatter;
- nazwy spoza `<subject>-<slug>`; podmiot z >1 notatką leżący PŁASKO (kandydat do folderu);
- hub spuchnięty (linie > próg); duplikat dosłowny / near-duplicate; daty względne („dziś/wczoraj").

**Wymaga osądu (tylko FLAGA → propozycja):**
- superseded vs aktualne (newest-wins to heurystyka, nie pewnik); redundancja semantyczna / co scalić
  bez utraty niuansu; świadome archiwum vs śmieć; leakage wysoka-półka↔working-detail (co przenieść w dół).

## Faza 2 — plan sprzątania (propose-then-confirm)
Przedstaw ponumerowany, rankowany plan. Podział:
- **AUTO (za zgodą partii, odwracalne):** daty względne→bezwzględne; `updated`=dziś; normalizacja
  frontmatter; fix broken-link TYLKO gdy cel JEDNOZNACZNY (dokładnie 1 plik o tej nazwie); formatowanie.
- **POZYCJA-PO-POZYCJI (zawsze):** usunięcie/archiwizacja (nawet pustego scaffolda); scalenie (pokaż
  keep-vs-cut + zarchiwizuj oba źródła przy 1. merge); rename; przeniesienie; trymowanie/kondensacja.
Nic nie wykonuj w tej fazie — to plan. Wykonanie w Fazie 5 po „tak".

## Faza 3 — struktura i wzorce (TYLKO propozycje)
Wykryj odchylenia od JUŻ ZAPISANYCH konwencji (folder-per-subject, `<subject>-<slug>`, status-na-górze-huba,
frontmatter, PARA) → zaproponuj doprowadzenie do nich. **Nowe** wzorce/szablony = sugestia do `_system`
lub pytanie, NIGDY auto-wdrożenie. Nie wymyślaj taksonomii PARA, nie przenoś projektów między
kontekstami, nie „poprawiaj" treści merytorycznej notatek (tylko struktura/porządek). Jeśli propozycja
dotyka >~20% plików kontekstu → STOP: pokaż jako rekomendację strategiczną do osobnej decyzji, nie partię.

## Faza 4 — warstwa statusu (regeneracja wg SPEC)
Czytaj `_system/templates/status-block.md` (SPEC formatu) i **ZASTĄP** blok `status:auto`:
- w `_<context>.md` — pełny blok (🎯/⏳/⏭️/⛔/👥), wyprowadzony z otwartych `- [ ]` + frontmatter;
- w hubach podmiotów — linia „**Status:**" (źródło dla rollupu kontekstu);
- w `Home.md` — slice `<!-- ctx:<context> -->` (przepisz TYLKO swój; `--all` = wszystkie).
🎯 Teraz niejednoznaczne → PROPONUJ i pytaj. Daty bezwzględne. ZASTĄP, nie dopisuj (treść ręczna poniżej
`/status:auto` nietknięta).

## Faza 4.5 — tracker→Brain (luka migracji, opcjonalnie `--gap`, READ-ONLY)
Wybierz tracker PER KONTEKST z `config.json` → `connectors`/`paths` (np. `scandit` → JIRA projekt SHELF;
`shadow-operator`/`agency`/`personal` → Notion) i zestaw zadania trackera z vaultem.
- **Notion:** `notion-fetch`/`notion-search`; gdy MCP padnie — fallback na HTTP API
  (`Authorization: Bearer $NOTION_TOKEN`, `Notion-Version: 2022-06-28`).
- **JIRA:** `searchJiraIssuesUsingJql` (cloudId z `config.json`).
Wypisz „**żyje w trackerze, brak/nieaktualne w Brain → kandydat do migracji**". NIE twórz notatek
(to robi `/brain-pull`), NIE modyfikuj trackera. Zakończ wskazówką:
„uruchom `/brain-pull <context>` dla tych pozycji".

## Faza 5 — wykonanie zatwierdzonego
Zastosuj WYŁĄCZNIE zatwierdzone pozycje. „Usuń" = `mv` do `04-Archive/` (zachowaj nazwę pliku).
Rename/przeniesienie: unikalne `<subject>-<slug>` ratuje wikilinki — i tak zweryfikuj brak nowych broken
po zmianie. Jednokierunkowo — `SESSION.md` nietknięty.

## Faza 6 — raport
Co przeanalizowano; co zmienione (konsolidacje / archiwa / rename / linki); co odłożone; stan warstwy
statusu (Home + `_<context>` + huby); kandydaci migracji (jeśli `--gap`). Trwałe lekcje repo
(reguły/wzorce kodu) → **zasugeruj** `/ai-extract-memory`, nie wpisuj do mózgu.
