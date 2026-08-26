# Plan: CCAR-P Prep Guide — v3 review-fix pass

**Spec:** [`ccar-p-prep-guide-v3.spec.md`](../specs/ccar-p-prep-guide-v3.spec.md)
· **Predecessor plan:** [`ccar-p-prep-guide.plan.md`](ccar-p-prep-guide.plan.md)
· **Change class:** documentation deliverable — no code paths, no new
dependency, no ADR trigger (constitution check below).

## Strategy

`cp docs/ccar-p-prep-guide-v2.html docs/ccar-p-prep-guide-v3.html`, then apply
**six edit passes on v3 in dependency order**, cheapest-and-safest first so a
later pass never invalidates an earlier check:

```
P0 copy v2 → v3 (byte-identical baseline; establishes the v2 tic counts as the gate)
P1 integrity/correctness edits  (tier A — smallest, highest-priority, no answer-key change)
P2 answer-key conversions       (tier B — FR-V3-1: 2–3 items become tuning-correct)
P3 giveaway audit               (tier B — FR-V3-2: even option lengths across all 30)
P4 style / anti-slop pass        (tier C — FR-V3-6: the large diff; done last so counts are final)
P5 registration + Stage-4 analyze (pointers; re-run every AC probe on v3)
```

P4 runs last on purpose: it is the largest textual churn, and running it after
the answer-key work means the final em-dash/antithesis counts (AC-V3-9) are
measured on the finished prose, not a moving target. P1–P3 are surgical; P4 is
broad but meaning-preserving.

## File touchpoints

| File | Pass | Change |
|---|---|---|
| `docs/ccar-p-prep-guide-v3.html` | P0–P4 | new file; all six defect classes fixed |
| `docs/ccar-p-prep-guide-v2.html` | — | **read-only**, retained as review provenance |
| `cases/claude-certification/log.md` | P5 | pointer line → v3 (supersedes v2) |
| `docs/architecture/log.md` | P5 | 2–4 line entry: v3 review-fix pass |

## P1 — integrity/correctness fix map (v2 line anchors; located by content in v3)

| Defect | v2 anchor | Edit |
|---|---|---|
| Disclaimer scope (AC-V3-1) | ~2503 footer | extend "figures in the teaching text and gauntlets" → also **"and the exam-facts figures (item count, time, passing score, domain weights)"**; all illustrative/unverified. |
| Facts-panel label (AC-V3-1) | ~372–378 exam-facts table | add an inline caption/badge on the panel: "Illustrative — verify current policy on the official page." (Predecessor FR-10 intended the hedge; make it local, not only in the footer.) |
| Fail-closed dogma (AC-V3-2) | 1155–1156 callout + 1306 table row | add one clause: fail-**open** is correct where blocking legitimate traffic is the greater harm (critical-alert / medical-path example); keep fail-closed as the **default**. |
| "Riskier than no checks" (AC-V3-3) | 950 + 1107 table row ("highest-risk state") | drop "riskier than nothing"; recast as **"manufactures false confidence"** — a stale green measures the previous system wearing the current one's name. Keep the diagnosis, cut the overreach. |
| "Different model judging" absolute (AC-V3-4) | 953 + 1109 table row | soften to a strong best practice: an independent/different judge is stronger; same-family self-eval is **weaker, not invalid**. |
| Self-authority (AC-V3-4) | 398 "harder than the real exam"; 395/697/1475 + others "the exam loves/favorite" (9) | recast "harder than the real exam" as a design goal, not a verified fact; convert "the exam loves/favorite" → "a classic trap / commonly mis-answered" (≤2 residual). |

## P2 — answer-key conversion (FR-V3-1) · shortlist + design contract

**Target: 3 items** (min 2). **Method = re-author a slot, not flip a key.**
Take an existing slot (its position, domain tag, industry flavor) and rewrite
its *scenario and options* so tuning is honestly correct. **Never invert the
answer key on an item whose facts make mechanism correct** — that manufactures a
wrong answer. Verified against the item text at plan time: Gablewick (E, v2
2047) and the energy-retailer RAG (B, v2 1733) are **correctly mechanism** and
are **excluded** — their lessons stay intact. (My first shortlist named these;
reading the items corrected it.)

**Design contract for every re-authored item:**
1. The new stem carries the diagnostic detail that makes tuning proportionate:
   bounded/measured blast radius, reversible, low-stakes or non-regulated
   surface, single identified cause, and the architectural move demonstrably
   buys nothing here.
2. The correct (tuning) option is marked `data-remedy="tuning"`.
3. The mechanism/upstream option stays present as a **distractor or
   adversarial**, and its `why` **names the over-engineering** ("a real control
   applied where a parameter change is owed — new failure surface, no risk
   retired").
4. Per-domain tag, single/multi-select shape, 15-per-gauntlet count, and the
   ≥2-distractor/≥1-adversarial rule are all preserved.

**Three designs (fresh scenarios authored into re-authorable slots — slot
selection = least-unique existing items, confirmed at implement time):**
- **τ1 — cost/latency proportionality (ops/cost domain).** A working, in-SLA
  assistant; one report shows p95 latency crept +400 ms after the system prompt
  grew; single cause, reversible. Correct = trim the bloated prompt / cap
  `max_tokens` / raise cache TTL. Trap (adversarial) = stand up a model-router +
  async queue — re-architecting a bounded, single-cause, reversible regression.
- **τ2 — output-format quality (internal drafting domain).** An internal draft
  assistant: content correct, heading style inconsistent, some summaries too
  long; internal, reversible, low-stakes. Correct = add two few-shot exemplars +
  a length instruction, re-measure on the existing eval. Trap = deterministic
  post-processor + mandatory human sign-off gate — over-engineering a reversible
  style nit.
- **τ3 — retrieval recall knob (RAG domain), the deliberate contrast to the
  energy-retailer item.** Docs-QA over a **static, correctly-owned** corpus that
  IS the ground truth; it misses answers that *are* in the corpus because
  relevant chunks rank just below the top-k cutoff. Correct = raise top-k /
  adjust chunk overlap / tune the reranker threshold. Trap = fine-tune the model
  / add an agent — over-engineering a recall knob. **Pairs with 1733 as the
  "one detail away" lesson:** tuning is wrong there (live state), right here
  (static ground truth, a recall knob).

Excluded as targets: every safety/regulated-path item (veterinary dosing 2025,
hospital-billing 2256, claims/underwriting) and the two mechanism-correct items
above — their answer keys are right and stay.

## P3 — giveaway audit (FR-V3-2) · method

Spec-time scan flags **26/30** items with correct-as-longest and **7/30** with
the "…and make it standing practice" pattern. Method, item by item:
- Where correct is longest: **trim the correct option's prose** to mid-pack
  length (the rationale, not the option, carries the depth) — do not pad
  distractors into nonsense. Secondary: tighten an over-long distractor.
- Where correct wins by comprehensiveness: move the "…and make it standing
  practice" completeness into the **rationale**, leaving the option a peer-
  length choice.
- Re-run the option-length probe after each batch; **target correct-is-longest
  ≤ 6/30** and completeness-pattern ≤ 2 (AC-V3-6/7). The 3 converted items
  (P2) must not be their group's longest.

## P4 — style / anti-slop pass (FR-V3-6) · measurable targets

Sweep all seven rooms; break the `setup — em-dash aside — antithetical
punchline` cadence into plain declaratives where it repeats. Targets (grep on
v3, AC-V3-9):

| Tic | v2 | v3 target |
|---|---|---|
| em-dashes `—` | 797 | ≤ 438 (≥45% cut) |
| "X, not Y" antithesis | 158 | ≤ 95 (≥40% cut) |
| silent/quiet family | 44 | ≤ 26 |
| load-bearing | 14 | ≤ 5 |
| most expensive [X] | 6 | ≤ 2 |
| the exam loves/favorite | 9 | ≤ 2 (shared with P1) |

Strained metaphors to cut/replace: "a memo is a hope wearing a control's
clothes" (1848), "this room dresses like the trivia room" (613), and the
reviewer's "curating a corpse" / "gates dress for meetings" / "governance
demoted … to hope" family — keep at most one vivid metaphor per room.
**Invariant:** meaning, correct answers (except P2 items), diagrams, weights,
and the semantic color key are unchanged (AC-V3-10). SVG `<text>` em-dashes and
mono/code content are left alone — only prose em-dashes count toward the cut.

## Constitution check (`.cursor/rules/architecture-principles.mdc`)

Documentation-only change: no new abstraction (G1 n/a), spec-before-code holds
(this spec precedes any edit, A7), the plan proposes the *least* change that
satisfies the review (A1 — surgical passes, v2 chassis untouched). No ADR seam
touched → decision-log entry only, no ADR. `check_gate` (skill-sync) not
exercised — no skill surface written.

## Risks & mitigations

- **R1 — P2 introduces a wrong answer.** Mitigation: the design contract; only
  reversible/low-stakes stems converted; mechanism option kept with an explicit
  over-engineering rationale; regulated-path items excluded.
- **R2 — P4 flattens genuinely load-bearing emphasis.** Mitigation: keep the
  sharpest ~40% of antithesis; cut the metronomic remainder; targets are
  ceilings, not quotas — stop when the prose reads clean, not at an exact count.
- **R3 — P3/P4 accidentally edit a diagram, weight, or answer role.** Mitigation:
  AC-V3-10 diff check — answer-key role diff vs v2 limited to P2 items; weights
  still sum to 100; no `<svg>`/`<text>` prose churn.
- **R4 — style cut regresses JS-off readability or ≤375px reflow.** Mitigation:
  re-run v2's chassis checks on v3 (AC-V3-11) in P5.

## Stage-4 analyze (done in P5, before sign-off)

Re-run every AC probe on v3: the six tic greps, the option-length script, the
`data-remedy` count, the disclaimer/fail-open/stale string checks, weights-sum,
no-external-`http(s)`, ≤1 MB, ≤375px reflow, theme tokens. Baseline gate:
`check_gate` green (unaffected). Report the before/after table.
