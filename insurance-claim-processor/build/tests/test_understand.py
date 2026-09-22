from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.understand import (
    MAX_IMAGE_BYTES,
    OversizeDocumentError,
    to_content_blocks,
)

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"


class UnderstandTests(unittest.TestCase):
    def test_image_bytes_become_image_content_block(self) -> None:
        payload = PNG_MAGIC + b"\x00" * 16
        blocks = to_content_blocks(payload)
        self.assertEqual(len(blocks), 1)
        image = blocks[0]["image"]
        self.assertEqual(image["format"], "png")
        self.assertEqual(image["source"]["bytes"], payload)

    def test_text_becomes_text_block(self) -> None:
        blocks = to_content_blocks("claimant hit a pole")
        self.assertEqual(blocks, [{"text": "claimant hit a pole"}])

    def test_text_bytes_become_text_block(self) -> None:
        blocks = to_content_blocks(b"plain claim text")
        self.assertEqual(blocks, [{"text": "plain claim text"}])

    def test_jpeg_magic_sets_format(self) -> None:
        payload = JPEG_MAGIC + b"\x00" * 8
        blocks = to_content_blocks(payload)
        self.assertEqual(blocks[0]["image"]["format"], "jpeg")
        self.assertEqual(blocks[0]["image"]["source"]["bytes"], payload)

    def test_media_type_detects_image_without_magic(self) -> None:
        payload = b"not-magic-but-declared"
        blocks = to_content_blocks(payload, media_type="image/gif")
        self.assertEqual(blocks[0]["image"]["format"], "gif")
        self.assertEqual(blocks[0]["image"]["source"]["bytes"], payload)

    def test_filename_detects_image_without_magic(self) -> None:
        payload = b"opaque-webp-bytes"
        blocks = to_content_blocks(payload, filename="damage.webp")
        self.assertEqual(blocks[0]["image"]["format"], "webp")

    def test_oversize_image_rejected(self) -> None:
        payload = PNG_MAGIC + b"\x00" * 64
        with self.assertRaises(OversizeDocumentError) as ctx:
            to_content_blocks(payload, max_bytes=len(payload) - 1)
        self.assertIsInstance(ctx.exception, ValueError)

    def test_text_not_bounded_by_image_cap(self) -> None:
        text = "x" * 100
        blocks = to_content_blocks(text, max_bytes=10)
        self.assertEqual(blocks, [{"text": text}])

    def test_max_image_bytes_is_five_mib(self) -> None:
        self.assertEqual(MAX_IMAGE_BYTES, 5_242_880)

    def test_default_cap_rejects_image_one_byte_over(self) -> None:
        payload = PNG_MAGIC + b"\x00" * (MAX_IMAGE_BYTES - len(PNG_MAGIC) + 1)
        self.assertEqual(len(payload), MAX_IMAGE_BYTES + 1)
        with self.assertRaises(OversizeDocumentError):
            to_content_blocks(payload)

    def test_non_image_non_utf8_does_not_unicode_decode_error(self) -> None:
        payload = b"\x00\x01\x02\x03\xff\xfe binary-not-utf8"
        try:
            blocks = to_content_blocks(payload)
        except UnicodeDecodeError:
            self.fail("non-image binary must not raise UnicodeDecodeError")
        self.assertEqual(len(blocks), 1)
        self.assertIn("text", blocks[0])
        self.assertIsInstance(blocks[0]["text"], str)


if __name__ == "__main__":
    unittest.main()
