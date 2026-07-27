---
description: Connect the current folder to the brain — load project memory + deep repo memory
argument-hint: [context]
allowed-tools: Read, Write, Bash, Grep, mcp__claude_ai_Atlassian__searchJiraIssuesUsingJql, mcp__claude_ai_Atlassian__getJiraIssue
---

# /brain-load — podłącz ten folder do mózgu

Wczytuje wiedzę o projekcie, w którym pracujesz, żeby Claude miał pełny obraz: **portfolio**
(pamięć projektu w vaulcie, wysoka półka) + **głęboki** (repo `CLAUDE.md`/`memory.md`).
Uruchamiana z DOWOLNEGO folderu (komenda globalna). Para z `/brain-update`.

Repo mózgu (config/ścieżki): `/Users/marcinjucha/Prywatne/projects/claude-brain`.

## Zbieranie danych (jedna paczka)
Discovery Fazy 0 + Fazy 2 leci JEDNYM wywołaniem shella, nie serią round-tripów:
- `pwd` + `git branch --show-current` (toleruj „not a git repository" — kontekst może być bez repo)
- listing rozwiązanego vaulta PŁASKO **i** o jeden poziom głębiej (foldery podmiotów):
  `ls <vault>` + `ls <vault>/*/` (albo `ls -R <vault>` z capem) — vault ma notatki płaskie
  OBOK folderów podmiotów (np. `agency/`: `justyna-kancelaria/`, `social-media/` + płaskie `oferta-*.md`).
- obecność `SESSION.md` w cwd
- `git worktree list`, gdy repo ma worktree
Zasada: JEDNA paczka, potem czytaj TYLKO te notatki, których wymaga zadeklarowany focus/ticket
— nie zrzucaj całego vaulta do kontekstu.

## Faza 0 — wykryj projekt + ticket
1. `pwd`. Dopasuj do `config.json` → `paths` (najdłuższy pasujący prefiks ścieżki).
   - Trafienie → masz `context`, `vault` (podfolder), `memory` (plik pamięci), `repoMemory`.
   - Brak → użyj `$1` jako kontekstu, albo zapytaj.
   - **Zadeklarowany kontekst > cwd (KRYTYCZNE):** jeśli użytkownik wskazał kontekst w promptcie
     (np. „halo efekt", „agency", „shadow-operator"), MA ON PIERWSZEŃSTWO — mapowanie cwd to tylko
     DOMYŚLNY kontekst, gdy nic nie zadeklarowano. Rozwiąż zadeklarowany kontekst na `vault`/`memory`
     w TEJ kolejności: (1) NAJPIERW znormalizuj synonim przez `paths[<cwd>].contextAliases`
     (np. „halo efekt"→`agency`); (2) rozwiąż nazwę kanoniczną przez `paths[<cwd>].contexts[<nazwa>]`
     (repo wielokontekstowe, `multiContext: true`) → daje `vault`/`memory` JEDNOZNACZNIE, preferuj to;
     (3) DOPIERO gdy repo nie ma `contexts` → dowolny wpis `paths` z tym `context`; ⚠️ krok 3 jest
     niejednoznaczny (`agency` ma 2 wpisy: `legal-mind`=`_halo-efekt.md` vs `doc-forge`=`_doc-forge.md`)
     — `contexts` z kroku 2 to rozstrzyga, NIE zgaduj z kroku 3. (Np. cwd `claude-marketing` domyślnie =
     `shadow-operator`, ale „halo efekt"→`agency`, vault `01-Projects/agency`, `_halo-efekt.md`.)
2. **Ustal ticket** (gdy kontekst ma tracker z ID w nazwie gałęzi): `git -C <cwd> branch --show-current`
   → wzorzec ID zależy od trackera kontekstu, NIE zakładaj `SHELF-` poza JIRA: kontekst JIRA
   (`scandit`) → `SHELF-[0-9]+` (np. `feature/SHELF-23428-...` → `SHELF-23428`); konteksty
   Notion/Trello mają notatki nazwane slugiem, bez ID w gałęzi → **brak ticketa to normalny stan,
   nie błąd**: pomiń backfill (Faza 2.5) i pracuj po slugu/focusie. Jak wywołane z
   `/ios-feature <TICKET>` — użyj tego argumentu. Brak gałęzi/repo → też pomiń backfill.

## Faza 1 — wczytaj górny poziom (mózg)
- Przeczytaj `vault.path`/`<vault>`/`<memory>` (np. `01-Projects/scandit/_scandit.md`) — status,
  co w toku, jak się łączy.
- Jeśli ticket wykryty (Faza 0 pkt 2) — NAJPIERW przeczytaj W CAŁOŚCI jego własną notatkę
  roboczą jako PODSTAWOWĄ notatkę tego worktree: `<vault>/<TICKET>*.md` (także wewnątrz
  folderów podmiotów `<vault>/<subject>/<TICKET>*.md`). To lustro rozwiązania
  worktree→ticket→notatka z hooka SessionStart.
- Przeczytaj powiązane working notes (linki w pamięci projektu / pliki w `<vault>` —
  także wewnątrz folderów podmiotów `<vault>/<subject>/`).

## Faza 2 — wczytaj dolny poziom (repo)
Trwała wiedza repo = **CLAUDE.md + skille**; `memory.md` to bufor uczenia z sesji (staging).
- Przeczytaj `CLAUDE.md` (reguły, dojrzałe konwencje) i — gdy istotne — skille w `.claude/skills/`.
- Przeczytaj `memory.md` jako świeże, jeszcze niepromowane lekcje.
- Jeśli istnieje `SESSION.md` w worktree — wczytaj (ulotny stan bieżącej gałęzi).
- Jeśli `config.json` `.knowledge[<context>].active == true` → uruchom `python3 /Users/marcinjucha/Prywatne/projects/claude-brain/scripts/sync-knowledge.py --context <context> --check` (READ-ONLY, nic nie zapisuje). Zbierz: dryf (ile snapshotów nieaktualnych), dangling, kandydaci-duplikaty, sieroty, used-by-stale, notatki `emerging`. Kontekst nieaktywny → pomiń.

## Faza 2.5 — auto-backfill notatki ticketu (BEZ pytania)
Jeśli ticket wykryty (Faza 0) **i** nie istnieje notatka `<TICKET>*.md` — ani płasko w
`<vault>`, ani wewnątrz folderu podmiotu `<vault>/<subject>/`:
- **Automatycznie** pobierz TEN JEDEN ticket z JIRA (nie pytaj — preferencja potwierdzona).
  Logika jak w `/brain-pull`, ale single-item: `searchJiraIssuesUsingJql` z
  `cloudId` z config (`connectors.jira.cloudId`), JQL `key = <TICKET>`, pola
  `summary,status,issuetype,priority,updated,description` — albo `getJiraIssue` po kluczu.
- Scaffolduj notatkę z `_system/templates/working-note.md`: gdy podmiot ma już folder lub
  klaster >1 notatki → do `<vault>/<subject>/<TICKET>-<slug>.md` (utwórz folder, jeśli brak);
  dla pojedynczego, izolowanego ticketu → płasko do `<vault>/<TICKET>-<slug>.md`:
  frontmatter (`tracker: jira`, `task_id`, `task_url`=`https://<site>/browse/<TICKET>`, `task`,
  `status` LUSTRO z trackera, `priority`, `project`, `context`, `updated`=dziś, tags) + sekcja
  **Kontekst** (summary + opis + acceptance criteria) + **Detal** zostaw pusty (pisze user).
- Jeśli notatka już istnieje → nic nie rób (tylko ją wczytaj w Fazie 1/2).

## Faza 2.6 — reconcile SESSION.md ↔ pamięć projektu
`SESSION.md` żyje per worktree, a worktree jest per ticket/podmiot — więc bierz pod uwagę TEŻ
`SESSION.md` w SIOSTRZANYCH worktree tego repo (`git worktree list`), nie tylko w cwd. Tanio:
siostrzany `SESSION.md` czytaj tylko gdy jego worktree/branch jest jedną z pozycji, które mózg
trzyma jako otwarte, ALBO gdy jest świeższy niż `updated:` pamięci projektu.
Jeśli którykolwiek `SESSION.md` wspomina tickety/pracę/etapy, których NIE ma w górnej pamięci
`<memory>` (np. `_scandit.md`):
- Zasygnalizuj: **„brain stale vs SESSION.md"** + wypisz deltę (czego brak / co nieaktualne na wysokiej półce).
- **NIE edytuj bloku `status:auto` ręcznie (TWARDA REGUŁA).** Blok jest generowany z
  `_system/templates/status-block.md` i oznaczony `<!-- status:auto — … nie edytuj ręcznie -->`.
  `/brain-load` tylko RAPORTUJE deltę i przekazuje ją do `/brain-update`, które jest właścicielem
  regeneracji — nie przepisuje bloku samo.
- Detal techniczny NIE idzie tu — to robi `/brain-update` (SESSION.md → notatka ticketu).

## Faza 2.7 — drift check (mózg vs ground truth)
READ-ONLY porównanie: co warstwa statusu `<memory>` twierdzi, że jest „w toku / w review",
vs ground truth TEGO kontekstu. Ground truth jest per-kontekst — rozgałęź po tym, co ISTNIEJE,
i cicho pomiń brakujące źródło:
- **kontekst z repo** (`scandit`, `legal-mind`, `doc-forge`, `claude-marketing`,
  `kacper-landing-page`, `claude-dev`):
  `git log --oneline -12 origin/<default-branch>` +
  `git for-each-ref --sort=-committerdate --format='%(committerdate:short) %(refname:short)' refs/remotes/origin | head -12`
  → oflaguj (a) pozycje, które mózg trzyma jako otwarte, a są już zmergowane, (b) branche
  z aktywnością świeższą niż `updated:` pamięci.
- **brak repo / cwd nie mapuje się na wpis w `paths`** (np. `personal`, kontekst czysto vaultowy):
  ground truth = same working notes — porównaj `status:`/`updated:` z frontmattera i pola trackera
  z tym, co twierdzi blok statusu pamięci. Notatka świeższa niż `updated:` pamięci = dryf.
- **tracker (Notion/JIRA)**: OPCJONALNIE, tylko na wyraźną prośbę. `/brain-load` NIE odpytuje
  trackera domyślnie — to brief startowy, ma być tani; odpytywanie należy do `/brain-sync` / `/brain-pull`.
Awaria sieci = RAPORTUJ, nie zamiataj: jeśli `git fetch` padnie (VPN off, host nieosiągalny) —
powiedz to i zaznacz, że refy są z ostatniego fetcha. Nigdy nie podawaj stałych refów jako świeżych.
Nie fetchuj automatycznie jako krok blokujący.
Wyjście: krótka lista delt, nie raport.

## Faza 3 — przedstaw obraz
Krótko podsumuj użytkownikowi: co to za projekt, na jakim etapie, co w toku, otwarte wątki,
i czego pamięć NIE wie (luki). Wymień: czy notatka ticketu była backfillowana, czy był
reconcile SESSION.md (w tym siostrzane worktree). Bez ścian tekstu — to brief startowy, nie raport.
- dryf (Faza 2.7): krótka lista delt „mózg mówi X, ground truth mówi Y" + źródło (git refs /
  frontmatter notatek), a przy awarii sieci — z jakiej daty są refy. Zamknij zdaniem, że blok
  `status:auto` regeneruje `/brain-update`, nie ta komenda.
- knowledge: zsynch. ✅ / albo: N dryf · M dup? · K emerging · dangling: … — przy problemach dodaj, że `/brain-update` rozwiązuje je (osąd: scal duplikaty, awansuj emerging→canon). Jeśli kontekst dziedziczy pule bazowe (`inherits`) — NAZWIJ WSZYSTKIE (np. „+ general-business + general-technical (uniwersalne)", jak `agency`), by było jasne, że dostępny jest też uniwersalny craft, nie tylko noty kontekstowe.

> Pamięć projektu w mózgu = wysoka półka (status/połączenia). Głęboka wiedza techniczna
> NIE jest tu kopiowana — żyje w repo (CLAUDE.md/skille, a świeże w memory.md). Czytaj oba poziomy; nie scalaj.
