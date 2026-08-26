"""Supporting-infra tests on the moto in-memory AWS — pure offline.

moto owns the plumbing Bedrock/SageMaker agents lean on (S3 for artifacts and
async payloads, IAM for execution roles) plus the SageMaker *control* plane
(create_model, endpoints, pipelines) that a Stubber would only contract-check.
It CANNOT mock ``bedrock-runtime`` — that is the Stubber tests' job.

The SageMaker control-plane assertion is capability-gated: if the installed moto
build hasn't implemented the operation it is SKIPPED, never errored, so the
harness stays green across moto versions.
"""
from __future__ import annotations

import json

import boto3
import pytest
from botocore.exceptions import ClientError

# Skip the whole module cleanly if moto isn't installed in this environment.
pytest.importorskip("moto")
from moto import mock_aws  # noqa: E402

REGION = "us-east-1"


@pytest.fixture(autouse=True)
def _dummy_aws_credentials(monkeypatch):
    """Guarantee no real AWS is ever reached, even if moto's patch had a hole.

    Bogus static creds + a fixed region mean a stray call fails signing rather
    than hitting a real account.
    """
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", REGION)


@mock_aws
def test_s3_put_get_roundtrip():
    s3 = boto3.client("s3", region_name=REGION)
    bucket = "aws-ai-artifacts-example"
    # us-east-1 is the default region: passing a LocationConstraint here is an error.
    s3.create_bucket(Bucket=bucket)

    key = "models/eval-report.json"
    payload = json.dumps({"accuracy": 0.91, "passed": True}).encode("utf-8")
    s3.put_object(Bucket=bucket, Key=key, Body=payload)

    fetched = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    assert json.loads(fetched) == {"accuracy": 0.91, "passed": True}

    listed = s3.list_objects_v2(Bucket=bucket)
    assert [o["Key"] for o in listed.get("Contents", [])] == [key]


@mock_aws
def test_iam_execution_role_created():
    iam = boto3.client("iam", region_name=REGION)
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "sagemaker.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }
    created = iam.create_role(
        RoleName="aws-ai-exec-role-example",
        AssumeRolePolicyDocument=json.dumps(assume_role_policy),
        Description="Execution role for the offline harness example.",
    )
    arn = created["Role"]["Arn"]
    assert arn.startswith("arn:aws:iam::")
    assert arn.endswith(":role/aws-ai-exec-role-example")

    # Scope an inline policy carrying the two-ARN Bedrock trap
    # (cases/aws-ai/ch06.md:72): a bedrock exec role needs BOTH the
    # foundation-model/* AND the inference-profile/* resource or you get
    # AccessDenied when invoking via a cross-region inference profile.
    account = boto3.client("sts", region_name=REGION).get_caller_identity()["Account"]
    inline = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                "Resource": [
                    "arn:aws:bedrock:*::foundation-model/*",
                    f"arn:aws:bedrock:*:{account}:inference-profile/*",
                ],
            }
        ],
    }
    iam.put_role_policy(
        RoleName="aws-ai-exec-role-example",
        PolicyName="bedrock-invoke",
        PolicyDocument=json.dumps(inline),
    )
    fetched = iam.get_role_policy(
        RoleName="aws-ai-exec-role-example", PolicyName="bedrock-invoke"
    )
    resources = fetched["PolicyDocument"]["Statement"][0]["Resource"]
    assert any("foundation-model/" in r for r in resources)
    assert any("inference-profile/" in r for r in resources)


@mock_aws
def test_sagemaker_control_plane_create_model_if_supported():
    """SageMaker control plane via moto — SKIPPED (not errored) if unimplemented."""
    iam = boto3.client("iam", region_name=REGION)
    role = iam.create_role(
        RoleName="sm-exec-example",
        AssumeRolePolicyDocument=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "sagemaker.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }
        ),
    )["Role"]["Arn"]

    sm = boto3.client("sagemaker", region_name=REGION)
    model_name = "offline-example-model"
    try:
        sm.create_model(
            ModelName=model_name,
            ExecutionRoleArn=role,
            PrimaryContainer={
                # Example ECR image ref — never resolved offline.
                "Image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/example:latest",
                "Mode": "SingleModel",
            },
        )
        listed = sm.list_models()
    except (NotImplementedError, ClientError) as exc:
        # moto raises NotImplementedError for unimplemented ops; some surface as
        # a ClientError. Either way this is a coverage gap, not a failure.
        code = ""
        if isinstance(exc, ClientError):
            code = exc.response.get("Error", {}).get("Code", "")
        if isinstance(exc, NotImplementedError) or "NotImplemented" in code:
            pytest.skip(f"moto build lacks sagemaker create_model/list_models: {exc}")
        raise

    names = [m["ModelName"] for m in listed.get("Models", [])]
    assert model_name in names
