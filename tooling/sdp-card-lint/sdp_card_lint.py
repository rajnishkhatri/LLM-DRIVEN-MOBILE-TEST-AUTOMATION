#!/usr/bin/env python3
"""sdp-card-lint (V5) — enforce the frozen sdp-* pattern-card template.

Read-only, stdlib-only, deterministic. Walks every `*/references/*.md` under the
given root(s) and asserts the §13 addressable-card invariant + the constitution's
card contract at the mechanical level:

  1. frontmatter carries a non-empty `id`   (addressable by a stable catalog id)
  2. a `## Trade-offs` section exists        (explicit trade-off surface)
  3. a `## Sources` section exists           (cited sources)
  4. a definition/motivation intro paragraph precedes the first `##`
     (self-contained: the card opens by saying what the pattern is and why)

Grammar (fixtures assert these literally):
    CARD sdp-resilience/references/CircuitBreaker.md MISSING sources-section
    OK sdp-resilience/references/RetryBackoff.md
    SUMMARY: 3 cards, 1 with issues -> exit 2

Exit: 0 all clean · 2 any card with an issue · 1 usage/config (no root, no cards).
Not bound as a gate — run it in implement/convergence:
    python3 tooling/sdp-card-lint/sdp_card_lint.py .cursor/skills
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
ID_LINE = re.compile(r"^id:\s*(\S.*?)\s*$", re.MULTILINE)
H1 = re.compile(r"^#\s+\S", re.MULTILINE)
TRADEOFFS = re.compile(r"^##\s+Trade-offs\s*$", re.IGNORECASE | re.MULTILINE)
SOURCES = re.compile(r"^##\s+Sources\s*$", re.IGNORECASE | re.MULTILINE)
SEE_ALSO = re.compile(r"^\s*See also:", re.IGNORECASE)


def find_cards(roots: list[Path]) -> list[Path]:
    """sdp-* pattern cards only: `<sdp-*>/references/*.md`.

    Scoped to skill dirs whose name starts with `sdp-` so that running the lint
    against a shared skills root (e.g. `.cursor/skills`) does not judge other
    families' reference docs (arch-*, aws-ai-*, okf) against this template.
    """
    cards: set[Path] = set()
    for root in roots:
        candidates = list(root.rglob("references/*.md"))
        if root.name == "references":  # root points directly at a references dir
            candidates += list(root.glob("*.md"))
        for p in candidates:
            if (
                p.is_file()
                and p.parent.name == "references"
                and p.parent.parent.name.startswith("sdp-")
            ):
                cards.add(p)
    return sorted(cards)


def check_card(text: str) -> list[str]:
    """Return the sorted list of MISSING element tokens for one card body."""
    missing: list[str] = []
    fm = FRONTMATTER.match(text)
    front = fm.group(1) if fm else ""
    body = text[fm.end():] if fm else text

    idm = ID_LINE.search(front)
    if not idm or not idm.group(1).strip():
        missing.append("id")

    if not TRADEOFFS.search(body):
        missing.append("trade-offs-section")
    if not SOURCES.search(body):
        missing.append("sources-section")

    # intro: non-empty prose between the H1 and the first '## ' heading,
    # excluding the H1 line itself and any 'See also:' pointer line. Start at the
    # line AFTER the H1 (H1.end() lands mid-line, so the H1's own tail must not
    # count as intro prose).
    h1 = H1.search(body)
    if h1:
        nl = body.find("\n", h1.start())
        start = nl + 1 if nl != -1 else len(body)
    else:
        start = 0
    first_h2 = re.search(r"^##\s", body[start:], re.MULTILINE)
    window = body[start: start + first_h2.start()] if first_h2 else body[start:]
    has_intro = any(
        line.strip() and not line.lstrip().startswith("#") and not SEE_ALSO.match(line)
        for line in window.splitlines()
    )
    if not has_intro:
        missing.append("intro")

    return missing


def main(argv: list[str]) -> int:
    roots = [Path(a) for a in argv[1:]] or [Path(".")]
    bad_root = [r for r in roots if not r.exists()]
    if bad_root:
        for r in bad_root:
            print(f"ERROR no such path: {r}", file=sys.stderr)
        return 1

    cards = find_cards(roots)
    if not cards:
        print("ERROR no cards found (looked for */references/*.md)", file=sys.stderr)
        return 1

    issues = 0
    for card in cards:
        rel = _display(card)
        missing = check_card(card.read_text(encoding="utf-8"))
        if missing:
            issues += 1
            for element in missing:
                print(f"CARD {rel} MISSING {element}")
        else:
            print(f"OK {rel}")

    code = 2 if issues else 0
    print(f"SUMMARY: {len(cards)} cards, {issues} with issues -> exit {code}")
    return code


def _display(path: Path) -> str:
    """Shorten to the '<skill>/references/<file>' tail for stable, readable output."""
    parts = path.parts
    if "references" in parts:
        i = parts.index("references")
        return "/".join(parts[max(0, i - 1):])
    return str(path)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
