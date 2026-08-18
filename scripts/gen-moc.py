#!/usr/bin/env python3
"""Regeneruje blok `moc:auto` w `<vault>/01-Projects/<ctx>/_MOC.md`.

Kontrakt formatu: `<vault>/_system/templates/moc-block.md` — TEN plik go NIE definiuje, tylko
implementuje. Zmiana formatu idzie NAJPIERW do SPEC-u.

⭐ KLUCZOWA DECYZJA PROJEKTOWA: blok auto NIE wypisuje wszystkich notatek.
Pierwsza wersja wypisywala jeden wiersz na notatke — 111 wierszy dla shadow-operatora. Tabela na 111
wierszy w pliku, ktorego sensem jest "nie czytaj wszystkiego", przeczy sama sobie i lamie regule 2
ze SPEC-u ("kazdy poziom pokazuje tylko szczyt nizszego"). Blok auto pokazuje wiec:
  (a) jeden wiersz na FOLDER — folderow jest kilka i tyle zostanie, wiec rosnie subliniowo,
  (b) WYLACZNIE pozycje wymagajace uwagi: dryf frontmattera i sieroty.
Pelna enumeracja nalezy do huba podmiotu i do systemu plikow, nie tutaj.

Skip: `_archiwum` (zliczane recznie), `resources` (proweniencja), `_inbox` (kolejka) — ze SPEC-u.
Dodatkowe foldery MATERIALU (nie notatek) deklaruje SAM plik `_MOC.md` we frontmatterze:
    moc_skip: [dna, GW, google doc]
WHY tam, a nie w argumencie komendy: lista jest per kontekst, a plik, ktory opisuje wlasna topografie,
jest jedynym miejscem, gdzie nie zdryfuje od tego, co opisuje.

Exit: 0 ok · 1 brak `_MOC.md` (normalny stan) · 2 blad IO/argumentow (np. zla sciezka --vault)
· 3 plik JEST, ale WYPADLY znaczniki moc:auto — to AWARIA, nie normalny stan, i wymaga uwagi.
"""
import re, sys, argparse, datetime, subprocess
from pathlib import Path

BEGIN, END = "<!-- moc:auto", "<!-- /moc:auto -->"


def content_date(repo, rel, fallback):
    """Data ostatniej MODYFIKACJI TRESCI — bez przenosin i bez zmian samego `updated:`.

    WHY nie `mtime` (2026-08-18): rusza sie przy KAZDYM dotknieciu (`git mv`, sync iCloud, poprawka
    frontmattera), nie przy zmianie tresci. Detektor na `mtime` dal 66 pozycji, z czego 38 bylo
    artefaktem commita `scandit -> scandit-shelfview: przemianowanie kontekstu` — git zapisal pliki
    jako dodane pod nowa sciezka, tresc sie nie zmienila, a `updated:` z czerwca bylo POPRAWNE.

    WHY commit ruszajacy TYLKO `updated:` jest POMIJANY: bez tego detektor zjada wlasny ogon —
    poprawiasz 76 frontmatterow, commitujesz, i przy nastepnym przebiegu wszystkie 76 wracaja z luka
    do dnia poprawki. Podbicie samej daty NIE JEST aktualizacja notatki.

    ⭐ WHY brak commitu modyfikacji zwraca None, a NIE `mtime`: to trzecia odsłona tej samej pętli.
    Pliki dodane commitem przenoszacym kontekst (`A`, nie `M`) nie maja ZADNEJ historii modyfikacji,
    wiec detektor spadal na `mtime` — a moj wlasny zapis poprawiajacy frontmatter przesuwal `mtime`
    na dzis i flaga wracala. Brak commitu `M` znaczy BRAK DOWODU na zmiane tresci, a bez dowodu
    nie flagujemy: `mtime` juz raz udawal ten dowod i dal 38 falszywych pozycji.
    """
    try:
        out = subprocess.run(
            ["git", "log", "--diff-filter=M", "--follow", "-8", "--format=%H %ad", "--date=short",
             "--", rel], cwd=repo, capture_output=True, text=True, timeout=25).stdout.strip()
        for line in out.splitlines():
            sha, _, day = line.partition(" ")
            patch = subprocess.run(["git", "show", "--format=", "--unified=0", sha, "--", rel],
                                   cwd=repo, capture_output=True, text=True, timeout=25).stdout
            body = [l for l in patch.splitlines()
                    if l[:1] in "+-" and not l.startswith(("+++", "---"))]
            if body and all(re.match(r"^[+-]updated:", l) for l in body):
                continue
            return day
        return None          # brak commitu `M` = brak dowodu na zmiane tresci
    except Exception:
        return None


SKIP_ALWAYS = {"_archiwum", "resources", "_inbox"}


def fm_field(text, name, trim=True):
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    fm = text[: end if end != -1 else 400]
    m = re.search(rf"^{name}:\s*(.+?)\s*$", fm, re.M)
    if not m:
        return ""
    v = m.group(1).split(" #")[0].strip()          # frontmatter niesie tu komentarze inline
    if not trim:                                   # pola STERUJACE (moc_skip, moc_orphans) nigdy
        return v                                   # nie moga byc obcinane — cichy powrot bledu
    return v[:38] + "…" if len(v) > 38 else v      # dluga wartosc rozwala tabele markdown


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--context", required=True)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    # TOLERANCYJNE rozwiazanie sciezki: `--vault` moze byc KORZENIEM vaulta albo FOLDEREM KONTEKSTU.
    # WHY: w konwencji komend brain-* `<vault>` znaczy `01-Projects/<ctx>`, a nie korzen — pierwsza
    # wersja tego skryptu przyjmowala korzen i doklejala prefiks, wiec wywolanie z brain-update
    # (2026-08-18) dawalo `.../01-Projects/shadow-operator/01-Projects/shadow-operator` i exit 2.
    # Krok 2 Fazy 3.5 byl przez to MARTWY od chwili wpiecia. Przyjmujemy oba warianty, zeby ta klasa
    # bledu nie wrocila przy nastepnym konsumencie.
    cand = [Path(a.vault) / "01-Projects" / a.context, Path(a.vault)]
    root = next((c for c in cand if (c / "_MOC.md").is_file() or c.is_dir() and c.name == a.context), None)
    if root is None:
        print("BLAD: nie znalazlem folderu kontekstu. Sprawdzone: "
              + " · ".join(str(c) for c in cand), file=sys.stderr)
        return 2
    moc = root / "_MOC.md"
    if not moc.is_file():
        print(f"BRAK `_MOC.md` w {root} — zalozenie topografii to decyzja czlowieka."); return 1

    src = moc.read_text(encoding="utf-8")
    extra = fm_field(src, "moc_skip", trim=False)
    list_orphans = fm_field(src, "moc_orphans", trim=False).strip().lower() == "list"
    skip = set(SKIP_ALWAYS)
    if extra:
        skip |= {x.strip().strip("'\"") for x in extra.strip("[]").split(",") if x.strip()}

    # ⚠️ `_MOC.md` JEST WYKLUCZONY z korpusu liczenia linkow — inaczej detektor karmi sam siebie:
    # wygenerowany blok wypisuje `[[notatke]]`, ktora flaguje, wiec przy NASTEPNYM przebiegu ta
    # notatka nie jest juz sierota. Realny przebieg (agency, 2026-08-18): pierwszy raz 27 sierot,
    # blok zapisal 30 wierszy z wikilinkami, drugi przebieg policzyl 0. Licznik cicho zerowal sie
    # do zera i wygladalo to jak posprzatany kontekst.
    corpus = {p: p.read_text(encoding="utf-8", errors="replace")
              for p in root.rglob("*.md") if p.name != "_MOC.md"}
    notes = [p for p in corpus
             if not skip & set(p.relative_to(root).parts)
             and p.name not in ("_MOC.md", "CLAUDE.md", "README.md")]

    per_folder, flagged, drift_mtimes = {}, [], []
    for p in sorted(notes, key=lambda x: (str(x.parent.relative_to(root)), x.name)):
        where = str(p.parent.relative_to(root)) or "."
        d = per_folder.setdefault(where, {"n": 0, "drift": 0, "orph": 0})
        d["n"] += 1
        txt = corpus[p]
        updated = fm_field(txt, "updated")[:10]
        status = fm_field(txt, "status") or "—"
        links = sum(1 for q, t in corpus.items() if q != p and re.search(r"\[\[" + re.escape(p.stem) + r"(\||#|\]\])", t))
        mtime = datetime.date.fromtimestamp(p.stat().st_mtime).isoformat()
        touched = content_date(root, str(p.relative_to(root)), mtime)
        nohist = touched is None
        why, gap = [], 0
        if touched and re.match(r"\d{4}-\d{2}-\d{2}", updated or "") and touched > updated:
            gap = (datetime.date.fromisoformat(touched) - datetime.date.fromisoformat(updated)).days
            d["drift"] += 1
            drift_mtimes.append(touched)
            why.append(f"tresc zmieniona {touched}, `updated:` mowi {updated} (**{gap} dni**)")
        if links == 0:
            d["orph"] += 1
            if list_orphans:                      # sieroctwo jest sygnalem TYLKO tam, gdzie
                why.append("zero linkow z innych notatek")   # linkowanie krzyzowe jest konwencja
        if why:
            flagged.append((gap, f"| [[{p.stem}]] | `{where}` | {status} | {' · '.join(why)} |"))

    tot = sum(d["n"] for d in per_folder.values())
    tdr = sum(d["drift"] for d in per_folder.values())
    tor = sum(d["orph"] for d in per_folder.values())

    out = [f"{BEGIN} — generowany przez brain-update wg _system/templates/moc-block.md; nie edytuj recznie -->",
           f"### Topografia — stan {datetime.date.today().isoformat()}", "",
           "| folder | notatek | frontmatter klamie | sierot |", "|---|---|---|---|"]
    for w, d in sorted(per_folder.items()):
        out.append(f"| `{w}` | {d['n']} | {d['drift'] or '—'} | {d['orph'] or '—'} |")
    orph_note = ("Sieroty sa WYPISANE z nazwy (`moc_orphans: list`)." if list_orphans else
                 "Sieroty sa tylko ZLICZONE — w tym kontekscie notatka-lisc bez linkow jest NORMA, "
                 "nie sygnalem. Wlacz wypisywanie flaga `moc_orphans: list` we frontmatterze.")
    out += ["", f"**Razem {tot} notatek · {tdr} z klamiacym frontmatterem · {tor} sierot.** "
                + ("Pomijane foldery: `_archiwum` `resources` `_inbox` + `moc_skip` z frontmattera. "
                   if extra else "Pomijane foldery: `_archiwum` `resources` `_inbox` (ten kontekst nie "
                                 "deklaruje `moc_skip`). ") + orph_note, ""]
    bulk = ""
    if drift_mtimes:
        from collections import Counter
        day, cnt = Counter(drift_mtimes).most_common(1)[0]
        if cnt >= 3 and cnt / len(drift_mtimes) >= 0.3:
            bulk = (f"\n⚠️ **{cnt} z {len(drift_mtimes)} tych plikow ma TE SAMA date modyfikacji "
                    f"({day})** — to sygnal JEDNEJ operacji zbiorczej (przenoszenie, reformat, resync "
                    f"iCloud), nie {len(drift_mtimes)} osobnych zaniedban. Licz to jako JEDEN dlug "
                    f"do przejrzenia, nie jako {len(drift_mtimes)}.\n")
    if flagged:
        out += [f"#### Do oceny ({len(flagged)}) — jedyne pozycje wypisane z nazwy", "",
                "| notatka | gdzie | status | co jest nie tak |", "|---|---|---|---|",
                *[r for _, r in sorted(flagged, key=lambda x: -x[0])], "",
                "Osad nalezy do `/brain-update`, nie do tego bloku. `updated:` starszy od pliku znaczy, "
                "ze ktos edytowal tresc i nie podbil daty — a wtedy kazda decyzja oparta na tej dacie "
                "stoi na klamstwie. Sierota moze byc martwa albo tylko niezalinkowana; to rozne rzeczy. "
                "⚠️ Data brana z GITA (ostatnia modyfikacja tresci, bez przenosin) — nie z `mtime`, ktory rusza sie przy kazdym dotknieciu pliku. "
                "wiec wiersze sa sortowane MALEJACO po luce — realny dryf jest na gorze." + bulk, ""]
    else:
        out += ["Zero pozycji do oceny.", ""]
    out.append(END)
    block = "\n".join(out)

    i, j = src.find(BEGIN), src.find(END)
    if i == -1 or j == -1:
        # exit 3, NIE 1: brak PLIKU to normalny stan kontekstu bez topografii, ale plik BEZ znacznikow
        # znaczy, ze ktos je skasowal — wtedy blok nigdy sie nie zregeneruje i nikt sie nie dowie.
        print(f"AWARIA: `{moc.name}` istnieje, ale WYPADLY znaczniki moc:auto — blok nie zregeneruje sie "
              f"nigdy, dopoki ich nie przywrocisz.", file=sys.stderr)
        return 3
    print(f"gen-moc [{a.context}]: notatek {tot} · dryf {tdr} · sierot {tor} · do oceny {len(flagged)}"
          + (" (--check)" if a.check else ""))
    if not a.check:
        moc.write_text(src[:i] + block + src[j + len(END):], encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
