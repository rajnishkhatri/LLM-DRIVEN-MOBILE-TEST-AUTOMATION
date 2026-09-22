"""Detect image vs text and shape Converse content blocks.

Detection only — no Bedrock call, no image library. Size is bounded by
bytes (AC-D3 / ADR 0006), not pixels.
"""

from __future__ import annotations

MAX_IMAGE_BYTES = 5_242_880  # 5 MiB — ingest cap (AC-D3 / ADR 0006)

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_JPEG_MAGIC = b"\xff\xd8\xff"
_GIF_MAGICS = (b"GIF87a", b"GIF89a")
_WEBP_RIFF = b"RIFF"
_WEBP_TAG = b"WEBP"

_MEDIA_TYPE_FORMATS = {
    "image/png": "png",
    "image/jpeg": "jpeg",
    "image/jpg": "jpeg",
    "image/gif": "gif",
    "image/webp": "webp",
}

_SUFFIX_FORMATS = {
    ".png": "png",
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
    ".gif": "gif",
    ".webp": "webp",
}


class OversizeDocumentError(ValueError):
    """Image payload exceeds max_bytes."""


def to_content_blocks(
    payload: bytes | str,
    *,
    media_type: str | None = None,
    filename: str | None = None,
    max_bytes: int = MAX_IMAGE_BYTES,
) -> list[dict]:
    """Detect image vs text → Converse content blocks.

    Text  → [{"text": <str>}]
    Image → [{"image": {"format": "png"|"jpeg"|"gif"|"webp",
                        "source": {"bytes": <bytes>}}}]
    Oversize image → raise OversizeDocumentError.
    """
    if isinstance(payload, str):
        return [{"text": payload}]

    fmt = _detect_image_format(payload, media_type=media_type, filename=filename)
    if fmt is None:
        return [{"text": payload.decode("utf-8", errors="replace")}]

    if len(payload) > max_bytes:
        raise OversizeDocumentError(
            f"image payload is {len(payload)} bytes; max_bytes={max_bytes}"
        )
    return [{"image": {"format": fmt, "source": {"bytes": payload}}}]


def _detect_image_format(
    payload: bytes,
    *,
    media_type: str | None,
    filename: str | None,
) -> str | None:
    magic = _format_from_magic(payload)
    if magic is not None:
        return magic
    hinted = _format_from_media_type(media_type)
    if hinted is not None:
        return hinted
    return _format_from_filename(filename)


def _format_from_magic(payload: bytes) -> str | None:
    if payload.startswith(_PNG_MAGIC):
        return "png"
    if payload.startswith(_JPEG_MAGIC):
        return "jpeg"
    if payload.startswith(_GIF_MAGICS):
        return "gif"
    if (
        len(payload) >= 12
        and payload.startswith(_WEBP_RIFF)
        and payload[8:12] == _WEBP_TAG
    ):
        return "webp"
    return None


def _format_from_media_type(media_type: str | None) -> str | None:
    if media_type is None:
        return None
    token = media_type.split(";", 1)[0].strip().lower()
    return _MEDIA_TYPE_FORMATS.get(token)


def _format_from_filename(filename: str | None) -> str | None:
    if filename is None:
        return None
    name = filename.lower()
    for suffix, fmt in _SUFFIX_FORMATS.items():
        if name.endswith(suffix):
            return fmt
    return None
