#!/usr/bin/env python3
"""
sync-knowledge.py — Brain knowledge → skill references snapshot + integrity checks.

The brain vault (03-Resources/<ctx>/knowledge/) is the SOURCE OF TRUTH for domain knowledge.
Consuming skills stay thin and declare what they need via `@references/knowledge/<slug>.md`
pointers (+ a `## Knowledge` block). This script snapshots those notes into each skill's
`references/knowledge/` (one-way, generated copy), auto-derives `used-by`, and runs integrity
checks. Config-driven and multi-context (shadow-operator / agency / scandit / …).

See: <vault>/_system/knowledge-system.md for the contract.

Usage:
  sync-knowledge.py --context shadow-operator     # snapshot + integrity (writes references)
  sync-knowledge.py --all                         # every active context
  sync-knowledge.py --context X --check           # dry-run; exit 1 if drift, exit 2 if dangling
  sync-knowledge.py --context X --used-by         # also rewrite vault notes' used-by (writes VAULT)
  sync-knowledge.py --context X --quiet           # print one summary line only if something changed

Exit codes: 0 ok · 1 drift (only in --check) · 2 dangling reference (hard error).
"""
import argparse, json, os, re, sys, glob

CONFIG = "/Users/marcinjucha/Prywatne/projects/claude-brain/config.json"
GEN_HEADER = ("<!-- GENERATED from brain {src} — DO NOT EDIT HERE; edit the brain note. "
              "Regenerate: claude-brain/scripts/sync-knowledge.py -->\n")
SLUG_PTR_RE   = re.compile(r'references/knowledge/([a-z0-9][a-z0-9-]*)\.md')
SLUG_TOKEN_RE = re.compile(r'[a-z0-9][a-z0-9-]+')
WIKILINK_RE   = re.compile(r'\[\[([a-z0-9][a-z0-9-]*)\]\]')
FM_FIELD_RE = lambda f: re.compile(r'(?m)^' + re.escape(f) + r':\s*(.*)$')
# wikilink targets that legitimately live outside knowledge/ (don't flag as dangling):
EXTERNAL_LINKS = {"knowledge-system"}

def die(msg, code=2):
    sys.stderr.write("sync-knowledge: " + msg + "\n"); sys.exit(code)

def load_config():
    with open(CONFIG, encoding="utf-8") as f:
        return json.load(f)

def vault_path(cfg):
    p = cfg.get("vault", {}).get("path")
    if not p: die("no vault.path in config")
    return p

def contexts(cfg, args):
    kn = cfg.get("knowledge", {})
    if not kn: die("no 'knowledge' block in config", 1)
    if args.all:
        return [c for c, v in kn.items() if v.get("active")]
    if not args.context: die("pass --context <name> or --all", 1)
    if args.context not in kn: die("unknown context: " + args.context, 1)
    return [args.context]

def source_notes(cfg, ctx):
    """{slug: abspath} for the brain knowledge notes of a context (excludes _MOC / _*.md)."""
    d = os.path.join(vault_path(cfg), cfg["knowledge"][ctx]["dir"])
    out = {}
    if not os.path.isdir(d):
        return out, d
    for path in glob.glob(os.path.join(d, "*.md")):
        base = os.path.basename(path)
        if base.startswith("_"):
            continue
        out[base[:-3]] = path
    return out, d

def find_skills(consumer_dirs):
    """SKILL.md paths under each consumer dir that contain a `## Knowledge` block.
    Dedup by realpath so a symlink-shared skill (e.g. agency legal-mind/doc-forge) is processed once."""
    skills, seen = [], set()
    for cdir in consumer_dirs:
        for sk in glob.glob(os.path.join(cdir, "*", "SKILL.md")):
            real = os.path.realpath(sk)
            if real in seen:
                continue
            seen.add(real)
            try:
                with open(sk, encoding="utf-8") as f:
                    txt = f.read()
            except OSError:
                continue
            if "## Knowledge" in txt:
                skills.append((sk, txt))
    return skills

def skill_deps(txt, known_slugs):
    """Slugs a skill depends on: all @references/knowledge/<slug>.md pointers, plus EVERY
    note-slug token on bullet lines inside the `## Knowledge` section (filtered by known_slugs,
    so prose words can't false-match AND multi-slug bullets like `- a + b — …` are fully caught,
    not just the first token)."""
    deps = set(SLUG_PTR_RE.findall(txt))
    m = re.search(r'(?ms)^##\s+Knowledge\b.*?(?=^##\s|\Z)', txt)
    if m:
        for line in m.group(0).splitlines():
            if re.match(r'\s*[-*]\s+', line):
                for tok in SLUG_TOKEN_RE.findall(line):
                    if tok in known_slugs:
                        deps.add(tok)
    return deps

def frontmatter(text):
    """The YAML frontmatter block only (between the first --- ... ---), so field lookups/rewrites
    never match a `used-by:`-like line in the note BODY."""
    m = re.match(r'(?s)\s*---\n(.*?)\n---', text)
    return m.group(1) if m else ""

def fm_value(text, field):
    m = FM_FIELD_RE(field).search(frontmatter(text))
    return m.group(1).strip() if m else None

def snapshot(cfg, ctx, write, report):
    """Regenerate each consuming skill's references/knowledge/ from the brain notes.
    Returns (changed_count, dangling_set)."""
    src, srcdir = source_notes(cfg, ctx)
    if not os.path.isdir(srcdir):
        # vault/source not available (e.g. machine without the vault) — skip, never flag dangling
        return 0, set(), src, srcdir
    consumers = cfg["knowledge"][ctx].get("consumers", [])
    rel_src = cfg["knowledge"][ctx]["dir"] + "/"
    changed, dangling = 0, set()
    for sk, txt in find_skills(consumers):
        deps = skill_deps(txt, set(src))
        skdir = os.path.dirname(sk)
        refdir = os.path.join(skdir, "references", "knowledge")
        for slug in sorted(deps):
            if slug not in src:
                dangling.add((os.path.basename(skdir), slug)); continue
            with open(src[slug], encoding="utf-8") as f:
                body = f.read()
            expected = GEN_HEADER.format(src=rel_src) + body
            dest = os.path.join(refdir, slug + ".md")
            cur = None
            if os.path.exists(dest):
                with open(dest, encoding="utf-8") as f:
                    cur = f.read()
            if cur != expected:
                changed += 1
                report.append(("regen", os.path.relpath(dest, skdir) + f"  ({os.path.basename(skdir)})"))
                if write:
                    os.makedirs(refdir, exist_ok=True)
                    with open(dest, "w", encoding="utf-8") as f:
                        f.write(expected)
        # remove stale snapshots no longer referenced
        if os.path.isdir(refdir):
            for path in glob.glob(os.path.join(refdir, "*.md")):
                slug = os.path.basename(path)[:-3]
                if slug not in deps:
                    changed += 1
                    report.append(("stale", os.path.relpath(path, skdir) + f"  ({os.path.basename(skdir)})"))
                    if write:
                        os.remove(path)
    return changed, dangling, src, srcdir

def integrity(cfg, ctx, src, srcdir):
    """Returns (issues, dangling_links). issues = list of (kind, msg)."""
    issues, dangling_links = [], False
    # which skills reference each slug (for used-by reconcile + orphan)
    consumers = cfg["knowledge"][ctx].get("consumers", [])
    ref_by = {s: set() for s in src}
    for sk, txt in find_skills(consumers):
        for slug in skill_deps(txt, set(src)):
            if slug in ref_by:
                ref_by[slug].add(os.path.basename(os.path.dirname(sk)))
    # MOC links (a note is "alive" if in MOC even if no skill yet)
    moc = os.path.join(srcdir, "_MOC.md")
    moc_links = set()
    if os.path.exists(moc):
        with open(moc, encoding="utf-8") as f:
            moc_links = set(WIKILINK_RE.findall(f.read()))
    for slug, path in sorted(src.items()):
        with open(path, encoding="utf-8") as f:
            txt = f.read()
        # dangling wikilinks
        for tgt in WIKILINK_RE.findall(txt):
            if tgt not in src and tgt not in EXTERNAL_LINKS:
                issues.append(("dangling-link", f"{slug} → [[{tgt}]] (no such note)")); dangling_links = True
        # orphan: referenced by no skill and not in MOC
        if not ref_by[slug] and slug not in moc_links:
            issues.append(("orphan", f"{slug} (no skill references it, not in _MOC)"))
        # used-by reconcile (advisory)
        declared = fm_value(txt, "used-by") or ""
        declared_set = set(re.findall(r'[a-z0-9][a-z0-9-]*', declared))
        actual = ref_by[slug]
        missing = actual - declared_set
        if missing:
            issues.append(("used-by-stale", f"{slug}: skille {sorted(missing)} ciągną, brak w used-by"))
    # dup candidates: title/tag Jaccard
    titles = {}
    for slug, path in src.items():
        with open(path, encoding="utf-8") as f:
            txt = f.read()
        h1 = re.search(r'(?m)^#\s+(.+)$', txt)
        toks = set(re.findall(r'[a-zżźćńółęąśA-Z]{4,}', (h1.group(1) if h1 else slug).lower()))
        titles[slug] = toks
    slugs = sorted(titles)
    for i in range(len(slugs)):
        for j in range(i + 1, len(slugs)):
            a, b = titles[slugs[i]], titles[slugs[j]]
            if a and b:
                jac = len(a & b) / len(a | b)
                if jac >= 0.6:
                    issues.append(("dup?", f"{slugs[i]} ~ {slugs[j]} (overlap {jac:.0%})"))
    return issues, dangling_links

def derive_used_by(cfg, ctx, src, write, report):
    """Rewrite each brain note's used-by frontmatter to the skills that actually reference it."""
    consumers = cfg["knowledge"][ctx].get("consumers", [])
    ref_by = {s: set() for s in src}
    for sk, txt in find_skills(consumers):
        for slug in skill_deps(txt, set(src)):
            if slug in ref_by:
                ref_by[slug].add(os.path.basename(os.path.dirname(sk)))
    for slug, path in src.items():
        with open(path, encoding="utf-8") as f:
            txt = f.read()
        actual = sorted(ref_by[slug])
        new_line = "used-by: [" + ", ".join(actual) + "]"
        if FM_FIELD_RE("used-by").search(frontmatter(txt)):
            new = FM_FIELD_RE("used-by").sub(new_line, txt, count=1)
            if new != txt:
                report.append(("used-by", f"{slug} → {actual}"))
                if write:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new)

def main():
    global CONFIG
    ap = argparse.ArgumentParser()
    ap.add_argument("--context"); ap.add_argument("--all", action="store_true")
    ap.add_argument("--check", action="store_true", help="dry-run; nonzero exit on drift/dangling")
    ap.add_argument("--used-by", action="store_true", help="also rewrite vault notes' used-by")
    ap.add_argument("--quiet", action="store_true", help="print summary only if something changed")
    ap.add_argument("--config", default=CONFIG, help="config.json path (override for testing)")
    args = ap.parse_args()
    CONFIG = args.config
    cfg = load_config()
    write = not args.check
    total_changed, hard_fail, lines = 0, False, []
    for ctx in contexts(cfg, args):
        report = []
        src, srcdir = source_notes(cfg, ctx)
        if not os.path.isdir(srcdir):
            if not args.quiet:
                print(f"[{ctx}] no knowledge dir yet ({srcdir}) — skip")
            continue
        # derive used-by FIRST (rewrites source notes) so snapshot reflects it in ONE pass
        if args.used_by:
            derive_used_by(cfg, ctx, src, write, report)
        changed, dangling, src, srcdir = snapshot(cfg, ctx, write, report)
        issues, dangling_links = integrity(cfg, ctx, src, srcdir)
        total_changed += changed
        if dangling or dangling_links:
            hard_fail = True
        if not args.quiet:
            verb = "would change" if args.check else "changed"
            print(f"[{ctx}] {len(src)} notes · {verb} {changed} snapshot file(s)")
            for kind, msg in report:
                print(f"  · {kind}: {msg}")
            for d in sorted(dangling):
                print(f"  ✗ DANGLING: skill {d[0]} → references/knowledge/{d[1]}.md (no brain note)")
            for kind, msg in issues:
                mark = "✗" if kind == "dangling-link" else "·"
                print(f"  {mark} {kind}: {msg}")
        if args.quiet and changed:
            lines.append(f"regenerated {changed} snapshot(s) for {ctx}")
    if args.quiet and lines:
        print("; ".join(lines))
    if hard_fail:
        sys.exit(2)
    if args.check and total_changed:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
