# JIRA connector

Most między zadaniami pracy w JIRA a notatkami roboczymi w vaulcie. Ten sam model co
Notion (podział ról, nie sync): **JIRA = właściciel zadania**, **vault = detal/proces**.
Wykonawca: **Claude Code przez Atlassian MCP** (`mcp__claude_ai_Atlassian__*`).

## Dostęp

- Site: `scandit.atlassian.net` · cloudId: `a19c74f3-95cf-4d55-9d33-366adfe6f7a0`
- Projekt: **SHELF** (repo `~/Scandit/digital-shelf-ios/`)
- Konwencja branchy: `feature|bugfix/SHELF-<nr>-<slug>` → slug zgodny z nazwą pliku notatki.

## Konwencja linkująca (frontmatter — wspólna dla wszystkich trackerów)

```yaml
tracker: jira
task_id: SHELF-23523
task_url: https://scandit.atlassian.net/browse/SHELF-23523
status: In Progress        # LUSTRO z JIRA — JIRA jest właścicielem
```

`task_id` (klucz JIRA) to twardy link. Plik notatki: `01-Projects/work/SHELF-<nr>-<slug>.md`.

## PULL (moje zadania JIRA → notatki robocze)

JQL bazowy (aktywne, przypisane do mnie):
```
project = SHELF AND assignee = currentUser() AND statusCategory != Done ORDER BY updated DESC
```
> Pobieraj wąsko pola (`summary,status,issuetype,priority,updated`) — pełne opisy ADF
> potrafią przekroczyć limit tokenów. Opis zadania zostaje w JIRA; do vaultu idzie tylko
> link + summary, a detal piszesz sam.

Claude dla każdego aktywnego zadania zakłada notatkę z szablonu `_system/templates/working-note.md`
(dedup po `task_id`), do `01-Projects/work/`.

## PUBLISH (finalny produkt → JIRA)

Sekcja `## Finalny produkt` notatki → komentarz lub opis zadania:
`mcp__claude_ai_Atlassian__addCommentToJiraIssue` / `editJiraIssue`. Zmiana statusu
(`transitionJiraIssue`) tylko za Twoją zgodą.
