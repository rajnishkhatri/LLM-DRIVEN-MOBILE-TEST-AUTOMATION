# Ari improvement-loop runbook

Status: v1 · Owner: Rajnish Khatri · 2026-10-01
Audience: whoever inherits Ari. This is the operating manual for the quality loop — how v1 was
derived, and the exact procedure that keeps it improving. It points at the artifacts; it does not
duplicate them.

**The one rule everything below enforces:** behavior changes enter through the golden set, never
around it. Data first, then code, then gates, then release.

## 0. Where everything lives

| Artifact | Path | It is |
|---|---|---|
| Eval spec | `ari/evals/eval-spec.md` | the acceptance criteria (layers §2 · dims §3 · method §4 · taxonomy §5 · sweep §6 · judge §7 · human layer §8 · gates §9) |
| Golden set | `ari/evals/golden-set.jsonl` | 72 labeled rows — the behavioral spec as data |
| Ten exemplars | `ari/evals/test-cases.md` | TC-01…TC-10, one+ per failure class |
| Rule table | `ari/build/ari_demo/router/rules.py` | stage-0 phrasebook (data, not logic) |
| Sweep + report | `ari/build/ari_demo/router/sweep.py` → `ari/build/sweep-report.md` | the thresholds' provenance |
| Judge stub | `ari/build/ari_demo/evals/judge.py` | rubric contract + calibration gate |
| Gates | `ari/build/tests/test_gate01…12_*.py` | the 12 release gates as pytest |
| Decision log | JSONL via `--log` (schema in `synthesis.py DecisionLog`) | one line per turn; the harvest corpus |

Run the gates (offline, deterministic — from `ari/build/`):

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest
```

## 1. The loop at a glance

```
OBSERVE          CODE                 SPEC                    IMPLEMENT         CALIBRATE        GATE → RELEASE
decision log  →  open coding       →  golden rows          →  rules / prompts → sweep;        →  12 gates green;
escapes          axial (3–7 classes)  (+ class if earned)     / judge / code    judge TPR/TNR     versioned change
system mining                                                                                  ↘  back to OBSERVE
```

**"Release" means any change to:** prompts, model or model config, thresholds, the rule table, the
judge rubric, or the taxonomy. Each one re-runs the gates. No exceptions for "small" changes — a
one-word prompt edit is a release.

## 2. How v1 was built — the replication recipe

Repeat these eight steps from zero for any new assistant or newly onboarded stream. Method source:
the AI-evals error-analysis ladder (open/axial coding per Grounded Theory; practiced in the
recipe-chatbot coursework) — spec §4 has the citations.

**S1 — Name the dimension space before writing queries.**
Do: pick the axes on which behavior can differ. v1: intent · ambiguity (incl. **trap**) ·
entitlement · adversarial · turn position (spec §3).
Done when: every axis has named levels and at least one level nobody expects in normal traffic
(trap, cross-tenant, doc-injection).

**S2 — Build the trace corpus, sampled by stakes, not traffic.**
Do: write (v1: synthesize; future: harvest) queries covering the grid. Over-weight what is rare but
fatal — v1 is 19% hostile/action rows against a ~0% traffic share.
Done when: every cell that maps to a design promise has rows, including deliberate traps and
genuinely ambiguous rows.

**S3 — Open coding.**
Do: walk every trace against the design's contracts (ADR behavior clauses, router sketch). Tag
every plausible divergence with a free-vocabulary code — do not force codes into bins, and code the
happy paths too (confirmation-bias check). v1: 25 open codes.
Done when: new traces stop producing new codes (saturation).

**S4 — Axial coding → failure taxonomy.**
Do: cluster codes by **shared mechanism AND shared detecting instrument**; a cluster earns class
status only if it differs from every other class in at least one of the two. Bound top-level
classes to 3–7. v1: 25 codes → 7 classes, F1–F7 (spec §5); each class definition is one testable
sentence — a design promise inverted.
Done when: every open code maps to exactly one class, and the codebook passes its acceptance test —
a new team member classifies a fresh trace the same way, inter-rater agreement ≥ 80%.

**S5 — Assign each class its instrument, at the lowest layer that catches it deterministically.**
Do: code assertion > calibrated judge > human review. Security and side-effect classes (F3/F4/F5)
must land on code probes (canaries, duplicate injection, conformance tests) — never judge-only.
Done when: the gate table (spec §9) has ≥ 1 gate per class and each gate names its bar type:
absolute (0 / 100%), statistical (≥ threshold), or regression.

**S6 — Freeze the golden set schema and label the rows.**
Do: schema per spec §6. Labeling rules: `expected` states obligations, not wording; ambiguous rows
get `route: null` + `acceptable` (any confident route on them is a failure by definition); `class`
tags only on rows built to probe one; canary values live in fixtures, never in rows.
Done when: a loader validates every enum on every row (gate-level check, `evals/golden_set.py`).

**S7 — Carve the rule table against the set; sweep the thresholds.**
Do: distinctive phrases only — each rule must hit its rows and stay silent on the null rows. Then
grid-sweep θ × margin over the set, choose maximum fast-path coverage subject to precision ≥ 0.99,
most-stringent tie-break, and commit the report:

```bash
python3 -m ari_demo.router.sweep
```

Done when: `sweep-report.md` carries the `CHOSEN theta=… margin=…` line and gate 1 pins the code
constants to it. v1 chose θ=0.8 / margin=0.5 (coverage 0.953 = 61/64 routable, precision 1.000).

**S8 — Write every gate failing before the code exists; spec the judge with its authority bar.**
Do: all 12 gates land red first — the build turns them green. The judge ships as a
contract-pinning stub: rubrics versioned, verdicts carry **no authority until TPR ≥ 0.9 AND
TNR ≥ 0.9** on a 20-row human-labeled slice (bare agreement is rejected — an always-"faithful"
judge scores ~85% on an imbalanced slice). Calling the uncalibrated judge raises; gate 5 asserts
the guard itself.
Done when: gates fail for the right reason (assertions, not ImportErrors), then go green with the
implementation.

## 3. The recurring loop — operating the live system

### 3.1 Harvest (weekly, and before any routing release)

Three mines, each pre-labeled by where users actually went:

| Mine | Extract | Becomes |
|---|---|---|
| Decision log: `FallThrough` turns the classifier then routed confidently | the query + classifier route | stage-0 rule candidates (the free layer should own what the paid layer keeps handling) |
| Decision log: clarify turns + user's follow-up | the resolved intent | new follow-up / ambiguous rows |
| Source systems: Jira ticket titles, Confluence search queries, Omni saved-report names | phrasing per route | vocabulary candidates, route labeled by revealed behavior |

### 3.2 Escapes (immediately, before the fix ships)

Any production mis-route, leak, or ungrounded answer becomes a golden row **first** — with
`source` naming the incident — then the fix is built against it. 100%-review classes (spec §8):
guardrail-intervened, entitlement refusals, injection-flagged turns, any F3–F6 escape.

### 3.3 Re-coding sessions (triggered, not scheduled)

Triggers: first batch of live traces · every prompt/model change · an escape cluster the codebook
doesn't fit · onboarding a new stream. Procedure: reviewers label traces with the §4 codebook; new
codes accumulate; re-run the axial pass. Classes may split or merge — the 3–7 bound holds. **A new
class is not real until it has an instrument and a gate.** The class list is provisional by design;
the protocol + codebook are the durable asset.

### 3.4 Golden-set upgrade protocol

1. New rows carry an honest `source` (`omni-logs-2026q1`, `jira-mined`, `escape-INC-123`) —
   provenance of the data itself.
2. Label per S6 rules; genuinely ambiguous harvested queries become new `route: null` rows (they
   grow the fall-through spec, not the phrasebook).
3. Append-mostly: a row that ever caught a real failure is retired only by a reviewed change that
   says why.

### 3.5 Rule evolution protocol (the only way phrases enter the router)

1. Golden rows exist first (3.4). No row, no rule.
2. Carve the distinctive phrase: hits its rows, silent on every null row, collides with no other
   route's rows.
3. Default the new rule to tier B weighted — it must win the scoring contest. Tier A is reserved
   for phrases decisive in every harvested context. Shared surface words get a weak counterweight
   (the `t-weak-ticket` pattern) so contests stay real and measurable.
4. Replay before promote: re-run `route_stage0` with the candidate table over the decision log's
   queries and diff old vs new routing. (No committed script yet — a ~20-line loop over the JSONL;
   first person to need it, commit it as `router/replay.py`.)
5. Re-run the sweep; commit the new report. Gate 1 forces the constants to match it.
6. Gates 1/2/3 green (precision ≥ 99%, per-path accuracy no regression, null rows still fall
   through). A greedy phrase dies here, in CI.
7. Ship as a release; then verify in the log: new rule ids firing, classifier volume down. That
   delta is the business case — fast-path coverage up at held precision.

### 3.6 Judge lifecycle

1. **Calibrate before authority:** 20-row human-labeled slice (1-page labeling guide, 3–5 worked
   annotations, uncertain cases tracked separately). Authority requires TPR ≥ 0.9 AND TNR ≥ 0.9.
2. Only then does gate 5 switch from asserting-the-guard to enforcing faithfulness ≥ 0.95.
3. Recalibrate on any judge-prompt or judge-model change (each is a release), and spot-check a
   fresh labeled slice periodically for drift.
4. Standing limit: the judge never sole-gates F3/F4/F5. Deterministic probes own those forever.

### 3.7 Release + red-gate protocol

Per release: gates green offline · E2E smoke via the CLI (TC-01 happy path, TC-08
`--inject-timeout`) · if routing was touched, the sweep report diff is in the change.
**When a gate is red:** the release stops. If the gate itself is judged wrong, fix it by a
reviewed, versioned change to the row label or the bar — with the reasoning in the change. Silent
overrides, skipped tests, and hand-edited thresholds are prohibited. A metric is an opinion; a gate
is a policy.

## 4. Ownership and cadence

| Change | Who may make it | Required evidence |
|---|---|---|
| Rule table / golden rows | any engineer, week one | protocol 3.5 — gates do the protecting |
| THRESHOLD / MARGIN | nobody by hand | sweep output only; gate 1 pins it |
| Prompts, model config | engineer + review | gates green; it is a release |
| Judge rubric | calibration owner | recalibration run attached |
| Taxonomy (split/merge/new class) | team coding session | codebook acceptance ≥ 80%; new class ⇒ new gate |
| Gate bars / row relabels | reviewed change only | written reasoning (3.7) |

Cadence: **per release** — gates + E2E smoke. **Weekly** — harvest pass (3.1). **Quarterly, and at
every stream onboarding** — source-system mining + a re-coding session (3.3), even if no trigger
fired, as a drift check.

## 5. Anti-patterns — the five sins

1. **Silent threshold edits.** The dial has receipts or it has nothing — thresholds are sweep
   outputs (gate 1 enforces this).
2. **Phrases before rows.** A rule with no golden rows is folklore in regex form; it will rot
   unmeasured.
3. **Trusting an uncalibrated judge.** Agreement ≠ accuracy on imbalanced data; TPR/TNR or no
   authority.
4. **Fetch-then-filter.** Entitlement runs before retrieval; the model cannot leak what it never
   receives. Never "fix" a leak by censoring the answer.
5. **Freezing the taxonomy.** The golden set defends the failures we named; only the re-coding
   loop discovers the ones we didn't. A taxonomy that never changes is a taxonomy nobody is
   checking.
