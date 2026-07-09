#!/usr/bin/env python3
"""brain-scan.py — read-only diagnostic scan of the Obsidian brain vault.

Feeds `/brain-sync` Phase 1 (inventory + deterministic diagnostics). READ-ONLY:
never writes, moves, or deletes anything. Vault root is read from
`claude-brain/config.json` → `vault.path`.

Usage:
  scripts/brain-scan.py                     # scan whole vault
  scripts/brain-scan.py --context scandit   # limit to one context's areas
  scripts/brain-scan.py --today 2026-07-07  # override "today" for stale check

Detects (deterministic — still needs human judgment before acting):
  broken [[wikilinks]] · empty/scaffold notes · relative dates in body ·
  stale `updated` (< file mtime) · orphan notes (0 incoming links) ·
  big files (>400 ln) · open-task counts.

NOTE on false positives (do NOT auto-fix blindly):
  - `[[slug]]`, `[[_<context>]]` in _system/templates → placeholders.
  - `[[SkillName]]` (e.g. so-pilot-launch) → refers to a repo skill, not a vault note.
  - `[[folder]]` (e.g. 00-Inbox) → folder link.
  - relative-date words inside knowledge-note PROSE are content, not undated refs.
  - checkbox lists inside mirrored dev-knowledge notes are content, not tasks.
"""
import os, re, sys, json, argparse, datetime, collections

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "..", "config.json")
SKIP_DIRS = {".git", ".obsidian", "04-Archive", "node_modules"}
SCAFFOLD_MARKERS = ["To jest serce notatki", "Treść gotowa", "TODO: wypełnij", "<!-- template", "Opisz tutaj"]
REL_DATE = re.compile(r"\b(dziś|dzisiaj|wczoraj|jutro|w zeszłym tygodniu|w tym tygodniu|za tydzień|ostatnio)\b", re.I)
BIG_LINES = 400
STALE_DAYS = 3


def load_cfg():
    d = json.load(open(CONFIG, encoding="utf-8"))
    vault = d["vault"]["path"]
    # context → set of vault sub-areas (project area + knowledge dir)
    areas = collections.defaultdict(set)
    for _, p in (d.get("paths") or {}).items():
        for ctx in ([p["context"]] + list((p.get("contexts") or {}).keys())):
            va = p.get("vault")
            if va:
                areas[ctx].add(va)
            for _, sub in (p.get("contexts") or {}).items():
                if sub.get("vault"):
                    areas[sub["context"] if "context" in sub else ctx].add(sub["vault"])
    kn = d.get("knowledge") or {}
    for ctx, k in kn.items():
        if k.get("dir"):
            areas[ctx].add(k["dir"])
    # inherited base pools (knowledge.<ctx>.inherits[]) belong to the inheriting context's scan
    # area too, else a leaf note's [[link]] up to a universal note false-flags as a broken link.
    for ctx, k in kn.items():
        for base in (k.get("inherits") or []):
            bdir = (kn.get(base) or {}).get("dir")
            if bdir:
                areas[ctx].add(bdir)
    return vault, {c: sorted(a) for c, a in areas.items()}


def fm(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return m.group(1) if m else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--context", help="limit scan to one context's vault areas")
    ap.add_argument("--today", help="YYYY-MM-DD override for stale check")
    ap.add_argument("--big-lines", type=int, default=BIG_LINES)
    args = ap.parse_args()

    vault, areas = load_cfg()
    today = datetime.date.fromisoformat(args.today) if args.today else datetime.date.today()
    prefixes = None
    if args.context:
        if args.context not in areas:
            sys.exit(f"unknown context '{args.context}'. known: {', '.join(sorted(areas))}")
        prefixes = [os.path.join(vault, a) for a in areas[args.context]]

    md = []
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if not f.endswith(".md"):
                continue
            fp = os.path.join(root, f)
            if prefixes and not any(fp.startswith(pre) for pre in prefixes):
                continue
            md.append(fp)

    rel = lambda p: os.path.relpath(p, vault)
    by_name = collections.defaultdict(list)
    for p in md:
        by_name[os.path.splitext(os.path.basename(p))[0]].append(p)

    incoming = collections.defaultdict(int)
    broken, scaffold, reldates, stale, big = [], [], [], [], []
    opentasks = collections.Counter()

    for p in md:
        try:
            text = open(p, encoding="utf-8").read()
        except Exception:
            continue
        f = fm(text)
        body = text[len(f) + 8:] if f else text
        for m in re.finditer(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]", text):
            tgt = m.group(1).strip()
            if tgt in by_name:
                for q in by_name[tgt]:
                    incoming[q] += 1
                incoming.setdefault(p, 0)
            else:
                broken.append((rel(p), tgt))
        if any(mk in text for mk in SCAFFOLD_MARKERS) or (len(body.strip()) < 80 and "type:" in f):
            scaffold.append(rel(p))
        if REL_DATE.search(body):
            reldates.append(rel(p))
        mu = re.search(r"updated:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", f)
        if mu:
            try:
                ud = datetime.date.fromisoformat(mu.group(1))
                mt = datetime.date.fromtimestamp(os.path.getmtime(p))
                if (mt - ud).days > STALE_DAYS:
                    stale.append((rel(p), mu.group(1), str(mt)))
            except Exception:
                pass
        n = len(re.findall(r"^\s*- \[ \]", body, re.M))
        if n:
            opentasks[rel(p)] = n
        lc = text.count("\n")
        if lc > args.big_lines:
            big.append((rel(p), lc))

    orphans = []
    for p in md:
        b = os.path.basename(p)
        if incoming.get(p, 0) == 0 and not b.startswith("_") and b != "Home.md" and "MOC" not in b:
            if "/knowledge/" in p or "/01-Projects/" in p:
                orphans.append(rel(p))

    def show(title, items, n=40):
        print(f"\n### {title} ({len(items)})")
        for it in items[:n]:
            print("  -", it)
        if len(items) > n:
            print(f"  … +{len(items)-n} more")

    scope = args.context or "ALL"
    print(f"brain-scan · context={scope} · today={today} · {len(md)} md files")
    show("BROKEN wikilinks (source → missing target)", [f"{s}  →  [[{t}]]" for s, t in broken])
    show("EMPTY/SCAFFOLD notes", scaffold)
    show("RELATIVE dates in body", reldates)
    show("STALE updated (updated < mtime by >%dd)" % STALE_DAYS, [f"{s} (updated {u}, mtime {m})" for s, u, m in stale], 30)
    show("ORPHAN notes (0 incoming links)", orphans, 40)
    show("BIG files (>%d lines)" % args.big_lines, [f"{s} ({n} ln)" for s, n in sorted(big, key=lambda x: -x[1])], 30)
    print(f"\n### Files with open tasks (top 20)")
    for p, n in opentasks.most_common(20):
        print(f"  - {p}: {n}")


if __name__ == "__main__":
    main()
