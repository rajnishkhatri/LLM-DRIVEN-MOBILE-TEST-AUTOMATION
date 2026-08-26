---
type: notes
title: 'Routing decisions to people by stakes, not by volume'
description: 'Route by confidence, reversibility, and cost of a wrong answer. Place review pre-action, post-action, or sampled, and put inputs plus the flag reason in front of the reviewer.'
tags: [claude, certification, responsible-ai]
---

Routing decisions to people by stakes, not by volume
Decision logging gave you a record of what each automated decision was based on: the inputs it saw, the path it took, and the output it produced. A logged decision can be explained after the fact, but a log alone does not decide which decisions a person should weigh in on before they take effect. A log explains decisions after the fact. A routing rule stops the wrong ones from taking effect at all. You will work out which decisions warrant a human review step and what that reviewer must see on the screen to make the call quickly. The log you have already built is the raw material for that view, so this is a matter of deciding what to surface from it and when, rather than instrumenting the system again from the start.

What sets the stakes of a decision
Think of human review as a budget: you have a finite amount of reviewer attention, and you must focus it on the highest-stakes items. The following variables work together to set the stakes of a decision.

Reversibility is how easily a wrong decision can be undone.
The cost of a wrong decision is what the mistake causes if it goes through uncorrected. These two set the stakes of the decision: a choice that is hard to reverse and expensive when wrong is high stakes, regardless of how the system arrives at it.
Confidence is the third variable that sits on top of the other two. It is the score the system produces about its own output, and it is useful only to the degree it is calibrated, because a model can be confidently wrong. Confidence does not change the stakes of a decision; it estimates how likely this output is to be wrong, which tells you how much of your volume should be routed to a person for review.
Combine these variables into one rule: route decisions to a person when they are low-confidence and either irreversible or high-cost; let confident, reversible, low-cost decisions through. A confident, easily reversed, low-cost decision can usually run without a human. A low-confidence, irreversible, high-cost decision almost always needs human review.

The decisions that consume your review budget are the ones where these variables disagree. A case can be high cost but easily reversed, or low confidence on something trivial to undo. When they conflict, give greater weight to cost and reversibility, because they determine the consequences of a mistake. Let confidence decide how much of that high-stakes volume you can safely let through unreviewed. Routing on confidence carries one assumption worth identifying: the confidence signal must be calibrated for the rule to hold, and confirming that calibration is a task of its own.

Where the human sits is a tradeoff between safety and speed
Once a decision is routed to a person, you choose where they sit in the flow. Involving a human earlier is safer and slower.

Placement	What it gives you	What it costs
Pre-action approval	The action cannot take effect until a person approves it, so nothing irreversible happens unreviewed.	It adds latency to every routed decision and a person must be available, so it does not scale to high volume.
Post-action audit	The action runs immediately and a person reviews it afterward, so throughput stays high.	A wrong action has already taken effect by the time it is caught, so it only suits reversible, lower-cost decisions.
Sampled review	A fraction of decisions are reviewed to monitor quality without slowing the overall process.	A bad decision can slip through unsampled, it monitors the system rather than guarding individual outcomes.
What the reviewer sees decides whether review is accurate
A reviewer who cannot see why a decision landed in their queue may approve without reviewing with the judgement it needed. Ensure your reviewers have three things: the inputs that drove the decision, the model's output, and the reason it was flagged. Without this reason, they cannot tell the difference between an edge case and routine traffic. Without the inputs, they cannot tell if the output is correct. What you put in front of the reviewer determines whether the review is accurate.

Anthropic's research on agent autonomy found that requiring sign-off on every action adds friction without meaningful safety gain. A better approach is to have a person monitor what is happening and step in when needed. One Anthropic pattern in agent workflows is to reduce per-step approvals and move review to higher-value checkpoints such as plan review or exception handling, to avoid consent fatigue; the exact review design depends on the risk of the workflow. Without this discernment, consent fatigue can happen. Consent fatigue is when a system asks for approval dozens of times in a row, and reviewers start clicking through and approving items without reading or providing the quality of review needed. That pattern is what led to plan-level review in Claude Code, where a person approves the plan rather than each step. Verify current framing against anthropic.com/research/measuring-agent-autonomy and anthropic.com/research/trustworthy-agents at publish time.

Diligence: the competency behind human review
Diligence is one of the four AI Fluency competencies: ensuring responsible AI collaboration. Applied to deployment, it means maintaining explicit human accountability checkpoints, recognizing when automation pressure is eroding oversight, and auditing workflows for gaps where AI acts without review, especially as automation scales.

For agent workflows, the routing rule becomes a checkpoint pattern: a gate that pauses execution for human review based on that task's risk and reversibility. Place a gate before any irreversible or high-stakes action an agent would otherwise take autonomously, and sample lower-stakes actions instead of gating each one. This is the same gate vocabulary that multi-agent design depends on.

COST · COMPLEXITY · RISK
Cost: Pre-action review adds latency to every routed decision and needs reviewer time, which is a recurring operating cost.
Complexity: Routing logic, a reviewer interface that shows inputs and flag reasons, and three placement paths are more complex to build than a single review queue.
Risk: Routing by volume rather than stakes either overwhelms reviewers and risks review quality degradation, or allows a high-stakes, irreversible action with no gate at all.
← Previous
Screen 13 of 22
☰ CONTENTS
Next →
