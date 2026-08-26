# Tasks: CCAR-P Prep Guide — v3 review-fix pass

**Spec:** [`ccar-p-prep-guide-v3.spec.md`](../specs/ccar-p-prep-guide-v3.spec.md)
· **Plan:** [`ccar-p-prep-guide-v3.plan.md`](ccar-p-prep-guide-v3.plan.md)
Legend: `[dep: …]` prerequisite · `∥` may run in parallel · each task ends with
its pass/fail check mapped to an AC.

---

### T0 — Baseline (P0)
`cp docs/ccar-p-prep-guide-v2.html docs/ccar-p-prep-guide-v3.html`.
**Pass/fail:** `diff` of the two files is empty; record the v2 tic counts and
option-length report (T-AUDIT) as the frozen baseline.

### T1 — Disclaimer scope + facts-panel label (P1) [dep: T0]
Extend the footer honesty clause to name the exam-facts figures; add an inline
"illustrative — verify on the official page" badge on the exam-facts panel.
**Pass/fail (AC-V3-1):** footer clause matches `exam-facts|item count|passing
score|domain weights`; facts panel contains the inline label.

### T2 — Fail-closed → default-not-law (P1) [dep: T0] ∥ T1
Edit the fail-closed callout (v2 1155–1156) and table row (1306): add the
fail-open-is-correct-when-blocking-is-costlier clause with a critical-alert /
medical-path example.
**Pass/fail (AC-V3-2):** the fail-closed passage contains a fail-open caveat;
fail-closed framed as default.

### T3 — Stale checks → "false confidence" (P1) [dep: T0] ∥ T1
Passage 950 + table row 1107: remove any "riskier than no checks / highest-risk
state" overreach; recast as "manufactures false confidence."
**Pass/fail (AC-V3-3):** no "riskier than" / "riskier than nothing" survives in
the stale-eval context; "false confidence" present.

### T4 — Judge-model + self-authority calibration (P1) [dep: T0] ∥ T1
(a) Soften "different model judging" (953, 1109) to weaker-not-invalid. (b)
Recast "harder than the real exam" (398) as a design goal; convert "the exam
loves/favorite" (9 sites) → "a classic trap / commonly mis-answered."
**Pass/fail (AC-V3-4):** "the exam loves/favorite" count ≤ 2; no factual
"harder than the real exam" claim; judge guidance non-absolute.

### T5 — Answer-key re-authoring ×3 (P2) [dep: T1–T4]
**Re-author 3 least-unique existing slots** (not flip keys) into the plan's
three tuning-correct designs (τ1 cost/latency, τ2 output-format, τ3 retrieval
recall knob): new stem with the diagnostic detail that makes tuning
proportionate; tuning option correct + `data-remedy="tuning"`; mechanism option
kept as distractor/adversarial with an over-engineering rationale; preserve
tag, select-shape, count, and the ≥2-distractor/≥1-adversarial rule. **Do not
touch** the mechanism-correct items 1733 / 2047 or any regulated-path item.
**Pass/fail (AC-V3-5):** `data-remedy="tuning"` on ≥2 (target 3) correct
options; each demoted mechanism option's `why` names the over-engineering;
per-domain tally and 15-per-gauntlet unchanged (T-AUDIT).

### T6 — Giveaway audit, all 30 items (P3) [dep: T5]
Trim correct options out of the "longest" slot; move completeness ("…and make
it standing practice") into rationales. Re-run T-AUDIT after each batch.
**Pass/fail (AC-V3-6/7):** correct-is-longest ≤ 6/30; completeness-pattern ≤ 2;
no converted (T5) item is its group's longest; every option keeps a rationale.

### T7 — Style / anti-slop pass, seven rooms (P4) [dep: T5, T6]
Break the repeated antithesis/em-dash cadence into declaratives; cut the
flagged metaphors (≤1 vivid metaphor/room). Prose only — leave SVG `<text>`,
mono, and code untouched.
**Pass/fail (AC-V3-9):** grep on v3 — em-dashes ≤438, "X, not Y" ≤95,
silent/quiet ≤26, load-bearing ≤5, most-expensive ≤2; named metaphors gone.
**Guard (AC-V3-10):** answer-role diff vs v2 limited to T5 items; weights sum
to 100; no diagram edits.

### T8 — Registration (P5) [dep: T7]
Repoint `cases/claude-certification/log.md` and add a `docs/architecture/log.md`
entry to v3 (supersedes v2). Keep the M1-atlas relative link; do not edit v2.
**Pass/fail (FR-V3-7):** both logs point at v3 with a supersedes note.

### T9 — Stage-4 analyze / sign-off (P5) [dep: T8]
Run T-AUDIT + all chassis checks (no external `http(s)` in loaded refs, ≤375px
reflow, theme tokens, ≤1 MB) on v3; produce the before/after table.
**Pass/fail (AC-V3-8/11):** every AC probe green; `check_gate` green
(unaffected). Present the table for owner acceptance.

---

## T-AUDIT — the verification script (re-run after T5, T6, T7, T9)

```bash
python3 - docs/ccar-p-prep-guide-v3.html <<'PY'
import re,sys,html
p=sys.argv[1]; s=open(p,encoding='utf-8').read()
prose=re.sub(r'<svg.*?</svg>',' ',s,flags=re.S)          # exclude diagram text
prose=re.sub(r'<(code|pre)[\s>].*?</\1>',' ',prose,flags=re.S)
def n(pat,txt=prose,fl=0): return len(re.findall(pat,txt,fl))
print("em-dashes         :",prose.count("—"),        "(≤438)")
print("X, not Y          :",n(r', not [a-z]'),        "(≤95)")
print("silent/quiet      :",n(r'silent|quiet',re.I:=0) if False else n(r'silent|quiet|silently|quietly',fl=re.I),"(≤26)")
print("load-bearing      :",n(r'load-bearing',fl=re.I),"(≤5)")
print("most expensive [X]:",n(r'most expensive [a-z]+',fl=re.I),"(≤2)")
print("exam loves/favorite:",n(r'exam.{0,4}(favorite|loves|love)',fl=re.I),"(≤2)")
print("data-remedy=tuning:",n(r'data-remedy="tuning"'),"(≥2)")
# option-length giveaway
blocks=re.findall(r'<ol class="opts">.*?</ol>',s,re.S)
orx=re.compile(r'<li class="opt" data-role="([^"]*)"[^>]*>(.*?)</li>',re.S)
def txt(h):
    h=re.sub(r'<span class="k">.*?</span>',' ',h,flags=re.S)
    h=re.sub(r'<p class="why">.*?</p>',' ',h,flags=re.S)
    return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',h))).strip()
long=comp=real=0
for b in blocks:
    o=orx.findall(b); roles=[r for r,_ in o]
    if 'correct|distractor|adversarial' in roles: continue
    real+=1; L=[len(txt(x)) for _,x in o]; ci=[i for i,(r,_) in enumerate(o) if r=='correct']
    if L and any(L[i]==max(L) for i in ci) and len(o)>2: long+=1
    if any(re.search(r'\band\b.*\b(standing|always|every|permanent|going forward)',txt(o[i][1]),re.I) for i in ci): comp+=1
print(f"correct-is-longest: {long}/{real} (≤6)")
print(f"completeness-and  : {comp} (≤2)")
print("weights sum 100   :", sum(int(x) for x in re.findall(r'(\d+)\s*%?\s*weight',s)) or 'check-manually')
print("external http(s)  :", len(re.findall(r'(?:src|href)="https?://',s)), "(0 for loaded assets)")
PY
```

## Two hard gates (per sdd-spec)
1. **SPEC-OK** — owner approves the spec (this package) before any edit. ← *here*
2. **PLAN/TASKS-OK** — owner approves plan+tasks before T5 (answer-key
   conversions), the only substantive-content step.
Then advance to **sdd-implement**.
