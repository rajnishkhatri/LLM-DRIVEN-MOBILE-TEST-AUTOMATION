#!/usr/bin/env python3
"""Desaturate a rendered PNG into a grayscale legibility proof.

Colour is never the only channel in these diagrams (rule 5): every family is
paired with a shape and/or a text tag, so the set must stay fully readable
printed in grayscale. This script produces the proof image the linter checks
for and the self-audit attaches.

Pillow only (no ImageMagick dependency), so the whole tooling stays one
language and one install. Usage:
    python3 grayscale_proof.py IN.png OUT-gray.png
"""
import sys
from pathlib import Path

from PIL import Image


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: grayscale_proof.py IN.png OUT-gray.png")
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    if not src.exists():
        sys.exit(f"grayscale_proof: input not found: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    # Convert via luminance ("L"), then back to RGB so the proof drops into any
    # viewer/report that expects a colour image but shows no colour.
    Image.open(src).convert("L").convert("RGB").save(dst)
    print(f"grayscale proof -> {dst}")


if __name__ == "__main__":
    main()
