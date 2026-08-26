---
type: failure-taxonomy
title: 'Watch-out: when fairness is treated as the model provider''s problem'
description: 'Failure trace: a model passed vendor fairness evals, but skew entered through an unmonitored retrieval corpus. With no decision log, the team could not explain or disprove the source.'
tags: [claude, certification, responsible-ai]
---

When fairness is treated as the model provider's problem
SETUP HOOK
Fairness may seem like a property of the model. The model provider trained it, ran the bias evaluations, and published the results, so it feels reasonable to treat fairness as something handled upstream before the model reaches your architecture. That framing holds up until your system pairs the model with your own retrieval corpus, because a corpus that over-represents some cases produces unequal outcomes the model provider never tested and cannot see.
A post-incident review
This failure mode is worth recognizing early; the team made a reasonable assumption that ended up being wrong. They used a model that passed its fairness evaluations, and the skew entered at a point they had not thought to watch. What follows is one architect describing the gap in a post-incident review.

"We assumed fairness was the model's job. The skew was in our retrieval corpus, and we had logged so little that we could not prove it."

The unequal outcomes did not come from the model's training. Instead they came from a corpus that over-represented some cases, an injection point the team never monitored because they had assigned fairness to the vendor. When the outcomes were questioned, the team had no decision-level log to reconstruct what had happened. They could neither explain the specific decisions the system made nor rule out the corpus as the cause, which left them unable to answer the only question the regulator was asking: where did the skew come from?

WHY THIS BROKE
Fairness was treated as a model property the vendor owns. Unequal outcomes enter at points the architect controls, and the retrieval corpus is one of them. Without decision logging at those points, the team could not explain the harm or disprove its source. Fairness and explainability are architecture requirements. Instrument them at the points where skew can enter. Assuming they arrive with the model leaves those points unmonitored.
← Previous
Screen 11 of 22
