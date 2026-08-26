---
type: notes
title: 'A discovery call is a structured elicitation, not a conversation'
description: 'Listen, translate, write down. Four question buckets turn a preference such as seamless into a testable constraint, then one translation-table row per item keeps the reasoning intact.'
tags: [claude, certification, stakeholder-engagement]
---

# A discovery call is a structured elicitation, not a conversation

You know how to evaluate the pattern, the deployment platform, and the control posture. Discovery reveals whether you are solving the right problem. A stakeholder will usually describe the problem in business terms. Your job is to listen to what the business is trying to achieve, identify the constraints hidden inside that description, and leave the call with a record the design can follow.

## Discovery establishes the artifacts the design depends on

A discovery conversation functions as a three-step filter: listen, translate, and write down.

1. First, listen to the business goal in plain language and pay attention to the meaning behind the word. Stakeholders usually describe the outcome they want but not the constraint you need to design for.
2. Second, translate that into requirements, assumptions, and unresolved constraints. This allows you to see what the design must support, what still needs confirmation, and what could block the solution later.
3. Third, write those items down before the conversation moves on. The design needs a clear record to follow. Without that filter, the design inherits your assumptions. The mismatch may not be revealed until much later, when changing trajectory is slower, harder, and more expensive.

## The core move is translation: a stated preference almost always hides a constraint

The most important skill in discovery is translation. Stakeholders usually speak in preferences, but design decisions are made against constraints. Imagine a stakeholder says, "We want this to feel seamless." If you write down "seamless" as the requirement, you have not learned enough to design anything yet. You only have the stakeholder's summary of the experience they want.

The real work starts with the next question: what would make it feel not seamless? That is where the hidden constraints begin to appear. Maybe the user should never wait more than a second or two for the next step. Maybe they should not have to re-enter information that already exists upstream. Maybe exceptions should move quietly to a human reviewer instead of exposing a technical error. Maybe the workflow must stay inside one application, so the user never has to jump between tools. Each answer sharpens the design.

That exchange transforms "seamless" into requirements the architecture must support: a latency target, an integration requirement, a handoff rule, and a safe failure path. The stakeholder names the outcome in business language. You turn it into something the system can build and be measured against.

The preference sits on the top level, and the constraint sits underneath it. When a stakeholder gives you an experience word like seamless, easy, fast, simple, or intuitive, treat it as a signal that more discovery is needed. Ask what would break that experience, what the user must never notice, what has to happen behind the scenes, and what must still be true when something goes wrong. Those answers are what belong in the design record.

A testable, bounded constraint is what the design can be built against. A stakeholder preference tells you where to investigate, while the follow-up questions produce the constraint itself.

## Four questions turn discovery into requirements

Discovery works best when you force a vague stakeholder statement into the four buckets below. A statement like "we want this to feel seamless" is not yet something you can design against. It usually hides one or more specific answers. Investigate the following:

1. **What the system must do.** These are the capabilities the deployment must deliver, expressed as business outcomes rather than features. This is where you separate the work Claude owns from the work that remains with an existing system or a human.
2. **What the system must not do.** These are the boundaries, prohibited actions, and cases that must route to a human. Stakeholders rarely volunteer these, so you must ask for them explicitly.
3. **What the system must cost.** This is the budget constraint, expressed in terms the stakeholder controls. A latency target, a per-interaction cost ceiling, or a volume forecast should all be taken into account here. These become crucial design constraints.
4. **What the system must prove.** This is the evidence that the deployment must be able to produce something of value. In regulated workflows, proof obligations are part of the requirement set. Identifying them in discovery is far cheaper than during a legal review weeks later.

"Seamless" may really mean a latency budget the user should not notice, a handoff that should not interrupt the flow, or a failure state that must not expose system internals. Once you discover those answers, you have requirements the team can design for, test, and defend.

## The output of discovery is a translation table

Each item found in discovery becomes one row in a translation table. The row captures the stakeholder statement as it was said, the constraint it implies, the architectural decision that constraint forces, and any assumption you are documenting when the constraint has not yet been confirmed. One row per item keeps the reasoning intact as the work moves from discovery into design, and it keeps assumptions top of mind.

| Stakeholder statement | Implied constraint | Required architectural decision | Assumption to document |
|---|---|---|---|
| "We want this to feel seamless." | The experience must stay inside an agreed-upon latency budget. Failures must not expose system internals or break the flow. | Set a p95 latency target as a design constraint, then design a graceful, internal-safe failure state. | Assumes "seamless" refers to perceived responsiveness and continuity of flow. Confirm understanding. |
| "It just needs to read the form and route it." | Routing may be a deterministic business rule. | Keep the routing decision in the rule engine. Claude extracts, and the system routes. | Assumes the routing logic is owned and maintained outside the model. Confirm owner. |
| "Clinicians will review the output anyway." | A licensed human must authorize output before it becomes part of a record with legal, financial, or clinical consequence. | Build a human-in-the-loop authorization step as a mandatory checkpoint. | Assumes review is an architectural gate. Confirm authority and timing. |
| "We are in healthcare, so be careful with data." | The workflow likely carries a proof obligation under a health-privacy regime. | Treat audit-trail and data-handling evidence as a core requirement from day one. | Assumes a covered workflow with a formal obligation. Confirm scope with compliance. |

## Cost · Complexity · Risk

**Cost:** A discovery call that runs long enough to identify the real constraints is far cheaper than redesigning the solution after a hidden constraint emerges during legal or compliance review.

**Complexity:** Working through the four question categories adds necessary structure, and translating preferences into constraints in real time takes deliberate practice.

**Risk:** The expensive failure is the unstated constraint that survives the test and becomes a production review blocker, when the cost of changing the design is at its highest.
← Previous
Screen 2 of 20
☰ CONTENTS
Next →
