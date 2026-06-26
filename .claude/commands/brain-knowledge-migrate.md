---
description: Migrate ONE skill's domain knowledge into the brain knowledge-system — EXTRACT (your skills, thin them) or MIRROR (team-shared skills, copy only). Usage /brain-knowledge-migrate [skill] [--mirror]
argument-hint: [skill] [--mirror]
allowed-tools: Bash, Read, Edit, Task
---

# /brain-knowledge-migrate — zmigruj wiedzę jednego skilla do mózgu

Migruje wiedzę domenową JEDNEGO skilla do knowledge-system mózgu. Komenda NIE powtarza metodyki —
**ENFORCE'uje bramkę walidacji + rozdział na dwa tryby**. Per-krokowy szczegół (schemat notatki,
reguła anty-dryf, forma pointer, kontrakt skill↔mózg, bezstratność 5a/5b/5c) żyje w JEDNYM źródle:
**`/Users/marcinjucha/Library/Mobile Documents/iCloud~md~obsidian/Documents/AI/_system/knowledge-system.md`**
(sekcje „Migracja skilla (procedura)", „Kontrakt skill ↔ mózg", „Schemat notatki"). Czytaj je, nie przepisuj.

Para z `/brain-knowledge-init` (onboarding kontekstu) i `/brain-update` (osąd: merge, awans emerging→canon).
Repo mózgu (skrypty/config): `/Users/marcinjucha/Prywatne/projects/claude-brain`.

## ⭐ RDZEŃ KOMENDY — dwa tryby (EXTRACT vs MIRROR)

|  | **EXTRACT** (default — TWOJE skille) | **MIRROR** (`--mirror` — WSPÓŁDZIELONE/zespołowe, np. Scandit `ios-*`) |
|---|---|---|
| Ciało skilla | ŚCIENIONE (wiedza → pointery) | **NIETKNIĘTE** (zespół trzyma pełny skill) |
| Notatka w mózgu | `home: brain` (mózg = źródło prawdy) | `home: <skill-slug>` (lustro; skill = źródło prawdy) |
| Blok `## Knowledge` w skillu? | TAK | **NIE** |
| Snapshot do `references/knowledge/` skilla? | TAK (sync mózg→skill) | **NIE — repo skilla całkowicie nietknięte** |
| Kierunek synca | mózg → skill (snapshot) | skill → mózg (odśwież lustro, gdy skill się zmieni) |
| Korzyść | single-source-w-mózgu + skill nadal odpalalny | tylko brain-side: notatka przeglądalna / surface'owalna / linkowalna / reużywalna przez TWOJE inne skille — BEZ zmiany tego, co widzi zespół |
| Bramka walidacji | pełne 5a + 5b + 5c | 5a (notatka == wiedza skilla) + 5b (niezależna kopia bezstratna); 5c funkcjonalne N/A (skill bez zmian) — zamiast tego potwierdź, że notatka czyta się SAMODZIELNIE |

**PO CO MIRROR:** skill współdzielony z zespołem (Scandit `ios-*`) MUSI zostać kompletny dla
współpracowników, a vault mózgu nie jest z nimi dzielony — więc wszystkie korzyści bazy wiedzy
dostajesz przez **SKOPIOWANIE (lustro)** wiedzy do mózgu, NIGDY nie ścieniając skilla ani nie dotykając jego repo.

## Faza 0 — ustal skill + tryb
- Skill z `$1`. Brak → zapytaj który skill.
- Sprawdź, że katalog skilla istnieje (`skills/<skill>/SKILL.md` w repo kontekstu). Nie istnieje → zapytaj/przerwij, NIE działaj na ślepo.
- **Dla MIRROR rozwiąż `<ctx>`** z REPO skilla → kontekstu w `config.json` `.knowledge` (np. skill w `digital-shelf-ios` → `scandit`; notatka-lustro ląduje w `03-Resources/scandit/knowledge/`). Potwierdź, że `<ctx>` jest zarejestrowany w configu.
- Tryb: **EXTRACT** domyślnie; **MIRROR** gdy `--mirror` LUB gdy skill jest współdzielony z zespołem.
  Niejasne, czy współdzielony? → zapytaj wprost: „czy ten skill jest używany przez zespół (np. repo
  iOS/Scandit, nie tylko Twoje)?". Zespołowy = MIRROR.
- **Potwierdź tryb przed jakimkolwiek działaniem** (blast radius MIRROR vs EXTRACT jest inny — EXTRACT
  zmienia ciało skilla, MIRROR nie). Nie ruszaj dalej bez potwierdzenia.

## Faza 1 — inwentaryzacja + plan
Wg playbooka w `_system/knowledge-system.md` („Migracja skilla", krok 1–2) — NIE powielaj kroków, wykonaj je:
- Rozdziel ciało SKILL.md: PROCEDURA („jak zrobić" — zostaje) vs WIEDZA domenowa („co wiemy" — idzie do notatek).
- Dla każdego kawałka wiedzy: **dedup-search** w `03-Resources/<ctx>/knowledge/` (reguła anty-dryf) →
  ROZSZERZ istniejącą notatkę, nie twórz rodzeństwa. Slug = kebab-case ASCII, ≥2 znaki, bez wiodących cyfr.
- Zaplanuj notatki (nowe / do rozszerzenia) + `status` (canon jeśli z dojrzałego skilla; emerging jeśli świeży wzorzec).
- Przedstaw plan (lista notatek + tryb) i potwierdź z użytkownikiem przed Fazą 2.

## Faza 2 — wykonanie (notatki: bezpośrednio; SKILL.md: przez `ai-manager-agent`)
Notatki w mózgu to pliki vaulta (NIE artefakt-definicja) → pisz/rozszerzaj je BEZPOŚREDNIO (lossless, slug-rule, schemat notatki z kontraktu).

- **EXTRACT:**
  - Notatki: `home: brain`.
  - Ścień `SKILL.md` (usuń prozę wiedzy, dodaj blok `## Knowledge` w formie **pointer** `@references/knowledge/<slug>.md` + self-check „wylistuj złożone notatki").
  - ⚠️ Edycja `SKILL.md` (plik-artefakt) MUSI iść przez subagenta **`ai-manager-agent`** (reguła MUST) — main loop NIE pisze SKILL.md sam, nawet z pełnym kontekstem.
- **MIRROR:**
  - Notatka: `home: <skill-slug>` (lustro), `status: mirror`, `mirror-source: <abs-path do SKILL.md>` (umożliwia silnikowi advisory `mirror-stale`), `status` ≠ `canon` (źródłem jest skill).
  - **NIE dotykaj `SKILL.md` ani repo skilla. NIE dodawaj bloku `## Knowledge`. NIE pisz snapshotu.** Lustro żyje tylko w mózgu.

## Faza 3 — sync
- **EXTRACT:** `python3 /Users/marcinjucha/Prywatne/projects/claude-brain/scripts/sync-knowledge.py --context <ctx> --used-by` (snapshot mózg→`references/knowledge/` + auto-derive `used-by`).
- **MIRROR:** pomiń snapshot (skill nietknięty, nie jest konsumentem). Lustro pozostaje wyłącznie notatką w mózgu; odświeżasz je ręcznie, gdy zespołowy skill się zmieni.

## Faza 4 — WALIDACJA (BRAMKA — NIE pomijać)
Pełny szczegół: `_system/knowledge-system.md` krok 5 (5a/5b/5c). Bez czystych wszystkich warstw migracja NIE jest „done".
- **5a — mechaniczna (grep):**
  - EXTRACT: każda teza/dyscyplina/liczba/przykład (a) ZNIKŁA z nowego ciała SKILL.md (zero duplikacji) **oraz** (b) jest w którejś notatce snapshotu; 0 osieroconych tez; 0 dangling (`sync-knowledge.py --check` exit 0).
  - MIRROR: notatka == wiedza skilla (nic nie zgubione); repo skilla bez żadnych zmian (`git status` czysty po stronie skilla).
- **5b — NIEZALEŻNY agent (adwersaryjny):** ODDZIELNY, świeży agent (NIE ten, co migrował — `fork` lub `ai-manager-agent`) porównuje OLD vs NEW i raportuje WSZYSTKO zgubione/zniekształcone/osłabione (warunek „kiedy/kiedy-nie", niuans, liczba, przykład, ton). Domyślnie zakłada, że coś wypadło, i musi jawnie wykluczyć.
- **5c — funkcjonalna:**
  - EXTRACT: świeży agent odpala ścieniony skill na REALNYM przypadku — potwierdź, że sam dociąga notatki (self-check je listuje) i stosuje dyscypliny w wyniku.
  - MIRROR: N/A (skill bez zmian) — zamiast tego potwierdź, że notatka-lustro czyta się SAMODZIELNIE (zrozumiała bez ciała skilla).

## Faza 5 — commit
Stage **JAWNIE** (nazwane ścieżki — nigdy `git add -A`; repo bywa z niepowiązaną pracą in-flight):
- EXTRACT: notatki vaulta + ścieniony `SKILL.md` + snapshoty `references/knowledge/`.
- MIRROR: TYLKO notatki vaulta.
Komunikat commita = tryb (EXTRACT/MIRROR) + który skill + wynik walidacji (5a/5b/[5c]). (Vault to osobne repo od repo skilla — commituj w odpowiednim.)

## Raport
Podsumuj: (a) skill + tryb, (b) notatki utworzone/rozszerzone (slugi), (c) co ze SKILL.md (ścieniony przez ai-manager-agent / nietknięty), (d) wynik 3-warstwowej bramki, (e) co zacommitowano i gdzie.
