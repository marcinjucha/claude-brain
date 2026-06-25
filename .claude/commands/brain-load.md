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
2. **Ustal ticket** (zawsze wyprowadzalny z gałęzi/worktree): `git -C <cwd> branch --show-current`
   → regex `SHELF-[0-9]+` (np. `feature/SHELF-23428-...` → `SHELF-23428`). Jak wywołane z
   `/ios-feature <TICKET>` — użyj tego argumentu. Brak gałęzi/ticketa → pomiń backfill (Faza 2.5).

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
Jeśli worktree `SESSION.md` (wczytany w Fazie 2) wspomina tickety/pracę, których NIE ma w
górnej pamięci `<memory>` (`_scandit.md`):
- Zasygnalizuj: **„brain stale vs SESSION.md"** + wypisz deltę (czego brak na wysokiej półce).
- Wpłyń tę górną deltę (status/połączenia, nie detal techniczny) do `<memory>`, `updated`=dziś.
- Detal techniczny NIE idzie tu — to robi `/brain-update` (SESSION.md → notatka ticketu).

## Faza 3 — przedstaw obraz
Krótko podsumuj użytkownikowi: co to za projekt, na jakim etapie, co w toku, otwarte wątki,
i czego pamięć NIE wie (luki). Wymień: czy notatka ticketu była backfillowana, czy był
reconcile SESSION.md. Bez ścian tekstu — to brief startowy, nie raport.
- knowledge: zsynch. ✅ / albo: N dryf · M dup? · K emerging · dangling: … — przy problemach dodaj, że `/brain-update` rozwiązuje je (osąd: scal duplikaty, awansuj emerging→canon).

> Pamięć projektu w mózgu = wysoka półka (status/połączenia). Głęboka wiedza techniczna
> NIE jest tu kopiowana — żyje w repo (CLAUDE.md/skille, a świeże w memory.md). Czytaj oba poziomy; nie scalaj.
