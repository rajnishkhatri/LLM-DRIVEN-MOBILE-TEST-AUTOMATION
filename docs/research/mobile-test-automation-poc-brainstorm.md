# SDD Stage 1 — Brainstorm: A Runnable POC for the Mobile Test-Automation Generation Loop

**Stage:** SDD Stage 1 (brainstorm / ideation) · kata-mode against this workspace
**Target:** `mobile-test-automation` · a demo-able POC / MVP of the generation→replay loop
**Binding:** `.sdd/binding.toml` — constitution `.cursor/rules/architecture-principles.mdc`; ADR home `docs/architecture/adrs/application/mobile-test-automation/`; spec/plan home `docs/sdd/`; `methodology_source = <none>` (skill body governs); `breadth_read_tool = explore subagent`
**Status:** DRAFT (promoted to docs 2026-07-29) — intent v2 CONFIRMED; research COMPLETE (§7); six-way ARB/auditor comparison COMPLETE with maintainability elevated to 22% per user (§8, v2 weights + §8.6 maintenance-economics model). Field compresses to a top cluster (O6 ≈75, O3 ≈74, O1/O5 ≈73). **POC = O3 hybrid; production posture sharpened to O1 spine + O6 "regenerate-and-filter, never hand-maintain."** **§7.5 (procedural+semantic memory architecture for self-healing) COMPLETE** — CoALA split; skill = pure `TestCaseIR` Steps behind a `callSkill`/`SKILL` opcode; write-back gated by the deterministic critic (never the LLM), individual-principal promotion (CF9), per-skill cross-conversation lineage; red-team surfaced 3 critical structural gaps (cross-conversation chain unowned by ADR 0012, write-back = unscreened 4th ADR 0009 egress, `CONFIRMED`≠certified vs spine K=1) — folded in as required controls §7.5.6 and risk rows R7/R8. Remaining gate: confirm v2 weights + the sharpened production posture + the §7.5 memory design, then advance to `sdd-spec` (with the ADR-triage items in §7.5.6 as hard constraints).
**Home:** `docs/research/mobile-test-automation-poc-brainstorm.md` (this file — promoted from the Stage-1 working plan draft at `~/.claude/plans/cursor-skills-sdd-brainstorm-we-already-peppy-lantern.md`).

> This is the Stage-1 brainstorm artifact per `sdd-brainstorm`: restate intent → **premise audit against repo evidence** → ~6 directions → hypothesis validation for the lead → dependency structure → human gate. No spec is written here; the gate only picks *what to specify next*.

---

## Context — why this brainstorm exists

The user has an **APPROVED** plan for the weeks-0–3 **shared spine** (`docs/sdd/plans/mobile-test-automation-spine.plan.md`, PLAN-OK 2026-07-28). The spine is deliberately **LLM-free** — F1 makes any model call a CI failure (`docs/sdd/specs/mobile-test-automation-spine.spec.md:49`). The user now wants to prototype the *actual value proposition*: the LLM-driven loop that turns a **test worksheet + device view-tree** into an executable Appium test. Whiteboard sketch:

1. Start with a few test worksheets; run apps locally (iOS + Android); extract the **view tree**.
2. Feed test script + view tree to a **ReAct Agent** → emits **JSON** → consumed by an **Appium framework**.
3. **Happy path (Replay):** Appium framework understands the LLM's JSON and executes on iOS/Android.
4. **Error path:** on failure, `error + original worksheet + view hierarchy` → **Reflexion Agent** → improved artifacts back into the ReAct loop; success → Replay; repeated error → loop again.

The user asked to **(a) restate intent and confirm**, then **(b) critically evaluate** the approach against the plan/architecture and name needed modifications.

---

## 1. Restated intent — CONFIRMED v2 (2026-07-29)

> Intent v1 was corrected by the user at the first gate. **v2 is confirmed.** The correction matters: the user does **not** want committed Appium scripts — they want a **runtime-interpreting Appium framework** that reads the LLM's JSON and executes it live. The stated objective is proving **adaptability and reliability**, and an interpreter demonstrates adaptability more directly than frozen scripts. This deliberately inverts premise P2 for the POC (see §2).

**Confirmed intent (v2):** the fastest end-to-end vertical slice that proves the system's *adaptability and reliability*, via a **runtime-interpreting Appium framework**:

- **Align, don't replace.** Map the canonical pipeline `ingest → interpret → resolve → generate → verify → replay → certify` onto the user's `generate → execute → reflect-and-repair`. The **ReAct loop** drives `interpret → resolve → generate`; the **Reflexion loop** sits at `verify/replay → (reflect) → generate`, bounded.
- **LLM emits JSON; a custom framework interprets it at runtime.** Deliverable is an **interpreter framework**, not test scripts: it reads the LLM's JSON (a **subset/extension of `TestCaseIR`** — user pick), resolves it against the live view-tree, and **executes actions dynamically at runtime**. This is what demonstrates adaptability.
- **Real devices, locally.** iOS via xctools, Android via Android Studio tooling — real hardware, run locally, **architected to scale to Perfecto cloud later**.
- **Reflect-and-repair.** Runtime error + worksheet + view-tree → Reflexion pass → improved JSON → re-execute, bounded.
- **Reasoner:** **Copilot**, behind a config-swappable model seam.
- **Nature:** **throwaway spike** — fastest path; light-spec; adaptability + reliability are the success criteria, not production-hardening.
- **JSON shape:** **reuse/extend `TestCaseIR`** (one vocabulary; eases later alignment even for a spike).

**One line:** *Prove adaptability and reliability end-to-end with a runtime-interpreting Appium framework — the LLM emits `TestCaseIR`-shaped JSON, the framework interprets and executes it live on real local iOS/Android devices, and a bounded ReAct↔Reflexion loop repairs failures — mapped onto the canonical ingest→…→certify pipeline, as a throwaway spike using Copilot, built to scale to Perfecto later.*

**Two honesty flags carried into the design (agreed):**
1. The runtime-interpreter approach **trades determinism/auditability** (the spine's top characteristics) for adaptability. Fine for a throwaway adaptability spike — but the POC's design intentionally diverges from the production replay pipeline, and "the interpreter worked in the POC" must never be read as "the production certification path works."
2. **Reliability comes from the bounded repair loop + deterministic per-step verification**, not from the LLM judging itself. The *verify* step stays rule-based even inside the interpreter.

## 1a. User research ask (in progress)

At the second gate the user asked for, as part of this brainstorm: **(i)** a detailed **interpreter-vs-scripts** analysis, and **(ii)** external research on how **Perfecto, Maestro, and others** build agentic pipelines, plus **2026 best practices**. Three research agents launched 2026-07-29 (two web: vendor pipelines / OSS + practices; one internal: repo-grounded interpreter-vs-scripts). §7 (new) holds the analysis; findings feed §2–§5.

---

## 2. Premise audit — the POC idea vs. the existing architecture

Per the skill, the problem statement is itself a hypothesis. Each load-bearing premise checked against repo evidence:

| # | Premise in the sketch | Status | Evidence |
|---|---|---|---|
| P1 | "A ReAct Agent + Reflexion Agent loop is the generation design." | **REFUTED as terminology / VERIFIED as substance** | The terms *ReAct*/*Reflexion* appear **nowhere** in the repo. But the **exact loop already exists unlabeled**: v1 blueprint frames it as "a **reasoning loop**" with a tool-using Element Resolver + a Self-Healing repair agent (`docs/research/architecture-diagrams.md:7`), and names "the two **evaluator-optimizer loops**" — `static-validate↔generate` and `replay↔self-heal`, each bounded (3 static repairs, 3 device retries) (`architecture-diagrams.md:122`). Your ReAct≈Element-Resolver+Code-Generator; your Reflexion≈the bounded self-heal loop. **So the intent is fully grounded; only the vocabulary and the 2-box collapse are new.** |
| P2 | "The LLM emits JSON that the Appium framework executes." | **INTENTIONAL DIVERGENCE (user-confirmed at gate 1)** | The production architecture emits **committed code**; the replay pipeline **"only consumes committed code… LLM output never touches it"** (`blueprint-revision-v2.md:73`; `mobile-test-automation-brainstorm.md:353`). The user **deliberately chose the opposite** for the POC: an LLM→JSON→**runtime interpreter** model, precisely to demonstrate *adaptability*. This is a legitimate throwaway-spike choice that trades determinism/auditability for adaptability. **It does NOT modify the production design** — the POC is a separate spike. The interpreter-vs-scripts tradeoff is the subject of §7 (dedicated analysis + external research). |
| P3 | "Run apps locally on iOS/Android and extract the view tree." | **REFUTED for certification / OK for a POC tier, with a caveat** | The architecture mandates a **Perfecto real-device certification tier** and warns **"never certify on emulator/simulator alone"** — iOS sim-vs-device element trees demonstrably diverge (`docs/research/agent-appium-test-pipeline.md:47-59, :184`). Local sim/emulator is *fine as a cheap POC/dry-run tier*, but a locator that grounds against a **simulator** tree may not survive on a real device. The view-tree source is architecturally the **Acquire UI Evidence** component / hierarchy-tool emitting `getPageSource` + a **pruned tree** (interactive elements + ancestors) to fit context (`blueprint-revision-v2.md:26,115`; `logical-components.md:111`). |
| P4 | "The Reflexion Agent resolves errors / decides success." | **REFUTED (subtle but load-bearing)** | Failure **classification is rule-based, not LLM**: "The pipeline decides only what happened; the LLM (or human) decides how to fix" (`blueprint-revision-v2.md:103`). The repo repeatedly rejects LLM self-judgment as the gate: "LLM-as-judge is a pre-filter, not the certification authority" (`agent-appium-test-pipeline.md:127`); "the same model that made the error has the same blind spots when reviewing it" (`diagramskill.md:12`). **Correct mapping: the deterministic replay/static gate is the "environment/critic"; the Reflexion LLM only *repairs*, it never *judges pass/fail*.** |
| P5 | "This is a POC, separate from the spine." | **VERIFIED — and it must be** | The spine is LLM-free by construction (F1 CI-fails any model call — `spec.md:49,68`). Any LLM in the loop places this POC in **Phase 1 / weeks 3–8+ territory**, not the spine. The phase model is three-tier: spine (0–3, no LLM) → Phase 1 Copilot-assisted (3–8) → Phase 2 gateway (14–22) (`architecture-diagrams` + `blueprint-revision-v2.md:121-127`). |
| P6 | "Two agents is the right granularity." | **REFUTED as a trend** | The derived design has been **consolidating** agents, not adding them: the 8-agent sketch's separate *Fix Proposer* was **withdrawn** because Repair Locators reuses Resolve Elements, and the *Style Agent* was **folded into** Generate Test Code (`logical-components.md:171,302`). A fresh 2-agent (or N-agent) topology should reconcile with this. For a POC, *fewer* moving parts is aligned; just don't enshrine "agents" as the architecture. |
| P7 | "Appium is the executor." | **VERIFIED** | Appium 2 is the target framework across all artifacts (`blueprint-revision-v2.md:5,37`; `architecture-diagrams.md:13`). |
| P8 | "Worksheet is the input unit." | **VERIFIED with a term-clash note** | In this repo "worksheet" usually means an *SDD Stage-1 artifact* (`characteristics-worksheet.md`). Your "worksheet" = the manual-test bundle, whose documented equivalent is **IR JSON + pruned view hierarchy + instructions + exemplars** (`blueprint-revision-v2.md:49`). Use **"test worksheet"** to disambiguate. |

**Audit verdict:** the POC's *intent* is squarely on-vision — it's the generation loop the whole program is built to enable. Four premises need correction before a spec: **(P2)** LLM emits *code behind a static gate*, not execution-JSON; **(P4)** the reflector *repairs*, the deterministic gate *judges*; **(P3)** local-device is a POC tier, not certification; and the **no-LLM-in-spine** line (P5) means this is a *separate* POC track, reusing the spine's `TestCaseIR`/`ReplayReport` contracts rather than modifying the spine.

---

## 3. Candidate directions (~6)

Three high-probability (follow existing repo patterns) + three exploratory. Each: what it is, the invariant it stresses, what breaks if chosen.

### High-probability (repo-pattern-following)

**D1 — "Vertical-slice Phase-1 loop, contracts-honest, Copilot-as-reasoner."**
Build the POC as a literal thin instance of the documented Phase-1 loop: ingest one worksheet → fill `TestCaseIR` → capture pruned view-tree → LLM generates **committed Appium code** → static gate → device replay (local sim first) → rule-classified `ReplayReport` → on fail, LLM *repair* pass (bounded) → re-replay. Reuses `TestCaseIR`/`LocatorCandidate`/`ReplayReport` verbatim (`blueprint-revision-v2.md:21`). *Follows:* the v1 topology (`architecture-diagrams.md:100-124`) and the spine contracts. *Stresses:* nothing new — it's the intended shape. *Breaks if chosen:* least; the risk is scope-creep toward the full pipeline. **This is the recommended lead.**

**D2 — "IR-first, deterministic-critic loop (rename the agents to their roles)."**
Same as D1 but explicitly frames the two "agents" as the documented roles — **Generator** (ReAct-style, tool-using over the view-tree) and **Repairer** (Reflexion-style, consumes the *rule-classified* `ReplayReport`) — with the **replay/static gate as the non-LLM critic** in between. *Follows:* ADR 0001 (reasoning behind a seam), ADR 0003 (bounded orchestration), the evaluator-optimizer framing. *Stresses:* keeps the LLM out of the pass/fail decision (P4). *Breaks if chosen:* nothing structural; it's D1 with the correct critic placement made central.

**D3 — "Behind the Invoke Models seam from commit one."**
Whatever D1/D2 do, route every model call through a single `InvokeModels` interface (config-selected impl), so the POC's Copilot/gateway/local-LLM choice is a config swap and the only vocabulary crossing the seam is the IR spine. *Follows:* ADR 0001 + F1/F2 exactly (`0001-…md:62-85`). *Stresses:* evolvability/replaceability (the displaced-but-driving characteristic). *Breaks if chosen:* trivially more upfront interface work; buys the Phase-1→Phase-2 swap for free and keeps the POC honest to the architecture. **Do-regardless hygiene — cheap, high-leverage.**

### Exploratory (different abstraction / integration / shift)

**D4 — "Demand-side first: deterministic locator resolution before the LLM."**
The skill's demand-side lens: make the expensive LLM call *not happen* when it needn't. Resolve locators deterministically first — object-repo lookup + accessibility-id match against the view-tree — and only invoke the LLM for the genuinely ambiguous residue. *Follows:* the locator cascade (`architecture-diagrams.md:153-166`), accessibility-id-first (`agent-appium-test-pipeline.md:55,183`). *Stresses:* cost/reproducibility. *Breaks if chosen:* more plumbing per screen; but it's the honest cost-control the research demands and it shrinks the LLM's error surface. Strong complement to D1, not a standalone POC.

**D5 — "Local-emulator POC tier as an explicit, labeled cheaper rung — with a real-device honesty gate."**
Embrace your "run locally" instinct but make it a *named tier* (`LOCAL_SIM` dry-run) distinct from the Perfecto certification tier, with a recorded caveat that a local pass ≠ a certified pass, and a single real-device confirmation at the end of the POC. *Follows:* cost-tiered validation (`mobile-test-automation-brainstorm.md:464-472`). *Stresses:* reproducibility (sim/device drift, P3). *Breaks if chosen:* if the POC's "success" is declared on sim alone, it over-claims — the drift evidence (`agent-appium-test-pipeline.md:47-59`) says the interesting failures appear on real devices. Needs the honesty gate or it misleads.

**D6 — "MCP-driven live-device ReAct as the exploratory arm."**
Your "ReAct Agent" taken literally: an Appium **MCP server** exposes the live UI tree as tools; the agent reasons→acts→observes on the device directly (`architecture-diagrams.md:128`). *Follows:* the tool-use pattern, loosely. *Stresses:* determinism (top-1 characteristic) and ADR 0013 (an agent driving a live device near credentials). *Breaks if chosen:* live agentic driving is non-deterministic, costs an LLM call per action, and collides with the "LLM output never touches replay" + credential-isolation lines. **Interesting for a research spike, wrong for the auditable POC** — name it, defer it.

---

## 4. Leading direction (D1+D2+D3+D4 composed) — hypotheses & validation

The lead is a **composite**: D1's vertical slice, framed by D2's deterministic-critic loop, behind D3's model seam, with D4's deterministic-first resolution. Hypotheses, each validated against `file:line`:

- **H1 — "The POC needs no new schemas; `TestCaseIR`/`LocatorCandidate`/`ReplayReport` carry it."** *Validated:* the schemas are "the spine; every module is swappable as long as the schemas hold" (`blueprint-revision-v2.md:21`); full record defs exist (`mobile-test-automation-brainstorm.md:199-241`, `blueprint-revision-v2.md:81-101`). ✅
- **H2 — "The generate→gate→repair loop is the documented design, so the POC de-risks the real thing."** *Validated:* the two bounded evaluator-optimizer loops are explicit (`architecture-diagrams.md:122`), re-hosted onto Spring services in v2 (`blueprint-revision-v2.md:11`). ✅
- **H3 — "Keeping the LLM out of pass/fail is required, not optional."** *Validated:* rule-based classification (`blueprint-revision-v2.md:103`), judge-as-pre-filter-only (`agent-appium-test-pipeline.md:127`), self-critique-is-weak (`diagramskill.md:12`). ✅
- **H4 — "A local-sim POC tier is safe *only if* labeled and not treated as certification."** *Validated as a constraint:* sim/device element-tree drift is documented on Apple's own forums; environment is the #2–3 UI-flaky cause (`agent-appium-test-pipeline.md:47-59`). ✅ (This is why D5's honesty gate matters.)
- **H5 — "Reuse beats new agents; don't hard-code a 2-agent topology into anything durable."** *Validated:* Fix Proposer withdrawn, Style Agent folded in (`logical-components.md:171,302`). ✅
- **H6 — "Perfecto access is the external gate that could block the *real-device* confirmation."** *`needs-probe`:* Perfecto/Octane credentials are on the spine's critical path (`spec.md:396`); a POC that wants a real-device pass inherits that dependency. Local-sim work does **not** need it — so the POC can start immediately and defer the real-device confirmation. ⏳

**Rejected sub-hypothesis (context-blindness guard):** "the LLM emits JSON Appium runs directly" (P2) — no repo evidence supports execution from raw LLM output; all evidence says committed **code** behind a static gate. Dropped.

---

## 5. Dependency structure & the real decision

- **Do-regardless (zero-risk, no external dep):** the model seam (D3), reusing the spine IR contracts (H1), the deterministic-critic framing (D2/H3). Start here on day one; needs no Perfecto/Octane/LLM-gateway approval.
- **Sequenced:** deterministic-first resolution (D4) → LLM generation → static gate → **local-sim** replay → rule-classify → bounded repair. Each stage feeds the next; the repair loop closes on the classified report, not on the LLM's opinion.
- **`needs-probe` / calendar-gated:** the **real-device confirmation** (Perfecto access, H6) and any **Octane** ingestion. The POC can be fully built and demoed on local sim + a couple of hand-made worksheets while this is pending.
- **The real decision the human owns** (three conflated axes, split for the gate):
  1. **What the POC proves** — the *loop mechanics* (generate→gate→repair) vs. *real-device fidelity* (does a generated test pass on actual iOS/Android hardware). These need different tiers and different external dependencies.
  2. **Where it lives** — a *throwaway spike* (light-spec carve-out, runbook §6) vs. a *seed of the weeks-3–8 Phase-1 build* (contracts-honest, behind the seam, promotable). This changes how much D3/H1 rigor is worth.
  3. **Reasoner choice** — local/open LLM for a frictionless demo vs. **Copilot** (the sanctioned Phase-1 reasoner, no new model-risk approval — `blueprint-revision-v2.md:17`) vs. the **Orchestrator AI gateway**. Behind the D3 seam this is a config swap, but it sets the demo's setup cost and how directly the POC becomes Phase-1.

---

## 6. Human gate — orthogonal tracks to pose

Direction-level acceptance only (the human picks *what to specify next*, not the spec). Posed as independent tracks:

- **Confirm the restated intent (§1).**
- **Pick what the POC must prove (§5 decision 1):** loop-mechanics-on-sim (fast, no external deps) vs. real-device-fidelity (needs Perfecto) vs. both in sequence.
- **Pick the artifact's fate (§5 decision 2):** throwaway spike vs. promotable Phase-1 seed.
- **Pick the reasoner (§5 decision 3):** local LLM vs. Copilot vs. gateway (all behind the D3 seam).

**Advance →** `sdd-spec` with the chosen direction + the four corrected premises (P2 code-not-JSON, P4 deterministic-critic, P3 sim-is-a-tier, P5 separate-from-spine) as hard constraints. If the human wants the throwaway spike, the runbook §6 light-spec carve-out applies.

> **⚠️ Ask-first flag for spec time:** an LLM in the loop is a new capability relative to the spine and will need its ADR posture stated — it sits behind ADR 0001's Invoke Models seam, must respect ADR 0013's execution isolation (generated code runs in a separate process, no gateway credential), and must not weaken F1 in the spine repo. If the POC lives in the spine repo, F1 will (correctly) fail it — so the POC belongs in a **separate module/repo** or explicitly in the weeks-3–8 Phase-1 codebase, never inside the LLM-free spine.

---

## 7. Interpreter vs. Scripts — analysis + external research (2026)

> Populated from three research agents launched 2026-07-29 (Perfecto/vendor agentic pipelines; Maestro/OSS + 2026 best practices; internal repo-grounded interpreter-vs-scripts synthesis). This section decides, with evidence, whether the POC's **runtime-interpreter** choice is sound and how leading tools in 2026 actually structure agentic test pipelines.

### 7.1 The two approaches, precisely

- **Approach A — Runtime Interpreter ("test-as-data").** LLM emits `TestCaseIR`-shaped JSON → a framework interprets it live, resolving locators against the current view-tree and executing Appium actions dynamically. Adaptable and self-healing at runtime; weaker on determinism/auditability.
- **Approach B — Code Generation ("test-as-code").** LLM emits committed Appium/TestNG code → deterministic static gate → committed code runs; LLM output never touches execution. Strong on determinism/auditability; adaptation requires regeneration.

### 7.2 External evidence — how Perfecto / Maestro / others do it (2026)

**The market has bifurcated, and the emerging consensus is a hybrid: interpret at runtime, materialize to code on demand.**

| Tool (2026) | Model | LLM output representation | Self-healing | Real-device / grounding |
|---|---|---|---|---|
| **Perfecto AI** (Perforce, launched Jul 2025) | **Runtime interpreter** — plain-language intent interpreted live against the UI; "ends the era of test scripts" | Interpreted intent, not a committed script | Runtime re-adaptation (semantic + visual validation) | Real devices; **rel. 26.2 (Mar 2026) added export-to-Appium-JavaScript** — the codegen escape hatch |
| **Maestro** (mobile.dev) | **Interpreter of a committed DSL** — YAML *is* the test, parsed + executed live; deterministic built-in waiting | LLM (MCP `RunFlowTool`, MaestroGPT) **authors YAML**; interpreter runs it | **Authoring-time** repair only (not runtime self-heal) | iOS **simulator-only** natively (real iOS needs community tooling); a11y tree surfaced as compact CSV |
| **Appium MCP server** (official, ~May 2025) | **Runtime interpreter** — agent perceive→act over MCP tools (`get_page_source`, `find_element`, `gesture`) | Structured tool calls (JSON); opt-in `generate_tests` codegen | "Recover via alternative elements from learned context" | Real + emulator; locator ladder (a11y-id > id > predicate > xpath) + opt-in vision |
| **callstack `agent-device`** (2026 OSS) | **Runtime interpreter** — inspect→act→verify | Structured commands over MCP; token-efficient a11y snapshots (`@e2` refs) | Runtime | **Real local iOS (XCTest) + Android (adb)** — closest to "agentic Maestro on real devices" |
| **Drizz / mabl** | Runtime interpreter (vision-first / multi-model) | NL intent → vision/attribute match at runtime | Intrinsic ("nothing to heal, we re-read the screen") | Real devices |
| **testRigor / Testim** | **Hybrid** — plain-English re-interpreted at runtime, grounded on stored/attribute locators | Constrained NL / multi-attribute locators | Ranked-attribute self-heal | Hybrid grounding |
| **QA Wolf** | **Code-generation** (the deterministic camp) | Committed Playwright/Appium code, reviewed + versioned in CI | n/a (regenerate) | Explicitly markets "deterministic & auditable" |

**Load-bearing external findings for our decision:**
- **The vendor consensus is "runtime-interpret by default, materialize to code on demand."** Perfecto's 26.2 Appium-JS export is the clearest proof: the live artifact is interpreted intent, but they bolted on a compiled-code exit for CI/CD + auditability. *This validates the hybrid our production north-star already implies* (interpret for adaptability, commit code for audit).
- **Maestro is the canonical "LLM authors a DSL, a fixed runtime interprets it" model** — and its trick is that the committed YAML is *both* adaptive-at-authoring and *deterministic-at-execution*. This threads the needle: agentic where you want flexibility, deterministic where you want reproducibility. Confirmed by codebase docs + an independent walkthrough, not just marketing.
- **Reliability reality-check (independent, not vendor):** autonomous interpreter agents driving live UIs score **~25–50% F1** — WebTestBench best = 26.4% ([arXiv 2603.25226]); GTArena GPT-4o 41.6% exact-match ([arXiv 2412.18426]); GUITester baseline 33% → **48.9% with a ReAct+Reflection loop** ([arXiv 2601.04500]). Every vendor "90% maintenance reduction" number is **unverified marketing**. → *A POC should keep the interpreter's scope tight and lean on a deterministic critic; do not expect autonomous reliability out of the box.*
- **Output-format nuance (matters for the LLM prompt design):** don't force JSON throughout — the "format tax" ([arXiv 2408.02442]) shows structure-during-reasoning *degrades* reasoning. Best practice: **reason free-form, emit the constrained `TestCaseIR` action-plan as the final step**. A small closed DSL interpreted by a fixed runtime is easier to make valid and to validate than free code — the interpreter is the guardrail.
- **Grounding (2026 SOTA):** hybrid **accessibility-tree/view-hierarchy first, vision fallback** (Set-of-Marks / ref-addressing), with a July-2026 caveat that agents **over-trust the structural channel** — corroborate the view-tree against a screenshot before acting ([arXiv 2607.04334]).
- **Reliability comes from a deterministic critic + bounded repair, not LLM-as-judge.** VeriHarness: only external gates accept a candidate, never the worker's self-assessment; **structured failure feedback with admissible alternatives roughly doubled repair success** (28%→72%) within a 4-call budget ([arXiv 2607.14167]). This is exactly the "reflector repairs, gate judges" shape (P4).
- **Real-device loops:** Android via **adb** is straightforward; iOS via **XCTest/Xcode** is the harder path (why Maestro is sim-only). `callstack/agent-device` drives **real local iOS + Android** through an MCP loop — a concrete reference architecture for your "run locally on real devices, scale to Perfecto later" requirement.

### 7.3 Internal evidence — what the repo's stance implies

**The repo is 100% Approach B (test-as-code).** The line *"the replay pipeline… only consumes committed code; LLM output never touches it"* appears verbatim three times (`blueprint-revision-v2.md:73`, `mobile-test-automation-brainstorm.md:353`, `characteristics-worksheet.md:38`) and is named the system's *most important internal boundary* — "every other decision inherits that line" (`characteristics-worksheet.md:272-273`). There is **no runtime-interpreter design anywhere**, and the one time an LLM-bearing replay concept appeared it was **withdrawn on sight** (`logical-components.md:26-29`). Perfecto's scriptless self-adapting engine (an interpreter-class product) was explicitly **declined as the target** — kept only as an embedded assertion fallback — because "the client wants portable, auditable, version-controlled test assets" (`architecture-diagrams.md:22`).

**But `TestCaseIR` is already ~80% a directly-interpretable action IR** — which is why your "reuse/extend TestCaseIR" pick is sound:
- `Step.action` is literally a runtime opcode set: `TAP, TYPE, SWIPE, WAIT, ASSERT, LAUNCH, NAVIGATE` (`mobile-test-automation-brainstorm.md:214`).
- `Assertion.kind` is an assertion opcode (`TEXT_EQUALS, ELEMENT_PRESENT, VALUE_CHECK, VISUAL, AI_VALIDATION`) and `aiValidationPrompt` already carries the `perfecto:ai:validation` payload (`:236-240`).
- `TargetElement.resolvedLocators` is an iterable `Locator{strategy,value,confidence,source}` cascade the interpreter can walk against the live view-tree (`:225-234`).
- `Step.index`/`controlFlow`/`inputData` map onto an interpreter loop one-to-one.

**Three additions the interpreter needs** (the schema lacks them because it's an *authoring* contract, not an *execution* one — `architecture-diagrams.md:83`): **(1)** per-step timeout/sync fields (determinism relies on "explicit waits only, fixed timeouts in config" — `blueprint-revision-v2.md:105`); **(2)** a runtime-resolution/heal policy (retry budget per step, heal-on-miss, fallback-to-VLM trigger); **(3)** a substitute for `codeCommit` pinning, since there is no committed code (F6 requires `codeCommit` and "null/absent is never valid" — `spec.md:88-96`).

**Constraints the interpreter STRESSES (must be respected even in a spike):**
- **ADR 0013 binds it *harder*, not softer.** Executing LLM-shaped JSON live is the *same* prompt-injection→execution attack path with a shorter fuse (no committed-code review, no Java static gate). The POC must still honor: **no gateway credential in the execution path, single-run device token, separate process** (`0013-…md:31-36, 97-103`). "Interpreting JSON" does **not** escape the security topology.
- **F1 (model seam):** if the interpreter calls the model *live* to resolve/heal mid-execution, that puts model access inside the execution path — stress on F1 and ADR 0013's "the gateway credential has no business in the execution context." Keep live model calls at the *reflect* boundary, not inside per-step execution.
- **Determinism / F6 / static-gate / locator-manifest:** all code-shaped; the interpreter bypasses the free static-rejection tier and has no `codeCommit`. **This is exactly why the POC stays a throwaway that never touches the production audit/reproducibility contracts.**

**Net:** Approach A reaches an adaptability demo **faster and with less code** (no Freemarker/`mvn compile`/Checkstyle/TestNG harness), reusing `TestCaseIR` as a ready-made action IR — but it is the model the repo **rejected twice** for production. Its only defensible role is precisely the one chosen: **a deliberately throwaway adaptability spike, kept away from the reproducibility/audit contracts it cannot satisfy.**

### 7.4 Verdict for THIS POC (adaptability + reliability, throwaway, scale-to-Perfecto)

**Recommendation: build the interpreter (Approach A) — it's the right choice for a throwaway adaptability spike — but adopt the Maestro/Perfecto hybrid shape so it stays honest and demonstrates reliability, not just adaptability.** Concretely, five design commitments:

1. **Interpreter core over `TestCaseIR` — the LLM emits data, a fixed runtime executes it.** `TestCaseIR` is already ~80% an action IR (`Step.action` opcodes, `Assertion.kind`, the `Locator` cascade). Extend it minimally with the three missing runtime fields (per-step timeout/sync, resolution/heal policy, a `codeCommit` substitute like `irDigest`). This reuses the production vocabulary, so the spike informs the real system even though it's throwaway. *(Internal §7.3; validates your "reuse/extend TestCaseIR" pick.)*

2. **Reason free-form, emit constrained `TestCaseIR` as the final step.** Avoid the "format tax" — don't force JSON during reasoning. This is the ReAct "Thought → Action" shape: the LLM thinks in prose, then emits the structured step. *(External: arXiv 2408.02442, CRANE.)*

3. **Deterministic critic, LLM reflector — reliability lives here.** The interpreter's own per-step pass/fail (element resolved? assertion held?) is the ground-truth oracle. The **Reflexion** pass consumes that *rule-classified* result (reuse the 7-class taxonomy) plus **admissible alternatives** (the other locator candidates, nearby view-tree elements) and *repairs the JSON* — it never judges pass/fail. Bound the loop (start at 3 retries, the documented budget). *(External VeriHarness: structured feedback with alternatives ~doubled repair success; internal P4/H3.)*

4. **Hybrid grounding: view-tree first, screenshot corroboration.** Resolve locators against the page-source/pruned tree (deterministic-first, D4), fall back to vision, and cross-check the structural channel against a screenshot before executing a step. *(External: SoM + the "believe their eyes" over-trust caveat, arXiv 2607.04334.)*

5. **Real local devices via adb (Android) + XCTest/Xcode (iOS), behind a driver seam, so Perfecto is a later swap.** Mirror `callstack/agent-device`'s shape. Keep the **model call at the reflect boundary, not inside per-step execution**, and honor ADR 0013 (no gateway credential in the execution path, single-run device handle, separate process) — because interpreting LLM JSON is the *same* injection→execution path with a shorter fuse. *(Internal §7.3 constraints; external agent-device reference.)*

6. **Memory is a gated, poison-defended accelerator, not a free flywheel.** Procedural + semantic memory (§7.5) raise the reliability ceiling and lower per-release cost — a confirmed sub-flow replays with **zero LLM call** and one fix amortizes across every reuser — but **write-back is a privileged transition gated by the deterministic critic** (never the LLM), and promotion into the *shared* library requires an **attributable individual principal** (CF9), not machine replays. The spike proves adaptability; **memory does not extend the audit path**. *(Design: §7.5; external CoALA/Voyager + MINJA/AgentPoison poisoning literature; internal ADR 0009/0012/0013, CF6/CF9.)*

**The honesty boundary (non-negotiable, agreed with user):** this interpreter is a **throwaway adaptability spike**. Production certification stays **code-based** (the repo's twice-rejected-A, always-B stance). The spike proves *"an LLM + view-tree + bounded ReAct↔Reflexion loop adapts to real screens and recovers from failures on real devices"* — it does **not** prove the production reproducibility/audit path, which the interpreter structurally cannot satisfy (no `codeCommit`, bypasses the static gate, F6 fails). When the POC succeeds, the natural bridge to production is Perfecto's own move: **materialize the successful interpreted run into committed Appium code** (export-on-success), which is exactly the north-star's Approach B.

**Why not pure Approach B for the POC?** It reuses the whole spine but demonstrates adaptability only *indirectly* (regenerate-and-re-gate) and front-loads the codegen+static-gate machinery — heavier for a throwaway whose one job is showing adaptability. B is the *production* answer; A is the *spike* answer. The user chose the spike deliberately.

**Net:** your instinct (interpreter, LLM→JSON→runtime execution) is well-supported by 2026 practice for the *authoring/adaptability* half — Perfecto and Maestro both run interpreters. The correction the evidence adds is: **pair it with a deterministic critic and a bounded structured-feedback repair loop for the *reliability* half, and treat committed code as the export-on-success bridge to production**, not as a competitor to the spike.

### 7.5 Memory architecture (procedural + semantic) for adaptive self-healing

> **Intent restatement.** The O3 hybrid interpreter's job is to prove *adaptability and reliability* on 10+ critical-path flows as a throwaway spike (`mobile-test-automation-poc-brainstorm.md:37,40`). A memory layer raises the **reliability ceiling** (fewer live LLM emissions → fewer stochastic wrong-heals) and lowers the **per-release maintenance cost** (a confirmed sub-flow replays with zero LLM call, and one fix amortizes across every reuser). It does **not** raise the audit ceiling: memory is a POC-spike accelerator that must never itself produce a compliance verdict. The honesty boundary of §7.4 stands — *the spike proves adaptability, not the audit path* (`mobile-test-automation-poc-brainstorm.md:335`) — and this section adds a **sixth design commitment** to the five at §7.4: *memory write-back is a gated, poison-defended egress, not a free flywheel.*

This is one design with two memory types over a **single shared substrate** (the existing object repository "keyed by screen"), a **single write authority** (the deterministic rule-based critic), and a **single lineage discipline** extended for cross-conversation reuse. It is deliberately expressed only in IR-spine vocabulary so nothing provider-shaped crosses the model-call seam (`0001-...md:82-84`).

#### 7.5.1 The two memory types (CoALA split)

| | **Procedural memory — the skill library** | **Semantic memory — the app-fact store** |
|---|---|---|
| Holds | Named, parameterized, version-pinned **skills** (`signIn`, `goToScreen`) | **Known-good locator sets per screen** + a navigation graph |
| Substrate | Skill-cache rows, same shape as the ADR 0002 response cache (`0002-...md:107`) | The object repository / POM "keyed by screen" — *reused, not a parallel store* (`agent-appium-test-pipeline.md:164`) |
| Vocabulary | Body = existing `List<Step>` verbatim (`mobile-test-automation-brainstorm.md:211-234`) | `Locator` record verbatim, cascade a11y-id > resource-id > class-chain > predicate > uiautomator > xpath (`mobile-test-automation-brainstorm.md:184-191,229-234`) |
| Write risk (CoALA asymmetry) | **Higher** — a corrupted confirmed skill fans out to every reuser | Lower — a bad locator set mis-grounds one repair |
| Gate strength | Stricter: N-clean-run quarantine **+ individual-principal promotion** (7.5.3) | Lighter confidence threshold, but same critic authority |

Both are **verdict-influencing state**, so both inherit F6 pinning (`spine.spec.md:88-105`), the M37 principal (`spine.spec.md:158-164`), and lineage discipline (7.5.4) — not a parallel machinery.

**What a skill is.** A skill is a macro over `Step`s and *nothing more* — it invents no action vocabulary. The only IR extension is one opcode (`ActionType.SKILL`) and one optional field (`Step.skillRef = {skillId, digest, args}`); a `SKILL` step expands, LLM-free at replay, into the referenced body with `args` bound (analogous to Maestro `runFlow`). Because the body is committed/pinned IR, expansion honors the replay boundary "LLM output never touches it; it only consumes committed code" (`blueprint-revision-v2.md:73`). Composition is allowed to depth ≤ 3 with a cycle check at store-write time, and only **confirmed** skills may be nested. The skill's `semanticName`+`description` is the string that gets embedded; the body is what gets stored (Voyager discipline).

**The semantic store.** A `Screen` has a stable `screenId` plus a recognition **signature** (co-present anchor elements), joined to the IR by the existing `TargetElement.screenContext` (`mobile-test-automation-brainstorm.md:222-227`) — no new IR field for screen scoping. Per logical element it holds a cascade-ordered `KnownGoodLocatorSet` carrying `Locator.confidence`/`source` and a `ConfirmStamp` with **first-class `deviceClass ∈ {SIM, REAL}`** — because iOS simulator and device accessibility trees diverge (`agent-appium-test-pipeline.md:47-53`). On a `LOCATOR_NOT_FOUND`/`STALE_ELEMENT` classification the store hands the Reflexion repair its **admissible-alternatives** set (this screen's cascade + sibling anchors) — the repair *chooses among* trusted candidates, it does not free-generate (`mobile-test-automation-poc-brainstorm.md:200`), which is also the primary poisoning defense (a well-populated trusted store collapses injection success). Navigation edges are harvested from existing `Step.action=NAVIGATE` + `controlFlow` (`mobile-test-automation-brainstorm.md:211-220`); a "path back to screen Y" resolves to a procedural skill reference, keeping semantic memory declarative.

#### 7.5.2 The write-back gate — the deterministic critic is the sole authority

Every healed step/skill is a **privileged state transition** that only the **deterministic rule-based critic** — never the LLM — can authorize. The critic is the pipeline's existing classifier: "classification MUST be rule-based against the fixed taxonomy … explicitly not LLM work" (`spine.spec.md:265-269`). The LLM (through Invoke Models, `0001-...md:82-84`) may only *propose* a repair; write authority derives solely from a green deterministic replay plus rule-based classification. **LLM self-scored confidence is deliberately absent from the gate predicate** — a poisoned heal's own confidence grows authoritative without ground truth.

Auto-heal-vs-never, tied to the 7-class taxonomy:

| Class | Write-back? |
|---|---|
| `LOCATOR_NOT_FOUND`, `STALE_ELEMENT` | MAY auto-heal (the ~25-30% slice, ~75% success — `agent-appium-test-pipeline.md:16`) |
| `ASSERTION_MISMATCH`, `APP_CRASH` | **NEVER heal** — genuine app-change signals; healing here masks regressions (§8.8 R5) |
| `ENV_INFRA` | **NEVER heal** — "MUST re-queue — never heal" (`spine.spec.md:116-119`) |
| `TIMEOUT_SYNC`, `DATA_PRECONDITION`, unmapped | Quarantine, not heal |

#### 7.5.3 Lifecycle state machine + promotion gate

Four states, all transitions critic-gated, every transition a superseding append (7.5.4):

```
CANDIDATE --[green replay, healable class, pinning complete]--> CANDIDATE (PRIVATE per-test cache only)
CANDIDATE --[N clean replays over >=M distinct tests  +  individual-principal decision]--> CONFIRMED (shared)
CANDIDATE --[criticalPath == true]--> HUMAN_DIFF_REVIEW --[human INSERT verdict]--> CONFIRMED
CONFIRMED --[canary window: reused by <=X tests before general shared reuse]--> CONFIRMED (general)
CONFIRMED --[green->red regression | consumed-digest mismatch]--> QUARANTINED (loud alert, M10a/M38)
QUARANTINED | CONFIRMED --[superseded | repeat-quarantine]--> RETIRED
any --> rollback: superseding append to prior CONFIRMED version (readers resolve latest non-superseded)
```

The gate predicate (deterministic critic is sole authority):

```
authorizeWriteBack(heal, replay, test):
  return  replay.verdict == GREEN
      and replay.reachedExpectedScreen
      and postconditionAssertsDistinguishingAnchorOfCorrectControl(heal)   # positive, not just screen-arrival
      and RULE_CLASSIFIER(replay.failedStep.failureClass) in {LOCATOR_NOT_FOUND, STALE_ELEMENT}
      and pinningComplete(heal)                                            # F6; else NO verdict recordable
      and consumedDigestsMatchPinned(heal)                                 # fail-closed equality check (7.5.4)
      and not criticalPath(test)                                           # else -> HUMAN_DIFF_REVIEW
  # LLM confidence is deliberately NOT a term.
```

**Critical-path interlock, conservative-by-default.** `criticalPath` is derived from a money/balance/auth `screenContext` allow-list, **not** opt-in tagging, so an untagged critical test cannot silently auto-heal. It is **data-flow-tainted**: any heal on a step that feeds a downstream `ASSERTION` target *inherits that assertion's criticality*, forcing human review even if the healed step is itself non-critical — this closes the "wrong-but-stable locator upstream of a balance assertion" false-green (residual R below). On critical paths, write-back routes to a human-reviewed diff; machine output is advisory (CF9, `spine.spec.md:386`).

#### 7.5.4 Audit, lineage, and the modified execution loop

**Cross-conversation lineage (this is a NEW construct, not inherited).** ADR 0012 chains rows *within a per-conversation chain* (`0012-...md:87-91`); a shared skill mutated across conversations belongs to no single conversation, so it has **no chain ADR 0012 constructs for it**. This section defines a **per-skill-lineage append-only chain** with its own head anchored into the ADR 0011 immutable object store per release, independent of the conversation chains, with its own verifier job. Without this named anchor, "prove this skill version produced this verdict and hasn't changed" is *not answerable* for shared memory — this is an ADR-level gap flagged for sdd-spec, not a detail the POC may hand-wave.

**Pinning a composed replay.** A replay composing N skills + M facts has no single `codeCommit`, so `ReplayReport` gains one field:

```
ReplayReport += { "memoryDigest": {
  "skillLineageHead":    "digest:<per-skill-chain head, 7.5.4>",   # NOT a conversation chain head
  "semanticStoreVersion":"digest:<per-screenContext sub-digest>",
  "skillsUsed": [ {skillId, skillCommit, trust:"CONFIRMED"} ],     # each replayed => ZERO LLM call
  "factsUsed":  [ {screenContext, factDigest, source:"OBJECT_REPO"} ]
} }
```

At replay, a **positive equality check** asserts every consumed fact/skill's live digest equals its pinned digest; any mismatch is fail-closed (no verdict recorded), mirroring F6 (`spine.spec.md:88-105`). LLM-derived skills additionally carry the ADR 0002 five-field key so a model bump cannot serve a stale skill (`0002-...md:51-53`).

**Modified ReAct↔Reflexion loop:**

```
for step in testCase.steps:
    skill = procedural.lookup(step.intent, screenContext)          # exact-match only for verdict-influencing replay
    if skill and skill.trust == CONFIRMED:
        r = replay(bind(skill, step.args))                          # *** ZERO LLM call — committed IR ***
        if r.ok: continue                                           # cache HIT: cost ~0
    facts  = semantic.admissibleAlternatives(screenContext)         # trusted candidates only (anti-poison)
    repair = reflexion.propose(step, facts) via InvokeModels        # ADR 0001 seam
    if RULE_CLASSIFIER(failure) not in {LOCATOR_NOT_FOUND, STALE_ELEMENT}:
        quarantine(); continue                                      # never heal ENV_INFRA / ASSERTION / CRASH
    if authorizeWriteBack(repair, replayOracle(repair), test):
        writeBack(repair, trust=CANDIDATE, principal=servicePrincipal)   # PRIVATE cache, supersede-not-update
        # promotion to shared CONFIRMED requires an INDIVIDUAL principal (7.5.3) — never a service principal
```

**Cosine-fallback retrieval never auto-executes.** Two-stage retrieval is exact `semanticName`+`appContext` match first (deterministic, auditable). Embedding cosine top-k may only **propose to a human/deterministic gate**; it may never silently select a skill a verdict depends on, because embedding drift (ANN recall, a newly-added sibling shifting neighbors) can return different skills run-to-run and the `memoryDigest` records *what ran*, not *what would be re-selected*. Whenever fallback is in play, the run is stamped `REPRODUCIBILITY_UNPINNED` so the verdict is flagged non-bit-reproducible rather than falsely pinned.

#### 7.5.5 How this strengthens the §8 arguments (concretely)

- **Maintainability (§8.6.2/§8.7).** The addressable delta per release is the ~12-22 cosmetic/locator-drift tests. A step served from a **confirmed** skill costs ~0 (no LLM call, no engineer edit); only the drifted residue costs one repair, and one write-back amortizes that fix across every reuser (Voyager-style composition). This is the concrete mechanism that pushes O3 toward O6's regenerate-and-filter TCO (`mobile-test-automation-poc-brainstorm.md:385-396`) — *the cache-hit-rate on procedural memory becomes THE per-release cost driver.* **Honest caveat:** the ~0-cost majority is a **steady-state** property; early releases run cold (few confirmed skills) and pay near-full cost until the flywheel spins up.
- **Reliability (§8.8).** Most steps replaying from committed IR removes the stochastic live-emission that drives silent wrong-heals (R1) and non-deterministic verdicts (R2). The deterministic critic as sole write authority + admissible-alternatives grounding directly harden R1/R5/R6. **New residual reliability rows R7/R8** (memory poisoning + wrong-but-stable false-green) are added to the register — memory *moves* risk from live emission to the write-back surface; it does not remove it.
- **Flywheel (§8.9).** Every gated write-back is a labelled correction/healing exemplar — exactly the "materialize-and-gate turns maintenance into a labelled-data pump" argument (`mobile-test-automation-poc-brainstorm.md:419-430`; `blueprint-revision-v2.md:49,109`). Procedural memory *formalizes* the exemplar/golden-set flywheel already in the design. **Caveat:** the write-back is the flywheel's data source **and** its poisoning attack surface — the same event that feeds Phase-2 training is the one that must be screened and gated.

#### 7.5.6 Honesty flags / required controls (red-team residuals that survive into the design)

These are **required**, not optional; the section is *not banking-safe* without them, and safe only as a fenced throwaway POC that never feeds a certification verdict.

1. **Cross-conversation lineage anchor is an unmet ADR-level gap.** The per-skill-lineage chain (7.5.4) is *specified here but not yet owned by an ADR*. Until a new ADR defines its anchor cadence and verifier, "prove it hasn't changed" is unanswerable for shared memory. **POC constraint: shared memory does not back any certification verdict.**
2. **Memory write-back is a 4th injection egress ADR 0009 does not screen.** ADR 0009's 2026-07-27 amendment sits at "flip-condition counter: 2 of 3," and "a fourth call site … forces the flip" (`0009-...md:122-123,165-167`). Healed NL fields (`description`/`semanticName`/`naturalReference`) derived from untrusted worksheet text are later embedded and surfaced as grounding — persistent injection with fan-out. **Required: either re-screen all healed NL fields through the screening library at write (carrying the screening-library-version marker), or forbid free NL in stored skills (canonical/opaque names only).** This must be reconciled with ADR 0009 explicitly and trips its flip counter to 3 of 3.
3. **`CONFIRMED` must not read as "certified."** N green machine replays is not certification; CF9 requires an attributable individual (`spine.spec.md:386`), and the spine's honest baseline is K=1 (`spine.spec.md:CF6`). **Required: any promotion into silently-reusable shared state requires an individual principal regardless of path criticality; service-principal auto-write is confined to the PRIVATE per-test candidate cache.** N/M thresholds bind under CF6's no-silent-change discipline. Consider renaming `CONFIRMED` to `MACHINE_PROMOTED` to prevent the misread.
4. **Wrong-but-stable false-green is structurally undetected.** The QUARANTINED trigger is green→red regression only; a heal that is silently wrong but consistently green emits no audit event. **Required controls:** the postcondition must assert a *positive distinguishing anchor of the correct control* (not mere screen arrival); a **canary window** caps blast radius on newly-promoted/reverted skills; and high-fan-in skills get periodic independent re-proof against fresh device ground truth.
5. **Stale/drift fail-closed.** `ttlReValidateOnAppVersion` must **not** be a per-record nullable boolean — the default is **mandatory demote-to-CANDIDATE on app-version bump**. A **SIM-confirmed fact can NEVER be returned to a REAL-device replay's admissible set** — a schema-level platform+deviceClass constraint, not advisory.
6. **Everything above is documented as NOT the production audit path.** The framing discipline the memory topic file already insists on must survive into the spec.

---

## 8. Six-way strategic comparison (ARB + auditor decision-grade)

> **Audience:** architecture review board + bank audit function. **Method:** the analysis triad an architect brings to a regulated-industry ARB — **(8.2) SWOT per option**, **(8.3) a weighted decision matrix** (weights derived from the architecture's own top-3 characteristics + the two user-mandated axes, surfaced for sign-off in 8.1), and **(8.4) a trade-off / tension analysis** in the style of the repo's own `style-decision.md` matrices, closing with **(8.5) a banking-compliance verdict**. Scope note: this situates the POC choice against the *strategic* landscape; it does **not** re-open the approved spine — the spine is the production north-star and appears here as the benchmark the others are measured against.

### 8.0 The six options

| # | Option | One-line characterization | Execution artifact | LLM role |
|---|---|---|---|---|
| **O1** | **Our spine** (approved) | LLM-free deterministic replay of committed code; the north-star | Committed Appium/TestNG **code** | None at all (F1 forbids it) — LLM lives upstream in Phase 1/2 |
| **O2** | **Pure interpreter** | LLM→JSON→live execution, minimal scaffolding | LLM's **JSON**, executed live | In the runtime loop, per step |
| **O3** | **Proposed hybrid** (§7.4) | Interpreter core + deterministic critic + bounded repair + export-to-code bridge | **JSON** live for the spike; **code** on export-to-prod | Reason+emit+repair, behind a seam; not in pass/fail |
| **O4** | **Perfecto AI** (vendor) | Scriptless runtime interpreter; export-to-Appium escape hatch (rel 26.2) | Interpreted intent; **exportable** to Appium JS | Vendor-internal, closed |
| **O5** | **Maestro** (OSS) | LLM authors declarative YAML DSL; fixed runtime interprets it | Committed **YAML** (data), interpreted live | Authors the DSL; not in execution |
| **O6** | **Meta TestGen-LLM** | "Assured Offline LLMSE" — LLM generates code candidates, deterministic **ensemble+filter** discards failures, human accepts survivors | Committed **code** (filtered) | Generates candidates offline; deterministic filter is the gate |

### 8.1 Comparison criteria & weights (⚠️ **confirm before scoring is final**) — v2, maintainability elevated

**Change from v1 (per user, 2026-07-29):** maintainability is now a **decisive** axis, not a secondary one — the stated goal is *minimum engineering/QA effort per monthly app release*, explicitly *minimizing maintenance of static test code*. Maintainability is therefore **raised 15 → 22** and **split into two visible sub-criteria** so the "static-code burden" is scored directly. Weights re-balanced (still sum = 100) by taking the added maintainability weight proportionally from reproducibility, adaptability, and speed. Full per-release effort model in **§8.6**.

| Criterion | Weight | Why this weight (banking + monthly-release lens) |
|---|---:|---|
| **Auditability & compliance** | **20** | The make-or-break axis. Can an auditor reconstruct a verdict from committed evidence, review the executable, attribute every decision? Banking model-risk + audit demand this. |
| **Maintainability** — *(a) static-code maintenance burden* | **13** | **User's dominant concern.** How much *committed test code* must be hand-edited/regenerated when the app releases monthly. Lower burden = higher score. |
| **Maintainability** — *(b) drift-adaptation effort (human hours/release)* | **9** | The other half: when a screen/flow changes, how much *human* effort (vs. automated re-resolution) to get green again. |
| **Reproducibility / determinism** | **13** | Top-1 characteristic (`:129-137`). Same input → same verdict, re-derivable. (Trimmed from 16 to fund maintainability.) |
| **Security (injection→execution)** | **13** | Top-3 characteristic + ADR 0013. Untrusted test text → generated actions → execution near credentials. |
| **Reliability (benchmark-grounded)** | **11** | Real F1/pass-rate, not vendor marketing. Independent benchmarks put autonomous interpreters at ~25–50%. |
| **Adaptability** | **8** | The POC's stated goal; strategically valuable but below compliance/maintenance in a bank. |
| **Speed-to-value / build cost** | **6** | Time + effort to first working value. |
| **Portability / vendor lock-in** | **7** | Bank preference for portable, owned, auditable assets over closed platforms (`architecture-diagrams.md:22`). |

> **v2 weights:** compliance + reproducibility + security = **46%** (still dominant); **maintainability = 22%** (now the second-largest bloc, ahead of any single technical axis). This directly encodes "minimize static-code maintenance under monthly releases." The split makes the trade-off honest: interpreters win **(a)** decisively but only draw even on **(b)**, because semantic drift still costs *someone* effort — the question is whether an LLM absorbs it or an engineer does (see §8.6).

### 8.2 SWOT per option

**O1 — Our spine (LLM-free committed code)**
- **S:** Maximal auditability/reproducibility (verdict = committed code + pinned versions); F1–F7 enforce boundaries; hash-chain lineage (ADR 0012); ADR 0013 credential isolation built in. Approved, funded, on a roadmap.
- **W:** No adaptability by itself — it's the *substrate*, not the generator; slowest to visible "AI value"; maintenance = regenerate-and-re-gate.
- **O:** Is the audit-ready foundation every other option must eventually land on; Meta-style filtering plugs straight in.
- **T:** If the org over-indexes on "show me the AI demo," the LLM-free spine looks unexciting and risks under-resourcing the load-bearing fitness functions.

**O2 — Pure interpreter (LLM→JSON→live)**
- **S:** Fastest adaptability demo; least code; reuses `TestCaseIR` as an action IR; showcases self-healing viscerally.
- **W:** **Fails the audit axis** — no committed executable, no `codeCommit`, bypasses the static gate; F6 fails; non-deterministic (stochastic even at temp 0); benchmark reliability ~25–50% F1.
- **O:** Great throwaway signal-generator; can seed the hybrid.
- **T:** **Compliance-fatal if mistaken for production** — the repo withdrew an LLM-in-replay concept on sight (`logical-components.md:26-29`); ADR 0013 injection→execution risk is *higher* here (shorter fuse).

**O3 — Proposed hybrid (interpreter + deterministic critic + export-to-code)**
- **S:** Adaptability of an interpreter *plus* a deterministic critic for reliability; reuses `TestCaseIR`; export-on-success bridges to the audit-ready code path; honors ADR 0013 (model call at reflect boundary, separate process).
- **W:** Two modes to build (interpret + export) = more moving parts than O2; the interpreted mode still isn't audit-grade until materialized to code.
- **O:** Matches the **2026 vendor consensus** (Perfecto's interpret-then-export); a clean migration story from spike → Phase-1 → production.
- **T:** Scope creep — the "critic + repair + export" can bloat a throwaway; must be disciplined to stay a spike.

**O4 — Perfecto AI (vendor scriptless)**
- **S:** Turnkey runtime adaptability + semantic/visual validation; real-device native; **rel 26.2 exports to Appium JS** (an audit bridge); Perfecto already in the stack.
- **W:** **Closed/proprietary** — the interpreter internals are a black box (transparency gap in release notes); validations must be pass/fail phrased; efficiency claims (50–70%) unverified.
- **O:** Fastest path to a *vendor-blessed* demo; the export can feed the committed-code path.
- **T:** **Vendor lock-in + auditability of a black box** — a bank auditor cannot inspect a closed model's decision; the repo explicitly declined it as the *target* precisely because "the client wants portable, auditable, version-controlled test assets" (`architecture-diagrams.md:22`).

**O5 — Maestro (LLM authors YAML DSL)**
- **S:** **Best determinism/audit story of the interpreter family** — the committed YAML is human-readable, versionable, diff-able, and runs deterministically; agentic at *authoring* only; built-in waiting reduces flakiness.
- **W:** **iOS is simulator-only natively** (real iOS needs community tooling) — a hard constraint for a real-device banking suite; no runtime self-healing (drift → test fails → human fixes); YAML is a *second vocabulary* to reconcile with `TestCaseIR`; Perfecto doesn't run Maestro.
- **O:** Proves "LLM authors data, fixed runtime interprets, artifact stays auditable" — the exact needle O3 threads.
- **T:** The iOS gap + Perfecto incompatibility make it a poor fit for *this* bank's certification tier; adopting its DSL forks the schema spine.

**O6 — Meta TestGen-LLM (Assured Offline LLMSE)**
- **S:** **Best-in-class reliability discipline** — deterministic ensemble+filter discards anything that won't build / is flaky / adds no coverage, *eliminating hallucination by construction*; output is committed code (fully auditable); **73% of surviving recommendations accepted** by engineers at Meta ([arXiv 2402.09171]).
- **W:** *Improves existing tests* more than green-field authoring from a worksheet; adaptability is indirect (regenerate+filter); needs a filter harness (≈ the spine's static+device gate).
- **O:** It is essentially **O1 + an LLM generator + a deterministic filter** — i.e., the production shape the spine is built to host. Validates the whole "codegen guarded by a deterministic gate" thesis with real numbers.
- **T:** Its numbers are unit-test-improvement, not mobile-UI green-field — don't over-transfer the 73%.

### 8.3 Weighted decision matrix (v2 — maintainability elevated)

Scores 1–5 (5 = best on that criterion). Weighted score = Σ(weight × score)/5, normalized to 100. **Scores are the analyst's, grounded in §7 + §8.6; adjust with the weights at the gate.**

| Criterion (weight) | O1 Spine | O2 Pure interp | O3 Hybrid | O4 Perfecto | O5 Maestro | O6 Meta-TestGen |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| Auditability & compliance (20) | **5** | 1 | 4 | 2 | 4 | **5** |
| Maint. (a) static-code burden (13) | 1 | **5** | **5** | **5** | 3 | 2 |
| Maint. (b) drift-adaptation effort (9) | 2 | 4 | **5** | **5** | 3 | 3 |
| Reproducibility / determinism (13) | **5** | 1 | 3 | 2 | 4 | **5** |
| Security injection→exec (13) | **5** | 2 | 4 | 3 | 4 | **5** |
| Reliability (benchmark) (11) | **5** | 2 | 3 | 3 | 4 | **5** |
| Adaptability (8) | 1 | **5** | **5** | **5** | 3 | 2 |
| Speed-to-value / build cost (6) | 2 | **5** | 3 | **5** | 4 | 2 |
| Portability / lock-in (7) | **5** | 4 | 4 | 1 | 4 | **5** |
| **Weighted total (/100)** | **≈73** | ≈50 | **≈74** | ≈62 | ≈73 | **≈75** |

**Reading (v2 — maintainability at 22%):** elevating maintainability **compresses the whole field and reshuffles the middle** — the committed-code lead over interpreters shrinks from ~11 points to a near-tie at the top:
- **O6 (Meta-TestGen ≈75), O3 (Hybrid ≈74), O1 (Spine ≈73), O5 (Maestro ≈73) now cluster within 2 points** — the maintainability re-weight lifted **O3 (Hybrid) into a virtual tie for the lead**, because it scores full marks on *both* maintainability sub-criteria while staying compliance-credible (4/5 audit). This is the analytically important result: **once "minimize static-code maintenance" is weighted as you want it, the hybrid is no longer just the POC answer — it becomes co-leading for production too.**
- **O1 (Spine) dropped from ≈82 to ≈73** — the static-code maintenance burden (score 1) is exactly the cost you flagged; it's the spine's weakest axis and now it's weighted heavily. O1 is still audit-perfect, but the monthly-release toll is real and now visible.
- **O6 (Meta-TestGen ≈75) still edges ahead** because its deterministic filter *regenerates* rather than hand-edits — its maintenance is "re-run the generator + filter," not "an engineer patches XPath." That's a lower-human-effort form of static-code maintenance than the spine's, which is why O6 > O1 on maintainability (2 vs 1).
- **O2 (Pure interpreter ≈50)** rises but stays last for production — zero static-code burden can't offset the audit/reproducibility/reliability penalties.
- **O4 (Perfecto ≈62)** gains from strong maintainability but the black-box/lock-in drag persists.

**The headline the re-weight surfaces:** *if minimizing static-code maintenance under monthly releases is a top-tier goal, the decision is no longer "committed-code vs interpreter" — it's "how do we get interpreter-grade maintenance economics without losing the audit trail," and the two answers that do that are **O3 (hybrid: interpret-then-materialize)** and **O6 (regenerate-and-filter, never hand-edit)**.* Both avoid the hand-maintained-static-code trap in different ways.

### 8.4 Trade-off / tension analysis (the real axis)

The six options array along **one dominant tension** the repo already names: **Adaptability ↔ Reproducibility/Auditability** (`characteristics-worksheet.md:330`). Plotting them:

```
 audit/determinism ▲
  (banking-safe)    │  O1 Spine ●        ● O6 Meta-TestGen
                    │        ● O5 Maestro
                    │              ● O3 Hybrid
                    │                     ● O4 Perfecto
                    │                            ● O2 Pure interp
                    └──────────────────────────────────────▶ adaptability
                                                     (demo-friendly)
```

- **The efficient frontier** runs O1/O6 → O5 → O3 → O4/O2. Everything off that line is dominated.
- **Maintainability-under-monthly-releases cuts across the tension:** interpreters (O2/O3/O4) *re-read the screen each run*, so cosmetic drift needs no rework — a real monthly-release advantage. Committed-code options (O1/O6) need regenerate-and-re-gate on drift, but the drift is *visible and reviewed* (safer, slower). O5 sits between — YAML edits are small and reviewable.
- **The banking auditor's single question** — *"show me the executable that produced this verdict, and prove it hasn't changed"* — is answerable by O1, O6, O5 (committed artifacts), *partially* by O3/O4 (only after export), and *not* by O2. This is why O2 cannot be a production answer regardless of its demo appeal.

### 8.5 Verdict — two decisions, not one

The comparison resolves into **two separate answers** because the POC question and the production question have different winners:

- **Production north-star (what the bank ships): O1 + O6.** The spine (O1) is the audit-ready substrate; the LLM generator + deterministic filter (O6, "Assured Offline LLMSE") is how you add AI *without* surrendering compliance. This is already the architecture's design — the comparison **independently validates it** against the 2026 landscape. Maestro (O5) is the credible OSS reference for the "authored-data, interpreted-deterministically" pattern but is ruled out for *this* bank by the iOS-simulator limit + Perfecto incompatibility. Perfecto AI (O4) is a *tactical* accelerator (its export bridges to O1), not the strategic core, because a bank cannot audit a black box.
- **The POC/spike (what proves the bet fast): O3 hybrid, seeded by O2.** For a throwaway whose job is demonstrating adaptability+reliability on 10+ critical-path flows, the hybrid is right: interpreter for adaptability, deterministic critic + bounded repair for reliability, `TestCaseIR` for continuity, and **export-on-success as the explicit bridge to the O1/O6 production path**. The honesty boundary (§7.4) stands: the spike proves adaptability, not the audit path.

**One-sentence ARB takeaway (v2, maintainability-weighted):** *Once "minimize static-code maintenance under monthly releases" is weighted as a top-tier goal, the field compresses to a near-tie at the top (O6 ≈75, O3 ≈74, O1/O5 ≈73) and the decision reframes from "code vs interpreter" to "how to get interpreter-grade maintenance economics without losing the audit trail" — answered by **O3 (interpret-then-materialize)** for the POC and **O6 (regenerate-and-filter, never hand-edit)** for production, both of which avoid the hand-maintained-static-code trap the spine alone would incur.*

### 8.6 Maintenance-economics analysis — per-release effort model (the decisive lens)

> This is the substance behind the user's refinement: apps release **monthly**, test artifacts churn constantly, and the goal is **minimum engineering/QA effort per release**, explicitly minimizing hand-maintenance of static code. A weighted row can't capture this — so here is the per-release cost model.

**8.6.1 What actually breaks on a monthly release** (drift taxonomy, from `agent-appium-test-pipeline.md:13-45`):
- **Cosmetic drift** (colour, position, label text, minor layout) — the *most common* churn. Breaks brittle locators (XPath especially), not semantics.
- **Locator drift** (id/accessibility-id renamed, hierarchy reshuffled by an OEM skin or refactor) — ~25-30% of failures are broken locators (`agent-appium-test-pipeline.md:43`).
- **Semantic drift** (a new step, a moved flow, a new gate/dialog) — the app genuinely changed; *any* approach requires a real update.
- **Environmental** (device/OS, infra) — orthogonal; handled by `ENV_INFRA` re-queue in all options.

**8.6.2 Who pays, and how much, per option** (H = human hours, A = automated/LLM):

| Option | Cosmetic drift | Locator drift | Semantic drift | Net human effort / release | Key risk |
|---|---|---|---|---|---|
| **O1 Spine** (hand/gen code) | Engineer edits committed code, re-gates | Engineer edits + re-gates | Engineer rewrites + re-gates | **Highest H** — every drift class touches committed code an engineer owns | The exact static-code-maintenance cost you want to avoid |
| **O2 Pure interpreter** | **A — re-reads screen, no edit** | **A — re-resolves live** | Fails; LLM re-generates JSON (A, low H) | **Lowest H** — but reliability ~25-50% means silent wrong-heals leak | False-heals + no audit of what changed |
| **O3 Hybrid** | **A — re-reads** | **A — deterministic-first + LLM repair** | LLM re-generates, deterministic critic gates (low H review) | **Low H** — interpreter economics + a gate that catches bad heals | Must re-materialize to code before a compliance verdict |
| **O4 Perfecto** | **A — vendor re-adapts** | **A — vendor self-heals** | Vendor re-interprets (A) | **Low H** — but effort moves *inside a black box* | Can't audit *what* the vendor healed; lock-in |
| **O5 Maestro** | **A — tolerant matching absorbs it** | Human edits YAML selector (small H) | Human/LLM edits YAML (small H) | **Medium-low H** — small, reviewable YAML edits; no runtime self-heal | iOS-sim limit; someone still edits YAML on locator drift |
| **O6 Meta-TestGen** | **A — regenerate + filter** | **A — regenerate + filter** | **A — regenerate + filter, human accepts** | **Low-medium H** — *regeneration replaces hand-editing*; human only reviews survivors | Filter harness must exist; green-field mobile ≠ Meta's unit-test-improvement setting |

**8.6.3 The load-bearing insight for your goal.** The thing you want — *minimize maintenance of static code* — is achieved by **two distinct strategies**, and it's important not to conflate them:

1. **Don't have static code (interpreter): O2/O3/O4.** Maintenance is "the runtime re-reads the current screen." Lowest static-code burden, but you trade the audit trail, and reliability is only ~25-50% autonomous — so *someone still reviews the heals*, or wrong-heals leak into a banking suite. **O3 adds the deterministic critic precisely to make this trade survivable.**
2. **Regenerate static code instead of hand-editing it (assured generation): O6.** The code still exists (auditable), but **no engineer patches XPath by hand** — on each release the LLM regenerates candidates and a deterministic filter keeps only the ones that build/pass/add coverage. Maintenance effort shifts from *edit* to *review-the-survivors*. This is the crucial reframing: **"minimize static-code maintenance" ≠ "eliminate static code" — it can mean "never hand-maintain it."**

**The banking-safe sweet spot** is therefore **not** the pure interpreter (O2 — lowest effort but un-auditable) and **not** the hand-maintained spine (O1 — auditable but highest effort). It is the **combination the top of the matrix now points to**: an **assured-generation production path (O6: regenerate-and-filter, so static code is never hand-maintained) with an interpreter front-end for adaptability/triage (O3)**. That gives you interpreter-grade maintenance economics *and* a committed, auditable artifact — resolving the tension your monthly-release constraint creates.

**Memory is the mechanism that makes O3's low maintenance real (§7.5).** The addressable delta per release is the ~12-22 cosmetic/locator-drift tests. A step served from a **confirmed** procedural skill costs ~0 (no LLM call, no engineer edit); only the drifted residue costs one repair, and one gated write-back amortizes that fix across *every* reuser. **The cache-hit-rate on procedural memory becomes THE per-release cost driver** — this is the concrete lever moving O3 toward O6's TCO. **Honest caveat:** the ~0-cost majority is a **steady-state** property — early releases run cold (few confirmed skills) and pay near-full cost until the flywheel populates. Do not budget day-one savings.

**Cost caveat (honesty):** "the LLM regenerates so humans don't maintain" has its own recurring cost — **LLM inference + the filter/gate run per release**, and a **review burden on survivors** (Meta: 73% accepted → 27% still needed a human look). It's *lower* human effort than hand-editing static code, not *zero*. And regeneration re-imports non-determinism unless cached/pinned (ADR 0002 cache key). The maintenance win is real but it moves cost from *engineer-hours* to *compute + lighter review*, which is usually the trade a bank wants (engineer time is the scarce, expensive resource) — but it should be stated, not assumed.

**Revised recommendation given the maintenance priority:**
- **POC (unchanged): O3 hybrid** — its interpreter core already gives the low static-code maintenance you want, and it's the fastest adaptability proof.
- **Production (sharpened by this analysis): O1 spine as substrate + O6 assured generation as the maintenance strategy.** The spine stays the audit-ready foundation, but the *maintenance model* is explicitly **regenerate-and-filter, never hand-maintain** — which is what keeps engineer effort low under monthly releases while preserving the committed-code audit trail. This is a stronger, more specific production posture than "just the spine," and it's what the re-weighted matrix independently points to.

### 8.7 Quantified cost / TCO model (per-release, illustrative)

> **Basis stated up front:** these are **order-of-magnitude planning figures**, not measured — they combine the repo's own targets, the research benchmarks, and standard engineering assumptions. Every input is labelled so the ARB can substitute real bank numbers. Assume a **suite of 100 automated critical-path tests**, a **monthly release**, and an all-in loaded QA-engineer cost of **~$100/hr** (placeholder — set to the bank's rate).

**Drift assumptions per monthly release** (from `agent-appium-test-pipeline.md:30-45`): ~20-30% of tests touch some drift each release; of those, cosmetic ≈ half, locator ≈ 25-30%, semantic ≈ 20-25%. So per 100 tests/month ≈ **20-30 tests need attention**, of which ≈ **5-8 are genuine semantic changes** (irreducible — every option pays these) and ≈ **12-22 are cosmetic/locator drift** (the addressable delta between options).

| Option | Static-code edits / release | Human hrs / release¹ | LLM+infra $ / release² | Est. **$/release**³ | 12-mo maintenance TCO | Notes |
|---|---|---|---|---|---|---|
| **O1 Spine** (hand-maintained code) | ~20-30 tests hand-edited + re-gated | **~20-30 h** | ~$0 (no gen) + device mins | **~$2,000-3,000** | **~$24k-36k** | Highest — every drift class is an engineer editing committed code |
| **O2 Pure interpreter** | ~0 (no committed code) | ~3-6 h (review heals) | ~$50-150 inference + device | **~$400-750** | ~$5k-9k | Lowest $ — but un-auditable; wrong-heals uncosted (risk in §8.8) |
| **O3 Hybrid** | ~0 live; materialize-on-export | ~5-8 h (review survivors + gate) | ~$100-250 inference + device | **~$700-1,050** | ~$8k-13k | Low — interpreter economics + a gate; materialization adds a step |
| **O4 Perfecto** (vendor) | ~0 (vendor-internal) | ~4-8 h (review) | **vendor license** (opaque) + device | **license-dominated** | license + ~$5k-10k | $ moves into an opaque license; lock-in |
| **O5 Maestro** | small YAML edits on locator drift | ~8-14 h (edit YAML) | ~$50-150 (authoring gen) + device | **~$850-1,550** | ~$10k-19k | Medium — small reviewable edits, but a human still edits on drift; no runtime heal |
| **O6 Meta-TestGen** (regenerate+filter) | **0 hand-edits** (regenerate) | ~5-8 h (review 73%-accept survivors) | ~$150-400 (regen ensemble) + gate + device | **~$800-1,200** | ~$10k-14k | Low human hrs; **cost shifts from engineer-time to compute** — the trade a bank wants |

*¹ Human hours = drift-tests × per-test effort; hand-edit ≈ 0.75-1 h/test (O1), review ≈ 0.2-0.3 h/test (O2/O3/O6). ² Inference = regeneration/repair token cost at ~current gateway rates for the drifted subset; device minutes are ~equal across options and omitted from the delta. ³ At $100/hr; **dominated by human hours**, which is the point.*

**What the model shows (the delta that matters):**
- **The maintenance cost is overwhelmingly human-hours, not compute.** O1's ~$24k-36k/yr vs O3/O6's ~$8k-14k/yr is almost entirely the difference between *engineers hand-editing static code* and *engineers reviewing regenerated/interpreted output*. **The 2-4× TCO gap is the concrete form of your "minimize static-code maintenance" goal.**
- **Regeneration (O6) and interpretation (O2/O3) both convert engineer-hours into compute** — the cheaper resource. O6 keeps the audit trail while doing so; O2 does not.
- **Perfecto (O4)'s cost is license-dominated and opaque** — a bank cannot model or audit it, which is itself a finding.
- **Break-even / sensitivity:** the interpreter/regeneration advantage grows with **suite size** and **release frequency**. At monthly releases and 100+ tests the gap is already 2-4×; at weekly releases or 500 tests it widens. Below ~1 release/quarter or <20 tests, the spine's simplicity may win — *but that is not this bank's situation* (monthly releases, 10+ critical-path flows growing to a real suite).

> **Substitute-your-numbers note for the ARB:** replace $100/hr, the 100-test suite size, the 20-30% drift rate, and the token rates with bank actuals; the *ranking* is robust to wide swings because it's driven by the human-hours-vs-compute structural difference, not the specific constants.

### 8.8 Self-healing risk register (why auto-heal needs controls in a banking suite)

> The interpreter/self-heal advantage (§8.6-8.7) carries a **specific, quantified danger** the ARB must see: an auto-heal that silently binds to the *wrong* element turns a test **green on a broken app** — a false-negative that is far more dangerous in banking than a false-positive. This register makes the risk and its controls explicit.

**The reliability ceiling (independent, not vendor):** self-healing repairs only the **~25-30% of failures that are broken locators**, at **~75% success on that slice** — so it fixes ~20% of all failures at best (`agent-appium-test-pipeline.md:16, 43`). Autonomous interpreter agents driving live UIs score **~25-50% F1** on independent benchmarks (§7.2: WebTestBench 26%, GUITester 33%→49%). Practitioner audits report ML-element-matching self-heal has **~3× the false-pass rate** of selector-fallback heal, and ~60% of teams disabled AI self-heal within 3 months (`agent-appium-test-pipeline.md:125`).

| # | Risk | Likelihood | Impact (banking) | Control |
|---|---|---|---|---|
| R1 | **Silent wrong-heal** — auto-heal binds to a plausible-but-wrong element; test passes on a broken flow | Med-High (interpreter) | **Critical** — false green on e.g. a payment/balance screen | Heal-confidence threshold ≥0.90; **alert on every heal**; disable auto-heal on critical fintech paths (payments/auth/balance) — heal there requires human confirm |
| R2 | **Non-deterministic verdict** — same input, different heal, different result | High (O2), Med (O3) | High — auditor can't reproduce | Deterministic critic gates acceptance (not the LLM); pin/cache model output (ADR 0002); **materialize to committed code before any compliance verdict** |
| R3 | **Un-audited change** — no record of *what* the heal changed | High (O2/O4) | **Critical** — fails the "prove it hasn't changed" audit question | Every heal is a lineage event (ADR 0012 hash-chain); the materialized diff is the reviewable artifact |
| R4 | **Injection→heal→execution** — untrusted test text steers a runtime heal near credentials | Med | Critical | ADR 0013: no gateway credential in exec path, single-run token, separate process; screening at the boundary (F3) |
| R5 | **Heal masks a real regression** — the app genuinely broke; heal "fixes" the test around it | Med | High — defect ships | Rule-based classification distinguishes `ASSERTION_MISMATCH`/`APP_CRASH` (never heal) from `LOCATOR_NOT_FOUND`/`STALE_ELEMENT` (may heal); `ENV_INFRA` re-queues, never heals |
| R6 | **Over-trust of the structural channel** — heal follows the a11y-tree when it conflicts with the screen | Med (2026 finding) | Med-High | Corroborate view-tree against a screenshot before committing an action (arXiv 2607.04334); track belief provenance |
| R7 | **Persistent memory poisoning** (memory design, §7.5) — untrusted worksheet text in healed NL fields (`description`/`semanticName`/`naturalReference`) is written to *shared* memory, then embedded and surfaced as grounding across conversations with fan-out (MINJA/AgentPoison class) | Med-High (with memory) | **Critical** — one poisoned `signIn` steers every reuser | Re-screen or bar free NL at write-back (reconcile as ADR 0009's 4th egress — trips its flip-counter to 3/3); admissible alternatives drawn from the *trusted store only*; append-only lineage + canary window bound blast radius (§7.5.2, §7.5.6-2) |
| R8 | **Wrong-but-stable false-green** (memory design, §7.5) — a locator heal binds to a plausible-but-wrong *still-present* control that satisfies the postcondition, replays green N times, machine-promotes, and ships a fintech regression the **regression-only** QUARANTINE trigger cannot detect | Med (with memory) | **Critical** — clean audit trail precisely in the false-green case that matters most | Postcondition asserts a **positive distinguishing anchor of the *correct* control** (not mere screen arrival); data-flow-tainted critical-path interlock forces human review; canary window + periodic independent re-proof of high-fan-in skills (§7.5.3, §7.5.6-4) |

> **R2/R3 note (memory):** memory *strengthens* R2 (most steps replay from committed IR — zero LLM call, no stochastic re-emission) and R3 (every write-back is a per-skill-lineage event) — **but** cosine-fallback retrieval re-imports non-determinism unless barred from auto-execution (the `REPRODUCIBILITY_UNPINNED` marker, §7.5.4), and the cross-conversation lineage anchor is a **new construct ADR 0012 does not yet own** (§7.5.6-1) — the single largest audit gap, deferred to `sdd-spec`.

**Register takeaway:** auto-heal is **safe only with a deterministic critic + human confirm on critical paths + a full audit trail of every heal**. This is *exactly* why the recommendation is **O3/O6, not O2** — O2's raw self-heal has none of these controls; O3 adds the critic and materialization; O6 regenerates under a deterministic filter so there is no "silent heal" at all. **In a banking suite, un-gated auto-heal is a control failure, not a feature.**

### 8.9 Flywheel / data-asset angle (maintenance that pays vs maintenance that's wasted)

> The blueprint's load-bearing premise: *"Phase 1 is not a throwaway prototype, it is the asset factory and data flywheel for Phase 2"* (`blueprint-revision-v2.md:15`). Each maintenance approach either **produces labelled training data as a byproduct** or **wastes it** — a decisive strategic difference the maintenance analysis would miss.

**What the flywheel wants** (`blueprint-revision-v2.md:107-109`): accepted code → exemplars/golden set; **human corrections → preference pairs**; diagnose-and-fix sessions → the healing agent's few-shot library; ReplayReports → failure-class base rates that calibrate the Phase-2 judge to TPR/TNR >90%.

| Option | Does its maintenance generate flywheel data? | Value |
|---|---|---|
| **O1 Spine** | **Yes, richly** — every engineer edit is a human correction (preference pair); every re-gate is a labelled ReplayReport | High — but at high human cost (§8.7) |
| **O2 Pure interpreter** | **Largely wasted** — runtime heals are ephemeral; no committed diff, often no record of what/why | **Low** — the maintenance effort produces no durable asset |
| **O3 Hybrid** | **Yes, if materialized** — export-on-success + the deterministic critic's classifications become exemplars + labelled outcomes; the repair loop's structured feedback is few-shot data | High — captures the flywheel *and* keeps human cost low |
| **O4 Perfecto** | **No (vendor-owned)** — the adaptations happen inside a black box; the bank doesn't own the labelled data | **Low/negative** — you pay to generate data another party keeps |
| **O5 Maestro** | **Partial** — YAML diffs are reviewable corrections (preference-pair-like), but no failure-class calibration data | Medium |
| **O6 Meta-TestGen** | **Yes, by construction** — the accept/reject decision on each regenerated candidate *is* labelled data (73% accept = a preference signal); the filter outcomes are failure-class base rates | **Highest** — the maintenance process *is* the data-labelling process |

**The strategic reframing this adds:** maintenance is not just a cost to minimize — in a flywheel design it's a **data-generation opportunity**. **O6's "regenerate-and-filter" and O3's "materialize-and-gate" both turn the monthly-release maintenance cycle into a labelled-data pump** for Phase 2; **O2 (pure interpreter) and O4 (Perfecto) spend the maintenance effort and get no durable asset** — O4 actively *gives the asset to the vendor*. This is a second, independent reason the recommendation lands on **O3 (POC) + O1/O6 (production)** rather than the pure interpreter or the vendor platform: they are the options where *the effort you spend maintaining tests compounds into the Phase-2 asset base* instead of evaporating.

**Memory formalizes this flywheel — and exposes its one hard tension (§7.5).** In the memory design every gated write-back *is* a labelled correction/healing exemplar: the deterministic critic's verdict is the label, the repair diff is the preference pair, the 7-class outcome is failure-class base-rate data — now *persisted and provenance-signed* rather than lost per run. Procedural memory turns the O3 "materialize-and-gate" pump from an argument into a concrete store. **The honest tension:** the write-back that feeds the Phase-2 data **is the same event** as the persistent-injection egress (R7). The flywheel's data source and its poisoning attack surface are one and the same — so screening + critic-gating + individual-principal promotion are a precondition for **both** data quality and safety, never an afterthought.

**Sources for the vendor/academic anchors:** [Perfecto AI launch](https://www.perforce.com/press-releases/perfecto-ai) · [Perfecto 26.2 Appium export](https://help.perfecto.io/perfecto-help/content/perfecto/release-notes/release-26-2.htm) · [Maestro AI/MCP (DeepWiki)](https://deepwiki.com/mobile-dev-inc/Maestro/6.5-ai-features-and-mcp-server) · [Meta TestGen-LLM (arXiv 2402.09171)](https://arxiv.org/abs/2402.09171) · [WebTestBench reliability](https://arxiv.org/html/2603.25226) · [Compiled AI: interpreter-vs-codegen tradeoff](https://arxiv.org/html/2604.05150v1) · [Structured-feedback repair (VeriHarness)](https://arxiv.org/html/2607.14167v1).

