# ADR 0002. Models are config behind a ModelPort; every swap is a release gated by the golden set

## Status
Accepted

## Context
The brief mandates GPT-4o ("it's what the other teams are using and it's good
enough"). The platform must outlive any model: vendors update models under
you, "good enough" is an untested claim, and the provenance tuple requires the
resolved model id per turn. The brief's challenge to this mandate must be a
decision record with alternatives, not an opinion. Prior art: claim-processor
ADR 0011 ModelAdapter (typed outcomes, resolved-id recorded) — pattern
quarried, not imported.

Alternatives: (a) **Hardcode GPT-4o** per the brief — vendor coupling; a
hardcoded model id is a scheduled outage (house lesson); quality claims stay
unfalsifiable; rejected. (b) **Multi-model per-turn routing now** — premature;
no traffic signal to route on; rejected, revisit at volume. (c) **Chosen:**
one ModelPort, model as configuration, swaps gated by evals.

## Decision
- **ModelPort** normalizes request/response and returns a typed outcome
  (ok / throttled / timed-out / invalid / guardrail-intervened); no caller
  ever sees a raw provider response or branches on a model family.
- **Demo default: Claude (Sonnet) on Bedrock** — builder fluency, prior art,
  and Bedrock-native audit (CloudTrail/CloudWatch) on every invocation.
  **GPT-4o is supported as config.** The question the brief hands Dana is
  *which default wins the golden set*, not *whether the platform can swap*.
- **Every model or prompt change is a release:** golden-set parity run before
  the flip; a fallback model (throttle/outage) passes through the same gate;
  a silent mid-conversation model swap is forbidden — the provenance tuple
  records the model + prompt version that actually answered.
- **Determinism for evals and the demo:** temperature 0, recorded fixtures;
  the live-Bedrock toggle exercises the same port.

## Consequences
Good: "which model" becomes a data question — an eval table, not a vendor
debate; that is the influence-without-authority instrument for four teams
already on GPT-4o. Model regressions are caught at the gate, not by
customers. Bad: one more abstraction (justified — it buys the gate and the
provenance field); fixtures must be re-recorded when prompts change.

## Compliance
CI rule: no model/prompt change merges without a golden-set run attached;
provenance completeness includes model + prompt version; contract test on the
typed-outcome enum; grep/AST check: no model-family branching outside the
adapter.

## Notes
Author: session pipeline (sdd-brainstorm → arch-characteristics → arch-decide)
Approved by / date: Rajnish Khatri / 2026-09-30
Last modified: 2026-09-29 / new
