---
description: Connect the current folder to the brain — load project memory + deep repo memory; z opisem zadania dogrywa też półkę wiedzy domenowej
argument-hint: [kontekst | opis zadania]
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
- kolejka w inboksie kontekstu, GDY kontekst go ma: `ls <vault>/_inbox/ 2>/dev/null | grep -v README`
  — liczba pozycji do przetworzenia. Folder nie istnieje → pusto i CICHO, to normalny stan, nie błąd.
  `README.md` jest kontraktem folderu, NIE pozycją w kolejce — nie licz go. To NIE `00-Inbox/` w
  KORZENIU vaulta (capture'y z Telegrama o nieznanym jeszcze adresie, opróżnia je `/brain-inbox`);
  `<vault>/_inbox/` jest per kontekst i na materiał o znanym adresie.
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
     niejednoznaczny (`agency` ma 2 wpisy: `agency-cms`=`_halo-efekt.md` vs `doc-forge`=`_doc-forge.md`)
     — `contexts` z kroku 2 to rozstrzyga, NIE zgaduj z kroku 3. (Np. cwd `claude-marketing` domyślnie =
     `shadow-operator`, ale „halo efekt"→`agency`, vault `01-Projects/agency`, `_halo-efekt.md`.)
   - **Sklasyfikuj `$ARGUMENTS` — JEDNA z trzech klas, nigdy kombinacja (rozstrzygnij PRZED
     resolucją):** (a) **deklaracja kontekstu** — po normalizacji (lowercase, trim) argument jest
     DOKŁADNIE nazwą kontekstu albo aliasem; (b) **deklaracja ticketu** — pasuje do wzorca ID
     trackera z pkt 2 (np. `SHELF-23428`); (c) **FOCUS** — cokolwiek innego = opis zadania/problemu.
     Dokładne trafienie (a)/(b) ZAWSZE wygrywa z interpretacją jako focus. **WHY:** goła nazwa
     kontekstu i gołe ID ticketu muszą zachować dotychczasowe zachowanie — tani brief startowy bez
     półki domenowej (Faza 2.8); inaczej każde `/brain-load scandit-shelfview` zaczęłoby ciągnąć noty, a
     `SHELF-23428` odpalałoby wybór not po ID bez treści semantycznej.
   - **Zbiór rozpoznawanych nazw = SUMA, nie tylko cwd (KRYTYCZNE):** wszystkie wartości
     `paths[*].context` + klucze `paths[<cwd>].contexts` + klucze `paths[<cwd>].contextAliases`.
     **WHY:** tylko `claude-marketing` ma `contexts`/`contextAliases` — recognizer zawężony do cwd
     uznałby `agency` wpisane z `digital-shelf-ios` za opis problemu; krok 3 powyżej i tak akceptuje
     dowolny wpis `paths` z tym `context`, więc recognizer musi być równie szeroki.
   - **Kontekst + opis zadania jednocześnie: kontekst zadeklaruj ZDANIEM W PROMPCIE**, nie wciskaj
     obu w argument („halo efekt: onboarding klienta" ⇒ NIE). Zdanie w promptcie jest już nadrzędne
     wobec cwd (reguła „Zadeklarowany kontekst > cwd" wyżej), więc `$ARGUMENTS` zostaw na sam opis.
     **WHY:** taki argument klasyfikuje się jako FOCUS, kontekst poleci z cwd i komenda CICHO dobierze
     noty z puli ZŁEGO kontekstu — a bez bramki potwierdzenia (Faza 2.8) nikt tego nie wyłapie przed
     wczytaniem.
2. **Ustal ticket** (gdy kontekst ma tracker z ID w nazwie gałęzi): `git -C <cwd> branch --show-current`
   → wzorzec ID zależy od trackera kontekstu, NIE zakładaj `SHELF-` poza JIRA: kontekst JIRA
   (`scandit-shelfview`) → `SHELF-[0-9]+` (np. `feature/SHELF-23428-...` → `SHELF-23428`); konteksty
   Notion/Trello mają notatki nazwane slugiem, bez ID w gałęzi → **brak ticketa to normalny stan,
   nie błąd**: pomiń backfill (Faza 2.5) i pracuj po slugu/focusie. Jak wywołane z
   `/ios-feature <TICKET>` — użyj tego argumentu. Brak gałęzi/repo → też pomiń backfill.

## Faza 1 — wczytaj górny poziom (mózg)
- Przeczytaj `vault.path`/`<vault>`/`<memory>` (np. `01-Projects/scandit-shelfview/_shelfview.md`) — status,
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
`<memory>` (np. `_shelfview.md`):
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
- **kontekst z repo** (`scandit-shelfview`, `agency-cms`, `doc-forge`, `claude-marketing`,
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

## Faza 2.8 — półka domenowa (WARUNKOWO: tylko gdy jest FOCUS)
- **Warunek wejścia:** Faza 0 pkt 1 sklasyfikowała `$ARGUMENTS` jako FOCUS (klasa c). Deklaracja
  kontekstu, deklaracja ticketu, brak argumentu → POMIŃ całą fazę. **WHY:** koszt czytania MOC i not
  jest OPT-IN — płacisz go tylko wtedy, gdy Marcin sam opisał, nad czym pracuje. Spójne z Fazą 2.7,
  która z tego samego powodu (brief startowy ma być tani) nie odpytuje trackera domyślnie.
- **`config.json` `.knowledge[<context>].active != true` → pomiń CICHO**, bez komunikatu. Flagę bierz
  z Fazy 2 (już tam sprawdzona) — nie sprawdzaj drugi raz i nie uruchamiaj `sync-knowledge.py`
  ponownie. **Odstępstwo od `/brain-knowledge`**, gdzie nieaktywna wiedza to twardy stop z
  komunikatem. **WHY:** tam ładowanie not JEST celem komendy, tu to opcjonalny dodatek do briefu —
  komunikat o nieaktywnej puli byłby szumem w podsumowaniu startowym.
- **Wzbogać opis problemu:** FOCUS + (gdy ticket wykryty) esencja jego notatki roboczej z Fazy 1 —
  summary / acceptance criteria. **WHY:** samo zdanie Marcina bywa skrótowe, a notatka ticketu jest
  już w kontekście — trafność wyboru rośnie za zero dodatkowego kosztu.
- **SPEC = `/brain-knowledge` (jedna definicja, zero driftu — tak jak `_system/templates/status-block.md`
  jest jedyną definicją formatu warstwy statusu). Wykonaj JEGO: „Faza 0 — rozwiąż kontekst + pulę
  wiedzy" pkt 2 (własny katalog wiedzy **oraz KAŻDA** pula z `inherits`), „Faza 1 — czytaj TANI indeks
  (MOC), nie wszystkie noty", „Faza 2 — MODELOWY wybór" i DRUGĄ POŁOWĘ „Fazy 3" (przeczytaj wybrane
  noty W CAŁOŚCI z vaulta). Jego Twardych ograniczeń NIE powtarzaj tutaj — czytaj je stamtąd;
  obowiązują bez zmian: noty z vaulta, nigdy ze snapshotów skilla; `inherits`; READ-ONLY; oraz to,
  że wiedza UZUPEŁNIA `so-agent`, nie zastępuje go.**
- **JEDYNE odstępstwo — pomiń shortlistę do potwierdzenia z pierwszej połowy jego Fazy 3: noty
  wczytuj OD RAZU.** **WHY:** puchnięcie kontekstu, przed którym broni tamto ograniczenie, w praktyce
  się nie materializuje — modelowy wybór po MOC dobiera noty trafnie, więc potwierdzanie było czystym
  tarciem na briefie startowym, nie zabezpieczeniem. **SELEKTYWNOŚCI to NIE rozluźnia: nadal klaster
  istotny dla problemu, NIGDY cała pula** — to część nośna, bo argument za pominięciem potwierdzenia
  upada w chwili, gdy wybór przestaje być selektywny. Skoro bramki nie ma, raport z Fazy 3 jest
  JEDYNYM miejscem, gdzie Marcin widzi, co weszło mu do kontekstu — jest obowiązkowy.
- Wybrana nota oflagowana w Fazie 2 jako `emerging` albo kandydat-duplikat → zaznacz to przy niej
  (nie canon), ale jej nie pomijaj. **WHY:** świeża wiedza bywa najtrafniejsza; ukrycie jej statusu
  kazałoby traktować ją jak zatwierdzoną doktrynę.

## Faza 3 — przedstaw obraz
Krótko podsumuj użytkownikowi: co to za projekt, na jakim etapie, co w toku, otwarte wątki,
i czego pamięć NIE wie (luki). Wymień: czy notatka ticketu była backfillowana, czy był
reconcile SESSION.md (w tym siostrzane worktree). Bez ścian tekstu — to brief startowy, nie raport.
- dryf (Faza 2.7): krótka lista delt „mózg mówi X, ground truth mówi Y" + źródło (git refs /
  frontmatter notatek), a przy awarii sieci — z jakiej daty są refy. Zamknij zdaniem, że blok
  `status:auto` regeneruje `/brain-update`, nie ta komenda.
- knowledge: zsynch. ✅ / albo: N dryf · M dup? · K emerging · dangling: … — przy problemach dodaj, że `/brain-update` rozwiązuje je (osąd: scal duplikaty, awansuj emerging→canon). Jeśli kontekst dziedziczy pule bazowe (`inherits`) — NAZWIJ WSZYSTKIE (np. „+ general-business + general-technical (uniwersalne)", jak `agency`), by było jasne, że dostępny jest też uniwersalny craft, nie tylko noty kontekstowe.
- `_inbox/` kontekstu — gdy pozycje SĄ: podaj ILE i WYPISZ nazwy (nazwa pliku zwykle wystarcza do
  decyzji) + jedno zdanie, że inbox jest KOLEJKĄ, nie półką: pozycja stąd ma zniknąć — zostać notatką,
  przenieść się do `resources/` podmiotu jako proweniencja, albo zostać usunięta. Kontraktu folderu tu
  NIE powtarzaj — żyje w `<vault>/_inbox/README.md` (ta sama zasada „SPEC w jednym miejscu", co w
  Fazie 2.8 odsyłającej do `/brain-knowledge`). Przetwarzanie NIE należy do tej komendy — jest
  READ-ONLY jak Fazy 2.7/2.8, decyzja per pozycja należy do sesji.
  **Zero pozycji albo brak folderu → nie pisz NIC (żadnego „inbox pusty").** **WHY:** ta sama zasada,
  co przy nieaktywnej wiedzy w Fazie 2.8 („pomiń CICHO, bez komunikatu") i przy pominiętej Fazie 2.8
  („nie dopisuj nic") — komunikat o pustej kolejce byłby szumem w briefie startowym. Cisza jest tu
  POPRAWNA, nie przeoczeniem; audyt nie ma tu czego „naprawiać".
- gdy Faza 2.8 się wykonała: **wymień noty FAKTYCZNIE wczytane, każdą z pulą pochodzenia** (własna
  pula kontekstu vs konkretna pula z `inherits`) + zaznacz `emerging`/kandydatów-duplikaty. **WHY:**
  bez bramki potwierdzenia to jedyna widoczność tego, co weszło do kontekstu — pominięcie
  potwierdzenia ma być JAWNE, nie ciche. Faza pominięta → nie dopisuj nic (żadnego „pominięto").

> Pamięć projektu w mózgu = wysoka półka (status/połączenia). Głęboka wiedza techniczna
> NIE jest tu kopiowana — żyje w repo (CLAUDE.md/skille, a świeże w memory.md). Czytaj oba poziomy; nie scalaj.
> Trzecia półka — domenowa (doktryna z vaulta) — dochodzi WARUNKOWO, tylko gdy argument to opis
> zadania (Faza 2.8), i wg SPEC-a `/brain-knowledge`, który pozostaje właścicielem jej reguł.
> Trzy osobne półki — nadal nie scalaj.
