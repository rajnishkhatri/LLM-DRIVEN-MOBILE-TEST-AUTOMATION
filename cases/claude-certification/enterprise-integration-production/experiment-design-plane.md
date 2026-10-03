---
type: validation-walkthrough
title: 'Checkpoint: place on the experiment-design plane'
description: 'Place five scenarios on the effect-size × confidence plane. Read the axes independently: stakes set the confidence requirement, not the effect size. The zone sets the sample size.'
tags: [claude, certification, enterprise-integration-production]
---

Place on the experiment-design plane
The plane has two axes: the expected effect size (how large a difference you expect to see) and the confidence requirement (how certain you need to be before acting on the result). Place each scenario in the correct zone. The correct placement determines the right experimental posture, which in turn determines the minimum sample size.

A. A minor wording change to a clarification message in a low-stakes FAQ chatbot.
B. A prompt architecture change for a medical intake summarizer where an error could delay treatment.
C. Adding a new classification category to a routing model expected to capture 30% of incoming volume.
D. Testing whether switching from Sonnet to Haiku on a simple formatting task saves cost without degrading quality.
E. A small change to the retrieval prompt in a RAG system processing 200 requests per day.

SMALL EFFECT · HIGH CONFIDENCE
B. A prompt architecture change for a medical intake summarizer where an error could delay treatment.
Small or unknown effect · high confidence. In a high-consequence deployment, a small sample that happens to look positive is not sufficient. The confidence requirement is driven by the consequence of a wrong call, not the expected effect size.
LARGE EFFECT · HIGH CONFIDENCE
C. Adding a new classification category to a routing model expected to capture 30% of incoming volume.
A 30% routing shift has a large effect that affects a substantial fraction of requests. High confidence is required before deploying a change of this magnitude.
SMALL EFFECT · MODERATE CONFIDENCE
E. A small change to the retrieval prompt in a RAG system processing 200 requests per day.
Retrieval prompt changes tend to have subtle, distributed effects on output quality. At 200 requests per day, reaching significance on a small effect takes longer, which raises the effective confidence requirement.
LARGE EFFECT · MODERATE CONFIDENCE
D. Testing whether switching from Sonnet to Haiku on a simple formatting task saves cost without degrading quality.
Large effect on cost · moderate confidence. The cost effect of a model tier change is expected to be large and is easy to measure. Quality degradation is the risk to monitor, but the cost signal is strong enough to reduce the confidence requirement for the cost component.
SMALL EFFECT · LOW CONFIDENCE
A. A minor wording change to a clarification message in a low-stakes FAQ chatbot.
The effect of a wording change on a clarification message is unlikely to be large. The cost of being wrong is low. A small, fast comparison is appropriate.
LARGE EFFECT · LOW CONFIDENCE
Not used in this exercise.
Check answers
Skip for now
CORRECT
You read both axes independently. The medical summarizer sits high on confidence despite a small expected effect because the consequence of a wrong call is high; the model-swap sits large-effect because the cost difference is big and easy to measure. The zone sets the sample size.
WHAT TO WATCH OUT FOR
The axes run together when the size of the intervention or the severity of the stakes is read as the effect size. Place each scenario in two passes: first effect size only (small, large, or unknown — and unknown powers as small), then confidence requirement only, driven by the consequence of a wrong call and how reversible it is. Volume (such as 200 requests per day) is neither axis; it only sets how long the sample takes to collect.
← Previous
Screen 16 of 21
☰ CONTENTS
Next →
