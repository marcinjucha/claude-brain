# Notion connector

Most między zadaniami w Notion a notatkami roboczymi w vaulcie. **Nie jest to sync** —
to podział ról (patrz `docs/architecture.md`):

- **Notion** = właściciel zadań (status, priorytet, deadline) + miejsce na **finalny produkt**.
- **Vault** = właściciel detalu: wiedza techniczna, proces, "jak to robimy".

Wykonawcą jest **Claude Code przez Notion MCP** (`mcp__notion__*`) — nie cron/skrypt, bo
pull/publish wymaga osądu (które zadanie zasługuje na notatkę, jak sformatować finał).

## Co warto, a czego nie scaffoldować

| Zadanie | Working note w vaulcie? |
|---------|--------------------------|
| Praca (Scandit/Stepstone), projekt kliencki, cokolwiek z detalem technicznym/procesem | ✅ tak |
| Drobny errand ("zarezerwować lot", "zadzwonić do X") | ❌ nie — zostaje tylko w Notion |

## Konwencja linkująca (frontmatter — wspólna dla wszystkich trackerów)

```yaml
---
type: working-note
tracker: notion            # notion | jira
task_id: 29a84f14-76e0-8056-b824-df44a26f00b1   # UUID strony Notion = klucz linku
task_url: https://app.notion.com/p/29a84f1476e08056b824df44a26f00b1
task: "Tytuł zadania z Notion"
status: In Progress        # LUSTRO statusu z Notion (Notion jest właścicielem — nie edytuj tu)
priority: High
project: "Nazwa projektu"
context: personal          # work | client | personal
updated: 2026-06-07
tags: [project, working-note]
---
```

`task_id` to jedyny twardy link. Reszta to lustro — źródłem prawdy dla statusu pozostaje tracker.
Konwencja jest wspólna z JIRA (`connectors/jira/`); różni je tylko `tracker` i format `task_id`.

## Procedura PULL (zadania Notion → notatki robocze)

Gdy poprosisz "pull zadań [kontekst]":
1. Claude odpytuje data source zadań (poniżej) filtrując po `Status` ∈ {In Progress, Todo, To Do}
   i kontekście (np. `Project Work` ≠ null dla pracy).
2. Dla każdego zadania **zasługującego na detal** (patrz tabela) — zakłada notatkę w
   `01-Projects/{work|clients}/<slug>.md` z frontmatter wyżej, jeśli jeszcze nie istnieje
   (dedup po `notion_id`).
3. Drobne errandy pomija — raportuje je tylko listą.

## Procedura PUBLISH (finalny produkt → Notion)

Gdy poprosisz "publish [notatka]":
1. Claude bierze sekcję `## Finalny produkt` z notatki roboczej.
2. `mcp__notion__notion-update-page` — wstawia treść do strony zadania w Notion.
3. Opcjonalnie zmienia `Status` (za Twoją zgodą).

## Bazy (Private Dashboard — z globalnego CLAUDE.md)

- **Zadania:** `collection://29084f14-76e0-80be-ac06-000b9ee2fc4f` ("Private Tasks Table")
  - Status: `In Progress | Waiting | Todo | Done | Won't do | Not Started | To Do`
  - Priorytety: `Critical | High | Medium | Low`
  - Relacja `🎯 Project` (limit 1), `Project Work` rollup ≠ null → praca, = null → prywatne
- **Projekty:** `collection://29084f14-76e0-80bb-8e2c-000be77d2a5f`

> Routing: legal-mind / Halo Efekt → ClickUp (NIE Notion). Reszta → ten Private Dashboard.
