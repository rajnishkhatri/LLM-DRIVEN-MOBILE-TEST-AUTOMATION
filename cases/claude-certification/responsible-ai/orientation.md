---
type: overview
title: 'Module introduction: responsible AI, safety, and risk'
description: 'Module 3 intro. Five outcomes: the training/application boundary, fail-closed guardrail placement, fairness logging, stakes-based human review, and an evidenced compliance register.'
tags: [claude, certification, responsible-ai]
---

The safety stack: who owns each layer, and what happens when one fails
The earlier modules ended with an operational production system: each step of a partner problem was assigned to the right owner, a reference architecture and a model were chosen, the use case was sized, evals were built as acceptance criteria, and the integration layers were put in place to embed Claude inside an enterprise stack.

This module addresses the major security question: what controls are in place to stop a system from refusing a valid request, producing an unfair outcome, or taking an action no one approved? Safety is a full set of controls, each covering a different part of the request path, each with a blind spot the next one has to catch. The Architect is responsible for placing each control and deciding what to do if it fails.

By the end of this module, you will be able to:
1Distinguish between what the model's training reduces and what your application layer must still enforce.
2Place input screening, output screening, and tool-call authorization at the appropriate points in the request path and determine when to use model-based versus deterministic checks, so the system fails closed instead of failing open.
3Identify where unequal outcomes can arise within a system and define the explanations required for users, regulators, and your own debugging team, so fairness and transparency are built into the design.
4Route decisions to the appropriate reviewer/ decision maker based on confidence, reversibility, and the cost of a wrong answer, so review effort is focused on the decisions that warrant them.
5Map each compliance obligation to a named control, an owner, and an evidence artifact, so the architecture can be accurately audited.
This module is for the Architect who has already built a working system: ownership assigned, architecture chosen, evals built, and Claude wired into an enterprise stack. Claude arrives with broad safety behavior in place, but it does not know the partner's data-handling rules, authorization model, or domain policy. Assuming Claude enforces a rule it was never given is the most common way a safety design can fail.

Everything in this module is built around one context: a system that passes every architecture review and still fails in production. The responsibility layer was incomplete, assumed, or correct at design time but wrong by the time someone audited it. The partners are enterprise buyers in regulated settings, where a control that looks solid in a demo becomes an audit finding when configurations drift or a reviewer asks for evidence the control is running.

THE DECISIONS MAP ONTO THE SECTIONS THAT FOLLOW
The alignment boundary is where you draw the line between what the model's training already reduces and what your application layer must still enforce. Assuming that trained alignment covers a domain policy leaves the rule unenforced in every layer. The module starts here because this impacts every downward decision.
Guardrail placement is where you position input screening, output screening, and tool-call authorization on the request path, choose whether each check is model-based or deterministic, and decide what the control does when it fails. A single filter at the end of the path does not cover the other two points, and a control that fails open is worse than no control, because it provides the appearance of protection without any of the function.
Fairness and transparency is where you identify where unequal outcomes can enter the system, and they build the logging that lets you explain any decision afterward. The four injection points are yours to instrument.
Human-review routing is where you decide which decisions a person should weigh in on and what that reviewer needs to do their job. Simply routing by volume floods the queue and often forces reviews to collapse into approvals. The decisions that warrant attention are the ones with high stakes and low confidence, and those stakes need to be pre-identified.
The compliance control register is where each obligation becomes an identified control, an accountable owner, and an evidence artifact that a reviewer can inspect. Choosing a compliant entry point is a prerequisite. A control with no owner and no living artifact can go non-operational without anyone noticing, and then appear as a gap during an audit.
These topics build on each other. The boundary you draw in the first section is enforced by the controls in the second, the logging you build for fairness is the same logging the reviewer uses in the fourth section, and the control register in the fifth section draws on every instrumented layer above it. The cumulative task at the end asks you to assemble all five into a defensible deployment from a single brief, which is exactly what this module equips you to do in front of a security reviewer or compliance auditor.

DISCLAIMER / NOTICE FOR EDUCATIONAL CONTENT
We built this Architect course Module 3: Responsible AI, Safety, and Risk for Architects to help you get real work done with Claude. Treat it as educational content. It doesn't constitute legal, financial, or other professional advice, so adapt what you learn to your own situation. Our products and services evolve quickly, so certain content may contain errors or be outdated; remember to verify on Anthropic's website or docs. Examples and scenarios used in the course are illustrative and often fictitious. If the course material mentions a company or product, it doesn't mean Anthropic endorses them, they endorse Anthropic, or that we're affiliated. Also note your use of Anthropic products and services is covered by our terms, policies and documentation; if anything in this course conflicts with them, they control.
← Previous
Screen 1 of 22
