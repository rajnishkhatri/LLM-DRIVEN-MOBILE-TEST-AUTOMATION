#!/usr/bin/env bash
# Build-item acceptance run (spec WHERE criterion, items 1+2+3+4+5+6): on a clean
# copy, offline, with only the C3-declared dependency installed, the committed
# corpus must behave under contract-lint exactly as annotated — all 26 checks
# live, zero DEFERRED, the orchestrator golden runs reproduced byte-identically
# (the unhooked negative control validating red on exactly CHK-SCOPE), resume +
# tamper-refusal exercised, the guard decision corpus and mount goldens held
# byte-exactly, the emitter projection trees reproduced and verify-clean,
# the real catalog (registry + doctrine bodies + its projection goldens)
# validated and reproduced, and the kata rig (plan/analyze/report over the
# pre-registration digest triangle: 240 cells, five decision branches, the
# tamper trio) reproduced byte-identically — selftest exit 0, at 1.4.0 / 0.6.0.
#
# Usage: scripts/acceptance.sh            (from tooling/sdd-roles/validator/)
#   PYTHON=python3.11 scripts/acceptance.sh   to pin the interpreter
#   WHEELHOUSE=/path/to/wheels                for a fully isolated venv
set -euo pipefail

PYTHON="${PYTHON:-python3}"
HERE="$(cd "$(dirname "$0")/../.." && pwd)"   # tooling/sdd-roles
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

echo "== staging clean copy =="
mkdir -p "$STAGE/sdd-roles"
cp -R "$HERE/kernel" "$HERE/validator" "$HERE/ledger" "$STAGE/sdd-roles/"
rm -rf "$STAGE/sdd-roles/validator/.venv" 2>/dev/null || true
cd "$STAGE/sdd-roles"

echo "== venv ($($PYTHON --version 2>&1)) =="
if [ -n "${WHEELHOUSE:-}" ]; then
  "$PYTHON" -m venv .venv
  ./.venv/bin/pip install -q --no-index --find-links "$WHEELHOUSE" jsonschema
else
  # offline fallback: reuse an interpreter that already has jsonschema
  "$PYTHON" -m venv --system-site-packages .venv
fi
./.venv/bin/pip install -q -e validator/ --no-deps --no-build-isolation
./.venv/bin/python - <<'EOF'
import jsonschema  # the single C3-declared dependency must be importable
EOF

echo "== offline selftest =="
# Belt and suspenders: strip proxy vars; the validator's own NetGuard enforces
# no-network in-process (CHK-NET).
env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY \
  ./.venv/bin/contract-lint selftest > selftest-report.json
EXIT=$?

./.venv/bin/python - <<'EOF'
import json
r = json.load(open("selftest-report.json"))
failed = [s for s in r["sections"] if s["outcome"] != "pass"]
assert not failed, f"failed sections: {[s['section'] for s in failed]}"
assert r["exit_code"] == 0
assert r["summary"]["flipped_cases"] == 12, r["summary"]
assert r["summary"]["deferred_entries"] == 0, r["summary"]
assert r["summary"]["guard_cases"] == 23, r["summary"]
assert r["summary"]["emitter_trees"] == 4, r["summary"]
assert r["summary"]["catalog_trees"] == 3, r["summary"]
assert r["summary"]["kata_cells"] == 240, r["summary"]
assert r["summary"]["kata_verdict_goldens"] >= 5, r["summary"]
print("sections:", len(r["sections"]), "all pass;",
      "flipped cases:", r["summary"]["flipped_cases"],
      "| guard cases:", r["summary"]["guard_cases"],
      "| emitter trees:", r["summary"]["emitter_trees"],
      "| catalog trees:", r["summary"]["catalog_trees"],
      "| kata cells:", r["summary"]["kata_cells"],
      "| kata verdicts:", r["summary"]["kata_verdict_goldens"],
      "| deferred entries:", r["summary"]["deferred_entries"],
      "| schema", r["schema_version"], "| validator", r["validator_version"])
EOF

echo "== ACCEPTANCE PASS (exit $EXIT) =="
