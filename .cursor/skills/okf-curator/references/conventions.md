# OKF convention — quick reference

The canonical convention lives at your workspace's `{{conventions_doc}}`
(read it for the full rules + any workspace-specific exclusions). This is the
working summary. (No conventions doc yet? Seed one from this file — the model
below IS the convention.)

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

- The set of bundles is `[lint].declared_bundles` in the workspace's OKF
  binding (`.okf/binding.toml`, or the home repo's committed reference). To
  promote a new directory to a bundle: add `index.md` + `log.md`, add `type:`
  frontmatter to its Concepts, and append its path to the binding's list.
- A **bundle-of-bundles** (a parent dir whose content lives in topic
  sub-bundles) is NOT declared itself — only its sub-bundles are — so nested
  files aren't double-counted. It still gets an `index.md` linking the
  sub-bundles.
- Run the gate: `{{lint_gate}}` → exit 0 means structurally sound.

## Where things go

- **Recipes** → `{{recipes_home}}<topic>/` (one sub-bundle per topic).
- **Authored research / design prompts** → `{{authored_research_home}}` (a
  declared bundle).
- **Research EVIDENCE** (coding rounds, stage reports, gold-set artifacts) →
  `{{evidence_home}}` — **EXCLUDED** from OKF (generated, not authored). Don't
  bundle it.
- **Architecture / style guides / guides / analyses / reviews** → their
  existing bundles under `{{docs_home}}`.

## Out of scope (never bundle)

Generated or ephemeral trees: the `{{evidence_home}}` evidence split, plus
anything matched by the binding's `[lint]` evidence rules (`evidence_segments`,
`evidence_suffixes`, `run_dir_pattern`). Also out of scope for OKF entirely:
runtime long-term memory, in-app RAG, and per-user content — those are
data-native and multi-tenant by design, not authored knowledge.
