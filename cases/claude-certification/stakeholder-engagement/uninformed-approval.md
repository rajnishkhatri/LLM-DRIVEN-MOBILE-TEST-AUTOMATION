---
type: failure-taxonomy
title: 'Watch-out: the approval that was not an informed choice'
description: 'Failure trace: the CTO approved four cents per call. Nobody translated that to monthly spend or named reversal cost, so a five-figure invoice arrived as a surprise.'
tags: [claude, certification, stakeholder-engagement]
---

# The approval that was not an informed choice

SETUP
A stakeholder who says yes at the end of a tradeoff presentation appears to have understood the tradeoff. The presentation was complete and technically accurate, and the room felt aligned. That feeling is the trap.

## A reconstructed pre-production review, from the CTO's perspective

The Architect presented a context-strategy tradeoff in technical terms. The CTO asked one question about cost, the Architect answered it accurately, and the CTO approved. Six weeks later the higher per-call cost appeared in the production invoice. This is the exchange, and then the note the CTO wrote when the bill was received. It shows where the presentation answered the wrong version of the question.

RECONSTRUCTED EXCHANGE + FOLLOW-UP

Architect: "We're recommending the larger context window, so the full policy document stays in view on every call. It keeps the design simpler and avoids a retrieval layer."

CTO: "What does the cost per call look like?"

Architect: "About four cents per interaction at the model tier we're using. If the policy document is static across calls, prompt caching could bring the input portion of that down significantly."

CTO: "Fine, approved. Let's keep it simple."

[Six weeks later, on the production invoice] CTO's note to the account team: "I approved a direction, not a number. Nobody told me four cents times our call volume was a five-figure monthly line. If the document was static, why weren't we caching it? And if we were going to build around full-context anyway, I needed to know what unwinding that would cost once the system depended on it."

## The issue: the reversal cost never entered the conversation

The presentation named what the design gained, simplicity, and it answered the per-call cost as asked. What it never identified was the third element: what happens to the business when this choice meets production volume and must be reversed after the system is built around it. The CTO approved a per-call number, not a monthly bill, and not the cost of unwinding a decision later. Two parts of the tradeoff were clearly communicated and understood. The third was not, and it turned out to be the load-bearing one.

WHY THIS BROKE: AN ACCURATE PRESENTATION CAN STILL ANSWER THE WRONG QUESTION

A stakeholder who approved a recommendation without understanding the reversal cost has not made an informed choice. The CTO heard a per-call figure and a simplicity argument and reasonably said yes. The reversal-cost element was the one factor that would have changed the decision. Name all three elements every time, and name the reversal cost especially when the design feels obviously simpler.
← Previous
Screen 6 of 20
☰ CONTENTS
Next →
