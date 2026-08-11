---
applyTo: "**/*.java,**/build.gradle*,**/pom.xml,**/db/migration/**"
description: o1 pipeline coding rules (ADR-anchored). Full catalog with trade-off justifications at docs/coding-rules/rules-catalog.md.
---

# o1 Coding Rules (Copilot condensed)

These 18 rules are binding for all Java code in this workspace. They are the
condensed form of `docs/coding-rules/rules-catalog.md` — read that catalog
for the trade-off justification, pattern/anti-pattern examples, and the
ADR-vs-book override table. Precedence: ADR > catalog > Clean Architecture
book advice. Rules marked **[CI]** are (or must be) enforced by ArchUnit /
migration checks — if you can violate one without a red build, flag the
missing gate. When reviewing, cite rule IDs (e.g., `CR-05`) in findings,
and verify behavior, not just shape: an adapter that never invokes its
collaborator, hardcoded pinning literals, or a silent no-op on an
audit/evidence path is a finding even when the package placement is
correct. Review reports open with a top-3 triage frame; gap/converge
reports use primary labels missing/partial/contradicts/unrequested with a
structured `Type: <label> (ACn). Severity: <sev>.` header per finding.

**A. Structure**
- **CR-01 [CI]** Cross a module boundary (`conversion`,
  `validation-certification`, `evidence`) only via its published `..api..`
  package. No reach-in to module internals.
- **CR-02 [CI]** No dependency cycles between packages or modules; break
  cycles with DIP the day they appear.
- **CR-03 [CI]** Packages are domain concepts (`ingestion`, `replay`,
  `certification`, `lineage`) plus `api`/`adapter`/`config`. Never
  `controllers`/`services`/`repositories`/`impl`/`util`/`helpers`.
- **CR-04** Types are package-private by default; `public` only for
  published API/DTO/config types with a real external importer.

**B. Seams**
- **CR-05 [CI, load-bearing]** Every model call goes through the Invoke
  Models seam. No provider SDK / Spring AI `ChatClient` / gateway /
  Copilot-specific types outside its adapter package. Prompt assembly,
  egress screening, caching, and pinning capture live behind the seam only.
- **CR-06 [CI, load-bearing]** Only the committed crossing vocabulary
  crosses that seam: `TestCaseIR`, `LocatorCandidate`, `ReplayReport`,
  `ObservationPacket`, `CandidateActionSet`. New crossing type = ADR
  amendment, not a merge. Check both directions: parameter types entering
  the seam and result types leaving it.
- **CR-07 [CI]** Evidence artifacts only via the S3 storage port. No
  S3/MinIO clients elsewhere, no filesystem stopgaps, no artifact payloads
  in the relational store (references + classification + retention date only).
  The adapter must actually perform the store; object keys built from
  model/user-influenced identifiers are a path-injection security finding.
- **CR-08 [CI]** Seams stay Strategy-shaped: interface + config-selected
  impl via Spring DI. No plugin registries or runtime discovery (declined by
  ADR 0005), and no importing an `*Impl`/adapter class directly.
- **CR-09** No provider/source conditionals in core: no `instanceof` on
  adapter types, no branching on provider names. Quirks are absorbed inside
  the adapter; if they can't be, fix the port contract.
- **CR-10** Ports are narrow and consumer-owned: the interface lives with
  its caller, exposes only what that caller uses, named for the need
  (`ProvenanceWriter`), not the technology.

**C. Core purity**
- **CR-11 [CI]** `domain`/`usecase` packages import no Spring, JPA,
  Jackson-annotation, HTTP, or provider types. Constructor injection;
  all wiring in `@Configuration` classes at the composition root.
- **CR-12 [CI-partial]** Only simple DTOs (records) cross boundaries.
  Never JPA entities outward, `ResultSet` rows or `HttpServletRequest`
  inward, and never one type serving as both entity and request model. No
  null-as-domain-signal across boundaries — use Optional or a typed result.
- **CR-13** Controllers/CLIs/listeners are humble: validate shape → map →
  call one use case → map back. No business decisions at the edge.

**D. Data & flow**
- **CR-14 [CI-partial]** Lineage writes are synchronous, in the same local
  transaction as the state change, full pinning set, lineage schema only.
  No cross-lifecycle foreign keys in either direction. Silent no-op lineage
  writes are findings (stub discipline on the audit path).
- **CR-15 [CI-partial]** Async exists at exactly two seams (conversion →
  device replay, conversion → human decisions) via transactional outbox +
  idempotent consumers. Any new queue/`@Async`/event bus needs a
  superseding ADR.
- **CR-16 (security)** The model proposes; determinism disposes. LLM output
  gets no execution authority, trust status, or permanence without a
  deterministic versioned gate. Generated code runs credential-isolated in a
  separate process after static capability checks. Every model call captures
  pinning fields (`UNPINNABLE_PHASE1` where impossible — never blank).
  Exact-match gates live as a versioned static factory on the committed
  enum (separate gate class only when rules exceed membership); rejections
  are always recorded, never silently dropped. Simplification is additive:
  folding machinery together never drops gate versioning, pinning capture,
  rejection recording, or cycle-freedom — and least machinery never
  licenses a package cycle (check a port's existing imports before
  depending on it directly). Captured pinning fields must reach the
  persisted provenance record, not stop in an in-memory DTO.

**E. Tests & metrics**
- **CR-17** Test through the module's published API (or explicit test API);
  no 1:1 test-class-per-impl-class mirroring of core logic; no
  `@SpringBootTest` for pure logic; production code never references test
  code.
- **CR-18** Method cyclomatic complexity ≤ 10 hard (≤ 5 target in core and
  edge classes); package Distance-from-main-sequence < 0.3 as an alarmed
  trend. Raising a threshold is a recorded decision, never a constant edit.
