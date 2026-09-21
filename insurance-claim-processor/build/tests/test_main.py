from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import boto3
from botocore.stub import Stubber

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.models import EXTRACT_MODEL_EXAMPLE
from claim_processor.store import LocalDocumentStore, put_pending_review


def _without_real_aws_gate():
    env = {k: v for k, v in os.environ.items() if k != "CLAIM_PROCESSOR_REAL_AWS"}
    return patch.dict(os.environ, env, clear=True)


class DecideCliTests(unittest.TestCase):
    def test_decide_payload_is_send_task_success_with_reviewer_id(self) -> None:
        from claim_processor.__main__ import send_decision

        client = boto3.client("stepfunctions", region_name="us-east-1")
        stubber = Stubber(client)
        output = json.dumps({"decision": "approve", "reviewer_id": "examiner-1"})
        expected = {"taskToken": "tok-abc", "output": output}
        stubber.add_response("send_task_success", {}, expected)
        stubber.activate()
        payload = send_decision(
            client,
            task_token="tok-abc",
            decision="approve",
            reviewer_id="examiner-1",
        )
        stubber.deactivate()
        self.assertEqual(payload["decision"], "approve")
        self.assertEqual(payload["reviewer_id"], "examiner-1")
        self.assertNotEqual(payload["decision"], "auto_approve")

    def test_decide_correct_includes_corrections_in_payload(self) -> None:
        from claim_processor.__main__ import send_decision

        client = boto3.client("stepfunctions", region_name="us-east-1")
        stubber = Stubber(client)
        output = json.dumps(
            {
                "decision": "correct",
                "reviewer_id": "examiner-2",
                "corrections": {"policy_number": "POL-FIXED"},
            }
        )
        expected = {"taskToken": "tok-fix", "output": output}
        stubber.add_response("send_task_success", {}, expected)
        stubber.activate()
        payload = send_decision(
            client,
            task_token="tok-fix",
            decision="correct",
            reviewer_id="examiner-2",
            corrections={"policy_number": "POL-FIXED"},
        )
        stubber.deactivate()
        self.assertEqual(payload["decision"], "correct")
        self.assertEqual(payload["reviewer_id"], "examiner-2")
        self.assertEqual(payload["corrections"], {"policy_number": "POL-FIXED"})

    def test_decide_refuses_without_real_aws_gate(self) -> None:
        from claim_processor.__main__ import main

        with _without_real_aws_gate():
            with self.assertRaises(SystemExit) as ctx:
                main(
                    [
                        "decide",
                        "--task-token",
                        "tok",
                        "--decision",
                        "approve",
                        "--reviewer-id",
                        "examiner-1",
                    ]
                )
        self.assertIn("CLAIM_PROCESSOR_REAL_AWS", str(ctx.exception))

    def test_real_flag_refuses_without_gate(self) -> None:
        from claim_processor.__main__ import main

        with _without_real_aws_gate():
            with self.assertRaises(SystemExit) as ctx:
                main(["--real", "--key", "claims/auto-fl-collision.txt"])
        self.assertIn("CLAIM_PROCESSOR_REAL_AWS", str(ctx.exception))

    def test_s3_flag_still_refuses_without_gate(self) -> None:
        from claim_processor.__main__ import main

        with _without_real_aws_gate():
            with self.assertRaises(SystemExit) as ctx:
                main(["--s3", "--key", "claims/auto-fl-collision.txt"])
        self.assertIn("CLAIM_PROCESSOR_REAL_AWS", str(ctx.exception))

    def test_inspect_prints_pending_review(self) -> None:
        from claim_processor.__main__ import main

        pending = {
            "extracted_info": {"claimant_name": "A. Claimant", "claim_amount": 100.0},
            "route": "human_review",
            "validation": {"accepted": True, "flags": []},
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = LocalDocumentStore(root)
            put_pending_review(store, "work", "claims/incomplete-claim.txt", pending)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(
                    [
                        "inspect",
                        "--root",
                        str(root),
                        "--bucket",
                        "work",
                        "--key",
                        "claims/incomplete-claim.txt",
                    ]
                )
        self.assertEqual(rc, 0)
        printed = json.loads(buf.getvalue())
        self.assertEqual(printed["route"], "human_review")
        self.assertEqual(printed["extracted_info"]["claimant_name"], "A. Claimant")

    def test_cli_model_flag_beats_env_beats_example(self) -> None:
        from claim_processor.__main__ import resolve_model_id

        self.assertEqual(
            resolve_model_id(None, "CLAIM_PROCESSOR_EXTRACT_MODEL_ID", EXTRACT_MODEL_EXAMPLE),
            EXTRACT_MODEL_EXAMPLE,
        )
        with patch.dict(
            os.environ, {"CLAIM_PROCESSOR_EXTRACT_MODEL_ID": "from-env"}, clear=False
        ):
            self.assertEqual(
                resolve_model_id(
                    None, "CLAIM_PROCESSOR_EXTRACT_MODEL_ID", EXTRACT_MODEL_EXAMPLE
                ),
                "from-env",
            )
            self.assertEqual(
                resolve_model_id(
                    "from-cli",
                    "CLAIM_PROCESSOR_EXTRACT_MODEL_ID",
                    EXTRACT_MODEL_EXAMPLE,
                ),
                "from-cli",
            )


if __name__ == "__main__":
    unittest.main()
