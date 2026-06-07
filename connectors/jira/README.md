# JIRA connector

Most między zadaniami pracy w JIRA a notatkami roboczymi w vaulcie. Ten sam model co
Notion (podział ról, nie sync): **JIRA = właściciel zadania**, **vault = detal/proces**.
Wykonawca: **Claude Code przez Atlassian MCP** (`mcp__claude_ai_Atlassian__*`).

## Dostęp

- Site: `scandit.atlassian.net`
- **cloudId — różne dla JIRA i Confluence (nie mylić):**
  - JIRA = UUID `a19c74f3-95cf-4d55-9d33-366adfe6f7a0`
  - Confluence = domena `scandit.atlassian.net`
- Projekt: **SHELF** (repo `~/Scandit/digital-shelf-ios/`)
- Konwencja branchy: `feature|bugfix/SHELF-<nr>-<slug>` → slug zgodny z nazwą pliku notatki.

> **Autorytet:** pełne reguły JIRA/Confluence/Sprint są w skillu Scandit
> `~/Scandit/digital-shelf-ios/.claude/skills/project-management/SKILL.md`
> (agent `atlassian-manager`). Poniżej tylko to, co istotne dla mózgu.

## Konwencja linkująca (frontmatter — wspólna dla wszystkich trackerów)

```yaml
tracker: jira
task_id: SHELF-23523
task_url: https://scandit.atlassian.net/browse/SHELF-23523
status: In Progress        # LUSTRO z JIRA — JIRA jest właścicielem
```

`task_id` (klucz JIRA) to twardy link. Plik notatki: `01-Projects/work/SHELF-<nr>-<slug>.md`.

## PULL (moje zadania JIRA → notatki robocze)

**Domyślnie sprint-scoped** ("co robić teraz") — lepsze niż "wszystkie otwarte":
```
assignee = currentUser() AND sprint in openSprints() AND project = SHELF ORDER BY priority DESC
```
Szerszy backlog (gdy trzeba): `... AND statusCategory != Done ORDER BY updated DESC`.

> Pobieraj wąsko pola (`summary,status,issuetype,priority,updated`) — i tak potrafi
> przekroczyć limit tokenów (opisy), wtedy czytaj zapisany plik wyniku przez `jq`.
> Opis zadania zostaje w JIRA; do vaultu idzie link + summary, detal piszesz sam.

Scaffold tylko zadań **aktywnych** (In Progress / To Do); pomiń Done/Implemented (zamknięte/review)
i czyste placeholdery. Dedup po `task_id`, do `01-Projects/work/`.

## PUBLISH (finalny produkt → JIRA)

Sekcja `## Finalny produkt` → komentarz/opis: `addCommentToJiraIssue` / `editJiraIssue`.

> **KRYTYCZNE: zawsze Markdown, NIGDY ADF.** ADF → surowy escaped JSON w UI JIRA
> (produkcyjne bugi SHELF-21506, 21765-21767). MCP sam konwertuje md→ADF. Nie używaj
> obiektów ADF ani `JSON.stringify()`.
> Przy tworzeniu zadań: komponenty zawsze `[{name:"iOS"},{name:"SHELFVIEW-APP"}]`
> (labele ukrywają task — SHELF-21606). Sprint: `customfield_10020` (liczba, nie tablica).

Zmiana statusu (`transitionJiraIssue`) tylko za zgodą użytkownika.
