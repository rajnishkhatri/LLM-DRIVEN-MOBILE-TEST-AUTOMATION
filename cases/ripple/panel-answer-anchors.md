---
type: notes
title: 'Panel answer anchors — the scripted 75 minutes'
description: >-
  Pyramid answer anchors for the full panel script: 17 questions across six
  segments plus the four scripted pressure probes. One card per question —
  the line they write down, the receipts behind it, the trap it tests. Q14
  was verified live against the CLI on 2026-10-02 and fails exactly as the
  script predicts; the card owns it.
tags: [ripple, interview, panel, ari]
---

# Panel answer anchors — the scripted 75 minutes

One card per scripted question. **Memorize each card's Line — it is the
sentence they write down.** The Because bullets reconstruct from the build;
the Trap names what the question is really testing. Numbers and module
sentences live in [code-tour-talk-track.md](code-tour-talk-track.md) and
[eval-layer-talk-track.md](eval-layer-talk-track.md) — this card holds first
moves, not inventory.

Q2/Q3 anchor on the three committed Dana questions (eval-spec §10); refresh
when the brief's seven land.

## Cold open

### 1. "Before we get to your walkthrough: what's the actual problem?"

- **Line:** "A treasury customer with one question faces three systems —
  the numbers live in Omni, the procedure lives in Confluence, the help
  lives in Jira — and today the customer is the integration layer. The
  cost isn't the swivel chair; it's that every manual hop strips
  provenance and crosses a permission boundary nobody is watching. Ari is
  one front door with the governance built into the frame."
- **Because:** fragmentation named in sentence one; the risk (ungoverned
  integration, not inconvenience) in sentence two; "solved" means unify
  access **without unifying risk**. The word *AI* does not appear in the
  first minute — the model is an implementation detail of routing and
  drafting, introduced after the problem stands on its own.
- **Shape for 5 minutes:** problem (90s) → what solved means (90s) → the
  three pillars reframed as checkable promises: reliable routing, evals as
  acceptance, one governance point (2m).
- **Trap:** no notes, verbatim capture. The first two sentences ARE the
  notes — rehearse them word for word.

## Brief and questions for Dana

### 2. "What answer were you expecting to this question?"

- **Line:** "Both of my sharpest questions came with a prior — a question
  without an expected answer is decoration."
- **Because:** ① deflection — expected "80%, counted as tickets-not-
  raised," which conflates deflected with resolved: a user who gave up
  counts as a win. ③ entitlement source of truth — expected "each backend
  keeps its own": three permission models, no single owner — which is
  exactly why the design pins one pre-model gate to the signed token.
- **Trap:** tests whether the questions were probes or theater. State the
  prior crisply, then bridge to what each branch changes (card 3).

### 3. "What would you have done differently in each branch?"

- **Line:** "Each question is a fork with a design on both branches —
  that's what made it worth Dana's time."
- **Because:** ① deflection honest already → adopt their definition and
  wire the outcome dashboard to it; conflated (expected) → ship
  resolved-vs-abandoned side by side before accepting any target. Same
  build, different dashboard emphasis. ③ single entitlement source exists
  → the gate reads it through an adapter and the demo's tables die early;
  fragmented (expected) → the pre-model gate becomes the unification
  point and the brief's roadmap names an owner and a granularity.
- **Trap:** invites you to admit the build depended on answers you didn't
  have. The honest counter: the ports and policy seams already carry both
  branches — that's why they're there.

### 4. "Which of the three backends worried you most, and why?"

- **Line:** "Omni — it's the one that can show another tenant's money and
  put a wrong number in front of a customer. But the real worry was never
  one backend; it's the seams: one write path and three permission
  models."
- **Because:** Omni carries the existential class (the F3 cross-tenant
  canaries live in its fixtures), the quiet injection door (hostile memo
  fields — our named hardening), and customer-facing numbers. Jira is the
  only writer — bounded by idempotency and approval-first. Confluence is
  the loud door — flagged and stripped.
- **Trap:** pick fast, then elevate. Refusing to pick reads evasive;
  picking without elevating misses the governance point.

## The ten test cases

### 5. "Why these 10?"

- **Line:** "Ten is the showcase, not the coverage — one case per failure
  class, doubled where the stakes demanded it, happy paths riding along.
  The eval is the 72 rows and 12 gates behind them."
- **Because:** the cut rule is mechanical: one per class minimum (F1
  splits into misroute and wrong-confidence); doubles went to F1 (the
  thesis, two distinct hazards) and F3 (the existential class, two
  directions of overreach); happy paths never get their own slot —
  TC-01/09/10 carry data/ticket/how-to while guarding F7/F5/F2; every
  case runs offline in front of the room.
- **Trap:** question 6 is this question re-asked. Same spine, different
  lead — consistency is the test.

### 6. "What made the cut, and what didn't?"

- **Line:** "The first thing cut was the ask itself: ten enumerated tests
  were rejected as the coverage and demoted to exemplars of a spec."
- **Because — three levels of rejection:** one failure mode deliberately
  ungated (over-escalation is tracked-not-gated: gating the cost metric
  teaches the router to guess); rows that guard without a showcase slot
  (Q-072's memo door → gate 7, Q-065's privilege claim → gate 6, the
  approval decline → gate 9, the trap kin → gate 1's precision); whole
  categories with reasons on file (SLO: no bar set — Dana input ②;
  deflection: wrong metric until decomposed; live model outcomes: unwired
  by design; breaker: no metric to read; judge-sole-gated security:
  forbidden by principle).
- **Kicker:** "Nothing was rejected from coverage — only from the
  showcase."

## Demo and code (you drive)

### 7. "Show me where the routing decision gets made."

- **Line:** "Two files: `router/stage0.py` makes the decision;
  `sweep-report.md` is why the dials are legal."
- **Move:** open `route_stage0()` — every rule regex runs, fired weights
  sum per capability; Tier A fires decisively at 1.0, Tier B contests by
  weight; answer only if the top score ≥ θ 0.8 AND the lead ≥ margin 0.5,
  else fall through to the classifier. Then the sweep report's CHOSEN
  line — gate 1 pins the code constants to it.
- **Trap:** "show me" tests whether you land on the exact function
  without hunting. Narrate while opening; rule ids are the provenance.

### 8. "How would you test that in isolation, without an LLM in the loop?"

- **Line:** "Stage-0 already has no LLM — regexes and arithmetic — so
  isolation is its native state: pytest over the 72-row golden set,
  offline, whole suite in 0.10 seconds."
- **Because:** gate 1 holds precision ≥ 0.99 at the swept dials; gate 2
  prints per-path accuracy live (0.953 coverage, 1.000 accuracy,
  classifier recovers 3/3); gate 3 proves route-null rows never
  confidently route; and the sweep is itself the isolation harness —
  replays all 64 routable rows against a 35-point dial grid.
- **Kicker:** the question assumes an LLM is in the loop. The design's
  first router deliberately isn't — that's the answer they remember.

### 9. "Omni returns a number. What does the user see besides that number?"

- **Line:** "The receipts: source@version, confidence, the rule that
  routed it, and the scope it was answered under — the full provenance
  tuple, on every answer including degraded ones."
- **Because:** live in TC-01: `cash_position@omni-2026-09-30`, rule id
  `d-cash-position`, scope tenant:Meridian/role:treasurer; gate 11
  asserts completeness on 100% of answers; the same tuple is the
  decision-log line, so any answer reconstructs.
- **Trap:** displayed or just logged? Both — the CLI renders it, the log
  keeps it. This surface is exactly what Dana's objection targets (P1).

### 10. "Why this failure path? Why not a different one?"

- **Line:** "The Omni timeout is the failure that tempts a model to cover
  — F6 is F2 with a tailwind — so it's the one worth staging."
- **Because:** an invented number during an outage is the worst compound
  failure for treasury; the degraded copy is deterministic — string-
  assertable precisely because no model writes it; and one path shows the
  whole discipline: routing lived (same rule id), fetch died, confidence
  0.0, ticket offer, conversation survives.
- **Trap:** alternatives (auth failure, malformed input) fail closed
  trivially and teach nothing. The chosen path is the one with a
  temptation inside it.

### 11. "Where does this fall over at a thousand concurrent sessions?"

- **Line:** "Honestly: it's a single-process CLI, so the ticket ledger
  and the decision log fall over first — both process-local — and there
  is no backpressure anywhere."
- **Because:** the idempotency store must become shared (the key —
  conversation + turn — survives the move); the decision log needs
  durable transport and retention (the schema survives); load shedding
  (C10) and the breaker (C1) are named slots waiting for a metric; live
  Bedrock adds throttling — the five-outcome enum already reserves
  THROTTLED's seat on the tested degrade path.
- **Trap:** they're testing the demo/production boundary, not expecting
  scale. "The constants are demo-sized; the contracts aren't."

### 12. "What's the first alert you'd want, and what would it measure?"

- **Line:** "Entitlement-refusal rate per tenant — a spike means someone
  is probing the walls. It's the near-miss feed for the class that can
  end the platform."
- **Because:** every refuse and narrow already emits an audit event, so
  the alert is a query over an existing stream, not new instrumentation.
  Runners-up: degrade rate (dependency sickness before users report it)
  and fall-through rate (router cost drift — tracked, not gated). Spec §8
  already routes these to 100% review.
- **Trap:** "first" forces a priority. Pick the stakes class, not the
  loudest pager.

## Live extension

### 13. "Support wants a fourth source, a public status page. How much of
what's on screen has to change?"

- **Line:** "A status page costs an adapter and some rows — not
  architecture. What changes: one new port implementation, phrasebook
  entries, golden rows, a re-sweep. What deliberately doesn't: the
  pipeline, synthesis, the twelve gates."
- **Because:** new StatusPort + fixture adapter; new rules enter Tier B
  by default (runbook rule-evolution protocol) with distinctive phrases;
  ~8 golden rows including traps against DATA ("is Omni down?" vs "why is
  my number stale?"); re-run the sweep — the dials are outputs, they may
  move, and the committed report says why. Entitlement for a public
  source is a one-line allow policy — the first capability where narrow
  isn't needed.
- **Kicker:** "The cost of source N+1 is rows and an adapter. That was
  the point of ports."

### 14. "My March forecast variance jumped and I think bank mapping is
wrong. How do I fix it?" — VERIFIED LIVE, IT FAILS

- **The move:** run it, in front of them. Verified 2026-10-02: routes
  **HOWTO, confidence 1.0, rule id `h-how-do`, sources (none) — and an
  empty answer.** Two blank lines and a confident receipt. Then the
  line: "That's a real failure — and the system just told us exactly
  where."
- **Read the record:** `rule ids: h-how-do` confesses the culprit —
  pattern `\bhow do (i|you|we)\b`, a Tier-A decisive rule that violates
  our own distinctive-phrases law. It survived sweep precision 1.000
  because no golden row contests it: the sweep only defends against rows
  that exist. Compounding: the HOWTO branch hardcodes confidence 1.0 and
  the no-match honesty fix reached the DATA path but never the docs path
  — and gate 4 (citation presence 100%) stays green because gates run
  over golden rows, and this row isn't one yet.
- **The fix protocol (runbook §3.5):** this query becomes a golden row —
  the label is the interesting conversation (route null + acceptable set,
  or a new trap family); carve `h-how-do` (demote to Tier B weak, or
  tighten to distinctive phrases); mirror the no-match honesty fix to
  docs; re-sweep; red gate → green.
- **Kicker:** "A misroute in the demo is the improvement loop's first
  customer — and the rule id already confessed."

### 15. If the demo breaks: "Walk me through the change you'd make."

- **Line:** "First move is the record, not the code — the decision log
  says which stage lied."
- **Protocol:** reproduce once → read the line (identity? route + rule
  ids? scope? sources? degraded?) → name the layer → whiteboard the
  smallest change at that layer → name the gate that should have caught
  it → write the red test first. Gates are born red.
- **Trap:** composure. A broken demo is a chance to demo observability —
  card 14 is this protocol, pre-rehearsed.

## Closing

### 16. "You had four hours. What would another 20 have brought?"

- **Line:** "Nothing new on the feature list — twenty more hours buy the
  platform: a calibrated judge, a swept live classifier, and replay as a
  committed tool."
- **Because, in order:** judge calibration on the 20-row slice — unlocks
  gate 5, which today proves only that the judge refuses authority
  uncalibrated; the live classifier behind the existing port, its floor
  swept (retire the unreceipted 0.6); `router/replay.py` committed so the
  promotion protocol has its instrument; the named hardenings (memo
  review-flag, docs no-match honesty, the `h-how-do` carve, degraded-copy
  consolidation); per-capability entitlement policy, fed by Dana's ③.
- **Trap:** platform wins, features lose — and this list is literally the
  deferred-by-decision list. "The next twenty hours were planned before
  the first four ended." Not a fourth backend: sources scale by adapter
  (card 13).

### 17. "What are your questions for us?"

- **Four, prepared — all work questions:** ① "Who labels assistant
  failures today, and does this design change their job?" ② "When an
  assistant answer is wrong in production, who gets paged, and what do
  they read first?" ③ "Where does entitlement truth live today, and who
  owns changing it?" ④ "Has a red eval ever stopped a release here?"
- **Because:** each is answerable only by people who do the work, and
  each telegraphs how you'd operate — review queues, on-call reality,
  governance ownership, gate culture. ④ doubles as a values probe: the
  answer tells you whether the gates would survive their culture.
- **Trap:** scope, reporting and comp questions lose.

## Pressure probes

### P1. Dana: "Showing the query makes it look like a database tool.
Customers asked for simple. Why are you right?"

- **Line:** "I'm not right about the pixels — the surface is hers. I'm
  right about the receipt: provenance must exist and be one tap away,
  because the first wrong unexplained number costs more trust than any
  clean screen buys."
- **Move:** concede the surface genuinely (collapse the tuple behind a
  source chip — entirely her call); hold the invariant (the tuple exists,
  is complete, is reachable); propose the decider — both variants behind
  a flag for the CAB cohort, measure verification behavior, not
  aesthetics.
- **Why hold:** her conversations say "simple." Simple is about clutter,
  not auditability — different question, and both get honored.

### P2. "She's got customer research. You've got a hypothesis."

- **Line:** "Not quite — I've got 72 labeled rows, a sweep report, and
  twelve executable gates. That's an instrument, not a hypothesis. And
  her research is an input to it: the next golden rows come from her
  transcripts."
- **Move:** never contest her data — subsume it. Research says what users
  want; the eval layer says what the system does; the harvest loop
  literally mines her channel for rows.
- **Kicker:** "The answer to research-versus-hypothesis is research AND
  receipts."

### P3. Deliberate silence after your answer.

- **Rule:** a finished answer ends. Three breaths, eye contact, nothing.
  If it truly stretches: "Happy to go deeper on any part of that." Never
  backfill, never soften a number, never reopen a concession. Their
  silence is scripted — so is your stillness.

### P4. Implied throughout: "What part of this was yours?"

- **Rule:** **I** for decisions, **we** for execution — consistent,
  unprompted. Prepared: "I chose θ 0.8 and margin 0.5 — from a sweep I
  designed. I rejected IAM for entitlement and wrote down why. I deferred
  the breaker. We ran the build as three parallel streams against a
  contract-first wave zero."
- Never "we decided" for a call you'd defend alone; never "I built" for
  the whole thing.
