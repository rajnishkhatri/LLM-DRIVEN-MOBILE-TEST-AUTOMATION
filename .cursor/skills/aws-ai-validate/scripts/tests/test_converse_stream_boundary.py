"""Boundary-fake test for ``converse_stream``.

The Converse *streaming* response is a botocore ``EventStream``, which the
``Stubber`` does not model cleanly (it validates discrete response shapes, not an
event iterator). The robust offline pattern is a **boundary fake**: replace the
client's ``converse_stream`` method with one that returns a canned event iterator,
then assert that your streaming-consumption code assembles the text and stop
reason correctly. This tests *your* code — the part that can actually be wrong —
without a real call and without over-fitting to botocore's internal EventStream.

Pairs with the non-streaming ``test_bedrock_converse_stubber`` (Stubber) — use the
Stubber for the request/response contract, this boundary fake for the stream
consumer.
"""
import boto3


def collect_stream_text(brt, model_id, messages):
    """Code under test: consume a Converse stream into (text, stop_reason)."""
    resp = brt.converse_stream(modelId=model_id, messages=messages)
    text_parts, stop_reason = [], None
    for event in resp["stream"]:
        if "contentBlockDelta" in event:
            delta = event["contentBlockDelta"]["delta"]
            if "text" in delta:
                text_parts.append(delta["text"])
        elif "messageStop" in event:
            stop_reason = event["messageStop"]["stopReason"]
    return "".join(text_parts), stop_reason


class _FakeConverseStream:
    """Mimics botocore's converse_stream return: {"stream": <event iterator>, ...}."""

    def __init__(self, events):
        self._events = events

    def __call__(self, **kwargs):
        return {"stream": iter(self._events),
                "ResponseMetadata": {"HTTPStatusCode": 200}}


def test_converse_stream_boundary_assembles_text(monkeypatch):
    brt = boto3.client("bedrock-runtime", region_name="us-east-1")
    events = [
        {"messageStart": {"role": "assistant"}},
        {"contentBlockDelta": {"delta": {"text": "Hello"}, "contentBlockIndex": 0}},
        {"contentBlockDelta": {"delta": {"text": ", world"}, "contentBlockIndex": 0}},
        {"contentBlockStop": {"contentBlockIndex": 0}},
        {"messageStop": {"stopReason": "end_turn"}},
        {"metadata": {"usage": {"inputTokens": 10, "outputTokens": 3}}},
    ]
    # Replace the client method at the boundary — no network, no credentials.
    monkeypatch.setattr(brt, "converse_stream", _FakeConverseStream(events))

    text, stop = collect_stream_text(
        brt, "us.anthropic.example-model-v1:0",
        [{"role": "user", "content": [{"text": "hi"}]}],
    )
    assert text == "Hello, world"
    assert stop == "end_turn"
