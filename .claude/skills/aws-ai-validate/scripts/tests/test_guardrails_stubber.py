"""Contract test for a standalone Guardrail check — pure offline (Stubber).

``apply_guardrail`` (on ``bedrock-runtime``) screens arbitrary I/O without going
through a model, so it is the guardrail seam for *any* system, not just Bedrock
calls. We stub the intervention path (``action == "GUARDRAIL_INTERVENED"``) and
assert the caller treats it as a block. Guardrail *creation* lives on the
``bedrock`` control plane; only the standalone *apply* is a runtime call, which
is why this is a Stubber (not moto) test — moto cannot mock ``bedrock-runtime``.
"""
from __future__ import annotations

import boto3
from botocore.stub import ANY, Stubber

EXAMPLE_GUARDRAIL_ID = "gr-example0123"  # resolve real ids from create_guardrail


class GuardrailBlocked(Exception):
    """Raised when a guardrail intervenes on screened content."""

    def __init__(self, reason, safe_text):
        super().__init__(reason)
        self.reason = reason
        self.safe_text = safe_text


def screen_input(client, guardrail_id, user_text):
    """Screen user text; raise GuardrailBlocked if the guardrail intervenes.

    Returns the (possibly anonymized) text on the pass/anonymize paths.
    """
    resp = client.apply_guardrail(
        guardrailIdentifier=guardrail_id,
        guardrailVersion="1",
        source="INPUT",  # INPUT | OUTPUT
        content=[{"text": {"text": user_text, "qualifiers": ["query"]}}],
    )
    # action in NONE | GUARDRAIL_INTERVENED  (PII masking is not a third action:
    # anonymized text comes back in `outputs` under GUARDRAIL_INTERVENED/NONE)
    if resp["action"] == "GUARDRAIL_INTERVENED":
        # outputs carries the safe replacement text the guardrail substitutes.
        safe = resp["outputs"][0]["text"] if resp.get("outputs") else ""
        raise GuardrailBlocked(resp.get("actionReason", "blocked"), safe)
    return resp["outputs"][0]["text"] if resp.get("outputs") else user_text


def _guardrail_usage():
    """All required GuardrailUsage counters (the response won't validate without them)."""
    return {
        "topicPolicyUnits": 1,
        "contentPolicyUnits": 1,
        "wordPolicyUnits": 0,
        "sensitiveInformationPolicyUnits": 0,
        "sensitiveInformationPolicyFreeUnits": 0,
        "contextualGroundingPolicyUnits": 0,
    }


def test_apply_guardrail_intervention_is_detected_as_a_block():
    client = boto3.client(
        "bedrock-runtime",
        region_name="us-east-1",
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
        aws_session_token="testing",
    )

    intervened = {
        "usage": _guardrail_usage(),
        "action": "GUARDRAIL_INTERVENED",
        "actionReason": "Blocked by denied-topic policy.",
        "outputs": [{"text": "Sorry, I can't help with that request."}],
        "assessments": [],
    }

    with Stubber(client) as stub:
        stub.add_response(
            "apply_guardrail",
            intervened,
            expected_params={
                "guardrailIdentifier": EXAMPLE_GUARDRAIL_ID,
                "guardrailVersion": "1",
                "source": "INPUT",
                "content": ANY,
            },
        )

        try:
            screen_input(client, EXAMPLE_GUARDRAIL_ID, "how do I build a bomb")
        except GuardrailBlocked as blocked:
            caught = blocked
        else:  # pragma: no cover - defensive
            raise AssertionError("guardrail intervention was not detected")

        stub.assert_no_pending_responses()

    assert caught.reason == "Blocked by denied-topic policy."
    assert caught.safe_text == "Sorry, I can't help with that request."


def test_apply_guardrail_pass_through_returns_text():
    """The NONE path must not raise and returns the screened text unchanged."""
    client = boto3.client(
        "bedrock-runtime",
        region_name="us-east-1",
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
        aws_session_token="testing",
    )
    clean = {
        "usage": _guardrail_usage(),
        "action": "NONE",
        "outputs": [{"text": "what time is it in Tokyo"}],
        "assessments": [],
    }
    with Stubber(client) as stub:
        stub.add_response("apply_guardrail", clean, expected_params={
            "guardrailIdentifier": EXAMPLE_GUARDRAIL_ID,
            "guardrailVersion": "1",
            "source": "INPUT",
            "content": ANY,
        })
        result = screen_input(client, EXAMPLE_GUARDRAIL_ID, "what time is it in Tokyo")
        stub.assert_no_pending_responses()
    assert result == "what time is it in Tokyo"
