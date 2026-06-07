---
description: Pull tasks from a context's tracker (Notion/JIRA) into vault working notes
argument-hint: <context> [--status <s>] [--dry]
allowed-tools: Read, Write, Bash, mcp__notion__notion-fetch, mcp__notion__notion-search, mcp__claude_ai_Atlassian__searchJiraIssuesUsingJql
---

# /brain-pull — zadania trackera → notatki robocze w vaulcie

Pobiera zadania z trackera danego kontekstu i scaffolduje notatki robocze w vaulcie.
**To nie sync** — tracker pozostaje właścicielem statusu; notatka trzyma detal/proces
i linkuje przez frontmatter `tracker` + `task_id` (patrz `connectors/`, `docs/contexts.md`).

Argument: `$ARGUMENTS` — pierwszy token to kontekst. Flagi: `--status <s>` (filtr), `--dry`
(tylko raport, nic nie zapisuj).

## Routing kontekstów

Źródło prawdy: `config.json` + `docs/contexts.md` (w repo claude-brain). Skrót:

| Kontekst | Tracker | Źródło | Folder vaultu | Nazwa pliku |
|----------|---------|--------|---------------|-------------|
| `personal` | Notion | `collection://29084f14-76e0-80be-ac06-000b9ee2fc4f` | `01-Projects` | `<slug>.md` |
| `scandit` | JIRA | projekt SHELF, cloudId `a19c74f3-95cf-4d55-9d33-366adfe6f7a0` | `01-Projects/work` | `SHELF-<nr>-<slug>.md` |
| `shadow-operator` | Notion | `collection://9cd84f14-76e0-823a-9146-876ae3400d3c` | `01-Projects/shadow-operator` | `<slug>.md` |
| `agency` / `social-media` | Notion | `collection://29284f14-76e0-8062-a18d-000bfce0cf23` | `01-Projects/agency[/social-media]` | `<slug>.md` |

Ścieżkę vaultu czytaj z `config.json` → `vault.path` (NIE hardkoduj).

## Faza 0 — rozwiąż kontekst
1. Wczytaj `config.json`; ustal `vault.path` i tracker dla `$1`.
2. Jeśli kontekst nieznany — wypisz dostępne (`personal`, `scandit`, `shadow-operator`, `agency`, `social-media`) i zapytaj.

## Faza 1 — pobierz zadania
- **JIRA:** `searchJiraIssuesUsingJql`, JQL: `project = SHELF AND assignee = currentUser() AND statusCategory != Done ORDER BY updated DESC`. Pola wąsko: `summary,status,issuetype,priority,updated` (pełne ADF przekracza limit tokenów → jeśli wynik za duży, czytaj zapisany plik przez `jq`).
- **Notion:** `notion-fetch` na `collection://...` po schemat, potem `notion-search` z `data_source_url` po otwarte zadania (Status ∈ {In Progress, Todo, To Do, Not Started}).
- Filtr `--status` zawęża do podanego statusu.

## Faza 2 — klasyfikuj (osąd)
Dla każdego zadania zdecyduj, czy zasługuje na notatkę roboczą:
- ✅ **TAK** — ma detal techniczny / proces / wiele kroków (praca, projekty, kreatorzy, social media).
- ❌ **NIE** — drobny errand ("zadzwonić", "zarezerwować", "kupić"). Zostaje tylko w trackerze.

## Faza 3 — scaffold (pomiń przy `--dry`)
Dla zadań zakwalifikowanych na TAK:
1. Dedup: pomiń, jeśli w folderze vaultu istnieje już plik z tym `task_id` w frontmatter.
2. Utwórz plik z szablonu `_system/templates/working-note.md`, wypełniając frontmatter
   (`tracker`, `task_id`, `task_url`, `task`, `status`, `priority`, `project`, `context`, `updated`)
   i sekcję Kontekst (summary zadania). Detal zostaw pusty — to pisze użytkownik.
3. Plik w folderze i wg konwencji nazw z tabeli.

## Faza 4 — raport
Wypisz: utworzone notatki (ścieżki), pominięte jako duplikaty, pominięte jako errandy (lista).
Nie zmieniaj statusów w trackerze — to robi tylko `/brain-publish` za zgodą użytkownika.
