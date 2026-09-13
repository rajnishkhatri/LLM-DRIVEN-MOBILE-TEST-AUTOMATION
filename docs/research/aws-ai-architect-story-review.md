# AWS-AI Architect Explainer — Stage-7 Code Review (2026-08-27)

**Reviewed artifact:** `docs/architecture/explainers/aws-ai-architect-story.html` ("The Loop, Left Running"; 111.8 KB of a 250 KB cap).
**Baseline:** `docs/sdd/specs/aws-ai-architect-story.spec.md` (IMPLEMENTED 2026-08-27), `docs/sdd/plans/aws-ai-architect-story.plan.md`, `docs/sdd/plans/aws-ai-architect-story.tasks.md`, brainstorm `docs/research/aws-ai-architect-explainer-brainstorm.md` §3 (14-row currency delta).
**Method:** static scan (document shell, `href`/`src`, ids/anchors, badge pairing, `data-delta` 1–14, file size, theme tokens) plus an HTTP-served browser pass (charset, quirks mode, 300px overflow, hash targets, figure lane labels). Findings first. No edits were made to the explainer.
**Verdict:** **not merge-ready as a published HTML page.** Two highs block C4/HTTP publication and AC-3. The narrative spine, badge pairing, dual-lane figures, and zero-external-URL self-containment are otherwise in good shape.
**Companion review:** [aws-ai-architect-story-review-multiagent.md](aws-ai-architect-story-review-multiagent.md) — an independent multi-agent pass over the full change-set (15 findings; overlap reconciled in its §4).
**Counts:** 2 High · 5 Medium · 3 Low · 0 security / XSS.

---

## 1. Findings (severity order)

| Sev | ID | Location | AC | Finding |
|---|---|---|---|---|
| High | H1 | `aws-ai-architect-story.html:1` | FR-1 / C4 | No charset or doctype — UTF-8 mojibake over HTTP, quirks mode |
| High | H2 | `html:308–312`, `:441`, `:1067` | AC-3 | `nowrap` unverified chips overflow the body under 375px |
| Medium | M1 | `html:1164` | AC-5 / FR-8 | Scorecard restates the P8 2× cache-write figure as verified-2026 |
| Medium | M2 | `html:1158–1168` | C1 / AC-9 | Scorecard counts five compressed topics, lists six, and misroutes two |
| Medium | M3 | `html:588` | AC-10 | `data-delta="3"` is on the prefill replacement, not on caching |
| Medium | M4 | `html:835–838` vs `:1168` | AC-9 | Part V has no decision-map backref; protocol stack has no honest card |
| Medium | M5 | tasks T9 · not in repo | Verification method | The static verifier that greened the ACs is not checked in |
| Low | L1 | `html:124–125` | AC-9 / FR-12 | Sticky legend has no `scroll-margin` on hash targets |
| Low | L2 | `html:481` vs `:441` | Honesty | F2 caption says prices live only on the model card |
| Low | L3 | `html:1043`; F2 `:455` | a11y / AC-8 | D1 empty header cell; F2 uses the envelope wash on Sonnet |

### H1 — Missing charset and doctype; UTF-8 mojibakes over HTTP

The file opens on `<title>` with no `<!DOCTYPE html>`, `<html lang>`, `<head>`, or `<meta charset="utf-8">`. Served over HTTP (`python3 -m http.server`; the C4 Artifact is also HTTP), the document reports `characterSet: windows-1252` and `compatMode: BackCompat`. The masthead renders as `ENGINEERING & PRODUCT Â· …` and `AWS â€” one tool loop`. Figure titles and the footer are similarly garbled.

`file://` often sniffs UTF-8, which is why T10 looked clean. o7-v2 has the same document-shell omission; this page is far more Unicode-heavy (middots, em-dashes, ×, arrows), so it fails harder.

**Fix:** prepend a standard shell — `<!DOCTYPE html>`, `<html lang="en">`, `<meta charset="utf-8">`. The existing viewport meta can stay.

### H2 — AC-3 fail: nowrap unverified chips overflow the body

`.unverified { white-space: nowrap }` plus uppercase and letter-spacing produces chips 305px and 353px wide. At a 300px viewport, `document.documentElement.scrollWidth` was 406 — body horizontal scroll. `.delta-pair` does not clip (337 vs 325 inner width); `.fig-card` and `.table-wrap` already self-contain with `overflow-x: auto`. AC-3 requires no body h-scroll at ≤375px.

**Fix:** drop `nowrap` on `.unverified` (and consider it on `code`), or wrap those spans so they break. Keep overflow-x only on wide figures and tables.

### M1 — Scorecard restates the P8 2× figure as verified-2026

The caching scorecard row says “writes 1.25×/2×” under a **verified 2026** badge. The footer lists the 2× one-hour cache-write multiplier as unverified and only marked on card D4. Repeating the figure without `.unverified` fails AC-5 for that occurrence.

### M2 — Scorecard counts five compressed topics, lists six, and misroutes two

C1 compressed RAG, caching, guardrails, observability/FinOps, and data-retention. The table adds **Protocol stack** (delta row 14), which already has full-depth Part V, and points it at **D5 Orchestration** (Harness vs Strands vs raw loop) — the wrong decision. Observability / FinOps points at **D7 evals**; invocation-logging-off and chargeback are not an eval-tier choice.

### M3 — `data-delta="3"` is on the prefill replacement, not on caching

Part II’s `.now` block (HTTP 400 on assistant prefill / tool-schema extraction) is tagged `data-delta="3"`. Row 3 is prompt caching; row 1 is prefill. Caching is correctly on D4. The extra tag makes the row-by-row coverage index lie — the check the tasks file treats as AC-10’s proof.

### M4 — Part V has no decision-map backref; protocol stack has no honest card

AC-9 requires each card linked from/to its motivating spine Part. Parts I, IV, VI, VII do this. Part V (protocol stack, row 14) ends on an envelope beat with no forward link, and the scorecard then dumps that row onto D5. There is no protocol-stack card to point at — the routing is invented.

### M5 — The static verifier that greened the ACs is not checked in

`test_gate = <none>` is a spec choice, but T9’s `verify_story.py` lived in a session scratchpad. Charset, body overflow, the `data-delta="3"` mis-tag, and the unmarked scorecard 2× would all have been catchable. Future edits can regress AC-2/3/4/5/6/8 with no ratchet.

### L1 — Sticky legend has no scroll-margin on hash targets

`.key` is `position: sticky; top: 0` and measured 89px tall (~129px at 300px). `#d-*` / `h2` have no `scroll-margin-top`. Native hash jump in the review UA left a gap (not occluded), but there is also no `:focus-visible` rule. Easy miss when a UA snaps flush to start.

### L2 — F2 caption says prices live only on the model card

Figcaption: “Prices live in the decision map (model card) with their unverified markers.” Part I’s delta-pair already prints Haiku/Sonnet/Opus/Fable list prices with a marker. The caption is false as written.

### L3 — D1 empty header cell; F2 uses the envelope wash on Sonnet

D1’s trade-off table starts with an empty `<th>` and no `<thead>` / `<caption>`. F2 is the enumerated single-lane exception, but the Sonnet 5 tile is `fill: var(--det-wash); stroke: var(--det)` — the envelope color on a comparative model chip. Readers who just learned the two-lane grammar will misread it.

---

## 2. Spec gates

| AC | Result | Note |
|---|---|---|
| AC-1 JS-off | Pass | Zero `<script>`; content is in document order |
| AC-2 `file://` / no external `href`/`src` | Pass | All `href`s are in-page `#` anchors |
| AC-3 ≤375px no body h-scroll | **Fail** | Confirmed at 300px (`docW` 406) |
| AC-4 superseded ⇒ adjacent `.now` | Pass | 8 delta-pairs; legend chip is the named exception |
| AC-5 P8 unverified markers | **Fail (partial)** | 5 markers on Part I / D3 / D4; scorecard 2× unmarked |
| AC-6 15-word shingle | Not re-run | T9 claimed clean; verifier not in repo |
| AC-7 sticky two-grammar legend | Pass | Only sticky; both themes tokenized |
| AC-8 two-lane SVG token fills | Pass | F2 enumerated exception; F1–F9 labeled |
| AC-9 nine cards + bidirectional links | **Fail (partial)** | Cards exist; Part V / protocol stack unbound |
| AC-10 14 delta rows | Pass with a lie | 1–14 present; row 3 also tagged on prefill |
| AC-11 seven Parts + envelope beats | Pass | Beats close I–VII; backrefs inside beats |
| AC-12 size + three-block theme | Pass | 111.8 KB; tokens in all three blocks |
| AC-13 seam + two-book footer | Pass | Masthead seam; About names both books |
| AC-14 `log.md` newest-first | Pass | 2026-08-27 entry names file, o7-v2, SDD |

---

## 3. What is solid

Dual-plane figures (amber model / teal envelope, F7 retired lane in dashed violet), the was/now pairing, still-true double badges, the nine ADR-shaped cards with default+deviate lines, P8 honesty in the footer, and zero network requests. No XSS surface, no secrets, no scripts. Architecture of the page matches the spec’s composite (D1 spine + D4 map + D5 lanes + D3 badges).

---

## 4. Suggested fix order

1. Document shell + charset (**H1**).
2. Let unverified chips wrap (**H2**).
3. Unmark or re-badge the scorecard 2× (**M1**); drop protocol stack from the compressed-topics table or give it a real card (**M2** / **M4**); move `data-delta="3"` off the prefill `.now` (**M3**).
4. Check the verifier into the repo next to the HTML if this page will keep evolving (**M5**).

Review only — the explainer was not changed in the review session.
