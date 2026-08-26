---
type: notes
title: 'Documentation that survives your absence serves the handoff recipient, the auditor, and the returning Architect'
description: 'One document, three readers. Completeness is whether a competent Architect who was not in the room can make a safe change after reading it: decision, rejected alternatives, named tradeoff, owner, evidence.'
tags: [claude, certification, stakeholder-engagement]
---

# Documentation that survives your absence serves the handoff recipient, the auditor, and the returning Architect

The feedback loop keeps the system healthy while you are running it. Documentation is what keeps it functioning after you are gone. This topic turns the full design into documentation that outlives a handoff and satisfies a compliance reviewer. Either the design carries its own reasoning into that handoff, or that reasoning disappears the moment you leave. In lifecycle terms, documentation is the handoff stage of the deployment lifecycle.

## One document serves three readers, and serving only one of them makes it incomplete

Architecture documentation serves three readers. The inheriting engineer takes over a deployment they had no part in building. The auditor arrives later, looking for evidence that a specific control is live and accounted for. The returning Architect, often you, comes back months later with no memory of the design sessions. A document built for one of these readers and not the others is incomplete even when it is detailed.

### For the handoff recipient: the rejected alternatives matter just as much as the decisions made

For whoever inherits the system, the document must carry the decisions that were made, the alternatives that were rejected, and the reason each rejection happened. A design delivered without its rejected alternatives cannot be understood by someone who was not in the room. They will reverse the right decision for the wrong reason or defend the wrong decision because they cannot tell which tradeoff it was resolving. The rejected options explain why the design is shaped the way it is.

### For the compliance reviewer: evidence matters more than assertions

For the compliance reviewer, the document must carry each regulatory obligation, the technical control that satisfies it, the owner of that control, and the evidence artifact that demonstrates the control is operating. This is the regulated deployment control register, carried forward into the living document that governs the deployment's production life. The reviewer does not accept mere assertions. They require evidence, which means that a statement that a control exists is not enough on its own.

### For the returning Architect: navigable without a briefing

For the Architect who returns months later, the document must stand on its own. Decisions are dated. Assumptions are explicitly labeled as assumptions rather than embedded as facts. Open items have owners and resolution criteria. The test is practical: after reading the document, can a competent Architect who was not present at the design sessions make a safe change to the system? If the answer is no, the document is not complete.

## Documentation completeness checklist

| Field | What it captures | Reader it primarily serves |
|---|---|---|
| Decision | The architectural choice that was made, including the date. | All three readers. |
| Rejected alternatives | The options that were considered but not chosen. | Handoff recipient. |
| Tradeoff named | The tradeoff the decision resolved, expressed in terms of gains, costs, and reversal implications. | Handoff recipient and returning Architect. |
| Owner | The person or team responsible for the decision or the control going forward. | Compliance reviewer and handoff recipient. |
| Evidence artifact | The artifact that demonstrates a control is actually operating. | Compliance reviewer. |
| Audit-ready status | Whether the available evidence is current and sufficient for review. | Compliance reviewer. |

## Cost · Complexity · Risk

**Cost:** Writing the rationale and evidence at design time takes time. Reconstructing it later from email threads, or failing to, costs a wrong reversal in production.

**Complexity:** The discipline is recording why, not just what, and labeling assumptions as assumptions, which is easy to skip when the reasoning feels obvious to the person who lived it.

**Risk:** The costly failure is a successor who reverses a load-bearing decision because the rationale was never documented, reintroducing a constraint violation the original design had solved.
← Previous
Screen 11 of 20
☰ CONTENTS
Next →
