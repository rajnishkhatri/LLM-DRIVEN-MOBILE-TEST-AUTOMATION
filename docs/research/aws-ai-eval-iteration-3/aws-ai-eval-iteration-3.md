---
type: analysis
title: aws-ai-* skill family — eval iteration 3 (verified fixes + honest-tie conversion)
description: >-
  Iteration-3 results after verifying the sampling-parameter deprecation against
  the authoritative Claude API reference, applying all reviewer skill-polish fixes
  across the six aws-ai-* skills, and making two eval-harness changes (a 6th eval-2
  assertion isolating the injected-client seam, and de-hinting eval-3). With-skill
  100% vs baseline 69.7% (+30.3, up from +27.5). Eval 2's honest Δ0 converted to
  +17; eval 3's telegraph flag resolved to an honest tie. Companion to the
  iteration-2 report and its feedback.
tags: [aws, bedrock, sagemaker, eval, benchmark, iteration-3, analysis, aws-ai-skill]
---

# aws-ai-* eval — iteration 3

**Provenance.** Run 2026-08-13 after processing the iteration-2 reviewer feedback
([feedback-iteration-2.json](../aws-ai-eval-iteration-2/feedback-iteration-2.json)),
which upheld every grade (zero overrides) and was entirely skill-polish. Iteration 3
verified the one factual claim, applied all reviewer fixes across the six skills, made
two eval-harness changes, then re-ran the same six prompts with_skill-vs-baseline, one
run per configuration. Companion to the
[iteration-2 report](../aws-ai-eval-iteration-2/aws-ai-eval-iteration-2.md).

## Headline

**With-skill 100% vs baseline 69.7% — +30.3 points** (iteration 2 was 100% vs
72.5%, +27.5). The delta grew because eval 2's *honest* Δ0 finally converted to a
real, fairly-isolated **+17**, and because the baseline's measured score dropped as
the two hardened eval-harness changes took effect.

## iter-2 → iter-3, per eval

| # | Eval | iter-2 with/base/Δ | iter-3 with/base/Δ | What moved it |
|---|---|---|---|---|
| 0 | assess | 100 / 80 / +20 | 100 / 80 / **+20** | unchanged score; skill answer materially better (Q Business trust/safety controls, labeled-data knockout, two cost shapes) |
| 1 | design | 100 / 80 / +20 | 100 / 80 / **+20** | unchanged score; skill answer adds metadata-filtering-as-correctness-lever + the console-vs-Lambda AccessDenied framing |
| 2 | build | 100 / 100 / **0** | 100 / 83 / **+17** | **the honest Δ0 converted.** New assertion [5] credits the injected-client testability seam; the baseline uses a module-level client and fails it |
| 3 | deploy | 100 / 67 / +33 | 100 / 67 / **+33** | de-hinted the prompt; [2] (cfn-lint/cdk-nag/gate) still the sole discriminator |
| 4 | validate | 100 / 75 / +25 | 100 / 75 / **+25** | unchanged (still the clearest single gotcha — moto can't mock bedrock-runtime) |
| 5 | router | 100 / 33 / +67 | 100 / 33 / **+67** | unchanged (the named 5-stage pipeline + credential gating) |
| — | **overall** | **100 / 72.5 / +27.5** | **100 / 69.7 / +30.3** | |

## What changed — executed in full

**Verified first (before baking anything in).** The reviewer's claim that
`temperature`/`top_p`/`top_k` are deprecated on current-generation Claude was
**confirmed against the authoritative Claude API reference**: they are *removed* on
Opus 4.7+/Opus 5 and Fable 5 (sending any returns a 400) and *rejected as non-default*
on Sonnet 5; they remain valid on Sonnet 4.5 / Opus 4.5 and earlier. On Bedrock these
breaking changes apply unchanged. So the guard is model-generation-specific, and the
iteration-2 eval-2 output that *omitted* `inferenceConfig` was already correct. This is
now documented in `references/bedrock.md` (beside the legacy-`\n\nHuman:` warning, as a
symmetric deprecated-parameter trap) and enforced in the build/deploy examples.

**Skill fixes (six skills, one editor per file, all additive/surgical):**
- **assess** — Q Business (recommended-path) trust/safety controls now required in the
  assessment (document-level ACLs, admin/content controls, response guardrails,
  grounding) — the reviewer's #1 pre-ship gap; "you have documents, not a labeled Q&A
  set" elevated to a standalone fine-tune knockout; a VP-ready one-liner; per-user vs
  per-token cost shown as two *shapes* with the crossover named; re-verify markers on
  fast-moving cost facts.
- **design** — metadata filtering elevated to "single biggest correctness lever" for
  regulated/insurance (tag + filter on line_of_business / jurisdiction / policy_form /
  plan_version / effective-expiration); the "works in the console but the Lambda gets
  AccessDenied" two-ARN symptom framing; model-id-in-IAM marked a startup-resolved
  pattern; TL;DR-first output ordering. `references/agents.md` now prefers default-deny
  `forbid … unless` Cedar for compliance domains.
- **build** — the verified sampling-param warning in `references/bedrock.md`; the one
  Converse example de-sampled to `maxTokens` only; example model ids framed as
  re-verify.
- **deploy** — sampling params removed from the inline handler + the bundled
  `sample_cdk_app/app.py`; specific-profile-id IAM scoping made the default (family
  wildcard demoted to an "if you rotate models often" variant); the
  `aws bedrock get-inference-profile → models[].modelArn` discovery CLI, the "lazy
  shortcut resources=['*']" callout, and the `aws_ecr_assets` import note added.
- **validate** — bundled-harness paths must be framed defensively ("in the skill's
  source repo / if present in your workspace") — the one partial S5 miss, now closed;
  example ids must use the `us.`-prefixed inference-profile form.
- **router** — "what's the cost of being wrong?" added as the leading triage question;
  a one-line pointer to where post-deploy eval + monitoring live (validate). The
  Bedrock-playground carve-out (S4) was verified already present.

**Eval-harness changes (2):**
- **eval 2 gained a 6th assertion** crediting the dependency-injected client (an
  offline-testable seam that pre-wires the validate-stage Stubber) — the reviewer's
  recommended way to isolate the honest Δ0 *without* over-fitting [4]'s OR-predicate.
- **eval 3's prompt was de-hinted** — the "we use the us. cross-region model ids"
  telegraph was removed (now "…this Bedrock agent (it calls Claude Sonnet)…").

## Honest findings (verified against the raw outputs)

- **Eval 2 [5] is a fair +17.** with_skill: `def run_conversation(client, model_id, …)`
  — injected client. baseline: module-level `bedrock = boto3.client(...)` + a
  no-client-param loop. The skill's real cross-stage edge (an offline-testable seam)
  is now isolated; [4] stays an honest OR-tie so it isn't double-counted.
- **Eval 3's telegraph flag is resolved — and [1] is an honest tie.** With the hint
  gone, *both* configs still grant both ARNs in a real `PolicyStatement` (the base
  model knows Claude Sonnet on Bedrock is inference-profile-only), so [1] is a genuine
  tie on merit, not a prompt artifact. The +33 rides entirely on [2] (the baseline runs
  `cdk deploy` with no cfn-lint/cdk-nag/gate). This is a *more honest* state than
  iteration 2, even though the number didn't move.
- **The sampling-param fix surfaced as a warning, not usage.** The eval-2 with_skill
  output now says "pass ONLY maxTokens — no temperature/topP/topK" — the verified
  guidance landed behaviorally.

## Offline harness

Re-verified after the skill edits (the deploy edit touched the bundled CDK app, not the
pytest harness): **8 passed** under the surgical connect-guard conftest. The bundled
`sample_cdk_app/app.py` was synth-verified in a fresh `aws-cdk-lib` venv — the
synthesized IAM policy shows the two specific ARNs (no wildcards) and the handler's
Converse call carries only `maxTokens`.

## Artifacts (in this folder)

- [aws-ai-eval-review-iter3.html](aws-ai-eval-review-iter3.html) — the review viewer,
  with iteration-2 outputs shown as "previous" for side-by-side comparison.
- [benchmark.json](benchmark.json) / [benchmark.md](benchmark.md) — aggregated results.

The current assertion set (the rubric — now 6 assertions on eval 2) lives in
[.claude/skills/aws-ai-lifecycle/evals/evals.json](../../../.claude/skills/aws-ai-lifecycle/evals/evals.json).
The iteration-2 annotator [rubric guide](../aws-ai-eval-iteration-2/aws-ai-rubric-guide-iter2.html)
is now one assertion behind on eval 2 and carries eval 3's old telegraphing prompt —
refresh it before the next annotation pass.

## What remains (optional)

- Refresh the annotator rubric guide for the iteration-3 rubric (eval-2 [5]; de-hinted
  eval-3).
- Run-to-run variance: ≥3 runs per configuration (all deltas here are single-run).
- The still-optional non-eval tracks: description-optimization for trigger accuracy,
  `.skill` packaging, and the gated real-AWS smoke (throwaway sandbox creds, requested
  only at that step).
