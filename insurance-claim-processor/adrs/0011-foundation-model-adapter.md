# ADR 0011. Put foundation models behind a Bedrock-family adapter

## Status
Accepted

## Context
Today one `ModelInvoker.converse` (`../build/claim_processor/invoker.py`) builds
the Converse envelope and normalizes the response for whatever `modelId` it is
given. That abstracts *within* Converse, but callers still assume a single
response shape, and the incoming ensembling (ADR 0013) and degradation
(ADR 0014) work must treat several models uniformly and reason about a per-call
*outcome* (ok / throttled / timed-out / invalid / guardrail). Best practice #2
asks for an adapter that normalizes inputs and outputs across FMs. Scope was
confirmed with the human as **Bedrock model families only** (Claude, Nova) —
not cross-provider.

Alternatives: (a) leave `converse` as is and branch on model family in the
pipeline — spreads family knowledge across callers, rejected (SRP/OCP); (b) a
full cross-provider anti-corruption layer (Bedrock + OpenAI + Anthropic-direct)
— larger blast radius, new deps/credentials/IAM, rejected as out of scope;
(c) a **Bedrock-family `ModelAdapter`** that encapsulates per-family request
shaping and returns a normalized result + typed outcome.

## Decision
We will introduce a `ModelAdapter` interface over Bedrock Converse that
normalizes requests (text+image content blocks, `inferenceConfig`,
`guardrailConfig`) and responses (`text`, resolved `model_id`, `usage`,
`stop_reason`, guardrail intervention), and returns a typed per-call
**outcome** (`ok | throttled | timed_out | invalid | guardrail_intervened`).

- The current `converse` envelope becomes the Claude/Nova implementation behind
  the interface; family-specific quirks (image-block shape, system-prompt
  placement, structured-output mode) live inside the adapter, never in callers.
- The adapter preserves the frozen invariants: one app-level call (C2 — no
  nested retry), no legacy completions contract (ADR 0001), `guardrailConfig`
  passthrough (ADR 0008), resolved id recorded (ADR 0001).
- Ensembling, degradation, the breaker, and metrics consume the normalized
  result + outcome — they never see a raw Bedrock response.

## Consequences
Good: one place owns model-shape knowledge (DIP/OCP); ensembling/degradation
become simple compositions over a stable interface; the typed outcome is the
clean input the breaker (ADR 0012) and metrics (ADR 0015) need. Bad: one more
abstraction — a **G1** item, justified: it *buys* uniform multi-model
composition and a single outcome vocabulary; the simpler thing (branch on family
in the pipeline) was rejected because ensembling would multiply those branches.
Cross-provider stays unbuilt; if a non-Bedrock provider is ever needed, this
interface is the seam to widen (revisit then, not now).

## Compliance
Fitness (offline): a contract test asserts one adapter interface; a grep/AST
check asserts no caller branches on a model-family string outside the adapter;
regression tests re-assert C2 (one call), no completions contract, guardrail
passthrough, resolved-id record (AC-L2–L4); an unrecognized response shape
raises `AdapterError`, not `KeyError`, and routes to degradation (AC-L1); the
outcome enum is asserted for each injected Stubber case (AC-L5).

## Notes
Author: sdd-spec (model-resilience increment)
Approved by / date: Rajnish Khatri / 2026-09-21
Superseded date:
Last modified: 2026-09-21 / new
