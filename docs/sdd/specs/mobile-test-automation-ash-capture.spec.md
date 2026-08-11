# Spec: Mobile Test Automation — ASH-Capture Authoring Arm

**Status:** **SPEC-OK — 2026-07-31.** Clarify pass complete (five forks resolved →
C1–C5 below); the combined gate closed the same day: SPEC-OK + ADR 0014
Accepted + the three riders ratified (ADR 0001 seam-vocabulary amendment,
ADR 0009 flip amendment at 3-of-3, A11 override). Next: Stage 3 (plan + tasks);
the S2 measurement spike is UNBLOCKED. Original paired gate design: ADR 0014
acceptance (Proposed → Accepted), one combined decision also ratifying the ADR
0001 seam-vocabulary amendment, the ADR 0009 flip amendment (counter 3 of 3), and
the A11 stored-biometric-credential override. Gate history: drafted 2026-07-31 at
SDD Stage 2 synthesis from four adversarially verified facet designs (all
UPHELD_WITH_AMENDMENTS; amendments folded in).

**Target:** ASH-Capture — automated screen-graph capture and discovery, the
authoring arm feeding NavigationManifests and hierarchy dumps to the conversion
pipeline. Weeks-3-8+ phase; supersedes nothing until ADR 0014 is Accepted (WP5
remains the fallback and escape hatch either way).

**Implementation home:** a separate ASH-Capture module/repository — never the
spine repo. F1 CI-fails any LLM stage in the spine repo
(`docs/sdd/plans/mobile-test-automation-spine.tasks.md:185`); the proposer
process, its Invoke Models implementation, and the gateway-credential
configuration land in the ASH repo only. Locked at spec scoping, 2026-07-31.

**Acceptance bar:** *"with pass/kill thresholds recorded before measuring, so the
~90/<10 claims can be retired or falsified"*
(`docs/sdd/plans/mobile-test-automation-spine.tasks.md:193`) — plus: a
legitimately changed screen re-keys in one visit instead of exhausting its budget,
and the signed-off spine board (T01–T43) is untouched.

**Prior artifacts (constraints, not proposals — do not re-decide):**

- `docs/research/o1-pipeline-walkthrough.md` — §11–§13 PROPOSED material; the
  starting point this spec corrects, per its own :467 disclaimer
- `docs/research/o1-pipeline-review.md` — 7-agent review, all 28 findings
  CONFIRMED; the defect list this spec closes
- `docs/sdd/plans/mobile-test-automation-spine.tasks.md` §Replan R1 — T01–T43
  STAY; D1 routed here; D2–D6 routed elsewhere; S1-before-S2 sequencing
- `docs/sdd/specs/mobile-test-automation-spine.spec.md` — signed-off baseline;
  M-rules, CF1–CF11, F1–F7 all import unchanged
- `docs/architecture/adrs/application/mobile-test-automation/0001…0013` — binding;
  ADR 0014 (paired with this spec) borrows their constructions, inherits none of
  their coverage

**Scope decisions locked (2026-07-31, from Replan R1 / REPLAN-OK):**

| ID | Decision |
|---|---|
| S1 | **Spine untouched** — T01–T43 stay unchanged in order; no spine spec/plan edit rides on this spec; guards land as CI configuration only |
| S2 | ScreenGraph tables are **not** in spine Flyway V1; no graph migration ships until the D3 (ADR 0012) amendment is Accepted |
| S3 | This spec's re-keying design is Lane-3 **S1**; the S2 measurement spike is sequenced strictly after it, with pass/kill thresholds pre-registered |
| S4 | D3 (graph lineage-chain scope, ADR 0012 amendment), D4 ("prod-grade data", ADR 0010), and D5 (invocation model, ADR 0007 ruling) are **external interfaces** — required from, never decided by, this spec |
| S5 | K stays 1 for spine replay (T37/CF6); the `CandidateActionSet` cap K = 3 is a distinct ADR 0014 budget value, recorded, unrelated to replay K |

**Clarify decisions locked (2026-07-31 — all five forks resolved by the owner):**

| ID | Fork | Resolution |
|---|---|---|
| C1 | ANCHOR REKEY | **Auto-RE-KEY on the strict path** — decision-table rule 5 applies to ANCHOR_LESS/WEAK_DES nodes (`D ≥ τ_strict ∧ P ∧ ¬K`), session rate guard unchanged; the S2 spike's measured bucket size confirms or flips this |
| C2 | CRED POSTURE | **A11 override CONFIRMED** (stored Touch/Face-ID creds rejected; per-run lease, ≤2 re-logins) **and the fallback accepted as recorded risk** — standing vault-held test password under executor-enforced lease discipline + rotation, verified on the week-0 access track |
| C3 | FLIP SCOPE | **ASH-repo-scoped screen-gate promotion + ADR 0009 amendment now**; the amendment records the spine-side promotion question as open and routes it to the spine's own change process — the signed-off spine is not reopened |
| C4 | BASELINE | **APPROVE_GRAPH_BASELINE blocks at the certification boundary only** — capture, discovery, and drift repair run freely; certification-bound conversions consume ASH-derived manifests only from a baseline-approved graph |
| C5 | RECALL SCOPE | **Flag, don't invalidate** — the committed engineer-reviewed Java stays the sole audit pin; quarantine stale-flags dependent manifests, forces re-capture on next touch, and writes a lineage cross-reference enumerating every affected conversion; no retroactive invalidation of spine verdicts |

**Open questions:** none — all five clarify forks resolved above.

## Problem

The spine converts and replays tests deterministically, but every screen it
learns about arrives through a per-screen human touch. ASH-Capture automates
that acquisition — an LLM proposes navigation actions, a deterministic executor
drives the device, and a versioned ScreenGraph accumulates replayable paths. The
walkthrough's draft of this subsystem, reviewed by seven agents, failed in
load-bearing ways: the success predicate compared landed signatures to *stored*
signatures, so a changed screen *"can never match and deterministically exhausts
its budget into the escape hatch (~20% of screens per release)"*
(`o1-pipeline-walkthrough.md:616-621`); one worker held both the gateway
credential and the authenticated device session (review Critical #4); deep links
executed with *"widest LLM action space, narrowest filter"*
(`o1-pipeline-review.md:64`); mid-loop edge commits laundered LLM provenance into
permanently trusted replay paths with no removal procedure (`:72`); concurrent
writers could fork the version chain *"exactly in release week"* (`:76`); and the
graph's human review control was silently dropped (`:90`). This spec, paired with
ADR 0014, is the corrected design: failure paths first, every trust decision
deterministic, every correction a superseding append.

## Target artifact

The ASH-Capture subsystem, delivered as:

| Item | Content |
|---|---|
| ADR 0014 | The paired decision record: arrival table + re-keying, backend scoping, honesty bounds, PostgreSQL snapshot storage, staged write path + CAS serialization, auto-commit control change, proposer/executor topology + credential model, CS1–CS7 call-site map + **flip 3 of 3**, deep-link/TYPE/environment admission (with the ADR 0001 and ADR 0009 amendment riders) |
| Capture Executor | Deterministic process `svc-ash-executor`: §11.4 loop, validator, device session, app-credential lease, sole writer; startup credential-absence assertion (**F8** candidate) |
| Action Proposer | Stateless process `svc-ash-proposer`: Invoke Models seam wrapper, gateway credential, parse-or-drop into `CandidateActionSet` (≤ **K = 3**); no grants, no vault, no persistence |
| Graph schema + migrations | `screen_graph_versions/nodes/edges` + per-backend `screen_node_signatures`/`screen_edge_status` (append-only observation logs outside the content hash) + `capture_run_edges` staging; ships only after the D3 amendment (S2) |
| Committed configs | Exact-route deep-link allowlist (NAV/MUTATING), navigation-field allowlist, synthetic input corpus, thresholds config (τ_d = 0.6, τ_strict = 0.8, R = 3, N = 1, K = 3, ≤ 2 re-logins) — all versioned, pinned on lineage, changeable only by recorded decision (**CF6**) |
| Screen-gate component | The flip's structural promotion: the only evidence-landing and channel adapters, ArchUnit-enforced (**F9** candidate) |
| Review integrations | M21/CF4-shaped quarantine records; `APPROVE_GRAPH_BASELINE` review view; typed-actor columns (M37 pattern) |
| Verdict log | Every arrival verdict with raw signal values — the S2 spike's input (**F12** candidate) |

## Acceptance criteria (EARS)

### Failure paths first

- **IF** a landed screen's titleAnchor matches the target but its skeletonHash
  differs from the stored same-backend signature, **THEN** the engine MUST
  evaluate DES overlap and MUST NOT return NOT-ARRIVED on skeletonHash inequality
  alone — hash inequality is never, alone, evidence of non-arrival
  (**des-before-verdict**, ADR 0014 D-A; closes review Critical #5).
- **IF** titleAnchor matches but DES overlap < τ_d, **THEN** the verdict MUST be
  NOT-ARRIVED and no re-key MUST commit — generic-title templated screens cannot
  trigger a false re-key (**title-collision-guard**, D-A rule 6).
- **IF** two settle dumps ≥ 1s apart yield different skeletonHashes, **THEN** the
  visit MUST return NO-VERDICT, consume exactly one no-progress strike, and
  commit no re-key — transient and loading states never re-key (D-A rule 2).
- **IF** a capture session's committed RE-KEY count would exceed 1 per target
  request, or reach ≥ 3 AND > 30% of visited nodes, **THEN** the session MUST
  abort with zero graph commits and route to human review — the per-target
  allowance takes precedence below the floor, so a single-target session
  committing its one permitted re-key never trips the guard
  (**rate-guard-floor**, D-A).
- **WHERE** the target node is ANCHOR_LESS or WEAK_DES, **IF** DES overlap <
  τ_strict OR graph-position evidence is absent, **THEN** the verdict MUST be
  NOT-ARRIVED, never RE-KEY — skeleton-only identity never self-re-keys, and
  rule 5b excludes these nodes (**strict-anchorless**, D-A rule 5).
- **IF** the executing backend has no stored signature row for the target node,
  **THEN** arrival MUST be decided on titleAnchor + the reference backend's
  (Perfecto) DES only — a deliberate, bounded cross-backend accessibilityId
  comparison — and success MUST write a FIRST_SEEN_ON_BACKEND row, never a
  RE-KEY; **IF** no backend has a row, **THEN** the run MUST route to the escape
  hatch (**reference-des**, D-B).
- **WHEN** graph search plans a replay on backend B, **THEN** edges lacking
  VERIFIED status for B MUST be treated as UNVERIFIED regardless of any other
  backend's status, and an arrival failure on B MUST mark the edge BROKEN for B
  only — phantom cross-backend drift is unrepresentable (**per-backend-status**,
  D-B; closes review Serious #15).
- **WHEN** graph commit finds two nodes in one version sharing (backend,
  skeletonHash, titleAnchor), **THEN** both MUST be flagged SIGNATURE_COLLIDED,
  excluded from auto-RE-KEY, and requests targeting them MUST route to the
  escape hatch — uniqueness is enforced away, not assumed (D-C).
- **IF** a node accrues ≥ R = 3 RE-KEY events within one appVersion, **THEN** it
  MUST be demoted to DYNAMIC_SKELETON with skeletonHash recorded but excluded
  from arrival; **IF** a DYNAMIC_SKELETON node's DES overlap < τ_d on 2
  consecutive attempts, **THEN** it MUST flag SIGNATURE_DEFEATING and route to
  the escape hatch, whose confirmation commits with MANUAL_ARRIVAL provenance
  (**demotion-ladder**, D-C).
- **IF** a deep-link probe targets an ANCHOR_LESS, DYNAMIC_SKELETON, or
  SIGNATURE_DEFEATING node, **THEN** confirmation MUST use the full arrival
  table at strict thresholds, and for SIGNATURE_DEFEATING targets the probe MUST
  NOT auto-confirm any edge (D-C).
- **IF** any code path attempts to change a stored signature, status, node flag,
  or edge by in-place UPDATE or DELETE, **THEN** the operation MUST fail under
  ADR 0014's INSERT/SELECT-only grant on graph tables — a new grant decision
  mirroring ADR 0012's construction, with its own CI assertion; corrections
  exist only as superseding snapshot rows carrying complete evidence records
  (**supersede-only**, D-D/D-E).
- **WHEN** a capture run terminates ABORT, CRASH, TIMEOUT, NO_PROGRESS,
  BUDGET_EXHAUSTED, or ESCAPE-before-completion, **THEN** zero nodes, edges, or
  RE-KEY verdicts from that run MUST appear in any committed graph version; its
  `capture_run_edges` staging rows MUST carry the terminal outcome and a
  retention class (**terminal-commit-only**, D-E). *(The retention-class value,
  originally a D4 interface, is RESOLVED by the ADR 0006 rider, Accepted
  2026-08-01: `CONSUMED | FORENSIC | PENDING_MINT`; a terminal-failure run's rows
  are `FORENSIC` — bounded 30-day TTL from a `terminal_outcome_at` column. The
  criterion's WHAT is unchanged — rows still MUST carry a retention class — so this
  resolves a forward reference without reopening sign-off.)*
- **IF** any commit contains an edge whose first committed status is not
  CANDIDATE — regardless of provenance, including MANUAL_CAPTURE — **THEN** the
  commit validator MUST reject the snapshot; and the per-release
  chain-verification job MUST recompute first-appearance statuses and quarantine
  any violator — a detective control compensating the validator-enforced floor
  (**candidate-at-birth**, D-E).
- **WHEN** two version INSERTs reference the same non-null `prev_version_sha`,
  or two roots share an `app_version`, **THEN** the second MUST fail with a
  unique-constraint violation at the database — including for a writer that
  bypasses the advisory lock (**fork-unrepresentable**, D-E; closes review
  Serious #14).
- **IF** a writer exhausts its lock timeout or 3 CAS rebase attempts, **THEN**
  its staged edges MUST park as COMMIT_CONTENDED with an alert, the sweeper MUST
  re-drive the commit, and the capture's hierarchy deliverable MUST still reach
  its requester — re-verification results are never silently dropped; the
  park-and-sweep buffer routes to ADR 0007's compliance review alongside D5,
  with fail-loud-and-recapture as the fallback (**park-not-drop**, D-E).
- **IF** a replay traverses a CANDIDATE or VERIFIED edge and the landed
  signature does not match the recorded to-node, **THEN** the edge MUST mark
  BROKEN for that backend with confirmation evidence reset; **IF** the landed
  signature matches a contradictory sibling's to-node, **THEN** the traversed
  sibling MUST mark BROKEN and a confirmation observation MUST record for the
  matching sibling (counting toward promotion only from a distinct run)
  (**broken-on-mismatch**, D-E).
- **WHEN** an edge is quarantined, **THEN** one transaction MUST mint a
  superseding version with the edge QUARANTINED and excluded from the
  path-search index, write a quarantine lineage row with enumerated reason
  (SCREENING_FLAG, HUMAN_REPORT, CHAIN_MISMATCH, VALIDATOR_RETRO) and actor, and
  stale-flag every NavigationManifest whose graphPath contains the edge — prior
  rows byte-identical (**quarantine-superseding**, D-E; closes review Serious
  #12's removal gap).
- **WHEN** an edge is quarantined, **THEN** the same transaction MUST write a
  lineage cross-reference enumerating every conversion whose manifest is
  stale-flagged; affected conversions and ReplayReports are flagged for audit,
  **never retroactively invalidated** — the committed engineer-reviewed Java
  remains the sole audit pin — and a stale-flagged manifest MUST force
  re-capture on next touch (**recall-scope**, C5; clarify-resolved 2026-07-31).
- **IF** a quarantine release lacks an INDIVIDUAL-kind principal, **THEN** the
  write MUST be rejected at the database — service principals and `system` are
  schema-rejected (M37/T03 CHECK construction) (D-F).
- **IF** a graph version row lacks `committed_by_principal` or `actor_kind`, or
  contains MANUAL_CAPTURE-provenance edges with a null `steering_principal`,
  **THEN** the row MUST be schema-rejected — the steering human is recorded even
  though the service writes (**typed-actor**, D-F; closes review finding #28).
- **IF** a SERVICE-actor commit's delta contains anything outside {new CANDIDATE
  nodes/edges with origin provenance; evidenced CANDIDATE→VERIFIED; →BROKEN;
  the release UNVERIFIED flip; manifest stale-flags}, **THEN** the commit MUST
  be rejected and a review-queue entry created (**delta-class-bound**, D-F;
  the named auto-commit control change's boundary).
- **IF** the graph lineage/chain row write fails, **THEN** the snapshot INSERT
  MUST roll back — no committed version exists without its chain link, in one
  local transaction (ADR 0007's provenance shape) (**chain-same-txn**, D-E).
- **WHILE** the D3 ADR 0012 amendment is not Accepted, no migration creating
  `screen_graph_versions` MUST ship, and spine Flyway V1 MUST contain no graph
  DDL — asserted in CI configuration, not a spine edit (**d3-gate**, S2).
- **IF** a VERIFIED root→target path exists, **THEN** path search MUST return no
  path containing a CANDIDATE edge, regardless of cost; **WHERE** a CANDIDATE
  edge is used, each CANDIDATE hop MUST be landed-signature-checked at replay;
  sibling selection MUST follow the most-recent `first_observed_at` tie-break
  (**verified-preferred**, D-E).
- **WHEN** a new appVersion's first commit occurs, **THEN** it MUST be a root
  (`prev_version_sha` NULL), exactly one per appVersion, derived by copying the
  prior release head with the VERIFIED→UNVERIFIED flip applied (CANDIDATE stays
  CANDIDATE), recording `derived_from_version_sha` in lineage
  (**release-root**, D-E).
- **IF** the Capture Executor's resolved configuration or environment contains a
  gateway credential, provider endpoint secret, or standing device-cloud
  credential at startup, **THEN** it MUST refuse to start and the covering test
  MUST fail the build (**startup-absence**, D-G; ADR 0013 construction, **F8**).
- **IF** the Action Proposer can resolve a device-cloud credential or app-
  credential vault reference, holds any database grant or writable persistent
  volume, or has any DeviceSession, vault-client, broker, queue-consumer, or
  outbox-relay type reachable from its packages, **THEN** the symmetric startup
  assertion, grant-assertion job, or ArchUnit rule MUST fail CI
  (**proposer-blind**, D-G, **F8**).
- **WHEN** the proposer returns output not validating against the committed
  `CandidateActionSet` schema (≤ K = 3 entries), **THEN** the executor MUST
  discard the entire response without executing any part and count one
  no-progress strike (**parse-or-drop**, D-G).
- **IF** any action reaches `DeviceSession.act()` or `launchDeepLink()` without
  a deterministic-validator verdict token, **THEN** the runtime assertion MUST
  reject it and quarantine the run; the static half (call sites reachable only
  from verdict-bearing types) MUST be CI-blocking (**verdict-token**, D-H CS6,
  **F9**).
- **WHEN** an ObservationPacket reaches the proposer channel without the
  screening library's screened marker, or device evidence (screenshot,
  pageSource, pruned tree, Object Spy, escape-hatch action stream) is written
  without a prior screening call, **THEN** the egress or write MUST be refused
  at runtime; the static half (screen-gate component dependency) MUST be
  CI-blocking (**screen-before-write**, D-H CS1/CS2/CS5, **F9**).
- **WHEN** a capture run attempts a third re-login (beyond the ≤ 2 bound),
  **THEN** the executor MUST abort to the escape hatch and write an attributable
  quarantine-style record — a silent re-login loop is impossible; unbounded
  re-login is standing access wearing a 10-minute costume (**relogin-bound**,
  D-G).
- **IF** a run presents an app-credential lease or device token minted for a
  different run ID or past its TTL, **THEN** the run MUST quarantine (ADR 0013
  session-scope mirror) (D-G).
- **WHEN** a run ends, **THEN** three post-run checks MUST pass: app-state reset
  verified; per-run biometric enrollment torn down where injection was used;
  artifacts, traces, and prompt payloads scanned by the screening library's
  secret detector with zero detections — a detection is an incident, not a
  warning (**post-run-sweep**, D-G).
- **WHILE** the ADR 0009 amendment recording the flip counter at 3 of 3 and the
  ASH-scoped screen-gate promotion is unmerged, the discovery loop MUST NOT
  execute against any device — the walkthrough's own gate: the loop cannot ship
  without the call-site map (**flip-gate**, D-H).
- **IF** a literal credential or literal input value (rather than a `vault:` or
  `corpus:` reference) appears in a NavigationManifest, `CandidateActionSet`,
  graph edge, or prompt payload, **THEN** schema validation MUST reject the
  document (**reference-not-literal**, D-G/D-I; FP10/T23 shape; closes review
  finding #26's schema-home gap).
- **IF** a proposed deep-link route does not exactly match a committed allowlist
  entry, or carries a query string or path segment beyond the entry's literal
  parameterless form, **THEN** the validator MUST reject it before any
  `launchDeepLink()` call and record a REJECTED_URL lineage row — v1 entries are
  exact literal URLs; no pattern syntax exists in the matching engine
  (**deny-by-default**, D-I; closes review Serious #8).
- **IF** `launchDeepLink()` is invoked with a URL failing the executor's
  independent allowlist re-check, **THEN** the executor MUST refuse and
  quarantine the run — the runtime half blocks even when the validator was
  bypassed (**executor-recheck**, D-I, **F11**).
- **WHEN** the graph loader loads a DEEP_LINK edge violating the CURRENT
  allowlist version, **THEN** it MUST exclude the edge from the in-memory graph
  (a load-time quarantine event in lineage, never an UPDATE), and **WHERE** no
  alternative verified path exists, capture MUST fall through to discovery or
  the escape hatch — never execute the excluded edge (**load-time-recheck**,
  D-I).
- **WHEN** a proposed route matches no entry (UNKNOWN), **THEN** it MUST
  quarantine into the M21/CF4-shaped review queue, never probe; admission
  thereafter requires a recorded, attributable allowlist commit (D-I).
- **IF** a proposed TYPE targets a field matching no navigation-field-allowlist
  entry, **THEN** the validator MUST reject it with a lineage row; **WHILE**
  rejected TYPEs exhaust the 3-strike rule, the run MUST route to the escape
  hatch with the field rule intact — never relaxed (**field-allowlist**, D-I).
- **IF** any TYPE outside `DeviceSession.login()` resolves to a `vault:`
  reference, **THEN** the executor MUST refuse and quarantine
  (**vault-login-only**, D-I).
- **IF** an escape-hatch-recorded TYPE step's value matches no corpus entry,
  **THEN** the step MUST commit only as `corpus:PENDING` with a quarantine
  record, and replay of that manifest MUST be refused until the reference
  resolves at a pinned corpusVersion — a raw literal never commits
  (**corpus-pending**, D-I).
- **IF** the capture worker's resolved configuration does not declare
  `envClass=RESETTABLE_TEST`, **THEN** discovery mode and probing MUST be
  disabled at startup (replay of committed, validator-admitted deterministic
  edges remains permitted — no LLM proposes during replay), with a
  build-failing regression test; **IF** the per-run reset-liveness check fails,
  **THEN** no probe or discovery action MUST execute that run
  (**env-attestation**, D-I).
- **WHERE** the environment descriptor declares `dataClass=PRODUCTION_DERIVED`
  (field reserved for D4's outcome), the worker MUST refuse discovery and
  probing until a superseding recorded decision under ADR 0010/D4 — a named
  suspension condition, not a silent dependency (**d4-suspension**, D-I).

### Happy path

- **WHEN** a landed screen's same-backend skeletonHash equals the stored hash
  and its titleAnchor matches (ANCHOR_LESS variant: `K ∧ P` — skeleton equality
  plus path evidence, since K ⇒ D = 1 makes a DES conjunct vacuous), **THEN**
  the verdict MUST be MATCH and the traversed edge MUST re-VERIFY for that
  backend as an appended observation row, with no model call and no re-key
  (D-A rule 1).
- **WHEN** the verdict is RE-KEY, RE-KEY-ANCHOR, or RE-KEY-FULL, **THEN**
  discovery MUST terminate DONE and the committed snapshot MUST carry the
  superseding row plus an evidence record: superseded/new signature, rule
  fired, signal values {A, D, K, P, S}, thresholds config version, backend,
  capture_session_id, typed actor, appVersion, timestamp (D-A).
- **Ubiquitous:** the arrival verdict MUST be a pure deterministic function of
  (both settle dumps, stored node/signature rows for the executing backend,
  recorded path evidence, committed thresholds-config version) — identical
  inputs, identical verdicts; τ_d, τ_strict, R, N, K, and the session caps are
  committed versioned constants changeable only by recorded decision (CF6). For
  |DES| ≤ 4, τ_strict = 0.8 quantizes to full DES presence — the S2 spike MUST
  log D as raw fractions (**F12** candidate).
- **WHEN** a screen legitimately changes in a release while retaining any
  continuity signal the table recognizes (rules 3, 4, 5b), **THEN** one visit
  MUST re-key it and every subsequent request MUST resolve via MATCH replay — a
  changed screen MUST NOT exhaust the 15-action budget into the escape hatch;
  ANCHOR_LESS both-changed nodes are the named residual, routed to the hatch
  and sized by the S2 spike (the direct falsification test for Critical #5; a
  pre/post-release fixture pair proves it).
- **Ubiquitous:** every arrival verdict, including NOT-ARRIVED and NO-VERDICT,
  MUST be logged with its raw signal values — the S2 spike's false-re-key and
  missed-re-key measurement input against pre-registered pass/kill thresholds.
- **Ubiquitous:** every ASH-Capture run involves exactly two service
  principals, `svc-ash-executor` and `svc-ash-proposer`; only the executor's
  principal ever appears as a writer, and every committed artifact attributes
  its writing principal (D-G).
- **WHEN** a capture run starts, **THEN** the executor MUST obtain a single-run
  device session token and a run-scoped app-credential lease resolved from an
  injected vault reference, both carrying the run ID and expiring at run end or
  the 30-minute ceiling (D-G).
- **WHEN** a discovery iteration completes, **THEN** the sequence MUST be: dump
  screened at landing (CS1) → ObservationPacket screened at egress (CS2) →
  schema-valid CandidateActionSet returned → validator filters applied → at
  most one survivor executed → re-dump screened at landing — each screening
  call recorded (D-G/D-H).
- **WHERE** the ASH-Capture repo exists, each call site CS1–CS7 MUST have a
  named static rule and a named runtime assertion in CI, each proven by a
  deliberately-violating sample that fails the build and is then removed (the
  T02 method; CS7 is anticipatory — it binds any future feedback field added to
  ObservationPacket) (**F9** candidate).
- **WHEN** a discovery run terminates with an arrival-table DONE verdict,
  **THEN** exactly one new graph version MUST commit in one local transaction —
  observed nodes/edges as CANDIDATE with full origin provenance
  (`proposer_kind` incl. model+provider version, `first_observed_run_id`,
  `first_observed_at`) plus the version's lineage/chain row (D-E).
- **WHEN** a deterministic replay from a distinct `capture_run_id` traverses a
  CANDIDATE edge and the landed signature matches, **THEN** the next commit
  MUST promote it to VERIFIED recording the confirming run and principal —
  same-run traversal never promotes; DEEP_LINK edges additionally require a
  recorded pass of the current allowlist version before promotion eligibility
  (**distinct-run-promotion**, D-E; N = 1 is a CF6-governed threshold).
- **WHEN** two runs commit concurrently against one head, **THEN** one MUST win
  directly and the other MUST rebase by `edge_id` set-merge onto the new head;
  the resulting chain MUST be linear per appVersion with both runs' edges
  present (D-E).
- **WHEN** a release's graph baseline review completes, **THEN** an
  `APPROVE_GRAPH_BASELINE` lineage row MUST exist — INDIVIDUAL principal,
  reviewed sha, prior baseline sha, diff digest — over a view listing every
  quarantine, override, and ANCHOR_LESS addition since the prior baseline (the
  CF9 shape: the machine advises, a named human confers trust) (D-F).
- **Ubiquitous:** every edge row in every committed version — including
  superseded and quarantined — MUST carry immutable origin provenance
  (canonical enum: `DISCOVERY | GRAPH_SEARCH | DEEP_LINK_PROBE | DRIFT_REPAIR |
  MANUAL_CAPTURE`), and per-observation lineage rows MUST enumerate every
  traversal — the LLM origin stays visible to audit forever, even as replay
  stays deterministic (D-E).
- **WHEN** the LLM proposes a parameterless route matching a NAV-class entry,
  **THEN** the validator MUST admit it, the probe MUST launch, and only a full
  arrival-table confirmation MUST commit a DEEP_LINK edge carrying
  `url_class=NAV`, `allowlist_version`, and `provenance=DEEP_LINK_PROBE`; graph
  search MUST grant cost-1 preference only to `url_class=NAV` edges (D-I).
- **WHEN** discovery types into an allowlisted navigation field, **THEN** the
  LLM MUST propose (field, corpusKey), the validator MUST resolve the value at
  the pinned corpusVersion, the committed artifact MUST store only the
  reference, and replay MUST resolve the byte-identical value from the same
  pinned version (D-I).
- **WHEN** the startup attestation and per-run reset liveness both pass,
  **THEN** discovery mode MUST enable and the attestation (envClass, allowlist
  version, corpus version, thresholds version) MUST be recorded in the run's
  lineage row (D-I).

## Non-goals (routed elsewhere or explicitly excluded)

- Spine changes of any kind — T01–T43, WP5, the three spine screening call
  sites, F1–F7, and K = 1 replay all stand (Replan R1)
- A0 Normalizer ratification — D2, its own decision
- Graph lineage-chain scope, anchor cadence — D3, the ADR 0012 amendment (this
  spec offers per-appVersion scope; it does not decide it)
- "Prod-grade data" definition — D4, ADR 0010 amendment (**DECIDED 2026-08-01**:
  SYNTHETIC vs PRODUCTION_DERIVED provenance predicate). Retention-class values for
  `capture_run_edges` — split to the **ADR 0006 rider (DECIDED 2026-08-01**:
  `CONSUMED | FORENSIC | PENDING_MINT`)
- Invocation model and the third-queue/park-buffer ruling — D5, ADR 0007
- Parameterized deep-link templates — the recorded single sanctioned growth
  path, decided only by the open-fork decision
- Learned screen fingerprints, fuzzy similarity — reserved future work if the
  S2 spike shows the DES discriminator failing
- A graph database — §13.5's flip conditions are on record; none apply
- Resolve Elements integration and object-repository write-back — later phases

## Constraints from the signed-off baseline

- The spine spec (2026-07-27) and plan (PLAN-OK 2026-07-28) are normative;
  every contradiction the review confirmed lives in the walkthrough, not the
  board
- F1: no LLM call in the spine repo — ASH-Capture is structurally elsewhere
- CF1–CF11 import unchanged; CF6 governs every threshold named here; CF9
  shapes the baseline review; M-rules apply wherever their construction is
  borrowed (M34, M35, M37, M40, M21/CF4, M36)
- ADR 0007: no third queue without a superseding ADR; provenance writes
  synchronous, same local transaction
- ADR 0012: supersede-not-update semantics adopted; its grants and chain scope
  are NOT inherited — graph grants are ADR 0014's own decision, chain scope is
  D3's

## Carried assumptions (recorded, not verified)

- The test IdP/vault can mint per-run app-credential leases — fallback: a
  standing vault-held test password under executor-enforced lease discipline
  with rotation; verify on the week-0 access track before first discovery
  execution (clarify C2, resolved 2026-07-31: fallback **accepted as recorded
  risk**; does not block the loop)
- The capture environment is resettable with a live reset capability
  (walkthrough:708 user-stated constraint, converted here to a testable
  precondition)
- Capture data remains production-realistic synthetic pending D4; the
  PRODUCTION_DERIVED suspension gate is the fallback
- ~20%-of-screens-per-release drift and the <10% escape-hatch target are
  unmeasured until the S2 spike; pass/kill thresholds pre-registered
- ADR 0013's short-lived device-token assumption continues to ride M8/M1

## Sign-off gate

**CLOSED — SPEC-OK 2026-07-31.** The clarify pass resolved all five forks
(C1–C5, locked above); the combined gate then closed in one owner decision
covering the spec, ADR 0014 (Proposed → Accepted), the ADR 0001
seam-vocabulary amendment, the ADR 0009 flip amendment (counter 3 of 3,
ASH-scoped promotion — both amendments now recorded in their home ADRs), and
the A11 stored-biometric-credential override. **Advance → Stage 3 (plan +
tasks)**; the plan gate is the next human gate.
The S2 measurement spike (Lane 3) remains blocked until this spec's re-keying
design lands (S1-before-S2, tasks.md:193). Any later risk-storming mitigation
that changes scope re-opens this gate via sdd-replan.