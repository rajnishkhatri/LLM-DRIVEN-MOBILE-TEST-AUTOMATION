"""Ari — governed treasury assistant demo (offline-deterministic).

Hexagonal, one quantum (ADR 0001): identity gate -> deterministic stage-0
router -> stage-1 classifier fallback -> fixture-backed adapters (behind a
guarded-call wrapper) -> synthesis with a full provenance tuple.

Everything runs offline under pytest, temperature-0, with no network and no
AWS credentials. A live-Bedrock path exists behind a config toggle (ADR 0002)
and is never exercised by the gates.
"""
