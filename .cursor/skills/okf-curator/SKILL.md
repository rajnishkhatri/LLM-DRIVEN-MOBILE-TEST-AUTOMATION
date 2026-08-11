---
name: okf-curator
type: skill
description: >-
  Curate your workspace's written knowledge plane — the authored docs tree,
  organized as OKF bundles (typed markdown Concepts plus index.md/log.md
  catalogs), governed by the workspace's conventions doc and held to the
  skill's bundled okf_lint gate. Use this skill whenever the user wants to
  write up, document, capture, or record something that already happened in
  the codebase — especially features that shipped, bugs that got fixed,
  deploy/infrastructure changes, or eval / telemetry / memory work (the
  WRITING of it lives here even when the underlying work was evaluation or
  runtime behavior). Also use it to: file or organize research notes and
  design decisions so they stay findable; check if docs are stale compared to
  recent code; update architecture docs, planning files, or the README to
  match current reality; safely move or reorganize documentation files (with
  full reference rewriting, including load-bearing context @-mentions); or fix
  doc structure / linting and get the tree passing the OKF lint gate. Trigger
  even when the user never mentions "docs", "documentation", "OKF", or
  "recipe" — the signal is that work occurred and now needs to be captured in
  writing, or that existing written knowledge needs refreshing, verifying, or
  reorganizing. Do NOT trigger for: fixing bugs in application code, tuning or
  building runtime/product systems, running tests, or answering general
  questions.
---

# OKF knowledge-plane curator

> **Workspace binding.** This skill is portable. Resolve each `{{placeholder}}`
> from the OKF binding: `.okf/binding.toml` at the workspace root, else the
> committed reference (this repo: `docs/skills/_okf/binding.reference.toml`),
> else **first-run auto-adapt** — inspect the ecosystem, propose values, get
> human confirmation, persist to `.okf/binding.toml`. See `binding.schema.md`
> and `FIRST_RUN.md` bundled with this skill. The bundled scripts resolve the
> same binding at runtime (`--binding PATH`, else discovery); the lint engine
> **hard-exits** rather than lint a guessed bundle set. Keys marked `<none>`
> in a binding mean that rule has no workspace analog — skip it and say so.

## Why this exists

A workspace's authored knowledge — recipes, research, architecture docs — is
structured as **OKF bundles**: directories of markdown Concepts (each with
`type` frontmatter) plus an `index.md` catalog and a `log.md` history, all
linted by the bundled `okf_lint` engine. The point of that structure is that
humans *and* agents can navigate it: an agent lands on a topic's `index.md`,
sees one line per Concept, and pulls only what it needs.

That value evaporates the moment the docs fall behind the code. You ship a
feature, the runbook that describes the old flow is now wrong, the new
capability has no recipe, and the next agent reads a confident lie. This skill
is the **maintenance discipline** that keeps the knowledge plane true after
every change — cheaply, and without breaking the structure.

Read [`references/conventions.md`](references/conventions.md) for the model and
the `type` vocabulary, and [`references/gotchas.md`](references/gotchas.md)
before any large change. The full rules live in your workspace's
`{{conventions_doc}}`.

## The four routines

Figure out which the user needs (they often need 1 then 4):

| The user wants… | Routine |
|---|---|
| "document this feature", "write a recipe", "capture what we shipped" | **1 — Document as a recipe** |
| "file this research", "keep the research organized" | **2 — File research** |
| "are the docs stale?", "what's out of date vs the code?" | **3 — Drift check** |
| "make the docs lint-clean", "fix the knowledge tree", or after 1/2 | **4 — Keep it extractable** |

The bundled scripts live in `scripts/` next to this file (invoke them from the
skill's install directory — below, `<skill>` means that directory). The
canonical lint engine is the bundled `<skill>/scripts/okf_lint.py`; your
workspace's `{{lint_gate}}` command drives it (in the skill's home repo, a
repo-root shim delegates to it). **End every routine by running `{{lint_gate}}`
and confirming exit 0.**

---

### Routine 1 — Document a feature as a recipe

1. **Pick the home — prefer a topic sub-bundle.** A recipe that belongs to a
   coherent topic (a tool, a subsystem, a deploy target) goes in that topic's
   sub-bundle `{{recipes_home}}<topic>/` (this workspace's live topics, where
   the binding lists them: `{{examples.topic_bundles}}`), so it's catalogued
   *and* linted as part of a declared bundle. If the topic is genuinely new,
   **create the sub-bundle dir and register it** — a flat recipe at
   `{{recipes_home}}` root is NOT inside a declared topic bundle, so reserve
   the root only for truly cross-cutting one-offs
   (`{{examples.cross_cutting_recipes}}`). When in doubt, a new topic
   sub-bundle is the better home: it's the form the linter governs and the
   catalog surfaces. Don't create two homes for one recipe — pick one.
2. **Write the recipe** in the house shape — see
   [`references/recipe-template.md`](references/recipe-template.md):
   `# Recipe N — <story title>`, a `**Goal:**` (what you'll have + why), a
   `**Status:**` line with real test counts/artifacts, `**Prerequisites:**` as
   relative links, then the story + steps + a **Verification** section. Ground
   it in the actual code — link the CLI driver, the tests, the modules.
   Recipes that teach the *why* age well; bare step lists rot.
3. **Add frontmatter** (`type`/`title`/`description`/`tags: [recipe, <topic>]`).
   For one new file you can write it by hand; for a batch use the script:
   ```bash
   python <skill>/scripts/add_frontmatter.py \
       {{recipes_home}}<topic> --type runbook --tag "recipe, <topic>"
   ```
4. **Regenerate the catalog + log:**
   ```bash
   python <skill>/scripts/make_bundle.py \
       {{recipes_home}}<topic> --title "<Topic> recipes" \
       --note "Added Recipe N — <title>."
   ```
   (`make_bundle` auto-computes each entry's conventions link from the
   binding's `{{conventions_doc}}` relative to the bundle dir — no depth flag
   needed. New topic → also append the sub-bundle path to
   `[lint].declared_bundles` in the workspace binding.)
5. **Gate:** `{{lint_gate}}` → exit 0.

### Routine 2 — File research

Decide which kind of research this is — it determines the home:
- **Authored design knowledge** (a reusable prompt, a design note that's a
  source of truth) → `{{authored_research_home}}` (a declared bundle). Add
  `type: research-prompt` (or a fitting type) frontmatter; regenerate its
  `index.md` + `log.md` with `make_bundle.py` (the conventions link is
  auto-computed for the bundle's own depth — a root-level bundle needs a
  different relative prefix than a nested one, and the script handles that).
- **Evidence / stage artifacts** (coding rounds, gold-set dumps, run reports) →
  `{{evidence_home}}` — this is **EXCLUDED** from OKF on purpose. Drop the file
  there and do NOT bundle, frontmatter, or catalog it. Bundling generated
  artifacts is churn for no value. (Binding says `<none>`? Then this workspace
  doesn't split authored vs evidence — file everything as authored, and say
  so in your summary.)

When unsure which it is, ask: *would a future agent treat this as a fact to
rely on, or as a record of what happened once?* Facts → the authored home;
records → the evidence home.

### Routine 3 — Drift check (code ↔ docs)

Surface docs that talk about code that just changed, so you can read them for
staleness:
```bash
python <skill>/scripts/drift_report.py --since HEAD~3
# deeper (also flags reference docs missing a brand-new public symbol):
python <skill>/scripts/drift_report.py --since <ref> --symbols
# scope to a subsystem:
python <skill>/scripts/drift_report.py --since <ref> --paths {{examples.drift_scope_pair}}
```
(The script reads which paths count as *code* and which globs hold authored
knowledge from the binding's `[drift]` table and `knowledge_globs`.)

**Pick the window deliberately.** `HEAD~3` is only right if the last 3 commits
are the feature. If recent commits are docs-only (an OKF migration, a
frontmatter pass), the script SAYS SO and you should widen `--since` to a
feature-branch base or `HEAD~N` that reaches the real code — otherwise the
report is empty or misleading. This is the single most common way a drift
check gives a false "all clear".

The output is a **worklist, not a verdict**, and each hit is labelled by match
type: `[path]` (the doc references a changed file path) or `[symbol-absent]`
(the doc describes the changed area but is missing a brand-new public symbol —
a strong stale-reference-doc signal that pure path-matching misses; use
`--symbols` to get these). For each hit: read it, fix stale prose /
`**Status:**` lines, or — if the change is net-new behaviour with no existing
doc — go to Routine 1 and write a recipe. The script suppresses bare generic-
basename noise (`README.md`, `server.py`); a `[path]` hit on a full changed
path is real.

### Routine 4 — Keep it extractable

```bash
{{lint_gate}}
```
- **Exit 0** → structurally sound; you're done.
- **FAIL, exit 1** (a bundle missing `index.md`/`log.md`) → regenerate it with
  `make_bundle.py`, or add the missing file. This is the only blocking
  condition.
- **Exit 2** → no binding resolvable, malformed TOML, or a required key missing
  (`[lint].declared_bundles`) — the engine refuses to lint a guessed or
  undeclared bundle set; run the `FIRST_RUN.md` flow, then re-run. Never "fix"
  this by treating `0 bundle(s)` as a clean tree.
- **WARN** (missing `type`, broken link) → non-blocking, but triage: add `type`
  to new Concepts (`add_frontmatter.py`, with `--insert-type-if-missing` for
  files that already carry non-OKF frontmatter); for a broken link, decide if
  it's real rot to fix or a forward-reference to leave. Don't chase WARNs that
  are root-relative code links or intentional not-yet-written references — see
  [`references/gotchas.md`](references/gotchas.md).

---

## Moving or renaming a doc (rare, high-care)

Only when a file genuinely belongs elsewhere. A move breaks references in
**both directions** and some are load-bearing (`{{context_mention_prefix}}…`
mentions in agent context files feed agent context). Never hand-move. Use the
script, dry-run first:
```bash
# preview
python <skill>/scripts/relocate.py --plan --move OLD.md=newdir/OLD.md
# apply (repeat --move per file)
python <skill>/scripts/relocate.py --apply --move OLD.md=newdir/OLD.md
```
Then verify: `git status` rename count, a repo-wide grep that no reference
resolves to the OLD path, every `{{context_mention_prefix}}…` mention resolves,
and `{{lint_gate}}` exit 0. The gotchas file documents every way this has
bitten before.

## Bundled resources

- `scripts/okf_lint.py` — **the OKF lint engine** (binding-driven; the gate).
- `scripts/_binding.py` — shared binding loader (`--binding` / discovery).
- `scripts/add_frontmatter.py` — typed-frontmatter prepender (pure-prepend,
  idempotent).
- `scripts/make_bundle.py` — `index.md` + `log.md` generator from frontmatter.
- `scripts/drift_report.py` — changed-code → mentioning-docs report.
- `scripts/relocate.py` — `git mv` + full reference rewrite (markdown links,
  context @-mentions, bare paths, and the moved file's own outbound links).
- `references/conventions.md` — the model + `type` vocabulary + where things go.
- `references/recipe-template.md` — the recipe house shape + a worked skeleton.
- `references/gotchas.md` — the failure log; read before any large or
  move-bearing change.

The bundled engine is canonical — your workspace's `{{lint_gate}}` drives it,
never duplicates it.
