#!/usr/bin/env bash
# Render one C4 view end-to-end: IR -> D2 -> SVG -> @2x PNG -> grayscale proof.
#
# This is the deterministic render phase. The LLM authors the IR; this script
# (not the model) produces every pixel, so shape/line encoding is identical
# across views and across runs.
#
# Usage:
#   scripts/render.sh IR.json OUTDIR
# Produces, in OUTDIR:
#   <view-id>.svg
#   <view-id>@2x.png
#   <view-id>.view.md          (combined: image first, node explainer + edge table under it)
#   proofs/<view-id>-gray.png
# where <view-id> is the IR view.id (falls back to the IR basename).
#
# DENSITY-TRIGGERED DECOMPOSITION: after rendering the primary view, the driver
# runs decompose.py. If the view is dense (>=30 edges, or a node with >=12
# incident edges), it emits companion OVERLAY views (by-theme or by-module) into
# OUTDIR/overlays/ and renders each through the same pipeline, then runs the
# SET-LEVEL linter (parity + drill-down + entanglement). The primary stays the
# authoritative whole; overlays are additive. See references/readability.md §1.
#
# Requires: d2, rsvg-convert, python3 + Pillow. See SKILL.md "Prerequisites".
set -euo pipefail

IR="${1:?usage: render.sh IR.json OUTDIR}"
OUTDIR="${2:?usage: render.sh IR.json OUTDIR}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# render_one IR OUTDIR  ->  renders a single view (IR -> D2 -> SVG -> @2x -> gray)
# plus its combined view.md. Factored out so overlays reuse the exact pipeline.
render_one() {
  local ir="$1" outdir="$2"
  local vid
  vid="$(python3 -c 'import json,sys,os
ir=json.load(open(sys.argv[1]))
print(ir.get("view",{}).get("id") or os.path.splitext(os.path.basename(sys.argv[1]))[0])' "$ir")"
  mkdir -p "$outdir/proofs"
  local d2="$outdir/$vid.d2" svg="$outdir/$vid.svg" png="$outdir/${vid}@2x.png"
  local gray="$outdir/proofs/${vid}-gray.png"
  local detail="$outdir/${vid}-detail.md" viewmd="$outdir/${vid}.view.md"
  # IR -> D2 + flat detail table + COMBINED view.md (image-first).
  python3 "$HERE/ir_to_d2.py" "$ir" \
    --detail-out "$detail" --view-md-out "$viewmd" --svg-name "$vid.svg" > "$d2"
  d2 "$d2" "$svg"
  local textn
  textn="$(grep -o '<text' "$svg" | wc -l | tr -d ' ')"
  if [ "$textn" -lt 1 ]; then
    echo "render.sh: FAIL no <text> elements in $svg (text flattened?)" >&2
    return 1
  fi
  echo "render.sh: $svg has $textn <text> elements"
  rsvg-convert --zoom=2 "$svg" -o "$png"
  python3 "$HERE/grayscale_proof.py" "$png" "$gray"
}

# view id from the IR (python is already a dependency), else the IR basename.
VIEW_ID="$(python3 -c 'import json,sys,os
ir=json.load(open(sys.argv[1]))
print(ir.get("view",{}).get("id") or os.path.splitext(os.path.basename(sys.argv[1]))[0])' "$IR")"

# 1. Render the PRIMARY view (the authoritative whole).
render_one "$IR" "$OUTDIR"
SVG="$OUTDIR/$VIEW_ID.svg"
echo "render.sh: primary -> $SVG , $OUTDIR/${VIEW_ID}.view.md"

# 2. Density-triggered decomposition. decompose.py decides (and logs) whether to
#    split, chooses the selector deterministically, and writes overlay IRs.
OVDIR="$OUTDIR/overlays"
MANIFEST="$(python3 "$HERE/decompose.py" "$IR" --out-dir "$OVDIR")"
echo "$MANIFEST"

# 3. Render each overlay through the SAME pipeline, then set-level lint.
OVERLAY_IRS=()
while IFS= read -r line; do
  case "$line" in
    overlay*)
      ov_id="$(printf '%s' "$line" | cut -f2)"
      ov_ir="$OVDIR/$ov_id.json"
      OVERLAY_IRS+=("$ov_ir")
      render_one "$ov_ir" "$OVDIR"
      echo "render.sh: overlay -> $OVDIR/$ov_id.svg , $OVDIR/$ov_id.view.md"
      ;;
  esac
done <<< "$MANIFEST"

if [ "${#OVERLAY_IRS[@]}" -gt 0 ]; then
  echo "render.sh: set-level lint (parity + drill-down + entanglement)"
  # The primary is passed via --primary and is in-scope for drill-down; the
  # parent context view (one grain up) is produced by its own render.sh call and
  # is out of scope for this single-view set (see check_drilldown_links).
  python3 "$HERE/lint_diagram.py" --primary "$IR" --overlays "${OVERLAY_IRS[@]}" \
    || echo "render.sh: WARNING set-level lint reported failures (see above)"
fi

echo "render.sh: done -> $SVG (+ ${#OVERLAY_IRS[@]} overlays)"
