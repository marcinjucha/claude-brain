#!/usr/bin/env python3
"""Zweryfikuj MECHANICZNIE, że każdy cytat z digestu/draftu stoi w transkrypcie. ZERO OSĄDU.

Wejście: `<work>/digest.md` + `<work>/meeting-note-draft.md` + znormalizowany transkrypt.
Wyjście: `<work>/quotes.tsv` — `cytat<TAB>mówca<TAB>timestamp<TAB>zweryfikowany`.

Skrypt robi DOKŁADNIE cztery rzeczy:
  1. wyciąga cytaty w TRZECH nazwanych kształtach (i tylko w nich), dopasowując WIELOLINIJKOWO:
     `Mówca [m:ss]: „treść"` (atrybuowany) · `źródło: CYTAT: „treść" [m:ss]` (źródło osi zakresu) ·
     `CYTAT [m:ss]: „treść"` (bez etykiety mówcy). Dwukropek po `[m:ss]` jest opcjonalny,
  2. rozbija cytat na segmenty po `…` i dopasowuje KAŻDY SEGMENT OSOBNO jako podciąg,
  3. wymaga trafienia w OKNIE ±90 s od podanego timestampu ORAZ zgodnej ETYKIETY MÓWCY,
  4. zapisuje TSV i raportuje jedną linijką na stdout.

DLACZEGO PER SEGMENT, A NIE CAŁOŚĆ: cytat z wielokropkiem („A … B") to legalny SPLICE dwóch
fragmentów jednej wypowiedzi — dopasowanie całości odrzucałoby go zawsze, czyli skrypt stałby się
fabryką pytań do człowieka. Segment po segmencie sprawdza dokładnie to, co cytat twierdzi:
że każdy jego kawałek padł verbatim.

DLACZEGO OKNO ±90 s: timestamp digestu bierze się z nagłówka bloku albo z markera zszycia `⟨m:ss⟩`,
więc cytat z końca długiego, scalonego bloku legalnie leży kilkadziesiąt sekund po nagłówku.
Bez okna weryfikacja byłaby albo bezużytecznie luźna (cały plik), albo fałszywie surowa (exact).

DLACZEGO ETYKIETA MÓWCY JEST WARUNKIEM: cytat przypisany złej osobie jest FAŁSZYWY, nawet gdy
zdanie w transkrypcie istnieje — a atrybucja jest tym, po co w /brain-meeting istnieje prefiks
`[do potwierdzenia]`. Skrypt NIE poprawia atrybucji (nie ma jak wiedzieć), tylko sprawdza zgodność.

NIE WOLNO — i dlaczego:
  - oceniać, czy cytat jest ISTOTNY / czy dobrze podpiera tezę — to osąd Fazy 2/3, nie regexa,
  - poprawiać cytatu do brzmienia z transkryptu — poprawiony cytat wygląda jak zweryfikowany,
    a jest przepisany; porażka musi zostać porażką,
  - dopasowywać całości cytatu ze splice'em — patrz wyżej,
  - podnosić exit 2 na samą PORAŻKĘ dopasowania: porażki blokują wysoką półkę na poziomie
    komendy (E6) i idą do raportu, a exit 2 rezerwujemy dla „nie da się w ogóle zweryfikować"
    (brak plików, brak transkryptu, zero cytatów do sprawdzenia).

Exit codes: 0 = wszystkie cytaty zweryfikowane · 1 = ≥1 cytat NIEzweryfikowany (patrz quotes.tsv)
            · 2 = błąd wejścia/IO albo brak czegokolwiek do weryfikacji.
"""

import argparse
import os
import re
import sys

# Cytat: „…” (polskie), “…” (typograficzne) albo "…" (ASCII). Mieszanki są normalne — digest
# pisze agent, nie edytor z jedną konwencją; odrzucenie cytatu za DOMKNIĘCIE innym znakiem produkowałoby
# fałszywe eskalacje E6, czyli dokładnie tę fabrykę pytań, której ten skrypt ma zapobiegać.
QUOTE = re.compile("[\u201e\u201c\"]([^\u201e\u201d\u201c\"\\n]{3,})[\u201d\u201c\"]")

# ⚠️ Wyłuskujemy WYŁĄCZNIE dwa kształty, nie „każdy cudzysłów w pliku".
# WHY (zweryfikowane na realnym digeście 2026-08-10 sprint kickoff catchup): naiwne
# `QUOTE.finditer` po każdej linii dało 451 „cytatów", z czego 199 odrzuconych — i niemal
# wszystkie odrzucenia były błędami EKSTRAKCJI, nie digestu: przy dwóch cytatach w jednej linii
# regex mówcy brał DRUGI CYTAT za etykietę mówcy (`mówca = „the routes are on the update flow`),
# a polska proza z pól `ODCZYTANIE:`/`hedge:` („microchart", „WARUNKOWO, brak właściciela warunku")
# leciała jako cytat bez timestampu. Taki szum czyni E6 bezwartościowym i blokuje wysoką półkę
# masowo bez powodu — dokładnie „fabryka pytań", której projekt komendy zabrania.
#
# ⚠️ DOPASOWANIE JEST WIELOLINIJKOWE — pliki czytamy CAŁE, nie linia po linii.
# WHY (zweryfikowane 2026-08-11 mobile sync): digest łamie długie cytaty na dwie linie
# („…to avoid this\n  discrepancy on the two screens"), a wariant linia-po-linii POMIJAŁ je
# W MILCZENIU: 35 linii `CYTAT` w digeście → 10 wyciągniętych cytatów. Cytat NIGDY NIE SPRAWDZONY
# wygląda w raporcie identycznie jak zweryfikowany — to gorsza awaria niż fałszywe odrzucenie,
# bo znika bez śladu. Dlatego `[^…]` zamieniono na `[\s\S]` z limitem długości, a białe znaki
# (w tym nowe linie) normalizuje `norm()` przed dopasowaniem.
# Dwukropek po `[m:ss]` jest OPCJONALNY — digest pisze i `Mówca [0:00]: „…"`, i `Mówca [0:00] „…"`.
#
# (a) cytat ATRYBUOWANY: `Mówca [m:ss]: „treść"` — mówca i timestamp PRZED cytatem.
ATTRIBUTED = re.compile(
    r"(?P<speaker>[A-Z\u0141\u015a\u017b\u00d3\u0106\u0118][\w.\u00c0-\u017f()@'\- ]{1,45}?)"
    r"\s*\[(?P<ts>\d?\d:\d\d(?::\d\d)?)\]\s*:?\s*"
    "[\u201e\u201c\"](?P<q>[\\s\\S]{3,600}?)[\u201d\u201c\"]"
)
# (b) cytat-ŹRÓDŁO osi zakresu: `źródło: CYTAT: „treść" [m:ss]` — bez mówcy, timestamp PO cytacie.
#     Mówca None ⇒ `verify` pomija sprawdzenie etykiety (sam tekst + okno czasowe nadal obowiązują).
# (c) cytat BEZ ETYKIETY MÓWCY: `CYTAT [m:ss]: „treść"` — digest czasem pomija nazwę.
#     WHY: bez tego kształtu taki cytat NIE BYŁ WYCIĄGANY WCALE (cicha luka — gorsza od odrzucenia,
#     bo nie widać jej w raporcie). Zweryfikowane 2026-08-11: dwa cytaty niewidzialne do momentu,
#     gdy agent dopisał etykietę ręcznie. Mówca None ⇒ `verify` sprawdza tekst + okno, nie etykietę.
BARE_QUOTE = re.compile(
    r"CYTAT\s*\[(?P<ts>\d?\d:\d\d(?::\d\d)?)\]\s*:?\s*"
    "[\u201e\u201c\"](?P<q>[\\s\\S]{3,600}?)[\u201d\u201c\"]"
)
SCOPE_SOURCE = re.compile(
    r"CYTAT:\s*[\u201e\u201c\"](?P<q>[\\s\\S]{3,600}?)[\u201d\u201c\"]"
    r"\s*\[(?P<ts>\d?\d:\d\d(?::\d\d)?)\]"
)
# Timestamp w tekście: [m:ss], [h:mm:ss], ⟨m:ss⟩ albo goły m:ss.
TIMESTAMP = re.compile(r"[\[\u27e8]?(\d?\d:\d\d(?::\d\d)?)[\]\u27e9]?")
# Linia znormalizowanego transkryptu: `[m:ss] Mówca: treść`
TRANSCRIPT_LINE = re.compile(r"^\[(\d?\d:\d\d(?::\d\d)?)\]\s*([^:]{1,60}):\s*(.*)$")
# Marker zszycia wewnątrz bloku.
SPLICE = re.compile(r"\u27e8(\d?\d:\d\d(?::\d\d)?)\u27e9")
# Okno tolerancji dopasowania timestampu, w sekundach.
WINDOW_SECONDS = 90


def to_seconds(stamp):
    parts = [int(p) for p in stamp.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def norm(text):
    """Klucz porównania: białe znaki + wielkość liter. Treści NIE zmienia."""
    return re.sub(r"\s+", " ", text).strip().lower()


def load_transcript(path):
    """Zwróć listę (sekundy, mówca, znormalizowana treść) — jeden wpis per segment."""
    segments = []
    with open(path, encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            match = TRANSCRIPT_LINE.match(raw.rstrip("\r\n"))
            if not match:
                continue
            head, speaker, body = match.group(1), match.group(2).strip(), match.group(3)
            # Każdy marker zszycia zaczyna nowy segment z własnym timestampem.
            cursor, stamp = 0, head
            for splice in SPLICE.finditer(body):
                segments.append((to_seconds(stamp), speaker, norm(body[cursor : splice.start()])))
                stamp, cursor = splice.group(1), splice.end()
            segments.append((to_seconds(stamp), speaker, norm(body[cursor:])))
    return segments


def extract_quotes(path):
    """Zwróć listę (cytat, mówca_lub_None, timestamp_lub_None, plik, nr_linii)."""
    found = []
    if not os.path.exists(path):
        return found
    with open(path, encoding="utf-8", errors="replace") as handle:
        blob = handle.read()

    def line_of(offset):
        """Numer linii, w której zaczyna się dopasowanie — do kolumny `źródło` w TSV."""
        return blob.count("\n", 0, offset) + 1

    for match in ATTRIBUTED.finditer(blob):
        found.append(
            (
                match.group("q").strip(),
                match.group("speaker").strip(" *_`\n"),
                match.group("ts"),
                os.path.basename(path),
                line_of(match.start()),
            )
        )
    for match in BARE_QUOTE.finditer(blob):
        found.append(
            (
                match.group("q").strip(),
                None,
                match.group("ts"),
                os.path.basename(path),
                line_of(match.start()),
            )
        )
    for match in SCOPE_SOURCE.finditer(blob):
        found.append(
            (
                match.group("q").strip(),
                None,
                match.group("ts"),
                os.path.basename(path),
                line_of(match.start()),
            )
        )
    return found



# Mapa aliasów wypełniana z `--alias`. WHY: digest pisze etykiety SKRÓCONE („MJ") i ODMIENIONE
# („Fabiana"), a transkrypt niesie pełne („Marcin Jucha (markos734@gmail.com)"). Bez tej mapy
# co drugi poprawny cytat odpadał na „etykieta mówcy nie zgadza się" — czyli skrypt karał digest
# za konwencję nazewniczą, nie za nieprawdę.
ALIASES = {}


def speaker_matches(key, label):
    """Dopasowanie po PREFIKSIE tokenów (min 4 znaki) — znosi polską odmianę nazwisk."""
    if key in label or label in key:
        return True
    ktokens = [t for t in re.findall(r"[\w\u00c0-\u017f]+", key) if len(t) >= 4]
    ltokens = [t for t in re.findall(r"[\w\u00c0-\u017f]+", label) if len(t) >= 4]
    for kt in ktokens:
        for lt in ltokens:
            if kt.startswith(lt[:4]) and lt.startswith(kt[:4]):
                return True
    return False

def verify(quote, speaker, stamp, segments):
    """Czy KAŻDY segment cytatu stoi w oknie ±WINDOW_SECONDS u tego mówcy?"""
    pieces = [norm(p).strip(" .,;:!?-\u2014()") for p in re.split(r"\s*(?:\u2026|\.\.\.)\s*", quote)]
    # ⚠️ Nawiasy TEŻ obcinamy: digest pisze elizję jako „(…)", więc bez tego każdy segment
    # kończył się nadmiarowym „(" i nie był podciągiem — 24 z 29 odrzuceń w przebiegu
    # 2026-08-11 to był TEN defekt skryptu, nie nieprawda w cytacie.
    # ⚠️ NAWIASY KWADRATOWE NIE są obcinane — świadomie. Marker `[nazwa niepewna]` /
    # `[do potwierdzenia]` postawiony WEWNĄTRZ cudzysłowu MA oblewać test, bo taki cytat nie jest
    # dosłowny. Obcinanie `[]` czyniło markery tolerowanymi na brzegu segmentu i kasowało
    # jedyny mechaniczny sygnał, że marker trafił w złe miejsce.
    pieces = [p for p in pieces if len(p) >= 3]
    if not pieces:
        return False, "cytat pusty po normalizacji"
    if stamp is None:
        return False, "brak timestampu"

    target = to_seconds(stamp)
    window = [
        (seconds, who, body)
        for seconds, who, body in segments
        if abs(seconds - target) <= WINDOW_SECONDS
    ]
    if not window:
        return False, "brak segmentu w oknie +/-%ds" % WINDOW_SECONDS

    if speaker:
        key = norm(ALIASES.get(speaker.strip(), speaker))
        matching = [seg for seg in window if speaker_matches(key, norm(seg[1]))]
        if not matching:
            return False, "etykieta mówcy nie zgadza się w oknie"
        window = matching

    haystack = " ".join(body for _, _, body in window)
    for piece in pieces:
        if piece not in haystack:
            return False, "segment nie znaleziony: %s" % piece[:40]
    return True, "ok"


def main():
    parser = argparse.ArgumentParser(description="Weryfikuj cytaty digestu wobec transkryptu.")
    parser.add_argument("--work", required=True, help="katalog roboczy <work>")
    parser.add_argument("--transcript", required=True, help="znormalizowany transkrypt")
    parser.add_argument(
        "--alias",
        action="append",
        default=[],
        metavar="SKROT=Pelna Nazwa",
        help="alias etykiety mówcy, np. --alias 'MJ=Marcin Jucha' (można podać wielokrotnie)",
    )
    args = parser.parse_args()
    for pair in args.alias:
        if "=" in pair:
            short, full = pair.split("=", 1)
            ALIASES[short.strip()] = full.strip()

    try:
        segments = load_transcript(args.transcript)
    except OSError as exc:
        print("BŁĄD: nie mogę odczytać %s (%s)" % (args.transcript, exc), file=sys.stderr)
        return 2
    if not segments:
        print(
            "BŁĄD: %s nie ma linii w formacie `[m:ss] Mówca:` — nie ma czego weryfikować."
            % args.transcript,
            file=sys.stderr,
        )
        return 2

    quotes = []
    for name in ("digest.md", "meeting-note-draft.md"):
        quotes.extend(extract_quotes(os.path.join(args.work, name)))
    if not quotes:
        print("BŁĄD: nie znalazłem ANI JEDNEGO cytatu w digest.md/meeting-note-draft.md.", file=sys.stderr)
        return 2

    rows, failed = [], 0
    for quote, speaker, stamp, source, number in quotes:
        ok, reason = verify(quote, speaker, stamp, segments)
        if not ok:
            failed += 1
        rows.append(
            (
                # ⚠️ Cytat może być WIELOLINIJKOWY (digest łamie długie cytaty) — do TSV wchodzi
                # ze zwiniętymi białymi znakami, inaczej nowa linia rozwala wiersz i `quotes.tsv`
                # przestaje być parsowalny (zweryfikowane 2026-08-11: 62 wiersze-śmieci).
                re.sub(r"\s+", " ", quote.replace("\t", " ")).strip(),
                re.sub(r"\s+", " ", speaker).strip() if speaker else "—",
                stamp or "—",
                "tak" if ok else "NIE",
                reason,
                "%s:%d" % (source, number),
            )
        )

    out = os.path.join(args.work, "quotes.tsv")
    try:
        with open(out, "w", encoding="utf-8") as handle:
            handle.write("cytat\tmówca\ttimestamp\tzweryfikowany\tpowód\tźródło\n")
            for row in rows:
                handle.write("\t".join(row) + "\n")
    except OSError as exc:
        print("BŁĄD: nie mogę zapisać %s (%s)" % (out, exc), file=sys.stderr)
        return 2

    print(
        "verify-quotes: cytatów %d, zweryfikowanych %d, ODRZUCONYCH %d, segmentów transkryptu %d → %s"
        % (len(rows), len(rows) - failed, failed, len(segments), out)
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
