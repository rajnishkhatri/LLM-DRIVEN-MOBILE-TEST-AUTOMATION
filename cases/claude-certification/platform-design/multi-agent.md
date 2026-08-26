---
type: architecture
title: 'Multi-agent systems and orchestration'
description: 'Orchestrator decomposes and synthesizes; subagents own scoped units. Subagent failure is usually recoverable; orchestrator failure usually is not.'
tags: [claude, certification, platform-design, architecture]
---

Multi-agent systems and orchestration
Pattern selection told you when to reach for an agent. Some problems are too large or too varied for a single agent to hold in one context. When that happens, the design moves to multiple agents working together: an orchestrator that decomposes the work and subagents that each carry part of it. This screen teaches how those systems are structured, how they fail, and where a human belongs in the loop.

Orchestrator and subagents: roles, delegation, synthesis

A multi-agent system has two roles.

The orchestrator
Owns the goal: it decomposes the work, decides what to delegate, and synthesizes the results into a single answer. The orchestrator never does the sub-task work itself; its job is delegation and synthesis.
The subagents
Own scoped sub-tasks: each runs in its own context, does one piece, and returns a result.
Three things must be designed, not assumed: how the work is decomposed into sub-tasks, how each subagent's result is structured so the orchestrator can combine it, and how the orchestrator resolves conflicts or gaps when the results come back.

The worked pattern: fan-out over a large work item

The most common multi-agent shape is a fan-out. For example: A parent agent faces a work item too large for one context: a 400-file codebase to audit, a 200-document corpus to summarize, and a regulatory filing to check against fifty rules. The orchestrator splits the item into independent units, dispatches one subagent per unit (in parallel where the units do not depend on each other), and then synthesizes the returned results into a single deliverable. Here the win is twofold: each subagent works in a clean context sized to its unit, and independent units run concurrently.

Error recovery: where a failure can be caught, and where it cannot

In a multi-agent system, the architectural question to ask is 'Where is each failure mode recoverable?'.

A subagent failure is usually recoverable: if one unit fails, the orchestrator can retry it, route it elsewhere, or drop it and flag the gap, while the rest of the work proceeds.
An orchestrator failure is usually not recoverable: if the agent that owns the goal and holds the synthesis loses its thread, the whole run fails, and partial subagent work may be stranded.
Design for this asymmetry, make subagent work idempotent and retryable, and protect the orchestrator's state.

Failure	Where it lands	Design response
A subagent returns a malformed or empty result	Subagent boundary (recoverable)	Validate each result; retry or re-route the failed unit; record the gap rather than failing the run.
Two subagents return conflicting results	Synthesis step (recoverable)	Give the orchestrator an explicit conflict-resolution rule, or escalate the conflict to a human.
The orchestrator loses the goal or its synthesis state	Orchestrator (often unrecoverable)	Protect orchestrator state; checkpoint progress so a failed run can resume rather than restart.
Traces fragment across orchestrator and subagents	Observability (cross-cutting)	Propagate a shared trace identifier so a single run is reconstructable end to end.
Human-in-the-loop checkpoint patterns for agent workflows

A multi-agent system can take many actions before a human ever sees the output, which makes checkpoint placement a deliberate design choice. A human-in-the-loop checkpoint is a gate that pauses execution for review, positioned by the risk and reversibility of the action about to be taken. Place a gate before any irreversible or high-stakes action a subagent would otherwise take autonomously; sample lower-stakes actions rather than gating each one. The full treatment of routing by stakes will be covered in a later section, here the point is that the gate is part of the orchestration design, not bolted on afterward.

COST · COMPLEXITY · RISK
Cost: Multi-agent systems multiply token spend, every subagent has its own context, and the orchestrator pays to synthesize. Reach for the pattern when the work genuinely exceeds one context, not as a default.
Complexity: Each added agent is another failure boundary to observe and govern. The discipline is the fewest agents that meet the requirement, with clear ownership of the goal.
Risk: The dangerous failure is the silent one: a subagent drops a unit and the orchestrator synthesizes a confident, complete-looking answer over incomplete work. Validate coverage, do not assume it.
← Prev
Screen 13 of 34
☰ CONTENTS
Next →