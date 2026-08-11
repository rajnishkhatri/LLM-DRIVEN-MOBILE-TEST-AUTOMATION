---
type: architecture
title: ADR 0012 — Make lineage tamper-evident with a per-conversion hash chain anchored in immutable object storage
description: 'The lineage-integrity decision spun out of stage-5 risk mitigation M38 (P1 register entry P1-5): lineage is called append-only, but in PostgreSQL append-only is a grant plus a convention, so nothing makes tampering evident. Every lineage row carries its predecessor''s digest within a per-conversion chain; chain heads are anchored into the immutable evidence object store through the ADR 0011 port, making tamper-evidence independent of the database being audited. Grants restrict the application role to INSERT/SELECT on lineage tables, asserted by an automated check, and corrections become compensating appends rather than updates. Detection, not prevention — stated as the honest limit.'
tags: [architecture, mobile-test-automation, adr, arch-decide]
---

# ADR 0012. Make lineage tamper-evident with a per-conversion hash chain anchored in immutable object storage

## Status

**Accepted** — 2026-07-27, at the combined gate that also re-signed-off the
spine spec (post-P1-mitigation baseline) and accepted ADR 0013. No missing
input blocked acceptance. Last responsible moment: **the first lineage
migration**, because the correction semantics this decision mandates
(supersede rather than update) must shape the schema from its first version —
retrofitting them onto an update-shaped schema is the expensive outcome this
ADR exists to avoid. Per ADR 0010 as amended, the security review runs as a
parallel track and did not block acceptance; the queue entry stands.

## Context

**Forces.** ADR 0007 makes the primary store the system of record and the spine
spec describes lineage as append-only. Stage-5 risk storming priced what that
description is actually worth: **in PostgreSQL, append-only is a grant and a
convention**, so anyone holding `UPDATE` can rewrite history and nothing in the
design makes the rewrite evident (P1 register entry P1-5, scored 3×2 = 6 by the
security lens, with a second facet at 4 for grant design that was neither built
nor asserted). Auditability & traceability is a driving characteristic;
security & privacy is top-3. The system's *product* is audit-grade certification
evidence, so the trustworthiness of the rows is not a supporting concern — it is
the deliverable.

**Why the evidence facts do not discount this.** E2 (mock data only) and E3
(validated internal network) reduce *confidentiality* risk. This is an
*integrity* risk, and the same reasoning already applied at M9 and M10 holds:
an audit chain on mock data still has to be intact. E3 in particular bounds who
can reach the database, which is precisely the population a privileged-insider
or misapplied-migration scenario draws from.

**What already exists to build on.** M9 (hash-at-pull) and M15 (hash-at-ingest)
digest *artifacts* and source snapshots. This decision extends the same
construction from files to **rows**, so the mechanism is familiar rather than
novel. ADR 0011 supplies immutable object storage — its object-lock precondition
is what makes anchoring worth doing.

**Alternatives considered.**

- **Per-conversion hash chain + chain-head anchoring into immutable object
  storage** (chosen).
- **Hash chain only, no anchoring** — cheaper and detects alteration, but the
  chain lives in the same store whose compromise is being detected: an actor able
  to rewrite a row can recompute the chain from that row forward. Detection
  survives only accidental corruption, not deliberate tampering.
- **Grants plus database audit logging / WAL archiving only** — near-zero cost,
  and defensible on the grounds that E3 bounds database reach. Same fatal
  property: detection depends on the platform being audited, so a privileged
  insider or a misapplied migration leaves no independent trace.
- **Cryptographic signing with a vault-held key** — stronger than anchoring
  (proves authorship, not just sequence), but it buys key management,
  rotation, and a signing-key compromise story for a property anchoring already
  delivers. The vault itself is unnamed until the M33 controls-baseline read
  returns, so this option depends on an open input that the chosen one does not.
- **External notarization service** — strongest independence, but a new external
  dependency with its own residency question, on a system whose external
  surface stage-5 has spent two passes trying to bound.

**Qualification.** Nygard test: passes — it changes the write path, adds a
primary-store→object-store dependency, and serves two driving characteristics
(one top-3). Third-law test: passes — every option trades independence,
key-management burden, write-path cost, or detection completeness. Timing:
now, because correction semantics must shape the first migration.

### Trade-off matrix

| Contextual factor (weight) | Chain + anchoring (chosen) | Chain only | Grants + DB audit log | Vault-key signing | External notarization |
|---|---|---|---|---|---|
| Independence from the store being audited (5) | **++** anchors sit under object lock | −− same store | −− same platform | + key is external, chain is not | ++ fully external |
| Detection completeness — alteration, deletion, reordering (5) | **++** chain covers all three | + all three, forgeable | − deletion visible only if logging is intact | ++ | ++ |
| No new key management (4) | **++** anchoring, not signing | ++ | ++ | −− rotation + compromise story | + service credentials only |
| No new external dependency (4) | **++** reuses ADR 0011 | ++ | ++ | + vault is internal but unnamed | −− new external surface, new residency question |
| Write-path cost (4) | **+** one read per append, serialized per conversion | + same | **++** none | − signing per row | −− network call on the write path |
| Cost to build in the spine (3) | **+** one column, one verifier, one anchor job | ++ | ++ | − | −− |

## Decision

**We will make lineage tamper-evident by chaining every lineage row to its
predecessor's digest within a per-conversion chain, anchoring chain heads into
the immutable evidence object store through the ADR 0011 port, restricting the
application role to `INSERT`/`SELECT` on lineage tables, and making every
correction a compensating append rather than an update.**

The why front and center: **anchoring is the load-bearing half.** A hash chain
alone proves internal consistency to whoever controls the database, which is the
wrong audience. Writing chain heads into a store where objects cannot be
overwritten means a database-side rewrite cannot also rewrite the evidence of
the rewrite — and it costs an interval job against a port ADR 0011 already
mandates, with no key material to manage.

**Technical justification:**

- **Chain scope is the conversion**, not the table. A conversion's lineage is
  inherently sequential, so chaining inside it adds no contention that the domain
  does not already have; a global chain would serialize every write in the system
  for no additional integrity property.
- **The digest computation joins the existing write transaction**, so ADR 0007's
  same-transaction invariant is preserved — a row and its chain link commit or
  fail together, and a partially chained lineage is not representable.
- **Verification is recomputation**, not a privileged operation: recompute each
  chain and compare its head to the anchors. A mismatch quarantines loudly (the
  M10a never-silent posture) rather than logging a warning.
- **Corrections as compensating appends** are the correct audit semantics
  independently of tampering — a superseding row preserves what was believed and
  when, where an update destroys it.

**Business justification:**

- **Strategic positioning:** "the evidence cannot be altered without detection,
  and here is the independent anchor" is an audit answer. "The table is
  append-only by convention" is an audit finding.
- **Cost:** one column, one interval job, one verifier, and a grant script —
  hours to low days, against a control that would be near-impossible to add
  credibly after the fact, since a chain built later can only attest from its
  start date forward.
- **Time to market:** nothing here gates the week-3 spine gate; the write-path
  cost is one indexed read per lineage append.

## Consequences

- **This detects; it does not prevent.** Stated plainly and not softened: an
  actor with `UPDATE` can still alter a row. What changes is that the alteration
  becomes provable rather than deniable, and provable-after-the-fact is the
  property an audit trail actually needs.
- **Anchoring is exactly as strong as object-lock immutability**, which ADR 0011
  lists as probe-dependent. If the platform branch returns a store without
  object lock, this control degrades to detection-within-one-system — the
  chain-only alternative by accident. That makes object lock a **hard
  requirement on ADR 0011's binding**, not a preference, and it is recorded as
  such here.
- **Compatible with crypto-shredding by construction** (M39, amended into ADR
  0011). Destroying an evidence object's encryption key makes the *object*
  unreadable; it alters no lineage row and therefore breaks no chain. Erasure and
  tamper-evidence do not collide — which is the one interaction worth checking
  before adopting both, and it checks out.
- **Supersede-not-update semantics constrain every future lineage consumer.**
  Readers must resolve the latest non-superseded row rather than assuming one row
  per fact. This is the real ongoing cost, and it is why the timing is "first
  migration" rather than "before release."
- **Restore gains a third step.** ADR 0011's post-restore custody reconcile is
  joined by chain verification: after a restore, chains must verify against
  anchors that survived independently. This is a genuine strengthening of M23 —
  a restore that silently lands mid-chain now surfaces.
- Losing options' trade-offs: chain-only and grants-plus-logging would have cost
  almost nothing and defended against accident but not intent; signing would have
  added authorship proof at the price of key management and a dependency on the
  still-unnamed vault; notarization would have bought maximum independence with a
  new external surface, on a system already fighting to bound that surface.
- Imposes on future work: no lineage `UPDATE` or `DELETE` from application code;
  every correction is a superseding append; new lineage row types join a chain.

## Compliance

- **Append-only grant assertion (automated, CI-blocking):** a test proves the
  application role cannot `UPDATE` or `DELETE` lineage tables, and that DDL is
  owned by a separate migration role. Same construction as F1/F2 but **not
  numbered into the F-series** — it is an ADR-owned mechanism, and arch-validate
  must inventory it alongside them.
- **Chain verification (automated, per release and after every restore):**
  recompute all chains, compare heads against anchors, prove zero mismatches.
  A mismatch quarantines and alerts; it never degrades to a warning.
- **Anchor freshness (automated, operational):** anchors are written at a defined
  interval and a stale anchor is an alert, because an anchoring job that has
  silently stopped leaves the window between the last anchor and now unprotected
  — the failure mode most likely to go unnoticed.
- **Immutability precondition (inherited assertion):** ADR 0011's
  deployment-time write-once check covers the anchor bucket explicitly, not only
  evidence buckets.
- **Restore drill extension (manual, quarterly):** chain verification joins the
  ADR 0011 restore drill, so the coherence claim is exercised rather than
  assumed.
- **Security-review queue entry (per ADR 0010):** this ADR governs the integrity
  of the audit record; the review runs as parallel work, drained before first
  production release.

### Graph-version lineage chain amendment (2026-08-01, ADR 0014 acceptance / Replan R1 D3)

ADR 0014 committed a `screen_graph_versions.lineage_digest TEXT NOT NULL` column (0014:354-355; schema at o1-pipeline-walkthrough.md:891) and ruled that no ScreenGraph migration ships until this amendment is Accepted, because `lineage_digest NOT NULL` is unsatisfiable without a defined chain (0014:355-357, :797-798). This amendment defines that chain. It is the one D-deferral of the three that is a *hard build blocker* — until it lands, ASH-Capture cannot legally migrate the graph tables and cannot store a single node or edge, so audit-grade capture provenance (o1-pipeline-walkthrough.md:884, :985) has no anchor. It does **not** touch, widen, or globalize the per-conversion lineage chain of the base decision (0012:88, :102-105); it adds a **separate, narrowly-scoped chain class** alongside it.

**Decision — five points.**

1. **A per-`app_version` graph-version chain, scope-parallel to the per-conversion chain — never global.** Each row in `screen_graph_versions` sets `lineage_digest = H(canonical(prev row's digest input))`, i.e. the digest of its predecessor version within the *same* `app_version` chain, computed inside the same local transaction that inserts the version + node/edge rows (preserving ADR 0007's same-transaction invariant exactly as the base decision does, 0012:106-108). The chain scope is **the `app_version`**, chosen for the identical reason the base decision scoped chains to the conversion (0012:102-105): a per-`app_version` chain is inherently sequential under ADR 0014's writer serialization and adds no contention the domain does not already have, whereas a chain over the whole `screen_graph_versions` table would serialize every release's writes for no added integrity property — the exact over-scoping the base decision rejects (0012:104-105).

2. **Canonical digest input and genesis constant, stated so verification is reproducible.** "Digest input" for a graph version is the SHA-256 over the canonical (UTF-8, field-sorted, no-whitespace-JSON) serialization of exactly these fields, in this order: `app_version`, `prev_version_sha`, `graph_version_sha` (the hash-of-graph-contents already defined at o1-pipeline-walkthrough.md:864), and the node/edge set digest. `derived_from_version_sha` (the informational cross-release reference, 0014:453-456) and all timestamps are **excluded** — they are audit references, not chained predecessors, so including them would falsify per-`app_version` linearity or make the digest non-reproducible after a restore. A **root commit** (`prev_version_sha IS NULL`) sets `lineage_digest` to the fixed versioned genesis constant `"GRAPHCHAIN-GENESIS-v1"` (a defined sentinel, never NULL and never a back-link to the prior release), so the `NOT NULL` contract holds at genesis and cross-release continuity stays an audit reference rather than a chained link. Each `app_version` chain's fork-freedom is inherited from ADR 0014's `UNIQUE (prev_version_sha) WHERE prev_version_sha IS NOT NULL` and `UNIQUE (app_version) WHERE prev_version_sha IS NULL` partial indexes (0014:442-456), which make commits per `app_version` totally ordered (0014:467-469) — this amendment **accepts the per-`app_version` chain scope ADR 0014 offered** (0014:757-758) rather than renegotiating serialization.

3. **Chain heads anchored via the ADR 0011 port — the load-bearing half, unchanged from the base decision.** The head of each `app_version` graph chain is anchored into the immutable evidence object store through the ADR 0011 port (0012:89, :95-98), on the base decision's interval-job cadence (0012:97-98, :172-174). This reuses the anchor-bucket write-once check ADR 0012 already added to ADR 0011 (0011:223-226), which already covers the anchor bucket for *all* chain classes — so no new ADR 0011 amendment is required, and the inheritance is recorded here rather than assumed. Anchoring remains the load-bearing half for the same reason as the base decision (0012:93-98): a graph chain living only in the database it protects is forgeable by whoever holds `UPDATE`. A predecessor-digest link is required *in addition to* anchoring because anchoring alone detects content alteration but not **deletion or reordering of versions** — first-class detection targets of the base decision (0012:79) that per-version anchors each validate individually and therefore miss.

4. **Chain-membership ruling for the records ADR 0014 parked (the D3 ruling awaited at 0014:248).**
   - **In the chain:** re-key evidence records (0014:244-248), quarantine lineage rows (0014:431), promotion lineage rows (0014:412), `APPROVE_GRAPH_BASELINE` rows (0014:497-498), and `REJECTED_URL` / load-time quarantine admission rows (0014:634-639) are **corrections-and-decisions-as-compensating-appends** and join the graph lineage chain — precisely the supersede-not-update audit semantic the base decision mandates (0012:112-114, :145-148, :158-159). They commit only at successful loop completion inside the minting version's transaction (0014:241-243), so they chain *with the version*, not independently.
   - **Out of the chain, by explicit ruling:** the append-only observation logs `screen_node_signatures` and `screen_edge_status` are **not chained and do not mint versions** — ADR 0014 placed them outside the content hash as context-FK observation logs precisely to avoid per-capture snapshot churn (0014:295-302, :728-730). Chaining their high-frequency `last_verified_at` / re-VERIFY / `FIRST_SEEN_ON_BACKEND` appends would reintroduce that churn and falsify the `graph_version_sha = hash-of-graph-contents` invariant (o1-pipeline-walkthrough.md:864). Their integrity is covered by append-only INSERT/SELECT grants (point 5) plus the fact that every *decision* derived from them lands as a chained evidence record under the version that consumed them. This is the honest limit, stated: verification-recency observations are grant-protected append-only, not chain-protected — the same posture ADR 0014 already accepted for them (0014:728-730).

5. **Grants and append-only CI extended to the `screen_graph_*` tables — inventoried with, not re-owned from, ADR 0014.** ADR 0014's INSERT/SELECT-only grant on the graph tables is a deliberately *new ADR 0014-owned decision* (0014:117, :372-377, F10 at 0014:793-794), mirroring rather than inheriting this ADR's lineage-table grant (0012:90, :163-166). This amendment does **not** transfer that ownership into ADR 0012's scope (which is lineage tables only, 0012:90) — doing so would silently widen 0012's stated scope. Instead, arch-validate **inventories both grant assertions together** for drift-detection: ADR 0012's lineage-table append-only mechanism and ADR 0014's F10 graph-table append-only mechanism are checked as one drift-detection set, two ownership scopes, so the two INSERT/SELECT-only invariants cannot diverge silently even though neither absorbs the other. The chain-membership ruling in point 4 is legitimately this amendment's (D3's) to make and stands.

**What this amendment does NOT do (guardrails against reversing the base decision):** it does not merge, widen, or globalize the per-conversion chain (0012:88); it does not add a second anchoring mechanism or a new key — anchoring, not signing, is preserved (0012:80, :95-98, :154-156); it does not permit any graph `UPDATE`/`DELETE` from application code (0012:158-159 extended); it does not re-own ADR 0014's graph grant; and it does not change the base decision's honest limit — this **detects; it does not prevent** (0012:130-133) tampering of graph history. Recorded here rather than reinterpreted in passing.

**Consequences riders (appended to `## Consequences`, 0012:128-159):**
- **The graph chain inherits the detect-not-prevent limit — and one gap is left open by ruling.** The `screen_node_signatures`/`screen_edge_status` observation logs are grant-protected append-only, not chain-protected (point 4). Every audit-load-bearing fact re-lands as a chained evidence record, so the residual is bulk-tampering of recency metadata only — recorded here as the honest limit, with a periodic tail-digest available as a fast-follow (see clarify gate) rather than framed as already closed.
- **The graph chain's linearity is coupled to ADR 0014's writer serialization.** Its contention-free order is guaranteed only *because* forks are unrepresentable (0014:442-456, :467-469). **Imposes on future work:** any D5 (ADR 0007) change to graph-write ordering that permits out-of-head-order commits re-opens this amendment (0014:757-758).

**Compliance riders (appended to `## Compliance`, 0012:161-183):** All are ADR 0012-owned mechanisms that arch-validate inventories alongside the F-series (not F-numbered — the base decision's convention, 0012:166-167), *except* the graph grant assertion, which stays ADR 0014-owned (F10) and is only *inventoried together* per point 5.

- **Graph chain verification (automated, per release + after every restore) — extends 0012:168-170.** Recompute every `app_version` graph chain using the canonical digest input and genesis constant of point 2, compare each head against its ADR 0011 anchor, prove zero mismatches; a mismatch **quarantines loudly and never degrades to a warning** (the never-silent posture, 0012:110-111, :168-170). This pass additionally recomputes first-appearance edge status and quarantines any edge whose first committed status was not CANDIDATE — **merged with ADR 0014's detective recompute (0014:409-411, :794-795) into one pass**, so chain-verification and the CANDIDATE-floor recompute do not race each other's quarantine writes and share one quarantine-reason provenance.
- **Graph anchor freshness (automated, operational) — extends 0012:171-174.** Graph chain heads are anchored at the base decision's defined interval; a stale graph anchor is an alert, closing the last-anchor-to-now window for graph versions exactly as for conversion chains.
- **Anchor-bucket immutability (inherited assertion — no new check) — 0011:223-226 / 0012:175-177.** ADR 0011's deployment-time write-once check already covers *the* anchor bucket, which now also holds graph chain-head anchors; no ADR 0011 amendment is required, recorded so the inheritance is explicit.
- **Restore-drill extension (manual, quarterly) — extends 0012:178-180 / 0011:232-233.** Graph chain verification joins the quarterly restore drill: after a restore, every `app_version` graph chain must verify against anchors that survived independently, surfacing a restore that silently lands mid-chain.
- **Graph grant assertion — inventoried, not re-owned (ADR 0014 F10, per point 5).** ADR 0014's Testcontainers grant test (0014:376, :793-794) proving the application role cannot `UPDATE`/`DELETE` any `screen_graph_*`, signature, status, or `capture_run_edges` table stays **ADR 0014-owned**; arch-validate inventories it in the same drift-detection set as ADR 0012's lineage-table grant so the two cannot diverge. Recorded here rather than reinterpreted in passing.
- **Migration gate lift — a mechanical predicate, not a status claim (resolves 0014:355-357, :797-798).** The ADR 0014 F10 assertion "no graph migration ships before the D3 amendment is Accepted" is evaluated by CI against a committed `d3-accepted` status marker (the ScreenGraph migrations stay behind the V1-no-graph-DDL guard until that marker is present in the repo); the guard flips off only when the marker is committed, so the gate lift is itself testable rather than a manual assertion. On that marker landing, `lineage_digest NOT NULL` is satisfiable and the ScreenGraph migration may leave the V1 hold (Replan R1; the V1 guard config itself stays, 0014:357).

## Notes

Author: arch-decide, invoked from stage-5 arch-risk (P1 mitigation M38)
Date: 2026-07-27
Approved by / date: the owner / 2026-07-27, at the combined gate (spec
post-P1-mitigation re-sign-off + ADR 0012 + ADR 0013 + the ADR 0011 M39
amendment, one approve-all decision)
Superseded date: —
Last modified / by / what: 2026-07-27 / arch-decide / Status flipped
Proposed → Accepted at the combined gate
Last modified / by / what: 2026-08-01 / ADR 0014 acceptance (Replan R1 D3, owner) / Graph-version lineage chain amendment added — defines a per-app_version graph chain (canonical digest input + "GRAPHCHAIN-GENESIS-v1" root constant, chain-heads anchored via the ADR 0011 port) that makes ADR 0014's `lineage_digest NOT NULL` satisfiable and lifts the ScreenGraph migration gate on a mechanical `d3-accepted` marker; re-key/quarantine/promotion/baseline/rejected-URL rows chained, observation logs ruled grant-protected-only; the graph grant assertion stays ADR-0014-owned (F10) and is inventoried-together, not re-owned. Status unchanged (Accepted) — the amendment defines a separate narrowly-scoped chain class alongside the per-conversion chain and never globalizes it; it does not reverse the decision.
