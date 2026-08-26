"""Contract test for the Bedrock Converse *tool-use loop* — pure offline.

`moto` cannot mock `bedrock-runtime`, so `botocore.stub.Stubber` is the only
pure-unit path for Bedrock inference. We stub two ``converse`` responses that
walk the real tool-use handshake:

  1. first response  -> ``stopReason == "tool_use"`` carrying a ``toolUse`` block
  2. second response -> ``stopReason == "end_turn"`` with the final text

and drive a tiny loop that must (a) echo the assistant turn back verbatim,
(b) build a ``toolResult`` block whose ``toolUseId`` matches the model's
``toolUseId``, and (c) terminate on the final text. This proves the *shape* of
the loop from research-2026.md §1.3 without a single network call.

Deliberately NOT tested here: the legacy ``\\n\\nHuman:``/``max_tokens_to_sample``
+ ``response["completion"]`` text-completions format (the real correctness bug in
cases/aws-ai/ch09.md:686). The Converse API is the only model-access path this
family emits.
"""
from __future__ import annotations

import boto3
from botocore.config import Config
from botocore.stub import ANY, Stubber

# Example id only — resolve real ids at runtime via list_foundation_models /
# list_inference_profiles (the ``us.`` prefix marks a cross-region inference
# profile). Never treat a hard-coded id as permanent; models drift monthly.
EXAMPLE_MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

TOOL_CONFIG = {
    "tools": [
        {
            "toolSpec": {
                "name": "get_weather",
                "description": "Get the current weather for a city.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {"city": {"type": "string"}},
                        "required": ["city"],
                    }
                },
            }
        }
    ],
    "toolChoice": {"auto": {}},
}


def _converse_response(content_blocks, stop_reason):
    """A minimal-but-valid ConverseResponse (all required members present)."""
    return {
        "output": {"message": {"role": "assistant", "content": content_blocks}},
        "stopReason": stop_reason,
        "usage": {"inputTokens": 42, "outputTokens": 12, "totalTokens": 54},
        "metrics": {"latencyMs": 123},
    }


def run_tool_use_loop(client, model_id, tool_config, user_text, tool_impl, max_turns=6):
    """Drive Converse until ``stopReason == "end_turn"``.

    Returns ``(final_text, tool_results)`` where ``tool_results`` is the list of
    ``toolResult`` blocks this loop constructed — the artifact the assertions
    inspect to prove the ``toolUseId`` was echoed correctly.
    """
    messages = [{"role": "user", "content": [{"text": user_text}]}]
    constructed_tool_results = []

    for _ in range(max_turns):
        # Always exactly these three kwargs — keeps the Stubber expected_params
        # key-set stable across both turns.
        resp = client.converse(
            modelId=model_id, messages=messages, toolConfig=tool_config
        )
        assistant_msg = resp["output"]["message"]
        # 1) Echo the assistant turn back VERBATIM before any toolResult, or the
        #    next request fails validation (research-2026.md §1.3).
        messages.append(assistant_msg)

        if resp["stopReason"] != "tool_use":
            final_text = next(
                b["text"] for b in assistant_msg["content"] if "text" in b
            )
            return final_text, constructed_tool_results

        # 2) One toolResult per toolUse block, echoing the toolUseId. A turn may
        #    carry several toolUse blocks; content is a LIST of blocks, never a
        #    bare string.
        tool_result_blocks = []
        for block in assistant_msg["content"]:
            if "toolUse" not in block:
                continue
            tu = block["toolUse"]  # tu["input"] is already a parsed dict
            output = tool_impl(tu["name"], tu["input"])
            tr = {
                "toolResult": {
                    "toolUseId": tu["toolUseId"],
                    "content": [{"json": output}],
                    "status": "success",
                }
            }
            tool_result_blocks.append(tr)
            constructed_tool_results.append(tr["toolResult"])

        messages.append({"role": "user", "content": tool_result_blocks})

    raise AssertionError("tool-use loop did not terminate within max_turns")


def test_converse_tool_use_loop_terminates_and_echoes_tool_use_id():
    client = boto3.client(
        "bedrock-runtime",
        region_name="us-east-1",
        config=Config(retries={"max_attempts": 1}),
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
        aws_session_token="testing",
    )

    tool_use_id = "tooluse_9aF3-example-id"
    first = _converse_response(
        [
            {"text": "Let me check the weather."},
            {
                "toolUse": {
                    "toolUseId": tool_use_id,
                    "name": "get_weather",
                    "input": {"city": "Paris"},
                }
            },
        ],
        stop_reason="tool_use",
    )
    final = _converse_response(
        [{"text": "It is 18 degrees C and clear in Paris."}],
        stop_reason="end_turn",
    )

    calls = {"count": 0}

    def tool_impl(name, tool_input):
        calls["count"] += 1
        assert name == "get_weather"
        assert tool_input == {"city": "Paris"}  # already a dict, no json.loads
        return {"tempC": 18, "condition": "clear"}

    with Stubber(client) as stub:
        # Real operation name "converse"; modelId asserted, the drifting
        # messages/toolConfig payloads matched with ANY.
        stub.add_response(
            "converse",
            first,
            expected_params={
                "modelId": EXAMPLE_MODEL_ID,
                "messages": ANY,
                "toolConfig": ANY,
            },
        )
        stub.add_response(
            "converse",
            final,
            expected_params={
                "modelId": EXAMPLE_MODEL_ID,
                "messages": ANY,
                "toolConfig": ANY,
            },
        )

        final_text, tool_results = run_tool_use_loop(
            client, EXAMPLE_MODEL_ID, TOOL_CONFIG, "What is the weather in Paris?", tool_impl
        )

        # Both stubbed responses were consumed — the loop made exactly 2 calls.
        stub.assert_no_pending_responses()

    assert final_text == "It is 18 degrees C and clear in Paris."
    assert calls["count"] == 1, "the tool should have run exactly once"
    assert len(tool_results) == 1
    # The load-bearing assertion: the toolResult echoes the model's toolUseId.
    assert tool_results[0]["toolUseId"] == tool_use_id
    assert tool_results[0]["content"] == [{"json": {"tempC": 18, "condition": "clear"}}]
    assert tool_results[0]["status"] == "success"
