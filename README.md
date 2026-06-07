# claude-brain — infrastruktura second brain

To repo to **hydraulika** second brain, nie jego treść. Treść (notatki, wiedza, PARA)
żyje w osobnym vaulcie Obsidiana. Tu trzymamy wszystko, co łączy ten vault ze światem:
connectory, konfiguracje MCP, workflowy n8n, skrypty setupowe.

## Architektura

```
┌─────────────────────────────────────────────────────────────┐
│  TREŚĆ (mózg)                                                 │
│  Obsidian vault  ~/Library/.../iCloud~md~obsidian/.../AI      │
│  PARA: 00-Inbox 01-Projects 02-Areas 03-Resources 04-Archive │
│  • plain markdown • iCloud sync • dostępny na telefonie       │
└───────────────▲─────────────────────────────────────────────┘
                │ czyta / pisze pliki .md bezpośrednio
                │
┌───────────────┴─────────────────────────────────────────────┐
│  HYDRAULIKA (to repo — claude-brain)                          │
│                                                               │
│  Claude Code ── silnik: operuje na plikach vaultu wprost      │
│  connectors/ ── Notion, Telegram, Perplexity, ...             │
│  mcp/        ── konfiguracje serwerów MCP                     │
│  n8n/        ── workflowy automatyzacji (eksporty .json)      │
│  scripts/    ── bootstrap, sync, maintenance                  │
└───────────────────────────────────────────────────────────────┘
                │
     ┌──────────┼──────────┬─────────────┐
     ▼          ▼          ▼             ▼
  Notion      JIRA      Telegram   (kolejne źródła)
  zadania     zadania   capture /
  osobiste    pracy     komunikacja
```

## Zasada projektowa

- **Vault nie wie o hydraulice.** To zwykłe pliki .md — działają bez tego repo.
- **Hydraulika wie o vaulcie** przez jedną ścieżkę w `config.json` (single source of truth).
- **Claude Code czyta/pisze vault bezpośrednio** — żadne MCP nie jest do tego potrzebne,
  bo to po prostu pliki na dysku. MCP/connectory są dla *zewnętrznych* systemów (Notion, Telegram).

## Status

| Element        | Stan        | Gdzie |
|----------------|-------------|-------|
| Vault PARA     | ✅ założony  | `.../Documents/AI` |
| Repo szkielet  | ✅ gotowy    | tutaj |
| Telegram capture | ✅ działa (bot @mjchiefbot, launchd w tle) | `connectors/telegram/` |
| Notion connector | ✅ spec + konwencja (osobiste, przez MCP) | `connectors/notion/` |
| JIRA connector | ✅ spec + demo pull (praca SHELF, 3 notatki) | `connectors/jira/` |
| `/brain-pull` + `/brain-publish` | ✅ zadania: tracker ↔ notatki (globalne) | `.claude/commands/` |
| `/brain-load` + `/brain-update` | ✅ wiedza: pamięć projektu ↔ sesja (globalne) | `.claude/commands/` |
| Dashboard + pamięć projektu (vault) | ✅ Home.md + `_<projekt>.md` | vault |
| n8n / `/brain-digest`  | ⬜ todo      | `n8n/` |

Pełny projekt: `docs/architecture.md`. Mapa kontekstów (Personal, Scandit, Shadow
Operator, HaloEfekt) z Notion IDs i repos: `docs/contexts.md`.
