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

## Faza 4 — raport
Co zaktualizowano: (a) pamięć projektu (`<memory>` — status/połączenia), (b) notatka robocza
(ticketu lub encji — detal; zaznacz jeśli powstała nowa, jeśli założono/zmigrowano folder
podmiotu, LUB jeśli detalu nie zrzucono przez niejednoznaczny target), (c) blok statusu (jeśli
odświeżony — `_<context>.md` + slice w Home) + ewentualne sugestie lekcji do repo `memory.md`.
SESSION.md nietknięty.
