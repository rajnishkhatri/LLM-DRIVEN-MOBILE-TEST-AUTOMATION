---
type: validation-walkthrough
title: 'Mixed quiz: platform design + team enablement'
description: '15 scenario-based questions mixing Module 1 (platform design) and Module 5 (team enablement), with full options, answers, and distractor analysis. Session result 15/15; full topic coverage of both modules.'
tags: [claude, certification, platform-design, team-enablement, quiz]
---

# Mixed quiz — platform design + team enablement

Revision record of the 2026-08-25 quiz session. 15 verbose, real-life scenario
questions alternating between [platform design](platform-design/index.md) and
[team enablement](team-enablement/index.md), each with four options where
distractors carry *real techniques attached to the wrong diagnosis*.
**Result: 15/15.**

## Coverage map

| # | Module | Topic |
|---|---|---|
| 1 | Platform design | Retrieval vs live state |
| 2 | Team enablement | Rollout triage: review discipline / spend posture / shared config |
| 3 | Platform design | Pattern selection (five factors) |
| 4 | Team enablement | Operational support: symptom → architecture cause |
| 5 | Platform design | Prompt caching mechanics (static-first ordering) |
| 6 | Team enablement | Skills distribution mechanisms |
| 7 | Platform design | Multi-agent failure asymmetry |
| 8 | Team enablement | Verification checklist as practice, not ritual |
| 9 | Platform design | Entry-point governance (constraints eliminate) |
| 10 | Team enablement | Developer workflows: inside vs beside |
| 11 | Platform design | Decomposition: Claude vs systems vs humans |
| 12 | Team enablement | Champion-and-batch purpose |
| 13 | Platform design | RAG chunking + hybrid indexing |
| 14 | Platform design | Four properties of Claude |
| 15 | Platform design | Deterministic-drift trace |

## Cross-cutting lessons (highest-yield for revision)

1. **Diagnosis before remedy.** The hardest distractors pair a genuinely good
   technique with the wrong diagnosis (Q9-B, Q14-A, Q15-A). Always separate
   "is this technique sound?" from "is this the actual lesson?"
2. **Category errors beat tuning errors.** Retrieval-over-live-state (Q1),
   probabilistic rules lookup (Q11d), LLM-as-rules-engine — no amount of
   tuning inside the wrong mechanism fixes the mechanism choice.
3. **Silent-success signatures.** Confident wrong answers + no errors + normal
   latency = the architecture is answering a different question (Q1, Q4).
4. **Controls must live where ground truth lives.** Orchestrator checks
   subagent completeness; decomposition validation sits *outside* the
   orchestrator (Q7); deterministic gates + sampled human review pair (Q15).
5. **Policy ≠ architecture.** No-trading enforced by *not exposing tools*
   (Q9) vs a policy hoping users refrain; org-provisioning *is* the no-opt-out
   control vs a mandatory-install memo (Q6).

---

## Q1 — Platform design: retrieval vs live state

**Scenario.** A telecom builds one RAG pipeline for its 900-agent call
center: the 12,000-doc knowledge base *and* nightly exports of the billing and
account databases indexed into the same vector store (hybrid dense+sparse).
Three months post-launch, the assistant sometimes states a balance or plan
tier contradicting the billing screen — no errors, normal latency.

- **A.** Move billing exports to 15-minute incremental re-index; add freshness timestamps so the model prefers the newest chunk.
- **B. (correct)** Category error, not freshness: plan/usage/balance are transactional live state owned by the billing system; indexed snapshots always answer from the past, and shorter refresh narrows but never closes the window. Split mechanisms — RAG for the stable knowledge base, tool call to the billing system of record for account lookups. The symptom signature (confident wrong answers, no errors, normal latency) is exactly how retrieval-applied-to-live-state presents.
- **C.** Weight BM25 higher for billing chunks via rank-fusion parameters so the correct snapshot outranks stale ones.
- **D.** Add a system-prompt constraint to cite retrieval timestamps and caveat answers older than 24 hours.

**Why the distractors fail.** A narrows the staleness window but keeps the
category error; similarity ranking can still surface an older chunk. C tunes
retrieval quality *within* the wrong mechanism — a perfect retrieval of a
snapshot still returns the past. D makes wrongness visible but shifts
verification onto 900 agents mid-call instead of fixing the architecture.

## Q2 — Team enablement: three incidents, three layers

**Scenario.** Six weeks into a 340-developer fintech rollout (12 champions,
batches of 40), three incidents land in one week: (1) an AI-generated ledger
refactor approved in 4 minutes silently changed an untested rounding rule;
(2) API spend tripled — batch-2 devs set Opus as default for lint fixes and
commit messages; (3) a batch-3 dev installed an unvetted community MCP server
with repo read + outbound network access. The VP says "pause the rollout —
AI code can't be trusted."

- **A.** One root cause (insufficient technical controls): CI gate on coverage delta, API-level Sonnet pinning, MCP allowlist block. Resume without process change.
- **B. (correct)** Three distinct gaps in the enablement layers: (1) review-discipline failure — 4-minute approval means comprehension never happened; enforce the verification checklist with review depth scaled to blast radius. (2) Spend-posture gap — baseline shipped without model defaults/task-tier guidance; publish defaults (Sonnet for routine) with caps and exception paths. (3) Shared-configuration governance gap — MCP servers are supply-chain surface; the baseline must carry an allowlist with a vetting path. Pausing wholesale misdiagnoses process gaps as a property of the technology.
- **C.** Roll back to the 12 champions (zero incidents), write runbooks for every failure mode, restart at half batch size.
- **D.** Fix review discipline and MCP vetting but treat spend as a developer judgment call that settles on its own.

**Why the distractors fail.** A automates past incident 1's essence — the
rounding change had *no test coverage*, so a coverage gate can't catch it;
comprehension is human. C is survivorship logic — champions were 12
self-selected enthusiasts. D waves off spend posture, which the module makes
part of the baseline, not something to "let settle."

## Q3 — Platform design: pattern selection, five factors

**Scenario.** Prior-authorization processing (4,000 independent requests/day):
extract fields from faxed PDFs, check against payer coverage policies
(quarterly updates), produce a packet for a human reviewer. Architect 1 wants
a full agent (flexibility); Architect 2 a workflow with a deterministic
validation gate between extraction and policy check; Architect 3 an agent
with tool-call logging hooks.

- **A. (correct)** Architect 2. The five factors: path is *predictable* (every request: extract → check → assemble), error cost high (clinical coverage decision), observability needs high (payer audits), latency/cost favor fixed steps. Agent autonomy buys nothing — the *inputs* vary, the *procedure* does not, and the module distinguishes those. The deterministic gate is exactly where workflows place validation.
- **B.** Architect 1: messy faxes need per-request flexibility; the agent can retry extraction, skip the policy check for clearly covered procedures, escalate ambiguity; the human reviewer caps error cost.
- **C.** Architect 3: agent flexibility + hook logging gets both benefits; parallel agents outperform a serial chain at this volume.
- **D.** Evaluator-optimizer: generator produces the packet, evaluator critiques against policy until convergence.

**Why the distractors fail.** B commits the input-variability ≠
path-variability fallacy, lets a probabilistic component decide when to
*bypass a control*, and leans on downstream reviewers who rubber-stamp
complete-looking packets. C's logging gives visibility into a nondeterministic
path when auditors need a *guaranteed* path; parallelization is a workflow
sub-pattern anyway. D misapplies evaluator-optimizer — it fits open-ended
generation quality, not procedural correctness a deterministic gate verifies
more cheaply.

## Q4 — Team enablement: operational support at 2 AM

**Scenario.** Sev-2: a freight-tracking assistant returns generic apologies
for ~30% of queries. On-call is from infra, has never touched the assistant.
Architecture: Claude via Bedrock + shipment-tracking API tool + RAG over
carrier policy docs + response filter suppressing unverified tracking claims.
Bedrock latency normal, no exceptions, no deploy in 72h; failures correlate
with one region.

- **A. (correct)** The runbook should map user-visible symptoms to architectural components: generic fallback + healthy model metrics + no exceptions means a dependency the model calls is failing, not the model. Regional correlation points at the tracking API's regional backend returning empty/degraded data — the tool "succeeds," the model gets nothing usable, and the response filter *correctly* suppresses the unverifiable answer, producing the apology. Escalate to the tracking-API team, not the AI platform team.
- **B.** Restart the assistant's pods first — 30% degradation with normal latency is a stale-connection-pool signature.
- **C.** RAG re-index: regional policy docs were dropped; the model refuses without grounding.
- **D.** Disable the over-triggering response filter temporarily; recalibrate in the morning.

**Why the distractors fail.** B is cargo-cult ops contradicted by the evidence
gathered. C misreads the data flow — "where's my freight" is a live-state tool
lookup, not a policy-doc retrieval; a RAG gap wouldn't correlate with shipment
region. D has an unfamiliar engineer disabling a safety control at 2 AM to
make symptoms disappear — the filter isn't malfunctioning.

## Q5 — Platform design: prompt caching mechanics

**Scenario.** Contract-review assistant, ~9,000 reviews/month across 200
clients. Prompt: static role/rules/format block (6,000 tokens, quarterly
updates), per-client playbook (~800 tokens), per-request contract
(5,000–60,000 tokens). Costs high, P50 latency 40% over target. Engineer
proposes caching with order: contract first, playbook, static block last,
breakpoint after the contract.

- **A.** Sound: caching the largest block (the contract) saves most; early context is weighted more; format instructions work best near generation.
- **B. (correct)** Inverts the mechanics — prompt caches match on *prefixes*, so order must be static-first, dynamic-last. The contract changes every request; placing it first invalidates the cache on every call (near-zero hits). Correct order: static block first (cached across all requests), client playbook next (cached per client), contract last (never cacheable). Converts the 6,000-token static block from per-request cost to mostly-cached, cutting cost and latency.
- **C.** Skip caching; tier models instead (Haiku first pass, Sonnet escalation) — tiering optimizes dollars, caching pennies.
- **D.** Ordering is fine; just move the breakpoint after the playbook for per-session cache reuse.

**Why the distractors fail.** A's prompt-engineering folklore can't override
prefix mechanics — you cannot cache content that differs every call. C poses a
false either/or; restructuring is nearly free while a Haiku first-pass on
clause-risk analysis is a quality-sensitive change needing eval gates. D is
mechanically impossible — everything downstream of a changed prefix is
invalidated regardless of breakpoints.

## Q6 — Team enablement: skills distribution mechanisms

**Scenario.** 2,000-engineer insurer, four skills to distribute: (1)
claims-domain regulatory skill, mandatory for every claims-BU engineer, zero
opt-out; (2) testing-conventions skill wanted across BUs, maintained by one
staff engineer updating weekly; (3) repo-specific migration skill for a
6-month replatform; (4) document-formatting skill a production API product
invokes programmatically.

- **A.** Org-provision all four — central distribution is the only real governance; fragmenting creates shadow-IT surface.
- **B. (correct)** (1) Org-provisioned — mandatory, centrally pushed, no opt-out; only this mechanism guarantees it. (2) Plugin — versioned install/update; the maintainer publishes releases teams pull deliberately instead of silently changing under them. (3) Project skill — lives in the repo it serves, travels with checkout, dies naturally when the replatform ends. (4) API skill — the consumer is a program, not a developer's editor. Each mechanism trades reach against governance differently; matching skill to mechanism *is* the governance decision.
- **C.** Plugin-by-default for flexibility: (1) plugin + mandatory-install policy; (2) org-provisioned; (3) team-scoped plugin; (4) project skill.
- **D.** (2) copied per-repo as project skills so teams control their versions and the single maintainer stops being a bottleneck.

**Why the distractors fail.** A's uniformity isn't governance — fit is;
central org would own a 6-month repo skill's cleanup and misses that (4)'s
consumer isn't a dev environment. C's "mandatory-install policy" is a memo
hoping to be a control; org provisioning *is* the control. D trades one
maintainer bottleneck for permanent fork drift — the weekly-update signal
demands versioned central publishing.

## Q7 — Platform design: multi-agent failure asymmetry

**Scenario.** Competitive-landscape reports: orchestrator decomposes into
8–12 competitor subtasks, parallel research subagents, synthesis (~20 min,
~$14). Failure X: one subagent hit tool timeouts, returned empty; the
orchestrator synthesized anyway — the client's primary rival was absent.
Failure Y: the orchestrator produced a malformed decomposition (one competitor
split into three overlapping subtasks, two dropped); all subagents "succeeded";
the report was confidently wrong in scope.

- **A.** Same class, same fix: post-synthesis QA agent compares report vs request, regenerates on mismatch.
- **B. (correct)** Different in kind. Subagent failure is *recoverable* — the orchestrator survives it, so X's fix is orchestrator-level completeness checking (every planned subtask returned non-empty; retry, reassign, or explicitly flag the gap — never silently synthesize around it). Orchestrator failure is *structural* — the component that would detect and repair the problem is the one that failed, and subagents can't see the malformed plan from inside their subtasks. Y's mitigation must sit outside the orchestrator: deterministic validation of the decomposition against the request (planned list matches requested list, no overlaps) *before* fan-out, because downstream checks inherit the orchestrator's wrong frame.
- **C.** Missing retries: exponential backoff for X; run the decomposition twice and require agreement (self-consistency) for Y.
- **D.** Collapse to a single sequential agent — no coordination, both failures impossible by construction.

**Why the distractors fail.** A checks downstream of the wrong frame, burns
the full run before checking, and can't distinguish "omitted by failure" from
"no findings" without subtask-level data the orchestrator had. C's
self-consistency is still probabilistic where the needed check ("planned vs
requested list") is cheap and deterministic — never sample what you can
compute. D turns 20 minutes into hours, floods one context, and a single
agent can still drop a competitor from its own list — you've removed the layer
where you could check.

## Q8 — Team enablement: checklist as ritual

**Scenario.** Verification checklist (correctness, security incl.
dependencies, maintainability, reviewer comprehension) in every PR template.
Audit of 60 merged AI-assisted PRs: 60/60 checked off, median review 3
minutes, 11 contain a dependency nobody can explain, 4 contain out-of-scope
behavior changes approved without comment.

- **A. (correct)** The checklist became a ritual instead of a verification — checkbox compliance substituted for the acts the boxes name. 3-minute medians mean comprehension (item 4) never happened; 11 mystery dependencies slipped through a box that *names* dependency review. Remediate the practice, not the artifact: scale review depth to blast radius, require reviewers to state in their own words what non-trivial changes do, sample-audit merged PRs routinely, treat "nobody can explain this dependency" as stop-the-line. A checklist works only when each box is an action performed, not a field completed.
- **B.** Humans failed, so automate every item: static analysis, dependency-diff bot, conventional-lint, 10-minute minimum review timer.
- **C.** Over-application caused fatigue; require the checklist only on critical paths, exempt routine changes.
- **D.** ~75% clean is better than human baselines; fix the 15 PRs and keep monitoring.

**Why the distractors fail.** B's tooling helps as a supplement, but
comprehension is constitutively human — a review timer enforces the
*appearance* of understanding (ritual again, now with a timer), and the 4
scope drifts passed tests; only a human asking "why is this here?" catches
them. C deepens vs exempts backwards — blast-radius scaling means deeper
review on critical paths, not dropping the baseline that demonstrably wasn't
running. D normalizes unexplained dependencies (supply-chain surface) against
a baseline nobody measured.

## Q9 — Platform design: entry-point governance

**Scenario.** Bank wealth-management, 3,000 advisors. Constraints: 7-year
retention + compliance-searchable surveillance of every AI interaction; EU
client PII stays in EU infrastructure; AI may draft and inform but never
trade or move money. Options: (1) consumer app, (2) Claude Enterprise
(SSO, audit logs), (3) API into the bank's region-hosted advisor platform,
(4) Claude Code for internal developers.

- **A.** Option 3 for cost: API undercuts Enterprise seats; built governance equals bought governance, differing only in effort.
- **B.** Option 2: Enterprise ships audit logs + admin controls + SSO out of the box; building compliance features Anthropic sells is a build-vs-buy error.
- **C. (correct)** Option 3, because the constraints don't prefer it — they *rule out* the alternatives, which is how governance actually operates. Consumer accounts eliminated outright. Enterprise has audit logs, but the binding constraints are jurisdictional data routing (EU PII processed in EU infrastructure requires region-by-region control of the integration path) and integration with the bank's *existing* surveillance archive (compliance searches one archive, not a second vendor console). The trade prohibition becomes an *architectural* control — the integration exposes no trading tools — rather than a policy asking users to refrain. Option 4 serves a different audience.
- **D.** Entry point is UX; compliance is satisfied at the model layer via a data-processing agreement — pick what advisors prefer.

**Why the distractors fail.** B (the strong distractor) satisfies *a*
surveillance requirement but not *this bank's* — the requirement is
integration with what compliance already operates, and Enterprise can't route
a specific client interaction region-by-region. A reaches the right letter
through rejected reasoning: constraints decided this, not cost, and built vs
bought governance differ in assurance and audit burden. D's DPA governs the
vendor's obligations but can't reroute the bank's data, merge logs, or remove
trading capability — paper controls don't substitute for architectural ones.

## Q10 — Team enablement: beside vs inside the workflow

**Scenario.** 55-person backend guild, 89% weekly active Claude Code use —
but the pattern is hand-write code, paste into a separate chat for
review/tests, copy back, reconcile manually. CI, the review tool, and the
test runner have zero AI integration. A staff engineer proposes mandating
agent mode for all feature work next sprint.

- **A.** Right mandate, wrong timeline — two sprints with training.
- **B.** The pattern works; 89% WAU is exceptional; measure output quality and only intervene if it degrades.
- **C. (correct)** AI landed *beside* the workflow instead of *inside* it: every interaction costs a context switch and manual reconciliation, and the surfaces where the team actually works (PRs, CI, test runner) never see AI — the highest-leverage points are untouched. But the mandate repeats the same mistake in mirror image — imposing a workflow rather than integrating with one. Embed AI into existing surfaces (editor assistance, PR-level review, CI-integrated test generation), let champions demonstrate the integrated paths, and let copy-paste die because the integrated path is genuinely less effort. Mandated adoption is compliance; sticky adoption comes from the easier path.
- **D.** Procure AI-native review and CI platforms; integrating AI into pre-AI tools is bolt-on friction.

**Why the distractors fail.** A haggles over the schedule of an imposition.
B's skepticism sounds disciplined but defends a metric that measures logins,
not leverage, while reconciliation stays invisible to review. D converts an
integration gap into a platform-replacement project — switching costs are
themselves the adoption killer; the module says integrate into existing
workflows.

## Q11 — Platform design: decomposition

**Scenario.** Airline IROPS handling: (a) draft personalized rebooking
emails, (b) allocate scarce seats on alternate flights, (c) summarize the
disruption for ops, (d) issue meal/hotel vouchers per the published
entitlement policy. Designer proposes one agent with booking, voucher, and
email tools: "one incident — one agent end-to-end is cleaner."

- **A.** Keep the single agent; add one human approval gate on the full output bundle.
- **B. (correct)** (a) and (c) go to Claude — language tasks, low-stakes, reversible before sending. (d) goes to an existing deterministic system — entitlement is a published rules table (delay × fare class), and running a lookup through a probabilistic model converts a computable answer into a sampled one; Claude may *invoke* it as a tool, but the decision logic lives in code. (b) — irreversible (seats given are gone), high stakes, accountability-laden — belongs with existing allocation logic plus human sign-off, not model discretion. "One incident, one agent" optimizes architectural tidiness over the fact that the tasks differ on every axis that matters.
- **C.** Keep the agent; enable extended thinking for (b) and load the policy docs into context for (d).
- **D.** Claude gets (a), (c), (d) — the policy is published and citable — while (b) goes to a human alone.

**Why the distractors fail.** A's bundled approval is the rubber-stamp
pattern — a human accountable for decisions they couldn't realistically
inspect. C: deliberate sampling is still sampling; grounding makes a wrong
entitlement *well-cited*, not computed — confidence is not validity. D
discards the existing allocation logic that encodes most of (b), and hands
(d) to the model on exactly the grounds B's reasoning blocks.

## Q12 — Team enablement: champion-and-batch purpose

**Scenario.** 400-engineer healthcare-software company. CTO: "Enable it for
everyone Monday, send a training video. Champions are a slow-motion rollout
with extra steps — if the tool is good, people will figure it out."

- **A. (correct)** Champions produce the enablement assets that don't exist yet: the shared configuration gets hardened against real usage before 400 people inherit its defects; the champion cohort surfaces the failure modes that become the runbook and review-discipline guidance; each batch inherits working answers plus a nearby human who has hit their problem before. Batching caps the blast radius of what you got wrong — a bad permission default at 40 users is a config fix, at 400 an incident. The CTO treats rollout as a distribution problem (ship the binary); the module treats it as a learning-system problem — the *org*, not just the users, is what's being trained. All-at-once doesn't skip the learning; it does it in production, everywhere, simultaneously.
- **B.** Champions exist for advocacy — buzz and testimonials overcome resistance; batches sustain word-of-mouth momentum.
- **C.** At 400 engineers the CTO is right; champion-and-batch is for 1,000+ orgs where coordination dominates.
- **D.** Champions are procurement validation — usage data justifies license spend; once ROI is proven, batching is optional.

**Why the distractors fail.** B can't explain why champions must precede
configuration hardening — if advocacy were the product, buy posters. C
invents a threshold the module never states; unknown failure modes don't
scale down with headcount. D mistakes a byproduct for the purpose and strips
out enablement-capacity pacing — finance approving seats doesn't write
runbooks.

## Q13 — Platform design: RAG chunking + hybrid indexing

**Scenario.** Pharma regulatory archive, 30,000 docs: clinical-study reports
(300+ pages, nested sections with tables), FDA letters (2–4 pages,
self-contained), SOPs (10–20 pages, flat). Queries: conceptual ("surrogate
endpoint justification") and exact-reference ("21 CFR 314.126"). First build:
fixed 512-token chunks, dense-only. Failures: methods severed from their
tables; CFR citation searches miss docs dense ranks as unrelated; short
letters split mid-thought.

- **A.** 2,048-token fixed chunks + a better embedding model; keep the pipeline uniform.
- **B. (correct)** Two independent failures. Chunking: match strategy to document structure — hierarchical for the clinical reports (chunks respect the section tree; tables travel with their explanations), semantic/whole-document for the short self-contained letters, structure-aware for SOPs. Indexing: the citation failure is an indexing-mode problem — "21 CFR 314.126" is an exact-match token that dense embeddings blur into concept-space; add sparse (BM25) alongside dense, fused with reciprocal rank fusion. Hybrid serves both query populations with one index architecture.
- **C.** RAG is wrong for this corpus: metadata database for citations; load full 300-page reports directly into context for conceptual questions.
- **D.** Keep fixed chunks + 128-token overlap; prompt the model to always quote CFR references verbatim to force exact matches.

**Why the distractors fail.** A moves boundaries without aligning them to
structure, and no embedding quality fixes exact-match retrieval — the failure
is representational. C solves chunking by reintroducing it one level up: at
30,000 docs you need retrieval to pick which report to load (that's RAG), and
the context window is a ceiling, not a target. D's overlap is a palliative,
and a *generation-time* instruction cannot reach backwards into *retrieval* —
if the chunk never surfaced, there's nothing to quote.

## Q14 — Platform design: the four properties

**Scenario.** Hospital drug-interaction assistant (RAG over formulary +
pharmacology references). Validation findings: (1) for a post-cutoff drug
present in the corpus, fluent answers blending retrieved facts with plausible
unverified interaction claims; (2) in a 40+ turn multi-patient session, one
patient's renal impairment attributed to another discussed 30 turns earlier,
dosing advice shifted; (3) the same question, paraphrased, yields materially
different contraindication emphasis. Safety board asks: three bugs or one
systemic problem?

- **A.** One root cause — retrieval quality. Better embeddings, re-ranking, per-turn re-retrieval resolve all three.
- **B. (correct)** Neither bugs nor one problem — three constitutive properties surfacing, each demanding a system-level mitigation: (1) knowledge boundary × confidence-not-validity — the model generates fluently past what sources support; grounding narrows but doesn't eliminate; mitigate with citation-required output contracts + verification of interaction claims against the corpus. (2) Working-memory degradation — long multi-entity sessions invite cross-attribution; bound session scope per patient or summarize-and-reset. (3) Next-token nondeterminism — paraphrase sensitivity is inherent; safety-critical facts like contraindications must be surfaced by a deterministic layer (structured interaction lookup rendered into every relevant answer), never left to sampled emphasis. "Bugs" implies patches exist; the design answer is architecture that expects these properties.
- **C.** Stricter system prompt ("only state facts in retrieved passages") + fixed output template fixes 1 and 3; chunk the session to fit the window for 2.
- **D.** Upgrade to the maximum-capability model with extended thinking, then re-validate.

**Why the distractors fail.** A collapses three properties into one
component: perfect retrieval can't stop generation *beyond* what was
retrieved, and emphasis variance survives identical retrieval. C treats
instruction as elimination — the confidence-not-validity error at the meta
level; and transcript 2 wasn't overflow — the session *fit*; degradation is a
within-limits phenomenon. D shifts the rates of all three behaviors but
changes none of their existence, and swaps models without eval gates.

## Q15 — Platform design: deterministic drift

**Scenario.** Product-description workflow with deterministic gates (schema
check, banned-word regex battery, keyword check; failures auto-regenerate).
A year at ~2% rejection with clean spot-checks → human sample-audit scaled to
near zero. A model upgrade lands; rejection *drops* to 1%, no alarms. Six
weeks later: thousands of live descriptions subtly worse (generic, hedging,
recited attributes, house style gone) and a handful of legal capability
claims phrased in ways the regex never anticipated.

- **A.** The gates were fine; the team skipped the model-swap eval gate — that process failure is the lesson.
- **B. (correct)** Deterministic checks verify only what they encode, and what they encode is frozen while the distribution they guard is not. Schema/regex/keyword gates check *surface form* and were blind to the shifted *content* distribution — all of it schema-valid, regex-clean, keyword-present. The dropped rejection rate was a signal read backwards: 1% meant the new distribution tripped fewer of the old tripwires, including the legal phrasings the regex never anticipated. Deterministic gates bound only the failure modes enumerated at writing time; the trace's lesson is they must be *paired* with ongoing sampled human/eval review, because the probabilistic side drifts in dimensions no fixed check watches — and the team had dismantled exactly that pairing.
- **C.** Coverage was too narrow from day one: add style classifiers, hedging detectors, an LLM-judge gate — so human audit stays unnecessary.
- **D.** Fixed checks on sampled output are a fundamental mismatch; replace the gate battery with a judge-LLM review layer.

**Why the distractors fail.** A is half-right (a swap eval would have caught
*this* instance) but drift doesn't need a model upgrade — prompt edits, input
shifts, and spec-sheet changes move the distribution too; the upgrade was the
trigger, not the lesson. C answers "our enumeration was incomplete" with
"enumerate harder" and re-commits the original sin (human audit stays off);
any expanded battery re-freezes at its new writing time. D overcorrects into
abandoning deterministic gates — the module's position is both/and:
deterministic checks for what's computable, sampled review for what isn't; a
judge LLM as the *only* control puts sampling variance into the control layer
itself.
