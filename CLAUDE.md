# claude-brain — infrastruktura second brain

To repo to **hydraulika**, nie treść. Treść (notatki) żyje w vaulcie Obsidiana,
którego ścieżka jest w `config.json` → `vault.path`. Zawsze czytaj tę ścieżkę stąd,
nie hardkoduj jej w skryptach.

## Co tu należy, a co nie

- **TU:** connectory (`connectors/`), konfiguracje MCP (`mcp/`), workflowy n8n (`n8n/`),
  skrypty setup/sync/maintenance (`scripts/`), dokumentacja architektury (`docs/`).
- **NIE TU:** notatki, wiedza, zadania-jako-treść — to idzie do vaultu.

## Zasada: silniki vs mózg

Silniki domenowe (skille/agenci, np. `claude-marketing`, `claude-dev`) i głęboka wiedza repo
(`CLAUDE.md`/skille/`memory.md`) **żyją w swoich repo**. Mózg **linkuje i mapuje, nie wchłania
ani nie kopiuje** — pamięć projektu w vaulcie trzyma wysoką półkę + mapę „zadanie → skill".

## Operowanie na vaulcie

Vault to zwykłe pliki `.md` na dysku — czytaj/pisz je bezpośrednio (Read/Write/Edit).
**Nie potrzeba MCP do dostępu do vaultu** — MCP/connectory są wyłącznie dla systemów
zewnętrznych (Notion, Telegram), nie dla plików lokalnych.

Struktura vaultu (PARA): `00-Inbox`, `01-Projects/{work,clients}`, `02-Areas`,
`03-Resources`, `04-Archive`, `_system/templates`.

## Routing zadań (warstwa zadań mózgu)

- Osobiste → **Notion** Private Dashboard (`connectors/notion/`).
- Praca Scandit → **JIRA** projekt SHELF, repo digital-shelf-ios (`connectors/jira/`).
- Notatka robocza linkuje do zadania przez frontmatter `tracker` + `task_id`. Plik pracy
  Scandit: `01-Projects/work/SHELF-<nr>-<slug>.md`.

## Status i kolejność

Patrz tabela statusu w `README.md`. Kolejność budowy: connectory → n8n → automatyzacje.

## Warstwa statusu + brain-sync

**Warstwa statusu** to auto-generowany blok `<!-- status:auto -->…<!-- /status:auto -->` —
**projekcja notatek**, nie osobna prawda: wyliczana z otwartych `- [ ]` i frontmatteru. Żyje na
3 poziomach (hub jednolinijkowiec → sekcja statusu w `_<context>.md` → wycinek per-kontekst w
`Home.md`, znaczony `<!-- ctx:… -->`); rollup tylko w górę. Format zdefiniowany w JEDNYM miejscu:
`_system/templates/status-block.md` (SPEC = single source of truth). Oba commandy SPEC tylko
**referują, nigdy nie kopiują** formatu; blok jest ZAWSZE podmieniany w miejscu, nigdy dopisywany.
**Why:** jedna definicja = brak driftu i puchnięcia; status pozostaje pochodną notatek, nie drugą
kopią stanu do ręcznego utrzymania.

**`brain-sync`** (`commands/brain-sync.md`) — okresowy audyt vaultu (per-kontekst po cwd, flagi
`--all`/`--status`/`--gap`): konsoliduje/czyści/porządkuje notatki kontekstu (propose-then-confirm,
archiwizacja zamiast usuwania do `04-Archive`, strefy nietykalne: `SESSION.md`, datowane wpisy
`### YYYY-MM-DD`, pliki archiwum, jawne warianty), robi PEŁNY recompute warstwy statusu + rollup
i raportuje luki migracji tracker→Brain (Notion+JIRA, READ-ONLY, sam pull deleguje do `/brain-pull`).
To okresowy odpowiednik event-driven `brain-update` (które regeneruje status WĄSKO — własny blok
kontekstu + własny wycinek w `Home.md`, tylko gdy status się zmienił). Dołącza do rodziny `brain-*`
(brain-load, brain-update, brain-pull, brain-publish, brain-inbox, brain-social).
