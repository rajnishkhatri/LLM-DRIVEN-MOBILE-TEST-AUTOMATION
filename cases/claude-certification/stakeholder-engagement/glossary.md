---
type: reference
title: Glossary
description: 'Module 4 terms from control register through translation table: reversal cost, feedback loop, outcome document, SLA, scenario-specific demo, and related lifecycle vocabulary.'
tags: [claude, certification, stakeholder-engagement]
---

# Glossary

The key terms used across this module, in alphabetical order.

**Control register**
The table carried forward from the regulated-deployment work that maps each regulatory obligation to a technical control, an accountable owner, and an evidence artifact a reviewer can inspect. In documentation it becomes the living record that governs the deployment's production life.

**Decision log (with rationale)**
A record of each architectural choice that captures not just the decision but the alternatives rejected and the tradeoff each resolved, so a successor does not reverse a load-bearing choice for an understandable wrong reason.

**Deployment lifecycle**
The phases a deployment runs through: discovery → design → handoff → monitoring → iteration. Discovery and tradeoff framing do the discovery-and-design work, the feedback loop is monitoring-and-iteration, documentation is handoff, and entry-point selection with the outcome document closes the loop. Identifying the phase a decision belongs to is what lets you judge when one phase is ready to move to the next.

**Discovery**
A structured elicitation, not a conversation: a three-step filter of listen, translate, and write down that turns a stakeholder's business goal into requirements, assumptions, and constraints the design can be built and measured against.

**Documentation completeness**
The test of whether a competent Architect who was not in the room can make a safe change after reading the document. It requires the decision, the rejected alternatives, the tradeoff each resolved, the owner, and the evidence artifact, and assumptions labeled as assumptions.

**Entry-point-responsibility map**
A documented record of which Claude entry point (direct API, Claude Code, Bedrock, Vertex, Microsoft Foundry) owns which task and why, written before integration begins. It prevents the common multi-platform failure of an entry point chosen for one task quietly taking on another because the routing was never documented.

**Evidence artifact**
Concrete proof that a control is operating: a signed agreement, a configuration screen, an authorization record, or a returned log query. A control asserted in a design document with no artifact is a claim, not proof.

**Feedback loop**
The decision layer that sits above the observability stack and answers Signals → Triage → Decide → Act → Review, mapping each signal to a trigger, an owner, and an action. Monitoring collects signals; the feedback loop decides which ones change behavior and whose.

**Governance table**
The pre-launch table that maps each production signal to its review trigger, the Architect's action, and any scheduled regulated checkpoint. It is the mechanism that turns policy into an operating routine and must exist before launch.

**Joint scoping**
A working session with the Anthropic Applied AI team to refine choices and resolve specialist questions. You arrive with a documented view of requirements and constraints, a proposed pattern or candidate set with tradeoffs named, and a short list of open questions only the Applied AI team can answer.

**Limit placement**
Deciding in advance which one or two limitations a demo will name, and framing them as intentional scope boundaries. In regulated settings an upfront, clearly scoped boundary signals rigor, while a discovered or deflected limitation erodes confidence.

**Outcome document**
The artifact that makes a deployment's value legible to a sponsor who was not on the build. Six fields: the use case with scope boundary, the metric before, the metric after, the auditable control, the measurement owner, and the reuse potential. The before-and-after business outcome and the reuse notes are what make it reusable IP rather than a technical record.

**Requirement vs assumption**
A requirement traces to something the stakeholder actually said; an assumption is something the design takes for granted that was never stated. An unsourced assumption is the most dangerous kind, because nobody remembers deciding it.

**Reversal cost**
What it costs to undo a decision after the system has been built around it, the third element of a tradeoff presentation. It is the element most presentations omit and the one that most often changes the meeting, turning "what is the better technical answer?" into "what is the better business choice?"

**Scenario-specific demo**
A demo built against the buyer's own workflow, data shapes, and constraints; it answers "what does this do with my problem?" rather than a capabilities demo's "what can this system do?" Only the scenario-specific demo creates confidence rather than mere interest.

**SLA (Service Level Agreement)**
A commitment that names what is measured, what counts as a breach, and what happens when a breach occurs. The thresholds trace to a tangible source: the user-experience expectation, the deployment's business criticality, or the eval acceptance criteria, rather than an arbitrary target.

**Tradeoff framing**
Presenting an architectural decision in terms a stakeholder can act on: what the choice gains, what it gives up, and what a reversal costs once the system is built around it (plus, in regulated settings, what it does to the compliance posture). The goal is to make an informed decision possible, not to deliver a verdict.

**Translation (discovery)**
The core discovery move: converting a stakeholder preference ("seamless," "fast," "simple") into a testable, bounded constraint by asking what would break the experience, what the user must never notice, and what must still be true when something goes wrong.

**Translation table**
The output of discovery: one row per item capturing the stakeholder statement as said, the implied constraint, the required architectural decision, and any assumption being documented until it is confirmed. One row per item keeps the reasoning intact as work moves from discovery into design.
← Previous
Screen 19 of 20
☰ CONTENTS
Next →
