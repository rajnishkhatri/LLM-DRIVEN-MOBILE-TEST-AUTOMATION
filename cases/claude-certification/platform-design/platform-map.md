---
type: architecture
title: 'Entry points, build-time interfaces, and delivery routes'
description: 'Three distinct platform layers: what a person interacts with, how an engineer programs against Claude, and where API traffic terminates. Collapsing them is a common architecture error.'
tags: [claude, certification, platform-design, architecture]
---

Entry points, build-time interfaces, delivery routes
Throughout this course you will choose how a user reaches Claude, but before that, you need a consistent set of vocabulary. Three terms are often used interchangeably, but they sit at different layers of the architecture. This screen teaches each of these terms. Choosing between them comes later, once the rest of the design is in place.

Three layers, three distinct decisions

These three layers are not alternatives to one another. Every deployment involves all three and confusing them is the most common source of muddled architecture conversations.

ENTRY POINTS
What a person or system directly interacts with. Entry Points are the wrappers that decide who can talk to Claude and how.

Examples: Claude.ai (web, mobile, desktop), Claude Code, a custom application built on the API.
BUILD-TIME INTERFACES
How an engineer programs against Claude, the layer the partner's code is written to.

Examples: The direct API, the SDKs, MCP, the Agent SDK.
DELIVERY ROUTES
Where API traffic terminates. Delivery routes determine whose infrastructure the request runs on.

Examples: Anthropic directly, AWS Bedrock, GCP Vertex AI, Microsoft Foundry.
Why keeping the layers distinct matters

An entry point is chosen for the user and the work. A build-time interface is chosen for the engineering team and the integration. A delivery route is chosen for the partner's cloud commitments and compliance posture. These are three different conversations with three different stakeholders, and a decision in one layer rarely dictates the others.

For now, focus on learning their names and their distinction. Selecting among them under real constraints will be taught later, once you have a model, a pattern, and an architecture to fit them to.

A FAILURE THAT CAME FROM COLLAPSING THE LAYERS
A proposal for a retail banking workflow solution put Claude Code, an engineering entry point, in front of a non-engineering audience because, in the author's words, "it's all Claude." It is all Claude, in the sense that the same model sits underneath every entry point. But the entry point is the wrapper, and Claude Code was built for developers running a terminal, not for bank branch staff following a workflow. Treating the three layers as one erased the distinction that should have ruled the choice out immediately.
COST · COMPLEXITY · RISK
Cost: Every entry point carries its own integration cost. Picking the wrong layer because the vocabulary was unclear can lead to paying for the wrong solution, then paying again to replace it.
Complexity: When the three layers are named and discussed precisely, a design review can isolate exactly which decision is contested. When they are blurred, the review argues in circles.
Risk: An entry point chosen before the user is named is a common and avoidable architecture error that is often traceable to collapsing these three distinct layers into one concept.
← Prev
Screen 3 of 34
☰ CONTENTS
Next →
