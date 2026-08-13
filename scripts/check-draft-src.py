#!/usr/bin/env python3
"""Sprawdź MECHANICZNIE, że każdy blok draftu notatki spotkania ma źródło w digeście. ZERO OSĄDU.

Wejście: `<work>/meeting-note-draft.md` (modyfikowany w miejscu) + `<work>/digest.md`.

Skrypt robi DOKŁADNIE trzy rzeczy:
  1. sprawdza, że KAŻDY nagłówek (`#…`) i KAŻDY bullet (`-`/`*`/`1.`) niesie `<!-- src: … -->`
     z ID itemu digestu — `D<n>` (kategoria) ALBO `N<n>` (pozycja `## NIEZAKLASYFIKOWANE`) —
     oba są RÓWNOPRAWNE; dozwolone też `NIEZAKLASYFIKOWANE#7` i lista `D1,D2,D14`,
  2. materiał BEZ `src:` PRZENOSI na koniec pliku do sekcji `## NIEZWERYFIKOWANE-POZA-DIGESTEM`
     (nie usuwa — usunięcie ukryłoby, że coś powstało bez źródła),
  3. przecina zbiór timestampów z `## NIEZAKLASYFIKOWANE` ze zbiorem z sekcji TWIERDZĄCYCH;
     niepusty przekrój ⇒ exit 2.

DLACZEGO `N<n>` MUSI BYĆ RÓWNOPRAWNE Z `D<n>` (zweryfikowane 2026-08-10): pozycje
`## NIEZAKLASYFIKOWANE` nie miały wtedy ID, więc ich bullety szły bez `src:`, leciały do kwarantanny,
a Faza 4a kwarantanny nie zapisuje — z notatki zniknęło 16 fragmentów, których przedmiotu nie dało się
nazwać, czyli dokładnie ten materiał, który ma być WIDOCZNY jako nierozstrzygnięty.

DLACZEGO `src:` JEST WYMAGANY: draft pisze ten sam agent, który czytał transkrypt, więc może
wprowadzić do notatki zdanie, którego nie ma w digeście — a Faza 3 rozstrzyga TYLKO po digeście.
Bez mapowania taki materiał wchodzi do vaulta bez werdyktu i bez cytatu.

DLACZEGO PRZEKRÓJ TIMESTAMPÓW JEST BŁĘDEM TWARDYM: ta sama wypowiedź nie może być jednocześnie
„niezaklasyfikowana" i podstawą twierdzenia — to dwie sprzeczne deklaracje o tym samym materiale,
i wersja twierdząca wygrywa po cichu przy zapisie.

NIE WOLNO — i dlaczego:
  - oceniać TREŚCI bloku ani jego przydatności — to osąd Fazy 2/3,
  - zgadywać brakującego `src:` po podobieństwie do itemu digestu — zgadnięte mapowanie wygląda
    dokładnie jak zweryfikowane,
  - usuwać materiału bez `src:` — przenosimy go do widocznej sekcji, żeby brak źródła był FAKTEM
    w raporcie, nie cichą stratą,
  - przepisywać, przestawiać ani reformatować bloków, które mają `src:`.

Exit codes: 0 = wszystko ma `src:`, brak kolizji · 1 = przeniesiono ≥1 blok bez `src:`
            · 2 = błąd wejścia/IO albo kolizja timestampów NIEZAKLASYFIKOWANE↔sekcja twierdząca.
"""

import argparse
import os
import re
import sys

# Dozwolone kształty ID: `D1` · `N7` · `NIEZAKLASYFIKOWANE#7` · lista `D1,D2,D14`.
# WHY tak luźno (zweryfikowane 2026-08-10 sprint kickoff catchup): wcześniejsze
# `[A-Za-z0-9_.\-]+` nie łykało ani `#`, ani przecinka — więc do kwarantanny leciały nagłówki
# sekcji, które legalnie AGREGUJĄ wiele itemów, oraz cała sekcja `## NIEZAKLASYFIKOWANE`.
# Efekt był odwrotny do celu skryptu: mechanizm chroniący przed cichą utratą materiału sam
# usunął z notatki 16 fragmentów, których przedmiotu nie dało się nazwać — czyli dokładnie ten
# materiał, który ma być widoczny jako nierozstrzygnięty. Luźniejszy zbiór znaków nie osłabia
# testu: brak `src:` NADAL jest porażką, sprawdzamy obecność mapowania, nie jego składnię.
SRC = re.compile(r"<!--\s*src:\s*([^>]{1,160}?)\s*-->")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+\S")
BULLET = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+\S")
TIMESTAMP = re.compile(r"\d?\d:\d\d(?::\d\d)?")
# Cytat w linii — granulacja kolizji (patrz `stamps` w `main`).
QUOTED = re.compile("[\u201e\u201c\"]([^\u201e\u201d\u201c\"]{3,})[\u201d\u201c\"]")
UNCLASSIFIED = re.compile(r"^\s{0,3}#{1,6}\s*NIEZAKLASYFIKOWANE", re.IGNORECASE)
QUARANTINE = "## NIEZWERYFIKOWANE-POZA-DIGESTEM"
QUARANTINE_RE = re.compile(r"^\s{0,3}#{1,6}\s*NIEZWERYFIKOWANE-POZA-DIGESTEM", re.IGNORECASE)


def main():
    parser = argparse.ArgumentParser(
        description="Sprawdź mapowanie draftu na digest (`<!-- src: … -->`). "
        "ID itemu digestu: `D<n>` (kategoria) albo `N<n>` (## NIEZAKLASYFIKOWANE) — RÓWNOPRAWNE."
    )
    parser.add_argument("--work", required=True, help="katalog roboczy <work>")
    args = parser.parse_args()

    draft = os.path.join(args.work, "meeting-note-draft.md")
    try:
        with open(draft, encoding="utf-8") as handle:
            lines = handle.read().splitlines()
    except OSError as exc:
        print("BŁĄD: nie mogę odczytać %s (%s)" % (draft, exc), file=sys.stderr)
        return 2

    # `existing` = kwarantanna z poprzedniego przebiegu (skrypt jest uruchamiany DWA razy: Faza 2p
    # i przed Fazą 4b), `moved` = to, co ten przebieg właśnie przeniósł. Rozdzielone, bo bez tego
    # drugi przebieg dubluje nagłówek sekcji i liczy stare bloki jako nowe porażki.
    kept, moved, existing = [], [], []
    # Sekcja, w której aktualnie jesteśmy: "unclassified" | "quarantine" | "claim"
    section = "claim"
    stamps = {"unclassified": set(), "claim": set()}

    for line in lines:
        # ⚠️ KWARANTANNA JEST LEPKA — sprawdzana PRZED dispatchem po nagłówku.
        # WHY: skrypt dokleja kwarantannę na KONIEC pliku, więc jest sekcją terminalną. Gdy
        # dispatch szedł pierwszy, każdy NAGŁÓWEK leżący już w kwarantannie (np. przeniesiony
        # tam tytuł H1 draftu) przeklasyfikowywał sekcję na "claim" i był przenoszony PONOWNIE
        # w każdym przebiegu — plik rósł o linijkę za każdym uruchomieniem, a komenda odpala ten
        # preflight dwukrotnie (po Fazie 2 i przed Fazą 4b). Zweryfikowane 2026-08-10: 247→248 linii.
        if section == "quarantine":
            # Istniejąca kwarantanna nie jest ani twierdzeniem, ani wejściem do zapisu.
            # Sam jej nagłówek pomijamy — zostanie wypisany raz, niżej.
            if not QUARANTINE_RE.match(line):
                existing.append(line)
            continue

        if HEADING.match(line):
            if UNCLASSIFIED.match(line):
                section = "unclassified"
            elif QUARANTINE_RE.match(line):
                section = "quarantine"
            else:
                section = "claim"

        # Nagłówki-SCAFFOLDING (`## NIEZAKLASYFIKOWANE`, `## NIEZWERYFIKOWANE-POZA-DIGESTEM`) nie
        # opisują materiału, więc nie mają czego cytować. WHY wyjątek: bez niego skrypt wrzucał do
        # kwarantanny WŁASNE nagłówki sekcji, tracąc granicę sekcji — a wtedy przekrój timestampów
        # liczył się na pustym zbiorze i kolizja przechodziła niezauważona.
        scaffolding = bool(UNCLASSIFIED.match(line) or QUARANTINE_RE.match(line))
        structural = (HEADING.match(line) or BULLET.match(line)) and not scaffolding
        if structural and not SRC.search(line):
            moved.append(line)
            continue

        if section in stamps:
            # ⚠️ Kolizję liczymy po WYPOWIEDZI (timestamp + początek cytatu), nie po samym
            # timestampie. WHY (2026-08-11): `normalize-transcript.py` scala kolejne bloki tego
            # samego mówcy, więc JEDEN timestamp (np. `0:00`) pokrywa kilkuminutowy monolog,
            # który legalnie niesie i twierdzenie, i materiał niezaklasyfikowany. Porównanie po
            # timestampie dawało exit 2 na POPRAWNYM drafcie i blokowało Fazę 3.
            # Intencja reguły zostaje: TA SAMA wypowiedź nie może być jednocześnie w kwarantannie
            # i podstawą twierdzenia. Linia bez cytatu nie jest twierdzeniem o wypowiedzi.
            quoted = QUOTED.search(line)
            if quoted:
                head = re.sub(r"\s+", " ", quoted.group(1)).strip().lower()[:60]
                for stamp in TIMESTAMP.findall(line):
                    stamps[section].add((stamp, head))
        kept.append(line)

    collision = stamps["unclassified"] & stamps["claim"]

    if moved or existing:
        while kept and not kept[-1].strip():
            kept.pop()
        kept.extend(["", QUARANTINE, ""])
        kept.extend([line for line in existing if line.strip()])
        kept.extend(moved)

    payload = "\n".join(kept) + "\n"
    try:
        with open(draft, "w", encoding="utf-8") as handle:
            handle.write(payload)
    except OSError as exc:
        print("BŁĄD: nie mogę zapisać %s (%s)" % (draft, exc), file=sys.stderr)
        return 2

    print(
        "check-draft-src: linii %d, bez src: przeniesionych %d (w kwarantannie już było: %d), "
        "timestampów twierdzących %d, niezaklasyfikowanych %d, KOLIZJI %d"
        % (
            len(lines),
            len(moved),
            len([line for line in existing if line.strip()]),
            len(stamps["claim"]),
            len(stamps["unclassified"]),
            len(collision),
        )
    )

    if moved:
        print(
            "UWAGA: %d bloków bez `src:` → kwarantanna. Pozycje `## NIEZAKLASYFIKOWANE` też MUSZĄ "
            "nieść `<!-- src: N<n> -->` — `N<n>` jest równoprawne z `D<n>`; bez niego materiał "
            "niezaklasyfikowany wypada z notatki." % len(moved),
            file=sys.stderr,
        )

    if collision:
        print(
            "BŁĄD: timestampy jednocześnie w NIEZAKLASYFIKOWANE i w sekcji twierdzącej: %s"
            % ", ".join(sorted(collision)),
            file=sys.stderr,
        )
        return 2
    return 1 if moved else 0


if __name__ == "__main__":
    sys.exit(main())
