#!/usr/bin/env python3
"""
session-commit-scope.py — git commit scoping helper for /brain-finish Phase 5.

Three modes:
  --survey <repo>...                 per repo: worktree-dirty paths, INDEX entries, untracked paths
  --plan <repo>... -- <path>...      group supplied paths by repo, flag no-ops and index entries that
                                     a commit would sweep, warn about a pre-commit hook, and emit the
                                     exact add/commit invocations
  --verify <repo> <sha> -- <path>... compare what the commit ACTUALLY holds against the intended set

BOUNDARY — the script NEVER decides WHICH paths are "this session's". That is judgment and stays
with the model, which knows what it wrote. The script's value is CORRECTNESS, not input size:

  1. It removes two real shell traps.
     - 2026-08-03: `git commit -- <paths> -m "msg"` fails with the misleading
       `pathspec '-m' did not match any file(s)` and echoes the whole message as a missing path.
       The emitted command always puts `-m` BEFORE `--`.
     - zsh does not word-split an unexpanded variable, so `P="a.md b.md"; git add $P` passes ONE
       path. The emitted commands list every path explicitly, shell-quoted.
  2. It mechanizes the index inspection that the 2026-07-29 incident proved gets forgotten:
     `git commit` commits the whole INDEX, not the paths you just staged — four renames staged by
     an earlier session were swept into a commit claiming to hold only that session's work.
  3. It closes the SECOND sweep vector, found on the first real /brain-finish run (2026-08-04):
     a repo `pre-commit` hook can `git add` files DURING the commit, so a correctly scoped pathspec
     is not a guarantee. `claude-marketing`'s hook runs sync-knowledge.py and stages the regenerated
     snapshots; commit d6ddaa9 was scoped to `memory.md` and landed with THREE files, two of them
     snapshots belonging to a parallel session, and left those two staged afterwards.
     We do NOT pass --no-verify: that hook also blocks on a dangling reference, so bypassing it
     would buy commit purity at the price of a real safety check. The guarantee therefore moves from
     PREVENT to DETECT AND REPORT TRUTHFULLY — hence the --plan hook warning and the --verify mode.

PATH RESOLUTION (--plan / --verify) — supplied paths are resolved in this order:
  1. absolute            → used as-is;
  2. repo-relative       → exists under one of the supplied repos;
  3. cwd-relative        → exists relative to the process CWD, then mapped into its repo;
  4. git-known           → --plan only: not on disk (e.g. a staged DELETION) but git reports it
                           dirty/staged/untracked in exactly one supplied repo;
  5. otherwise           → hard error.
An AMBIGUOUS path (exists both repo-relative and cwd-relative, resolving to DIFFERENT files) is a
hard error, never a guess: silently picking one of two real files is exactly the class of mistake
this script exists to prevent. WHY resolution order at all — the interface reads `--plan <repo> --
<paths>`, so repo-relative paths are the natural call; resolving them against CWD (the pre-2026-08-04
behavior) failed every path whenever the target repo was not the CWD, which is the normal case for
the vault and for claude-brain.

Explicitly NOT in scope: counting memory.md against its threshold (one `wc -l` in Phase 0 —
wrapping it is overhead, not leverage).

Exit codes: 0 ok · 1 advisory warnings (--plan: no-op path and/or sweep risk; --verify: EXTRA or
            MISSING entries) · 2 hard error (unreadable repo, unresolvable or ambiguous path, or a
            supplied path outside every known repo).
"""
import argparse
import os
import shlex
import subprocess
import sys

INDEX_CODES = "MADRCT"      # column 1: staged change -> a commit would include it
WORKTREE_CODES = "MADRCT"   # column 2: unstaged change in the worktree


def die(msg, code=2):
    sys.stderr.write("session-commit-scope: " + msg + "\n")
    sys.exit(code)


def git(repo, *args):
    """Run git in `repo`; return stdout as bytes. Dies on failure."""
    proc = subprocess.run(("git", "-C", repo) + args,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        die("git %s failed in %s: %s" % (" ".join(args), repo,
                                         proc.stderr.decode("utf-8", "replace").strip()))
    return proc.stdout


def git_soft(repo, *args):
    """Run git in `repo`; return (returncode, stdout bytes). Never dies.

    Used for probes where a non-zero exit is a legitimate answer (`config --get` of an unset key).
    """
    proc = subprocess.run(("git", "-C", repo) + args,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode, proc.stdout


def repo_root(path):
    if not os.path.isdir(path):
        die("not a directory: " + path)
    return git(path, "rev-parse", "--show-toplevel").decode("utf-8").strip()


def pre_commit_hook(root):
    """Return the path of an executable `pre-commit` hook, or None.

    Honors core.hooksPath (a repo can relocate its hooks); falls back to the hooks dir git itself
    reports, which is correct for worktrees and separate git dirs too.
    """
    rc, out = git_soft(root, "config", "--get", "core.hooksPath")
    configured = out.decode("utf-8", "replace").strip() if rc == 0 else ""
    if configured:
        base = configured if os.path.isabs(configured) else os.path.join(root, configured)
    else:
        rc2, out2 = git_soft(root, "rev-parse", "--git-path", "hooks")
        rel = out2.decode("utf-8", "replace").strip() if rc2 == 0 else ".git/hooks"
        base = rel if os.path.isabs(rel) else os.path.join(root, rel)
    candidate = os.path.join(base, "pre-commit")
    if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
        return candidate
    return None


HOOK_WARNING = ("⚠ HOOK      %s — a pre-commit hook may stage files OUTSIDE your pathspec; "
                "check the commit afterwards with --verify")


def scan(root):
    """Parse `git status --porcelain=v1 -z -uall` into three ordered path lists.

    -z is used deliberately: git quotes paths containing spaces or non-ASCII in its default
    output, and the vault has both (a `google doc/` folder, Polish filenames). With -z the paths
    arrive raw and NUL-separated, so no unquoting is needed.
    """
    raw = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    fields = raw.split(b"\x00")
    index, dirty, untracked = [], [], []
    i = 0
    while i < len(fields):
        entry = fields[i]
        i += 1
        if len(entry) < 4:
            continue
        xy = entry[:2].decode("utf-8", "replace")
        path = entry[3:].decode("utf-8", "surrogateescape")
        x, y = xy[0], xy[1]
        if xy == "??":
            untracked.append(path)
        else:
            if x in ("R", "C"):
                # rename/copy: the ORIGIN path follows as its own NUL-terminated field
                if i < len(fields):
                    origin = fields[i].decode("utf-8", "surrogateescape")
                    i += 1
                    index.append("%s (<- %s)" % (path, origin))
                else:
                    index.append(path)
            elif x in INDEX_CODES:
                index.append(path)
            if y in WORKTREE_CODES:
                dirty.append(path)
    return {"index": index, "dirty": dirty, "untracked": untracked}


def commit_files(root, sha):
    """Paths a commit actually touches, per `git show --name-only`.

    -z for the same reason as scan(): raw NUL-separated paths, no unquoting of non-ASCII names.
    The empty --format= still emits a newline before the name list, so leading newlines are
    stripped per field. A rename is reported under its NEW name only, which is what we compare.
    """
    raw = git(root, "show", "--name-only", "--format=", "-z", sha)
    out = []
    for field in raw.split(b"\x00"):
        name = field.strip(b"\n")
        if name:
            out.append(name.decode("utf-8", "surrogateescape"))
    return out


def print_survey(root, st):
    print("REPO %s" % root)
    for kind in ("index", "dirty", "untracked"):
        for p in st[kind]:
            print("  %-9s %s" % (kind, p))
    print("  TOTAL   index=%d dirty=%d untracked=%d"
          % (len(st["index"]), len(st["dirty"]), len(st["untracked"])))


def bare(path_entry):
    """Strip the '(<- origin)' annotation a rename entry carries."""
    return path_entry.split(" (<- ", 1)[0]


def resolve(p, roots, known=None):
    """Resolve one supplied path to an absolute path. See PATH RESOLUTION in the module docstring.

    `known` (optional) maps root -> set of git-known relative paths, used as step 4 so that a path
    which no longer exists on disk (a staged deletion) still resolves.
    """
    if os.path.isabs(p):
        return os.path.abspath(p)

    hits = []          # (how, abspath) — ordered repo-relative first, then cwd-relative
    for root in roots:
        cand = os.path.abspath(os.path.join(root, p))
        if os.path.exists(cand):
            hits.append(("repo-relative to " + root, cand))
    cwd_cand = os.path.abspath(p)
    if os.path.exists(cwd_cand):
        hits.append(("cwd-relative", cwd_cand))

    distinct = []
    for _, cand in hits:
        if cand not in distinct:
            distinct.append(cand)
    if len(distinct) > 1:
        die("ambiguous path %s — resolves to DIFFERENT files repo-relative and cwd-relative (%s); "
            "pass an absolute path" % (p, " vs ".join(distinct)))
    if distinct:
        return distinct[0]

    if known:
        matches = [os.path.join(root, p) for root, rels in known.items() if p in rels]
        if len(matches) == 1:
            return os.path.abspath(matches[0])
        if len(matches) > 1:
            die("ambiguous path %s — git reports it in more than one supplied repo (%s); "
                "pass an absolute path" % (p, " vs ".join(matches)))

    die("path not found (tried repo-relative and cwd-relative): %s" % p)


def group_by_repo(abs_paths, ordered_roots):
    """Split absolute paths into {root: [relpath...]} plus a list of paths outside every root."""
    grouped = {root: [] for root in ordered_roots}
    orphans = []
    for ap in abs_paths:
        for root in ordered_roots:
            if ap == root or ap.startswith(root + os.sep):
                grouped[root].append(os.path.relpath(ap, root))
                break
        else:
            orphans.append(ap)
    return grouped, orphans


def do_survey(repos):
    for r in repos:
        root = repo_root(r)
        print_survey(root, scan(root))
    return 0


def do_plan(repos, paths):
    roots = [repo_root(r) for r in repos]
    # longest root first, so a nested repo wins over its parent
    ordered = sorted(set(roots), key=len, reverse=True)
    states = {root: scan(root) for root in ordered}
    known_rels = {root: set(st["dirty"]) | set(st["untracked"]) | {bare(e) for e in st["index"]}
                  for root, st in states.items()}

    resolved = [resolve(p, ordered, known_rels) for p in paths]
    grouped, orphans = group_by_repo(resolved, ordered)

    warn = False
    for root in ordered:
        rels = grouped[root]
        if not rels:
            continue
        st = states[root]
        known = known_rels[root]
        print("REPO %s" % root)
        hook = pre_commit_hook(root)
        if hook:
            # advisory only — a hook is normal, not an error, so it must not change the exit code
            print("  " + HOOK_WARNING % hook)
        for rel in rels:
            print("  scoped    %s" % rel)
        noop = [r for r in rels if r not in known]
        for r in noop:
            warn = True
            print("  ⚠ NO-OP    %s — not dirty/staged/untracked (typo?)" % r)
        supplied = set(rels)
        sweep = [e for e in st["index"] if bare(e) not in supplied]
        for e in sweep:
            warn = True
            print("  ⚠ SWEEP    %s — staged but NOT in your set; `git commit` includes the whole index" % e)
        add_paths = [r for r in rels if r in known]
        if add_paths:
            quoted = " ".join(shlex.quote(r) for r in add_paths)
            print("  RUN  git -C %s add -- %s" % (shlex.quote(root), quoted))
            print("  RUN  git -C %s commit -m \"<msg>\" -- %s" % (shlex.quote(root), quoted))
        else:
            print("  RUN  (nothing to commit in this repo)")
        print("  TOTAL   scoped=%d no-op=%d sweep-risk=%d" % (len(rels), len(noop), len(sweep)))

    for p in orphans:
        sys.stderr.write("session-commit-scope: path outside every known repo: %s\n" % p)
    if orphans:
        return 2
    return 1 if warn else 0


def do_verify(repo, sha, paths):
    """Compare a landed commit against the intended path set.

    The EXTRA list is the load-bearing output: it is what makes a run's report truthful about what
    actually landed, since a pre-commit hook can stage files the pathspec never named.
    """
    root = repo_root(repo)
    actual = commit_files(root, sha)

    # Single repo here, so a path that no longer exists on disk (a committed deletion) is simply
    # taken as repo-relative rather than erroring — a MISSING/ok verdict is more useful than a stop.
    intended = []
    for p in paths:
        if os.path.isabs(p):
            ap = os.path.abspath(p)
        elif os.path.exists(os.path.abspath(os.path.join(root, p))) or os.path.exists(os.path.abspath(p)):
            ap = resolve(p, [root])
        else:
            ap = os.path.abspath(os.path.join(root, p))
        intended.append(ap)

    grouped, orphans = group_by_repo(intended, [root])
    for p in orphans:
        sys.stderr.write("session-commit-scope: path outside every known repo: %s\n" % p)
    if orphans:
        return 2
    rels = grouped[root]

    print("REPO %s" % root)
    print("  COMMIT    %s (%d file(s))" % (sha, len(actual)))
    actual_set, intended_set = set(actual), set(rels)
    extra = [a for a in actual if a not in intended_set]
    missing = [r for r in rels if r not in actual_set]
    for r in rels:
        if r in actual_set:
            print("  ok        %s" % r)
    for r in missing:
        print("  ⚠ MISSING  %s — intended but NOT in the commit" % r)
    for a in extra:
        print("  ⚠ EXTRA    %s — in the commit but NOT intended (pre-commit hook staged it?)" % a)

    # A hook that staged files during the commit usually leaves them staged afterwards — a primed
    # trap for the NEXT commit, which would sweep them in. Report it, advisory only.
    leftovers = scan(root)["index"]
    for e in leftovers:
        print("  ⚠ LEFTOVER %s — still staged after the commit; clean before the next one" % e)

    print("  TOTAL   intended=%d actual=%d extra=%d missing=%d staged-leftovers=%d"
          % (len(rels), len(actual), len(extra), len(missing), len(leftovers)))
    return 1 if (extra or missing) else 0


def main():
    ap = argparse.ArgumentParser(
        prog="session-commit-scope.py",
        description="Survey git state per repo, plan a path-scoped commit, or verify a landed one.")
    ap.add_argument("--survey", nargs="+", metavar="REPO",
                    help="report dirty / index / untracked paths per repo")
    ap.add_argument("--plan", nargs="+", metavar="REPO",
                    help="plan a scoped commit; list paths after a bare --")
    ap.add_argument("--verify", nargs=2, metavar=("REPO", "SHA"),
                    help="compare a landed commit against the intended paths, listed after a bare --")
    ap.add_argument("paths", nargs="*", metavar="PATH",
                    help="paths to scope (only with --plan / --verify, after --)")
    args = ap.parse_args()

    chosen = [bool(args.survey), bool(args.plan), bool(args.verify)]
    if sum(chosen) != 1:
        ap.error("pass exactly one of --survey, --plan or --verify")
    if args.survey:
        if args.paths:
            ap.error("--survey takes repos only; got extra paths: %s" % " ".join(args.paths))
        sys.exit(do_survey(args.survey))
    if args.verify:
        if not args.paths:
            ap.error("--verify needs the intended paths after a bare --")
        sys.exit(do_verify(args.verify[0], args.verify[1], args.paths))
    if not args.paths:
        ap.error("--plan needs paths after a bare --")
    sys.exit(do_plan(args.plan, args.paths))


if __name__ == "__main__":
    main()
