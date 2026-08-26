# sample_cdk_app — a Lambda "Bedrock agent" (CDK v2, Python)

A minimal, **offline-synthesizable** CDK app whose only job is to encode the
two-ARN Bedrock IAM trap in real infrastructure-as-code. One `Stack`, one Lambda
function playing the agent role, and an execution-role policy that grants
`bedrock:InvokeModel` on **both** a `foundation-model/*` and an
`inference-profile/*` resource ARN.

## Why two ARNs

A model id starting with `us.` (e.g. `us.anthropic.claude-sonnet-4-5-...`) is a
*cross-region inference profile*, not a bare model. The role therefore needs
both resources or invocation fails with an `AccessDenied` that never says which
permission is missing (cases/aws-ai/ch06.md:72). Note the asymmetry the code
makes explicit: the `foundation-model` ARN has an **empty account segment**
(`arn:aws:bedrock:<region>::foundation-model/*`) while the `inference-profile`
ARN carries the account.

## Run it

```bash
# cdk is an npm tool:  npm i -g aws-cdk
pip install -r requirements.txt
cdk synth
```

`cdk synth` renders the CloudFormation template with **no Docker and no AWS
account** — the Lambda uses inline code, so nothing is bundled at synth time.
Inspect the synthesized template's IAM policy to see both resource ARNs.

## Not production-shaped on purpose

Inline Lambda code keeps `synth` offline. A real Strands/AgentCore agent's
dependencies exceed Lambda's 250 MB zip limit, so ship it as a
`DockerImageFunction` (container image, up to 10 GB) on ARM64/Graviton
(ch06.md:83); a loop longer than Lambda's 15-minute ceiling belongs on AgentCore
Runtime instead. The handler itself uses the native **Converse** API — never the
legacy `\n\nHuman:`/`max_tokens_to_sample` completion format.

## Optional static gates (no AWS needed)

```bash
cdk synth > template.json      # offline; runs any cdk-nag Aspects you add
cfn-lint template.json         # or point cfn-lint at cdk.out/*.template.json
pip install cdk-nag            # add AwsSolutionsChecks Aspect to flag IAM5, etc.
```
