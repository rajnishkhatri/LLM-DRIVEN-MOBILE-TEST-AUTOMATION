---
type: notes
title: 'The four properties architects design around'
description: 'Next-token prediction, knowledge, working memory, and steerability each pair a capability with a limitation and a mitigation; none is a flaw to fix, all are forces the architecture designs around.'
tags: [claude, certification, platform-design, notes]
---

The four properties architects design around
Before you decide what Claude should do in a solution, you need a clear understanding of how Claude behaves. Four properties of the model shape every following design decision. None of these properties are a flaw to be fixed, each is a force you design around – like how a structural engineer designs around the properties of their building materials.

Consider this screen as initial groundwork, you are not being asked to make any design decisions at this point. The goal is to recognize the four properties by name and understand each property's design consequences to prepare you to make informed choices in judgment exercises later in the module.

The four properties and their design consequences

For each property below, the same characteristics that make Claude capable in one situation are the same that makes it fail in another. Read each row as a capability paired with its matching limitation, and the mitigation that an architect reaches for.

Select each property to see its paired capability, limitation, and mitigation.

Next-token prediction
Knowledge
Working memory
Steerability
Capability: Tasks built on common patterns: summarizing, reformatting, and explaining well-established concepts.

Limitation: Anything requiring precision on specifics. Claude can produce text that appears accurate but isn't. This risk concentrates around names, dates, citations, and statistics.

Mitigation: Use citations, uncertainty signaling, and generator-verifier loops. Route specific factual lookups through tool calls or authoritative sources rather than relying solely on the model's output.
From property to design consequence

We will revisit each of these properties in a later part of this course. Map each property to their design consequence now so the connection is in place before you need it:

Non-determinism. The same input can produce different outputs across runs. This is why evaluation frameworks exist: you cannot certify behavior you only observed once. (Feeds the evaluation work in Module 2.)
Context as a finite resource. The context window is a hard edge with a fixed token budget. What you put in it, in what order, and what you leave out are design decisions that affect both what the model can work with and what it costs to run. (Feeds model and context strategy, later in this module.)
Confidence is not validity. Claude can produce a wrong answer in the same fluent, assured tone it uses for a right one. This is why human-in-the-loop placement and verification are architectural choices, not afterthoughts. (Feeds the responsible-deployment work in Module 3.)
Knowledge and capability boundaries. The model is reliable with topics that are common, recent, and consistent in its training data, and unreliable with topics that are rare, private, or fast-changing. For unreliable topics, web search, retrieval, tools, and MCP can be used to make an external system the source of truth instead of the model. (Feeds reference architectures and RAG, later in this module.)
SCENARIO: A FAILURE THAT BEGAN WITH A MISREAD PROPERTY
An architect saw a demo run cleanly five times in a row and concluded the behavior was deterministic. On that basis the team shipped a financial reconciliation pipeline that treated each model output as a fixed, repeatable result and built no checks around it. In the second week of production the outputs drifted: the same statement, re-processed, produced a different categorization. This discrepancy was discovered by chance only when an analyst happened to re-run a batch. Nothing had changed in the input, but different outputs were produced because the model is a non-deterministic system and the architecture had been built as though it was deterministic.
The lesson is not that the model is unreliable, it's that a demo is not evidence of determinism and that the four properties are present whether your architecture acknowledges them or not.
COST · COMPLEXITY · RISK
Cost: Designing without considering these properties is the most expensive mistake an architect can make, because the cost lands after launch, when rework is most expensive and rebuilding trust is the hardest.
Complexity: Naming the four properties up front keeps later design conversations precise. You can acknowledge "this is a knowledge-boundary problem" instead of debating if the model is "good enough."
Risk: The properties do not announce themselves. A system that does not design around these properties won't produce an error; it drifts quietly and the gap results in variable outputs that may be found in an audit or by an angry user, not by the system itself.
← Prev
Screen 2 of 34
☰ CONTENTS
Next →