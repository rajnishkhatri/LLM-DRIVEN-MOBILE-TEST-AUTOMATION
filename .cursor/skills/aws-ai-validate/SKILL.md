---
name: aws-ai-validate
type: skill
description: >-
  AWS-AI capability workflow stage 5: prove an AI/ML build holds up — offline
  botocore-Stubber + moto contract harness, static IaC checks, agent
  evaluation/observability, a cost & security review, then a deliberately gated
  real-AWS smoke. Use when the user asks "is this Bedrock/SageMaker/agent design
  production-ready", "does this hold up", "validate/test my AWS AI code",
  "run the offline harness", "smoke-test against a real account", or wants the
  Well-Architected GenAI/ML checklist that feeds arch-validate's
  GenAI-intersection. This is where the family's eval + cost + security + guardrail
  criteria live, and the ONLY place real credentials are ever requested. Do NOT
  use to write new build code (aws-ai-build), to author CDK (aws-ai-deploy), to
  choose a service (aws-ai-assess), or to run the whole architecture governance
  pass (arch-validate — this only supplies its GenAI slice).
---

# Stage 5 — Validate (offline harness → gated real-AWS)

> Binding: `.aws-ai/binding.toml` (see aws-ai-lifecycle). Verification stack:
> `{{test_stack}}` (`stubber+moto`, pure-Python, always on); `{{localstack}}`
> opt-in. Real creds: `{{aws_profile}}` (stays `<none>` until this stage's gate).
> Inputs: `{{build_home}}` (code under test), `{{deploy_home}}` (CDK to synth).
> Report → `{{validate_home}}`. Policy floor: `{{constitution}}` (cost ceilings,
> model-access, data-residency). Reference:
> `../aws-ai-lifecycle/references/boto3-foundations.md` §6 (the coverage matrix).

Micro-loop: run the offline harness → check agent eval/observability → do the
cost/security review → **only then** the gated real-AWS smoke, and only with
human-supplied throwaway creds. The bundled `scripts/` harness is the proof; the
report to `{{validate_home}}` is the artifact. This is the terminal stage — a
failure loops back to **aws-ai-build** or **aws-ai-deploy**, never forward.

The harness is bundled next to this skill: `scripts/verify.py` (the runner),
`scripts/tests/` (the Stubber + moto suite), `scripts/requirements-dev.txt`,
`scripts/README.md`. Every command below is copy-runnable from the repo root.

## Agent work

1. **Offline contract tests — the always-on default.** Install once
   (`python -m pip install -r .claude/skills/aws-ai-validate/scripts/requirements-dev.txt`),
   then run the whole suite:
   `python .claude/skills/aws-ai-validate/scripts/verify.py`. This exercises the
   real AWS response *shapes* your build depends on with **no network and no
   credentials** — the runner scrubs any ambient `AWS_PROFILE`/keys, injects bogus
   static creds, and disables IMDS, so even a mis-written test fails signing
   rather than reaching an account. The `bedrock-runtime` cases use botocore
   `Stubber` on purpose: **`moto` cannot mock `bedrock-runtime`, so the Stubber is
   the only pure-unit path** for `converse`/`converse_stream`, the full tool-use
   loop (`stopReason="tool_use"` → echo the assistant turn → `toolResult` with a
   list-of-blocks body → loop to `end_turn`), `apply_guardrail`
   (`GUARDRAIL_INTERVENED` must be treated as a block), and `sagemaker-runtime`
   `invoke_endpoint`. Because `Stubber` validates each canned response against the
   botocore service model, these double as contract tests: if AWS moves a required
   field, the stub stops validating and the test tells you. Matrix and rationale:
   `../aws-ai-lifecycle/references/boto3-foundations.md` §6.
2. **Infra tests — moto `@mock_aws` for the supporting plane.** Where `moto`
   *does* reach, prefer it over `Stubber`: S3 put/get, the IAM execution role
   (assert **both** `foundation-model/*` and `inference-profile/*` ARNs are
   present — omitting either is the classic `AccessDenied` trap), Lambda, Step
   Functions, and the **SageMaker control plane** (`create_training_job`,
   `create_pipeline`, `create_model`, `create_endpoint`). Guard control-plane
   calls with a capability check that **skips** cleanly when the installed `moto`
   lacks the operation, so the suite degrades instead of failing on a version
   gap. These run in-process alongside step 1 under the same `verify.py` — extra
   pytest args pass straight through
   (`verify.py -k infra -v`, `verify.py -k converse`).
3. **Static IaC + types — verification that needs no mock at all.** For the
   `{{iac_tool}}` app in `{{deploy_home}}`: `cdk synth` (offline; runs Aspects and
   cdk-nag), then `cfn-lint` on the emitted template, then `cdk-nag`
   (`AwsSolutionsChecks` — flags `AwsSolutions-IAM5` wildcards, unencrypted
   resources, public exposure; record any deliberate exception as a
   `NagSuppressions` entry with a reason, never a silent delete). Type-check the
   Python against the service models:
   `pip install 'boto3-stubs[bedrock-runtime,sagemaker,sagemaker-runtime,s3,iam]'`
   then `mypy` over `{{build_home}}` and `scripts/tests/` — this catches wrong
   params, wrong keys, and wrong return shapes before any runtime, which is
   exactly where hand-rolled Converse/tool-use code drifts.
4. **Evaluation & observability — is the *agent* good, not just the call
   valid?** Contract tests prove the plumbing; they say nothing about answer
   quality or runaway tool loops. For agent builds, wire the three-pass evaluation
   pattern (`{{methodology_source}}/ch07.md:379-422`): a session-level
   `Builtin.GoalSuccessRate`, trace-level `Builtin.Correctness`/`Helpfulness`, and
   a domain-specific LLM-as-judge (`eval_client.run(evaluators=[...])`, config from
   `bedrock_agentcore_starter_toolkit`, `ch07.md:313`) — no single metric captures
   behavior, and the custom judge catches business-rule violations the built-ins
   miss (a politely-refused out-of-scope answer still scores 0.0). Confirm tracing
   is emitting: Strands `StrandsTelemetry().setup_otlp_exporter()` to an OTel
   collector / CloudWatch GenAI Observability / Langfuse
   (`ch07.md:506-524`) — you need the reasoning trace (which tools, in what order,
   token counts, cost per turn), because a 200 OK can still hide a hallucination or
   a redundant-tool-call loop. Test the safety layers as two distinct things:
   Bedrock **Guardrails** on the model (`ch07.md:764-772`) filter *text* on input
   and output but **do not intercept tool calls** (`ch07.md:755-758`), so
   tool-level governance needs **AgentCore Policy / Cedar** — deterministic
   `forbid`/`unless` rules evaluated against every `InvokeTool` before it runs
   (refund-over-$1000, same-department-physician, own-org-only;
   `ch07.md:797-841`). Assert both: a prompt-injection attempt must be blocked by
   the Cedar `org_id` check, not merely discouraged by the prompt. Deeper API:
   `../aws-ai-lifecycle/references/agents.md`.
5. **Cost & security review — the Well-Architected GenAI + ML Lenses.** Run the
   design against the two lenses (both revised 2025-11-19): the **Generative AI
   Lens** for FM/RAG/agent work (excessive-agency and prompt-injection security,
   RAG retrieval quality and contextual-grounding, prompt/token cost engineering)
   and the **Machine Learning Lens** for custom-trained SageMaker models (data
   drift, retraining triggers, endpoint right-sizing). Check the cost traps
   concretely: idle SageMaker real-time endpoints bill per instance-hour (prefer
   serverless/async, or scale-to-zero via inference components), Bedrock spend is
   on-demand vs provisioned vs batch (~50% off) with prompt caching (~90% off
   cached input), and any figure must sit under `{{constitution}}`'s ceilings.
   Security: least-privilege IAM (specific model + inference-profile ARNs, never
   `*`; `iam:PassRole` scoped by `iam:PassedToService` for SageMaker roles), VPC
   endpoints for private traffic. **This checklist is the deliverable that
   supplies arch-validate's GenAI-intersection** — emit it in a form that stage
   can lift, not just as prose for yourself.
6. **The gated real-AWS smoke path — only here, only with consent.** Everything
   above is free and credential-less; a real account is touched *only* at this
   step. Two latches both hold or the run stays offline (with a warning): the
   `--online` flag **and** the env var, set by the human, not by you:
   `AWS_AI_ALLOW_ONLINE=1 python .claude/skills/aws-ai-validate/scripts/verify.py --online`.
   Before running, name each call that will hit AWS and whether it can incur cost
   (a `converse` on a live model, a KB `retrieve`, an endpoint `invoke`), and get
   explicit approval per cost-bearing action — a real model call costs tokens the
   moment it fires. Use throwaway sandbox creds in `{{aws_profile}}` scoped to a
   non-production account in `{{region_default}}`, resolve model IDs live
   (`list_foundation_models` / `list_inference_profiles`) rather than trusting a
   pinned example, and tear down anything provisioned. Write the pass/fail
   report — offline results, eval scores, lens findings, and the online smoke
   outcome — to `{{validate_home}}`.

## Human gate

This is the **credential gate**, and the only one in the whole family that asks
for real access: `{{aws_profile}}` stays `<none>` through assess/design/build/
deploy and steps 1–5 here. Real creds are requested *now*, from the human, as
throwaway sandbox creds — never reused from an earlier stage, never inferred from
ambient environment. The human approves each cost-bearing action in step 6
individually (the same conflated-axes discipline as arch-*: not one bundled
"go"); an unapproved cost-bearing call is a defect, not a shortcut. As the
terminal stage, a green run closes the loop and (in design-time supplement mode)
hands the cost/security checklist back to **arch-validate**; a red run loops back
to **aws-ai-build** (contract/eval failure) or **aws-ai-deploy** (synth/IaC
failure), never back to stage 1.

## Constraints

- **Offline first.** The `stubber+moto` harness is the default and runs with no
  network and no credentials; `{{localstack}}` stays `off` unless Docker is up and
  cross-service integration is genuinely needed. No real AWS call happens outside
  step 6's double-latched path.
- **Credentials-gated, cost-approved.** Real creds appear only at the gate, are
  throwaway/sandbox, and nothing that can incur cost runs without explicit
  per-action human approval under `{{constitution}}`'s ceilings.
- **The harness is the proof, not the prose.** A claim of "validated" means
  `verify.py` is green and the eval/lens findings are written to
  `{{validate_home}}` — a description of what *would* pass is not a pass. Contract
  tests are the floor; agent quality needs the eval passes on top of them.
- **Never report an execution you did not perform.** Do not write "I ran it, N
  passed" or paste a pass count you did not *just* produce — actually run
  `verify.py` and quote its real output, or say plainly that you have not run it
  yet. And reference the bundled paths **defensively**: the
  `.claude/skills/aws-ai-validate/scripts/…` tree exists in this skill's source
  repo but may be absent in a consumer's workspace, so confirm a file is there
  before asserting it, and copy the harness in if it isn't. **Whenever the output
  points at that bundled path, frame it as living in the skill's source repo or
  "if present in your workspace" — never as though it already exists in the
  reader's repository** (no "this repo already ships a harness at `…/scripts/`"):
  a reader in a different repo will find the path missing, so the framing must
  survive being copied elsewhere.
- **Don't pin what drifts.** Resolve model IDs at run time, keep the Stubber
  responses matched to the current service model (a validation failure is a real
  API change to chase, not a test to loosen), and treat the SageMaker SDK V2/V3
  split and the two `agentcore` CLIs as version-checked, not assumed. When a
  fixture or example must carry a literal model id, use the `us.`-prefixed
  inference-profile id (e.g. `us.anthropic.claude-3-5-sonnet-…`): a bare
  foundation-model id 400s on inference-profile-only current Claude models — the
  model-side twin of deploy/design's two-ARN lesson.
