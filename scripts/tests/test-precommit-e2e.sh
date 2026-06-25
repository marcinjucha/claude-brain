#!/usr/bin/env bash
# End-to-end pre-commit test in a REAL throwaway git repo: install the GENERATED hook (via
# install-precommit with a test --config), then exercise clean / drift-regen-stage / dangling-block.
set -uo pipefail
INSTALL="/Users/marcinjucha/Prywatne/projects/claude-brain/scripts/install-precommit.sh"
SYNC="/Users/marcinjucha/Prywatne/projects/claude-brain/scripts/sync-knowledge.py"
ROOT="$(mktemp -d)"; PASS=0; FAIL=0
ok(){ PASS=$((PASS+1)); echo "  ✅ $1"; }
no(){ FAIL=$((FAIL+1)); echo "  ❌ $1"; }
G(){ git -C "$ROOT/repo" -c user.email=t@t -c user.name=t "$@"; }

# fixtures: vault note + skill (pointer form) + config + git repo
K="$ROOT/vault/03-Resources/e2e/knowledge"; mkdir -p "$K"
printf -- "---\nid: rule-one\nstatus: canon\n---\n# Rule one\nORIGINAL-BODY\n" > "$K/rule-one.md"
printf -- "---\ntype: moc\n---\n# MOC\n- [[rule-one]]\n" > "$K/_MOC.md"
mkdir -p "$ROOT/repo/skills/s1"
cat > "$ROOT/repo/skills/s1/SKILL.md" <<'EOF'
---
name: s1
---
# S1
## Knowledge
- @references/knowledge/rule-one.md — the rule
EOF
cat > "$ROOT/config.json" <<EOF
{ "vault": { "path": "$ROOT/vault" }, "paths": {},
  "knowledge": { "e2e": { "dir": "03-Resources/e2e/knowledge", "active": true, "consumers": ["$ROOT/repo/skills"] } } }
EOF
G init -q

echo "### setup: install GENERATED pre-commit (with test --config) + first sync + initial commit"
bash "$INSTALL" "$ROOT/repo" e2e "$ROOT/config.json" >/dev/null
[ -x "$ROOT/repo/.git/hooks/pre-commit" ] && ok "pre-commit zainstalowany i wykonywalny" || no "brak pre-commit"
python3 "$SYNC" --context e2e --config "$ROOT/config.json" >/dev/null 2>&1
G add -A; G commit -q -m init
G rev-parse HEAD >/dev/null 2>&1 && ok "initial commit przeszedł (stan czysty)" || no "init commit padł"
grep -q "ORIGINAL-BODY" "$ROOT/repo/skills/s1/references/knowledge/rule-one.md" && ok "snapshot ma ORIGINAL-BODY" || no "snapshot zły"

echo "### A) DRIFT: edytuj notatkę w vaulcie → commit → pre-commit regeneruje+stage'uje snapshot"
printf -- "---\nid: rule-one\nstatus: canon\n---\n# Rule one\nEDITED-BODY-V2\n" > "$K/rule-one.md"
printf "tweak\n" >> "$ROOT/repo/skills/s1/SKILL.md"   # something to commit
G add skills/s1/SKILL.md
G commit -q -m "edit skill; expect snapshot auto-refresh"
if G rev-parse HEAD >/dev/null 2>&1; then ok "commit przeszedł"; else no "commit padł"; fi
# the committed snapshot must now reflect the vault edit (pre-commit regenerated + staged it)
if G show HEAD:skills/s1/references/knowledge/rule-one.md 2>/dev/null | grep -q "EDITED-BODY-V2"; then
  ok "ZACOMMITOWANY snapshot odświeżony do EDITED-BODY-V2 (pre-commit regen+stage działa)"
else
  no "zacommitowany snapshot NIE odświeżony (regen/stage nie zadziałał)"
fi
[ -z "$(G status --porcelain)" ] && ok "drzewo czyste po commicie (snapshot zestage'owany, nie zwisa)" || no "drzewo brudne: $(G status --porcelain)"

echo "### B) DANGLING: dodaj wskaźnik do nieistniejącej notatki → commit ZABLOKOWANY"
printf -- "- @references/knowledge/ghost.md — nie istnieje\n" >> "$ROOT/repo/skills/s1/SKILL.md"
G add skills/s1/SKILL.md
if G commit -q -m "should be blocked" 2>/dev/null; then
  no "commit przeszedł mimo dangling (BRAK blokady!)"
else
  ok "commit ZABLOKOWANY przez pre-commit (dangling → exit 2 → block)"
fi
# fix it back → commit should pass again
G reset -q HEAD skills/s1/SKILL.md 2>/dev/null
sed -i '' '/ghost.md/d' "$ROOT/repo/skills/s1/SKILL.md" 2>/dev/null || sed -i '/ghost.md/d' "$ROOT/repo/skills/s1/SKILL.md"
printf "post-fix real change\n" >> "$ROOT/repo/skills/s1/SKILL.md"   # ensure there IS something to commit
G add -A
if G commit -q -m "dangling removed"; then ok "po usunięciu dangling commit znów przechodzi" || true; else no "nadal blokuje po naprawie"; fi

echo; echo "================  PRE-COMMIT E2E: $PASS PASS / $FAIL FAIL  ================"
rm -rf "$ROOT"
[ $FAIL -eq 0 ]
