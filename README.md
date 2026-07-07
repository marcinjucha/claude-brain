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
│  commands/   ── rodzina /brain-* (globalne komendy)           │
│  connectors/ ── Notion, JIRA, Telegram                        │
│  mcp/        ── konfiguracje serwerów MCP                     │
│  n8n/        ── workflowy automatyzacji (eksporty .json)      │
│  scripts/    ── bootstrap, sync, maintenance, knowledge-system │
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
| Rodzina `/brain-*` (9 komend) | ✅ zadania · pamięć · status · knowledge (globalne) | `commands/` → `.claude/commands/` |
| Warstwa statusu (`status:auto`) | ✅ auto-blok, rollup 3-poziomowy | `_system/templates/status-block.md` |
| Knowledge-system | ✅ wiedza skilli → vault (source of truth) + pre-commit | `scripts/`, `_system/knowledge-system.md` |
| Dashboard żywy + social board (Dataview) | ✅ Home.md, `_social-board.md` (wymaga pluginu) | vault · `docs/obsidian-setup.md` |
| Pamięć projektu (vault) | ✅ `_<projekt>.md` | vault |
| n8n / `/brain-digest`  | ⬜ todo      | `n8n/` |

Pełny projekt: `docs/architecture.md`. Mapa kontekstów (Personal, Scandit, Shadow
Operator, HaloEfekt) z Notion IDs i repos: `docs/contexts.md`.

## Jak używać — rodzina `/brain-*`

Komendy są **globalne** (symlinkowane z `commands/` do `~/.claude/commands/` przez
`scripts/link-commands.sh`), więc odpalasz je z dowolnego folderu. Który kontekst i tracker
złapią, wynika z `cwd` przez mapę `config.json` → `.paths`.

**Codzienny cykl pracy w projekcie:**

| Komenda | Do czego |
|---------|----------|
| `/brain-load` | Podłącza bieżący folder do mózgu: wczytuje pamięć projektu z vaultu + głęboką pamięć repo. Zacznij tu każdą sesję. |
| `/brain-pull` | Ściąga zadania z trackera kontekstu (Notion/JIRA/Trello) do notatek roboczych w vaulcie. |
| `/brain-update` | Po pracy aktualizuje pamięć projektu (status, done, connections) i **wąsko** regeneruje warstwę statusu (własny blok + wycinek w `Home.md`). Event-driven. |
| `/brain-publish` | Wypycha finalny produkt z notatki roboczej z powrotem do trackera (Notion/JIRA/Trello). |

**Skrzynka i treść:**

| Komenda | Do czego |
|---------|----------|
| `/brain-inbox` | Triage `00-Inbox` (capture'y z Telegrama) — rozdziela każdy element do właściwego trackera, potem kasuje przetworzony plik. |
| `/brain-social` | Scaffold notatki social + draft hooka, skryptu i copy (pipeline treści). |

**Konserwacja (okresowa):**

| Komenda | Do czego |
|---------|----------|
| `/brain-sync` | Okresowy audyt vaultu kontekstu: konsoliduje/czyści notatki (propose-then-confirm, archiwizacja zamiast usuwania), robi **pełny** recompute warstwy statusu + rollup, raportuje luki migracji tracker→Brain. Okresowy odpowiednik `brain-update`. |

**Knowledge-system (wiedza domenowa skilli → vault):**

| Komenda | Do czego |
|---------|----------|
| `/brain-knowledge-init` | Onboarduje kontekst do knowledge-systemu: tworzy katalog wiedzy w vaulcie, aktywuje kontekst w `config.json`, instaluje pre-commit w repo-konsumentach. |
| `/brain-knowledge-migrate` | Migruje wiedzę domenową JEDNEGO skilla do vaultu — EXTRACT (twoje skille, ścieńcza je) albo MIRROR (skille zespołowe, tylko kopia). |

Vault (03-Resources/<ctx>/knowledge/) jest **źródłem prawdy** dla wiedzy domenowej; skille
zostają cienkie i deklarują potrzeby przez `@references/knowledge/<slug>.md`. Snapshot do skilli
robi `scripts/sync-knowledge.py` (jednokierunkowo, generowana kopia). Kontrakt:
`<vault>/_system/knowledge-system.md`.

## Skrypty (`scripts/`)

| Skrypt | Do czego |
|--------|----------|
| `link-commands.sh` | Symlinkuje `commands/*.md` do `~/.claude/commands/` (rejestruje rodzinę `/brain-*`). |
| `run-telegram-capture.sh` + `com.mjucha.brain.telegram.plist` | Bot Telegrama (@mjchiefbot) w tle przez launchd — capture do `00-Inbox`. |
| `knowledge-init.sh` | Hydraulika `/brain-knowledge-init` (katalog + `active:true` + pre-commit). Idempotentny. |
| `sync-knowledge.py` | Snapshot wiedzy vault→skille + integrity checks (`--context <ctx>` / `--all`). |
| `install-precommit.sh` | Instaluje pre-commit hook pilnujący spójności knowledge w repo-konsumencie. |
