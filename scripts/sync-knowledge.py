#!/usr/bin/env python3
"""
sync-knowledge.py — Brain knowledge → skill references snapshot + integrity checks.

The brain vault (03-Resources/<ctx>/knowledge/) is the SOURCE OF TRUTH for domain knowledge.
Consuming skills stay thin and declare what they need via `@references/knowledge/<slug>.md`
pointers (+ a `## Knowledge` block). This script snapshots those notes into each skill's
`references/knowledge/` (one-way, generated copy), auto-derives `used-by`, and runs integrity
checks. Config-driven and multi-context (shadow-operator / agency / scandit / …). A context may
`inherits: [<base>]` (e.g. business contexts inherit the `general-business` universal pool); each
inherited base dir is unioned into that context's source set, snapshots, and cross-context
used-by/orphan aggregation, so a universal note is shared without duplication.

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
    """Returns (src, own_dir, origin): src={slug: abspath}, origin={slug: rel_dir}.
    Beyond the context's own knowledge dir, UNIONS in every base context listed in
    `inherits: [...]` (e.g. a business context inherits `general-business`) so a shared /
    universal note becomes a first-class part of THIS context's source set — which resolves
    cross-context wikilinks AND lets snapshot deliver it to this context's consumers. The
    context's OWN dir wins on a slug collision (first-listed wins); excludes _MOC / _*.md.
    `inherits` is a generic list, so non-business pools (general-technical, a truly-global
    `general`, …) are a config-only addition later — no engine change.
    Returns a 4th element `collisions` = [(slug, hidden_reldir, winner_reldir)] so a silently
    shadowed note (same slug in a base pool AND the context — e.g. a promotion left a stale leaf
    copy) is surfaced, not dropped without trace."""
    kn = cfg["knowledge"]
    own_dir = os.path.join(vault_path(cfg), kn[ctx]["dir"])
    reldirs = [kn[ctx]["dir"]]
    for base in kn[ctx].get("inherits", []):
        if base in kn and kn[base]["dir"] not in reldirs:
            reldirs.append(kn[base]["dir"])
    out, origin, collisions = {}, {}, []
    for reldir in reldirs:
        d = os.path.join(vault_path(cfg), reldir)
        if not os.path.isdir(d):
            continue
        for path in glob.glob(os.path.join(d, "*.md")):
            base = os.path.basename(path)
            if base.startswith("_"):
                continue
            slug = base[:-3]
            if slug in out:
                collisions.append((slug, reldir, origin[slug]))  # own / earlier-listed pool wins
                continue
            out[slug] = path
            origin[slug] = reldir
    return out, own_dir, origin, collisions

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
    src, srcdir, origin, _ = source_notes(cfg, ctx)
    if not os.path.isdir(srcdir):
        # vault/source not available (e.g. machine without the vault) — skip, never flag dangling
        return 0, set(), src, srcdir
    consumers = cfg["knowledge"][ctx].get("consumers", [])
    changed, dangling = 0, set()
    for sk, txt in find_skills(consumers):
        deps = skill_deps(txt, set(src))
        skdir = os.path.dirname(sk)
        refdir = os.path.join(skdir, "references", "knowledge")
        for slug in sorted(deps):
            if slug not in src:
                # Context-agnostic guard: a snapshot already on disk that declares a DIFFERENT
                # context belongs to another context sharing this consumer dir (e.g. agency's
                # ag-knowledge physically living in a shadow-operator consumer repo via symlink).
                # It is not THIS context's note — skip it, don't flag a false dangling. Validation
                # thus depends on whose snapshots are actually present, not a single hardcoded ctx.
                foreign = os.path.join(refdir, slug + ".md")
                if os.path.exists(foreign):
                    with open(foreign, encoding="utf-8") as _f:
                        ftxt = _f.read()
                    # snapshots begin with a GEN_HEADER comment line BEFORE the frontmatter;
                    # strip it so frontmatter()/fm_value can see the `context:` field.
                    if ftxt.startswith("<!--") and "\n" in ftxt:
                        ftxt = ftxt.split("\n", 1)[1]
                    snap_ctx = (fm_value(ftxt, "context") or "").strip()
                    if snap_ctx and snap_ctx != ctx:
                        report.append(("skip-foreign-ctx", f"{slug} (context={snap_ctx} ≠ {ctx})"))
                        continue
                dangling.add((os.path.basename(skdir), slug)); continue
            with open(src[slug], encoding="utf-8") as f:
                body = f.read()
            # REFLECT/mirror self-snapshot guard: never snapshot a skill-homed note back INTO its
            # own home skill (circular brain→skill→brain — its source IS that skill). Covers the
            # new `reflection` form and legacy `mirror`.
            if (fm_value(body, "status") or "").strip() in ("reflection", "mirror") and (fm_value(body, "home") or "").strip() == os.path.basename(skdir):
                report.append(("skip-skill-homed-self", f"{slug} (odbicie home={os.path.basename(skdir)})"))
                continue
            # per-note origin: a note inherited from a base context (general-business) records
            # ITS real source dir, not the consuming context's dir, so "edit the brain note" points right.
            expected = GEN_HEADER.format(src=origin[slug] + "/") + body
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

def global_ref_by(cfg):
    """{slug: set(skill_dirname)} aggregated across ALL contexts. A shared/universal note
    (home = a base context, pulled in by several contexts via `inherits`) is referenced by
    the consumers of EVERY context that includes it; per-context ref_by would see only one
    context's slice and flip-flop the note's used-by / false-orphan it on each run. This
    global reverse map is the load-bearing fix: every context's run derives the SAME union
    for a shared note, so used-by is stable and orphan is correct regardless of `active`."""
    ref = {}
    kn = cfg["knowledge"]
    for cx in kn:
        src_cx, _, _, _ = source_notes(cfg, cx)
        if not src_cx:
            continue
        for sk, txt in find_skills(kn[cx].get("consumers", [])):
            for slug in skill_deps(txt, set(src_cx)):
                ref.setdefault(slug, set()).add(os.path.basename(os.path.dirname(sk)))
    return ref

def integrity(cfg, ctx, src, srcdir, origin, gref):
    """Returns (issues, dangling_links). issues = list of (kind, msg).
    `gref` = precomputed global_ref_by (cross-context consumer aggregate); `origin` maps
    slug→home rel-dir so each note's wikilinks are validated against its OWN home context
    (enforces the directional rule under any run)."""
    issues, dangling_links = [], False
    ref_by = {s: gref.get(s, set()) for s in src}
    kn = cfg["knowledge"]
    dir_to_ctx = {kn[c]["dir"]: c for c in kn}
    _src_cache = {}
    def home_src(slug):
        hc = dir_to_ctx.get(origin.get(slug, ""), ctx)
        if hc not in _src_cache:
            s, _, _, _ = source_notes(cfg, hc)
            _src_cache[hc] = set(s)
        return _src_cache[hc]
    # MOC links (a note is "alive" if in MOC even if no skill yet) — own MOC + inherited bases' MOCs
    moc_dirs = [srcdir]
    for base in cfg["knowledge"][ctx].get("inherits", []):
        if base in cfg["knowledge"]:
            moc_dirs.append(os.path.join(vault_path(cfg), cfg["knowledge"][base]["dir"]))
    moc_links = set()
    for md in moc_dirs:
        mp = os.path.join(md, "_MOC.md")
        if os.path.exists(mp):
            with open(mp, encoding="utf-8") as f:
                moc_links |= set(WIKILINK_RE.findall(f.read()))
    for slug, path in sorted(src.items()):
        with open(path, encoding="utf-8") as f:
            txt = f.read()
        st = (fm_value(txt, "status") or "").strip()
        # wikilink integrity — validate against the note's OWN home context src (not the
        # currently-synced context's union). Catches genuine danglings AND enforces the
        # directional rule: leaf→base links resolve (base is in a leaf's home src), but a
        # base/universal note linking DOWN to a context-specific note fails HERE under ANY
        # run (the leaf note is absent from the base's home src) — a clear violation, not a
        # confusing cross-context "no such note" landmine deferred to a sibling context.
        hsrc = home_src(slug)
        for tgt in WIKILINK_RE.findall(txt):
            if tgt in hsrc or tgt in EXTERNAL_LINKS:
                continue
            if tgt in src:
                issues.append(("link-rule", f"{slug} ({dir_to_ctx.get(origin.get(slug,''), ctx)}) → [[{tgt}]] "
                               f"(context-specific target; a base/universal note may only link within its own pool)"))
            else:
                issues.append(("dangling-link", f"{slug} → [[{tgt}]] (no such note)"))
            dangling_links = True
        if st in ("reflection", "mirror"):
            # REFLECT note (and legacy `mirror`) = consumer-less BY DESIGN (source is a standalone
            # team skill, not brain — skill untouched, no `## Knowledge`, no snapshot). Don't flag
            # orphan/used-by-stale; instead flag staleness vs the source skill (heuristic, advisory).
            # Field is `reflects-source`; fall back to legacy `mirror-source` for not-yet-migrated notes.
            msrc = fm_value(txt, "reflects-source") or fm_value(txt, "mirror-source")
            if msrc and os.path.isfile(msrc):
                try:
                    if os.path.getmtime(msrc) > os.path.getmtime(path):
                        issues.append(("reflection-stale", f"{slug}: źródło (skill) nowsze niż odbicie — odśwież (skill→mózg)"))
                except OSError:
                    pass
            continue
        if st == "pointer":
            # POINTER note = title + gist + link only, ZERO knowledge in body, consumer-less BY
            # DESIGN (skill is the source of truth; agent loads it natively in the repo). No body
            # to drift → no staleness check; exclude from orphan/used-by so survival no longer
            # depends on _MOC membership.
            continue
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

def derive_used_by(cfg, ctx, src, write, report, gref):
    """Rewrite each brain note's used-by frontmatter to the skills that actually reference it.
    Uses the cross-context aggregate (`gref`) so a shared/inherited note's used-by is the full
    union (every including context's consumers), not just the currently-synced context's slice.
    NOTE: because `src` includes inherited base-pool notes, a leaf-context `--used-by` run also
    rewrites base notes' files (in the base dir) — idempotently, to the same global union."""
    ref_by = {s: gref.get(s, set()) for s in src}
    for slug, path in src.items():
        with open(path, encoding="utf-8") as f:
            txt = f.read()
        actual = sorted(ref_by[slug])
        new_line = "used-by: [" + ", ".join(actual) + "]"
        if FM_FIELD_RE("used-by").search(frontmatter(txt)):
            new = FM_FIELD_RE("used-by").sub(new_line, txt, count=1)
        elif actual:
            # field absent + real consumers exist → INSERT it at the end of the frontmatter
            # block (just before the closing ---). Without this, derive_used_by could only
            # UPDATE an existing field, so a freshly-created note never gained used-by and
            # `used-by-stale` persisted forever. Function-style replacement avoids backref
            # interpretation of `\` in new_line.
            new = re.sub(r'(?s)(\A\s*---\n.*?\n)(---)',
                         lambda m: m.group(1) + new_line + "\n" + m.group(2), txt, count=1)
        else:
            new = txt
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
    # global consumer aggregate is context-independent — compute ONCE, reuse for every context
    # (integrity + derive_used_by), instead of recomputing the full-repo skill sweep per context.
    gref = global_ref_by(cfg)
    total_changed, hard_fail, lines = 0, False, []
    for ctx in contexts(cfg, args):
        report = []
        src, srcdir, origin, collisions = source_notes(cfg, ctx)
        if not os.path.isdir(srcdir):
            if not args.quiet:
                print(f"[{ctx}] no knowledge dir yet ({srcdir}) — skip")
            continue
        for slug, hidden, winner in collisions:
            report.append(("collision", f"{slug}: {hidden} shadowed by {winner} (slug clash — rename or dedup)"))
        # derive used-by FIRST (rewrites source notes) so snapshot reflects it in ONE pass
        if args.used_by:
            derive_used_by(cfg, ctx, src, write, report, gref)
        changed, dangling, src, srcdir = snapshot(cfg, ctx, write, report)
        issues, dangling_links = integrity(cfg, ctx, src, srcdir, origin, gref)
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
                mark = "✗" if kind in ("dangling-link", "link-rule") else "·"
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
