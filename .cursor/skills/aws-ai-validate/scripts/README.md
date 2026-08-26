# aws-ai-validate — offline verification harness

The runnable proof for the `aws-ai-*` family: it exercises the real AWS response
*shapes* your build code depends on, with **no network and no credentials**. It
is the always-on default gate before the deliberately gated real-AWS path.

## What it covers

| Test | Tool | Why this tool |
|---|---|---|
| `tests/test_bedrock_converse_stubber.py` | botocore `Stubber` | `moto` cannot mock `bedrock-runtime`; the Stubber is the only pure-unit path. Drives the full Converse **tool-use loop** (`tool_use` → `toolResult` echo → `end_turn`). |
| `tests/test_guardrails_stubber.py` | botocore `Stubber` | `apply_guardrail` is a `bedrock-runtime` call; asserts a `GUARDRAIL_INTERVENED` action is treated as a block. |
| `tests/test_sagemaker_runtime_stubber.py` | botocore `Stubber` | Pins the `invoke_endpoint` streaming-`Body` parse contract. |
| `tests/test_infra_moto.py` | `moto` `@mock_aws` | S3 put/get, an IAM execution role (with the two-ARN Bedrock trap), and a capability-gated SageMaker control-plane call that **skips** if the installed moto lacks it. |

`Stubber` validates each stubbed response against the botocore service model, so
these double as **contract tests**: if AWS changes a required field, the stub
stops validating and the test tells you.

## Run it

```bash
python -m pip install -r requirements-dev.txt
python verify.py                       # OFFLINE (default) — Stubber + moto, no AWS
```

`verify.py` discovers `./tests`, runs pytest, prints a PASS/FAIL summary, and
exits non-zero on failure. Extra arguments are forwarded to pytest:

```bash
python verify.py -k converse -v        # filter / verbosity pass through
```

Optional static checks (installed by `requirements-dev.txt`):

```bash
pip install 'boto3-stubs[bedrock-runtime,sagemaker,sagemaker-runtime,s3,iam]'
mypy tests/                            # catches wrong params/keys before runtime
```

## The gated-online contract

The harness refuses any real AWS call unless **both** latches are set:

```bash
AWS_AI_ALLOW_ONLINE=1 python verify.py --online    # gated real-AWS path
```

Passing only `--online` (without `AWS_AI_ALLOW_ONLINE=1`) — or only the env var
without the flag — keeps the run **offline** and prints a warning. In offline
mode the child pytest process is launched with ambient AWS credentials scrubbed,
bogus static creds injected, and IMDS disabled, so a mis-written test fails
signing rather than reaching a real account. Real calls may incur cost and need
explicit human approval per the family constraints.
