# Spec: Mobile Test Automation — o7 Interpreter (Committed-IR Replay, fork of the weeks 0–3 spine)

**Status:** DRAFT — Stage-2, **clarify pass run 2026-08-05 (C1–C5 locked, below); awaiting owner sign-off gate.** Forks the signed-off spine spec (`docs/sdd/specs/mobile-test-automation-spine.spec.md`, **post-P1-mitigation baseline** + the **A0-fold amendment** 2026-08-01 + the **ADR-0015 owner override** 2026-08-02). Depends on **ADR 0016 (Proposed)** — the recorded overturn that makes committed-IR replay the executable path. Nothing here is decided until ADR 0016 is Accepted and this gate closes.
**Target:** mobile-test-automation — the **o7 interpreter fork** of the replay stage. o1 (LLM → Java/TestNG codegen) and o7 (committed-IR interpreter) are **both live**; this spec governs o7 only.
**Implementation home:** the **same separate Spring Boot repository** the spine scaffolds. o7 is a module inside the existing `validation-certification`/device-gate topology (H-SB), not a new repo — the interpreter is a Spring Boot module hosted by the device-gate worker (ADR 0016), Appium java-client 10.x (H-SB, C-MIG).
**Acceptance bar:** the spine's week-3 gate, **re-based for o7** — this spec **re-bases clause (a)** of the spine's week-3 gate (`docs/sdd/specs/mobile-test-automation-spine.spec.md:6`, `spec.md:329`–`spec.md:334`), replacing the spine's *"one hand-written Appium test flows end to end"* with *"the committed reference `TestCaseIR` is walked end to end by the interpreter on a real Perfecto device and yields a `ReplayReport` valid against the re-based schema"*, **while clause (b) carries unchanged**. The M19 real-input clause (clause b of the spine WHERE criterion) carries **unchanged**: ingestion must still have produced `REAL_INGESTED` IR from real source material.

**Prior artifacts (constraints, not proposals — do not re-decide):**

- `docs/sdd/specs/mobile-test-automation-spine.spec.md` — the **signed-off spine spec** this forks; everything in it holds EXCEPT the replay-pipeline-v1 stage (`spec.md:65`), which this spec replaces. o7 amends four spine surfaces (F6 pinning set, M37 attribution locus, the replay-pipeline-v1 row, and tasks T30/T31–T32/T37/T40/T41) — all **via ADR 0016**, never silently.
- `docs/architecture/adrs/application/mobile-test-automation/0016-*.md` — **ADR 0016 (Proposed)**: overturn the recorded "production stays code-based" boundary from the POC brainstorm **for committed-IR replay only** (NOT for raw-LLM-output interpretation). Supersedes no ADR; **amends the spine spec** (F6, M37, the replay-pipeline-v1 row, T30/T40/T41) — mirroring how ADR 0015's A0-fold landed as a spec amendment.
- ADRs 0001, 0009, 0012, 0013 — inherited **unchanged in force**, several **strengthened** by o7 (see the fork-lineage note and the delta table below). ADR 0013's already-recorded rejection of "human review of every generated script before execution" as a security control is the **precedent** that makes the R4 pre-commit-review removal defensible.

## Fork lineage

o7 is the spine spec's **interpreter-replacement delta**. The rule of this fork: **everything in the signed-off spine spec holds, except the replay-pipeline-v1 stage, which this spec replaces.**

**Inherited UNCHANGED from the spine (not re-specified here; the spine spec is authoritative):**

- Ingestion CLI — Excel (POI) + Octane REST behind one adapter contract (C1), per-adapter canonicalization + source-snapshot digest (M15), the A0-fold phrase-canon/noise-strip table (ADR 0015).
- Screening library at the **three** spine call sites (ADR 0009 as amended, M35). o7 adds **no new trust boundary** — the interpreter consumes already-committed, already-screened IR.
- Hierarchy tool — `getPageSource` XML, Object Spy output, pruned tree, capture-side screening.
- Provenance / lineage — append-only, lifecycle-partitioned, per-conversion hash-chain (ADR 0012), same-transaction writes (ADR 0007), retention-class field (M39). **Unchanged by o7.**
- Replay queue seam — CI enqueues, device-gate worker consumes, transactional outbox, idempotent consumer (ADR 0007, C2).
- Classification taxonomy — `LOCATOR_NOT_FOUND`, `STALE_ELEMENT`, `TIMEOUT_SYNC`, `ASSERTION_MISMATCH`, `APP_CRASH`, `DATA_PRECONDITION`, `ENV_INFRA` — **still deterministic, rule-based, unchanged**; the interpreter maps the Appium exception types and Perfecto failure reasons it encounters while walking the IR into the unchanged taxonomy, using the **same deterministic mapping rules the TestNG runner used** (same rules, same seven classes; the exceptions now surface from the interpreter's java-client calls rather than from generated TestNG code).
- Fitness functions F1–F4 (module boundaries, no-model-call, source-type containment, screening egress); task zero (three-module scaffold + F1–F4 CI-blocking + ADR 0012 grant assertion + warn-only secrets scan).
- Carry-forward rules CF1–CF11 — inherited (see the carry-forward note; only CF9's reading is clarified).

**REPLACED by o7 (the whole of this spec's real work) — the spine's replay-pipeline-v1 stage (`spec.md:65`):**

| Spine (o1) — replaced | o7 — replacement |
|-----------------------|------------------|
| Static gate: format, `mvn compile`, Checkstyle, Error Prone, locator-manifest rule | **IR gate**: schemaValid, opcodeClosed, boundedWaits, locatorManifest, noLiteralCreds, ambiguityClear, dryRun — deterministic, pre-device, **zero device cost, and zero compilation** (there is no generated Java to compile) |
| Device gate: TestNG executes generated Java on a pinned Perfecto pool with pinned Appium | **Interpreter** (Spring Boot module in the device-gate worker) walks the committed `TestCaseIR` step-by-step over Appium java-client 10.x / Perfecto; LLM-free, non-adaptive, version-pinned; no per-test Java exists to execute |
| `ReplayReport` pins `codeCommit` (SHA of generated Java) | `ReplayReport` pins **`irDigest`** (SHA of the committed canonical IR) + **`interpreterVersion`** (the interpreter's Git SHA); adds the `cloudAdaptivity` attestation pair (`selfHealing`/`perfectoAI`) + captured-Perfecto-versions evidence (F6 re-based, ADR 0016) |
| Pre-commit **engineer review** of the generated script | **Removed** (R4): IR + locator manifest auto-committed by `svc:conversion-pipeline`; the spec-section-7 human evaluator becomes the **sole, post-run** attribution anchor. R2 = novelty-sampled review on the existing CF4/M21 flag |

The classification stage and everything downstream of the `ReplayReport` are the spine's, unchanged.

## Scope decisions locked

| ID | Decision |
|----|----------|
| S1 | o7 covers **only** the replay-stage replacement + its schema/attribution deltas (the IR gate, the interpreter, the 3 new IR runtime fields, the re-based `ReplayReport` pins, the R4+R2 review model, the execution-plan renderer). Everything else is the spine spec **unchanged**; where this spec is silent, the spine spec governs. |
| S2 | o7 is a **fork, not a migration** — **both pipelines stay live**. o1 (LLM→Java/TestNG codegen) is not removed by this spec; o7 is the committed-IR interpreter path alongside it. |
| S3 | **Three new IR runtime fields** on `TestCaseIR` (F-B/E2): `timeoutMs` (per-step bounded wait), `syncAfter` (`WAIT_FOR_IDLE` \| `NONE`), `healPolicy` (value **fixed to `NONE`** — no self-heal, ever). Plus `irDigest` (SHA of the canonical IR) as the audit pin. |
| S4 | The **IR gate replaces the static gate**. It is deterministic, pre-device, zero device cost, and requires **no compilation** — o7 has no generated code to compile, so the `mvn compile`/Checkstyle/Error Prone legs of the o1 static gate have **no o7 analogue** and are dropped, not ported. |
| S5 | **R4 + R2 review model.** R4: the pre-commit engineer review is **removed**; the IR + locator manifest are auto-committed by a service principal (`svc:conversion-pipeline`); the mandatory spec-section-7 human evaluator becomes the **sole attribution anchor, POST-RUN** (certifies after the interpreter runs). R2: novelty-sampled review reusing the spine's existing **CF4/M21 sampling flag** (novel source shape → mandatory review; known shape → sampled). R1: the deterministic IR gate + a no-device dry-run is the correctness substrate that makes pre-commit human review removable. **HARD BOUNDARY — R5 (fully autonomous, no human on the certification verdict) is BARRED** on the certified path (CF9 + M37 require an individual principal on the verdict). |
| S6 | **A-STD evidence now; D7 later.** The standard evidence bundle is built now — the `ReplayReport` re-based to pin `irDigest` + `interpreterVersion`. A **signed in-toto attestation is a named follow-on (D7)**, not built now. |
| S7 | **F-B — no per-test Java in the pipeline.** No per-test generated Java/TestNG artifacts exist. The interpreter itself **is** Spring Boot Java (pipeline infra is already Spring Boot per the spine + ADR 0005); vendored Appium java-client internals do **not** count against F-B. What is removed is **per-test generated Java/TestNG**. |
| S8 | **C-MIG — official Appium java-client with a raw-W3C fallback behind a seam.** The interpreter uses the official java-client 10.x; a raw-W3C WebDriver path sits behind an interface seam for the cases the java-client cannot express. Build scope + activation-recording resolved by **C1** below (seam + java-client live now, raw-W3C stub behind the seam, activation recorded in lineage). |
| S9 | The **committed locator cascade is NOT self-heal.** At runtime the interpreter tries the committed locators in the committed order; exhausting the committed cascade with no match is a **HARD FAIL → red build**. It never searches for, generates, or adapts a locator. |

**Clarify decisions locked (2026-08-05):**

| ID | Decision |
|----|----------|
| C1 | **raw-W3C fallback seam — seam + java-client now, raw-W3C stub behind the seam.** The driver seam interface + the official Appium java-client 10.x adapter ship live now; the raw-W3C-protocol adapter stays an unimplemented stub behind the seam, activated only when a concrete java-client limitation forces it — mirroring the spine's C5 read-only-stub pattern. One live driver path; the conformance corpus (C3) covers it plus a seam-contract test. **When the raw-W3C path does activate, that activation MUST be recorded in the run's lineage** so a driver fallback is never silent adaptivity in disguise. |
| C2 | **R2 novelty-sampling rate — reuse the spine's M36 draw, plan-level.** o7 does **not** introduce an o7-specific sampled-review fraction; it references the spine's existing **M36 "small fixed random draw"** (spec.md:308–311) by name, and the plan sets the draw size. No second sampling regime is forked; CF4's golden-set accumulation is unchanged. |
| C3 | **Interpreter release gate — a committed IR-conformance corpus gates every `interpreterVersion` pin.** A committed corpus of `TestCaseIR → expected-interpreter-behavior` cases — one per opcode (`TAP/TYPE/SWIPE/WAIT/ASSERT/LAUNCH/NAVIGATE`) and per assertion kind (`TEXT_EQUALS/ELEMENT_PRESENT/VALUE_CHECK`), plus the committed-cascade-miss → hard-fail case and each classification-taxonomy trigger — MUST pass before any `interpreterVersion` may be pinned into the pipeline; owned by the pipeline team, run no-device where possible. This makes `interpreterVersion` a *behaviorally* meaningful pin (guards the OpenTest/Selenium-IDE die-unmaintained failure mode) and is the ADR 0016 conformance-corpus release-gate fitness function. |
| C4 | **E2 execution-plan renderer — per-run evidence, rendered from the `irDigest`.** The human-readable execution plan is rendered deterministically from the committed `irDigest` at replay time into the A-STD evidence bundle; it is **never** committed as an authoritative artifact and **never** gated on. It lives in the `evidence` module (ADR 0005 module 3), on the T37 `ReplayReport` path — a pure re-derivable projection, so there is no IR-gate plan-consistency check and no committed-plan drift surface. |
| C5 | **Perfecto captured-version delta — evidence within the pinned major.minor, quarantine across it.** Captured `appiumVersion`/`automationVersion` deltas **within** the pinned major.minor are evidence-only; a captured delta that crosses **outside** the pinned major.minor quarantines the run, exactly like the spine's M24 record-actual / pinned-facet-mismatch rule (persisted quarantine status, ENV_INFRA-adjacent). "Pinned per epoch" ≡ the epoch boundary **is** the pinned major.minor: drift below that line is captured, drift across it is a failure path. |

## Problem

The **codegen stage is the LLM-adjacent part of o1** — it is where a model's output becomes Java, where per-run-generated code is compiled and executed, and where the "execute untrusted generated code" attack surface that ADR 0013 mitigates actually lives. o7 **deletes that stage**. The committed `TestCaseIR` — already screened, already committed, already the source of truth — becomes the **executable**, walked step-by-step by a version-pinned, non-adaptive, **LLM-free** interpreter over Appium/Perfecto. There is no per-run Java, no compile step, and no per-run-generated code to execute; the interpreter is fixed, audited, version-pinned code that executes committed **data**.

This is only defensible because it **preserves the two things the codegen path also had to preserve** and strengthens the spine's core premise:

- **Determinism** — a run's result is a function of the committed IR, the pinned interpreter, and the (evidenced) device stack, nothing else. The `pass^k` premise (a certified conversion passes k independent runs — the spec's K-integrity / K/K signal, CF6/D6) survives only if there is **no runtime AI** and **no self-heal**: every source of run-to-run adaptivity — cloud AI, locator repair, unbounded waits — is barred by construction so that a green is a property of the committed artifact, not of a lucky adaptive recovery. This is why `healPolicy` is fixed to `NONE`, why every wait is bounded, and why cloud adaptivity must be attested off per session.
- **The LLM-free spine** — ADR 0001 (F1) holds that no model call exists anywhere in the spine. The interpreter **strengthens** F1's intent: it walks committed data and by construction issues no model call at all. Deleting the codegen stage removes an LLM-*adjacent* surface (the codegen consumed model output upstream) from the replay path entirely.

The overturn is bounded: ADR 0016 overturns the POC brainstorm's "production stays code-based" boundary **only for committed-IR replay**, **not** for raw-LLM-output interpretation. The interpreter never interprets a model's live output; it interprets a committed, screened, gated artifact.

## Target artifact

Additions and replacements inside the **existing** spine repository (H-SB — a Spring Boot module, not a new deployable):

| Item | Content |
|------|---------|
| Interpreter module | A **Spring Boot module hosted by the device-gate worker** (ADR 0016, H-SB), replacing TestNG execution. Walks the committed `TestCaseIR` step-by-step over **Appium java-client 10.x** (H-SB) with a **raw-W3C fallback behind a seam** (C-MIG). **LLM-free by construction** (ADR 0001, strengthened), **non-adaptive** (no self-heal, no runtime AI), **version-pinned** (`interpreterVersion` = the module's Git SHA). Closed opcode set: `TAP`, `TYPE`, `SWIPE`, `WAIT`, `ASSERT`, `LAUNCH`, `NAVIGATE`. Assertion kinds: `TEXT_EQUALS`, `ELEMENT_PRESENT`, `VALUE_CHECK`. |
| IR gate | Replaces the o1 static gate (S4). Deterministic, pre-device, **zero device cost, zero compilation**. Seven checks: **schemaValid** (IR validates against the committed schema), **opcodeClosed** (only the closed opcode set + closed assertion kinds), **boundedWaits** (every `WAIT`/step carries a finite `timeoutMs`; no unbounded wait/sleep), **locatorManifest** (every locator the IR references is present in the committed `LocatorCandidate` manifest — no orphan), **noLiteralCreds** (vault-key indirection only, never a literal), **ambiguityClear** (no IR step flagged ambiguous survives to replay), **dryRun** (a no-device structural walk of the whole IR succeeds). |
| 3 new IR runtime fields | On `TestCaseIR` (S3): `timeoutMs` (per-step bounded wait), `syncAfter` (`WAIT_FOR_IDLE` \| `NONE`), `healPolicy` (fixed `NONE`). Plus `irDigest` (SHA of the canonical IR) as the audit pin. Added to the T05 Java records; JSON Schema regenerated and committed (drift fails CI, as in the spine). |
| Re-based `ReplayReport` pins | `codeCommit` (o1: SHA of generated Java) is **not applicable in o7** and is replaced by **`irDigest`** (SHA of the committed canonical IR) + **`interpreterVersion`** (the pinned interpreter's Git SHA). **`irDigest` subsumes the spine's `irVersion` pin as well as `codeCommit`** — the content-addressed digest *is* the IR version, so o7 rows carry **neither** `codeCommit` **nor** `irVersion` (ADR 0016 F6 amendment). `appiumVersion`/`automationVersion` are **demoted from pinned facet to captured evidence** — session-reported and captured, no longer pinned (Perfecto controls their upgrade schedule). Adds a per-session **`cloudAdaptivity`** attestation pair — **`selfHealing`** and **`perfectoAI`**, each `DISABLED` | `ENABLED` | `UNKNOWN` | `NOT_APPLICABLE` (Perfecto cloud-AI / self-heal is off) and **captured Perfecto versions as evidence** — session-reported `appiumVersion`/`automationVersion`/server/driver — pinned "per epoch, not forever" (Perfecto pins only major.minor from a curated menu and upgrades drivers on its own schedule; full-stack pinning is impossible). The o7 F6 applicable set is `{irDigest, interpreterVersion, pipelineVersion, appiumVersion (captured), device/OS/model, appVersion}`. F6's complete-or-invalid rule is **preserved**; the pinning **set** is amended (ADR 0016). The embedded `irGate` block additionally carries the **`gateVersion`** that produced its verdicts — without it the report records a gate outcome while dropping the pin that outcome's own reproducibility claim rests on (`IRGate.report.json` auditPin). **`gateVersion` is deliberately NOT in the F6 applicable set**: F6 is scoped to *execution* pins and carries complete-or-invalid teeth, and widening it for a gate concern would give a load-bearing rule new reach. Owner decision, 2026-08-09. |
| Execution-plan renderer (E2, C4) | Emits a rendered, human-readable **execution plan** as **per-run evidence** — rendered deterministically FROM the `irDigest` at replay time, **not** a separate source of truth and **never** committed as authoritative. Lives in the **`evidence` module** (ADR 0005 module 3), on the T37 `ReplayReport` path; landed alongside the `ReplayReport` in the A-STD evidence bundle. A pure re-derivable projection — no IR-gate plan-consistency check, no committed-plan drift surface (C4). |
| IR-conformance corpus (C3) | A committed corpus of `TestCaseIR → expected-interpreter-behavior` cases (one per opcode + assertion kind, plus committed-cascade-miss → hard-fail and each classification-taxonomy trigger) that MUST pass before any `interpreterVersion` is pinned into the pipeline; owned by the pipeline team, run no-device where possible. The behavioral contract that makes `interpreterVersion` a meaningful F6 pin and the ADR 0016 conformance-corpus release-gate fitness function (guards the OpenTest/Selenium-IDE die-unmaintained failure mode). |

## Acceptance criteria (EARS)

### Failure paths first

- **IF** a `TestCaseIR` references an opcode outside the closed set (`TAP`, `TYPE`, `SWIPE`, `WAIT`, `ASSERT`, `LAUNCH`, `NAVIGATE`) or an assertion kind outside `{TEXT_EQUALS, ELEMENT_PRESENT, VALUE_CHECK}`, **THEN** the IR gate MUST fail before any device is acquired (**opcodeClosed**). A vendor or authoring extension that adds an opcode is a spec change, never a silent runtime capability.
- **IF** any step lacks a finite `timeoutMs`, or requests an unbounded wait / sleep / poll-forever, **THEN** the IR gate MUST fail (**boundedWaits**). This is a **determinism control**, not a style rule — an unbounded wait makes a run's result a function of wall-clock timing rather than of the committed artifact, breaking the `pass^k` premise. (This **subsumes the spine's `Thread.sleep` static-gate lint, `spec.md:110`, via ADR 0016** — there is no test code to lint, so the unbounded-wait determinism control relocates from source-lint to schema-level `timeoutMs` enforcement.)
- **IF** a locator referenced by the IR is absent from the committed `LocatorCandidate` manifest, **THEN** the IR gate MUST fail **before any device is acquired** (**locatorManifest / no-orphan**). The interpreter never resolves a locator that was not committed.
- **IF** the no-device **dry-run** structural walk of the whole IR fails, **THEN** no replay request may be enqueued (**dryRun**). The dry-run is the R1 correctness substrate that makes the removed pre-commit engineer review safe to remove — a structurally broken IR never reaches a device.
- **IF** ingested IR carries a **literal** secret or credential rather than a vault-key reference, **THEN** the IR gate MUST fail (**noLiteralCreds**) — vault-key indirection is enforced at the gate/schema, never by review. (Carries the spine's schema-level literal-cred rejection into the o7 gate.)
- **IF** any IR step is flagged **ambiguous**, **THEN** the IR gate MUST fail (**ambiguityClear**) — an ambiguous step is resolved before commit or not replayed; the interpreter does not disambiguate at runtime.
- **IF** the committed **locator cascade is exhausted at runtime** without a match, **THEN** the run MUST **hard-fail (red build)** and the interpreter MUST NOT search for, generate, or adapt a locator (**`healPolicy: NONE`**). Classification is `LOCATOR_NOT_FOUND` (unchanged taxonomy). The committed cascade tried in committed order is **not** self-heal; exhausting it is a real failure, not a prompt to adapt.
- **IF** a `ReplayReport` is missing `irDigest` **or** `interpreterVersion`, **THEN** it MUST fail schema validation and **no verdict may be recorded** (**F6 re-based**). `codeCommit` and `irVersion` are **not applicable in o7** (both subsumed by `irDigest`), and their absence is **NOT** a substitute for the o7 pins — F6's complete-applicable-set-or-invalid rule holds against the **o7** pinning set. Null or absent is never valid for an applicable pinning field.
- **IF** a `ReplayReport` or lineage row **still carries** `codeCommit` **or** `irVersion`, **THEN** it MUST fail schema validation — o7 rows carry `irDigest` in their place; a retained o1 pin is a fork-boundary leak, not a valid extra field (**F6 re-based**).
- **IF** the **interpreter version is not pinned** — `interpreterVersion` absent, or a floating tag / branch name / `latest` rather than a Git commit SHA — **THEN** the IR gate MUST fail (mirrors the spine's runner-image-pinned-by-digest rule, `spec.md:99`; content-addressed by construction, a label is never a valid value).
- **IF** an `interpreterVersion` is pinned into the pipeline without a **green run of the committed IR-conformance corpus** at that version, **THEN** the release MUST be refused (**C3**). The corpus — one case per opcode + assertion kind, plus committed-cascade-miss → hard-fail and each classification-taxonomy trigger — is the behavioral contract that makes `interpreterVersion` a meaningful F6 pin; a version bump that silently changes what an opcode does is an audit-equivalence break, and the corpus is what catches it before the pin is trusted.
- **IF** a device session does **not** attest **both** `cloudAdaptivity.selfHealing = DISABLED` **and** `cloudAdaptivity.perfectoAI = DISABLED` — i.e. either is `ENABLED`, `UNKNOWN`, or absent — **THEN** the run MUST **quarantine** with an alert. `NOT_APPLICABLE` also proceeds, but **only** when the report references the written vendor confirmation that the source is outside the code-path execution path (ADR 0016, *Accepted residual risk*); an unreferenced `NOT_APPLICABLE` MUST fail schema validation — never counted as a normal run. Perfecto/BrowserStack inject cloud-AI / self-heal into Appium runs (post-2025); an adaptive session would break determinism, so an un-attested-off session is not the run that was requested. (Same persisted quarantine status as the spine's M24 pinned-facet mismatch.)
- **IF** a `ReplayReport` or lineage row omits the **captured Perfecto version evidence** — the session-reported `appiumVersion`/`automationVersion`/server/driver identifiers — **THEN** it MUST fail validation. These are captured as **evidence, not pins** ("pinned per epoch, not forever"), but their **absence** is still invalid: full-stack pinning is impossible, so the captured session versions are the only reconstruction the audit has.
- **IF** a **certification verdict** row lacks an **INDIVIDUAL** principal, **THEN** it MUST be **invalid at the database level** (**M37 relocated to the verdict**). The service-principal commit (`svc:conversion-pipeline`) is a **valid M37 principal for the commit row** but is **not a valid certifier** — the individual-principal requirement is preserved by relocating it from the commit row (o1's committing engineer) to the **verdict row** (o7's post-run section-7 evaluator). A catch-all `system` principal remains forbidden.
- **IF** a **fully-autonomous path attempts to issue a certification verdict with no human evaluator** (R5), **THEN** it MUST be **refused** — R5 is **barred** on the certified path (CF9 + M37). The interpreter's machine `PASS` is a **precondition**, never a certification; a certification is an attributable individual decision.
- **IF** the same replay request is delivered to the device-gate worker more than once, **THEN** exactly one interpreter run MUST result — the consumer is idempotent and a redelivery MUST NOT double-spend device minutes (**carried unchanged** from ADR 0007 / C2; the interpreter replaces TestNG behind the same idempotent-consumer contract).
- **IF** an interpreter run fails for **infrastructure** reasons, **THEN** classification MUST be `ENV_INFRA` and the run MUST **re-queue** with the spine's bounded retry cap + backoff, dead-lettering to persisted quarantine with an alert on cap exhaustion — **never heal, never count against the test** (**carried unchanged**; the interpreter inherits the ENV_INFRA re-queue contract).
- **IF** a pulled device artifact is read by any downstream step before its SHA-256 digest is recorded in the append-only lineage row for the pull, **THEN** that read MUST fail (**hash-at-pull, carried unchanged** — the interpreter pulls Perfecto Smart Reporting artifacts exactly as the TestNG worker did).
- **IF** a lineage row lacks an authenticated principal (individual for human actions; per-component **service** principal — including `svc:conversion-pipeline` for the auto-commit and the device-gate/interpreter worker for the run), **THEN** the row MUST be invalid at the DB level; a catch-all `system` principal is never valid (**M37 carried**; the verdict-row individual requirement above is the o7 **amendment**, not a replacement of this rule).
- **IF** a lineage row commits without its per-conversion hash-chain link, **THEN** the write MUST fail; a chain-verification mismatch quarantines with an alert (**ADR 0012 carried unchanged** — the interpreter run's lineage rows chain exactly as the spine's do).
- **IF** the interpreter run's actually-reported execution context mismatches the requested set on a facet the run **claims** to pin (device model, OS version), **THEN** the run MUST quarantine with an alert (**record-actual / M24 carried, pinned-facet set narrowed via ADR 0016; see Delta**). The pinned-facet set narrows to **device model + OS version**: `appiumVersion`/`automationVersion` are **removed from the pinned-facet set and captured as evidence** in o7 (Perfecto controls them).
- **IF** the captured Perfecto `appiumVersion`/`automationVersion` for a run **crosses outside the pinned major.minor epoch**, **THEN** the run MUST quarantine with an alert — the same persisted quarantine status as the M24 pinned-facet mismatch (**C5**). Drift **within** the pinned major.minor is evidence-only and does not quarantine; the epoch boundary **is** the pinned major.minor ("pinned per epoch, not forever"). This is the determinism guardrail for the demoted Perfecto facets — captured-not-pinned does not mean unbounded.

### Happy path

- **Ubiquitous:** the interpreter MUST build as a **Spring Boot module inside the existing repository**, hosted by the device-gate worker, with **no per-test generated Java** anywhere in the pipeline (F-B). The interpreter's own Java and vendored Appium java-client internals do **not** count against F-B; **per-test generated Java/TestNG** is what MUST NOT exist. A CI/ArchUnit rule (T02) MUST fail the build if a per-test generated Java/TestNG artifact appears in the replay path.
- **Ubiquitous:** `TestCaseIR` MUST carry the three new runtime fields — `timeoutMs`, `syncAfter` (`WAIT_FOR_IDLE`\|`NONE`), `healPolicy` (fixed `NONE`) — plus `irDigest`, as Java records with Jackson bindings; the regenerated JSON Schema MUST be committed and drift MUST fail CI (as in the spine).
- **Ubiquitous:** the **IR gate MUST run first** and complete pre-device with **zero device cost and zero compilation**, rejecting on any of its seven checks (schemaValid, opcodeClosed, boundedWaits, locatorManifest, noLiteralCreds, ambiguityClear, dryRun). It replaces the o1 static gate; there is no `mvn compile`/Checkstyle/Error Prone leg because there is no generated Java.
- **WHEN** the IR gate passes, **THEN** a replay request MUST be enqueued via the producer's transactional outbox (C2, unchanged); **WHEN** the device-gate worker consumes it, **THEN** the **interpreter** MUST acquire a device from a pinned Perfecto pool by capability set and **walk the committed `TestCaseIR` step-by-step** over Appium java-client 10.x — trying each committed locator cascade in committed order, honouring each step's `timeoutMs` and `syncAfter`, and **never** searching for, generating, or adapting a locator (`healPolicy` NONE). The worker MUST hold **no gateway credential** (ADR 0013 topology, **strengthened** — there is no generated code to execute at all).
- **WHEN** the interpreter runs, **THEN** it MUST attest **`cloudAdaptivity.selfHealing = DISABLED`** and **`cloudAdaptivity.perfectoAI = DISABLED`** for the session. `UNKNOWN` is the required value where the provider returns no attestation — it is an honest record, not a pass, and quarantines exactly as `ENABLED` does. `NOT_APPLICABLE` is available **only** with a referenced written vendor confirmation; it is never an engineer's judgement call and never a default.
- **WHEN** the interpreter pulls a Perfecto Smart Reporting artifact, **THEN** it MUST compute and record a per-artifact SHA-256 digest at landing **before any downstream read** (hash-at-pull, carried unchanged).
- **WHEN** the interpreter pulls a Perfecto Smart Reporting artifact, **THEN** it MUST pass that artifact through the screening library at landing (ADR 0009 boundary (2), unchanged).
- **WHEN** the interpreter runs, **THEN** it MUST **capture the session-reported Perfecto versions as evidence** (`appiumVersion`/`automationVersion`/server/driver).
- **WHEN** the interpreter run completes, **THEN** classification MUST be **rule-based against the unchanged fixed taxonomy** (`LOCATOR_NOT_FOUND`, `STALE_ELEMENT`, `TIMEOUT_SYNC`, `ASSERTION_MISMATCH`, `APP_CRASH`, `DATA_PRECONDITION`, `ENV_INFRA`) — deterministic rules mapping Appium exception types and Perfecto failure reasons; explicitly **not** LLM work (unchanged from the spine).
- **WHEN** a run yields a verdict-eligible result, **THEN** the `ReplayReport` MUST validate against the **re-based schema** — carrying `irDigest` + `interpreterVersion` (replacing `codeCommit` and `irVersion`), the `cloudAdaptivity` attestation pair, and the captured Perfecto version evidence, with the complete applicable pinning set (F6 preserved) — and a rendered **execution plan** MUST be emitted as **evidence**, rendered FROM the `irDigest` (E2), landed alongside the report and **not** treated as a source of truth.
- **WHEN** the machine `PASS` precondition is met, **THEN** certification MUST be issued as an **attributable individual decision** by the **spec-section-7 human evaluator, POST-RUN** (CF9 preserved); the interpreter's `PASS` is a precondition, never the certification. The **commit** is by `svc:conversion-pipeline` (R4) and is a valid M37 principal for the commit row; the **verdict** carries the individual evaluator's principal (M37 relocated).
- **WHERE** novelty-sampled review applies (R2), **THEN** an IR from a **source shape not seen before** MUST route to **mandatory** review, and an IR from a **known shape** MUST route to **sampled** review at the spine's existing **M36 "small fixed random draw"** (spec.md:308–311, C2), reusing the **CF4/M21 sampling flag** on the quarantine/review-record shape — no new review surface and no o7-specific sampling regime is introduced (the draw size is a plan-level value).
- **WHEN** the interpreter falls back from the official java-client to the **raw-W3C driver path** (C1), **THEN** that activation MUST be recorded in the run's lineage row — a driver fallback is an evidenced event, never silent adaptivity in disguise. (In this baseline the raw-W3C adapter is a stub behind the seam; the criterion binds the moment it is implemented.)
- **WHERE** the o7 week-gate is exercised, the binding clause (replacing the spine's clause (a), `spec.md:330`, within the WHERE criterion at `spec.md:329`–`spec.md:334`): **the committed reference `TestCaseIR`, committed to the repo, MUST be walked end-to-end by the interpreter — IR gate, device gate on a real Perfecto device, classification — and yield a `ReplayReport` that validates against the re-based schema with a complete applicable pinning set (`irDigest` + `interpreterVersion` + both `cloudAdaptivity` attestations `DISABLED` + captured Perfecto version evidence)**. The spine's clause **(b)** (ingestion produced `REAL_INGESTED` IR from real source material, M19) carries **unchanged** and still binds the o7 gate.

## Non-goals (out of o7 scope, deferred, or barred)

- **Per-test Java codegen** — deleted (F-B). o7 has no generated Java/TestNG in the pipeline; this is the whole point of the fork, not a deferral.
- **Self-heal / locator repair loops** — barred by `healPolicy: NONE`; exhausting the committed cascade is a hard fail. Not deferred — **structurally excluded** to preserve determinism.
- **Runtime AI / cloud adaptivity** — barred; must be attested off per session (`cloudAdaptivity.selfHealing` + `cloudAdaptivity.perfectoAI`, both `DISABLED`). Perfecto/BrowserStack cloud-AI is a determinism break, not a feature.
- **Raw-LLM-output interpretation** — the ADR 0016 overturn is **only** for committed-IR replay. The interpreter never interprets a model's live output.
- **D7 — signed in-toto attestation** — a **named follow-on**, not built now (S6). A-STD standard evidence bundle (re-based `ReplayReport`) is what ships.
- **R5 — fully-autonomous certification** — **BARRED** on the certified path (CF9 + M37 require an individual principal on the verdict). Not a future feature; a hard boundary.
- **Removing o1** — out of scope (S2). Both pipelines stay live; this spec does not retire the codegen path.
- **Full-stack Perfecto version pinning** — impossible (Perfecto controls driver upgrades); captured as evidence, not pinned. Not a gap to close.
- Anything the **spine spec already scopes out** (Phase 2 machinery, review-queue UI, metrics dashboard / read model, object-repository write-back, envelope-encryption machinery, etc.) remains out of scope here.

## Delta to the signed-off spine spec

Each amendment is **via ADR 0016** and is described in ADR 0016's Consequences + a spine-spec amendment section (mirroring the ADR-0015 A0-fold landing). ADR 0016 **supersedes nothing** (supersede links are ADR→ADR); it **amends** the spec.

| Spine surface | Spine reference | o7 amendment | Via |
|---------------|-----------------|--------------|-----|
| **F6 pinning set** | `spec.md:88`–`spec.md:105` | `codeCommit` → `irDigest` + `interpreterVersion`; **`irVersion` is subsumed by `irDigest`** (the content-addressed digest *is* the version — o7 rows carry neither `codeCommit` nor `irVersion`); `appiumVersion`/`automationVersion` **demoted from pinned facet to captured evidence** (Perfecto controls them); add the `cloudAdaptivity` attestation pair (`selfHealing`/`perfectoAI`, tri-state) + captured-Perfecto-version evidence. o7 F6 applicable set = `{irDigest, interpreterVersion, pipelineVersion, appiumVersion (captured), device/OS/model, appVersion}`. **Complete-or-invalid rule preserved**; the applicable **set** changes. | ADR 0016 |
| **IR-gate verdict provenance** | *(new in o7)* | `ReplayReport.irGate` carries the **`gateVersion`** that produced its seven verdicts, matching the `gateVersion` on `IRGate.report.json`. **Not** added to the F6 applicable set — see the F6 row. | Owner decision 2026-08-09 (pre-gate hygiene, next-items I5) |
| **M37 attribution locus** | `spec.md:159`–`spec.md:164` | Attribution for the **certification verdict** moves from the commit row (o1: committing engineer) to the **verdict row** (o7: post-run section-7 evaluator). Commit is now `svc:conversion-pipeline` — a valid M37 service principal, not the attribution anchor. Individual-principal requirement **preserved by relocation**. | ADR 0016 |
| **M24 pinned-facet set** | `spec.md:152`–`spec.md:157` | **Appium/automation version removed from the pinned-facet set** (now captured evidence, Perfecto-controlled); the pinned facets **narrow to device model + OS version**. Quarantine-on-mismatch **preserved for the retained facets**. | ADR 0016 |
| **Replay-pipeline-v1 row** | `spec.md:65` | `static gate (mvn compile, Checkstyle, Error Prone, locator-manifest) → device gate (TestNG, pinned Appium) → classification` becomes `IR gate → interpreter walks committed IR on Appium/Perfecto → classification`. Classification taxonomy **unchanged**. | ADR 0016 |
| **`Thread.sleep`/explicit-waits static-gate rule** | `spec.md:110`–`spec.md:111` | **Subsumed by the IR-gate `boundedWaits` check** — there is no test code to lint; the unbounded-wait determinism control relocates from source-lint to schema-level `timeoutMs` enforcement. | ADR 0016 |
| **T02** (F-rules) | task roster | Add the **no-per-test-Java** ArchUnit rule (per-test generated Java/TestNG in the replay path fails the build). | ADR 0016 |
| **T05** (Java records) | task roster | Add the **3 runtime IR fields** (`timeoutMs`, `syncAfter`, `healPolicy`) + `irDigest` to `TestCaseIR`. | ADR 0016 |
| **T07** (F6 validation) | task roster | Re-base the pinning-set validation to the o7 set (`irDigest` + `interpreterVersion` + both `cloudAdaptivity` attestations `DISABLED` + captured Perfecto evidence; reject retained `codeCommit`/`irVersion`). | ADR 0016 |
| **T30** (static gate) | task roster | **Replaced** by the **IR gate** (seven deterministic checks; no compilation). | ADR 0016 |
| **T31–T32** (enqueue + device-gate worker) | task roster | The device-gate worker now **hosts the interpreter** instead of running TestNG; enqueue/idempotent-consumer contract unchanged. | ADR 0016 |
| **T35** (classification) | task roster | **Unchanged** — same deterministic taxonomy. Listed for completeness. | — |
| **T37** (`ReplayReport` emission) | task roster | Re-based pins (as T07) + emit the rendered execution plan (E2). | ADR 0016 |
| **T40** (commit a reference test) | task roster | o1 commits a hand-written Appium reference test; o7 commits a **reference `TestCaseIR`** instead. | ADR 0016 |
| **T41** (gate clause a) | task roster; clause (a) at `spec.md:330` (WHERE criterion `spec.md:329`–`spec.md:334`) | *"one hand-written Appium test flows end to end"* becomes *"the committed reference IR is walked end to end by the interpreter, yielding a re-based `ReplayReport`"*. Clause (b) (M19 `REAL_INGESTED`) unchanged. | ADR 0016 |
| **New task** (IR-conformance corpus) | task roster (adjacent to T40's reference IR) | Add the committed **IR-conformance corpus** + its release-gate check — no `interpreterVersion` is pinned without a corpus-green run (C3, ADR 0016 fitness function). | ADR 0016 / C3 |

## Carry-forward inheritance

o7 inherits the spine's carry-forward rules **CF1–CF11 unchanged**, with **one clarification** and **one enforcement note**:

- **CF9 (advisory judge, never autonomous) — clarified for o7:** the **interpreter's `PASS` is the machine precondition**; the **section-7 human evaluator's post-run certification is the individual verdict**. This is the exact reading CF9 already carries, made concrete against the interpreter: a machine PASS is a precondition, never a certification.
- **R5-barred is the enforcement of CF9's "never autonomous":** the failure-path criterion that refuses a fully-autonomous certification verdict is precisely CF9 + M37 enforced on the o7 path. o7 adds no weakening of CF9; it **operationalizes** it.

All other carry-forwards (CF1 custody-before-certify, CF2 certify-read-source, CF3 certify-locally/publish-async, CF4 review-record calibration fields — **which R2 reuses for novelty sampling**, CF5 published-asset-version, CF6 K-integrity, CF7 fidelity re-derivation, CF8 vault-key indirection flip, CF10 generated-code execution isolation — **strengthened**, since there is no generated code to execute, CF11 auditor-export inheritance) carry **unchanged**. The weeks-3–8 spec still imports CF1–CF11 at its scoping step; o7 does not drop or amend any of them beyond the CF9 clarification above.

## Recorded precedent (why removing the pre-commit engineer review is defensible)

ADR 0013 **already rejected** "human review of every generated script before execution" as a security control — recorded as *"genuinely effective and genuinely fatal to the system's purpose."* That is the load-bearing precedent for R4: the pre-commit review was **never the security control**. Its residue decomposes cleanly:

- **Correctness** — now owned by the **IR gate + no-device dry-run (R1)**: a structurally invalid IR never reaches a device.
- **M37 attribution** — now owned by the **post-run verdict (R4)**: the individual principal lands on the certification, not the commit.

The commit becomes a service-principal action (`svc:conversion-pipeline`), which ADR 0013's isolation posture is **strengthened** by: with no per-run-generated code to execute at all, the "execute untrusted generated code" attack path ADR 0013 mitigates is largely **dissolved** — the interpreter is fixed, audited, version-pinned code executing committed **data**. The ADR 0013 credential topology (device-gate/interpreter worker holds **no gateway credential**) is **preserved**.

## Clarify pass

Run 2026-08-05, five questions, each with a recommended answer anchored to an existing spine mechanism rather than new machinery; **all five followed the recommendation** and are locked as C1–C5 above. C1 (raw-W3C seam) reuses the C5 stub pattern; C2 (R2 rate) reuses M36; C3 (interpreter release gate) adds the committed IR-conformance corpus as the behavioral contract behind `interpreterVersion`; C4 (E2 renderer) places the plan as per-run evidence in the `evidence` module; C5 (Perfecto drift) reuses the M24 quarantine rule with the pinned major.minor as the epoch boundary. No answer varied from the recommendation.

This spec is written to the confirmed design bundle (owner-approved 2026-08-05) and does **not** re-litigate F-B / E2 / H-SB / C-MIG / R-YES / A-STD / R4+R2 / the R5 bar; those are locked. Sign-off is gated on ADR 0016 moving Proposed → Accepted at the same gate that closes this spec.

## Pre-gate amendment — 2026-08-09 (field shapes; three owner decisions)

Recorded visibly rather than patched in silently. **This spec is not yet signed
off**, so these are corrections to the artifact *before* signature — which is the
point: closing the gate over an internal contradiction ratifies the contradiction.
Source: next-items plan I5 / research report §7.5 item 6.

**1. Cloud-adaptivity attestation is a structured tri-state pair, not a boolean.**
Was `cloudAdaptivityDisabled` (boolean) in 9 places here and
`cloudAdaptivity.{selfHealing, perfectoAI}` in ADR 0016 (:208, :263, :339) and
`ReplayReport.json:28`. **The ADR and the mocks win**, with values extended to
`DISABLED` | `ENABLED` | **`UNKNOWN`**. Rationale: ADR 0016:339-341 quarantines a
run "without both attestations, **or with either enabled**" — three distinct
states, which one boolean cannot carry. `UNKNOWN` is the honest value when the
provider returns no attestation, and it quarantines exactly as `ENABLED` does;
neither Perfecto nor BrowserStack offers per-session cryptographic attestation
(next-items I7), so `UNKNOWN` will be a real value, not a theoretical one.
All 9 sites rewritten.

**2. `dryRun` is the seventh entry inside `checks`, not a sibling.** This spec
(:33, :82, :119), ADR 0016 (:328-329) and `ReplayReport.irGate` all say **seven
checks** and name `dryRun` among them; only `IRGate.report.json` disagreed, and it
has been corrected. Beyond the count: with `dryRun` outside `checks`, any
"all checks PASS" iteration over `checks{}` silently skips it — a fail-open on the
check this spec (:95) calls the R1 correctness substrate that makes removing
pre-commit engineer review safe.

**3. `ReplayReport.irGate` carries `gateVersion`; it does NOT join F6.** Not a
spec-vs-mock conflict as originally filed: `gateVersion` is an established
gate-report convention (o1 `StaticGate.report.json:6` carries it with the same
auditPin), and F6 governs `ReplayReport`, a different artifact. The real gap was
that `irGate` recorded seven verdicts while dropping the pin their reproducibility
rests on. Added. Kept **out** of the F6 applicable set — see the F6 row in the
delta table for why.

**4. Attestation posture accepted, and a fourth state added (next-items I7,
same day).** Posture: **(b) post-run assertion** — each run asserts from its own
evidence (`healsApplied: NONE` + no healed-locator markers in the session log)
that no cloud healing occurred — recorded explicitly as **evidence of absence, not
a signed guarantee**. **(c) self-hosted Appium** is the named escalation, not
adopted: it would give up the Perfecto lab these specs name, so it is an
sdd-replan event. **(a) capability echo** is rejected — Perfecto exposes no toggle
to echo.

This forced a fourth attestation state. Perfecto documents self-healing as a
**Scriptless product feature** with **no code-path AI toggle and no toggle to
attest at all** — so `perfectoAI` could never reach `DISABLED`, and decision 1's
quarantine rule would quarantine **every run**: a gate that never opens rather
than a risk accepted. `cloudAdaptivity.*` therefore admits **`NOT_APPLICABLE`**,
reusing the spine's existing `PinnedValue` vocabulary (`{REAL, NOT_APPLICABLE,
UNPINNABLE_PHASE1}`) rather than inventing one. It is valid **only** with a
written vendor confirmation on file and referenced from the report; unreferenced,
it is a schema violation, never a default and never an engineer's call.

**That confirmation does not exist yet.** Until Perfecto states in writing that
Scriptless self-healing does not touch code-path Appium sessions, `perfectoAI =
UNKNOWN` and runs quarantine. The question is folded into the already-open
Perfecto vendor contact (next-items I6) — one channel, two questions.

**What none of this does.** H10 is still not *satisfied*; ADR 0016 now records
precisely how far short the evidence falls and what would close it (the D7 in-toto
signed-attestation follow-on, still not built). Interpreter-side self-heal was
never at risk — `healPolicy: NONE` and hard-fail on cascade exhaustion are
structural (:98, :135), not attested.

## Sign-off gate

**OPEN — awaiting owner Stage-2 sign-off.** On sign-off: this spec closes, ADR 0016 flips Proposed → Accepted at the same gate (the ADR is the *why*, this spec the *what*), and the paired sdd-replan of the signed-off spine spec records the F6 / M37 / M24 / replay-pipeline-v1 / T30-T41 amendments in the spine spec itself (mirroring the ADR-0015 A0-fold landing). Only then does Stage-2 advance to **plan** (the second hard gate: spec → plan → tasks). No plan or task derivation happens before this gate closes.
