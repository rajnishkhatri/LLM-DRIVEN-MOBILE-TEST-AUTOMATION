---
type: notes
title: 'Ari v2 — enhancement and implementation plan'
description: >-
  Implementation design for Ari v2 on the existing hexagon. Three pillars
  (overlap, the model gateway, token-scoped reads and confirm-before-write),
  the functional and non-functional requirements, what stays out of scope,
  and an eight-step build sequence that keeps the twelve eval gates green.
tags: [ripple, ari, architecture, plan]
---

# Ari v2 — enhancement and implementation plan

Ari stays one process. The four tiers in the brief are layers inside the
hexagon that already exists: the embed contract, the identity gate, the
stage-0 router plus `ModelPort`, and the adapters. Stage-0 remains the
decider. A stage-0 hit does not call the model.

This note is the implementation design for the enhancement that lands before
the CAB. It records the requirements, the decision behind each pillar, and
the ordered build. It does not change `ari/build/`. The ADR amendments it
drives are named at the end and staged in the ADR files (dated 2026-10-03);
the code that implements them is the eight-step build.

The previous draft of this file is retired. It specified its own `app.py`,
a Redis cache, per-session dollar figures, and tickets created inside the
first turn. None of that is in the running demo, the worksheet, or ADR
0001–0003.

## SCQA

**Situation.** Four product surfaces (Forecasting, Onboarding, Analytics,
Support) and three backends (Omni, docs, Jira). One pipeline in
[`ari/build/ari_demo/app.py`](../../ari/build/ari_demo/app.py) already
composes them: identity gate, entitlement pre-check, stage-0, classifier
fallback, a guarded adapter call, synthesis, decision log.

**Complication.** A sentence outside the 72-row golden set still gets a
confident route, a write, or a provenance row the ADR does not mean. The
panel sentence "My March forecast variance jumped and I think bank mapping
is wrong. How do I fix it?" was run live on 2026-10-02: stage-0 returns
HOWTO at score 1.0 on rule `h-how-do`, and synthesis emits an empty answer
at confidence 1.0. Separately, a ticket route calls `TicketPort.create` on
the same turn, and the docs adapter accepts a `RequestContext` it never
reads.

**Question.** How do the three pillars land on that spine before the CAB,
with the twelve gates in
[`ari/evals/eval-spec.md`](../../ari/evals/eval-spec.md) §9 still green?

**Answer.** Three changes, each proved by existing gates plus new
build-failing assertions (routing *and* answer shape, not a single new
assertion per change). The build order is the eight steps at the end of
this note. One part of the Complication is only partly closed: F2 reroutes
the March sentence away from a confident HOWTO, but the
empty-answer-at-confidence-1.0 path stays live for a *pure* how-to miss that
trips no data phrase. That residual is named in Out of scope, not hidden,
and it is not one of the three changes.

## Requirements

The enhancement is partitioned into three categories. A behavior sits in
exactly one of them.

### Functional requirements

What the system must do on a turn.

| # | Requirement | Where it lands | Proof |
|---|---|---|---|
| F1 | A stage-0 match of **one** capability still returns that route and does not call the model. | [`stage0.py`](../../ari/build/ari_demo/router/stage0.py) `route_stage0`; [`app.py`](../../ari/build/ari_demo/app.py) `_route` | Gates 1–2 stay green on the 72. |
| F2 | When **more than one** capability fires, stage-0 does not return score 1.0. The turn emits a `CapabilityPlan` when every fired capability is a read, or exactly one clarify when a write fired or the reads are mutually exclusive. The branch is computed from the fired set, not left to the implementer. A `CapabilityPlan` is not a confident answer (its confidence reflects which reads returned content); a clarify carries no answer confidence. | `route_stage0` overlap rule; new type in [`types.py`](../../ari/build/ari_demo/domain/types.py) | Held-out utterances, including the March sentence, asserted **outside** the 72 (routing and answer shape). A build-failing **negative** assertion: a single-capability how-to that only brushes a data phrase still routes single-capability. Gates 1–3 stay green on the 72. |
| F3 | A clarify is recorded as `Route.CLARIFY`. Provenance, the decision log, and the CLI flag agree. | `Route` enum; `Pipeline.handle` stops passing `Route.OUT_OF_SCOPE` for a clarify | Gate 11: the tuple is complete, and the route field is CLARIFY. |
| F4 | A data answer's text is the fixture value (memo quoted as data). Synthesis does not call `ModelPort` on `Route.DATA`. | [`synthesis.py`](../../ari/build/ari_demo/synthesis/synthesis.py) DATA branch | New assertion: answer text equals the fixture value. Gate 11 still complete, with model version recorded as the explicit "no model" marker. |
| F5 | Omni and docs return only rows the token can see, including when the utterance names no tenant. A chunk is returned only when the token is entitled to it; a chunk that is neither tenant-stamped nor explicitly marked shared is **withheld** (default-deny). | [`omni.py`](../../ari/build/ari_demo/adapters/omni.py) already scopes by `ctx.tenant`. [`docs.py`](../../ari/build/ari_demo/adapters/docs.py) must start reading `ctx`. | Gate 6, extended two ways: a query that never says "Acme" cannot surface `CANARY-ACME-7719` or a tenant-stamped doc chunk; **and** an un-annotated chunk (no stamp, no shared marker) is withheld cross-tenant. A fixture-lint flags any un-annotated chunk. |
| F6 | A ticket route returns a draft. `TicketPort.create` runs on the confirm turn. A cancel does not call `create`. A repeated confirm returns the same ticket id, because the idempotency key is anchored to the **draft**, not to the confirming turn. | [`app.py`](../../ari/build/ari_demo/app.py) TICKET branch; [`ticket.py`](../../ari/build/ari_demo/adapters/ticket.py) keeps C9 | Gate 8: exactly one ticket, on the confirm turn. |
| F7 | Docs retrieval and the Jira call sit under the guarded wrapper. A timeout or an explicit cancel stops the call. The ticket **write** is not retried. | [`guarded.py`](../../ari/build/ari_demo/resilience/guarded.py), called from the docs path and the confirm path | Gate 10: injected timeout still degrades with a deterministic ticket offer. |
| F8 | One extra read source (a status page, **served from a fixture** so the demo stays offline and deterministic) is dispatched from a registry. Adding it does not add a branch in `app.py`. | New adapter behind a read port; registry in the composition root | Gate 12: imports still point inward; the new source is invisible to `domain/` and `ports/` callers that do not ask for it. |
| F9 | The CLI carries `turn_id` and a pending draft so the confirm turn is a second call with the same conversation and a new turn id. The CLI runs one conversation as a single long-lived session, so the pending draft the pipeline holds survives from the draft turn to the confirm turn. | [`app.py`](../../ari/build/ari_demo/app.py) `main` | Gate 8 drives the pipeline directly (two `handle` calls): the draft is visible in the first response; `create` is absent until the confirm call. |
| F10 | `RequestContext` carries the product surface (Forecasting, Onboarding, Analytics, Support) so a later spend report can attribute a turn, and so the decision log records which product asked. v2 records the field. v2 does not compute spend. | [`types.py`](../../ari/build/ari_demo/domain/types.py) `RequestContext` | Gate 12's frozen-context test still passes, and Gate 11's tuple stays complete with the surface recorded. The field is defaulted so existing constructors keep compiling. |

F1–F4 are the performance pillar. F10 is the economics pillar (what the
model gateway is allowed to spend, and what a turn records so spend can be
attributed later). F5–F9 are the compliance pillar. The split is by the
constraint that forces the change. F4 sits with performance, not economics:
the data path skips the model so a number cannot be rephrased — a
groundedness and latency gain that Pillar 1 decides, builds, and gates. The
economics reading (a governed model call not spent on a data turn) is real
but secondary, and it is not where F4 is proved.

A how-to cache, in any form, is **not** in v2. It is deferred with a stated
forcing function (see Storage and Out of scope), so the pillar's own
build-when-a-gate-fails discipline applies to it too.

### Non-functional requirements

How the system must behave while doing F1–F10. Measures below are the ones
already committed in the worksheet, the eval spec, or the code. No new
latency, cost, or availability number is introduced here.

| Characteristic | Requirement for v2 | Committed measure | Decision |
|---|---|---|---|
| **Security** (worksheet #1) | Every adapter filters by the token it was given, default-deny. The phrase list in [`entitlement.py`](../../ari/build/ari_demo/core/entitlement.py) stays as the pre-model refuse/narrow, and it is no longer the only control. | Gate 6: 0 violations, build-failing, including the un-annotated-chunk case. | Confused-deputy control lives in the adapter, because a query that names no tenant never trips the phrase list. [`omni.py`](../../ari/build/ari_demo/adapters/omni.py) already loads one tenant file. Docs must do the analogous filter, and must withhold a chunk it cannot prove is shared. |
| **Testability** (worksheet #2) | Each build step keeps the twelve gates green and adds its assertion(s). Held-out sentences are not folded into the 72 to make a sweep look finished. | Gates 1–12 in eval-spec §9. | The March sentence is a held-out, build-failing assertion — not folded into the 72. The sweep still defends only the rows it contains; the held-out and negative assertions defend the sentences it cannot see. A green build means the asserted cases hold, not that the misroute class is closed (assumption 4). |
| **Auditability** (worksheet #3) | Every answer, including a plan, a clarify, a draft, and a degraded turn, carries a complete provenance tuple. A clarify's route field says CLARIFY. | Gate 11: 100% of answers. | `Route.OUT_OF_SCOPE` remains the refusal route. Overloading it to mean "we asked a question" makes the decision log reconstruct the wrong act. One known residual (empty-answer-at-1.0 on a pure how-to miss) is disclosed in Out of scope, not claimed as closed. |
| **Fault tolerance** (worksheet #4, elevated) | A timed-out or cancelled docs or Jira call degrades that capability. The conversation continues. The model does not invent the missing content. | Gate 10. | `guarded_read` already wraps Omni. Docs and the Jira confirm call join that wrapper. Retry stays on idempotent reads (ADR 0001, C2). The ticket write stays single-shot plus the C9 replay. |
| **Extensibility** (worksheet #5, demoted below auditability) | Source N+1 is an adapter plus registry entry plus golden rows. | Gate 12: imports point inward. | The status page is the one source added in this sequence, because the panel question is already that source. It is a read, served from a fixture so the demo stays deterministic. It does not justify a new route enum value unless the sweep says the existing routes cannot name it. |
| **Responsiveness** (worksheet #6) | A stage-0 hit makes no model call. On the data path, answer time follows the backend the adapter just called. | The worksheet marks volume and SLO `needs-input`. The v2 promise is the absence of a model call, which is assertable in a test by observing that `ModelPort.generate` was not invoked. | A millisecond SLA is not set. Setting one would launder a `needs-input` into a commitment. |
| **Cost-efficiency** (worksheet #7, first to cull) | Routing on a fast-path hit stays off `ModelPort`. The product surface is stored so a later report can attribute spend per surface. | ADR 0002: the model is config behind the port; a swap is a release. | No token price, no per-session dollar figure, no multi-model router. ADR 0002 already rejected multi-model-per-turn until there is a traffic signal. |
| **Deployment shape** | One process. Adapters are in-process objects behind ports. | ADR 0001 topology: one quantum, hexagonal, dependencies inward. | A second deployable (a serverless function per adapter, a separate model service) waits until a characteristic actually diverges — a latency budget, a scaling limit, or a trust boundary the worksheet does not yet have. |
| **Storage** | v2 adds **no store**. A how-to cache behind `DocsPort` is deferred until a latency or volume gate forces it; the stale-citation risk it would guard is already covered by provenance recording the doc version. | F2 in the eval spec treats a stale version citation as an ungrounded answer; provenance carries the version with no cache. | A new datastore is a new operational quantum (backup, tenancy, eviction), and no volume signal pays for one yet. The deferral matches the vector-index and datastore rule below. |
| **Retrieval** | Docs stay keyword match over fixtures, behind `DocsPort`. | Gate 4: citation presence 100% on how-to rows in the 72. | A vector index is a later adapter behind the same port, built when a retrieval-quality gate fails on real passages. Choosing an engine now would freeze a dependency the fixtures do not exercise. |

### Out of scope

Explicitly not solved in this enhancement.

- **Millisecond SLAs, token-cost percentages, per-session dollar figures, and a load-test result.** The worksheet lists volume, latency, and residency as `needs-input`. Publishing a number here would be a fabricated commitment.
- **A how-to cache, in any form — port, in-process dict, or Redis.** v2 adds no cache. There is no latency or volume signal that would pay for one, and the stale-citation risk a stale cache would introduce is already covered by provenance recording the doc version. A cache behind `DocsPort` is a later decision, built when a latency or volume gate fails — the same rule the vector index and a datastore follow.
- **A vector engine.** Same reason as retrieval above. The port can take one later; v2 does not select one.
- **Zero-shot or classifier-primary routing as the MVP.** ADR 0001 keeps stage-0 first. Reversing that is the dial already described in the ADR (threshold past 1.0), and it re-opens cost, latency, and injection posture. It is not a v2 step.
- **80% deflection as a CAB target.** Eval-spec §10: deflection is not resolution until the baseline and the definition come from Dana. v2 does not adopt the number.
- **A second `app.py`, a second deployable, or a serverless split.** The composition root stays `Pipeline`.
- **Implementing `ActionPort`.** ADR 0003: contract only. Gate 9 keeps approval unbypassable against the unimplemented port. Phase-2 payment or forecast execution stays unbuilt.
- **The other named warts in the code tour.** Orphan line after doc sanitizing, hostile memos with no review flag, the two `DEGRADED_COPY` strings, and the classifier floor 0.6 with no sweep receipt. They stay visible. They are not steps in this sequence.
- **HOWTO no-match honesty as its own step.** A pure how-to miss still returns an empty answer at confidence 1.0 in [`synthesis.py`](../../ari/build/ari_demo/synthesis/synthesis.py). The March sentence is fixed by F2 (it stops being a confident HOWTO), which leaves the empty-docs path for a later assertion. This residual sits against the Auditability characteristic — a complete tuple over empty content reads as audited but is ungrounded, the "provenance row the ADR does not mean" the Complication opens with. It is disclosed here rather than hidden, and closing it is the first follow-on after v2. Folding it into this pass would add a behavior the eight steps do not prove.
- **Live Bedrock and judge calibration.** Gate 5 stays unauthoritative until the labeled slice exists. v2 does not pretend to unlock it.
- **An embeddable SDK, streaming transport, or a new chat UI.** The demo entry remains the CLI.

## Pillar 1 — Performance

**Decision.** Overlap does not short-circuit. One Tier-A capability wins
outright only when it is the only capability that fired. If another
capability also fired, the turn emits a `CapabilityPlan` when every fired
capability is a read, and one clarify when a write fired or the reads are
mutually exclusive — a rule the router computes from the fired set, not a
judgment left to the implementer. The overlap rule generalizes the
*response* across every Tier-A rule; it does **not** generalize *detection*
— overlap can only fire when both capabilities already have phrases in the
stage-0 table. Data answers are built in synthesis from the fixture and do
not call `ModelPort`.

**v1 evidence.** In [`stage0.py`](../../ari/build/ari_demo/router/stage0.py),
a single Tier-A capability returns `RouteDecision(..., score=1.0, margin=1.0)`
before any weighted score is computed. [`rules.py`](../../ari/build/ari_demo/router/rules.py)
marks `h-how-do` (`\bhow do (i|you|we)\b`) as Tier A. The March sentence
matches that rule and no DATA rule: `variance` and `forecast variance` are
not in the stage-0 table (they exist only as a classifier hint in
[`classifier.py`](../../ari/build/ari_demo/model/classifier.py)). So the
short-circuit is sufficient to finish the sentence as HOWTO even when the
product meaning is compound — the brief's research note treats that
sentence as Omni plus the bank-mapping article plus a ticket offer. The
72-row sweep never contests `h-how-do`, which is why gate 1 can be perfect
and the sentence can still be wrong. On the data path,
[`synthesis.py`](../../ari/build/ari_demo/synthesis/synthesis.py) calls
`_through_model` with the fixture text. Offline that call echoes the
prompt; the call is still a `ModelPort` dependency on every data answer.

**v2 change.**

1. `route_stage0` collects every capability that fired. `len(tier_a) == 1`
   is decisive only when no other capability fired at all. Otherwise the
   function returns a fall-through the pipeline maps to a `CapabilityPlan`
   when every fired capability is a read, or to `Route.CLARIFY` when a write
   fired or the reads are mutually exclusive. The branch is computed from the
   fired set.
2. Detection is phrase-bounded, and the plan says so plainly. The overlap
   rule fires only when both capabilities already have phrases in the stage-0
   table, so the March sentence needs a second signal: add a Tier-B data
   phrase for `forecast variance`, then re-run the existing sweep. This fixes
   the *response* for every Tier-A rule at once; it does **not** fix
   *detection* for a future compound sentence whose second half is
   unregistered — that still needs its phrase, or the classifier hint fed
   into the overlap check (named here as the next move, not a v2 step). Gate
   1's bar is unchanged (≥ 99% on the 72, sweep report recommitted if θ or
   margin moves). The March sentence is asserted in a held-out test, not by
   inserting it into the 72. A build-failing **negative** assertion guards
   the other direction: a single-capability how-to that only brushes the new
   phrase must still route single-capability. Q-032 ("And how do I set a
   lower limit just for interns?") stays a single-capability HOWTO: it does
   not contain the new phrase.
3. The DATA branch of `synthesize` copies `OmniRow.value` and the memo
   line. It does not construct a `ModelRequest`.

**Gate.** Gates 1–3 on the 72, plus the held-out March assertion and the
build-failing over-clarify negative assertion (F2). The fixture-value
assertion (F4).

**Tradeoff.**

| Choice | Alternative | Why this one | What it costs |
|---|---|---|---|
| Overlap rule for every Tier-A rule | Carve only `h-how-do` down to Tier B | A carve fixes one pattern. The next decisive phrase (`h-what-do-mean`, `h-settings-page`) can do the same thing the day a second capability shares the utterance. The rule is one policy in the router, which is the open/closed place for it. The generalization is of the *response*; detection stays bounded by the phrase table, which the next move (classifier hints into overlap) addresses. | A clear "how do I" that also brushes a data phrase will clarify or plan instead of answering immediately. That is the point of the margin on the 72; a build-failing negative assertion guards that direction (a single-capability how-to brushing the new phrase still routes single), and the held-out set is where we watch the rest. |
| `CapabilityPlan` when every fired capability is a read; one clarify when a write fired or the reads are mutually exclusive | Always clarify | The branch is a rule the router computes from the fired set, not a judgment call — which keeps ADR 0001's "never guess" honest at the new branch too. The March sentence is a compound read request (numbers and the mapping article): a plan names both reads and withholds the write. A clarify is the right tool only when the fork is exclusive. Neither path picks a single capability at score 1.0. | Two result shapes to synthesize and to log. The plan type is a domain record (fired capabilities, rule ids, no write), not a second router. |
| Skip `ModelPort` on DATA | Keep the echo, because offline it is a no-op | The echo hides the dependency. The day the live adapter is wired, every balance is a prompt. Copying the fixture makes F2's "fabricated number" class structurally unreachable on this path. | Data answers lose any future phrasing the model might have added. The worksheet ranks that loss below an unauditable number. How-to synthesis may still call the port; this pillar does not take that call away. |

## Pillar 2 — Economics

**Decision.** [`ari/adrs/0002-model-port-eval-gated.md`](../../ari/adrs/0002-model-port-eval-gated.md)
stays the only gateway to a model. Routing stays off it on a fast-path hit
(F1, F4). `RequestContext` gains the product surface so later spend can be
attributed (F10). Adapters stay in-process. Serverless is the option not
taken.

**v1 evidence.** ADR 0002 already says the demo default is a configured
model, every swap is a golden-set release, and multi-model-per-turn waits
for a traffic signal. `RequestContext` today is user, tenant, role,
conversation id, turn id. The four surfaces from the brief are not on the
context, so a decision-log line cannot say which product asked. The
composition root constructs `OmniAdapter`, `DocsAdapter`, and
`TicketAdapter` in-process.

**v2 change.** Add `product_surface: str = "unspecified"` to
`RequestContext`. The CLI grows a `--surface` choice limited to the four
names. The decision log writes the field. No price table, no token counter,
no second function.

**Gate.** Gate 12 (the new field is frozen with the rest of the context,
and no port grows a way to be called without a context). Gate 11 (the log
line still has a complete tuple; surface is additional, not a substitute
for entitlement scope).

**Tradeoff.**

| Choice | Alternative | Why this one | What it costs |
|---|---|---|---|
| One quantum, ports in-process | A serverless function per adapter, or a separate model service now | Richards' quantum splits when a characteristic cannot be met inside the boundary. The characteristics that would force a split (a latency SLO, a scaling ceiling, a trust boundary between teams) are `needs-input` or already satisfied by the port. A second deployable would duplicate identity propagation and the decision log before either one has a reason. | A hot adapter cannot be scaled alone. That is the bill we pay until a measured characteristic says the monolith is the bottleneck. |
| Record the surface; do not price the turn | Build a cost dashboard in v2 | Attribution is a field on a record that already exists. A dashboard needs prices, token counts, and a volume Dana has not given. Shipping the dashboard would require inventing those inputs. | The field earns its place now as **provenance** — the decision log attributes each turn to a surface, which is a present read, not a latent one. What stays latent is the *price*: no dollar figure until Dana gives a volume. A recorded surface with no price is cheaper and more honest than a wrong number in the CAB brief. |
| Fast-path stays off `ModelPort` | Send every turn through the model "so the personality is consistent" | The brief's "use one model" is answered at the config layer by ADR 0002 (one model behind the port). The fast path then accepts a *voice seam* — its copy is deterministic synthesis, not model prose — in exchange for auditability and zero fabrication risk on routing and data. That is the trade, stated plainly, not a redefinition of "personality." | The fast path will not sound like the model path. A fixed string is trivially consistent with itself, which is testable, but it is deliberately not the model-path voice. The eval spec already accepts that: degraded and refusal copy are deterministic on purpose. |

## Pillar 3 — Compliance

**Decision.** [`ari/adrs/0003-governance-seam-identity.md`](../../ari/adrs/0003-governance-seam-identity.md)
already requires `RequestContext` on every port. v2 makes the adapters
honor it: they return only rows that token can see, even when the query
names no tenant, and they **withhold** a chunk they cannot prove is shared.
Numbers are copied from the fixture. A ticket route returns a draft;
`TicketPort.create` runs on the confirm turn. `ActionPort` stays
unimplemented.

**v1 evidence.** [`entitlement.py`](../../ari/build/ari_demo/core/entitlement.py)
refuses when the utterance names another known tenant or says "all
tenants". Gate 6 tests that function. It does not test the adapters. A
Meridian treasurer who asks a data question with no tenant name is
`allow`, and Omni then loads `omni_meridian.json` — the right file, but
the control is inside the adapter, not in the phrase list. Docs never
consult `ctx`: [`docs.py`](../../ari/build/ari_demo/adapters/docs.py)
`retrieve` scores keywords and returns the best chunk from the whole
fixture set. [`app.py`](../../ari/build/ari_demo/app.py) on `Route.TICKET`
calls `TicketAdapter.create` before the user has confirmed. `ActionPort`
is a `Protocol` with a conformance test and no implementation, which is
the ADR.

**v2 change.**

1. Docs chunks carry a tenancy marker. A chunk stamped `Acme Corp` is
   returned only when `ctx.tenant` is Acme. A chunk is treated as the shared
   help center only when it is *explicitly* marked shared; a chunk with
   neither a tenant stamp nor a shared marker is **withheld** — the default
   is deny, because the realistic error is forgetting to stamp a tenant doc,
   and a fail-open default would leak it to every tenant. A fixture-lint
   flags any un-annotated chunk. The gate plants two chunks: one stamped (a
   Meridian query that never says "Acme" must not contain it, the canary
   discipline) and one un-annotated (it must not be served cross-tenant),
   and the build fails on either leak.
2. Omni's existing tenant-file split is the contract to keep, and the new
   assertion calls the adapter, not only `precheck`. The phrase list stays
   for the social-engineering rows ("auditor for all tenants"), which are
   a different mechanism from file selection.
3. TICKET synthesis returns the draft copy that already exists for a
   missing receipt ("want me to do that?") and a `PendingDraft` held by the
   pipeline for the life of the conversation. The draft fixes its own
   idempotency key **at creation** — `(conversation, draft id)`, not the
   turn that later commits — so every confirm of that draft carries the same
   key and C9 collapses a repeat onto one ticket id. The next turn is
   classified against the pending draft: a confirm calls `create` with that
   fixed key; a cancel drops the draft and does not call the port; an
   unrelated new request leaves the draft pending and is routed on its own.
   A confirm must match the draft it confirms (the draft id the response
   carried), so a second ticket-shaped turn cannot silently commit the wrong
   draft.
4. `guarded_read` wraps `DocsPort.retrieve`. The confirm path uses the
   timeout-and-cancel half of the wrapper and does not use the retry,
   because a write is not an idempotent read. C9 still collapses a
   duplicate confirm, now that the key is the draft's and stable across
   confirm turns.

**Gate.** Gate 6 for F5 (both the stamped-leak and the un-annotated-chunk
directions). Gate 8 for F6 (the single ticket moves to the confirm turn;
the duplicate-injection assertion moves with it). Gate 9 unchanged:
approval still cannot be bypassed, because there is still no implementation
to bypass it with. Gate 10 for F7.

**Tradeoff.**

| Choice | Alternative | Why this one | What it costs |
|---|---|---|---|
| Adapters filter by token, default-deny | Keep filtering in the phrase list and trust the adapter | The phrase list cannot see a query that never names the other tenant. ADR 0003's rejected alternative is "service super-user, filter afterwards." Filtering in the adapter, with the token, is the same decision applied one layer down: the rows that are not this tenant are never returned. Defaulting to deny stops the same "trust the author to annotate" posture the pillar rejects at the phrase layer from sneaking back in as a fail-open default. Prompt-level enforcement stays rejected. | Every new fixture needs a tenancy story. A shared doc must be explicitly *marked* shared, or it is withheld — so the failure mode is a help-center chunk going missing (caught by a test), never a tenant chunk leaking. The fixture-lint and the un-annotated-chunk gate make the convention enforceable, not just documented next to the loader. |
| Draft, then `create` on confirm | Create on the first ticket-shaped turn, which is what v1 does | A misroute or a frustrated utterance currently writes a Jira row. Eval-spec F5 (unsafe side effect) is the class. Confirm-before-write matches the phase-2 rule already in ADR 0003 — human review routed by stakes — applied to the one write v1 actually performs. The idempotency key is the draft's, fixed at creation as `(conversation, draft id)` — stable across however many times the user confirms, which is what lets C9 return one ticket id. | One extra turn. A user who walks away leaves a draft and no ticket. Eval-spec §10 would count a silent create as deflection; a draft they did not confirm is an honest non-resolution. The CAB demo shows the draft and the confirm as two CLI turns (F9). |
| `ActionPort` stays a contract | Stub an `execute` that always refuses | Gate 9 asserts that **no** `execute` path exists at all — a structural invariant that is stronger and more auditable than a method that merely returns a refusal, which any edit could turn into one that proceeds. An implementation belongs to the phase-2 ADR, with approval, idempotency, and an audit event, not to this sequence. | The panel cannot be shown a payment-run refusal coming out of a real method. They can be shown the conformance test and the absent path. That is the stronger artifact. |
| Numbers copied from the fixture | Let the model phrase the figure "so it reads naturally" | Same stake as pillar 1's model skip. A phrased number is an ungrounded answer if one digit moves. The memo is still quoted as data, which is the Q-072 rule: quoting a hostile memo is correct; executing it is the failure. | The data reply is blunt. Blunt and reconstructable is the auditability characteristic. |

## Assumptions until Tuesday

Each assumption is in force for the CAB conversation. Each names the
observation that retires it.

1. **The product token is the entitlement source.** Omni and docs trust
   `RequestContext.tenant` and `role` stamped by the identity gate. This
   retires if the entitlement source of truth is a service-account-only
   Omni (Ari would then be a confused deputy, and ADR 0003's rejected
   alternative would be the integration we were handed).
2. **The deflectable class to report is tier-1 how-to, with a well-formed
   ticket counted beside resolution.** A draft is not a resolution. This
   retires if a ticket sample is mostly bank-file failures, in which case
   the deflectable class is data-path degradation, not how-to, and the
   success story we tell Dana changes.
3. **The latency promise is: no model call on a stage-0 hit, and answer
   time on the data path follows the backend.** This retires if a backend
   is slower than the conversation can hide — at that point the worksheet's
   `needs-input` SLO becomes a real budget, and the in-process quantum
   decision in pillar 2 is reopened. Until then, no millisecond target is
   stated.
4. **The 72-row sweep plus the held-out and negative assertions are an
   adequate verification surface for the three behavior changes.** The gates
   certify the 72; the new behavior (overlap, draft-before-write, adapter
   default-deny) is proved by the named assertions, which are build-failing,
   not anecdotal. This retires when a labeled field slice or a coverage
   target for compound-overlap utterances exists — at which point "twelve
   gates green" is measured against the field, not only the frozen set.
   Until then, a green build means the asserted cases hold, not that the
   misroute class is closed. This is the load-bearing assumption behind the
   whole argument-from-gates, which is why it is named rather than left
   implicit.

## Build sequence

Ordered so each step leaves the twelve gates green and adds its
assertion(s). No step edits an ADR. No step adds a store, a second process,
or a model call on a fast-path hit. Gates a step does not name — gate 7
among them — are regression guards: no step may turn one red.

1. **`Route.CLARIFY` and `CapabilityPlan` in `types.py`.** `app.py` records
   a clarify as CLARIFY. Gate 11 is the proof: the tuple is complete and
   the route is not OUT_OF_SCOPE. `golden_set.ROUTES` gains CLARIFY so the
   loader stays honest. Existing OUT_OF_SCOPE refusals stay refusals. (This
   step relabels the existing classifier-fallback clarify path, so it has a
   real subject to assert against before step 2's overlap arrives.)
2. **Overlap rule in `stage0.py`, plus the Tier-B `forecast variance`
   phrase.** The rule generalizes the response across Tier-A; detection
   stays phrase-bounded, recorded as such. Re-sweep. Held-out utterances,
   including the March sentence, asserted in their own test, separate from
   the 72, plus a build-failing **negative** assertion that a
   single-capability how-to brushing the new phrase still routes
   single-capability. Gates 1–3 are the proof on the golden set; the
   held-out and negative tests are the new assertions.
3. **Data synthesis skips `ModelPort`.** Assertion: the answer text is the
   fixture value. Provenance records an explicit no-model version string
   so gate 11's "model version present" check still passes for a reason
   a reader can see.
4. **Omni and docs filter by the token, default-deny.** Assertions: a query
   that never says "Acme" cannot read Acme, through the adapter, not only
   through `precheck`; and an un-annotated docs chunk is withheld
   cross-tenant, with a fixture-lint flagging it. Gate 6, extended.
5. **Ticket draft, then create on confirm.** The draft fixes its
   idempotency key at creation `(conversation, draft id)`. Gate 8 drives the
   pipeline directly (two `handle` calls), so it is green at this step
   before the CLI plumbing of step 8: one ticket, on the confirm turn, and a
   duplicate confirm replays onto the same id.
6. **`guarded_read` around docs, and the timeout/cancel half around the
   Jira confirm.** A cancel stops the call before `create`. Gate 10. The
   retry count on the write path is zero.
7. **Registry dispatch for one extra read source (status page, a fixture).**
   A new source is a registry entry, not a new branch in `app.py`. The
   registry is the seam for source N+1; Omni and docs can migrate behind it
   when a third source makes it earn its keep. Gate 12.
8. **CLI carries `turn_id` and a pending draft.** Gate 8 already proves the
   draft/confirm flow at the pipeline in step 5; this step makes it
   demonstrable *at the CLI* as two turns of one long-lived session.
   `--surface` lands here too, because the CLI is the only caller that knows
   which product embedded the turn (F9, F10).

## ADR amendments (staged 2026-10-03)

Staged now as dated amendments in the ADR files
([0001](../../ari/adrs/0001-deterministic-first-router.md),
[0003](../../ari/adrs/0003-governance-seam-identity.md)); the decision is
recorded now and the eight-step build above is its implementation, with each
amendment's Compliance delta confirmed when those assertions are green.

- **ADR 0001.** The single-Tier-A short-circuit gains a clause: it applies
  when that capability is the only one that fired. Overlap yields a plan
  (all reads) or a clarify (a write, or exclusive reads), by a rule computed
  from the fired set. The clause generalizes the response, not detection —
  detection stays bounded by the stage-0 phrase table, which the amendment
  records as a known limit. The reversal story (the threshold dial, the road
  back) is unchanged.
- **ADR 0003.** The ticket write gains the same stakes rule the action
  port already has: a human confirm precedes `create`, with the idempotency
  key fixed to the draft. Adapter-level entitlement gains a default-deny
  rule: a docs chunk with no tenancy marker is withheld, not shared.
  Identity propagation and "ActionPort is a contract" stay as written.

## What this note is for

Walk the SCQA, then one pillar, then the step that proves it. The
requirements tables are the boundary if the conversation drifts into
SLAs, a cache store, or a second service. The eight steps are the order
of work when the code pass starts.
