---
description: Update the brain's project memory after working in a folder (status, done, connections)
argument-hint: [context] [note]
allowed-tools: Read, Edit, Write, Bash, Grep
---

# /brain-update — zapisz sesję do pamięci projektu

Po pracy w folderze aktualizuje **górny poziom** pamięci — plik projektu w vaulcie (status,
co zrobione, nowe połączenia). Para z `/brain-load`. Globalna.

Repo mózgu (config/ścieżki): `/Users/marcinjucha/Prywatne/projects/claude-brain`.

## Faza 0 — wykryj projekt + ticket
`pwd` → dopasuj do `config.json` → `paths` (najdłuższy prefiks). Ustal `<vault>` i `<memory>`.
Brak trafienia → użyj `$1` / zapytaj.
**Zadeklarowany kontekst > cwd (KRYTYCZNE):** kontekst wskazany przez użytkownika w promptcie
(np. „halo efekt"→`agency`, „shadow-operator") MA PIERWSZEŃSTWO nad mapowaniem cwd; cwd to tylko
domyślny kontekst, gdy nic nie zadeklarowano. Rozwiąż go na `<vault>`/`<memory>` W TEJ KOLEJNOŚCI:
(1) **znormalizuj** synonim przez `paths[<cwd>].contextAliases` (np. „halo efekt"→`agency`);
(2) rozwiąż nazwę kanoniczną przez `paths[<cwd>].contexts[<nazwa>]` (`multiContext`) — to daje
`<vault>`/`<memory>` JEDNOZNACZNIE, preferuj to; (3) DOPIERO gdy repo nie ma `contexts` — dowolny
wpis `paths` z tym `context`. ⚠️ Krok 3 bywa wieloznaczny (np. `agency` ma 2 wpisy: `legal-mind`=
`_halo-efekt.md` vs `doc-forge`=`_doc-forge.md`) — `contexts` z kroku 2 to rozstrzyga, NIE zgaduj
z kroku 3. Repo wielokontekstowe (np. `claude-marketing` = shadow-operator domyślnie + agency)
zapisuje do pamięci ZADEKLAROWANEGO kontekstu, nie cwd-domyślnego. Ticket z gałęzi (jeśli kontekst JIRA):
`git -C <cwd> branch --show-current` → regex `SHELF-[0-9]+` (jeden z możliwych kluczy
notatki w Fazie 2b; kontekst Notion używa klucza encji). Klucz notatki = **podmiot (subject)**;
gdy podmiot ma >1 powiązaną notatkę, jego notatki mieszkają w folderze `<vault>/<subject>/`
(szczegóły rozwiązania ścieżki w Fazie 2b).

## Faza 1 — zbierz co się zmieniło (źródło: TA sesja/konwersacja + dodatki)
**Główne źródło: ta sesja/konwersacja** — uniwersalne, działa wszędzie (np. dla Notion/marketingu
nie ma SESSION.md, a praca żyje w rozmowie: „przeanalizowałem Call 2 Kacpra, oto decyzje").
Z niej wyciągnij: co zrobione, decyzje (z WHY), dead-endy, otwarte pytania, „co dalej",
dotknięte pliki/encje, zmiany statusu. Dodatkowo: **+ SESSION.md jeśli istnieje** (bonus dla
iOS worktree — ulotny scratchpad gałęzi) **+ `git log` od ostatniej aktualizacji** (wsparcie).
SESSION.md NIE jest wymagany. **Tylko jednokierunkowo: sesja → mózg.** NIGDY nie zapisuj
z powrotem do SESSION.md (pozostaje pasywny — „sesja nie wie o mózgu").
Daty względne (np. „wczoraj", „dziś") zamień na bezwzględne (`YYYY-MM-DD`).

## Faza 2a — pamięć projektu / wysoka półka (status + połączenia)
W `<vault>/<memory>` (np. `_scandit.md`): odśwież sekcje **Status**, **W toku**,
**Jak się łączy**. Ustaw `updated` na dziś. Zwięźle — to mapa, nie dziennik.

**KONDENSUJ, nie akumuluj (KRYTYCZNE — najczęstszy błąd tej komendy):** aktualizacja =
**ZASTĄP** istniejący wpis nowym stanem, NIE doklejaj kolejnych zdań. Po edycji wpis ma być
**nie dłuższy niż przed** (chyba że to genuinely nowy temat). Wpis per-ticket/temat ≈ 1 akapit:
aktualny status + „co dalej" + linki (`[[working-note]]`, spawnowane tickety). Stary stan
nadpisz, nie archiwizuj obok.

**Detal techniczny NIE należy tu — idzie do notatki roboczej (Faza 2b).** Jeśli łapiesz się na
pisaniu: nazw plików/symboli, wartości/parametrów, mechanizmów, kroków procesu, list findings,
cytatów z kodu, ścieżek decyzji — to sygnał, że piszesz dziennik. Przenieś to do working note,
a w pamięci projektu zostaw jedno zdanie statusu + link. **Jeśli istniejący wpis już spuchł od
detalu — przy tej aktualizacji go skondensuj** (detal do working note), nie powielaj.

Jeśli plik nie istnieje → utwórz z analogicznej struktury co `_scandit.md`.
Tu idzie TYLKO wysoki poziom (status/postęp/połączenia), NIE detal techniczny.

## Faza 2b — notatka robocza / working detail (detal z sesji)
Roboczy detal z sesji (decyzje, dead-endy, „co dalej", dotknięte pliki/encje) wpłyń do
**notatki roboczej**. Jednostka notatki: per-TICKET dla kontekstów JIRA, per-ENCJA
(klient/twórca/prospect) dla kontekstów Notion.

**Ustal klucz notatki (target):**
- Klucz = **podmiot (subject)**: dla kontekstów JIRA ticket z gałęzi (`SHELF-[0-9]+`); dla
  kontekstów Notion **encja, nad którą pracowano** (twórca/prospect/klient). Encję rozwiąż z:
  jawnego argumentu `$2` jeśli podany; inaczej wywnioskuj z konwersacji (która encja była
  w centrum); inaczej dopasuj istniejącą notatkę w `<vault>` (także wewnątrz folderów
  `<vault>/<subject>/`) po nazwie.
- **Ścieżka (folder-per-subject):** gdy podmiot ma (lub będzie miał) >1 powiązaną notatkę —
  notatka główna + notatki zadaniowe — wszystkie mieszkają RAZEM w folderze podmiotu:
  target `<vault>/<subject>/<subject>*.md` (główna `<subject>.md`, zadaniowe `<subject>-<slug>.md`).
  - Notion: per-encja, np. Kacper → `<vault>/kacper-snela/kacper-snela.md` + `kacper-snela-*.md`.
  - JIRA / tematyczne: per-temat, gdy kilka notatek dzieli podmiot (np. ARKit → `<vault>/arkit/`).
  - **POJEDYNCZA, izolowana notatka zostaje PŁASKO** w `<vault>` (np. jednorazowy ticket
    `<vault>/<TICKET>-<slug>.md`). Folder zakłada się DOPIERO gdy płaski podmiot urośnie do
    klastra (>1 notatka) — patrz „migracja-przy-dotknięciu" niżej. Nie wymuszaj folderu z góry.

**Zapisz detal:**
- **Folder:** jeśli podmiot kwalifikuje się do folderowania (>1 notatka), a folder
  `<vault>/<subject>/` nie istnieje → utwórz go przed zapisem.
- **Migracja-przy-dotknięciu:** jeśli notatki podmiotu leżą obecnie PŁASKO w `<vault>` i tworzą
  klaster główna+zadaniowa (>1 notatka) → najpierw skonsoliduj je do `<vault>/<subject>/`
  (przenieś pliki, zachowując nazwy), DOPIERO POTEM zapisz. Pojedynczą izolowaną notatkę
  zostaw płasko.
- Notatka istnieje → dopisz/zaktualizuj sekcje **Detal techniczny / jak to robimy** i
  **Decyzje i pytania otwarte**. `updated`=dziś.
- Notatka nie istnieje, ale encja/ticket jednoznacznie zidentyfikowane → utwórz z
  `_system/templates/working-note.md` (frontmatter jak w `/brain-load` Faza 2.5) pod ścieżką
  z „Ustal klucz notatki" (`<vault>/<subject>/<subject>*.md` lub płasko dla pojedynczej),
  wypełnij detalem i **zaznacz w raporcie, że powstała nowa notatka**.
- Target niejednoznaczny / nie da się ustalić → **NIE zgaduj i nie twórz złej notatki**:
  zaktualizuj TYLKO wysoką półkę (Faza 2a) i napisz w raporcie, że working detail nie został
  zrzucony (brak jasnego targetu).
- **Wikilinki przetrwają przeniesienie:** Obsidian rozwiązuje `[[nazwa]]` po nazwie pliku
  niezależnie od folderu — działa, bo nazwy plików pozostają UNIKALNE dzięki konwencji
  `<subject>-<slug>`. Linków NIE trzeba przepisywać po migracji do folderu.
- Daty bezwzględne. Dalej jednokierunkowo — do SESSION.md nic nie wraca.

## Faza 3 — rozdziel poziomy (WAŻNE)
- **Wysoka półka (Faza 2a):** status, postęp, połączenia, „co dalej". → pamięć projektu `<memory>`.
  ZASTĘPUJ stary status, nie akumuluj; gdy wpis rośnie w detal → przenieś detal do working note.
- **Working detail (Faza 2b):** decyzje, dead-endy, dotknięte pliki, proces. → notatka robocza
  (ticketu dla JIRA / encji dla Notion).
- **Trwałe lekcje repo (NIE tu):** reguły kodu, pułapki architektury. → ścieżką
  `/ai-extract-memory` (do `memory.md`, bufor sesji) → `/ai-curate-memory` (promocja do CLAUDE.md/skilli).
  Jeśli w sesji pojawiła się taka lekcja — **zasugeruj** użytkownikowi ten zapis, nie wpisuj jej do mózgu.

## Faza 3.5 — odśwież blok statusu (WĄSKO, wg SPEC)
Jeśli ta sesja zmieniła status: zregeneruj blok `status:auto` wg `_system/templates/status-block.md`
WĄSKO — tylko (a) blok w `_<context>.md` bieżącego kontekstu i (b) slice `<!-- ctx:<context> -->`
w `Home.md`. **NIE** przeliczaj innych kontekstów ani całego Home (to robi `/brain-sync`). ZASTĄP blok
(kondensuj, nie akumuluj); treść ręczna poniżej `/status:auto` nietknięta. Huby podmiotów: odśwież linię
„**Status:**" dotkniętego podmiotu. WHY: brain-update jest ŹRÓDŁEM statusu na bieżąco, brain-sync go tylko
spina i roluje — jeden format (SPEC) = brak dryfu.

## Faza 3.7 — utrzymanie bazy wiedzy (knowledge-system)
Dwa zakresy o ROZDZIELNYM gatowaniu:
- **EXTRACT** (kroki 1, 2a/2b/2c-emerging, 3) — uruchom TYLKO gdy `config.json` `.knowledge[<context>].active == true`.
- **Maintenance ODBIĆ** (krok 2-reflection) — uruchom ZAWSZE, gdy kontekst ma jakiekolwiek notatki `status: reflection` (lub legacy `status: mirror`), NIEZALEŻNIE od `active`. WHY: kontekst może mieć odbicia do odświeżenia (np. claude-dev ma odbicia skilli meta) niezależnie od EXTRACT-u — `reflection-stale` trzeba naprawić nawet gdy EXTRACT nieaktywny. (Uwaga o scandit: config ma `active: true`. Snapshot-sync jest de-facto NO-OPEM dla kontekstów brain-only / reflection-only / pointer-only — skille zespołu nie mają bloku `## Knowledge`, więc silnik ich NIE snapshotuje — dlatego `active: true` jest bezpieczne. Konsekwencja: hook Fazy 3.8, bramkowany `active==true`, DZIAŁA dla scandit.)

Jeśli EXTRACT aktywny (`active == true`):
1. Uruchom `python3 /Users/marcinjucha/Prywatne/projects/claude-brain/scripts/sync-knowledge.py --context <context> --used-by` — regeneruje snapshoty + przepisuje `used-by` w notatkach mózgu + raport integralności.
2. **Osąd agenta** (to, czego skrypt nie zrobi automatycznie) na podstawie raportu:
   - **kandydaci-duplikaty (dup?):** oceń, czy to ta sama idea; jeśli tak — scal (przenieś treść do jednej notatki, zaktualizuj `[[linki]]` i wskaźniki, usuń drugą), wg reguły anty-dryf z `_system/knowledge-system.md`.
   - **emerging → canon:** dla notatek `status: emerging` (home=brain) sprawdź, czy wzorzec utrzymał się na **N≥3 odrębnych ŹRÓDŁACH** (twórcy / tickety / atomy — wg kontekstu; np. kontekst JIRA jak scandit promuje po ticketach/atomach; zapisane slugi przypadków w ciele notatki); jeśli tak — zmień `status` na `canon`.
   - **notatki `status: reflection` (i legacy `status: mirror`) — maintenance ODBIĆ (URUCHOM ZAWSZE, niezależnie od `active`; patrz nagłówek fazy):** NIE awansuj (nigdy nie stają się brain-canon), NIE scalaj, NIE rozwijaj w nich treści — odbicie to ODBICIE skilla. **Przy `reflection-stale` (z raportu integralności, gdy aktywny; inaczej z heurystyki mtime: `reflects-source` — z fallbackiem na legacy `mirror-source` — nowszy niż notatka) ODŚWIEŻ odbicie SAM — to robi agent brain-update, NIE zalecaj użytkownikowi:** przeczytaj AKTUALNY skill-źródło z `reflects-source`, zregeneruj noty-odbicia BEZSTRATNIE ATOMOWO (re-ekstrakcja skill→brain), bump `updated`. Nadpisanie jest BEZPIECZNE — reguła develop gwarantuje, że w odbiciu NIE ma własnej wiedzy (net-nowa wiedza żyje w osobnej notatce `home: brain`). Net-nowa wiedza z sesji idzie więc do `home: brain`, NIGDY do odbicia. W raporcie: „odświeżono odbicie X ze skilla" (patrz `_system/knowledge-system.md` §„Tryb REFLECT"). **Notatki `status: pointer` (link-only stub, zero wiedzy) — NIE odświeżaj wiedzą; utrzymaj tylko poprawny link/gist.**
   - **dangling / sieroty:** napraw (dangling = krytyczne; sierota = rozważ link z MOC albo usuń). Notatki `status: reflection` / `pointer` (i legacy `mirror`) są legalnie bez-konsumenta (engine wyłącza je z orphan-check) — NIE traktuj odbicia/pointera jako sieroty do usunięcia.
3. Zaktualizuj `_MOC.md` kontekstu, jeśli doszły/zniknęły notatki.
   - **Nota UNIWERSALNA (venture-niezależny craft):** jeśli sesja utworzyła LUB awansowała notatkę uniwersalną, jej wpis w `_MOC.md` oraz każdy awans emerging→canon należą do MOC WŁAŚCIWEJ PULI BAZOWEJ — `general-business` (craft biznesowy) ALBO `general-technical` (craft inżynieryjny/web-stack) — wg testu trójdzielnego w `brain-conventions` §„Trzeci wymiar zapisu — TRZY POOLE", NIE do MOC bieżącego kontekstu. Są DWIE żywe bazy uniwersalne, nie jedna.
   - **Promocja kontekst → baza uniwersalna (mechanizm):** gdy nota dojrzała do promocji z kontekstu do bazy, NIE rób ręcznego `git mv`. Uruchom `python3 /Users/marcinjucha/Prywatne/projects/claude-brain/scripts/promote-to-universal.py` (przenosi notę + przepisuje `context:` + przenosi wpis MOC + guard: odmawia przy naruszeniu reguły kierunkowej), potem `python3 …/scripts/sync-knowledge.py --all --used-by` (resync snapshotów + `used-by` we WSZYSTKICH kontekstach dziedziczących bazę), na końcu `…/sync-knowledge.py … --check` (dry-run: exit 1 dryf / 2 dangling). WHY: promocja rusza notę między poolami i musi przenieść MOC + nie złamać reguły kierunkowej — skrypt robi to atomowo, ręczne `mv` gubi wpis MOC i omija guard.

EXTRACT nieaktywny (`active != true`) → pomiń kroki 1, 3 i podpunkty emerging/dedup, ale **wykonaj maintenance odbić (krok 2-reflection), jeśli kontekst ma notatki `status: reflection` (lub legacy `mirror`)**. Brak jakichkolwiek notatek (w tym odbić) → pomiń całą fazę (jedno zdanie w raporcie).

## Faza 3.8 — surfacing kandydatów wiedzy (in-loop hook do silnika)
Jeśli `knowledge[<ctx>].active == true`: po zapisach statusu/notatki roboczej wykonaj TYLKO **tani pre-filtr Stopnia 1**
(brzytwa z `brain-conventions`) nad JUŻ-zebranym materiałem sesji, by wskazać **0–3 prawdopodobnych KANDYDATÓW** na
notatki domenowe. **Ta faza wyłącznie SURFACE'UJE** — NIE stosuj tu pełnej brzytwy (Stopień 2 / atom-vs-synteza),
NIE dobieraj finalnego brzmienia, NIE bramkuj i NIE zapisuj.
**PRZEKAŻ kandydatów do silnika `/brain-extract-knowledge`** — silnik jest JEDYNYM właścicielem pełnej brzytwy,
verify-confirm (jego Faza 4) i zapisu (Faza 5). **Jest DOKŁADNIE JEDNO potwierdzenie — w silniku — nie dwa.**
Lekko: **0 kandydatów to poprawny, częsty wynik** — powiedz to.
WHY: standalone opt-in zamiera (dowód: nudge Faza 4(e) → 0 notatek); adopcja bierze się z wpięcia surfacing-u w komendę,
którą i tak odpalasz z nawyku. Dawniej ta faza dublowała bramkę silnika (propozycja tu + verify tam) i podwójnie
męczyła użytkownika — teraz surface-tu, bramka-w-silniku.

## Faza 4 — raport
Co zaktualizowano: (a) pamięć projektu (`<memory>` — status/połączenia), (b) notatka robocza
(ticketu lub encji — detal; zaznacz jeśli powstała nowa, jeśli założono/zmigrowano folder
podmiotu, LUB jeśli detalu nie zrzucono przez niejednoznaczny target), (c) blok statusu (jeśli
odświeżony — `_<context>.md` + slice w Home) + ewentualne sugestie lekcji do repo `memory.md`.
(d) utrzymanie wiedzy: ile snapshotów zsynch., co scalono/awansowano/naprawiono (lub 'pominięto — brak aktywnej wiedzy').
(e) **nudge wiedzy domenowej:** jeśli bufor repo `memory.md` zawiera wpisy `## Domain Concepts`
/ `## Architecture Decisions` wyglądające na cross-atom SYNTEZĘ (obejmuje ≥2 atomy, żadna pojedyncza
lokalizacja repo jej nie niesie) — zanotuj: „memory.md ma wiedzę domenową — rozważ
`/brain-extract-knowledge`, aby wyekstrahować ją do NOTATEK mózgu (`03-Resources/<ctx>/knowledge/`)."
Pojedyncze, atomowe reguły-kodu/pułapki-arch idą osobno przez `/ai-curate-memory` (do CLAUDE.md/skilli),
NIE do mózgu. (brain-update tu NIE promuje — tylko sygnalizuje ten okresowy następny krok; główny wyzwalacz to Faza 3.8.)
SESSION.md nietknięty.
