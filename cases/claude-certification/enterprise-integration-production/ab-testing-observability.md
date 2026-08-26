---
type: guide
title: 'A/B testing and observability at scale'
description: 'Hypothesis, assignment, primary metric, and sample size before a live split. Shadow testing when exposure is too risky. Trace, aggregate, detect, attribute.'
tags: [claude, certification, enterprise-integration-production]
---

A/B testing and observability at scale
Integration patterns get Claude into the enterprise stack. The question that follows is whether it is performing the way it should once it is there. Observability answers the monitoring question. Structured A/B testing answers the improvement question. Without both, you are either flying blind or making changes you cannot measure.

Structured A/B testing for live Claude systems
An A/B test for a Claude system follows the same structure as any experiment: a hypothesis, a treatment group, a control group, a metric, and a sample size large enough to make the result statistically meaningful. The difference from traditional software A/B testing is that LLM outputs are probabilistic, which makes the results noisier and the interaction effects harder to control.

The hypothesis must be specific and testable. "The new prompt is better" fails on both counts: it names no treatment, no metric, and no threshold. A usable hypothesis reads like this: "Replacing the instruction to summarize with an instruction to extract the three most important action items will increase task success rate by at least 5% without degrading response latency p95." It names the treatment, the metric, the threshold for success, and the constraint.

Component	What it requires	What goes wrong when it is missing
Hypothesis	A specific, falsifiable statement naming the treatment, the expected direction of the primary metric, and any constraints on secondary metrics.	Without a hypothesis, any result can be interpreted as a win. You can always find a metric that moved in the right direction if you look at enough of them after the fact.
Treatment and control assignment	Random assignment of requests to treatment (new version) or control (current version). Assignment must be consistent for a given user or session to avoid contamination.	Non-random assignment means the groups are not comparable. If the treatment group happens to receive more complex queries, an apparent win may be an artifact of input distribution.
Primary metric	A single metric defined before the experiment runs. Task success rate, cost per completion, latency p95, or user satisfaction proxy. Choosing the metric after seeing the results is outcome-shopping.	An unspecified primary metric turns an experiment into a retrospective correlation, which is a much weaker basis for a decision.
Sample size	Calculated from the minimum detectable effect, the baseline metric value, and the required confidence level. For LLM systems, the variance in outputs is higher than for deterministic systems, which means the required sample size is larger.	An underpowered experiment produces results that cannot distinguish a real effect from noise. A team that runs until they see what they want will find what they were looking for, whether it is real or not.
Reading results without overclaiming
Statistical significance means the result is unlikely to have occurred by chance given the sample size. Whether it is large enough to matter is a separate question. A change can be statistically significant but still too small to justify the operational cost of shipping and maintaining the new version.

The two questions to ask before declaring a winner are: is the effect large enough to justify the operational overhead of maintaining the new version? And did any secondary metric degrade? A prompt change that improves task success rate while increasing cost by 30% may not be a net win, depending on the budget constraints of the deployment.

LLM experiments have an additional failure mode that classical A/B tests do not: interaction effects between the treatment and specific input types. A prompt change that improves performance on typical inputs may degrade performance on edge-case inputs that appear rarely in the test period but frequently in a future seasonal spike. Test period and input distribution alignment matters more in LLM experiments than in most other software contexts.

Shadow testing: validating a change before any user sees it
A live A/B test sends real users to the new version, which means a regression reaches some fraction of them before the experiment closes. There is a way to test against real traffic without taking that exposure. You run the new version in parallel with the current one, send it a copy of live requests, and serve every user the current version's response. The new version's outputs are logged rather than returned, and you score them offline after the fact. The deployment decision is made before a single user has seen the new version. That pattern is called shadow testing.

The choice between the two patterns comes down to how much risk the deployment can carry and how much traffic it sees.

Use a live A/B test when the deployment can absorb a small, bounded amount of exposure to a worse version and the traffic volume is high enough to reach a statistically meaningful sample in a reasonable window. The payoff is that you measure the new version against real user behavior, including the downstream signals a live response produces, such as whether the user accepted the answer or followed up.
Use shadow testing when a single bad output carries too much risk, or when traffic is too low to support a live split before the change is needed. The cost of shadow testing is the loss of downstream signal: with no users receiving the shadow output, scoring relies on an offline rubric or golden answers rather than real user behavior. For a regulated-industry deployment, where exposing users to an unvalidated model change may not be permissible at all, shadow testing is often the only acceptable way to validate the change.
Observability at scale: instrumentation design, dashboards, anomaly detection
Production observability for a Claude system needs to answer four questions: what is the system doing, how well is it performing, when did it change, and why did it change? Each question requires a different layer of instrumentation.

Request-level tracing. Every request should produce a trace that includes the model, model version, input token count, output token count, latency, stop reason, and any tool calls made. This is the raw material for everything else.
Metric aggregation. Aggregate the request-level data into the metrics the dashboard displays: cost per request, latency p50 and p95, task success rate (if the downstream system provides an acceptance signal), and error rate by error type. Per-request decomposition is critical: aggregate metrics can look healthy while a small fraction of requests consume most of the budget.
Anomaly detection. Set threshold alerts on the metrics that matter for the deployment. A cost spike that exceeds 150% of the 7-day average deserves an alert. A latency p95 that crosses the SLA threshold deserves an alert. Model drift (gradual change in the distribution of model outputs over time) is harder to detect with threshold alerts and benefits from periodic distribution comparison.
Change attribution. When a metric moves, the instrumentation should be able to distinguish Model drift (the model's behavior on stable inputs changed), data drift (the input distribution changed), and model update effects (the model version changed and the new version behaves differently on existing inputs). These three causes have different mitigations and mixing them up produces the wrong fix.
A failure taxonomy: classifying what you are looking at
Instrumentation tells you a metric moved; diagnosis tells you what kind of failure moved it. Before attributing a change, classify the failure. The common classes are distinct and call for different fixes:

Prompt failure. The instruction was ambiguous or underspecified and the model filled the gap. The fix is in the prompt, not the model.
Hallucination. The model produced confident, fluent content that is not grounded in the input or a reliable source. The fix is grounding through retrieval, tool use, or verification. Stronger instruction will not resolve it.
Model mismatch. The chosen tier is wrong for the task or was swapped without re-evaluation. The fix is model selection, gated by an eval.
Orchestrator-workers failure. In multi-agent systems, trace across the orchestrator and its subagents: a recoverable subagent failure (retry or flag) looks different from an unrecoverable orchestrator failure. Attribution requires a trace that spans both.
Discernment: judging the output
Discernment is one of the four AI Fluency competencies, defined as the discipline of judging the quality of what the model produced rather than accepting it at face value. Applied to a production system, Discernment is the habit of classifying each output as acceptable, needs revision, or needs override, and feeding that judgment back into the evals and the monitoring. A team without Discernment watches metrics move and never asks whether the underlying outputs were actually good.

Connecting observability data to business value
The people who funded the Claude deployment are not reading the request-level trace. They are reading a KPI dashboard that measures the outcome the deployment was designed to improve. The observability stack needs a translation layer that connects the technical metrics to the business metrics they drive.

For a customer service agent, the business metric might be average handle time, first-contact resolution rate, or customer satisfaction score. The observability stack measures latency, task success rate, and error rate. The translation layer maps task success rate to first-contact resolution and latency to handle time, so the business owner can see whether the system is moving the numbers they care about.

Build this translation layer when the system is designed, not after the first business review. If the technical and business metrics are not mapped at build time, the first business review will raise a question about what is driving the change in handle time. Without that mapping, answering it requires a retrospective reconstruction rather than running a live query.

COST · COMPLEXITY · RISK
Cost: Running an A/B test without pre-specifying the primary metric means you can always find a result you want. Underpowered experiments produce false positives. A change that looks like an improvement gets deployed, and the team ends up maintaining a version no better than what it replaced while absorbing the full operational overhead.
Complexity: Observability instrumentation added after the first production incident means the root cause question cannot be answered from the existing log data. The incremental complexity of building the instrumentation correctly the first time is lower than the complexity of retroactive log reconstruction.
Risk: An LLM system with aggregate-only observability metrics can look healthy while a small fraction of requests is consuming most of the budget and producing wrong outputs. Aggregate metrics protect against obvious failures. Per-request decomposition protects against the non-obvious ones.
← Previous
Screen 14 of 21
☰ CONTENTS
Next →
