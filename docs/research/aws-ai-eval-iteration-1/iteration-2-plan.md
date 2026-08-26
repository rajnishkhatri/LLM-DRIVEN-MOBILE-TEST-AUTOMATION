---
type: plan
title: aws-ai-* eval — iteration 2 plan (from reviewer feedback)
description: >-
  Synthesis of the human review of eval iteration 1 into concrete iteration-2
  actions: seven skill improvements the reviewer found (Q Business gap, loop
  max-iterations guard, pytest-socket, playground path, no-fabricated-execution,
  Verified-Permissions-for-Lambda, model-id tension) and five eval-set hardenings
  (assertions that currently fail to isolate skill value). Raw feedback in
  feedback-iteration-1.json.
tags: [aws, bedrock, sagemaker, eval, iteration-2, plan, aws-ai-skill]
---

# aws-ai-* eval — iteration 2 plan

Source: human review of iteration 1 (see [feedback-iteration-1.json](feedback-iteration-1.json)
and [the iteration-1 report](aws-ai-eval-iteration-1.md)). Every iteration-1 grade
was confirmed correct; the value here is what the pass rates hid — real skill gaps
(where the baseline genuinely beat or matched the skill) and evals that don't yet
isolate skill value.

## A. Skill improvements (make the skills better)

| # | Skill / file | Change | Evidence |
|---|---|---|---|
| **S1** | `aws-ai-assess` + `references/` (service matrix) | **Add Amazon Q Business** as the purpose-built managed-assistant tier in the service-selection spectrum. For "internal employee portal over N policy PDFs" it is arguably the best default (permission-aware, ready UI, per-user pricing); the skill's spectrum (Bedrock KB / SageMaker / AgentCore) has a hole exactly where this prompt's best answer lives. | evals 0 & 5 — baseline surfaced Q Business, skill never did |
| **S2** | `aws-ai-build` + `references/bedrock.md` (Converse loop) | **Add a max-iterations guard** to the tool-use loop — no `while True` without a bound; raise on exhaustion (a misbehaving model otherwise loops forever). | eval 2 — baseline had the guard, skill did not |
| **S3** | `aws-ai-validate` + harness | **Adopt `pytest-socket` (`--disable-socket`)** as a network-level backstop ("a forgotten stub becomes a SocketBlockedError, not a bill") and a **`converse_stream` boundary-fake** pattern + autouse `conftest.py` fixture. | eval 4 — both genuine improvements from the baseline |
| **S4** | `aws-ai-lifecycle` router (+ `aws-ai-assess`) | **Acknowledge the Bedrock playground manual-prototype path** as a legitimate early exploration step (manual, not CI-automated; caveated) rather than treating ALL real-AWS access as gated to Stage 5. Offline-first stays the default for anything automated/CI. | eval 5 — baseline's cheap-playground step is genuinely better for a first-timer |
| **S5** | `aws-ai-validate` SKILL guidance | **Never claim "I ran it / 7 passed" unless the harness was actually executed** in the current context; report the *actual* result. Reference bundled test paths **defensively** (they live in the skill's source repo and may be absent in the user's workspace). | eval 4 with_skill — twice asserted "I ran it just now — 7 passed" (not embedded in the skill, so it was fabricated by the run) |
| **S6** | `aws-ai-design` `references/` | When the host is **Lambda**, lead the authorization story with **Verified Permissions** (Lambda-applicable) rather than AgentCore Policy, then note AgentCore Policy for AgentCore hosts. Minor. | eval 1 nit |
| **S7** | family-wide (references) | Resolve the **model-id tension**: examples hard-code IDs while the rule says "never hard-code." Frame every inline id explicitly as a **re-verify marker** (resolve via `list_foundation_models` / `list_inference_profiles`). Minor. | evals 1/2/3 nits |

## B. Eval-set hardening (make the assertions isolate skill value)

| # | Eval | Change |
|---|---|---|
| **E0** | assess | Tighten assertion 2: "managed RAG" alone must **fail** — require a **self-host/SageMaker tier OR an instance-hour-vs-per-token cost axis** in the evidence. RAG-with-reason (a1) is necessary but no longer sufficient (baseline passes it). Add a **Q Business** expectation. |
| **E1** | design | Add a real discriminator: the **guardrails-don't-see-tool-calls tool boundary** (Cedar / Verified Permissions permit-deny before write tools), or the **trust read/write role split**, or **PrivateLink `aws:sourceVpce` enforcement**. The baseline misses all of these — this turns the current Δ0 into a real gap. |
| **E2** | build | Add a discriminator for the **dependency-injected client (offline-testable seam)** OR the **two-ARN IAM note** OR the **legacy-format warning** — plus the **max-turns guard** (S2). Only the skill produces these. |
| **E3** | deploy | **Do NOT rely on dropping the "us." hint** — the baseline knows the two-ARN trap *and* the multi-region fan-out from general knowledge. Instead **tighten assertion 3** to require **cfn-lint OR cdk-nag OR an explicit deploy gate** (not just "cdk synth", which is too loose). That offline-validation discipline + human gate is where the skill actually separates. |
| **E4** | validate | Keep (clearest win). Optionally add expectations rewarding `pytest-socket` / `converse_stream` once S3 lands. |
| **E5** | router | Keep (earned +67). Optionally add an expectation that the answer offers the caveated playground path (S4). |
| — | all | Consider **≥3 runs per configuration** in iteration 2 for real run-to-run variance (iteration 1 was 1 run each). |

## Execution order

1. Apply skill improvements S1–S7 (edit the stage skills + references + harness).
2. Re-run the offline harness (`verify.py`) to confirm S2/S3 changes still pass.
3. Update `evals.json` with the hardened assertions E0–E3 (+ E4/E5 options).
4. Re-run the eval workflow (with_skill vs baseline), re-grade, re-aggregate,
   regenerate the viewer → **iteration-2** workspace.
5. Compare iteration-1 vs iteration-2 deltas; expect the hardened evals (E0–E3) to
   convert Δ0 → positive where the skill genuinely leads.

## Cross-check note

The reviewer's own correction on E3 is important: an earlier idea (use multi-region
fan-out as the discriminator) **won't work** because the baseline produces it too.
The durable discriminator for deploy is **offline-validation discipline + deploy
gate**, not ARN breadth.
