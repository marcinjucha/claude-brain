#!/usr/bin/env python3
"""sync-procesy.py — LUSTRO checklist procesu: mózg → snapshot w skillu.

    --context <ctx>   zsynchronizuj procesy jednego kontekstu
    --all             wszystkie konteksty z config.json
    --check           READ-ONLY: pokaż dryf, nic nie zapisuj (exit 1, gdy dryf jest)

KIERUNEK JEST JEDNOKIERUNKOWY: źródło żyje w `03-Resources/<ctx>/procesy/<etap>.md`, skill
dostaje KOPIĘ z nagłówkiem „DO NOT EDIT". Bliźniak `sync-knowledge.py`, ale dla drugiej
kategorii wiedzy — wykonywalnej (wiersz „proces wykonywalny" w `_system/knowledge-system.md`).

PO CO TO ISTNIEJE: w `launch-tworcy.md` pięć z ośmiu kroków ma `WYKONAWCA: AGENT`, a agent
nigdy nie zobaczy pliku w vaulcie — skille są lazy i czytają wyłącznie własne `resources/`.
Bez lustra połowa procesu obowiązywałaby tylko człowieka, wbrew kryterium podziału półek.

CEL BIERZE SIĘ Z POLA `snapshot-do:` W FRONTMATTERZE ŹRÓDŁA, nie z konwencji nazw. Wartość jest
relatywna do katalogu `skills/` konsumenta (`config.json` → `knowledge[<ctx>].consumers`); prefiks
do `skills/` włącznie jest obcinany, więc oba zapisy działają:
    snapshot-do: "so-launch-sequence/resources/launch-checklist.md"
    snapshot-do: "claude-marketing/skills/so-launch-sequence/resources/launch-checklist.md"
Brak pola → plik jest świadomie tylko dla człowieka; skrypt raportuje `pomijam` i nie zgaduje celu.

LUSTRO JEST TĘPE. Kopiuje treść i dokłada nagłówek. Zero transformacji — każda transformacja
to miejsce, w którym lustro zacznie kłamać, a wtedy skill i vault mówią co innego o tym samym kroku.
Dwa wyjątki, oba ODEJMUJĄCE (nigdy nie dopisujemy treści, której nie ma w źródle):
  · sekcja `## Instancje` — to stan per twórca, czyli warstwa volatile; w skillu byłaby martwa
  · ścieżki podawane są jako VAULT-RELATYWNE, nigdy absolutne — absolutna ścieżka iCloud nie
    istnieje na VPS-ie ani w Coworku, a to jest cały powód, dla którego snapshoty w ogóle są

Kody wyjścia: 0 OK · 1 błąd użycia/IO albo (przy --check) wykryty dryf.
"""

import argparse
import json
import re
import sys
from pathlib import Path

CONFIG = Path("/Users/marcinjucha/Prywatne/projects/claude-brain/config.json")

FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)
SNAP_RE = re.compile(r"^snapshot-do:\s*\"?([^\"\n]+)\"?\s*$", re.M)
UPDATED_RE = re.compile(r"^updated:\s*(\S+)\s*$", re.M)
ETAP_RE = re.compile(r"^etap:\s*\"?([^\"\n]+)\"?\s*$", re.M)
# sekcja wycinana z lustra: stan per twórca nie ma czego robić w skillu
DROP_SECTIONS = ("## Instancje",)

HEADER = (
    "<!-- GENERATED from brain {src} — DO NOT EDIT HERE; edit the brain process file.\n"
    "     Regenerate: claude-brain/scripts/sync-procesy.py --context {ctx}\n"
    "     Source updated: {updated} · etap: {etap} -->\n"
)


def load_config():
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        sys.exit(f"BŁĄD: nie umiem wczytać {CONFIG}: {exc}")


def strip_sections(body: str) -> str:
    """Usuwa sekcje z DROP_SECTIONS wraz z treścią do następnego nagłówka H2."""
    out, skip = [], False
    for ln in body.split("\n"):
        if ln.startswith("## "):
            skip = any(ln.startswith(s) for s in DROP_SECTIONS)
        if not skip:
            out.append(ln)
    return "\n".join(out).rstrip() + "\n"


def build_snapshot(src_path: Path, vault: Path, ctx: str) -> tuple[str, str] | None:
    """Zwraca (relatywny cel, treść snapshotu) albo None, gdy plik nie deklaruje celu."""
    raw = src_path.read_text(encoding="utf-8")
    fm = FM_RE.search(raw)
    meta = fm.group(1) if fm else ""
    m = SNAP_RE.search(meta)
    if not m:
        return None
    target = m.group(1).strip()
    if "skills/" in target:                      # obetnij prefiks repo
        target = target.split("skills/", 1)[1]
    updated = (UPDATED_RE.search(meta) or [None, "?"])[1]
    etap = (ETAP_RE.search(meta) or [None, "?"])[1]
    src_rel = src_path.relative_to(vault).as_posix()

    head = HEADER.format(src=src_rel, ctx=ctx, updated=updated, etap=etap)
    return target, head + strip_sections(raw)


def sync_ctx(cfg, ctx: str, check: bool) -> tuple[int, int, int]:
    vault = Path(cfg["vault"]["path"])
    src_dir = vault / "03-Resources" / ctx / "procesy"
    if not src_dir.exists():
        print(f"[{ctx}] brak katalogu procesy/ — nic do zrobienia")
        return 0, 0, 0

    consumers = [Path(c) for c in cfg.get("knowledge", {}).get(ctx, {}).get("consumers", [])]
    zrodla = sorted(p for p in src_dir.glob("*.md") if not p.name.startswith("_"))
    if not zrodla:
        print(f"[{ctx}] katalog procesy/ jest pusty")
        return 0, 0, 0

    zmienione = zgodne = pominiete = 0
    for src in zrodla:
        zbudowane = build_snapshot(src, vault, ctx)
        if zbudowane is None:
            print(f"  · pomijam: {src.name} — brak pola `snapshot-do:` (proces tylko dla człowieka)")
            pominiete += 1
            continue
        target_rel, tresc = zbudowane
        if not consumers:
            print(f"  ⚠️  {src.name} deklaruje `snapshot-do: {target_rel}`, ale kontekst "
                  f"{ctx} nie ma konsumentów w config.json — snapshot NALEŻNY, nie ma gdzie go położyć")
            pominiete += 1
            continue
        for skills_dir in consumers:
            dst = skills_dir / target_rel
            stare = dst.read_text(encoding="utf-8") if dst.exists() else None
            if stare == tresc:
                print(f"  ok:    {dst}")
                zgodne += 1
                continue
            zmienione += 1
            etykieta = "DRYF" if check else "regen"
            print(f"  {etykieta}:{' ' if check else '  '}{dst}"
                  + ("" if dst.exists() else "   (nowy plik)"))
            if not check:
                if not dst.parent.exists():
                    print(f"         ⚠️  brak katalogu {dst.parent} — skill nie istnieje albo "
                          f"nie ma resources/; NIE tworzę go w ciemno")
                    zmienione -= 1
                    pominiete += 1
                    continue
                dst.write_text(tresc, encoding="utf-8")
    return zmienione, zgodne, pominiete


def main():
    ap = argparse.ArgumentParser(description="Lustro checklist procesu: mózg → skill")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--context", metavar="CTX")
    g.add_argument("--all", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="READ-ONLY: pokaż dryf, nic nie zapisuj (exit 1, gdy dryf jest)")
    a = ap.parse_args()

    cfg = load_config()
    konteksty = list(cfg.get("knowledge", {})) if a.all else [a.context]

    suma_zmian = 0
    for ctx in konteksty:
        print(f"[{ctx}]")
        z, ok, pom = sync_ctx(cfg, ctx, a.check)
        suma_zmian += z
        print(f"  → {z} do zapisu · {ok} zgodnych · {pom} pominiętych\n")

    if a.check and suma_zmian:
        print(f"DRYF: {suma_zmian} snapshot(ów) nieaktualnych. "
              f"Uruchom bez --check, żeby wyrównać.")
        sys.exit(1)
    if not a.check and suma_zmian:
        print(f"ZAPISANE: {suma_zmian} snapshot(ów).")


if __name__ == "__main__":
    main()
