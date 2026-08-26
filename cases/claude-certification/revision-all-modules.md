---
type: notes
title: 'Revision sheet: all five modules'
description: 'Condensed exam-prep summary of all five Claude Architect modules — the core frameworks, decision rules, failure traces, and takeaways of each, plus the cross-module through-lines.'
tags: [claude, certification, revision]
---

# Revision sheet — all five modules

One condensed section per module: the frameworks worth memorizing, the
decision rules, the named failure traces, and each module's five takeaways.
Deep detail lives in the topic sub-bundles; quiz practice for Modules 1 and 5
lives in the [mixed quiz](quiz-mixed-platform-team-enablement.md).

---

## Module 1 — Platform design ([bundle](platform-design/index.md))

**Four design decisions before you build:** what Claude owns, the shape of
the work (pattern), which reference architecture you commit to, and where the
work interacts with Claude (entry point).

**The four properties architects design around** — each pairs a capability,
a limitation, and a mitigation; none is a flaw to fix:

| Property | Design consequence |
|---|---|
| Next-token prediction | Non-determinism; paraphrase sensitivity — safety-critical facts need a deterministic layer |
| Knowledge | Training cutoff; knowledge boundary — ground with retrieval, verify claims against sources |
| Working memory | Context is a finite, *degrading* resource — a ceiling, not a target; long multi-entity sessions cross-attribute |
| Steerability | Instruction reduces, never eliminates; confidence is not validity |

**Decomposition** (before architecture): split work into Claude / existing
systems / humans. Computable rules stay in code (Claude may *invoke* the
tool, never *be* the rules engine). Irreversible, high-stakes,
accountability-laden decisions get existing logic + human sign-off.
Over-assigning to Claude is the most common and expensive early mistake.

**Pattern selection** — augmented LLM → workflow → agent is a spectrum of
*autonomy granted*. Five factors in sequence: predictability, error cost,
observability, latency, cost — the first that rules a pattern out decides.
Key trap: **input variability is not path variability** (messy inputs ≠
agent; if the procedure is fixed, use a workflow with deterministic gates).
Workflow sub-patterns: chaining, routing, parallelization,
evaluator-optimizer (the last fits open-ended quality, not procedural
correctness).

**Seven primitives:** tools, MCP, subagents, hooks, skills, agent teams,
dynamic workflows. **Three platform layers** (don't collapse them): entry
points (what a person touches), build-time interfaces (how engineers
program), delivery routes (where API traffic terminates — Direct API,
Bedrock, Vertex, Foundry).

**Reference architectures — the biggest misapply:** retrieval asked to own
**transactional live state** that a tool call to the system of record should
own. Symptom signature: confident wrong answers, no errors, normal latency.
Shorter re-index narrows the staleness window but never closes it.

**Model & context strategy:** Sonnet default; every swap gated by evals.
Distinguish context window / retrieval / persistent state / summaries.
Context strategies: monolithic, progressive, retrieval, compaction.

**RAG pipeline:** chunk by corpus structure (fixed-size, semantic,
hierarchical — tables travel with their explanations); index by query pattern
(dense for concepts, sparse/BM25 for exact tokens, hybrid for both);
reciprocal rank fusion is the defensible merge default. Chunking failures and
indexing failures are *independent* — diagnose separately.

**Prompt caching:** caches match on **prefixes** → order static-first,
dynamic-last, by how widely each block is shared. Anything downstream of
changed content is invalidated regardless of breakpoints.

**Multi-agent:** orchestrator decomposes and synthesizes; subagents own
scoped units. **Subagent failure is recoverable** (orchestrator survives —
completeness-check, retry, or flag; never silently synthesize around a gap).
**Orchestrator failure is structural** (the repair component is the failed
component) — its mitigation must sit *outside*: deterministic validation of
the plan before fan-out.

**Entry-point governance:** compliance constraints don't score options —
they **eliminate** them; what survives is the answer. Prefer architectural
controls (don't expose the tool) over policy (ask users to refrain).

**Failure traces:** deterministic-drift (a must-be-right threshold folded
into Claude; 41 misroutes surfaced at audit, not in monitoring — fixed gates
verify only what they encode; pair with sampled review),
flexibility-nondeterminism (agent chosen for unknown flexibility; traces
showed four enumerable paths — autonomy became a compliance gap),
watch-fan-out (synthesis counted returned results, not dispatched units —
coverage assumed, not verified).

**Five takeaways:** decomposition before architecture; pattern = autonomy
granted; tested reference architectures before invention; Sonnet default with
every swap gated; entry point chosen by the work, not the shelf.

---

## Module 2 — Enterprise integration & production ([bundle](enterprise-integration-production/index.md))

**Evals as acceptance criteria:** write the eval suite *before* production
code; it gates every model swap and prompt revision. Three grader kinds:
code-based (deterministic checks — prefer wherever behavior is unambiguous),
model-based (judgment calls), human review. Keep the golden dataset current
with every system change — a suite frozen at launch measures the past.

**POC → production:** a demo hides cost at volume, the token tail, p95
latency, and retries/fallbacks/circuit breakers. Model volume and tokens
before committing to architecture; name the failure mode specific to your
architecture type and document its mitigation. Prompt caching on a stable
system prompt is often the load-bearing cost lever.

**Use-case sizing and feasibility:** run the four AI properties over every
use case; size call volume, token budget, model tier, sensitivity. Verdicts
come in three forms — feasible as scoped / feasible with constraints / not
feasible — and every constrained verdict names its **load-bearing boundary
condition**. A verdict without the constraint is not defensible.

**Enterprise integration patterns:** compliance eliminates entry points
first; then identity (server-side, never client-asserted), authorization,
data handling (minimum necessary data in the context window), observability
(instrumented at design time, not after the first incident).

**A/B testing & observability:** hypothesis, assignment, primary metric, and
sample size *before* the split; shadow-test when exposure is too risky. At
scale: per-request tracing separate from aggregate dashboards; a translation
layer maps technical metrics to the business metrics stakeholders care about.

**Failure traces:** demo-cost-profile (POC bill treated as the production
cost model), eval-wrong-thing (ten familiar contracts, never updated),
fifty-session-winner (underpowered sample, uncontrolled inputs, metric chosen
after the fact), pii-in-prompt (SSN in the user message; request logs
captured PHI the task never needed), scoping-skipped-constraints (capability
confirmed before volume/length/latency were gathered).

---

## Module 3 — Responsible AI ([bundle](responsible-ai/index.md))

**Safety is a stack, not a setting.** Four layers: trained behavior →
system-prompt instruction → runtime screening → authorization. Training
reduces broad harm but never saw your domain policy — the dangerous failure
is silent: assuming Claude enforces a rule that doesn't live in a layer.
(Trace: trained-refusals-as-policy — refusals passed review, so nobody
encoded the cross-unit disclosure rule.)

**A guarded path has three control points:** input screening, output
screening, and tool-call authorization — they answer different questions;
one output filter covers none of the others (trace: output-filter-as-design —
the refund tool ran before anything checked the request). Chain model-based
and deterministic checks. **Fail closed** when a guardrail errors — a
guardrail that silently passes traffic is the appearance of protection
without the function.

**LLM risk catalog:** direct and indirect prompt injection, token-budget
exhaustion, tool/action abuse, data exposure. Walk the request path to write
the assessment.

**Fairness is instrumented, not assumed.** Four injection points you own:
corpus, prompt framing, few-shot examples, downstream routing. Vendor
fairness evals don't cover them (trace: fairness-as-vendor-problem — skew
entered through an unmonitored retrieval corpus). Log every decision; if you
cannot reconstruct an explanation, you cannot provide one.

**Route review by stakes, not volume:** confidence, reversibility, cost of a
wrong answer decide what a human sees; place review pre-action, post-action,
or sampled; give the reviewer the inputs *and* the flag reason. Routing
everything floods the queue until review collapses into approval (trace:
routing-everything — 400 items/day, an approve button, no context).

**Compliance register:** a regulation states an outcome; you supply the
control, a **named owner**, and a **living evidence artifact** revalidated
over time. A compliant entry point is a *prerequisite*, not proof (trace:
entry-point-as-compliance — no owner, no artifact; a logging change wrote
metadata to a second region and surfaced at audit). A control with no owner
and no evidence goes non-operational and fails when it matters.

---

## Module 4 — Stakeholder engagement ([bundle](stakeholder-engagement/index.md))

**Discovery is structured elicitation, not a conversation:** listen,
translate, write down. Four question buckets turn a preference ("seamless")
into a testable constraint; one translation-table row per item keeps the
reasoning intact. Don't let discovery become design (trace:
discovery-became-design — two statements produced a sketch; licensed
authorization, PHI handling, and two-state retention never got asked).
An unsourced assumption is the item nobody remembers deciding.

**Tradeoff framing:** every choice presented as **gain, give-up, and
reversal cost** — approval without translated cost is not informed consent
(trace: uninformed-approval — four cents per call approved; the five-figure
invoice arrived as a surprise). A capabilities demo creates interest; only a
scenario-specific demo creates confidence.

**Feedback loops:** the decision layer *above* observability — signal →
trigger → owner → action. SLA thresholds trace to UX, criticality, or evals;
regulated checkpoints fire on a schedule, not only at a threshold. Dashboards
alone don't decide (trace: observability-replaced-loop — eval score drifted
from week four; the stakeholder noticed in week twelve).

**Documentation for handoff:** one document, three readers (handoff
recipient, auditor, returning Architect). Completeness test: can a competent
Architect who wasn't in the room make a safe change? Write the decision, the
**rejected alternatives**, and the tradeoff each resolved *while you still
hold the reasoning* (trace: rationale-in-head — the successor "fixed" latency
and reintroduced the residency violation the design had solved).

**Entry points & outcomes:** choose the route on latency, compliance, and
cost; multi-entry-point designs need an entry-point responsibility map. The
outcome document has six fields — scope, metric before, metric after,
auditable control, measurement owner, reuse potential — and its metric must
be one a CFO can defend (trace: wrong-metric-outcome — volume/latency/error
rate proved the system *ran*; the CFO asked what claim-processing time did).

---

## Module 5 — Team enablement ([bundle](team-enablement/index.md))

**Team setup — four decisions:** shared environment (baseline `CLAUDE.md`,
approved MCP servers, permission defaults — a shared asset with no version or
rollback is a liability), champion-and-batch rollout, Skills distribution,
spend posture.

**Champion-and-batch:** champions produce the enablement assets that don't
exist yet (hardened config, failure modes → runbooks, a nearby human per
batch); batching caps the blast radius of what you got wrong. Rollout is a
learning-system problem, not a distribution problem — all-at-once does the
learning in production, everywhere, simultaneously.

**Skills distribution — four mechanisms, each a governance posture:**
org-provisioned (mandatory, no opt-out), plugin (versioned, deliberate
pulls), project skill (travels with the repo, dies with the work), API skill
(the consumer is a program). Matching skill to mechanism *is* the governance
decision.

**Spend posture:** model defaults (Sonnet for routine), task-tier guidance,
caps, exception paths — part of the baseline, not something that settles.

**Developer workflows:** weave AI *inside* the existing editor / review / CI
/ test loop, not *beside* it (copy-paste round trips tax every interaction
and keep AI off the highest-leverage surfaces). Mandated adoption is
compliance; sticky adoption is the integrated path being easier.

**Review discipline — the verification checklist:** correctness against
intent, security (incl. dependencies), maintainability, and human
understanding. Each box is an action performed, not a field completed —
checkbox compliance with 3-minute reviews is ritual. Scale review depth to
blast radius; treat "nobody can explain this dependency" as stop-the-line.

**Operational support:** map user-visible symptoms to architecture causes
(healthy model metrics + no exceptions + generic fallback = a dependency the
model calls); capture them in runbooks; define escalation paths so the team
resolves recurring issues without the Architect.

---

## Cross-module through-lines

1. **The four properties are the master lens** — they drive feasibility
   verdicts (M2), decomposition (M1), risk assessment (M3), and sizing
   conversations with stakeholders (M4).
2. **Compliance eliminates before anything else scores** — entry-point
   selection in M1, integration patterns in M2, entry-point-as-prerequisite
   in M3, route selection in M4.
3. **Deterministic where computable, sampled review where not** — workflow
   gates (M1), code-based evals first (M2), chained guardrails (M3),
   verification checklists (M5). And every fixed check is frozen at writing
   time — pair it with ongoing sampled human/eval review.
4. **Confidence is not validity** — grounding narrows fabrication but never
   eliminates it; instruction reduces but never guarantees; a well-cited
   wrong answer reads exactly like a right one.
5. **Ownership makes controls real** — a control with no owner and no
   evidence (M3), a signal with no trigger-owner (M4), a checklist nobody
   performs (M5): all the same failure wearing different clothes.
6. **Write the rationale while you hold it** — rejected alternatives (M4),
   ADR-style decision records, runbooks (M5); the successor without them
   reintroduces the exact failure the design solved.
