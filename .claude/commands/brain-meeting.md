---
description: Turn a meeting transcript into a vault meeting note + one-sentence project-memory update, decided autonomously from quoted evidence; the human is asked only where scope, referent or ownership is unsourced. Usage: /brain-meeting [context] [transcript-path]
argument-hint: [context] [transcript-path]
allowed-tools: Read, Edit, Write, Bash, Grep, Glob, Task
---

# /brain-meeting — transkrypt spotkania → notatka + jedno zdanie na wysokiej półce

Zamienia transkrypt Fathoma w **rekord spotkania** w vaulcie (w folderze PODMIOTU, którego spotkanie
dotyczy; `<vault>/meetings/` tylko dla spotkań bez jednego podmiotu) plus **JEDNO zdanie statusu**
w pamięci projektu. Rdzeniem komendy są dwie rzeczy: **TEST DECYZJA-vs-DELIBERACJA** (Faza 2) i
**LICENCJA ZAPISU** (Faza 3) — nic nie trafia na wysoką półkę bez cytatu verbatim i sourcowanego zakresu.
Siostra `/brain-update`: tamta bierze MOJĄ sesję, ta bierze transkrypt rozmowy INNYCH LUDZI.

## ⭐ ZASADA NADRZĘDNA — o co pytasz człowieka

> **Człowiek jest pytany WYŁĄCZNIE o to, czego NIE MA w transkrypcie. Wszystko, co W NIM JEST, agent
> rozstrzyga sam — i wolno mu to zapisać tylko w słowach i w ZAKRESIE, na które transkrypt daje licencję.**

Dowód z pierwszego przebiegu (2026-08-10, realny transkrypt 66 min): bramka temat-po-temacie dała 22
tury, z których człowiek zmienił DOKŁADNIE JEDNĄ rzecz (odrzucił mapowanie pliku w T15). Jednocześnie
do vaulta weszły cztery twierdzenia szersze niż źródło — i na każde z nich człowiek powiedział „tak".
Bramka pytała więc o rzeczy rozstrzygnięte transkryptem, a przepuszczała te nierozstrzygnięte.
**Licencja zapisu pochodzi z CYTATU + SOURCOWANEGO ZAKRESU, nigdy ze skinięcia głową.**

⚠️ Rozdzielanie CYTATU od MOJEGO ODCZYTANIA nie znika — przenosi się z rozmowy do SCHEMATU PLIKU
(`podstawa:`/`zakres:` jako WARUNEK TWARDY werdyktu `AUTO`) i do mechanicznego preflightu.

Repo mózgu (config/skrypty): `/Users/marcinjucha/Prywatne/projects/claude-brain`.

## Fazy

```
0: Kontekst + wejście + roster + zespol.md + hub spotkań    inline
1: Normalizacja transkryptu      scripts/normalize-transcript.py
2: Ekstrakcja + draft notatki    AGENT brain-manager  ← JEDYNA faza widząca transkrypt
2p: Preflight cytatów i draftu   scripts/verify-quotes.py + scripts/check-draft-src.py
2r: Przebieg naprawczy cytatów   AGENT brain-manager — TYLKO gdy verify-quotes.py exit 1
3: AUTO-WERDYKTY (bez tur)       inline
4a: Zapis notatki spotkania      AGENT brain-manager — NOWA inwokacja, nie resume
3b: JEDNA batchowa tura (E1–E6)  inline — tylko itemy eskalowane
4b: Zapis <memory> + notatek roboczych  AGENT brain-manager
5: Surfacing wiedzy              inline, gated → /brain-extract-knowledge
6: Raport                        inline
```

## ⚠️ KRYTYCZNE: MUSISZ WYWOŁAĆ AGENTÓW

Fazy 2, 4a i 4b to **realne wywołania Task** z `subagent_type="brain-manager"` (4a i 4b to DWIE
osobne inwokacje, nie jedna). Faza **2r** dochodzi jako CZWARTA, osobna inwokacja — tylko warunkowo,
gdy `verify-quotes.py` zwróci exit 1.

**NIE**: „uruchomię brain-managera" · opis tego, co agent zrobi · ekstrakcja transkryptu we własnym kontekście.
**TAK**: natychmiastowe wywołanie Task → czekasz na wynik → pokazujesz podsumowanie.

⚠️ **Orkiestrator NIGDY nie czyta transkryptu** — ani surowego, ani znormalizowanego. Z materiału
spotkania widzi wyłącznie linijkę statystyk z Fazy 1, ≤25-linijkowe podsumowanie agenta oraz pliki
`<work>/` (digest, walkthrough, `quotes.tsv`, `written.md`). Czyta też `<vault>/<memory>` w Fazie 3 — to nie transkrypt. Wyjątek
mechaniczny: `grep` po samych ETYKIETACH mówców w Fazie 0 (roster — nazwy, zero treści). WHY: transkrypt
godzinnego spotkania zjada kontekst, w którym mają się zmieścić AUTO-werdykty nad wszystkimi tematami
i jednolinijkowe diffy `<memory>`; **rozstrzyganie jest tu produktem, nie ekstrakcja**.

## Krytyczne reguły

1. **Licencja zapisu, nie bramka zgody.** Faza 4a (notatka spotkania) startuje, gdy wszystkie tematy
   mają `verdict:` ≠ `—` (`AUTO` wystarcza). Faza 4b (`<memory>` + notatki robocze) startuje WYŁĄCZNIE,
   gdy każdy temat idący wyżej ma `podstawa:` z cytatem verbatim ORAZ `zakres:` ustalony z wypowiedzi
   albo z huba poprzednich spotkań (Krok F) ORAZ żadnej otwartej eskalacji. Faza 2 ma vault **READ-ONLY**.
2. **Pytania doprecyzowujące** po Fazie 0 (parafraza + 3–4 pytania zamknięte, ≤4 linijki).
3. **Zero inwencji w cudze powody.** WHY = powód wypowiedziany (z WŁASNYM cytatem verbatim) ALBO
   wskazany autorytet ALBO „WHY nie podano na spotkaniu". Nigdy nie rekonstruuj uzasadnienia
   z kontekstu otaczających tur, żeby decyzja wyglądała mądrzej.
4. **Bramka atrybucji `[do potwierdzenia]`.** Fathom myli mówców (zweryfikowane: linia 1:02:47
   przypisana Filippo Martinoniemu to „Yes" Marcina Radomskiego). Każde twierdzenie, w którym KTO jest
   nośne — właściciel akcji, zobowiązanie, autorytet-jako-WHY — dostaje prefiks `[do potwierdzenia]`.
   Na ESKALACJĘ idzie WYŁĄCZNIE item, w którym nośnym KTO jest MJ (moja akcja, moje zobowiązanie, moje
   capacity) albo w którym właściciel jest niejednoznaczny MJ-vs-Marcin (E2) — tylko tam mam wiedzę,
   której nie ma w transkrypcie. Atrybucja do OSÓB TRZECICH nie jest pytaniem: zapisujesz ją z prefiksem
   (reguła 5) i raportujesz w Fazie 6. ⚠️ Prefiks zdejmuje TYLKO odpowiedź, która NAZYWA ten item;
   zbiorcze „ok"/„domyślne" NIGDY nie zdejmuje prefiksu.
5. **Prefiks przeżywa zapis.** Niepotwierdzone twierdzenie o właścicielu zapisujesz Z prefiksem —
   nie kasujesz go i nie awansujesz na fakt. Prefiks zdejmuje **WYŁĄCZNIE** werdykt
   `POTWIERDZONE-ATRYBUCJA` z Fazy 3 (samo `POTWIERDZONE` go NIE zdejmuje).
6. **DECYDUJESZ SAM.** Pytasz WYŁĄCZNIE, gdy zachodzi jeden z SZEŚCIU warunków (lista ZAMKNIĘTA, każdy
   sprawdzalny mechanicznie):
   - **E1** `zakres:` NIEUSTALONY albo `WNIOSKOWANY` na itemie idącym na wysoką półkę / do notatki
     roboczej → „Czego dotyczy X — Androida, iOS, obu? / czyj sklep?"
     ⚠️ Oś ze `źródło: POPRZEDNIE-SPOTKANIE` albo `źródło: ROSTER` E1 **NIE** odpala — obie są
     sourcowane (Krok F). Wpis rosteru z `[LUKA]` na TEJ osi podstawą nie jest — tam E1 odpala.
   - **E2** item wchodzi do `<memory>` jako MOJA akcja/capacity, albo właściciel jest MJ-vs-Marcin
     niejednoznaczny → „To Twoja akcja czy Marcina Radomskiego?"
     ⚠️ **E2 JEST NIETKNIĘTY** — jedyny wyzwalacz, który zarobił na siebie w 100% (2026-08-10 catchup:
     3 odpalenia, 3 odpowiedzi Marcina). WHY: kolizja imion i własność MOICH akcji to wiedza, której
     w transkrypcie NIE MA i której nie da się wyprowadzić z żadnego artefaktu — jedyne miejsce, gdzie
     człowiek wnosi informację, a nie tylko akceptację.
   - **E3** *(ZAWĘŻONY — w praktyce NIE ODPALA)* mapowanie tematu na notatkę roboczą **nie jest już
     pytaniem**. Rozstrzygasz je SAM wg inwariantu 6 (zgodność TREŚCI + zgodność `project:`/`repo:`
     targetu z osią `platforma:`): oba warunki spełnione ⇒ dopisujesz z obowiązkową adnotacją;
     którykolwiek niespełniony ⇒ nie dopisujesz, temat zostaje w notatce spotkania. **W ŻADNYM z tych
     dwóch przypadków nie pytasz.** WHY zdjęcia pytania: w przebiegu 2026-08-10 E3 odpalił 4×, Marcin
     nie odpowiedział na ŻADNE, a orkiestrator sam rozstrzygnął D13 → `SHELF-24396-navigation-pop-crash.md`
     po zgodności treści (`navigation.pop(3)` przy wyjściu z module-advancement) i zgodzie
     `project: Digital Shelf iOS` — i była to właściwa decyzja; pozostałe trzy słusznie zostały bez dopisku.
     Pytanie o mapowanie jest do człowieka bezwartościowe, bo odpowiedź jest w TREŚCI notatki targetu.
   - **E4** musiałem uzupełnić lukę, a chcę to zapisać (WHY bez własnego cytatu, wywnioskowana zmiana
     stanu) → „Zakładam, że …; zgadza się?"
   - **E5** *(ZAWĘŻONY)* istniejąca linia `<memory>` byłaby ZASTĄPIONA treścią, której digest **NIE
     POKRYWA** — czyli grozi realna UTRATA informacji → pokaż `jest:`→`będzie:`.
     ⚠️ Nadpisanie TEGO SAMEGO tematu nowszym stanem (także z innego spotkania tego samego dnia)
     **NIE jest E5** — rozstrzygasz je SAM wg inwariantu 3 (pamięć ZASTĘPUJE) i pokazujesz
     jednolinijkowy diff w raporcie Fazy 6(d). WHY: w przebiegu 2026-08-10 E5 odpalił 2× (D1 niemiecka
     lokalizacja — ten sam temat, stan późniejszy tego samego dnia; D30 sprzeczność zapisana jako ryzyko,
     bez zmiany starej linii), Marcin nie odpowiedział na żadne, a oba `DOMYŚLNIE:` były oczywiście
     poprawne. Pytanie o nadpisanie tego samego tematu pyta o inwariant, nie o wiedzę.
   - **E6** cytat nie przeszedł `verify-quotes.py` **I przeżył PRZEBIEG NAPRAWCZY Fazy 2r** — czyli
     transkrypt tego brzmienia po prostu nie zawiera. Świeża porażka `verify-quotes.py` NIE jest E6:
     idzie najpierw do Fazy 2r (naprawa mechaniczna z transkryptu, maks. 3 iteracje).
     WHY: w przebiegu 2026-08-10 preflight odrzucił 23 cytaty i WSZYSTKIE 23 były naprawialne
     mechanicznie (wycięty filler, brak domknięcia zdania, marker w środku cudzysłowu); po jednym
     przebiegu naprawczym 186/186. Cytat naprawia TRANSKRYPT, nie Marcin — pytanie „ten cytat się nie
     zweryfikował" jest do człowieka bezwartościowe.

   Wszystko inne: `verdict: AUTO` + linia w raporcie Fazy 6. Poza tą listą NIE WOLNO zadać pytania —
   „na wszelki wypadek" odtwarza bramkę, którą ta reguła usuwa.
   ⚠️ **Miara zdrowia tej listy:** w przebiegu 2026-08-10 z 9 eskalacji wartość dało 3 (wszystkie E2).
   Wyzwalacz, na który człowiek systematycznie nie odpowiada, a domyślne jest zawsze poprawne, NIE jest
   pytaniem — jest raportem. Przenieś go do Fazy 6.

## Co gwarantuje AUTO-werdykt (zamiast bramki)

S1 oczy człowieka na każdym twierdzeniu → `podstawa:` (cytat verbatim + mówca + [m:ss]) jest WARUNKIEM
   TWARDYM `verdict: AUTO`; brak cytatu = brak licencji = notatka spotkania, nigdy `<memory>`.
S2 korekta pomyłek mówców Fathoma → `[do potwierdzenia]` ZOSTAJE domyślnie i przeżywa zapis; zdejmuje
   go tylko odpowiedź NAZYWAJĄCA item (reguła 4). Do człowieka idzie tylko E2.
S3 przegląd brzmienia wysokiej półki → `jest:`→`będzie:` pokazywane tylko dla E5; Faza 6 wypisuje KAŻDĄ
   linię AUTO, która ruszyła `<memory>`, jako jednolinijkowy diff — audyt po fakcie na zapisanym diffie.
S4 rozdzielenie CYTATU od MOJEGO ODCZYTANIA → z rozmowy przenosi się do SCHEMATU PLIKU: blok bez
   `podstawa:`/`zakres:` nie może nieść werdyktu AUTO; sprawdza to preflight, nie tura.
S5 wznawialność → bez zmian: ta sama maszyna stanów w `walkthrough.md`, `stop`/`back`/`status`.

## Wiedza milcząca zespołu (nazwana luka, nie defekt)

Transkrypt NIE zawiera tego, co dla uczestników oczywiste: platformy, właściciela obszaru, klienta,
znaczenia skrótu. To normalna ekonomia rozmowy — nie traktuj tego jako braku w materiale i NIE wypełniaj
domysłem. Kolejność sięgania po tę wiedzę: (1) bieżący transkrypt, (2) hub `meetings/` (poprzednie
spotkania — Faza 0), (3) **`<ctx-folder>/zespol.md` — roster z obszarami/platformami**,
(4) `CLAUDE.md` kontekstu, (5) ESKALACJA do Marcina — dopóki korpus notatek nie urośnie, ON jest
źródłem tego kontekstu.
WHY roster PRZED `CLAUDE.md`: roster odpowiada na „kto za co odpowiada", `CLAUDE.md` na „jakie są
pułapki" — a to pierwsze pytanie zadaje się częściej.

⚠️ **REGUŁA PROWENIENCJI (twarda).** Fakt pochodzący od Marcina, a nie ze źródła, zapisujesz z jawną
proweniencją — „ustalenie MJ <data>, NIE treść spotkania" — NIGDY jako cytat i NIGDY jako ustalenie
spotkania. Zapis bez tej adnotacji zamienia wiedzę człowieka w rzekomy zapis spotkania i po miesiącu
nie da się ich rozróżnić. Realny przypadek (2026-08-10 → 2026-08-12): platforma betu na shelf
reconstruction; silnik wiedzy słusznie odmówił zapisania noty w OBU wersjach, bo transkrypt nie
rozstrzyga, a fakt wszedł na wysoką półkę dopiero z adnotacją o autorze ustalenia.

## Mówcy i etykiety

⚠️ Roster i aliasy ustala Faza 0 i wkleja w DWA miejsca: prompt Fazy 2 ORAZ `--alias` do
`verify-quotes.py` w Fazie 2p (bez tego preflight odrzuca poprawne cytaty za odmianę nazwiska). AKCJE-MOJE zbiera WYŁĄCZNIE akcje OPERATORA.
⚠️ **Nazwę osoby sprawdzasz w `zespol.md`, nie „poprawiasz" ze słuchu.** W przebiegu 2026-08-10
orkiestrator wpisał „Pratik" tam, gdzie cytat mówi „Prativa" — **dwie różne, realne osoby**
(Pratik Mukerji ≠ Prativa Adhikari). Roster z rolami wyłapuje to od razu; bez niego podmiana nazwiska
wygląda jak literówka i przechodzi. Nazwa NIEOBECNA w rosterze → `[nazwa niepewna]` + zgłoszenie
w Fazie 6(g), NIGDY dopasowanie do najbliżej brzmiącego wpisu.
Imię pasujące do DWÓCH osób z rosteru → `[do potwierdzenia]` + notka „imię niejednoznaczne: <A> vs <B>"
+ eskalacja E2; NIGDY nie wybierasz sam. Zwrot po imieniu („Is that right, Marcin?") rozstrzyga, KTO
odpowiada w następnej turze — Fathom tego nie rozstrzyga.

## Katalog roboczy

`<work>` = `~/.claude/brain-meeting/<ctx>-<data>-<slug>/` → `digest.md`, `meeting-note-draft.md`,
`walkthrough.md`, `quotes.tsv`, `written.md`, `transcript.normalized.txt`, oraz `transcript.raw.txt`
(tylko gdy transkrypt był WKLEJONY, nie podany ścieżką — patrz Faza 0).

⚠️ **NIE scratchpad sesji**: scratchpad ma session-id w ścieżce, a rozstrzyganie z Fazy 3 może
przeżyć restart / summaryzację sesji — wtedy nowa sesja nie odnajdzie ani werdyktów, ani draftu, ani
markerów zapisu. `<work>` wyprowadzasz z `<ctx>`+daty+sluga, więc `/brain-meeting` uruchomiony ponownie
trafia w ten sam katalog i wznawia od pierwszego tematu bez werdyktu. Poza vaultem → nie zaśmieca grafu
Obsidiana.

⚠️⚠️ **CYKL ŻYCIA:** katalog jest USUWANY, ale **WYŁĄCZNIE jako ostatnia czynność Fazy 6, po
wyemitowaniu raportu**. Przeżywa w CZTERECH przypadkach: `stop` w środku rozstrzygania · przerwana sesja ·
błąd zapisu w Fazie 4 (przeżywa RAZEM z `written.md` — bez markerów wznowienie dubluje notę i wpisy
w notatkach roboczych) · Faza 5 wystawiła kandydatów, a silnik wiedzy jeszcze nie przebiegł (wtedy
przeżywa sam `digest.md` — Faza 6(h)). WHY: maszyna stanów jest
potrzebna dokładnie w tych sytuacjach; „czyść po zakończeniu" przeczytane jako „czyść zawsze na wyjściu"
zabija wznawialność.

## ⭐ TEST DECYZJA-vs-DELIBERACJA

> Spotkanie to DELIBERACJA. Zapisu jest wart jej wynik, nie jej przebieg. Ten test rozstrzyga, co
> jest wynikiem. Wklejasz go CAŁY w prompt Fazy 2.

**Krok A — zbierz WĄTEK tematu, nie wzmiankę.** Kluczem wątku jest KROTKA
`(temat, platforma, klient, flow)`, nie sama etykieta. Zgrupuj wzmianki o TYM SAMYM kluczu i weź
**OSTATNI, NIEOTWARTY PONOWNIE** stan. ⚠️ Ta sama etykieta + RÓŻNY zakres = DWA WĄTKI; nigdy nie scalasz
i nie przenosisz stanu jednego na drugi. Nie wiesz, czy zakres ten sam → rozdziel i oznacz
`platforma: NIEUSTALONA`; scalenie „na wszelki wypadek" produkuje FAŁSZYWY stan końcowy. Realna awaria
(2026-08-10): tura [19:43] o MVP „Android only" posłużyła jako wcześniejszy stan wątku o release 122,
który nie ma żadnej platformy. Wcześniejsze stany NIE są faktami; mogą pojawić się
raz, wyłącznie w notatce spotkania, jako ślad rozstrzygnięcia — i tylko gdy stan REALNIE zmienił się
w trakcie. Przykład: release 122 pada trzy razy — „plany są niejasne" → „poczekalibyśmy na shelf
reconstruction" → „cut po dacie niemieckiej lokalizacji, shelf reconstruction w późniejszym release".
Powstaje JEDEN wpis, niosący stan trzeci.

**Krok B — trzy bramki, WSZYSTKIE muszą przejść:**
1. **TERMINALNA** — żadna późniejsza tura nie otwiera, nie miękczy i nie kwestionuje tematu.
   (Otwarte ponownie → kandydatem staje się stan późniejszy; restart Kroku B na nim.)
2. **BEZWARUNKOWA** — nie wisi na nierozstrzygniętym przyszłym fakcie. Markery: „zobaczmy czy…",
   „jeśli będzie capacity", „w zależności od", „poczekalibyśmy na", „gdy X wejdzie", „zakładając".
   Wypowiedź warunkowa → **PLANY-TIMELINE z NAZWANYM warunkiem** (nigdy DECYZJA). Warunek jest
   NAZWANY, gdy ktoś powiedział, OD CZEGO to zależy (capacity, data, wejście X). Właściciel warunku
   zapisujesz, gdy padł; gdy nie padł, dopisujesz dosłownie „brak właściciela warunku" — to NIE
   przenosi itemu do innej kategorii. Do **RYZYKA-PYTANIA** przenosisz wyłącznie wtedy, gdy sam
   warunek jest NIENAZWANY (nikt nie powiedział, od czego to zależy) — wtedy nie ma czego zapisać
   jako plan. WHY jedna reguła: dwie równoległe („brak właściciela → pytania otwarte" vs przykład
   routujący dokładnie ten przypadek do PLANU) rozjeżdżały routing tego samego zdania.
3. **NAZWANA KONSEKWENCJA** — ktoś mówi, co się zmienia: w zakresie / poza, w tym sprincie / nie,
   kto robi, do kiedy. Sentyment („powinniśmy to w końcu zrobić") bez konsekwencji NIE jest decyzją.

Cztery przepracowane przykłady (realne, sprint planning 2026-08-10):

| Wypowiedź | Bramki | Zapis |
|---|---|---|
| „Let's see if we have capacity, then we'll do it for both" | pada #2 — warunek | PLAN: „oba platformy warunkowo — zależne od capacity; brak właściciela warunku". NIGDY „zdecydowano: iOS też" |
| „So we won't do it this sprint then" (skip-module) | przechodzi 1, 2, 3 | DECYZJA, konsekwencja = poza tym sprintem. WHY tylko jako DRUGI CYTAT VERBATIM niosący powód — jeśli takiego cytatu nie ma, `WHY nie podano na spotkaniu`. Nigdy „WHY wynika z kontekstu otaczających tur" |
| release 122 cięty po dacie niemieckiej lokalizacji | przechodzi po Kroku A | DECYZJA, WHY = data niemieckiej lokalizacji, konsekwencja = shelf reconstruction do późniejszego release |
| „It's what Christian decided" (nad dwukrotnie podniesioną obiekcją) | przechodzi — AUTORYTET JEST WAŻNYM WHY | DECYZJA z WHY = autorytet decyzyjny, PLUS wpis RYZYKO: obiekcja podniesiona dwukrotnie i przegłosowana. Nigdy nie wymyślaj technicznego uzasadnienia, żeby WHY wyglądało lepiej |

**Krok C — dyscyplina WHY.** WHY to powód wypowiedziany, nazwany autorytet, albo NIEOBECNY. Gdy
nieobecny: „WHY nie podano na spotkaniu" — nigdy nie rekonstruuj. To reguła no-invention zastosowana
do cudzego rozumowania, gdzie pokusa jest największa.

⚠️ **WHY musi mieć WŁASNY CYTAT VERBATIM** — drugi cytat obok cytatu decyzji (może pochodzić z innej
tury i innego mówcy, ale musi być dosłowny). Brak takiego cytatu = `WHY nie podano na spotkaniu`.
WHY tego wymogu: „WHY z otaczających tur" brzmi jak cytowanie, a jest rekonstrukcją z kontekstu —
dokładnie to, czego zabrania reguła no-invention. Cytat albo nic.

**Test KSZTAŁTU (sprawdzalny):** cytat WHY musi nieść marker przyczyny/powinności —
`because|since|so that|the reason|we need to|it's what X decided|bo|dlatego|żeby`. Cytat kończący się
`?` NIGDY nie jest WHY (pytanie nie jest powodem). WHY zapisujesz SŁOWAMI CYTATU — nie zamieniasz nazwy
własnej z cytatu na inną (osoba ≠ klient); podmiana = `[nazwa niepewna]`. Brak markera →
`WHY nie podano na spotkaniu`.

**Krok D — bramka atrybucji.** Fathom myli mówców (zweryfikowane: 1:02:47 przypisane Filippo
Martinoniemu to „Yes" Marcina Radomskiego). Gdy KTO jest nośne — właściciel akcji, zobowiązanie,
autorytet-jako-WHY — item dostaje `[do potwierdzenia]`. Na ESKALACJĘ (E2) idzie WYŁĄCZNIE item, w którym
nośnym KTO jest MJ albo w którym właściciel jest niejednoznaczny MJ-vs-Marcin; atrybucja do osób trzecich
zostaje zapisana Z prefiksem i zaraportowana (reguła 4). Awans na zwykły fakt (zdjęcie prefiksu) tylko
werdyktem `POTWIERDZONE-ATRYBUCJA`, i tylko na odpowiedzi NAZYWAJĄCEJ ten item.

⚠️ **`zespol.md` służy TU do wykrywania NIESPÓJNOŚCI atrybucji.** Gdy cytat przypisuje komuś pracę
SPRZECZNĄ z jego obszarem z rosteru, to sygnał **zlania mówców przez Fathoma**, nie nowy fakt
o zespole. Realny przypadek (2026-08-11): etykieta Roman Beier mówi „I've been doing the portrait
multicapture", a `zespol.md` ma Romana jako **DESIGN, nie implementację** — i faktycznie ta sama
etykieta odpowiada sama sobie dwie tury później. **Sprzeczność z rosterem ⇒ `[do potwierdzenia]`,
NIE aktualizacja rosteru.** Rosteru ta komenda nie pisze (Faza 6(g)).

**Krok E — small talk. Oceniasz TU, NIGDY skryptem.** Test: czy to ogranicza pracę? „Od środy
w przyszłym tygodniu mnie nie ma" = capacity → **PLANY-TIMELINE**, gdzie NAZWANYM warunkiem jest
**konkretny zakres dat nieobecności** (daty względne → bezwzględne: „nieobecny 2026-08-19 → …").
Bez dających się ustalić dat („będę czasem niedostępny") warunek jest NIENAZWANY → zostaje
w notatce spotkania, NIE idzie na wysoką półkę. Rozmowa o wakacjach = nie.
W wątpliwości: zostaw w notatce spotkania, trzymaj poza pamięcią projektu.

**Krok F — BRAMKA ZAKRESU.** Każdy item dostaje `zakres:` — `platforma:` (iOS/Android/KMP/backend/
cross-platform) · `klient:` (Coop/Loblaw/Carrefour/Zebra/wewnętrzne) · `flow:` — i per oś `źródło:`
o JEDNEJ z CZTERECH wartości:
- `CYTAT: „<verbatim>" [m:ss]` — najsilniejsza,
- `POPRZEDNIE-SPOTKANIE: <slug> — <cytat/decyzja z huba>` — ranguje się MIĘDZY cytatem
  a wnioskowaniem: NIE blokuje wysokiej półki (w przeciwieństwie do `WNIOSKOWANY`) i NIE idzie na
  eskalację E1, ale zdanie MUSI nazwać zakres w treści i podać, że podstawa jest z poprzedniego
  spotkania. Trzy wystąpienia tej samej osi w trzech różnych spotkaniach ⇒ oś jest ustalona bez
  eskalacji. Źródłem jest pole `POPRZEDNIE SPOTKANIA (hub)` z Fazy 0 — nigdy pełne noty,
- `ROSTER: <osoba> — <obszar/platforma z zespol.md>` — ranguje się **NA RÓWNI
  z `POPRZEDNIE-SPOTKANIE`**: NIE blokuje wysokiej półki, NIE odpala E1, ale zdanie MUSI nazwać
  zakres w treści. Stosujesz **WYŁĄCZNIE**, gdy `zespol.md` przypisuje mówcy ten obszar **JAWNIE**
  i proweniencja TEJ OSI to `[z notatki <slug>]` albo `[ustalenie MJ <data>]`.
  ⚠️ Oś oznaczona w `zespol.md` jako `[LUKA]` (np. „platforma `[LUKA]`" przy osobie, której obszar
  jest sourcowany) ORAZ każda osoba z sekcji `## Nazwy niepewne …` **NIE JEST PODSTAWĄ** — wtedy oś
  zostaje `WNIOSKOWANY` i idzie na E1 normalnym trybem. Proweniencja jest PER OŚ, nie per wiersz:
  sourcowany obszar nie sourcuje platformy.
  WHY ta wartość istnieje: w przebiegu 2026-08-11 (mobile sync) item D1 eskalował E1 wyłącznie dlatego,
  że oś `platforma: Android` miała `WNIOSKOWANY: mówca jest devem Android` — niesourcowaną inferencję
  z roli mówcy. `zespol.md` zamienia dokładnie tę inferencję w podstawę sourcowaną.
  WHY ograniczenie do `[LUKA]`: bez niego plik rólowy stałby się pretekstem do zgadywania — „jest
  w rosterze" znaczyłoby „jest ustalone", a połowa wierszy rosteru to jawnie nazwane luki,
- `WNIOSKOWANY: <podstawa>` — dosłownie tak („mówca jest devem Android", „TC52 to urządzenie Zebra").

Domknięcie definicji: oś, pod którą nie da się podłożyć ŻADNEJ z tych czterech podstaw, nie dostaje
piątej wartości `źródło:` — brak podstawy nie JEST podstawą — tylko sama oś przyjmuje stan
`NIEUSTALONA` (`NIEUSTALONY` tam, gdzie mowa o `zakres:`). I to jest dokładnie ten stan, na który
odpala eskalacja E1.

Zakres ustalasz WYŁĄCZNIE z wypowiedzi, z huba poprzednich spotkań albo z `zespol.md` (jawny wpis
o proweniencji ≠ `[LUKA]`) — NIGDY z tego, że temat
brzmi ogólnie, i NIGDY z sąsiedztwa w transkrypcie: spotkanie SKACZE między tematami.
Wypełniasz TYLKO osie, które ZDANIE TWIERDZI. Zdanie o fakcie platformowym bez sourcowanej platformy
NIE idzie na wysoką półkę; zdanie o kliencie bez sourcowanego klienta zapisujesz z NIEUSTALONYM
w treści („klient NIEUSTALONY — spotkanie nie powiedziało"), nigdy przez uogólnienie.
⚠️ ROZSZERZENIE ZAKRESU (wypowiedź o Androidzie zapisana jako fakt o produkcie) to ta sama awaria co
wymyślone WHY. `WNIOSKOWANY` zachowuje się jak `[do potwierdzenia]` i idzie na eskalację E1;
`POPRZEDNIE-SPOTKANIE` i `ROSTER` NIE (to sourcowane podstawy, nie domysł).

## Pięć kategorii + routing

| Kategoria | Wysoka półka (`<memory>`) | Notatka spotkania | Notatka robocza |
|---|---|---|---|
| **DECYZJE** | tak — jedno zdanie, gdy zmienia status/zakres | tak — z cytatem i WHY | tak, gdy temat ma notatkę |
| **AKCJE-MOJE** | tak — jako „co dalej" | tak | tak |
| **AKCJE-CUDZE** | tylko gdy blokują moją pracę | tak — z właścicielem (`[do potwierdzenia]`, gdy KTO nośne) | tak, gdy dotyczą podmiotu notatki |
| **PLANY-TIMELINE** | tak — z NAZWANYM warunkiem | tak | tak |
| **RYZYKA-PYTANIA** | tylko gdy nierozstrzygnięte i blokujące | tak — zawsze | tak → `## Decyzje i pytania otwarte` |

**Inwarianty routingu:**
1. Nic nie ląduje WYŁĄCZNIE na wysokiej półce — każdy item ma pełny zapis w notatce spotkania.
2. Temat bez ticketu/notatki roboczej **zostaje w notatce spotkania**; nie tworzysz notatki roboczej
   na podstawie spotkania.
3. Pamięć projektu **ZASTĘPUJE** stary stan, nigdy nie dokleja.
4. **Zero detalu technicznego** na wysokiej półce (nazwy plików, parametry, mechanizmy → niżej).
   ⚠️ **ZAKRES NIE JEST DETALEM TECHNICZNYM — jest PODMIOTEM zdania.** Fakt z osią `platforma:`
   ≠ cross-platform MUSI nazwać platformę w treści („na Androidzie…"), z osią `klient:` ≠ wewnętrzne —
   nazwać klienta. WHY: pamięć tego kontekstu ma `repo: digital-shelf-ios`, więc zdanie bez platformy
   nie jest neutralne — czyta się jako iOS. Dokładnie tak fakt androidowy stał się faktem platformowym
   w przebiegu 2026-08-10.
5. `[do potwierdzenia]` **przeżywa zapis** — przenosisz prefiks dosłownie. Jedyny wyjątek: werdykt
   `POTWIERDZONE-ATRYBUCJA` z Fazy 3, który go zdejmuje.
6. Mapowanie tematu na notatkę roboczą jest FAKTEM, gdy klucz ticketu PADŁ na spotkaniu. Bez
   wypowiedzianego klucza **rozstrzygasz SAM, bez pytania**, po DWÓCH warunkach:
   (a) zgodność **TREŚCI** itemu z treścią notatki targetu — **nie** zbieżność NAZWY PLIKU,
   (b) zgodność `project:`/`repo:` we frontmatterze targetu z osią `platforma:` itemu.
   **Oba spełnione ⇒ DOPISUJESZ**, z obowiązkową adnotacją: „klucz SHELF nie padł na spotkaniu;
   mapowanie po zgodności treści, nie po nazwie pliku — decyzja z `<data>`".
   **Którykolwiek niespełniony (w tym: nie da się go ocenić) ⇒ NIE dopisujesz** — temat zostaje
   w notatce spotkania. Sprzeczność z osią `platforma:` ⇒ mapowanie ODRZUCONE, raportuj.
   ⚠️ Zbieżność NAZWY PLIKU nigdy nie jest podstawą — ani do dopisania, ani do pytania.
   Pole `mapowanie-hipoteza:` zostaje w `walkthrough.md` jako ŚLAD (czym była podstawa), ale NIE
   generuje już eskalacji. WHY: patrz E3 w regule 6 — 4 pytania, 0 odpowiedzi, decyzja i tak wyszła
   z treści notatki, nie od człowieka. Każde takie samodzielne mapowanie liczy się w Fazie 6(d).
7. `źródło-właściciela:` jest POLEM, nie osądem: `WŁASNE-ZOBOWIĄZANIE` (cytat właściciela w 1. osobie)
   | `PRZYPISANE` (nazwany w cudzym cytacie, brak cytatu zgody) | `WYWNIOSKOWANE`. Dwa ostatnie ⇒
   `[do potwierdzenia]` AUTOMATYCZNIE. Wiersz AKCJI bez tego pola jest niekompletny.
8. Cytat źródłowy z hedge (`I think|maybe|might|probably|suggested|shouldn't|hopefully`) ⇒ zapis
   ZACHOWUJE hedge („może dotykać splat", „Benoit RADZI czekać") albo dostaje `[do potwierdzenia]`.
   Nie awansujesz rady na decyzję ani powinności („shouldn't be") na opis stanu.
9. Zdanie na wysokiej półce niewywodliwe z CYTATU zapisujesz ze znacznikiem `[odczytanie]`.

---

## Fazy — szczegóły

### Faza 0 — kontekst + wejście (inline)

Kontekst wg logiki `/brain-update` Faza 0: **zadeklarowany w `$1`/prozie > cwd→`config.json` `.paths`
(najdłuższy prefiks) > zapytaj**. ⚠️ Uruchomienie z samego vaulta NIE mapuje się na kontekst (ścieżki
vaulta nie ma w `.paths`) — tam kontekst musi być zadeklarowany. Rozwiąż `<vault>`, `<memory>`,
`knowledge[<ctx>].active`.

Wejście: `$2` = **ŚCIEŻKA do pliku (preferowane)**. Wklejony transkrypt: zrzuć do
`<work>/transcript.raw.txt` i jedź dalej, ale zaznacz koszt w raporcie. WHY preferowana ścieżka:
wklejony transkrypt jest już WYDANY w kontekście głównym i normalizacja tego nie odkręci — oszczędza
kontekst tylko wtedy, gdy nigdy do niego nie wszedł.

Data + typ spotkania z nazwy pliku / nagłówka Fathoma; daty względne → `YYYY-MM-DD`. `<slug>` z typu.
Wszystko rozwiązane z pliku/`$1`/cwd → NIE pytasz: raportujesz jedną linijką „kontekst · data · typ ·
ścieżka" i jedziesz. Pytasz WYŁĄCZNIE o pole nierozwiązywalne (najczęściej kontekst przy uruchomieniu
z vaulta).

**TOŻSAMOŚĆ MÓWCÓW — krok obowiązkowy.**
1. Przeczytaj JAWNIE `<vault>/CLAUDE.md` i `<vault>/<ctx-folder>/CLAUDE.md`, wyciągnij mapę aliasów.
   **Przeczytaj też `<vault>/<ctx-folder>/zespol.md`, jeśli istnieje** — tabele osób
   (`## Zespół — rdzeń` oraz `## Poza zespołem …`: kolumny Osoba · Obszar/platforma · Dowód),
   sekcję `## Nazwy niepewne …` i sekcję `## Luki do uzupełnienia przez MJ`. Wynik wklejasz w prompt
   Fazy 2 jako pole `ROLE I OBSZARY (zespol.md)`. Plik nie istnieje →
   `ROLE I OBSZARY: brak pliku zespol.md`.
   To plik **REFERENCYJNY** (`type: reference` — dane), NIE pamięć projektu i NIE nota wiedzy: nie
   niesie statusu ani tezy, więc nie cytujesz go jako ustalenia spotkania.
   ⚠️ Proweniencję przenosisz RAZEM z wpisem i **PER OŚ** (`[z notatki <slug>]` /
   `[ustalenie MJ <data>]` / `[LUKA]`) — Krok F rozstrzyga po niej, czy wolno użyć `źródło: ROSTER`.
   Ta sama osoba może mieć obszar sourcowany z notatek, a `platforma [LUKA]` w tym samym wierszu.
2. Zbuduj ROSTER — same etykiety, zero treści:
   ```bash
   # na SUROWYM eksporcie Fathoma (`0:00 - Marcin Jucha`) — dostępne już w Fazie 0
   grep -ohE '^[0-9]?[0-9]:[0-9]{2}(:[0-9]{2})? *- *.+$' <transcript> \
     | sed -E 's/^[0-9:]+ *- *//' | sort -u
   # na ZNORMALIZOWANYM pliku (`[m:ss] Mówca:`) — gdy Faza 1 już przebiegła
   grep -ohE '^\[[0-9:]+\] [^:]+:' <work>/transcript.normalized.txt | sed 's/^\[[0-9:]*\] //; s/:$//' | sort -u
   ```
   (nie łamie zakazu czytania transkryptu — do kontekstu wchodzą tylko nazwy).
   ⚠️ Faza 0 poprzedza normalizację, więc DOMYŚLNY jest wariant surowy; wariant znormalizowany służy
   do weryfikacji rosteru po Fazie 1 (fallback z Fazy 1 zostawia materiał surowy — wtedy roster surowy
   jest jedynym, jaki masz).
3. Rozstrzygnij, która etykieta to OPERATOR i czy dwóch mówców dzieli IMIĘ: kolizja + brak mapy →
   JEDNO pytanie zamknięte „W rosterze są <A> i <B> — samo «<imię>» znaczy kogo?" (uprawnione: nie wiem,
   DO KOGO odnosi się wypowiedź). Brak kolizji albo mapa w CLAUDE.md → NIE pytaj.
4. Alias potwierdzony ręcznie DOPISZ do `<vault>/<ctx-folder>/CLAUDE.md`.
5. **Mapa aliasów idzie w DWA miejsca, nie w jedno:** (i) w prompt Fazy 2 jako pole `ALIASY:`,
   (ii) jako powtarzalny `--alias "SKROT=Pelna Nazwa"` do `verify-quotes.py` w Fazie 2p.
   Mapa obejmuje **skróty** (`MJ=Marcin Jucha`), **pełne etykiety transkryptu** (Fathom eksportuje
   `Marcin Jucha (markos734@gmail.com)`) oraz **formy ODMIENIONE** — polska deklinacja nazwisk sprawia,
   że digest pisze „Fabiana", „Marcina", a transkrypt „Fabian Nater".
   WHY: bez `--alias` preflight 2026-08-10 odrzucił 60 cytatów na „etykieta mówcy nie zgadza się";
   z mapą zostało 23, każdy z realnego powodu. Skrypt karał digest za konwencję nazewniczą, nie
   za nieprawdę — a masowe fałszywe odrzucenia blokują wysoką półkę bez powodu.

WHY: `normalize-transcript.py` z zasady nie rusza atrybucji, więc aliasy nie mają gdzie się rozwiązać
poza Fazą 0.

**KONTEKST Z POPRZEDNICH SPOTKAŃ — krok obowiązkowy.**
Przeczytaj hub `<vault>/meetings/meetings.md` (jeśli istnieje) — **tabelę rejestru, nie pełne noty** —
i weź z niej listę poprzednich spotkań tego kontekstu z ich kluczowymi decyzjami. Ten skrót wklejasz
w prompt Fazy 2 jako pole `POPRZEDNIE SPOTKANIA (hub)`. Hub nie istnieje →
`POPRZEDNIE SPOTKANIA: brak — to pierwsze spotkanie w tym kontekście`.
Gdy spotkanie ma jeden PODMIOT, przeczytaj też tabelę huba tego podmiotu (`<vault>/<subject>/…`) —
to ten sam rejestr, tylko węższy.

WHY: zakres wypowiedzi (platforma / klient / flow) bywa nierozstrzygnięty w JEDNYM transkrypcie, ale
rozstrzygnięty przez poprzednie spotkania — „ten wątek od trzech spotkań jest androidowy" jest legalną
podstawą osi `zakres:` ze `źródło: POPRZEDNIE-SPOTKANIE <slug>` (Krok F) — jedna z DWÓCH podstaw
dopuszczalnych poza cytatem z bieżącego transkryptu (druga to `zespol.md` → `źródło: ROSTER`). Korpus `meetings/` ma STOPNIOWO zastępować Marcina
jako źródło kontekstu — to jest miara dojrzewania tej komendy (patrz „Wiedza milcząca zespołu").

⚠️ Ograniczenie: hub daje tylko skrót decyzji. Jeśli skrót nie rozstrzyga zakresu, NIE otwierasz
pełnych not „na wszelki wypadek" (koszt kontekstu) — eskalujesz E1.

Zanim ruszysz dalej — a przy wklejonym transkrypcie PRZED jego zrzutem: `mkdir -p <work>`
(Faza 1 i wklejony transkrypt piszą tam), oraz uruchom
`ls <vault>` i `ls <vault>/*/` — wynik wklejasz do promptu Fazy 2 w pole ISTNIEJĄCE NOTATKI (ls).
Treści notatek NIE czytasz.

⚠️ WHY `mkdir -p` jest tu, a nie „gdzieś w Fazie 1": `--out` do nieistniejącego katalogu zwraca
exit 2, a fallback Fazy 1 przeczytałby to jako „skrypt padł" i zjechał na materiał surowy
z czysto mechanicznego powodu, przy poprawnym transkrypcie Fathoma.

### Faza 1 — normalizacja (skrypt)

```bash
python3 /Users/marcinjucha/Prywatne/projects/claude-brain/scripts/normalize-transcript.py \
  --in <transcript> --out <work>/transcript.normalized.txt --format fathom \
  --max-reduction 40 --dup-threshold 0.93
```

Do kontekstu **WYŁĄCZNIE jedna linijka statystyk** ze stdout.

**FALLBACK (nie przerywaj komendy) — odpal go, gdy zajdzie DOWOLNY z trzech warunków:**
1. skrypt padł (wyjątek, brak pliku),
2. `exit ≠ 0` (1 = redukcja > limitu, wyjście NIE zapisane; 2 = błąd IO/wejścia),
3. linijka statystyk mówi **`bloki mówców: 0`**.

→ podaj Fazie 2 SUROWY transkrypt z flagą `NORMALIZED: nie`.

⚠️ **`bloki mówców: 0` to JEDYNY sygnał „to nie format Fathom".** Wejście bez nagłówków mówcy
przechodzi przez skrypt NIETKNIĘTE i kończy się `exit 0` — czyli wygląda jak sukces. Warunek
sformułowany jako „to nie format Fathom" nigdy by nie odpalił; musisz przeczytać ten licznik.

WHY fallback nie przerywa: utrata normalizacji to koszt (więcej tokenów, artefakty ASR w materiale),
nie blokada — a abort zostawia Marcina bez notatki.

### Faza 2 — ekstrakcja + draft (AGENT brain-manager)

**Sufficient context for quality:**
```yaml
Input needed:
  - ścieżka do transkryptu (ŚCIEŻKA, nie treść)
  - <ctx>, <vault>, <memory>, data + typ spotkania, <work>
  - NORMALIZED: tak|nie
  - output `ls <vault>` + `ls <vault>/*/` (istniejące notatki robocze — agent SAM mapuje temat→ticket)
  - ROSTER mówców + mapa aliasów + która etykieta to OPERATOR
  - ROLE I OBSZARY (zespol.md) — osoba · obszar/platforma · PROWENIENCJA per oś; plus nazwy niepewne
    i luki. Podstawa `źródło: ROSTER` (Krok F) i detektor niespójności atrybucji (Krok D)
  - POPRZEDNIE SPOTKANIA (hub) — SKRÓT z tabeli rejestru (data · typ · kluczowe decyzje · slug)
  - pełny TEST DECYZJA-vs-DELIBERACJA + 5 kategorii + tabela routingu (wklejone w prompt)
  - format znormalizowanego pliku (`[m:ss] Mówca:` + markery `⟨m:ss⟩`)
NOT needed:
  - treść pamięci projektu (Faza 3 ją przeczyta, Faza 4b do niej pisze)
  - kontrakt knowledge-system
  - PEŁNE noty poprzednich spotkań (tylko skrót z huba — patrz wyżej)
```

**Prompt do agenta** (wklej test, kategorie i routing w całości):
```
Wyekstrahuj z transkryptu spotkania materiał do notatki spotkania i do pamięci projektu.

TRANSKRYPT: <ścieżka>          NORMALIZED: tak|nie
KONTEKST: <ctx> · VAULT: <vault> · PAMIĘĆ: <memory>
SPOTKANIE: <data> · <typ>      KATALOG ROBOCZY: <work>
ISTNIEJĄCE NOTATKI (ls): <output ls <vault> + ls <vault>/*/>
ROSTER MÓWCÓW: <etykiety> · ALIASY: <mapa z CLAUDE.md> · OPERATOR: <etykieta>
ROLE I OBSZARY (zespol.md): <tabele osoba · obszar/platforma · proweniencja + nazwy niepewne + luki
  — ALBO: brak pliku zespol.md>
  ⚠️ Wpis JAWNY o proweniencji `[z notatki …]`/`[ustalenie MJ …]` ⇒ oś dostaje
  `źródło: ROSTER: <osoba> — <obszar/platforma>` (Krok F), a teza NAZYWA zakres w treści.
  Oś z `[LUKA]` oraz każda osoba z sekcji nazw niepewnych ⇒ podstawą NIE JEST: zostaje `WNIOSKOWANY`.
  Cytat sprzeczny z obszarem osoby ⇒ podejrzenie zlania mówców przez Fathoma: `[do potwierdzenia]`,
  NIE korekta rosteru (Krok D). Plik jest REFERENCYJNY — nie cytujesz go jako ustalenia spotkania.
POPRZEDNIE SPOTKANIA (hub): <skrót tabeli rejestru: data · typ · kluczowe decyzje · slug
  — ALBO: brak — to pierwsze spotkanie w tym kontekście>
  ⚠️ To — obok `ROLE I OBSZARY` — jedna z DWÓCH podstaw zakresu poza cytatem z bieżącego transkryptu.
  Użyta ⇒ oś dostaje `źródło: POPRZEDNIE-SPOTKANIE: <slug> — <decyzja z huba>` (Krok F), a teza
  NAZYWA zakres w treści. Skrót nie rozstrzyga ⇒ oś NIEUSTALONA (eskalacja E1). Pełnych not
  NIE otwierasz.

Format znormalizowanego pliku: `[m:ss] Mówca: tekst`; `⟨m:ss⟩` w środku bloku = miejsce zszycia
kolejnej wypowiedzi TEGO SAMEGO mówcy — użyj go jako timestampu cytatu.

[gdy NORMALIZED: nie] Sąsiadujące powtórzone SERIE 3–4 zdań to ARTEFAKT ASR/eksportu, nie kilka
wypowiedzi — i bywają NIEDOKŁADNE (te same liczby, inne brzmienie). Ta sama myśl 20 minut później
to już NAWRÓT tematu i jest istotna.

[TU WKLEJ CAŁY ⭐ TEST DECYZJA-vs-DELIBERACJA — Kroki A–F]
[TU WKLEJ PIĘĆ KATEGORII + TABELĘ ROUTINGU + 9 INWARIANTÓW]

⚠️ ZAPIS TYLKO do <work>/. <vault> jest dla Ciebie READ-ONLY — nie tworzysz notatki spotkania,
nie ruszasz <memory>, nie dopisujesz do notatek roboczych. WHY: licencję zapisu nadaje dopiero Faza 3
(cytat verbatim + sourcowany zakres + preflight), a atrybucja mówców w Fathomie jest niepewna —
niezweryfikowany właściciel akcji wpisany do pamięci projektu wygląda potem jak fakt.

Zapisz OBA pliki, DOPÓKI TRZYMASZ TRANSKRYPT (drugi raz go nie zobaczysz):
1. <work>/digest.md — 5 kategorii; każdy item: teza · **ZAKRES (Krok F: platforma/klient/flow +
   `źródło:` per oś)** · CYTAT (verbatim, MÓWCA + dokładny [m:ss] z nagłówka bloku albo najbliższego
   markera ⟨m:ss⟩) · MOJE ODCZYTANIE · WHY (powód z DRUGIM CYTATEM VERBATIM | autorytet | „WHY nie
   podano na spotkaniu") · **`źródło-właściciela:` (inwariant 7)** · routing (wysoka półka? notatka
   spotkania? która notatka robocza?) · `[do potwierdzenia]` gdy KTO jest nośne · dla wątków
   wielokrotnie podnoszonych: ślad rozstrzygnięcia.
   Każdy item ma ID postaci `D<n>` — Faza 3 i draft się na nie powołują.
   Na końcu pliku sekcja `## NIEZAKLASYFIKOWANE` — wszystko, co nie wpadło w żadną z 5 kategorii,
   z cytatem i jednym zdaniem „dlaczego nie pasuje". WHY: bez tej sekcji materiał niepasujący
   do kategorii ginie po cichu, a Faza 3 nie ma go na czym pokazać Marcinowi.
   ⚠️ **Pozycje `## NIEZAKLASYFIKOWANE` dostają ID `N1`…`N<n>` na TYCH SAMYCH PRAWACH co `D<n>`**,
   a ich bullety w drafcie MUSZĄ nieść `<!-- src: N<n> -->`. WHY (przebieg 2026-08-10): 16 pozycji
   niezaklasyfikowanych nie miało ID, więc ich bullety były bez `src:`, `check-draft-src.py` wrzucił
   je do kwarantanny, a Faza 4a — słusznie wg instrukcji — kwarantanny nie zapisała. Mechanizm
   chroniący przed cichą utratą materiału sam usunął z notatki 16 fragmentów, których przedmiotu
   nie dało się nazwać — czyli dokładnie ten materiał, który ma być widoczny jako nierozstrzygnięty.
2. <work>/meeting-note-draft.md — pełny rekord spotkania.
   ⚠️ KAŻDY nagłówek i bullet `meeting-note-draft.md` MUSI nieść komentarz `<!-- src: D1 -->`
   (albo `<!-- src: N1 -->` dla pozycji niezaklasyfikowanych) z id itemu digestu. Materiał bez `src:` nie może istnieć w drafcie. Token alfanumeryczny/nazwa własna
   występująca w transkrypcie DOKŁADNIE RAZ i nieobecna w rosterze → dopisujesz `[nazwa niepewna]`;
   taki token BLOKUJE wysoką półkę. Ten sam timestamp nie może być jednocześnie w
   `## NIEZAKLASYFIKOWANE` i w sekcji twierdzącej — wybierz jedno.

SELF-REFLECTION INSTRUCTION:
Przed ekstrakcją odpowiedz sobie na 4 pytania i zapisz odpowiedzi w digeście:
(1) które tematy wracają więcej niż raz (Krok A)?
(2) gdzie brzmienie sugeruje decyzję, ale brakuje wypowiedzianej konsekwencji (bramka 3)?
(3) gdzie przypisanie mówcy jest nośne i niepewne?
(4) które wątki scaliłem z wzmianek o RÓŻNYM zakresie (platforma/klient/flow) i skąd wiem, że to jeden
    przedmiot?

ODPOWIEDŹ: ≤25 linijek — ile itemów w każdej kategorii, ile z `[do potwierdzenia]`, które tematy
zmapowały się na notatki robocze, czego NIE dało się zaklasyfikować.
NIGDY nie wypisuj draftu ani cytatów w odpowiedzi.
```

**Po agencie:** ≤25-linijkowa odpowiedź agenta JEST podsumowaniem — bez parafrazy i bez ankiety.
Przechodzisz od razu do Fazy 2p.

### Faza 2p — preflight mechaniczny (skrypty)

```bash
python3 /Users/marcinjucha/Prywatne/projects/claude-brain/scripts/verify-quotes.py \
  --work <work> --transcript <work>/transcript.normalized.txt \
  --alias "MJ=Marcin Jucha" --alias "Marcina=Marcin Radomski" --alias "Fabiana=Fabian Nater"
python3 /Users/marcinjucha/Prywatne/projects/claude-brain/scripts/check-draft-src.py --work <work>
```

⚠️ **`--alias` jest OBOWIĄZKOWE, jeśli Faza 0 zebrała jakikolwiek alias** — przekazujesz CAŁĄ mapę
z kroku 5 Fazy 0 (skróty + pełne etykiety Fathoma + formy odmienione), jeden `--alias` per para.
Przykłady powyżej są ILUSTRACJĄ formatu, nie listą do przepisania.

`verify-quotes.py` blokuje Fazę 3 na exit 2 (nie da się zweryfikować cytatów) i wypełnia
`<work>/quotes.tsv`; jego PORAŻKI **nie idą do człowieka** — idą do **Fazy 2r (przebieg naprawczy)**,
a do człowieka tylko to, co 2r nie naprawił (**E6**). `check-draft-src.py` przenosi materiał bez `src:` do
`## NIEZWERYFIKOWANE-POZA-DIGESTEM` i exituje 2, gdy timestamp stoi jednocześnie w
`## NIEZAKLASYFIKOWANE` i w sekcji twierdzącej. Oba uruchamiasz PONOWNIE przed Fazą 4b.

⚠️ **FALLBACK Fazy 1 (`NORMALIZED: nie`) → `verify-quotes.py` NIE MA na czym przebiec** (surowy eksport
nie ma linii `[m:ss] Mówca:`, więc skrypt zwróci exit 2 z definicji, nie z powodu cytatów). Wtedy:
preflightu cytatów NIE ODPALASZ, `check-draft-src.py` odpalasz normalnie, a KAŻDY item idący na wysoką
półkę dostaje `[do potwierdzenia]` i Faza 6 mówi wprost „cytaty niezweryfikowane mechanicznie —
fallback normalizacji". NIE zamieniasz tego w bramkę zgody i NIE eskalujesz zbiorczo: E6 dotyczy
POJEDYNCZEGO odrzuconego cytatu, a nie braku przebiegu skryptu.
⚠️ W tym trybie **Fazy 2r też NIE odpalasz** — nie ma `quotes.tsv`, czyli nie ma listy do naprawy.

### Faza 2r — PRZEBIEG NAPRAWCZY CYTATÓW (AGENT brain-manager, warunkowo)

**Odpalasz WYŁĄCZNIE gdy `verify-quotes.py` zwrócił exit 1.** To NOWA inwokacja Task
(`subagent_type="brain-manager"`) — agent ma dostęp do transkryptu, orkiestrator nie ma i mieć nie może.

WHY ta faza istnieje: w przebiegu 2026-08-10 preflight odrzucił 23 cytaty i **wszystkie 23 były
naprawialne mechanicznie z transkryptu** — wycięty filler („we're, we're"), brak domknięcia kropką tam,
gdzie zdanie biegnie dalej, marker `[nazwa niepewna]` postawiony WEWNĄTRZ cudzysłowu. Po JEDNYM
przebiegu naprawczym: 186/186, zero cytatów naciągniętych, zero tez bez oparcia. Cytat naprawia
TRANSKRYPT, nie Marcin — E6 do człowieka było bezwartościowe.

**Prompt do agenta:**
```
Napraw cytaty odrzucone przez preflight — do BRZMIENIA Z TRANSKRYPTU.

TRANSKRYPT: <work>/transcript.normalized.txt
ODRZUCONE: <work>/quotes.tsv — wiersze z `zweryfikowany ≠ tak` (kolumna `powód` mówi, co nie pasuje)
PLIKI DO POPRAWY: <work>/digest.md · <work>/meeting-note-draft.md
ITERACJA: <n> z 3

Dla KAŻDEGO takiego wiersza znajdź rzeczywiste brzmienie w transkrypcie i popraw CYTAT w pliku.

REGUŁY TWARDE:
- poprawiasz CYTAT do transkryptu, NIGDY odwrotnie — transkryptu nie ruszasz,
- zachowujesz filler i powtórzenia dosłownie („we're, we're" zostaje),
- skrót przez `…` jest LEGALNY — skrypt sprawdza segmenty osobno,
- marker `[nazwa niepewna]` / `[do potwierdzenia]` NIGDY wewnątrz cudzysłowu — wynosisz go
  do prozy OBOK cytatu (marker w środku cudzysłowu jest fałszywym cytatem),
- NIE zmieniasz timestampów, klasyfikacji, routingu, ID itemów ani ICH LICZBY,
- teza opierała się na brzmieniu, którego w transkrypcie NIE MA ⇒ **NIE naciągasz cytatu**:
  zostawiasz cytat, który FAKTYCZNIE padł, i dopisujesz do itemu `⚠️ TEZA NIE MA OPARCIA W CYTACIE`.

ODPOWIEDŹ: ≤10 linijek — ile cytatów poprawionych, ile oznaczonych `TEZA NIE MA OPARCIA W CYTACIE`,
ile nie dało się znaleźć w transkrypcie. NIGDY nie wypisuj cytatów ani treści transkryptu.
```

**Po agencie:** odpal `verify-quotes.py` PONOWNIE (z tym samym `--alias`). Nadal exit 1 → kolejna
iteracja, **maksymalnie 3 razy**. Po trzeciej cytat zostaje **ODRZUCONY JAWNIE** i dopiero wtedy idzie
do człowieka jako **E6**.

**Item z `⚠️ TEZA NIE MA OPARCIA W CYTACIE` jest ZABLOKOWANY przed wysoką półką** — zostaje w notatce
spotkania (brak licencji zapisu, reguła 1), i Faza 6(d) go wymienia.

### Faza 3 — AUTO-WERDYKT + JEDNA BATCHOWA TURA (inline)

Przeczytaj `<vault>/<memory>` — tylko wpisy dotyczące podmiotów z digestu — i wypełnij `jest:`
dosłownym cytatem z pliku. Brak wpisu → `jest: —(nowy podmiot)`. WHY: Faza 2 pamięci projektu NIE
czyta (jest jej wprost zabroniona), a Faza 4b to pierwsza faza, która do niej PISZE — bez tego odczytu
diff `jest:`→`będzie:` pokazywałby stan, którego nikt nie pobrał.

Zbuduj `<work>/walkthrough.md` z digestu: **jeden blok per TEMAT** (nie per wzmianka), pola
`temat:` `kategoria:` **`zakres:` (osie + `źródło:` per oś)** `cytat:` `timestamp:` **`podstawa:`**
`moje-odczytanie:` `why:` `do-potwierdzenia:` **`źródło-właściciela:`** `routing:`
**`mapowanie-hipoteza:`** `propozycja-pamięci:` **`źródło-frazy:`** `verdict: —`.
`## NIEZAKLASYFIKOWANE` idzie JEDNYM blokiem, `verdict: AUTO`, domyślnie do sekcji „Niezaklasyfikowane /
do weryfikacji" notatki spotkania i NIGDY na wysoką półkę — ale **ID `N<n>` poszczególnych pozycji
wypisujesz w tym bloku**, bo draft powołuje się na nie przez `src:`. Eskalujesz tylko fragment,
w którym nośnym KTO jest MJ (E2).
(`timestamp:` = dokładny `[m:ss]` cytatu — bez niego cytatu nie da się zweryfikować w nagraniu.
`do-potwierdzenia: tak|nie` — musi być POLEM, nie domysłem z treści.)

`verdict:` to **MASZYNA STANÓW**. Dozwolone: `—` | `AUTO — podstawa: <cytat+[m:ss]>` |
`AUTO-SKORYGOWANE: <treść> — podstawa: <…>` | `POTWIERDZONE` | `POTWIERDZONE-ATRYBUCJA` |
`POTWIERDZONY-ZAKRES` | `SKORYGOWANE: <treść>` | `WYCOFANE`.
`AUTO` bez `podstawa:` NIE idzie na wysoką półkę. `POTWIERDZONY-ZAKRES` = jedyny werdykt zamieniający
oś `WNIOSKOWANY` na ustaloną. `POTWIERDZONE-ATRYBUCJA` dotyczy WYŁĄCZNIE osoby — niepewność TREŚCI
(hedge „I think") zapisujesz znacznikiem `[niepewne]`, nie zdejmujesz nim prefiksu.

⚠️ **`POTWIERDZONE` vs `POTWIERDZONE-ATRYBUCJA` — dwie różne rzeczy:**
- `POTWIERDZONE` = treść itemu przyjęta. Prefiks `[do potwierdzenia]` **ZOSTAJE** i jedzie do zapisu
  dosłownie (reguła 5).
- `POTWIERDZONE-ATRYBUCJA` = Marcin potwierdził KTO to powiedział / czyja to akcja. Dopiero to
  **ZDEJMUJE** prefiks `[do potwierdzenia]` i awansuje item na zwykły fakt; wolno go użyć TYLKO na
  itemie, który ten prefiks miał.
WHY rozdzielenie: jedno słowo `POTWIERDZONE` znaczyło jednocześnie „awansuj na fakt" i „prefiks
zostaje" — dwie sprzeczne instrukcje na tym samym werdykcie, więc Faza 4 nie miała jak rozstrzygnąć.

**ZAWSZE czytaj plik**, by ustalić następny blok do rozstrzygnięcia = pierwszy z `verdict: —`. WHY: sesja może zostać
zsummaryzowana w środku rozstrzygania. Gdyby stan żył tylko w rozmowie, wznowiona sesja nie wiedziałaby,
gdzie stanęła ani co już rozstrzygnięto — i albo pytałaby od nowa, albo zapisała niezweryfikowane.

**PRZEBIEG AUTO — bez tur.** Dla każdego bloku wpisujesz `verdict: AUTO — podstawa: …` (albo
`AUTO-SKORYGOWANE: …`). ⚠️ `będzie:` składasz WYŁĄCZNIE z fraz obecnych w digeście; dla każdego NOWEGO
rzeczownika podajesz `źródło-frazy: <item digestu>`. Kwalifikator zakresu bez cytatu NIE wchodzi.

**Potem JEDNA wiadomość:** numerowana lista wyłącznie eskalowanych itemów (E1–E6), każda linia = pytanie
+ `DOMYŚLNIE: <co robię, gdy pominiesz>`. Odpowiedź wpisujesz do pliku NATYCHMIAST jako
`POTWIERDZONE` (E4 — założenie przyjęte) / `POTWIERDZONE-ATRYBUCJA` (E2) / `POTWIERDZONY-ZAKRES` (E1) /
`SKORYGOWANE: <treść>` / `WYCOFANE`.
Wyjście z fazy bez zmian: brak `verdict: —`.

⚠️ **NUMEROWANA LISTA ESKALACJI JEST OSTATNIM ELEMENTEM WYPOWIEDZI.** Po niej NIE umieszczasz nic:
żadnego raportu, żadnych statystyk, żadnej informacji o naprawach skryptów, żadnego podsumowania.
Wszystko inne idzie **PRZED** listą albo do NASTĘPNEJ wypowiedzi, już po odpowiedzi Marcina.
WHY: w przebiegu 2026-08-10 orkiestrator wypisał 9 eskalacji, a potem w trzech kolejnych wiadomościach
raportował naprawy skryptów — Marcin zapytał wprost „o co pytasz?". Lista pytań pod ścianą raportów
przestaje być pytaniem.

⚠️ **KOLEJNOŚĆ:** AUTO-werdykty → **Faza 4a** (notatka spotkania) → ta JEDNA batchowa tura → **Faza 4b**
(`<memory>` + notatki robocze). WHY: notatka spotkania nie zależy od odpowiedzi na eskalacje (wszystko
idzie tam z prefiksami), a wysoka półka zależy — więc rekord spotkania istnieje na dysku, nawet jeśli
Marcin nigdy nie odpowie.

Format eskalowanej linii:
```
3. [E1] Release 122 — „cut po niemieckiej lokalizacji": zakres platformy NIEUSTALONY
   (cytat Fabiana nie nazywa platformy). Czego dotyczy — iOS, Androida, obu?
   DOMYŚLNIE: zostaje w notatce spotkania, NIE wchodzi do <memory>.
```
Format linii E5 (nadpisanie `<memory>` GROŻĄCE UTRATĄ treści — nie każde nadpisanie, patrz reguła 6):
```
5. [E5] jest:   „Release 122: plany niejasne"
        będzie: „Release 122: cut po niemieckiej lokalizacji (~ten sprint), shelf reconstruction
                 w osobnym release — [[meeting-2026-08-10-sprint-planning]]"
   Digest pokrywa tylko część starej linii. Nadpisujemy?
   DOMYŚLNIE: nie nadpisuję — stara linia zostaje nietknięta, nowe zdanie idzie tylko do notatki
   spotkania, a rozbieżność raportuję (inwariant 3 zabrania doklejania do <memory>).
```
⚠️ Gdy digest POKRYWA starą linię (ten sam temat, nowszy stan — także z innego spotkania tego samego
dnia): **NIE eskalujesz.** Nadpisujesz wg inwariantu 3 i pokazujesz jednolinijkowy diff w Fazie 6(d).

### Faza 4a/4b — zapis (AGENT brain-manager, NOWA inwokacja)

⚠️ To **NOWA inwokacja Task, NIE `SendMessage`** do agenta z Fazy 2. WHY: kontekst agenta z Fazy 2 jest
zapchany całym transkryptem i wznowiony agent po cichu zaimportuje detal transkryptu do pamięci
projektu — dokładnie awaria „piszesz dziennik", przed którą ostrzega `/brain-update` Faza 2a. Pisarz
widzi TYLKO skorygowany digest + draft.

**WZNOWIENIE — czytaj `<work>/written.md` PRZED wywołaniem agenta.** MARKER UKOŃCZENIA PER CEL, pisany
przez agenta natychmiast po każdym celu, czytany przez orkiestratora i wklejany w prompt. Format:
```
a-hub-note: <nota> | <hub>
b-high-shelf: <memory>
c-working-notes: <ścieżki albo: brak>
```
Cel wymieniony = ZROBIONY, agent go POMIJA. WHY: (a) ma regułę „plik istnieje → rozszerz slug", więc
restart nie nadpisze noty, ale ZDUBLUJE ją pod `<slug>-2` + drugi wiersz w hubie; (c) DOPISUJE, więc
restart dokleja te same wpisy; tylko (b) jest idempotentne.

**Podział na 4a/4b:** cel (a) idzie osobną, WCZEŚNIEJSZĄ inwokacją niż (b)+(c). WHY: (a) jest
idempotentny tylko w połączeniu z markerem, a (b)/(c) zależą od odpowiedzi na eskalacje — rozdzielenie
znaczy, że wysoka półka nigdy nie jest pisana z niedokończonych werdyktów.

**Sufficient context for quality:**
```yaml
Input needed:
  - ścieżki <work>/digest.md, <work>/walkthrough.md, <work>/meeting-note-draft.md
  - <vault>, <memory>, data + typ, <slug>, <subject> (folder podmiotu — gdy spotkanie ma jeden podmiot)
  - lista notatek roboczych, do których mapują się tematy z werdyktem — wraz z tymi zmapowanymi
    SAMODZIELNIE po zgodności treści (inwariant 6), z zaznaczeniem, które wymagają adnotacji
    „klucz SHELF nie padł na spotkaniu"
  - reguły routingu + 9 inwariantów (wklejone)
NOT needed:
  - transkrypt — ZABRONIONY
  - statystyki normalizacji
  - przebieg batchowej tury z Fazy 3
```

**Prompt do agenta:**
```
Zapisz zatwierdzony materiał ze spotkania do vaulta.

DIGEST: <work>/digest.md · DRAFT: <work>/meeting-note-draft.md
WERDYKTY: <work>/walkthrough.md — czytaj JE jako prawdę.
  AUTO / AUTO-SKORYGOWANE → zapisz (AUTO-SKORYGOWANE: treść z werdyktu); prefiks `[do potwierdzenia]`
    ZOSTAJE. `AUTO` bez `podstawa:` NIE idzie na wysoką półkę.
  POTWIERDZONY-ZAKRES → oś zakresu jest ustalona; nazwij ją w treści.
  Oś ze `źródło: POPRZEDNIE-SPOTKANIE` też jest ustalona — nazwij zakres w treści i dopisz, że
    podstawa pochodzi z poprzedniego spotkania (`[[<slug>]]` w notatce spotkania, ŚCIEŻKA w nocie wiedzy).
  Oś ze `źródło: ROSTER` też jest ustalona — nazwij zakres w treści i dopisz, że podstawą jest roster
    (`zespol.md`, ŚCIEŻKA — nie wikilink), a NIE wypowiedź na spotkaniu.
  POTWIERDZONE → zapisz; prefiks `[do potwierdzenia]` ZOSTAJE dosłownie.
  POTWIERDZONE-ATRYBUCJA → zapisz i ZDEJMIJ prefiks `[do potwierdzenia]` (atrybucja potwierdzona).
  SKORYGOWANE → zapisz treść korekty, nie oryginał agenta.
  WYCOFANE → NIE zapisuj nigdzie.
VAULT: <vault> · PAMIĘĆ: <memory> · SPOTKANIE: <data> · <typ> · SLUG: <slug>
NOTATKI ROBOCZE W GRZE: <lista>

⚠️ NIE otwieraj transkryptu, nawet „dla kontekstu". Wszystko, co ma być zapisane, jest w tych trzech
plikach; transkrypt zawiera detal, który na wysokiej półce jest szkodliwy.

JUŻ ZROBIONE (markery <work>/written.md): <treść albo: nic>. Cel wyżej POMIŃ CAŁKOWICIE.

FAZA 4a — TYLKO CEL (a), przed batchową turą.  FAZA 4b — CELE (b) i (c), po niej.
(po KAŻDYM ukończonym celu dopisz jego linię do <work>/written.md ZANIM ruszysz następny)

TRZY CELE:
(a) Notatka spotkania — pełny rekord z draftu OGRANICZONY do bloków, których `<!-- src: … -->` mapuje
    na temat z werdyktem ≠ WYCOFANE. NIE zapisujesz niczego z sekcji `## NIEZWERYFIKOWANE-POZA-DIGESTEM`.
    ⚠️ Sekcja `## NIEZAKLASYFIKOWANE` wchodzi do notatki **NORMALNIE** — jej bullety mają `src: N<n>`,
    więc NIE są kwarantanną. Zapisujesz je jako „Niezaklasyfikowane / do weryfikacji", NIGDY na wysoką
    półkę. Kwarantanna to WYŁĄCZNIE `## NIEZWERYFIKOWANE-POZA-DIGESTEM`, i nic więcej.
    Timestamp z `## NIEZAKLASYFIKOWANE` nie może pojawić się w sekcji twierdzącej.
    ŚCIEŻKA: spotkanie dotyczy podmiotu, który ma już folder `<vault>/<subject>/` → zapisz TAM jako
    `<subject>-<data>-<slug>.md` i dopisz linię do huba tego podmiotu (tak leżą istniejące notatki
    spotkań, np. `justyna-kancelaria/2026-07-04-…`, `kacper-snela/kacper-snela-spotkanie-2026-07-29-…`).
    Brak jednego podmiotu (sprint planning, all-hands) → `<vault>/meetings/meeting-<data>-<slug>.md`;
    folder i hub `meetings/meetings.md` utwórz w kształcie `releases/releases.md` (frontmatter +
    `## Jak czytać i rozwijać tę notatkę` + tabela rejestru: Data · Typ · Uczestnicy · Kluczowe
    decyzje · Nota).
    FRONTMATTER noty (wymagany): `type: working-note`, `context: <ctx>`, `project:` (gdy kontekst go
    ma), `subject:` (gdy jest podmiot), `updated: <data>`, `tags: [meeting, <ctx>]`.
    Plik już istnieje → NIE nadpisuj: rozszerz slug i zaraportuj obie ścieżki.
(b) <vault>/<memory> — JEDNO zdanie + [[link]] per temat, który zmienia status/zakres śledzonego
    podmiotu. ZASTĄP stary stan, nie doklejaj. Zero detalu technicznego. Wpis już spuchnięty od
    detalu → skondensuj przy tej okazji (reguła KONDENSUJ z /brain-update Faza 2a).
    Pisz WYŁĄCZNIE w ręcznych sekcjach PONIŻEJ `<!-- /status:auto -->` (`## Na jakim etapie (status)`,
    `## W toku (working notes)`, `## Jak się łączy z resztą`). ⚠️ NIGDY między `<!-- status:auto -->`
    i `<!-- /status:auto -->` — ten blok jest PROJEKCJĄ notatek i `/brain-update` nadpisze go w całości,
    kasując Twoje zdanie.
(c) Tematy zmapowane na notatkę roboczą → dopisz do `## Decyzje i pytania otwarte` w TEJ notatce.
    Brak notatki → temat zostaje w notatce spotkania; NIE twórz notatki roboczej na podstawie spotkania.
    Mapowanie bez wypowiedzianego klucza ticketu (inwariant 6) dopisujesz **z adnotacją**: „klucz SHELF
    nie padł na spotkaniu; mapowanie po zgodności treści, nie po nazwie pliku — decyzja z <data>".

[TU WKLEJ TABELĘ ROUTINGU + 9 INWARIANTÓW]

`[do potwierdzenia]` z werdyktów przenieś DOSŁOWNIE — zdejmujesz go WYŁĄCZNIE na werdykcie
`POTWIERDZONE-ATRYBUCJA`. Daty bezwzględne.

⚠️ PRZED RAPORTEM:
- AUTO / AUTO-SKORYGOWANE → zapisz; `[do potwierdzenia]` ZOSTAJE.
- `mapowanie-hipoteza:` → rozstrzygasz wg inwariantu 6 (zgodność TREŚCI + zgodność `project:`/`repo:`
  z osią `platforma:`); oba spełnione → dopisujesz Z ADNOTACJĄ, którykolwiek nie → NIE dopisujesz.
- Item z `⚠️ TEZA NIE MA OPARCIA W CYTACIE` (Faza 2r) → wysoka półka ZABRONIONA, zostaje w notatce.
- Cytat z hedge → inwariant 8 (zachowaj hedge albo `[do potwierdzenia]`).
- Zdanie niewywodliwe z cytatu → `[odczytanie]`.
- Fakt platformowy bez nazwanej platformy = ZAPIS ZABRONIONY, zostaje w notatce spotkania.

SELF-REFLECTION INSTRUCTION:
Przed zapisem odpowiedz sobie na 2 pytania i zastosuj odpowiedzi:
(1) które z tych zdań to detal należący do notatki spotkania, a nie do pamięci projektu?
(2) który istniejący wpis w <memory> mam ZASTĄPIĆ, a nie uzupełnić?

RAPORT: co utworzono, co zastąpiono, co skondensowano, co pominięto.
```

**Po agencie — WERYFIKACJA NA DYSKU, nie z raportu.**
```bash
ls -la <nota>
grep -c '<slug>' <hub>                                  # musi być 1
grep -n '<slug>' <vault>/<memory>
grep -n -A5 'Decyzje i pytania otwarte' <każda notatka robocza>   # brak duplikatów
```
Rozbieżność raport↔dysk → uzupełnij `written.md` zgodnie z DYSKIEM (dysk jest prawdą) i wywołaj agenta
ponownie WYŁĄCZNIE na brakujące cele. Do Fazy 6(a)–(c) wchodzi wynik weryfikacji, nie raport agenta.
WHY: raport to intencja, nie stan systemu plików; agent, który padł w środku, nie emituje raportu wcale —
w przebiegu 2026-08-10 agent Fazy 4 padł na błędzie API i orkiestrator musiał ręcznie grepować vault,
żeby ustalić, co istnieje.

### Faza 5 — surfacing wiedzy (inline, gated)

Gate `knowledge[<ctx>].active == true`, inaczej jedno zdanie w raporcie. Nad **DIGESTEM PO WERDYKTACH**
(nie nad transkryptem) wyłącznie **tani pre-filtr Stopnia 1** brzytwy (`brain-conventions`)
→ **0–3 kandydatów** → przekaż do `/brain-extract-knowledge`, JEDYNEGO właściciela pełnej brzytwy,
decyzji o zapisie i samego zapisu. **Silnik ZAPISUJE i RAPORTUJE — potwierdzenia nie ma w ogóle**
(lustro `/brain-update` Faza 3.8); weto użytkownika żyje PO zapisie, przez raport silnika i
`status: superseded-by`. WHY: podwójna bramka (propozycja tu + verify tam) męczyła użytkownika,
a pojedyncza też okazała się tarciem przy komendzie odpalanej z nawyku — obrona jakości stoi na
brzytwie, dedupie i `sync --check`, nie na pytaniu. ⚠️ Bramka digestu w Fazie 3 tej komendy ZOSTAJE —
to inna bramka (dotyczy treści spotkania, gdzie atrybucja mówców jest niepewna).

**FORMA PRZEKAZANIA (dokładnie ta, silnik ma na nią wejście — `/brain-extract-knowledge` Faza 0/1):**
`/brain-extract-knowledge` z `--from-meeting <work>/digest.md` plus lista 0–3 kandydatów. Silnik
pomija wtedy własny INGEST i bierze digest jako źródło; `source:` noty to ŚCIEŻKA notatki spotkania
(nie `SHELF-XXXXX`). ⚠️ Spotkanie WEWNĘTRZNE nie idzie do `distill-coaching` — ta ścieżka jest dla
wejść ZEWNĘTRZNYCH (call coachingowy, kurs, artykuł).

⚠️ **W nocie wiedzy NIGDY nie cytuj spotkania wikilinkiem `[[…]]`** — podaj `source:`/ścieżkę.
WHY: `sync-knowledge.py` rozpoznaje `[[slug]]` i nieistniejący target daje `dangling-link` + exit 2,
czyli zablokowany commit. Notatka spotkania nie jest notą wiedzy, więc nigdy nie będzie targetem.

**0 kandydatów to poprawny i częsty wynik — powiedz to wprost.** WHY: faza, która czuje się
zobowiązana wyprodukować kandydata, to droga, którą wymyślona wiedza wchodzi na zaufaną półkę —
a materiał ze spotkania jest szczególnie kuszący, bo brzmi jak wnioski.

Cel to „dlaczego platforma jest jaka jest" — cross-atom synteza, której żadna lokalizacja w repo nie
niesie. Kwalifikujący się przykład (realny, z transkryptu 2026-08-10): onboarding **na platformie, na
której integracja SDK faktycznie idzie (sprawdź `zakres:` itemu, NIE zakładaj)** zależy od shelf
reconstruction ZEWNĘTRZNEGO zespołu (zespół Matthiasa Blocha, priorytetyzowany pod innego klienta);
zespół zgłosił ryzyko dwukrotnie — „does it sound a little bit dangerous that we are betting
everything on this?" — a odpowiedź brzmiała „it's what Christian decided". To trwała wiedza
platformowa: wyjaśnia strukturalną zależność i jej autorytet decyzyjny.
⚠️ Zdanie BEZ nazwanej platformy jest ROZSZERZENIEM ZAKRESU i jest ZABRONIONE: prawda o jednej
platformie, zapisana bez platformy w pamięci, której `repo:` to `digital-shelf-ios`, czyta się jako
prawda o iOS. To realna awaria pierwszego przebiegu (2026-08-10) — i silnik wiedzy słusznie ODMÓWIŁ
zapisania tej noty w obu wersjach, bo transkrypt nie rozstrzyga platformy w ŻADNĄ stronę.

**NIE kandydaci:** pojedyncze wzmianki techniczne, jednostkowe progi/bugi (atomy repo →
`/ai-extract-memory` → `/ai-curate-memory`), status sprintu, cokolwiek wciąż z `[do potwierdzenia]`
(łamie DURABLE przez konstrukcję — fragmenty `[do potwierdzenia]` są zabronione w notach mózgu)
· cokolwiek z osią zakresu `NIEUSTALONA` albo `WNIOSKOWANY` — nota wiedzy MUSI nazwać platformę
i klienta w samej tezie · cokolwiek z `[nazwa niepewna]`.
⚠️ Oś ze `źródło: POPRZEDNIE-SPOTKANIE` albo `źródło: ROSTER` jest DOPUSZCZALNA dla noty wiedzy — ale
teza musi nazwać ten zakres w treści, a `source:` noty wymienia OBIE ścieżki: bieżącą notatkę spotkania
i tę, z której zakres pochodzi (notatkę poprzedniego spotkania albo `zespol.md`). Zakres z podstawy
zewnętrznej niewymieniony w tezie = ROZSZERZENIE ZAKRESU.

### Faza 6 — raport (inline)

(a) **Notatka spotkania:** ścieżka + linijka w hubie.
(b) **Pamięć projektu:** które wpisy ZASTĄPIONE / dodane / skondensowane.
(c) **Notatki robocze:** do których dopisano.
(d) **Werdykty:** ile AUTO / AUTO-SKORYGOWANE / eskalowanych / zmienionych przez Marcina / WYCOFANE;
    ile cytatów odrzucił `verify-quotes.py` w PIERWSZYM przebiegu, ile naprawiła Faza 2r, ile przeżyło
    naprawę (= liczba E6), ile itemów dostało `⚠️ TEZA NIE MA OPARCIA W CYTACIE` (z ich listą);
    **ile mapowań na notatki robocze rozstrzygnięto SAMODZIELNIE po zgodności treści** (bez
    wypowiedzianego klucza ticketu) i ile z nich ODRZUCONO — ta liczba jest miarą autonomii, dokładnie
    jak licznik `POPRZEDNIE-SPOTKANIE` niżej; ile itemów wyszło z `[do potwierdzenia]`
    (= liczba `POTWIERDZONE-ATRYBUCJA`); **oraz LISTA każdej decyzji AUTO, która ruszyła `<memory>`,
    jako jednolinijkowy diff** — to zastępuje bramkę audytem po fakcie;
    **oraz ile osi zakresu wzięło się z `POPRZEDNIE-SPOTKANIE` zamiast z eskalacji E1**
    **oraz ile osi zakresu wzięło się ze `źródło: ROSTER`** (`zespol.md`). Te trzy liczby razem —
    `POPRZEDNIE-SPOTKANIE` · `ROSTER` · samodzielne mapowania na notatki robocze — są miarą tego, ile
    kontekstu system wyprowadza SAM, zamiast pytać Marcina; rosną w czasie, jeśli korpus dojrzewa.
(e) **Normalizacja:** statystyki albo „fallback — materiał surowy" (z podaniem, który z trzech
    warunków fallbacku zaszedł).
(f) **Wiedza:** przekazani kandydaci albo „0 kandydatów" albo „knowledge nieaktywna". Gdy `digest.md`
    przeżył (patrz (h)) — podaj jego ścieżkę, bo to wejście silnika.
(g) ⚠️ **CZEGO TA KOMENDA NIE ZROBIŁA** — konkretnie, nie jako ogólnik:
  - blok `status:auto` w `<vault>/<memory>` **NIE** został przeliczony,
  - slice `<!-- ctx:<ctx> -->` w `Home.md` **NIE** został odświeżony,
    → więc pamięć projektu ma nowy stan, a Home stary. Uruchom: `/brain-update <ctx>`.
  - **karty w trackerze (Trello/Notion/JIRA) NIE zostały utworzone** dla nowych AKCJI-MOJE, mimo że
    ta komenda wpisała je na wysoką półkę jako „co dalej". Właściciel tworzenia kart to
    `/brain-update` Faza 3.6 — uruchom ją, inaczej next-action żyje tylko w vaulcie.
  - utrzymanie knowledge-system (`sync-knowledge.py`, odświeżenie odbić) — właściciel
    `/brain-update` Faza 3.7. Ta komenda tego NIE robi.
  - **`zespol.md` NIE został uzupełniony.** Nazwisko, które padło na spotkaniu, a NIE MA go w rosterze,
    raportujesz tu jako brak w rosterze (z cytatem/timestampem) — **nie dopisujesz go sam**.
    To samo dotyczy sprzeczności cytat↔obszar z Kroku D. WHY: proweniencja `[ustalenie MJ]` musi
    pochodzić OD MARCINA, nie od agenta — inaczej roster zaczyna sourcować własne domysły i
    `źródło: ROSTER` przestaje być podstawą. Ta sama reguła co przy aliasach w `CLAUDE.md`.
  WHY tak głośno: cicha omisja znaczy, że Home kłamie i nikt nie wie dlaczego.
(h) `<work>/` — **USUŃ go jako OSTATNIĄ czynność Fazy 6, już PO wypisaniu raportu (a)–(g)**, i tylko
    gdy `<work>/written.md` ma WSZYSTKIE TRZY linie (`a-`, `b-`, `c-`) i raport został wyemitowany.
    ⚠️ `quotes.tsv` (cytat · mówca · timestamp · zweryfikowany) kopiujesz do `<vault>/meetings/` obok
    noty PRZED usunięciem katalogu — bez tego żadnego cytatu nie da się już zweryfikować.
    Podaj usuniętą ścieżkę, żeby było widać, że rozstrzyganie istniało. WHY ta kolejność: „usuń, jeśli Faza 6 przeszła" oceniane WEWNĄTRZ
    Fazy 6 jest nierozstrzygalne — jedyny wykonalny wariant to „raport najpierw, kasowanie na końcu".
    ⚠️ **WYJĄTEK — `digest.md` przeżywa**, gdy Faza 5 wystawiła ≥1 kandydata, a silnik
    `/brain-extract-knowledge` jeszcze NIE został uruchomiony: digest jest wtedy JEDYNYM wejściem
    silnika. Zostaw sam `digest.md`, podaj jego ścieżkę w (f) i napisz wprost, dlaczego został.
    0 kandydatów albo silnik już przebiegł → usuwasz cały katalog. Transkrypt nietknięty.

## Komendy

- `continue` — dalej
- `skip` — pomiń fazę; **Fazy 3 NIE da się pominąć, gdy Faza 4 ma się wykonać**. Pominięcie batchowej
  tury = zastosowanie WSZYSTKICH `DOMYŚLNIE:`, nie zapis bez licencji.
- `back` — w Fazie 3: wskazany temat wraca do `verdict: —`; po Fazie 4a `back` NIE odkręca zapisu
  notatki spotkania (patrz `written.md`) — odkręcasz go ręcznie albo rozszerzasz slug
- `status` — w Fazie 3: N/M tematów z werdyktem, ile eskalacji otwartych
- `stop` — wyjście; `<work>/` **ZOSTAJE** (razem z `written.md`), wznowisz tą samą komendą (jeden
  z przypadków przeżycia katalogu — patrz CYKL ŻYCIA; ta linia jest nośna, nie kosmetyczna, bo bez niej
  `stop` czyta się jako „wyjdź i posprzątaj", co zabija wznawialność)

## Zasada wystarczającego kontekstu

✅ decyzje i werdykty · ścieżki plików roboczych · klucze istniejących notatek · reguły routingu ·
   SKRÓT huba poprzednich spotkań (tabela rejestru) do Fazy 2 · tabele `zespol.md` z proweniencją
   (`ROLE I OBSZARY`) do Fazy 2
❌ treść transkryptu · PEŁNE noty poprzednich spotkań · statystyki normalizacji do Fazy 4 ·
   przebieg batchowej tury eskalacji

> „Czy agent wyprodukuje WYSOKĄ JAKOŚĆ mając TYLKO to?" — Faza 2 potrzebuje transkryptu i mapy
> notatek. Faza 4 potrzebuje werdyktów i draftu; transkrypt obniżyłby jakość, nie podniósł.

## `scripts/normalize-transcript.py` — kontrakt

**Args:** `--in <path>` (wymagany) · `--out <path>` (wymagany) · `--format fathom` (default, dziś jedyna
dozwolona wartość) · `--max-reduction 40` (procent) · `--dup-threshold 0.93` (próg podobieństwa serii).

**Robi DOKŁADNIE cztery rzeczy:**
1. usuwa **wyłącznie boilerplate eksportu Fathoma** — linię `VIEW RECORDING …` i separatory `---`.
   ⚠️ **TIMESTAMPY SĄ ZACHOWANE, NIE USUWANE.** Linie treści przechodzą verbatim, więc realna godzina
   w zdaniu („let's meet at 10:30") też przeżywa.
2. scala kolejne bloki TEGO SAMEGO mówcy w jeden blok (etykieta mówcy verbatim). Wyjście:
   `[m:ss] Mówca: tekst`, a KAŻDE miejsce zszycia niesie swój timestamp inline jako `⟨m:ss⟩`.
3. wyrzuca **SĄSIADUJĄCE POWTÓRZONE SERIE do 8 zdań**, wewnątrz JEDNEGO segmentu JEDNEGO mówcy —
   nigdy przez granicę mówcy. Dopasowanie jest **PAROWE** (zdanie n vs zdanie n) i wymaga łącznie:
   identycznych zbiorów cyfr nośnych · obu zdań ≥40 znaków · `SequenceMatcher ratio ≥ --dup-threshold`.
   Seria 1-zdaniowa: **wyłącznie dokładne dopasowanie**.
4. raportuje jedną linijką na stdout.

**Linijka statystyk (dokładne pola):**
```
normalize-transcript: N linii/N znaków → N linii/N znaków (redukcja treści X.X%),
bloki mówców: N, scalone: N, zdania z powtórzonych serii usunięte: N
```
plus `, ZNAKI PODMIENIONE (nie-UTF8): N`, gdy wejście nie było poprawnym UTF-8.
**Redukcja liczona jest na ZDANIACH TREŚCI**, nie na całym pliku — boilerplate, wcięcia i znaki nowej
linii to formatowanie, a wliczane fałszywie „redukowały" krótki transkrypt o 40%+.
`bloki mówców: 0` = wejście NIE miało nagłówków mówcy, czyli to nie eksport Fathoma (patrz Faza 1 —
to JEDYNY wiarygodny sygnał, bo takie wejście przechodzi nietknięte z exit 0).

**Exit codes:**
- `0` — ok.
- `1` — redukcja > `--max-reduction` **ORAZ** treść ≥ 2000 znaków → zjadł treść, nie artefakty;
  **plik wyjściowy NIE zostaje zapisany**.
- `2` — błąd wejścia/IO (m.in. `--out` do NIEISTNIEJĄCEGO katalogu — dlatego Faza 0 robi `mkdir -p`).
- Redukcja > limitu, ale treść < 2000 znaków → `UWAGA:` na stderr i **exit 0**. WHY: w krótkim wyimku
  jedna legalnie usunięta powtórka 4 zdań to ponad 40% treści i bramka strzelałaby na POPRAWNYM
  przebiegu.

**Zapis następuje DOPIERO po przejściu bramki** — inaczej uszkodzone wyjście leżałoby na dysku obok
exit 1 i następny krok mógłby wziąć je za dobre.

Wszystko inne jest **osądem Fazy 2** — lista „NIE WOLNO" z uzasadnieniami żyje w docstringu skryptu.

## Kontrakty skryptów (Faza 2p)

### `scripts/verify-quotes.py`

**Args:** `--work <work>` · `--transcript <work>/transcript.normalized.txt` (oba wymagane) ·
`--alias "SKROT=Pelna Nazwa"` (opcjonalny, **POWTARZALNY** — `action="append"`).

**Robi DOKŁADNIE cztery rzeczy:** wyciąga cytaty w DWÓCH kształtach — atrybuowanym
`Mówca [m:ss]: „treść"` (mówca i timestamp PRZED cytatem) oraz źródłowym
`źródło: CYTAT: „treść" [m:ss]` (bez mówcy, timestamp PO cytacie; wtedy etykiety NIE sprawdza) ·
rozbija cytat po `…`/`...` i dopasowuje **KAŻDY SEGMENT OSOBNO** jako podciąg (obcinając interpunkcję
brzegową per segment) · wymaga trafienia w oknie **±90 s** ORAZ zgodnej ETYKIETY MÓWCY · zapisuje
`<work>/quotes.tsv` (`cytat · mówca · timestamp · zweryfikowany · powód · źródło`).

⚠️ **`--alias` PRZEKAZUJESZ ZAWSZE, gdy Faza 0 zebrała aliasy.** Dopasowanie etykiet jest po PREFIKSIE
tokenów (min 4 znaki), więc znosi polską odmianę nazwisk, ale skrótów (`MJ`) i pełnych etykiet Fathoma
(`Marcin Jucha (markos734@gmail.com)`) samo z siebie nie połączy. Bez mapy przebieg 2026-08-10 odrzucił
60 cytatów na „etykieta mówcy nie zgadza się"; z mapą 23 — czyli bez `--alias` skrypt karze digest
za konwencję nazewniczą, nie za nieprawdę, i masowo blokuje wysoką półkę.
Wyłuskiwane są WYŁĄCZNIE te dwa kształty, nie „każdy cudzysłów w pliku": naiwny wariant dał na tym samym
digeście 451 „cytatów" i 199 odrzuceń, niemal wszystkie błędy EKSTRAKCJI (drugi cytat w linii brany
za etykietę mówcy, polska proza z pól `ODCZYTANIE:` bez timestampu).

⚠️ **Per segment, nie całość** — cytat z wielokropkiem to legalny SPLICE dwóch fragmentów jednej
wypowiedzi; dopasowanie całości odrzucałoby go zawsze i skrypt stałby się fabryką pytań do człowieka.
Okno ±90 s: timestamp bierze się z nagłówka bloku albo z markera `⟨m:ss⟩`, więc cytat z końca scalonego
bloku legalnie leży kilkadziesiąt sekund po nagłówku. Cudzysłów domykający ASCII `"` jest akceptowany
obok `”` — odrzucenie cytatu za znak domknięcia to ta sama fabryka pytań.

**Exit codes:** `0` wszystkie zweryfikowane · `1` ≥1 cytat ODRZUCONY (szczegóły w `quotes.tsv`;
porażki BLOKUJĄ wysoką półkę i idą **najpierw do Fazy 2r**, do człowieka wyłącznie jako **E6** i tylko
po nieudanej naprawie) ·
`2` nie da się w ogóle weryfikować (brak transkryptu, zero linii `[m:ss] Mówca:`, zero cytatów) —
**to jedyny warunek blokujący Fazę 3**.

### `scripts/check-draft-src.py`

**Args:** `--work <work>` (wymagany). Modyfikuje `meeting-note-draft.md` W MIEJSCU.

**Robi DOKŁADNIE trzy rzeczy:** sprawdza `<!-- src: … -->` na KAŻDYM nagłówku i bullecie ·
materiał bez `src:` PRZENOSI (nie usuwa) do `## NIEZWERYFIKOWANE-POZA-DIGESTEM` · przecina zbiór
timestampów z `## NIEZAKLASYFIKOWANE` ze zbiorem z sekcji twierdzących.

⚠️ **`N<n>` jest RÓWNOPRAWNYM ID obok `D<n>`** — tak samo `NIEZAKLASYFIKOWANE#7` i lista `D1,D2,D14`
(nagłówek legalnie AGREGUJE wiele itemów). Test sprawdza **OBECNOŚĆ mapowania, nie jego składnię**.
WHY: wcześniejszy, ciaśniejszy wzorzec nie łykał ani `#`, ani przecinka, więc do kwarantanny leciały
nagłówki agregujące i cała sekcja `## NIEZAKLASYFIKOWANE` — 16 fragmentów zniknęło z notatki, bo Faza 4a
kwarantanny nie zapisuje. Mechanizm chroniący przed cichą utratą materiału sam ją spowodował.

⚠️ **KWARANTANNA JEST LEPKA** — jest sekcją TERMINALNĄ (doklejaną na koniec pliku), więc nagłówek już
leżący w kwarantannie NIE przeklasyfikowuje sekcji z powrotem na „twierdzącą". WHY: bez tego każdy
przeniesiony nagłówek był przenoszony PONOWNIE w każdym przebiegu, a komenda odpala ten preflight
dwukrotnie (Faza 2p i przed Fazą 4b) — plik rósł o linijkę za każdym uruchomieniem (247→248).

Nagłówki-scaffolding (`## NIEZAKLASYFIKOWANE`, `## NIEZWERYFIKOWANE-POZA-DIGESTEM`) są ZWOLNIONE
z wymogu `src:` — bez tego wyjątku skrypt wrzucał do kwarantanny własne granice sekcji i przekrój
timestampów liczył się na pustym zbiorze. Uruchomienie DRUGIE jest idempotentne: stara kwarantanna
nie liczy się jako nowa porażka i nagłówek nie dubluje się.

**Exit codes:** `0` wszystko zmapowane, brak kolizji · `1` przeniesiono ≥1 blok bez `src:` ·
`2` błąd IO albo KOLIZJA timestampów NIEZAKLASYFIKOWANE↔sekcja twierdząca.
