# o7 Pipeline — End-to-End Walkthrough (Zelle Send-Money)

> **What this is.** A stage-by-stage walkthrough of the **o7 pipeline** — the
> interpreter-based **fork of o1**, where o1's LLM→Java *code-generation* stage is deleted and
> the committed `TestCaseIR` is executed directly by a **version-pinned, LLM-free interpreter**
> over Appium/Perfecto. o7 shares o1's spine *contract* (committed reviewed artifacts, an
> LLM-free deterministic spine, SHA-pinned auditability); it changes the *shape of the
> executable*. It traces one real banking flow — **Zelle send-money** — from an Octane test
> case all the way to a certified `ReplayReport`.
>
> **Lineage.** o7 forks o1. Where an artifact is unchanged from o1, this doc reuses the o1
> mock set (`mocks/o1-spine/`); o7's changed/new artifacts live in `mocks/o7-spine/`. o1
> (code-gen) and o7 (interpreter) both remain live.
>
> **Status:** DRAFT companion to the Stage-1 brainstorm
> (`docs/research/mobile-test-automation-interpreter-spine-brainstorm.md`). Reflects the
> owner-confirmed design bundle **F-B · E2 · H-SB · C-MIG · R-YES · A-STD**, with the
> pre-commit-review question resolved as **R4 + R2** (see §0 and §7). Every artifact below is
> *mocked illustration*, shaped to match the committed mocks in `mocks/o7-spine/` (o7-changed)
> and `mocks/o1-spine/` (shared authoring-arm artifacts).
>
> **Scenario throughout:** `ACC-2087` — *"Send $25 to a saved Zelle recipient and see the
> confirmation."* Flow: **Sign in → Home → Pay & Transfers → Zelle → Send money.**
> Platform: iOS / iPhone 15 / iOS 17.4, on the Perfecto cloud.

---

## 0. What o7 changes from o1 (read this first)

The **two-halves** shape is unchanged: an **LLM-bounded authoring arm** produces committed,
reviewed artifacts; an **LLM-free spine** consumes only committed artifacts; the handoff is a
**git commit**. Exactly **one thing** changes — *the shape of the executable*.

| o1 (code-gen, parent) | o7 (interpreter, this doc) |
|---|---|
| LLM generates per-test **Java/TestNG** → engineer reviews+commits the Java | **No generation.** The committed **`TestCaseIR.json`** *is* the executable |
| Static gate: `mvn compile` / Checkstyle / Error Prone / format | **IR gate**: JSON-schema + closed-opcode + bounded-waits + no-orphan-locator + no-literal-creds + ambiguity-clear |
| Device gate: TestNG runs the compiled Java | **Interpreter** walks IR steps over Appium (java-client behind a seam) |
| Audit pin = `codeCommit` (SHA of the Java) | Audit pin = **`irDigest` + `interpreterVersion`**; Perfecto server/driver versions captured as *evidence* (unpinnable remainder) |
| **Engineer reviews every generated test before commit** | **Auto-commit by a service principal (R1 substrate); the human moves to *after* the run (R4) and is novelty-sampled (R2)** |

Two properties are **structural**, not policy, and carry over untouched:
- **LLM-free execution.** The interpreter contains no model call. Locator fallback is an
  *authoring-time* concern; at replay every locator is already committed.
- **No self-heal (`healPolicy: NONE`).** A locator miss is a **red build**, never a runtime
  repair. This one policy line is the entire difference from every "self-healing" vendor —
  and it is why the verdict is a *stable regression signal* (runtime-LLM agents fail the
  all-k-runs-must-agree regime by `pass^k` arithmetic).

### The review decision, in one paragraph (R4 + R2)
The old pre-commit engineer review did **two** jobs: **correctness** (does the IR match
intent?) and **attribution** (an individual principal signs the ADR-0012 hash-chain, spec
M37). Its **security** rationale was *already retired* by ADR 0013, which explicitly rejected
per-script human review as the control ("dissolves the system's reason to exist") and instead
removed all credentials from the execution path. So the review's only residue is correctness +
a signature. **R4** moves the human to the *already-mandatory* §7 evaluator (post-run) as the
sole attribution anchor; **R2** thins even that touch by routing only *novel* test-shapes to a
human, using the spec's existing CF4/M21 novelty-sampling flag; **R1** (deterministic IR gate +
no-device dry-run) is the substrate that makes service-principal auto-commit defensible.
**Hard line:** the *certification* verdict still requires a named individual (CF9 + M37) — the
human is removed from *authoring/commit*, never from *certification*.

---

## 1. The whole pipeline on one page

![o7 pipeline end to end for the Zelle send-money flow: the LLM-bounded authoring arm produces a committed TestCaseIR and locator manifest; a git commit signed by a service principal hands them to the LLM-free spine, where a deterministic IR gate and a version-pinned interpreter run the Zelle flow on Appium/Perfecto and emit a ReplayReport, with a single human evaluator certifying after the run.](o1-diagrams/o7-pipeline-zelle-end-to-end.svg)

*Figure 1 — o7 end to end on the Zelle send-money flow. The same flow is shown as text below for detail and accessibility.*

```
        AUTHORING ARM  (LLM-bounded, produces committed artifacts)                 THE SPINE  (LLM-free)
  ───────────────────────────────────────────────────────────────────────  ───────────────────────────────────
  Octane ACC-2087
      │
      ▼
  ┌──────────┐   ┌──────────┐   ┌────────────────┐   ┌─────────────────────┐    ┌──────────┐   ┌──────────────┐   ┌──────────┐
  │ INGEST   │──►│ A1 PARSE │──►│ A2 SEMANTIC    │──►│ CAPTURE HIERARCHY + │──► │ IR GATE  │──►│ INTERPRETER  │──►│ VERDICT  │
  │ (det.)   │   │ (det.)   │   │ INTERP (det-   │   │ LOCATOR RESOLUTION  │    │ (det.,   │   │ walks IR on  │   │ ReplayRpt│
  │          │   │ skeleton │   │ first, LLM     │   │ (det. cascade,      │    │ pre-     │   │ Appium/      │   │ irDigest │
  │          │   │          │   │ fallback)      │   │ LLM last-resort)    │    │ device)  │   │ Perfecto     │   │ pinned   │
  └──────────┘   └──────────┘   └───────┬────────┘   └──────────┬──────────┘    └────┬─────┘   └──────┬───────┘   └────┬─────┘
                                        │ TestCaseIR.skeleton   │ LocatorCandidate        │ PROCEED       │ per-step        │
                                        ▼ (structure)           ▼ .manifest.json          ▼               ▼ evidence        ▼
                              ══════════ committed TestCaseIR.json + manifest ═══════════ git commit (SERVICE principal, R1/R4) ═══
                                                                                          │                                 │
                                                                                          └────────── LLM-free from here ────┘
                                                                                                                            │
                                                                                                            ┌───────────────▼──────────────┐
                                                                                                            │ §7 HUMAN EVALUATOR (R4)       │
                                                                                                            │ • novelty-sampled (R2)        │
                                                                                                            │ • PASS = attributable CERTIFY │
                                                                                                            │ • FAIL → bounded loop to A2   │
                                                                                                            └───────────────────────────────┘
```

The **only LLM call sites** are inside the authoring arm and are all *bounded* (A2 semantic
fallback, locator last-resort, and — outside this flow — ASH-Capture proposers). **Nothing
past the git commit calls a model.**

---

## 2. Authoring arm — building the committed Zelle IR

### 2.1 Ingestion (deterministic) — Octane → normalized intent

The Octane test case `ACC-2087` enters through the deterministic ingestion CLI (Excel/Octane
adapters, per-adapter canonicalization). The raw script:

> *Send money via Zelle:*
> 1. sign in with test credentials
> 2. from the home screen, open Pay & Transfers
> 3. open Zelle
> 4. send $25 to the saved recipient "Alex Rivera"
> 5. verify the confirmation shows "$25.00 sent to Alex Rivera"

Screening (ADR 0009) runs at the ingestion boundary; the canonicalized intake is emitted.
*(A0 the LLM normalizer is RATIFIED with open obligations — orthogonal to this flow.)*

### 2.2 A1 Parser (deterministic) — structure only

A1 splits intent into a **skeleton** — raw intent text per step, recognized patterns, no
semantics filled. Shape matches `mocks/o1-spine/TestCaseIR.skeleton.json`:

```json
{
  "sourceSystem": "octane", "sourceId": "ACC-2087",
  "title": "Send $25 to a saved Zelle recipient and see the confirmation",
  "preconditions": ["app freshly installed", "on the login screen"],
  "testData": { "username": "vault:user_qa", "password": "vault:pass_qa",
                "recipient": "Alex Rivera", "amount": "25.00" },
  "platforms": ["IOS", "ANDROID"],
  "provenance": { "a1Version": "sha:a1:6f2b...", "derivedFrom": "sha:a0:1c9d...", "parsedAt": "2026-08-05T10:02Z" },
  "steps": [
    { "index": 0, "intent": "sign in with test credentials", "recognizedPattern": "login",
      "credsNote": "present-but-unresolved", "action": null, "target": {"screenContext": null}, "ambiguityFlags": [] },
    { "index": 1, "intent": "open Pay & Transfers from the home screen", "recognizedPattern": "navigate",
      "action": null, "target": {"screenContext": null}, "ambiguityFlags": [] },
    { "index": 2, "intent": "open Zelle", "recognizedPattern": "navigate", "action": null, "ambiguityFlags": [] },
    { "index": 3, "intent": "send $25 to saved recipient Alex Rivera", "recognizedPattern": "form-submit",
      "action": null, "ambiguityFlags": ["recipient-selection-mechanism-unspecified"] },
    { "index": 4, "intent": "verify confirmation shows the sent amount and recipient", "recognizedPattern": "assertion",
      "action": null, "ambiguityFlags": [] }
  ]
}
```

Note the `ambiguityFlag` on step 3 — A1 doesn't know *how* the recipient is chosen (tap a saved
tile? search?). **This flag is now load-bearing** (see §4, the IR gate blocks on unresolved flags).

### 2.3 A2 Semantic Interpreter (deterministic-first, LLM fallback) — the committed IR

A2 expands compound steps into runtime opcodes, resolves the navigation into `NAVIGATE` +
`screenContext`, structures the assertion, and *resolves the ambiguity flag* (deterministically
if the login/navigate patterns match a known template; via bounded LLM fallback otherwise — the
**last** model call before the commit). It leaves `resolvedLocators` empty (no device touched yet).

Expanding the 5 business steps into interpreter opcodes gives **11 committed steps**. This is the
**committed `TestCaseIR.json`** — the executable. **F-B/E2 add the three runtime fields**
(`timeoutMs`, `syncAfter`, `healPolicy`) the interpreter needs:

```json
{
  "sourceSystem": "octane", "sourceId": "ACC-2087",
  "title": "Send $25 to a saved Zelle recipient and see the confirmation",
  "irVersion": "sha:ir:2087:d41c9a...", "irDigest": "sha:ir:2087:d41c9a...",
  "testData": { "username": "vault:user_qa", "password": "vault:pass_qa",
                "recipient": "Alex Rivera", "amount": "25.00" },
  "platforms": ["IOS", "ANDROID"],
  "provenance": { "a2Version": "sha:a2:8b1e...", "irVersion": "sha:ir:2087:d41c9a...", "committedAt": "2026-08-05T10:07Z" },
  "steps": [
    { "index": 0, "action": "TAP",  "timeoutMs": 7000, "syncAfter": "WAIT_FOR_IDLE", "healPolicy": "NONE",
      "target": { "naturalReference": "the username field", "elementType": "field", "screenContext": "LoginScreen",
        "resolvedLocators": [{ "strategy": "ACCESSIBILITY_ID", "value": "usernameField", "confidence": 0.98, "source": "OBJECT_REPO" }] } },
    { "index": 1, "action": "TYPE", "inputData": "${testData.username}", "timeoutMs": 7000, "syncAfter": "NONE", "healPolicy": "NONE",
      "target": { "naturalReference": "the username field", "screenContext": "LoginScreen",
        "resolvedLocators": [{ "strategy": "ACCESSIBILITY_ID", "value": "usernameField", "confidence": 0.98, "source": "OBJECT_REPO" }] } },
    { "index": 2, "action": "TYPE", "inputData": "${testData.password}", "timeoutMs": 7000, "syncAfter": "NONE", "healPolicy": "NONE",
      "target": { "naturalReference": "the password field", "screenContext": "LoginScreen",
        "resolvedLocators": [{ "strategy": "ACCESSIBILITY_ID", "value": "passwordField", "confidence": 0.98, "source": "OBJECT_REPO" }] } },
    { "index": 3, "action": "TAP",  "timeoutMs": 7000, "syncAfter": "WAIT_FOR_IDLE", "healPolicy": "NONE",
      "target": { "naturalReference": "the Sign In button", "screenContext": "LoginScreen",
        "resolvedLocators": [{ "strategy": "ACCESSIBILITY_ID", "value": "loginButton", "confidence": 0.97, "source": "OBJECT_REPO" }] } },
    { "index": 4, "action": "ASSERT", "timeoutMs": 8000, "syncAfter": "NONE", "healPolicy": "NONE",
      "target": { "naturalReference": "the home dashboard", "screenContext": "HomeScreen",
        "resolvedLocators": [{ "strategy": "ACCESSIBILITY_ID", "value": "homeDashboard", "confidence": 0.95, "source": "OBJECT_REPO" }] },
      "assertion": { "kind": "ELEMENT_PRESENT", "expected": null } },
    { "index": 5, "action": "TAP",  "timeoutMs": 7000, "syncAfter": "WAIT_FOR_IDLE", "healPolicy": "NONE",
      "target": { "naturalReference": "Pay & Transfers tab", "screenContext": "HomeScreen",
        "resolvedLocators": [{ "strategy": "ACCESSIBILITY_ID", "value": "payTransfersTab", "confidence": 0.96, "source": "OBJECT_REPO" }] } },
    { "index": 6, "action": "TAP",  "timeoutMs": 7000, "syncAfter": "WAIT_FOR_IDLE", "healPolicy": "NONE",
      "target": { "naturalReference": "the Zelle option", "screenContext": "PayTransfersScreen",
        "resolvedLocators": [{ "strategy": "ACCESSIBILITY_ID", "value": "zelleMenuItem", "confidence": 0.94, "source": "OBJECT_REPO" }] } },
    { "index": 7, "action": "TAP",  "timeoutMs": 7000, "syncAfter": "WAIT_FOR_IDLE", "healPolicy": "NONE",
      "target": { "naturalReference": "the saved recipient Alex Rivera", "screenContext": "ZelleScreen",
        "resolvedLocators": [
          { "strategy": "ACCESSIBILITY_ID", "value": "recipient_AlexRivera", "confidence": 0.91, "source": "OBJECT_REPO" },
          { "strategy": "XPATH", "value": "//XCUIElementTypeCell[@name='recipient_AlexRivera']", "confidence": 0.86, "source": "PAGE_SOURCE" }
        ] } },
    { "index": 8, "action": "TYPE", "inputData": "${testData.amount}", "timeoutMs": 7000, "syncAfter": "NONE", "healPolicy": "NONE",
      "target": { "naturalReference": "the amount field", "screenContext": "ZelleSendScreen",
        "resolvedLocators": [{ "strategy": "ACCESSIBILITY_ID", "value": "amountField", "confidence": 0.95, "source": "OBJECT_REPO" }] } },
    { "index": 9, "action": "TAP",  "timeoutMs": 7000, "syncAfter": "WAIT_FOR_IDLE", "healPolicy": "NONE",
      "target": { "naturalReference": "the Send button", "screenContext": "ZelleSendScreen",
        "resolvedLocators": [{ "strategy": "ACCESSIBILITY_ID", "value": "zelleSendButton", "confidence": 0.96, "source": "OBJECT_REPO" }] } },
    { "index": 10, "action": "ASSERT", "timeoutMs": 10000, "syncAfter": "NONE", "healPolicy": "NONE",
      "target": { "naturalReference": "the confirmation banner", "screenContext": "ZelleConfirmationScreen",
        "resolvedLocators": [{ "strategy": "ACCESSIBILITY_ID", "value": "zelleConfirmationBanner", "confidence": 0.93, "source": "OBJECT_REPO" }] },
      "assertion": { "kind": "TEXT_EQUALS", "expected": "$25.00 sent to Alex Rivera" } }
  ]
}
```

**Read the flow in the `screenContext` column:** `LoginScreen → HomeScreen → PayTransfersScreen →
ZelleScreen → ZelleSendScreen → ZelleConfirmationScreen`. That is exactly your five-screen path,
expanded to the taps/types the device needs. Notice step 7 carries **two** locator candidates in
committed cascade order — the interpreter tries `ACCESSIBILITY_ID` first, `XPATH` only if the
first *is absent from the tree*; both are committed, so this is **not** self-heal (§6).

### 2.4 Capture Hierarchy + Locator Resolution (deterministic; how `resolvedLocators` got filled)

Before the IR was committed, the hierarchy tool opened an Appium session on a live Perfecto
device, pulled `getPageSource` + Object Spy for each screen, and the **deterministic cascade**
(`OBJECT_REPO > PAGE_SOURCE > OBJECT_SPY > VLM > LLM-guess`) chose each locator. The output is the
committed **`LocatorCandidate.manifest.json`** (shape as in `mocks/o1-spine/`; o7 copy at `mocks/o7-spine/`):

```json
{
  "testId": "ACC-2087", "irVersion": "sha:ir:2087:d41c9a...", "manifestDigest": "sha:loc:2087:7e3a...",
  "candidates": [
    { "strategy": "ACCESSIBILITY_ID", "value": "usernameField",           "confidence": 0.98, "source": "OBJECT_REPO" },
    { "strategy": "ACCESSIBILITY_ID", "value": "passwordField",           "confidence": 0.98, "source": "OBJECT_REPO" },
    { "strategy": "ACCESSIBILITY_ID", "value": "loginButton",             "confidence": 0.97, "source": "OBJECT_REPO" },
    { "strategy": "ACCESSIBILITY_ID", "value": "homeDashboard",           "confidence": 0.95, "source": "OBJECT_REPO" },
    { "strategy": "ACCESSIBILITY_ID", "value": "payTransfersTab",         "confidence": 0.96, "source": "OBJECT_REPO" },
    { "strategy": "ACCESSIBILITY_ID", "value": "zelleMenuItem",           "confidence": 0.94, "source": "OBJECT_REPO" },
    { "strategy": "ACCESSIBILITY_ID", "value": "recipient_AlexRivera",    "confidence": 0.91, "source": "OBJECT_REPO" },
    { "strategy": "ACCESSIBILITY_ID", "value": "amountField",             "confidence": 0.95, "source": "OBJECT_REPO" },
    { "strategy": "ACCESSIBILITY_ID", "value": "zelleSendButton",         "confidence": 0.96, "source": "OBJECT_REPO" },
    { "strategy": "ACCESSIBILITY_ID", "value": "zelleConfirmationBanner", "confidence": 0.93, "source": "OBJECT_REPO" }
  ]
}
```

The **no-orphan-locator rule** (survives from the old static gate, reworded): every locator the IR
references must appear here. It does. This is the *artifact* the IR gate checks against in §4.

---

## 3. The handoff — auto-commit by a service principal (R1 + R4)

**This is the step that used to be a human.** Under R1+R4, when the authoring artifacts are ready:

```
                       ┌─────────────────────────────────────────────────────────┐
   TestCaseIR.json ───►│  IR GATE (deterministic, §4)  +  NO-DEVICE DRY-RUN       │
   manifest.json  ───►│  resolve every locator against the committed captured    │──► all green?
                       │  hierarchy; prove each step is executable                │      │
                       └─────────────────────────────────────────────────────────┘      │
                                                                                         ▼
                          ┌──────────────────────────────────────────────────────────────────┐
                          │  git commit — authored by SERVICE principal                       │
                          │  principal = "svc:conversion-pipeline"  (M37-legal service acct)   │
                          │  hash-chain link computed in the same write txn (ADR 0012)         │
                          │  novelty flag set by R2 sampler: NOVEL=false (matches login+nav    │
                          │    +form-submit family already in the golden corpus)              │
                          └──────────────────────────────────────────────────────────────────┘
```

- **No human here.** The deterministic gate + dry-run is the correctness vouch; the service
  principal signs. This is legal under M37 (a *per-component service principal* is a valid
  attribution for automated actions; only a catch-all `system` principal is forbidden).
- **The novelty sampler (R2)** stamps `NOVEL=false` because this test's *shape* (login →
  navigate → form-submit → assert) already exists in the conformance corpus. A genuinely new
  shape would stamp `NOVEL=true` and flag the eventual verdict for mandatory human scrutiny.
- **Security is not riding on this commit** — ADR 0013 removed all credentials from the
  execution path, so an unreviewed-but-gated IR cannot exfiltrate anything even if malformed.

---

## 4. IR gate (replaces the static gate) — deterministic, pre-device

Seconds, no device. Purpose unchanged from the old static gate: **reject bad artifacts before
spending a device minute.** Only the checks change (no compiler; validate the IR instead):

```json
{
  "testId": "ACC-2087",
  "irDigest": "sha:ir:2087:d41c9a...", "manifestDigest": "sha:loc:2087:7e3a...",
  "interpreterVersion": "sha:interp:9f0c22...", "gateVersion": "sha:gate:1f4c8b...",
  "gatedAt": "2026-08-05T10:08Z",
  "checks": {
    "schemaValid":     { "status": "PASS", "details": "TestCaseIR v2 schema (victools-exported); 11 steps valid" },
    "opcodeClosed":    { "status": "PASS", "details": "11/11 actions ∈ {TAP,TYPE,SWIPE,WAIT,ASSERT,LAUNCH,NAVIGATE}" },
    "boundedWaits":    { "status": "PASS", "details": "11/11 steps carry explicit timeoutMs; 0 unbounded/implicit waits" },
    "locatorManifest": { "status": "PASS", "details": "10/10 IR-referenced locators present in manifest; 0 orphans" },
    "noLiteralCreds":  { "status": "PASS", "details": "inputData uses ${testData.*}/vault: refs only; 0 literal secrets" },
    "ambiguityClear":  { "status": "PASS", "details": "0 unresolved ambiguityFlags (step-3 flag resolved by A2)" }
  },
  "dryRun":  { "status": "PASS", "details": "all 11 steps resolvable against committed captured hierarchy; no device used" },
  "findings": [],
  "decision": "PROCEED_TO_DEVICE_GATE",
  "auditPin": "gateVersion sha:gate:1f4c8b... over irDigest sha:ir:2087:d41c9a... — deterministic; re-runnable at these SHAs."
}
```

**What each check buys you:** `opcodeClosed` kills DSL-sprawl (no vocabulary drift); `boundedWaits`
is the `Thread.sleep`-ban analog (determinism control, not style); `ambiguityClear` is the new
consumer for A1/A2's flags; `dryRun` is R1's correctness substrate. A FAIL here routes back to A2
deterministically — **no Copilot re-prompt loop, no device time spent.**

---

## 5. The interpreter — device gate (replaces TestNG execution)

The interpreter is a **loop over IR steps with a dispatch table**, hosted as an engine in the
`validation-certification` Spring Boot module (H-SB), talking to Appium through a `Driver` seam
(C-MIG: java-client 10.x now, raw-W3C behind the seam if drift bites).

### 5.1 Pseudocode (the whole engine)

```
function replay(ir, manifest, perfectoCaps):
    # ── session setup: determinism lives HERE, set explicitly, once ──
    session = Driver.open(perfectoCaps + {                     # pinned: appiumVersion=2.19, automationVersion=<xcuitest bundle>
        "perfecto:securityToken": vault("perfecto_token"),     #   single-run device token (ADR 0013)
        "appium:settings": { "waitForIdleTimeout": 200, "reduceMotion": true }
    })
    assertCloudAdaptivityDisabled(session)   # A-STD: record selfHealing/perfectoAI = DISABLED
    session.setImplicitWait(0)               # implicit waits OFF; every wait is explicit + bounded

    report = new ReplayReport(irDigest=ir.digest, interpreterVersion=SELF.version)

    for step in ir.steps:                                       # deterministic, ordered, no branching on model output
        t0 = clock()
        element = null
        for locator in step.target.resolvedLocators:           # committed cascade order — NOT self-heal
            element = session.findElement(locator, within=step.timeoutMs)
            if element != null: break
        if element == null:
            report.fail(step, classify(session), evidence(step, session, t0))   # healPolicy:NONE → HARD STOP
            return report                                        # a miss is a red build, never a repair

        switch step.action:
            TAP:    element.click()
            TYPE:   element.sendKeys( resolve(step.inputData) )  # ${testData.*}/vault → value, never logged raw
            SWIPE:  session.w3cActions( step.gesture )           # tick-based → replay-deterministic
            ASSERT: checkAssertion(element, step.assertion)      # TEXT_EQUALS / ELEMENT_PRESENT / VALUE_CHECK
            ...
        if step.syncAfter == "WAIT_FOR_IDLE":
            session.waitForIdle(bounded=step.timeoutMs)

        report.recordStep(step, element.usedLocator, screenshotPrePost(session), elapsed=clock()-t0)  # per-step evidence

    report.finish(verdict = report.allPassed() ? "PASS" : "FAIL")
    session.close()
    return report
```

### 5.2 What the run looks like on the Zelle flow

```
step  action  screen                     locator used                     result   ms
────  ──────  ─────────────────────────  ───────────────────────────────  ──────  ────
 0    TAP     LoginScreen                usernameField (ACCESSIBILITY_ID)  ✓ ok     140
 1    TYPE    LoginScreen                usernameField                     ✓ ok      90   (value from vault, not logged)
 2    TYPE    LoginScreen                passwordField                     ✓ ok      85
 3    TAP     LoginScreen                loginButton                       ✓ ok     210   → WAIT_FOR_IDLE
 4    ASSERT  HomeScreen                 homeDashboard  ELEMENT_PRESENT     ✓ ok     120
 5    TAP     HomeScreen                 payTransfersTab                   ✓ ok     180   → WAIT_FOR_IDLE
 6    TAP     PayTransfersScreen         zelleMenuItem                     ✓ ok     160   → WAIT_FOR_IDLE
 7    TAP     ZelleScreen                recipient_AlexRivera (ACC_ID)      ✓ ok     150   (candidate 1 hit; XPATH not needed)
 8    TYPE    ZelleSendScreen            amountField  "25.00"              ✓ ok      95
 9    TAP     ZelleSendScreen            zelleSendButton                   ✓ ok     220   → WAIT_FOR_IDLE
10    ASSERT  ZelleConfirmationScreen    zelleConfirmationBanner            ✓ ok     130
                                          TEXT_EQUALS "$25.00 sent to Alex Rivera"
────────────────────────────────────────────────────────────────────────────────────
verdict: PASS   ·   11/11 steps   ·   healsApplied: NONE   ·   K=1 run
```

---

## 6. Determinism & the no-self-heal line (why step 7's cascade is safe)

Step 7 lists two locators. If `recipient_AlexRivera` (candidate 1) is **found**, it is used and
candidate 2 is never touched. If candidate 1 is **absent**, the interpreter tries the committed
`XPATH` — and if *that* is also absent, the step **hard-fails**. Critically:
- Both candidates were **committed at authoring time** and are in the manifest. The interpreter
  chooses among *committed* options in *committed* order — it never asks a model, never invents a
  locator, never relaxes a match. That is the difference between a **committed cascade** (o7:
  deterministic, auditable) and **runtime self-heal** (rejected: a model picks a new locator mid-run).
- `healPolicy: NONE` means there is no "try something clever on miss." Miss → classify → red build
  → repair happens back in the **authoring arm** (new IR version, re-gated, re-committed).

Determinism sources handled explicitly at session start: implicit-wait 0, bounded explicit waits
per step, `waitForIdleTimeout`, `reduceMotion`, tick-based W3C Actions for gestures. The
**unpinnable remainder** (Perfecto upgrades drivers on its own schedule; `appiumVersion` is
major.minor only) is *captured as evidence*, not pretended-pinned — see §8.

---

## 7. Verdict + the human (R4 + R2) — where certification happens

### 7.1 The machine ReplayReport (re-based audit pin, A-STD evidence bundle)

```json
{
  "testId": "ACC-2087",
  "irDigest": "sha:ir:2087:d41c9a...",
  "interpreterVersion": "sha:interp:9f0c22...",
  "locatorManifestDigest": "sha:loc:2087:7e3a...",
  "irGate": { "schemaValid":"PASS","opcodeClosed":"PASS","boundedWaits":"PASS",
              "locatorManifest":"PASS","noLiteralCreds":"PASS","ambiguityClear":"PASS","dryRun":"PASS" },
  "deviceGate": {
    "runs": 1, "passes": 1, "flakiness": "NOT_DERIVABLE_AT_K1",
    "pinnedVersions": {
      "interpreter": "sha:interp:9f0c22...",
      "appiumRequested": "2.19", "appiumReported": "2.19.0",           /* evidence, unpinnable remainder */
      "driverReported": "XCUITest 9.4.0",                             /* evidence, unpinnable remainder */
      "device": "iPhone 15 / iOS 17.4", "appVersion": "8.4.0"
    },
    "cloudAdaptivity": { "selfHealing": "DISABLED", "perfectoAI": "DISABLED" }   /* A-STD, post-2025 control */
  },
  "executionPlanRef": "acc-2087.plan.md",       /* E2: rendered plan attached as EVIDENCE, never a pin */
  "healsApplied": "NONE",
  "verdict": "PASS",
  "commitPrincipal": "svc:conversion-pipeline",         /* R1/R4: the COMMIT was service-signed */
  "noveltyFlag": false,                                  /* R2: shape known → sampled, not mandatory-review */
  "certification": { "status": "PENDING_HUMAN", "certifiedBy": null },   /* CF9: machine PASS ≠ certified */
  "auditPin": "irDigest sha:ir:2087:d41c9a... executed by interpreterVersion sha:interp:9f0c22... — reviewable & reproducible; Perfecto server/driver versions captured as recorded evidence (pinned per epoch, not forever)."
}
```

### 7.2 The one human, moved to *after* the run (R4), and sampled (R2)

```
                         ┌──────────────────────────────────────────────────────────────┐
   machine PASS  ───────►│  §7 HUMAN EVALUATOR  (the SINGLE human touch in the flow)     │
   noveltyFlag=false ───►│                                                              │
                         │  R2 routing:                                                 │
                         │    NOVEL=true  → MANDATORY human validation                  │
                         │    NOVEL=false → SAMPLED (this run falls in the audit sample) │
                         │                                                              │
                         │  If validated PASS:                                          │
                         │    certification.status = CERTIFIED                          │
                         │    certification.certifiedBy = "jdoe (individual principal)" │  ← CF9 + M37: the
                         │    → this INDIVIDUAL principal signs the verdict lineage row  │     attribution anchor
                         │    → PASS feeds the flywheel (locators, exemplars, labels)   │
                         │                                                              │
                         │  If FAIL: bounded loop back to A2 with error + original      │
                         │    intent (iteration budget — an existing open Replan item)  │
                         └──────────────────────────────────────────────────────────────┘
```

**The attribution shift, stated plainly:** under the *old* design the **commit row** carried the
individual principal (the engineer who reviewed the Java). Under **R4**, the **commit row** carries
a *service* principal and the **certification/verdict row** carries the *individual* principal
(`jdoe`). No lineage row is ever principal-less (M37 holds), and the **certified path still has a
named human** (CF9 holds). What's deleted is the *pre-commit* human touch — halving the recurring
human cost (two touches → one) without weakening either invariant.

### 7.3 The E2 execution plan (the compliance-officer artifact)

Attached to the report as `acc-2087.plan.md`, deterministically rendered from `irDigest`:

```
# Execution Plan — ACC-2087  (irDigest sha:ir:2087:d41c9a..., interpreter sha:interp:9f0c22...)
 0. TAP    "username field"  → ACCESSIBILITY_ID=usernameField        (budget 7000ms, then WAIT_FOR_IDLE)
 1. TYPE   ${testData.username} → usernameField
 2. TYPE   ${testData.password} → passwordField
 3. TAP    "Sign In button"  → loginButton                            (→ WAIT_FOR_IDLE)
 4. ASSERT home dashboard present → homeDashboard
 5. TAP    "Pay & Transfers"  → payTransfersTab                       (→ WAIT_FOR_IDLE)
 6. TAP    "Zelle"            → zelleMenuItem                          (→ WAIT_FOR_IDLE)
 7. TAP    "recipient Alex Rivera" → recipient_AlexRivera             (fallback XPATH committed, order fixed)
 8. TYPE   ${testData.amount} → amountField
 9. TAP    "Send"            → zelleSendButton                        (→ WAIT_FOR_IDLE)
10. ASSERT confirmation TEXT_EQUALS "$25.00 sent to Alex Rivera" → zelleConfirmationBanner
    healPolicy=NONE for every step — a miss is a red build, never a runtime repair.
```

An auditor/compliance officer reads *this*, not code. It is derived from `irDigest` so it cannot
drift from what ran — but it is **evidence, not the pin** (that avoids the two-competing-pins
problem the earlier review flagged).

---

## 8. The auditor conversation (what this whole thing is for)

> **Auditor:** *"Show me exactly what produced this CERTIFIED verdict for the Zelle transfer, and
> prove it hasn't changed."*

- **The executable:** `irDigest sha:ir:2087:d41c9a...` (the reviewed IR) executed by
  `interpreterVersion sha:interp:9f0c22...` (the interpreter, audited once as infrastructure).
  Both are git SHAs; re-clone and re-run to reproduce.
- **What ran, in English:** `acc-2087.plan.md` (E2), byte-derived from the IR.
- **Who vouched:** commit signed by `svc:conversion-pipeline`; **certification signed by the
  individual principal `jdoe`** (CF9 + M37). The ADR-0012 hash-chain makes the lineage tamper-evident.
- **The cloud we can't pin:** `appiumReported 2.19.0 / XCUITest 9.4.0` captured as **recorded
  evidence** — "pinned per epoch with recorded migrations," never claimed as frozen-forever.
- **No hidden adaptivity:** `cloudAdaptivity: { selfHealing: DISABLED, perfectoAI: DISABLED }`,
  `healsApplied: NONE`. The verdict is a *deterministic replay*, not an agent's best-effort.

*(A-STD ships this bundle now; the follow-on D7 ADR can later wrap it as a Sigstore-signed in-toto
`test-result` attestation for cryptographic tamper-evidence — near-zero schema invention.)*

---

## 9. Where a failure would land (the same flow, one screen drifted)

Suppose release 8.5.0 renamed `zelleSendButton` → `zelleSubmitButton`. Step 9 finds neither the
committed `ACCESSIBILITY_ID` nor any committed fallback:

```
 9    TAP     ZelleSendScreen   zelleSendButton (ACCESSIBILITY_ID)   ✗ NOT FOUND   7000  (timeout)
       └─ healPolicy: NONE → HARD STOP. classify: LOCATOR_NOT_FOUND. red build.
```

- The interpreter does **not** guess a new button — no self-heal (that is the whole point).
- ReplayReport: `verdict: FAIL`, `classificationOnFailure: "LOCATOR_NOT_FOUND"`, per-step evidence
  (pre/post screenshots) attached, `certification: PENDING_HUMAN` never reached.
- **Repair happens in the authoring arm:** re-capture the screen → cascade re-resolves the locator
  → new IR version `sha:ir:2087:e88f...` → re-gated → re-committed (service principal). No Java to
  regenerate, no page-object to hand-edit — the drift→regenerate→re-review cascade of the old
  design is simply gone.
- Because this is a *known test shape*, R2 keeps it on the auto-lane; only the eventual re-run's
  verdict is sampled.

---

## 10. Cross-references

- Design rationale, directions, gate: `docs/research/mobile-test-automation-interpreter-spine-brainstorm.md`
  (§2b = the R4+R2 review decision; §0c = external research; §3 = directions D1–D7).
- o1 (parent) code-gen walkthrough — the pipeline o7 forks: `docs/research/o1-pipeline-walkthrough.md`.
- o7 mock set (changed/new artifacts): `docs/research/mocks/o7-spine/` (v2 IR, manifest, IRGate.report,
  re-based ReplayReport, ExecutionPlan). Shared authoring-arm mocks reused from `docs/research/mocks/o1-spine/`
  (skeleton, NormalizedIntent, page source, object spy, ASH capture, locator-resolution).
- Load-bearing invariants: spec M37 (principal attribution), CF9 (individual certifier), ADR 0012
  (hash-chain), ADR 0013 (credential isolation — retired the security case for pre-commit review),
  ADR 0009 (screening), F6 (pinning set — amended for `irDigest`/`interpreterVersion`).
- **Records into ADR 0016:** executable = committed IR; pin re-base; M37 amendment (attribution
  moves commit-row → verdict-row); §7 evaluator re-scoped to attribution anchor; dry-run/gate
  strength as the correctness control; R5 barred on the certified path.
```
