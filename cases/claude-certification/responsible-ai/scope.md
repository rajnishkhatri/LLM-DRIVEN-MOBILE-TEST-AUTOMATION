---
type: notes
title: 'What the model''s training enforces versus what you own'
description: 'Training-time alignment reduces broad harm; inference-time controls enforce domain policy. Four layers from trained behavior to authorization, each with a job and a blind spot.'
tags: [claude, certification, responsible-ai]
---

What the model's training enforces versus what you own
Earlier work established the architecture, the model, and the integration. Here we answer: before you start adding controls, how much safe behavior is already handled by the model, and how much is still yours to build? You need to understand this boundary clearly to avoid creating duplicate protections or assuming the model is enforcing a rule it has never seen.

Anthropic trains Claude against a constitution: a written document that describes the values and behavior the model should exhibit, so the model is deployed with broad safety behavior already in place. Anthropic revises this document over time, and the most recent published version is from January 2026. The document is used during training to generate examples the model learns from and to rank candidate responses. This shapes how the model responds to ambiguous or sensitive requests but does not necessarily catch bad outputs. It sets a priority order for the model to follow when goals conflict: be broadly safe, be ethical, comply with guidelines, and be genuinely helpful to operators and users. That ordering matters because a helpful answer is sometimes unsafe. The ordering is holistic rather than strict, so higher-priority goals generally take precedence when they conflict, though the model weighs them together rather than applying them in a rigid sequence. The model arrives with a class of harmful output already reduced before you write a single prompt. The built-in layer handles broad, general-purpose harm, but does not cover your specific domain: any policies specific to your users and product are still yours to enforce.

Training-time alignment and inference-time control are two layers with distinct purposes
Training-time alignment shapes model behavior before deployment. It reduces broad classes of harmful output by steering Claude to refuse dangerous requests and default toward safer responses. Because it is set before any deployment exists, it is general by design. This is both a strength and a weakness: it does not know your partner's domain policy, data-handling rules, or authorization model. A request can fit Claude's general alignment and still violate a deployment-specific rule, such as disclosing another customer's order information or advising outside an approved script. Remember, Claude cannot enforce a rule it was never given.

Deployment-specific rules are enforced by the second layer: inference-time control. This includes the runtime guardrails you configure for your deployment, such as system instructions, input and output checks, tool permissions, and human review gates. System instructions shape the model's behavior, but deployment-specific policy is enforced only when those instructions are paired with runtime controls such as screening, authorization, and review. Training-time alignment lowers baseline risk, and inference-time control enforces the rules specific to your deployment.

A layered view: each layer has a job and a blind spot
Treat safety as four layers stacked from Claude outward. Each one covers something the layer below cannot, and each one fails in a way the next must catch.

Select each layer to see what it reliably covers, what it does not, and who owns it.

Trained behavior
System-prompt instruction
Runtime screening
Authorization
What it reliably covers: Broad classes of harmful or unsafe output, applied to every request without configuration.

What it does not cover: Your domain policy, your data rules, your authorization model.

Who owns it: Anthropic.
COST · COMPLEXITY · RISK
Cost: Each added layer costs latency and engineering. A pre-screen on input and a check on output add two extra calls or rules to every request.
Complexity: Four layers means four places to design, version, and test. The system prompt and the screening logic drift independently if not governed.
Risk: The most dangerous failure is a silent one: assuming Claude enforces a domain rule that it was never given. Since the rule doesn't exist in any layer, nothing prevents a violation.
← Previous
Screen 2 of 22
☰ CONTENTS
Next →
