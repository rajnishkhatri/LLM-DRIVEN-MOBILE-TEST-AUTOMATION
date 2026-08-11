---
type: architecture
title: ADR 0014 — Confine the LLM to proposing in ASH-Capture; commit deterministic arrival, isolated capture topology, and append-only graph authority
description: 'Spawned by Replan R1 Lane 2 D1 (2026-07-31) after a 7-agent review confirmed 28 findings against the ASH-Capture walkthrough proposal: the discovery loop could not terminate on legitimately changed screens (Critical #5), one worker held both the gateway credential and the authenticated device session (Critical #4), deep links executed with no admission filter, edges entered the graph trusted at birth with no removal procedure, concurrent writers could fork the version chain, and per-commit human review was silently dropped. This ADR decides all seven D1 items plus the §13 PostgreSQL storage choice as one architecture: a two-process proposer/executor split with credentials never co-resident; a deterministic arrival decision table with supersede-based re-keying; backend-scoped signatures on shared node identity; deny-by-default deep-link and TYPE admission; staged CANDIDATE-at-birth graph writes with fork-unrepresentable CAS serialization and a named auto-commit control change; the full ADR 0009 call-site map with the flip counter ruled 3-of-3; and PostgreSQL snapshot storage. Committed now: topology, schemas, trust semantics. Deferred by named interface: the graph lineage-chain scope (D3, ADR 0012 amendment), the prod-grade-data definition (D4, ADR 0010), and the invocation model (D5, ADR 0007 ruling).'
tags: [architecture, mobile-test-automation, adr, arch-decide]
---

# ADR 0014. Confine the LLM to proposing in ASH-Capture; commit deterministic arrival, isolated capture topology, and append-only graph authority

## Status

**Accepted** — 2026-07-31, at the combined gate with SPEC-OK on
`docs/sdd/specs/mobile-test-automation-ash-capture.spec.md` (owner decision, one
combined gate). The three riders were ratified at the same gate and are now
recorded in their home ADRs: the ADR 0001 seam-vocabulary amendment
(`ObservationPacket`/`CandidateActionSet`), the ADR 0009 ASH-Capture flip
amendment (counter 3 of 3, ASH-repo-scoped screen-gate promotion), and the A11
stored-biometric-credential override.

Drafted 2026-07-31 at SDD Stage 2 synthesis from four adversarially verified
facet designs (all four verdicts UPHELD_WITH_AMENDMENTS; every verifier
amendment applied in this text). The clarify pass ran the same day and resolved
**all five open forks** (owner decisions, recorded as C1–C5 in the spec):

- **C1** — ANCHOR_LESS/WEAK_DES nodes MAY auto-commit a RE-KEY on the strict path
  (rule 5), session rate guard unchanged.
- **C2** — the A11 override is confirmed; the lease-minting fallback (standing
  vault-held test password under executor-enforced lease discipline + rotation) is
  accepted as recorded risk, verified on the week-0 access track.
- **C3** — the ADR 0009 flip is executed ASH-repo-scoped now; the amendment records
  the spine-side promotion question as open, routed to the spine's own change
  process.
- **C4** — APPROVE_GRAPH_BASELINE blocks at the certification boundary only.
- **C5** — quarantine recall = flag-and-stale with a lineage cross-reference
  enumerating affected conversions; no retroactive invalidation; the committed
  Java stays the sole audit pin.

Acceptance of this ADR also ratifies three riders, each a recorded decision in its
own right:

- an **ADR 0001 amendment** adding `ObservationPacket` and `CandidateActionSet` to
  the Invoke Models seam's crossing vocabulary (0001:82-85 currently restricts the
  seam to the IR spine; `CandidateActionSet.locator` reuses the existing
  `LocatorCandidate` type where possible) — without it the proposer either violates
  0001's contract or smuggles a second contract past it;
- an **ADR 0009 amendment** recording the flip counter at **3 of 3** and the
  ASH-repo-scoped screen-gate promotion (see Decision D-H), following 0009's own
  2026-07-27 amendment channel (0009:242-256);
- an explicit **override of user-stated constraint A11** ("re-login via stored
  Touch/Face-ID creds", o1-pipeline-walkthrough.md:785), taken on review finding #9's
  grounds (o1-pipeline-review.md:66) — **human-confirmed at the 2026-07-31 clarify
  pass (C2)**; ratified finally at this gate. The 10-minute session cap itself is
  retained.

Recorded-not-verified assumptions (0013 precedent, 0013:13-17): (1) the test
IdP/vault can mint per-run app-credential leases — fallback: a standing vault-held
test password with executor-enforced lease discipline and rotation cadence
(clarify-resolved 2026-07-31, C2: fallback **accepted as recorded risk**, verified
on the week-0 access track; the decision direction does not depend on the answer,
only the enforcement point moves); (2) the capture environment's data remains production-*realistic*
synthetic pending D4 — if D4 rules it production-derived, ADR 0010:148's PII flip
condition suspends discovery via a named config gate.

Last responsible moment: the process *topology*, graph *schema*, and trust
*semantics* are decided **now** — each is the expensive retrofit. The sandbox
technology (ADR 0013's open item), the D3 chain scope, the D5 invocation model, and
parameterized deep-link templates are each deferred to their own later moment.

Per ADR 0010, the security review runs as a parallel track; the §12.4 queue entry
for ASH-Capture stands and did not block drafting.

## Context

**Forces.** The ASH-Capture walkthrough (o1-pipeline-walkthrough.md §11-§13,
PROPOSED material per :467) puts an LLM inside a loop that drives an authenticated
banking-app session on real devices, and the 7-agent review confirmed 28 findings
against it. The load-bearing ones:

1. **Termination defect (Critical #5).** The success predicate compares the landed
   signature to the *stored* signature (walkthrough:604), so a legitimately changed
   screen "can never match and deterministically exhausts its budget into the escape
   hatch (~20% of screens per release)" (walkthrough:616-621) — collapsing the <10%
   escape-hatch target at every release (walkthrough:719-722).
2. **Credential inversion (Critical #4).** "One worker calls the model (step 2) and
   taps the device (step 4) with app-session authority" (review:54) — rebuilding the
   co-location ADR 0013 exists to remove. §12.2's claim that ASH "inherits" 0013
   (walkthrough:779) was aspiration, not analysis.
3. **Widest LLM action space, narrowest filter (Serious #8/#12).** A probed
   `erica://transfer?...` route executes with no URL admission check and, on a
   landed-signature match, becomes "the permanent VERIFIED cost-1 preferred edge"
   (review:64); edges recorded mid-loop are "replayed forever as 'NO LLM' paths"
   with "no procedure to quarantine or remove a bad edge" (review:72).
4. **Fork and drift (Serious #14/#15/#16).** No lock, CAS, or uniqueness on
   `prev_version_sha` — concurrent capture forks the chain "exactly in release week"
   (review:76); three backends write incomparable hashes into one graph (review:78);
   the signature guarantees neither uniqueness nor stability on "exactly the screens
   a bank has most of" (review:80).
5. **Dropped and untyped controls (Serious #9/#20/#26/#28).** §3 and §11 contradict
   each other on capture-time app credentials (review:66); auto-commit silently
   drops the graph review control (review:90); TYPE values have no schema home
   (review:102); `committed_by` is free text that cannot record the steering human
   (review:108).
6. **The screening IOU.** "The call-site map belongs in ADR 0014; the loop cannot
   ship without it" (walkthrough:612-614), against an ADR 0009 flip counter already
   at 2 of 3 (0009:114).

Replan R1 (REPLAN-OK 2026-07-31) ruled T01-T43 STAY unchanged and routed all of the
above here as D1, with D3/D4/D5 as separate decisions this ADR must interface with,
not make (tasks.md:184-188). Sequencing S1-before-S2 (tasks.md:193) makes this ADR
the gate on the measurement spike.

**Existing-ADR honesty.** No ADR 0001-0013 defines screen signatures, arrival
predicates, DES, backend scoping, edge lifecycle, URL admission, typed-input policy,
or a capture-time app session. ADR 0013's scope is generated-code *execution*
(0013:97-103); ADR 0009 screens *content* by data class (0009:85-92); ADR 0012's
chain and grants scope to *lineage tables and per-conversion chains only*
(0012:90, :101-105, :163-166). Everything below is new ADR 0014 decision content
that *borrows* those ADRs' constructions — it inherits none of their coverage.

**Alternatives considered.**

- **Deterministic-arbiter architecture (chosen)** — the LLM proposes candidate
  actions only; every execution, admission, arrival, commit, and trust decision is a
  deterministic function of committed, versioned inputs, in a process that cannot
  reach a model.
- **Walkthrough as drafted** — single worker, denylist-only filtering,
  VERIFIED-at-birth edges, stored biometric creds, free-text actors, bare-FK chain.
  Its strongest form is "least machinery"; it is also, clause for clause, the
  confirmed finding list above.
- **Human-gated everything** (review each edge, each re-key, each probe) — safest
  per artifact, but at ~20% screen drift per release it recreates the release-week
  human spike ASH exists to eliminate: the escape-hatch flood returns as a
  review-queue flood.
- **No ASH** (keep WP5 manual capture only) — zero new risk, and permanently pays
  the per-screen human cost the program was built to remove; WP5 is retained as
  ASH's fallback and escape hatch either way (tasks.md:163).
- Per-sub-decision rejected options (denylist, normalize-then-hash, fuzzy/learned
  matching, queue channel, SERIALIZABLE, graph service, age-based promotion, ban
  TYPE, working-agreement-only environment control, graph DB) are dispatched inside
  each Decision item below, each with the simpler-thing-considered stated.

**Qualification.** Nygard test: passes — process topology, storage schema, and
trust semantics are structural, expensive to retrofit, and constrain every future
consumer. Third-law test: passes — four defensible architectures existed (matrix
below); the losers are named with what they would have bought. Timing: topology,
schemas, and semantics now; sandbox technology, chain scope (D3), data
classification (D4), invocation model (D5), and template extensions later, each at
its own last responsible moment.

### Trade-off matrix

| Contextual factor (weight) | Deterministic arbiter (chosen) | Walkthrough as drafted | Human-gated everything | No ASH (WP5 only) |
|---|---|---|---|---|
| Injection blast radius on an authenticated banking session (5) | **++** proposer holds no device authority; deny-by-default admission; no gateway credential near the device | −− widest action space, narrowest filter, both credentials in one worker | + humans catch what filters miss, slowly | ++ no LLM near a device |
| Discovery termination across releases (5) | **++** re-key in one visit; bounded churn ladder | −− ~20% of screens exhaust budget every release | − terminates via queue, at human speed | −− every screen is a human touch |
| Auditability / provenance survival (4) | **++** typed actors, append-only supersede, origin survives quarantine | −− laundered LLM provenance, free-text actors, forkable chain | + reviewed but unscalable records | + manual but sparse |
| Release-week human load (4) | **++** one baseline review + true escape-hatch residue | − escape-hatch flood (~20% of screens) | −− flood relocated to a review queue | −− full manual re-capture |
| Machinery added (3) | − two processes, staging table, three committed configs | ++ least machinery | − queue + reviewer tooling | ++ none |
| Device-minute cost (3) | + replay-first, promotion piggybacks on normal traversal | + similar until the drift storm, then escape-hatch device waste | −− re-verification serialized behind humans | − every capture is manual device time |

## Decision

**We will confine the LLM in ASH-Capture to proposing candidate actions and route
every other judgment through deterministic, committed, versioned machinery: we will
split capture into a credential-isolated Capture Executor and a stateless Action
Proposer as two OS processes that can never resolve each other's credentials; we
will separate the arrival predicate from the identity computation and drive arrival
from a fixed-order deterministic decision table that terminates discovery with
supersede-based RE-KEY verdicts; we will scope signatures and edge verification per
backend on a shared, backend-neutral node identity; we will admit deep links only
from a deny-by-default exact-route allowlist and typed input only from a committed
synthetic corpus into allowlisted navigation fields, gated on a machine-checked
resettable-test-environment attestation; we will land discovery observations in a
run-scoped staging table, commit them only on successful termination as CANDIDATE
edges, promote to VERIFIED only on distinct-run deterministic confirmation, make
version-chain forks unrepresentable by schema, and remove poisoned edges only by
superseding quarantine snapshots; we will name and accept the auto-commit control
change under a bounded delta class with typed actors and a per-release
APPROVE_GRAPH_BASELINE human review; we will enumerate all seven LLM-adjacent call
sites, rule the ADR 0009 flip counter at 3 of 3, and execute the forced flip as an
ASH-repo-scoped screen-gate promotion; and we will store the ScreenGraph in
PostgreSQL as append-only full snapshots anchored to object storage via the ADR
0011 port.**

The why front and center: **the model proposes; determinism disposes.** Every
confirmed critical finding traces to one root — LLM output or LLM-influenced state
acquiring authority (execution authority, trust status, graph permanence,
credential reach) without passing a deterministic, auditable gate. This ADR
inserts that gate at every crossing and removes the prize (credentials, trusted
status, mutable history) from every place the model can reach.

### D-A. Arrival and re-keying: two predicates, one decision table, supersede-based re-keys

*Identity* stays `(skeletonHash, titleAnchor)` per §11.1 (walkthrough:488-496),
computed fresh on every dump; the stored signature is a versioned observation,
never the arrival test.

*New construct — distinguishing-element set (DES).* At graph-commit time, per node
and per backend: the set of accessibilityIds appearing in that node's skeleton and
no other node's skeleton within the same graph version and backend (cap 7, minimum
3; below 3 flags `WEAK_DES`, treated per the ANCHOR_LESS strict rule).

*Arrival decision table.* Signals, all against the executing backend's stored rows:
`A` titleAnchor exact match; `D` fraction of the node's DES present in the landed
dump; `K` skeletonHash equality; `P` graph-position evidence (reached by replaying
a stored path whose every prior arrival returned MATCH, or by a discovery step from
a MATCHed parent); `S` settle stability (two dumps ≥1s apart, identical
skeletonHash). Thresholds τ_d = 0.6, τ_strict = 0.8, R = 3, committed as versioned
config constants (S2 spike calibrates against pre-registered pass/kill thresholds,
tasks.md:193). Quantization note: for |DES| ≤ 4, τ_strict = 0.8 requires full DES
presence — the S2 spike must log D as raw fractions, not pass/fail, or threshold
calibration is meaningless. First matching rule wins.

Nodes with a CONFIRMED anchor:

| # | Rule | Verdict |
|---|---|---|
| 1 | `K ∧ A` (ANCHOR_LESS variant: `K ∧ P`) | **MATCH** — edge re-VERIFIES for this backend |
| 2 | `¬S` | **NO-VERDICT** — transient/loading; one no-progress strike; never re-keys |
| 3 | `A ∧ D ≥ τ_d ∧ ¬K` | **RE-KEY** — supersede skeletonHash |
| 4 | `¬A ∧ K` | **RE-KEY-ANCHOR** — supersede titleAnchor only (a `D ≥ τ_d` conjunct is retained as defensive-only: K ⇒ D = 1 except on hash collision) |
| 5 | node ANCHOR_LESS: `D ≥ τ_strict ∧ P ∧ ¬K` | **RE-KEY** (strict path; clarify-resolved 2026-07-31, C1: **auto-RE-KEY permitted**, session rate guard unchanged; S2's measured bucket size confirms or flips) |
| 5b | `¬A ∧ ¬K ∧ D ≥ τ_strict ∧ P ∧ S` | **RE-KEY-FULL** — both anchor and skeleton legitimately changed while the distinguishing elements survive; supersedes both; counts against the session guard; ANCHOR_LESS/WEAK_DES nodes excluded (they stay under rule 5) |
| 6 | otherwise (incl. `A ∧ D < τ_d` title collision; `¬A ∧ ¬K ∧ D < τ_strict` no continuity) | **NOT-ARRIVED** — discovery continues or escape-hatches per §11.4 |

Rule 5b exists because a release that relabels "Overview" to "Accounts Overview"
*and* restructures the layout is a common redesign shape; without it the verifier
constructed exactly the Critical-#5 exhaustion for the both-changed subset. The
ANCHOR_LESS variant of rule 1 is `K ∧ P`, not `K ∧ D ≥ τ_strict`, because K ⇒ D = 1
makes the D-conjunct vacuous — bare-K arrival is exactly what the non-guarantees
below forbid.

`DYNAMIC_SKELETON` nodes (K excluded as an input, making the table total over node
states): `A ∧ D ≥ τ_d` → MATCH; `A ∧ D < τ_d` → NOT-ARRIVED, counting toward the
2-strike SIGNATURE_DEFEATING demotion; ANCHOR_LESS ∧ DYNAMIC_SKELETON → escape
hatch.

The §11.4 success predicate becomes: DONE on MATCH or any RE-KEY variant; the
escape hatch is reached only via NOT-ARRIVED exhaustion.

*Re-key semantics.* A RE-KEY commits only at successful loop completion, only as a
new graph-version snapshot (§13.3 model, walkthrough:906-910), adopting ADR 0012's
supersede semantics — "every correction a compensating append rather than an
update" (0012:87-91, :112-114). Each re-key carries an evidence record:
superseded/new signature, rule fired, signal values {A, D, K, P, S}, thresholds
config version, backend, capture_session_id, typed actor, appVersion, timestamp.
Chain *membership* of these records awaits the D3 amendment — adopted semantics,
not claimed chain scope.

*False-re-key bounds.* (1) Rules 3/4/5/5b each require a surviving continuity
signal; (2) the DES per-version uniqueness guarantee; (3) settle stability; (4) a
**session rate guard**: at most 1 committed re-key per target request, and a
session aborts committing nothing (routing to human review) only when its RE-KEY
count is **≥ 3 AND > 30% of visited nodes** — the per-target allowance takes
precedence below that floor, so a single-target session committing its one
permitted re-key never trips the guard. Recovery from a slipped false re-key is a
superseding snapshot: findable and reversible, never destructible.

*Purity.* The arrival verdict is a pure deterministic function of (both settle
dumps, stored node/signature rows for the executing backend, recorded path
evidence, committed thresholds-config version). No model call anywhere in the
predicate, the DES computation, or the demotion ladder.

Simpler things rejected: anchor-only arrival (generic-title collisions re-key the
wrong node; ANCHOR_LESS has no predicate); fuzzy skeleton similarity (a
tunable-forever knob, dominated by the precomputed set-membership DES); learned
fingerprints (the walkthrough's own *heavier* fallback, :726-729, and a model
inside the arrival predicate); human-confirmed re-keys (at ~20%/release, the
review-queue flood); in-place UPDATE (violates supersede semantics outright).

### D-B. Cross-backend comparability: backend-scoped observations on shared identity

`screen_id` is cross-backend; signatures and edge verification are per-backend.
Signature fields move off `screen_graph_nodes` into `screen_node_signatures
(graph_version_sha, screen_id, backend, skeleton_hash, title_anchor,
anchor_status, des_json, last_verified_at)`; edge `status` moves to
`screen_edge_status (graph_version_sha, edge_id, backend, status,
last_verified_at)`. Edge rows keep locator/action — locators are the portable
layer.

Operational rules: (a) arrival always selects the executing backend's signature
row; (b) backend-crossing replay treats every edge lacking VERIFIED-for-this-
backend as UNVERIFIED under §11.4's existing semantics (walkthrough:587-590) —
verify-or-BROKEN *for that backend only*; (c) BROKEN on backend B never alters
another backend's status: phantom cross-backend drift is structurally
unrepresentable. A node with no signature row for the executing backend is decided
on titleAnchor + the **designated reference backend's DES (Perfecto** — the
release-facing backend; accessibilityId is the most portable field), and success
writes a `FIRST_SEEN_ON_BACKEND` signature row — never a RE-KEY, so backend
novelty cannot masquerade as screen change. This is a **deliberate, bounded
cross-backend accessibilityId comparison** — the no-cross-backend-comparison
guarantee is scoped to skeletonHash and titleAnchor. If no backend has a row:
escape hatch.

**Write semantics vs the snapshot model (decided, not left silent):**
`screen_node_signatures` and `screen_edge_status` are **append-only observation
logs outside the content hash** — `graph_version_sha` on them is a context foreign
key, not hashed content. Re-VERIFY confirmations, `last_verified_at` refreshes,
and FIRST_SEEN_ON_BACKEND rows append without minting a graph version. This
resolves the review-#24 churn question for this table family: the version sha
remains hash-of-graph-contents (walkthrough:864), and observations accrue without
falsifying it or minting a snapshot per capture.

Simpler things rejected: Perfecto-only capture (hard-couples all capture to the
pinned cloud pool during the month-start burst and fails silently on the first
local capture; retained as a permissible *operating policy* atop the scoped
schema — open question settled by S2 device-hour data, not by this schema);
normalize-then-hash (a hand-curated mapping that drifts with every OS/Appium
version and reproduces the incomparability invisibly; can be layered later inside
scoped rows); fully separate per-backend graphs (triples identity bookkeeping and
forfeits the sharing that works).

### D-C. Signature honesty bounds: normative non-guarantees plus a deterministic ladder

Normative text: the signature guarantees neither (1) **uniqueness** — distinct
screens may share `(backend, skeletonHash, titleAnchor)`; nor (2) **stability** —
dynamic skeletons, A/B variants, and personalization legitimately change
skeletonHash within one appVersion; nor (3) **semantic identity**. Consequences:
skeletonHash inequality is never, alone, non-arrival (rule 3); skeletonHash
equality is never, alone, arrival on collided or anchor-less nodes (rule 1's
ANCHOR_LESS variant requires P).

*Collision enforcement:* at graph commit, no two nodes in a version may share
`(backend, skeletonHash, titleAnchor)`; violators are flagged
`SIGNATURE_COLLIDED`, excluded from auto-RE-KEY, and requests targeting them route
to the §11.8 escape hatch unchanged. Enforcement replaces §11.1's
collision-freedom-by-construction overclaim (walkthrough:498).

*Demotion ladder:* ≥ R = 3 RE-KEY events within one appVersion demotes a node to
`DYNAMIC_SKELETON` (skeletonHash recorded for audit, excluded from arrival —
absorbing A/B ping-pong without multi-variant storage); a DYNAMIC_SKELETON node
with D < τ_d on 2 consecutive attempts flags `SIGNATURE_DEFEATING` and routes
deterministically to the escape hatch; human confirmation commits with
`MANUAL_ARRIVAL` provenance and refreshes the DES. Both demotions are
snapshot-committed flag changes with the re-key evidence-record shape.

*Deep-link probe confirmation* upgrades from signature-equality to the full
arrival table; ANCHOR_LESS and DYNAMIC_SKELETON targets take the strict path;
SIGNATURE_DEFEATING targets can never auto-confirm an edge — human confirmation
required.

Simpler things rejected: immediate escape-hatch on instability (the status quo
that collapses the <10% target); multi-variant signature storage (the ladder
reaches the same end state with one counter and two flags).

### D-D. Storage: PostgreSQL append-only snapshots (the §13 decision, adopted with corrections)

The ScreenGraph lives in the existing PostgreSQL primary store — no graph DB, no
second system of record (ADR 0006) — as the §13.3 three-table schema amended by
D-B/D-E/D-F: full snapshot per `graph_version_sha` (hash of graph contents),
supersede-not-update, diffable per release; each version's full JSON anchored to
object storage via the ADR 0011 port as immutable evidence. The honest caveats
carried from §13: `lineage_digest` "joins" a chain ADR 0012 does not construct —
the graph chain scope is **D3's ADR 0012 amendment**, and no graph migration ships
until it is Accepted (`lineage_digest NOT NULL` is unsatisfiable without a defined
chain; graph tables stay out of spine Flyway V1 per Replan R1, tasks.md:164, with
the V1-has-no-graph-DDL guard landing as CI configuration, not a spine edit).
§13.6's "route graph mutations through the existing outbox" is **rejected** — it
inverts ADR 0007, whose provenance writes are synchronous same-local-transaction
and whose outbox serves exactly two seams (0007:55-63, :95); see D-E.

ADR 0006 lifecycle placement: `capture_run_edges` (D-E) is disposable
conversion-state-lifecycle data, purgeable per its D4 retention class;
`screen_graph_versions/nodes/edges` and the observation logs are audit-lifecycle
data with the evidence class's retention posture. `first_observed_run_id` and
`capture_run_id` are recorded values, never foreign keys into conversion-state
tables (F4-class rule, 0006:146-148). Canonical provenance enum, resolving the
:543-vs-:897 drift: `DISCOVERY | GRAPH_SEARCH | DEEP_LINK_PROBE | DRIFT_REPAIR |
MANUAL_CAPTURE` — `DRIFT_REPAIR` is included because repair traversals are a
distinct origin worth auditing; the walkthrough gets the Lane-1 editorial fix.

New grant decision (mirroring, not inheriting, ADR 0012's construction — 0012's
grant and CI assertion cover lineage tables only, 0012:90, :163-166): the
application role holds **INSERT/SELECT-only** grants on all `screen_graph_*`,
signature, status, and staging tables, with its own CI-blocking grant-assertion
test (Testcontainers construction per tasks.md:50). Hard DELETE of a poisoned edge
is thereby prohibited by *this ADR's* grant decision.

### D-E. Graph write path: staged, CANDIDATE at birth, promoted by distinct-run replay, quarantined by supersession, fork-unrepresentable

1. **Staging absorbs step 6.** A `capture_run_edges` table keyed by
   `capture_run_id` receives every observation; nothing in it is loadable by
   `load_graph_for_version`. A run ending ABORT / CRASH / TIMEOUT / NO_PROGRESS /
   BUDGET_EXHAUSTED / ESCAPE-before-completion commits **zero** graph rows (the
   ABORT/CRASH outcome values are new enum members this ADR adds beyond
   walkthrough:605-606); staging rows keep the terminal outcome and a retention
   class (value deferred to D4). Only step-7 success or a completed escape-hatch
   session mints a version. The simpler in-memory-accumulate-and-write-once
   alternative is rejected because CRASH forensics require the observation stream
   to survive the process, parked commits need durable staged edges, and
   escape-hatch sessions span human time beyond one process lifetime.
2. **Deterministic edge identity:** `edge_id = SHA-256(canonical(from_screen_id,
   action_kind, locator_json, to_screen_id))` — closes the review's unspecified-
   generation gap and makes concurrent merges idempotent. Contradictory siblings
   (same from/action/locator, different to_screen) get two deterministic rules:
   path-search selection among sibling CANDIDATEs is by most-recent
   `first_observed_at`; a traversal of sibling A whose landed signature matches
   sibling B's to-node marks A `BROKEN` and records a confirmation observation for
   B (counting toward B's promotion only from a run distinct from B's
   `first_observed_run_id`).
3. **State machine:** first committed status is always `CANDIDATE` — uniformly for
   `DISCOVERY`, `DEEP_LINK_PROBE`, and `MANUAL_CAPTURE`. `CANDIDATE →(promotion)→
   VERIFIED`; `CANDIDATE|VERIFIED →(landed-signature mismatch)→ BROKEN`;
   `VERIFIED →(release flip)→ UNVERIFIED →(re-verify)→ VERIFIED` (inherited
   CANDIDATEs stay CANDIDATE across releases); `any →(trust revocation)→
   QUARANTINED`. Status is a separate per-backend column from provenance; status
   transitions never overwrite provenance. The CANDIDATE-at-birth floor is
   application-validator-enforced (unlike fork prevention, which is
   schema-enforced) — acknowledged, and compensated by a **detective control**:
   the per-release chain-verification job recomputes first-appearance statuses and
   quarantines any edge whose first committed status was not CANDIDATE.
4. **Promotion:** a CANDIDATE edge becomes VERIFIED when a deterministic replay
   from a **different** `capture_run_id` (and device session) traverses it and the
   landed signature matches — recorded in lineage (confirming run, principal,
   landed-signature digest). Threshold N = 1 distinct-run confirmation is a named,
   versioned config value **under CF6's no-silent-disable rule**: raisable without
   schema change, changeable only by recorded decision. Path search uses a
   CANDIDATE edge only when no VERIFIED path exists, and every CANDIDATE hop is
   landed-signature-checked — a CANDIDATE traversal is the confirmation
   opportunity, not blind trust. **Scope honesty on findings 8/12:** this closes
   the *persistence-and-preference* half (no trust at birth, promotion gated,
   quarantine exists); the *execution-safety* half is closed by D-I's admission
   controls, because a reproducible poisoned edge would otherwise auto-promote on
   its first legitimate CANDIDATE traversal — reproducibility is not safety. The
   priced residual: a parameterless route a human misclassified as NAV could
   still probe, commit, and promote; hardening: promotion eligibility for
   `DEEP_LINK` edges (and any action kind under D-I's policy) additionally
   requires a recorded pass of the current allowlist version.
5. **Quarantine:** one transaction mints a superseding version with the edge
   `QUARANTINED` and excluded from the path-search index, writes a quarantine
   lineage row (reason enum: `SCREENING_FLAG | HUMAN_REPORT | CHAIN_MISMATCH |
   VALIDATOR_RETRO`; actor), and stale-flags every NavigationManifest whose
   `graphPath` contains the edge. Removal is exclusion in a superseding snapshot —
   never UPDATE/DELETE. Quarantine records reuse the M21/CF4 review-queue shape
   (tasks T16/T36); release from quarantine is a recorded, attributable
   individual override. **Recall scope (clarify-resolved 2026-07-31, C5):** the
   quarantine transaction also writes a lineage cross-reference enumerating every
   conversion whose manifest is stale-flagged; affected conversions and
   ReplayReports are flagged for audit, never retroactively invalidated — the
   committed engineer-reviewed Java remains the sole audit pin — and a
   stale-flagged manifest forces re-capture on next touch.
6. **Writer serialization — correctness in the schema:** `UNIQUE
   (prev_version_sha) WHERE prev_version_sha IS NOT NULL` and `UNIQUE
   (app_version) WHERE prev_version_sha IS NULL` make forks and duplicate roots
   unrepresentable even for a writer that skips every protocol. The writer
   protocol is a short CAS transaction: `pg_advisory_xact_lock(hashtext(
   app_version))` with ~30s `lock_timeout` (fairness only) → re-read head → rebase
   staged edges by `edge_id` set-merge if the head moved → INSERT version + rows +
   chain row in one local transaction → retry ≤ 3 on unique violation. Device work
   is strictly outside the commit transaction. **Release-boundary structure:**
   each `app_version`'s chain begins with a **root commit** (`prev_version_sha IS
   NULL`) derived by copying the prior release head's node/edge sets with the
   `VERIFIED→UNVERIFIED` flip applied (CANDIDATE stays CANDIDATE); the root's
   lineage row records an informational `derived_from_version_sha` — without this,
   root uniqueness, per-app_version linearity, and the chain scope offered to D3
   would be mutually incoherent.
7. **Contention behavior:** after timeout or 3 CAS failures, staged edges are
   **parked** (`COMMIT_CONTENDED`) with an alert and re-driven by a sweeper;
   re-verification results are never silently dropped, and the capture's primary
   deliverable (the hierarchy dump) is delivered regardless. The park-and-sweep
   mechanism is queue-shaped and is therefore **routed to ADR 0007's manual
   compliance review** alongside D5, with the argument on record: it is a bounded
   retry buffer over rows the same process family owns — not a third
   component-to-component seam — and the eventual commit still writes snapshot +
   chain row in one local transaction. If D5's ruling disagrees, the fallback is
   fail-loud-and-recapture instead of park.
8. Because commits per `app_version` are totally ordered by construction, the D3
   chain inherits a linear, contention-free order — this ADR *offers*
   per-app_version chain scope to the amendment; it does not decide it.

Simpler things rejected: VERIFIED at record time (the finding itself);
provisional-in-graph tags (pollutes the sha or requires UPDATE); age-based
promotion (time is not evidence); per-edge human review (thousands of edges);
advisory lock alone (binds only cooperators); SERIALIZABLE (opt-in and less
diagnosable); a single-writer graph service or leader election (a new always-on
component plus a queue for a problem two partial indexes solve).

### D-F. Auto-commit vs review: a named control change with a bounded delta class

ASH-Capture removes per-commit human review from graph snapshots — recorded here
as a deliberate control change (review finding 20), accepted because: (a) nothing
auto-committed carries trust at birth (the CANDIDATE floor); (b) the spine's
actual audit pin — the engineer-reviewed committed Java — is untouched, and no
decided spine stage consumes the graph or manifest; (c) the baseline review below.

- **Service auto-commit** (actor_kind SERVICE, principal `svc-ash-capture`, the
  M37/T08 per-component pattern): permitted only for a schema-validated delta
  class — new CANDIDATE nodes/edges with full origin provenance; evidenced
  CANDIDATE→VERIFIED promotions; →BROKEN markings; the per-release UNVERIFIED
  flip; manifest stale-flags. A commit validator rejects any service delta outside
  the class and routes it to the review queue.
- **Individual principal required** (actor_kind INDIVIDUAL; `system` and service
  principals schema-rejected, the M37/T03 CHECK construction): quarantine
  release/override; escape-hatch commits (`steering_principal NOT NULL` whenever
  the delta contains MANUAL_CAPTURE edges — the human who steered is recorded even
  though the service writes); the per-release review.
- **`APPROVE_GRAPH_BASELINE`:** one lineage row per app_version — individual
  principal, reviewed `graph_version_sha`, prior baseline sha, diff digest — over
  a review view surfacing every quarantine, override, ANCHOR_LESS addition,
  provenance mix, and promotion statistics. The CF9 shape: the machine produces
  and advises, a named human confers trust, attributably (spec.md:386). Whether
  the baseline blocks certification-bound consumption or is advisory is an open
  fork.
- **Schema:** `committed_by TEXT` becomes `committed_by_principal TEXT NOT NULL
  CHECK (<> 'system')`, `actor_kind CHECK (IN ('SERVICE','INDIVIDUAL'))`,
  conditional `steering_principal`.

Simpler things rejected: full auto-commit (the confirmed finding); per-snapshot
human review (volume guarantees rubber-stamping); free-text `committed_by`
(cannot record the steering human).

### D-G. Process topology and the capture-time credential model

**Two OS processes.** The **Capture Executor** (`svc-ash-executor`) owns the §11.4
decision tree, all budgets, the deterministic validator, the device session (a
short-lived single-run token, ADR 0013's mechanism verbatim in shape,
0013:97-103), the capture-scoped app-credential lease, and every write — it is the
only principal that ever appears as a writer. The **Action Proposer**
(`svc-ash-proposer`) is a stateless request/response wrapper around the Invoke
Models seam holding the gateway credential; it has no DeviceSession type, no vault
client, no database grant, no writable persistent volume, and parses model free
text into the committed `CandidateActionSet` schema inside its own process — model
free text never crosses the boundary (transposing 0013's "generated code never
loads into the orchestrator's process", 0013:122-124). Symmetric startup
credential-absence assertions (0013:186-190 pattern) and symmetric ArchUnit rules
(T02 method: proven by a deliberately-violating sample) on both sides. The
proposer, its Invoke Models implementation, and the gateway-credential
configuration land in the **ASH-Capture repository only**; nothing model-adjacent
lands in the spine repository, whose "no LLM call" do-regardless (tasks.md:132)
and F1 rule remain untouched.

**What crosses:** executor→proposer, a screened `ObservationPacket` {screened
screenshot, screened pruned tree, current signature, target descriptor, remaining
budget}; proposer→executor, a `CandidateActionSet` of **≤ K = 3** entries {kind,
locator (reusing `LocatorCandidate`), value-reference — never a literal, route} —
K = 3 is a recorded ADR 0014 budget value (consistent with the 3-strike
no-progress budget), pinned because an unpinned K is exactly the unrecorded budget
CF6/N10 discipline forbids. Schema-validated twice (proposer parse-or-drop;
executor re-validation before the deterministic validator's filters). **Channel:**
synchronous localhost request/response — not a queue (0007:95). ADR 0007:55-57
defaults non-queue calls to "synchronous and in-process"; this channel keeps the
synchronous half and deliberately breaks the in-process half — the exception is
inherited from ADR 0013's separate-process shape commitment (0013:121-125) and
recorded here explicitly rather than half-cited. Per the Status rider, these two
schemas join the Invoke Models seam vocabulary by recorded ADR 0001 amendment.

**Credential model.** §3's no-app-creds claim stands for the spine's manual tool;
§11 retracts it for ASH — capture gets its own credential decision (review C18's
first branch): a per-run, capture-scoped app-credential lease, resolved by the
executor only from an injected vault reference (M34 pattern) at run start, held in
memory, carrying the run ID, expiring at run end or the 30-minute ceiling.
Re-login is bounded at **≤ 2 per capture request** (3 sessions × the retained
10-minute cap; sized to the loop's own arithmetic); a third attempt aborts to the
escape hatch with an attributable quarantine-style record — the phrase "the real
bound on authenticated LLM-driving time" is Recommendation 8's (review:167).
Stored Touch/Face-ID device-persisted credentials are **rejected** — a
keychain-persisted credential on a shared cloud-pool device outlives the run and
survives to the next tenant (this is the A11 override in Status). Biometric gates
use the backend's injection API with per-run enrollment torn down at run end;
backends without injection route that flow to the escape hatch. Post-run hygiene
is three enumerated checks: app-state reset verified; biometric enrollment torn
down; committed artifacts, traces, and prompt payloads scanned by the screening
library's secret detector with zero detections — a detection is an incident
(0009:210-214).

Simpler things rejected: one process with module boundaries (module boundaries
are not startup-assertable; the exact defect 0013 corrected); a third validator
process (machinery without a threat — the validator holds no credential); a queue
channel (0007:95, and at-least-once semantics wreck run-scoped budgets and lease
TTLs); a direct provider adapter bypassing Invoke Models (0001's named erosion
failure); keeping §11.4's stored creds + unbounded re-login ("standing access
wearing a 10-minute costume"); human-entered credentials per run (reintroduces
the per-run human touch ASH removes).

### D-H. The ADR 0009 call-site map and the forced flip

Seven enumerated LLM-adjacent seams, each carrying 0009's mandatory two-half
construction (static ArchUnit half + runtime assertion — "Both halves are
required", 0009:180-186):

| CS | Seam | Class | Binding |
|---|---|---|---|
| CS1 | Hierarchy dump landing every loop iteration (steps 1/5) | (2) device evidence | screen before any write (T28/M35 construction) |
| CS2 | `ObservationPacket` egress toward the proposer/model | (3) model egress | screen before channel send; the proposer's channel adapter is the only ingress to the seam |
| CS3 | Deep-link sub-loop intake: app docs + screen titles | (1) untrusted source text | screen at intake before any prompt |
| CS4 | Deep-link prompt egress | (3) — second path | invokes the existing CS2 call site (0009:90-92) |
| CS5 | Escape-hatch human action stream + per-screen dumps | (2) device evidence | screen before manifest/edge commit |
| CS6 | `CandidateActionSet` entering the executor | **none of the three — new ADR 0014 control class** | owned by the deterministic validator, its own two-half construction: ArchUnit — `DeviceSession.act()`/`launchDeepLink()` reachable only from validator-verdict-bearing types; runtime — an action without a verdict token is rejected and the run quarantines; persisted candidate documents fall under stored-artifact zero-detection (0009:210-214) |
| CS7 | Feedback/repair context re-entering a prompt | (3) — **anticipatory** | binds any future feedback field added to `ObservationPacket`; today no such flow is defined (step-2's input set is fixed, walkthrough:594-595) |

**Flip ruling.** The counter reached 2 of 3 by counting additional paths into
existing classes (0009:93-96); consistency forbids ruling ASH's paths free. The
third additional path is grounded on **CS2** — discovery evidence egress toward a
provider, a path the manual hierarchy tool never had — with CS3 and CS5 as further
independent new paths; CS1 may be ruled either a new class-2 path or the automated
continuation of the already-counted hierarchy-capture output (walkthrough:776)
**without changing the outcome — the counter crosses 3 of 3 on any arithmetic**,
and "a third additional path … forces the flip rather than inviting it"
(0009:122-123). The flip is executed **where the new paths live**: in the ASH
repo, screening is promoted from a library call to a structurally visible
screen-gate component — the executor's only evidence-landing adapter and the
proposer's only channel adapter both route through it, ArchUnit-enforced. The
spine's three call sites are untouched (tasks.md:166); whether the spine's
screening must also be promoted was clarify-resolved 2026-07-31 (C3): **ASH-scoped
promotion now**, with the spine-side question recorded open in the ADR 0009
amendment and routed to the spine's own change process. The discovery loop must not execute against
any device while that amendment is unmerged (the walkthrough's own gate, :614).

Simpler things rejected: ruling ASH's paths second-paths (internally inconsistent
with how the counter reached 2, and leaves the program's largest LLM surface on
the invocation-dependent posture 0009 concedes is its weakness, 0009:149-153);
program-wide promotion now (reopens the signed-off spine without a human gate);
screening-library coverage of CS6 (screening bounds content, not action
authority).

### D-I. Deep-link admission, TYPE policy, and the environment precondition

**Exact-route allowlist, deny by default.** Per release, the deterministic static
parse of intent filters/entitlements (walkthrough:636-638) is human-classified
once into committed, versioned entries classed `NAV` or `MUTATING`; the allowlist
version is a pinning field on every probe's lineage row (0009:81-82 pattern).
**v1 entries are exact literal URLs — no wildcard, parameter, or pattern syntax
exists in the matching engine**; template syntax arrives, if ever, only via the
recorded open-fork decision on typed parameter templates. Admission (in the
deterministic validator, applying to BOTH the discovery loop's DEEP_LINK actions
and §11.6 probe candidates) requires exact match + class NAV + no query string or
extra path segments — parameters are where action semantics ride, so
parameterless is the deterministic proxy for action-bearing.
`DeviceSession.launchDeepLink()` independently re-validates against the same
allowlist (two-half construction; covers manifest-replay paths that never touch
the discovery validator). MUTATING matches are rejected with a `REJECTED_URL`
lineage row; UNKNOWN routes quarantine-for-review (never silent, never probed) in
the M21/CF4 record shape — admission thereafter only by a recorded, attributable
allowlist commit. Committed `DEEP_LINK` edges carry `url_class` +
`allowlist_version`; at load, the graph loader **excludes** any DEEP_LINK edge
violating the *current* allowlist from the in-memory graph (recorded as a
load-time quarantine event in lineage) — any persisted status change is a
superseding append, never an in-place UPDATE; where no alternative verified path
exists, capture falls through to discovery or the escape hatch per §11.4 — never
the quarantined edge. Cost-1 preference extends only to `url_class=NAV` edges.

**TYPE policy.** The LLM proposes (field, corpusKey) — never the string. Values
resolve only from a committed, versioned synthetic `capture-input-corpus`
(`corpusVersion` pinned on lineage); admissible only into fields matching a
committed **navigation-field allowlist** (role + accessibility-id pattern;
amount/IBAN/payee/OTP/PIN-patterned fields never allowlisted; deny by default).
`vault:` references resolve exclusively inside `DeviceSession.login()`; the
executor refuses and quarantines any other vault-resolving TYPE. Edges and
manifest steps store `corpus:`/`vault:` references only — a literal fails schema
validation (the FP10/T23 shape). Rejected TYPEs that exhaust the 3-strike rule
route to the escape hatch rather than relaxing the field rule. **Escape-hatch
reconciliation:** a hatch-recorded TYPE step commits the field plus the resolved
corpus key when the human-typed value matches a corpus entry; otherwise it
commits as `value: "corpus:PENDING"` plus a quarantine record — a human either
adds the (synthetic) value to the corpus by recorded, versioned commit or the
manifest dies; replay of a PENDING manifest is refused until the reference
resolves at a pinned corpusVersion. A raw literal never commits.

**Environment precondition.** Discovery mode and probing are gated on a
machine-checked attestation: resolved config declares `envClass=RESETTABLE_TEST`
(startup assertion, build-failing test) and the reset capability answers a
per-run liveness check before the first probe. Replay of committed edges remains
permitted — those execute committed, validator-admitted, deterministic actions
re-checked at load time and at the executor; no LLM proposes anything during
replay (this carve-out does not presuppose the D-F review outcome). The
descriptor reserves a `dataClass` field for **D4**; `PRODUCTION_DERIVED` refuses
discovery until a superseding recorded decision under ADR 0010/D4 — a named
suspension condition in config, not a silent dependency.

Simpler things rejected: verb-pattern denylist (fails open on every novel route —
the LLM's proposals are exactly the unanticipated space; deny-by-default is cheap
because the route universe is statically enumerable); post-execution check only
(the harm precedes the check); validator-only single half (0009:180-186);
LLM route classifier (a model inside the safety filter); screen-the-string TYPE
(the risk rides on the field, not the string); banning TYPE (inflates the
escape-hatch bucket for no gain); a working agreement for the environment (M35's
own recorded history, 0009:105-107); a sandboxed app build (violates the
no-app-team-ask constraint and poisons signature comparability).

**Technical justification:**

- **Removes the prize, not just the path** — no process holds both a model
  credential and device/app authority; no LLM output executes without a
  deterministic verdict token; no artifact acquires trust at birth.
- **Termination restored with bounded churn** — the decision table (rules 3/4/5b)
  re-keys changed screens in one visit; the ladder caps per-node churn at R; the
  rate guard converts systematic failure into a loud stop.
- **Bad states unrepresentable where it matters most** — chain forks and duplicate
  roots die at the database; supersede-only history makes every correction
  findable and reversible; phantom cross-backend drift has no representation.
- **Every gate is a pure function of committed inputs** — thresholds, allowlists,
  corpus, and schemas are versioned config; identical inputs yield identical
  verdicts, so the S2 spike can measure false/missed re-key rates against
  pre-registered thresholds.

**Business justification:**

- **Cost:** eliminates the ~20%-of-screens-per-release escape-hatch flood (the
  release-week human spike) at the price of one baseline review and three
  human-maintained config files per release; promotion piggybacks on normal replay
  traversal, adding no dedicated device-minutes.
- **Time to market:** unblocks Lane 3 — the S2 measurement spike is worthless
  until the loop can terminate on changed screens (tasks.md:193); this ADR is the
  S1 gate.
- **Strategic positioning:** a banking estate can adopt LLM-driven capture only
  with audit-grade answers to "who proposed this, who approved it, and what could
  it ever have done" — typed actors, immutable origin provenance, and
  deny-by-default admission are that answer.

## Consequences

- **Three human-maintained committed configs per release** (route allowlist,
  navigation-field allowlist, input corpus) — one classification pass each; a
  misclassification is the residual risk class below.
- **Promotion measures replayability, not safety — priced, not hidden.** The
  surviving scenario is on record: a parameterless route misclassified NAV by a
  human probes, commits CANDIDATE, and auto-promotes on its first legitimate
  traversal. Bounds: DEEP_LINK promotion requires a recorded allowlist-version
  pass; retroactive tightening excludes the edge at load; quarantine reverses it
  append-only. Equivalent in kind to a bad code review.
- **A named residual of Critical #5 remains for ANCHOR_LESS nodes whose anchor
  and skeleton both change** — rule 5b excludes them; they route to the escape
  hatch. The S2 spike sizes this bucket with its own pass/kill threshold.
- **FIRST_SEEN arrival performs a deliberate, bounded cross-backend
  accessibilityId comparison** (reference-backend DES) — the
  no-cross-backend-comparison guarantee is honestly scoped to
  skeletonHash/titleAnchor.
- **The observation logs live outside the content hash** — `graph_version_sha` no
  longer covers verification recency. Deliberate: the alternative was snapshot
  churn per capture or a falsified sha (review #24).
- **Auto-commit removes per-commit human review** — a recorded control change,
  compensated by the CANDIDATE floor, the untouched spine audit pin, and the
  baseline review. Clarify-resolved 2026-07-31 (C4): the baseline review
  **blocks at the certification boundary only** — capture, discovery, and drift
  repair run freely; certification-bound conversions consume ASH-derived
  manifests only from a baseline-approved graph. (A fully advisory review could
  silently lapse — the exact finding-20 failure mode — which is why it was
  rejected.)
- **Two processes cost deployment and IPC complexity**; the park-and-sweep buffer
  must clear ADR 0007's compliance review or degrade to fail-loud-and-recapture.
- **The CANDIDATE floor is validator-enforced, not schema-enforced** — the
  detective recompute closes the bypass to detection, not prevention.
- **The lease-minting assumption is accepted, not verified**; its fallback (a
  standing vault password under executor-enforced discipline) materially weakens
  the story and is a recorded risk acceptance (clarify-resolved 2026-07-31, C2:
  accepted; verified on the week-0 access track).
- **Deferring parameterized deep links caps coverage** — parameterized detail
  screens ride tap paths until the typed-template fork is decided.
- Losing options' trade-offs: the walkthrough-as-drafted would have shipped
  fastest and reproduced every confirmed finding; human-gated-everything would
  have maximized per-artifact scrutiny at the cost of the program's economics;
  no-ASH would have kept risk at zero and the manual capture cost forever;
  denylist admission would have saved one classification pass and failed open on
  the exact threat; a graph DB would have bought traversal elegance at the price
  of a second system of record and a second integrity mechanism.
- Imposes on future work: every future lineage/graph consumer inherits
  supersede-not-update and typed actors; D3 must honor the offered
  per-app_version chain scope or renegotiate serialization; D5 must rule on the
  park-and-sweep buffer; any new backend needs its own signature rows and DES
  before release-facing use; any fourth LLM-adjacent path lands behind the
  screen-gate component by construction; the S2 spike must log raw signal values.

## Compliance

Fitness-function candidates continue the F1-F7 series; all are **CANDIDATE**
until ratified with this ADR.

- **F8 — credential-topology assertions (CANDIDATE; automated, startup + CI-blocking):**
  startup credential-absence checks in both processes (executor: no gateway
  credential, provider secret, or standing device credential; proposer: no
  device-cloud credential, vault mount, or database grant), each covered by a
  build-failing test (0013:186-190 construction); ArchUnit halves both ways (no
  provider/gateway type reachable from executor packages; no DeviceSession or
  vault-client type reachable from proposer packages; no broker/queue-consumer/
  outbox-relay type reachable from either channel package), each proven by a
  deliberately-violating sample per the T02 method; a grant-assertion job proves
  `svc-ash-proposer` holds zero database grants and an M40-style config check
  proves it has no writable persistent volume; a run presenting a lease or token
  minted for another run ID, or past TTL, quarantines.
- **F9 — screening call-site enforcement (CANDIDATE; automated, CI-blocking + runtime):**
  the two-half construction at CS1-CS5/CS7 (static: evidence-landing and channel
  packages depend on the screen-gate component, with no path from DeviceSession
  outputs to storage or channel except through it; runtime: unscreened payloads
  rejected at write and at egress) and the CS6 verdict-token construction
  (static: `act()`/`launchDeepLink()` call sites reachable only from
  validator-verdict-bearing types; runtime: verdict-token-less actions rejected,
  run quarantined). Zero secret/PII detections in prompt payloads, traces, and
  stored artifacts; a detection is an incident (0009:210-214).
- **F10 — graph write integrity (CANDIDATE; automated, CI-blocking + per-release):**
  Testcontainers proof that two concurrent transactions extending one head yield
  exactly one commit (fork-unrepresentable); commit-validator tests (birth-status
  VERIFIED rejected; out-of-class service deltas rejected and queued; actor
  CHECKs); the INSERT/SELECT-only grant assertion on all graph/signature/status/
  staging tables (this ADR's grant, tasks.md:50 construction); the per-release
  chain-verification job's detective recompute of first-appearance statuses,
  quarantining violations; a CI assertion that spine Flyway V1 contains no graph
  DDL (CI config, not a spine edit) and that no graph migration ships before the
  D3 amendment is Accepted.
- **F11 — admission enforcement (CANDIDATE; automated, blocking before execution):**
  validator + `launchDeepLink()` two-half tests (bypass harness proves the
  runtime half blocks alone); parameterless/exact-match rejection tests; the
  load-time exclusion test asserting no UPDATE is issued against
  `screen_graph_edges`; schema tests that a literal credential or input value in
  any manifest, edge, or `CandidateActionSet` fails validation; corpus-PENDING
  replay-refusal test; environment attestation and reset-liveness tests
  (build-failing on regression).
- **F12 — arrival determinism (CANDIDATE; automated, per build + feeding S2):**
  golden pre/post-release fixture pairs replay identical verdicts from identical
  inputs (the full tuple: both settle dumps, backend rows, path evidence, config
  version); a changed-screen fixture proves one-visit re-key with no
  budget exhaustion; every verdict (including NOT-ARRIVED/NO-VERDICT) logged with
  raw signal values, D as a raw fraction.
- **Red-team corpus case class (per release, owner: the security function per
  M36):** injection-steered discovery and probe scenarios, including the priced
  NAV-misclassification residual; a regression blocks the release.
- **Security-review queue entry (per ADR 0010):** the §12.4 ASH-Capture entry
  stands; the parallel track does not block acceptance.
- **Manual governance (per release, named humans):** the allowlist/corpus/field
  classification pass and the `APPROVE_GRAPH_BASELINE` review, both attributable
  individual decisions; threshold changes (τ_d, τ_strict, R, N, K, re-login
  bound, session caps) only by recorded decision under CF6.

## Notes

Author: sdd-synthesize (SDD Stage 2), invoked from Replan R1 Lane 2 D1; four
facet designs (signature, topology, writes, deeplink) adversarially verified —
all UPHELD_WITH_AMENDMENTS; all 36 verifier amendments applied in this text
Date: 2026-07-31
Approved by / date: Rajnish Khatri / 2026-07-31 (combined gate: SPEC-OK on the
ASH-Capture spec + this ADR Proposed → Accepted; the same gate ratified the ADR
0001 seam-vocabulary amendment, the ADR 0009 flip amendment — both now recorded
in their home ADRs — and the A11 constraint override, human-confirmed at
clarify C2)
Superseded date: —
Last modified / by / what: 2026-07-31 / combined SPEC-OK + acceptance gate
(owner) / clarify resolutions C1–C5 folded in; status Proposed → Accepted;
riders recorded in ADRs 0001 and 0009
Prior modification: 2026-07-31 / sdd-synthesize / initial draft from
verified facet packs