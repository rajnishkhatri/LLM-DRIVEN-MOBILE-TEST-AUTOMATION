---
type: reference
title: 'Seven AI primitives an architect assembles'
description: 'Inventory of tools, MCP, subagents, hooks, skills, agent teams, and dynamic workflows. Later patterns are assemblies of these parts, not abstract categories.'
tags: [claude, certification, platform-design, reference]
---

The parts an architect assembles solutions from
Every pattern and architecture in this course is an assembly of a small set of primitives. Name them once, here, so the later lessons become combinations of parts you already recognize.

This screen names the seven primitives, their job, and a one-line statement to teach you what each one is for. You are not choosing among them yet; you are learning what each one is for.

Seven primitives, seven jobs

Read each primitive as a single job. Rather than going deep on any one primitive, keep a wholistic view of all seven for now. A key skill as an architect is composing these primitives to develop a solution.

Click each card to flip it: the front names the primitive and its one-word job, the back gives the one-line definition.

ACT
Tools

FLIP ↻
What lets the model take an action or fetch a result from your code, a function the model can call.
CONNECT
MCP

FLIP ↻
A protocol for exposing a set of tools so multiple Claude clients can reach the same entry points.
ISOLATE / PARALLELIZE
Subagents

FLIP ↻
Hand a scoped sub-task to a separate context so work runs in isolation or in parallel.
GUARANTEE
Hooks

FLIP ↻
Deterministic code that fires on defined events to enforce a rule the model cannot skip.
PACKAGE A PROCEDURE
Skills

FLIP ↻
A versioned, reusable unit (instructions plus optional scripts) that packages a repeatable procedure.
COORDINATE PEERS
Agent Teams

FLIP ↻
Multiple agents working as coordinated peers, each owning part of a larger goal.
COMPOSE AT RUNTIME
Dynamic Workflows

FLIP ↻
Assemble the steps of a workflow at runtime rather than fixing them in advance.
Agent Teams (coordinated peer agents) and Dynamic Workflows (runtime composition) extend older vocabulary of single agents and fixed workflows. You will see them named in current practitioner conversations even though many existing systems predate them.

Why inventory them now

The patterns taught later in this module, the augmented call, the workflow, the agent, are not abstract categories. Each pattern is a particular assembly of the seven primitives. A workflow is steps wired in your code, often using tools. An agent is the model choosing its own sequence of tool calls. A multi-agent system is an orchestrator delegating to subagents. When you reach those lessons, you will be composing primitives you have already named, not meeting them for the first time.

SCENARIO: A FAILURE THAT CAME FROM MISSING SHARED VOCABULARY
In an architecture review, someone said "we'll use an agent." Five people in the room heard five different things: one heard a single tool-using model, one heard a multi-step workflow, one heard a team of subagents, one heard Claude Code, and one heard a chatbot. The design conversation stalled for twenty minutes before anyone realized they were describing different architectures with the same word. By establishing a common understanding of the primitive vocabulary, the team can operate with clarity and efficiency.
COST · COMPLEXITY · RISK
Cost: Reaching for a heavier primitive than the job requires is paid for in latency, tokens, and operational surface area, every request. E.g., Using a team of agents when a single tool call would suffice.
Complexity: Each primitive added to a design is a part to build, observe, and govern. The discipline is to use the fewest primitives necessary to meet the requirement.
Risk: Without a shared vocabulary, teams cannot effectively communicate because they do not agree on what the parts are.
← Prev
Screen 5 of 34
☰ CONTENTS
Next →