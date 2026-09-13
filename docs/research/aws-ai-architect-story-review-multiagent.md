---
type: analysis
title: 'SDD Stage 7 — Multi-agent code review: AWS-AI architect explainer change-set'
description: >-
  Fifteen confirmed findings from a ten-angle multi-agent review (finders →
  1-vote adversarial verify with mutation testing → gap sweep) of the full
  aws-ai-architect-story change-set — the HTML explainer, the SDD artifacts,
  the new claude-architect-foundation bundle, and the registration edits.
tags: [sdd, review, aws, bedrock, claude, explainer, okf]
---

# AWS-AI Architect Explainer — Stage-7 Multi-Agent Review (2026-08-27)

**Reviewed change-set:** the full uncommitted set — `docs/architecture/explainers/aws-ai-architect-story.html` ("The Loop, Left Running", 111.8 KB), the SDD triplet (`docs/sdd/specs/aws-ai-architect-story.spec.md`, `.plan.md`, `.tasks.md`), `docs/research/aws-ai-architect-explainer-brainstorm.md`, the new `cases/claude-architect-foundation/` bundle (14 files), the registration edits (`.okf/binding.toml`, `docs/CONVENTIONS.md`, `docs/architecture/log.md`, `cases/aws-ai/log.md`, `docs/skills/okf-curator-instructions.md`), and the out-of-repo gate `verify_story.py` (session scratchpad).
**Baseline:** the spec's AC-1…AC-14 + C1…C4, brainstorm §3 (14-row currency delta), `docs/CONVENTIONS.md`, and the o7-v2 / ccar-p-v3 house precedents.
**Method:** ten independent finder angles (line-by-line, removed-behavior/AC audit, cross-file tracer, language pitfalls, verifier-fidelity, reuse, simplification, efficiency, altitude, conventions) → dedup → 1-vote adversarial verification (including **mutation testing** of the gate: synthetic violations run through the real `verify_story.py`, and live browser measurement of the page) → one fresh gap-sweep finder. Extra-high recall; ~35 candidates; 15 findings survived, all **CONFIRMED**.
**Companion review:** [aws-ai-architect-story-review.md](aws-ai-architect-story-review.md) — an independent browser-focused pass from a parallel session (2 High · 5 Medium · 3 Low). Reconciliation in §4; neither record supersedes the other.
**Consumed by:** Stage 9 (`sdd-converge`) gap classification. Review only — no edits were made to the change-set.

**Verdict:** not merge-ready. The chassis is sound (anchors resolve, no duplicate ids, token values match the o7-v2 anchor exactly, the shingle scan catches planted verbatim text, all nine cards cross-link both ways), but the page carries live honesty-grammar defects, two rendering defects the static gate cannot see, and the change's verification evidence rests on artifacts that die with a temp directory.

---

## 1. Findings (severity order, all CONFIRMED)

| # | Location | Category | Finding |
|---|---|---|---|
| 1 | `html:693`, `:588` | correctness | Two `data-delta` anchors mislabel their rows: 693 tags memory/context prose as row 11 (evals); 588 tags row-1 prefill content as row 3 (caching) — rows 3-lite/11-lite are not covered where the spec's structure table places them |
| 2 | `html:1164` | correctness | Scorecard caching row repeats the P8 2× 1h cache-write multiplier with no `.unverified` marker under a teal verified-2026 badge (FR-8/AC-5 are per-occurrence; card D4 carries the marker this row lacks) |
| 3 | `html:311` (CSS), `:1067` | correctness | `.unverified { white-space: nowrap }` overflows the 375 px viewport (measured `scrollWidth` 392) — AC-3 fails live; the static gate is blind to layout |
| 4 | `html:1` | correctness | No `<!DOCTYPE html>`, no `<meta charset>` — quirks mode (`BackCompat` confirmed) + windows-1252 mojibake risk on the canonical `file://` read |
| 5 | `cases/claude-architect-foundation/aws-claude/prompt-engineering.md:1` | correctness | 72 KB raw course dump left in the declared bundle: no frontmatter (the repo's only lint WARN), uncataloged 11th file contradicting log.md's "split into 10 Concepts", and an LLM-directed `<critical>` instruction block now swept into `knowledge_globs` (prompt-injection-shaped) |
| 6 | `html:1158` | correctness | Scorecard prose says "Five topics were deliberately compressed"; the table has six rows, and the sixth (Protocol stack, row 14) got full spine treatment in Part V — both the count and "whole treatment" are false |
| 7 | `html:125` | correctness | Sticky `.key` legend (~89 px at 375 px) with zero `scroll-margin-top` anywhere — every in-page anchor jump lands its target under the legend |
| 8 | `docs/architecture/log.md:10` | altitude | The gate (`verify_story.py`), the ten research dossiers, and the AC-10 content map live only in a session scratchpad (absolute paths hard-coded) while spec/tasks/log record their green as durable evidence — vs the ccar-p-v3 precedent of committing the T-AUDIT gate |
| 9 | `verify_story.py:87` | correctness | Mutation-confirmed honesty false-greens: AC-4 never checks the pair contains a `.now`; the legend exemption substring-matches any ancestor class containing "key"; AC-8 misses `style=` fills, `stop-color`, named colors, `rgb()`; the F2 exemption keys on aria-label substrings ("ladder"/"endpoints") |
| 10 | `verify_story.py:158` | correctness | Mutation-confirmed structural false-greens: AC-2 URL scan evadable (case, unquoted, protocol-relative `//`, `@import`); AC-11 passes trailing non-beat asides and needs the exact byte order `<section class="part" id="part-N">`; AC-12 never checks the dark block sits in `@media` and reads only the first `<style>`; the shingle scan has no corpus floor (empty glob → vacuous green) and no `encoding=` |
| 11 | `docs/sdd/plans/aws-ai-architect-story.tasks.md:26` | spec-conformance | AC-10's required "row-by-row checklist in the tasks file" does not exist — only "covered = anchors 1–14", which is exactly the shortcut that let finding 1's mislabels count as coverage |
| 12 | `docs/architecture/log.md:10` | correctness | Log says the private Artifact was "published at converge per spec C4"; T12 published it during implement (pre-review), and no artifact URL is recorded anywhere in the repo despite T12's "link delivered" criterion |
| 13 | `html:1035` | correctness | F9's caption puts the context decision in the amber model lane; the scorecard's RAG/KB and caching rows declare the teal envelope as lane owner — the page's own epistemic grammar contradicts itself |
| 14 | `docs/skills/okf-curator-instructions.md:101` | conventions | The Routine-1 template names undeclared `cases/claude-architect-foundation/` as a declared-bundle home (line 26 has the inverse granularity drift); the parent's index.md cites a "bundle-of-bundles" convention `docs/CONVENTIONS.md` never defines, and the claude-certification precedent points the other way |
| 15 | `docs/skills/okf-curator-instructions.md:51` | altitude | Bundle registration is hand-copied in five spots across three files with no drift guard (skill-sync's manifest covers none of them) — this diff already produced the line-26 vs line-101 drift |

Fix-order note: 3, 4, 7 are mechanical page fixes; 1, 2, 6, 13 are content edits; 5 is delete-or-catalog; 8 + 9 + 10 resolve together by committing a repaired verifier; 11, 12, 14, 15 are record/registration edits.

## 2. Refuted candidates (do not re-litigate)

- **Part I badge + marker stacking (`html:441`)** — a verified-2026 badge and an inline unverified marker on the same paragraph is the spec-mandated pattern (FR-5 + FR-8 jointly force it); the marker sits adjacent to the exact figures it disclaims. The defect pattern is finding 2 (badge *without* marker), not this.
- **Footer "10 Concepts" (`html:1174`)** — internally accurate: it counts the cataloged Concepts and discloses the dump in the same sentence.
- **"`check_gate` doesn't exist"** — it resolves to `python tooling/skill-sync/skill_sync.py check` (exit 0, "6 families, 0 drifted").
- **"24 bundle files" miscount** — the wrong count appears only in ephemeral session notes, not in any repo file (actual corpus: 25).

## 3. Below-threshold observations (recorded for a cleanup batch, not findings)

- Dead CSS in the page: `.pull`, `.kicker`, `.wrap`, `.lane-pill.llm`, and tokens `--pass`/`--fail` defined in all three theme blocks but never referenced.
- ~17 KB of repeated presentational SVG attributes (825 occurrences) plus seven byte-identical per-figure `<marker>` defs — a shared `figure svg text` rule + one shared marker covers them (bytes count against the 250 KB cap).
- `verify_story.py` dead code: the `part_children` parser subsystem (self-contradictory `tag in (..., "div", ...) and tag != "div"`), `warnings`, `superseded_badges`, `hits`; AC-2 is also checked twice with divergent semantics.
- `aria-label` on the role-less `div.key` (line 354) is ignored for generic elements — the page's only legend has no accessible name.
- Anchor-coverage dilution (PLAUSIBLE tier): `html:936` tags mostly row-11 content as row 12; row 6's quota-burndown material rides the row-1 anchor at `:496` while the row-6 card D2 omits it.
- `html:581` "Four of the ten course Concepts lean on that pattern" vs the bundle log's three named prefill-dependent Concepts (PLAUSIBLE — hinges on whether tool-use.md "leans on" a pattern it cites only to replace).
- The brainstorm's P1 premise audit ("verified: 12 md each, ~42 KB") never matched the tree (13 files, ~140 KB with the dump) — resolves with finding 5.

## 4. Reconciliation with the companion review

Overlaps (independent double-confirmation): companion H1 ≈ finding 4 (charset/doctype; companion adds HTTP-served mojibake evidence), H2 ≈ 3 (nowrap overflow; measured at 300 px and 375 px respectively), M1 ≈ 2 (scorecard 2× unmarked), M2 ≈ 6 (five-vs-six; companion adds that Protocol stack and Observability/FinOps rows misroute to the wrong decision cards D5/D7), M3 ≈ the `:588` half of 1, M5 ≈ 8 (verifier not checked in), L1 ≈ 7 (scroll-margin).

Companion-unique (carry into converge alongside the 15): **M4** — Part V has no decision-map backref and the protocol stack has no honest card to route to; **L2** — F2's caption claims prices live only on the model card while Part I also prints them; **L3** — D1's trade-off table opens with an empty `<th>` (no `<thead>`/`<caption>`), and F2's Sonnet 5 tile wears the envelope wash.

Unique to this review: the `:693` row-11 mislabel (1), the bundle-dump/instruction-block cluster (5), both mutation-confirmed gate false-green sets (9, 10), the AC-10 checklist absence (11), the C4 timing/URL misrecord (12), the F9 lane contradiction (13), and both registration findings (14, 15).
