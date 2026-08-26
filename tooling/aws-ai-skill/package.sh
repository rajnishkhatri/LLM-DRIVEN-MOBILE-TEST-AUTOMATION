#!/usr/bin/env bash
# package.sh — build the distributable aws-ai-* skill bundles from source.
#
# Source of truth is .cursor/skills/aws-ai-* (the skill-sync source; byte-
# identical to the .claude projection). This script NEVER edits the source — it
# stages a clean copy and zips it, so the bundles can always be regenerated after
# a skill edit + `skill_sync.py fix`.
#
# Produces, under dist/:
#   aws-ai-family.zip        all six skill dirs as siblings — the portable unit.
#                            Extract into any skills/ parent (~/.claude/skills/,
#                            a repo .claude/skills/ or .cursor/skills/). Required
#                            layout: the stage skills resolve the router's shared
#                            references via ../aws-ai-lifecycle/references/*, so
#                            they MUST sit as siblings of the router.
#   <member>.skill  (x6)     one single-skill zip per member (top-level <name>/
#                            dir + SKILL.md), matching this repo's .skill format
#                            (cf. tooling/coding-rules-skill/dist/coding-rules.skill)
#                            for the claude.ai "add skill" / profile-install flow.
#                            Install ALL SIX — a lone stage has dangling refs.
#
# Excluded from every bundle: evals/ (dev-only benchmark rubric), __pycache__,
# .pytest_cache, *.pyc, .DS_Store. Bundled runnable scripts/ (deploy CDK app,
# validate offline harness) ARE included — the skill bodies reference them.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="$ROOT/.cursor/skills"
DIST="$ROOT/tooling/aws-ai-skill/dist"
MEMBERS=(aws-ai-lifecycle aws-ai-assess aws-ai-design aws-ai-build aws-ai-deploy aws-ai-validate)

# -X strips extra file attributes; the -x globs drop dev-only + generated files.
EXCLUDES=(-x '*/evals/*' '*/__pycache__/*' '*.pyc' '*/.pytest_cache/*' '*.DS_Store' '*/.DS_Store')

for m in "${MEMBERS[@]}"; do
  [ -f "$SRC/$m/SKILL.md" ] || { echo "ERROR: missing $SRC/$m/SKILL.md" >&2; exit 1; }
done

rm -rf "$DIST"
mkdir -p "$DIST"

cd "$SRC"

echo "→ per-skill .skill bundles"
for m in "${MEMBERS[@]}"; do
  rm -f "$DIST/$m.skill"
  zip -rqX "$DIST/$m.skill" "$m" "${EXCLUDES[@]}"
  echo "  built dist/$m.skill"
done

echo "→ family bundle"
rm -f "$DIST/aws-ai-family.zip"
zip -rqX "$DIST/aws-ai-family.zip" "${MEMBERS[@]}" "${EXCLUDES[@]}"
echo "  built dist/aws-ai-family.zip"

echo
echo "=== bundle manifest ==="
cd "$DIST"
for z in *.skill aws-ai-family.zip; do
  n=$(unzip -l "$z" | awk 'END{print $2}')
  b=$(wc -c < "$z" | tr -d ' ')
  printf "  %-26s %4s files  %8s bytes\n" "$z" "$n" "$b"
done
echo
echo "Rebuild after any skill edit: tooling/aws-ai-skill/package.sh"
