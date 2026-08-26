---
type: overview
title: 'Module introduction: four design decisions before you build'
description: 'Designing with Claude starts with four decisions: what Claude owns, the shape of the work, which reference architecture you are committing to, and where the work interacts with Claude.'
tags: [claude, certification, platform-design, overview]
---

TEACHING
2 MIN
·
MODULE INTRODUCTION
Designing solutions with Claude goes beyond just choosing a model.
When designing solutions with Claude, there are four key decisions to make before you begin building.

01
What part of the work should Claude own?
Before you shape anything, you should decide what to hand to Claude, what to leave with existing systems, and what stays with a human.
02
What shape is the work?
Are you augmenting a live call, automating a workflow, or deploying an agent that acts on its own?
03
Can you name the reference architecture you're committing to?
Picking a reference architecture upfront can save you from expensive pivots later.
04
Where does your work interact with Claude?
Selecting the right entry point, model, and context strategy will keep your solution working and cost-conscious.
In this module, you will learn how to make these decisions to translate an ambiguous business problem into a proposed solution and defend your choices against credible alternatives.

By the end of this module, you'll be able to:

1Break down a partner's request into what Claude does, what existing systems do, and what humans do, using the four properties of generative AI as your decision lens.
2Choose between an augmented call, a workflow, and an agent by naming what each choice costs.
3Pick a reference architecture pattern for the problem shape in front of you and recognize when retrieval is doing a job that live-state should own.
4Make defensible model, context-window, and context-strategy decisions, and use evaluations as the gate before any model swap.
5Know where each platform entry point fits (Claude.ai, the API, an SDK, Claude Code, or an MCP server) and what customization belongs at each layer.
6Distinguish between the Claude entry points a user sees, the build-time interfaces an engineer codes against, and the delivery routes an enterprise procures, as well as identify which are ruled out by governance or regulated-industry constraints before any other tradeoff applies.
WHO THIS MODULE IS FOR
This module is for the Architect who turns a partner's ambiguous request into a solution someone can build, fund, and defend. You are technical, decisive, and tradeoff-aware. You are not writing the production code in this module, and it does not teach you to. It teaches the decisions that sit above the code: what work Claude should own, what shape that work takes, which reference architecture fits, and what model, context, and entry point choices keep the system accurate and affordable once it is real.
"The work" in this module

Everything here is built around one sample engagement: taking a business problem from a partner and arriving at a proposed architecture you can stand behind when a credible alternative is on the table. In this scenario, the partners are enterprise buyers in high-stakes, often regulated, settings where a design choice that looked clean in a demo becomes a misroute discovered in an audit three months later. This scenario is presented as a series of decisions, with each decision asking something different from you.

The decisions map onto the following sections:

Decomposition is where you assign each part of the request to Claude, to an existing system, or to a human, using the four properties of generative AI as the lens. Getting this wrong by over-assigning to Claude is the most common and most expensive early mistake.
Pattern selection is where you decide whether the work is an augmented call, a workflow, or an agent. Each choice provides and costs you something, naming the costs is the objective.
Reference architectures are where a known, good blueprint either fits the problem shape or is misapplied. The failure to watch for is retrieval quietly doing a job that the live transactional state should own.
Model, context, and entry point are where you choose a model tier, a context strategy, and a delivery route, and where evaluations become a stage-gate before any model swap. Check if governance and regulated-industry constraints rule-out a route before considering any cost or latency tradeoffs.
Rather than memorizing these as stages, the objective in this module is to recognize which decision is in front of you, as each one rewards a different move: the decision that serves you well in decomposition is different from when you are choosing an entry point. In the cumulative task at the end of this module you will put all this together to assemble full architecture from a new brief.

DISCLAIMER / NOTICE FOR EDUCATIONAL CONTENT
We built this Architect course Module 1: Claude Platform & Solution Design to help you get real work done with Claude. Treat it as educational content. It doesn't constitute legal, financial, or other professional advice, so adapt what you learn to your own situation. Our products and services evolve quickly, so certain content may contain errors or be outdated; remember to verify on Anthropic’s website or docs. Examples and scenarios used in the course are illustrative and often fictitious. If the course material mentions a company or product, it doesn't mean Anthropic endorses them, they endorse Anthropic, or that we're affiliated. Also note your use of Anthropic products and services is covered by our terms, policies and documentation; if anything in this course conflicts with them, they control.
← Prev
Screen 1 of 34
