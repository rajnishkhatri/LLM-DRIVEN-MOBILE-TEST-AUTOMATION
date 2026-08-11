---
type: runbook
title: OKF curator — how to use in this workspace
description: >-
  Workspace-resolved instructions for okf-curator (knowledge-plane curation +
  lint) in LLM-DRIVEN-MOBILE-TEST-AUTOMATION (design repo for MTA / spine / O7).
tags: [okf, curator, documentation, instructions, cursor]
---

# OKF curator — instructions for this workspace

Use this when something **already happened** and needs to be captured in the
authored knowledge plane — or when docs need drift-check, reorganize, or lint
repair. It is the short, path-resolved playbook.

| Need | Doc |
|---|---|
| Clone / provision skills | [../SETUP.md](../SETUP.md) |
| Conventions (rules-of-record) | [../CONVENTIONS.md](../CONVENTIONS.md) |
| Skill body / routines detail | [../../.cursor/skills/okf-curator/SKILL.md](../../.cursor/skills/okf-curator/SKILL.md) |
| First-run / install notes | skill `FIRST_RUN.md` · `INSTALL.md` |
| Agent pointers | [../../AGENTS.md](../../AGENTS.md) |

**This repo is the design workspace.** OKF here governs architecture and
coding-rules *case* bundles — not a live `recipes/` tree. Keys marked `<none>`
in the binding mean “skip that rule and say so.”

---

## 0. Before you start

1. Open **this folder** as the Cursor workspace root (okf-curator is under
   `.cursor/skills/`; Claude has no projection — use Cursor or run the lint CLI).
2. Confirm the binding exists at `.okf/binding.toml` (already resolved — do not
   blank it).
3. Tell the agent to **load okf-curator** for the routine you need. End every
   routine by running the lint gate and confirming exit 0.

### Binding (already set — `.okf/binding.toml`)

| Key | This workspace |
|---|---|
| conventions_doc | `docs/CONVENTIONS.md` |
| lint_gate | `python .cursor/skills/okf-curator/scripts/okf_lint.py` |
| docs_home | `docs/` |
| recipes_home | `<none>` |
| authored_research_home | `<none>` |
| evidence_home | `<none>` |
| context_mention_prefix | `<none>` |
| knowledge_globs | `cases/coding-rules/**/*.md`, `docs/architecture/**/*.md`, `docs/sdd/**/*.md`, `docs/research/**/*.md`, `docs/skills/**/*.md` |
| `[lint].declared_bundles` | `cases/coding-rules`, `docs/architecture` |
| reserved | `index.md`, `log.md`, `README.md` |

Skill body: `.cursor/skills/okf-curator/`. Scripts live next to `SKILL.md`.

**Honest scope:** with `recipes_home` / research / evidence homes `<none>`,
Routine 1–2 “recipe/research homes” from the portable skill do not apply as
written — capture durable design knowledge under declared bundles (or
`docs/research/` / `docs/sdd/` as appropriate), regenerate catalogs where the
bundle model requires `index.md`/`log.md`, and say when a portable step is
skipped.

---

## 1. The four routines

| User wants… | Routine |
|---|---|
| Document what shipped / write a capture | **1 — Document** (prefer a declared bundle topic; no `recipes_home` here) |
| File research / design notes | **2 — File research** (no split authored vs evidence — binding `<none>`; file as authored facts under a sensible home) |
| “Are the docs stale vs the code?” | **3 — Drift check** |
| Lint-clean / fix the knowledge tree | **4 — Keep it extractable** |

Always finish with **Routine 4** (lint gate).

---

## 2. Golden rules (short)

1. **Binding drives lint** — never invent a bundle set; `declared_bundles` is
   load-bearing.
2. **Exit codes matter** — 0 clean; 1 missing `index.md`/`log.md` (blocking);
   2 no/malformed binding (refuse to guess). WARN (missing `type`, broken link)
   is non-blocking but triage.
3. **Catalogs are regenerated** — prefer `make_bundle.py` over hand-editing
   `index.md` / `log.md`.
4. **Moves use `relocate.py`** — never hand-`mv` load-bearing docs.
5. **Do not OKF-bundle generated evidence** — even though `evidence_home` is
   `<none>`, do not catalog dump artifacts as Concepts.

---

## 3. Copy-paste prompts (Cursor)

### Document / capture

```text
Load okf-curator. Resolve .okf/binding.toml (not placeholders). Capture:
<what shipped or changed>. Prefer a home under a declared bundle
(docs/architecture/ or cases/coding-rules/) or docs/research/ / docs/sdd/ as
appropriate — recipes_home is <none> here. Add typed frontmatter, regenerate
catalogs if the dir is a bundle, run lint_gate, paste exit code. STOP if a new
declared_bundle registration is needed.
```

### Drift check

```text
Load okf-curator. Run drift_report.py --since <ref> using this repo's binding
knowledge_globs. Treat the output as a worklist, not a verdict. Propose doc
fixes; do not invent code. End with lint_gate.
```

Widen `--since` past docs-only commits or the report falsely clears.

### Lint / extractability

```text
Load okf-curator. Run the lint_gate from .okf/binding.toml from repo root.
Triage FAIL vs WARN. Fix blocking catalog gaps with make_bundle.py. Do not
“fix” exit 2 by treating 0 bundles as clean.
```

### Smoke

```bash
python .cursor/skills/okf-curator/scripts/okf_lint.py
```

Or in chat:

```text
Load okf-curator. Confirm .okf/binding.toml paths, list declared_bundles, run
lint_gate, report exit code — do not rewrite docs.
```

---

## 4. Gate / smoke probes

| Probe | Expect |
|---|---|
| `python .cursor/skills/okf-curator/scripts/okf_lint.py` | Exit **0** when declared bundles are structurally sound |
| Exit **1** | Bundle missing `index.md` / `log.md` — regenerate or add |
| Exit **2** | Binding missing/malformed / no `declared_bundles` — fix binding, do not guess |

There is no human token like `SPEC-OK` for OKF — **lint exit 0** is the gate.
You still approve content truthfulness; lint only checks structure/extractability.

---

## 5. Useful scripts (from skill dir)

| Script | Role |
|---|---|
| `scripts/okf_lint.py` | Lint engine (the gate) |
| `scripts/make_bundle.py` | Regenerate `index.md` + `log.md` |
| `scripts/add_frontmatter.py` | Typed frontmatter |
| `scripts/drift_report.py` | Code ↔ docs worklist |
| `scripts/relocate.py` | Safe move + reference rewrite |

Invoke as `python .cursor/skills/okf-curator/scripts/<name>.py …` from repo
root (or pass `--binding .okf/binding.toml`).

---

## 6. What not to do here

- Do not blank or “simplify” `.okf/binding.toml` placeholders that are already
  resolved.
- Do not add undeclared bundle dirs and expect lint to pick them up — register
  under `[lint].declared_bundles` when you intentionally create a new bundle.
- Do not use okf-curator to implement product code or run SDD/arch stages —
  it curates writing *about* work that already landed.
- Do not treat WARN broken links to not-yet-written Concepts as automatic
  blockers — see skill `references/gotchas.md`.
