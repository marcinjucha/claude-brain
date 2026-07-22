---
description: Prime the current context with the relevant DOMAIN-KNOWLEDGE shelf — model-driven note selection from the vault
argument-hint: <opis problemu>
allowed-tools: Read, Bash, Grep
---

# /brain-knowledge — załaduj półkę wiedzy domenowej do kontekstu

`/brain-knowledge <opis problemu>` dogrywa do BIEŻĄCEGO kontekstu **wiedzę domenową** —
atomowe noty z `03-Resources/<ctx>/knowledge/`. `/brain-load` ładuje tylko wysoką półkę
(pamięć projektu / status); noty domenowe są osiągalne tylko przez snapshot w skillu, co
wymaga wywołania agenta — więc doktryna nigdy nie ląduje w głównym kontekście roboczym, gdzie
Marcin chce z nią ROZUMOWAĆ. Ta komenda wypełnia dokładnie tę lukę: opisz problem, komenda
MODELOWO wybiera trafne noty (osąd modelu nad MOC — NIE mechaniczny ranker słów kluczowych)
i wczytuje je do kontekstu. Komenda globalna. Repo mózgu: `/Users/marcinjucha/Prywatne/projects/claude-brain`.

## Faza 0 — rozwiąż kontekst + pulę wiedzy
1. `pwd`. Dopasuj do `config.json` → `paths` (najdłuższy pasujący prefiks) → `context`.
   - **Zadeklarowany kontekst > cwd (KRYTYCZNE):** jeśli Marcin wskazał kontekst w promptcie
     (np. „halo efekt", „agency", „shadow-operator"), MA ON PIERWSZEŃSTWO — cwd to tylko DOMYŚLNY
     kontekst. Rozwiąż zadeklarowany w TEJ kolejności (jak `brain-load`): (1) znormalizuj synonim
     przez `paths[<cwd>].contextAliases` (np. „halo efekt"→`agency`); (2) rozwiąż nazwę kanoniczną
     przez `paths[<cwd>].contexts[<nazwa>]` (repo `multiContext: true`) — daje JEDNOZNACZNIE;
     (3) dopiero gdy repo nie ma `contexts` → dowolny wpis `paths` z tym `context`.
   - Opis problemu = argument komendy (`$ARGUMENTS`). Brak opisu → poproś o niego, nie zgaduj.
2. Rozwiąż katalog(i) wiedzy: własny `.knowledge[<ctx>].dir` **oraz KAŻDĄ** pulę z
   `.knowledge[<ctx>].inherits` (np. shadow-operator → +`general-business`). Bazę vaulta bierz
   z `.vault.path`. Odzwierciedla to `source_notes()` z `sync-knowledge.py` — puli bazowej NIE pomijaj.
3. Jeśli `.knowledge[<ctx>].active != true` → powiedz to wprost i ZATRZYMAJ się (nie ma czego ładować).

## Faza 1 — czytaj TANI indeks (MOC), nie wszystkie noty
- Przeczytaj `_MOC.md` z katalogu kontekstu ORAZ z każdej dziedziczonej puli. MOC (tytuły +
  jednolinijkowe haki + klastry etapowe) to powierzchnia retrievalu — NIE czytaj wszystkich
  ~91 pełnych not, żeby zdecydować.
- Dopiero gdy MOC nie wystarcza → jako wtórny indeks wylistuj nazwy plików `.md` +
  frontmatter `tags` (`type/context/status/tags/used-by`).

## Faza 2 — MODELOWY wybór
Mając opis problemu, OSĄDŹ na podstawie MOC/indeksu, które atomowe noty są trafne. Zrób
shortlistę. To osąd modelu nad MOC, NIE silnik punktacji — bierz klaster istotny dla problemu.

## Faza 3 — PROPOSE-THEN-CONFIRM, potem załaduj
- Pokaż Marcinowi shortlistę PRZED wczytaniem: dla każdej noty tytuł + jednolinijkowe
  „dlaczego trafna" + z której puli (kontekst / baza). Pogrupuj. Trzymaj się selektywności —
  klaster, nie cała baza.
- Po potwierdzeniu: przeczytaj wybrane noty W CAŁOŚCI z VAULTA i wyłóż ich esencję do kontekstu.

## Twarde ograniczenia (każde z WHY)
1. **Czytaj noty z VAULTA `03-Resources/<ctx>/knowledge/` (źródło/canon) — NIGDY ze snapshotów
   skilla `references/knowledge/`.** WHY: snapshoty dryfują i są leniwe; vault to jedyna droga do
   not jeszcze niewpiętych w żaden skill.
2. **Honoruj `inherits`** — kontekst biznesowy ciągnie pulę(-e) bazowe; odtwórz rozwiązanie z
   `sync-knowledge.py`. WHY: inaczej gubisz uniwersalny craft dostępny temu kontekstowi.
3. **SELEKTYWNIE + propose-then-confirm** — ładuj klaster, nie wszystko. WHY: wczytanie na ślepo
   wszystkich not = puchnięcie kontekstu i szum, który rozcieńcza sygnał.
4. **READ-ONLY** — komenda nic nie zapisuje, nie cache'uje, nie tworzy artefaktu; czyta vault
   na żywo przy każdym uruchomieniu. WHY: żadnej trzeciej kopii wiedzy do utrzymania.
5. **UZUPEŁNIA `so-agent`, NIE zastępuje go.** Decyzje domenowe / pracę wieloetapową / deliverable
   routuj przez `so-agent` (on WYKONUJE robotę); `/brain-knowledge` używaj, gdy chcesz mieć doktrynę
   OBECNĄ we wspólnym kontekście, by wspólnie rozumować / krytykować / decydować. WHY: nie kolidować
   ze stałą regułą „decyzje domenowe przez so-agent" — ta komenda tylko wnosi wiedzę, nie decyduje.

> Mózg = źródło. `/brain-load` = wysoka półka (status). `/brain-knowledge` = półka domenowa
> (doktryna) na żądanie. so-agent = wykonanie. Trzy różne role — nie mieszaj.
