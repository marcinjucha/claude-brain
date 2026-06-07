---
description: Connect the current folder to the brain — load project memory + deep repo memory
argument-hint: [context]
allowed-tools: Read, Bash, Grep
---

# /brain-load — podłącz ten folder do mózgu

Wczytuje wiedzę o projekcie, w którym pracujesz, żeby Claude miał pełny obraz: **portfolio**
(pamięć projektu w vaulcie, wysoka półka) + **głęboki** (repo `CLAUDE.md`/`memory.md`).
Uruchamiana z DOWOLNEGO folderu (komenda globalna). Para z `/brain-update`.

Repo mózgu (config/ścieżki): `/Users/marcinjucha/Prywatne/projects/claude-brain`.

## Faza 0 — wykryj projekt
1. `pwd`. Dopasuj do `config.json` → `paths` (najdłuższy pasujący prefiks ścieżki).
   - Trafienie → masz `context`, `vault` (podfolder), `memory` (plik pamięci), `repoMemory`.
   - Brak → użyj `$1` jako kontekstu, albo zapytaj.

## Faza 1 — wczytaj górny poziom (mózg)
- Przeczytaj `vault.path`/`<vault>`/`<memory>` (np. `01-Projects/work/_scandit.md`) — status,
  co w toku, jak się łączy.
- Przeczytaj powiązane working notes (linki w pamięci projektu / pliki w `<vault>`).

## Faza 2 — wczytaj dolny poziom (repo)
- Przeczytaj `repoMemory` z bieżącego folderu (`CLAUDE.md`, `memory.md`) — głęboka wiedza techniczna.
- Jeśli istnieje `SESSION.md` w worktree — wczytaj (ulotny stan bieżącej gałęzi).

## Faza 3 — przedstaw obraz
Krótko podsumuj użytkownikowi: co to za projekt, na jakim etapie, co w toku, otwarte wątki,
i czego pamięć NIE wie (luki). Bez ścian tekstu — to brief startowy, nie raport.

> Pamięć projektu w mózgu = wysoka półka (status/połączenia). Głębokie lekcje techniczne
> NIE są tu kopiowane — żyją w repo `memory.md`. `/brain-load` czyta oba; nie scalaj ich.
