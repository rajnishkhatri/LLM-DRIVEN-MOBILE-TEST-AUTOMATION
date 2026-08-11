---
type: architecture
title: ADR 0016 — Execute the committed TestCaseIR with a version-pinned interpreter; delete the code-generation stage
description: 'The o7 fork''s founding decision, recording the R-YES overturn: the committed TestCaseIR becomes the executable and the per-test Java/TestNG code-generation stage is deleted, replaced by a version-pinned, non-adaptive, LLM-free Spring Boot interpreter (Appium java-client 10.x, raw-W3C fallback behind a seam) walking the IR on Perfecto. Amends the signed-off spine spec on three load-bearing axes — the F6 pinning set (codeCommit → irDigest + interpreterVersion, plus a per-session cloud-adaptivity-disabled attestation and captured-not-pinned Perfecto versions), the M37 attribution anchor (certification-verdict attribution relocated from the human commit row to the post-run section-7 evaluator; commit is now a service principal svc:conversion-pipeline), and the replay-pipeline-v1 row (static gate → IR gate; TestNG device gate → interpreter walk). Removes the pre-commit engineer review on the strength of ADR 0013''s already-recorded rejection of per-script human review as a security control, relocating its correctness residue to the deterministic IR gate + dry-run and its attribution residue to the post-run verdict; bars R5 (fully autonomous certification) as a hard boundary under CF9 + M37. healPolicy is fixed to NONE and the committed locator cascade is a hard-fail, never a runtime repair. Signed in-toto attestation of the ReplayReport (D7) is named as a follow-on, not built now.'
tags: [architecture, mobile-test-automation, adr, arch-decide, o7-interpreter-fork]
---

# ADR 0016. Execute the committed TestCaseIR with a version-pinned interpreter; delete the code-generation stage

## Status

**Proposed** — 2026-08-05, awaiting the owner's SDD Stage-2 gate. This is the
founding decision of the **o7 interpreter fork**, drawn from the o7 interpreter
brainstorm (2026-08-05). It records the **R-YES overturn** the brainstorm's
confirmed bundle demands: the boundary the POC brainstorm recorded — "production
stays code-based" — is reversed **for committed-IR replay only**, never for
raw-LLM-output interpretation, and the reversal is recorded here rather than
taken silently.

**Both pipelines stay live.** o1 (LLM → Java/TestNG code generation) is the
parent and is not retired; o7 forks it by deleting the code-generation stage and
making the committed `TestCaseIR` the executable. This ADR **supersedes nothing**
(supersede links are ADR→ADR) but **amends the signed-off spine spec**
(`docs/sdd/specs/mobile-test-automation-spine.spec.md`, status SIGNED OFF /
re-sign-off 2026-07-27, plus the A0-fold amendment 2026-08-01 and the ADR-0015
owner override 2026-08-02) on three load-bearing axes — **F6** (spec.md:88–105),
**M37** (spec.md:158–164), and the **replay-pipeline-v1 row** (spec.md:65) — plus
tasks T30/T40/T41. The amendment lands in **Consequences** and a paired
**sdd-replan** of the spine spec, mirroring how ADR 0015's A0-fold and A0-override
landed as spec amendments rather than as new spec sign-offs.

Last responsible moment for the **executable-shape** decision recorded here:
**now**, at the o7 fork's Stage-2 gate — it determines the device-gate worker's
structure (T31–T32), the F6 pinning set (T07), and the T02 ArchUnit rule set, and
is the expensive retrofit. The **interpreter product** (conformance corpus,
release cadence, maintainer) is resourced from the same gate; the signed in-toto
attestation (**D7**) is deferred as a named follow-on (A-STD).

## Context

**Forces.** The o1 replay pipeline v1 (spec.md:65) generates per-test Java/TestNG
from an LLM, then runs it: `static gate (format, mvn compile, Checkstyle, Error
Prone, locator-manifest rule) → device gate (pinned Perfecto pool, TestNG, pinned
Appium) → rule-based classification → ReplayReport`. Three forces push against
keeping generated code as the executable:

1. **The generated Java is an audit liability, not an audit asset.** F6
   (spec.md:88–105) pins `codeCommit` (in o1, the commit SHA of the generated
   Java) so that a verdict is reproducible. But the reproducible artifact is machine-authored
   code no human wrote and every human must still read to trust. The committed
   IR is already the reviewed, screened, canonical intent (M15; ADR 0009); the
   Java is a lossy re-expression of it that adds a compile step, a code-review
   step, and a second thing to pin.
2. **Determinism is the product requirement, and generated-then-adapted code
   fights it.** The certified path needs a stable **K/K / pass-rate signal**
   (CF6/D6, spec.md:383) — K-integrity, the spec's term for pass^k in the eval
   literature. An executable that a device cloud can silently make *adaptive*
   at runtime — Perfecto/BrowserStack inject cloud-AI self-heal into Appium runs
   post-2025 — cannot carry that signal. The executable must be **non-adaptive by
   construction**, which the interpreter can guarantee and a bought adaptive tool
   cannot.
3. **The pre-commit engineer review is the throughput tax the whole system was
   built to remove, and ADR 0013 already recorded that this review was never the
   security control** (0013:74–76, 0013:179). Its residue is correctness and
   M37 attribution — both relocatable.

**What the spine already gives o7 for free.** The IR, `LocatorCandidate`
manifest, and `ReplayReport` already exist as Java records (T05, spec.md:60); the
screening library already screens at three call sites (ADR 0009, spec.md:62); the
lineage store, hash-chain, and M37 principal schema already exist (ADR
0006/0012, spec.md:66). o7 consumes already-committed, already-screened IR and
adds **no new trust boundary** (ADR 0009 strengthened, below).

**Alternatives considered.**

- **A version-pinned, non-adaptive, LLM-free interpreter over the committed IR,
  built as a Spring Boot module on Appium java-client 10.x** (chosen — F-B, H-SB,
  C-MIG, E2). The IR is the executable; the code-generation stage is deleted; a
  rendered execution plan is emitted as evidence, not as a second source of truth.
- **Keep code generation (status quo o1 — the parent).** Passes o7's whole reason
  by. o1 remains live for teams that want generated Java; o7 exists precisely to
  delete that stage. Not a competitor — the baseline being forked from.
- **Buy an analyst-leader adaptive test tool.** Rejected: the market leaders are
  ranked *for* self-healing / runtime adaptivity — the exact property that fails
  the K/K determinism requirement (force 2) — and they drive their own device
  farms, locking out Perfecto, which the bank's contract fixes. "Buy a leader" is
  refuted by the requirement, not merely dispreferred.
- **A Maestro-style YAML/JSON-flow interpreter.** Matches o7's shape almost
  exactly (a declarative flow walked by a fixed runner) but **bypasses Appium** and
  drives devices through its own stack — so it cannot drive Perfecto. Right shape,
  wrong substrate.
- **Robot Framework: compile IR → `.robot`, run Robot over Appium.** The strongest
  genuine buy-not-build fallback — a mature, maintained runner whose `output.xml`
  is an excellent off-the-shelf audit artifact. Passed because it is an awkward
  fit (IR → `.robot` is a second codegen we just deleted, and `.robot` becomes a
  per-test generated artifact that re-trips F-B) and still needs an interpreter
  *product* wrapper (IR gate, pin re-base, cloud-adaptivity attestation) that
  Robot does not supply. Named as the fallback if the build path is refused.
- **Write the interpreter in Python or TypeScript.** Rejected in favour of H-SB:
  the pipeline stack is already decided Spring Boot (ADR 0005; spine spec's
  3-module monolith), the vendored Appium java-client is a first-class JVM
  dependency, and a second-language runtime would fork the build, the CI, and the
  pinning story for no gain.

**Review-removal alternatives (weighed on their own axis).**

- **R4 + R2 on an R1 substrate** (chosen): the deterministic IR gate + no-device
  dry-run (R1) is the correctness substrate; the IR + locator manifest are
  auto-committed by `svc:conversion-pipeline` (R4); novelty-sampled review (R2)
  reuses the spec's existing CF4/M21 sampling flag; the section-7 human evaluator
  certifies **post-run** as the sole attribution anchor.
- **R5 — fully autonomous, no human on the certification verdict.** **BARRED** on
  the certified path. CF9 (spec.md:386) makes certification an attributable
  *individual* decision and a machine PASS a precondition, never a certification;
  M37 (spec.md:158–164) forbids a verdict row without an individual principal.
  R5 is not a deferred option; it is a hard boundary.
- **Keep the pre-commit human review.** Rejected on recorded precedent: ADR 0013
  already ruled per-script human review "genuinely effective and genuinely fatal
  to the system's purpose" (0013:74–76) and rejected it as a *security control*
  (0013:179). It was never the control; its residue is correctness (→ R1) and
  attribution (→ R4).

**Qualification.** Nygard test: passes — it deletes a pipeline stage, changes the
device-gate worker's structure, and re-bases the pinning set and the attribution
anchor, serving a top-3 characteristic (auditability/determinism). Third-law
test: passes — every option trades determinism, audit-artifact quality, vendor
lock-in, throughput, or build cost. Timing: the executable shape must be decided
now (it is the retrofit); the D7 attestation must not be.

### Trade-off matrix

| Contextual factor (weight) | Pinned IR-interpreter, build (chosen) | Keep o1 codegen | Buy analyst-leader | Maestro-style | Robot Framework (IR→.robot) |
|---|---|---|---|---|---|
| Determinism / K-integrity (CF6/D6) (5) | **++** non-adaptive by construction, `healPolicy: NONE` | + until cloud-AI creeps in | −− ranked *for* self-heal | ++ if pinned | ++ |
| Audit-artifact quality (5) | **++** IR is the reviewed artifact; execution plan as evidence | − pins machine-written Java nobody authored | −− opaque vendor runner | + flow is readable | ++ `output.xml` is excellent |
| Drives Perfecto (bank-fixed) (5) | **++** Appium java-client 10.x + raw-W3C fallback | ++ | −− own device farm | −− bypasses Appium | ++ via Appium |
| Fits the decided stack (ADR 0005) (4) | **++** Spring Boot module | ++ | − | − | + JVM but new runner |
| Throughput (removes review tax) (4) | **++** IR gate + dry-run replace pre-commit review | −− human reads every script | + | + | + |
| Build / maintenance cost (4) | **−−** we own an interpreter product (corpus, releases, maintainer) | ++ nothing new | ++ bought | + OSS | **+** mature, maintained |
| No per-test generated Java (F-B) (5) | **++** none exists | −− the whole stage | ++ | ++ | −− `.robot` re-trips F-B |

## Decision

**We will delete the per-test code-generation stage and execute the committed
`TestCaseIR` directly: a version-pinned, non-adaptive, LLM-free interpreter — a
Spring Boot module on Appium java-client 10.x with a raw-W3C fallback behind a
seam — walks the committed IR on the pinned Perfecto pool; the IR is the single
source of truth and the executable, and a rendered human-readable execution plan
is emitted as evidence, not as a second source. We re-base the audit pin from
`codeCommit` to `irDigest` + `interpreterVersion`, relocate certification-verdict
attribution from the commit row to the post-run section-7 evaluator, remove the
pre-commit engineer review, and bar fully-autonomous certification.**

The why front and center: **make the reviewed artifact the executed artifact.**
o1 reviews the IR, generates Java from it, and then must re-establish trust in the
Java. o7 executes the thing that was already reviewed. Everything below follows
from that single move.

**Technical justification:**

- **The executable is the committed IR; the code-generation stage is deleted
  (F-B, E2).** No per-test Java/TestNG artifact is generated anywhere in the o7
  pipeline. The interpreter *itself* is Spring Boot Java (pipeline infra is
  already Spring Boot — ADR 0005 / spine spec), and the vendored Appium
  java-client internals are library code, not per-test artifacts; neither counts
  against F-B. What F-B removes is **per-test generated Java/TestNG**. The IR is
  the single source of truth (E2); the emitted execution plan is rendered **from
  the `irDigest`** as human-readable evidence and is never a parallel source.
- **C-MIG — official java-client, raw-W3C fallback behind a seam.** The
  interpreter drives Appium through the official java-client 10.x for coverage and
  support, with a raw-W3C-protocol fallback behind a driver seam for the commands
  the client wraps awkwardly or lags on. The seam keeps the migration path open
  without forking the interpreter on the client's release schedule.
- **The IR gate replaces o1's static gate — deterministic, pre-device, zero
  device cost (R1).** It runs seven checks: `schemaValid`, `opcodeClosed` (only
  the closed opcode set `{TAP, TYPE, SWIPE, WAIT, ASSERT, LAUNCH, NAVIGATE}`,
  assertion kinds `{TEXT_EQUALS, ELEMENT_PRESENT, VALUE_CHECK}`), `boundedWaits`
  (every step carries a finite `timeoutMs`; no unbounded wait or sleep),
  `locatorManifest` (every IR-referenced locator is present in the committed
  `LocatorCandidate` manifest — no orphan), `noLiteralCreds` (vault-key
  indirection, never a literal — CF8, spec.md:385), `ambiguityClear` (no IR step
  flagged ambiguous), and `dryRun` (a no-device structural walk of the whole IR
  succeeds). It replaces `mvn compile`/Checkstyle/Error Prone — there is no code
  to compile — and is CI-blocking.
- **The committed locator cascade is not self-heal.** At runtime the interpreter
  tries the committed locators in the committed order; a miss after exhausting the
  committed cascade is a **hard fail → red build**. It never searches for,
  generates, or adapts a locator. `healPolicy` is fixed to **NONE**, always.
  Adaptivity is barred by construction, which is what earns the K/K signal (CF6/D6).
- **New IR runtime fields o7 adds (F-B/E2):** `timeoutMs` (per-step bounded wait),
  `syncAfter` (`WAIT_FOR_IDLE | NONE`), `healPolicy` (value fixed to `NONE`), and
  `irDigest` (SHA of the canonical IR). Added to the T05 records.
- **Audit-pin re-base (the F6 amendment — spec.md:88–105).** o1's applicable F6
  pinning set (spec.md:89; echoed in ADR 0006:85) is `{irVersion, codeCommit,
  pipelineVersion, appiumVersion, device/OS/model, appVersion}`. **`irDigest`**
  (SHA of the committed canonical IR) **subsumes both o1 IR/code pins**: it
  replaces `codeCommit` (o7 has no generated code) **and supersedes `irVersion`**
  (the content-addressed digest *is* the version). o7 adds
  **`interpreterVersion`** (the pinned interpreter's Git SHA). The o7 F6 applicable
  set is therefore `{irDigest, interpreterVersion, pipelineVersion, appiumVersion
  (captured, not pinned), device/OS/model, appVersion}` — `codeCommit` **and**
  `irVersion` are both removed. Perfecto server/driver versions are captured
  as **evidence, not pinned**: Perfecto pins `appiumVersion`/`automationVersion`
  only to major.minor from a curated menu and upgrades drivers on its own
  schedule, so full-stack pinning is impossible — capture the session-reported
  versions (`appiumRequested`/`appiumReported`/`driverReported`), **"pinned per
  epoch, not forever."** Each session additionally attests
  **`cloudAdaptivity.selfHealing = DISABLED`** and **`perfectoAI = DISABLED`** —
  because the cloud injects adaptivity into Appium runs post-2025, and an
  undisabled cloud AI would break determinism. F6's **complete-or-invalid** rule
  is preserved: the pinning *set* changes, the "null/absent is never valid" rule
  does not.
- **M37 amendment — attribution anchor relocated, not weakened (spec.md:158–164).**
  In o1, the individual principal is the human engineer who committed the
  generated code. In o7 the commit is by a **service principal
  `svc:conversion-pipeline`** — a valid M37 per-component service principal, just
  no longer the attribution anchor — and the **individual-principal requirement
  moves to the certification-verdict row**: the section-7 human evaluator certifies
  **post-run**, and *that* row carries the individual principal. The section-7
  evaluator is **re-scoped from "final check" to "attribution anchor."** M37's
  intent (no lineage attribution without an individual principal; the `system`
  catch-all forbidden) is preserved by relocation, not by exception.
- **Review removal (R4 + R2 on the R1 substrate).** The pre-commit engineer review
  is removed. Its correctness residue is owned by the IR gate + dry-run (R1); its
  attribution residue is owned by the post-run verdict (R4). **R2** = novelty-
  sampled review reusing the spec's existing CF4/M21 sampling flag — a **novel
  source shape forces a mandatory review; a known shape is sampled.** This is
  defensible precisely because ADR 0013 already recorded (0013:74–76, 0013:179)
  that per-script human review was never the security control.

**Business justification:**

- **Throughput:** deleting the code-generation and code-review steps removes the
  per-test human tax that ADR 0013 named "genuinely fatal to the system's
  purpose" (0013:74–76), replacing it with a deterministic, zero-device gate.
- **Audit posture:** a bank auditor asking "what exactly ran?" gets "the committed
  IR at this `irDigest`, walked by the interpreter at this `interpreterVersion` —
  both reviewable, both reproducible," rather than "machine-generated Java at this
  `codeCommit` that a human then re-reviewed."
- **Vendor independence:** building the interpreter over Appium/Perfecto avoids the
  analyst-leader lock-in (own device farm) and the Maestro lock-out (bypasses
  Appium) while keeping the bank-fixed Perfecto substrate.
- **D7 (signed in-toto attestation of the ReplayReport)** is named now and built
  later (A-STD): the standard evidence bundle re-based to pin `irDigest` +
  `interpreterVersion` ships now; the cryptographically signed attestation is a
  follow-on, not a Stage-2 deliverable.

## Consequences

- **We now own an interpreter as a maintained product, not a script.** The build
  path's real cost is a conformance corpus, a release cadence, and a named
  maintainer. Unmaintained interpreters die — OpenTest and Selenium IDE are the
  cautionary cases — so the interpreter is **resourced as a product from this
  gate**, with a conformance-corpus release gate (Compliance, below). This is the
  bad-side cost we accept for determinism and audit quality.
- **Amendment to the signed-off spine spec (paired sdd-replan).** This ADR amends,
  not supersedes:
  - **F6 (spec.md:88–105):** `irDigest` subsumes both `codeCommit` and `irVersion`
    (spec.md:89) — the content-addressed digest is the version — and o7 adds
    `interpreterVersion`, so the applicable set becomes `{irDigest,
    interpreterVersion, pipelineVersion, appiumVersion (captured), device/OS/model,
    appVersion}`; `codeCommit` and `irVersion` are both removed. Plus per-session
    `cloudAdaptivity.selfHealing`/`perfectoAI = DISABLED` attestation and
    captured-not-pinned Perfecto `appiumReported`/`driverReported` evidence; the
    complete-or-invalid rule is unchanged.
  - **M37 (spec.md:158–164):** certification-verdict attribution moves to the
    verdict row (section-7 evaluator, post-run); commit is `svc:conversion-pipeline`.
  - **Replay-pipeline-v1 row (spec.md:65):** `static gate → IR gate`;
    `device gate (TestNG, pinned Appium) → interpreter walks committed IR on
    Appium/Perfecto`; classification and `ReplayReport` emission unchanged in
    shape, re-based in pins. The classification taxonomy
    (`LOCATOR_NOT_FOUND, STALE_ELEMENT, TIMEOUT_SYNC, ASSERTION_MISMATCH,
    APP_CRASH, DATA_PRECONDITION, ENV_INFRA`) is **unchanged and still
    deterministic/rule-based** (T35).
  - **Tasks:** T02 (add the no-per-test-Java ArchUnit rule), T05 (add
    `timeoutMs`/`syncAfter`/`healPolicy`/`irDigest`), T07 (re-base F6 validation),
    T30 (static gate → IR gate), T31–T32 (worker hosts the interpreter, not
    TestNG), T37 (re-based pins), T40 (commit a **reference `TestCaseIR`** instead
    of a hand-written Appium test), T41 (gate clause a: "one hand-written Appium
    test flows end to end" → "the committed reference IR is walked end to end by
    the interpreter").
- **ADR 0013's attack path is largely dissolved, and this is a consequence to
  record, not a control to relax.** There is no per-run-generated code to execute
  at all; the interpreter is fixed, audited, version-pinned code that executes
  committed **data**, not per-run-generated Java. The "execute untrusted generated
  code" path ADR 0013 mitigates is therefore mostly gone. But **the ADR 0013
  credential topology is preserved**: the device-gate worker still holds no
  gateway credential and still runs the interpreter in the committed separate-
  process shape (CF10). o7 strengthens ADR 0013; it does not repeal it.
- **ADR 0001 (F1) is strengthened.** The interpreter is LLM-free by construction —
  it walks committed data — so no model call exists anywhere on the replay path.
  ADR 0009's three call sites are untouched: the interpreter consumes
  already-committed, already-screened IR and adds no new trust boundary. ADR 0012's
  per-conversion hash-chain lineage is unchanged.
- **R5 is barred, and that is a deliberate ceiling on future autonomy.** No future
  work may make the certification verdict fully autonomous on the certified path:
  CF9 (spec.md:386) + M37 (spec.md:158–164) require an individual principal on the
  verdict. The interpreter's PASS is forever a precondition, never a certification.
- **Losing options' trade-offs.** Keeping o1 codegen would have kept an audit
  artifact nobody authored and a review tax ADR 0013 already condemned. Buying an
  analyst-leader would have bought self-heal that fails K-integrity and a device farm
  that locks out Perfecto. A Maestro-style interpreter would have matched the shape
  but bypassed Appium and so could not drive Perfecto. Robot Framework would have
  bought a mature `output.xml` audit artifact but re-introduced a per-test
  generated `.robot` (re-tripping F-B) and still needed the interpreter-product
  wrapper — it survives only as the buy-not-build fallback. A Python/TS interpreter
  would have forked the stack against ADR 0005 for no gain.
- **Downside accepted.** No OSS JSON-IR Appium interpreter exists, so build is the
  evidenced conclusion, not a preference — and building means carrying the product
  cost above. If the interpreter product is ever under-resourced, the recorded
  fallback is Robot Framework (IR → `.robot` over Appium), accepting the F-B
  re-trip as the price of an off-the-shelf maintained runner.
- **Imposes on future work.** No per-test generated Java may enter the o7 pipeline;
  every `ReplayReport`/lineage row carries `irDigest` + `interpreterVersion` (never
  `codeCommit`); the certification-verdict row carries an individual principal;
  every session attests cloud adaptivity disabled; `healPolicy` stays `NONE`; the
  interpreter ships against a conformance corpus each release; R5 stays barred.

## Compliance

- **No-per-test-generated-Java rule (automated, CI-blocking — F-B, T02):** an
  ArchUnit rule that no per-test generated Java/TestNG type exists in the o7
  pipeline — no generated test class, no `@Test`-annotated generated type, no
  codegen output package. The interpreter's own types and the vendored Appium
  java-client are allowlisted (they are not per-test artifacts). A regression fails
  the build.
- **IR gate (automated, CI-blocking, deterministic, pre-device — R1, T30):** the
  seven checks (`schemaValid`, `opcodeClosed`, `boundedWaits`, `locatorManifest`,
  `noLiteralCreds`, `ambiguityClear`, `dryRun`) run before any device is touched;
  any failure quarantines and does not proceed to the interpreter walk. Zero device
  cost by design.
- **Re-based pinning-set schema check (automated, blocking — F6-rebased,
  spec.md:88–105, T07):** every `ReplayReport`/lineage row MUST carry `irDigest`
  **and** `interpreterVersion`, and MUST NOT carry `codeCommit` **or** `irVersion`
  (both subsumed by `irDigest`); a row missing either required pin, or still
  carrying `codeCommit` or `irVersion`, fails schema validation and no verdict is
  recorded. Complete-or-invalid preserved.
- **Cloud-adaptivity-disabled attestation (automated, per session — F6-rebased):**
  each session's `ReplayReport` MUST attest `cloudAdaptivity.selfHealing = DISABLED`
  **and** `perfectoAI = DISABLED`; a run without both attestations, or with either
  enabled, quarantines and records no verdict. Perfecto `appiumReported` /
  `driverReported` are captured as evidence, explicitly not pinned.
  **[Amended 2026-08-09, pre-acceptance]** Each attestation is a **four-state**
  value: `DISABLED` | `ENABLED` | `UNKNOWN` | `NOT_APPLICABLE`.
  - `DISABLED` — provider attests the feature is off. Proceeds.
  - `ENABLED` — provider attests it is on. Quarantines.
  - `UNKNOWN` — no attestation obtainable. **Quarantines**, exactly as `ENABLED`
    does, so the rule above is unchanged in effect. It exists so the record
    distinguishes *"the provider said off"* from *"the provider said nothing"*,
    which a boolean cannot — and **no provider offers per-session cryptographic
    attestation today**, so this is a real operating value, not a theoretical one.
  - `NOT_APPLICABLE` — the adaptivity source is not in the code-path execution
    path. Proceeds, but **only** with a written vendor confirmation on file and
    referenced from the report; unreferenced, it is a schema violation. See
    *Accepted residual risk* below for why this state exists and what it costs.

  Owner decisions 2026-08-09: the four-state shape resolves the o7 spec's
  competing `cloudAdaptivityDisabled` boolean in favour of this ADR's shape
  (next-items I5), and `NOT_APPLICABLE` is the resolution of the
  no-Perfecto-toggle deadlock (next-items I7).
- **Individual-principal on the certification verdict (automated, DB-level — M37,
  spec.md:158–164):** the certification-verdict row is invalid at the database
  level unless it carries an **individual** principal (the section-7 evaluator);
  `svc:conversion-pipeline` is valid on the *commit* row but rejected as the
  verdict-row principal; the `system` catch-all is forbidden on both. This is what
  makes R5 unrepresentable in the schema.
- **`healPolicy = NONE` assertion (automated, per run):** the interpreter refuses
  to start a run whose IR carries any `healPolicy` other than `NONE`; a
  locator-cascade miss after the committed order is exhausted is recorded as a hard
  fail (`LOCATOR_NOT_FOUND`) — never a heal, never a retry-with-search.
- **Conformance-corpus release gate (automated, per interpreter release — product
  resourcing):** the interpreter MUST pass a maintained conformance corpus (the
  closed opcode set × assertion kinds × sync/timeout behaviours) before any release
  is cut; a corpus regression blocks the release. This is the guard against the
  OpenTest/Selenium-IDE failure mode (an interpreter that dies from being
  unmaintained). The corpus is owned and resourced from this gate.
- **Novelty-sampled review (manual, per-conversion cadence — R2, reusing CF4/M21):**
  a **novel source shape** forces a **mandatory** human review before the auto-
  commit is trusted; a **known shape** is **sampled** at the CF4/M21 rate. The
  section-7 evaluator's post-run certification is the always-on individual anchor
  regardless of the sampling outcome. This is the one manual-cadence control; every
  other check above is automated.
- **D7 (named follow-on, not a compliance item yet — A-STD):** a signed in-toto
  attestation of the `ReplayReport`, binding `irDigest` + `interpreterVersion` +
  the captured session evidence under a signature, is a future release gate. Named
  here so the follow-on is not surprised; **not built now.**

  **[2026-08-09] Deferral reaffirmed on evidence, and scoped so it can be picked
  up cold** (external research §6; next-items I8). Adopting D7 today would make o7
  an **early adopter building both the emitter and the verification policy**, not
  a follower of an established practice — the deferral is now a researched
  position rather than an unexamined "later".

  - **Predicate choice is not obvious.** The vetted **Test Result** predicate
    (`https://in-toto.io/attestation/test-result/v0.1`; required `result` ∈
    {PASSED, WARNED, FAILED} and `configuration`, `subject` = the source artifacts
    tested) has had **no substantive change since 2023-05-25** while the
    attestation repo itself ships actively. The **Runtime Trace** predicate
    (`monitor` / `monitoredProcess` / `monitorLog`) is arguably the **better fit**
    for o7, which wants to attest *how the run executed*, not merely its verdict.
    Both sit at **v0.1**, and **no verifier tooling surfaced** — so an emitter
    alone would produce signatures nothing checks.
  - **⚠ Do not claim SLSA compliance for test runs.** SLSA v1.2 defines **Build
    and Source tracks only**. There is no test track. An attestation of a
    `ReplayReport` is not a SLSA artifact and must never be described as one — the
    audit value of this whole design depends on not overstating what a signature
    covers.
  - **What would change the answer:** either predicate reaching v1 with verifier
    tooling, or a hard external requirement for per-session cryptographic
    attestation. The second is already live as an *unmet* requirement — see
    *Accepted residual risk* below, where D7 is named as the closure path for a
    gap that (b) post-run assertion only partially covers.
  - **Scoped honestly:** "no established practice found" is a **not-found** across
    the sources reviewed, not a proof of absence.

## Accepted residual risk — cloud-adaptivity attestation (recorded 2026-08-09)

**Recorded, not papered over**, per the external research §6 finding. Owner
decision 2026-08-09 (next-items plan I7).

**The gap.** Neither Perfecto nor BrowserStack documents any signed or
cryptographically verifiable per-session attestation that cloud AI / self-healing
was off. *Scoped honestly: this is an absence across the pages reviewed, not an
exhaustive proof.* For **Perfecto specifically** — the only cloud these specs name
— self-healing is documented as a **Scriptless product feature**, there is **no
code-path AI toggle**, and therefore **no toggle to attest at all**.

**What is NOT at risk.** Interpreter-side self-heal is structurally excluded, not
merely attested: `healPolicy` is fixed `NONE` and an exhausted committed locator
cascade is a hard fail (o7 spec:98, :135). That half is fully under our control.
The residual risk is **only** cloud-side injection into the Appium session.

**Posture accepted: (b), with (c) as the named escalation.**
- **(b) Post-run assertion — the operating posture.** Each run asserts from its
  own evidence that no cloud healing occurred (`healsApplied: NONE`, plus absence
  of healed-locator markers in the session log). **This is evidence of absence,
  not a signed guarantee, and is recorded as such.** It is defeasible: a vendor
  that healed silently and logged nothing would pass it.
- **(c) Self-hosted Appium — the named escalation, not adopted now.** The only
  option that actually satisfies H10 as written. Adopting it would give up
  Perfecto's real-device lab, which these specs name as the device path (C5 epoch
  rule, captured Perfecto evidence) — so it is an **sdd-replan event**, not a
  configuration change. Escalate if the vendor answer is unsatisfactory or any
  determinism break is observed.
- **(a) Capability echo — rejected.** Perfecto exposes no such toggle, so for the
  named cloud it would echo nothing.

**Fourth attestation state: `NOT_APPLICABLE`.** Because Perfecto offers no toggle,
`perfectoAI` could otherwise never reach `DISABLED`, and the quarantine rule above
would quarantine **every** run — a gate that never opens rather than a risk
accepted. `cloudAdaptivity.*` therefore admits a fourth value, reusing the spine's
existing `PinnedValue` vocabulary (`{REAL, NOT_APPLICABLE, UNPINNABLE_PHASE1}`)
rather than inventing one:

> **`NOT_APPLICABLE`** — this adaptivity source is not in the code-path execution
> path. **Valid only where a written vendor confirmation is on file and
> referenced from the report.** Absent that reference the value is `UNKNOWN`, and
> `UNKNOWN` quarantines. `NOT_APPLICABLE` is *not* an engineer's judgement call
> and *not* a default — an unreferenced `NOT_APPLICABLE` is a schema violation.

**Open dependency.** The written confirmation does not exist yet: Perfecto must
state that Scriptless self-healing does not touch code-path Appium sessions.
Until it does, `perfectoAI = UNKNOWN` and runs quarantine. **This question is
folded into the already-open Perfecto vendor contact** (next-items I6, the Appium
3 real-device question) — one channel, two questions.

**What this acceptance does not do.** It does not make H10 satisfied; it records
precisely how far short of H10 the evidence falls and what would close it. The
in-toto signed-attestation follow-on (D7, above) remains the eventual closure
path and is still not built.

## Notes

Author: sdd-spec (SDD Stage 2), from the o7 interpreter brainstorm (2026-08-05).
Records the R-YES overturn (the o7 fork's founding decision); the confirmed design
bundle (F-B / E2 / H-SB / C-MIG / R-YES / A-STD / R4+R2 on an R1 substrate, R5
barred) is owner-approved 2026-08-05 and is not re-litigated here.
Date: 2026-08-05 (drafted).
Approved by / date: pending — awaits the owner's SDD Stage-2 gate.
Superseded date: — (supersedes no ADR; amends the spine spec — see Consequences +
the paired sdd-replan).
Cross-references: ADR 0001 (F1 no-model-call seam — strengthened), ADR 0005
(Spring Boot modular monolith — H-SB inherits the stack), ADR 0009 (screening call
sites — no new trust boundary), ADR 0012 (hash-chain lineage — unchanged), ADR
0013 (generated-code execution isolation — attack path dissolved, credential
topology preserved; the 0013:74–76 / 0013:179 precedent that per-script review was
never the control), ADR 0015 (spec-amendment landing pattern). Spine-spec anchors:
F6 spec.md:88–105; M37 spec.md:158–164; replay-pipeline-v1 spec.md:65; CF9
spec.md:386; CF8 spec.md:385 (vault-key indirection); CF10 spec.md:387
(separate-process shape).
Last modified / by / what: 2026-08-05 / sdd-spec (SDD Stage 2) / initial draft —
Status Proposed, awaiting the owner's Stage-2 gate.
