"""Shared fixtures — FROZEN wave-0. Builds RequestContext DIRECTLY (a frozen
domain type) rather than through the identity gate, so workers B and C do not
depend on worker A's gate() stub. Only gate 12 exercises gate() itself.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from ari_demo.domain import tokens
from ari_demo.domain.types import RequestContext
from ari_demo.evals.golden_set import load_golden_set

BUILD_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = BUILD_ROOT / "fixtures"


@pytest.fixture(scope="session")
def golden():
    return load_golden_set()


@pytest.fixture
def treasurer_ctx() -> RequestContext:
    return RequestContext(
        user="treasurer@Meridian Foods",
        tenant="Meridian Foods",
        role="treasurer",
        conversation_id="conv-demo",
        turn_id="t1",
    )


@pytest.fixture
def junior_ctx() -> RequestContext:
    return RequestContext(
        user="analyst@Meridian Foods",
        tenant="Meridian Foods",
        role="junior-analyst",
        conversation_id="conv-demo",
        turn_id="t1",
    )


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def tmp_jira(tmp_path) -> Path:
    """A writable copy of the Jira seed so the committed fixture never mutates."""
    dst = tmp_path / "jira_store.json"
    shutil.copy(FIXTURES / "jira_store.json", dst)
    return dst


@pytest.fixture
def mint():
    """Factory for signed tokens (gate 12)."""
    def _mint(role="treasurer", tenant="Meridian Foods", user=None,
              conversation_id="conv-demo", turn_id="t1") -> str:
        return tokens.mint_token(user or f"{role}@{tenant}", tenant, role,
                                 conversation_id, turn_id)
    return _mint


def ctx_for(row) -> RequestContext:
    """Persona-aware RequestContext for a golden row (wave-2 gates 7/11)."""
    persona = row.persona or {}
    tenant = persona.get("tenant", "Meridian Foods")
    role = persona.get("role", "treasurer")
    return RequestContext(
        user=f"{role}@{tenant}", tenant=tenant, role=role,
        conversation_id="conv-demo", turn_id=row.id,
    )


@pytest.fixture
def pipeline():
    """The wired pipeline (wave 2). Raises NotImplementedError until wave 2 —
    only gates 7 and 11 request it, and only pass after the merge."""
    from ari_demo.app import build_pipeline
    return build_pipeline(decision_log_path=None)
