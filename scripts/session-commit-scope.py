#!/usr/bin/env python3
"""
session-commit-scope.py — git commit scoping helper for /brain-finish Phase 5.

Two modes:
  --survey <repo>...            per repo: worktree-dirty paths, INDEX entries, untracked paths
  --plan <repo>... -- <path>... group supplied paths by repo, flag no-ops and index entries that
                                a commit would sweep, and emit the exact add/commit invocations

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

Explicitly NOT in scope: counting memory.md against its threshold (one `wc -l` in Phase 0 —
wrapping it is overhead, not leverage).

Exit codes: 0 ok · 1 advisory warnings (no-op path and/or sweep risk) · 2 hard error
            (unreadable repo, or a supplied path outside every known repo).
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


def repo_root(path):
    if not os.path.isdir(path):
        die("not a directory: " + path)
    return git(path, "rev-parse", "--show-toplevel").decode("utf-8").strip()


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

    grouped = {root: [] for root in ordered}
    orphans = []
    for p in paths:
        ap = os.path.abspath(p)
        for root in ordered:
            if ap == root or ap.startswith(root + os.sep):
                grouped[root].append(os.path.relpath(ap, root))
                break
        else:
            orphans.append(p)

    warn = False
    for root in ordered:
        rels = grouped[root]
        if not rels:
            continue
        st = states[root]
        known = set(st["dirty"]) | set(st["untracked"]) | {bare(e) for e in st["index"]}
        print("REPO %s" % root)
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


def main():
    ap = argparse.ArgumentParser(
        prog="session-commit-scope.py",
        description="Survey git state per repo, or plan a path-scoped commit.")
    ap.add_argument("--survey", nargs="+", metavar="REPO",
                    help="report dirty / index / untracked paths per repo")
    ap.add_argument("--plan", nargs="+", metavar="REPO",
                    help="plan a scoped commit; list paths after a bare --")
    ap.add_argument("paths", nargs="*", metavar="PATH",
                    help="paths to scope (only with --plan, after --)")
    args = ap.parse_args()

    if bool(args.survey) == bool(args.plan):
        ap.error("pass exactly one of --survey or --plan")
    if args.survey:
        if args.paths:
            ap.error("--survey takes repos only; got extra paths: %s" % " ".join(args.paths))
        sys.exit(do_survey(args.survey))
    if not args.paths:
        ap.error("--plan needs paths after a bare --")
    sys.exit(do_plan(args.plan, args.paths))


if __name__ == "__main__":
    main()
