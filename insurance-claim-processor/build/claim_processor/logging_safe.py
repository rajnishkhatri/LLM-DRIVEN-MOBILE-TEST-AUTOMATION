from __future__ import annotations

import logging
import re

# Same PII shapes the validator flags (pii_ssn / pii_pan) — AC-H1.
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_PAN = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
_REDACTED = "[REDACTED]"
_RESERVED_RECORD_KEYS = frozenset(logging.makeLogRecord({}).__dict__)


def redact(text: str) -> str:
    """Return text with raw PII patterns replaced. Does not mutate ``text``."""
    redacted = _SSN.sub(_REDACTED, text)
    return _PAN.sub(_REDACTED, redacted)


def _redact_value(value: object) -> object:
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, dict):
        return {k: _redact_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_value(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_redact_value(v) for v in value)
    return value


class _RedactFilter(logging.Filter):
    """Mutate a record so handlers only ever see redacted message / extra / exc."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except (TypeError, ValueError):
            message = str(record.msg)
        record.msg = redact(message)
        record.args = ()
        for key, value in list(record.__dict__.items()):
            if key in _RESERVED_RECORD_KEYS:
                continue
            record.__dict__[key] = _redact_value(value)
        if record.exc_info:
            exc_type, exc, tb = record.exc_info
            if exc is not None:
                record.exc_info = (
                    exc_type,
                    type(exc)(
                        *[
                            redact(arg) if isinstance(arg, str) else arg
                            for arg in exc.args
                        ]
                    ),
                    tb,
                )
        if record.exc_text:
            record.exc_text = redact(record.exc_text)
        return True


_FILTER = _RedactFilter()


def get_logger(name: str) -> logging.Logger:
    """Return a stdlib logger that emits only redacted messages."""
    logger = logging.getLogger(name)
    if not any(isinstance(existing, _RedactFilter) for existing in logger.filters):
        logger.addFilter(_FILTER)
    return logger
