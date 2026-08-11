#!/usr/bin/env python3
"""procesy-scan.py — deterministyczna robota dla /improve-process.

Trzy tryby, wszystkie zwracają WYCINEK, nigdy całego pliku:

  --inventory <plik>            indeks kroków procesu (ID · KIEDY · licznik ❌)
  --dedup "<teza>" --ctx <ctx>  pięć powierzchni + JAWNY NEGATYW (gdzie szukano z zerem)
  --diff <źródło> <instancja>   kategorie rozjazdu + UNANCHORED

DLACZEGO SKRYPT, NIE AGENT: negatyw dedupu („nie znalazłem w tych pięciu miejscach")
jest wiarygodny tylko wtedy, gdy generuje go coś, co nie umie zapomnieć sprawdzić.
Model raportujący własną staranność jest nieodróżnialny od modelu, który pominął krok.

CISZA NIE JEST SUKCESEM: gdy plik nie ma ani jednej pozycji w rozpoznawanym formacie,
skrypt NIE drukuje zer — mówi NIE UMIEM ODCZYTAĆ i kończy kodem 3. Ten guard powstał,
bo count-budget.py drukował „SUMA 0 słów" na pliku o innym schemacie i wyglądało to
jak czysty przebieg.

Kody wyjścia: 0 OK · 1 błąd użycia/IO · 3 nie umiem odczytać.

FORMAT POZYCJI (kontrakt ze /improve-process):

    ### P-LAUNCH-03 · Zmierz realne tempo mowy twórcy
    - KIEDY: przed pierwszą mapą bloków
    - BLOKUJE: policzenie długości jakiegokolwiek skryptu
    - PRZESŁANKI: [ZMIERZONA] min. 5 evergreenów · [ZAŁOŻONA] kanał ma stałą normę
    - KOSZT: 10 minut
    - WYKONAWCA: AGENT
    - ❌ 2026-08-11 — planowaliśmy przy 135 wpm, pomiar dał 158
"""

import argparse
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

CONFIG = Path("/Users/marcinjucha/Prywatne/projects/claude-brain/config.json")

ITEM_RE = re.compile(r"^###\s+(P-[A-Z0-9]+-\d+)\s*·\s*(.+?)\s*$", re.M)
FIELD_RE = re.compile(r"^-\s+(KIEDY|BLOKUJE|PRZESŁANKI|KOSZT|WYKONAWCA)\s*:\s*(.+?)\s*$", re.M)
ANTI_RE = re.compile(r"^-\s+❌\s+(.+?)\s*$", re.M)
# pozycja instancji bez ID — checkbox albo nagłówek H3, w którym ID nie występuje
UNANCHORED_RE = re.compile(r"^(?:\s*-\s*\[[ xX]\]\s+|###\s+)(?!P-[A-Z0-9]+-\d+)(.+?)\s*$", re.M)
TICKED_RE = re.compile(r"^\s*-\s*\[[xX]\]\s+.*?(P-[A-Z0-9]+-\d+)", re.M)

# Przesłanki MIĘKKIE: krok na nich stojący nie może być odhaczony, tylko świadomie pominięty.
# „MOJE ODCZYTANIE" jest równie miękkie jak „ZAŁOŻONA" — dziś P-LAUNCH-03 i 06 stoją właśnie na nim
# i bez tej stałej nie były zgłaszane ani w inwentarzu, ani w kategorii 3 diffu.
SOFT = ("ZAŁOŻONA", "MOJE ODCZYTANIE")

STOP = {
    "przed", "przez", "który", "która", "które", "żeby", "jest", "jako", "tego", "tych",
    "tylko", "nasze", "naszej", "sobie", "wtedy", "kiedy", "zanim", "czego", "gdzie",
    "bardzo", "jeden", "jedna", "jedno", "wszystko", "jeśli", "albo", "oraz", "dla",
}


def load_config():
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        sys.exit(f"BŁĄD: nie umiem wczytać {CONFIG}: {exc}")


def fold(text: str) -> str:
    """Bezogonkowa forma do porównań — 'przesłanki' i 'przeslanki' mają się spotkać."""
    nfd = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn").replace("ł", "l")


def strip_fences(raw: str) -> str:
    """Wycina bloki ``` — przykład formatu w nagłówku pliku NIE jest odhaczeniem.
    Zmierzone 2026-08-11: świeża kopia szkieletu raportowała „1 odhaczonych", bo kontrakt
    odhaczania w nagłówku pokazuje wzorzec `- [x] P-LAUNCH-04 — DOWÓD: …` jako przykład."""
    out, fence = [], False
    for ln in raw.split("\n"):
        if ln.lstrip().startswith("```"):
            fence = not fence
            continue
        if not fence:
            out.append(ln)
    return "\n".join(out)


def parse_items(path: Path):
    """Zwraca [{id, tytul, pola{}, antywzorce[], linia}]. Puste = nie umiem odczytać."""
    if not path.exists():
        sys.exit(f"BŁĄD: brak pliku {path}")
    raw = path.read_text(encoding="utf-8")
    marks = list(ITEM_RE.finditer(raw))
    items = []
    for i, m in enumerate(marks):
        body = raw[m.end(): marks[i + 1].start() if i + 1 < len(marks) else len(raw)]
        items.append({
            "id": m.group(1),
            "tytul": m.group(2),
            "pola": dict(FIELD_RE.findall(body)),
            "antywzorce": ANTI_RE.findall(body),
            "linia": raw[: m.start()].count("\n") + 1,
        })
    return items, raw


def cmd_inventory(args):
    items, raw = parse_items(Path(args.inventory))
    if not items:
        h2 = re.findall(r"^##\s+(.+)$", raw, re.M)[:12]
        print(f"NIE UMIEM ODCZYTAĆ TEGO PLIKU: {args.inventory}")
        print("Powód: zero pozycji w formacie `### P-ETAP-nn · tytuł`.")
        print("To NIE znaczy, że proces jest pusty — znaczy, że parser nie rozpoznał struktury.")
        if h2:
            print("Nagłówki H2, które widzę: " + " · ".join(h2))
        sys.exit(3)

    print(f"{'ID':16}{'❌':>4}{'WYKON.':>9}  KROK / KIEDY")
    print("-" * 78)
    for it in items:
        kiedy = it["pola"].get("KIEDY", "—")
        wyk = it["pola"].get("WYKONAWCA", "?")[:8]
        prz = it["pola"].get("PRZESŁANKI", "?")
        print(f"{it['id']:16}{len(it['antywzorce']):>4}{wyk:>9}  {it['tytul']}")
        print(f"{'':29}  KIEDY:    {kiedy}")
        print(f"{'':29}  PRZESŁ.:  {prz[:120]}{'…' if len(prz) > 120 else ''}")
    zalozone = [i["id"] for i in items
                if any(s in i["pola"].get("PRZESŁANKI", "") for s in SOFT)]
    print("-" * 78)
    print(f"RAZEM {len(items)} kroków · {sum(len(i['antywzorce']) for i in items)} antywzorców")
    if zalozone:
        print("⚠️  kroki z przesłanką ZAŁOŻONĄ (nie wolno odhaczyć, tylko świadomie pominąć): "
              + ", ".join(zalozone))


def surfaces(cfg, ctx):
    """Pięć powierzchni dedupu. Zwraca [(etykieta, [ścieżki])]."""
    vault = Path(cfg["vault"]["path"])
    kn = cfg.get("knowledge", {})
    dirs = [kn.get(ctx, {}).get("dir")] + [
        kn.get(b, {}).get("dir") for b in kn.get(ctx, {}).get("inherits", [])
    ]
    know = [vault / d for d in dirs if d]

    skill_roots = [Path(c) for c in kn.get(ctx, {}).get("consumers", [])]
    skill_files = []
    for root in skill_roots:
        if root.exists():
            skill_files += sorted(root.glob("*/resources/*checklist*.md"))
            skill_files += sorted(root.glob("*/SKILL.md"))

    return [
        ("bufor sesyjny", [vault / "01-Projects" / ctx / "memory.md"]),
        ("wiedza + bazy dziedziczone", [f for d in know for f in sorted(d.glob("*.md"))]),
        ("checklisty i ciała skilli", skill_files),
        ("debrief operatora", [vault / "01-Projects" / ctx / "_operator-debrief.md"]),
        ("istniejące procesy", sorted((vault / "03-Resources" / ctx / "procesy").glob("*.md"))),
    ]


def resolve_origin(raw):
    """Origin przychodzi jako ścieżka albo 'ścieżka:linia' — obsłuż OBA.
    Bez tego wykluczenie nie działa i kandydat wychodzi jako duplikat samego siebie."""
    if not raw:
        return None
    cand = raw
    if ":" in raw:
        head, tail = raw.rsplit(":", 1)
        if tail.isdigit():
            cand = head
    try:
        return Path(cand).resolve()
    except Exception:  # noqa: BLE001
        return Path(cand)


def cmd_dedup(args):
    cfg = load_config()
    origin = resolve_origin(args.exclude_origin)
    keys = sorted({fold(w) for w in re.findall(r"\w{5,}", args.dedup, re.U)} - STOP)
    if len(keys) < 2:
        sys.exit("BŁĄD: teza za krótka — podaj zdanie, nie hasło (potrzebuję ≥2 słów treściowych)")
    # PRÓG GĘSTOŚCI, nie stała: przy tezie z 8 słów treściowych „2 trafione" łapie każdą
    # linię o twórcy i skrypcie. Zmierzone 2026-08-11: próg 2 dał 12 trafień, z czego
    # jedno prawdziwe. Połowa słów tezy w jednej linii to już nie zbieg okoliczności.
    # CEIL, nie round: round(2.5) w Pythonie daje 2 (bankierskie zaokrąglenie), więc teza
    # pięciosłowna spadała do progu 2 i sypała szumem — zmierzone 29 trafień, z czego jedno realne.
    need = min(4, max(2, math.ceil(len(keys) * 0.6)))
    CAP = 10

    print(f"TEZA: {args.dedup}")
    print(f"SŁOWA KLUCZOWE ({len(keys)}): {', '.join(keys)}")
    print(f"PRÓG: ≥{need} różnych słów w jednej linii\n")

    hits, nieczytelne, wylaczone = [], [], set()
    for etykieta, paths in surfaces(cfg, args.ctx):
        for p in paths:
            if origin and (p.resolve() == origin or p.name == origin.name):
                wylaczone.add(f"{etykieta}: {p.name} (origin kandydata)")
                continue
            try:
                lines = p.read_text(encoding="utf-8").split("\n")
            except Exception:  # noqa: BLE001
                nieczytelne.append(str(p))
                continue
            for n, line in enumerate(lines, 1):
                f = fold(line)
                score = sum(1 for k in keys if k in f)
                if score >= need:
                    hits.append((score, etykieta, p, n, lines))

    # DRUGI PRZEBIEG, AKAPITOWY — BEZWARUNKOWY, nie „tylko gdy liniowy dał zero".
    # WHY: duplikat rozłożony na dwie linie jest dla dopasowania liniowego niewidzialny. Zmierzone
    # 2026-08-11 na regule dopisanej tego dnia do trzech skilli: przebieg liniowy zwracał 1 trafienie
    # i twierdził, że „checklisty i ciała skilli (26 plików)" są PUSTE — a przebieg akapitowy znajdował
    # tam 7 trafień. Negatyw był fałszywy dokładnie tam, gdzie cały mechanizm anty-puchnięcia na nim stoi.
    for etykieta, paths in surfaces(cfg, args.ctx):
        for p in paths:
            if origin and (p.resolve() == origin or p.name == origin.name):
                continue
            try:
                raw = p.read_text(encoding="utf-8")
            except Exception:  # noqa: BLE001
                continue
            off = 1
            for para in raw.split("\n\n"):
                score = sum(1 for k in keys if k in fold(para))
                if score >= need and len(para.strip()) > 40:
                    hits.append((score, etykieta + " [akapit]", p, off, None))
                off += para.count("\n") + 2

    # dedup po (plik, linia) — akapit i linia potrafią wskazać to samo miejsce
    widziane, unikalne = set(), []
    for h in sorted(hits, key=lambda h: -h[0]):
        klucz = (str(h[2]), h[3])
        if klucz in widziane:
            continue
        widziane.add(klucz)
        unikalne.append(h)
    hits = unikalne

    for score, etykieta, p, n, lines in hits[:CAP]:
        print(f"● {etykieta}  [{score}/{len(keys)} słów]")
        if lines is None:
            print(f"  {p}:~{n}\n")
        else:
            print(f"  {p}:{n}")
            for c in range(max(0, n - 2), min(len(lines), n + 1)):
                print(f"  {'>' if c == n - 1 else ' '} {lines[c].strip()[:150]}")
            print()

    # NEGATYW LICZONY RAZ, NA KOŃCU: wszystkie powierzchnie minus te z jakimkolwiek trafieniem.
    # Inkrementalne budowanie w pętli liniowej było źródłem kłamstwa — powierzchnia z trafieniem
    # akapitowym zostawała na liście „przeszukane z zerem".
    trafione = {e.replace(" [akapit]", "") for _, e, _, _, _ in hits}
    # Powierzchnia WYKLUCZONA (origin kandydata) nie może trafić na listę „przeszukane z zerem" —
    # nie została przeszukana, tylko pominięta. Ta sama klasa kłamstwa co negatyw liczony w pętli.
    wykluczone_etykiety = {w.split(":")[0] for w in wylaczone}
    wszystkie = [(e, len(ps)) for e, ps in surfaces(cfg, args.ctx)]
    def _pl(n):
        return "brak plików" if not n else (f"{n} plik" if n == 1 else f"{n} plików")
    puste = [f"{e} ({_pl(n)})" for e, n in wszystkie
             if e not in trafione and e not in wykluczone_etykiety]

    print("-" * 78)
    print(f"TRAFIENIA: {len(hits)}" + (f" (pokazane {CAP} najgęstszych)" if len(hits) > CAP else ""))
    print("PRZESZUKANE Z ZEREM TRAFIEŃ LEKSYKALNYCH")
    print("(dopasowanie po SŁOWACH, nie po znaczeniu — parafraza tu nie trafi):")
    for e in puste:
        print(f"  · {e}")
    if wylaczone:
        print("WYŁĄCZONE z przeszukania (origin kandydata) — negatyw ICH NIE OBEJMUJE:")
        for e in sorted(wylaczone):
            print(f"  · {e}")
    if nieczytelne:
        print("⚠️  NIEPRZESZUKANE (błąd odczytu) — negatyw ICH NIE OBEJMUJE:")
        for x in nieczytelne:
            print(f"  · {x}")
        sys.exit(3)


def cmd_diff(args):
    src_items, _ = parse_items(Path(args.diff[0]))
    if not src_items:
        sys.exit(f"NIE UMIEM ODCZYTAĆ ŹRÓDŁA: {args.diff[0]} (zero pozycji `### P-…`) — kod 3")
    inst_path = Path(args.diff[1])
    if not inst_path.exists():
        print(f"INSTANCJA NIE ISTNIEJE: {inst_path}")
        print("To NIE jest błąd — faza rozjazdu jest nieblokująca. Zgłoś jako SKIPPED.")
        return
    inst_raw = strip_fences(inst_path.read_text(encoding="utf-8"))
    inst_items, _ = parse_items(inst_path)

    src_ids = {i["id"] for i in src_items}
    # ID w instancji to NIE tylko nagłówki `### P-…`: kopia bywa odhaczana checkboxami
    # `- [x] P-LAUNCH-01 — DOWÓD: …` i wtedy parse_items widzi zero pozycji, a kategoria 1
    # ogłasza wszystkie kroki jako brakujące, choć kategoria 3 w tym samym wyjściu mówi,
    # że są odhaczone. Zmierzone 2026-08-11 na instancji z trzema odhaczeniami.
    inst_ids = {i["id"] for i in inst_items} | set(re.findall(r"P-[A-Z0-9]+-\d+", inst_raw))
    ticked = set(TICKED_RE.findall(inst_raw))

    unanchored_all = [x.strip() for x in UNANCHORED_RE.findall(inst_raw)
                      if len(x.strip()) > 12
                      and not x.strip().startswith(("KIEDY", "BLOKUJE", "PRZESŁANKI", "KOSZT", "WYKONAWCA"))]

    if not inst_ids:
        # CISZA NIE JEST SUKCESEM: bez ani jednego ID kategoria 1 byłaby fałszywa
        # („instancja w tyle o wszystko"), a to jest bliźniak buga „SUMA 0 słów".
        print(f"NIE UMIEM ODCZYTAĆ INSTANCJI: {inst_path}")
        print("Powód: zero pozycji `### P-…` i zero odhaczeń z ID kroku.")
        print("Kategoria 1 byłaby fałszywa, więc jej NIE drukuję. Poniżej tylko UNANCHORED.")
        print(f"\nUNANCHORED ({len(unanchored_all)}):")
        for x in unanchored_all[:25]:
            print(f"  ? {x[:140]}")
        if len(unanchored_all) > 25:
            print(f"  … i {len(unanchored_all) - 25} dalszych")
        sys.exit(3)

    print(f"ŹRÓDŁO: {args.diff[0]}  ({len(src_items)} kroków)")
    print(f"INSTANCJA: {inst_path}  ({len(inst_ids)} pozycji z ID, {len(ticked)} odhaczonych)\n")

    print("1. W ŹRÓDLE, BRAK W INSTANCJI — instancja jest w tyle:")
    for i in sorted(src_ids - inst_ids) or ["  (brak)"]:
        print(f"  · {i}" if i.startswith("P-") else i)

    print("\n2. W INSTANCJI, BRAK W ŹRÓDLE — kandydaci na PROMUJ albo PUNKT DECYZYJNY:")
    for i in sorted(inst_ids - src_ids) or ["  (brak)"]:
        print(f"  · {i}" if i.startswith("P-") else i)

    print("\n3. ODHACZONE, A STOJĄ NA MIĘKKIEJ PRZESŁANCE — odhaczenie bez pokrycia:")
    zal = [i["id"] for i in src_items
           if i["id"] in ticked
           and any(s in i["pola"].get("PRZESŁANKI", "") for s in SOFT)]
    for i in zal or ["  (brak)"]:
        print(f"  · {i}" if i.startswith("P-") else i)

    unanchored = [x for x in unanchored_all
                  if not re.search(r"P-[A-Z0-9]+-\d+", x)]
    print(f"\n4. UNANCHORED — pozycje instancji BEZ ID ({len(unanchored)}):")
    print("   Te linie są dla diffu niewidzialne. „Brak rozjazdu\" ich NIE obejmuje —")
    print("   trzeba je przeczytać semantycznie albo zakotwiczyć ID.")
    for t in unanchored[:25]:
        print(f"  ? {t[:140]}")
    if len(unanchored) > 25:
        print(f"  … i {len(unanchored) - 25} dalszych")


def main():
    ap = argparse.ArgumentParser(description="Deterministyczna robota dla /improve-process")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--inventory", metavar="PLIK", help="indeks kroków procesu")
    g.add_argument("--dedup", metavar="TEZA", help="pięć powierzchni + jawny negatyw")
    g.add_argument("--diff", nargs=2, metavar=("ŹRÓDŁO", "INSTANCJA"), help="kategorie rozjazdu")
    ap.add_argument("--ctx", help="kontekst brain (wymagany przy --dedup)")
    ap.add_argument("--exclude-origin", metavar="PLIK",
                    help="pomiń ten plik w dedupie — origin kandydata, inaczej odrzuci sam siebie")
    a = ap.parse_args()

    if a.inventory:
        cmd_inventory(a)
    elif a.dedup:
        if not a.ctx:
            ap.error("--dedup wymaga --ctx")
        cmd_dedup(a)
    else:
        cmd_diff(a)


if __name__ == "__main__":
    main()
