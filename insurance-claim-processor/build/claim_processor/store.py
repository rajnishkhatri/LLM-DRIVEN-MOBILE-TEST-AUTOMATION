from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol


class DocumentStore(Protocol):
    def get_text(self, bucket: str, key: str) -> str: ...

    def get_bytes(self, bucket: str, key: str) -> bytes: ...

    def put_json(self, bucket: str, key: str, payload: dict[str, Any]) -> None: ...


def pending_review_key(claim_key: str) -> str:
    """HITL pause object — mirror of pipeline.result_key_for → results/<key>.json."""
    return f"pending-review/{claim_key}.json"


def put_pending_review(
    store: DocumentStore, bucket: str, claim_key: str, payload: dict[str, Any]
) -> None:
    store.put_json(bucket, pending_review_key(claim_key), payload)


def get_pending_review(
    store: DocumentStore, bucket: str, claim_key: str
) -> dict[str, Any]:
    return json.loads(store.get_text(bucket, pending_review_key(claim_key)))


class LocalDocumentStore:
    """Filesystem stand-in so the PoC runs with no AWS account."""

    def __init__(self, root: Path):
        self.root = root

    def _path(self, bucket: str, key: str) -> Path:
        return self.root / bucket / key

    def get_text(self, bucket: str, key: str) -> str:
        return self._path(bucket, key).read_text(encoding="utf-8")

    def get_bytes(self, bucket: str, key: str) -> bytes:
        return self._path(bucket, key).read_bytes()

    def put_json(self, bucket: str, key: str, payload: dict[str, Any]) -> None:
        path = self._path(bucket, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class S3DocumentStore:
    """S3 Land / Record — injected client, never created at import."""

    def __init__(self, s3_client: Any):
        self._s3 = s3_client

    def get_text(self, bucket: str, key: str) -> str:
        return self.get_bytes(bucket, key).decode("utf-8")

    def get_bytes(self, bucket: str, key: str) -> bytes:
        return self._s3.get_object(Bucket=bucket, Key=key)["Body"].read()

    def put_json(self, bucket: str, key: str, payload: dict[str, Any]) -> None:
        self._s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(payload, indent=2).encode("utf-8"),
            ContentType="application/json",
        )
