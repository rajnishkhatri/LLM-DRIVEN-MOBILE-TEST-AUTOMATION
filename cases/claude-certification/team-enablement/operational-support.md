---
type: guide
title: 'Supporting debugging and operational issue resolution'
description: 'Connect operational symptoms to architecture causes, capture them in a runbook, and define an escalation path so the team resolves recurring issues without the Architect.'
tags: [claude, certification, team-enablement]
---

Supporting debugging and operational issue resolution
There's always a time when a live deployment surprises its team. When it does, the Architect is the person who connects what the team is seeing to why it is happening. The Architect is also responsible for upskilling the team, so next time they feel empowered to resolve the issue themselves. This screen is about the support role, the symptom-to-cause reasoning that defines it, and building the team toward self-sufficiency.

The support role is translation, not firefighting
When an operational issue lands, the team usually identifies a symptom, not a cause. For example, they'll note that latency spiked, outputs degraded, or a tool started failing. The team then pulls in the Architect, whose value is connecting the operational symptom to its architecture cause: the same diagnostic discipline Module 2 built for production systems, now applied in support of a team that owns the deployment. Resolving one incident yourself is firefighting; teaching the team the symptom-to-cause path they can follow again in the future is support that lasts.

Connect symptoms to architecture causes
Many operational symptoms trace to a small set of architectural causes. Identifying these allows the team to reason clearly from what they see to where to look.

Symptom → likely architecture cause → first action

| Symptom | Likely architecture cause | First action |
|---|---|---|
| Output quality degraded gradually, but there was no code change | A model or prompt change, or retrieval drift as the corpus grew. | Compare against an eval set; check what changed in the model, prompt, or corpus. |
| Latency spiked | Context size grew, a tool got slow, or a cache stopped hitting. | Use telemetry and request traces to find the slowest span: check token counts per request and the slowest tool call, and confirm cache behavior. |
| Intermittent tool failures | Authorization, rate limits, or an unhandled error path. | Inspect the failing tool's auth and limits; trace one failed call end to end. |
| Cost rose without a usage change | Model tier crept up, or caching regressed. | Check per-request model tier and cache hit rate against the budget model. |

Build self-sufficiency: runbooks and escalation paths
Self-sufficiency is engineered into functioning teams. A runbook captures the known symptom-to-cause-to-action paths so the team can resolve recurring issues without the Architect. The table above is the foundation of a good runbook. An escalation path identifies who handles what and when an issue leaves the team, so people know the boundary of what they can resolve and what must get escalated. Always encourage a team to keep a runbook for their deployment and define a clear escalation path. The goal is a team that needs you only when new problems arise, not for ones you've already taught them how to face.

WATCH OUT FOR
The drift that waited for a quarterly review. A support team watched a deployment's dashboards stay green for an entire quarter while answer quality quietly slid. No one connected the slow decline to its cause: a growing retrieval corpus the index had not kept pace with. The symptoms were visible the whole time, but the runbook entry that says gradual quality decline with no code change points at the model, the prompt, or retrieval drift was missing. With that path written down, a first-line engineer could have resolved the issue in an afternoon; but without it, it waits for a review.
Cost · Complexity · Risk
Cost Teaching the symptom-to-cause path costs more of the Architect's time up front than fixing the incident directly, but it is the only version of support that reduces future load instead of repeating it.
Complexity The hard part is resisting the urge to firefight: the fast fix is to resolve it yourself, but the durable fix is to help the team create a runbook entry and identify the escalation path that lets the team resolve the next issue without your help.
Risk The biggest failure mode is a slow degradation no one connects to a cause, so it runs until a scheduled review catches it rather than the team catching it the day it starts.
← Previous
Screen 6 of 10
☰ CONTENTS
