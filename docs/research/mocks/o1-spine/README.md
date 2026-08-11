# O1 Spine — Mock Artifact Index

End-to-end mock coverage of the **O1 (Spine)** mobile test-automation pipeline:
the decided LLM-free replay spine **and** the proposed ASH-Capture automation
that feeds it. 22 files, spanning ingestion → capture → resolution → codegen →
gates → verdict, plus the four LLM call sites (one decided, three proposed).

Scenario throughout: **ACC-1042** — "Login with valid credentials shows
welcome" (Octane source), on iOS / iPhone 15 / iOS 17.4.

---

## Pipeline flow diagram

```
                         AUTHORING ARM (LLM-bounded)                          SPINE (LLM-free)
  ───────────────────────────────────────────────────────────────  ──────────────────────────────

  Octane / Jira / ALM / Excel
        │
        ▼
  ┌─────────────────┐    ┌─────────────────┐
  │ NormalizedIntent │    │  A0 NORMALIZER   │  LLM  [PROPOSED ADR 0014]
  │   .input.txt      │───►│  (intake)        │
  └─────────────────┘    └────────┬─────────┘
                                   │ NormalizedIntent.json
                                   ▼
                          ┌─────────────────┐
                          │  A1 PARSER       │  deterministic
                          │  (structure)     │
                          └────────┬─────────┘
                                   │ TestCaseIR.skeleton.json
                                   ▼
                          ┌─────────────────┐
                          │  A2 SEMANTIC     │  deterministic-first
                          │  INTERPRETER     │  (LLM fallback)
                          └────────┬─────────┘
                                   │ TestCaseIR.json  ◄── committed handoff to spine
                                   ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  CAPTURE HIERARCHY  (deterministic tool)                     │
  │  LoginScreen.pageSource.xml                                  │
  │  LoginScreen.pruned.json   ──► LLM context                   │
  │  LoginScreen.objectSpy.json                                   │
  └──────────────────────────────────────────────────────────────┘
                                   │
          ┌────────────────────────┴────────────────────────┐
          ▼                                                 ▼
  ┌──────────────────────┐            ┌───────────────────────────────────┐
  │ LOCATOR RESOLUTION    │            │  ASH-CAPTURE (proposed)            │
  │ cascade:             │            │  builds ScreenGraph + manifests     │
  │ OBJECT_REPO >        │            │                                     │
  │ PAGE_SOURCE >        │            │  ┌───────────────────────────────┐ │
  │ OBJECT_SPY >         │            │  │ DISCOVERY LOOP  §11.4 (LLM)   │ │
  │ VLM > LLM-guess      │──┐         │  │  proposes ≤K next actions    │ │
  │                      │  │         │  └──────────────┬────────────────┘ │
  │ ◄── fallback prompt ─┘  │         │               ▼                  │
  │   (when det. sources    │         │  ┌───────────────────────────────┐ │
  │    fall below floor)    │         │  │ DEEP-LINK SUB-LOOP §11.6     │ │
  └──────────┬─────────────┘         │  │  (LLM) proposes routes       │ │
             │                       │  └──────────────┬────────────────┘ │
             │ LocatorCandidate.     │                 ▼                  │
             │ manifest.json         │  ┌───────────────────────────────┐ │
             ▼                      │  │ DRIFT/REPAIR §11.5             │ │
  ┌──────────────────────┐           │  │  reuses discovery prompt       │ │
  │  CODE GENERATION     │  LLM      │  │  (scoped re-discovery)        │ │
  │  (offline, one-shot)  │           │  └───────────────────────────────┘ │
  └────────┬─────────────┘           └───────────────────────────────────────┘
           │ LoginTest.java
           ▼
  ══════════════════════════════════════════════════════════════════ SPINE
  ┌──────────────────────┐    ┌──────────────────────┐
  │  STATIC GATE          │    │  DEVICE GATE         │
  │  (deterministic)      │───►│  (Perfecto, 3 runs)  │
  │  StaticGate.report.json│   │  flakiness check     │
  └──────────────────────┘    └──────────┬───────────┘
                                         │ ReplayReport.json
                                         ▼
                                ┌──────────────────┐
                                │  VERDICT          │
                                │  CERTIFIED / etc. │
                                └──────────────────┘
                                         │
                                ┌────────▼─────────┐
                                │ HUMAN EVALUATOR   │
                                │ PASS → flywheel   │
                                │ FAIL → loop A0    │
                                └──────────────────┘
```

---

## File index (22 files)

### Authoring arm — ingestion (A0 → A1 → A2)

| # | File | Stage | Type | Honesty |
|---|---|---|---|---|
| 1 | `NormalizedIntent.input.txt` | A0 input | raw Octane export | PROPOSED ADR 0014 |
| 2 | `NormalizedIntent.prompt.md` | A0 | LLM prompt exchange | PROPOSED ADR 0014 |
| 3 | `NormalizedIntent.json` | A0 output | cleaned intent | PROPOSED ADR 0014 |
| 4 | `TestCaseIR.skeleton.json` | A1 output | structure-only IR | Decided (deterministic) |
| 5 | `TestCaseIR.json` | A2 output | committed IR | Decided |

### Capture hierarchy (deterministic tool)

| # | File | Stage | Type | Honesty |
|---|---|---|---|---|
| 6 | `LoginScreen.pageSource.xml` | Capture | full Appium dump | Decided |
| 7 | `LoginScreen.pruned.json` | Capture | pruned tree for LLM | Decided |
| 8 | `LoginScreen.objectSpy.json` | Capture | Perfecto smart locators | Decided |

### Locator resolution (cascade + LLM fallback)

| # | File | Stage | Type | Honesty |
|---|---|---|---|---|
| 9 | `LocatorCandidate.manifest.json` | Resolution output | chosen locators | Decided |
| 10 | `LocatorResolution.fallback.input.json` | §4 fallback input | cascade audit trail | Decided spine |
| 11 | `LocatorResolution.fallback.prompt.md` | §4 fallback | LLM prompt exchange | Decided spine |
| 12 | `LocatorResolution.fallback.output.json` | §4 fallback output | proposed locator | Decided spine |

### ASH-Capture (proposed automation)

| # | File | Stage | Type | Honesty |
|---|---|---|---|---|
| 13 | `ASHCapture.discovery.input.json` | §11.4 step 2 input | loop state + pruned tree | PROPOSED ADR 0014 |
| 14 | `ASHCapture.discovery.prompt.md` | §11.4 step 2 | LLM prompt exchange | PROPOSED ADR 0014 |
| 15 | `ASHCapture.discovery.output.json` | §11.4 step 2 output | ≤K proposed actions | PROPOSED ADR 0014 |
| 16 | `ASHCapture.deeplink.input.json` | §11.6 step 2 input | static parse + app docs | PROPOSED ADR 0014 |
| 17 | `ASHCapture.deeplink.prompt.md` | §11.6 step 2 | LLM prompt exchange | PROPOSED ADR 0014 |
| 18 | `ASHCapture.deeplink.output.json` | §11.6 step 2 output | candidate routes | PROPOSED ADR 0014 |
| 19 | `ASHCapture.driftrepair.input.json` | §11.5 input | scoped re-discovery state | PROPOSED ADR 0014 |

### Code generation + gates + verdict (spine)

| # | File | Stage | Type | Honesty |
|---|---|---|---|---|
| 20 | `LoginTest.java` | Code Gen output | committed Appium Java | Decided |
| 21 | `StaticGate.report.json` | Static Gate | deterministic gate verdict | Decided |
| 22 | `ReplayReport.json` | Device Gate | verdict + audit pin | Decided |

---

## How it works — the four LLM call sites

The pipeline has exactly **four** places an LLM is invoked. One is in the
decided spine; three are in the proposed ASH-Capture automation. Each is
documented below with its input, what the LLM does, what it does NOT do, and
which mock files represent it.

### 1. Locator Resolution fallback (base O1 pipeline, §4) — DECIDED

**Where:** `o1-pipeline-walkthrough.md:164-195`. The locator resolution stage
runs a **fixed, auditable cascade** to resolve every `naturalReference` in the
IR (e.g. "the username field") to a concrete locator.

**The cascade (order of preference):**
```
OBJECT_REPO > PAGE_SOURCE > OBJECT_SPY > VLM > LLM-guess
```
The first three sources are **deterministic**. The LLM is invoked only as the
last two fallbacks, when the deterministic sources fail to resolve a reference
with confidence at or above the cascade floor.

**Input to the LLM fallback** (`LocatorResolution.fallback.input.json`):
- The `naturalReference` to resolve (e.g. "the Forgot Password link").
- The `cascadeFloor` (0.85) — minimum confidence to accept a deterministic candidate.
- The **cascade audit trail** — every deterministic source tried, with its
  status (`MISS` / `BELOW_FLOOR`) and reason. This makes the fallback auditable
  rather than a black box.
- The **pruned tree** of the current screen (from `LoginScreen.pruned.json`),
  embedded inline so the LLM call is self-contained.
- A `screenshotRef` for the `VLM` (vision) source.

**What the LLM does:**
- Proposes the single best concrete locator, picking a strategy from the
  allowed set (`ACCESSIBILITY_ID` > `ID` > `CLASS_CHAIN` > `XPATH`), with a
  confidence and one-sentence reasoning.
- In the mock, it resolves "the Forgot Password link" → `forgotPasswordButton`
  (`ACCESSIBILITY_ID`, 0.91), correctly treating the "link" vs "Button" type
  mismatch as UI-labeling looseness rather than a true mismatch.

**What the LLM does NOT do:**
- It does NOT invent elements not in the pruned tree (returns `NO_MATCH`).
- It does NOT execute anything on a device — it only proposes.
- It does NOT modify the IR or the pruned tree.

**Output** (`LocatorResolution.fallback.output.json`): a proposed locator
tagged `source: "LLM-guess"`. If accepted by the human evaluator and
committed, it is appended to `LocatorCandidate.manifest.json`. The static gate
then enforces the no-orphan-locator rule — even LLM-guessed locators must
appear in the manifest.

**Mock files:** `LocatorResolution.fallback.{input.json, prompt.md, output.json}`

---

### 2. ASH-Capture discovery loop (Part II, §11.4 step 2) — PROPOSED

**Where:** `o1-pipeline-walkthrough.md:591-607`. The core LLM call of the
proposed ASH-Capture automation. Invoked **only** when a screen is NOT in the
`ScreenGraph` or its path is `BROKEN` — the happy path (screen in graph,
verified path) uses **no LLM** and replays known steps via graph search.

**The hybrid split (load-bearing):** the LLM **proposes** ≤K candidate next
actions; a **deterministic validator** filters them and executes the survivor.
The LLM never touches the device.

**Input to the LLM proposer** (`ASHCapture.discovery.input.json`):
- The **loop state**: current screen + signature, target screen + signature,
  step budget remaining (≤15), no-progress strikes (≤3), session time (10-min cap).
- The **pruned tree** of the current screen (interactive elements + ancestors).
- A `screenshotRef` (for VLM confirmation).
- The **denylist** (`logout`/`transfer`/`pay`/`confirm`/`sign out`) —
  defense-in-depth; the LLM should not even suggest these.
- `knownEdgesFromCurrentNode` — so the validator can prefer verified edges.
- `cascadeFloor` (0.85) and `maxProposalsK` (3).

**What the LLM does:**
- Proposes ≤K candidate next actions ranked by likelihood of progressing
  toward the target, each with a `kind` (`TAP`/`TYPE`/`SCROLL`), a `locator`,
  a `confidence` (0–1), and one-sentence `reasoning`.
- In the mock (HomeScreen → AccountOverview): rank 1 `accountsTab` (0.90,
  clear label match), rank 2 `hamburgerMenu` (0.62, indirect menu drill-down),
  rank 3 `paymentsTab` (0.48, speculative adjacent tab). Confidence reflects
  uncertainty honestly.

**What the LLM does NOT do:**
- It does NOT propose actions on elements not in the pruned tree.
- It does NOT propose denylisted actions.
- It does NOT execute, navigate, or touch the device — only the deterministic
  validator does (step 4: `DeviceSession.act()`).
- It does NOT invent screen signatures or graph edges.

**What happens after the LLM (steps 3–7, deterministic):**
- The validator filters by locator cascade + confidence floor, denylist,
  known edges, and budget.
- The survivor is executed; the new screen is dumped and signed.
- The edge `(from → to)` is **recorded into the graph as a side effect**.
- If `signature == target` → commit manifest + edges. DONE.
- If no-progress / budget exhausted / timeout → **human escape hatch**.

**Budgets:** ≤15 actions per discovery · ≤60s per step · ≤3 no-progress strikes
· hard 10-min session cap.

**Screening:** every ingress/egress is a call site
(`adr-0009:ash-discovery-proposer-egress`); the loop cannot ship without its
ADR 0014 call-site map.

**Mock files:** `ASHCapture.discovery.{input.json, prompt.md, output.json}`

---

### 3. ASH-Capture deep-link sub-loop (Part II, §11.6 step 2) — PROPOSED

**Where:** `o1-pipeline-walkthrough.md:634-654`. Deep links **supplement** —
never replace — the graph. The app supports an "erica" deep-link scheme but
**not for every screen**. ASH **discovers** existing deep links; it does NOT
invent ones the app doesn't support.

**The three steps:**
1. **Static parse** (deterministic) — APK intent filters (Android) / iOS
   entitlements → scheme + hosts. iOS yields scheme only; routes are in code.
2. **LLM proposes** candidate routes per screen from app docs + screen titles.
   ← *This is the mock.*
3. **Deterministic probe** — launch each candidate, check the landed signature
   against the target, keep only confirmed matches as `DEEP_LINK` edges (cost 1).

**Input to the LLM route proposer** (`ASHCapture.deeplink.input.json`):
- The `staticParse` output (scheme `erica` + known hosts) — the LLM does NOT
  invent the scheme; it only proposes routes *within* the parsed scheme.
- The `appDocsSummary` (release notes + auto-discovered screen titles from the
  graph). The target `AccountOverview` is marked `deepLinkHint: "unknown"` —
  exactly the case the LLM is asked to resolve.
- `knownDeepLinkEdges` — already-confirmed deep links, so the LLM doesn't
  re-propose them.
- `urlDenylist: []` + an **honest gap note** — the probe currently has NO URL
  denylist (Replan R1 D1), so a route like `erica://transfer?...` could execute
  and persist as a preferred cost-1 edge. The LLM's self-restraint is the first
  line of defense until the denylist ships.

**What the LLM does:**
- Proposes ≤K candidate deep-link URLs ranked by likelihood of landing on the
  target, each within the parsed scheme, with a confidence and reasoning.
- In the mock: rank 1 `erica://accounts/overview` (0.85, sub-route of known
  host + title match), rank 2 `erica://accounts/details` (0.62, plausible
  alternative sub-route), rank 3 `erica://accountoverview` (0.40, speculative
  flattened route).

**What the LLM does NOT do:**
- It does NOT invent URL schemes outside the parsed `scheme`.
- It does NOT propose routes already in `knownDeepLinkEdges`.
- It does NOT execute or probe — the deterministic probe (step 3) does that.
- It does NOT propose destructive routes (`transfer`/`pay`/`confirm`/`delete`/`logout`).

**Synthesis (§11.6):** when discovery finds a multi-tap path to a screen *and*
a deep link is probe-confirmed for that same screen, the deep link becomes the
preferred cost-1 edge and the tap path stays as fallback. This mock chains
with the discovery mock — same target `AccountOverview`.

**Mock files:** `ASHCapture.deeplink.{input.json, prompt.md, output.json}`

---

### 4. Drift/repair re-discovery (Part II, §11.5) — PROPOSED, reuses #2

**Where:** `o1-pipeline-walkthrough.md:623-632`. The drift/repair loop is a
**scoped re-run** of the discovery loop prompt (#2) — it does NOT need its own
prompt. The only difference is the `loopState`: the current screen is the last
known-good node (not root), and the target is the broken edge's destination.

**Two triggers:**
- **Post-release** (new `appVersion`): all edges flip to `UNVERIFIED`. Captures
  re-verify lazily — the first capture of each changed screen pays the
  discovery cost; unchanged screens re-verify cheaply (replay + signature
  match, no LLM). Planning assumption: ~20% of screens change per release.
- **Capture failure** (landed signature ≠ expected): the specific edge is
  marked `BROKEN`; re-discovery runs from the last known-good node, repairing
  just that sub-path — not the whole graph.

**Input mock** (`ASHCapture.driftrepair.input.json`):
- `trigger: "CAPTURE_FAILURE"` — the `HomeScreen → AccountOverview` edge
  replayed the stored path but landed on a different signature after the 8.5.0
  release, so the edge was marked `BROKEN`.
- `lastKnownGoodNode`: `HomeScreen` (still `VERIFIED`).
- `scope: "SCOPED_REDISCOVERY"` — re-discovery runs from the last known-good
  node only; the rest of the graph is untouched.
- `promptReuse: "ASHCapture.discovery.prompt.md"` — explicit that this reuses
  the §11.4 step-2 prompt unchanged.
- `knownEdgesFromCurrentNode` — the verified `PaymentsActivity` and
  `ProfileScreen` edges are preserved, so the validator can prefer them.

**Known defect surfaced in the mock** (`knownDefect`):
The **signature re-keying defect** (Replan R1 D1/S1,
`o1-pipeline-walkthrough.md:616-621`): the success predicate
(`signature == target`) compares against the *stored* signature from the
previous appVersion. If `AccountOverview` legitimately changed in 8.5.0 — the
very case this repair exists for — the loop can **never** match and will
deterministically exhaust its budget into the human escape hatch. Until a
signature re-keying mechanism is designed, the <10% escape-hatch target fails
at every release. This is the single biggest threat to automatic drift repair.

**Mock file:** `ASHCapture.driftrepair.input.json` (single file; reuses the
discovery prompt + output shape from #2).

---

## Honesty summary

| Call site | Status | Screening call-site | Key open defect |
|---|---|---|---|
| 1. Locator Resolution fallback | DECIDED spine | `adr-0009:locator-fallback-egress` | none |
| 2. Discovery loop proposer | PROPOSED ADR 0014 | `adr-0009:ash-discovery-proposer-egress` | signature re-keying (R1 D1/S1) |
| 3. Deep-link route proposer | PROPOSED ADR 0014 | `adr-0009:ash-deeplink-proposer-egress` | URL denylist gap (R1 D1) |
| 4. Drift/repair re-discovery | PROPOSED ADR 0014 | reuses #2 | signature re-keying (R1 D1/S1) |

All three ASH-Capture call sites carry `PROPOSED ADR 0014` and cannot ship
without their ADR 0014 screening call-site map. The decided spine (call site
#1) ships under existing ADRs.

