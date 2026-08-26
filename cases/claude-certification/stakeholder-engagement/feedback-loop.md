---
type: notes
title: 'The feedback loop decides which signals reach a stakeholder, and the SLA names what you owe when one breaks'
description: 'A feedback loop is the decision layer above observability: signal, trigger, owner, action. SLA thresholds trace to UX, criticality, or evals. Regulated checkpoints fire on a schedule, not only at a threshold.'
tags: [claude, certification, stakeholder-engagement]
---

# The feedback loop decides which signals reach a stakeholder, and the SLA names what you owe when one breaks

Production observability and the audit trail record what a live deployment is doing. This topic covers filtering those signals, deciding when to escalate beyond the team, and defining what the SLA requires when performance falls below standard. The system is live; keeping it trustworthy over time is what takes effort. In lifecycle terms, the feedback loop is the monitoring-and-iteration stage of the deployment lifecycle.

## A live deployment drifts without active monitoring

Imagine a customer support assistant that is launched in solid shape. It answers quickly, stays in tone, and handles the most common questions well. At first, everything looks stable. But over time, usage patterns change, new prompt styles appear, and customer issues become more complex. Some responses merely slow down, and some answers start missing the mark entirely.

Nothing breaks dramatically, which is what makes drift hard to catch. Quality erodes gradually rather than all at once. A team without a feedback loop may not see the decline until users already feel it.

## The feedback loop is a decision layer that sits above the observability stack

Observability gives you the raw material: latency, error rates, eval scores, usage patterns, and other signals from the system. But a signal by itself is not yet a decision. One spike may be noise. Another may point to a real problem. A third may be important only if it keeps happening.

The feedback loop sits on top of observability to answer five questions:

Signals → Triage → Decide → Act → Review

1. **Signals:** What is the system showing us?
2. **Triage:** What needs attention now, and what can wait?
3. **Decide:** Does the issue need a team fix, a stakeholder review, or no action?
4. **Act:** What correction, guardrail update, or escalation is required?
5. **Review:** Did the response work, and does the rule need to change?

Think of it like a control room in a train station. The sensors can tell you where the trains are late, but someone still must decide whether a delay is minor, whether passengers need to be informed, and whether the schedule needs to change. That judgment layer is what makes the system manageable instead of just measurable.

## An SLA names three things, and the thresholds come from somewhere tangible

Once the feedback loop decides that something matters, the SLA defines what happens when it crosses the line. An SLA is a commitment that makes three things clear:

1. What are we measuring?
2. What counts as a breach?
3. What happens when a breach occurs?

The threshold should never be arbitrary. It should trace back to something tangible:

1. Latency should reflect the user-experience expectation identified earlier.
2. Availability should reflect how critical the deployment is to the business.
3. Quality should reflect the eval results and acceptance criteria already established.

That traceability matters because it keeps the SLA defensible. If the number cannot be tied to one of those sources, it is probably just a target someone chose because it sounded reasonable.

Cost is the expectation that breaks most often after launch. Production volume routinely runs one to two orders of magnitude above the pilot, so a cost that looked trivial in the proof of concept becomes a five-figure monthly line at scale. Pre-empt it: give the stakeholder a consumption forecast at expected production volume, name the spend-control posture (caching, model tiering, budget alerts), and frame the model-tiering narrative before the first invoice rather than after it.

## Regulated deployments add review checkpoints that run on a schedule

Observability records what happened; the feedback loop determines what to do about it. In regulated deployments, some reviews must happen even when nothing has gone wrong. A healthcare workflow with a documentation obligation may require periodic output audits on a defined schedule. A data-residency deployment may need scheduled confirmation that the environment still meets residency rules. These are design-time obligations rather than tasks to be added later. If they are not built early, they become far more expensive to establish when someone asks for proof.

Build a governance table that maps each signal to its trigger, the Architect's response, and any regulatory checkpoint. The table should exist before launch. It is the mechanism that turns policy into an operating routine.

### Production-signal governance table

| Signal type | Review trigger | Architect action | Regulated-industry checkpoint |
|---|---|---|---|
| Output quality (eval score) | Score crosses the threshold drawn from the eval suite. | Diagnose whether the cause is prompt, data, or model drift, then decide to iterate versus re-architect. | Periodic output audit against the documentation standard, on an established schedule, regardless of score. |
| Latency p95 | Crosses the budget set from user-experience requirements. | Investigate the bottleneck, then tune or escalate to a stakeholder review if the budget itself is wrong. | Usually none, unless latency is masking a logging or traceability gap. |
| Cost per interaction | Crosses the budget envelope agreed in discovery. | Identify the driver, then bring a tradeoff to the stakeholder if the budget needs revisiting. | Usually none, unless cost controls are part of a regulated operating constraint. |
| Data-residency configuration | Scheduled confirmation. | Confirm and record residency posture and flag any drift immediately. | Residency confirmation on the established schedule. |

## Cost · Complexity · Risk

**Cost:** The loop creates an ongoing Architect effort. Note that this is cheaper than discovering decline in a quarterly review after every dashboard looked good.

**Complexity:** The hardest part is deciding which signals deserve attention and which are noise, because observability tooling cannot make that judgment for you.

**Risk:** The biggest failure mode is a compliance checkpoint that was never wired to a trigger, allowing a documented-standard violation to run for weeks before a routine review catches it.
← Previous
Screen 8 of 20
☰ CONTENTS
Next →
