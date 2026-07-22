---
name: brain-conventions
description: Konwencje pracy z mózgiem + wspólna dyscyplina destylacji wiedzy — brzytwa, dwie półki, jednokierunkowość, home/status/reflection (reflection/pointer/legacy-mirror), 4 twarde ograniczenia destylacji, schemat noty. Ładowana przez /brain-extract-knowledge, distill-coaching, brain-manager.
---

# brain-conventions — konwencje mózgu + wspólna dyscyplina destylacji

Jedyny osiągalny (context-agnostic) dom dla (1) konwencji pracy z mózgiem oraz (2) wspólnej DYSCYPLINY DESTYLACJI, którą konsumują ZARÓWNO `/brain-extract-knowledge` (wiedza z własnej pracy), JAK i `distill-coaching` (wejścia zewnętrzne). Skill jest ładowalny z dowolnego kontekstu — globalna komenda nie może zależeć od skilla lokalnego dla jednego kontekstu.

**Pełny kontrakt (schemat noty, snapshot, dedup, REFLECT, POINTER, promocja):** `<vault>/_system/knowledge-system.md`. Ten skill WSKAZUJE kontrakt, nie przepisuje go.

---

## Część 1 — Konwencje operacyjne mózgu

- **Dwie półki.** Wysoka: pamięć projektu `_<ctx>.md` + working notes — status / połączenia / detal roboczy, mutowalne, kondensowane. Głęboka: `03-Resources/<ctx>/knowledge/` — trwała, atomowa synteza „dlaczego domena jest jaka jest". WHY: mieszanie statusu z trwałą syntezą degraduje oba — status puchnie, synteza się starzeje razem z ticketem.

- **Dwie drabiny pamięci + crossover.** Repo-drabina (zespołowa): `/ai-extract-memory` → `memory.md` → `/ai-curate-memory` → `CLAUDE.md`/skille. Brain-drabina (prywatna): `/brain-update` → pamięć projektu / working note → `/brain-extract-knowledge` → noty wiedzy. **Crossover:** pojedynczy zakotwiczony atom → repo; cross-atom SYNTEZA → brain. Reguła: **„Own the synthesis, link the atom"** — brain trzyma tylko syntezę, której żadna pojedyncza lokalizacja repo nie niesie, resztę linkuje.

- **home / status / reflection** (skrót; pełne definicje: kontrakt §Schemat, §Tryb REFLECT, §Tryb POINTER):
  - `home: brain` — mózg jest źródłem prawdy (brak pola = default `brain`).
  - `home: <skill>` — źródłem wciąż jest skill (jeszcze niezmigrowany albo zespołowy); nota jest odbiciem, NIE oznaczaj `canon`.
  - `status: reflection` — ATOMOWE odbicie skilla zespołu/zewnętrznego (skill NIETKNIĘTY, skill = źródło; `reflects-source`); NIE rozwijaj wiedzy w miejscu (refresh skill→brain ją nadpisze) — net-nowa wiedza idzie do osobnej noty `home: brain`.
  - `status: pointer` — link-only stub (tytuł + gist + link do żywego skilla, ZERO wiedzy w ciele); nie odświeża się wiedzą.
  - `status: mirror` — LEGACY/wycofany (gruba kopia całego skilla w jednym pliku); zastępowany przez `reflection`, silnik traktuje jak reflection.
  - `emerging` → `canon` po utrwaleniu (kryterium promocji — kontrakt / komenda).

- **Jednokierunkowość session → brain.** Nic nie wraca do `SESSION.md` (sesja pozostaje pasywna — „sesja nie wie o mózgu").

- **Condense-not-accumulate (wysoka półka).** Aktualizacja = ZASTĄP stary stan, nie doklejaj. Po edycji wpis nie dłuższy niż przed. WHY: to najczęstszy błąd — mapa staje się dziennikiem.

- **Additive / read-only wobec repo.** Ekstrakcja do mózgu NIGDY nie usuwa/przenosi z `memory.md`/`CLAUDE.md`/skilli. WHY: przeniesienie repo → brain sprywatyzowałoby wiedzę współdzieloną z zespołem.

---

## Część 2 — Wspólna DYSCYPLINA DESTYLACJI

Ta część jest load-bearing centralizacją: to na nią wskazują OBAJ destylerzy (`/brain-extract-knowledge`, `distill-coaching`). Forma uniwersalna, agnostyczna kontekstowo.

### Cztery twarde ograniczenia

- **CP1 — UNIWERSALNOŚĆ.** Output ZAWSZE uniwersalny + jawne „Stosuj gdy / nie gdy". Flaguj zasada-vs-sugestia. WHY: jeden przypadek zakodowany jako reguła chybi na następnym; bezpieczna jest tylko forma warunkowa.
  - **Paradygmat SPRZECZNY z kanonem.** Gdy źródło pochodzi z paradygmatu przyległego, ale SPRZECZNEGO z kanonem — wyekstrahuj tylko UNIWERSALNY RDZEŃ, ODRZUĆ technikę kontekstową, która przeczy kanonowi, i ogródź notę TWARDYM „nie gdy" (nigdy ciche pominięcie). WHY: naiwna destylacja przemyca technikę, która skaża kanon, jeśli można ją później zastosować tam, gdzie nie wolno.
- **CP2 — KONKRETNE PRZYPADKI → `references/`, nie ciało.** Nazwany przypadek/twórca/nisza = ILUSTRACJA, nie kanon; żyje w `references/` skilla docelowego (albo w nocie mózgu oznaczonej jako przykład), nigdy w głównym ciele. WHY: ciało zostaje signal-only i uniwersalne.
- **CP3 — NO-INVENTION + TRACEABILITY.** Koduj TYLKO to, co źródło mówi; zero fabrykowanych metryk/cytatów. Zachowaj wskaźnik do źródła (mówca + timestamp / kotwica sekcji / ticket). Wnioskowanie operatora oznacz `[inference]`. WHY: wymyślona liczba/cytat po cichu zatruwa bazę, której ufają artefakty downstream.
- **CP4 — ZAPIS ARTEFAKTÓW przez `ai-manager-agent`.** Pliki-artefakty (`skills/**/SKILL.md`, `agents/*.md`, `commands/*.md`) pisze WYŁĄCZNIE subagent `ai-manager-agent`; równoległe zapisy partycjonuj po pliku. **Noty vaulta (`03-Resources/<ctx>/knowledge/*.md`, working notes, `_MOC.md`) NIE są plikami-artefaktami → pisz je BEZPOŚREDNIO.** WHY: standing rule repo — orkiestrator nie pisze plików-artefaktów inline nawet z pełnym kontekstem; racjonalizacje („prościej", „mam kontekst") nie znoszą MUST.

### Dwustopniowa brzytwa (kwalifikacja wiedzy → dom)

Wspólna definicja, do której odnosi się `/brain-extract-knowledge`:

- **Stopień 1 — kwalifikacja.** Wszystkie trzy muszą zajść, inaczej → repo (nie brain): (a) DURABLE (ustalone, nie `[do potwierdzenia]`) — wyjątek: NOTA-WYMAGANIE, patrz niżej, (b) CROSS-TICKET RELEVANT (przyda się na przyszłym niepowiązanym tickecie), (c) DOMENA / PRODUKT / FIZYKA-WHY (nie mechanika kodu). ⚠️ Klasyfikuj po SUBSTANCJI, NIE po trybie gramatycznym — reguła domenowa bywa rozkazująca („nigdy…", „zawsze…") i wciąż jest domeną, nie mechaniką.
- **Stopień 2 — dom (rozstrzygający).** Pojedynczy zakotwiczony ATOM już żyjący w repo (jeden próg / jeden bug / jedna reguła-pliku) → zostaje w repo, nota mózgu może go tylko `references:`-linkować, nie kopiować. SYNTEZA obejmująca ≥2 atomy, której nie niesie żadna pojedyncza lokalizacja repo → nota mózgu.

### Rodzaj wiedzy: NOTA-WYMAGANIE (kontrakt behawioralny produktu)

Osobny rodzaj noty: „jak dany widget / ficzura / flow MA SIĘ ZACHOWYWAĆ" (kontrakt produktowy) — rozłączny z „po co flow istnieje" (domena-WHY) i z mechaniką kodu (repo). WHY: zespół często wie coś o produkcie, ale nie pamięta z PEWNOŚCIĄ jakie SĄ wymagania — nota-wymaganie to zaufane miejsce, gdzie się to sprawdza zamiast zgadywać z kodu. Generyczne dla dowolnego produktu/kontekstu (agencja, CMS, klient, app).

- **Kwalifikacja (niuans brzytwy Stopień 1a).** Wymaganie ma rdzeń TRWAŁY (zasada: dlaczego musi się tak zachowywać) + szczegóły REWIDOWALNE (konkretny kontrakt stanów). Dopuść notę, gdy przechodzi trwała ZASADA (durable + cross-ticket + produkt-WHY); rewidowalność szczegółów NIE dyskwalifikuje — pod warunkiem że są jawnie OGRODZONE (§Kontrakt) i mają linię autorytetu (§Autorytet). Bez tego niuansu brzytwa odrzuciłaby wymaganie jako „nie-durable".
- **Struktura trójdzielna (każda reguła niesie swoje WHY).** §Zasada — trwały rdzeń (przetrwa refaktory i zmianę szczegółów); §Kontrakt — rewidowalne stany/zachowania, KAŻDY z trwałym WHY (reguła może się zmienić, powód zwykle zostaje); §Autorytet — źródło prawdy = tracker/PM/product-owner, nota = ZROZUMIENIE INŻYNIERII dla orientacji (NIE wyrocznia), przy zmianie wymagań aktualizuj §Kontrakt, `references` = kotwice drift-audit.
- **Status.** `emerging` domyślnie; trwała §Zasada może awansować do `canon` po N≥3 źródłach, ale §Kontrakt zostaje rewidowalny — nigdy cicho zamrożony w canon (obalenie zachowania → aktualizacja §Kontrakt, nie `superseded-by` całej noty, o ile §Zasada trzyma).

### Trzeci wymiar zapisu — TRZY POOLE: uniwersalna-BIZNES vs uniwersalna-TECHNICZNA vs SPECJALISTYCZNA (w obrębie mózgu)

Oś ORTOGONALNA do brzytwy: brzytwa decyduje repo-vs-brain; ta decyduje — GDY już wiesz, że to nota mózgu — który POOL/KONTEKST mózgu ją trzyma. Są DWIE żywe bazy uniwersalne, nie jedna.

- **Test (trójdzielny).** Czy teza jest venture-niezależna, i jeśli tak — biznesowa czy techniczna?
  - **Uniwersalna-BIZNES** (czysty craft: sprzedaż / marketing / launch / oferta / produkt / voice-copy, bez specyfiki jednego venture) **→** `03-Resources/general-business/knowledge/` (`context: general-business`) + jej `_MOC.md`.
  - **Uniwersalna-TECHNICZNA** (inżynieria venture-niezależna: web/TS stack — TanStack / Supabase / RLS / React / Zod / Tailwind — + zasady stack-agnostyczne: SRP / TDD / kompozycja / abstrakcje) **→** `03-Resources/general-technical/knowledge/` (`context: general-technical`) + jej `_MOC.md`.
  - **Specjalistyczna** (specyfika jednego venture) **→** bieżący kontekst `03-Resources/<ctx>/knowledge/`.

  WHY: uniwersalna teza zapisana RAZ w swojej bazie spływa do skilli KAŻDEGO kontekstu, który tę bazę dziedziczy, bez duplikacji; ta sama teza wpisana per-kontekst rozjeżdża się w N kopii.
- **Dziedziczenie to LISTA (multi-inherit).** Kontekst komponuje te bazy, które go dotyczą — `inherits` jest listą, nie pojedynczą wartością: np. `agency` dziedziczy OBIE (`["general-business", "general-technical"]`), `claude-dev` → `["general-technical"]`, shadow-operator → `["general-business"]`, iOS scandit → `[]` (żadnej). WHY: kontekst potrafi konsumować oba rodzaje craftu naraz — jedna oś dziedziczenia by go do tego nie dopuściła.
- **Fail-safe.** Domyślaj się KONTEKSTU specyficznego; promuj do którejkolwiek bazy uniwersalnej dopiero na realny popyt 2. kontekstu. WHY: łatwiej podnieść notę do bazy niż odkręcić fałszywie-uniwersalną, na której inny kontekst już zbudował.
- **Reguła kierunkowa.** Nota uniwersalna `[[linkuje]]` TYLKO w obrębie WŁASNEGO poolu — nigdy w dół do noty kontekstowej ani w bok do drugiego poolu uniwersalnego (silnik zablokuje commit); nota kontekstowa MOŻE linkować w górę do uniwersalnej. WHY: link poza pool związałby bazę z jednym venture / drugim poolem, łamiąc jej niezależność.
- **Mechanizm promocji.** Podniesienie noty do bazy uniwersalnej robi `scripts/promote-to-universal.py` (przenosi notę + resync + audyt linków), NIE ręczny `git mv`.
- **Pełny mechanizm:** `_system/knowledge-system.md` §„Wiedza uniwersalna" (oba poole, dziedziczenie-lista, resync, audyt). Ten skill WSKAZUJE, nie przepisuje.

### Reguły wspólne dla obu destylerów

- **Anty-dryf dedup-search PRZED utworzeniem noty.** Przeszukaj `knowledge/` po istniejący slug/tezę i ROZSZERZ istniejącą, nie twórz rodzeństwa. Dedup przy zapisie = najtańsza obrona przed degradacją na skali.
- **Verify-understanding — obowiązkowy checkpoint przed zapisem.** Zrestytuuj zdestylowany model użytkownikowi i potwierdź; nie zapisuj na ciszy.
- **Improve-existing-vs-new.** Faworyzuj rozszerzenie istniejącego artefaktu/noty; nowy wymaga uzasadnionej luki (test: czy istniejący artefakt już to posiada?).

### Schemat noty

Pełny schemat: kontrakt `_system/knowledge-system.md` §Schemat notatki (NIE przepisuj). Pola dodawane przez `/brain-extract-knowledge` przy ekstrakcji z pracy: `created`, `references` (ścieżki/kotwice repo, z których synteza czerpie — kotwica drift-audit, NIE `reflects-source`), `superseded-by` (tylko przy obaleniu — nigdy cichy delete).

---

House style: signal-vs-noise (jeśli Claude to zna = szum), WHY-carrying, zwięźle.
