---
type: style-guide
title: OKF conventions — LLM-DRIVEN-MOBILE-TEST-AUTOMATION
description: >-
  Knowledge-plane rules-of-record for the MTA/spine/O7 design workspace.
  Seeded from the okf-curator skill's conventions model; binding lives at
  .okf/binding.toml.
tags: [okf, conventions]
---

# OKF convention — LLM-DRIVEN-MOBILE-TEST-AUTOMATION

This file is the knowledge-plane rules-of-record. The okf-curator skill and
bundled lint engine read paths from `.okf/binding.toml`.

## The model

- **Concept** — one markdown file with YAML frontmatter. `type` is required; `title`,
  `description`, `tags` are recommended. Body is free-form markdown.
- **Bundle** — a directory of Concepts plus `index.md` (catalog) + `log.md`
  (newest-first history). Reserved filenames: `index.md`, `log.md`, `README.md`.
- **Cross-links** — relative markdown links or `[[name]]`. Broken links are tolerated
  (not-yet-written knowledge) but linted as WARN.

## `type` vocabulary in use

Self-describing strings; consumers tolerate any value. Common ones (reuse
before inventing new ones):

| `type` | For |
|---|---|
| `recipe` | a numbered implementation recipe |
| `runbook` | operational step-by-step (deploy, ops) |
| `specification` / `spec` | a contract / design spec |
| `validation-walkthrough` | manual end-to-end validation procedure |
| `failure-taxonomy` | categorized failure modes (eval) |
| `rubric` | a judging rubric |
| `overview` | conceptual intro to a topic |
| `architecture` | architecture document |
| `analysis` | an analysis / comparison |
| `guide` / `handbook` | how-to / contributor guide |
| `plan` / `roadmap` | a plan or roadmap |
| `style-guide` | a code style guide |
| `reference` / `notes` / `narrative` / `process-guide` | misc authored knowledge |
| `skill` | a `SKILL.md` Concept |

## Declared bundles & the linter

- The set of bundles is `[lint].declared_bundles` in `.okf/binding.toml`. To
  promote a new directory to a bundle: add `index.md` + `log.md`, add `type:`
  frontmatter to its Concepts, and append its path to the binding's list.
- A **bundle with nested Concepts** is different: one declared dir whose
  Concepts sit in subdirectories it owns (no sub-bundles). The linter walks
  recursively and finds them. `docs/architecture` is the live example —
  its subdirectories are the `arch-*` artifact homes, not topics.
- Run the gate: `python .cursor/skills/okf-curator/scripts/okf_lint.py`
  → exit 0 means structurally sound.

## Where things go (this workspace)

| Kind | Home |
|---|---|
| Coding-rules case studies (OKF bundle) | `cases/coding-rules/` |
| `arch-*` delivery-project artifacts (MTA) | `docs/architecture/<artifact-home>/mobile-test-automation/` — declared bundle |
| SDD specs / plans | `docs/sdd/{specs,plans}/` (in `knowledge_globs`, not a declared bundle) |
| Research / option studies | `docs/research/` (in `knowledge_globs`) |
| Skill manuals | `docs/skills/` (in `knowledge_globs`) |
| Feature recipes | unused (`recipes_home = <none>`) |
| Authored research split | unused (`authored_research_home` / `evidence_home = <none>`) |
| Agent `@`-mentions of docs | unused (`context_mention_prefix = <none>`) |

Grow `declared_bundles` one directory at a time as folders are promoted to
OKF shape.

## Out of scope (never bundle)

Generated or ephemeral trees matched by `[lint]` evidence rules
(`evidence_segments`, `evidence_suffixes`, `run_dir_pattern`) — currently
`outputs`, `node_modules`, `staging`, `*-workspace`, `run-N`. Also `.arch/` —
optional practice-kata homes outside published knowledge. Delivery-project
artifacts live in the bundled `docs/architecture/` instead.
