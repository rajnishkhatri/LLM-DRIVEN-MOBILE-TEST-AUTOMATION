#!/usr/bin/env python3
"""Static verifier for aws-ai-architect-story.html (R1 grammar).

Checked in next to the deliverable per spec FR-15 (Replan R1, 2026-08-28).
Stdlib only; a converge tool, not a CI gate. Exit 0 iff every check passes.

Checks (spec docs/sdd/specs/aws-ai-architect-story.spec.md):
  AC-2   zero external src/href/url()
  AC-3s  static assist: no nowrap on .unverified; scroll-margin + focus-visible
  AC-4   zero residue of the removed temporal grammar (classes + label strings)
  AC-5   every occurrence of a P8-unverified value carries the marker
  AC-6   no 15-word shingle shared with either source bundle
  AC-7s  legend defines lanes + the unverified chip
  AC-8   SVG fills/strokes are tokens (no hex); F2 carries no lane tokens
  AC-9s  nine cards, tables + default-lines, bidirectional part links
  AC-10  data-delta 1..14 all present
  AC-11s seven parts in order, each with an envelope beat
  AC-12  size <= 250 KB; dark-token parity across the three theme blocks
  AC-15s document shell: doctype, html lang, meta charset
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PAGE = HERE / "aws-ai-architect-story.html"

BUNDLE_GLOBS = [
    ("cases/claude-architect-foundation/aws-claude", "**/*.md"),
    ("cases/aws-ai", "**/*.md"),
]

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


html = PAGE.read_text(encoding="utf-8")

# ---- AC-15 static: document shell ----------------------------------------
head = html[:1024]
check("AC-15 doctype is the first bytes", html.lstrip().lower().startswith("<!doctype html>"))
check("AC-15 <html lang> present", '<html lang="en"' in head)
check('AC-15 <meta charset="utf-8"> present', '<meta charset="utf-8">' in head)

# ---- AC-2: zero external resource/navigation URLs ------------------------
ext = re.findall(r'(?:src|href)\s*=\s*["\']https?://', html, re.I)
ext += re.findall(r'url\(\s*["\']?\s*https?://', html, re.I)
check("AC-2 zero external src/href/url()", not ext, f"{len(ext)} external URL(s)")

# ---- AC-4: zero residue of the removed temporal grammar ------------------
residue_tokens = [
    "b-verified", "b-course", "b-superseded", "b-human",
    "delta-pair", 'class="was"', 'class="now"',
]
found_tokens = [t for t in residue_tokens if t in html]
check("AC-4 zero grammar classes in markup", not found_tokens, ", ".join(found_tokens))

no_style = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.S | re.I)
visible = re.sub(r"<[^>]+>", " ", no_style)
label_strings = ["verified 2026", "course-era", "superseded"]
found_labels = [s for s in label_strings if re.search(re.escape(s), visible, re.I)]
check("AC-4 zero label strings in visible text", not found_labels, ", ".join(found_labels))

# ---- AC-5: every P8 value occurrence carries the unverified marker -------
# Footer is the reconciliation list itself and is exempt.
body_no_footer = re.sub(r"<footer.*?</footer>", " ", html, flags=re.S | re.I)
cards = re.findall(r'<article class="decision-card".*?</article>', body_no_footer, re.S)
rest = re.sub(r'<article class="decision-card".*?</article>', " ", body_no_footer, flags=re.S)
segments = cards + re.split(r"</p>|</tr>|</li>|</figcaption>", rest)
P8_PATTERNS = [r"\$\d+\s*/\s*\$\d+", r"1\.25×", r"per-GB-indexed"]
unmarked = []
for seg in segments:
    for pat in P8_PATTERNS:
        if re.search(pat, seg) and "unverified" not in seg:
            snippet = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", seg)).strip()[:80]
            unmarked.append(f"{pat} in '{snippet}'")
check("AC-5 every P8 occurrence marked unverified", not unmarked, "; ".join(unmarked))
check("AC-5 footer as-of line present", "As of 2026-08-27" in html)

# ---- AC-6: 15-word shingle scan vs both source bundles -------------------
def word_list(text):
    return re.findall(r"[a-z0-9']+", text.lower())

page_words = word_list(visible)
page_shingles = {tuple(page_words[i : i + 15]) for i in range(max(0, len(page_words) - 14))}
collisions = []
scanned = 0
for base, glob in BUNDLE_GLOBS:
    root = REPO / base
    if not root.is_dir():
        continue
    for md in root.glob(glob):
        scanned += 1
        src_words = word_list(md.read_text(encoding="utf-8", errors="replace"))
        for i in range(max(0, len(src_words) - 14)):
            sh = tuple(src_words[i : i + 15])
            if sh in page_shingles:
                collisions.append(f"{md.relative_to(REPO)}: '{' '.join(sh[:8])}…'")
                break
check("AC-6 no 15-word shingle vs bundles", not collisions,
      "; ".join(collisions) if collisions else f"{scanned} source files scanned")

# ---- AC-7 static: legend = lanes + unverified chip, nothing else ---------
key_m = re.search(r'<div class="key".*?</div>\s*</div>', html, re.S)
key_html = key_m.group(0) if key_m else ""
check("AC-7 legend has both lanes", "lane-llm" in key_html and "lane-det" in key_html)
check("AC-7 legend defines the unverified chip", "unverified" in key_html)

# ---- AC-8: SVG fills are tokens; F2 carries no lane tokens ---------------
svgs = re.findall(r"<svg.*?</svg>", html, re.S)
hex_fills = [m for svg in svgs for m in re.findall(r'(?:fill|stroke)="(#[0-9A-Fa-f]{3,8})"', svg)]
check("AC-8 no hex fills/strokes inside SVG", not hex_fills, ", ".join(hex_fills))
f2 = next((s for s in svgs if "F2 ·" in s), "")
check("AC-8 F2 exists", bool(f2))
check("AC-8 F2 (single-lane exception) has no lane tokens",
      f2 != "" and "--llm" not in f2 and "--det" not in f2)
two_lane = [s for s in svgs if s is not f2]
missing_lane = [i for i, s in enumerate(two_lane) if "--llm" not in s or "--det" not in s]
check("AC-8 every architecture figure has both lanes", not missing_lane,
      f"figure index(es) {missing_lane}")

# ---- AC-10: delta rows 1..14 all anchored --------------------------------
missing_rows = [n for n in range(1, 15) if f'data-delta="{n}"' not in html]
check("AC-10 data-delta 1..14 all present", not missing_rows, str(missing_rows))

# ---- AC-11 static: seven parts in order, each with an envelope beat ------
part_ids = re.findall(r'<section class="part" id="part-(\d)">', html)
check("AC-11 parts 1..7 in order", part_ids == [str(n) for n in range(1, 8)], str(part_ids))
beatless = []
for n in range(1, 8):
    m = re.search(rf'<section class="part" id="part-{n}">.*?</section>', html, re.S)
    if not m or 'class="envelope-beat"' not in m.group(0):
        beatless.append(n)
check("AC-11 every part closes on an envelope beat", not beatless, str(beatless))

# ---- AC-9 static: nine cards, tables, default lines, bidirectional links -
CARD_PARTS = {
    "d-endpoint": [1], "d-routing": [1], "d-model": [1], "d-retention": [1],
    "d-context": [4], "d-orchestration": [5, 6], "d-governance": [6],
    "d-deploy": [6], "d-evals": [7],
}
card_ids = re.findall(r'<article class="decision-card" id="([\w-]+)"', html)
check("AC-9 nine decision cards", len(card_ids) == 9 and set(card_ids) == set(CARD_PARTS),
      str(card_ids))
bad_cards = []
for cid in card_ids:
    m = re.search(rf'<article class="decision-card" id="{cid}".*?</article>', html, re.S)
    block = m.group(0) if m else ""
    if "<table" not in block or "default-line" not in block or 'href="#part-' not in block:
        bad_cards.append(cid)
check("AC-9 each card: table + default-line + part backref", not bad_cards, str(bad_cards))
unlinked = []
for cid, parts in CARD_PARTS.items():
    for n in parts:
        m = re.search(rf'<section class="part" id="part-{n}">.*?</section>', html, re.S)
        if not m or f'href="#{cid}"' not in m.group(0):
            unlinked.append(f"part-{n} → #{cid}")
check("AC-9 each motivating part links to its card", not unlinked, "; ".join(unlinked))

# ---- AC-12: size + three-block token parity + body background ------------
size = PAGE.stat().st_size
check("AC-12 file size <= 250 KB", size <= 250 * 1024, f"{size / 1024:.1f} KB")
style_m = re.search(r"<style>(.*?)</style>", html, re.S)
style = style_m.group(1) if style_m else ""

def block_tokens(pattern):
    m = re.search(pattern, style, re.S)
    return set(re.findall(r"--[\w-]+(?=\s*:)", m.group(1))) if m else set()

light = block_tokens(r":root\s*\{(.*?)\}")
dark_media = block_tokens(r':root:not\(\[data-theme="light"\]\)\s*\{(.*?)\}')
dark_forced = block_tokens(r':root\[data-theme="dark"\]\s*\{(.*?)\}')
check("AC-12 dark blocks define identical token sets", dark_media and dark_media == dark_forced,
      f"media-only: {sorted(dark_media - dark_forced)}; forced-only: {sorted(dark_forced - dark_media)}")
check("AC-12 every dark token exists in the light palette", dark_media <= light,
      str(sorted(dark_media - light)))
body_m = re.search(r"(?<![\w.-])body\s*\{(.*?)\}", style, re.S)
check("AC-12 body background is a token", bool(body_m) and "background: var(--" in body_m.group(1))

# ---- AC-3 static assists + FR-12 a11y ------------------------------------
unv_rule = re.search(r"\.unverified\s*\{([^}]*)\}", style)
check("AC-3 .unverified chip wraps (no nowrap)", bool(unv_rule) and "nowrap" not in unv_rule.group(1))
check("FR-12 scroll-margin-top clears the sticky legend", "scroll-margin-top" in style)
check("FR-12 :focus-visible style present", ":focus-visible" in style)
n_tables = len(re.findall(r"<table\b", html))
n_theads = len(re.findall(r"<thead\b", html))
check("FR-12 every table has a thead", n_tables > 0 and n_tables == n_theads,
      f"{n_theads}/{n_tables}")
empty_th = re.findall(r"<th[^>]*>\s*</th>", html)
check("FR-12 no empty header cells", not empty_th, f"{len(empty_th)} empty <th>")

# ---- report ---------------------------------------------------------------
fails = [(n, d) for n, ok, d in results if not ok]
width = max(len(n) for n, _, _ in results)
for name, ok, detail in results:
    mark = "PASS" if ok else "FAIL"
    line = f"[{mark}] {name.ljust(width)}"
    if detail and not ok:
        line += f"  — {detail}"
    elif detail and ok and "scanned" in detail:
        line += f"  ({detail})"
    print(line)
print(f"\n{len(results) - len(fails)}/{len(results)} checks green")
sys.exit(1 if fails else 0)
