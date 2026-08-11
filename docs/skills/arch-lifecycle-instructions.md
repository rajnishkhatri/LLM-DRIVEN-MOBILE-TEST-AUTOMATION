---
type: runbook
title: Arch lifecycle — how to use in this workspace
description: >-
  Workspace-resolved instructions for driving the arch-* skills in
  LLM-DRIVEN-MOBILE-TEST-AUTOMATION (design repo for MTA / spine / O7).
tags: [architecture, lifecycle, instructions, cursor]
---

# Arch lifecycle — instructions for this workspace

Use this when you want to run the **architect workflow** (`arch-*`) in
`LLM-DRIVEN-MOBILE-TEST-AUTOMATION`. It is the short, path-resolved playbook.

| Need | Doc |
|---|---|
| Clone / provision skills | [../SETUP.md](../SETUP.md) |
| SDD how-to (spec-driven code/docs changes) | [sdd-lifecycle-instructions.md](sdd-lifecycle-instructions.md) |
| Full operator manual (all four families) | [sdd-usage-guide.md](sdd-usage-guide.md) |
| C4 diagram render (IR → D2 → lint) | [generating-architecture-diagrams/SKILL.md](generating-architecture-diagrams/SKILL.md) |
| Agent pointers | [../../AGENTS.md](../../AGENTS.md) |

**This repo is the design workspace** (ADRs, worksheets, components, risk). It
is **not** the Java spine/o1 delivery repo — `coding-rules` is not mounted here.

---

## 0. Before you start

1. Open **this folder** as the Cursor / Claude Code workspace root.
2. From repo root, confirm the gate (re-run `fix` only if drifted):

```bash
python3 tooling/skill-sync/skill_sync.py check
```

Expected: `SUMMARY: 5 families, 0 drifted, 0 shadow -> exit 0`.

3. Prefer a **fresh chat** after provisioning (skills register at session start).
4. Tell the agent to **load the skill** for the stage you are in (see below).
   Do **not** say “run the whole kata” in one shot unless you explicitly want
   provisional-gate mode — you hold every gate.

### Binding (already set — `.arch/binding.toml`)

| Key | This workspace |
|---|---|
| methodology_source | `<none>` (chapter cites may not resolve locally) |
| constitution | `.cursor/rules/architecture-principles.mdc` |
| worksheet_home | `.arch/worksheets/` |
| component_home | `.arch/components/` |
| adr_home | `.arch/adrs/` |
| risk_home | `.arch/risk/` |
| diagram_notation | `mermaid` |
| breadth_read_tool | `explore subagent` |
| `[roots] mobile-test-automation` | `docs/architecture/` |

Skill bodies: `.cursor/skills/arch-*` (Cursor SoT) and `.claude/skills/arch-*`
(Claude projection via skill-sync).

**Where artifacts land**

| Intent | Home |
|---|---|
| Real MTA / spine product design | `docs/architecture/` (`worksheets/`, `components/`, `adrs/`, `risk/` … under target slug) |
| Practice / throwaway kata (default binding) | `.arch/worksheets/<slug>/` etc. — or a disposable slug under `docs/architecture/` that you delete after |

Do **not** mutate real `mobile-test-automation` ADRs in a smoke unless you
explicitly opt in.

---

## 1. Which skill owns which stage

| Stage | Skill | You are here when… |
|---|---|---|
| Router / “what stage?” | `arch-lifecycle` | Starting a kata, reviewing a system, or lost |
| 1 Characteristics | `arch-characteristics` | Need −ilities / worksheet / top-3 |
| 2 Components | `arch-components` | Need logical component set + diagram |
| 3 Style / quanta | `arch-style` | Join of 1+2; monolith vs distributed; sync/async |
| 4 Decide (ADRs) | `arch-decide` | Significant decision with trade-offs on both sides |
| 5 Risk | `arch-risk` | Score risks / risk-storm after a design lands |
| 6 Validate | `arch-validate` | Diagram set + 9 intersections + governance |

Stages **1 and 2** may run in either order or in parallel; **3+** are sequenced.
New kata must **not** start at 3 (Accidental Architecture). Stages **4–6 recur**.

**Two modes**

- **Kata** (default): premises from the kata statement; you play stakeholders.
- **Review**: claims need `file:line` evidence; often enter at risk or validate.

---

## 2. Golden rules (short)

1. **One stage per turn** — agent drafts → **you** gatekeep → advance or loop.
2. **You own gates** — never auto-Accepted ADRs; never self-CHAR-OK.
3. **Trade-offs, not advocacy** — least-worst; spectrums, not coin flips.
4. **Why > how** — ADRs and worksheets record the why.
5. **Label multi-option picks** — `CHAR-OK`, `STYLE-OK` with variances, etc.
6. **Durable state in files** — under binding homes, not only chat.
7. **Style follows characteristics** — never lead with a fashionable style.

---

## 3. Copy-paste prompts (Cursor)

Paste one block at a time. Replace `<…>` placeholders.

### Router

```text
Load arch-lifecycle from .cursor/skills/. Using .arch/binding.toml (not
placeholders), summarize entry, the six stages, and artifact homes for this
repo. For: <one-line kata or “review mobile-test-automation”>.
Name the owning skill and the human gate before we advance. Do not start yet.
```

### Stage 1 — Characteristics

```text
Load arch-characteristics. Kata mode. Target slug: <slug>.
Domain: <short kata statement — users, requirements, constraints>.
Artifact home: <docs/architecture/ OR .arch/>.
Draft the ≤7 worksheet with objective measures, proposed top-3, clusters, and
STOP for CHAR-OK. Mark THROWAWAY if this is a smoke.
```

Your reply: `CHAR-OK` (optionally amend top-3 / driving list).

### Stage 2 — Components

```text
CHAR-OK. Load arch-components. One Figure 8-6 pass for <slug>.
Use the worksheet top-3. Write logical-components.md (roles, stories,
characteristic splits, mermaid). STOP for COMP-OK.
```

Your reply: `COMP-OK` or redirect (merge/split/reassign).

### Stage 3 — Style / quanta

```text
COMP-OK. Load arch-style. Run the four determinations for <slug>
(quantum count, data topology, sync/async, style). Score 2–3 candidates
against the driving characteristics. Write style-decision.md. STOP for
STYLE-OK — I will confirm each determination (or STYLE-OK = all four).
```

Your reply: `STYLE-OK` or variances per determination 1–4.

### Stage 4 — ADRs

```text
STYLE-OK. Load arch-decide. Account for every style handoff item
(Written / Merged / Deferred). Draft ADRs as Proposed under the binding
adr_home for <slug>. Surface first-use approval-criteria if missing.
STOP for ADR-OK — do not mark Accepted until I say so.
```

Your reply: `ADR-OK` (Accept) / revise / defer named ADRs.

### Stage 5 — Risk

```text
ADR-OK. Load arch-risk. Storm pass P1 on criterion: <e.g. availability>
using the container diagram. Blind lenses → median consensus → priced
mitigations. STOP for RISK-OK (I arbitrate scores and accept/reject mitigations).
```

Your reply: `RISK-OK` or overrides (`Issue=9`, `reject M3`, `cheaper M1`, …).

### Stage 6 — Validate

```text
RISK-OK. Load arch-validate. Produce C1/C2/C3 diagram set + nine-intersections
checklist + governance table from ADR Compliance rows. STOP for VALIDATE-OK —
sign-off is per intersection, not one global “looks good”.
```

Your reply: `VALIDATE-OK` or list intersection overrides.

### Presentation-grade diagrams (optional, after validate)

When you need linted D2/SVG (not just mermaid in the arch artifacts):

```text
Follow docs/skills/generating-architecture-diagrams/SKILL.md for
<target>. Fact-freeze IR; do not invent SLAs/vendors/counts. Lint must pass.
```

---

## 4. Artifact naming

| Kind | Path pattern (MTA root) | Default practice root |
|---|---|---|
| Characteristics worksheet | `docs/architecture/worksheets/<slug>/characteristics-worksheet.md` | `.arch/worksheets/<slug>/` |
| Style decision | `docs/architecture/worksheets/<slug>/style-decision.md` | `.arch/worksheets/<slug>/` |
| Validation report | `docs/architecture/worksheets/<slug>/validation-report.md` | `.arch/worksheets/<slug>/` |
| Logical components | `docs/architecture/components/<slug>/logical-components.md` | `.arch/components/<slug>/` |
| Diagram set | `docs/architecture/components/<slug>/diagram-set.md` | beside components |
| ADRs | `docs/architecture/adrs/application/<slug>/NNNN-….md` | `.arch/adrs/…` |
| Risk report | `docs/architecture/risk/<slug>/risk-report.md` | `.arch/risk/<slug>/` |

Product slug in this repo: **`mobile-test-automation`**.

Ask-first / significant decision → ADR via `arch-decide`. Worksheet = *what
matters*; ADR = *why we chose*.

---

## 5. Gate tokens you type

| Token | Meaning |
|---|---|
| `CHAR-OK` | Approve characteristics worksheet; unlock components |
| `COMP-OK` | Approve component set (this pass); unlock style |
| `STYLE-OK` | Approve all four determinations (or list variances) |
| `ADR-OK` | Accept Proposed ADRs (+ approval criteria if first use) |
| `RISK-OK` | Accept consensus scores + mitigation accepts/rejects |
| `VALIDATE-OK` | Sign off intersections / close the kata pass |

Batch / provisional multi-stage runs are allowed **only** if you explicitly
ask — every gate stays `PENDING HUMAN` until a ratification checklist is done.

---

## 6. Smoke / sanity

To prove arch-* is ready after setup (no new kata):

```text
Load arch-lifecycle. Confirm .arch/binding.toml + skill paths for this repo,
run skill_sync check, and summarize whether arch-* is ready — do not start a kata.
```

Or from the repo root:

```bash
python3 tooling/skill-sync/skill_sync.py check
```

Throwaway smoke pattern (same idea as SDD D1): tiny disposable kata, mark
**THROWAWAY**, human gates each stage, prefer `.arch/` or a disposable slug
under `docs/architecture/`, **delete after**, ask before commit/PR.

---

## 7. What not to do here

- Do not start style selection without a characteristics worksheet.
- Do not mark ADRs **Accepted** without an explicit human yes.
- Do not claim statistical independence for same-model risk lenses — they are
  coverage; you arbitrate.
- Do not invent SLAs / vendors / regions / counts on diagrams (honesty tags).
- Do not install **coding-rules** into this design repo (spine/o1 later).
- Do not run `skill_sync.py check` from a subdirectory (fails loud).
- Do not treat practice smoke ADRs as product decisions for
  `mobile-test-automation` unless you deliberately promote them.
