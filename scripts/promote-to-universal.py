#!/usr/bin/env python3
"""
promote-to-universal.py — deterministically MOVE knowledge notes from a context into a base
(universal) pool it `inherits`, so they become cross-context craft shared without duplication.

This is the MECHANICAL half of a migration (move files + rewrite `context:` + move MOC bullets +
a hard directional-rule SAFETY GUARD). The JUDGMENT half — deciding WHICH slugs are universal and
resolving any boundary link — stays with the operator/agent (do it BEFORE running; the guard refuses
an unsafe set). After this, run `sync-knowledge.py --all --used-by` to regen snapshots + used-by.

Safety design (why it's safe to re-run migrations with this):
- REFUSES if any moving note `[[links]]` DOWN to a note that would STAY behind (that link would become
  a base→leaf directional violation → commit block). You must fix such a link (judgment) first.
- REFUSES if the base is not actually `inherits`-ed by the source context (the move would hide the note).
- `--check` = dry-run: validates + prints the exact plan, writes nothing.
- Moves are `git mv` when the file is tracked (history preserved), else plain mv; MOC bullets are
  carried verbatim (descriptions never lost), removed from source MOC and appended to the base MOC.

Usage:
  promote-to-universal.py --from shadow-operator --to general-business --slugs a,b,c --check
  promote-to-universal.py --from shadow-operator --to general-business --slugs a,b,c        # execute
"""
import argparse, json, os, re, glob, subprocess, sys

CONFIG = "/Users/marcinjucha/Prywatne/projects/claude-brain/config.json"
WIKILINK_RE = re.compile(r'\[\[([a-z0-9][a-z0-9-]*)\]\]')
EXTERNAL_LINKS = {"knowledge-system"}          # kept in sync with sync-knowledge.py
FM_CONTEXT_RE = re.compile(r'(?m)^(context:\s*).*$')

def die(msg): sys.stderr.write("promote-to-universal: " + msg + "\n"); sys.exit(2)

def load_cfg(path):
    with open(path, encoding="utf-8") as f: return json.load(f)

def ctx_dir(cfg, ctx):
    kn = cfg["knowledge"]
    if ctx not in kn: die(f"unknown context: {ctx}")
    return os.path.join(cfg["vault"]["path"], kn[ctx]["dir"])

def slugs_in(d):
    return {os.path.basename(p)[:-3] for p in glob.glob(os.path.join(d, "*.md"))
            if not os.path.basename(p).startswith("_")}

def is_tracked(path):
    r = subprocess.run(["git", "-C", os.path.dirname(path), "ls-files", "--error-unmatch",
                        os.path.basename(path)], capture_output=True)
    return r.returncode == 0

def moc_bullets(moc_path, slugs):
    """Return {slug: [full bullet lines that wikilink it]} and the remaining MOC text without them."""
    if not os.path.exists(moc_path): return {}, None
    lines = open(moc_path, encoding="utf-8").read().splitlines(keepends=True)
    carried, kept = {}, []
    for ln in lines:
        m = WIKILINK_RE.search(ln)
        if m and m.group(1) in slugs and re.match(r'\s*[-*]\s', ln):
            carried.setdefault(m.group(1), []).append(ln)
        else:
            kept.append(ln)
    return carried, "".join(kept)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", required=True)
    ap.add_argument("--to", dest="base", required=True)
    ap.add_argument("--slugs", required=True, help="comma-separated slugs to promote")
    ap.add_argument("--check", action="store_true", help="dry-run: validate + print plan, write nothing")
    ap.add_argument("--config", default=CONFIG)
    args = ap.parse_args()
    cfg = load_cfg(args.config)
    moving = [s.strip() for s in args.slugs.split(",") if s.strip()]
    if not moving: die("no slugs")

    src_d, base_d = ctx_dir(cfg, args.src), ctx_dir(cfg, args.base)
    # GUARD 1: base must be inherited by src, else the moved note would vanish from src's view
    if args.base not in (cfg["knowledge"][args.src].get("inherits") or []):
        die(f"'{args.src}' does not inherit '{args.base}' (add inherits first, else the move hides the notes)")

    src_slugs, base_slugs = slugs_in(src_d), slugs_in(base_d)
    problems = []
    for s in moving:
        if s not in src_slugs: problems.append(f"'{s}' not found in {args.src}")
        if s in base_slugs:    problems.append(f"'{s}' already exists in {args.base}")
    # GUARD 2 (directional rule): every outlink of a moving note must resolve WITHIN the new pool
    # (another moving note, a note already in the base, or an EXTERNAL link). A link to a note that
    # STAYS in the source = a would-be base→leaf violation → refuse; fix that link (judgment) first.
    allowed = set(moving) | base_slugs | EXTERNAL_LINKS
    for s in moving:
        p = os.path.join(src_d, s + ".md")
        if not os.path.isfile(p): continue
        for tgt in sorted(set(WIKILINK_RE.findall(open(p, encoding="utf-8").read()))):
            if tgt not in allowed:
                where = "stays in " + args.src if tgt in src_slugs else "unknown/other context"
                problems.append(f"DIRECTIONAL: {s} → [[{tgt}]] ({where}) — fix this link before promoting")
    if problems:
        sys.stderr.write("REFUSED — resolve first:\n" + "\n".join("  ✗ " + x for x in problems) + "\n")
        sys.exit(2)

    # plan is safe — build the actions
    src_moc, base_moc = os.path.join(src_d, "_MOC.md"), os.path.join(base_d, "_MOC.md")
    carried, src_moc_new = moc_bullets(src_moc, set(moving))
    verb = "WOULD" if args.check else "will"
    print(f"[promote] {len(moving)} notes: {args.src} → {args.base}  ({verb})")
    for s in moving:
        print(f"  · move {s}.md  + rewrite context: {args.src} → {args.base}"
              + ("  + carry MOC bullet" if s in carried else "  (no MOC bullet)"))
    print(f"  · source _MOC: remove {sum(len(v) for v in carried.values())} bullet(s); base _MOC: append them")
    if args.check:
        missing_moc = [s for s in moving if s not in carried]
        if missing_moc: print(f"  note: no source-MOC bullet for {missing_moc} (add to base _MOC by hand)")
        print("[check] safe. Re-run without --check, then: sync-knowledge.py --all --used-by")
        return

    for s in moving:
        src_p, dst_p = os.path.join(src_d, s + ".md"), os.path.join(base_d, s + ".md")
        txt = open(src_p, encoding="utf-8").read()
        new = FM_CONTEXT_RE.sub(r"\1" + args.base, txt, count=1)
        if is_tracked(src_p):
            subprocess.run(["git", "-C", src_d, "mv", os.path.basename(src_p),
                            os.path.relpath(dst_p, src_d)], check=True)
        else:
            os.rename(src_p, dst_p)
        with open(dst_p, "w", encoding="utf-8") as f: f.write(new)
    # rewrite source MOC (bullets removed) + append carried bullets to base MOC
    if src_moc_new is not None:
        with open(src_moc, "w", encoding="utf-8") as f: f.write(src_moc_new)
    if carried:
        with open(base_moc, "a", encoding="utf-8") as f:
            f.write("\n## Zmigrowane (do re-sekcji)\n" + "".join(b for v in carried.values() for b in v))
    print(f"[promote] done. Now run: sync-knowledge.py --all --used-by   (then --check must be exit 0)")

if __name__ == "__main__":
    main()
