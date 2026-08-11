---
type: architecture
title: Architecture characteristics worksheet — Mobile Test Automation LLM Pipeline
description: 'Stage-1 (arch-characteristics) worksheet for the mobile-test-automation target, revision 3 with the gate closed: seven driving characteristics with objective definitions, measures and caveat classes, the confirmed top-3 (reproducibility, security & privacy, verifiability), six tension pairs, an elimination probe, the three clusters handed to stage 3, and the adjudication of the critical re-review.'
tags: [architecture, mobile-test-automation, arch-characteristics, kata]
---

# Architecture Characteristics Worksheet — Mobile Test Automation LLM Pipeline

- **Target:** mobile-test-automation
- **Artifact home:** `docs/architecture/` (per the `[roots]` override in `.arch/binding.toml`; the katas archived under `.arch/` are unaffected)
- **Stage:** 1 (arch-characteristics)
- **Mode:** kata (premises = research synthesis + blueprint v2 + compass artifact; domain knowledge flagged where used)
- **Date:** 2026-07-26
- **Status:** REVISION 3 — **gate CLOSED 2026-07-26.** Rev 2's driving set survives unchanged; the gate decisions changed the top-3 ordering (§7), relabeled cluster B (§10), and added one tension pair (§8).
- **Revision driver:** v1 promised model-level determinism the platform cannot deliver, delegated security outside the system's actual trust boundary, and committed to output targets the research explicitly rejected. Full adjudication in §9. Rev 3 records the gate decisions in §11.

---

## 1. Domain ingest

Sources: `docs/research/mobile-test-automation-brainstorm.md`, `docs/research/blueprint-revision-v2.md`,
`docs/research/compass_artifact_wf-d19f43b7-e322-5052-814e-7ba2d0682adb_text_markdown.md`.

**Problem.** Human testers execute manual test scripts against native iOS/Android apps on a Perfecto
Mobile device lab. Manual assets live in ALM Octane, OpenText ALM/QC, and Excel. The system converts
those assets into portable, auditable, version-controlled Appium 2 (Java/TestNG) tests, certifies
them, and admits them to the regression suite.

**Load-bearing constraints, quoted.**

> "the team is Java/Spring Boot" — the runtime is a Spring Boot modular monolith.

> "models come through Orchestrator AI ... no direct model vendor SDKs anywhere."

> "Phase 1 is not a throwaway prototype, it is the asset factory and data flywheel for Phase 2."

> "The replay pipeline is boring on purpose ... LLM output never touches it; it only consumes committed code."

> "Device hardware is the one nondeterministic input."

> "No PII/secrets in prompts (reference vault keys in IR `test_data`) ... prompt-injection screening of
> ingested test content (test steps are untrusted input); full audit trail."

**Domain fact that shapes everything below (flagged as domain knowledge):** this is a banking/fintech
context. That makes evidence, attribution, and data protection structural obligations rather than
operational hygiene.

---

## 2. Candidate extraction

Per `IdentifyingArchChar.md:10` — three sources. Each candidate marked `explicit` (stated) or
`implicit` (necessary but unstated, with the implying fact named).

| Candidate | Source | Origin |
|---|---|---|
| Reproducibility of validation | explicit | "Replay should be deterministic pipeline"; "pinned tool versions recorded in every report" |
| Security & privacy | explicit | vault-key test data; prompt-injection screening; on-prem/VPC LLM; secure-field screenshot blocking |
| Auditability / traceability | explicit | `provenance` field "raw source refs for audit"; "full audit trail (source → IR → code → runs) for the fintech compliance context" |
| Replaceability of the reasoning engine | explicit | Phase 1 Copilot → Phase 2 Orchestrator AI; "one adapter class implements the interface" |
| Interoperability | explicit | Octane REST, ALM/QC REST, Excel POI, Perfecto, gateway, object repository |
| Verifiability of generated output | explicit | certification thresholds; "nothing lands without passing objective gates"; judge calibrated to TPR/TNR > 90% |
| Reliability / recoverability | explicit | "per-test persistence, so an interrupted batch resumes"; bounded loops (3 static repairs, 3 device retries); `ENV_INFRA` re-queue |
| Testability of the pipeline itself | implicit | a pipeline that gates other tests must itself be trustworthy |
| Performance / latency | explicit | "generation time < 30s per test case"; gateway latency risk |
| Cost efficiency | explicit | "device minutes dominate cost" is a named decision trigger |
| Scalability | implicit | batch conversion of a legacy manual suite is bounded, not open-ended growth |
| Elasticity | implicit | no burst-shaped external traffic; conversion is an internal batch workload |
| Maintainability | explicit | prompt/schema/agent changes must not cascade |
| Observability | explicit | OpenTelemetry with LLM spans exported to Langfuse |

---

## 3. Three-part test

Test per `ArchitecturalChar.md:19-43`: (a) nondomain, (b) requires **structural** support,
(c) critical to success.

| Candidate | (a) | (b) | (c) | Disposition |
|---|---|---|---|---|
| Reproducibility | yes | yes — forces an LLM-free validation boundary, pinning, provenance capture, cache semantics | yes | **Driving** |
| Security & privacy | yes | yes — secret indirection in the IR schema, an input-screening boundary, artifact classification, restricted repository writes | yes | **Driving** |
| Evolvability / replaceability | yes | yes — single model boundary, schema spine, Phase-1-assets-as-Phase-2-artifacts | yes | **Driving** |
| Reliability & recoverability | yes | yes — checkpoint/resume state, bounded loops, infra-vs-defect separation | yes | **Driving** |
| Auditability & traceability | yes | yes — lineage store, immutability, attribution of human decisions | yes | **Driving** |
| Interoperability | yes | yes — adapter seams per source system and per external platform | yes | **Driving** |
| Verifiability | yes | yes — tiered gates as first-class components, judge calibration, HITL routing | yes | **Driving** |
| Testability (of the pipeline) | yes | partial — served by the same seams verifiability and evolvability already demand | yes | **Demoted to design** — no additional structure beyond the model boundary + schema contracts |
| Observability | yes | partial — tracing is instrumentation on existing components | yes | **Demoted to design**; its audit-grade subset is absorbed by auditability |
| Maintainability | yes | partial — realized by the same schema spine and model boundary evolvability creates | yes | **Merged into evolvability** — no distinct structure |
| Performance / latency | yes | no — a 30s generation budget and gateway latency are satisfied by async work and caching | moderate | **Demoted to design** |
| Cost efficiency | yes | no — the tiered gate ordering is a design/sequencing choice, not a new structure | yes | **Demoted to design**, tracked as a fitness function |
| Scalability | yes | no | no | **Others considered** — bounded batch, not growth-shaped |
| Elasticity | yes | no | no | **Others considered** — no burst-shaped demand |

**Why testability's demotion is honest but uncomfortable:** a pipeline that certifies other tests
should be exceptionally well tested. The demotion says only that no *additional* structure is needed —
the model boundary makes the LLM mockable and the schema contracts make each stage independently
exercisable. It stays on the elimination watchlist in §7.

---

## 4. Composite decomposition

`MeasuringAndGoverning.md:24` — composites have no direct measure.

**"Determinism" (v1's top characteristic) was a false composite and is retired.** It bundled three
different claims with three different owners:

| Claim | Owner | Achievable? |
|---|---|---|
| Same committed code, re-validated, yields the same recorded verdict | validation pipeline | Yes — this is what the blueprint actually specifies |
| Same input + prompt version yields the same generated artifact | response cache | Yes **on cache hit only** — this is idempotence, not model determinism |
| The model itself returns byte-identical output | Orchestrator AI | **No** — temperature 0 and seeds reduce variance; they do not guarantee byte-identical output, and the source itself names model deprecation as an out-of-team-control risk |

Replaced by **Reproducibility**, defined over evidence rather than over model behavior. Team language
("deterministic replay") is preserved as the ubiquitous term for the validation pipeline.

**"Maintainability"** decomposed into modifiability of prompts/schemas (→ evolvability) and
diagnosability (→ auditability). No residue justifies a separate driver.

---

## 5. Driving characteristics — definitions and measures

Each measure names its type (operational / structural / process) and its caveat class.

### 1. Reproducibility *(team language: "deterministic replay")*

**Definition.** Any certification verdict can be reconstructed and re-derived from recorded inputs:
committed code, pinned tool versions, identified prompt/model versions, and captured device context.
Generation stability and execution repeatability are measured separately and never averaged together.

**Measures.**
- *Structural:* 100% of certification verdicts carry complete pinning — `irVersion`, `codeCommit`,
  `pipelineVersion`, `appiumVersion`, device/OS/model, `appVersion`, prompt version, **and model/provider
  version**.
- *Operational (execution repeatability):* K/K device passes with zero flakiness across K runs
  (K=3 conversion, K=5 certification), `ENV_INFRA` excluded and reported separately.
- *Operational (generation stability):* on cache hit, byte-identical artifact 100% of the time; on
  cache miss, re-generation produces a certification-equivalent artifact — report the rate, do not
  assume it.

**Caveat class.** The `ENV_INFRA` exclusion is gameable: over-classifying real defects as
infrastructure inflates repeatability. Audit the infra-classification rate as its own trend. Report
max variance alongside the mean — averages hide the flaky device in the pool.

### 2. Security & Privacy

**Definition.** Secrets and PII never enter prompts, logs, generated code, or retained artifacts;
ingested manual-test content is treated as untrusted input; access to the device lab, source systems,
and the object repository is least-privilege and attributable.

**Measures.**
- *Structural:* 100% of test data referenced by vault key, never literal value, enforced at the IR schema.
- *Operational:* zero secret/PII detections in prompt payloads, traces, and stored artifacts (automated
  detector on every egress).
- *Operational:* 100% of ingested source text passes injection screening before reaching any model;
  screening measured against a maintained red-team corpus, reporting bypass rate.
- *Structural:* every device artifact (video, page source, network capture, screenshot) carries a data
  classification and a bounded retention.

**Caveat class.** Detector-based measures give false confidence — an undetected class reads as zero.
Pair the detector with periodic manual sampling of stored prompts and artifacts.

### 3. Evolvability / Replaceability

**Definition.** The reasoning engine can be replaced (Copilot → Orchestrator AI → a future provider)
and source systems added, without modifying the IR, the validation pipeline, or the certification gates.

**Measures.**
- *Structural:* Phase 2 cutover touches zero files in the replay and certification modules, and zero
  fields of `TestCaseIR` / `LocatorCandidate` / `ReplayReport`.
- *Structural:* a provider swap touches only the model-boundary adapter — files changed outside it = 0.
- *Structural:* a new source adapter changes no conversion or validation code; each adapter has its own
  contract test.
- *Process:* at cutover, Phase 2 certification rate on the Phase 1 golden set ≥ Phase 1 certification rate.

**Caveat class.** "Files changed" is gameable by hiding coupling in configuration. Pair with the
golden-set parity run, which fails if behavior actually moved.

### 4. Reliability & Recoverability

**Definition.** An interrupted or partially failed conversion batch resumes without repeating device
work; repair and retry loops are bounded; infrastructure failures never masquerade as defects.

**Measures.**
- *Operational:* interrupted batch resumes with zero duplicated device runs and zero lost conversions.
- *Structural:* loop bounds enforced in code — 3 static repairs, 3 device retries, then the human queue.
- *Operational:* zero heal attempts triggered by `ENV_INFRA`.
- *Operational:* gateway rate-limit and deprecation events absorbed at a single choke point; measure
  retry success rate and unhandled-failure count.

**Caveat class.** A high overall completion rate can hide a subpopulation that always fails. Report
completion by source system and screen family, not just in aggregate.

### 5. Auditability & Traceability

**Definition.** For any certified test, the full lineage is reconstructable and attributable:
source asset → IR → prompt and model version → generated code commit → run artifacts → every human
decision, with identity and timestamp.

**Measures.**
- *Structural:* 100% lineage completeness on sampled certified tests — no missing link in the chain.
- *Structural:* every human approval, override, and correction attributable to an identity.
- *Operational:* an auditor reconstructs a sampled certification verdict from stored evidence alone,
  without access to the running system: 100% success on sample.
- *Structural:* evidence is append-only and tamper-evident.

**Caveat class.** Retention policy and completeness pull against each other, and against privacy —
see the tension table.

### 6. Interoperability

**Definition.** Ease of integrating source systems and external platforms through published contracts.
*(Disambiguation: interoperability = ease of integration via published interfaces; compatibility =
adherence to industry standards. This system needs the former.)*

**Measures.**
- *Structural:* contract tests green for each source adapter (Excel first, then Octane, then ALM/QC).
- *Structural:* Perfecto and the model gateway each sit behind exactly one abstraction; a vendor API
  change touches only that abstraction.
- *Structural:* Perfecto AI extension commands (`perfecto:ai:validation`, `perfecto:ai:user-action`) are
  emitted through a single abstraction, so a platform change does not sweep generated tests.

**Caveat class.** Counting adapters rewards breadth over depth. The Excel adapter is explicitly the
least deterministic input; a green contract test does not mean the messy real workbook parses.

### 7. Verifiability

**Definition.** No generated test enters the regression suite without passing objective gates, and the
subjective gate (semantic fidelity) is itself calibrated before it is trusted.

**Measures.**
- *Structural:* admission requires the conjunction of: compiles and passes static rules; K/K device
  passes on all target platforms; semantic-fidelity PASS; all locators above the confidence floor;
  zero flakiness in the K runs.
- *Process:* the fidelity judge is calibrated against a human-labeled held-out set to TPR and TNR > 90%
  **before** it gates anything.
- *Operational:* first-replay pass rate ≥ 60% (roadmap gate); below 40% triggers the accessibility-ID
  investment decision instead of more tuning.
- *Operational:* static gate catch rate — share of rejected generations stopped before device time.
- *Operational:* locator stability ≥ 85% surviving two app versions; semantic fidelity ≥ 95% of steps.

**Caveat class.** Code-coverage-style measures on generated tests are gamed by assertion-free tests;
fidelity is the anti-gaming measure and must not be relaxed to hit throughput. Judge calibration decays
as the model changes — recalibrate on every gateway model change.

---

## 6. Others considered

- **Scalability, elasticity** — the workload is a bounded internal batch over an existing manual suite,
  not open-ended user growth or burst traffic. Fails (c).
- **Performance / latency** — real (30s generation budget, gateway latency) but satisfied by async
  processing and caching. Demoted to design; tracked as a fitness function, not a driver.
- **Cost efficiency** — genuinely critical, but the remedy is gate *ordering* (static before device),
  which the tiered-validation design already encodes. Demoted to design; "device minutes dominate cost"
  remains a decision trigger.
- **Observability** — instrumentation on existing components; its audit-grade subset is inside
  auditability.
- **Testability** — demoted to design, on the elimination watchlist.
- **Usability of the human-review queue** — real operational concern, not architecturally structural.

---

## 7. Confirmed top 3, and the elimination probe

**Top 3 (unordered, as the gate requires) — confirmed at the gate on 2026-07-26:**

1. **Reproducibility** — it is the constraint that draws the system's most important internal boundary:
   the replay pipeline consumes only committed code. Every other decision inherits that line.
2. **Security & Privacy** — banking context; it changes the IR schema (vault keys), adds a trust
   boundary for untrusted manual-test text, and constrains artifact retention. It cannot be delegated
   to the gateway, which only mediates model calls.
3. **Verifiability** — the system's purpose. Nothing lands without passing objective gates, and the one
   subjective gate is calibrated before it is trusted.

**Evolvability / Replaceability was displaced from the top 3 and remains driving.** The reasoning is the
tiebreaker asymmetry, not a downgrade of its importance:

> Top-3 membership is the rule that settles conflicts *between* characteristics. It is therefore worth
> something only when the opponent ranks lower.

| | Verifiability | Evolvability / Replaceability |
|---|---|---|
| Its real adversary | Cost efficiency and throughput | Reproducibility |
| Where that adversary ranks | **Outside** the top 3 (both demoted to design, §6) | **Inside** the top 3 |
| Can rank settle the fight? | Yes — rank is the only thing that outranks delivery pressure | No — two top-3 members cannot be ordered by rank; handled by the §8 tension entry instead |
| Failure mode if it loses | Pass-ratio thresholds slide under schedule pressure; the source calls this "determinism theater" | Phase 1 becomes the throwaway prototype the blueprint forbids |
| Retrofit cost if under-built | Additive — a gate can be tightened at any time without restructuring | Structural — the model boundary and IR shape are cheap now, expensive once Phase 1 assets exist |

**The counter-argument, recorded because it is strong.** Evolvability demands the expensive-to-retrofit
kind of structure and Verifiability demands the additive kind, which is the classic last-responsible-moment
argument for the rev-2 ordering. The gate weighed gate erosion under delivery pressure as the larger live
risk than the Phase 2 cutover, and chose accordingly. Reasonable stakeholders could rank this differently.

**Compensating control (gate condition, not optional).** Because Evolvability lost its rank, it is
protected structurally instead: **Stage 4 must produce an ADR on the model boundary** — Invoke Models as
the sole model-call seam, with the Phase 1 → Phase 2 swap surface, the IR spine's stability guarantee, and
the "files changed outside the adapter = 0" measure as its Compliance section. The ADR is the protection
that rank would otherwise have supplied. Carried to Stage 4 as **ADR-1**.

> **Update after the Stage 3 gate (2026-07-26).** Stage 3 proposed realizing this control as a *microkernel
> plug-in seam*, which would have made the boundary architectural. **The gate declined the hybridization**
> in favour of a plain modular monolith, on the defensible grounds that a registry is unwarranted machinery
> for one week-3 adapter. The consequence for this characteristic is direct and should not be softened:
> ADR-1 plus fitness functions **F1** (no provider SDK outside the adapter) and **F2** (no source-system
> type leaves an adapter) are now the *entire* protection for Evolvability — there is no runtime seam
> behind them. F1 and F2 are build-time dependency rules (ArchUnit or equivalent) that live only in CI:
> if they are not built and maintained, this characteristic has no protection at all. See
> `style-decision.md` §5, §7, and §9.

**Elimination probe — if one driver had to go, which?** **Interoperability.** The roadmap is
Excel-first and needs exactly one adapter at week 3; adapters are additive behind a stable IR. The cost
of dropping it is rework only if the IR turns out to be source-shaped rather than domain-shaped.
Security, reproducibility, and auditability cannot be dropped — regulatory. Evolvability cannot be
dropped — it is the program premise. Verifiability cannot be dropped — without it the output is
unusable.

---

## 8. Tension pairs

| Tension | Nature | Handling |
|---|---|---|
| **Security ↔ Verifiability** | Banking apps blank screenshots on secure screens (`isSecureTextEntry`, `FLAG_SECURE`), destroying the visual evidence element resolution wants | Hierarchy-based locators are primary; flag screens where vision is unavailable; never weaken the secure-field protection to improve grounding |
| **Auditability ↔ Security/Privacy** | A complete audit trail wants to retain video, page source, and network captures — exactly the artifacts likeliest to contain PII | Classify and redact at capture, retain references plus redacted evidence, bound retention; completeness of *lineage* is non-negotiable, completeness of *raw artifacts* is not |
| **Reproducibility ↔ Evolvability** | Model and prompt upgrades invalidate cached outputs and shift generation behavior | Version evidence rather than freezing models; budget the prompt-tuning sprint the blueprint already anticipates; recalibrate the judge on every model change |
| **Reproducibility ↔ Cost** | K-run confidence consumes scarce device minutes | Tiered gates: reject statically before spending device time; K=3 for conversion, K=5 only for certification |
| **Verifiability ↔ Throughput** | Gates and human review fight the "median under 2 hours of engineer time" target | Hold the gates, move the effort earlier (better locators, accessibility IDs); do not let pass-ratio thresholds slide, which the source names as "determinism theater". Verifiability's top-3 rank exists to win exactly this fight (§7) |
| **Verifiability ↔ Reproducibility** *(new in rev 3, created by a gate decision)* | The gate decision merged the semantic-fidelity judge into Certify Conversion, so the certification gate now makes a model call. A nondeterministic grader sits inside the component that must issue reproducible verdicts | Record the judge's model and prompt version in the verdict alongside every other pinning field, and treat the fidelity outcome as recorded evidence rather than a re-derivable computation. Recalibration becomes a versioned event in the lineage. **This is a cost knowingly accepted, not a solved problem** — see §10 and Stage 2 §1 |

---

## 9. Adjudication of the critical re-review (v1 → v2)

| Finding | Verdict | Justification |
|---|---|---|
| "Determinism" conflates model behavior with pipeline behavior | **Accepted, recalibrated** | The *characteristic* was correctly identified from an explicit constraint; the *definition and measure* were wrong. v1's "byte-identical output" and "< 0.1% divergence across 1 000 reruns" are both unachievable and, at 1 000 device reruns, in direct conflict with the cost trigger. Retired as a composite (§4), not deleted |
| Security wrongly delegated to Orchestrator AI | **Accepted** | The gateway mediates model calls only. It does not touch ALM credentials, Perfecto tokens, hierarchy dumps, screenshots, test data, or repository writes, and it does not screen untrusted ingested text. Promoted to driving |
| Interoperability committed to rejected output targets | **Accepted** | The research rejects native XCUITest and Espresso ("iOS-only" / "Android-only"); those names appear only as Appium *drivers*. v1's "≥ 3 output generators" measure would have driven structure toward a scope the design excluded. Measure rewritten around adapter contracts |
| Measures arbitrary or gameable | **Accepted in part** | The 99.5% completion target and the 80% unit-coverage target are unsupported and gameable — accepted, replaced with source-grounded numbers. **Rejected:** the claim that 99.5% completion "conflicts with" a 60% first-replay target. Those measure different things (technical completion vs conversion quality); the number was invented, but it was not contradictory |
| Auditability collapsed into observability | **Accepted** | Observability answers "what is happening"; auditability requires attribution, immutability, retention, and reconstruction from evidence alone. Different structure, regulated context |
| Tension pairs and elimination probe missing | **Accepted** | Both are required by the stage instructions. v1 also omitted explicit/implicit marking, an "Others Considered" list, and caveat classes. All added |
| *(new, found while writing §5)* Cache key omits model version | **Accepted** | The source specifies `hash(input + prompt_version)`. Because the same source names model deprecation as an out-of-team-control risk, a gateway model change would silently reuse cached output from a different model, breaking reproducibility invisibly. Model/provider version is now required in the pinning measure |
| *(new)* Worksheet written outside its artifact home | **Accepted** | v1 was written to `.arch/worksheets/mobile-test-automation-characteristics.md`; the convention is `<worksheet_home>/<target>/characteristics-worksheet.md`, which for this target now resolves to `docs/architecture/worksheets/mobile-test-automation/`. Corrected; the misplaced file is removed |

---

## 10. Divergent clusters (quantum input for Stage 3)

One set for the whole system is the named fatal flaw (`ArchCharScope.md:8`). Three clusters, and they
do not average.

| Cluster | Dominant characteristics | Character |
|---|---|---|
| **A — Conversion (LLM-bearing)** | Evolvability, verifiability, security | High change velocity, nondeterministic, human-in-the-loop, provider-dependent |
| **B — Validation & Certification** *(replay LLM-free; certification gate is model-bearing as of rev 3)* | Reproducibility, reliability, auditability, verifiability | Mostly boring and low change velocity, the audit surface and the cost control — but no longer model-free at its exit point |
| **C — Evidence & Provenance** | Auditability, security | System-of-record lifecycle: append-only, retention-governed, outlives both other clusters |

**Rev 3 correction to cluster B's label.** Rev 2 called cluster B "LLM-free." That is no longer accurate.
The Stage 2 gate merged the semantic-fidelity judge into Certify Conversion, which puts a model call
inside cluster B. Rather than leave a label contradicting the component set, the boundary is restated
precisely: **replay** is LLM-free and consumes only committed code, exactly as the blueprint requires;
**certification** now calls the gateway to grade assertion fidelity.

**Two things Stage 3 must confront, not one:**

1. **The phase asymmetry.** In Phase 1, cluster A is performed by humans in an IDE while clusters B and C
   are already automated services. The phase boundary therefore runs *through* cluster A and around B and
   C — which is precisely why the blueprint can promise that Phase 2 changes nothing outside conversion.
   That is a quantum signal, not an implementation detail.
2. **The entanglement the gate decision created.** Because Certify Conversion (cluster B) now calls Invoke
   Models (cluster A) synchronously, B and A can no longer be scoped as independent quanta without B
   inheriting A's nondeterminism, provider dependency, and recalibration cadence — Dynamic Quantum
   Entanglement (`ArchCharScope.md:72-74`). Determination 1 (quantum count) and Determination 3
   (sync vs async) must both address this explicitly. The available mitigations — making the fidelity call
   asynchronous, or grading fidelity in cluster A before certification consumes a recorded result — are
   Stage 3 decisions, deliberately not taken here.

---

## 11. Gate status — CLOSED 2026-07-26

- [x] Driving list confirmed (7 characteristics, §5) — unchanged from rev 2
- [x] Top 3 **reordered**: Verifiability promoted, Evolvability displaced to driving-not-top-3 (§7)
- [x] Demotions accepted (§3, §6 — including testability and cost efficiency)
- [x] Tension handling accepted (§8), with one pair added by a gate decision
- [x] Cluster reading accepted (§10), with cluster B's label corrected

**Decisions recorded at this gate:**

| Decision | Call | Consequence carried forward |
|---|---|---|
| Verifiability vs Evolvability for the third slot | Verifiability promoted | Evolvability protected by a mandatory Stage 4 ADR on the model boundary (**ADR-1**) rather than by rank |
| Semantic-fidelity judge merged into Certify Conversion (Stage 2 gate) | Applied, against recommendation | Cluster B relabeled (§10); new Verifiability ↔ Reproducibility tension (§8); A↔B entanglement is now a mandatory Stage 3 determination and a Stage 4 ADR (**ADR-4**) |
| Cache key omits model/provider version (§9 finding) | Accepted as a defect | Stage 4 ADR (**ADR-2**) |

**Unblocked:** Stage 3 (arch-style) may proceed. Re-entry into this stage is expected if Stage 3's
quantum decision changes the cluster reading in §10.
