---
description: Pull tasks from a context's tracker (Notion/JIRA/Trello) into vault working notes
argument-hint: <context> [--status <s>] [--dry]
allowed-tools: Read, Write, Bash, mcp__notion__notion-fetch, mcp__notion__notion-search, mcp__claude_ai_Atlassian__searchJiraIssuesUsingJql
---

# /brain-pull — zadania trackera → notatki robocze w vaulcie

Pobiera zadania z trackera danego kontekstu i scaffolduje notatki robocze w vaulcie.
**To nie sync** — tracker pozostaje właścicielem statusu; notatka trzyma detal/proces
i linkuje przez frontmatter `tracker` + `task_id` (patrz `connectors/`, `docs/contexts.md`).

Argument: `$ARGUMENTS` — pierwszy token to kontekst. Flagi: `--status <s>` (filtr), `--dry`
(tylko raport, nic nie zapisuj).

Repo mózgu (źródło config/ścieżek, działa z każdego projektu):
`/Users/marcinjucha/Prywatne/projects/claude-brain`. Czytaj jego `config.json` i `docs/contexts.md`
po ścieżce absolutnej — komenda jest globalna i bywa uruchamiana spoza repo.

## Routing kontekstów

Źródło prawdy: `config.json` + `docs/contexts.md` (w repo claude-brain). Skrót:

| Kontekst | Tracker | Źródło | Folder vaultu | Nazwa pliku |
|----------|---------|--------|---------------|-------------|
| `personal` | Notion | `collection://29084f14-76e0-80be-ac06-000b9ee2fc4f` | `01-Projects` | `<slug>.md` |
| `scandit-shelfview` | JIRA | projekt SHELF, cloudId `a19c74f3-95cf-4d55-9d33-366adfe6f7a0` | `01-Projects/scandit-shelfview` | `SHELF-<nr>-<slug>.md` |
| `scandit-pple-sdk` | JIRA | projekt SHELF, cloudId `a19c74f3-95cf-4d55-9d33-366adfe6f7a0` | `01-Projects/scandit-pple-sdk` | `SHELF-<nr>-<slug>.md` |
| `shadow-operator` | **Trello** (aktywny) | board `mTwOoGKz` (z `tracker_trello` we frontmatter `_<context>.md`). **Model KREATOR-jako-LISTA** (zmiana 2026-07-22): **LISTA = encja (kreator)**; STATUS niesie: pozycja w liście (W toku góra → Do zrobienia → ⏳Czekam → ✓Done dół) + labelka **⏳ Czekam** + karta oznaczona complete (`dueComplete`). BRAK list statusowych. | `01-Projects/shadow-operator` | `<slug>.md` |
| `agency` (Trello) | **Trello** | board `tkOXUJUS` (z `tracker_trello` we frontmatter `_<context>.md`). **Model ENCJA-jako-LISTA** (zmiana 2026-07-22): **LISTA = encja (obszar/klient)** — np. Venture/leady · Platforma · Website/SEO · Justyna; STATUS = pozycja + labelka **⏳ Czekam** + `dueComplete`. BRAK list statusowych. | `01-Projects/agency` | `<slug>.md` |
| `shadow-operator` | Notion | **Tasks Tracker** `collection://37984f14-76e0-80f1-95f2-000bd6a8a39a` (relacja `Prospect` → kreator). Kreatorzy/prospekty osobno: Prospecting Tracker `collection://9cd84f14-76e0-823a-9146-876ae3400d3c` (źródło prospectingu/archiwum) | `01-Projects/shadow-operator` | `<slug>.md` |
| `agency` | Notion | `collection://29284f14-76e0-8062-a18d-000bfce0cf23` | `01-Projects/agency` | `<task-id>-<slug>.md` |
| `social-media` | Notion | projekt **AAA-P-10** `33c84f1476e08111acd6e3e197be747f` (relacja `✅ Tasks`) | `01-Projects/agency/social-media` | `<task-id>-<slug>.md` |

`scandit-shelfview` vs `scandit-pple-sdk`: `scandit-shelfview` = aplikacja Shelfview (repo `digital-shelf-ios`),
`scandit-pple-sdk` = PPLE SDK (repo `digital-shelf-sdk-ios`) — SAM projekt JIRA (SHELF), OSOBNA pula
wiedzy domenowej i osobna pamięć projektu.

Ścieżkę vaultu czytaj z `config.json` → `vault.path` (NIE hardkoduj).

## Faza 0 — rozwiąż kontekst
1. Wczytaj `config.json`; ustal `vault.path` i tracker dla `$1`.
2. Jeśli kontekst używa Trello — rozwiąż board z `tracker_trello` we frontmatter `_<context>.md` (np. `shadow-operator` → `mTwOoGKz`).
3. Jeśli kontekst nieznany — wypisz dostępne (`personal`, `scandit-shelfview`, `scandit-pple-sdk`, `shadow-operator`, `agency`, `social-media`) i zapytaj.

## Faza 1 — pobierz zadania
- **JIRA:** `searchJiraIssuesUsingJql`, domyślnie sprint-scoped: `assignee = currentUser() AND sprint in openSprints() AND project = SHELF ORDER BY priority DESC` (szerzej: `... AND statusCategory != Done`). Pola wąsko: `summary,status,issuetype,priority,updated` (i tak bywa za duże → czytaj zapisany plik przez `jq`). Scaffold tylko aktywne (In Progress/To Do); pomiń Done/Implemented i placeholdery. Pełne reguły: skill Scandit `project-management`.
- **Notion (cały kontekst, np. `personal`, `agency`):** `notion-fetch` na `collection://...` po schemat, potem `notion-search` z `data_source_url` po otwarte zadania (Status ∈ {In Progress, Todo, To Do, Not Started, Inbox}).
- **Notion (pod-projekt, np. `social-media`):** NIE używaj `notion-search` po całej tabeli —
  semantyka zwraca obce zadania łapiące się na słowa. Zamiast tego `notion-fetch` na stronie
  **projektu** i odczytaj relację `✅ Tasks`, potem `notion-fetch` każdego zadania.
- **Trello (granularność = ENCJA, nie karta) — oś ENCJA/STATUS zależy od MODELU boardu (czytaj z `tracker_trello`):** Bash `curl` na Trello REST (bez MCP). Pobierz karty + listy:
  `GET https://api.trello.com/1/boards/{boardId}/cards?fields=name,due,dueComplete,idList,labels&filter=open&key=$TRELLO_API_KEY&token=$TRELLO_TOKEN`
  oraz `GET https://api.trello.com/1/boards/{boardId}/lists?fields=name&filter=open&key=$TRELLO_API_KEY&token=$TRELLO_TOKEN` żeby zmapować `idList` → nazwę listy.
  AUTH jak w `/brain-publish` (creds w `claude-marketing/.env.local`: `TRELLO_API_KEY`+`TRELLO_TOKEN`; `set -a; source .env.local; set +a`; token bywa krótki → przy „invalid token" odnów przez `/1/authorize`).
  **Model ENCJA-jako-LISTA (oba aktywne boardy od 2026-07-22):** ENCJA = **nazwa LISTY**; grupuj karty po `idList` → JEDNA notatka per encja. STATUS karty = z pozycji + labelka `⏳ Czekam` (jeśli jest) + `dueComplete`. Pomiń karty z `dueComplete: true` (= Done). NIE ma list statusowych. Czym jest encja per board: shadow-operator (`mTwOoGKz`) = **kreator** (→ notatka per kreator); agency (`tkOXUJUS`) = **obszar/klient** (Venture/leady · Platforma · Website/SEO · Justyna — kolumna-klient np. Justyna → jej notatka; kolumny-obszary CMS to grupowanie kanbanowe, niekoniecznie 1 notatka).
  Każda karta → `- [ ] <nazwa karty>` w `## Next-actions` (STATUS + due jeśli jest). NIE rób notatki per karta.
- `task_id` dla Notion Agency = ludzkie ID (`AAA-T-###`); `task_url` = pełny URL (zawiera UUID do publish).
- Filtr `--status` zawęża do podanego statusu.

## Faza 2 — klasyfikuj (osąd)
Dla każdego zadania zdecyduj, czy zasługuje na notatkę roboczą:
- ✅ **TAK** — ma detal techniczny / proces / wiele kroków (praca, projekty, kreatorzy, social media).
- ❌ **NIE** — drobny errand ("zadzwonić", "zarezerwować", "kupić"). Zostaje tylko w trackerze.
- **Trello (per ENCJA):** encja z kartami = ma proces → TAK (jedna notatka). Encja = nazwa LISTY (model ENCJA-jako-LISTA — kreator dla shadow-operator, obszar/klient dla agency). Pomiń karty ukończone (`dueComplete: true`) i oczywiste archiwa oraz encje, które są tylko errandami.

## Faza 3 — scaffold (pomiń przy `--dry`)
Dla zadań zakwalifikowanych na TAK:
1. Dedup: pomiń, jeśli w folderze vaultu istnieje już plik z tym `task_id` w frontmatter.
2. Utwórz plik z szablonu `_system/templates/working-note.md`, wypełniając frontmatter
   (`tracker`, `task_id`, `task_url`, `task`, `status`, `priority`, `project`, `context`, `updated`)
   i sekcję Kontekst (summary zadania). Detal zostaw pusty — to pisze użytkownik.
3. Plik w folderze i wg konwencji nazw z tabeli.
4. **Trello (dedup per ENCJA, nie per `task_id`):** shadow-operator ma już notatki per kreator
   (`kacper-snela.md`, `barbara-bylina.md`). Encja = nazwa LISTY (model ENCJA-jako-LISTA — kreator dla shadow-operator, obszar/klient dla agency, np. lista „Justyna" → `justyna-kancelaria/`). Podział ról: Trello mirroruje TYLKO next-actions;
   notatka w mózgu = źródło prawdy dla całego detalu/procesu/kontekstu. Dlatego pull Trello → mózg dotyka WYŁĄCZNIE
   sekcji `## Next-actions` (twórz/odśwież ją z kart pogrupowanych po encji) i NIGDY nie nadpisuje reszty istniejącej notatki
   (Kontekst, Detal techniczny, Decyzje, Finalny produkt — to jest brain-owned). Jeśli notatka dla tej encji
   już istnieje (dopasuj po nazwie encji = nazwie listy-kreatora / labelki / istniejącym pliku) → ODŚWIEŻ `## Next-actions` w miejscu, resztę zostaw nietkniętą,
   NIE twórz duplikatu. Pełny scaffold z szablonu dostaje tylko zupełnie nowa encja (brak notatki). Frontmatter notatki Trello:
   `tracker: trello`, `task_url` = referencja boardu (luźny round-trip z `/brain-publish`; cel publish per-karta ustawiasz ręcznie gdy trzeba), `task` = nazwa encji, `context: shadow-operator`, `updated` = dziś. Zostaw `## Kontekst` (summary); detal techniczny zostaw użytkownikowi.

## Faza 4 — raport
Wypisz: utworzone notatki (ścieżki), pominięte jako duplikaty, pominięte jako errandy (lista).
Dla Trello rozdziel też: notatki utworzone vs odświeżone (`## Next-actions`).
Nie zmieniaj statusów w trackerze — to robi tylko `/brain-publish` za zgodą użytkownika.
