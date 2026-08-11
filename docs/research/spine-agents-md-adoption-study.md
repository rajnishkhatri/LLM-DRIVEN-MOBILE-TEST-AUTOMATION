# Spine `AGENTS.md` — practice-adoption study (vs the AgentsFramework `AGENTS.md`)

> **What this is.** A conservative adoption study: which practices from the
> **AgentsFramework** `AGENTS.md` (`docs/research/AGENTS_Agents_framework.md` — a
> Python/LangGraph ReAct-agent workspace) are worth pulling into the **spine**
> `AGENTS.md` (`docs/sdd/plans/spine-repo/AGENTS.md`, v1.0.0). Scope was set by the
> owner: **hexagonal architecture, architecture tests, and general (non-agents-
> specific) guidelines** — keep only high-value *backpressure* signals, remove
> slop, err conservative.
>
> **The finding that reframed the task.** The spine already has the substance of
> both headline interests, and enforces it more rigorously than the source. Ports/
> adapters are present as **enforced partial boundaries** (F1/F2, CR-05..CR-13);
> architecture tests are **CI-blocking from the first commit** (ArchUnit A-1..E-1 +
> F1–F4 + B-5); anti-slop is **mechanical** (CR-18 + the "Shape is necessary, not
> sufficient" doctrine); and *every* `Never` rule already names its enforcer. So
> this is not a "port hexagonal + arch tests in" job — it is a narrow gap-hunt.
> **Net-new reduces to one gate worth adopting, two optional convention lines, and
> one deferral. Everything else is already present, cosmetic, cap-breaking, or
> unenforceable prose.**
>
> **Method.** Full read of both `AGENTS.md` files + a workspace infra map (Explore
> pass, 2026-08-10) over the spine spec/plan, the 17 ADRs under
> `docs/architecture/adrs/application/mobile-test-automation/`, the 18-rule
> `rules-catalog.md`, and `archunit-seeds.md`. Each candidate is judged against the
> owner's bar: *does it apply backpressure (ideally a mechanical sensor, at minimum
> a rule tracing to a real failure), or is it aspirational prose the spine's own
> ratchet would reject?*
>
> **Status.** STUDY + PROPOSAL — **not landed.** The spine task board still
> **awaits TASKS-OK**, and the spine `AGENTS.md` is "final in content, not yet
> landed." Nothing here edits that file. The one adoption (§6) was **ratified
> 2026-08-10** and routes through **sdd-spec** for a marker before it can land; its
> scope attaches to T04/T02 via tasks.md Amendment A7, not a new task number.
> `docs/research/` is outside OKF governance (not a declared bundle), so this file
> carries no frontmatter/catalog by design.
>
> **Provenance.** Sources: `docs/research/AGENTS_Agents_framework.md`;
> `docs/sdd/plans/spine-repo/AGENTS.md`. Infra facts cross-checked against the ADR
> bundle, `tooling/coding-rules-skill/references/{rules-catalog,archunit-seeds}.md`,
> and `docs/sdd/specs/mobile-test-automation-spine.spec.md`. Authored 2026-08-10.

---

## Executive verdict

| Candidate (from AgentsFramework) | Backpressure | Cost | Verdict |
|---|---|---|---|
| Hexagonal as a *named style* | — | reopens ratified ADRs | **REJECT — already have the substance; style is a closed decision** |
| Architecture tests | strong, but | already CI-blocking | **REJECT — 7/8 invariants already enforced; 0 net-new** |
| **Test-suite-erosion gate (G8)** | **strong (mechanical)** | **T04+T02 + spec marker M44** | **ADOPTED 2026-08-10 → M44 live (SPEC-OK 2026-08-10); A7 rides board TASKS-OK (§6)** |
| Evidence-not-assertions + watch-it-fail | medium (convention) | ≤2 lines | **OPTIONAL — include only if you accept unenforced lines** |
| Mechanical ADR-ratchet gate | strong, but | machinery | **DEFER — M3/M18 discipline already covers it; wire only if a leak appears** |
| Anti-slop "musts" prose block | weak (unenforced) | — | **REJECT — CR-18 is the mechanical version; prose is weaker** |
| ✅/⚠️/🚫 restructure | none (cosmetic) | churn | **REJECT** |
| Nested per-folder `AGENTS.md` | weak here | 5–7 files + drift | **REJECT — ArchUnit enforcement removes the "loads too late" reason** |
| Comprehension-gate answer-before-reveal ritual | unenforceable | — | **REJECT — spine already made this honesty call** |
| G9 defensive-coding prose gate | weak (no sensor) | cap-breaker | **REJECT — CR-16 + M10a quarantine cover the spirit** |
| Thin-wrapper line-count test (invariant #6) | crude | — | **REJECT — C-1 + CR-13 cover the intent; line-count is gameable** |
| Subagent-as-context-firewall / explore | n/a | — | **REJECT — source's agent tooling, not architecture** |

---

## §1 — Hexagonal architecture: the spine chose a *lighter, ratified* variant

The substance of ports/adapters is present **and enforced**; the *named style* and a
*full* hexagonal ring are deliberately absent, and adopting them would fight two
Accepted ADRs.

| Question | Finding |
|---|---|
| Substance of ports/adapters present? | **Yes, enforced.** Storage **port** (ADR 0011); source **adapters**; model-boundary **adapter**; `CR-10` ports are consumer-owned (`ProvenanceWriter`, not `S3ClientWrapper`); `CR-11` framework-free core; `CR-13` humble adapters. |
| "Hexagonal / Ports & Adapters" as a named style? | **No — deliberately.** Zero occurrences across ADRs/spec/rules. |
| The chosen style | ADR 0005: **"plain modular monolith partitioned by cluster."** The microkernel/plugin ring was **considered and declined** ("unwarranted machinery… Spring DI supplies the Strategy seam for free"). ADR 0017 re-litigates it for o7 and **declines again**, narrowing the flip trigger to "a second live execution backend on the driver seam." |
| Boundary shape | `CR-08`: **"partial boundaries, Strategy-shaped"** — interface + DI-selected impl. A deliberate *subset* of hexagonal, not a ring around every module. |

**Verdict: nothing to adopt, and a caution.** Recommending "go hexagonal" would
(a) duplicate substance you already enforce, and (b) reopen a **twice-ratified**
(0005, 0017) style decision whose flip conditions ("a fourth source adapter or a
second concurrent reasoning provider" / "a second live execution backend") are
**untripped**. Full hexagonal is *heavier* than what was chosen on purpose. A real
desire to revisit it routes to **sdd-replan against ADR 0005**, never into
`AGENTS.md`.

---

## §2 — Architecture tests: already CI-blocking, and broader than the source

Every one of the AgentsFramework's 8 "STRICTLY ENFORCED" invariants maps to a spine
rule that already exists:

| AgentsFramework invariant | Spine equivalent (already enforced) | Covered? |
|---|---|---|
| 1. Dependencies flow downward only | A-1 (cross-module only via `.api..`) + A-2 (no cycles) + Layout "cluster→contracts only" | ✅ |
| 2. Kernel has ZERO outward deps | CR-11/C-1 framework-free core + contracts-only dependency | ✅ |
| 3. Components framework-agnostic | C-1 (framework-free core; wiring only at composition root) | ✅ |
| 4. Services framework-agnostic | C-1 + module boundaries | ✅ |
| 5. No peer imports between components | Layout "cluster modules never depend on each other" + B-4 (no backchannel) | ✅ |
| 6. Orchestration nodes thin (≤10–15 lines) | app "thin assembly" + C-1 + CR-13 — **intent only, no line-count test** | ◑ intent |
| 7. Services MUST NOT import components | A-1 + module boundaries | ✅ |
| 8. Meta-layer MUST NOT import orchestration | N/A — spine has no meta layer | — |

**7 of 8 already enforced.** #6 is covered *in intent* by C-1/CR-13; the only missing
piece is a **line-count** fitness function, which is a crude, gameable mechanism
(logic gutted into a helper defeats it) and not worth adding. The spine's A-1..E-1
suite is in fact **broader** than the source — it adds no-cycles (A-2),
no-technical-layer-names (A-3), encapsulation (A-4), no-registry (B-5),
async-confinement (D-2), and the CR-18 complexity / distance-from-main-sequence
ratchet — none of which the AgentsFramework has.

**Verdict: zero net-new architecture tests.** This surface is a duplicate; adding any
would be the exact slop we are removing.

---

## §3 — The genuine candidates (general guidelines)

Only three source practices are *both* absent from the spine *and* plausibly
backpressure. The concrete adoption for the lead item is §6.

### 3.1 — Test-suite-erosion gate — **LEAD ADOPT** (detail in §6)

**Source:** `test_no_test_weakening.py` / G8 — fails a removed test, or a newly
skipped/`xfail`ed test, lacking a justification token.

**Gap:** `Never weaken a fitness function` guards **only** ArchUnit F1–F7. Nothing
guards erosion of the *ordinary* suite (contract tests M20, unit tests) — a deleted
`@Test`, an added `@Disabled`, an `assumeTrue(false)`, a body gutted to
`assertTrue(true)`.

**Backpressure:** Strong and *mechanical* — the one candidate that is a true sensor.
Same class as CR-18: an objective backstop against a **known agent-decay mode**.
CR-18 already backstops two modes (accidental complexity, zone-of-pain packages);
silent suite-erosion is a documented *third* mode CR-18 doesn't reach.

**Ratchet tension (stated honestly):** the spine is greenfield, so there is no
spine-*local* failure yet. The justification is **inductive** — CR-18 precedent
(you already pre-empt *known* agent-decay modes mechanically) + the near-certainty
that agent-written suites erode. Real, but precedent-based → must be **owner-ratified
as a deliberate CR-18 extension**, not slipped in.

### 3.2 — "Evidence, not assertions" + "watch it fail first" — **OPTIONAL** (≤2 lines)

**Source:** `✅ Always` — "paste the actual command/test output, not a summary";
"red/green TDD — watch it fail first. A test that never failed proves nothing."

**Gap:** No explicit line. The DoD mandates *what must be green*, not *how you prove
it*, and never states the watch-it-fail discipline.

**Backpressure:** Medium, **convention-only (no sensor).** Each traces to a real
agent failure mode — false-green claims, and vacuous tests that could never fail —
but by the strict bar these are disciplines, not gates.

**Verdict — conservative:** include only if you accept two unenforced lines.
Given "err conservative," the default recommendation is to **drop them** and let the
fail-fast DoD carry the weight — *unless* you specifically value "watch it fail
first" for the interpreter's replay tests, where a test that can't fail is a genuine
hazard. Cheap either way. Proposed wording, if adopted:
- DoD preamble: *"Paste the actual command output for each step below — a summary is not a result."*
- Testing note (`Common changes`): *"Write the test, watch it fail, then implement — a test that never failed proves nothing."*

### 3.3 — Mechanical ADR-ratchet gate — **DEFER**

**Source:** `test_adr_ratchet.py` — a governed path changed without a new ADR (or
`ADR-OK:` waiver) fails CI.

**Gap:** Not mechanical. But convention is tight: `Authority chain` → ADRs;
`Change a fitness function → recorded decision, never just a commit (M3/M18)`;
`Add an async edge → Stop, ADR 0007`.

**Verdict:** **Defer.** A git-range ratchet is more machinery than a not-yet-existent
repo has earned, and the source's own honesty ("hooks can't capture a typed answer;
convention + PR-review") is a call the spine *already made* (`Enforcer: none —
review obligation`). Revisit only if, once the repo exists, a structural change
actually slips past review.

---

## §4 — The reject pile (removing the slop)

| From AgentsFramework | Why reject for the spine |
|---|---|
| Anti-slop "musts" prose block | You already have **mechanical** anti-slop (CR-18 + "Shape is necessary, not sufficient"). Prose is *weaker* than what exists and violates "each rule names its enforcer." |
| ✅/⚠️/🚫 restructure | Cosmetic. `Never` + `Common changes` + `Working agreement` already carry it, each `Never` naming an enforcer — a feature the tri-split would dilute. Pure churn. |
| Nested per-folder `AGENTS.md` ×5–7 | The source nests because its invariants are enforced by *reading files*; yours are enforced by *ArchUnit*, so "loads too late" doesn't bite. Cost: 5–7 files + drift, against a provenance story built on "exactly one copy." |
| Comprehension-gate answer-before-reveal ritual | Unenforceable (hooks can't capture answers). Spine already made this honesty call — keep only sensors. |
| G9 defensive-coding gate (prose) | Convention-only in source. Spine's domain versions cover the spirit mechanically: "unknown quarantines" (M10a), CR-16 "the model proposes; determinism disposes." A general prose rule = a 19th cap-breaker with no sensor. |
| Thin-wrapper **line-count** test | Crude, gameable; intent covered by C-1 + CR-13. |
| Subagents-as-context-firewalls / explore subagent | Source's agent tooling, not architecture. Irrelevant to the spine's `AGENTS.md`. |
| Mutation testing (PIT / crap4java / mutate4java) | **Not from this file** — belongs to the separate `sdd-roles` project. PIT is already a *deliberate deferral* in the spine on a JUnit-6 blocker. Do not conflate. |

---

## §5 — Recommendation

1. **Adopt one thing:** the **test-suite-erosion gate** (§6) — as a CI gate, not a
   CR rule (respect the 18-cap), owner-ratified as a deliberate extension of CR-18's
   pre-emptive-backstop precedent, with a `TEST-WEAKEN-OK:` waiver tied to M3/M18.
2. **Optionally** add ≤2 convention lines (§3.2) — only if you want "watch it fail
   first" for replay tests; otherwise drop.
3. **Defer** the ADR-ratchet gate (§3.3) until the repo exists and a real leak
   justifies it.
4. **Reject** §4 wholesale.
5. **Do not** touch hexagonal/architecture-tests — present and enforced; changing
   the *style* is an sdd-replan against ADR 0005/0017, not a file edit.

**Scrupulously honest framing:** because the spine is greenfield, *none* of these has
a spine-local failure yet. Even the lead recommendation rests on **precedent +
known-certainty**, not a local incident. The maximally conservative outcome is: the
erosion gate is the one idea worth an owner decision; everything else is either
already yours or slop.

**Process caveats.** The board **awaits TASKS-OK** and the file is "final in content,
not yet landed," so any edit needs owner involvement; and adding a gate is a new
**task**, so it touches the tasks board, not just `AGENTS.md`.

---

## §6 — Proposal: the test-suite-erosion gate (RESOLVED 2026-08-10)

> **RESOLVED 2026-08-10 — ratified with four owner decisions.** The authoritative,
> live record is `mobile-test-automation-spine.tasks.md` **Amendment A7** (T04 + T02
> scope); this section is the reasoning behind it and is kept in sync, not duplicated.
> The four decisions: **(1) adopt now** on the CR-18 + T22 precedent basis;
> **(2) route via sdd-spec** to mint a real marker before landing (not a marker-less
> dev-process gate); **(3) split enforcement by reliability** — deterministic signals
> (removed/`@Disabled`/`assumeTrue(false)`) block from commit one, the gutted-body
> heuristic is warn-only indefinitely; **(4) the waiver must cite a recorded decision**
> (`TEST-WEAKEN-OK: <ref>`, M3/M18), not free-text. The `AGENTS.md` deltas are staged
> in A7, not applied to the content-final v1.0.0 file. **sdd-spec pass — DONE:**
> the spec minted marker **M44** (six criteria M44-1..M44-6) at **owner SPEC-OK
> 2026-08-10** in its test-suite-erosion amendment (post-erosion-gate baseline).
> A7's sdd-spec dependency is satisfied; it now rides the pending board TASKS-OK
> like A1–A6, on which the staged `AGENTS.md` deltas apply.

### 6.1 — Failure mode guarded

Agent-written suites erode in ways every existing spine gate misses: a `@Test`
**deleted**, a test **`@Disabled`**, an assumption **short-circuited**
(`assumeTrue(false)`), or a body **gutted** to a tautology (`assertTrue(true)`). Each
turns the suite green while *removing* the signal it was green for. `Never weaken a
fitness function` stops this **only** for ArchUnit F1–F7; the contract tests (M20) and
unit tests are unguarded.

### 6.2 — Why a gate, not a CR rule

The `rules-catalog.md` is **hard-capped at 18 rules**. A 19th rule ("CR-19") breaks
the cap and needs its own ADR. The erosion check is not a *coding* rule anyway — it is
a **diff-scoped CI gate**, exactly the shape of the gates already in the file:
gitleaks, the custom `Thread.sleep`/unbounded-wait Checkstyle check (T30), and the
grant assertion (ADR 0012). It joins that list; the catalog is untouched.

### 6.3 — Mechanism

**Primary — a test-inventory range gate (CI).** Removals cannot be caught on the
classpath (deleted code isn't there), so the hard enforcement is a git-range diff:

1. Build a canonical inventory of test methods at the **base** ref and the **head**
   ref. A test method = one annotated (JUnit Jupiter 6, `org.junit.jupiter.api.*`)
   `@Test` · `@ParameterizedTest` · `@RepeatedTest` · `@TestFactory`.
2. Flag, in head vs base:
   - **removed** — present at base, absent at head;
   - **disabled** — carries `@Disabled` at head (or newly at head vs base);
   - **short-circuited** — body contains `assumeTrue(false)` / `assumeFalse(true)`
     (`org.junit.jupiter.api.Assumptions`);
   - **gutted** *(advisory heuristic, warn-only)* — a `@Test` body with no assertion
     call (`assert*` / `assertThat` / Mockito `verify(`).
3. **Waiver (must cite a recorded decision — owner decision 4):** a blocking finding
   is allowed **iff** the commit range carries `TEST-WEAKEN-OK: <ref>`, where `<ref>`
   points at a durable record — a lightweight decisions-log line or an ADR — naming
   why the weaker suite is still sound. Not free-text: M3/M18 applied literally
   ("recorded decision, never just a commit"). Token string provisional; semantics
   fixed.
4. **Enforce by signal reliability (owner decision 3):** the deterministic findings
   (removed / `@Disabled` / short-circuited) **block from commit one** — zero false
   positives, and little history to diff early, so blocking is inert until tests
   accumulate. The **gutted** finding is **warn-only, indefinitely** (heuristic —
   misfires on helper/expected-exception tests).

**Complement — an ArchUnit assist (optional, in `architecture-tests/`).** ArchUnit can
ban `@Disabled` present on the *current* classpath without an approved marker — a
cheap in-suite tripwire. It **cannot** replace the range gate: it never sees removed
code. State this limitation wherever the assist is wired so nobody mistakes it for
full coverage.

**JUnit-6 note.** Under Boot 4.1 the suite is Jupiter 6 — `@Disabled` is
`org.junit.jupiter.api.Disabled`, assumptions are `org.junit.jupiter.api.Assumptions`.
The gate keys off Jupiter 6 symbols, consistent with the `archunit-junit6` coordinate.

### 6.4 — Rollout (split by reliability)

**Not** the gitleaks warn→block curve, on reflection (owner decision 3): the
deterministic checks (removed / `@Disabled` / `assumeTrue(false)`) **block from commit
one** like F1–F4 — ~zero false positives, so no warn-in period is warranted, and early
on there is little test history to diff. The **gutted-body heuristic stays warn-only
indefinitely** — it misfires on helper- and expected-exception-based tests, so it
flags for review but never wedges the build.

### 6.5 — `AGENTS.md` deltas (staged in A7; applied on landing)

**Add to `Never`** (matching the file's terse, enforcer-named form):

```
- **Never weaken the test suite.** A removed `@Test`, a new `@Disabled`, or an
  `assumeTrue(false)` needs a `TEST-WEAKEN-OK: <recorded-decision ref>` line in the
  commit range naming why the weaker suite is still sound (M3/M18 — a decisions-log
  line or ADR, never bare text). *(Enforcer: test-inventory range gate, T04 —
  blocking from commit one for these deterministic signals; a gutted-assertion body
  is a warn-only heuristic; ArchUnit assist bans un-waivered `@Disabled`.)*
```

**Add to `Definition of done`** (as a CI/range step — it needs base+head, like
gitleaks, so it is not a local `mvn verify` step):

```
6. The test-inventory gate passes — no un-waivered removed/disabled/short-circuited
   test in the PR range. (CI/range-scoped; locally, do not remove or disable a test
   without the `TEST-WEAKEN-OK:` line.)
```

**Add a `Common changes` row:**

```
| Remove or disable a test | Stop — add `TEST-WEAKEN-OK: <recorded-decision ref>` (M3/M18), or don't. |
```

### 6.6 — Cost

- One CI gate script (range diff of test inventories) + pipeline wiring — comparable
  to the existing gitleaks/Checkstyle-custom-check effort.
- Optional ArchUnit assist — a few lines in `architecture-tests/`.
- No new task number — the scope attaches to **T04** (gate) + **T02** (ArchUnit
  assist) via Amendment A7, plus one new **spec marker** via sdd-spec; three small
  `AGENTS.md` deltas.
- Ongoing: near-zero — the waiver token reuses the recorded-decision habit already in
  place.

### 6.7 — Owner decisions (resolved 2026-08-10)

1. **Adopt now** on the CR-18 + T22 precedent basis — not deferred to a first incident.
2. **Route via sdd-spec** to mint a real marker before landing — not a marker-less
   dev-process gate, not land-now-backfill.
3. **Split enforcement by reliability** — deterministic signals block from commit one;
   the gutted-body heuristic is warn-only indefinitely.
4. **Waiver must cite a recorded decision** (`TEST-WEAKEN-OK: <ref>`, M3/M18), not bare
   free-text.

Authoritative tracker: `mobile-test-automation-spine.tasks.md` Amendment A7. **sdd-spec
pass — DONE:** the spec minted marker **M44** at **owner SPEC-OK 2026-08-10** in its
test-suite-erosion amendment (`mobile-test-automation-spine.spec.md`); A7's sdd-spec
dependency is satisfied and it now rides the pending board TASKS-OK like A1–A6.
