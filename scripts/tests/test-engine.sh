#!/usr/bin/env bash
# Empirical black-box tests for the knowledge-system engine. Isolated fixtures + REAL scripts via
# --config. Multi-char slugs (real-world; SLUG_TOKEN_RE requires >=2 chars by design).
set -uo pipefail

SCRIPT="/Users/marcinjucha/Prywatne/projects/claude-brain/scripts/sync-knowledge.py"
INSTALL="/Users/marcinjucha/Prywatne/projects/claude-brain/scripts/install-precommit.sh"
ROOT="$(mktemp -d)"
PASS=0; FAIL=0
ok(){ PASS=$((PASS+1)); echo "  ✅ $1"; }
no(){ FAIL=$((FAIL+1)); echo "  ❌ $1"; }
note(){ cat > "$1/$2.md" <<EOF
---
type: knowledge
id: $2
status: canon
used-by: [placeholder]
---
# Teza $2
treść $2
EOF
}
build(){
  rm -rf "$ROOT/vault" "$ROOT/repo" "$ROOT/repo2"
  local K="$ROOT/vault/03-Resources/testctx/knowledge"; mkdir -p "$K"
  note "$K" alpha; note "$K" beta; note "$K" gamma; note "$K" delta; note "$K" epsilon
  printf -- "---\ntype: moc\n---\n# MOC\n- [[alpha]] [[beta]] [[delta]] [[epsilon]]\n" > "$K/_MOC.md"
  mkdir -p "$ROOT/repo/skills/test-skill"; git -C "$ROOT/repo" init -q 2>/dev/null || true
  cat > "$ROOT/config.json" <<EOF
{ "vault": { "path": "$ROOT/vault" }, "paths": {},
  "knowledge": {
    "testctx":  { "dir": "03-Resources/testctx/knowledge",  "active": true,  "consumers": ["$ROOT/repo/skills"] },
    "inactive": { "dir": "03-Resources/inactive/knowledge", "active": false, "consumers": ["$ROOT/repo/skills"] },
    "novault":  { "dir": "03-Resources/novault/knowledge",  "active": true,  "consumers": ["$ROOT/repo/skills"] }
  } }
EOF
}
CFG(){ echo "$ROOT/config.json"; }
SK="$ROOT/repo/skills/test-skill/SKILL.md"
REF(){ echo "$ROOT/repo/skills/test-skill/references/knowledge"; }

echo "### T1 — REGRESSJA: realny shadow-operator --check"
out="$(python3 "$SCRIPT" --context shadow-operator --check 2>&1)"; rc=$?
echo "$out" | grep -q "would change 0" && [ $rc -eq 0 ] && ok "shadow-operator 0 zmian, exit 0" || no "regresja: $out (rc=$rc)"

echo "### T2 — MULTI-SLUG BULLET bez inline-pointerów (bug A#2/C#1)"
build
printf -- "---\nname: test\n---\n# Test\n## Knowledge\n- alpha + beta — opis bez pointerow\n" > "$SK"
python3 "$SCRIPT" --config "$(CFG)" --context testctx >/dev/null 2>&1; rc=$?
[ -f "$(REF)/alpha.md" ] && ok "alpha (1. token) zsnapshotowany" || no "brak alpha.md"
[ -f "$(REF)/beta.md" ] && ok "beta (2. token po '+') zsnapshotowany — FIX działa" || no "brak beta.md (bug!)"
[ $rc -eq 0 ] && ok "exit 0" || no "exit=$rc"

echo "### T3 — DANGLING (forma pointer = autorytatywna) → exit 2 + flaga"
printf -- "- @references/knowledge/zzz-nieistnieje.md\n" >> "$SK"
out="$(python3 "$SCRIPT" --config "$(CFG)" --context testctx --check 2>&1)"; rc=$?
[ $rc -eq 2 ] && ok "exit 2 na dangling" || no "exit=$rc (oczek. 2)"
echo "$out" | grep -qi "DANGLING" && ok "raport: DANGLING" || no "brak flagi DANGLING"

echo "### T4 — ORPHAN: gamma poza MOC i skillem → orphan; beta w MOC → nie"
build; printf -- "## Knowledge\n- alpha\n" > "$SK"
out="$(python3 "$SCRIPT" --config "$(CFG)" --context testctx 2>&1)"
echo "$out" | grep -qi "orphan: gamma" && ok "gamma = orphan" || no "gamma nie wykryte: $out"
echo "$out" | grep -qi "orphan: beta" && no "beta błędnie orphan (jest w MOC)" || ok "beta NIE orphan (w MOC)"

echo "### T5 — IDEMPOTENCJA"
python3 "$SCRIPT" --config "$(CFG)" --context testctx >/dev/null 2>&1
out="$(python3 "$SCRIPT" --config "$(CFG)" --context testctx --check 2>&1)"; rc=$?
echo "$out" | grep -q "would change 0" && [ $rc -eq 0 ] && ok "0 zmian, exit 0" || no "nieidempotentny: $out (rc=$rc)"

echo "### T6 — STALE removal"
build; printf -- "## Knowledge\n- alpha\n- beta\n" > "$SK"
python3 "$SCRIPT" --config "$(CFG)" --context testctx >/dev/null 2>&1
[ -f "$(REF)/beta.md" ] && ok "setup: beta.md istnieje" || no "setup: brak beta.md"
printf -- "## Knowledge\n- alpha\n" > "$SK"
python3 "$SCRIPT" --config "$(CFG)" --context testctx >/dev/null 2>&1
[ ! -f "$(REF)/beta.md" ] && ok "beta.md usunięte (stale)" || no "beta.md zostało"
[ -f "$(REF)/alpha.md" ] && ok "alpha.md zostało" || no "alpha.md zniknęło błędnie"

echo "### T7 — SYMLINK DEDUP"
build; mkdir -p "$ROOT/repo2/skills"; ln -s "$ROOT/repo/skills/test-skill" "$ROOT/repo2/skills/test-skill"
cat > "$ROOT/config.json" <<EOF
{ "vault": { "path": "$ROOT/vault" }, "paths": {},
  "knowledge": { "testctx": { "dir": "03-Resources/testctx/knowledge", "active": true,
    "consumers": ["$ROOT/repo/skills", "$ROOT/repo2/skills"] } } }
EOF
printf -- "## Knowledge\n- alpha\n" > "$SK"
out="$(python3 "$SCRIPT" --config "$(CFG)" --context testctx 2>&1)"
cnt="$(echo "$out" | grep -c "regen:.*alpha.md")"
[ "$cnt" -eq 1 ] && ok "alpha.md regen RAZ mimo 2 konsumentów (dedup)" || no "regen ×$cnt (brak dedup)"

echo "### T8 — INACTIVE pominięty w --all"
build
out="$(python3 "$SCRIPT" --config "$(CFG)" --all 2>&1)"
echo "$out" | grep -q "\[inactive\]" && no "inactive przetworzony" || ok "inactive pominięty"

echo "### T9 — MISSING vault dir (active novault) → no-op, exit≠2"
out="$(python3 "$SCRIPT" --config "$(CFG)" --context novault 2>&1)"; rc=$?
echo "$out" | grep -qi "no knowledge dir" && ok "'no knowledge dir', skip" || no "nie obsłużył: $out"
[ $rc -ne 2 ] && ok "exit≠2 (nie blokuje commita bez vaulta)" || no "exit 2 błędnie"

echo "### T10 — derive_used_by SCOPED do FM (bug A#4)"
build
cat > "$ROOT/vault/03-Resources/testctx/knowledge/delta.md" <<'EOF'
---
type: knowledge
id: delta
used-by: [stare]
---
# Teza delta
przykład w treści: used-by: NIE-RUSZAJ-MNIE
EOF
printf -- "## Knowledge\n- delta\n" > "$SK"
python3 "$SCRIPT" --config "$(CFG)" --context testctx --used-by >/dev/null 2>&1
grep -q "used-by: NIE-RUSZAJ-MNIE" "$ROOT/vault/03-Resources/testctx/knowledge/delta.md" && ok "linia used-by w TREŚCI nietknięta" || no "treść skorumpowana"
head -6 "$ROOT/vault/03-Resources/testctx/knowledge/delta.md" | grep -q "used-by: \[test-skill\]" && ok "FM used-by → faktyczni konsumenci" || no "FM nie zaktualizowane"

echo "### T11 — install-precommit w WORKTREE (bug A#1)"
WT_MAIN="$ROOT/wtmain"; mkdir -p "$WT_MAIN"; git -C "$WT_MAIN" init -q
git -C "$WT_MAIN" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init
git -C "$WT_MAIN" worktree add -q "$ROOT/wt" 2>/dev/null
[ -f "$ROOT/wt/.git" ] && ok "potwierdzono: w worktree .git to PLIK" || no "setup worktree"
out="$(bash "$INSTALL" "$ROOT/wt" testctx 2>&1)"; rc=$?
hp="$(git -C "$ROOT/wt" rev-parse --git-path hooks 2>/dev/null)"; case "$hp" in /*) ;; *) hp="$ROOT/wt/$hp";; esac
[ $rc -eq 0 ] && [ -x "$hp/pre-commit" ] && ok "pre-commit w worktree ($hp) — FIX działa" || no "instalacja padła: $out (rc=$rc)"

echo "### T12 — --used-by JEDNYM przebiegiem zostawia snapshoty w sync (bug kolejności)"
build
printf -- "## Knowledge\n- @references/knowledge/alpha.md\n" > "$SK"
python3 "$SCRIPT" --config "$(CFG)" --context testctx --used-by >/dev/null 2>&1
out="$(python3 "$SCRIPT" --config "$(CFG)" --context testctx --check 2>&1)"; rc=$?
echo "$out" | grep -q "would change 0" && [ $rc -eq 0 ] && ok "po --used-by snapshoty w sync (derive PRZED snapshot)" || no "dryf po --used-by: $out (rc=$rc)"
head -8 "$ROOT/vault/03-Resources/testctx/knowledge/alpha.md" | grep -q "used-by: \[test-skill\]" && ok "used-by w źródle zaktualizowane" || no "used-by nie zaktualizowane"

echo "### T13 — MIRROR: orphan-exclude (C2) + mirror-stale (C1) + self-snapshot-guard (C3)"
build
SRC="$ROOT/teamskill.md"; printf "team content\n" > "$SRC"
cat > "$ROOT/vault/03-Resources/testctx/knowledge/gamma.md" <<EOF
---
type: knowledge
id: gamma
status: mirror
home: test-skill
mirror-source: $SRC
---
# Mirror gamma
treść lustra
EOF
# C2: gamma (mirror) NIE referowane przez skill i NIE w MOC → NIE orphan
printf -- "## Knowledge\n- @references/knowledge/alpha.md\n" > "$SK"
out="$(python3 "$SCRIPT" --config "$(CFG)" --context testctx --check 2>&1)"
echo "$out" | grep -qi "orphan: gamma" && no "mirror gamma błędnie orphan (C2)" || ok "mirror gamma NIE orphan mimo braku w MOC i konsumencie (C2)"
# C1: źródło nowsze niż lustro → mirror-stale
sleep 1; touch "$SRC"
out="$(python3 "$SCRIPT" --config "$(CFG)" --context testctx --check 2>&1)"
echo "$out" | grep -qi "mirror-stale: gamma" && ok "mirror-stale wykryte gdy źródło nowsze (C1)" || no "brak mirror-stale: $out"
# C3: skill referuje gamma a home==test-skill → NIE self-snapshot
printf -- "## Knowledge\n- @references/knowledge/gamma.md\n" > "$SK"
python3 "$SCRIPT" --config "$(CFG)" --context testctx >/dev/null 2>&1
[ ! -f "$(REF)/gamma.md" ] && ok "mirror gamma NIE zsnapshotowane do własnego home-skilla (C3)" || no "circular self-snapshot lustra!"

echo; echo "================  WYNIK: $PASS PASS / $FAIL FAIL  ================"
rm -rf "$ROOT"
[ $FAIL -eq 0 ]
