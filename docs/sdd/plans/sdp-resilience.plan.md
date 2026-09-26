# Plan: `sdp-*` family — wave 1 (`sdp-lifecycle` + `sdp-resilience`)

**Status:** **DRAFT — awaiting PLAN-OK (owner gate).** No tasks, no implementation
until sign-off.
**Spec:** `docs/sdd/specs/sdp-resilience.spec.md` (**SPEC-OK 2026-09-13**).
**ADR:** `docs/architecture/adrs/tooling/sdp/0001-stand-up-the-sdp-tactical-patterns-skill-family.md` (Proposed, drafted with this plan).

## Shape (A1 — least machinery)

Two authored skill dirs under the `.cursor/skills` source of truth, projected to
`.claude/skills` by the **existing** `skill_sync` tool; the pattern knowledge is
**hand-distilled Markdown cards** (P1) in the member's own `references/`; **one**
new ~50-line stdlib lint for the card template (V5). No generator (P2 is
fast-follow), no IR (P3 deferred), no binding file (C7), no new runtime dependency.

```
.cursor/skills/
  sdp-lifecycle/
    SKILL.md                         router (3-key frontmatter; routing in description prose)
    evals/evals.json                 V1 family eval set (C6 format)
  sdp-resilience/
    SKILL.md                         member (Agent work / Human gate / Constraints)
    references/
      CircuitBreaker.md   (C1)       ┐ first three → freeze the template (AC-11)
      RetryBackoff.md     (C2)       │
      TimeoutsDeadlines.md(C7)       ┘
      Bulkhead.md         (C8)       ┐ then apply the frozen template
      Idempotency.md      (C9)       │
      LoadShedding.md     (C10)      │
      GracefulDegradation.md (C11)   ┘
tooling/sdp-card-lint/
  sdp_card_lint.py                   V5 (read-only, deterministic, stdlib)
```
Projections `.claude/skills/sdp-lifecycle/**` + `sdp-resilience/**` are **generated**
by `skill_sync fix` (never hand-authored — the ADR-0003 sibling discipline).

**G1 note (the abstractions).** Two: (a) **the `sdp` family/manifest node**, (b)
**the frozen card template**. What (a) buys: a tactical clinic `arch-*` lacks, plus
an addressable card layer consumers cite (§13) — and, because it is a manifest
node, it rides the existing drift guard for free. What (b) buys: consumers get a
stable section contract to project from; the P2 generator later has a proven schema.
**Simpler things rejected** (closed at Stage 1, recorded not re-litigated): W1
"agents just read the bundle Concepts" — a line-cited Concept is a fragile join and
carries no addressable id (§13); W2 "patch `arch-*`" — closed by C3, and `arch-*`
owns style/decision discipline, not intra-service mechanics (grep gap, Hs3).

## File touchpoints

| Op | Path | Why (FR) |
|---|---|---|
| NEW | `.cursor/skills/sdp-lifecycle/SKILL.md` | router (FR-1) |
| NEW | `.cursor/skills/sdp-lifecycle/evals/evals.json` | V1 eval set (FR-7) |
| NEW | `.cursor/skills/sdp-resilience/SKILL.md` | category skill (FR-2) |
| NEW | `.cursor/skills/sdp-resilience/references/{CircuitBreaker,RetryBackoff,TimeoutsDeadlines,Bulkhead,Idempotency,LoadShedding,GracefulDegradation}.md` | 7 owned cards (FR-4/5/6/8) |
| NEW | `tooling/sdp-card-lint/sdp_card_lint.py` | V5 card-template lint (FR-9) |
| EDIT | `tooling/skill-sync/manifest.toml` | add `[[family]] id="sdp"` (FR-10) |
| GEN | `.claude/skills/sdp-lifecycle/**`, `.claude/skills/sdp-resilience/**` | `skill_sync fix` projections (FR-10) |
| EDIT | `docs/skills/README.md` | family row (mece §2 do-regardless hygiene) — if the file exists; else skip and note |
| NEW | `docs/architecture/adrs/tooling/sdp/0001-*.md` | ADR, Proposed (FR-13) — **written now** |
| APPEND | `docs/architecture/log.md` | decision entry (FR-13 / AC-12) — **written now** |

## Manifest node (literal, to add)

```toml
[[family]]
id = "sdp"
source = ".cursor/skills"
members = ["sdp-lifecycle", "sdp-resilience"]
projections = [".claude/skills"]
```
Same shape as `arch`/`aws-ai` (Cursor source, Claude projection). One family entry;
later waves append members to the `members` list — a manifest edit, not code.

## Card template application (FR-5 / AC-11)

1. Distill C1/C2/C7 from the bundle Concepts into `references/` on the derived
   template shape (spec §"card template"), **adding the `id:` frontmatter field**.
2. **Freeze** the template from those three (this is the "after the first three,
   not before" step — the freeze is an implement-time act, gated by AC-11).
3. Apply the frozen template unchanged to C8/C9/C10/C11. Any section the four need
   that the three did not surface is a **template-amendment decision**, logged — not
   a silent per-card drift.
4. Cross-links C3/B3/B7 are named in `sdp-resilience/SKILL.md` as "cross-link, do
   not own" — no card authored (AC-6).

## V5 lint contract (FR-9 — minimal)

`sdp_card_lint.py <dir>` walks `*/references/*.md`; for each card asserts:
(1) frontmatter carries a non-empty `id`; (2) a `## Trade-offs` section exists;
(3) a `## Sources` section exists; (4) an intro paragraph (definition+motivation)
precedes the first `##`. Exit 0 clean; exit 2 with one `CARD <path> MISSING <element>`
line per violation; exit 1 usage. Read-only, stdlib, deterministic sorted output —
the `okf_lint.py`/`skill_sync.py` house form. **Not** bound as a gate (the single
`check_gate` slot is skill-sync); V5 runs in implement + convergence as a named
command.

## arch-style handoff + sdp↔sdd disambiguation (FR-4 / FR-11)

Both live entirely in `description` prose + the router's handoff section (there is
no trigger field — AC-15). The router/member descriptions carry: the resilience
trigger utterances; `Routes to:` (router only); a **"Do NOT use for architecture
STYLE / how many quanta / monolith-vs-distributed — hand off to arch-style"** clause;
and a **"Not for the SDD lifecycle (sdd-*)"** clause. When a style fact is needed in
a card, cite `arch-style/references/style-selection.md` as FACT — never re-run the
four determinations (the E-card discipline, e.g. `Monolith.md:61`).

## Order (Stage-3 task seeds — verification mapped 1:1 to ACs)

- **T1 — Family births.** Add the manifest node; scaffold both `SKILL.md`s
  (descriptions with routing + boundaries, no cards yet); `skill_sync fix` →
  `check` exit 0. *Verify:* AC-7, AC-15, AC-16.
- **T2 — Triad + freeze.** Distill C1/C2/C7; freeze the template; write
  `sdp_card_lint.py`; lint green on 3. *Verify:* AC-3, AC-11, AC-17 (on 3).
- **T3 — Complete the 7.** Apply the frozen template to C8/C9/C10/C11; name the
  C3/B3/B7 cross-links; V5 green on 7; every card self-contained. *Verify:* AC-4,
  AC-6, AC-14, AC-17 (on 7), AC-13 (seam anchors present).
- **T4 — Entry + handoff + disambiguation.** Finalize E2/E4 bypass wording and the
  arch-style/sdd boundaries. *Verify:* AC-1, AC-2, AC-5, AC-9, AC-10.
- **T5 — V1 evals.** Author `evals/evals.json` (the 7 required cases); run
  `with_skill`; record in-bucket vs bucket-hop for the T2b killing-test. *Verify:*
  AC-8 (+ re-exercises AC-1/2/5/9/10).
- **T6 — Hygiene + gates.** `docs/skills/README.md` row; re-run `check_gate` + OKF
  lint green; confirm the log/ADR are in place. *Verify:* AC-12, AC-16.

TDD posture: for the script (V5) red-first per the repo norm; for the skills/cards,
the V1 evals + V5 lint are the executable checks a task closes against.

## Constitution cross-check (`.cursor/rules/architecture-principles.mdc`)

The bound constitution is the thin 5-part **card contract** (`:24` definition+
motivation+example/diagram · `:27` trade-offs on every decision · `:28` cite
well-known sources), enforced by AC-17 + V5. **There is no "8 invariants" list and
no ask-first list in this file** (spec C-const) — the ask-first ADR trigger is
sourced from the SDD convention + the handover §2 ruling, and is honored by writing
ADR 0001. No invariant machinery exists in this repo to violate beyond the card
contract; decision-log duty is discharged now (AC-12).

## Risks / notes

- **T2b is an untested bet.** If real resilience symptoms hop job buckets, the
  job-shaped cut is wrong. Not resolved by this plan — *instrumented*: AC-8 is the
  killing-test; a red result routes to revisiting T2a / T2-defer at skill #2, not to
  reworking wave 1.
- **ADR seam vs the turn-end hook.** The ADR lands in the **new** seam
  `docs/architecture/adrs/tooling/sdp/`, not the bound `adr_home`. If the workspace
  turn-end decision-record reminder keys strictly on `adr_home`, it may not detect
  this ADR — flagged for the owner; the ADR + log entry are written regardless.
- **`docs/skills/README.md`** may or may not exist; T6 edits it if present, else the
  family row is skipped with a note (non-blocking hygiene).
- **No runtime dependency, no new gate binding.** `check_gate` stays skill-sync;
  V5 is a standalone command; `test_gate` stays `<none>` (V1 evals are the gate).
