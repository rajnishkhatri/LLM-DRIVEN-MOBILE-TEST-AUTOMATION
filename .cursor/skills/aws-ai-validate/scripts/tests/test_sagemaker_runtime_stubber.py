"""Contract test for a SageMaker real-time endpoint invocation — offline.

``sagemaker-runtime.invoke_endpoint`` returns its payload as a streaming ``Body``
blob. moto *can* mock this operation, but a Stubber contract test pins the exact
parse path — wrap the endpoint's JSON body in a ``StreamingBody`` and prove the
caller reads and decodes it — without standing up a moto backend. This is the
runtime half of the SageMaker story; the control plane (create_model / pipelines)
is exercised by the moto test.
"""
from __future__ import annotations

import io
import json

import boto3
from botocore.response import StreamingBody
from botocore.stub import ANY, Stubber

EXAMPLE_ENDPOINT = "sentiment-classifier-example"


def invoke_json_endpoint(client, endpoint_name, payload):
    """Invoke a JSON-in/JSON-out real-time endpoint and return the parsed body."""
    body = json.dumps(payload).encode("utf-8")
    resp = client.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType="application/json",
        Accept="application/json",
        Body=body,
    )
    # Body is a botocore StreamingBody — must be .read() then decoded, exactly
    # once. This is the parse contract the test locks in.
    return json.loads(resp["Body"].read().decode("utf-8"))


def _streaming_body(raw: bytes) -> StreamingBody:
    return StreamingBody(io.BytesIO(raw), len(raw))


def test_invoke_endpoint_body_stream_is_parsed():
    client = boto3.client(
        "sagemaker-runtime",
        region_name="us-east-1",
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
        aws_session_token="testing",
    )

    predicted = {"label": "POSITIVE", "score": 0.987}
    response_bytes = json.dumps(predicted).encode("utf-8")

    with Stubber(client) as stub:
        stub.add_response(
            "invoke_endpoint",
            {"Body": _streaming_body(response_bytes), "ContentType": "application/json"},
            expected_params={
                "EndpointName": EXAMPLE_ENDPOINT,
                "ContentType": "application/json",
                "Accept": "application/json",
                "Body": ANY,
            },
        )

        result = invoke_json_endpoint(
            client, EXAMPLE_ENDPOINT, {"inputs": "I love this product"}
        )

        stub.assert_no_pending_responses()

    assert result == {"label": "POSITIVE", "score": 0.987}
    assert result["label"] == "POSITIVE"
