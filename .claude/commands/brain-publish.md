---
description: Publish a vault working note's final product back to its tracker (Notion/JIRA)
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

## Faza 4 — status (opcjonalnie, tylko za zgodą)
Jeśli podano `--status` lub użytkownik prosi: JIRA `getTransitionsForJiraIssue` →
`transitionJiraIssue`; Notion `notion-update-page` ustaw `Status`. Nigdy bez potwierdzenia.

## Faza 5 — zaktualizuj notatkę
W froncie notatki ustaw `status` (lustro nowego stanu, jeśli zmieniony) i `updated` na dziś;
dopisz linię `published: <data>` jeśli nie istnieje. Zaraportuj: co, gdzie, link.
