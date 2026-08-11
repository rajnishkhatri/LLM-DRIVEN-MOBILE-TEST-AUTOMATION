---
type: reference
title: 'ArchUnit Seeds — Mechanical Enforcement for the o1 and o7 Coding Rules'
description: >-
  CI-blocking fitness-function seeds for the mechanical subset of
  rules-catalog.md (A–E, o1/spine — including B-5 no-registry, spine plan:14,
  approved, wired by spine T02), plus the three ADR-named o7 interpreter
  assertions (F, ADR 0016/0017, both Proposed). Copy into the workspace's
  architecture-test module, resolve {{placeholders}} from the binding, and wire
  into the build. F1/F2/F4 are load-bearing per ADR 0001/0006 — their
  suppression requires a superseding ADR.
tags: [coding-rules, o1-pipeline, o7-interpreter, archunit, fitness-functions]
---

# ArchUnit Seeds

Rules that a machine can enforce must not live as prose (catalog header).
This file is the mechanical subset of `rules-catalog.md`, as ArchUnit test
seeds plus two non-ArchUnit checks (migration + PMD). Resolve
`{{base_package}}` and seam globs from the binding before committing.

Conventions: one test class `ArchitectureRulesTest` (or split per group);
`@AnalyzeClasses(packages = "{{base_package}}")`; JUnit 5. Seeds are
starting points — tighten package globs to the workspace's real tree on
first run, and record any weakening as a finding, not a tweak.

> **Multi-glob binding values are LISTS, not `" | "`-joined strings.**
> ArchUnit's `resideInAPackage` / `resideOutsideOfPackage` take **one** package
> identifier. A joined string like `"..a.. | ..b.."` is not a package
> identifier and matches nothing — and because these are `noClasses().that()`
> selectors, a never-matching *exclusion* silently widens the rule to every
> class in the build, so the legitimate seam code itself starts failing. It
> looks like a false positive and gets "fixed" by weakening the rule. Keys that
> can hold more than one glob (`seams.source_adapter_internal_packages`,
> `seams.async_seam_packages`) are TOML arrays, and the rules that read them
> use the plural forms `resideInAnyPackage(…)` / `resideOutsideOfPackages(…)`.
> Corrected in both this file and `binding.template.toml` on 2026-08-09, found
> while resolving the spine binding. **If an o1 workspace already installed the
> pre-fix template, re-check D-2 and B-2 there** — a green run against the
> joined form proved nothing.

```java
@AnalyzeClasses(packages = "{{base_package}}",
    importOptions = ImportOption.DoNotIncludeTests.class)
class ArchitectureRulesTest {

  // ── A-1 (CR-01): cross-module access only via published api packages.
  // ADR 0005 Compliance. One @ArchTest per module pair, or use this generic:
  @ArchTest
  static final ArchRule modules_accessed_only_via_api =
      noClasses().that().resideInAPackage("{{base_package}}.conversion..")
          .should().dependOnClassesThat(
              resideInAPackage("{{base_package}}.evidence..")
                  .and(not(resideInAPackage("{{base_package}}.evidence.api.."))))
          .because("CR-01/ADR-0005: modules are imported only via their published API");
  // Repeat for each ordered module pair (6 rules for 3 modules), or adopt
  // Spring Modulith's ApplicationModules.verify() if the workspace uses it.

  // ── A-2 (CR-02): no package cycles.
  @ArchTest
  static final ArchRule no_package_cycles =
      slices().matching("{{base_package}}.(**)")
          .should().beFreeOfCycles()
          .because("CR-02: the dependency graph is a DAG; break cycles via DIP");

  // ── A-3 (CR-03): no technical-layer package names.
  @ArchTest
  static final ArchRule packages_scream_domain =
      noClasses().should().resideInAnyPackage(
              "..controllers..", "..services..", "..repositories..",
              "..impl..", "..util..", "..utils..", "..helpers..", "..managers..")
          .because("CR-03/ADR-0005: packages are domain concepts "
              + "(ingestion, replay, certification, lineage...), never layers");

  // ── A-4 (CR-04): implementations behind a seam are not public.
  @ArchTest
  static final ArchRule seam_impls_not_public =
      classes().that().haveSimpleNameEndingWith("Adapter")
          .or().haveSimpleNameEndingWith("Impl")
          .and().resideOutsideOfPackage("..api..")
          .should().notBePublic()
          .because("CR-04: public means published; impls are wired by config, not imported");

  // ── B-1 (CR-05 / F1, LOAD-BEARING): no provider/gateway types outside the
  // Invoke Models adapter. Suppression requires a superseding ADR (ADR 0001).
  // The ban list comes from the binding ALONE — expand
  // seams.provider_sdks.packages, never this line. The three SDK roots that used
  // to be hardcoded here are already the binding's default value; keeping both
  // copies is how the two drift apart.
  @ArchTest
  static final ArchRule f1_invoke_models_is_the_only_model_seam =
      noClasses().that().resideOutsideOfPackage("{{seam.invoke_models_adapter}}")
          .should().dependOnClassesThat().resideInAnyPackage(
              "{{seam.provider_sdks.packages}}")
          .because("CR-05/ADR-0001 F1: every model call goes through the Invoke Models seam");

  // ── B-2 (CR-06 / F2, LOAD-BEARING): no source-system type leaves ingestion;
  // only IR crosses. Approximate: source-adapter internals stay in their package.
  // NOTE the plural `resideInAnyPackage` — {{seam.source_adapter_internal_packages}}
  // is a LIST (one glob per vendor-typed adapter). See the multi-glob warning
  // below this class.
  @ArchTest
  static final ArchRule f2_only_ir_leaves_ingestion =
      noClasses().that().resideOutsideOfPackage("{{seam.source_adapter_packages}}")
          .should().dependOnClassesThat()
          .resideInAnyPackage("{{seam.source_adapter_internal_packages}}")
          .because("CR-06/ADR-0001 F2: the IR spine is the only vocabulary that "
              + "crosses; source-system types never leave their adapter");

  // ── B-3 (CR-07): storage clients only inside the storage-port adapter.
  @ArchTest
  static final ArchRule storage_only_via_port =
      noClasses().that().resideOutsideOfPackage("{{seam.storage_port_adapter}}")
          .should().dependOnClassesThat().resideInAnyPackage(
              "software.amazon.awssdk.services.s3..", "io.minio..")
          .because("CR-07/ADR-0011: no evidence artifact is written outside the port");

  // ── B-3b (CR-07): no filesystem writes in the evidence module outside the
  // port adapter — closes the java.nio.file stopgap gap found in eval iteration 1.
  @ArchTest
  static final ArchRule no_filesystem_evidence_stopgaps =
      noClasses().that().resideInAPackage("{{base_package}}.evidence..")
          .and().resideOutsideOfPackage("{{seam.storage_port_adapter}}")
          .should().dependOnClassesThat().resideInAnyPackage("java.nio.file..")
          .orShould().dependOnClassesThat().haveFullyQualifiedName("java.io.File")
          .because("CR-07/ADR-0011: filesystem stopgaps are how a retention "
              + "design gets set by accident");

  // ── B-4 (CR-08): no backchannel to seam implementations.
  @ArchTest
  static final ArchRule no_seam_backchannels =
      noClasses().that().resideOutsideOfPackage("{{seam.invoke_models_adapter}}")
          .should().dependOnClassesThat()
          .haveSimpleNameEndingWith("InvokeModelsAdapter")  // adjust to real impl names
          .because("CR-08: partial boundaries erode via impl imports "
              + "(partial-boundaries.md); clients know only the interface");

  // ── B-5 (spine plan:14, APPROVED): no plug-in registry at a spine seam.
  // Provenance is the approved spine plan, NOT ADR 0017 (Proposed) — this rule
  // stands on its own and does not wait for the o7 gate. Wired by spine T02.
  // Why it is not covered by F1/F2: those guard WHAT crosses a seam; this
  // guards HOW an implementation is bound to one. A ServiceLoader-based
  // registry passes F1 and F2 unharmed. Scope: the three CR-08 seams only —
  // the C-MIG driver seam is o7's and is guarded by F-1 below.
  @ArchTest
  static final ArchRule spine_seams_bound_by_spring_di_not_by_a_registry =
      noClasses().that().resideInAnyPackage(
              "{{seam.source_adapter_packages}}",
              "{{seam.invoke_models_adapter}}",
              "{{seam.storage_port_adapter}}")
          .should().dependOnClassesThat().haveFullyQualifiedName("java.util.ServiceLoader")
          .orShould().dependOnClassesThat().resideInAnyPackage(
              "org.reflections..", "io.github.classgraph..")
          .orShould().dependOnClassesThat().haveFullyQualifiedName(
              "org.springframework.core.io.support.SpringFactoriesLoader")
          .orShould().dependOnClassesThat().haveFullyQualifiedName(
              "org.springframework.context.annotation."
              + "ClassPathScanningCandidateComponentProvider")
          .because("spine plan:14 (approved): source adapters are Spring-selected "
              + "implementations of one interface — no registry, no plug-in "
              + "machinery, no runtime discovery; the declined-microkernel decision "
              + "(ADR 0005/0001) is reopened by a superseding ADR, not by a "
              + "ServiceLoader");

  // ── C-1 (CR-11): framework-free core.
  @ArchTest
  static final ArchRule core_is_framework_free =
      noClasses().that().resideInAnyPackage("..domain..", "..usecase..")
          .should().dependOnClassesThat().resideInAnyPackage(
              "org.springframework..", "jakarta.persistence..",
              "jakarta.servlet..", "com.fasterxml.jackson.annotation..")
          .because("CR-11: entities and use cases import no framework; "
              + "wiring lives in the composition root");

  // ── C-2 (CR-12): web edges and persistence entities never meet.
  @ArchTest
  static final ArchRule edges_dont_touch_entities =
      noClasses().that().resideInAnyPackage("..web..", "..cli..")
          .should().dependOnClassesThat()
          .areAnnotatedWith("jakarta.persistence.Entity")
          .because("CR-12: boundaries carry simple DTOs, never persistence rows");

  // ── D-2 (CR-15): async machinery confined to the two decided seams.
  // Covers JDK fire-and-forget primitives too — the CompletableFuture gap
  // found in eval iteration 1.
  // NOTE the plural `resideOutsideOfPackages` — {{seam.async_seam_packages}} is
  // a LIST (one glob per decided seam). See the multi-glob warning below.
  @ArchTest
  static final ArchRule async_only_at_decided_seams =
      noClasses().that().resideOutsideOfPackages("{{seam.async_seam_packages}}")
          .should().dependOnClassesThat().resideInAnyPackage(
              "org.springframework.jms..", "org.springframework.amqp..",
              "org.springframework.kafka..")
          .orShould().dependOnClassesThat().haveNameMatching(
              "java\\.util\\.concurrent\\.(CompletableFuture|ExecutorService|"
              + "ScheduledExecutorService|ForkJoinPool|Executors)")
          .orShould().beAnnotatedWith("org.springframework.scheduling.annotation.Async")
          .because("CR-15/ADR-0007: queues exist at exactly two seams — "
              + "JDK fire-and-forget included; a new async edge needs a superseding ADR");
}
```

## D-1 (CR-14 / F4): schema-migration checks — not ArchUnit

Run as a migration-lint step (e.g., a test that introspects the migrated
schema, or checks in the migration pipeline):

1. **No cross-lifecycle FKs:** assert zero foreign keys between any
   `lineage_*` schema table and any conversion-state schema table, in either
   direction (ADR 0006 F4 + D4 rider). Violation fails the migration.
2. **Retention-class totality:** `capture_run_edges.retention_class` carries
   `CHECK (retention_class IN ('CONSUMED','FORENSIC','PENDING_MINT'))` and
   `NOT NULL` (ADR 0006 D4 rider).
3. **No payload columns:** no `bytea`/BLOB columns on conversion-state or
   lineage tables — artifacts live behind the storage port, the store holds
   references (CR-07/ADR 0006).

## E-1 (CR-18): complexity — PMD for CC, ArchUnit sketch for Distance

Cyclomatic complexity is a PMD/Checkstyle job, not ArchUnit. PMD ruleset
fragment (hard ceiling; the tighter core/edge targets stay review-level):

```xml
<rule ref="category/java/design.xml/CyclomaticComplexity">
  <properties>
    <property name="methodReportLevel" value="10"/>  <!-- CR-18 hard ceiling -->
  </properties>
</rule>
```

Normalized Distance from the Main Sequence: wire the chapter's ArchUnit
custom-condition sketch (`code-complexity.md`, Example 5-5) with
`MAX_DISTANCE = 0.3`, using an existing metrics library for A and I rather
than a bespoke implementation — run it **alarming, not blocking**, and feed
the trend to converge (CR-18's verdict on thresholds: changing one is a
recorded decision, never a constant edit).

## F-1 … F-3 (o7 interpreter — ADR 0016 / ADR 0017)

> **Status caveat.** ADR 0016 and ADR 0017 are both **Proposed**, awaiting the
> owner's SDD Stage-2 gate (ADR 0017 additionally needs the designated security
> owner's signature). These three seeds encode assertions those ADRs *name in
> their Compliance sections*; writing the seed does not accept the ADR. Wire them
> only once the gate closes — until then they are reference text, and the o7
> interpreter has no source tree to run them against.

These are the three assertions named in ADR 0016/0017 that had **no seed** —
the largest gap between "specified" and "enforced" on the o7 path. Placeholders
`{{seam.driver_*}}` and `{{o7.replay_packages}}` are **unresolved**: `.sdd/binding.toml`
has no `[coding-rules]` section, so no base package or seam glob exists for o7.
Ask; do not guess. (Package *names* are decided — ADR 0005:69-75 keeps
`ingestion`, `hierarchy-tool`, `conversion`, `replay`, `certification` — it is
the base package and the seam globs that are missing.)

Note also that **CR-08 enumerates three seams** (Invoke Models, source adapters,
storage port) and does **not** list the C-MIG driver seam ADR 0017 adds. These
seeds assume the driver seam is added to that enumeration; if the catalog is
amended instead, re-point the globs.

> **F-1 was split, 2026-08-09.** The no-registry rule over the **three CR-08
> spine seams** now lives above as **B-5**, sourced from the *approved* spine
> `plan:14` and wired by spine **T02** — it does not wait for the o7 gate. What
> remains here is the **driver-seam** half, which is genuinely ADR 0017's and
> genuinely gated. B-5 and F-1 are the same assertion over disjoint package
> sets; keep them that way. Do not merge them, and do not delete B-5 if ADR 0017
> is later rejected.

```java
@AnalyzeClasses(packages = "{{base_package}}",
    importOptions = ImportOption.DoNotIncludeTests.class)
class O7InterpreterRulesTest {

  // ── F-1 (ADR 0017 Compliance): no runtime plug-in registry at the DRIVER
  // seam. The discovery mechanisms are the detectable half of "registry-shaped".
  // The spine seams (source adapters, Invoke Models, storage port) are covered
  // by B-5 above on approved-plan authority and are NOT repeated here.
  @ArchTest
  static final ArchRule driver_seam_bound_by_spring_di_not_by_a_registry =
      noClasses().that().resideInAnyPackage(
              "{{seam.driver_adapter_packages}}")
          .should().dependOnClassesThat().haveFullyQualifiedName("java.util.ServiceLoader")
          .orShould().dependOnClassesThat().resideInAnyPackage(
              "org.reflections..", "io.github.classgraph..")
          .orShould().dependOnClassesThat().haveFullyQualifiedName(
              "org.springframework.core.io.support.SpringFactoriesLoader")
          .orShould().dependOnClassesThat().haveFullyQualifiedName(
              "org.springframework.context.annotation."
              + "ClassPathScanningCandidateComponentProvider")
          .because("ADR 0017 Compliance: the C-MIG driver seam is bound by "
              + "Spring DI (interface + injected "
              + "implementation); a service-registry / runtime-discovery / "
              + "classpath-scanning binding fails the build until this ADR's "
              + "execution-backend trigger has fired and a superseding or amending "
              + "ADR is on file");

  // ── F-1b (ADR 0017): the canonical registry shape is a keyed map of seam
  // implementations. ArchUnit works on RAW types, so Map<String, Driver> is
  // indistinguishable from any other Map — this is a name heuristic only, and
  // the precise form stays a review obligation (see review channel below).
  @ArchTest
  static final ArchRule no_registry_shaped_fields_at_the_driver_seam =
      noFields().that().areDeclaredInClassesThat()
              .resideInAnyPackage("{{seam.driver_adapter_packages}}")
          .should().haveNameMatching(".*([Rr]egistry|[Bb]yName|[Bb]yKey|[Pp]lugins)")
          .because("ADR 0017: a keyed map of drivers is a runtime registry in "
              + "disguise — it reintroduces the 'which implementation bound at "
              + "runtime' variable that F6 complete-or-invalid must pin or break");

  // ── F-2 (ADR 0017 Compliance): exactly ONE live driver adapter behind the
  // C-MIG seam. The raw-W3C adapter stays a stub (C1) and must not be a bean.
  // Verify the counting-condition import on first run:
  //   static com.tngtech.archunit.lang.conditions.ArchConditions.containNumberOfElements
  //   static com.tngtech.archunit.base.DescribedPredicate.equalTo
  @ArchTest
  static final ArchRule exactly_one_live_driver_adapter =
      classes().that().implement("{{seam.driver_interface}}")
          .and().areAnnotatedWith("org.springframework.stereotype.Component")
          .should(containNumberOfElements(equalTo(1)))
          .because("ADR 0017 Compliance: a second LIVE adapter IS the "
              + "execution-backend trigger — it must fail the build until the "
              + "reopening ADR exists, so the trigger cannot be crossed silently");

  // If the workspace wires drivers with @Bean factory methods rather than
  // stereotype annotations, the class-level rule above sees nothing. Use the
  // method-level form INSTEAD (not as well), or the seam is silently unguarded:
  //   methods().that().areAnnotatedWith("org.springframework.context.annotation.Bean")
  //       .and().haveRawReturnType("{{seam.driver_interface}}")
  //       .should(containNumberOfElements(equalTo(1)))
  // Decide which wiring style the workspace uses BEFORE wiring this seed.

  // ── F-3 (ADR 0016 Compliance, F-B / T02): no per-test generated Java or
  // TestNG type in the replay path.
  @ArchTest
  static final ArchRule no_testng_in_the_replay_path =
      noClasses().that().resideInAPackage("{{o7.replay_packages}}")
          .should().dependOnClassesThat().resideInAnyPackage("org.testng..")
          .because("ADR 0016 Compliance (F-B, T02): no per-test generated "
              + "Java/TestNG type exists in the o7 pipeline; the interpreter's own "
              + "types and the vendored Appium java-client are allowlisted — they "
              + "are not per-test artifacts");

  // ── F-3b (ADR 0016 T02): no codegen output package survives the fork.
  @ArchTest
  static final ArchRule no_codegen_output_packages =
      noClasses().should().resideInAnyPackage(
              "..generated..", "..generatedtests..", "..codegen..")
          .because("ADR 0016 T02: the code-generation stage is deleted; a codegen "
              + "output package reappearing is the regression this rule exists to "
              + "catch");

  // ── F-3c (ADR 0016 T02): no @Test-annotated type in production sources.
  // DoNotIncludeTests excludes test sources by LOCATION, so anything caught
  // here is a generated test living in the main tree.
  @ArchTest
  static final ArchRule no_test_annotated_types_in_production_sources =
      noClasses().should().beAnnotatedWith("org.junit.jupiter.api.Test")
          .orShould().beAnnotatedWith("org.testng.annotations.Test")
          .because("ADR 0016 T02 / F-B: a @Test type in the main tree is a "
              + "per-test generated artifact by another name");
}
```

**Scope boundary this section does NOT cross:** o7 is a *fork*, not a migration —
both pipelines stay live (o7 spec:45, :140). The A–E seeds above continue to
govern the o1 arm unchanged. Do not "unify" the two rule sets, and do not point
F-1…F-3 at o1 packages.

## What ArchUnit cannot check (review channel)

Behavioral compliance is not mechanically checkable and stays a review
obligation per the catalog's "Shape is necessary, not sufficient": an
adapter must actually invoke its collaborator on the documented path (a
well-shaped no-op passes every rule above); pinning fields must be derived
from the prompt registry / gateway response, not hardcoded literals; and
silent no-op implementations on audit/evidence paths are findings. Reviews
must not treat a green ArchUnit run as behavioral certification.

Two additions from the o7 seeds (F-1…F-3), both structural blind spots rather
than judgement calls:

1. **Registry shape is only half-detectable.** ArchUnit's type model is *raw*, so
   `Map<String, Driver>` and `Map<String, String>` are the same type to it. B-5
   and F-1 catch the discovery *mechanisms* (ServiceLoader, classpath scanners,
   SpringFactoriesLoader) and F-1b catches registry *naming* — a keyed collection
   of seam implementations under an innocent name passes all three. Reviewers must
   read the seam wiring, not just the green run. Note F-1b is **driver-seam only**:
   the spine seams have no name-heuristic counterpart, so on the spine arm this
   blind spot is wider still.
2. **"Live" vs "stub" is behavioral, not structural.** F-2 counts registered
   beans; it cannot tell whether the raw-W3C adapter's methods actually do
   nothing. A raw-W3C adapter that stops being a stub *without* gaining a bean
   annotation crosses ADR 0017's execution-backend trigger invisibly. Pair F-2
   with the C1 criterion (o7 spec:129) that raw-W3C activation is recorded in the
   run's lineage — the lineage record, not the ArchUnit rule, is what makes a
   driver fallback non-silent.

## Deployment-unit check (ADR 0005 Compliance, outside ArchUnit)

CI asserts exactly one deployable artifact; a second deployable fails the
build until a superseding ADR exists. Implement in the build script (count
bootJar/image outputs), not in ArchUnit.

**This check continues to bind for o7** (ADR 0017: "the one-deployable CI check
(0005:126) continues to bind for o7"). o7 is a *module* inside the existing
`validation-certification`/device-gate topology (o7 spec:5), not a new
deployable — an agent scaffolding a standalone o7 service breaks this check by
design. Do not "fix" that red build.
