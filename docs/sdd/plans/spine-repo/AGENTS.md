# AGENTS.md

Mobile test automation — shared spine. One Maven reactor, one Spring Boot
deployable. This file summarizes; it does not replace the spec, plan, and ADRs it
points at. Those are maintained by humans and are the source of truth.

## Before you start

Talk to the maintainer before analyzing the codebase, setting up build
environments, running scripts, or writing code. This repository is governed by a
signed-off spec and an ADR set; work that starts from the code alone reliably
violates a constraint no linter catches. If you are derived from this file
(`CLAUDE.md`, `copilot-instructions.md`, `.cursorrules`), copy this block verbatim.

**Both pipelines stay live.** The repo legitimately contains `codeCommit`-carrying
(o1, code-generation) and — once its gate closes — `irDigest`-carrying (o7,
interpreter) rows. Do **not** delete o1 code generation as dead code, do **not**
"unify" the two schemas, do **not** migrate o1 rows. Removing o1 is out of scope.

## Authority chain

1. The maintainer, in conversation. 2. ADRs (`docs/architecture/adrs/`).
3. The coding-rules catalog. 4. The book.
Where the o7 spec is silent, the spine spec governs.

Rules here are individually non-contradictory on purpose — several harnesses
concatenate instruction files positionally and resolve conflicts arbitrarily, so
ordering resolves nothing. Two rules in conflict is a bug in this file: report it,
do not pick one.

## Layout

Five Maven modules plus a thin assembly. `app` builds the single deployable.

| Path | Holds |
|---|---|
| `spine-contracts/` | the three IR records, marker enums, JSON-schema export |
| `screening/` | screening library — own artifact, own version (the M35 marker needs a citable version) |
| `conversion/` | cluster module |
| `validation-certification/` | cluster module — hosts the device-gate worker |
| `evidence/` | cluster module — evidence, lineage, rendered plans |
| `app/` | thin Spring Boot assembly — **the only deployable** |
| `architecture-tests/` | ArchUnit fitness functions, CI-blocking |

Cluster modules depend on `spine-contracts` only, never on each other. ADR 0005's
"three modules" governs *domain partitioning* — a shared contracts kernel and a
shared library are not a fourth partition (ratified at PLAN-OK).

## Definition of done

Never return control to the maintainer without, in this order — fail fast:

1. `mvn -q verify` passes.
2. ArchUnit fitness functions pass (F1–F4 + module boundaries + B-5 no-registry).
   A red fitness function is a design finding, not a test to fix.
3. Flyway migrations apply clean against Postgres via Testcontainers.
4. The grant assertion passes — the app role cannot `UPDATE`/`DELETE` lineage.
5. `spotless:check`, Error Prone, NullAway and Checkstyle pass.

Do not run the full test suite to check one change; scope to the module.

## Never

Each rule names what enforces it. Where nothing does, it says so — those are the
ones that need you to actually read them.

- **Never weaken a fitness function.** No `@SuppressWarnings`, no suppression-file
  entries, no `@Disabled`, no widening a rule's package glob to make it pass. F1–F4
  are load-bearing per ADR 0001/0006; suppression requires a superseding ADR.
  *(Enforcer: none. This is the rule that guards the other rules.)*
- **Never introduce a second deployable.** CI asserts exactly one bootable jar.
  *(Enforcer: build script, ADR 0005:126.)*
- **Never add a plug-in registry at a seam.** Source adapters are Spring-selected
  implementations of one interface — no `ServiceLoader`, no classpath scanning, no
  runtime discovery. *(Enforcer: ArchUnit B-5, wired by T02, on plan:14 authority —
  F1/F2 guard the seam boundary, not the binding mechanism, so this needed its own
  rule. Detects discovery mechanisms only: a keyed map of implementations under an
  innocent name still passes, and stays a review obligation. The o7 driver seam's
  copy is ADR 0017's seed F-1, still **Proposed**.)*
- **Never let a source-system type leave its adapter.** Only IR crosses.
  *(Enforcer: ArchUnit F2.)*
- **Never call a model provider outside the model-boundary adapter.**
  *(Enforcer: ArchUnit F1.)*
- **Never `UPDATE` or `DELETE` a lineage row.** Corrections are superseding
  appends. The app role holds `INSERT`/`SELECT` only.
  *(Enforcer: DB grants + Testcontainers assertion.)*
- **Never write a lineage row outside the transaction that changes state.** If the
  lineage write fails, the state change rolls back. *(Enforcer: test.)*
- **Never record `system` as a principal.** Individual or per-component service
  principal, always. *(Enforcer: DB `CHECK`.)*
- **Never hash after reading.** SHA-256 into append-only lineage *before* any
  downstream read. Reordering this for performance breaks the audit and nothing
  catches it. *(Enforcer: none — review obligation.)*
- **Never use `Thread.sleep` or an unbounded wait.** An unbounded wait makes a
  run's result a function of wall-clock timing rather than of the committed
  artifact. *(Enforcer: custom Checkstyle check, plan:69 / T30.)*
- **Never commit a literal credential.** Credentials are injected references.
  *(Enforcer: gitleaks, warn-only until weeks 3–8, then blocking.)*
- **Never use a named volume or bind mount for a data dir.** Ephemeral only.
  *(Enforcer: CI config check, M40.)*
- **Never let a redelivery double-spend device minutes.** One redelivery, exactly
  one run. Infra failures re-queue with bounded retry and dead-letter to
  quarantine — never heal, never count against the test. *(Enforcer: consumer.)*
- **Never default an unmapped outcome into a classification class.** Unknown
  quarantines. *(Enforcer: runtime, M10a.)*

## Stack

Decided, not suggestions. Rows come from the approved plan (plan:64-73) and the
2026-08-09 owner decisions on the dimensions the plan left open. Do not substitute
a version you remember.

| | |
|---|---|
| Java | **21** — **Temurin 21.0.8+**. Not Oracle JDK: NullAway's JSpecify mode has no Java 21 support on it. |
| Build | **Maven**, multi-module reactor, `./mvnw` |
| Store | **PostgreSQL 16**, JSONB for IR payloads, **Flyway** |
| Queue | **Postgres outbox**, `SELECT … FOR UPDATE SKIP LOCKED`. No broker. |
| Framework | **Spring Boot 4.1** — exact patch pinned by T01, not by you. |
| Format | **Spotless** + **palantir-java-format 2.97.0** (`spotless-maven-plugin` 3.9.0) |
| Static analysis | **Error Prone 2.50.0** + **NullAway 0.13.8** (JSpecify mode) + **Checkstyle** |
| Null safety | **JSpecify**, package-level `@NullMarked`. Never `org.springframework.lang.@Nullable` — Spring 7 deprecated it. |
| Fitness functions | **ArchUnit 1.5.0**, artifact `archunit-junit6` |
| CI test infra | **Testcontainers** (Postgres, MinIO), BOM-managed |

Test stack comes from the Boot BOM — **never declare a JUnit version**. Under Boot
4.1 that is JUnit **6**, which is why ArchUnit's artifact is `archunit-junit6`;
`archunit-junit5` is the wrong coordinate and will not resolve the right engine.

**Deliberately deferred — do not add these to the POM:** SBOM (CycloneDX),
dependency locking / trusted checksums, reproducible-build settings, Sonar. All
additive; none blocks the scaffold. **Mutation testing (PIT) is deferred on a
hard blocker**, not on cost: whether `pitest-junit5-plugin` works against JUnit
Jupiter 6 is unverified. Do not wire it as a build gate until someone checks.

**Still `UNRESOLVED` — ask, do not choose:** the attribution-trailer policy
(working agreement, below). Version facts behind the decided rows are in
`docs/research/o7-agents-md-external-research.md` §5 — but read §5 against **Java
21**, not the Java 25 it was written for.

**Two standing assumptions, not settled facts.** PostgreSQL is a working
assumption pending bank-catalog confirmation, and ADR 0011 (object storage) is
Proposed / PROBE-PENDING with a MinIO default. Either resolving against us is an
**sdd-replan event, not a silent patch** — if you hit one, stop and say so.

**Traps.** Maven 4 is not GA — `maven.apache.org/docs/history.html` is the version
authority, not GitHub's prerelease flag, which marks RCs `prerelease=false`. Pin
plugin versions; a floating one breaks the build on someone else's schedule.
Enforcer pins the baseline: `requireJavaVersion [21,22)`, `requireMavenVersion
[3.9.16,4.0.0)`. NullAway on Java 21 also needs
`-XDaddTypeAnnotationsToSymbol=true` — without it JSpecify mode silently does
less, it does not fail. `mvn package -DskipTests` still runs AOT processing under
Boot 4.x; only `maven.test.skip` suppresses it.

## Appium (device-gate work)

**java-client declares Selenium with an open version range** — `[4.42.0, 5.0)` on
`selenium-api`, `selenium-remote-driver` and `selenium-support`. Under Maven that
re-resolves at every rebuild, so pinning `java-client` alone **does not pin the
stack**. Exclude those three from the java-client dependency and declare each
explicitly. No linter catches this; it silently falsifies the pinning claim.

No implicit waits, no driver-level default timeout — mixing implicit and explicit
waits produces unpredictable timeouts (Selenium's docs). The bounded-wait rule
reaches driver *configuration*, not just the IR.

The device-cloud driver version is **observed, not controlled** — record what the
session reports, never assume what you requested. Always emit `appiumVersion`.

**Do not commit to an Appium 3 pin.** Perfecto documents Appium 3 on
emulators/simulators only (Release 25.10); real-device support is **unconfirmed**,
and the question is open with the vendor. Until it is answered, treat any Appium 3
real-device capability as unproven — do not pin it, and do not infer support from
a session that happens to start.

## Common changes

| You want to… | Do this |
|---|---|
| Add a source adapter | New implementation of the one interface, Spring-selected. Not a registry entry. |
| Add an async edge | Stop — ADR 0007 decided exactly two async seams. A third needs a superseding ADR. |
| Add a lineage field | Migration + schema, append-only. Never an `UPDATE` path. |
| Change a fitness function | Recorded decision, never just a commit (M3/M18). |
| Change K, retry cap, retention | Plan-level values — a recorded update, not an edit. |
| Touch the certification verdict | Read ADR 0012 and the M37 principal rules first. |

## o7 interpreter — NOT YET IN SCOPE

o7 (the interpreter fork: committed `TestCaseIR` executed by a version-pinned,
LLM-free interpreter, replacing code generation) is **specified but not accepted**.
Its spec is DRAFT, ADRs 0016 and 0017 are **Proposed**, and the Stage-2 gate is
open with **two** signatures pending (owner + designated security owner).

**Do not implement o7. Do not derive an o7 plan or o7 tasks.** When the gate
closes, o7 lands as a Spring Boot **module inside this repository** hosted by the
device-gate worker — never a new deployable — and these activate: LLM-free replay
path; `healPolicy` fixed to `NONE`; `irDigest` subsumes both `codeCommit` and
`irVersion`; closed opcode set extended only by spec change; the seven-check IR
gate; per-session cloud-adaptivity attestation; exactly one live driver behind the
seam. Full set: `mobile-test-automation-o7-interpreter.spec.md`. If a red build
later comes from those assertions — a second live driver, a registry-shaped
binding, a generated test class — **that failure is the mechanism, not a defect.**

## Reading (on demand — do not preload)

`«ws»/` = the **Architect workspace**, a separate checkout. Grepping for those
paths *here* finds nothing — that is not evidence they are missing. Ask for it.

| Topic | Path |
|---|---|
| CR-xx coding rules | `docs/coding-rules/rules-catalog.md` — **point at it, never restate it** |
| ArchUnit seeds | `docs/coding-rules/archunit-seeds.md` |
| Seam globs, base package | `.sdd/binding.toml` → `[coding-rules]` |
| Spine contract, EARS criteria | `«ws»/docs/sdd/specs/mobile-test-automation-spine.spec.md` |
| Technology, module reading, plan values | `«ws»/docs/sdd/plans/mobile-test-automation-spine.plan.md` |
| Task board, WP order | `«ws»/docs/sdd/plans/mobile-test-automation-spine.tasks.md` |
| Architecture decisions | `«ws»/docs/architecture/adrs/application/mobile-test-automation/` — index first |
| o7 (not yet in scope) | `«ws»/docs/sdd/specs/mobile-test-automation-o7-interpreter.spec.md`; ADRs 0016, 0017 |
| Mock artifacts | `«ws»/docs/research/mocks/` — **warning:** the o7 mocks still carry `irVersion`; copying their shape reintroduces a fork-boundary leak |

The first three are installed by T01 (`INSTALL.md` steps 1–2). If they are
missing, the scaffold is incomplete — **ask; do not proceed on memory of the
rules.** The `[coding-rules]` binding ships **resolved** (`base_package =
com.bank.spine`); the only unresolved values are the seam globs explicitly marked
`CHANGE-ME`, each of which names the question to ask. A `{{placeholder}}` anywhere
else means the wrong file was installed.

**Two numbering schemes, do not conflate.** M- and F-numbers in *this file*
(M3, M18, M35, M40, M10a, F1–F4) are **spine-spec markers** — resolve them in the
spec, never by inference. Letter-hyphen ids (A-1, B-5, F-1) are **seed ids** in
`docs/coding-rules/archunit-seeds.md`. Spec `F4` and seed `F-1` are unrelated.

## Working agreement

Do not push. "Open a PR" in a task description is intent, not permission — ask.
Attribution trailer policy: **`UNRESOLVED`** — conventions conflict across projects
(`Generated-by:`, `Assisted-by:`, forbidden entirely, no AI-authored PRs), so ask
rather than guessing.

When a gate closes, a module lands, or the layout changes, update this file in the
same PR.

<!-- version: 1.0.0 — spine T01 deliverable, content final as of 2026-08-09.
     Summarizes; does not replace the spec/plan/ADRs. One UNRESOLVED remains by
     design: the attribution-trailer policy (working agreement). The spine task
     board still awaits TASKS-OK, so this file is final in CONTENT, not yet
     landed. Regenerate the Stack table from the POM once it exists. -->
