#!/usr/bin/env python3
"""Static verifier for insurance-claim-processor-story.html.

Converge-gate tool for the AC set in
docs/sdd/specs/claim-processor-story.spec.md — stdlib only, exit 0 = green.
Run from anywhere; paths resolve relative to this file / the repo root.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent  # docs/architecture/explainers -> repo root
PAGE = HERE / "insurance-claim-processor-story.html"

SOURCES = [
    "insurance-claim-processor/design/solution-design.md",
    "insurance-claim-processor/assess/capability-brief.md",
    "insurance-claim-processor/worksheets/characteristics-worksheet.md",
    "insurance-claim-processor/worksheets/style-decision.md",
    "insurance-claim-processor/components/logical-components.md",
    "insurance-claim-processor/risk/resilience-clinic.md",
    "insurance-claim-processor/validate/architecture-validation.md",
    "insurance-claim-processor/validate/eval-report.md",
    "insurance-claim-processor/build/DEPLOY-WALKTHROUGH.md",
    "insurance-claim-processor/build/DEPLOY-LEDGER.md",
    "insurance-claim-processor/build/README.md",
]

# AC-5a — flagged tunables: every occurrence inside a class*="unverified" element
UNVERIFIED_VALUES = ["$10,000", "0.70"]
# AC-5b — census keywords: each must sit within WINDOW chars of a status marker
CENSUS = [
    "waitForTaskToken",
    "remediation Lambda",
    "ensemble",
    "Knowledge Base",
    "contextual-grounding",
]
STATUS_MARKERS = ("DESIGNED", 'class="status', "NOT YET", "PENDING", "FLAG OFF",
                  "DEFERRED", "STILL AHEAD", "not yet")
WINDOW = 1600

SINGLE_LANE_WHITELIST = {"F2", "F3", "F12", "F13"}
SHINGLE_N = 15
SHINGLE_EXCLUDE = re.compile(r"[^a-z ]")

failures: list[str] = []
passes: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    if ok:
        passes.append(label)
    else:
        failures.append(f"{label}{' — ' + detail if detail else ''}")


def main() -> int:
    if not PAGE.exists():
        print(f"FATAL: {PAGE} missing")
        return 1
    raw = PAGE.read_text(encoding="utf-8")

    # ---- AC-14 static: document shell ----
    check(raw.lstrip().startswith("<!DOCTYPE html>"), "AC-14 doctype first bytes")
    check('<html lang="en">' in raw, "AC-14 html lang")
    check('<meta charset="utf-8">' in raw[:600], "AC-14 charset in head")
    check('name="viewport"' in raw[:800], "AC-14 viewport meta")

    # ---- AC-2: no external resource/navigation URLs ----
    ext = re.findall(r'(?:src|href)="(https?://[^"]+)"', raw) + \
        re.findall(r"url\(\s*['\"]?https?://", raw)
    check(not ext, "AC-2 zero external http(s) src/href/url()", str(ext[:3]))

    # ---- defs block boundaries (for AC-4 / AC-8) ----
    m = re.search(r"<defs>.*?</defs>", raw, re.S)
    check(bool(m), "defs block present")
    defs = m.group(0) if m else ""
    outside = raw.replace(defs, "")

    # ---- AC-4: symbol library discipline ----
    sym_defs = re.findall(r'<symbol id="(sym-[\w-]+)"', raw)
    check(len(sym_defs) == len(set(sym_defs)), "AC-4 each symbol defined once",
          str([s for s in sym_defs if sym_defs.count(s) > 1]))
    check(len(sym_defs) >= 14, "AC-4 symbol vocabulary >= 14", str(len(sym_defs)))
    uses = re.findall(r'<use href="#([\w-]+)"', outside)
    bad_use = [u for u in uses if u not in sym_defs and not u.startswith("f")]
    check(not bad_use, "AC-4 every <use> targets a defined symbol", str(bad_use[:5]))
    check("<symbol" not in outside, "AC-4 no symbol defined outside defs")
    # label adjacency: within 600 chars after each <use>, a visible <text> exists
    unlabeled = 0
    for mm in re.finditer(r'<use href="#sym-[\w-]+"[^>]*/>', outside):
        tail = outside[mm.end():mm.end() + 600]
        if "<text" not in tail:
            unlabeled += 1
    check(unlabeled == 0, "AC-4 every icon placement has a nearby text label",
          f"{unlabeled} unlabeled")

    # ---- AC-8: no hex fills/strokes outside defs; lane presence per figure ----
    hexes = re.findall(r'(?:fill|stroke)="#[0-9A-Fa-f]{3,8}"', outside)
    check(not hexes, "AC-8 no hex fill/stroke outside <defs>", str(hexes[:4]))

    figures = re.findall(r'<figure[^>]*data-fig="(F\d+)"[^>]*>(.*?)</figure>',
                         raw, re.S)
    fig_ids = [f for f, _ in figures if f != "F0"]
    # ---- AC-10: F1..F14 in order; nine parts each with envelope beat ----
    check(fig_ids == [f"F{i}" for i in range(1, 16)],
          "AC-10 figures F1..F15 present in order", str(fig_ids))
    parts = re.findall(r'<section class="part" id="part-(\d)">(.*?)</section>',
                       raw, re.S)
    check(len(parts) == 9, "AC-10 nine part sections", str(len(parts)))
    beatless = [n for n, body in parts if 'class="envelope-beat"' not in body]
    check(not beatless, "AC-10 every part ends with an envelope beat",
          str(beatless))

    for fid, body in figures:
        if fid == "F0":
            continue
        # AC-7: in-SVG plain-English title + caption + citation
        check('class="fig-title"' in body, f"AC-7 {fid} in-SVG title sentence")
        check("<figcaption" in body, f"AC-7 {fid} figcaption present")
        check("insurance-claim-processor/" in body and ", as of 2026-09-2" in body,
              f"AC-7 {fid} sourced figcaption citation")
        # steps on flow figures
        m2 = re.search(rf'data-fig="{fid}"[^>]*data-steps="yes"', raw)
        if m2:
            n_steps = body.count('class="step"')
            check(n_steps >= 3, f"AC-7 {fid} numbered step markers", str(n_steps))
        # two lanes unless whitelisted
        if fid not in SINGLE_LANE_WHITELIST:
            check("--llm-wash" in body and "--det-wash" in body,
                  f"AC-8 {fid} both lane washes present")

    # ---- AC-5a: unverified values marker-wrapped at every occurrence ----
    for val in UNVERIFIED_VALUES:
        for mm in re.finditer(re.escape(val), raw):
            ctx = raw[max(0, mm.start() - 220):mm.start()]
            check("unverified" in ctx,
                  f"AC-5 '{val}' occurrence carries unverified marker",
                  f"at offset {mm.start()}")

    # ---- AC-5b: census keywords near a status marker ----
    for kw in CENSUS:
        idxs = [mm.start() for mm in re.finditer(re.escape(kw), raw)]
        check(bool(idxs), f"AC-5 census keyword present: {kw}")
        near = any(
            any(s in raw[max(0, i - WINDOW):i + WINDOW] for s in STATUS_MARKERS)
            for i in idxs)
        check(near, f"AC-5 status chip near census keyword: {kw}")
    check("What&#8217;s live, as of 2026-09-23" in raw or
          "What’s live, as of 2026-09-23" in raw,
          "AC-5 footer live-status line dated")

    # ---- AC-9 static: ten cards, each table + default-line + ADR id ----
    cards = re.findall(r'<article class="decision-card" id="(d-[\w-]+)">(.*?)'
                       r"</article>", raw, re.S)
    check(len(cards) == 10, "AC-9 ten decision cards", str(len(cards)))
    expected_ids = {"d-host", "d-hitl", "d-guardrail", "d-iam", "d-rag",
                    "d-docunderstand", "d-config", "d-breaker", "d-ensemble",
                    "d-degrade"}
    got_ids = {cid for cid, _ in cards}
    check(got_ids == expected_ids, "AC-9 exact card id set",
          str(sorted(expected_ids ^ got_ids)))
    for cid, body in cards:
        check("<table>" in body, f"AC-9 {cid} trade-off table")
        check('class="default-line"' in body, f"AC-9 {cid} default line")
        check(re.search(r"ADR \d{4}", body) is not None, f"AC-9 {cid} ADR id")
        check('href="#part-' in body, f"AC-9 {cid} back-anchor to a part")

    # ---- AC-11: cited paths exist on disk ----
    cited = set(re.findall(r"insurance-claim-processor/[\w/.-]+\.md", raw))
    for rel in re.findall(r"[+·] (adrs|build|validate|worksheets|specs|risk)/"
                          r"([\w.-]+\.md)", raw):
        cited.add(f"insurance-claim-processor/{rel[0]}/{rel[1]}")
    missing = [c for c in sorted(cited) if not (REPO / c).exists()]
    check(not missing, "AC-11 every cited source path exists", str(missing[:5]))

    # ---- AC-12: size cap + theme discipline ----
    size_kb = PAGE.stat().st_size / 1024
    check(size_kb <= 350, "AC-12 file size <= 350 KB", f"{size_kb:.1f} KB")
    blocks = re.findall(r":root(?:\[data-theme=\"dark\"\]|:not\(\[data-theme="
                        r"\"light\"\]\))?\s*\{(.*?)\}", raw, re.S)
    check(len(blocks) >= 3, "AC-12 three theme blocks", str(len(blocks)))
    if len(blocks) >= 3:
        light = set(re.findall(r"--([\w-]+)\s*:", blocks[0]))
        for i, blk in enumerate(blocks[1:3], start=2):
            toks = set(re.findall(r"--([\w-]+)\s*:", blk))
            extra = toks - light
            check(not extra, f"AC-12 theme block {i} defines no orphan tokens",
                  str(sorted(extra)))
            missing_tok = {"paper", "ink", "det", "llm", "human"} - toks
            check(not missing_tok,
                  f"AC-12 theme block {i} redefines the core palette",
                  str(sorted(missing_tok)))
    check(re.search(r"body\s*\{[^}]*background:\s*var\(--paper\)", raw)
          is not None, "AC-12 explicit token body background")

    # ---- AC-8b: no SVG text may extend past its figure's viewBox ----
    # Approximate glyph advance: mono ~0.615em, sans ~0.52em (+letter-spacing).
    # Added after the 2026-09-23 Stage-7 review found six clipped labels this
    # verifier missed; factors are calibrated so a real overrun fails loudly.
    import html as _html
    for sm in re.finditer(r'<svg viewBox="0 0 (\d+) (\d+)"[^>]*>(.*?)</svg>',
                          raw, re.S):
        vb_w = int(sm.group(1))
        body = sm.group(3)
        fm = re.search(r'letter-spacing="2">([^<]+)</text>', body)
        fig = _html.unescape(fm.group(1)).split(" ·")[0] if fm else "?"
        for tm in re.finditer(r"<text([^>]*)>([^<]*)</text>", body):
            attrs, txt = tm.group(1), _html.unescape(tm.group(2))
            def _attr(name: str, default: str) -> str:
                am = re.search(name + r'="([^"]+)"', attrs)
                return am.group(1) if am else default
            x = float(_attr("x", "0"))
            fs = float(_attr("font-size", "12"))
            ls = float(_attr("letter-spacing", "0"))
            mono = "mono" in _attr("font-family", "")
            w = len(txt) * (fs * (0.615 if mono else 0.52) + ls)
            anchor = _attr("text-anchor", "start")
            x0 = x - w if anchor == "end" else x - w / 2 if anchor == "middle" \
                else x
            x1 = x0 + w
            check(x1 <= vb_w - 4 and x0 >= 2,
                  f"AC-8b {fig} text within viewBox",
                  f"[{x0:.0f},{x1:.0f}] vs {vb_w}: {txt[:50]!r}")

    # ---- AC-6: 15-word shingle originality vs sources ----
    def norm_words(text: str) -> list[str]:
        return SHINGLE_EXCLUDE.sub(" ", text.lower()).split()

    page_words = norm_words(re.sub(r"<[^>]+>", " ", raw))
    page_shingles = {" ".join(page_words[i:i + SHINGLE_N])
                     for i in range(len(page_words) - SHINGLE_N + 1)}
    for src in SOURCES:
        p = REPO / src
        if not p.exists():
            check(False, f"AC-6 source readable: {src}")
            continue
        words = norm_words(p.read_text(encoding="utf-8"))
        hits = [" ".join(words[i:i + SHINGLE_N])
                for i in range(len(words) - SHINGLE_N + 1)
                if " ".join(words[i:i + SHINGLE_N]) in page_shingles]
        check(not hits, f"AC-6 no {SHINGLE_N}-word overlap with {Path(src).name}",
              hits[0][:80] if hits else "")

    # ---- report ----
    print(f"PASS {len(passes)}  FAIL {len(failures)}  ({size_kb:.1f} KB)")
    for f in failures:
        print(f"  FAIL: {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
