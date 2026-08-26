---
type: validation-walkthrough
title: 'Checkpoint: sort the eval types'
description: 'Place eight evaluation tasks into code-based or model-based buckets. The split is whether the check is deterministic or needs a judgment call.'
tags: [claude, certification, enterprise-integration-production]
---

Sort the eval types
Eight evaluation tasks are listed below. Drag each one into the bucket where it belongs: model-based eval or code-based eval. The right placement follows whether the behavior being checked requires interpretation or is straightforward.

1. Check that every response is valid JSON matching the defined output schema.
2. Assess whether the model's reasoning in a complex analysis is sound and complete.
3. Verify that the response length is under 500 tokens.
4. Score how appropriately the system handles an emotionally charged customer complaint.
5. Confirm that the extracted claim number matches the quantitative value in the source document.
6. Evaluate whether the summary captures the most important points from a long briefing document.
7. Verify that all required sections (executive summary, methodology, findings, recommendations) are present in the output.
8. Assess whether the tone of a customer-facing message is appropriately professional for the brand.
CODE-BASED EVAL
1. Check that every response is valid JSON matching the defined output schema.
Schema validation is deterministic. A function either parses or it does not. No interpretation is required.
3. Verify that the response length is under 500 tokens.
Length is a number. This is a one-line assertion, so it does not require interpretation.
5. Confirm that the extracted claim number matches the quantitative value in the source document.
Quantitative value comparison is a string match. The expected value is known, so a function can check it.
7. Verify that all required sections (executive summary, methodology, findings, recommendations) are present in the output.
Section presence is a simple checklist where each heading either exists in the output or doesn't. No interpretation is required.
MODEL-BASED EVAL
2. Assess whether the model's reasoning in a complex analysis is sound and complete.
Reasoning quality requires judgment. A deterministic function cannot score whether an argument is logically complete.
4. Score how appropriately the system handles an emotionally charged customer complaint.
Appropriateness is a judgment. The range of valid responses is too wide and context-dependent for a deterministic check.
6. Evaluate whether the summary captures the most important points from a long briefing document.
Importance and completeness are interpretive. The LLM-as-a-judge model is needed to assess whether the right items were included.
8. Assess whether the tone of a customer-facing message is appropriately professional for the brand.
Brand voice and tonal appropriateness are judgment calls that a function cannot encode reliably.
Check answers
Skip for now
CORRECT
You have the core framework. Notice that everything in the code-based bucket is either a structural check or a comparison against a known quantitative value. Everything in the model-based bucket requires a judgment call that a function cannot supply. That split is the deciding criterion.
← Previous
Screen 4 of 21
☰ CONTENTS
Next →
