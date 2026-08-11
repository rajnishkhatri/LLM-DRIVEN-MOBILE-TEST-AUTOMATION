---
type: reference
title: 'o1 Pipeline Coding Rules — Canonical Catalog'
description: >-
  18 decidable coding rules for the o1 pipeline Java/Spring Boot workspace,
  extracted from cases/coding-rules (Clean Architecture chapters + metrics)
  and specialized to the mobile-test-automation ADRs. Single source of truth
  behind the Claude, Cursor, and Copilot front-ends.
tags: [coding-rules, o1-pipeline, java, spring-boot]
---

# o1 Pipeline Coding Rules — Canonical Catalog

**This is the single source of truth.** The Claude, Cursor, and Copilot
front-ends are thin pointers at this file; never fork rule content into them.

**Hard cap: 18 rules.** Every rule is (a) *decidable* — a reviewer can point
at a line and say violated or not; (b) *anchored* — it serves a named ADR
and/or source chapter; (c) *priced* — its trade-off is stated, not assumed.
A change that adds a rule must remove or merge another, or justify raising
the cap in its own right.

**Precedence: ADR > this catalog > the book.** Where Clean Architecture's
generic advice conflicts with a decided ADR, the ADR wins (see the override
table below). Where this catalog is silent, the book chapters in
`cases/coding-rules/` are advisory background, not rules.

**Binding.** Placeholders (`{{base_package}}`, module/package names, seam
package globs) resolve from the workspace binding — `binding.template.toml`
next to this file, persisted as `[coding-rules]` keys in the target repo's
`.sdd/binding.toml` (or a standalone `.coding-rules.toml`). Defaults assume
ADR 0005's shape: three Gradle/Maven modules `conversion`,
`validation-certification`, `evidence`; the blueprint's five stage names
(ingestion, hierarchy, conversion, replay, certification) live on as
*packages inside* those modules.

---

## How to apply

**Implementing (sdd-implement Stage 6, or any coding task).** Before writing
code in an area, load the rule groups it touches: any new class → A; anything
calling a model, storage, or an external system → B; anything in a `domain`
or `usecase` package → C; anything writing state or lineage → D; every test →
E. The red/green and small-diff discipline stays with sdd-implement — this
catalog only constrains *what shape* the green code may take.
**Simplification is additive, never subtractive:** collapsing machinery
(e.g., folding a gate into its enum) must preserve every rule-justified
property — gate versioning, pinning capture, rejection recording,
cycle-freedom. A smaller diff that drops one of these is a violation, not a
simplification.

**Reviewing (Stage 7 code review, sdd-converge Stages 9–10).** Report
violations as findings tagged with the rule ID (`CR-05`) so gaps classify
mechanically. Mechanical rules (marked **ArchUnit**) should be failing CI,
not review comments — if you find one by eye, the finding is *two* findings:
the violation and the missing/disabled fitness function. Metric rules (CR-18)
are trend signals for converge, not per-diff blockers.

**Shape is necessary, not sufficient.** Structural compliance can certify a
well-shaped no-op — an adapter in the right package holding a client it
never calls. On every seam and audit path, verify *behavior*, not just
location: the adapter actually invokes its collaborator on the documented
path; pinning fields are derived from the prompt registry / gateway
response, never hardcoded literals (decorative pinning is absent pinning);
and a method on an audit/evidence/security path that returns without doing
its work is a finding, not a pass (stub discipline). Storage keys or paths
built from model- or user-influenced identifiers without sanitization are a
security finding, not a style note. Two structural siblings of the same
disease: a published API package with no implementations and no callers is
its own finding (a decorative boundary — the sanctioned doors unused while
side doors carry the traffic), and a framework-annotated codebase with no
composition root and no runnable entry point (a Boot starter without the
Boot plugin or any `@SpringBootApplication`) is structurally non-runnable —
flag it, don't assume someone else wired it.

**Report shape (review mode).** Open with a three-sentence triage frame —
"top 3 to fix now" plus the shape of the remaining debt — before any table;
a tech lead scanning 17 findings needs the frame first. When findings
interlock into one failure story (unrecorded actions → forgotten provenance
→ no-op lineage → unstored evidence), add a one-paragraph synthesis naming
the chain. Surface incidental runtime defects caught in passing (an
unconditional NPE, a guaranteed parse failure) as their own findings —
never bury them in parentheticals.

**Converge reports are routing artifacts.** Use the sdd-converge canonical
vocabulary as the primary label on every gap — `missing` / `partial` /
`contradicts` / `unrequested` — so the report is machine-routable with no
human translation step. Give every finding a structured header line:
`Type: <label> (ACn). Severity: <sev>.` Tag runtime defects `DEFECT` and
convention hits `STANDARDS` as secondary tags: a DEFECT routes to a
different fix-task shape (make it run) than a `contradicts` (redo via the
right mechanism).

**Enforcement channels.** `ArchUnit` = ships as a CI-blocking test (seed code
in `archunit-seeds.md`). `Migration` = schema-migration check. `Review` =
judgment call a human or agent reviewer makes, with the decidable proxy
stated in the rule.

---

## Where the ADRs override the book

| Book says | This workspace does | Why the ADR wins |
|---|---|---|
| "Don't marry the framework" — wrap Spring, keep DI out of sight (`frameworks.md`) | Spring DI **is** the seam mechanism: ADR 0005's gate declined the microkernel because "Spring DI supplies the Strategy seam for free" | Wrapping the wrapper is machinery with no buyer; the calibrated rule is CR-11 — annotations stay out of *core*, not out of the codebase |
| OCP taken to its limit — plugin structure at every variation point | Strategy-shaped **partial** boundaries at exactly two seams; registry machinery is a named, declined alternative with a flip condition (4th source adapter / 2nd concurrent provider) | Full boundaries are expensive (`partial-boundaries.md`); ADR 0001/0005 priced them and chose convention + F1/F2. CR-08 protects what was chosen |
| REP / independent deployability — components as releasable jars | **One deployable**, CI-asserted (ADR 0005 Compliance) | Reproducibility, security, and verifiability all won on "one process, one clock, one transaction boundary"; module seams exist for a *future* extraction, not a present one |
| "The database is a detail" (`database.md`) | The database *engine* is a detail (CR-07, CR-12); the **data topology is architecture** — lifecycle-partitioned schemas, no cross-lifecycle FKs, in-transaction lineage (ADR 0006/0007) | Martin's own caveat: "the data model is architecturally significant." Here retention and audit reconstruction are top-3 characteristics, so schema shape is ADR-governed, not detail |
| YAGNI vs. anticipatory boundaries — architect's judgment call (`partial-boundaries.md`) | The judgment is already exercised: the ADRs enumerate which boundaries exist and at what strength. Adding a speculative seam or eroding a decided one are both violations | Boundary placement is arch-decide's job with a gate and a flip condition — not a per-PR improvisation |

---

## A. Structure — modules and packages

### CR-01 — Cross a module boundary only through its published API

**Rule.** The three modules (`conversion`, `validation-certification`,
`evidence`) may be imported by another module only via their published
interface packages (`{{base_package}}.<module>.api..`). No reach-in to
internals, ever.

**Trade-off.** *Buys:* the future service-based extraction cuts along seams
that already exist in code (ADR 0005's named migration path), and module
tests stay buildable in isolation. *Costs:* API packages need deliberate
design; some calls take one more hop. *Verdict:* this is the entire
structural residue of the declined microkernel — losing it silently converts
the modular monolith into the layered sinkhole the style warns against.

**Anchor.** ADR 0005 (Compliance: "imported only via their published
interface packages"); `component-cohesion.md`, `component-coupling.md`.

**Pattern.** `evidence` exposes `evidence.api.ProvenanceWriter`;
`conversion` code imports only `..evidence.api..` types.
**Anti-pattern.** `import {{base_package}}.evidence.lineage.LineageRowMapper;`
from inside `conversion` — compiles fine, and the extraction seam is gone.

**Enforcement.** ArchUnit (seed A-1), CI-blocking. Quarterly
boundary-violation trend review per ADR 0005 cadence.

### CR-02 — No dependency cycles between packages or modules

**Rule.** The package and module dependency graphs are DAGs. A cycle is
broken the day it appears — by DIP (interface in the depended-on side) or by
extracting the shared piece — never waived.

**Trade-off.** *Buys:* buildable, testable, independently reasoned-about
slices; without it, entangled packages become "one large component" and
every module test drags the world in (`component-coupling.md`, the
morning-after syndrome). *Costs:* occasional extra interface or a new
package when a cycle must be cut. *Verdict:* cheapest structural rule per
unit of protection; cycles are also the one decay mode that gets strictly
harder to fix with time.

**Anchor.** `component-coupling.md` (ADP, and the two documented
cycle-breaking mechanisms); ADR 0005.

**Pattern.** `certification` needs a hook into `replay` → define the
interface in `certification`, implement it in `replay` (dependency inverted,
cycle gone).
**Anti-pattern.** `replay` imports `certification` "just for one enum."

**Enforcement.** ArchUnit slices (seed A-2), CI-blocking.

### CR-03 — Packages scream the pipeline domain, never the technical layer

**Rule.** Package names inside modules are domain concepts — `ingestion`,
`hierarchy`, `conversion`, `replay`, `certification`, `lineage` — plus the
sanctioned edges `api`, `adapter`, `config`. Forbidden as package names:
`controllers`, `services`, `repositories`, `impl`, `util`, `helpers`,
`managers`, or any layer-first top level.

**Trade-off.** *Buys:* a new reader learns *what the system does* from the
tree (`screaming-architecture.md`); change-sets cluster inside one package
because closure follows the domain, not the layer (CCP). *Costs:* Spring
tutorials and IDE templates fight you; some genuinely shared plumbing needs
a deliberate home instead of `util`. *Verdict:* ADR 0005's stage explicitly
*corrected* the blueprint away from technical partitioning — the layered
Architecture Sinkhole is this system's named failure mode, and layer-named
packages are its first symptom.

**Anchor.** ADR 0005 (the correction); `screaming-architecture.md`,
`package.md` (package-by-component).

**Pattern.** `{{base_package}}.conversion.replay.ReplayReport` — the path
reads as the domain.
**Anti-pattern.** `{{base_package}}.services.ReplayService` +
`{{base_package}}.repositories.ReplayRepository` — two layers, zero domain.

**Enforcement.** ArchUnit naming guard (seed A-3), CI-blocking for the
forbidden names; Review for whether a new domain package name earns its
place.

### CR-04 — Package-private by default; `public` means published

**Rule.** A type is `public` only if something outside its package
legitimately imports it (API types, crossing DTOs, config classes). Default
everything else — especially implementations behind an interface — to
package-private.

**Trade-off.** *Buys:* the compiler enforces the architecture instead of
review discipline — with everything public, "all four architectural
approaches are exactly the same" (`package.md`); fewer public types = fewer
possible dependencies = cheaper CR-01/CR-02. *Costs:* test classes must
live in the same package (they should anyway, CR-17), and Spring component
scanning needs package-private-friendly wiring (constructor injection via
config classes handles it). *Verdict:* free encapsulation from the language;
the only reason it's rare is muscle memory.

**Anchor.** `package.md` ("overly liberal use of the public access
modifier"; lean on the compiler, not post-hoc tooling).

**Pattern.** `public interface LocatorScorer` in `..certification.api`;
`class WeightedLocatorScorer implements LocatorScorer` package-private next
to it, exported only through config.
**Anti-pattern.** `public class WeightedLocatorScorer` — now any package can
`new` it and the interface is decoration.

**Enforcement.** Review (decidable: is there an importer outside the
package? If not, the `public` is unjustified). ArchUnit partial guard for
`*Impl`/adapter classes (seed A-4).

---

## B. Seams — the convention-protected boundaries

### CR-05 — Every model call goes through the Invoke Models seam

**Rule.** No type outside the Invoke Models adapter package
(`{{seam.invoke_models_adapter}}`) references a provider SDK, gateway
client (Spring AI `ChatClient` included), or Copilot-specific construct.
Prompt assembly, egress screening, response caching, and pinning-field
capture live behind the seam — a call site that does any of these itself is
a violation even if it routes the call correctly.

**Trade-off.** *Buys:* the Phase 1 → Phase 2 provider swap stays "a config
change and nothing else" — measurable as *files changed outside the adapter
= 0*; screening/caching/pinning obligations have one enforcement point
instead of N call sites. *Costs:* the seam is a bottleneck for new
model-call features; its interface must be designed, not accreted.
*Verdict:* evolvability was displaced from the top-3 characteristics **on
the condition** that this boundary would protect it; the microkernel that
would have enforced it at runtime was declined. This rule (as F1) is the
entire remaining protection — treat a bypass as an architecture breach, not
a style nit.

**Anchor.** ADR 0001 (F1, load-bearing); `boundaries.md`, `ocp.md`.

**Pattern.** `certification` code calls
`invokeModels.propose(observationPacket)` and receives typed IR back.
**Anti-pattern.** A quick `ChatClient.builder(...)` inside a replay helper
"just for this one classification call." Also: pinning fields filled with
hardcoded literals (`"prompt-v3"`) instead of values derived from the
prompt registry and gateway response — decorative pinning is absent
pinning.

**Enforcement.** ArchUnit F1 (seed B-1), CI-blocking, load-bearing. Any
suppression or deletion of the rule requires a superseding ADR — not a code
review (ADR 0001 Compliance).

### CR-06 — Only the committed crossing vocabulary crosses the seam

**Rule.** The types crossing the Invoke Models seam are exactly the
committed, versioned set: the IR spine (`TestCaseIR`, `LocatorCandidate`,
`ReplayReport`) plus the ASH amendment (`ObservationPacket`,
`CandidateActionSet`). No provider/gateway/Copilot shape leaves the seam; no
source-system type enters it; ingestion emits IR and nothing else. The
inventory covers **both directions** — parameter types entering the seam
and result types leaving it. A port signature that couples to another
package's internal type leaks vocabulary inbound just as an unlisted
result type leaks it outbound; check both halves in review.

**Trade-off.** *Buys:* "every module is swappable as long as the schemas
hold" — the blueprint's own guarantee — plus a single, auditable inventory
of what the LLM can see and emit. *Costs:* new crossing needs = a schema
change plus an ADR amendment (deliberately slow). *Verdict:* the seam is
worthless if arbitrary types tunnel through it; ADR 0014 had to amend ADR
0001 to add two types precisely so the inventory stays *complete* — code
that smuggles a third type past it defeats the bookkeeping the whole
program's swap premise rests on.

**Anchor.** ADR 0001 (F2 + the 2026-07-31 seam-vocabulary amendment);
`clean-architecture.md` ("which data crosses the boundaries").

**Pattern.** Adapter maps the gateway's response JSON into
`CandidateActionSet` before returning.
**Anti-pattern.** Returning the provider's `ChatResponse` "temporarily," or
passing an ingestion-source DTO into the proposer for "extra context."

**Enforcement.** ArchUnit F2 (seed B-2), CI-blocking. Review for the
completeness half (is a new type crossing? → route to ADR amendment, do not
merge).

### CR-07 — Evidence artifacts exist only behind the storage port

**Rule.** No evidence artifact is read or written except through the
S3-compatible storage port. No S3/MinIO client types outside the port's
adapter package (`{{seam.storage_port_adapter}}`); no filesystem stopgaps;
artifact *payloads* never transit the primary store — the relational side
holds reference + classification + retention date only.

**Trade-off.** *Buys:* the week-0 platform-probe outcome (bank platform
service vs. self-operated MinIO) stays a config change; object-lock
immutability — a precondition of the restore-ordering invariant — is
promised in one contract instead of hoped for at N call sites. *Costs:* one
interface plus a dev/CI MinIO container. *Verdict:* ADR 0011's own framing —
deferring the *binding* is cheap, but skipping the *port* would let a
filesystem stopgap set the retention design by accident. In a bank, evidence
handling is audit posture, not plumbing.

**Anchor.** ADR 0011; ADR 0006 (blob references, never payloads);
`database.md`, `presenters-objects.md` (gateways as humble objects).

**Pattern.** `evidencePort.store(artifact, classification, retainUntil)`
returning a reference the lineage row records.
**Anti-pattern.** `Files.write(Path.of("/tmp/evidence/" + id), bytes)` in a
replay worker, or a `byte[]` column on a conversion-state table. An adapter
that holds the storage client but never invokes it is a Critical behavioral
violation, not a compliant placement; object keys built by concatenating
model- or user-influenced identifiers are a path-injection security
finding.

**Enforcement.** ArchUnit (seed B-3), CI-blocking.

### CR-08 — Keep partial boundaries Strategy-shaped: no registries, no backchannels

**Rule.** The decided seams (Invoke Models, source adapters, storage port)
are interface + config-selected implementation via Spring DI — nothing
selected at runtime, no plugin registry. Two directions of drift are both
violations: *completing* the boundary (registry machinery, runtime
discovery) and *eroding* it (a client importing an `*Impl` directly).

**Trade-off.** *Buys:* the placeholder for a future full boundary at the
cost of one interface (`partial-boundaries.md`'s Strategy option); no
version-tracked plugin contracts for a system with exactly one
implementation per seam. *Costs:* nothing prevents backchannel imports
"other than the diligence and discipline of the developers" — the chapter's
own warning — which is why the ArchUnit guard exists. *Verdict:* the gate
priced both alternatives and declined the registry ("unwarranted machinery
for the one adapter the week-3 gate needs"). Building it anyway re-litigates
a closed decision; eroding the Strategy seam forfeits the compensating
control evolvability was promised. The flip condition (4th source adapter or
2nd concurrent provider) reopens the ADR — code doesn't.

**Anchor.** ADR 0005 (declined microkernel + flip condition), ADR 0001;
`partial-boundaries.md` (Strategy as one-dimensional boundary, FitNesse
decay story).

**Pattern.** `@Configuration` selects `CopilotInvokeModels` vs.
`GatewayInvokeModels` by property; clients know only the interface.
**Anti-pattern.** `if (adapterRegistry.lookup(sourceType) != null)` — a
registry nobody decided; `new PerfectoSourceAdapter()` inside a use case — a
backchannel.

**Enforcement.** ArchUnit (seed B-4: clients of a seam package may not
reference its implementation classes), CI-blocking. Review for
registry-shaped machinery.

### CR-09 — Adapters are substitutable: no provider conditionals in core

**Rule.** Core code never branches on *which* implementation is behind a
port — no `instanceof` on adapter types, no switching on provider/source
names, no reading a config flag to vary business behavior per provider.
Provider quirks are absorbed *inside* the adapter; if they can't be, the
port contract (including its error taxonomy) is wrong — fix the contract.

**Trade-off.** *Buys:* the LSP guarantee that makes CR-05/CR-08 worth
having: a swap that's a config change only stays that way if no core path
secretly depends on the concrete type. *Costs:* adapters get thicker —
normalization, retries, quirk-absorption live there. *Verdict:* the book's
taxi-dispatch story (`lsp.md`) shows the decay: one `startsWith("acme")`
if-statement metastasizes into per-vendor special cases across the codebase.
With a Phase 2 provider swap on the roadmap, every such branch is a future
cutover defect.

**Anchor.** `lsp.md`; ADR 0001 (contract-parity check at cutover is the
system-level LSP test).

**Pattern.** Adapter maps provider timeout → `ModelCallTimeout` from the
port's error taxonomy; core handles `ModelCallTimeout` identically for all
providers.
**Anti-pattern.** `if (props.provider == Provider.COPILOT) { retry(); }` in
certification logic.

**Enforcement.** Review (decidable: grep core packages for adapter type
names, provider enums, `instanceof` on port types — any hit is a finding).

### CR-10 — Ports are narrow and consumer-owned

**Rule.** A port interface lives in the package of the code that *calls* it,
exposes only the operations that consumer uses, and is named for the
consumer's need (`ProvenanceWriter`), not the technology
(`S3ClientWrapper`). No "god" service interfaces aggregating unrelated
operations; a second consumer wanting different operations gets a second
interface, even over the same implementation.

**Trade-off.** *Buys:* depending only on what you use (ISP) — a change to
an operation you don't call can't force you to recompile, re-test, or
re-review; interfaces stay stable because they track a consumer's need, not
an implementation's surface. *Costs:* more, smaller interfaces; an
implementation may implement several. *Verdict:* fat interfaces are how
transitive baggage leaks across the three modules and how the seam
vocabulary (CR-06) erodes one convenience method at a time — "depending on
something that carries baggage that you don't need" (`isp.md`) is precisely
the coupling the module map exists to prevent.

**Anchor.** `isp.md`, `ocp.md` (information hiding); `dip.md` (stable
abstractions).

**Pattern.** `certification` owns `interface JudgeGateway { Verdict
score(ReplayReport r); }` — one method, its need.
**Anti-pattern.** `interface PipelineServices` with 14 methods used by
nobody in full.

**Enforcement.** Review (decidable: does every consumer of the interface use
every method group? Does the interface live with a consumer or in a shared
grab-bag?).

---

## C. Core purity — the Dependency Rule

### CR-11 — Framework-free core; wiring only at the composition root

**Rule.** Packages holding entities and use-case logic (`..domain..`,
`..usecase..`, and each module's inner rule code) import no Spring, JPA,
Jackson-annotation, HTTP, or provider types. Core classes take dependencies
by constructor; `@Configuration` classes at the composition root (Main
component) do all wiring. `@Autowired`/`@Component` sprinkled through core
is a violation even though it works.

**Trade-off.** *Buys:* use-case tests run without Spring context, container,
or database — plain constructors and fakes (`screaming-architecture.md`'s
testability claim, and the in-process gate speed ADR 0005 bought); core code
survives framework major-version churn untouched. *Costs:* config classes to
maintain, and you give up annotation-scanning convenience in exactly the
packages where it's cheapest to give up. *Verdict:* this is the *calibrated*
"don't marry the framework" (`frameworks.md`): Spring stays — it is the seam
mechanism per ADR 0005 — but at the edges. Martin's own example concedes the
point: "use Spring to inject dependencies into your Main component; it's OK
for Main to know about Spring."

**Anchor.** `frameworks.md`, `main-components.md`, `clean-architecture.md`
(Dependency Rule); ADR 0005 (Spring DI as the sanctioned mechanism).

**Pattern.** `class CertificationPolicy { CertificationPolicy(JudgeGateway
judge) {...} }` — no annotations; a `CertificationConfig` builds it.
**Anti-pattern.** `@Service class CertificationPolicy { @Autowired
JudgeGateway judge; }` — core now compiles against Spring, and field
injection defeats the constructor's contract.

**Enforcement.** ArchUnit (seed C-1: no framework imports in core
packages), CI-blocking.

### CR-12 — Simple DTOs cross boundaries — never entities, rows, or framework types

**Rule.** Data crossing any boundary (module API, seam, controller ↔ use
case, use case ↔ gateway) is a simple, dependency-free structure (Java
`record`s are ideal). Never: JPA entities outward, `ResultSet`/row
structures inward, `HttpServletRequest`/transport types inward, or request
DTOs doubling as domain entities "because the fields match today." Outcomes
are typed: returning `null` as a domain signal ("not applicable") across a
boundary is a violation — use `Optional` or a typed result.

**Trade-off.** *Buys:* each side changes independently — the schema can
migrate without breaking the API, the API can version without table surgery;
crossing types are trivially serializable for lineage capture. *Costs:*
mapping code that feels like duplication the week it's written. *Verdict:*
the fields matching today is the trap — entities and crossing models "change
for very different reasons," and welding them violates SRP/CCP at the exact
place ADR 0006 needs freedom: lifecycle-partitioned schemas can't evolve
independently if their row types leak into the IR spine.

**Anchor.** `clean-architecture.md` ("which data crosses"),
`business-rules.md` (request/response models); ADR 0006.

**Pattern.** `record CertifyRequest(String irId, int attempt) {}` in the
API package; mapper in the adapter.
**Anti-pattern.** Controller returns the `LineageRowEntity`; use case takes
`HttpServletRequest`.

**Enforcement.** ArchUnit partial (seed C-2: web/adapter packages may not
reference JPA entity packages and vice versa); Review for DTO/entity
merging.

### CR-13 — Humble adapters at the edges: parse, delegate, format — decide nothing

**Rule.** Controllers, CLI commands, queue listeners, and export writers
(the ADR 0008 surfaces) contain no business decisions: they validate shape,
map to a request model, call one use case, map the response. Anything
worth unit-testing lives behind them.

**Trade-off.** *Buys:* the hard-to-test edge stays too thin to hide bugs;
business rules get tested without HTTP/CLI scaffolding (`presenters-objects.md`
— the Humble Object split is *the* testability move at a boundary); review
UIs and CLIs can be reshaped without touching certification logic. *Costs:*
one mapping layer per surface; trivial endpoints feel over-ceremonied.
*Verdict:* ADR 0008 deliberately chose plain CLIs + a thin review UI with no
BFF — the least edge machinery. That decision only stays cheap if the edge
stays humble; a fat controller is a BFF nobody decided to build.

**Anchor.** `presenters-objects.md`; ADR 0008; `test-boundaries.md`.

**Pattern.** `run()` in a CLI command: parse args → `certifyUseCase.execute(req)`
→ format exit code/message. Cyclomatic complexity ~2.
**Anti-pattern.** A controller that loads lineage rows, computes a verdict
delta, and decides certification status inline.

**Enforcement.** Review (decidable proxy: any branch on *domain state* in an
edge class is a finding; CC of edge methods > 5 is a smell escalation —
CR-18 machinery).

---

## D. Data and flow discipline

### CR-14 — Lineage is written in-transaction, to the lineage schema, by the owning path

**Rule.** Every lineage write is synchronous and in the same *local*
transaction as the state change it describes, carries the full pinning set,
and targets the lineage schema only. No component writes lineage anywhere
else; no foreign keys between lineage and conversion-state schemas (either
direction); conversion-state staging never gains survival past
certification.

**Trade-off.** *Buys:* "no missing link in the chain" survives crashes —
the state change and its evidence commit or abort together; retention
deletion stays provably safe because no lineage row references disposable
state. *Costs:* the lineage write is on the hot path's latency, and
cross-schema *reads* must stay FK-free lookups (accepted in ADR 0006's D4
rider). *Verdict:* audit reconstruction "from stored evidence alone" is a
top-3 characteristic; in-transaction writes are trivial in one process and
the hard case in any distributed design — this is a monolith dividend ADR
0005 explicitly counted. Async "eventual" lineage would quietly refund it.

**Anchor.** ADR 0006 (F4, lifecycle partition, D4 retention rider), ADR
0007 (in-transaction rule); `database.md` (data model is significant).

**Pattern.** `@Transactional` use case: mutate conversion state + append
lineage row (full pinning set) in one method, one datasource.
**Anti-pattern.** `eventPublisher.publishAsync(new LineageEvent(...))` after
commit; an FK from a lineage row to a staging row. A lineage/provenance
implementation that silently returns without writing passes every shape
check and destroys the chain — silent no-ops on the audit path are
findings.

**Enforcement.** Migration checks (F4 + retention-class checks, seed D-1);
Review for the transactional-boundary half (decidable: is the lineage append
inside the same `@Transactional` method as the mutation?).

### CR-15 — Async at the two decided seams only; outbox out, idempotent in

**Rule.** Queues exist at exactly two seams: Coordinate Conversion → Replay
on Devices, and Coordinate Conversion → Route Human Decisions. Producers
enqueue via a transactional outbox in the same local transaction as their
state change; consumers are idempotent and write their own lineage; no
distributed transaction ever spans a queue. Introducing any other queue,
`@Async`, scheduled hand-off, or event bus requires a superseding ADR —
not a PR.

**Trade-off.** *Buys:* zero duplicated device runs (the dominant spend
control) and resumable batches, while everything else keeps the one-clock,
one-transaction simplicity the style was chosen for. *Costs:* the two seams
carry outbox/redelivery machinery and its testing burden. *Verdict:*
pipeline-as-macro-style was rejected partly *because* of the repair loops
and human escalation; asynchrony is priced per-seam here, and each new async
edge re-imports the distributed-consistency problem ADR 0006 rejected a
store-per-cluster to avoid. Two is the decided number.

**Anchor.** ADR 0007; ADR 0005 (sync-by-default determination).

**Pattern.** Producer: state change + outbox row, one transaction; relay
ships the queue message; consumer keys idempotency on the batch/run ID.
**Anti-pattern.** `@Async` on a certification method to "speed up the
batch"; a direct `queueClient.send()` beside a DB write (dual-write, no
outbox).

**Enforcement.** ArchUnit partial (seed D-2: queue-client and `@Async`
usage confined to the two seam packages); Review for new async edges.

### CR-16 — The model proposes; determinism disposes

**Rule.** LLM output never acquires authority — execution authority, trust
status, graph permanence, or credential reach — without passing a
deterministic, versioned, auditable gate. Concretely: model output is data
until a committed decision table / schema validation / static capability
gate passes it; generated code executes only in the credential-isolated
separate process (no long-lived credentials, no gateway credential, ever)
after static capability rules pass; every model call captures its pinning
fields (`UNPINNABLE_PHASE1` where structurally impossible — never blank).

**Trade-off.** *Buys:* bounded blast radius for the system's dominant novel
risk — every confirmed critical finding in risk analysis traced to LLM
output acquiring authority without a gate (ADR 0014's stated root); "remove
the prize rather than build the cage" survives new jailbreak techniques,
which likelihood-only mitigations don't. *Costs:* gates and schemas to
maintain; some agentic convenience deliberately forgone. *Verdict:* this is
the program's security posture, decided across three ADRs. In code review
it's the highest-severity rule in this catalog: a violation is a security
finding, not a style finding.

**Anchor.** ADR 0014 ("the model proposes; determinism disposes"), ADR 0013
(credential isolation, separate process, static capability rules), ADR 0001
(pinning capture at the seam).

**Pattern.** Proposer returns `CandidateActionSet` → deterministic decision
table selects/rejects → only then does the executor act. **Gate shape:** an
exact-match gate against a committed enum belongs as a versioned static
factory on the enum itself (gate version as a constant); a separate gate
class is warranted only when the rules exceed membership (capability
checks, thresholds, multi-field validation). Rejections are recorded — an
invalid proposal that vanishes silently is an audit blank spot. Captured
pinning fields (gate/prompt/model versions) must reach the **persisted**
provenance record itself — pinning that stops in an in-memory DTO is
decorative pinning by another route. And least machinery never licenses a
cycle (CR-02): before depending on a port directly, check the port's
existing imports — if it already imports your package's types, keep a
consumer-owned port (CR-10) or move the shared type to a neutral package.
**Anti-pattern.** Executing a model-suggested action because a confidence
field is high; running generated code in the orchestrator's process "for
the POC"; a model call site with no pinning capture.

**Enforcement.** Review (decidable checklist: for each model-output
consumer — is there a deterministic gate between output and effect? For
generated code — separate process? credentials absent? static gate?).
Process-isolation and credential topology also land as deployment checks
outside this catalog's scope.

---

## E. Tests and metrics

### CR-17 — Test the API, not the structure

**Rule.** Tests exercise a module through its published API (or a dedicated
test API with explicit superpowers) — not by mirroring one test class per
production class. Production code never depends on test code. Fakes for
ports (in-memory `JudgeGateway`, MinIO container for the storage port) live
with the port's contract; core logic tests use plain constructors, no Spring
context.

**Trade-off.** *Buys:* refactoring freedom — structure can change without
mass test rewrites (the Fragile Tests Problem is structural coupling, not
test count); tests document behavior at the same seams the architecture
protects, so they double as boundary regression checks. *Costs:*
coarser-grained failures take marginally longer to localize; a test API is
code to maintain. *Verdict:* sdd-implement's red/green discipline produces
*many* tests; whether they ossify the codebase or protect it is decided
entirely by what they couple to. "The structure of the tests must not
reflect the structure of the application" is the difference.

**Anchor.** `test-boundaries.md`; `package.md` (same-package tests enable
CR-04); ADR 0001 (contract-parity golden set as the seam's test).

**Pattern.** `CertificationPolicyTest` drives scenarios through the
module's API with a fake gateway; one behavior per test.
**Anti-pattern.** `WeightedLocatorScorerTest` pinning every private
weight; `@SpringBootTest` on a pure-logic test.

**Enforcement.** Review (decidable: does the test import non-API internals
of another package? does a production class reference test scope?). The
merge-time test-weakening ratchet (sdd bundle) stays the deletion backstop.

### CR-18 — Complexity and structure metrics are review ratchets, not vibes

**Rule.** Thresholds, checked at review/converge time: method cyclomatic
complexity ≤ 10 hard ceiling, ≤ 5 target in core packages; edge classes
(CR-13) target ≤ 5; package Normalized Distance from the Main Sequence
D < 0.3 as a watched trend (alarmed, not build-breaking initially).
Rising trends are an extraction-trigger conversation per ADR 0005's
cadence — not a cleanup ticket, and never silently re-thresholded.

**Trade-off.** *Buys:* an objective backstop against the two known decay
modes of agent-written code — brute-force accidental complexity and
zone-of-pain packages (high concreteness + high fan-in) — which per-diff
human review reliably misses because each diff looks locally fine.
*Costs:* false positives in genuinely complex domain algorithms; metric
plumbing in CI. *Verdict:* with three coding agents writing most diffs,
"gathering metrics without alarms" is theater (`code-complexity.md`: a
fitness function needs an objective measure *and* a feedback loop). The
thresholds here are the chapter's own defaults, tightened where this
system's edges should be trivially thin.

**Anchor.** `code-complexity.md` (CC, A/I, Distance, AI-slop framing);
`component-coupling.md` (metric definitions); ADR 0005 (quarterly trend
cadence).

**Pattern.** Converge report includes: methods over CC target (count +
worst), per-package D with trend arrow, flagged edge classes.
**Anti-pattern.** Raising `MAX_CC` in config to make a red build green —
that's a threshold decision, which is an ADR-trigger, not a constant edit.

**Enforcement.** ArchUnit/PMD seeds (seed E-1: CC checks; D-metric
condition per the chapter's ArchUnit sketch), alarming; converge-time
review consumes the trend.

---

## Chapters deliberately not represented

Cut on the selectivity filter (decidable + load-bearing here + not better
mechanized): `clean-embedding.md` (embedded C), `services.md` (informs the
*migration target* only — revisit at extraction time), `components.md`
(history), `layers-boundaries.md` and `independence.md` (their applicable
content is subsumed by CR-01/CR-03/CR-11 and the decided ADRs),
`boundaries-anatomy.md` (taxonomy background for B-group rules),
`policy-level.md` (its dependency-direction content is CR-02/CR-11's
rationale), `srp.md`/`main-components.md`/`boundaries.md` (present as
rationale inside rule cards rather than as standalone rules).
