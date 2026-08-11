# O1 Spine — Pipeline Walkthrough Guide

A step-by-step teaching walkthrough of the **O1 (Spine)** architecture for mobile test
automation, built from the explanations, mock artifacts, and diagrams produced in this
session. Read it alongside the mock suite at `mocks/o1-spine/` and the canonical blueprint
at `blueprint-revision-v2.md`.

> **Review status (2026-07-31).** This walkthrough was critically reviewed — 28 confirmed
> findings, full report in `o1-pipeline-review.md`. The editorial corrections (Replan R1
> Lane 1, E1–E6) are applied in this revision: spine-boundary redraw, K=1 phase-labeling,
> honest mock ReplayReport, flywheel rename, coverage-numbers-as-targets, and
> NavigationManifest demotion + ADR 0009 call-outs. ADR-grade items (signature re-keying,
> proposer/executor credential split, deep-link URL denylist, graph lineage chain,
> "prod-grade data" definition, K policy) remain **OPEN** — see Replan R1 Lane 2 in
> `docs/sdd/plans/mobile-test-automation-spine.tasks.md`.

---

## 0. The One-Sentence Idea

> **O1 is the LLM-free deterministic replay of committed code.**

LLMs are used upstream to *author* artifacts (IR, locators, Java), but the replay pipeline
itself consumes only committed artifacts and contains no LLM in the execution path
(`blueprint-revision-v2.md:73`). Everything below is a consequence of that sentence.

The "spine" is the deterministic replay pipeline; the "authoring arm" is everything that
feeds it. The handoff between the two halves is a **git commit**.

---

## 1. The Two Halves

```
┌──────────────────────────────┐      ┌──────────────────────────────┐
│   AUTHORING ARM (upstream)    │      │   THE SPINE (downstream)       │
│   LLM-bounded, produces        │ ──►  │   LLM-free, consumes only      │
│   committed artifacts          │      │   committed artifacts           │
└──────────────────────────────┘      └──────────────────────────────┘
   [A0 deferred] ingestion/A1 → A2 →   static gate → device gate →
   hierarchy → locator res → code gen    verdict → human evaluator
```

A2 commits `TestCaseIR.json`; Code Generation commits `LoginTest.java`. The spine reads
those commits and never asks the LLM anything. This is what makes O1 auditable: the
executable artifact that produced a verdict is reviewable, pinned by SHA, and reproducible
by anyone with the repo.

---

## 2. The Authoring Arm — Stage by Stage

### 2.0 A0 — Normalizer (LLM)  *[DEFERRED — ADR 0015; not a current stage]*

**Purpose.** Automate intake. Take free-form English or a manual test script string
(from Octane, Jira, ALM, Excel) and produce a `NormalizedIntent` that makes A1's
deterministic parser succeed more often.

**What A0 is NOT.** It does **not** produce the `TestCaseIR`. It only extracts and cleans
intent so A1 has a higher success-rate probability. The IR is still owned by A1+A2.

**What A0 does.** Extract intent from messy natural language; strip noise (boilerplate,
headers, numbering); normalize phrasing ("sign in" / "log in" / "login" → one canonical
form); emit an A1-friendly structured intent.

**The data flywheel does NOT apply to A0.** A0 is a pure intake normalizer; the flywheel
feeds A2, Code Generation, and the O6 ensemble — not A0. (Deliberately no longer written
"F1 (flywheel)": **F1 is the no-model-call fitness function** — a CI rule — and the name
collision was an audit hazard.)

**Status — DEFERRED (ADR 0015, Accepted 2026-08-01).** A0-as-an-LLM-stage was routed to a
RATIFY-OR-DEFER decision (Replan R1 D2) and **deferred** — an evidence-gated future re-open,
not a current pipeline stage. Its two flows are a class-(1) untrusted-source-text intake and
a class-(3) model egress; under ADR 0009's boundary-scoping amendment (`0009:90–92`) both are
**second paths into already-screened classes**, so A0 trips **no fourth flip** (the review's
"2/3→3/3 territory" framing predates ADR 0014's amendment and is stale). A ratified A0 would
still owe an sdd-replan amendment to the ingestion CLI, F1 out-of-spine placement (ADR 0001),
and the ADR 0009 call-site map onto the existing class-(1)/(3) call sites. The **lexical** work
A0 named — phrase-canonicalization ("sign in"/"log in"/"login" → one form) and noise-stripping
— is instead **folded, deterministically, into the per-adapter canonicalization surface
(`spec.md:61`, M15)** with no model call and no new injection surface (ADR 0015). Screen-context
inference (`screenContextHint`) is **A2's** job (§2.2), not A0's. A0's LLM stage re-opens only
on a **measured A1 parse-failure rate** (M16 corpus + a real free-form-English sample,
decomposed fold-fixable vs LLM-only, gated on whether A2's existing LLM-fallback already
absorbs it).

```
Input:  free-form English or manual script string (from Octane/Jira/etc.)
Output: NormalizedIntent   (NOT a TestCaseIR)
```

### 2.1 A1 — Parser (deterministic, "structure only")

**Purpose.** Take the canonicalized intake from the ingestion CLI (per-adapter
deterministic canonicalization, M15; A0's LLM stage deferred per ADR 0015) and split it into
a partially-filled `TestCaseIR` skeleton — structure only, no semantics filled in yet.

**What A1 does.**
- Splits the intent into N steps with the raw intent text preserved per step.
- Recognizes deterministic patterns (e.g. the login pattern).
- Notes that credentials exist but values are absent (values come from the vault at runtime).
- **Does NOT fill** `action`, `resolvedLocators`, `assertion`, or `controlFlow`.

**Worked example.** Using the session's test script:

> *Validate customer account balance is correct:*
> 1. sign in to app using these test creds: username/pwd
> 2. on home screen navigate to payment and activity screen
> 3. on payment and activity screen navigate to account overview screen
> 4. check all the accounts one by one
> 5. verify the account balance for each account

A1 produces a 5-step skeleton — each step carries its raw intent text, but `action`,
`target.resolvedLocators`, `assertion`, and `controlFlow` are all empty/null. A1 has
*structure*, not *meaning*.

### 2.2 A2 — Semantic Interpreter (deterministic-first, LLM fallback)

**Purpose.** Turn A1's structural skeleton into a semantically complete, committed
`TestCaseIR`. This is where "verify the balance shows correctly" becomes a structured
assertion.

**What A2 does.**
- **Expands** compound steps (e.g. login → `TAP / TYPE / TAP / TYPE / TAP`).
- **Normalizes** navigation → `action: NAVIGATE` + `naturalReference` + `screenContext`.
- **Extracts** loops → `controlFlow` (e.g. `over: "accounts"` on the loop step).
- **Structures** vague assertions → `kind: VALUE_CHECK`, `expected: ${account.expectedBalance}`.
- **Flags** ambiguity (e.g. expected source unspecified, dynamic account list).
- **Leaves `resolvedLocators` empty** — no device has been touched yet.

**Output.** The committed `TestCaseIR.json` — see `mocks/o1-spine/TestCaseIR.json`. For
the login scenario it has 6 steps (TAP, TYPE, TAP, TYPE, TAP, ASSERT). Note: in the real
pipeline locators are filled by the next stage (Capture Hierarchy + Locator Resolution),
not by A2; the mock shows the IR in its final committed form for readability.

**Key fields to notice in the mock:**
- `sourceSystem: "octane"`, `sourceId: "ACC-1042"` — provenance of the intent.
- `testData` references the vault, not literal creds (`vault:user_qa`).
- `provenance.irVersion: "sha:4f2c91e8..."` — the IR itself is version-pinned.
- Each step has `action`, `target.naturalReference`, `target.resolvedLocators`,
  `assertion`, `controlFlow`, `ambiguityFlags`.

---

## 3. Capture Hierarchy (deterministic tool)

**Purpose.** Obtain the live UI view hierarchy from a real device so locators can be
resolved deterministically. This is the bridge from "intent" to "concrete elements."

**Tool.** `hierarchy-tool` — a small CLI plus service (`blueprint-revision-v2.md:26`).
One implementation, two callers: a human runs it in Phase 1; the Element Resolver
service invokes it as a tool in Phase 2.

**Inputs to the CLI.**
- A Perfecto device (already provisioned).
- The app under test installed on that device (IPA for iOS, APK for Android).
- App/user credentials (in the vault; the tool authenticates to the device cloud, not to
  the app — app creds are used only at replay time, not at hierarchy-capture time).

**How `getPageSource` is obtained.**
- The CLI opens an Appium session against the Perfecto device with the app installed.
- It calls `driver.getPageSource()` which returns the current view hierarchy as XML.
- In parallel it pulls Perfecto Object Spy smart locators and (on iOS) the XCUITest
  accessibility tree.
- It writes **two** outputs: the full dump, and a **pruned tree** (interactive elements
  + ancestors) so the LLM context window isn't blown (`blueprint-revision-v2.md:115`).

**Outputs.**
- `LoginScreen.pageSource.xml` — full Appium hierarchy dump.
- `LoginScreen.pruned.json` — pruned tree for LLM context.
- `LoginScreen.objectSpy.json` — Perfecto smart locators.

---

## 4. Locator Resolution (deterministic cascade)

**Purpose.** For every `naturalReference` in the IR (e.g. "the username field"), pick the
best concrete locator using a fixed, auditable cascade.

**The cascade (order of preference).**
1. `ACCESSIBILITY_ID`
2. `id`
3. `class chain`
4. `xpath`

**Sources (where candidates come from).**
`OBJECT_REPO` > `PAGE_SOURCE` > `OBJECT_SPY` > `VLM` > `LLM-guess`

**Output.** `mocks/o1-spine/LocatorCandidate.manifest.json`:

```json
{
  "testId": "ACC-1042",
  "irVersion": "sha:4f2c91e8...",
  "candidates": [
    { "strategy": "ACCESSIBILITY_ID", "value": "usernameField", "confidence": 0.98, "source": "OBJECT_REPO" },
    { "strategy": "ACCESSIBILITY_ID", "value": "passwordField", "confidence": 0.98, "source": "OBJECT_REPO" },
    { "strategy": "ACCESSIBILITY_ID", "value": "loginButton",   "confidence": 0.97, "source": "OBJECT_REPO" },
    { "strategy": "ACCESSIBILITY_ID", "value": "welcomeBanner", "confidence": 0.95, "source": "OBJECT_REPO" }
  ]
}
```

Every candidate carries a `confidence` and a `source`. The static gate later enforces
that *every* locator used in the generated Java appears in this manifest or the object
repository — no orphan locators allowed.

---

## 5. Code Generation (LLM, offline, one-shot per IR version)

**Purpose.** Turn the committed IR + the locator manifest into committed Appium Java.
This is an LLM stage, but it runs **offline**, **once per IR version**, and its output
is **reviewed and committed by an engineer** before anything executes on a device.

**Output.** `mocks/o1-spine/LoginTest.java` — a TestNG class using page objects
(`LoginScreen`, `HomeScreen`), with credentials pulled via `vault(...)` rather than
literals:

```java
public class LoginTest extends BaseTest {
    @Test(description = "ACC-1042: Login with valid credentials shows welcome")
    public void loginShowsWelcome() {
        LoginScreen login = new LoginScreen(driver);
        login.usernameField().click();
        login.usernameField().sendKeys(vault("user_qa"));
        login.passwordField().click();
        login.passwordField().sendKeys(vault("pass_qa"));
        login.loginButton().click();
        HomeScreen home = new HomeScreen(driver);
        assertEquals(home.welcomeBanner().getText(), "Welcome, QA User");
    }
}
```

**Why this is the audit pin.** This Java file is the executable artifact. Its git SHA is
what `ReplayReport.codeCommit` pins. When an auditor asks "show me exactly what ran",
this SHA is the answer — not an LLM call, not a runtime interpretation.

---

## 6. The Spine — Stage by Stage

### 6.1 Static Gate (deterministic, pre-device)

**Purpose.** Reject bad generations in seconds, before any device minute is spent
(`blueprint-revision-v2.md:75`).

**Checks.**
1. **Format** — google-java-format.
2. **`mvn compile`** — does the Java compile against the test framework and page
   objects? It compiles against the *test project* (Appium client, TestNG, page-object
   library) — **not** against the IPA/APK. The IPA/APK is the *app under test*; it is
   installed on the device at replay time, not compiled against.
3. **Checkstyle** — style conformance.
4. **Error Prone** — common bug patterns.
5. **Locator-manifest rule** — every locator used in the Java must exist in the object
   repository or the `LocatorCandidate` manifest. Orphan locators fail the gate.

**On failure.** Reject the generation, loop back to Code Generation (bounded retries).

### 6.2 Device Gate (Perfecto, K runs)

**Purpose.** Execute the compiled Java on real devices, K times, to measure flakiness
(`blueprint-revision-v2.md:77`).

**How.**
- Acquire a device from a pinned Perfecto pool by capability set.
- Execute via TestNG with pinned Appium and driver versions.
- Run K times. **K=1 is the signed-off baseline** (spec M10b — the ReplayReport's outcome
  fields are designed so K-of-K becomes derivable later without vendor aggregates). K=3
  for conversion / K=5 for certification is a **weeks-3-8+ target**, now gated on the S2
  flake-base-rate entry criterion (Replan R1 **D6 DECIDED 2026-08-01**: replay K = 1 retained
  for the spine; a raise is an **event-anchored** CF6 recorded decision — no certification
  verdict may be issued while the K re-decision is un-taken — never a walkthrough default).
- Pull Smart Reporting artifacts per run (video, page source, report URL).

**Flakiness verdict.** `STABLE` / `FLAKY` / `UNKNOWN` based on pass ratio across K runs.

### 6.3 Verdict — ReplayReport

**Purpose.** The single feedback artifact both phases consume
(`blueprint-revision-v2.md:79`).

**Output.** `mocks/o1-spine/ReplayReport.json`:

```json
{
  "testId": "ACC-1042",
  "irVersion": "sha:4f2c91e8...",
  "codeCommit": "sha:9be1a3f7...",
  "staticGate": { "format": "PASS", "compile": "PASS", "checkstyle": "PASS",
                  "errorProne": "PASS", "locatorManifest": "PASS", "findings": [] },
  "deviceGate": { "runs": 1, "passes": 1,
                  "flakiness": "NOT_DERIVABLE_AT_K1",
                  "classification": null,
                  "pinnedVersions": { "appium": "2.5.1", "driver": "XCUITest 5.12",
                                      "device": "iPhone 15 / iOS 17.4",
                                      "appVersion": "8.4.0",
                                      "pipelineVersion": "sha:2c77d0b1..." } },
  "verdict": "PASS",
  "certification": { "status": "CERTIFIED",
                     "certifiedBy": "named individual principal (CF9) — never mechanical" },
  "auditPin": "codeCommit sha:9be1a3f7... — the executable that produced this verdict
               is the committed Java at this SHA, reviewable and reproducible."
}
```

**Critical fields.**
- `codeCommit` — the SHA of the Java that ran. **This is the audit pin.**
- `staticGate` — all checks must PASS.
- `deviceGate` — honest at the **K=1 baseline**: one run recorded; a flakiness verdict
  becomes derivable only when a CF6 recorded decision raises K (M10b).
- `verdict` — the *machine* verdict. Static PASS + device pass are **preconditions** for
  certification; `CERTIFIED` itself is an attributable individual decision (CF9) and is
  never emitted mechanically by the pipeline.
- `healsApplied` — **not present** in O1. The spine does not self-heal. (Compare with
  O2/O3 where this field exists and is the locus of the audit argument.)

---

## 7. Human Evaluator + Flywheel (close-out)

**Human evaluator's job.** Validate the test result against the *original input intent*
(not just against the IR). Two outcomes:

- **PASS** → done. Feed accepted locators and exemplars into the flywheel.
- **FAIL** → loop back to ingestion (the deterministic CLI) with the error + the original
  intent. The error from iteration *N* becomes part of the input to iteration *N+1*. **This
  loop must be bounded** — the iteration budget and its owner are undecided (an OPEN Replan R1 Lane-2
  item); every other loop in this architecture is bounded, and an unbounded regeneration
  loop is not a decided design.

**The flywheel.** Every successful conversion produces labeled data at no extra cost
(`blueprint-revision-v2.md:107`):

```
accepted locators   ──► object repository (enriched)
accepted exemplars  ──► prompt library / few-shot store
accept/reject labels ──► preference training data (O6 ensemble)
                          │
                          └──► cheaper, higher-success-rate A0/A2/CodeGen next iteration
```

This is why Phase 1 (human-driven, Copilot-assisted) is not a throwaway prototype — it is
the asset factory and data flywheel for Phase 2 (programmatic, via Orchestrator AI).

---

## 8. The Full Pipeline (A0 deferred — ADR 0015)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  INGESTION ARM  (intent → committed TestCaseIR)                              │
│  LLM use is bounded here; the spine downstream is LLM-free.                  │
└─────────────────────────────────────────────────────────────────────────────┘

  Raw source                 INGESTION CLI (deterministic)    A1 — PARSER (deterministic)
  ──────────                 per-adapter canonicalization,     ────────────────────────────
  Octane / ALM /             M15 (Excel POI + Octane REST):    deterministic splitter:
  Jira / Excel /       ──►   • canonicalize source rendering ─► • split into N steps
  plain English              • phrase-canon table + noise-      • recognize login pattern
  (string)                     strip (ADR 0015, deterministic)  • note creds exist, values absent
                            • source-snapshot digest (M15)     • does NOT fill action/locator/
                            Output: canonicalized intake         assertion/controlFlow
                                                               Output: partial TestCaseIR
                            ┌─────────────────────────────┐      (structure only, raw intent
                            │ A0 — NORMALIZER (LLM)        │      text per step)
                            │ [DEFERRED — ADR 0015;        │
                            │  re-opens on measured A1     │
                            │  parse-failure rate]         │
                            └─────────────────────────────┘
                                  │
                                  ▼
                        A2 — SEMANTIC INTERPRETER (det-first, LLM fallback)
                        ─────────────────────────────────────────────────────
                        • expand login → TAP/TYPE/TAP/TYPE/TAP
                        • normalize navigation → NAVIGATE + screenContext
                        • extract loops → controlFlow (over: "accounts")
                        • structure vague assertion → VALUE_CHECK + expected
                        • flag ambiguity (expected source, dynamic list)
                        • leave resolvedLocators EMPTY (no device touched)
                        Output: committed TestCaseIR.json
                                  │
                                  ▼  (git commit — committed TestCaseIR.json)
┌─────────────────────────────────────────────────────────────────────────────┐
│  AUTHORING ARM (continued)  (committed IR → committed Java)                  │
│  Still LLM-bounded: capture + locator resolution are deterministic tools;    │
│  CODE GENERATION below is an LLM stage — it is NOT part of the spine.        │
└─────────────────────────────────────────────────────────────────────────────┘

  committed TestCaseIR.json
         │
         ▼
  CAPTURE HIERARCHY (deterministic CLI — hierarchy-tool)
  • connect to live Perfecto device (IPA/APK installed, creds in vault)
  • Appium getPageSource XML + Perfecto Object Spy + XCUITest tree
  • emit full dump AND pruned tree (interactive elements + ancestors)
  Output: LoginScreen.pageSource.xml, .pruned.json, .objectSpy.json
         │
         ▼
  LOCATOR RESOLUTION (deterministic, cascade)
  cascade: accessibility id > id > class chain > xpath
  sources: OBJECT_REPO > PAGE_SOURCE > OBJECT_SPY > VLM > LLM-guess
  Output: LocatorCandidate.manifest.json (strategy, value, confidence, source)
         │
         ▼
  CODE GENERATION (LLM, offline, one-shot per IR version — authoring arm)
  • IR + manifest → Appium Java (page objects, BaseTest)
  • credentials via vault() calls, never literals
  • output reviewed + committed by an engineer BEFORE the spine sees it
  Output: LoginTest.java  (committed; this is the audit pin)
         │
         ▼  (git commit — handoff to the spine)
┌─────────────────────────────────────────────────────────────────────────────┐
│  THE SPINE  (committed code → verdict)                                       │
│  LLM-free from the STATIC GATE onward. LLM output never touches it;          │
│  it only consumes committed code.                                            │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
  ┌─────────────── STATIC GATE (deterministic, pre-device) ───────────────┐
  │  format check │ mvn compile │ Checkstyle │ Error Prone │              │
  │  locator-manifest rule (every locator must be in repo or manifest)   │
  │  FAIL → reject generation, loop back to CODE GENERATION             │
  └──────────────────────────────────────────────────────────────────────┘
         │ (all PASS)
         ▼
  ┌─────────────── DEVICE GATE (Perfecto, K runs) ───────────────────────┐
  │  run compiled Java on real devices (K=1 signed-off baseline;         │
  │  K=3/5 is a weeks-3-8+ target — raising K = CF6 recorded decision)   │
  │  outcome fields let flakiness be derived once K>1 is decided         │
  └──────────────────────────────────────────────────────────────────────┘
         │
         ▼
  ReplayReport.json
  • pins codeCommit SHA of the Java that ran
  • staticGate results, deviceGate results (K=1 honest), machine verdict
  • healsApplied: NONE (spine does not self-heal)
  • machine PASS is a PRECONDITION; CERTIFIED is issued by an
    attributable individual (CF9), never mechanically
         │
         ▼
  HUMAN EVALUATOR
  • validate test result against original input intent
  • PASS  → done; feed accepted locators + exemplars into FLYWHEEL
  • FAIL  → loop back to INGESTION (the deterministic CLI) with error + original intent
            (BOUNDED — iteration budget + owner are an OPEN Replan R1 item;
             an unbounded regeneration loop is not a decided design)
```

---

## 9. A0 status: deferred (ADR 0015) — what the diagram carries instead

1. **A0's front LLM box is DEFERRED, not current** (ADR 0015, Replan R1 D2). It re-opens
   only on a measured A1 parse-failure rate (M16 corpus + a real free-form-English sample,
   decomposed fold-fixable vs LLM-only, gated on A2's existing LLM-fallback) — not on
   assertion.
2. **Intake is the deterministic ingestion CLI** (Excel POI + Octane REST behind one
   adapter contract), with per-adapter deterministic canonicalization (`spec.md:61`, M15),
   which now MAY carry a committed **phrase-canonicalization table + noise-strip ruleset**
   (ADR 0015) — the lexical work A0 named, done deterministically, crossing no trust
   boundary and adding no injection surface.
3. **Screen-context inference stays A2's job** (§2.2 `NAVIGATE + screenContext`), inside the
   already-screened Invoke Models seam — it is not a reason to resurrect a front A0 surface.
4. **The data-flywheel clarification stands**: F1 is the no-model-call fitness function, not
   "the flywheel"; the flywheel feeds A2, CodeGen, and O6's ensemble.
5. **The spine boundary is unchanged**: A2's committed `TestCaseIR.json` is still the
   handoff point; everything downstream remains LLM-free and consumes only committed
   artifacts.

---

## 10. Cross-References

- Mock artifacts: `mocks/o1-spine/` (`TestCaseIR.json`, `LocatorCandidate.manifest.json`,
  `LoginTest.java`, `ReplayReport.json`).
- Mock suite index: `mocks/README.md` (explains the six-way O1–O6 comparison).
- Canonical blueprint: `blueprint-revision-v2.md` (the deterministic replay pipeline,
  the flywheel, the phase-1/phase-2 split).
- ARB comparison: `mobile-test-automation-poc-arb-comparison.md` (why O1 is the
  production north-star and O3 is the proposed POC).
- Brainstorm: `mobile-test-automation-poc-brainstorm.md` (the six options and their
  trade-offs).

---

# Part II — ASH-Capture: Automated State-Aware Hierarchy Capture

> **Status: PROPOSED this session (2026-07-31).** Not yet an ADR. This section records the
> design produced in this session for automating the Capture Hierarchy stage of the O1
> pipeline. Provenance (new vs already-planned) is in §12 below.

## 11. The ASH-Capture proposal

ASH-Capture lives in the **authoring arm**, upstream of the spine. It replaces the manual
`hierarchy-tool` run. The spine is untouched and remains LLM-free. (Correction per review:
no *decided* spine stage consumes the `NavigationManifest` — it is a **capture provenance
record**; promoting it to a replayed spine input would itself be an ADR-scoped change with
schema, screening, and lineage obligations.) If ASH-Capture breaks
entirely, the spine keeps working off existing manifests and manual capture remains the
escape hatch — the survivability guarantee.

```
A0 → A1 → A2 → [ASH-Capture] → Locator Resolution → Code Gen → spine
```

### 11.1 Screen-signature function (load-bearing)

```
signature(screen) = (skeletonHash, titleAnchor)

skeletonHash  = hash of sorted (elementType, accessibilityId) tuples
               — excludes text content, so dynamic data (balances, timestamps)
                 does not change the hash
titleAnchor   = the screen's accessibility title element, auto-discovered:
                 heuristic finds the header/nav-bar element with an accessibility
                 label on first dump of the screen
```

- Two screens collide only if **both** skeleton and title match.
- Title anchors are **auto-discovered**, not app-team-declared. No new instrumentation ask.
- A screen with **no discoverable title anchor** is flagged `ANCHOR_LESS` and routed to
  the human escape hatch. This is the one structural limit of "no app-team cooperation."

### 11.2 `ScreenGraph` schema (committed, versioned, auditable-not-gated)

```json
{
  "appVersion": "8.4.0",
  "graphVersion": "sha:...",
  "nodes": {
    "LoginScreen": {
      "signature": { "skeletonHash": "h1", "titleAnchor": "Login" },
      "firstSeenAt": "2026-07-29T14:00Z",
      "lastVerifiedAt": "2026-07-29T14:00Z",
      "anchorStatus": "CONFIRMED"
    }
  },
  "edges": [
    {
      "from": "LoginScreen", "to": "HomeScreen",
      "action": { "kind": "TAP", "locator": {"strategy":"ACCESSIBILITY_ID","value":"loginButton"} },
      "cost": 2,
      "sessionPrecondition": "FRESH",
      "provenance": "DISCOVERY",
      "lastVerifiedAt": "2026-07-29T14:00Z",
      "status": "VERIFIED"
    },
    {
      "from": "ROOT", "to": "AccountOverview",
      "action": { "kind": "DEEP_LINK", "locator": {"strategy":"DEEP_LINK","value":"erica://accounts/overview"} },
      "cost": 1,
      "sessionPrecondition": "FRESH",
      "provenance": "DEEP_LINK_PROBE",
      "status": "VERIFIED"
    }
  ]
}
```

- `cost`: `DEEP_LINK=1 < SCROLL=2 < TAP=2 < TYPE=3`. Graph search minimizes cost → prefers
  deep links.
- `status`: `VERIFIED | UNVERIFIED | BROKEN`. On each release, edges flip to `UNVERIFIED`
  and re-verify lazily on first capture.
- `provenance`: `DISCOVERY | GRAPH_SEARCH | DEEP_LINK_PROBE | MANUAL_CAPTURE`.

### 11.3 `NavigationManifest` schema (capture provenance record — PROPOSED)

```json
{
  "screenContext": "AccountOverview",
  "rootMode": "FRESH_LOGIN",
  "rootScreen": "LoginScreen",
  "steps": [
    { "action": "TAP",  "locator": {"strategy":"ACCESSIBILITY_ID","value":"usernameField"} },
    { "action": "TYPE", "locator": {...}, "value": "vault:user_qa" },
    { "action": "TAP",  "locator": {...}, "value": "loginButton" },
    { "action": "DEEP_LINK", "locator": {...}, "value": "erica://accounts/overview" }
  ],
  "provenance": "GRAPH_SEARCH",
  "graphPath": ["ROOT->AccountOverview"],
  "irRef": null,
  "version": "sha:...",
  "appVersion": "8.4.0"
}
```

- `rootMode`: `FRESH_LOGIN` (default) or `DEEP_LINK` (deep link lands the root screen
  directly).
- `provenance` tracks whether the path came from an IR, a graph search, a discovery run,
  or a manual capture — so audits can trace origin.
- **Status honesty (review fix):** today no decided spine stage consumes this artifact —
  the spine's committed inputs are `TestCaseIR.json` + the Java, and the committed Java
  remains *the* audit pin. *If* ADR 0014 promotes the manifest to a replayed spine input
  (reading `steps` + `rootMode`; the rest audit metadata), that promotion carries its own
  schema, ADR 0009 screening, and ADR 0012 lineage obligations.

### 11.4 Capture flow (the decision tree)

```
request(screenContext)
  │
  ├─ ensure root: FRESH_LOGIN via stored creds (Touch/Face ID creds)
  │
  ├─ screen in graph AND a VERIFIED path exists from root?
  │     YES → graph search (min-cost), replay steps, dump. NO LLM.
  │            [target ~90% of runs — UNMEASURED until the §12.4 spike]
  │
  ├─ screen in graph but path UNVERIFIED (post-release)?
  │     → replay path; if lands on expected signature → re-VERIFY, dump.
  │       if lands elsewhere → mark edge BROKEN, fall through to discovery.
  │
  └─ screen NOT in graph, or path BROKEN → DISCOVERY (LLM):
        loop:
          1. dump current hierarchy, compute signature
          2. LLM proposes ≤K candidate next actions
             (input: screenshot + pruned tree + current signature + target)
          3. deterministic validator filters by:
               • locator cascade + confidence floor
               • denylist (logout/transfer/pay/confirm patterns) — defense-in-depth
               • known graph edges from this node (prefer verified)
               • step budget remaining
          4. execute survivor via DeviceSession.act()
          5. re-dump, compute new signature
          6. record edge (from->to) into graph [side effect]
          7. if signature == target → commit manifest + edges. DONE
             if no-progress (3x same sig) OR budget exhausted OR timeout
               → HUMAN ESCAPE HATCH
```

**Budgets:** ≤15 actions per discovery · ≤60s per step · ≤3 no-progress strikes · hard
10-min session cap (re-login if hit).

**Screening (ADR 0009).** Every LLM ingress/egress in this loop is a screening call site —
the screenshot + pruned tree entering the proposer, and the proposed actions leaving it.
The call-site map belongs in ADR 0014; the loop cannot ship without it.

**Known defect (Replan R1 D1/S1 — design before measuring).** The success predicate
(`signature == target`) compares against the *stored* signature. On a legitimately changed
screen — the very case discovery exists for — the loop can never match and
deterministically exhausts its budget into the escape hatch (~20% of screens per release
under the drift assumption). A signature **re-keying** mechanism is required; until it is
designed, the <10% escape-hatch target fails at every release.

### 11.5 Drift/repair loop

- **On monthly release** (new `appVersion`): all edges flip to `UNVERIFIED`. Captures
  re-verify lazily — the first capture of each changed screen pays the discovery cost;
  unchanged screens re-verify cheaply. This is the accepted cold-miss cost (planning
  assumption ~20% of screens per release — unmeasured).
- **On capture failure** (landed signature ≠ expected): the specific edge is marked
  `BROKEN`; re-discovery runs from the last known-good node, repairing just that sub-path.
- **Graph versioning**: a `ScreenGraph` is committed per `appVersion`; diffs are auditable
  across releases.

### 11.6 Deep-link sub-loop (supplemental)

**Discovery (one-time per release + on demand):**
1. **Static parse** — APK intent filters (Android) / entitlements associated domains
   (iOS) → scheme + hosts. (iOS yields scheme only; routes are in code.)
2. **LLM proposes** candidate routes per screen from app docs + screen titles.
3. **Deterministic probe** — launch each candidate deep link, check the landed signature
   against the target screen. Keep only confirmed matches as `DEEP_LINK` edges (cost 1).

**Synthesis ("create them along the way"):** when discovery finds a multi-tap path to a
screen *and* a deep link is probe-confirmed for that same screen, store the deep link as
the preferred edge (cost 1) and keep the tap path as fallback. We **discover** existing
deep links and store them as edges as they're confirmed — we do **not** invent deep links
the app doesn't support (that would need app-team work and is out of scope).

**Honest scope:** deep links cover a subset — smaller on iOS where routes live in code.
They supplement, never replace, the graph. **Security gap (review):** the deterministic
probe currently has **no URL denylist** — the validator's action denylist does not cover
deep-link URLs, so a probed route like `erica://transfer?...` would execute and, if
confirmed, persist as the *preferred cost-1 edge*. A URL deny/allow-list is a Lane-2
ADR 0014 item (Replan R1 D1).

### 11.7 Device interface

```
DeviceSession
├── login(vaultRef)            → {ok}
├── screenshot()               → bytes
├── hierarchy()                → {pageSourceXml, prunedTree, objectSpy}
├── act(action, locator)       → {ok, landedSignature}
└── launchDeepLink(url)        → {ok, landedSignature}

Implementations:
├── PerfectoSession        (cloud: Appium + Object Spy)
├── LocalIOSSession        (xcrun simctl + Appium XCUITest)
└── LocalAndroidSession    (adb + Appium UiAutomator2)
```

- `hierarchy()` returns a **normalized** form regardless of backend. Object Spy is
  Perfecto-rich on cloud; on local it falls back to the XCUITest tree (iOS) /
  `uiautomator dump` (Android). The locator cascade degrades gracefully and the `source`
  field on each locator marks where it came from — so audits know which captures were
  Perfecto vs local.

### 11.8 Human escape hatch (the <10%, extreme/boundary only)

Triggered by: discovery failure (budget exhausted / no-progress / `ANCHOR_LESS` screen /
unreachable state).

```
human manually navigates app to target screen
  (via the device session, which records every action taken)
  │
  └─ system captures the action stream:
       • resolves locators per step (cascade)
       • computes signature per landed screen
       • commits:
           - NavigationManifest[target]   (the path the human took)
           - graph edges for every transition
           - discovered title anchors for each new screen
```

So even the escape hatch produces committed, auditable artifacts — the human only steers;
the system records. This mirrors the blueprint's Phase-1 pattern (human drives, system
records, flywheel accumulates). Over releases, the escape-hatch bucket should shrink as
anchors get discovered and edges get verified.

### 11.9 Trade-offs baked in

| Trade-off | Resolution in this design |
|---|---|
| Determinism vs coverage | Hybrid by design; graph = deterministic cache, discovery = non-deterministic frontier |
| Auditability vs maintenance | Graph is auditable-not-gated; drift loop is the maintenance cost |
| Autonomy vs app-team cooperation | Anchors auto-discovered, no app-team ask; escape hatch covers the gap |
| Safety | Environmental (resettable test env, "prod-grade data"); denylist is defense-in-depth only. **"Prod-grade data" is undefined** — production-*derived* data flips ADR 0010's PII condition and the whole control regime (Replan R1 D4) |
| Session | 10-min, from-root, cheap re-login via stored creds |
| Deep links | Supplemental, prefer-when-available; can't fully cover iOS |
| Speed vs 100% | Deep-link cost-1 edges optimize speed; graph + escape hatch chase 100% discoverability |

### 11.10 Coverage target

- **>90% automated** via graph replay + discovery.
- **<10% human escape hatch**, only for extreme/boundary failures (anchor-less screens,
  unreachable states, signature-defeating app states).

Both numbers are **unmeasured targets** — falsifiable claims pending the §12.4 spike, not
facts. And the <10% figure collapses while the §11.4 re-keying defect stands: every
legitimately changed screen then routes to the hatch deterministically, exactly when
demand peaks (each release).

### 11.11 Open watch-items (not blockers)

1. The **`ANCHOR_LESS` → escape-hatch** routing is the one place "no app-team cooperation"
   bites. If the anchor-less bucket is larger than ~10% in practice, fallbacks are either
   (a) ask the app team for title IDs on just those screens, or (b) a learned-fingerprint
   path for that subset. Worth measuring early on a real release.
2. The **deep-link "synthesis" interpretation** — this design reads it as *discovering
   existing deep links and storing them as edges*, not *inventing new ones*. If the intent
   is to have the system propose new deep-link routes for the app team to implement, that
   is a separate, larger feature and should be split out.
3. The **discovery success predicate** (§11.4 defect note): without signature re-keying,
   changed screens exhaust their budget into the escape hatch by construction. Re-keying
   design (Replan R1 S1) strictly precedes the measurement spike — measuring first would
   size a known-broken loop.

---

## 12. Provenance — what is NEW this session vs already planned

This section tracks the origin of every idea in Part II, so a reader (or a future ADR)
can tell what is a fresh proposal from this session and what is already decided elsewhere.

### 12.1 NEW — proposed this session (2026-07-31), not yet in any ADR or prior artifact

These are the net-new design contributions from this session. None of them appear in the
existing ADRs, the blueprint, or the brainstorm. They would need their own ADR(s) before
implementation.

| # | New contribution | Where it appears |
|---|---|---|
| N1 | **ASH-Capture subsystem** as a named component of the authoring arm | §11 |
| N2 | **Hybrid discovery loop** (LLM proposes + deterministic validator shortlists) for state-aware navigation | §11.4 |
| N3 | **`NavigationManifest`** as a new committed artifact type (per-screen deterministic path; capture provenance record — spine-input status **undecided**) | §11.3 |
| N4 | **`ScreenGraph`** as a new committed, versioned, auditable artifact (nodes = screen signatures, edges = deterministic locator-actions) | §11.2 |
| N5 | **Screen-signature function** = `(skeletonHash, titleAnchor)` with auto-discovered accessibility title anchors | §11.1 |
| N6 | **Deep-link sub-loop** — static parse + LLM-proposed routes + deterministic probe; deep links as `DEEP_LINK` graph edges (cost 1) | §11.6 |
| N7 | **Drift/repair loop** tied to monthly release cadence (edges flip `UNVERIFIED` on new appVersion; lazy re-verify; `BROKEN`-edge repair) | §11.5 |
| N8 | **Human escape hatch** for the <10% extreme/boundary cases (human steers, system records and commits graph edges + manifest) | §11.8 |
| N9 | **`DeviceSession` abstraction** with Perfecto / local-iOS (xctools) / local-Android (adb) implementations and normalized hierarchy output | §11.7 |
| N10 | **Budgets & termination** for discovery (≤15 actions, ≤60s/step, ≤3 no-progress strikes, 10-min session cap) | §11.4 |
| N11 | **Coverage target framing**: >90% automated, <10% human escape hatch | §11.10 |
| N12 | **`ANCHOR_LESS` routing** as the named structural limit of "no app-team cooperation" | §11.1, §11.11 |
| N13 | **A0 Normalizer** (LLM intake stage upstream of A1) — proposed this session in Part I; NOT in any ADR or the blueprint. **DECIDED — DEFERRED per ADR 0015 (Accepted 2026-08-01, Replan R1 D2):** A0-as-an-LLM-stage is an evidence-gated future re-open; the deterministic phrase-canon/noise-strip it named is folded into the M15 adapter-canonicalization surface, and screen-context inference stays A2's. Both A0 flows are **second paths into already-screened classes (1)/(3)** (`0009:90–92`) — **no fourth flip** (the "2/3→3/3" framing predates ADR 0014 and is stale). Its ADR 0009 "call-site map" = second path into the existing ingestion (class 1) and Invoke Models (class 3) call sites, not new call sites. *(Corrected: the first draft mislisted A0 under §12.2 "already planned".)* | §2.0, §8, §9 |

### 12.2 ALREADY PLANNED — in existing ADRs, the blueprint, or prior session artifacts

These are pre-existing decisions/constraints that ASH-Capture *inherits* or *respects* but
did not invent. ASH-Capture is consistent with all of them; it does not change them.

| # | Already-decided item | Source | How ASH-Capture uses it |
|---|---|---|---|
| A1 | **LLM-free spine** — replay consumes only committed code, no LLM in execution path | `blueprint-revision-v2.md:73` | ASH-Capture lives entirely in the authoring arm; the spine consumes only the committed `NavigationManifest` |
| A2 | **`hierarchy-tool`** — CLI + service that dumps `getPageSource` XML + Object Spy + pruned tree | `blueprint-revision-v2.md:26` | ASH-Capture *automates* this tool's invocation; the tool's outputs are unchanged |
| A3 | **Pruned tree** (interactive elements + ancestors) to fit LLM context | `blueprint-revision-v2.md:115` | Used as LLM input in the discovery loop (§11.4 step 2) |
| A4 | **Locator cascade** (accessibility id > id > class chain > xpath) and sources (OBJECT_REPO > PAGE_SOURCE > OBJECT_SPY > VLM > LLM-guess) | brainstorm §7, mocks | The deterministic validator filters proposed actions by this cascade (§11.4 step 3) |
| A5 | **Credential isolation** — execution holds no long-lived creds, uses short-lived single-run session tokens | ADR 0013 | ASH-Capture's `DeviceSession.login()` uses vault refs, not long-lived creds; the capture worker holds no gateway credential |
| A6 | **Tamper-evident lineage** — per-conversion hash chain anchored in immutable storage | ADR 0012 | The committed `ScreenGraph` and `NavigationManifest` should join the lineage chain; their `version`/`graphVersion` SHAs are the audit pins |
| A7 | **Phase-1 pattern** — human drives, system records, flywheel accumulates | `blueprint-revision-v2.md:39-51` | The human escape hatch (§11.8) reuses this exact pattern |
| A8 | **Data flywheel** — accepted conversions become exemplars / preference labels | `blueprint-revision-v2.md:107` | Accepted graph edges + manifests feed the flywheel; escape-hatch captures become discovery exemplars |
| A9 | **K-run flakiness policy** — `STABLE / FLAKY / UNKNOWN` based on pass ratio (K=1 is the signed-off baseline; raising K is a CF6 recorded decision — Replan R1 D6) | `blueprint-revision-v2.md:77` | Unchanged; ASH-Capture produces the hierarchy the spine then replays under K-run policy |
| A10 | **Monthly release cadence** with new features / improvements | user-stated constraint | Drives the drift/repair loop (§11.5) |
| A11 | **10-minute session, re-login via stored Touch/Face-ID creds, lower test env inside secure network** | user-stated constraint | Drives the session model (§11.4 root, §11.4 budgets) and the environmental safety posture (§11.9) |
| A12 | **App supports "erica" deep-link scheme** (not all screens) | user-stated constraint | Drives the deep-link sub-loop (§11.6) |

### 12.3 Relationship to the spine contract (restated for safety)

ASH-Capture does **not** alter the spine contract. The spine still:
- consumes only committed artifacts (`NavigationManifest`, `TestCaseIR`, `LoginTest.java`),
- runs no LLM, no graph search, no discovery,
- holds no long-lived credentials (ADR 0013),
- pins every verdict to a committed SHA (ADR 0012 lineage).

If the entire ASH-Capture subsystem fails, the spine continues to work off existing
manifests, and manual `hierarchy-tool` capture remains the documented escape hatch. That
fallback is the survivability guarantee that lets ASH-Capture ship incrementally.

### 12.4 Next steps toward an ADR

Before ASH-Capture becomes implementable, it needs:
1. An **ADR** (next free number, 0014) recording the hybrid-discovery + committed-graph +
   manifest decision and its trade-offs (this §11 is the draft body).
2. A **measurement spike** on one real release to size the `ANCHOR_LESS` bucket (open
   watch-item 1) and the iOS deep-link coverage (open watch-item 2).
3. A **security-review queue entry** (per ADR 0010 as amended) since ASH-Capture introduces
   a new LLM-in-the-loop surface and a new committed artifact type.

---

## 13. How the graph is stored — PostgreSQL, not a graph DB

> **Decision: store the `ScreenGraph` in PostgreSQL.** No graph database. This section
> records the reasoning and the schema. This is a candidate section of ADR 0014.

### 13.1 Why the graph doesn't need a graph DB

The deciding factor is **size and access pattern**, not the fact that it is "a graph."

**Size.** A mobile banking app has on the order of hundreds of screens and a few thousand
edges. A graph DB's whole reason to exist — traversal at scale, billion-edge workloads,
Cypher/Gremlin query optimization — is wasted on a graph this small. Dijkstra over a few
thousand edges runs in **microseconds in process memory**. You don't need a database engine
to do the traversal; you need a database to **store and version** the graph, which Postgres
does fine.

**Access pattern.** The only query is "shortest path from root to target for a given
appVersion." That is: load one appVersion's subgraph into memory, run Dijkstra, done.
There are no complex multi-hop ad-hoc traversals, no concurrent multi-service graph
queries, no recursive Cypher patterns that SQL would express badly. The workload is
*load + in-process search + write back edge updates* — a relational store handles it
directly.

### 13.2 Why Postgres specifically — the ADRs already decided this

The existing architecture already chose Postgres as the single primary store, and the
graph is exactly the kind of data that decision covers:

- **ADR 0006** — single primary store partitioned by lifecycle. Adding a graph DB
  introduces a *second* system of record without justification, plus the operational cost
  (backup, DR, security review per ADR 0010, schema migration tooling) for a graph of a few
  thousand edges.
- **ADR 0012** — tamper-evident lineage as a per-conversion hash chain in Postgres anchored
  to immutable object storage. The `ScreenGraph` is **audit-grade data** — every edge
  carries `provenance` and `lastVerifiedAt`, and every graph change must be tamper-evident.
  That's easiest if the graph lives in the same store as the lineage chain it joins. A
  separate graph DB means a separate integrity mechanism.
- **ADR 0007** — outbox for provenance writes. Graph mutations should go through the same
  outbox so they're consistent with lineage. Trivial if the graph is in Postgres;
  cross-store if it isn't.
- **ADR 0011** — evidence object storage behind an S3 port. The full graph JSON for each
  version can be anchored to object storage as immutable evidence, with Postgres holding
  the queryable index — the identical pattern already used for lineage.

### 13.3 Concrete schema (PostgreSQL)

Three tables, versioned by snapshot (append-only, matching ADR 0012's supersede-not-update
semantics):

```sql
-- one row per committed graph version (the audit pin)
CREATE TABLE screen_graph_versions (
  graph_version_sha  TEXT PRIMARY KEY,         -- hash of the graph contents
  app_version         TEXT NOT NULL,
  created_at          TIMESTAMPTZ NOT NULL,
  committed_by        TEXT NOT NULL,            -- engineer or "ash-capture"
  prev_version_sha    TEXT REFERENCES screen_graph_versions(graph_version_sha),
  lineage_digest      TEXT NOT NULL             -- intended graph lineage link; ADR 0012
                                                -- defines per-conversion chains only —
                                                -- extending it to graph versions is an
                                                -- ADR 0012 amendment (Replan R1 D3)
);

-- nodes for that version
CREATE TABLE screen_graph_nodes (
  graph_version_sha   TEXT REFERENCES screen_graph_versions(graph_version_sha),
  screen_id           TEXT NOT NULL,
  skeleton_hash       TEXT NOT NULL,
  title_anchor        TEXT,                     -- NULL = ANCHOR_LESS
  anchor_status       TEXT NOT NULL,            -- CONFIRMED | ANCHOR_LESS
  first_seen_at       TIMESTAMPTZ NOT NULL,
  last_verified_at    TIMESTAMPTZ,
  PRIMARY KEY (graph_version_sha, screen_id)
);

-- edges for that version
CREATE TABLE screen_graph_edges (
  graph_version_sha   TEXT REFERENCES screen_graph_versions(graph_version_sha),
  edge_id             TEXT NOT NULL,
  from_screen         TEXT NOT NULL,
  to_screen           TEXT NOT NULL,
  action_kind         TEXT NOT NULL,            -- TAP | TYPE | SCROLL | DEEP_LINK
  locator_json        JSONB NOT NULL,           -- {strategy, value}
  cost                INT NOT NULL,
  session_precondition TEXT NOT NULL,           -- FRESH | NONE
  provenance          TEXT NOT NULL,            -- DISCOVERY | GRAPH_SEARCH | DEEP_LINK_PROBE | DRIFT_REPAIR | MANUAL_CAPTURE
  status              TEXT NOT NULL,            -- VERIFIED | UNVERIFIED | BROKEN
  last_verified_at    TIMESTAMPTZ,
  PRIMARY KEY (graph_version_sha, edge_id)
);

CREATE INDEX ON screen_graph_edges (graph_version_sha, from_screen) WHERE status = 'VERIFIED';
```

**Versioning model.** Each committed graph is a **full snapshot** keyed by
`graph_version_sha`. Drift repair doesn't mutate rows — it writes a *new*
`graph_version_sha` (with `prev_version_sha` pointing at the prior one). Diffing two
releases = comparing their node/edge sets. This is the same supersede-not-update semantics
ADR 0012 mandates for lineage, applied to the graph.

**Why snapshot-per-version, not append-only-edge-rows.** The graph is small, so snapshot
storage is cheap, and snapshot diffs are trivial to audit ("here's exactly what changed
between v8.4 and v8.5"). Append-only edges with valid-from/valid-to (slowly-changing-
dimension style) would be more storage-efficient but harder to diff and easier to get
wrong. For a few thousand edges, simplicity wins.

### 13.4 How capture uses it

```python
# capture.py (mock logic)
def load_graph_for_version(app_version):
    gv = latest_graph_version_sha(app_version)
    nodes = fetch_nodes(gv)          # SELECT ... WHERE graph_version_sha = gv
    edges = fetch_edges(gv)         # SELECT ... WHERE graph_version_sha = gv AND status='VERIFIED'
    return Graph(nodes, edges)      # in-memory object

def capture(target, app_version, device):
    g = load_graph_for_version(app_version)        # one round-trip
    path = dijkstra(g, root, target)              # in-process, microseconds
    device.login("vault:user_qa")
    for e in path:
        device.act(e.action, e.locator)
    return device.hierarchy()
```

One read to load the version, in-process search, then act. No graph DB query language, no
traversal server, no second datastore to keep available.

### 13.5 When the answer would flip (the honest caveat)

A graph DB would become justified if **any** of these became true:

- The graph grew to millions of edges (e.g., capturing element-level state graphs, not
  just screens).
- Traversal became the dominant workload with complex multi-hop patterns SQL expresses
  poorly.
- Multiple services needed concurrent graph traversal at scale.

None of those apply to a per-app screen graph of a few hundred nodes. If one ever does,
the snapshot-per-version model in Postgres still works as the system of record; a graph DB
could be added *in front of it* as a traversal cache later, fed from Postgres — but that's
a future optimization, not a day-one decision.

### 13.6 Recommendation

Stay on PostgreSQL. Add the three tables above. Route graph mutations through the existing
outbox (ADR 0007) so they join the lineage chain (ADR 0012). Anchor each version's full
JSON to object storage via the ADR 0011 port as immutable evidence. No new datastore, no
new operational burden; the *storage choice* adds no new security-review surface — but
ASH-Capture as a subsystem still requires the §12.4 security-review queue entry (the
first draft's "no new security review surface" overstated this and contradicted §12.4).
The graph inherits the tamper-evidence and auditability the rest of the system already
has, subject to the ADR 0012 amendment flagged in §13.3.

This is exactly the kind of decision that should become a section of **ADR 0014**, since
it touches ADRs 0006, 0007, 0011, and 0012.


