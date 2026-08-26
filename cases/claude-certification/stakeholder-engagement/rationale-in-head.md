---
type: failure-taxonomy
title: "Watch-out: the design rationale that lived in the Architect's head"
description: 'Failure trace: a thorough diagram with no rejected alternatives. The successor switched context strategy to fix latency and reintroduced the residency violation the original design had solved.'
tags: [claude, certification, stakeholder-engagement]
---

# The design rationale that lived in the Architect's head

SETUP
An Architect who was present at every design decision holds the rationale for all of them. Writing it down feels redundant when you already know it, and there is always something more urgent than documentation. That is exactly how the rationale leaves with the person.

## A postmortem: a financial-services handoff where the rationale never made it to the page

In this case, the original Architect left a mid-sized financial-services engagement twelve weeks after launch. Their replacement inherited a thorough architecture diagram with no rationale attached. A performance issue prompted a proposal to switch context strategies, the replacement made the switch, and it reintroduced a data-handling pattern that violated the deployment's data-residency constraint. The postmortem traces the failure to the one row that was missing. This is what that looks like in the record.

| Stage | What happened | What the document carried |
|---|---|---|
| Launch | Original Architect designs a context strategy specifically to keep regulated data in-region. | An architecture diagram showing the final design. |
| Handoff | Original Architect leaves in week twelve. No design sessions are recorded. | The diagram, with no rejected alternatives and no rationale. |
| Change | Replacement hits a performance issue and switches context strategies to fix it. | Nothing explains why the original strategy was chosen. |
| Failure | The switch reintroduces a data-handling pattern that breaks the data-residency rule. | The reason the original design avoided that pattern existed only in the departed Architect's head. |

## What broke: the diagram showed what and lost the why

The replacement was competent and acted reasonably on the information they had. The diagram told them what the system was, not why it was that way. The original context strategy was a deliberate choice to satisfy a residency constraint, and that reasoning was never written as a decision with a named tradeoff and a rejected alternative. With no rationale documented, the replacement could not tell that the strategy they were changing was load-bearing for compliance, so they reversed the right decision for an understandable wrong reason.

WHY THIS BROKE: A DESIGN WITHOUT ITS RATIONALE IS A DESIGN THAT CANNOT BE SAFELY CHANGED

The completeness test is whether a competent Architect who was not in the room can make a safe change after reading the document. Here the answer was no, and nobody knew it until production broke. Record the decision, the rejected alternatives, and the tradeoff each resolved. Remember: if it is never written, then it leaves with you.
← Previous
Screen 12 of 20
☰ CONTENTS
Next →
