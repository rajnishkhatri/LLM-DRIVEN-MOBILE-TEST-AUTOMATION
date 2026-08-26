#!/usr/bin/env python3
"""Minimal CDK v2 (Python) app — a Lambda 'Bedrock agent' with the two-ARN trap.

This renders offline with ``cdk synth`` (no Docker, no AWS account): the Lambda
uses inline code so nothing has to be bundled at synth time. Its purpose is to
encode, in real infrastructure-as-code, the single most common Bedrock IAM
mistake — granting ``bedrock:InvokeModel`` on the foundation-model ARN alone.

The trap (cases/aws-ai/ch06.md:72): a model id beginning ``us.`` is a
cross-region *inference profile*, so the execution role needs BOTH resource
types or invocation fails with an ``AccessDenied`` that does not say which
permission is missing:

  * ``arn:aws:bedrock:<region>::foundation-model/*``          (no account id)
  * ``arn:aws:bedrock:<region>:<account>:inference-profile/*`` (has account id)

Note the foundation-model ARN has an EMPTY account segment (``::``) while the
inference-profile ARN carries the account — a real, easy-to-miss asymmetry.

Production note: a real Strands/AgentCore agent's dependencies blow past Lambda's
250 MB zip limit, so ship it as a ``DockerImageFunction`` (container, 10 GB) on
ARM64 — see ch06.md:83. That container variant needs
``from aws_cdk import aws_ecr_assets as ecr_assets`` at the top alongside
``aws_lambda`` (an easy import to forget — leaving it out is a copy-paste
``NameError``). Inline code is used here only so the sample stays
offline-synthesizable. Imports are restricted to ``aws-cdk-lib`` + ``constructs``.
"""
import aws_cdk as cdk
from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_iam as iam,
    aws_lambda as lambda_,
)
from constructs import Construct

# Example id ONLY. Resolve real ids at deploy time via list_foundation_models /
# list_inference_profiles; the ``us.`` prefix marks a cross-region inference
# profile (which is exactly why the inference-profile ARN below is required).
EXAMPLE_MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

# Base foundation-model id = the profile id minus its geo prefix
# (us./eu./apac./global.) — the member model the cross-region profile routes to,
# and what the foundation-model ARN below must name.
_GEO_PREFIXES = ("us.", "eu.", "apac.", "global.")
BASE_MODEL_ID = next(
    (EXAMPLE_MODEL_ID[len(p):] for p in _GEO_PREFIXES if EXAMPLE_MODEL_ID.startswith(p)),
    EXAMPLE_MODEL_ID,
)

# Inline handler kept tiny so `cdk synth` needs no bundling. It uses the native
# Converse API — never the legacy "\n\nHuman:"/max_tokens_to_sample completion
# format (the correctness bug in cases/aws-ai/ch09.md:686).
#
# Sampling params are removed on current-generation Claude models (VERIFIED
# against the authoritative Claude API reference, 2026-08). On Bedrock Converse,
# do NOT set inferenceConfig.temperature / topP / topK for a current-gen Claude
# model: Opus 4.7+/Opus 5 and Fable 5 REMOVE them (sending any returns a 400) and
# Sonnet 5 rejects a non-default value with a 400. Omit inferenceConfig entirely,
# or pass only maxTokens (as below). They remain valid on older Claude models
# (Sonnet 4.5 / Opus 4.5 and earlier), so the guard is model-generation-specific:
# when the resolved id is a current-gen Claude, drop the sampling params. Treat
# this as a deprecated-parameter trap symmetric with the legacy completion format
# above — both silently break against current Claude models.
_HANDLER_SRC = """
import json, os
import boto3

_client = boto3.client("bedrock-runtime")  # init outside the handler (ch06.md:55)

def handler(event, _context):
    model_id = os.environ["BEDROCK_MODEL_ID"]
    prompt = (event or {}).get("prompt", "Hello from the sample agent.")
    if not isinstance(prompt, str):
        raise ValueError("prompt must be a string")
    resp = _client.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 512},  # maxTokens only — no temperature/topP/topK (see note above)
    )
    text = resp["output"]["message"]["content"][0]["text"]
    return {"statusCode": 200, "body": json.dumps({"reply": text})}
"""


class BedrockAgentStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        agent_fn = lambda_.Function(
            self,
            "BedrockAgentFn",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=lambda_.Code.from_inline(_HANDLER_SRC),
            architecture=lambda_.Architecture.ARM_64,
            memory_size=1024,
            timeout=Duration.minutes(5),
            environment={"BEDROCK_MODEL_ID": EXAMPLE_MODEL_ID},
        )

        # THE TWO-ARN TRAP, encoded in CDK. Scoped to the two Converse actions on
        # BOTH the foundation-model and inference-profile resources — never "*".
        #
        # DEFAULT: least-privilege — scope to the SPECIFIC inference-profile id and
        # its member base foundation-model. No wildcard, so cdk-nag
        # AwsSolutions-IAM5 stays quiet with nothing to suppress. Discover the full
        # cross-region member set (a us./eu./apac./global. profile routes to several
        # regions) with:
        #   aws bedrock get-inference-profile \
        #     --inference-profile-identifier us.anthropic.claude-sonnet-4-5-20250929-v1:0
        # then read models[].modelArn and add one foundation-model ARN per region.
        agent_fn.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=[
                    # foundation-model ARN: EMPTY account segment, base model id.
                    f"arn:aws:bedrock:{self.region}::foundation-model/{BASE_MODEL_ID}",
                    # inference-profile ARN: account id + the specific profile id.
                    f"arn:aws:bedrock:{self.region}:{self.account}:inference-profile/{EXAMPLE_MODEL_ID}",
                ],
            )
        )
        # VARIANT — if you rotate models often. Scope to the anthropic.* family
        # wildcard instead of a single id, and leave a REASONED audit trail for the
        # AwsSolutions-IAM5 finding the wildcard then raises (it will NOT stay quiet
        # on a "/*"):
        #     resources=[
        #         f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.*",
        #         f"arn:aws:bedrock:{self.region}:{self.account}:inference-profile/anthropic.*",
        #     ]
        #     NagSuppressions.add_resource_suppressions(
        #         agent_fn,
        #         [{"id": "AwsSolutions-IAM5",
        #           "reason": "anthropic.* invoke scope is intentional: models rotate "
        #                     "faster than deploys; still bounded to the two Converse "
        #                     "actions and the anthropic family."}],
        #         apply_to_children=True,
        #     )
        # Lazy shortcut (NOT recommended): resources=["*"] — prefer the
        # least-privilege two-ARN grant above.

        # IAM-authenticated invoke surface (least privilege — not public NONE).
        fn_url = agent_fn.add_function_url(
            auth_type=lambda_.FunctionUrlAuthType.AWS_IAM
        )

        CfnOutput(self, "AgentFunctionName", value=agent_fn.function_name)
        CfnOutput(self, "AgentFunctionUrl", value=fn_url.url)


app = cdk.App()
BedrockAgentStack(app, "SampleBedrockAgentStack")
app.synth()
