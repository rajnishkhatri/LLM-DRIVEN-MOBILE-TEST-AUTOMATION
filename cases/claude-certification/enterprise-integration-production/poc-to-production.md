---
type: guide
title: 'From POC to production: cost, latency, and reliability'
description: 'A demo hides cost, p95 latency, retries/fallbacks/circuit breakers, and architecture-specific failure modes. Model volume and tokens before committing.'
tags: [claude, certification, enterprise-integration-production]
---

From POC to production: cost, latency, and reliability
Your eval suite tells you whether the system behaves correctly, but nothing about whether it can afford to behave correctly at the volume your partner expects. That gap is the Proof of Concept (POC)-to-production gap, and it has four dimensions: cost, latency, reliability, and failure modes. All four are invisible in a demo.

A POC also gives you the first signal on whether the system moves the business metric it was designed to improve. That signal is worth capturing deliberately: measure the outcome the partner cares about on your POC sample, even before you model production cost. A cost profile that fits the budget on a system that does not produce a measurable improvement in the metric that matters is still a failed deployment.

Where a Proof of Concept (POC) and a production system differ
A POC is designed to demonstrate capability. It runs at low volume, on clean inputs, and with a patient user. A production system runs at the volume your partner's business generates, on real inputs, and with users who have no tolerance for slow or incorrect responses. The four dimensions where a POC misleads you are cost, latency, reliability, and failure modes.

Dimension	Why it's invisible in a demo	What it looks like when it fails
Cost	A POC running 10–50 requests per day produces a negligible bill. Monthly cost projections at production volume are a different calculation entirely.	The billing dashboard shows a cost that exceeds the budget signed off at project approval. The architecture must be renegotiated after deployment.
Latency	A demo typically runs one request at a time. Latency p95 under concurrent load is a different number than median latency under a single request.	SLA breaches and user abandonment. Latency that is acceptable for a demo can be unacceptable for a real-time user-facing workflow.
Reliability	A POC has no retry logic, no fallback, and no circuit breaker. When it fails, the developer refreshes and tries again. There are no users waiting.	Without retry logic or fallback handling, any transient API failure takes the entire user-facing workflow down rather than degrading gracefully.
Failure modes	A demo is tested on inputs the developer expects. Production raises inputs the developer did not expect. Failure modes are specific to architecture type.	Silent degradation, made-up outputs on edge-case inputs, or complete failure on an input class that was never tested.
Cost and latency modeling: Know the numbers before you build
The cost and latency model is built before you finalize the architecture. The three inputs you need are call volume (requests per day or per month), token budget per request (input tokens plus expected output tokens), and model tier. From those three, you can estimate monthly cost and check it against your budget ceiling before any code is written.

The token budget per request is where most cost models go wrong. Teams calculate the average token count on the inputs they have and assume that is the distribution. In practice, token distributions are often skewed: most requests are short, but a tail of long requests consumes a disproportionate share of the total cost. A cost model based on average usage can significantly underestimate the cost impact of these longer requests, often by a factor of two or three.

Latency follows a similar pattern. Median latency reflects the middle of the pack, but SLA breaches are usually caused by slower requests at the high end. That is why p95 is a more useful design target than the median. P95 is the latency value below which 95% of requests complete. Only the slowest 5% fall above it.

Caching is the most effective cost and latency lever when the system prompt is long and stable. Prompt caching preserves the processed prompt prefix for the cached tokens, so the API does not reprocess them on subsequent requests. Savings scale with both the length of the cached prefix and how often it's reused. If, for example, cache reads are charged at 10% of the standard input token rate, a long prefix reused across many requests produces the largest effective savings. Find the most current cache read rate at platform.claude.com/docs/en/about-claude/pricing. The risk is consistency: if the cached content needs to reflect live state, caching creates a consistency window that may violate the requirements of the use case. What is stored is the prompt prefix.

Reliability controls: what to build into every model call
The reliability controls that belong in the production Claude system address different failure scenarios and sit at different layers of the call stack.

Transient error recovery with exponential backoff. When a model returns a transient error, such as a rate limit 429, timeout, or 5xx, the system should retry with progressively longer delays between attempts. This prevents a flood of retries from turning a brief hiccup into a prolonged outage. Set the maximum number of attempts and total wait time based on how much delay your use case can tolerate.
Fallback chains. If the primary model or endpoint is unavailable, the system should automatically route the request to an alternative such as a different model tier or a cached response. It should not raise an error to the user. Fallback behavior should be tested as part of your eval suite.
Circuit breakers. A circuit breaker measures the error rate on a downstream dependency and trips when errors exceed an established threshold. Once tripped, requests fail immediately rather than waiting for a timeout. This prevents one degraded dependency from taking down the broader system.
Reliability controls must sit at the right stage to be effective: new attempts belong close to the API call, circuit breakers at the service boundary, and fallback chains in the orchestration layer. Placing them in the wrong layer means protecting the wrong part of the system and leaving the right part exposed.

Failure modes by architecture type
Agents handle tasks that cannot be completed in a single model call: they can use tools, observe results, adjust plans mid-execution, and complete multi-step processes that require dynamic reasoning at each step. Claude Code is a production example, and it navigates codebases, runs tests, applies fixes, and iterates across a workflow that is impossible in a single-turn architecture. The controls below govern how to build these systems reliably.

Architecture	What breaks first	Mitigation
Agent	Unbounded tool use and growing context. An agent that can call tools without budget constraints or turn limits will run up cost and latency in ways that are invisible until a single request exceeds the budget ceiling.	Set per-turn token budgets, maximum tool call counts, and explicit stopping criteria. Constrain the tool set to the minimum required. Eval the agent's stopping behavior, not just its output quality.
RAG (retrieval-augmented generation)	Retrieval quality drift. The retrieval layer degrades when documents are added or removed from the index without reindexing, when the query and the document representation fall out of alignment, or when the index is refreshed on a schedule that creates staleness for live-state queries.	Keep retrieval quality in the eval loop. Monitor retrieval precision and recall as system metrics, not just output quality. Separate live-state queries from static knowledge queries.
Document processing pipeline (Evaluator-optimizer)	No exception path for low-confidence extractions. A pipeline that routes all documents through the same flow regardless of extraction confidence will produce wrong outputs on edge cases at the same rate it produces correct outputs on clean documents.	Add confidence scoring to the extraction step. Route low-confidence extractions to a human review queue rather than downstream processing. Include edge-cases and difficult documents in your eval set.
Orchestrator-workers	Failure boundaries between orchestrators and subagents blur, traces fragment, and a dropped subagent can fail silently at synthesis.	Define recoverable (subagent: retry or flag) versus unrecoverable (orchestrator) boundaries. Create a shared trace ID across all agents. Reconcile coverage at synthesis so results equal the units submitted.
COST · COMPLEXITY · RISK
Cost: Don't assume your proof-of-concept costs will match production. Model costs before committing to an architecture, rather than after the first billing cycle.
Complexity: Retries, fallback chains, and circuit breakers are much harder to add to a system that wasn't designed for them. Build reliability in from the start rather than scrambling to fix it after the first production incident.
Risk: A system with no fallback and no circuit breaker has one point of failure: the primary model endpoint. When that endpoint goes down at peak load, there is no recovery path, the entire user-facing workflow fails instead of degrading gracefully.
MODEL VERSION PINNING
Note: Model version pinning applies to every architecture in the table above equally. It is an operational discipline, not an architecture choice. Pin model versions in your configuration, monitor the Anthropic model deprecation page at platform.claude.com/docs/en/about-claude/model-deprecations, and maintain a version-update runbook.
← Previous
Screen 5 of 21
☰ CONTENTS
Next →
