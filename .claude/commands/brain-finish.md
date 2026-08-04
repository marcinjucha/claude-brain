---
description: "Zamknij sesję — brain-update → lekcje do memory.md → wiedza domenowa → commit per repo. Jeden przebieg, bez bramek. Usage: /brain-finish [kontekst]"
argument-hint: [kontekst]
allowed-tools: Read, Edit, Write, Bash, Grep, Agent
---

# /brain-finish — zamknięcie sesji jednym przebiegiem

Orkiestrator zamknięcia sesji: uruchamia `/brain-update`, zbiera lekcje repo do `memory.md`,
odpala silnik wiedzy domenowej i commituje per repo. **Zero pytań i zero bramek w trakcie** —
jedyny checkpoint to raport na końcu. Cienki router: nie powtarza mechaniki podkomend.

`$ARGUMENTS` = **zadeklarowany kontekst** (opcjonalny) — JEDYNY argument.
Repo mózgu (config/skrypty): `/Users/marcinjucha/Prywatne/projects/claude-brain`.

## Fazy

```
0: Preflight — kontekst, memory.md N, kandydaci repo, baseline gita   (INLINE, zawsze)
1: /brain-update                                                      (FORK, zawsze)
2: lekcje sesji → memory.md  (/ai-extract-memory SPEC)                (FORK, self-skip)
3: /brain-extract-knowledge  (bramka odroczona)                       (FORK, warunkowo)
4: zapis kolejki odroczonej do notatki roboczej                       (INLINE)
5: Commit per repo                                                    (INLINE — nie delegować)
6: Raport                                                             (INLINE)
```

**Kolejność jest WYMUSZONA — dwa sprzężenia danych, nie jedno.**
- **1 → 3:** `/brain-update` Faza 3.8 surface'uje 0–3 KANDYDATÓW na noty wiedzy i przekazuje ich
  silnikowi. brain-finish **czyta tę listę** i nigdy nie buduje drugiej logiki wyboru.
- **2 → 3:** `/brain-extract-knowledge` Faza 1 ingestuje NAJPIERW sekcje `## Domain Concepts` /
  `## Architecture Decisions` z `memory.md` — woli źródła już zdestylowane nad surową sesją.
  Wyekstrahuj lekcje PRZED wiedzą, inaczej silnik traci swoje preferowane wejście.

## ⚠️ CRITICAL: WYKONUJ FORKI I SLASH-KOMENDY — NIGDY ŚWIEŻEGO AGENTA

```
NIE:
❌ Agent(subagent_type: "ai-manager-agent" | "brain-manager" | "general-purpose") dla Faz 1–3
❌ opisywać, co zrobi /brain-update, zamiast go wykonać
❌ delegować Fazy 5 (commit) — ani forkowi, ani agentowi

TAK:
✅ Agent(subagent_type: "fork") dla Faz 1–3 — fork dziedziczy TĘ konwersację
✅ Fazy 0, 4, 5 i 6 inline
✅ przekazać każdemu forkowi rozwiązaną trójkę <ctx>/<vault>/<memory> jako WARTOŚCI
✅ SKIP to normalny wynik, nie porażka do ponowienia
```
Powód w jednym zdaniu: wszystkie trzy podkomendy mają TĘ konwersację jako główne źródło, a świeży
agent jej nie widzi. Pełne WHY — Reguła 1.

## Krytyczne reguły

**1. Fazy 1–3: `subagent_type: "fork"` albo inline. NIGDY świeży agent.**
Wszystkie trzy podkomendy biorą TĘ konwersację jako główne źródło: `/brain-update` Faza 1 nazywa
je wprost („TA sesja/konwersacja"), `/ai-extract-memory` analizuje konwersację,
`/brain-extract-knowledge` Faza 2 destyluje materiał sesji. Świeży agent startuje pusty i zwróci
puste albo wymyślone. **Nie hipotetycznie:** własny wrapper `/ai-extract-memory` deleguje do
ŚWIEŻEGO `ai-manager-agent` z instrukcją „analyze the current conversation", której ten agent nie
widzi — dlatego **brain-finish idzie za SPEC-em tej komendy, nie za jej wrapperem.** Zapisane jako
reguła z WHY, bo każda inna komenda w tym ekosystemie robi to zakazanym sposobem i pierwszy
przebieg będzie chciał do tego wzorca dopasować.

**2. Cienki router: nigdy nie powtarzaj mechaniki podkomendy.**
Każda faza dostaje jedno zdanie kontraktu (co musi wrócić) + wskaźnik do SPEC-u + wyłącznie DELTY,
które narzuca brain-finish. WHY: orkiestrator opisujący kroki podkomendy starzeje się szybciej niż
sama podkomenda. Realny precedens 2026-08-03: plik opisujący ZMIANY w narzędziu rozjechał się
z kanonem w czterech miejscach w cztery dni, bo każda kolejna decyzja unieważniała jego deltę, a nie
treść — i nie było tego widać, dopóki oba pliki nie stanęły obok siebie. Ta sama zasada anty-dryfu,
dla której `_system/templates/status-block.md` jest JEDYNĄ definicją formatu bloku statusu.

**3. `/ai-curate-memory`: TYLKO wykrycie i rekomendacja, nigdy wykonanie.**
Zapisy wiedzy są ADDYTYWNE (nowa nota `emerging`, nic nie ubywa, trywialnie odwracalne) — dlatego
ich bramkę można odroczyć. Kuracja jest ODEJMUJĄCA I PRZENOSZĄCA: jej Step 3 kończy się twardym
„WAIT for user confirmation", Step 4 przepisuje pliki CLAUDE.md i SKILL.md w całym projekcie i
USUWA wpisy z `memory.md`, a Step 4b odmawia usunięcia wpisu-celu bez potwierdzonego zapisu do
mózgu. Przebieg bez bramki albo się zatnie, albo wyrzuci syntezę, której nie ma nigdzie indziej.
Faza 0 mierzy N; Faza 6 rekomenduje.

**4. ZERO pytań i zero bramek w trakcie. Świadome odstępstwo.**
Rodzina `ai-*` otwiera się pytaniami doprecyzowującymi; brain-finish celowo tego nie robi — i ten
plik to mówi, żeby audyt nie „naprawił" bramki z powrotem. WHY: komenda odpala się z nawyku na
koniec sesji, a bramka-pytanie w tym momencie to dokładnie to tarcie, które zabiło standalone
opt-in (`/brain-update` Faza 3.8 zapisuje dowód: „standalone opt-in zamiera (dowód: nudge Faza 4(e)
→ 0 notatek)"). Bramka wiedzy nie jest usunięta, jest ODROCZONA przez `status: emerging` + kolejkę
do przeglądu. Bramki kuracji odroczyć nie można (Reguła 3), więc kuracji się nie wykonuje. Jedyny
checkpoint użytkownika to raport Fazy 6.

**5. Rozwiąż kontekst RAZ, w Fazie 0, i przekazuj go jako wartości.**
`claude-marketing` mapuje się domyślnie na `shadow-operator`, a na kontekst agencyjny przez
zadeklarowany alias; każda podkomenda ma własną Fazę 0, która wykrywa kontekst z cwd od nowa —
niezależne rozwiązywanie może wysłać Fazę 1 do jednego kontekstu, a Fazę 3 do drugiego i rozerwać
jedną sesję na dwa mózgi.

**6. Izolacja awarii.** Padnięta faza nie blokuje pozostałych. Jej ścieżki są WYŁĄCZONE z commita
i raportowane jako „zapisane, niescommitowane — faza padła". Nigdy nie commituj po cichu połowicznego
stanu.

**7. Trello w biegu bez bramek: wykonuj tylko to, co preautoryzowane.** Komentarze (bez pytania) i
NOWE karty w liście `📥 Inbox` (id `6a6a3cfd664820d00d897e9b`). Przenoszenie kart, odznaczanie
(`dueComplete`) i labelki zostają PROPOZYCJAMI w raporcie — odhaczanie kart to własny checkpoint
przeglądu Marcina i przebieg bez bramek nie ma prawa go zabrać.

**Brak sekcji „Socratic Self-Reflection Gate" — świadomie.** Ta bramka istnieje, by wyłapać
niedopasowanie ZANIM agent dostanie ręcznie zbudowany kontekst; tu forki dziedziczą sesję,
a routing jest stały i linearny, więc refleksja per-faza byłaby ceremonią. Zapisane, żeby jej brak
czytał się jako decyzja.

---

## Faza 0 — Preflight (INLINE, zawsze)

(a) **Rozwiąż `<ctx>` / `<vault>` / `<memory>`** wg `/brain-update` Faza 0 (zadeklarowany
`$ARGUMENTS` > cwd→`config.json` `.paths`).
(b) `wc -l <project>/memory.md` → **N**, wobec progów 150 / 180 / 200.
(c) **Wypisz kandydatów repo:** repo vaulta Obsidiana, repo projektu (cwd) oraz `claude-brain`
TYLKO jeśli ta sesja dotknęła jego skryptów/configu.
(d) `python3 /Users/marcinjucha/Prywatne/projects/claude-brain/scripts/session-commit-scope.py --survey <repo>…` — złap
**PRZED-ISTNIEJĄCY baseline** brudnych ścieżek / wpisów indeksu / untracked **zanim cokolwiek
zostanie zapisane**. Ten baseline jest tym, co czyni listę „zostało niescommitowane" z Fazy 6
ZMIERZONĄ, a nie zgadniętą.

Wypisz jednorazowy plan preflightu (kontekst + jak rozwiązany, N, repa, które fazy prawdopodobnie
się wykonają) i **jedź dalej. Bez pytań** (Reguła 4).

**Kontrakt dalej:** `<ctx>`, `<vault>`, `<memory>`, N, lista repo, baseline survey.

## Faza 1 — `/brain-update` (FORK, zawsze, bez skipu)

**Kontekst do forka:** rozwiązana trójka; ograniczenie Trello z Reguły 7; plus „jesteś wewnątrz
brain-finish — na końcu idzie raport, więc NIE proś o potwierdzenia, o które normalnie byś poprosił;
cokolwiek niepotwierdzalne wraca jako PROPOZYCJA w Twoim zwrocie".

**Musi wrócić:** (a) zapisane ścieżki w vaulcie (wysoka półka, notatka robocza, blok statusu, MOC);
(b) **lista kandydatów z Fazy 3.8 (0–3)** — bramkuje Fazę 3; (c) jego sugestie lekcji repo z Fazy 3
/ Fazy 4(e); (d) Trello: co wykonane vs zaproponowane; (e) wynik snapshot-syncu z Fazy 3.7.

SPEC: `/Users/marcinjucha/Prywatne/projects/claude-brain/.claude/commands/brain-update.md`.

## Faza 2 — lekcje sesji → `memory.md` (FORK, self-skip przy braku sygnału)

Idzie za SPEC-em `/ai-extract-memory` — jego **ciałem promptu agenta** (tabela sygnałów, format
wpisu, limit 200 linii, raport liczby linii) — a **NIE** za jego wrapperem orkiestracyjnym
(Reguła 1).

**Kontekst do forka:** ścieżka `<memory>`; N; sugestie z Fazy 3/4(e) Fazy 1, żeby ta sama lekcja
nie została złapana dwa razy; oraz podział celu zapisu, dosłownie:
- uniwersalny, venture-niezależny craft → **NIE** do `memory.md`; podaj to na listę kandydatów Fazy 3
- reguła / pułapka / preferencja specyficzna dla repo albo skilla → `memory.md`
- niepewne → `memory.md` (fail-safe: to bufor, a `/ai-curate-memory` promuje później)

**Musi wrócić:** dodane wpisy (sekcja + tytuł), pozycje uniwersalnego craftu przekierowane do
Fazy 3, nowe N, albo „brak sygnału".

**WHY tej fazy nie można wyciąć:** `/brain-update` Faza 3 wprost ODMAWIA zapisu trwałych lekcji
repo i tylko SUGERUJE tę ścieżkę — Faza 2 domyka zawieszoną sugestię brain-update'u.

SPEC: `/Users/marcinjucha/.claude/commands/ai-extract-memory.md`.

## Faza 3 — wiedza domenowa (FORK, warunkowo)

**SKIP, gdy zachodzi którekolwiek — i powiedz które** (skip to normalny wynik, nie porażka):
1. `config.json` `knowledge[<ctx>]` nie istnieje albo `active != true`;
2. Faza 1 surface'owała ZERO kandydatów **ORAZ** Faza 2 nie przekierowała tu żadnej lekcji
   uniwersalnego craftu.

Inaczej: fork wykonuje `/brain-extract-knowledge` z przekazaną listą kandydatów.

**JEDYNE delty brain-finish wobec tego silnika:**
- jego Faza 4 (verify-confirm) jest **ODROCZONA, nie usunięta** → każda nota zapisana jako
  `status: emerging`, a **`canon` jest w przebiegu brain-finish ZABRONIONY** (promocja dzieje się
  wyłącznie w `/brain-update` Faza 3.7, po N≥3 odrębnych źródłach);
- każda zapisana/rozszerzona nota idzie do kolejki odroczonej z Fazy 4;
- zaraportuj, czy zregenerowano snapshoty — rozszerzenie szeroko konsumowanej noty ma szeroki
  promień rażenia (2026-07-29: rozszerzenie noty deklarowanej przez 9 skilli zregenerowało 9 plików
  snapshotów) i jest winne osobno zatwierdzonego przebiegu `sync-knowledge.py`.

**Musi wrócić:** noty utworzone/rozszerzone ze slugami i ścieżkami, dotknięty MOC, stan snapshotów,
albo „SKIPPED — <który warunek>".

SPEC: `/Users/marcinjucha/Prywatne/projects/claude-brain/.claude/commands/brain-extract-knowledge.md`.

## Faza 4 — zapis kolejki odroczonej (INLINE)

Dopisz kolejkę do przeglądu **do notatki roboczej sesji** (ten sam target, który rozwiązała
`/brain-update` Faza 2b; gdy target był niejednoznaczny → dopisz do pamięci projektu `<memory>`).

**Kolejka zawiera:** odroczoną bramkę wiedzy (noty `emerging` do zweryfikowania) + niezastosowane
propozycje Trello + ewentualny należny przebieg `sync-knowledge.py` + rekomendację
`/ai-curate-memory`, jeśli N tego wymaga.

**WHY kolejka MUSI trafić do pliku, nie tylko na czat:** w raporcie czatowym umiera razem z okienkiem,
co przeczy całemu sensowi tej komendy; w notatce roboczej podnosi ją następny `/brain-load`.

**WHY ta faza jest PRZED commitem (rozstrzygnięcie kolejności):** commit musi być OSTATNIM ZAPISEM
przebiegu, żeby wszystko, co ta sesja zapisała — łącznie z plikiem kolejki — było w środku, a raport
mówił prawdę o tym, co zostało zacommitowane. Odrzucony wariant: drugi mały commit na plik kolejki
PO raporcie — dawałby dwa commity w każdym przebiegu, a linia raportu o pierwszym byłaby już
nieaktualna w chwili wypisania.

## Faza 5 — Commit per repo (INLINE — NIE WOLNO delegować)

**WHY inline:** potrzebuje SUMY ścieżek ze wszystkich poprzedzających faz, a użytkownik musi
zobaczyć zawężony `git status --short` + `git diff --stat` przed wylądowaniem commita; najwyższy
promień rażenia, nie może siedzieć za filtrem wyjścia forka.

Mechanika, w tej kolejności:
1. `python3 /Users/marcinjucha/Prywatne/projects/claude-brain/scripts/session-commit-scope.py --survey <repo>…`
   — **przebieg ponowny** (drzewo zmieniło się od Fazy 0).
2. `python3 /Users/marcinjucha/Prywatne/projects/claude-brain/scripts/session-commit-scope.py --plan <repo> -- <path>…`
   z **sumą zapisanych ścieżek podaną przez model**, minus ścieżki faz, które padły (Reguła 6).
3. Pokaż zawężony `git status --short` + `git diff --stat` per repo.
4. `git add -- <paths>` — **WYMAGANE**, bo świeża nota wiedzy jest untracked, a
   `git commit -- <untracked-path>` się wywala. **Nigdy `git add -A`.**
5. `git commit -m "<msg>" -- <paths>` — `-m` **PRZED** `--`, ścieżki wypisane jawnie.
   WHY inline: `git commit -- <paths> -m "msg"` wywala się mylącym `pathspec '-m' did not match any
   file(s)` i wypisuje całą treść wiadomości jako brakującą ścieżkę; a zsh NIE robi word-splittingu
   na nierozwiniętej zmiennej, więc `P="a.md b.md"; git add $P` przekazuje JEDNĄ ścieżkę.
6. Wiadomość wg konwencji commitów projektu (WHY-focused, body 80–300 znaków) **BEZ prefiksu
   `[TICKET]`** — to konwencja gałęzi Scandit, a repa vaulta i mózgu nie mają gałęzi z ticketami.
   Prozę podawaj przez `-m`, nigdy heredocem.
7. **Tylko bieżąca gałąź** — bez tworzenia gałęzi, bez pusha.

SPEC stylu wiadomości: skill `ai-git-commit-patterns`.

## Faza 6 — Raport (INLINE)

W tej kolejności:
1. **Kontekst** — rozwiązana wartość + czy zadeklarowany, czy wywiedziony z cwd.
2. **Per pod-krok RAN / SKIPPED + powód**, z wyraźnym stwierdzeniem, że skip jest normalny (zero
   kandydatów wiedzy jest częste i poprawne).
3. **Co zapisano**, pogrupowane per system — wysoka półka vaulta · notatka robocza · noty wiedzy ·
   `memory.md`.
4. **Commity** — jedna linia per repo (repo, krótki sha, subject, liczba plików), a potem jawnie
   **przed-istniejące wpisy brudne/staged ZOSTAWIONE NIESCOMMITOWANE, wypisane po ścieżkach**.
   WHY obowiązkowo: 2026-07-29 cztery zmiany nazw zastage'owane przez wcześniejszą sesję wpadły do
   commita, który twierdził, że zawiera tylko pracę tamtej sesji — jawne stage'owanie NIE wystarcza,
   bo `git commit` commituje CAŁY indeks.
5. **Kolejka do przeglądu** (ta sama, którą zapisała Faza 4 — plus ścieżka pliku, w który wpadła).
6. **Nie zapisano i dlaczego**, w tym każda padnięta faza, której ścieżki wyłączono z commita.

## Argumenty i komendy

`$ARGUMENTS` = **zadeklarowany kontekst** — load-bearing dla repo dwukontekstowego, gdzie
zadeklarowany kontekst musi przebić domyślny z cwd.

**Follow-upy OFEROWANE, nie wykonywane** po raporcie: `/ai-curate-memory` gdy N tego wymaga,
`sync-knowledge.py` gdy przebieg jest należny, zastosowanie propozycji Trello.

**`continue` / `skip` / `back` / `status` / `stop` — CELOWO USUNIĘTE** (zapisane, żeby audyt nie
przywrócił ich jako „brakującej sekcji"): istnieją, by prowadzić checkpointy użytkownika per faza,
a ta komenda z założenia ich nie ma (Reguła 4). Bez bramki do przejścia `continue` jest no-opem;
`skip`/`back` zapraszałyby do przestawiania kolejności w biegu, co łamie dwa wymuszone sprzężenia
danych; `status` to dokładnie raport Fazy 6; a między fazami nie ma czego `stop`ować — przerywanie
jest zadaniem harnessa, a Reguła 6 już definiuje, co raportuje przebieg częściowy.

## Wystarczający kontekst (dla forków)

Fork **dziedziczy konwersację**, więc NIE powtarzaj mu materiału sesji. Prompt każdej fazy niesie
wyłącznie: (a) rozwiązaną trójkę `<ctx>`/`<vault>`/`<memory>`, (b) wartości zwrócone z faz wyżej,
(c) wskaźnik do SPEC-u, (d) delty, które narzuca brain-finish.

**Pytanie testowe:** „czy ten fork trafi do złego kontekstu, wyprowadzi ponownie listę, którą mu
podano, albo zdubluje zapis z góry?" — jeśli tak, brakującym elementem jest jedno z (a)–(d)
i nic innego tam nie należy.
