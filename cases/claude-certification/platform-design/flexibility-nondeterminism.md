---
type: failure-taxonomy
title: 'Watch-out: when the team wanted flexibility and got non-determinism'
description: 'Failure trace: an agent was chosen for unknown future flexibility; traces later showed four enumerable paths. Autonomy became a compliance gap.'
tags: [claude, certification, platform-design, failure-taxonomy]
---

When the team wanted flexibility and got non-determinism
SETUP HOOK: WHEN TEAMS PICK AGENTS AND SHOULDN'T
This is a common mistake. Agents are often chosen because a task feels open-ended, not because the task requires one. But feeling uncertain about how to structure the work is different from a task where the steps genuinely can't be determined in advance. If you could have written the steps in code, you could have used a workflow instead of an agent and avoided taking on unnecessary complexity of non-deterministic control flow.
The three quotes below are from a single team's 90-day retrospective. Each one names a different layer of the same underlying mistake.

"We picked an agent because we didn't want to constrain it too early. By month two we'd added so many guardrail tools we'd basically rewritten the workflow inside the agent loop, minus the logging."
"Compliance came in and asked which step approved the disbursement. We pointed at a model turn. They asked which version of the model. We checked the trace. The version had rolled forward two weeks earlier and nobody had re-validated."
"The actual paths through the system, when we mined the traces, fell into only four shapes. Four. We could have written that as a router and four chains and saved ourselves six months."
What broke and why

Each quote names a distinct failure, and they compound in order.

The team optimized for unknown future flexibility instead of the known present shape. When the team mined their traces at month three, the actual paths through the system fell into four shapes, all enumerable from week one. The workflow they needed was a router with four chains. They built an agent instead and spent six months reconstructing that structure inside the loop.

Non-determinism became a compliance problem. When an auditor asked which step had approved a disbursement, the team could only point to a model turn. What the agent pattern specifically added was having no discrete, auditable step to point to. This is how agent autonomy becomes a compliance risk: not in normal operation, but when an external party needs a deterministic answer and the system can only produce a trajectory.

An unpinned model version compounded the gap. The auditor then asked which version of the model had run. The trace showed the version had rolled forward two weeks earlier with no re-validation checkpoint. That roll-forward is a model-governance gap and would have been a problem under any pattern: an unpinned version with no re-validation gate or a workflow that shipped the same way would have inherited the same exposure. Only one of these two failures is about the agent pattern itself.

Choosing an agent when you're not sure if it is the right pattern is not a safe default. An agent is the right choice only when the steps through the work genuinely can't be determined in advance. If the steps are known upfront, choosing an agent over a workflow means paying for flexibility you won't use: extra tokens, latency, and audit gaps that surface when compliance asks something your traces can't answer.
Agents shouldn't be avoided, but they should be fit for purpose. If the work had been genuinely unpredictable, an agent would have been the right call for exactly that reason. This team's mistake was jumping to an agent when the four paths through their system were knowable from the start. A router and four chains would have given them a clean, auditable structure. Instead, they spent six months rebuilding that structure by hand inside an agent loop.
← Prev
Screen 12 of 34
☰ CONTENTS
Next →
