# Tasks: Mobile Test Automation — Weeks 0–3 Shared Spine

**Plan:** `docs/sdd/plans/mobile-test-automation-spine.plan.md` (APPROVED 2026-07-28)
**Spec:** `docs/sdd/specs/mobile-test-automation-spine.spec.md` (signed off 2026-07-27, post-P1 baseline)
**Implementation home:** the new `mobile-test-automation-spine` repository (S2) — every task below lands there; this workspace holds only these artifacts.
**Order:** T01–T04 (WP0, strictly first — M18) → T05–T07 (WP1) → {T08–T13 (WP2) ∥ T14–T16 (WP3)} → {T17–T25 (WP4) ∥ T26–T29 (WP5) ∥ T30–T39 (WP6)} → T40–T43 (WP7)

## EARS criteria index (traceability keys)

Failure paths, in spec order:

| Key | Criterion (short) | Key | Criterion (short) |
|---|---|---|---|
| FP1 | F1 model-seam CI fail | FP14 | corpusClass absent → invalid (M19) |
| FP2 | F2 source-type escape CI fail | FP15 | quarantine-unknown status (M10a) |
| FP3 | F3 both halves, ingestion egress | FP16 | record-actual pinned-facet mismatch → quarantine (M24) |
| FP4 | F4 lineage FK → CI fail | FP17 | principal schema-enforced, no `system` (M37) |
| FP5 | F6 pinning set; markers; runner-env; prompt SHA value-space | FP18 | app-role UPDATE/DELETE refused + CI assertion (ADR 0012) |
| FP6 | idempotent consumer, no double-spend | FP19 | hash-chain link in-tx or write fails (ADR 0012) |
| FP7 | `Thread.sleep` static fail | FP20 | retention-class absent → invalid (M39) |
| FP8 | locator-manifest static fail (C5) | FP21 | capture/landing screening, two-half F3 (M35) |
| FP9 | ENV_INFRA requeue, cap, DLQ + alert (M21) | FP22 | unmarked real-derived fixture → CI fail (M35) |
| FP10 | literal secret in IR → schema reject | FP23 | screening flag → quarantine + recorded override (M35) |
| FP11 | lineage write fails → state rolls back | FP24 | credential = injected reference; warn-only scan (M34) |
| FP12 | hash-at-pull before any read (M9) | FP25 | named volume/bind mount → CI config fail (M40) |
| FP13 | hash-at-ingest snapshot digest (M15) | | |

Happy paths, in spec order:

| Key | Criterion (short) | Key | Criterion (short) |
|---|---|---|---|
| HP1 | single deployable, three modules, boundary check | HP11 | per-adapter canonicalization + stored snapshot (M15) |
| HP2 | task zero: scaffold + F1–F4 + grant assertion + secrets scan | HP12 | artifacts in object storage w/ class + retention (ADR 0006/M39) |
| HP3 | records + Jackson + committed schema + drift check | HP13 | lineage same-tx, pinning + principal + chain link |
| HP4 | ingestion CLI → schema-valid screened IR, ambiguity flags | HP14 | anchoring interval + stale alert + verification (ADR 0012) |
| HP5 | hierarchy tool outputs, screened at capture, pool identity | HP15 | sampling flag + red-team regression report (M36) |
| HP6 | static gate first, seconds, zero device cost | HP16 | build identity in every emission (M32) |
| HP7 | outbox enqueue → idempotent worker → pinned pool run + pull | HP17 | K-of-K-derivable outcome fields (M10b) |
| HP8 | rule-based 7-class classification | HP18 | outbox/queue schema projection-reusable (M17) |
| HP9 | Smart Reporting contract tests (M10) | HP19 | week-3 gate: clause a (end-to-end) + clause b (`REAL_INGESTED`) |
| HP10 | dual-fixture contract suite from week 0 (M20) | | |

## WP0 — Task zero (M18: precedes any feature commit)

| Id | Task | Depends | EARS / verify | Pass/fail |
|----|------|---------|---------------|-----------|
| T01 | Scaffold Maven reactor: root `pom.xml` (enforcer, pinned plugin versions) + six empty-but-shaped modules `spine-contracts/ screening/ conversion/ validation-certification/ evidence/ app/`; `app` builds one Spring Boot deployable. **[A1 2026-08-09]** Also create the repo-root **`AGENTS.md`** and **`CLAUDE.md`** by copying `spine-repo/AGENTS.md` + `spine-repo/CLAUDE.md` (this directory) **verbatim** — **[A6 2026-08-09]** they are literal files now, not a body to extract from a marker; before declaring `AGENTS.md` canonical, assert the root carries no `.cursorrules` / `.rules` / `.windsurfrules` / `.clinerules` / `AGENT.md` / `.github/copilot-instructions.md`. **[A2 2026-08-09]** Also install the coding-rules bundle `AGENTS.md` points at (`INSTALL.md` steps 1–2): copy `references/rules-catalog.md` + `references/archunit-seeds.md` into `docs/coding-rules/`, and append the **resolved** `mobile-test-automation-spine.binding.toml` (this directory) into `.sdd/binding.toml` — **not** `binding.template.toml`, whose defaults are o1-shaped and wrong for the spine tree **[A4 2026-08-09]**. **[A5 2026-08-09]** POM pins the I4 decisions: **Temurin JDK 21.0.8+** (not Oracle), **Spring Boot 4.1** (exact patch resolved at T01 execution), **Spotless + palantir-java-format 2.97.0**, **Error Prone 2.50.0 + NullAway 0.13.8** (JSpecify mode, `-XDaddTypeAnnotationsToSymbol=true`), **Checkstyle** (same config T30 needs), **ArchUnit 1.5.0 `archunit-junit6`**; enforcer `requireJavaVersion [21,22)` + `requireMavenVersion [3.9.16,4.0.0)`. **No** SBOM / dependency-locking / reproducible-build / PIT / Sonar wiring | — | HP1, HP2 — `mvn package` yields exactly one bootable jar; module tree matches plan §2. **[A1]** `AGENTS.md` + `CLAUDE.md` present at root; no competing agent-instruction file present. **[A2]** `docs/coding-rules/{rules-catalog,archunit-seeds}.md` present; `.sdd/binding.toml` contains a `[coding-rules]` section; every pointer in the `AGENTS.md` "Where the rules live" table resolves to an existing path. **[A4]** binding parses as TOML and `base_package = "com.bank.spine"`; no `{{placeholder}}` survives in the installed seeds except the three CHANGE-ME seams the binding names. **[A5]** `mvn -q verify` green on the empty scaffold with `spotless:check`, Error Prone, NullAway and Checkstyle all wired and passing; `java -version` reports a non-Oracle 21.0.8+; enforcer fails a deliberately-floating dependency version | |
| T02 | `architecture-tests/`: ArchUnit rules wired CI-blocking — F1 (no provider SDK/gateway/Copilot type outside a model-boundary adapter package), F2 (no POI/Octane/ALM type beyond its adapter package), F3-static (ingestion egress paths call `screening`), F4 (no lineage FK into conversion-state schema — Flyway-source scan), module-boundary rules (cluster deps → `spine-contracts` only), no-gateway-credential-config in `devicegate` (ADR 0013 shape). **[A3 2026-08-09]** Plus **B-5 no-registry** (`archunit-seeds.md` B-5): no `ServiceLoader` / classpath scanner / `SpringFactoriesLoader` dependency from the three CR-08 seam packages — source adapters, Invoke Models, storage port | T01 | FP1, FP2, FP3(static), FP4, HP2 — each rule proven by a deliberately-violating sample that fails the build, then removed. **[A3]** B-5 proven the same way — a `ServiceLoader`-bound source adapter fails the build | |
| T03 | Flyway `V1__lineage_core.sql`: lineage tables (append-only), roles — app role `INSERT`/`SELECT` only, DDL under migration role; principal column NOT NULL + CHECK rejecting `system`; retention-class + corpusClass columns NOT NULL where applicable | T01 | FP17, FP18(schema), FP14/FP20(DB half) — migration applies clean on Postgres 16 via Testcontainers | |
| T04 | CI pipeline-as-code (`ci/`): runner image pinned **by digest** (M28); gitleaks warn-only (M34); ephemeral-volume config check — named volume/bind mount for a data dir fails (M40); grant-assertion job — Testcontainers proves app role `UPDATE`/`DELETE` on lineage is refused; fixture screening-marker check (activated fully in T24) | T01, T03 | FP18(assertion), FP24(scan), FP25, HP2 — pipeline green on empty scaffold; each check proven by a violating sample | |

### Amendment A1 — 2026-08-09 (T01 scope, pending TASKS-OK)

**What changed.** T01 gains one create-only deliverable: the repo-root `AGENTS.md`
(+ a one-line `CLAUDE.md` importing it). No other task changes; no EARS criterion
is added, removed, or reinterpreted; no plan value moves.

**Why here rather than later.** The file is an agent-facing contract for a repo
that does not exist yet. Landing it *with* the scaffold avoids an orphan file in
this workspace and a later relocation step, and puts it in the same commit as the
module tree and fitness functions it describes. Owner decision, 2026-08-09.

**Content + provenance.** `spine-repo/AGENTS.md` in this directory — a literal
file, copied verbatim. **[A6 2026-08-09]** It was previously the body below a
`---8<---` marker inside `mobile-test-automation-spine.AGENTS.md`; that file now
keeps only provenance, status and the change log, and points at the real one.
Derived from
`docs/research/o7-agents-md-external-research.md` §8. Stack rows are taken from the
approved plan (plan:64-73) — **Java 21, Maven, PostgreSQL 16, Flyway, ArchUnit,
Testcontainers**; every dimension the plan does not pin is marked `UNRESOLVED`
rather than guessed, including the attribution-trailer policy.

**Standing item this creates.** `AGENTS.md` restates nothing the CR-xx catalog or a
fitness function already enforces — it points. When ADR 0016/0017 are accepted and
the o7 module lands, its "NOT YET IN SCOPE" section activates and should shrink to
pointers as the ArchUnit seeds F-1…F-3 (`archunit-seeds.md`) get wired.

**Not decided by this amendment.** The o7 Stage-2 gate stays open (two signatures
pending); the spine board still awaits its own TASKS-OK.

### Amendment A2 — 2026-08-09 (T01 scope, pending TASKS-OK)

**What changed.** T01 gains two create-only deliverables: `docs/coding-rules/`
(`rules-catalog.md` + `archunit-seeds.md`, copied verbatim from
`tooling/coding-rules-skill/references/`) and the `[coding-rules]` section of
`.sdd/binding.toml` (appended from `binding.template.toml`). No other task
changes; no EARS criterion is added, removed, or reinterpreted; no plan value
moves.

**Why.** A1 landed `AGENTS.md`, which names the CR-xx catalog as authority #3 and
sends agents to `docs/coding-rules/rules-catalog.md` and
`docs/coding-rules/archunit-seeds.md`. **Nothing in T01 installed them.** An
instruction file pointing at a path that does not exist is the documented failure
mode (microsoft/apm#695); the draft's "first three missing = bundle not installed,
ask" fallback is mitigation, not a fix. This closes it in the same commit that
creates the pointer.

**Content + provenance.** Steps 1–2 of `tooling/coding-rules-skill/INSTALL.md`,
unchanged. Steps 3–5 (per-agent front-ends) are deliberately **not** pulled in —
`AGENTS.md` is the spine's single instruction file per A1, and adding
`.claude/skills/`, `.cursor/skills/` and `.github/instructions/` would recreate
the competing-instruction-file condition T01 asserts against. Step 6 (CI wiring)
is T02's job, not T01's.

**Expected-unresolved at T01.** The appended `[coding-rules]` binding ships with
placeholders. `base_package` has no value anywhere in the repo and the skill's own
rule is *ask, don't guess* — resolving it is a separate owner decision. T01's
verify asserts the section **exists**, not that it is resolved.

**Not decided by this amendment.** Nothing about rule content, thresholds, or
which rules are load-bearing. The bundle is copied, not edited.

### Amendment A3 — 2026-08-09 (T02 scope, pending TASKS-OK)

**What changed.** T02 gains one ArchUnit rule — **B-5**, no plug-in registry at
the three CR-08 seams (source adapters, Invoke Models, storage port). No other
task changes; no EARS criterion is added, removed, or reinterpreted.

**Why here rather than at the o7 gate.** `plan:14` is **approved** and states the
principle directly: *"No registry, no plug-in machinery. Source adapters are
Spring-selected implementations of one interface."* That same line claims *"F1/F2
ArchUnit rules are the boundary"* — and that is the gap. **F1 and F2 guard what
crosses a seam, not how an implementation is bound to it.** A `ServiceLoader`-based
registry passes both unharmed. So the principle is approved and unenforced today,
not on some future date.

**Provenance is the plan, not ADR 0017.** ADR 0017 (Proposed) carries the same
assertion for the o7 C-MIG driver seam; that half stays gated as seed F-1. B-5
stands on `plan:14` alone and has **no dependency on the o7 gate** — if ADR 0017
were rejected outright, B-5 would still bind. The seed file records the split
explicitly so nobody re-merges them.

**Consequential edits made with this amendment.**
`tooling/coding-rules-skill/references/archunit-seeds.md`: B-5 added to the o1/spine
class, F-1 narrowed to `{{seam.driver_adapter_packages}}` and renamed
`driver_seam_bound_by_spring_di_not_by_a_registry`, split note added to §F, review
channel item 1 updated (F-1b's name heuristic is driver-seam only — the spine arm's
blind spot is wider). `mobile-test-automation-spine.AGENTS.md`: the Never-block
entry's enforcer changes from `**none today**` to T02.

**Known limit, carried forward not closed.** B-5 catches discovery *mechanisms*.
ArchUnit's raw type model cannot distinguish `Map<String, SourceAdapter>` from any
other `Map`, so a hand-rolled keyed registry under an innocent name still passes.
That stays a review obligation; the seed file's review channel records it.

**Not decided by this amendment.** ADR 0017's status, the driver seam, and the o7
Stage-2 gate are all untouched.

### Amendment A4 — 2026-08-09 (T01 scope, pending TASKS-OK)

**What changed.** T01 installs a **resolved** spine binding
(`mobile-test-automation-spine.binding.toml`, this directory) instead of the raw
`binding.template.toml` A2 named. No task gains or loses work; no EARS criterion
moves. A2's deliverable is replaced in kind, not extended.

**Why.** The owner supplied `base_package = "com.bank.spine"` on 2026-08-09,
which was the only value blocking resolution (next-items I2, owner decision #1).
With it, every remaining seam glob is derivable from the **approved** plan §2 tree
(`plan:29-56`) plus the ADRs — so shipping placeholders would now be a choice, not
a constraint.

**The template was actively wrong for the spine, in four places.** This is why the
resolved file replaces it rather than being appended after it:
1. `modules` listed **three**; the PLAN-OK ruling (2026-07-28) makes it **six**
   (three clusters + `spine-contracts` + `screening` + thin `app`).
2. `storage_port_adapter` said `..evidence.storage.adapter..`; the approved tree
   says **`objectstorage`** (`plan:46`).
3. `source_adapter_internal_packages` said `..ingestion.adapter.internal..` — a
   package the approved tree **does not have**. The real vendor-typed packages are
   `excel/` and `octane/` (`plan:39`), which is also T02's own F2 wording.
4. `async_seam_packages` said `..replay.dispatch.. | ..review.dispatch..`, naming
   **neither** spine package. Real: the `evidence` outbox producer (`plan:46`) and
   the `devicegate` worker consumer (`plan:42-43`).

**Three latent seed defects found and fixed in the same pass.** All three were
invisible until a binding was actually resolved against the seeds — which is the
argument for resolving one before T01 rather than during it.

**(1) Multi-glob values could not reach their rules.** ArchUnit's
`resideInAPackage` / `resideOutsideOfPackage` take **one** package identifier, but
the template supplied `" | "`-joined strings to both. A joined string matches no
package — and since these sit in `noClasses().that()` **exclusion** position, a
never-matching exclusion **widens the rule to every class in the build**, so the
legitimate seam code fails first. That reads as a false positive and invites
exactly the weakening the seeds forbid. Multi-glob keys are now TOML **arrays**;
B-2 and D-2 use the plural `resideInAnyPackage` / `resideOutsideOfPackages`.
Fixed in `archunit-seeds.md` **and** `binding.template.toml`, so the o1 arm gets
it too.

**(2) B-1's ban list never read the binding at all.** The seed referenced
`{{provider_sdk_packages}}` — a placeholder matching **no binding key** (the key
is `seams.provider_sdks.packages`) — alongside a hardcoded copy of the same three
SDK roots. So the rule worked *by accident*, on the hardcoded copy, and the
binding's list was decorative. Harmless today because the two lists were
identical; the trap is that **adding the Phase-2 gateway SDK to the binding would
silently not have been enforced** — on F1, a load-bearing rule. B-1 now reads the
binding alone, with no parallel copy to drift from.

**(3) The provider-SDK values were not ArchUnit globs.** They were bare roots
(`org.springframework.ai`) with no trailing `..`. That was inert while defect (2)
kept them unread; routing B-1 through the binding made the shape load-bearing, and
without the suffix the rule matches only classes sitting *directly* in the root
package — under-banning F1 rather than failing loudly. Suffixes added in both
bindings and the template.

**Action for the o1 arm — CLOSED 2026-08-09.** Owner confirms **no o1 workspace
exists yet**, so nothing was ever installed from the pre-fix bundle and there is
no re-check to run. All three defects were caught before first install. Had one
existed, D-2/B-2/B-1 would all have needed re-checking — a green run proved
nothing against any of them.

**Three values stay CHANGE-ME, deliberately.** They are underdetermined by the
approved material, and the binding names each one and what to ask:
- `invoke_models_adapter` — **reserved and empty in phase 1.** The spine makes no
  model call at all (`plan:16`), so B-1 correctly reads as "no provider SDK
  anywhere" today. The adapter's real home is a weeks-3-8 decision.
- `async_seam_packages` — ADR 0007's **second** seam (Route Human Decisions) is
  **out of spine scope** (`plan:58`). Add it when ADR 0008's review path lands;
  adding a third entry for any other reason is a new async seam and needs a
  superseding ADR (`0007:95`).
- `provider_sdks.packages` — the Phase-2 gateway SDK is still unknown. The
  template's defensive default is kept; over-banning costs nothing here.

**One assumption, stated not buried.** Module package roots are assumed to be
`<base_package>.<module dir, hyphens removed>`. Only B-3b depends on it; every
other glob uses `..name..`, which ArchUnit matches at any depth. If
`validation-certification` maps to anything but
`com.bank.spine.validationcertification`, that one line changes.

**Not decided by this amendment.** No threshold moved (CR-18: an ADR-level
decision). ADR 0011 stays Proposed/PROBE-PENDING — only its *port* is bound here,
which was always safe; the production binding still waits on the week-0 probe.

### Amendment A5 — 2026-08-09 (T01 scope, pending TASKS-OK)

**What changed.** T01's `pom.xml` gains concrete pins for the six stack dimensions
the approved plan left open. No task gains or loses work; no EARS criterion moves.
Owner decisions 2026-08-09 (next-items I4).

| Dimension | Decision |
|---|---|
| JDK distribution | **Temurin 21.0.8+**, explicitly **not Oracle JDK** |
| Framework | **Spring Boot 4.1** — line decided now, exact patch pinned when T01 runs |
| Formatter | **Spotless** + **palantir-java-format 2.97.0** (`spotless-maven-plugin` 3.9.0) |
| Static analysis | **Error Prone 2.50.0** + **NullAway 0.13.8** + **Checkstyle** (T30's config, reused) |
| Null safety | **JSpecify** + package-level `@NullMarked`; NullAway at `ERROR` |
| Architecture tests | **ArchUnit 1.5.0**, artifact **`archunit-junit6`** |

**Why the JDK distribution is a decision and not a detail.** The plan pins "Java
21" and names no vendor. NullAway's JSpecify mode targets Java 25; its documented
Java 21 fallback is "most JDK 21.0.8+ distributions **except Oracle JDK**" plus
`-XDaddTypeAnnotationsToSymbol=true`. So on Oracle JDK the null-safety row is not
available at all. Temurin keeps it. **If bank policy later mandates Oracle JDK,
that is an sdd-replan trigger for this row**, not a silent drop of NullAway.

**Why Checkstyle is in the set despite the research saying "skip it."** Report §5
recommended Error Prone + NullAway and explicitly skipping Checkstyle — written
**before the plans directory was read**, the same gap that produced its Java 25
baseline. Checkstyle is **already approved and load-bearing here**: plan:69 and
**T30** name "Spotless + `mvn compile` + Checkstyle + Error Prone + custom
Checkstyle checks", and the `Thread.sleep` ban (**FP7**, a Never-block rule) *is*
one of those custom checks. Checkstyle ships regardless; pointing the same config
at the spine's own source costs ~nothing and avoids two rule sources. SpotBugs and
PMD stay out — the §5 argument that a five-analyser list invites an agent to add
all five still holds.

**Deferred deliberately, with reasons.** SBOM (CycloneDX), dependency locking /
trusted checksums, reproducible-build settings and Sonar are **additive and block
nothing** in the scaffold; add them in a later task. **Mutation testing (PIT) is
deferred on a blocker, not on cost**: whether `pitest-junit5-plugin` works against
JUnit Jupiter 6 is **unverified** (report §5 flags it explicitly). Wiring it as a
build gate on an unverified pairing would make the scaffold's first green run a
coin flip. Verify before adopting.

**Two mechanical corrections carried in.** Report §5's enforcer row specified
`requireJavaVersion [25,26)` for its Java 25 baseline — corrected to **`[21,22)`**.
And the coding-rules bundle's `INSTALL.md` step 6 specified
`archunit-junit5:1.3.0` in **Gradle** syntax; under Boot 4.1's JUnit 6 BOM the
artifact must be **`archunit-junit6`**, and the spine is Maven. Both fixed at
source. **The ArchUnit one fails silently** — the wrong engine suffix discovers no
`@ArchTest` at all, so the suite reports success having run nothing. INSTALL.md now
carries a JUnit-version → artifact table and says so.

**Not decided by this amendment.** The attribution-trailer policy is still
`UNRESOLVED` (owner decision #6). No plan value moves; `Java 21` and `Maven` were
already pinned and are not relitigated here.

### Amendment A6 — 2026-08-09 (T01 mechanics only, pending TASKS-OK)

**What changed.** Nothing in scope, content, or verification. T01 copies two
**literal files** (`spine-repo/AGENTS.md`, `spine-repo/CLAUDE.md`) instead of
extracting a body from below a `---8<---` marker. Recorded because A1 named the
old mechanism explicitly, and a task step that no longer matches its artifact is
how a scaffold silently produces the wrong file.

**Why.** Owner asked for the finished files to be saved under `docs/`. Copying
them beside a wrapper that still carried the same body would have created **two
copies of one file** — the drift risk being avoided in the first place. The body
now exists exactly once; the wrapper keeps provenance, status and the change log
and points at it. **Edit `spine-repo/AGENTS.md`, then update the wrapper's change
log — never the reverse.**

**Not decided by this amendment.** No EARS criterion, no verify column entry, and
no `AGENTS.md` content changed. A1–A5 all stand as written.

### Amendment A7 — 2026-08-10 (T04 + T02 scope, RATIFIED; sdd-spec marker M44 minted at SPEC-OK 2026-08-10 — approved at board TASKS-OK 2026-08-10, applies when implement runs)

**Status.** RATIFIED by the owner 2026-08-10 (four decisions at the foot of this
amendment). The sdd-spec dependency is now **satisfied**: the owner routed it through
**sdd-spec** to earn a real spec criterion first, and on **2026-08-10 SPEC-OK** the
spec minted marker **M44** (six criteria M44-1..M44-6, generalizing M20) in the
`mobile-test-automation-spine.spec.md` test-suite-erosion amendment. A7 therefore no
longer waits on a marker — it now **rides the pending board TASKS-OK exactly like
A1–A6**. Sequence remaining: **board TASKS-OK → A7 lands → the staged `AGENTS.md`
deltas apply and `[A7]` tags go onto T04/T02, advancing to sdd-implement.** Nothing is
applied to a task cell or to `spine-repo/AGENTS.md` (v1.0.0, content-final) until that
board gate. Study and full mechanism: `../../research/spine-agents-md-adoption-study.md`
§6; the marker itself: `../specs/mobile-test-automation-spine.spec.md` (M44 amendment).

**What it is.** A **test-suite-erosion gate**: a CI check that fails a silently-
weakened suite (a removed `@Test`, an added `@Disabled`, a short-circuited
`assumeTrue(false)`, or a `@Test` gutted of its assertions) unless the commit range
carries a waiver that **cites a recorded decision**. Net-new scope — not a refinement
of already-approved work — which is why it earned a marker via sdd-spec (M44, SPEC-OK
2026-08-10) before joining A1–A6 on the pending board TASKS-OK.

**The gate — T04 scope (primary).** T04 (`ci/`) gains a **test-inventory range
gate**. Removals cannot be seen on the classpath (deleted code is not there), so the
mechanism is a git-range diff: inventory the JUnit Jupiter 6 test methods
(`@Test`/`@ParameterizedTest`/`@RepeatedTest`/`@TestFactory`) at base and at head, and
enforce **by signal reliability** (owner decision 3):

- **Deterministic → blocking from commit one (like F1–F4):** a **removed** test, an
  added **`@Disabled`**, or an **`assumeTrue(false)`/`assumeFalse(true)`**
  (`org.junit.jupiter.api.Assumptions`). Zero false positives — a removed test is
  removed — so no warn-in period is warranted. Early on there is little test history
  to diff, so blocking is inert until tests accumulate.
- **Heuristic → warn-only, indefinitely:** a `@Test` whose body carries no assertion
  (`assert*`/`assertThat`/`verify(`). This misfires on helper- and expected-exception-
  based tests, so it never blocks — it only flags for review.

A blocking finding passes only with a waiver (below). House-style acceptance: proven
by a deliberately-weakened sample — a deleted `@Test` and an added `@Disabled` each
fail the range gate from commit one, then are restored.

**The assist — T02 scope (optional complement).** `architecture-tests/` may add an
ArchUnit rule banning an un-waivered `@Disabled` **on the current classpath** — a
cheap in-suite tripwire. It **cannot** replace the range gate: ArchUnit never sees a
removed test. Wire it only with that limitation stated at the call site.

**The waiver — must cite a recorded decision (owner decision 4).** A blocking finding
is allowed only if the commit range carries `TEST-WEAKEN-OK: <ref>`, where `<ref>`
points at a durable record — a lightweight decisions-log line or an ADR — naming why
the weaker suite is still sound. **Not bare free-text:** this is M3/M18 applied
literally ("recorded decision, never just a commit"). A routine removal cites a
two-line decision-log entry, not a full ADR. The token *string* is provisional and
reconciles with the board's unified waiver vocabulary when the (currently UNRESOLVED)
attribution/waiver convention settles; the *semantics* (must-cite-a-record) are fixed.

**Why this, and why nothing more (the backpressure argument).** The gate is the one
practice from the AgentsFramework `AGENTS.md` that is *both* absent here *and* a true
mechanical sensor (its `test_no_test_weakening.py` / G8). It extends an existing
in-repo doctrine rather than inventing one: **CR-18** already accepts mechanical
backstops against *known* agent-decay modes, and **T22 already fails a meta-test when
a fixture family is removed** (M20) — the erosion gate generalizes that "removal
fails a gate" principle from fixture families to test methods. It is a **gate, not a
19th CR rule** — the `rules-catalog.md` is hard-capped at 18, and the check is a
diff-scoped CI gate anyway (the class of gitleaks, the T30 `Thread.sleep` check, the
T04 grant assertion), so the catalog is untouched.

**The greenfield basis, accepted on the record (owner decision 1).** There is no
spine-local erosion incident yet; the justification is **precedent (CR-18, T22) + the
near-certainty that agent-written suites erode**, not a local failure. The spine's
ratchet says do not add a rule without a justifying failure — the owner **consciously
accepted the precedent basis 2026-08-10** rather than deferring, on the reasoning that
the precedent already lives in-repo and the deterministic checks are inert until tests
exist.

**Staged `AGENTS.md` deltas** (apply to `spine-repo/AGENTS.md` on landing; bump
`1.0.0 → 1.1.0`; add a wrapper change-log line — never edit the wrapper first):

- Add to `Never` (matching the file's terse, enforcer-named form):
  ```
  - **Never weaken the test suite.** A removed `@Test`, a new `@Disabled`, or an
    `assumeTrue(false)` needs a `TEST-WEAKEN-OK: <recorded-decision ref>` line in the
    commit range naming why the weaker suite is still sound (M3/M18 — a decisions-log
    line or ADR, never bare text). *(Enforcer: test-inventory range gate, T04 —
    blocking from commit one for these deterministic signals; a gutted-assertion body
    is a warn-only heuristic; ArchUnit assist bans un-waivered `@Disabled`.)*
  ```
- Add to `Definition of done` (a CI/range step — it needs base+head, like gitleaks,
  so it is not a local `mvn verify` step): *"The test-inventory gate passes — no
  un-waivered removed/disabled/short-circuited test in the range."*
- Add a `Common changes` row: *"Remove or disable a test | Stop — add
  `TEST-WEAKEN-OK: <recorded-decision ref>` (M3/M18), or don't."*

**Owner decisions — resolved 2026-08-10.**
1. **Adopt now** on the CR-18 + T22 precedent basis (not deferred to a first incident).
2. **Route via sdd-spec** to mint a real marker before landing (not a marker-less
   dev-process gate; not land-now-backfill).
3. **Split enforcement by reliability** — deterministic signals block from commit one;
   the gutted-body heuristic is warn-only indefinitely.
4. **Waiver must cite a recorded decision** (`TEST-WEAKEN-OK: <ref>`, M3/M18), not
   bare free-text.

**Not decided / not yet done.** The **marker itself is not minted here** — that is the
sdd-spec pass this amendment routes to (it reopens the 2026-07-27 signed-off spec and
needs SPEC-OK). No task cell is edited inline (add `[A7]` tags to T04/T02 on landing);
no `AGENTS.md` content is changed (deltas staged, not applied); A1–A6 stand as written.

## WP1 — `spine-contracts`

| Id | Task | Depends | EARS / verify | Pass/fail |
|----|------|---------|---------------|-----------|
| T05 | Java records `TestCaseIR`, `LocatorCandidate`, `ReplayReport` with Jackson; `PinnedValue` marker enum `{REAL, NOT_APPLICABLE, UNPINNABLE_PHASE1(reserved)}`; `corpusClass` (`REAL_INGESTED`/`FIXTURE`); `retentionClass` field | T01 | HP3, C4 — records serialize/deserialize round-trip; enum carries all three values | |
| T06 | victools JSON-Schema export; schemas committed under `spine-contracts/src/main/resources/schema/`; build regenerates and diffs — drift fails CI | T05 | HP3 — mutate a record without regenerating → build fails | |
| T07 | F6 validation: every applicable pinning field (`irVersion`, `codeCommit`, `pipelineVersion`, `appiumVersion`, device/OS/model, `appVersion`) real; not-yet-applicable fields require explicit `NOT_APPLICABLE`; null/absent never valid; `UNPINNABLE_PHASE1` rejected in the spine; prompt-version value-space documented as prompts-repo Git SHA (M30); missing `corpusClass`/`retentionClass`/snapshot-digest → invalid | T05, T06 | FP5, FP13(schema), FP14, FP20 — validator unit tests: one failing case per field class | |

## WP2 — `evidence` core (∥ WP3)

| Id | Task | Depends | EARS / verify | Pass/fail |
|----|------|---------|---------------|-----------|
| T08 | Append-only lineage write API: row written in the **same local transaction** as the state change (write fails → state rolls back); authenticated principal mandatory (individual or per-component service principal — `svc-ingestion-cli`, `svc-devicegate-worker`, `svc-pipeline`); corrections = superseding appends; readers resolve latest non-superseded | T03, T05 | FP11, FP17, HP13 — Testcontainers: forced lineage failure rolls back state; `system`/null principal rejected at DB | |
| T09 | Per-conversion hash chain: predecessor digest computed inside the write transaction; unchainable write fails; chain-verification routine — mismatch quarantines with alert, never a warning | T08 | FP19 — tamper a row in test, verification quarantines; partial chain unrepresentable | |
| T10 | Outbox + queue tables + `SELECT … FOR UPDATE SKIP LOCKED` consumer skeleton; idempotency key = replay-request ID; schema supports async/retryable/idempotent projection reuse (M17) | T03 | HP18, FP6(groundwork) — schema review vs M17 criterion; duplicate insert with same key is a no-op | |
| T11 | Object-storage **port** interface + MinIO adapter (AWS SDK S3 client); every stored artifact carries data classification, retention date, retention class (`SPINE_POC`, 30-day lock); primary store holds references, never payloads | T05 | HP12, FP20 — Testcontainers MinIO: store/retrieve; landing without retention class rejected | |
| T12 | Anchoring job: lineage chain heads → object store via the port every 24h + on release; stale anchor >36h alerts; verification (recompute vs anchors) wired per release and after restore | T09, T11 | HP14 — clock-forced staleness test alerts; verification passes on intact chain | |
| T13 | Build-identity capture: Git commit SHA embedded at build time (Maven git-commit-id plugin), recorded in every lineage row and artifact each CLI/tool/worker writes | T08 | HP16 — lineage rows from two differently-built binaries show distinct SHAs | |

## WP3 — `screening` library (∥ WP2)

| Id | Task | Depends | EARS / verify | Pass/fail |
|----|------|---------|---------------|-----------|
| T14 | Screening API: one-line, in-process, no network; secret/PII redaction + injection screening rules; library version constant exposed for fixture markers | T01 | spec screening row (M35 cheap-call criterion) — unit benchmark: no network, single call site returns screened payload + verdict | |
| T15 | Red-team corpus seeded; regression suite reports **case count, source mix (seeded/operational/external), last-addition date, bypass rate** | T14 | HP15(report half, M36) — report artifact produced in CI with all four fields | |
| T16 | Quarantine-for-review failure mode: flagged payload quarantines (never hard-stops); release = recorded, attributable override (M18 no-silent-disable); quarantine record carries the **sampling flag** (novel source shapes + fixed random draw) and matches the future review-queue shape (M21/CF4) | T14 | FP23, HP15(flag half) — flagged fixture quarantines; override writes an attributed lineage row | |

## WP4 — Ingestion (∥ WP5, WP6)

| Id | Task | Depends | EARS / verify | Pass/fail |
|----|------|---------|---------------|-----------|
| T17 | Source-adapter contract + per-adapter deterministic canonicalization contract (interface in `conversion.ingestion`); no source-system type crosses out (F2 enforces) | T05 | C1, HP11(contract) — contract javadoc + two implementing stubs compile behind it | |
| T18 | Excel adapter (Apache POI): workbook + row-range canonicalization with normalized cell rendering; adapter contract tests on canonicalization determinism | T17 | HP4, HP11 — same workbook canonicalizes byte-identical across two runs/JVMs | |
| T19 | Octane REST adapter (API-key auth): record-fields canonical serialization; adapter contract tests | T17 | HP4, HP11 — recorded Octane fixture canonicalizes deterministically | |
| T20 | Hash-at-ingest: SHA-256 of canonicalized payload computed at intake, written to lineage; canonical snapshot stored in object storage under classification/retention rules; IR without digest fails schema validation | T17, T08, T11 | FP13, HP11(storage) — IR missing digest rejected; auditor can fetch stored snapshot by digest | |
| T21 | Screening at ingestion egress: every step's text passes the library; **F3 runtime half** — egress assertion rejects unscreened payloads (static half lives in T02) | T17, T14 | FP3(runtime) — bypass attempt in test is rejected at runtime, not just at CI | |
| T22 | Dual-fixture contract suite bound to the **contract** (not adapters): M16 real-workbook family (screened fixtures) + Octane record fixtures, running in CI from week 0 regardless of adapter completion | T17 | HP10 (M20) — suite runs green with one adapter stubbed out; removing a fixture family fails a meta-test | |
| T23 | Ambiguity flags in IR (never silently resolved); vault-key indirection schema rule — literal secret/credential in ingested data rejects the document | T05, T17 | HP4(flags), FP10 — ambiguous fixture yields flagged IR; credential-bearing fixture fails validation | |
| T24 | Fixture screening-marker CI check active: committed fixture derived from real source without the screening-library-version marker fails CI; raw workbooks never enter Git | T04, T14 | FP22 — unmarked fixture in a test branch fails the pipeline | |
| T25 | Ingestion CLI: run against Excel workbook or Octane test → schema-valid `TestCaseIR` JSON with source reference + snapshot digest; `corpusClass` recorded; lineage written as `svc-ingestion-cli` with build identity | T18–T21, T23, T13 | HP4, FP14, HP16 — end-to-end CLI run on a screened fixture emits valid IR + lineage row | |

## WP5 — Hierarchy tool (∥ WP4, WP6)

| Id | Task | Depends | EARS / verify | Pass/fail |
|----|------|---------|---------------|-----------|
| T26 | Perfecto session bootstrap + full `getPageSource` XML + Object Spy output capture | T05; Perfecto creds (external) | HP5 — live-device capture produces both raw outputs | |
| T27 | Pruned tree: interactive elements + their ancestors, suitable for IDE/workspace context | T26 | HP5 — pruned output contains every interactive node and its ancestor path, nothing else | |
| T28 | Screening at capture: **every** output (raw XML, Object Spy, pruned tree) passes the screening library **before it is written** — the Acquire UI Evidence call site (M35); two-half F3 construction applies | T26, T14 | FP21(capture half) — write path without screening call fails CI (static) and rejects at runtime | |
| T29 | Capture record: device + pool identity recorded on every capture; off-pinned-pool captures flagged (consumer is weeks 3–8 certification — M24 rider) | T26, T08 | HP5(identity) — off-pool capture in test carries the flag in its lineage row | |

## WP6 — Replay pipeline (∥ WP4, WP5)

| Id | Task | Depends | EARS / verify | Pass/fail |
|----|------|---------|---------------|-----------|
| T30 | Static gate: Spotless format, `mvn compile`, Checkstyle, Error Prone + custom checks — `Thread.sleep` ban; locator-manifest rule validating against the committed `LocatorCandidate` manifest only (object-repo behind read-only stub, C5) | T05 | HP6, FP7, FP8 — completes in seconds, zero device cost; sleeping/unmanifested-locator samples each fail | |
| T31 | On static-gate pass: replay request enqueued via producer's transactional outbox | T30, T10 | HP7(enqueue) — gate pass yields exactly one outbox row, in the producer's transaction | |
| T32 | Device-gate worker: SKIP LOCKED consume; **idempotent** — redelivery of the same request yields exactly one device run, no double-spent minutes; acquires pinned Perfecto pool by capability set; TestNG + pinned Appium/driver; single run; holds **no gateway credential** (ADR 0013 — asserted by T02's ArchUnit rule); runs as `svc-devicegate-worker` | T10, T08; Perfecto creds (external) | FP6, HP7(execute) — duplicate delivery test produces one run; credential-config assertion green | |
| T33 | Artifact pull: per-artifact SHA-256 recorded in append-only lineage **at landing, before any downstream read** (read without digest fails — M9); each artifact passes screening at landing (M35); landed to object storage with retention class | T32, T11, T14 | FP12, FP21(landing half) — read-before-digest attempt fails; unscreened landing rejected | |
| T34 | Record-actual: actual execution context (device model/ID, OS, Appium server version, stack identifiers) recorded alongside the requested set, delta explicit; mismatch on any **pinned** facet → quarantine + alert (same persisted status as T35's) | T32, T08 | FP16 — substituted-device simulation quarantines, never counts as a normal run | |
| T35 | Classification: deterministic rules mapping Appium exception types + Perfecto failure reasons → `{LOCATOR_NOT_FOUND, STALE_ELEMENT, TIMEOUT_SYNC, ASSERTION_MISMATCH, APP_CRASH, DATA_PRECONDITION, ENV_INFRA}`; unmapped outcome → quarantine **status** (not an eighth class) + alert | T32 | HP8, FP15 — rule table covers fixture set; novel exception type quarantines | |
| T36 | ENV_INFRA hygiene: requeue with cap 3, backoff 1m→5m→15m (config); cap exhausted → dead-letter into persisted quarantine + alert, never dropped; quarantine record shape = future review-queue record (M21/CF4) | T35, T10 | FP9 — forced-infra-failure test requeues 3× then dead-letters with alert | |
| T37 | `ReplayReport` emission: validates against committed schema; full applicable pinning set (F6); outcome fields sufficient to derive K-of-K later without vendor aggregates (M10b, K=1 baseline honest) | T32, T35, T07 | FP5, HP17 — report missing a pinning field records no verdict; K-derivation fields present | |
| T38 | Smart Reporting contract tests: recorded Perfecto fixture responses; vendor format drift fails a test the day it appears (register S2/S3) | T33 | HP9 (M10) — mutated fixture (simulated drift) fails the suite | |
| T39 | Gate-run lineage rows (static + device) carry the **CI-runner environment**: runner-image digest + JDK/Maven/pipeline-tool versions (M28) | T08, T04 | FP5(runner-env clause) — gate-run row without runner digest fails validation | |

## WP7 — Week-3 gate

| Id | Task | Depends | EARS / verify | Pass/fail |
|----|------|---------|---------------|-----------|
| T40 | Commit the hand-written Appium reference test; credential resolved through an **injected reference** from the CI secret store, never a literal (M34; vault binds later as provider swap) | T30 | FP24 — test authenticates in CI with no literal in the repo; gitleaks stays quiet | |
| T41 | **Gate clause a:** the committed test flows end to end — static gate → device gate on a real Perfecto device → classification — yielding a `ReplayReport` valid against the committed schema with the complete applicable pinning set; gate evidence recorded in lineage with runner environment | T40, T31–T37, T39 | HP19(a) — the report validates; every pipeline hop has its lineage row | |
| T42 | Set the real-input floor (M19): **blocked on the M16 corpus request returning** — placeholder ≥5 distinct real workbooks; setting it is a recorded plan-value update, not a guess. If the corpus slips past week 2, raise sdd-replan | external: M16 corpus | plan §4 — floor value recorded in plan + this file before T43 runs | |
| T43 | **Gate clause b:** ingestion CLI has produced schema-valid, screening-passed `TestCaseIR` from the real M16 Excel corpus at or above the floor, recorded `REAL_INGESTED` in lineage; fixtures-only evidence does not satisfy | T25, T42 | HP19(b), FP14 — lineage query counts `REAL_INGESTED` rows ≥ floor | |

## Parallelization notes

- **Hard sequence:** T01→T02/T03/T04 must all land before any feature task (M18 — a build without wired fitness functions is not a valid baseline).
- WP2 (T08–T13) ∥ WP3 (T14–T16) after WP1.
- WP4 ∥ WP5 ∥ WP6 after WP1–WP3, with cross-links: T21/T24/T28/T33 need T14; T20/T25/T29/T33–T39 need T08/T11.
- **External blockers (start-anyway rule):** Perfecto creds gate T26/T32 execution (code can be written against recorded fixtures first); Octane API key gates T19's live leg; M16 corpus gates T42/T43 and T22's real-family fixtures (screened); MinIO/Postgres provisioning covered by Testcontainers until real infra lands. Nothing external gates WP0/WP1/WP3.
- **Do-regardless:** no LLM call, no gateway credential, no raw workbook in Git, no F1–F7 weakening without a recorded decision (M18).

## Analyze checklist (Stage 4 — run 2026-07-28)

- [x] Spec ↔ plan ↔ tasks: S1 (spine-only scope — no weeks-3–8 task present), S2 (all tasks land in the new repo), C1 (T18+T19 behind T17's contract), C2 (T10/T31/T32), C3 (Postgres via T03, flagged assumption), C4 (T05/T07 markers), C5 (T30 manifest-only + objectrepo stub)
- [x] Failure paths FP1–FP25 each covered by ≥1 task with a verifiable fail condition: FP1/FP2/FP4→T02; FP3→T02+T21; FP5→T07/T37/T39; FP6→T32; FP7/FP8→T30; FP9→T36; FP10→T23; FP11→T08; FP12→T33; FP13→T20+T07; FP14→T03/T07/T25/T43; FP15→T35; FP16→T34; FP17→T03+T08; FP18→T03+T04; FP19→T09; FP20→T03/T07/T11; FP21→T28+T33; FP22→T24; FP23→T16; FP24→T04+T40; FP25→T04
- [x] Happy-path criteria HP1–HP19 mapped: HP1→T01; HP2→T01–T04; HP3→T05+T06; HP4→T18/T19/T23/T25; HP5→T26–T29; HP6→T30; HP7→T31–T33; HP8→T35; HP9→T38; HP10→T22; HP11→T17–T20; HP12→T11; HP13→T08; HP14→T12; HP15→T15+T16; HP16→T13+T25; HP17→T37; HP18→T10; HP19→T41+T43
- [x] Carry-forwards CF1–CF11: spine provisions only — CF1→T33; CF2/CF6→T37; CF3→T10; CF4→T16; CF5 none needed; CF7→T17–T20 canonicalization; CF8→T04+T40; CF9/CF11→T08 principals (+T11 retention); CF10→T32. No CF machinery built early
- [x] Constitution: trade-offs surfaced per decision (plan §1/§6); three G1 abstractions each carry the simpler-thing-rejected rationale (plan §1)
- [x] Grounding: ADRs 0001–0013, both worksheets, `logical-components.md`, `blueprint-revision-v2.md:123` (gate quote verbatim), constitution, `.sdd/binding.toml` all verified present; every new-repo path is create-only; all new dependencies (victools, ArchUnit, Testcontainers, gitleaks, POI, AWS SDK) belong to the new repo's `pom.xml`/`ci/` — deliverables of T01/T04, not workspace deps
- [x] check_gate / test_gate `<none>` in this workspace — the new repo's CI is the deliverable (T04); baseline-green requirement transfers to T01–T04 completing before any feature task
- [x] ADR posture: no new ADR raised; ADR 0011 PROBE-PENDING and C3 Postgres assumption carried as the two standing sdd-replan triggers (with T42's M16 floor)

**Result: 0 CRITICAL findings.** One OPEN value carried honestly (T42 real-input floor, blocked on the M16 corpus); two external replan triggers named above.

## Sign-off gate

**TASKS-OK GRANTED — owner 2026-08-10.** The 43-task board (T01–T43) and amendments **A1–A7** are approved. **Advance to Stage 6 (`sdd-implement`) is DEFERRED** pending toolchain provisioning — Temurin **JDK 21.0.8+**, **Maven ≥3.9.16** (`<4.0.0`), a **running Docker daemon** (Testcontainers), and **git** — because this environment cannot yet produce the red→green per-task evidence `sdd-implement` requires. No repo is scaffolded; the spine artifacts stay as docs.

This stamp **resolves the `pending TASKS-OK` state** on every amendment A1–A7. Their **file-level application is a task deliverable, not gate bookkeeping**, so it executes when implement runs — A1/A2/A4/A5/A6 as **T01**, A3 as **T02**, and **A7's staged `AGENTS.md` deltas (bump `spine-repo/AGENTS.md` v1.0.0 → 1.1.0) + `[A7]` tags on T04/T02**; nothing is applied to a task cell or to the content-final `AGENTS.md` until then.

Two standing **replan triggers** remain: T42's M16 real-input floor and the ADR 0011 probe outcome. **Resume checkpoint:** memory `spine-tasks-ok-implement-hold` (provisioning list; first task on resume = T01).

---

## Replan R1 — 2026-07-31 (APPROVED — REPLAN-OK 2026-07-31; Lane 1 applied same day)

**Trigger:** (b) scope-change proposals + (c) review findings. `docs/research/o1-pipeline-walkthrough.md` introduced A0 Normalizer (LLM intake), the ASH-Capture subsystem (ADR 0014 in flight), K=3/5 device runs, and PostgreSQL ScreenGraph storage; a 7-agent critical review (2026-07-31, all 28 findings CONFIRMED — full report: `docs/research/o1-pipeline-review.md`) found the walkthrough contradicts the signed-off spec/plan in several load-bearing places and that the proposals carry undecided ADR-grade obligations.

**Replan verdict: T01–T43 all STAY, unchanged, in the existing order. Zero spine tasks are invalidated.** The signed-off spec (2026-07-27) and plan (PLAN-OK 2026-07-28) remain normative; every contradiction the review confirmed lives in the *walkthrough document* (descriptive/PROPOSED material), not in the task board. Per the skill's backward-propagation rule, no spec edit is made here — the scope-bearing items route forward to `sdd-spec`/`arch-decide` below; the walkthrough gets editorial corrections so it stops mis-describing the decided system.

### Task-impact confirmation (why nothing slips)

| Tasks | Status | Reason |
|---|---|---|
| T26–T29 (WP5 hierarchy tool) | **STAY** | Manual `hierarchy-tool` is the decided design; ASH-Capture supersedes it only if/when ADR 0014 is accepted. Building WP5 is not wasted — it is ASH-Capture's escape hatch and fallback either way. |
| T03 (Flyway V1) | **STAY** | ScreenGraph tables are ADR 0014 scope — do **not** add them to V1; graph storage joins a later migration after the ADR. |
| T37 (ReplayReport, K=1 honest) | **STAY — reaffirmed** | The walkthrough's K=3/5 is an unrecorded change to a signed-off value (CF6). K stays 1 until a recorded decision says otherwise (D6 below). |
| T14–T16, T21, T28, T33 (screening) | **STAY — reaffirmed** | The review found *zero* ADR 0009 screening mentions in the walkthrough's 886 lines; the task board already implements screening at every decided egress. The defect is in the doc, not the plan. |
| T42/T43 + ADR 0011 probe | **STAY** | The two pre-existing standing replan triggers are untouched by R1. |

### Lane 1 — Editorial fixes (no new decisions; apply to `o1-pipeline-walkthrough.md` + `.html` + `o1-diagrams/`)

| Id | Fix | Finding |
|---|---|---|
| E1 | Redraw §1/§8 (and diagram captions) so LLM Code Generation sits **outside** the "LLM-free spine" box, matching the spec boundary | Critical #1 |
| E2 | Phase-label every end-state behavior (K-runs, auto-capture, unbounded evaluator loop, mechanical CERTIFIED) as weeks-3-8+/target, not current fact; certification stays an attributable individual decision (CF9) | Criticals #2, #7 |
| E3 | Fix the mock ReplayReport: `runs: 1`, seven-class classifier verdict, full F6 pinning set | Critical #2, Serious |
| E4 | Rename "F1 (flywheel)" — F1 is the no-LLM fitness function; the collision is an audit hazard | Serious #F18 |
| E5 | Mark all coverage numbers (>90%, <10%, ~20% cold-miss) as unmeasured targets; fix §12 provenance (A0 is NEW this session, not already-planned) | Criticals #3, #5 |
| E6 | Demote NavigationManifest from "the spine's input / audit pin" to *capture provenance record* (no spine stage consumes it); add explicit ADR 0009 screening call-outs at A0 intake and every discovery-loop LLM ingress/egress | Criticals #3, #6 |

### Lane 2 — ADR-grade decisions (route → `sdd-spec` / `arch-decide`; blocked-by-decision, not by build)

| Id | Decision needed | Home |
|---|---|---|
| D1 | ADR 0014 must *decide* (not describe): proposer/executor **process split** so no worker holds both the gateway credential and the authenticated device session (ADR 0013); **signature re-keying** on legitimate screen change (the discovery-termination defect — success predicate currently compares to the stale signature, so ~20% of screens/release deterministically exhaust budget into the escape hatch); deep-link **URL denylist** + TYPE-action policy; edge **commit/quarantine semantics** + single-writer serialization (concurrent capture forks the version chain); cross-backend signature comparability; ADR 0009 call-site map; auto-commit vs. reviewed graph writes (a dropped human control on a spine-adjacent artifact class) | **DRAFTED 2026-07-31** via sdd-spec Stage 2 (10-agent workflow, 4/4 facets UPHELD_WITH_AMENDMENTS, 36 amendments applied): `adr_home/0014-confine-the-llm-to-proposing-in-ash-capture.md` (Proposed) + `docs/sdd/specs/mobile-test-automation-ash-capture.spec.md` (clarify pass complete — C1 auto-RE-KEY strict path, C2 A11 override + lease fallback accepted, C3 ASH-scoped 0009 flip, C4 baseline blocks at certification only, C5 flag-don't-invalidate recall). **GATE CLOSED 2026-07-31: SPEC-OK + ADR 0014 Accepted; ADR 0001 seam-vocabulary and ADR 0009 flip (3-of-3, ASH-scoped) amendments recorded in their home ADRs; A11 override ratified.** Lane-3 S1 (re-keying design) delivered; **S2 spike UNBLOCKED**. Next: Stage 3 plan + tasks for the ASH repo. |
| D2 | A0 Normalizer: ratify or defer. New LLM ingress consuming raw untrusted Octane/Jira text → ADR 0009 screening obligation (flip-counter 2/3→3/3 territory); must live **outside** the spine repo (F1 CI-fails it) | **DECIDED 2026-08-01 via sdd-spec Stage 2 (6-agent audit, 3/3 lenses → FOLD+DEFER, high confidence; RATIFY refused): [ADR 0015](../../architecture/adrs/application/mobile-test-automation/0015-defer-the-llm-normalizer-a0-and-fold-deterministic-canonicalization-into-ingestion.md) Accepted.** A0 LLM stage **DEFERRED** (evidence-gated re-open on a measured A1 parse-failure rate); minimal deterministic phrase-canon + noise-strip **FOLDED** into the M15 adapter surface (spine spec A0-fold amendment, criteria A0-1..A0-6); screenContext scope-ruled to A2. **Flip framing corrected: A0 trips NO fourth flip** — both flows are second-paths into already-screened classes (1)/(3), stale "2/3→3/3" superseded by ADR 0014's amendment. Walkthrough §2.0/§8/§9/§12 updated to DEFERRED. |
| D3 | ADR 0012 amendment: cross-version graph lineage chain — `lineage_digest` currently "joins" a chain 0012 doesn't construct (same gap as §7.5 memory red-team) | **DECIDED 2026-08-01 (sdd-spec Stage 2; 7-agent design→adversarial-verify workflow, UPHELD_WITH_AMENDMENTS): [ADR 0012](../../architecture/adrs/application/mobile-test-automation/0012-tamper-evident-lineage-hash-chain-anchored-in-immutable-storage.md) Graph-version lineage chain amendment added, Status unchanged (Accepted).** Per-`app_version` chain (never global — same over-scoping rejection as the base 0012:104-105); canonical digest input (`app_version`+`prev_version_sha`+`graph_version_sha`+node/edge-set-digest, timestamps/`derived_from` excluded); genesis constant `"GRAPHCHAIN-GENESIS-v1"` so `lineage_digest NOT NULL` holds at root; chain-membership ruling (re-key/quarantine/promotion/`APPROVE_GRAPH_BASELINE`/`REJECTED_URL` rows **in**; `screen_node_signatures`/`screen_edge_status` observation logs **out**, grant-protected-only — the honest limit); graph grant stays ADR-0014-owned (F10), inventoried-together not re-owned. **This was the hard build blocker — its acceptance LIFTS the ScreenGraph migration gate** (0014:355-357, :797-798) on a mechanical committed `d3-accepted` marker; ScreenGraph DDL may now leave the V1 hold. |
| D4 | ADR 0010: define "prod-grade data" — production-*realistic* vs production-*derived*; the PII flip condition hangs on this one adjective | **DECIDED 2026-08-01 (sdd-spec Stage 2; same workflow, UPHELD_WITH_AMENDMENTS): [ADR 0010](../../architecture/adrs/application/mobile-test-automation/0010-security-review-as-a-parallel-non-blocking-track.md) Prod-grade-data definition amendment added, Status unchanged (Accepted).** SYNTHETIC vs PRODUCTION_DERIVED as a **provenance predicate** (masked production data = PRODUCTION_DERIVED; deny-by-default when unattested; one manifest covers corpus AND environment) so ADR 0014's `dataClass` is machine-checkable parallel to `envClass`; a PRODUCTION_DERIVED attestation **both** suspends discovery at runtime (filed as an incident record) **and** reopens ADR 0010 as a governance event. **Retention-class enum for `capture_run_edges` (0014:363-367) SPLIT OUT to a named companion ADR 0006 rider — now ACCEPTED 2026-08-01: `CONSUMED\|FORENSIC\|PENDING_MINT`** (this ADR owns the provenance line because it owns the flip trigger; ADR 0006 owns retention because retention is lifecycle). |
| D5 | ADR 0007 ruling: graph-mutation invocation model (walkthrough mischaracterizes the outbox) | **DECIDED 2026-08-01 (sdd-spec Stage 2; same workflow, UPHELD_WITH_AMENDMENTS): [ADR 0007](../../architecture/adrs/application/mobile-test-automation/0007-queue-two-seams-outbox-provenance-writes.md) ASH-Capture graph-mutation ruling added, Status unchanged (Accepted).** Ruling 1: ScreenGraph mutations are **synchronous same-local-transaction** writes (ratifies ADR 0014 D-D's rejection of walkthrough §13.6 as a positive 0007 ruling). Ruling 2: park-and-sweep **PERMITTED** as a non-precedential intra-process-family retry over `capture_run_edges` on two structural bounds (single-owner + non-precedential). Ruling 3: **default fail-loud** — fail-loud-and-recapture is conformant ONLY for deterministically re-derivable re-verification results; quarantine/BROKEN commits (human/screening-originated, not replay-derivable) must park or fail-loud-with-incident, never silently recapture. **Keep/kill of the buffer is S2-evidence-gated on measured graph-commit CAS-contention rate.** |
| D6 | K policy: keep K=1 (spec M10b) or record a CF6 decision raising it; the walkthrough cannot decide this silently | **DECIDED 2026-08-01 (sdd-spec Stage 2; 6-agent workflow: 3 lenses → 2 skeptics → synthesis; unanimous DEFER, high confidence, survives both skeptics): CF6 recorded decision — replay K = 1 RETAINED for the spine, raise pre-registered as an event-gated entry criterion.** First invocation of CF6's "changing K is a recorded decision" clause (spec.md:383). K stays 1 (M10b baseline); a raise to 3/5 (blueprint:77) is gated on the S2 flake-base-rate threshold and **event-anchored** — no certification verdict may be issued while the K re-decision is un-taken (owner ruled soft phase-checkpoint + hard verdict-event forcing function, because phase boundaries are elastic). Inconclusive S2 → hold K=1 + bounded re-run deadline. **A1/G1:** RAISE-now rejected (flakiness verdict with no weeks-0–3 consumer, 3–5× device-minutes on an unmeasured pool, uninterpretable pass-ratio); bare KEEP rejected narrowly (unassigned evaporation gap). Constraint-safe (no M10b reversal, EXERCISES CF6, no ASH-K touch, no schema). Full text: scratchpad `d6-decision-final.md`; log 2026-08-01. **Closes Replan R1 Lane 2 (D1–D6 all DECIDED).** |

### Lane 3 — Measurement spike (strictly sequenced)

S1 **first**: design the signature re-keying mechanism (D1) — the §12.4 spike is worthless while the loop cannot terminate on changed screens. **S1 DELIVERED** (ADR 0014 Accepted 2026-07-31). S2 then: measure escape-hatch/ANCHOR_LESS rate, cross-backend hash stability, month-start device-minutes, human touches per test, **and (added by D5, 2026-08-01) measured graph-commit CAS-contention rate**, **and (added by D6, 2026-08-01) a measured device-lab flake-base-rate** — with pass/kill thresholds recorded **before** measuring, so the ~90/<10 claims can be retired or falsified and the D5 park-and-sweep buffer is retired-or-kept by data (below the CAS-contention threshold, the buffer is dropped for fail-loud-and-recapture by recorded operating decision, no further ADR needed). **S2 UNBLOCKED** (D1 delivered).

**D6 flake-base-rate datum (pre-registered decision structure; S2 owner sets the numeric value against the real Perfecto pool):** S2 MUST report a numbered device-lab flake base-rate, evaluated against three pre-committed CF6 branches for the replay-K re-decision — **raise-forces** (measured base-rate ≥ the threshold that makes a K=1 gate unsafe → K raised to 3/5 via a CF6 recorded decision, pass-ratio threshold set at raise time per blueprint:119); **keep-justifies** (base-rate low enough that K=1's binary pass/fail is honest → K held at 1, recorded); **inconclusive** (ambiguous/insufficient sample → hold K=1 AND schedule a bounded S2 re-run, recorded as its own CF6 decision — never an indefinite hold). D6 fixes these three branches; S2 sets the numeric threshold. The K re-decision is **event-gated**: no certification verdict may be issued while it is un-taken (D6, 2026-08-01).

### Replan R1 Lane-2 status (2026-08-01): ALL DECIDED

**D1 ✅ (ADR 0014 Accepted) · D2 ✅ (ADR 0015 Accepted) · D3 ✅ (ADR 0012 amend) · D4 ✅ (ADR 0010 amend) · D5 ✅ (ADR 0007 amend) · D6 ✅ (CF6 recorded decision).** Lane 2 is fully closed. The ADR 0006 retention rider (spun out of D4) is now **✅ ACCEPTED 2026-08-01** (`CONSUMED\|FORENSIC\|PENDING_MINT`). The one remaining open thread is NOT a Lane-2 decision: the S2 measurement spike (Lane 3, unblocked, now carrying the CAS-contention + flake-base-rate pre-registered thresholds).

### Open items after the D3/D4/D5 gate (2026-08-01)

- **ADR 0006 retention-class rider (✅ ACCEPTED 2026-08-01)** — D4 split the retention-class enum for `capture_run_edges` (0014:363-367) out to a named companion ADR 0006 rider; that rider is now **Accepted**. Enum `CONSUMED | FORENSIC | PENDING_MINT`, one value per distinct purge behavior — `CONSUMED` (event-purged in-band after mint + read-gated backstop), `FORENSIC` (bounded 30-day CF6-governed TTL from a new `terminal_outcome_at` column, for zero-graph-row terminal-failure staging), `PENDING_MINT` (hands-off; folds parked-contended + escape-hatch rows). Strictly conversion-state (no value outlives certification); interim ships two present-but-unconstrained columns, the enum CHECK is the one-cell follow-up (ASH task A13b). Recorded as an ADR 0006 amendment, Status unchanged (Accepted). **Never blocked the ScreenGraph migration** (lifted by D3); it gated only the staging table's retention attestation.
- **Graph-migration gate LIFTED (2026-08-01)** — D3 Accepted satisfies ADR 0014 F10 (0014:797-798); ScreenGraph DDL may leave the V1-no-graph-DDL hold once the committed `d3-accepted` marker lands (the marker itself is the mechanical CI predicate, not a manual assertion).

### ASH-Capture design improvements surfaced by the D3/D4/D5 gate (2026-08-01 — for the ASH Stage-3 build, not applied to the base ADRs here)

Seven consolidated improvements the three amendment facets found in ADR 0014 while closing D3/D4/D5. These strengthen the ASH design; they are recorded here as Stage-3 build inputs (some are already reflected in the amendment bodies, noted below):

1. **`dataClass` as a first-class startup attestation symmetric with `envClass` (D4).** Extend F11 so `dataClass` and `envClass` are checked by the *same* deny-by-default, build-failing startup-assertion construction (0014:659-664). Today `dataClass` is a bare reserved field with only a suspension behavior — an unattested `PRODUCTION_DERIVED` env passes because nothing populates it (latent false-green).
2. **One provenance root — the SYNTHETIC manifest covers corpus AND environment, not corpus alone (D4).** A synthetic corpus in a production-derived environment lets the loop *read* real customer values off live screens even while it only *types* synthetic ones, defeating the injection-blast-radius argument (0014:154). *Already promoted into the normative D4 amendment body.*
3. **Inventory the ADR 0012 lineage grant and the ADR 0014 F10 graph grant as one drift-detection set (D3).** ADR 0014 D-D mirrored rather than inherited 0012's grant/CI construction (0014:372-377) — two independently-maintained assertions over overlapping append-only invariants. arch-validate checks both together (NOT ownership transfer — graph grant stays ADR-0014-owned). *Already in the D3 amendment body (point 5).*
4. **Unify the two per-release detective recomputes into one non-racing pass (D3).** ADR 0014's chain-verification job (0014:409-411) and D3's graph chain-head verification share trigger (per-release + post-restore) and tables — run as one pass so they do not race each other's quarantine writes and share one quarantine-reason provenance.
5. **Explicit graph `lineage_digest` genesis (D3).** The `"GRAPHCHAIN-GENESIS-v1"` constant + canonical field-sorted digest input prevents an implementer setting root `lineage_digest = NULL` (breaks `NOT NULL`) or back-linking to the prior release (breaks per-`app_version` linearity). *Already in the D3 amendment body (point 2).*
6. **Cross-link ADR 0014 D-D to the dated 0007 D5 ruling (D5).** D-D rejected the §13.6 outbox routing citing 0007 before 0007 had ruled; now that D5 has landed, add a one-line back-reference from 0014 D-D to the dated 0007 ruling (mirroring the two-sided ADR 0009 flip pattern) so a reader of 0014 alone can verify the outbox rejection is authorized by 0007's own owner. *Small ADR 0014 edit, deferred to the ASH Stage-3 pass.*
7. **Add measured graph-commit CAS-contention rate to S2's pre-registered thresholds (D5).** *Already applied to Lane 3 S2 above* — it is the single datum that decides whether the park-and-sweep buffer earns its machinery.

### Gate + routing (on REPLAN-OK)

Lane 1 → apply now (doc-only). Lane 2 → **sdd-spec/arch-decide** next session(s). Lane 3 → blocked on D1. Spine board → unchanged; still awaiting its own TASKS-OK. Decision-log entry (2–4 lines) written on approval.
