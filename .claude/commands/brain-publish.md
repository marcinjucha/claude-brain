---
description: Publish a vault working note's final product back to its tracker (Notion/JIRA/Trello)
argument-hint: <note-path|task-id> [--status <s>]
allowed-tools: Read, Edit, Bash, mcp__notion__notion-fetch, mcp__notion__notion-update-page, mcp__claude_ai_Atlassian__addCommentToJiraIssue, mcp__claude_ai_Atlassian__editJiraIssue, mcp__claude_ai_Atlassian__getTransitionsForJiraIssue, mcp__claude_ai_Atlassian__transitionJiraIssue
---

# /brain-publish — finalny produkt notatki → tracker

Bierze sekcję `## Finalny produkt` z notatki roboczej w vaulcie i wypycha ją do zadania
w trackerze wskazanym we frontmatter (`tracker` + `task_id` + `task_url`). Odwrotność
`/brain-pull`. **Operacja wychodząca na zewnątrz — zawsze potwierdź przed wysłaniem.**

Repo mózgu (źródło config/ścieżek, działa globalnie):
`/Users/marcinjucha/Prywatne/projects/claude-brain`. Ścieżkę vaultu czytaj z jego `config.json`.

Argument `$ARGUMENTS`: ścieżka do notatki, albo `task_id` (np. `SHELF-21761`, `AAA-T-174`) —
wtedy znajdź notatkę po `task_id` w froncie (grep w `vault.path`).

## Faza 0 — znajdź notatkę i odczytaj front
1. Zlokalizuj plik (ścieżka wprost, lub grep `task_id:` w vaulcie).
2. Odczytaj frontmatter: `tracker`, `task_id`, `task_url`, `task`, `status`.
3. **Trello** gdy `tracker: trello` — referencja karty = `task_url` (np. `https://trello.com/c/<shortLink>`) lub `task_id` (id karty / shortLink). REST `/1/cards/{id}` przyjmuje shortLink z URL jako `{id}` — wyciągnij go z `task_url`, gdy brak `task_id`.

## Faza 1 — wyciągnij finalny produkt
- Wytnij treść sekcji `## Finalny produkt (...)` do następnego `##`.
- Jeśli pusta / wciąż placeholder ("Treść gotowa...", same nagłówki) → **przerwij**:
  "Sekcja Finalny produkt jest pusta — nie ma czego publikować."

## Faza 2 — podgląd + potwierdzenie (ZAWSZE)
Pokaż użytkownikowi: cel (tracker + `task_url`), tryb (komentarz vs nadpisanie opisu),
i dokładną treść do wysłania. Czekaj na "tak". Nic nie wysyłaj bez zgody.

## Faza 3 — publikuj
- **JIRA:** domyślnie **komentarz** (`addCommentToJiraIssue`) — bezpieczne, dopisuje.
  Nadpisanie opisu (`editJiraIssue`) tylko na wyraźną prośbę.
  > **KRYTYCZNE: treść jako Markdown string, NIGDY ADF/JSON.** ADF → surowy JSON w UI
  > (bugi SHELF-21506, 21765-21767). MCP sam konwertuje md→ADF. cloudId JIRA = UUID
  > `a19c74f3-95cf-4d55-9d33-366adfe6f7a0`.
- **Notion:** dopisz treść do strony zadania (`notion-update-page`, `task_url`/UUID jako id).
- **Trello:** domyślnie **komentarz** do karty (dopisuje, bezpieczne — jak komentarz JIRA):
  `POST https://api.trello.com/1/cards/{id}/actions/comments` z paramami `text`, `key`, `token`
  (url-encode `text`). Nadpisanie **opisu** karty tylko na wyraźną prośbę:
  `PUT https://api.trello.com/1/cards/{id}` z `desc`, `key`, `token`.
  > **AUTH Trello (Faza 3 + 4):** Trello NIE ma MCP — używaj Bash `curl` przeciw Trello REST API.
  > Klucze w `.env.local` repo `claude-marketing`:
  > `/Users/marcinjucha/Prywatne/projects/claude-marketing/.env.local` → `TRELLO_API_KEY` + `TRELLO_TOKEN`.
  > Załaduj: `set -a; source .env.local; set +a`. Token jest krótkożyciowy (wygasa po 1 dniu) —
  > jeśli call zwróci "invalid token", odnów go przez
  > `https://trello.com/1/authorize?expiration=1day&scope=read,write&response_type=token&key=$TRELLO_API_KEY`
  > i zaktualizuj `.env.local`.

## Faza 4 — status (opcjonalnie, tylko za zgodą)
Jeśli podano `--status` lub użytkownik prosi: JIRA `getTransitionsForJiraIssue` →
`transitionJiraIssue`; Notion `notion-update-page` ustaw `Status`. Nigdy bez potwierdzenia.
- **Trello:** na boardach Trello listy=status, labelka=encja (klient/osoba). Status =
  **przeniesienie karty** do listy o nazwie odpowiadającej `--status`
  ("📋 Do zrobienia" / "🔵 W toku" / "⏳ Czekam" / "✅ Done"). Rozwiąż listę po nazwie na boardzie karty:
  - board karty: `GET /1/cards/{id}?fields=idBoard`
  - listy boardu: `GET /1/boards/{idBoard}/lists?filter=open`
  - znajdź listę po nazwie wg `--status`, przenieś kartę: `PUT /1/cards/{id}?idList={listId}`.
  Labelka karty = ENCJA (klient/osoba) i jej NIE ruszamy przy zmianie statusu.
  Auth jak w Fazie 3 (curl + `TRELLO_API_KEY`/`TRELLO_TOKEN`). Tylko za zgodą.

## Zasada jakości kart (next-action → board)
Dotyczy PRZYPADKU, gdy operacja wypycha **wiele kart next-action** na board (nie standardowy
pojedynczy `## Finalny produkt` → jedno istniejące zadanie). Każda karta MUSI być:
1. **Jedna rzecz** — pojedyncza, atomowa akcja, nie pakiet kroków.
2. **Niezależna** — wykonywalna sama z siebie. Jeśli jest zablokowana niezakończoną zależnością, to NIE jest to-do — to "czekam".
3. **Przypisana do właściciela** — do tego, kto ją wykonuje.

Routing po właścicielu/gotowości (Trello, listy=status z Fazy 4):
- Akcje, które właściciel notatki (Marcin/operator) może zrobić **TERAZ** → lista aktywna ("📋 Do zrobienia" / "🔵 W toku").
- Akcje zależne od kogoś innego (twórca/klient — np. kupno domeny, publikacja ankiety) → "⏳ Czekam". Dodaj je jako karty (NIE pomijaj — to śledzone zależności), tylko na liście czekam, nie na to-do.
- Element zablokowany/bramkowany (np. "pełny launch — zablokowany do walidacji") też idzie na "⏳ Czekam", nie na to-do.

> **WHY:** zablokowana albo spakowana karta na liście aktywnej kłamie o gotowości — sugeruje "do zrobienia teraz", a nie da się jej ruszyć; wyrzucenie zależności zamiast dodania na "czekam" gubi jej śledzenie.

## Faza 5 — zaktualizuj notatkę
W froncie notatki ustaw `status` (lustro nowego stanu, jeśli zmieniony) i `updated` na dziś;
dopisz linię `published: <data>` jeśli nie istnieje. Zaraportuj: co, gdzie, link.
