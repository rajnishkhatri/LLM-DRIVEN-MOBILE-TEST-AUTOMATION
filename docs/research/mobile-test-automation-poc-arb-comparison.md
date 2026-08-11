# Architecture Review Board · Audit Function · Decision-Grade

**How the mobile test system generates & runs tests: a six-way comparison**
A strategic evaluation of six architectures for LLM-driven mobile test automation, weighted for a banking context where auditability and maintenance under monthly app releases are decisive. SWOT, a weighted decision matrix, a maintenance-economics model, a self-healing risk register, and a data-asset lens.

| | |
|---|---|
| **Target** | `mobile-test-automation` |
| **Method** | SWOT · weighted matrix · TCO · risk register |
| **Weighting** | maintainability elevated to 22% |
| **Status** | Draft for ARB sign-off |

> **Scope:** this situates the choice against the strategic landscape; it does not re-open the approved spine. The spine is the benchmark the others are measured against.

---

## Summary — the decision, up front

Two questions with two different winners. The POC question and the production question do not resolve to the same option — and once minimizing hand-maintained static code under monthly releases is weighted as a first-class goal, the field compresses to a near-tie at the top.

**Production north-star — Spine as substrate + assured generation.**
Keep the LLM-free deterministic replay spine as the audit-ready foundation, and make the maintenance model regenerate-and-filter, never hand-maintain (the Meta "Assured Offline LLMSE" pattern). This preserves the committed-code audit trail while shifting maintenance cost from engineer-hours to compute.

**POC / spike — The proposed hybrid (O3).**
A runtime-interpreting Appium framework — LLM emits TestCaseIR JSON executed live on real local devices — with a deterministic critic and a bounded ReAct↔Reflexion repair loop. Fastest proof of adaptability; materialize successful runs to committed code as the bridge to production.

---

## 01 — The six options

Two axes separate them: what the execution artifact is (committed code vs interpreted data), and where the LLM sits (upstream, in the loop, or authoring a DSL).

| # | Option | Characterization | Execution artifact | LLM role |
|---|---|---|---|---|
| O1 | Our spine (approved) | LLM-free deterministic replay of committed code — the north-star | Committed Appium/TestNG code | None (F1 forbids it); LLM lives upstream |
| O2 | Pure interpreter | LLM → JSON → live execution, minimal scaffolding | LLM's JSON, executed live | In the runtime loop, per step |
| O3 | Proposed hybrid | Interpreter core + deterministic critic + bounded repair + export-to-code | JSON live; code on export | Reason + emit + repair, behind a seam |
| O4 | Perfecto AI (vendor) | Scriptless runtime interpreter; Appium export (rel 26.2) | Interpreted intent; exportable | Vendor-internal, closed |
| O5 | Maestro (OSS) | LLM authors YAML DSL; fixed runtime interprets it | Committed YAML, interpreted live | Authors the DSL; not in execution |
| O6 | Meta TestGen-LLM | Assured Offline LLMSE — generate candidates, deterministic filter, human accepts | Committed code (filtered) | Generates offline; filter is the gate |

---

## 02 — Weighted decision matrix

Scores 1–5 (5 = best), weighted for a banking + monthly-release context. Elevating maintainability to 22% compresses the field: the ~11-point committed-code lead collapses to a 4-way near-tie, and the hybrid rises into it.

| Criterion (weight) | O1 Spine | O2 Pure interp | O3 Hybrid | O4 Perfecto | O5 Maestro | O6 Meta-Gen |
|---|---|---|---|---|---|---|
| Auditability & compliance (20) | 5 | 1 | 4 | 2 | 4 | 5 |
| Maint. (a) static-code burden (13) | 1 | 5 | 5 | 5 | 3 | 2 |
| Maint. (b) drift-adaptation effort (9) | 2 | 4 | 5 | 5 | 3 | 3 |
| Reproducibility / determinism (13) | 5 | 1 | 3 | 2 | 4 | 5 |
| Security (injection→exec) (13) | 5 | 2 | 4 | 3 | 4 | 5 |
| Reliability (benchmark) (11) | 5 | 2 | 3 | 3 | 4 | 5 |
| Adaptability (8) | 1 | 5 | 5 | 5 | 3 | 2 |
| Speed-to-value / build cost (6) | 2 | 5 | 3 | 5 | 4 | 2 |
| Portability / lock-in (7) | 5 | 4 | 4 | 1 | 4 | 5 |
| **Weighted total /100** | **73** ↓ from 82 | **50** | **74** ↑ from 71 | **62** | **73** | **75** |

Score guide: 4–5 strong · 3 mixed · 1–2 weak.

**Top cluster: O6 75 · O3 74 · O1 73 · O5 73 — within 2 points.**

The re-weight is the analytically important move: once "minimize static-code maintenance" is weighted as intended, the decision reframes from *code vs interpreter* to *how to get interpreter-grade maintenance economics without losing the audit trail* — answered by O3 (interpret-then-materialize) and O6 (regenerate, never hand-edit).

---

## 03 — The dominant tension

Every option sits on one trade-off the architecture already names — adaptability against auditability. The efficient frontier runs from the audit-safe corner to the demo-friendly corner; anything off it is dominated.

```
▲ audit / determinism (banking-safe)
  │   O1 Spine (73)        O6 Meta-Gen (75)
  │            O5 Maestro (73)
  │                  O3 Hybrid (74)
  │                          O4 Perfecto (62)
  │                                  O2 Pure interp (50)
  └──────────────────────────────────────────────▶ adaptability (demo-friendly)
```

The auditor's single question — "show me the executable that produced this verdict, and prove it hasn't changed" — is answerable by O1/O5/O6 (committed artifacts), only after export by O3/O4, and not at all by O2. That is why O2 cannot be a production answer regardless of its demo appeal.

---

## 04 — SWOT by option

The condensed strategic read on each. Strengths and weaknesses are current-state; opportunities and threats are forward-looking.

### O1 — Our spine (LLM-free committed code) · ≈73 /100

- **Strengths.** Maximal auditability & reproducibility; F1–F7 fitness functions; hash-chain lineage; credential isolation built in. Approved and funded.
- **Weaknesses.** No adaptability alone — it's the substrate, not the generator. Highest static-code maintenance; slowest to visible AI value.
- **Opportunities.** The audit-ready foundation every other option must land on; Meta-style assured generation plugs straight in.
- **Threats.** If the org over-indexes on "show me the demo," the load-bearing fitness functions risk under-resourcing.

### O2 — Pure interpreter · ≈50 /100

- **Strengths.** Fastest adaptability demo; least code; reuses TestCaseIR as an action IR; self-healing is visceral. Lowest static-code burden.
- **Weaknesses.** Fails the audit axis — no committed executable, no codeCommit, bypasses the static gate. Non-deterministic; ~25–50% F1.
- **Opportunities.** Excellent throwaway signal-generator; can seed the hybrid.
- **Threats.** Compliance-fatal if mistaken for production; injection→execution risk is higher here (shorter fuse).

### O3 — Proposed hybrid · ≈74 /100

- **Strengths.** Interpreter adaptability plus a deterministic critic for reliability; reuses TestCaseIR; export-on-success bridges to the audit path; honors credential isolation.
- **Weaknesses.** Two modes to build (interpret + export); the interpreted mode isn't audit-grade until materialized.
- **Opportunities.** Matches the 2026 vendor consensus (interpret-then-export); a clean spike → Phase-1 → production migration.
- **Threats.** Scope creep — critic + repair + export can bloat a throwaway; discipline required to stay a spike.

### O4 — Perfecto AI (vendor scriptless) · ≈62 /100

- **Strengths.** Turnkey runtime adaptability + semantic/visual validation; real-device native; rel 26.2 exports to Appium JS; already in the stack.
- **Weaknesses.** Closed/proprietary — interpreter internals are a black box; validations must be pass/fail; efficiency claims unverified.
- **Opportunities.** Fastest vendor-blessed demo; the export can feed the committed-code path.
- **Threats.** Lock-in + un-auditable black box — a bank auditor cannot inspect a closed model's decision. Declined as the target for exactly this reason.

### O5 — Maestro (LLM authors YAML DSL) · ≈73 /100

- **Strengths.** Best determinism/audit story of the interpreter family — committed YAML is readable, versionable, diff-able, runs deterministically; agentic at authoring only.
- **Weaknesses.** iOS is simulator-only natively; no runtime self-healing; YAML is a second vocabulary to reconcile with TestCaseIR; Perfecto doesn't run Maestro.
- **Opportunities.** Proves "LLM authors data, fixed runtime interprets, artifact stays auditable" — the needle O3 threads.
- **Threats.** The iOS gap + Perfecto incompatibility make it a poor fit for this bank's certification tier; its DSL forks the schema spine.

### O6 — Meta TestGen-LLM (Assured Offline LLMSE) · ≈75 /100

- **Strengths.** Best-in-class reliability discipline — a deterministic ensemble+filter eliminates hallucination by construction; output is committed, auditable code; 73% of survivors accepted at Meta.
- **Weaknesses.** Improves existing tests more than green-field authoring; adaptability is indirect; needs a filter harness (≈ the spine's gate).
- **Opportunities.** It is O1 + an LLM generator + a deterministic filter — the production shape the spine is built to host. Validates the whole thesis with real numbers.
- **Threats.** Its figures are unit-test-improvement, not mobile-UI green-field — don't over-transfer the 73%.

---

## 05 — Maintenance economics — per-release TCO

Order-of-magnitude planning figures (substitute bank actuals): 100 automated critical-path tests, monthly release, ~$100/hr loaded QA cost. The cost is overwhelmingly human-hours, not compute — which is exactly the lever for "minimize static-code maintenance."

| Option | Static-code edits / release | Human hrs | LLM+infra $ | Est $/release | 12-mo TCO |
|---|---|---|---|---|---|
| O1 Spine | ~20–30 tests hand-edited + re-gated | 20–30 h | ~$0 gen | $2,000–3,000 | $24k–36k |
| O2 Pure interp | ~0 (no committed code) | 3–6 h | ~$50–150 | $400–750 | $5k–9k |
| O3 Hybrid | ~0 live; materialize on export | 5–8 h | ~$100–250 | $700–1,050 | $8k–13k |
| O4 Perfecto | ~0 (vendor-internal) | 4–8 h | license (opaque) | license-dom. | license +$5k–10k |
| O5 Maestro | small YAML edits on locator drift | 8–14 h | ~$50–150 | $850–1,550 | $10k–19k |
| O6 Meta-Gen | 0 hand-edits (regenerate) | 5–8 h | ~$150–400 | $800–1,200 | $10k–14k |

The 2–4× TCO gap between O1 (~$24k–36k/yr) and O3/O6 (~$8k–14k/yr) is almost entirely the difference between engineers hand-editing static code and engineers reviewing regenerated/interpreted output. Both regeneration (O6) and interpretation (O2/O3) convert engineer-hours into compute — the cheaper resource. O6 keeps the audit trail while doing so; O2 does not. The advantage widens with suite size and release frequency.

---

## 06 — Self-healing risk register

The interpreter/self-heal advantage carries a specific danger: an auto-heal that silently binds to the wrong element turns a test green on a broken app — a false-negative far more dangerous in banking than a false-positive. **Un-gated auto-heal is a control failure, not a feature.**

| Risk | Likelihood | Impact | Control |
|---|---|---|---|
| R1 · Silent wrong-heal | Med–High | Critical | Confidence ≥0.90; alert on every heal; disable auto-heal on payments/auth/balance — human confirm required |
| R2 · Non-deterministic verdict | High (O2) | High | Deterministic critic gates acceptance (not the LLM); pin/cache output; materialize to code before any compliance verdict |
| R3 · Un-audited change | High (O2/O4) | Critical | Every heal is a hash-chain lineage event; the materialized diff is the reviewable artifact |
| R4 · Injection → heal → exec | Med | Critical | No gateway credential in exec path; single-run token; separate process; screening at the boundary (F3) |
| R5 · Heal masks a real regression | Med | High | Rule-based classification: ASSERTION_MISMATCH / APP_CRASH never heal; ENV_INFRA re-queues, never heals |
| R6 · Over-trust structural channel | Med | Med–High | Corroborate view-tree against a screenshot before acting; track belief provenance |
| R7 · Persistent memory poisoning †| Med–High | Critical | Re-screen or bar free NL at write-back (memory write-back is a 4th injection egress); admissible alternatives from the trusted store only; append-only lineage + canary window bound blast radius |
| R8 · Wrong-but-stable false-green †| Med | Critical | Postcondition asserts a positive distinguishing anchor of the *correct* control (not mere screen arrival); data-flow-tainted critical-path interlock; canary window + periodic re-proof of high-fan-in skills |

Self-healing repairs only the ~25–30% of failures that are broken locators, at ~75% on that slice — ~20% of all failures at best. Practitioner audits report ML-element-match self-heal has ~3× the false-pass rate of selector-fallback, and ~60% of teams disabled AI self-heal within 3 months. Auto-heal is safe only with a deterministic critic + human confirm on critical paths + a full audit trail — which is why the recommendation is O3/O6, not O2.

> **† R7/R8 arise only if the O3 hybrid adds a procedural/semantic memory layer** (§7.5 of the brainstorm, [mobile-test-automation-poc-brainstorm.md](mobile-test-automation-poc-brainstorm.md)). Memory raises reliability and lowers per-release cost, but write-back becomes shared mutable verdict-influencing state — so it is banking-safe only human-ratified-CANDIDATE-only and never feeding a certification verdict. These two rows extend R1–R6 for that design; they do not change the six-way verdict.

---

## 07 — Data-asset / flywheel lens

Maintenance is not only a cost — in a flywheel design it is a data-generation opportunity. Each approach either produces labelled training data as a byproduct or wastes it. A second, independent reason the recommendation lands where it does.

| Option | Maintenance generates flywheel data? | Value |
|---|---|---|
| **O1 Spine** | **Yes, richly** — every edit is a human correction (preference pair); every re-gate is a labelled ReplayReport | High |
| **O2 Pure interp** | **Largely wasted** — runtime heals are ephemeral; no committed diff, often no record of what/why | **Low** |
| **O3 Hybrid** | **Yes, if materialized** — export + critic classifications become exemplars & labelled outcomes; repair feedback is few-shot data | High |
| **O4 Perfecto** | **No** — adaptations happen in a black box; the bank doesn't own the labelled data | **Low / neg.** |
| **O5 Maestro** | **Partial** — YAML diffs are reviewable corrections, but no failure-class calibration data | Medium |
| **O6 Meta-Gen** | **Yes, by construction** — the accept/reject decision on each candidate is labelled data; filter outcomes are failure-class base rates | **Highest** |

O6's "regenerate-and-filter" and O3's "materialize-and-gate" both turn the monthly-release maintenance cycle into a labelled-data pump for Phase 2; O2 and O4 spend the effort and get no durable asset — O4 actively *gives the asset to the vendor*. The effort you spend maintaining tests should compound into the Phase-2 asset base, not evaporate.

---

> Draft for ARB sign-off. Weights, scores, and the illustrative TCO constants are the analyst's and are to be ratified with bank actuals; the ranking is robust to wide swings because it is driven by the human-hours-vs-compute structural difference, not the specific constants. Grounded in the `mobile-test-automation` architecture artifacts, 2026 vendor/academic research (Perfecto, Maestro, Appium MCP, Meta TestGen-LLM), and independent reliability benchmarks. Companion to the SDD Stage-1 brainstorm (`docs/research/mobile-test-automation-poc-brainstorm.md`).
