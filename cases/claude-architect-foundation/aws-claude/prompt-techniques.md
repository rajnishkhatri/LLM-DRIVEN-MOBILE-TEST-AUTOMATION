---
type: guide
title: 'Prompt engineering techniques — clarity, specificity, XML, examples'
description: 'Four high-leverage prompt edits: lead with an action verb, add attributes or steps, wrap interpolated content in XML tags, and show desired outputs with examples.'
tags: [claude, bedrock, aws-claude, prompting]
---

# Prompt engineering techniques — clarity, specificity, XML, examples

Prompt engineering improves written prompts so outputs are more reliable. The loop is: set a goal → write a poor first version → evaluate → apply a technique → re-evaluate. Each technique is only "better" if the [eval pipeline](prompt-evaluation.md) score moves.

Worked goal in the course: a one-day athlete meal plan from height, weight, goals, and dietary restrictions. A flexible evaluator class, concurrent runs, generated datasets, and an HTML report make the deltas visible. `prompt_inputs` interpolates variables; `extra_criteria` feeds the model grader; dataset generation needs a purpose description, input specs, and a case count. First drafts usually score poorly — that is the baseline, not a failure.

## Being clear and direct

The first line is the most important. Lead with an **action verb** and a specific task: write, generate, create, identify, analyze.

Good first lines:

- "Write three paragraphs about how solar panels work"
- "Identify three countries that use geothermal energy and include generation stats for each"
- "Generate a one day meal plan for an athlete that meets their dietary restrictions"

Structure: action verb + specific task + output expectations. In the meal-plan eval this move raised the score from 2.32 to 3.92.

## Being specific

Add guidelines that point the output in a direction.

- **Type A — attributes:** length, structure, format. Recommended on almost every prompt.
- **Type B — steps:** a process the model must follow. Use on complex problems, or when the model would otherwise skip a viewpoint.

Both combine in production prompts. Adding guidelines in the meal-plan eval moved the score from 3.92 to 7.86.

## Structure with XML tags

Wrap interpolated blocks in descriptive tags so the model can tell instructions from data:

```xml
<sales_records>...</sales_records>
<athlete_information>...</athlete_information>
```

Name tags after the content (`sales_records`, not `data`). This matters most when several large blocks could be confused (code vs docs, records vs instructions). It also helps on smaller inserts so the model treats them as external input, not as further instructions. Ambiguous boundaries are a common source of degraded output.

## Providing examples

**One-shot** = one example. **Multi-shot** = several. Wrap examples in XML; include a sample input and the ideal output.

Use examples when:

- A corner case needs an explicit warning plus a demonstration (sarcasm, empty inputs).
- The output format is complex (nested JSON) — showing beats describing.
- Eval has already produced a high-scoring output you can promote into the prompt, optionally with a sentence on *why* it is ideal.

Explaining why an example is good reinforces the pattern. Reach for examples whenever edge-case handling or output shape must stay consistent.
