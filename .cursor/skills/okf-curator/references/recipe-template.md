# Recipe house shape

Recipes in `{{recipes_home}}<topic>/` follow a consistent shape so a human or
agent can scan one and know exactly what it does, whether it's done, and what
it depends on. Match it — consistency is what makes the bundle browsable.

## Anatomy

```markdown
---
type: recipe             # default for a numbered recipe. Use a narrower type when it
                         # fits better: runbook (ops steps), validation-walkthrough,
                         # specification, failure-taxonomy, rubric, overview, spec, …
title: 'Recipe N — <Story title>'
description: '<one line: what this recipe accomplishes>'
tags: [recipe, <topic>]  # topic = the sub-bundle dir. Use HYPHENS, not underscores,
                         # to match the rest of the tree (e.g. my-topic, not
                         # my_topic). Never tag a research note `recipe`.
---

# Recipe N — <Story title>

**Goal:** <2–4 sentences. What you'll have when this recipe is done, and why it
matters. Concrete and outcome-focused.>

**Status:** <Complete | In progress | Planned> | <test counts / artifacts, if any>
**Prerequisites:** <Recipes / plans this builds on, as relative markdown links>

---

## Quick reference

| Item | Value |
|------|-------|
| CLI driver | `<path to the driver script>` |
| Test harness | `<path to the tests>` |

## Before we start: a short story (optional but encouraged)

A paragraph framing the *problem* the recipe solves — the bug that hid, the gap that
bit. Recipes that teach the "why" age better than bare step lists.

## Steps

1. ...
2. ...

## Verification

How to know it worked (commands, expected output, a trace to check).
```

## Numbering & filename

- Files are `NN_snake_case_title.md`, ordered by `NN`. The cross-cutting recipes that
  don't belong to a topic live at `{{recipes_home}}` root
  (`{{examples.cross_cutting_recipes}}`).
- The `title` H1 carries the story; the `description` is the dry one-liner the catalog
  shows.

## Worked skeleton (fill with your workspace's subject)

The shape below is a real recipe with its workspace-specific subject
genericized — your binding's `[examples].recipe_walkthrough` names the live
instance in the skill's home workspace, if you want a full worked model.

```markdown
---
type: validation-walkthrough
title: 'Recipe N — End-to-End <pipeline> Validation Runbook'
description: 'End-to-end <pipeline> validation on <deploy target>.'
tags: [recipe, <topic>]
---

# Recipe N — End-to-End <pipeline> Validation Runbook

**Goal:** Validate the full <pipeline> on <deploy target>: every event type
lands where it should, derived artifacts attach, and the safety properties
hold. Then verify rollback safety and document findings.

**Status:** Ready to run
**Prerequisites:** Recipes N-1 and earlier completed; the <feature-enabled>
deployment live (link the deploy plan as a relative markdown link).
```

After writing the file, regenerate the sub-bundle catalog and append a log entry:

```bash
# make_bundle computes each entry's conventions-doc link relative to the
# bundle dir automatically — no depth flag needed (it was a foot-gun: wrong
# depth = a broken convention link in every catalog entry).
python <skill>/scripts/make_bundle.py \
    {{recipes_home}}<topic> --title "<Topic> recipes"
{{lint_gate}}        # must exit 0
```
