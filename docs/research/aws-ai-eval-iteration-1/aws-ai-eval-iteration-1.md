---
type: analysis
title: aws-ai-* skill family — eval iteration 1 (with-skill vs baseline)
description: >-
  Results and rubric for the first skill-creator eval pass over the aws-ai-*
  family: six realistic prompts answered with the skill vs a general-knowledge
  baseline, graded against discriminating assertions. Records the +19-point
  benchmark, the per-eval interpretation, the reviewer rubric, the grader
  fairness fixes, and the two weak evals to harden in iteration 2. Companion to
  the research and corpus-inventory Concepts.
tags: [aws, bedrock, sagemaker, eval, benchmark, rubric, skill-creator, analysis, aws-ai-skill]
---

# aws-ai-* eval — iteration 1

**Provenance.** Run 2026-08-12 via the skill-creator eval methodology, adapted
to a skill *family*. Six realistic user prompts (one per stage skill + the
router) were each answered two ways — **with_skill** (the agent reads the
`aws-ai-lifecycle` router, routes to the right stage, follows its methodology +
references) and **without_skill** (the same prompt from general knowledge, no
skill). One run per configuration (iteration 1). Deterministic, negation-aware
grading against the assertions in
[.claude/skills/aws-ai-lifecycle/evals/evals.json](../../../.claude/skills/aws-ai-lifecycle/evals/evals.json).
Companion to [aws-ai-bedrock-sagemaker-research.md](../aws-ai-bedrock-sagemaker-research.md)
and [aws-ai-corpus-inventory.md](../aws-ai-corpus-inventory.md).

## Headline

**With-skill 100% vs baseline 80.6% — +19 points.** (The ±26% spread on the
baseline is eval-to-eval variance, not repeated-run variance — there was one run
per configuration.)

| # | Eval | Targets | with_skill | baseline | Δ |
|---|---|---|--:|--:|--:|
| 0 | assess-service-selection | `aws-ai-assess` | 100% | 75% | **+25** |
| 1 | design-agent-rag-iam | `aws-ai-design` | 100% | 100% | 0 |
| 2 | build-converse-tool-loop | `aws-ai-build` | 100% | 100% | 0 |
| 3 | deploy-cdk-two-arn | `aws-ai-deploy` | 100% | 100% | 0 |
| 4 | validate-offline-stubber | `aws-ai-validate` | 100% | 75% | **+25** |
| 5 | router-where-to-start | `aws-ai-lifecycle` | 100% | 33% | **+67** |

## Interpretation

The skill reaches 100% on every eval; the baseline is *strong* (80.6%) because
the base model (Opus) already knows well-documented AWS APIs. So the measured
lift concentrates exactly where a naive answer falls short:

- **Family process / routing (+67%, eval 5).** The baseline gives a sensible but
  generic "define your use case → pick a model → build a POC." It lacks the
  family's named `assess → design → build → deploy → validate` pipeline and the
  offline-first / credential-gating discipline — the router's core contribution.
- **Non-obvious gotchas (+25% each, evals 0 & 4).** The baseline reached for
  `moto` broadly and missed that **moto cannot mock `bedrock-runtime`** (so
  Stubber is the only pure-unit path); the skill flags it. On assessment, the
  skill holds the RAG-over-fine-tune line with a stated reason and stays at
  assessment altitude.
- **Well-documented tasks (Δ0, evals 1–3).** Design, the Converse tool-use loop,
  and a CDK stack are things the base model already produces correctly. The skill
  *matches* rather than beats — its value there is reliability (e.g. warning off
  the legacy completion format) rather than a pass-rate delta.

## Rubric

The full reviewer walkthrough — per-eval prompt, the discriminating signal, and
good-vs-poor examples — is in
[aws-ai-rubric-guide.html](aws-ai-rubric-guide.html). The assertions themselves
live in the seed
[evals.json](../../../.claude/skills/aws-ai-lifecycle/evals/evals.json). The
discriminators (the assertions only the skill should reliably satisfy):

- **assess:** recommends RAG over fine-tuning *with a reason*.
- **design:** least-privilege IAM flags BOTH `foundation-model/*` and
  `inference-profile/*` ARNs.
- **build:** does not use the legacy `\n\nHuman:` / `max_tokens_to_sample`
  completion format; correct `toolConfig → tool_use → toolResult(toolUseId) →
  end_turn` loop.
- **deploy:** the two-ARN IAM pairing in the CDK role.
- **validate:** notes moto cannot mock `bedrock-runtime` → Stubber required.
- **router:** the five-stage pipeline + offline/credential-gating.

## Grader fairness fixes (applied before the numbers above)

The grader is pattern-based, so two adjustments were made after inspecting
outputs, to avoid false grades:

1. **Negation-aware legacy check.** Eval 2's skill answer was initially penalized
   for *warning against* the legacy completion format ("do not use
   `max_tokens_to_sample` …"). The grader now fails only genuine *use*, not a
   cautionary mention. (Eval 2 is 100/100, not 75/100.)
2. **Use-case credit.** Eval 5's baseline opened with "nail down the use case
   first," which is assessment in spirit; the grader now credits that (baseline
   eval 5 is 33%, not 0%).

## Weak evals to harden in iteration 2

- **Eval 3 telegraphs its answer.** The prompt says "we use the us. cross-region
  model ids," which effectively hands both configurations the inference-profile
  ARN — so the baseline passes the two-ARN discriminator too. Drop the hint so
  the eval tests whether the skill catches the trap *unprompted*.
- **Evals 1–2 test tasks the base model aces.** Design and the Converse loop are
  well-documented; they don't isolate skill value. Replace with harder cases
  (e.g. a design that tempts an over-engineered multi-agent answer; a build that
  tempts the legacy format).
- Consider **≥3 runs per configuration** in iteration 2 to get real run-to-run
  variance rather than eval-to-eval spread.

## Artifacts (in this folder)

- [aws-ai-eval-review.html](aws-ai-eval-review.html) — the interactive feedback
  viewer (Outputs + Benchmark tabs; "Submit All Reviews" downloads
  `feedback.json`).
- [aws-ai-rubric-guide.html](aws-ai-rubric-guide.html) — the reviewer rubric
  walkthrough.
- [benchmark.json](benchmark.json) / [benchmark.md](benchmark.md) — the
  aggregated results (note: the generated header says "3 runs each" — that is the
  aggregator's default; iteration 1 was 1 run each).

## How to reproduce

1. Eval set: `.claude/skills/aws-ai-lifecycle/evals/evals.json`.
2. Run: the eval-run workflow (`run-aws-ai-evals.mjs`) fans out 6 prompts ×
   {with_skill, baseline} as subagents, each writing to a review workspace.
3. Grade: `grade_evals.py` (deterministic, negation-aware) → `grading.json`
   per run.
4. Aggregate: skill-creator's `aggregate_benchmark.py <workspace> --skill-name
   aws-ai-family` → `benchmark.json`/`.md`.
5. View: skill-creator's `generate_review.py <workspace> --benchmark … --static
   <out.html>`.
