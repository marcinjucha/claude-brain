---
description: Onboard a context to the knowledge-system (vault knowledge dir + activate + pre-commit)
argument-hint: [context]
allowed-tools: Bash, Read, Edit
---

# /brain-knowledge-init — podłącz kontekst do bazy wiedzy

Onboarduje kontekst (`shadow-operator` / `agency` / `scandit` / nowy) do knowledge-system:
tworzy katalog wiedzy w vaulcie + aktywuje + instaluje pre-commit u konsumentów, potem
naprowadza na pracę z TREŚCIĄ. Para z `/brain-load` (surfacing) i `/brain-update` (maintenance).
Kontrakt: `_system/knowledge-system.md`.

Repo mózgu (config/skrypty): `/Users/marcinjucha/Prywatne/projects/claude-brain`.

## Faza 0 — ustal kontekst
Kontekst z argumentu `$1`. Brak → wywnioskuj z cwd→`config.json` `.paths` (jak `/brain-load`
Faza 0) albo zapytaj. Kontekst MUSI być zarejestrowany w `config.json` `.knowledge.<ctx>`
(z `consumers`). Sprawdź:
`jq -e '.knowledge["<ctx>"]' /Users/marcinjucha/Prywatne/projects/claude-brain/config.json`.
Brak wpisu → **najpierw dodaj** wpis i dopiero wtedy uruchom Fazę 1. Przykład wpisu do
`.knowledge`:
```json
"<ctx>": { "dir": "03-Resources/<ctx>/knowledge", "active": false, "consumers": ["/abs/ścieżka/repo/.claude/skills"] }
```
(`consumers` = lista folderów `skills/` repo, które mają dostawać snapshot + pre-commit.)

**Kontekst może być PULĄ BAZOWĄ:** wpis w `.knowledge` z `active: true` i `consumers: []` (brak własnych konsumentów), a INNE konteksty wciągają je przez `inherits: [...]` — pule bazowe to `general-business` (uniwersalny craft biznesowy) i `general-technical` (uniwersalny craft inżynieryjny/webowy). Onboarding nowego kontekstu oznacza dopisanie do jego wpisu w configu RĘCZNIE tych pul bazowych, które go dotyczą (`["general-business"]` dla biznesu, `["general-technical"]` dla web-devu, OBU jak `agency`; stack iOS/inne mogą nie dziedziczyć żadnej) — tool nie scaffolduje tej relacji.

## Faza 1 — uruchom plumbing
```bash
bash /Users/marcinjucha/Prywatne/projects/claude-brain/scripts/knowledge-init.sh <context>
```
Robi 3 kroki, idempotentnie: (1) katalog wiedzy w vaulcie + starter `_MOC.md`,
(2) `active:true` w `config.json` (backup `config.json.bak`), (3) pre-commit w każdym repo
z `consumers`.
⚠️ Jeśli repo konsumenta ma już własny `pre-commit` (np. iOS/swiftlint w `digital-shelf-ios`) —
installer NIE nadpisze, tylko ostrzeże; trzeba zmergować ręcznie jedną linię (skrypt to wypisze).

## Faza 2 — treść (per skill, ręcznie / z agentem)
Plumbing nie pisze wiedzy — to osobna praca z TREŚCIĄ, per skill:
- Napisz notatki wiedzy w `03-Resources/<ctx>/knowledge/` — atomowe, **tytuł = teza**, wg
  `_system/knowledge-system.md` (schemat notatki: `type/context/id/status`).
- W skillach tego kontekstu dodaj blok `## Knowledge` + wskaźniki `@references/knowledge/<slug>.md`
  (ekstrakcja jak w pilocie `so-monetisation-audit`: wiedza domenowa → notatka, skill zostaje
  cienką procedurą).
- Sync zadzieje się sam (SessionStart + pre-commit); ręcznie:
  `python3 /Users/marcinjucha/Prywatne/projects/claude-brain/scripts/sync-knowledge.py --context <context>`.

## Faza 3 — raport
Podsumuj: (a) co utworzono (katalog wiedzy + `_MOC.md`, czy nowy czy już istniał),
(b) czy aktywowano w configu, (c) gdzie zainstalowano pre-commit (lista konsumentów),
(d) ostrzeżenia (konsument poza git / istniejący hook do ręcznego merge),
(e) następny krok: praca z treścią (Faza 2).
