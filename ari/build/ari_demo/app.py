"""Composition root + CLI — WAVE 2 (stub).

Wires the pipeline: identity gate -> entitlement pre-check -> stage-0 router
-> (stage-1 classifier fallback) -> adapter via the guarded wrapper -> synthesis
-> decision log. Builds the provenance tuple end to end (gate 11) and proves the
injection canaries are inert across router+adapter+synthesis (gate 7).

CLI: python -m ari_demo "question" --persona treasurer [--inject-timeout]
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .domain.types import AriResponse, RequestContext


class Pipeline:
    """The wired Ari pipeline. `handle` runs one turn end to end."""

    def __init__(self, *, decision_log_path: Optional[Path] = None, **wiring):
        self._wiring = wiring
        self._decision_log_path = decision_log_path

    def handle(
        self,
        query: str,
        ctx: RequestContext,
        *,
        inject_timeout: bool = False,
    ) -> AriResponse:
        raise NotImplementedError("wave 2: wire gate->router->adapter->synthesis")


def build_pipeline(
    *,
    persona: str = "treasurer",
    decision_log_path: Optional[Path] = None,
    inject_timeout: bool = False,
) -> Pipeline:
    """Assemble a Pipeline with the offline adapters/model. `persona` selects a
    default RequestContext helper for the CLI; gates pass ctx explicitly."""
    raise NotImplementedError("wave 2: construct offline pipeline")


def main(argv: Optional[list[str]] = None) -> int:
    raise NotImplementedError("wave 2: tiny CLI for the live panel demo")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
