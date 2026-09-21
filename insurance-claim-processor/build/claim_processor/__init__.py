"""Insurance claim document PoC — Converse + RAG + validator.

Clients are dependency-injected. Nothing here calls AWS at import time.
Real AWS is opt-in via CLAIM_PROCESSOR_REAL_AWS=1 (gated aws-ai-validate).
"""

__version__ = "0.1.0"
