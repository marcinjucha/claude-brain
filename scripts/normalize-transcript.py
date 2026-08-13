#!/usr/bin/env python3
"""Normalizuj transkrypt Fathoma — usuń artefakty ASR/eksportu, NIC WIĘCEJ.

Skrypt robi DOKŁADNIE cztery rzeczy:
  1. usuwa boilerplate nagłówka/stopki Fathoma (linia VIEW RECORDING, separator `---`),
  2. scala kolejne bloki TEGO SAMEGO mówcy w jeden blok — etykieta mówcy verbatim,
     a KAŻDY timestamp zachowany jako marker `⟨mm:ss⟩` w miejscu zszycia,
  3. wyrzuca SĄSIADUJĄCE POWTÓRZONE SERIE ZDAŃ wewnątrz jednego bloku wypowiedzi
     (patrz `drop_adjacent_duplicate_runs` — to jest realny kształt artefaktu Fathoma),
  4. raportuje redukcję jedną linijką na stdout.

TIMESTAMPY SĄ ZACHOWANE, NIE USUWANE. WHY: Faza 3 komendy /brain-meeting cytuje materiał
w formacie `CYTAT (Fabian, ~55:00)` — bez timestampów agent nie ma czym się posłużyć, a
weryfikacja cytatu przez człowieka przestaje być możliwa. Pierwsza wersja tego skryptu je
kasowała i była sprzeczna z komendą, która ją wywołuje.

DLACZEGO SERIE, A NIE POJEDYNCZE ZDANIA: zweryfikowane na realnym transkrypcie
(sprint planning 2026-08-10) — Fathom powtarza BLOK 3–4 zdań, nie jedno zdanie. Sekwencja ma
kształt `[A B C D][A B C D']`, więc poprzednikiem A jest D, nie A: dedup sąsiadujących
POJEDYNCZYCH zdań strukturalnie nie ma jak tego złapać i na realnym materiale usuwał ZERO
duplikatów. Do tego powtórzenie bywa NIEDOKŁADNE („back mostly to you, Pratik. Let us know if
you need help" vs „back mostly on your part, Pratik. That does not actually need help"), więc
exact-match nie wystarcza — porównanie serii jest progowe (`--dup-threshold`).

NIE WOLNO — i dlaczego:
  - ciąć small talku — regex nie odróżni rozmowy o wakacjach od „od środy mnie nie ma"
    (ograniczenie capacity na sprint planningu); osąd należy do Fazy 2 komendy /brain-meeting.
  - dedupować NIE-sąsiadujących powtórzeń — to samo zdanie 20 minut później to NAWRÓT tematu,
    dokładnie sygnał, na którym stoi rozstrzyganie stanu końcowego (Krok A testu
    DECYZJA-vs-DELIBERACJA).
  - dedupować PRZEZ granicę mówcy — dwie osoby mówiące to samo to zgoda, nie artefakt.
  - usuwać krótkich wypowiedzi — „Yes"/„Ok" to odpowiedzi, czasem jedyny zapis zgody.
  - usuwać timestampów — patrz wyżej.
  - poprawiać atrybucji mówcy — nie ma jak wiedzieć; zgadywanie wyprałoby złego właściciela
    w transkrypt wyglądający pewnie. Błędy atrybucji łapie bramka `[do potwierdzenia]`.
  - przestawiać, przepisywać, parafrazować, streszczać — wyjście musi być tym samym zapisem,
    tylko bez artefaktów.
  - wyrzucać linii, której nie umie sklasyfikować — nieparsowalne linie przechodzą verbatim.

Kształt wejścia (realny eksport Fathoma):
    <tytuł spotkania>
    VIEW RECORDING - 63 mins (No highlights): https://fathom.video/share/...
    ---
    0:00 - Marcin Jucha
      Ok, so let's start.
      Sprint planning, right?
    0:12 - Fabian Mueller
      Yes.

Wyjście:
    <tytuł spotkania>

    [0:00] Marcin Jucha: Ok, so let's start. Sprint planning, right?

    [0:12] Fabian Mueller: Yes.

Exit codes: 0 ok · 1 redukcja > --max-reduction (zjadł treść, nie artefakty) · 2 błąd wejścia/IO.
"""

import argparse
import re
import sys
from difflib import SequenceMatcher

# Nagłówek bloku mówcy: `<timestamp> - <Speaker Name>`, NIEwcięty.
# WHY brak `\s*` na początku: Fathom wcina linie treści dwiema spacjami, a zdanie
# „  12:30 - and then we stopped" pasowało do wzorca i STAWAŁO SIĘ mówcą — czyli skrypt
# fabrykował atrybucję, czego docstring wprost zabrania. Nagłówek jest zawsze w kolumnie 0.
SPEAKER_BLOCK = re.compile(r"^(\d?\d:\d\d(?::\d\d)?)\s*-\s*(\S.*?)\s*$")
# Nazwa mówcy nie jest zdaniem. Dłuższy „mówca" = to była treść, przepuść verbatim.
MAX_SPEAKER_LEN = 60
# Cyfry nośne: liczby, godziny, daty, splity („70/30", „10:30", „122", „2026-08-10").
SALIENT_DIGITS = re.compile(r"\d+(?:[:/.\-]\d+)*")
# Poniżej tej długości seria porównuje się wyłącznie exact-match.
MIN_FUZZY_LEN = 40
# Minimum treści, przy którym bramka `--max-reduction` jest twarda (patrz `main`).
GUARD_MIN_CONTENT = 2000
# Boilerplate eksportu: linia VIEW RECORDING + separator `---`
VIEW_RECORDING = re.compile(r"^\s*VIEW RECORDING\b.*$", re.IGNORECASE)
SEPARATOR = re.compile(r"^\s*-{3,}\s*$")

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

# Górna granica długości porównywanej serii. Powyżej ~8 zdań „powtórzenie" to już
# nawrót tematu, nie artefakt eksportu.
MAX_RUN = 8


def norm_key(text):
    """Klucz porównania: spacje + wielkość liter. Treści NIE zmienia — tylko porównanie."""
    return re.sub(r"\s+", " ", text).strip().lower()


def split_sentences(text):
    return [p.strip() for p in SENTENCE_SPLIT.split(text) if p.strip()]


def _runs_match(sentences, i, k, threshold):
    """Czy seria [i:i+k] powtarza się natychmiast w [i+k:i+2k]?

    Wymóg jest PAROWY: zdanie n pierwszej serii musi pasować do zdania n drugiej serii.
    WHY: porównywanie zlepionego bloku („blob") jest za luźne przy długiej serii — na realnym
    materiale dopasowało ogólnie-podobny fragment i pochłonęło niepowiązany ogon, usuwając
    zdanie „There was a question around those security fixes." Wymóg parowy to wyklucza:
    artefakt eksportu powtarza zdania W TEJ SAMEJ KOLEJNOŚCI, więc parowanie jest darmowe,
    a przypadkowe podobieństwo całości przestaje wystarczać.
    """
    first = sentences[i : i + k]
    second = sentences[i + k : i + 2 * k]
    if len(first) != k or len(second) != k:
        return False

    for left, right in zip(first, second):
        a, b = norm_key(left), norm_key(right)
        if not a or not b:
            return False
        if a == b:
            continue
        if k == 1:
            # Jedno zdanie: wyłącznie dokładne dopasowanie. Progowe porównanie na jednym
            # krótkim zdaniu zlewałoby różne odpowiedzi („Yes." vs „Yeah.").
            return False
        # CYFRY MUSZĄ SIĘ ZGADZAĆ. WHY: powtórka eksportu odtwarza liczby identycznie, a
        # równoległa wyliczanka RÓŻNI SIĘ właśnie liczbą. Bez tego warunku zniknęło
        # „The split for the second launch is 80/20" po zdaniu o „70/30" — czyli dokładnie
        # ten rodzaj treści (splity, daty, numery release), po który istnieje ten pipeline.
        if set(SALIENT_DIGITS.findall(a)) != set(SALIENT_DIGITS.findall(b)):
            return False
        # Krótkie zdania: za mało materiału, żeby próg cokolwiek znaczył.
        if len(a) < MIN_FUZZY_LEN or len(b) < MIN_FUZZY_LEN:
            return False
        if SequenceMatcher(None, a, b).ratio() < threshold:
            return False
    return True


def drop_adjacent_duplicate_runs(sentences, threshold):
    """Usuń SĄSIADUJĄCE powtórzone SERIE zdań wewnątrz jednej wypowiedzi.

    Przy pozycji `i` szukamy najdłuższej serii `k`, której kopia stoi bezpośrednio po niej;
    zachowujemy pierwszą, wyrzucamy drugą. Od najdłuższej do najkrótszej, żeby powtórzony
    blok 4 zdań nie został rozłożony na cztery niezależne decyzje.

    Przebieg powtarzamy do stabilizacji — `[A][A][A]` wymaga dwóch przejść.
    """
    dropped_total = 0
    current = list(sentences)

    for _ in range(5):
        out, i, dropped, n = [], 0, 0, len(current)
        while i < n:
            matched_k = 0
            for k in range(min(MAX_RUN, (n - i) // 2), 0, -1):
                if _runs_match(current, i, k, threshold):
                    matched_k = k
                    break
            if matched_k:
                out.extend(current[i : i + matched_k])
                dropped += matched_k
                i += 2 * matched_k
            else:
                out.append(current[i])
                i += 1
        dropped_total += dropped
        current = out
        if dropped == 0:
            break

    return current, dropped_total


def normalize_fathom(lines, threshold):
    """Zwróć (linie_wyjscia, stats) — stats to dict z licznikami do raportu."""
    # blocks: [[speaker, [(timestamp, [linie treści]), ...]], ...]
    blocks = []
    passthrough_prefix = []
    seen_speaker = False
    merged = 0

    for raw in lines:
        line = raw.rstrip("\r\n")

        if SEPARATOR.match(line) or VIEW_RECORDING.match(line):
            continue

        match = SPEAKER_BLOCK.match(line)
        if match and len(match.group(2)) <= MAX_SPEAKER_LEN:
            timestamp, speaker = match.group(1), match.group(2)
            seen_speaker = True
            if blocks and blocks[-1][0] == speaker:
                merged += 1  # scalenie z poprzednim blokiem tego samego mówcy
                blocks[-1][1].append((timestamp, []))
            else:
                blocks.append([speaker, [(timestamp, [])]])
            continue

        if not line.strip():
            continue

        # Treść przechodzi VERBATIM — bez usuwania timestampów, bo „let's meet at 10:30"
        # to treść, nie artefakt.
        content = line.strip()

        if seen_speaker and blocks:
            blocks[-1][1][-1][1].append(content)
        else:
            # Tytuł spotkania i cokolwiek przed pierwszym mówcą — verbatim.
            passthrough_prefix.append(content)

    out, dropped_total = list(passthrough_prefix), 0
    if passthrough_prefix:
        out.append("")

    # Redukcja liczona na TREŚCI, nie na formatowaniu — patrz `main`.
    content_in = content_out = 0

    for speaker, segments in blocks:
        rendered = []
        for index, (timestamp, content_lines) in enumerate(segments):
            joined = " ".join(content_lines).strip()
            if not joined:
                continue
            # Dedup NA SEGMENT — nigdy przez granicę mówcy ani przez granicę timestampu.
            sentences = split_sentences(joined)
            content_in += sum(len(s) for s in sentences)
            kept, dropped = drop_adjacent_duplicate_runs(sentences, threshold)
            content_out += sum(len(s) for s in kept)
            dropped_total += dropped
            text = " ".join(kept)
            # Pierwszy segment: timestamp w nagłówku. Kolejne: marker w miejscu zszycia.
            # Pusty pierwszy segment nie może oddać swojego timestampu następnemu.
            rendered.append(text if not rendered else "⟨%s⟩ %s" % (timestamp, text))
            if not rendered[:-1]:
                head_timestamp = timestamp
        if not rendered:
            continue
        out.append("[%s] %s: %s" % (head_timestamp, speaker, " ".join(rendered)))
        out.append("")

    while out and out[-1] == "":
        out.pop()

    stats = {
        "dropped": dropped_total,
        "merged": merged,
        "speaker_blocks": len(blocks),
        "content_in": content_in,
        "content_out": content_out,
    }
    return out, stats


def main():
    parser = argparse.ArgumentParser(
        description="Normalizuj transkrypt Fathoma (usuń artefakty, nie treść)."
    )
    parser.add_argument("--in", dest="infile", required=True, help="ścieżka do transkryptu")
    parser.add_argument("--out", dest="outfile", required=True, help="ścieżka wyjściowa")
    parser.add_argument(
        "--format", default="fathom", choices=["fathom"], help="format wejścia (dziś tylko fathom)"
    )
    parser.add_argument(
        "--max-reduction",
        type=float,
        default=40.0,
        help="maksymalna dopuszczalna redukcja znaków w procentach (default 40)",
    )
    parser.add_argument(
        "--dup-threshold",
        type=float,
        default=0.93,
        help="próg podobieństwa serii zdań uznawanej za powtórzenie (default 0.93)",
    )
    args = parser.parse_args()

    try:
        with open(args.infile, "rb") as handle:
            blob = handle.read()
    except OSError as exc:
        print("BŁĄD: nie mogę odczytać %s (%s)" % (args.infile, exc), file=sys.stderr)
        return 2

    try:
        text = blob.decode("utf-8")
        mangled = 0
    except UnicodeDecodeError:
        # Podmiana znaków jest CICHĄ zmianą treści — raportuj ją, nie chowaj.
        text = blob.decode("utf-8", errors="replace")
        mangled = text.count("�")

    lines = text.splitlines(keepends=True)
    in_lines = len(lines)
    in_chars = sum(len(line) for line in lines)

    out_lines, stats = normalize_fathom(lines, args.dup_threshold)
    payload = "\n".join(out_lines) + "\n"
    out_chars = len(payload)

    # Redukcja mierzona na TREŚCI, nie na całym pliku. WHY: boilerplate, wcięcia i znaki
    # nowej linii to formatowanie — licząc je, krótki transkrypt „redukował się" o 40%+
    # i fałszywie wywalał bramkę, mimo że nie usunięto ani jednego zdania.
    if stats["content_in"] == 0:
        reduction = 0.0
    else:
        reduction = (1 - stats["content_out"] / stats["content_in"]) * 100

    print(
        "normalize-transcript: %d linii/%d znaków → %d linii/%d znaków "
        "(redukcja treści %.1f%%), bloki mówców: %d, scalone: %d, "
        "zdania z powtórzonych serii usunięte: %d%s"
        % (
            in_lines,
            in_chars,
            len(out_lines),
            out_chars,
            reduction,
            stats["speaker_blocks"],
            stats["merged"],
            stats["dropped"],
            (", ZNAKI PODMIENIONE (nie-UTF8): %d" % mangled) if mangled else "",
        )
    )

    # Bramka ma sens statystyczny tylko na materiale, w którym artefakt jest marginesem.
    # WHY GUARD_MIN_CONTENT: w krótkim wyimku jedna legalnie usunięta powtórka 4 zdań to
    # ponad 40% treści i bramka strzelałaby na POPRAWNYM przebiegu. Na realnym spotkaniu
    # artefakty to promile, więc próg nadal łapie systemowe zjadanie treści.
    if reduction > args.max_reduction and stats["content_in"] >= GUARD_MIN_CONTENT:
        print(
            "BŁĄD: redukcja treści %.1f%% > limit %.1f%% — skrypt zjadł treść, nie artefakty. "
            "Plik wyjściowy NIE został zapisany."
            % (reduction, args.max_reduction),
            file=sys.stderr,
        )
        return 1
    if reduction > args.max_reduction:
        print(
            "UWAGA: redukcja treści %.1f%% > limit %.1f%%, ale materiał ma tylko %d znaków "
            "(próg bramki: %d) — za mało, by uznać to za systemowe zjadanie treści. Sprawdź wyjście."
            % (reduction, args.max_reduction, stats["content_in"], GUARD_MIN_CONTENT),
            file=sys.stderr,
        )

    # Zapis DOPIERO po bramce — inaczej uszkodzone wyjście leży na dysku obok exit 1
    # i następny krok pipeline'u może je wziąć za dobre.
    try:
        with open(args.outfile, "w", encoding="utf-8") as handle:
            handle.write(payload)
    except OSError as exc:
        print("BŁĄD: nie mogę zapisać %s (%s)" % (args.outfile, exc), file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
