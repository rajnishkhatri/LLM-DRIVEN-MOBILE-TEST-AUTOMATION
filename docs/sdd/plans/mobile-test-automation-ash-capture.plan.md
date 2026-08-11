# mobile-test-automation-ash-capture — Plan

**Status:** **PLAN-OK — recorded 2026-08-01.** Approved as drafted; three plan-gate forks ruled on the recommendations (2026-08-01, owner): (1) **proposer topology** = co-located two OS processes in one deployment unit over the synchronous localhost channel (F8 assertions are per-process; promotable to independent scaling later as a deployment change, not architecture — 0014:539-544); (2) **WP ordering** = front-load the D-A/write core (WP-A4 arrival + WP-A2 write path) as the critical path to deliver S1 and unblock the S2 spike soonest, WP-A5 topology in parallel off WP-A0; (3) **`capture_run_edges.retention_class` interim posture** = ship the column present-but-unconstrained, the enum CHECK lands as a one-cell follow-up migration when the ADR 0006 rider is Accepted. **UPDATE 2026-08-01: the ADR 0006 rider is now Accepted** — the enum is `CONSUMED | FORENSIC | PENDING_MINT`, the interim ships two columns (`retention_class` + `terminal_outcome_at`, the `FORENSIC` 30-day-TTL basis), and the follow-up CHECK is task A13b. **No external dependency remains OPEN.** No feature commit lands before WP-A0 (task-zero) is green. Next stage: **sdd-implement** (WP-A0 first).

| Header | Value |
|---|---|
| Spec | `docs/sdd/specs/mobile-test-automation-ash-capture.spec.md` (SPEC-OK; 61 named EARS criteria, 45 failure-path + happy-path) |
| Constitution | A1 (least machinery), G1 (every new abstraction justified), A7 (spec-before-code, satisfied by construction), S1 (spine board untouched), F1 (no LLM in spine) |
| Gates asserted CI-blocking | F8 (credential-absence, both processes), F9 (screen-gate / CS1–CS7 two-half), F10 (grant assertion), F11 (executor allowlist re-check), F12 (arrival determinism) |
| ADR posture | **No NEW ADR.** ADR 0014 (Accepted) plus its D3/D4/D5 amendments cover the whole design; the **ADR 0006 retention-class rider is now Accepted (2026-08-01)** — enum `CONSUMED\|FORENSIC\|PENDING_MINT`, closing the last external dependency. **No ADR item remains OPEN.** |
| Repo posture | **Standalone Maven reactor + two Spring Boot deployables**, consuming **published** `spine-contracts` + `screening` as versioned dependencies (reuse, never fork). Spine board T01–T43 untouched (S1). |

---

## 1. Approach (A1 — the simplest thing that satisfies the criteria)

Build ASH-Capture as its **own Maven reactor and two Spring Boot deployables** in a **new repository**, consuming the already-published spine artifacts as versioned dependencies, with the least machinery that satisfies every ASH EARS criterion:

- **Two processes, because credential non-co-residence demands it — not one.** The Capture Executor (`svc-ash-executor`) and the Action Proposer (`svc-ash-proposer`) are two OS processes that can never resolve each other's credentials (0014:166-183, :513-530). One process with module boundaries is **rejected**: "module boundaries are not startup-assertable; the exact defect 0013 corrected" (0014:566-567). A boundary proves *availability*, not credential *absence* — so the split is the simplest thing that makes the startup credential-absence assertion (F8) even *possible* (spec **startup-absence**, **proposer-blind**).
- **No graph DB — PostgreSQL append-only snapshots (D-D).** The ScreenGraph lives in the existing PostgreSQL primary store as full snapshots per `graph_version_sha`, supersede-not-update, no second system of record (0014:346-360). Fork-safety here is two partial unique indexes, not a new engine (0014:442-445, **fork-unrepresentable**).
- **No third queue — D5 park-and-sweep is an intra-process buffer, not a seam.** Contention parks staged edges (`COMMIT_CONTENDED`) and a sweeper re-drives them (0014:457-466); "a bounded retry buffer over rows the same process family owns — not a third component-to-component seam". It **defaults fail-loud** (0014:465-466, **park-not-drop**). The executor↔proposer channel is a synchronous localhost request/response, deliberately **not** a queue (0014:539-544).
- **Reuse the published spine, do not re-build it.** `spine-contracts` and `screening` are consumed as **versioned published Maven dependencies** — the cleanest F1 boundary — never forked or copied. `CandidateActionSet.locator` reuses the existing `LocatorCandidate` type (0014:44-46); the screen-gate is a *promotion* of the existing screening library (0014:600-601), not a re-implementation.
- **No LLM anywhere but the proposer.** The proposer, its Invoke Models seam implementation, and the gateway-credential config land in the **ASH repo only**; nothing model-adjacent touches the spine repo (0014:527-530).

---

## 2. Repository architecture

```
mobile-test-automation-ash-capture/     (new repo — standalone reactor, TWO deployables)
├── pom.xml                             reactor + enforcer; pins published spine deps by version:
│                                       spine-contracts:<v>, screening:<v>  (CONSUMED, never forked)
│
├── svc-ash-executor/                   DEPLOYABLE 1 — the sole writer, holds device + app-cred lease
│     loop/          §11.4 decision tree, budgets, 3-strike no-progress          (0014:514-516)
│     arrival/       two predicates + fixed-order decision table (rules 1-6/5b),
│                    DES computation, demotion ladder — pure fn, no model call    (0014:192-262)
│     validator/    deterministic validator: CandidateActionSet re-validation,
│                    deep-link admission (D-I), TYPE/field allowlist, VERDICT TOKEN mint (CS6)
│     device/        DeviceSession: single-run token, launchDeepLink() re-validate,
│                    biometric injection API, login() (sole vault:-resolver)       (0014:558-563)
│     credential/    run-scoped app-cred lease (injected vault ref, TTL/30-min ceiling),
│                    ≤2 re-login bound, post-run sweep (3 hygiene checks)           (0014:547-564)
│     writepath/     CAS writer protocol (advisory lock + rebase + retry≤3),
│                    edge_id SHA-256, CANDIDATE-at-birth, promotion, quarantine,
│                    park-and-sweep sweeper (intra-process, fail-loud default)      (0014:379-469)
│     screengate/    the ASH screen-gate COMPONENT — executor's only evidence-landing
│                    adapter (CS1/CS5); every DeviceSession→storage path routes here (0014:599-602)
│     commit/        commit-validator (delta-class D-F), typed-actor columns,
│                    APPROVE_GRAPH_BASELINE review view, per-release chain-verify job (0014:478-506)
│
├── svc-ash-proposer/                   DEPLOYABLE 2 — SEPARATE PROCESS, ZERO grants
│                                       (no DeviceSession type, no vault client, no DB grant,
│                                        no writable volume — 0014:519-524, spec proposer-blind)
│     seam/          Invoke Models seam IMPLEMENTATION  (lives ONLY here — F1)      (0014:519-528)
│     parse/         model-free-text → CandidateActionSet (≤K=3), parse-or-drop;
│                    free text NEVER crosses the boundary                           (0014:521-522)
│     channel/       proposer's channel adapter = the seam's only ingress (CS2),
│                    routes through screen-gate before egress                       (0014:584,:602)
│
├── ash-graph/                          Graph schema + Flyway migrations module
│   db/migration/    screen_graph_versions/nodes/edges (snapshot per sha);
│                    screen_node_signatures + screen_edge_status (per-backend,
│                    append-only observation logs OUTSIDE the content hash);
│                    capture_run_edges STAGING (keyed by capture_run_id);
│                    UNIQUE(prev_version_sha) WHERE NOT NULL + UNIQUE(app_version)
│                    WHERE prev_version_sha IS NULL  (forks unrepresentable);
│                    INSERT/SELECT-only grants on ALL screen_graph_*/sig/status/staging
│                    GATED on the d3-accepted marker: no graph migration ships until
│                    D3 (ADR-0012 amendment) is Accepted — it IS Accepted now.
│   NOTE: capture_run_edges ships TWO interim columns (retention_class +
│         terminal_outcome_at), both present-but-unconstrained; the enum CHECK is
│         DECIDED (ADR-0006 rider Accepted 2026-08-01: CONSUMED|FORENSIC|
│         PENDING_MINT) and lands in the one-cell follow-up A13b.
│
├── ash-config/                         committed configs + thresholds + seam schemas
│                    CandidateActionSet.schema.json / ObservationPacket.schema.json
│                    deeplink-allowlist (exact-route, NAV/MUTATING, no wildcards)
│                    navigation-field-allowlist (role + a11y-id; amount/IBAN/OTP never)
│                    capture-input-corpus (synthetic, corpusVersion pinned)
│                    thresholds.yaml  τ_d=0.6 τ_strict=0.8 R=3 N=1 K=3 ≤2-relogin
│                    — CF6-governed, pinned on lineage
│
├── ash-archtests/                      F8/F9/F11 ArchUnit halves + runtime-half harnesses
│                    F8: no provider/gateway type reachable from executor pkgs;
│                        no DeviceSession/vault-client from proposer pkgs;
│                        no broker/queue/outbox type from either channel pkg
│                    F9: evidence-landing + channel pkgs depend on screen-gate;
│                        act()/launchDeepLink() reachable only from verdict-bearing types
│                    F11: validator + launchDeepLink() two-half; load-time
│                        exclusion asserts NO UPDATE on screen_graph_edges
│
├── app/                                Spring wiring for BOTH deployables (profile-split)
└── ci/                                 F8-F12 CI-blocking; d3-accepted marker gate;
                                        flip-gate assertion; spine-Flyway-V1-no-graph-DDL scan;
                                        Testcontainers (Postgres); grant-assertion job
                                        (CI CONFIG, not a spine edit — S1)
```

**Consumed (published spine artifacts — dependencies, NOT rebuilt):** `spine-contracts` (`LocatorCandidate` reused by `CandidateActionSet`, IR records, marker enums), `screening` (secret/PII detector + red-team corpus, promoted to a screen-gate *component* here), the ADR 0011 object-storage port + MinIO adapter (graph JSON anchoring), Flyway + Testcontainers + ArchUnit tooling conventions.

**New in this repo:** both deployables, the deterministic arrival table + DES, the deterministic validator + verdict token, the CAS write path + `capture_run_edges` staging, the per-backend signature/status schema, the screen-gate component, the three committed configs, the Invoke Models seam **implementation** + gateway-cred config, and F8–F12.

---

## 3. Technology selections (plan-level, inside ADR envelopes)

| Concern | Pick | Envelope |
|---|---|---|
| Language / build | Java 21, Maven multi-module reactor (standalone) | mirrors spine; owner decision (this session) |
| Store | PostgreSQL 16, JSONB graph snapshots, Flyway | D-D — no graph DB (0014:346-360) |
| Graph write serialization | `pg_advisory_xact_lock` + two partial unique indexes, retry ≤3 | D-E — forks unrepresentable (0014:442-445) |
| **Invoke Models seam impl** | provider adapter behind the ADR 0001 seam — **lives ONLY in `svc-ash-proposer`** | F1; D-G (0014:519-528) |
| **Gateway-credential config** | injected into the proposer process **only**; executor asserts its absence at startup | ADR 0013; F8 (0014:519-524) |
| App-credential lease | injected vault ref (M34), in-memory, run-ID-scoped, TTL / 30-min ceiling | D-G (0014:547-551) |
| Object storage | ADR 0011 port + MinIO adapter — **consumed from spine**, anchors graph JSON | D-D (0014:355-357) |
| Fitness functions | ArchUnit (F8/F9/F11 static halves) + runtime-assertion halves in code | ADR 0009 two-half (0014:768-806) |
| CI test infra | Testcontainers (Postgres) — grant assertion, fork-unrepresentable proof | F10 (0014:793-794) |
| Secrets scan | screening library's secret detector — zero-detection post-run sweep | D-G (0014:563-564) |
| Screening | **published `screening` library**, promoted to a screen-gate component here | D-H flip 3-of-3 (0014:599-602) |
| Channel | synchronous localhost request/response (NOT a queue) | D-G (0014:539-544) |

### G1 — new abstractions, with the simpler thing rejected

| Abstraction | What it buys | Simpler thing rejected, why |
|---|---|---|
| **Two-process split** | Credential **non-co-residence** as a *startup-assertable* property (F8) | One process with module boundaries — "module boundaries are not startup-assertable; the exact defect 0013 corrected" (0014:566-567) |
| **Screen-gate component** | Structural, ArchUnit-enforced screening **visibility** (F9) | A plain screening library call — invisible to ArchUnit; the flip crossing 3-of-3 forces structural promotion (0014:591-598) |
| **Deterministic validator + verdict token** (CS6) | LLM can **only propose**: `act()`/`launchDeepLink()` reachable only from verdict-bearing types | Trust the proposer's output — "that's the whole ADR"; screening "bounds content, not action authority" (0014:613-614) |
| **`capture_run_edges` staging table** | Zero graph rows commit on ABORT/CRASH/TIMEOUT/NO_PROGRESS/BUDGET_EXHAUSTED; CRASH forensics survive the process | In-memory-accumulate-and-write-once — forensics/parked-commits/escape-hatch sessions span human time beyond one process (0014:388-391) |
| **Per-backend signature/status rows** | Phantom cross-backend drift structurally unrepresentable | Signature fields on `screen_graph_nodes` — three backends write incomparable hashes into one graph (0014:96-97) |
| **Append-only observation logs outside the content hash** | Re-VERIFY / `last_verified_at` append without minting a graph version | Fold verification recency into the content hash — forces snapshot churn or a falsified sha (0014:729-730) |
| **CAS writer protocol** | Chain forks and duplicate roots die **at the database** | Advisory lock alone / SERIALIZABLE / a single-writer graph service — "a new always-on component plus a queue for a problem two partial indexes solve" (0014:472-476) |

---

## 4. Plan-level values the spec delegated

All config-shaped, adjustable without re-opening the plan **except** the ADR-0006-blocked row, which is a real open decision. τ_d, τ_strict, R, N, K, the re-login bound, and the session caps are **committed versioned constants under CF6's no-silent-disable rule** — changeable only by a recorded decision. They live in the versioned `thresholds.yaml`, whose version stamps every arrival evidence record (0014:246).

| Value | Setting | Note / ground |
|---|---|---|
| DES arrival threshold **τ_d** | **0.6** | standard path (rules 3/6); CF6-governed, S2-calibrated (0014:208-210) |
| Strict DES threshold **τ_strict** | **0.8** | ANCHOR_LESS/WEAK_DES strict path (rules 5/5b); S2 spike MUST log D as a raw fraction (0014:210-212) |
| Re-key demotion count **R** | **3** | ≥ R RE-KEY within one appVersion → `DYNAMIC_SKELETON` (D-C, 0014:329-331) |
| Distinct-run promotion **N** | **1** | one distinct-`capture_run_id` confirmation promotes CANDIDATE→VERIFIED (D-E, 0014:414-417) |
| `CandidateActionSet` cap **K** | **3** | proposer budget; distinct from spine replay K=1 (S5); unpinned K forbidden by CF6/N10 (0014:536-538) |
| Re-login bound | **≤ 2 per capture request** | third attempt aborts to the escape hatch with an attributable record (0014:552-555) |
| Session rate guard (floor) | abort at **RE-KEY ≥ 3 AND > 30% of visited nodes**; **≤ 1 committed re-key per target request** | per-target allowance takes precedence below the floor (0014:252-256) |
| App-credential lease TTL / ceiling | run-scoped, carries run ID; expires at run end or a 30-minute ceiling | executor-only, injected vault ref (M34) (0014:551) |
| Device session token | single-run, carries run ID; expires at run end / ceiling | ADR 0013 mechanism verbatim in shape (0014:516) |
| Service principals | **`svc-ash-executor`** (sole writer + device + lease), **`svc-ash-proposer`** (stateless, gateway cred, zero grants) | only the executor ever appears as a writer (0014:514-520) |
| Reference backend (D-B) | **Perfecto** | sole backend allowed for the FIRST_SEEN cross-backend accessibilityId DES comparison (0014:287-289) |
| Retention class for `capture_run_edges` | **DECIDED — ADR 0006 rider Accepted 2026-08-01: `CONSUMED \| FORENSIC \| PENDING_MINT`** | D4 split the retention-class enum out to a named companion ADR 0006 rider; that rider is now **Accepted**. Three values, one per distinct purge behavior: `CONSUMED` (event-purged in-band after mint + read-gated backstop), `FORENSIC` (bounded 30-day CF6-governed TTL from `terminal_outcome_at`, for zero-graph-row terminal-failure staging), `PENDING_MINT` (hands-off; folds parked-contended + escape-hatch rows). Strictly conversion-state — no value outlives certification (durable copy is `screen_graph_*`). Interim ships **two** columns present-but-unconstrained (`retention_class` + `terminal_outcome_at`); the enum CHECK is the one-cell follow-up **A13b**. **No delegated value remains open.** |

Every threshold is now *closed* (a committed value). The retention-class row — the last external decision, a genuine one rather than a "set-it-later" placeholder — was closed by the **ADR 0006 rider, Accepted 2026-08-01**. **No delegated value remains OPEN.**

---

## 5. Work packages and dependency order

Task zero is **WP0 by spec mandate** (M18): scaffold + the fitness functions wired **CI-blocking before any feature commit.** The discovery loop cannot execute against any device until the ADR 0009 flip amendment is merged (**flip-gate**) — that amendment **is merged now**, so WP0 asserts the flip-gate as a CI predicate rather than gating the board on an external merge. The `d3-accepted` marker is a **mechanical committed CI predicate** — D3 is Accepted, so WP0 lands the marker and WP1 (schema+migrations) is unblocked from day one.

Legend: **∥** = parallelizable with siblings once the shared dependency is met.

| WP | Content | Depends | EARS closed | Wk |
|---|---|---|---|---|
| **WP0** | **Task zero (M18 — strictly first).** ASH reactor scaffold (standalone, depending on **published** `spine-contracts`+`screening`); two-process modules; CI wires **F8** (credential-absence startup assertions both processes + symmetric ArchUnit halves + the **grant-assertion job** + M40 writable-volume check), **F9** (CS1–CS7 static screen-gate rules + CS6 **verdict-token** static construction), **F11** (executor `launchDeepLink()` allowlist re-check); the **flip-gate CI assertion**; the committed **`d3-accepted` marker**; the **spine-Flyway-V1-no-graph-DDL scan** (CI config only, S1). Each rule proven by a deliberately-violating sample (T02). | — (published spine artifacts) | **startup-absence**, **proposer-blind** (F8); **verdict-token**, **screen-before-write** (F9 static); **executor-recheck** (F11 static); **flip-gate**; **d3-gate** (both clauses) | 0 |
| **WP1** | **Graph schema + migrations (D-D/D-E).** `screen_graph_versions/nodes/edges`, per-backend `screen_node_signatures`/`screen_edge_status` (append-only, outside the content hash), `capture_run_edges` staging; **INSERT/SELECT-only grant** (ADR 0014's own grant, mirroring not inheriting ADR 0012) with CI-blocking assertion; the two **partial unique indexes**; typed-actor columns; **two interim columns present-but-unconstrained** (`retention_class` + `terminal_outcome_at`); the enum CHECK is **DECIDED (ADR 0006 rider Accepted 2026-08-01)** and lands as the one-cell follow-up **A13b**. Unblocked by the `d3-accepted` marker. | WP0 | **supersede-only**, **fork-unrepresentable**, **per-backend-status**, **d3-gate** (migration half), **retention-class-check** (A13b) | 1 |
| **WP2** | **Arrival decision table + re-keying (D-A) — the core.** Two-predicate split; DES computation (cap 7, min 3, `WEAK_DES`); the fixed-order rule table 1→6 incl. 5b; MATCH re-VERIFY; `¬S`→NO-VERDICT strike; supersede-based re-key with full evidence record; the session rate guard. **Pure deterministic function** of committed inputs (F12). | WP1 | **des-before-verdict**, **title-collision-guard**, **strict-anchorless**, **rate-guard-floor**, D-A rules 1/2/3/4/5/5b/6, **verdict-pure-function**; **F12** | 1–2 |
| **WP3** | **Backend-scoped signatures (D-B).** `screen_id` cross-backend; arrival always selects the executing backend's row; backend-crossing replay treats non-VERIFIED-for-B edges as UNVERIFIED; the **Perfecto reference-backend** FIRST_SEEN cross-backend DES path. | WP2 | **reference-des** | 2 |
| **WP4** | **Demotion / collision (D-C).** Collision enforcement (`SIGNATURE_COLLIDED` → hatch); the demotion ladder (≥R RE-KEY → `DYNAMIC_SKELETON`; 2× D<τ_d → `SIGNATURE_DEFEATING` → hatch); deep-link probe upgraded to the full strict arrival table. | WP2, WP3 | **demotion-ladder**, **D-C-signature-collided**, **D-C-deeplink-strict** | 2–3 |
| **WP5** | **Staged write path + fork-unrepresentable CAS + park-and-sweep (D-E / D5).** Terminal-commit-only staging; `edge_id = SHA-256(canonical(...))`; CANDIDATE-at-birth floor + detective per-release chain recompute; distinct-run promotion (N=1); quarantine-by-superseding-snapshot + lineage cross-reference (C5); the CAS writer protocol; release-root with the VERIFIED→UNVERIFIED flip; **park-and-sweep** buffer (D5-permitted, **default fail-loud**); broken-on-mismatch; verified-preferred search; chain-same-tx. | WP1, WP4 | **terminal-commit-only**, **candidate-at-birth**, **fork-unrepresentable** (writer half), **park-not-drop**, **broken-on-mismatch**, **quarantine-superseding**, **recall-scope**, **chain-same-txn**, **verified-preferred**, **release-root**, **done-commit**, **distinct-run-promotion**, **concurrent-rebase** | 3–4 |
| **WP6** | **Typed-actor + baseline review (D-F).** INDIVIDUAL-kind CHECK on quarantine release; principal/actor_kind/steering_principal schema rejection; the bounded **delta-class** commit validator; `APPROVE_GRAPH_BASELINE` lineage row + review view (CF9; blocks at the certification boundary only — C4). | WP5 | **typed-actor**, **D-F-individual-principal**, **delta-class-bound**, **approve-graph-baseline** | 4 |
| **WP7** | **Two-process topology + credential model + leases (D-G).** The two-OS-process split; the synchronous localhost channel (schema-validated twice, parse-or-drop, ≤K=3); per-run device token + run-scoped app-cred lease (TTL/30-min ceiling); ≤2 re-login bound → escape hatch; lease/token mismatch → quarantine; the three post-run-sweep checks. **F8** deepened to full runtime coverage. | WP0 (∥ WP1) | **parse-or-drop**, **relogin-bound**, **post-run-sweep**, **two-service-principals**, **run-scoped-lease**, **D-G-lease-scope**, **origin-provenance-forever**; **F8** runtime | 1–2 (∥ WP1) |
| **WP8** | **CS1–CS7 screening call sites + screen-gate (D-H).** The screen-gate as the executor's only evidence-landing adapter + the proposer's only channel adapter, ArchUnit-enforced; each CS1–CS7 with a named static rule + named runtime assertion proven by a violating sample (T02); CS7 anticipatory. **F9** deepened to full runtime coverage. | WP0, WP7 | **screen-before-write** (runtime), **verdict-token** (runtime), **cs-named-rules**, **discovery-screening-sequence** | 2 |
| **WP9** | **Deep-link / TYPE / env / dataClass admission (D-I, incl. D4's dataClass predicate).** Exact-literal deny-by-default deep-link allowlist + REJECTED_URL/UNKNOWN quarantine + load-time re-check exclusion; navigation-field allowlist + synthetic corpus TYPE policy; **env-attestation**; **`dataClass`** as a first-class startup attestation symmetric with `envClass` (D4) with `PRODUCTION_DERIVED` suspension. **F11** deepened to full coverage. | WP2, WP5, WP7 | **deny-by-default**, **executor-recheck** (runtime), **load-time-recheck**, **D-I-unknown-quarantine**, **field-allowlist**, **vault-login-only**, **corpus-pending**, **reference-not-literal**, **env-attestation**, **d4-suspension**, **attestation-recorded**, **nav-deeplink-admit**, **nav-field-corpus** | 3 |
| **WP10** | **Verdict log + S2-spike input (F12).** Every arrival verdict (incl. NOT-ARRIVED, NO-VERDICT) logged with raw signal values, **D as a raw fraction**; golden pre/post-release fixture pairs; the changed-screen one-visit-re-key falsification fixture. Feeds the S2 measurement spike (S1-before-S2). | WP2, WP5 | **verdict-log-all**, **changed-screen-one-visit**, **D-A-rekey-evidence**; **F12** | 4 |

**Dependency order (topological):**
`WP0 → { WP1 ∥ WP7 } → WP2 → { WP3, then WP4 } → WP5 → { WP6, WP9, WP10 } ; WP8 after { WP0, WP7 }.`
WP1 and WP7 run in parallel off WP0 (schema vs process-topology touch disjoint surfaces). WP3→WP4 is a short serial chain on the arrival core. Once WP5 lands, WP6 / WP9 / WP10 are mutually parallel. WP8 joins after WP7 (it wraps the proposer channel adapter WP7 builds) and WP0 (it deepens the F9 skeleton). WP2 is the hard serial spine — everything arrival-shaped waits on it.

**Plan-WP ↔ task-WP crosswalk.** The tasks doc (`mobile-test-automation-ash-capture.tasks.md`, IDs `A01…A45`) groups the same work into seven task-WPs; this plan's finer-grained arrival split (WP2/WP3/WP4) is folded into one task group. The mapping is 1:1-or-many-to-one and lossless:

| Plan WP | Task WP | Task IDs |
|---|---|---|
| WP0 (task zero) | **WP-A0** | A01–A05b |
| WP1 (graph schema + write path) | **WP-A2** | A10–A18 |
| WP2 + WP3 + WP4 (arrival table · backend signatures · demotion/collision) | **WP-A4** | A23–A30 |
| WP5 (staged CAS + park-and-sweep) | **WP-A2** (schema/writer) + **WP-A4** (arrival-driven commit) | A14–A18, A29 |
| WP6 (typed-actor + baseline) | **WP-A5** | A38 |
| WP7 (two-process topology + credentials) | **WP-A5** | A31–A37 |
| WP8 (CS1–CS7 + screen-gate) | **WP-A3** | A19–A22 |
| WP9 (deep-link/TYPE/env/dataClass admission) | **WP-A6** | A39–A45 |
| WP10 (verdict log + S2 input) | **WP-A4** | A30 |
| (config/contracts, implicit in WP0/WP1) | **WP-A1** | A06–A09 |

The task-WP grouping is the build-execution view (seven parallelizable streams off WP-A0); this plan's WP list is the design-decomposition view (one WP per ADR 0014 decision letter D-A…D-I). They describe the same tasks.

### External critical path

Three external couplings gate ASH-Capture; **none gates WP0, so start WP0 regardless.**

1. **Perfecto pool + vault + gateway credential access (the week-0 access track).** The pinned **Perfecto** pool is the reference backend for the D-B FIRST_SEEN comparison and every real discovery run — it gates **WP3** and any device-executing slice of **WP2/WP5/WP9/WP10**. The **vault** must mint the per-run app-credential lease (D-G); its **C2 fallback** (a standing vault-held test password under executor-enforced lease discipline + rotation) is **accepted as recorded risk** (C2) and does not block the loop, but the lease-vs-fallback posture **must be verified on the week-0 access track before first discovery execution** (0014:58-59). The **gateway credential** lands **only** in `svc-ash-proposer` (F1); its provisioning gates **WP7/WP8** device-executing runs. None gates WP0/WP1 — schema and CI scaffolding proceed on Testcontainers alone.
2. **The S2 measurement spike coupling (S1-before-S2, strictly sequenced).** ASH's re-keying design **is** Lane-3 S1; the S2 spike is worthless until the loop can terminate on changed screens and is sequenced strictly after it, with pass/kill thresholds pre-registered. **WP2 + WP10 together deliver S1.** S2 then measures escape-hatch/ANCHOR_LESS bucket size, cross-backend hash stability, device-minutes, human touches, the **CAS-contention rate** (which keeps-or-kills the WP5 park-and-sweep buffer, D5), and the **device-lab flake base-rate** (D6). S2 is UNBLOCKED the moment WP2/WP10 land; it gates no WP but consumes their output. The C1 strict-path auto-RE-KEY and the rule-5b residual bucket are confirmed-or-flipped by S2's measured bucket size.
3. **The ADR 0006 retention rider — ✅ ACCEPTED 2026-08-01 (no longer a blocker).** D4 split the retention-class enum into a named companion ADR 0006 rider; that rider is now **Accepted**. The enum is `CONSUMED | FORENSIC | PENDING_MINT` (one value per distinct purge behavior; strictly conversion-state, no value outlives certification). It was always **narrowly scoped** — it gated **only** the `retention_class` CHECK cell in **WP1** and the `terminal-commit-only` criterion's retention-class clause, never the ScreenGraph migration (lifted by D3) nor any structural DDL. **WP1 ships two interim columns present-but-unconstrained** (`retention_class` + `terminal_outcome_at`, the `FORENSIC` TTL basis); the enum CHECK + its two CI checks land as the one-cell follow-up **A13b**. **Every D3/D4/D5-derived dependency and the ADR 0006 rider are now DECIDED — no external item remains OPEN.**

---

## 6. Constitution alignment (G1) & risks

| Invariant | How this plan satisfies it |
|---|---|
| **A1 — least machinery** | No graph DB (Postgres snapshots); no third queue (park-and-sweep is intra-process); reuse published spine libs, do not re-build. Every rejected simpler alternative recorded in §3's G1 table. |
| **G1 — abstractions justified** | The seven new abstractions each state what they buy + the simpler thing rejected (§3 G1 table). No abstraction lacks a rejection. |
| **A7 — spec before code** | Satisfied by construction: SPEC-OK spec + Accepted ADR 0014 precede this plan. |
| **S1 — spine untouched** | Spine board T01–T43 unedited; ASH guards land as CI config only (the spine-Flyway-V1-no-graph-DDL check is a scan of the published artifact, not an edit). |
| **F1 — no LLM in spine** | Proposer + Invoke Models impl + gateway-cred config live in the ASH repo only; F8 asserts absence in the executor and the whole spine repo has no model-adjacent type. |
| **ADR 0013 — credential isolation** | Two OS processes; startup-absence assertions both ways (F8); single-run device token + run-scoped app-cred lease, TTL/30-min ceiling. |
| **ADR 0009 flip 3-of-3** | Screen-gate is the structural promotion; CS1–CS7 each get a named static rule + runtime assertion via the T02 method; flip-gate asserted green. |

**Risks:** (1) ADR 0006 rider remaining OPEN past WP1 — mitigated by shipping the column present-but-unconstrained (one-cell follow-up, no rework of DDL). (2) Perfecto/vault/gateway access slipping the week-0 track — mitigated because WP0/WP1 proceed on Testcontainers alone; only device-executing slices wait. (3) S2 measured bucket size flipping C1/rule-5b — accepted, S2 is strictly after S1 and gates no WP. (4) Two-process deployment + IPC cost — accepted (ADR 0014 §consequences).

---

## 7. Gate

**Status: CLOSED — PLAN-OK recorded 2026-08-01.** Approved as drafted. The three plan-gate forks were ruled on the recommendations (see the status header): co-located two-process proposer over the localhost channel; front-load the D-A/write core (WP-A4 + WP-A2 write) to unblock S1→S2; ship `capture_run_edges.retention_class` present-but-unconstrained with a one-cell follow-up. No feature commit lands until WP-A0 is green. **UPDATE 2026-08-01: the one recorded OPEN external item — the ADR 0006 retention-class rider — is now ACCEPTED** (enum `CONSUMED\|FORENSIC\|PENDING_MINT`; interim ships `retention_class` + `terminal_outcome_at`; CHECK is the one-cell follow-up A13b). **No external dependency remains OPEN.** Every D3/D4/D5-derived dependency is DECIDED and unblocking. **No new ADR** — ADR 0014 + its D3/D4/D5 amendments cover the design; the ADR 0006 rider (now Accepted) was the sole external item. **Next: `sdd-implement`, starting with WP-A0 (task-zero) — scaffold + F8/F9/F11 CI-blocking + flip-gate + d3-marker before any feature commit.** The S2 measurement spike unblocks once WP-A4 + the WP-A2 write path land (= Lane-3 S1).