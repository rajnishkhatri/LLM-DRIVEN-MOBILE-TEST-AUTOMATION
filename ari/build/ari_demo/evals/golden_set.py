"""Golden-set loader — FROZEN (HANDOVER §5.3). Parses ari/evals/golden-set.jsonl,
validates every enum against the vocabularies the 72 rows use, and exposes
dim-based selection. A typo in the file must fail loudly, not route silently.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# ari/build/ari_demo/evals/golden_set.py -> repo .../ari/evals/golden-set.jsonl
_DEFAULT_PATH = (
    Path(__file__).resolve().parents[3] / "evals" / "golden-set.jsonl"
)

# Vocabularies (eval-spec §3, §6). The loader rejects anything outside them.
INTENTS = {"data", "howto", "ticket", "out-of-scope", "action", "ambiguous"}
AMBIGUITIES = {"unambiguous", "underspecified", "ambiguous", "trap"}
ENTITLEMENTS = {"in-scope", "role-overreach", "cross-tenant"}
ADVERSARIAL = {
    "none",
    "query-injection",
    "doc-injection",
    "data-injection",
    "social-engineering",
}
TURNS = {"first", "followup", "postfailure"}
ROUTES = {"DATA", "HOWTO", "TICKET", "OUT_OF_SCOPE", "ACTION_P2"}
STAKES = {"low", "med", "high"}

_DIM_VOCAB = {
    "intent": INTENTS,
    "ambiguity": AMBIGUITIES,
    "entitlement": ENTITLEMENTS,
    "adversarial": ADVERSARIAL,
    "turn": TURNS,
}


class GoldenSetError(ValueError):
    """A malformed or out-of-vocabulary golden-set row."""


@dataclass(frozen=True)
class Row:
    id: str
    query: str
    dims: dict
    expected: dict
    stakes: str
    source: str
    context: Optional[str] = None
    persona: Optional[dict] = None
    cls: Optional[str] = None  # the row's `class` field (Python keyword)

    # ---- convenience accessors used by the gates -------------------------
    @property
    def intent(self) -> str:
        return self.dims["intent"]

    @property
    def ambiguity(self) -> str:
        return self.dims["ambiguity"]

    @property
    def entitlement(self) -> str:
        return self.dims["entitlement"]

    @property
    def adversarial(self) -> str:
        return self.dims["adversarial"]

    @property
    def turn(self) -> str:
        return self.dims["turn"]

    @property
    def expected_route(self) -> Optional[str]:
        return self.expected.get("route")

    @property
    def acceptable(self) -> Optional[list]:
        return self.expected.get("acceptable")

    @property
    def is_route_null(self) -> bool:
        return self.expected.get("route", "sentinel") is None


def _validate(row: Row) -> None:
    for dim, vocab in _DIM_VOCAB.items():
        val = row.dims.get(dim)
        if val not in vocab:
            raise GoldenSetError(
                f"{row.id}: dims.{dim}={val!r} not in {sorted(vocab)}"
            )
    if row.stakes not in STAKES:
        raise GoldenSetError(f"{row.id}: stakes={row.stakes!r} not in {sorted(STAKES)}")
    route = row.expected.get("route", "sentinel")
    if route not in (None, "sentinel") and route not in ROUTES:
        raise GoldenSetError(f"{row.id}: expected.route={route!r} not in {sorted(ROUTES)}")
    if route is None and not row.acceptable:
        raise GoldenSetError(f"{row.id}: route-null row must carry an `acceptable` set")
    for acc in row.acceptable or []:
        if acc not in ROUTES:
            raise GoldenSetError(f"{row.id}: acceptable route {acc!r} not in {sorted(ROUTES)}")


def load_golden_set(path: Optional[Path] = None) -> list[Row]:
    """Parse + validate every row. Raises GoldenSetError on the first defect."""
    src = Path(path) if path else _DEFAULT_PATH
    rows: list[Row] = []
    for i, line in enumerate(src.read_text().splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise GoldenSetError(f"line {i}: invalid JSON: {exc}") from exc
        row = Row(
            id=obj["id"],
            query=obj["query"],
            dims=obj["dims"],
            expected=obj["expected"],
            stakes=obj["stakes"],
            source=obj["source"],
            context=obj.get("context"),
            persona=obj.get("persona"),
            cls=obj.get("class"),
        )
        _validate(row)
        rows.append(row)
    if not rows:
        raise GoldenSetError(f"no rows loaded from {src}")
    return rows


def select(rows: list[Row], **dims) -> list[Row]:
    """Filter rows by dim equality, e.g. select(rows, intent='data').

    Special keys: `route_null=True/False`, `cls='F3'`.
    """
    out = rows
    route_null = dims.pop("route_null", None)
    cls = dims.pop("cls", None)
    if route_null is not None:
        out = [r for r in out if r.is_route_null == route_null]
    if cls is not None:
        out = [r for r in out if r.cls == cls]
    for dim, val in dims.items():
        out = [r for r in out if r.dims.get(dim) == val]
    return out
