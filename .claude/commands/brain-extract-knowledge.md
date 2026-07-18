---
description: Wyekstrahuj TRWAŁĄ wiedzę domenową (cross-atom synteza „dlaczego projekt jest jaki jest") ze SKOŃCZONEJ pracy do atomowych notatek `home: brain`. Silnik; para z /brain-update. Globalna.
argument-hint: [ticket] [--sweep]
allowed-tools: Read, Edit, Write, Bash, Grep
---

# /brain-extract-knowledge — destyluj wiedzę domenową ze skończonej pracy do mózgu

Wyciąga **cross-atom SYNTEZĘ** (dlaczego produkt/domena są jakie są) ze SKOŃCZONEJ pracy (ticket/sesja)
do atomowych notatek `home: brain` w `03-Resources/<ctx>/knowledge/`, surface'owanych na starcie sesji,
linkowanych z `_MOC.md`. Siostra `/brain-update` (który trzyma status/detal roboczy). **BRAIN-ONLY** —
nigdy nie snapshotuje do skilli zespołu, repo NIETKNIĘTE.

> Źródło ZEWNĘTRZNE (call / kurs / artykuł / framework) → użyj `distill-coaching`, NIE tej komendy. Ten silnik jest do WYKONANEJ PRACY WEWNĘTRZNEJ (ticket / sesja).

To jest **SILNIK**. Główny wyzwalacz = in-loop hook w `/brain-update`; standalone = on-demand + `--sweep`
(backfill klastra zamkniętych ticketów). Kontrakt (schemat, reguła anty-dryf, forma pointer, tryby):
**`<vault>/_system/knowledge-system.md`** — czytaj, NIE przepisuj. Repo mózgu (config/skrypty):
`/Users/marcinjucha/Prywatne/projects/claude-brain`.

**Dyscyplina** (CP1–4, dwustopniowa brzytwa, dedup, verify-understanding, schemat noty) — skill **`brain-conventions`** (osiągalny w KAŻDYM kontekście; ta komenda jest samowystarczalna).

## ⭐ BRZYTWA (dwustopniowa — mechanizm centralny)

> Domena-WHY (nie mechanika kodu) decyduje o KWALIFIKACJI; atom-vs-synteza decyduje o DOMU. Brain trzyma
> tylko syntezę, której żaden pojedynczy atom repo nie niesie — resztę LINKUJE, nie kopiuje.

Dla KAŻDEGO kandydata:

**Stopień 1 — bramka kwalifikacji.** Wszystkie TRZY muszą zajść, inaczej → repo (`memory.md`/CLAUDE.md/skill), NIE brain:
1. **DURABLE** — ustalone, NIE prowizoryczne / NIE `[do potwierdzenia]` / nie czeka na dowód on-device.
   - **Wyjątek: NOTA-WYMAGANIE** (kontrakt behawioralny „jak widget/ficzura ma się zachowywać"): dopuszczalna, gdy przechodzi trwała ZASADA, mimo rewidowalnych szczegółów — pod warunkiem struktury §Zasada / §Kontrakt (rewidowalny, każda reguła z WHY) / §Autorytet (źródło prawdy = tracker/PM, nota = zrozumienie inżynierii). Pełna definicja: skill `brain-conventions` §„Rodzaj wiedzy: NOTA-WYMAGANIE".
2. **CROSS-TICKET RELEVANT** — ktoś na przyszłym, niepowiązanym tickecie chciałby to mieć wyświetlone.
3. **DOMENA/PRODUKT/FIZYKA-WHY** — nie mechanika kodu (konwencja kodowania / użycie API / reguła repo → CLAUDE.md/skill).
- ⚠️ **NIE klasyfikuj po trybie gramatycznym.** Tryb rozkazujący („musi/zawsze/nigdy") NIE znaczy mechanika-kodu —
  reguły domenowe tego projektu bywają rozkazujące (np. „nigdy nie kalibruj bramki na odtworzonych pozycjach",
  „mierz prostopadle-do-prostej w świecie XZ"). Klasyfikuj po SUBSTANCJI (domena/produkt/fizyka vs struktura-kodu), nie po czasowniku.

**Stopień 2 — decyzja o domu (bramka ROZSTRZYGAJĄCA).** Z kwalifikowanych pytaj: czy to POJEDYNCZY, zakotwiczony ATOM,
który już żyje w repo (jeden próg, jeden bug, jedna reguła-pliku)?
- TAK → zostaje w repo; notatka mózgu może go tylko `references:`-linkować, NIGDY kopiować. BRAK osobnej notatki.
- NIE — czy to SYNTEZA obejmująca ≥2 atomy, której NIE niesie żadna pojedyncza lokalizacja repo? → **notatka mózgu**.
- „obejmuje ≥2 atomy" = cross-ATOM, nie dosłownie cross-ticket. POJEDYNCZY ticket może dać syntezę, jeśli łączy ≥2 wcześniej osobne atomy repo.

## Reguła warstwy (dual-source / anty-dryf)

- Brain = ŚCIŚLE INNA WARSTWA (cross-atom synteza), NIE re-hosting lekcji repo.
- **„Own the synthesis, link the atom."** Nigdy nie powtarzaj zmiennych atomów (progi, snippety, dokładne brzmienie buga) — linkuj je.
  Test per-zdanie: „czy to zdanie może zdezaktualizować się NIEZALEŻNIE od repo? TAK → to skopiowany atom → ZABRONIONE (zamień na wskaźnik)."
- Ekstrakcja jest ŚCIŚLE ADDYTYWNA + READ-ONLY względem repo. NIGDY nie usuwaj/przenoś nic z `memory.md`/CLAUDE.md/skilli
  (przeniesienie repo→brain sprywatyzowałoby wiedzę współdzieloną z zespołem). Odchudzanie bufora jest POZA ZAKRESEM (należy do `/ai-curate-memory` wewnątrz repo).

## Status + decay

- `status: emerging` (default) — synteza opiera się na JEDNYM świeżo zamkniętym tickecie (może jeszcze zostać obalona — np. shadow-mode czekający na walidację fizyczną).
- `status: canon` — utrzymane na **N≥3 odrębnych ŹRÓDŁACH** (tickety / atomy / twórcy — wg kontekstu) ORAZ zweryfikowana.
- Obalenie później → `status: superseded-by [[nowa-notatka]]`, NIGDY cichy delete (to, że coś było wierzone i obalone, samo jest trwałą wiedzą — filozofia dead-endów vaulta).
- Fragmenty `[do potwierdzenia]` są z konstrukcji ZABRONIONE w brain (nie przechodzą Stopnia 1 / durability).
- Decay łapany przy ODCZYCIE przez `brain-sync --deep`, nie przy zapisie — komenda ma tylko ostemplować proweniencję, by audyt mógł działać.

## Schemat notatki (kontrakt + te dodatki)

`type: knowledge`, `context: <ctx>`, `id: <slug>` (kebab-case ASCII, ≥2 znaki, bez wiodącej cyfry),
`status: emerging|canon`, `home: brain`, `source: SHELF-XXXXX` (ticket źródłowy), `created: YYYY-MM-DD`,
`updated: YYYY-MM-DD`, `references:` (lista ścieżek/kotwic repo, z których synteza czerpie — kotwica DRIFT-AUDIT,
jawnie NIE `mirror-source`, brak synca), `used-by:` (zostaw puste — własność narzędzia), `superseded-by:` (tylko przy obaleniu).
Ciało: atomowe, tytuł = teza; dla decyzji dodaj „Stosuj gdy / nie gdy"; linkuj hojnie `[[slug]]`.

---

## Faza 0 — wykryj kontekst + ticket

`pwd` → dopasuj do `config.json` `.paths` (najdłuższy prefiks; **kontekst zadeklarowany > cwd**, logika jak `/brain-update` Faza 0).
Rozwiąż `<vault>` i `knowledge[<ctx>].dir`. Potwierdź, że `knowledge[<ctx>]` istnieje w configu.
Ticket: `git -C <cwd> branch --show-current` → regex `SHELF-[0-9]+`, albo `$1`.
Tryb `--sweep`: przyjmij LISTĘ/klaster kluczy ticketów zamiast jednego.

## Faza 1 — zbierz JUŻ-ZDESTYLOWANE źródła (INGEST, read-only)

Czytaj w kolejności wiarygodności: sekcje domenowe repo `memory.md` (`## Domain Concepts`, `## Architecture Decisions`, `## Bugs Found`)
+ notatka robocza ticketu w `<vault>` + `SESSION.md` jeśli jest + `git log` ticketu (potwierdza CO shipnięto, kotwiczy traceability).
**Preferuj źródła już zdestylowane nad surową sesją** (nie powtarzaj ekstrakcji przy niższej jakości weryfikacji).
Daty względne → bezwzględne (`YYYY-MM-DD`). Nie modyfikuj żadnego źródła.

## Faza 2 — destyluj kandydatów (EXTRACT ESSENCE)

Zamień fragmenty źródeł w kandydatów: **usuń specyfikę ticketu/przypadku** do wskaźnika źródła, przeformułuj jako reużywalny wzorzec
z jawnym „Stosuj gdy / nie gdy", oznacz zasada-vs-sugestia, koduj TYLKO to, co mówi źródło (zero inwencji — dyscyplina
CP1 uniwersalność/warunkowość + CP3 no-invention/traceability: skill `brain-conventions`). Każdy kandydat: `{proponowany-slug, teza, gdy/gdy-nie, zasada|sugestia, wskaźnik(i)-źródła, references, szkic-ciała}`.

## Faza 3 — BRZYTWA + dedup (BRAMKA)

Zastosuj dwustopniową brzytwę do każdego kandydata (Stopień 1 kwalifikacja → Stopień 2 atom-vs-synteza).
Potem dedup-search w `knowledge/` (ORAZ skanuj `memory.md`/CLAUDE.md/skille za atomem, per reguła warstwy) → decyzja
**ROZSZERZ istniejącą** vs **UTWÓRZ nową** vs **ODRZUĆ** (pojedynczy atom → tylko link / route do repo). **Preferuj ROZSZERZ** (anty-eksplozja).
Fragmenty niezaliczające brzytwy: zbierz do nudge'a w raporcie, NIE zapisuj.

## Faza 4 — zweryfikuj zrozumienie (BRAMKA OBOWIĄZKOWA)

Przedstaw użytkownikowi zdestylowany model + per-kandydat {rozszerz `<slug>` | utwórz `<nowy-slug>` | odrzuć→gdzie} + status.
WSZYSTKICH kandydatów w JEDNYM restatement; akceptuj batch-confirm + per-kandydat skip. **NIGDY nie działaj dalej na ciszy.**
(Verify-understanding z dyscypliny `brain-conventions` — obowiązkowe, bo to notatki torem canon surface'owane na starcie sesji; źle zdestylowana notatka myli orientację.)

## Faza 5 — zapis (WRITE) + integralność

Per potwierdzony kandydat, w tej kolejności:
0. **Rozstrzygnij dom noty — TRÓJDZIELNIE (trzeci wymiar zapisu — test w `brain-conventions` §„Trzeci wymiar zapisu — TRZY POOLE", NIE przepisuj):** są DWIE żywe bazy uniwersalne, nie jedna. Czy teza jest venture-niezależna, i jeśli tak — biznesowa czy techniczna?
   - **Uniwersalna-BIZNES** (czysty craft sprzedaż/marketing/launch/oferta/produkt/voice-copy) **→** `03-Resources/general-business/knowledge/` (`context: general-business`) + jej `_MOC.md`.
   - **Uniwersalna-TECHNICZNA** (inżynieria/web-stack venture-niezależna — TanStack/Supabase/RLS/React + zasady stack-agnostyczne SRP/TDD/kompozycja) **→** `03-Resources/general-technical/knowledge/` (`context: general-technical`) + jej `_MOC.md`. ⚠️ Ten silnik odpala się TAKŻE w kontekstach technicznych (np. claude-dev) — ekstrakcja uniwersalno-techniczna routuje TU, nie do general-business.
   - **Specjalistyczna** (związana z tym jednym venture) **→** bieżący kontekst `03-Resources/<ctx>/knowledge/`.
   Reguła kierunkowa: nota uniwersalna linkuje TYLKO w obrębie WŁASNEGO poolu (nie w dół do noty kontekstowej, nie w bok do drugiego poolu uniwersalnego — silnik zablokuje commit). Fail-safe: domyślaj się kontekstu specyficznego; promuj do którejkolwiek bazy uniwersalnej dopiero na realny popyt 2. kontekstu. (Ustala `context:` + docelowy `dir`+`_MOC` dla kroków 1–2.)
1. Utwórz/rozszerz notatkę `<dir>/knowledge/<slug>.md` **BEZPOŚREDNIO** (plik vaulta — NIE plik-artefakt, więc NIE przez ai-manager-agent dla samej NOTATKI), schemat wyżej.
2. Zaktualizuj właściwy `_MOC.md` (bazy uniwersalnej albo kontekstu — ten sam, do którego trafiła nota) **BEZPOŚREDNIO** pod właściwą sekcją — **WYMAGANE ZAWSZE** (silnik flaguje sierotę, gdy notatka nie jest referencjonowana przez żaden skill ANI nie ma jej w `_MOC`; wpis w MOC to JEDYNY orphan-guard dla notatek brain-only).
3. `python3 /Users/marcinjucha/Prywatne/projects/claude-brain/scripts/sync-knowledge.py --context <ctx> --check` (dry-run; exit 1 dryf / 2 dangling) — **używaj `--check` WYŁĄCZNIE, NIGDY gołego przebiegu** (goły przebieg ZAPISUJE snapshoty do konsumentów-skilli zespołu → łamie brain-only); napraw dangling `[[link]]` i uruchom ponownie.
4. Finalny pass no-invention/traceability nad tym, co wylądowało.

**NIGDY: snapshot, obsługa mirror, blok `## Knowledge`, wskaźnik gdziekolwiek.** To brain-only synteza — repo pozostaje jedynym źródłem swoich atomów.

## Faza 6 — raport

- Notatki utworzone (slug + teza + status) / rozszerzone (co wmerge'owano).
- Wpisy `_MOC.md` dodane.
- Wynik `sync --check`.
- Wyniki dedup (co złożono zamiast tworzyć — transparentność anty-dryf).
- Odroczone/odrzucone (porażki brzytwy + niejednoznaczny dom) z powodami.
- Nudge lekcji repo (reguły-kodu / pułapki-arch → „rozważ `/ai-extract-memory`→`/ai-curate-memory`").
- Źródła nietknięte (jednokierunkowo).

## Obsługa niejednoznaczności

- Ticket nierozstrzygnięty (brak `SHELF-XXXXX`, kilka w grze) → NIE zgaduj; zapytaj albo weź `$1`. Brak notatki roboczej/SESSION.md → działaj na `memory.md`+`git log`, zaznacz reduced-source.
- Dom fragmentu niejednoznaczny → rozstrzygnij w Fazie 4, nigdy po cichu. Jasna synteza domenowa → brain; reguła-kodu/pułapka-arch repo → ODROCZ + nudge; niejasne po restatement → POMIŃ + wylistuj w „odroczone". Źle-zadomowiona notatka zanieczyszcza zaufaną bazę → skip-and-report bije zgadywanie.
- Remis rozszerz-vs-utwórz → preferuj ROZSZERZ, ale pokaż cel merge'a w Fazie 4 do weta.
