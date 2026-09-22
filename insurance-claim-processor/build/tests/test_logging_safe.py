from __future__ import annotations

import logging
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.logging_safe import get_logger, redact

# Same stand-in SSN as the auto sample packet and validator tests (AC-H1).
_SSN = "078-05-1120"
# 16-digit PAN stand-in matching validator / logging_safe _PAN (AC-H1 / C-01).
_PAN = "4111111111111111"
_PACKET = (
    "Wait, the claimant also listed SSN 078-05-1120 on a handwritten intake "
    "sheet — do not copy that into the summary."
)
_RESERVED_RECORD_KEYS = frozenset(logging.makeLogRecord({}).__dict__)


class _CaptureHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        parts = [self.format(record)]
        for key, value in record.__dict__.items():
            if key not in _RESERVED_RECORD_KEYS:
                parts.append(f"{key}={value!s}")
        self.messages.append("\n".join(parts))


class LoggingSafeTests(unittest.TestCase):
    def _emit(self, logger_name: str, emit) -> str:
        logger = get_logger(logger_name)
        handler = _CaptureHandler()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        try:
            emit(logger)
        finally:
            logger.removeHandler(handler)
        captured = "\n".join(handler.messages)
        self.assertTrue(captured, "expected the logger to emit a record")
        return captured

    def test_redact_strips_ssn_from_packet(self) -> None:
        self.assertIn(_SSN, _PACKET)
        self.assertNotIn(_SSN, redact(_PACKET))

    def test_redact_strips_pan_stand_in(self) -> None:
        self.assertNotIn(_PAN, redact(f"card {_PAN}"))

    def test_ssn_packet_absent_from_captured_logs(self) -> None:
        captured = self._emit(
            "claim_processor.logging_safe.test",
            lambda logger: logger.info("processing packet: %s", _PACKET),
        )
        self.assertNotIn(_SSN, captured)

    def test_ssn_absent_from_extra(self) -> None:
        captured = self._emit(
            "claim_processor.logging_safe.extra",
            lambda logger: logger.info("processing", extra={"packet": _PACKET}),
        )
        self.assertNotIn(_SSN, captured)

    def test_ssn_absent_from_exception(self) -> None:
        def emit(logger: logging.Logger) -> None:
            try:
                raise ValueError(f"bad packet {_SSN}")
            except ValueError:
                logger.exception("processing failed")

        captured = self._emit("claim_processor.logging_safe.exc", emit)
        self.assertNotIn(_SSN, captured)

    def test_pan_absent_from_message_extra_and_exception(self) -> None:
        captured_info = self._emit(
            "claim_processor.logging_safe.pan_info",
            lambda logger: logger.info("card %s", _PAN),
        )
        captured_extra = self._emit(
            "claim_processor.logging_safe.pan_extra",
            lambda logger: logger.info("card", extra={"pan": _PAN}),
        )

        def emit_exc(logger: logging.Logger) -> None:
            try:
                raise ValueError(f"card {_PAN}")
            except ValueError:
                logger.exception("card failed")

        captured_exc = self._emit("claim_processor.logging_safe.pan_exc", emit_exc)
        for captured in (captured_info, captured_extra, captured_exc):
            self.assertNotIn(_PAN, captured)


if __name__ == "__main__":
    unittest.main()
