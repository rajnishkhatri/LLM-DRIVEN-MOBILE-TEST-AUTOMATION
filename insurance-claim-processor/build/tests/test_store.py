from __future__ import annotations

import json
import sys
import unittest
from io import BytesIO
from pathlib import Path

import boto3
from botocore.response import StreamingBody
from botocore.stub import Stubber

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.store import S3DocumentStore


class S3StubberTests(unittest.TestCase):
    def test_get_and_put(self) -> None:
        client = boto3.client("s3", region_name="us-east-1")
        stubber = Stubber(client)
        payload = b"claim text"
        stubber.add_response(
            "get_object",
            {"Body": StreamingBody(BytesIO(payload), len(payload))},
            {"Bucket": "b", "Key": "k"},
        )
        stubber.add_response(
            "put_object",
            {},
            {
                "Bucket": "b",
                "Key": "results/k.json",
                "Body": json.dumps({"ok": True}, indent=2).encode("utf-8"),
                "ContentType": "application/json",
            },
        )
        stubber.activate()
        store = S3DocumentStore(client)
        self.assertEqual(store.get_text("b", "k"), "claim text")
        store.put_json("b", "results/k.json", {"ok": True})
        stubber.deactivate()
        stubber.assert_no_pending_responses()


if __name__ == "__main__":
    unittest.main()
