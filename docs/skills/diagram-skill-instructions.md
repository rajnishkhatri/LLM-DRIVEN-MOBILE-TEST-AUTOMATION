---
type: runbook
title: Architecture diagrams skill — how to use in this workspace
description: >-
  Workspace-resolved instructions for the C4 IR → D2 → lint diagram pack in
  LLM-DRIVEN-MOBILE-TEST-AUTOMATION (design repo for MTA / spine / O7).
tags: [diagrams, c4, d2, instructions]
---

# Diagram skill — instructions for this workspace

Use this when you need **presentation-grade C4-flavored diagrams** (context /
container / component) with a fact-frozen IR, reserved shapes, honesty tags,
and a deterministic lint — not a whiteboard sketch.

| Need | Doc |
|---|---|
| Clone / machine prereqs | [../SETUP.md](../SETUP.md) §1 + §6 |
| Full skill (man page) | [generating-architecture-diagrams/SKILL.md](generating-architecture-diagrams/SKILL.md) |
| Install into another agent/repo | [generating-architecture-diagrams/INSTALL.md](generating-architecture-diagrams/INSTALL.md) |
| Architecture *design* workflow | [arch-lifecycle-instructions.md](arch-lifecycle-instructions.md) |
| Agent pointers | [../../AGENTS.md](../../AGENTS.md) |

**This repo keeps the pack under `docs/skills/generating-architecture-diagrams/`.**
Agents follow `AGENTS.md` — you do **not** need a second copy under
`.cursor/skills/` for day-to-day use here.

---

## 0. Before you start

1. Open **this folder** as the workspace root.
2. Machine tools (once):

```bash
brew install d2 librsvg
python3 -m pip install Pillow
d2 --version && rsvg-convert --version | head -1 && python3 -c "import PIL; print('Pillow', PIL.__version__)"
```

3. Tell the agent to follow
   `docs/skills/generating-architecture-diagrams/SKILL.md` (not invent a
   one-off Mermaid poster for the strict deliverable).
4. Prefer inputs from arch-* artifacts (`logical-components.md`,
   `diagram-set.md`, worksheets) under `docs/architecture/` or `.arch/`.

### Paths

| Item | Location |
|---|---|
| Skill SoT | `docs/skills/generating-architecture-diagrams/` |
| Driver | `…/scripts/render.sh` |
| Linter | `…/scripts/lint_diagram.py` |
| Honesty tags | `…/references/honesty-tags.md` |
| IR schema | `…/references/ir-schema.md` |
| Worked examples | `…/assets/examples/silicon-sandwiches/`, `…/assets/examples/mobile-test-automation/` |
| Arch mermaid default | `.arch/binding.toml` `diagram_notation = mermaid` (quick/inline only) |

---

## 1. When to use / when not

| Use this skill | Use something else |
|---|---|
| Generate a new C4 set from a logical model | `arch-*` to *choose* style/components/ADRs |
| Improve readability of an existing `diagram-set.md` (zero topology change) | Inline Mermaid in worksheets mid-design |
| Lint-proven SVG / grayscale proof for reviews | Book-style concept figures (rings, nesting geometry) — hand-author D2/Mermaid |

Do **not** invent SLAs, vendors, regions, instance counts, or latencies. Unknowns
become honesty tags (`SLA: UNKNOWN (pending)`, `PROVISIONAL`, `PROPOSED ADR NNNN`)
— see [honesty-tags.md](generating-architecture-diagrams/references/honesty-tags.md).

---

## 2. Golden rules (short)

1. **IR is fact-frozen** — no fillable numeric invention fields; stop and ask
   when a required fact is missing.
2. **Linter is the gate** — LLM correction from linter messages; never skip lint.
3. **Readability ≠ topology change** — improve-existing relocates detail to
   tables; adding/removing edges is an arch-* task.
4. **Always `--detail`** when linting — groundedness / C4 key checks need it.
5. **Verbatim labels** — short on-canvas names; heavy facts in `detail[]`.

---

## 3. Copy-paste prompts

### Generate from architecture artifacts

```text
Follow docs/skills/generating-architecture-diagrams/SKILL.md for
docs/architecture/<path or slug>. Classify generate-new vs improve-existing.
Fact-freeze IR; honesty tags for unknowns — do not invent SLAs/vendors/regions/
counts. Render with scripts/render.sh, lint with lint_diagram.py --detail until
PASS. Report views, linter line, and any honesty tags left.
```

### Improve readability only

```text
Follow docs/skills/generating-architecture-diagrams/SKILL.md in improve-existing
mode on <diagram-set.md>. Zero topology change. Relocate cramped detail into
tables; run render + lint --detail. STOP if a fact is missing rather than guessing.
```

### Smoke (bundled example)

From `docs/skills/generating-architecture-diagrams/`:

```bash
bash scripts/render.sh \
  assets/examples/silicon-sandwiches/ir.json \
  assets/examples/silicon-sandwiches

python3 scripts/lint_diagram.py \
  --ir assets/examples/silicon-sandwiches/ir.json \
  --svg assets/examples/silicon-sandwiches/01-context.svg \
  --d2 assets/examples/silicon-sandwiches/01-context.d2 \
  --proof assets/examples/silicon-sandwiches/proofs/01-context-gray.png \
  --detail assets/examples/silicon-sandwiches/01-context-detail.md
```

Expect a `PASS …` line and exit 0.

---

## 4. Workflow (one line each)

1. Author or ingest `ir.json` (per view).
2. Readability pass (short labels, detail tables, locators, split if dense).
3. `bash scripts/render.sh IR.json OUTDIR` → SVG, @2x PNG, grayscale proof, `view.md`; dense views may emit overlays.
4. `python3 scripts/lint_diagram.py … --detail` → fix IR on FAIL, re-render (≤ ~3 loops).
5. Self-audit from `assets/self-audit-template.md`.

---

## 5. Gate

| Gate | Meaning |
|---|---|
| `lint_diagram.py` exit **0** / `PASS` | Diagram set acceptable |
| Exit **1** | Fix IR from the exact linter message; re-render |

No human token analogous to `VALIDATE-OK` — that belongs to `arch-validate`.
This skill’s gate is the **deterministic linter** (plus your acceptance of
honesty-tagged gaps).

---

## 6. What not to do here

- Do not invent SLAs / vendors / regions / counts to “complete” a diagram.
- Do not skip grayscale proof or `--detail` lint.
- Do not use this pipeline for Clean-Architecture ring / principle figures.
- Do not treat Mermaid in arch worksheets as a substitute for the linted D2
  deliverable when you asked for presentation-grade diagrams.
- Do not require reinstalling the pack under `.cursor/skills/` in this repo —
  `docs/skills/…` + `AGENTS.md` is the intended surface.
