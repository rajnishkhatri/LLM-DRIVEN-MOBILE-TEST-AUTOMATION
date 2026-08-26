---
type: validation-walkthrough
title: 'Assemble a responsible deployment'
description: 'Capstone: five sequenced decisions for a public-sector benefits assistant under FedRAMP. Boundary, runtime controls, fairness logging, human-review routing, and the control register.'
tags: [claude, certification, responsible-ai]
---

Assemble a responsible deployment
Try it now. You are handed a self-contained brief, and you make five sequenced decisions that build a responsible deployment. The decisions run in order because each one sets the conditions for the next. A weak early choice narrows what the later ones can do. If you leave a domain rule in trained behavior in decision one, there is no layer downstream that can put it back.

You built each layer on its own across the module. Here is the stack you are assembling, in order:

Trained behavior shapes baseline safety; your application policy defines domain-specific rules; the runtime controls below enforce those rules in operation.
Runtime screening and authorization sit on the request path and stop disallowed content and unpermitted actions.
Fairness and transparency controls address unequal outcomes at their source and ensure each decision can be reconstructed. They depend on effective logging.
Human-review routing sends the decisions a model should not finalize alone to a person, by stakes. It depends on the same logging.
The control register ties each obligation to a control, an owner, and an evidence artifact.
THE BRIEF
A public-sector benefits assistant helps an agency determine program eligibility, recommending whether to approve, deny, or refer. The brief gives you what the decisions need and nothing more:
Framework: FedRAMP at the agency's required impact level, plus the agency's rule that a denied applicant gets the specific reason.
High-stakes, low-confidence case: An applicant near the eligibility threshold with incomplete documentation, where a wrong denial removes someone's benefits.
Skew-prone output: The recommendation and the reason attached to a denial.
Data: Applicant-submitted fields, agency records retrieved at decision time, and any derived features.
1. Set the boundary between trained behavior and your application layer.

2. Place the runtime controls.

3. Specify the fairness and transparency controls.

4. Define the human-review routing.

5. Build the control register.

Reveal model answer
Skip for now
MODEL ANSWER
1. Set the boundary between trained behavior and your application layer. Trained behavior refuses broad harm classes but never saw this program's eligibility rules, so those belong to the application layer. Leave them in trained behavior and no control downstream can reach them.
2. Place the runtime controls. Position input screening, output screening, and tool-call authorization, choose model-based or deterministic at each, and set the failure direction. Fail closed, because a screen that fails open lets an unscreened denial reach an applicant.
3. Specify the fairness and transparency controls. Name which of the four injection points (corpus, prompt framing, examples, routing) could skew this outcome, and build the decision logging once, since the affected applicant, the regulator, the build team, and the control register all draw on it.
4. Define the human-review routing. Route by confidence, reversibility, and cost of a wrong answer, and pick a placement: pre-action approval, post-action audit, or sampled review. Send a low-confidence, hard-to-reverse denial to pre-action approval. Key the rule to stakes, not volume, or a quiet queue waves a high-stakes denial through.
5. Build the control register. Map each FedRAMP obligation to a control, an owner, and the evidence a reviewer accepts. A control with no evidence artifact is a claim you cannot prove operated.
Mark complete
← Previous
Screen 19 of 22
