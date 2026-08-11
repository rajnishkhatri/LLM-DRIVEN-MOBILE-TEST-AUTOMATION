"""Path-independent artifact loading.

Artifacts are resolved by their `artifact_type` content field, never by
filename or path — the property CHK-SELF's temp-copy stability rests on.

Target-directory convention (kernel/docs/corpus-guide.md):
- root-level *.json files are kernel artifacts (expect.json / invocation.json
  are case metadata, not artifacts);
- root-level *.ndjson files are stage ledgers, one artifact per line;
- files in subdirectories are data (referenced by artifact refs), not artifacts.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

KNOWN_TYPES = (
    "role_registry",
    "handoff_contract",
    "stage_ledger_entry",
    "gate_outcome",
    "debug_report",
    "invocation_descriptor_set",
    "speckit_mapping",
    "kernel_config",
    "kata_preregistration",
    "kata_workload",
    "kata_plan",
    "kata_results",
    "kata_verdict",
)

SCHEMA_FILES = {
    "role_registry": "role-registry.schema.json",
    "handoff_contract": "handoff-contract.schema.json",
    "stage_ledger_entry": "stage-ledger-entry.schema.json",
    "gate_outcome": "gate-outcome.schema.json",
    "debug_report": "debug-report.schema.json",
    "invocation_descriptor_set": "invocation-descriptor.schema.json",
    "speckit_mapping": "speckit-mapping.schema.json",
    "kernel_config": "kernel-config.schema.json",
    "kata_preregistration": "kata-preregistration.schema.json",
    "kata_workload": "kata-workload.schema.json",
    "kata_plan": "kata-plan.schema.json",
    "kata_results": "kata-results.schema.json",
    "kata_verdict": "kata-verdict.schema.json",
}

NON_ARTIFACT_NAMES = {"expect.json", "invocation.json"}


@dataclass
class Artifact:
    label: str
    data: Any
    atype: str | None
    parse_error: bool
    raw: bytes | None = None  # exact line bytes for ledger lines (CHK-CHAIN)


@dataclass
class Context:
    root: Path
    kernel_dir: Path
    artifacts: list[Artifact]
    schemas: dict[str, dict]
    config: dict | None
    registry_data: dict | None
    ledgers: list[tuple[str, list[Artifact]]] = field(default_factory=list)
    config_digest: str | None = None
    registry_digest: str | None = None


def load_schemas(kernel_dir: Path) -> dict[str, dict]:
    schemas: dict[str, dict] = {}
    for atype, fname in SCHEMA_FILES.items():
        path = kernel_dir / "schemas" / fname
        schemas[atype] = json.loads(path.read_text(encoding="utf-8"))
    return schemas


def _parse_artifact(label: str, text: str) -> Artifact:
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return Artifact(label, None, None, True)
    atype = data.get("artifact_type") if isinstance(data, dict) else None
    if atype not in KNOWN_TYPES:
        atype = None
    return Artifact(label, data, atype, False)


def _load_file(path: Path, label: str) -> list[Artifact]:
    if path.suffix == ".ndjson":
        out = []
        raw_lines = path.read_bytes().split(b"\n")
        for i, raw in enumerate(raw_lines):
            if raw.strip():
                art = _parse_artifact(f"{label}#L{i + 1}", raw.decode("utf-8"))
                art.raw = raw
                out.append(art)
        return out
    return [_parse_artifact(label, path.read_text(encoding="utf-8"))]


def load_target(target: Path) -> tuple[Path, list[Artifact], list[tuple[str, list[Artifact]]]]:
    if target.is_file():
        loaded = _load_file(target, target.name)
        ledgers = [(target.name, loaded)] if target.suffix == ".ndjson" else []
        return target.parent, loaded, ledgers
    artifacts: list[Artifact] = []
    ledgers: list[tuple[str, list[Artifact]]] = []
    for name in sorted(p.name for p in target.iterdir()):
        path = target / name
        if not path.is_file() or name in NON_ARTIFACT_NAMES:
            continue
        if path.suffix in (".json", ".ndjson"):
            loaded = _load_file(path, name)
            artifacts.extend(loaded)
            if path.suffix == ".ndjson":
                ledgers.append((name, loaded))
    return target, artifacts, ledgers


def _canonical(kernel_dir: Path, subdir: str, fname: str) -> dict | None:
    path = kernel_dir / "corpus" / "valid" / subdir / fname
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError):
        return None


def _resolve_source(
    root: Path,
    artifacts: list[Artifact],
    atype: str,
    kernel_dir: Path,
    subdir: str,
    fname: str,
) -> tuple[dict | None, str | None]:
    """Return (data, sha256-of-source-file-bytes) for the active config/registry.
    Digest anchoring (CHK-GENESIS/CHK-THRESH item-2) needs the file digest, so
    the source file is located: target-local root file first, canonical last."""
    local = next(
        (a for a in artifacts if a.atype == atype and not a.parse_error and "#" not in a.label),
        None,
    )
    if local is not None:
        path = root / local.label
        digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        return local.data, digest
    path = kernel_dir / "corpus" / "valid" / subdir / fname
    if path.is_file():
        data = _canonical(kernel_dir, subdir, fname)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return data, digest
    return None, None


def build_context(target: Path, kernel_dir: Path) -> Context:
    root, artifacts, ledgers = load_target(target)
    schemas = load_schemas(kernel_dir)
    config, config_digest = _resolve_source(
        root, artifacts, "kernel_config", kernel_dir, "KernelConfig", "kernel-config.json"
    )
    registry_data, registry_digest = _resolve_source(
        root, artifacts, "role_registry", kernel_dir, "RoleRegistry", "role-registry.json"
    )
    return Context(
        root=root,
        kernel_dir=kernel_dir,
        artifacts=artifacts,
        schemas=schemas,
        config=config,
        registry_data=registry_data,
        ledgers=ledgers,
        config_digest=config_digest,
        registry_digest=registry_digest,
    )
