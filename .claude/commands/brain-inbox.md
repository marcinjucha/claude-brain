---
description: Triage skrzynki mózgu (00-Inbox, capture'y z Telegrama) — rozdziel każdy element do właściwego trackera, potem usuń przetworzony plik
argument-hint: [--dry]
allowed-tools: Read, Write, Bash, Glob, mcp__notion__notion-fetch, mcp__notion__notion-search, mcp__notion__notion-create-pages, mcp__notion__notion-update-page
---

# /brain-inbox — triage skrzynki mózgu → tracker, potem czyść

Klasyfikuje każdy capture w `00-Inbox` (notatki wpadające z Telegrama), kieruje go do
właściwego trackera (Notion / JIRA / Prospecting Tracker), a po **potwierdzonym i udanym
zapisie** USUWA plik capture'a. Cel: skrzynka wyczyszczona do zera.

Flaga `$ARGUMENTS`: `--dry` — tylko raport (klasyfikuj i wypisz tabelę routingu, NIC nie
zapisuj i NIC nie usuwaj).

Repo mózgu (źródło config/ścieżek, działa z każdego projektu):
`/Users/marcinjucha/Prywatne/projects/claude-brain`. Czytaj jego `config.json` po ścieżce
absolutnej — komenda jest globalna i bywa uruchamiana spoza repo. NIE hardkoduj ścieżki vaultu.

## Routing — dokąd trafia element

Źródło prawdy: `config.json`. Skrót docelowych trackerów:

| Typ elementu | Tracker / akcja | Źródło | Kluczowe property |
|--------------|-----------------|--------|-------------------|
| **ZADANIE** — errand prywatny ("kup", "dodać do arkusza", "zadzwoń", "zarezerwuj") | Notion **personal Tasks** | `collection://29084f14-76e0-80be-ac06-000b9ee2fc4f` | `Task` (tytuł), `Status` (`Not Started`/`Todo`), `Priorytety`, `Area`, `Notes` |
| **ZADANIE** — praca / Scandit (rzadkie) | JIRA projekt **SHELF**, cloudId `a19c74f3-95cf-4d55-9d33-366adfe6f7a0` | create issue | summary z treści; jeśli brak narzędzia create → zgłoś do ręcznego wpisu |
| **ZADANIE** — agencja / Halo Efekt | Notion **agency Tasks** | `collection://29284f14-76e0-8062-a18d-000bfce0cf23` | `Name` (tytuł), `Status`, `Priority`, `Notes` |
| **LEAD-KREATOR** — nazwa twórcy + link social/Instagram/YouTube | shadow-operator **Prospecting Tracker** | `collection://9cd84f14-76e0-823a-9146-876ae3400d3c` | `Info` (tytuł = nazwa twórcy), `Description`, `Platform` (Instagram/YouTube), `Contact Info` (URL), `Status`, `Notes`. ⚠️ property to `ER`, nie `Engagement Rate` — zostaw `ER` puste (nieznane przy capture) |
| **ŚMIEĆ / DUPLIKAT / pusty** ("Yo", powitania, pusta treść) | brak zapisu | — | tylko do usunięcia |

Lead-kreator to NOWY prospekt, NIE zadanie. Gdy element niejednoznaczny — pokaż go w tabeli
oznaczony `?`, żeby użytkownik rozstrzygnął na etapie potwierdzenia.

## ⚠️ Kolejność bezpieczeństwa (load-bearing — usunięcie jest nieodwracalne)

1. Zbuduj proponowaną tabelę routingu.
2. **UŻYTKOWNIK POTWIERDZA** (Faza 3).
3. Dla każdego potwierdzonego elementu: utwórz wpis w trackerze **i zweryfikuj, że zapis się udał**.
4. **DOPIERO POTEM** usuń plik capture'a (`rm`).
5. Śmieci: usuń bez zapisu.
6. Jeśli zapis się NIE udał — ZACHOWAJ plik i zgłoś go w raporcie. NIGDY nie usuwaj przed potwierdzonym, udanym zapisem.

## Faza 0 — config + skan inboxu
1. Wczytaj `config.json` (ścieżka absolutna) → `vault.path` + klucz `inbox` (`00-Inbox`).
   Złóż katalog inboxu: `<vault.path>/00-Inbox/`.
2. Sparsuj `$ARGUMENTS` — ustal, czy podano `--dry`.
3. `Glob` `*.md` w katalogu inboxu. Jeśli pusto — zaraportuj „skrzynka pusta" i zakończ.

## Faza 1 — wczytaj capture'y
- `Read` każdego pliku; sparsuj frontmatter (`source`, `status`, `captured`, `from`) + treść.
- Przetwarzaj WYŁĄCZNIE pliki z `status: inbox`. Pozostałe pomiń (nie ruszaj).

## Faza 2 — klasyfikuj + zaproponuj routing (osąd)
Dla każdego capture'a przypisz TYP + cel wg tabeli routingu:
- **ZADANIE** → wywnioskuj kontekst z treści (prywatny errand → personal Tasks; praca/Scandit → JIRA SHELF; agencja/Halo Efekt → agency Tasks).
- **LEAD-KREATOR** (nazwa twórcy + link social/IG/YT) → Prospecting Tracker.
- **ŚMIEĆ / DUPLIKAT / pusty** → tylko do usunięcia, bez zapisu.
Niejednoznaczne oznacz `?`. Zbuduj proponowaną tabelę.

## Faza 3 — potwierdź routing
Pokaż tabelę: `pozycja → typ → tracker/akcja → usunięcie`. Poproś użytkownika o potwierdzenie
lub korektę (zmiana typu/celu, rozstrzygnięcie `?`). Czekaj na odpowiedź.
**Przy `--dry`: wypisz tabelę i ZAKOŃCZ tutaj — żadnych zapisów ani usunięć.**

## Faza 4 — utwórz wpisy w trackerze
Dla potwierdzonych elementów twórz wpisy z właściwą kolekcją + property (jak w tabeli routingu):
- Notion: `notion-create-pages` na właściwym `collection://...`.
- JIRA SHELF (rzadkie): jeśli dostępne narzędzie create issue — utwórz; w przeciwnym razie ZACHOWAJ plik i odnotuj element do ręcznego wpisu.
- **Zweryfikuj każdy zapis** (otrzymane id/URL strony). Zapis bez potwierdzenia = traktuj jak nieudany.

## Faza 5 — usuń capture'y
- Usuń (`rm`) każdy plik, którego zapis się POWIÓDŁ, oraz każdy plik-śmieć.
- ZACHOWAJ + oznacz każdy, którego zapis się nie udał (lub czeka na ręczny wpis JIRA).

## Faza 6 — raport
Wypisz: utworzone wpisy (typ, tracker, id/link), usunięte jako śmieci, pominięte/błędy (pliki
zachowane wraz z powodem). Przy `--dry`: tylko proponowana tabela routingu, bez akcji.
