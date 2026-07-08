# claude-brain — infrastruktura second brain

To repo to **hydraulika** second brain, nie jego treść. Treść (notatki, wiedza, PARA)
żyje w osobnym vaulcie Obsidiana. Tu trzymamy wszystko, co łączy ten vault ze światem:
komendy `/brain-*`, skill/agent brain, connectory, konfiguracje MCP, workflowy n8n, hooki, skrypty.

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
│  .claude/commands/ ── rodzina /brain-* (globalne komendy)     │
│  .claude/skills/   ── brain-conventions (dyscyplina + konwencje)│
│  .claude/agents/   ── brain-manager (thin router)             │
│  connectors/ ── Notion, JIRA, Telegram                        │
│  hooks/      ── SessionStart (inject kontekstu + regen wiedzy)│
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

## Dwie półki pamięci (w vaulcie)

Mózg trzyma pamięć na **dwóch półkach o różnym cyklu życia**:

- **Wysoka półka — pamięć projektu:** `01-Projects/<ctx>/_<ctx>.md` (status/postęp/połączenia,
  KONDENSOWANA — zastępuj, nie akumuluj) + **notatki robocze** per-ticket/encja (detal, decyzje,
  dead-endy). Mutowalna, opisuje stan bieżący. Właściciel zapisu: `/brain-load` (orient),
  `/brain-update` (zapis po sesji), `/brain-sync` (audyt okresowy).
- **Głęboka półka — notatki wiedzy:** `03-Resources/<ctx>/knowledge/` (PARA Resources → nie
  archiwizuje się z projektem). Trwała, **atomowa synteza domenowa** — „dlaczego domena/produkt
  są jakie są". Właściciel zapisu: `/brain-extract-knowledge` (z pracy), `distill-coaching`
  (z wejść zewnętrznych), `/brain-knowledge-migrate` (ze skilla).

## Dwie drabiny pamięci + crossover (rdzeń modelu)

Trwała wiedza wspina się dwiema równoległymi drabinami, które **spotykają się na górze**:

- **Drabina repo (zespołowa):** `/ai-extract-memory` → `memory.md` (bufor sesji, git-tracked)
  → `/ai-curate-memory` → **CLAUDE.md** (reguły dla człowieka) / **skille** (HOW ładowane przez agenta).
  Zostaje w repo, współdzielona z zespołem.
- **Drabina brain (osobista):** `/brain-update` → pamięć projektu + notatka robocza
  → `/brain-extract-knowledge` → **notatki wiedzy** (`home: brain`). Twoja cross-projektowa synteza.

**Crossover (kluczowa reguła):** pojedynczy zakotwiczony **atom** (jeden próg, jeden bug, jedna
reguła-pliku) zostaje w repo — mózg go co najwyżej LINKUJE. **Cross-atom SYNTEZA** (spina ≥2 atomy,
których żadna pojedyncza lokalizacja repo nie niesie) idzie do notatki wiedzy mózgu. Hasło:
**„Own the synthesis, link the atom."** `/ai-curate-memory` (target #1) i `/brain-update` (Faza 3.8)
routują taką syntezę do `/brain-extract-knowledge`. Wspólną dyscyplinę (brzytwa, no-invention,
dedup, verify, schemat noty) trzyma skill **`brain-conventions`** — jedno źródło dla obu silników.

## Jak zaczyna się sesja

- **SessionStart hook (pasywny, always-on):** gdy `cwd` mapuje się na kontekst brain,
  `hooks/session-start-brain.sh` **wstrzykuje (read-only)** pamięć projektu + indeks wiedzy (`_MOC.md`
  danego kontekstu) + worktree `SESSION.md` + notatkę bieżącego ticketu. `hooks/session-start-knowledge.sh`
  regeneruje snapshoty wiedzy przy dryfie (dla kontekstów `active`). Hook tylko *pokazuje* — nie działa.
- **`/brain-load` (aktywny):** dopiero on *działa* na tym kontekście — pełny orient, sieciowy backfill
  notatki ticketu. Zacznij tu każdą sesję pracy.

Notatki brain-only (`home: brain`) są widziane przy starcie, bo hook wstrzykuje `_MOC.md`, a każdy
silnik ma OBOWIĄZEK wpisać nową notę do `_MOC.md` (jedyny orphan-guard dla notatek bez konsumenta-skilla).

## Mapa komend

Komendy są **globalne** (pliki w `.claude/commands/`, symlinkowane do `~/.claude/commands/` przez
`scripts/link-commands.sh`). Który kontekst/tracker złapią — wynika z `cwd` przez `config.json` → `.paths`
(kontekst zadeklarowany w promptcie ma pierwszeństwo nad cwd).

| Komenda | Kiedy | Czyta | Pisze |
|---------|-------|-------|-------|
| `/brain-load` | start sesji pracy | pamięć projektu, notatka robocza, pamięć repo, tracker | backfill notatki ticketu + delta wysokiej półki |
| `/brain-update` | po sesji pracy | ta sesja, `SESSION.md`, `git log` | pamięć projektu + notatka robocza + blok statusu; proponuje noty wiedzy (Faza 3.8) |
| `/brain-pull` | pobranie zadań | tracker (Notion/JIRA/Trello) | notatki robocze |
| `/brain-publish` | wysłanie produktu | notatka robocza (`## Finalny produkt`) | tracker |
| `/brain-inbox` | triage capture | `00-Inbox` | tracker; kasuje przetworzony plik |
| `/brain-social` | nowa treść | szablon | notatka social + draft |
| `/brain-sync` | audyt okresowy | cały vault kontekstu (`brain-scan.py`) | konsolidacja notatek, pełny recompute statusu, raport luk |
| `/brain-knowledge-init` | onboarding kontekstu | config | katalog wiedzy + `active:true` + pre-commit |
| `/brain-knowledge-migrate` | migracja wiedzy SKILLA | `SKILL.md` | notatki wiedzy (EXTRACT ścieńcza / MIRROR odbija) |
| `/brain-extract-knowledge` | synteza z SKOŃCZONEJ pracy | `memory.md` (sekcje domenowe), notatka robocza, `git log` | noty `home:brain` + `_MOC.md` (brain-only, nigdy snapshot do skilli zespołu) |
| `/ai-extract-memory` | zebranie lekcji repo | ta sesja | `memory.md` (bufor git-tracked) |
| `/ai-curate-memory` | promocja lekcji repo | `memory.md`, CLAUDE.md, skille | CLAUDE.md / skille; syntezę routuje → `/brain-extract-knowledge` |

## Cykl życia wiedzy

`capture` (Telegram → `00-Inbox`, triage `/brain-inbox`) → `praca` (`SESSION.md` + rozmowa)
→ `zapis` (`/brain-update`: wysoka półka + notatka robocza) → `destylacja` (`/brain-extract-knowledge`
lub `/brain-update` Faza 3.8 lub `/ai-curate-memory` target #1 zamieniają cross-atom „dlaczego" w noty
`home:brain`, `emerging`→`canon` po N≥3 źródłach) → `migracja` (wiedza skilla zespołu przez
`/brain-knowledge-migrate`, EXTRACT/MIRROR) → `surface` (SessionStart wstrzykuje `_MOC.md`;
`sync-knowledge.py` snapshotuje noty EXTRACT do `references/knowledge/` skilli) → `utrzymanie`
(`/brain-sync` audyt + `--deep` wykrywa superseded + pre-commit/SessionStart integralność).

## mirror vs brain-owned

- **`home: brain`** — mózg jest źródłem prawdy, notę posiadasz i rozwijasz. Notatki syntezy z pracy
  (scandit: brain-only, surface przez SessionStart) LUB konsumowane przez TWOJE skille (snapshot).
- **`status: mirror`** — nota tylko ODBIJA skill zespołu (`/brain-knowledge-migrate --mirror`);
  refresh skill→mózg, nigdy nie rozwijaj w miejscu. Net-nowa wiedza dla zespołu → PR do skilla,
  nie do lustra. (Scandit ma dziś 13 luster + rosnącą warstwę brain-owned syntezy.)

Pełny kontrakt (schemat noty, brzytwa, promocja, tryb MIRROR): `_system/knowledge-system.md`.
Dyscyplina destylacji dzielona przez silniki: skill `brain-conventions`.

## Zasada projektowa

- **Vault nie wie o hydraulice.** To zwykłe pliki .md — działają bez tego repo.
- **Hydraulika wie o vaulcie** przez jedną ścieżkę w `config.json` (single source of truth).
- **Claude Code czyta/pisze vault bezpośrednio** — żadne MCP nie jest do tego potrzebne,
  bo to po prostu pliki na dysku. MCP/connectory są dla *zewnętrznych* systemów (Notion, Telegram).
- **Wiedza domenowa: mózg = źródło, atomy = repo.** Cross-atom synteza jest brain-owned; pojedyncze
  atomy zostają w repo i są LINKOWANE (nie kopiowane) — anty-dryf.

## Status

| Element | Stan | Gdzie |
|---------|------|-------|
| Vault PARA | ✅ założony | `.../Documents/AI` |
| Repo szkielet | ✅ gotowy | tutaj |
| Telegram capture | ✅ działa (bot @mjchiefbot, launchd) | `connectors/telegram/` |
| Notion connector | ✅ spec + konwencja | `connectors/notion/` |
| JIRA connector | ✅ spec + demo pull (SHELF) | `connectors/jira/` |
| Rodzina `/brain-*` (10 komend) | ✅ zadania · pamięć · status · knowledge (globalne) | `.claude/commands/` → `~/.claude/commands/` |
| Skill `brain-conventions` | ✅ dyscyplina destylacji + konwencje brain | `.claude/skills/` → `~/.claude/skills/` |
| Agent `brain-manager` | ✅ thin router (izolacja ciężkich operacji brain) | `.claude/agents/` → `~/.claude/agents/` |
| Warstwa statusu (`status:auto`) | ✅ auto-blok, rollup 3-poziomowy | `_system/templates/status-block.md` |
| Knowledge-system | ✅ mózg = źródło (canon/emerging/mirror) + pre-commit | `scripts/`, `_system/knowledge-system.md` |
| SessionStart hooki | ✅ inject kontekstu + regen snapshotów wiedzy | `hooks/session-start-*.sh` |
| Konteksty wiedzy (`active`) | scandit · shadow-operator · agency · claude-dev | `config.json` `.knowledge` |
| n8n / `/brain-digest` | ⬜ todo | `n8n/` |

**Uwaga — konteksty:** `.paths` (brain-loadable projekty) obejmuje scandit + repa marketing/agency.
`claude-dev` jest kontekstem **knowledge-only** (jego skille konsumują snapshoty wiedzy; nie ma
projektu-vaulta `01-Projects/claude-dev`) — celowo bez wpisu `.paths`, obsługiwany przez knowledge-sync
w swoim repo, nie przez `/brain-load`.

Pełny projekt: `docs/architecture.md`. Mapa kontekstów: `docs/contexts.md`.

## Layout referencyjny

**Skrypty (`scripts/`):**

| Skrypt | Do czego |
|--------|----------|
| `link-commands.sh` | Symlinkuje artefakty brain do `~/.claude/`: komendy (`commands/*.md`), skille (`skills/*/`), agentów (`agents/*.md`). Idempotentny, `--dry-run`, nie nadpisuje zwykłych plików. Odpal po dodaniu dowolnego artefaktu. |
| `brain-scan.py` | Read-only diagnostyka vaultu (broken wikilinks, orphan, stale dates, big files) — zasila `/brain-sync` Fazę 1. |
| `sync-knowledge.py` | Snapshot wiedzy vault→skille (EXTRACT) + integrity (`--check` exit 1 dryf / 2 dangling; orphan advisory). |
| `knowledge-init.sh` | Hydraulika `/brain-knowledge-init` (katalog + `active:true` + pre-commit). Idempotentny. |
| `install-precommit.sh` | Pre-commit pilnujący spójności knowledge w repo-konsumencie. |
| `run-telegram-capture.sh` + `com.mjucha.brain.telegram.plist` | Bot Telegrama (launchd) — capture do `00-Inbox`. |
| `tests/` | Testy silnika knowledge-system. |

**Hooki (`hooks/`):**

| Hook | Do czego |
|------|----------|
| `session-start-brain.sh` | Wstrzykuje (read-only) pamięć projektu + `_MOC.md` + `SESSION.md` + notatkę ticketu przy starcie sesji. |
| `session-start-knowledge.sh` | Regeneruje snapshoty wiedzy przy dryfie (konteksty `active`). |
| `install.sh` / `install-knowledge.sh` | Rejestrują hooki w `~/.claude/settings.json`. |

**Skill/agent brain:** `brain-conventions` (skill) i `brain-manager` (agent) mieszkają w
`.claude/skills/` i `.claude/agents/` tego repo (wersjonowane) i są symlinkowane do `~/.claude/`
przez `scripts/link-commands.sh` (obsługuje komendy, skille i agentów jednym przebiegiem).
