---
type: analysis
title: aws-ai-* skill family — eval iteration 2 (skill fixes + hardened evals)
description: >-
  Iteration-2 results after applying the seven reviewer-identified skill fixes
  (S1–S7) and hardening four evals (E0–E3). With-skill 100% vs baseline 72.5%
  (+27.5 points, up from +19). Records what changed, the iter-1→iter-2 delta
  comparison, the fairness verification, and what remains. Companion to the
  iteration-1 report and the iteration-2 plan.
tags: [aws, bedrock, sagemaker, eval, benchmark, iteration-2, analysis, aws-ai-skill]
---

# aws-ai-* eval — iteration 2

**Provenance.** Run 2026-08-13 after executing
[iteration-2-plan.md](../aws-ai-eval-iteration-1/iteration-2-plan.md) in full:
the seven skill fixes S1–S7 and the four eval hardenings E0–E3. Same six prompts,
same with_skill-vs-baseline method, one run per configuration; the with_skill runs
now read the improved skills, graded against the harder assertions. Companion to
the [iteration-1 report](../aws-ai-eval-iteration-1/aws-ai-eval-iteration-1.md).

## Headline

**With-skill 100% vs baseline 72.5% — +27.5 points** (iteration 1 was
100% vs 80.6%, +19). The delta grew and became *more meaningful*: the baseline's
measured score dropped precisely because the hardened assertions now test the
skill's real edge, which a general-knowledge answer does not reach.

## iter-1 → iter-2, per eval

| # | Eval | iter-1 with/base/Δ | iter-2 with/base/Δ | What moved it |
|---|---|---|---|---|
| 0 | assess | 100 / 75 / **+25** | 100 / 80 / **+20** | E0: added a Q Business assertion (baseline now passes it too) + tightened the managed-vs-self-host axis (baseline fails it). Skill still leads by one assertion. |
| 1 | design | 100 / 100 / **0** | 100 / 80 / **+20** | E1: added the tool-authorization-boundary discriminator (guardrails don't see tool calls → Cedar/Verified Permissions). Baseline only screens tool *outputs*; it never authorizes the tool *call*. |
| 2 | build | 100 / 100 / **0** | 100 / 100 / **0** | E2 added a cross-stage-discipline assertion — but the baseline independently writes a `max_turns` guard, so the OR-predicate credits it. Honest Δ0: the base model is genuinely strong here. |
| 3 | deploy | 100 / 100 / **0** | 100 / 67 / **+33** | E3: tightened "offline validation" to *require* cfn-lint / cdk-nag / a deploy gate. Baseline does `cdk synth` then `cdk deploy` with none of that discipline. |
| 4 | validate | 100 / 75 / **+25** | 100 / 75 / **+25** | unchanged (already the clearest win). |
| 5 | router | 100 / 33 / **+67** | 100 / 33 / **+67** | unchanged (the router's staged process + credential-gating). |
| — | **overall** | **100 / 80.6 / +19** | **100 / 72.5 / +27.5** | |

The two evals that iteration 1 flagged as failing to isolate skill value (1 and 3)
converted from Δ0 to **+20** and **+33**. Eval 2 stayed Δ0 *honestly* — see below.

## What changed (executed in full)

**Skill fixes (S1–S7):**
- **S1** Amazon Q Business added to the assess service-matrix (the one place the
  baseline genuinely beat the skill) — as the purpose-built managed-assistant tier,
  a fourth matrix column, and a "reinventing Q Business" antipattern.
- **S2** max-turns guard on the Converse tool-use loop (`for _turn in range(MAX_TURNS)`
  + `else: raise`) in `references/bedrock.md`.
- **S3** harness: a `converse_stream` boundary-fake test + a network backstop (see
  the honest deviation below).
- **S4** router now allows a *caveated* Bedrock-playground manual-prototype path
  (manual/ad-hoc ≠ the gated automated real-AWS path).
- **S5** validate skill: "never report an execution you did not perform" + reference
  bundled paths defensively.
- **S6** design/agents: lead the tool-authorization story with **Verified Permissions**
  for Lambda/ECS hosts, **AgentCore Policy** for AgentCore Runtime.
- **S7** model-id-as-re-verify-marker note in the loop example.

**Eval hardenings (E0–E3):** eval 0/1/2 grew to five assertions each with the
discriminators above; eval 3's loose "cdk synth" assertion now requires real
validation discipline.

## Honest deviation — the network backstop

The reviewer suggested `pytest-socket --disable-socket`. Adopting it *literally*
broke every mocked test: it blocks at socket **creation** (and `gethostbyname`),
but botocore resolves the endpoint hostname while preparing a request — *before*
the Stubber/moto short-circuit — so a blanket block fails on DNS. The reviewer's
**intent** ("a forgotten stub is a loud error, not a silent bill") is served by
blocking real outbound **connects** instead: a surgical `conftest.py` wraps
`socket.create_connection` to raise for non-localhost hosts. Under Stubber and
`@mock_aws` no real connect happens, so mocked tests pass; a leaked call raises —
**verified** by asserting a real `bedrock-runtime` connect is blocked. `pytest-socket`
was dropped as the wrong granularity. Harness result: **8 passed** (the 7 originals
plus the new stream test).

## Why eval 2 is still Δ0 (and that's correct)

The E2 assertion credits *any* of: a dependency-injected client, the two-ARN IAM
note, or a max-turns guard. The baseline independently writes a `max_turns` guard,
so it passes — honestly. The skill's distinctive edge on this task (an injected
client that is offline-testable, pre-wiring the eval-4 Stubber seam) is real but
not *exclusive* enough to isolate with a keyword assertion without over-fitting.
Left as an honest Δ0 rather than gamed to a positive.

## Fairness verification

Every iteration-2 grade was checked against the raw outputs: eval-0 baseline fairly
fails the tightened self-host axis; eval-1 baseline's only guardrail-near-tool
mention is about screening tool *outputs* with `ApplyGuardrail`, not authorizing the
tool *call* (fair FAIL); eval-3 baseline has zero cfn-lint/cdk-nag (earned +33);
eval-2 both pass via an independently-written max-turns guard.

## Artifacts (in this folder)

- [aws-ai-eval-review-iter2.html](aws-ai-eval-review-iter2.html) — the review viewer,
  with iteration-1 outputs shown as "previous" for side-by-side comparison.
- [aws-ai-rubric-guide-iter2.html](aws-ai-rubric-guide-iter2.html) — the **annotator
  rubric walkthrough**: every assertion with its mechanical PASS rule, the real
  PASS/FAIL evidence quotes pulled from these iteration-2 outputs, and the specific
  mis-grading trap per row (hollow keyword match, negated mention, a genuine pass the
  pattern grader could miss). Grounds the three fairness rules and marks the nine
  discriminator rows where the skill's measured edge actually lives. Successor to the
  iteration-1 [rubric guide](../aws-ai-eval-iteration-1/aws-ai-rubric-guide.html),
  updated for the hardened rubric.
- [benchmark.json](benchmark.json) / [benchmark.md](benchmark.md) — aggregated
  results (header says "3 runs each" — aggregator default; this was 1 run each).

The current assertion set (the rubric) lives in
[.claude/skills/aws-ai-lifecycle/evals/evals.json](../../../.claude/skills/aws-ai-lifecycle/evals/evals.json)
and is shown per-card in the viewer.

## What remains (optional)

- A third iteration would chase eval 2's honest Δ0 (harder to isolate without
  over-fitting) and could add ≥3 runs per configuration for run-to-run variance.
- Description-optimization (`run_loop.py`) for trigger accuracy, `.skill` packaging,
  and the gated real-AWS smoke (throwaway sandbox creds, requested only then).
