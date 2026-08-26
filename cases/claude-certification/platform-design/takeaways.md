---
type: notes
title: 'Five takeaways'
description: 'Decomposition before architecture, pattern as autonomy granted, tested reference architectures before invention, Sonnet as default with every swap gated, and entry point chosen by the work not the shelf.'
tags: [claude, certification, platform-design]
---

Key takeaways
01
Decomposition is the move that comes before architecture.
Before you can choose a pattern, you have to split the work into three buckets: what Claude handles, what your existing systems handle, and what humans handle. The split is driven by how the model behaves on each piece of the work, which is what tells you whether a task belongs with Claude at all or somewhere else in the stack. Designs that skip this step end up forcing Claude into work that another system would do at lower cost or asking it to operate without the context a human would have given a colleague.
02
Choosing a pattern is choosing how much autonomy to grant.
The augmented LLM, the workflow, and the agent are points on a spectrum from "Claude assists one step" to "Claude plans the whole sequence", with four workflow sub-patterns underneath. The decision depends on five factors: predictability (how predictable the task is), error cost (how expensive a wrong answer would be), observability (how visible the work is while it runs), latency (how long you can wait), and cost (how much you can spend per run). When error cost is the binding constraint, error cost picks the pattern. The tightest constraint is the factor that decides.
03
Reach for the tested reference architectures before inventing your own.
The five reference architectures: Agent, RAG, Document processing pipeline (Evaluator-optimizer), Routing, and Coding agent are documented because other teams have already learned what breaks in each one. Combine them when different parts of your system break differently and pick one when you are still uncertain what the system will need to handle. The most common mistake is to use retrieval as a substitute for live state. Retrieval is built for static documents and stale snapshots, so don't use them during a conversation that needs live data.
04
Choosing a model: start with Sonnet and treat every swap as a release.
Sonnet is the default tier because it balances intelligence, speed, and cost for most production workloads. Moving to Opus or Haiku is a deliberate decision that needs the same gate any other release gets: an eval set that defines what "better" means, and a rollback criterion set before the swap, not after. The same principle applies to context. Progressive context, where the model receives only what it needs at each step, holds up better over a long-lived deployment than monolithic context that loads everything up front and grows until it breaks.
05
Pick the entry point by the work it has to do, not by what is already on the shelf.
Claude.ai, the direct API, the SDK, Claude Code, and MCP each carry a different core tradeoff: speed of setup versus depth of control, prebuilt UI versus custom integration, breadth of tools versus focus. The right recommendation is the one where you can name the tradeoff out loud at the time you make it. Naming the tradeoff out loud when you recommend the entry point is what tells you, later, when to switch.
Sources

Anthropic Skilljar, Claude 101: model family (Opus, Sonnet, Haiku), Claude.ai and API entry points.
Anthropic Skilljar, Claude Code 101 In Action: Claude Code customization stack, CLAUDE.md, subagents, MCP, Skills.
Anthropic Skilljar, AI Fluency Foundations: the four-properties framework, next-token prediction, knowledge, working memory, steerability.
Anthropic Skilljar, Building with the Claude API: RAG, chunking, hybrid retrieval, tool use, extended thinking, evaluation.
← Prev
Screen 33 of 34
