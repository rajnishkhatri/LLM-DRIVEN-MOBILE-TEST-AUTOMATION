# ADR 0008. Bedrock Guardrails on Converse from day one; validator as backup

## Status
Proposed — depends on ADR 0001

## Context
Privacy is a top-3 characteristic and the packets contain PII (an SSN appears
in the auto sample). The original design §4 used the app-level `ContentValidator`
as the PoC PII stand-in with real Guardrails as a promote; eval recommendation
#3 argues the opposite — Guardrails should be *the* control and the regex
validator the backup. Since the runtime is going to real Bedrock anyway,
wiring `guardrailConfig` is a small delta.

## Decision
We will attach **Bedrock Guardrails to the Converse call from the first
real-AWS cut**:

- **PII: ANONYMIZE**, not BLOCK — claim inputs legitimately contain PII we must
  process; the control prevents PII **leaking into summaries and logs**, it
  does not reject the input.
- **Contextual grounding** threshold (~0.70, **re-verify**) on the summary vs
  retrieved policy chunks — a model-level integrity lever atop the validator's
  citation-required rule.
- **Prompt-attack** filter on input.
- Applied via Converse-native `guardrailConfig` (standalone `apply_guardrail`
  for any text Bedrock did not generate).

The app **`ContentValidator` is retained as defense-in-depth** — it does what
Guardrails cannot: schema validation, citation-required, empty-field detection,
and residual-PII detection → flag → HITL (ADR 0005). Guardrails never see a
tool decision; the PoC has no tools, so no Cedar/Verified Permissions yet.

Rejected: **PII BLOCK** (would reject legitimate PII-bearing claims);
**validator-only, Guardrails deferred** (leaves privacy on regex while on real
Bedrock — the eval-rec-#3 anti-pattern).

## Consequences
Good: privacy and grounding enforced at the model boundary, structural rather
than regex-dependent; defense-in-depth with the validator; `GUARDRAIL_INTERVENED`
is an auditable signal.
Bad: a Guardrail resource to create and **version** in the manual deploy, plus
per-unit cost; the grounding threshold needs tuning (too high blocks valid
summaries, too low lets ungrounded text through) — **re-verify**; Guardrails do
no schema/citation work, so the validator is not redundant.

## Compliance
Fitness: `guardrailConfig` is present on every Converse call; the
`GUARDRAIL_INTERVENED` rate on PII is recorded; **no raw PII (e.g. an SSN)
appears in application logs** (log-shape test); a summary below the grounding
threshold is flagged `ungrounded`; the validator still asserts schema +
citation. Regression: a Converse call without `guardrailConfig` fails the
fitness check.

## Notes
Author: aws-ai-design (provisional kata run)
Approved by / date:
Last modified: 2026-09-21
