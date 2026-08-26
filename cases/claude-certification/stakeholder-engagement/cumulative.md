---
type: validation-walkthrough
title: 'Capstone: architect a regulated multi-platform deployment end to end'
description: 'Seven sequenced decisions for a two-state clinical-documentation assistant: discovery row, logging-versus-latency tradeoff, scheduled audit trigger, residency decision log, Bedrock plus API map, CFO outcome metrics, expansion gate.'
tags: [claude, certification, stakeholder-engagement]
---

# Capstone: architect a regulated multi-platform deployment end to end

Here is a self-contained brief. A regional healthcare network with a health-privacy obligation is deploying a clinical documentation assistant across two cloud platforms. The original Architect is rotating off, and the customer's CFO is asking for evidence of business value. Work through the seven decisions in order. Each one builds on the last.

THE BRIEF

The network runs across two states. Nurses dictate patient interactions, and the assistant drafts the structured clinical note. A licensed clinician must authorize every note before it reaches the patient record. The deployment carries a health-privacy obligation with an audit-trail requirement and a data-residency rule. The partner is standardized on AWS but runs some non-regulated back-end work on the direct API. You are four weeks into the deployment, and the CFO wants to know what the deployment is worth.

**Decision 1 · Discovery.** From the brief, name the must-prove constraint that most shapes the architecture, and write the one requirement row it forces. (Applies the discovery translation framework.)

Reveal model answer

Must-prove constraint: The health-privacy obligation with audit-trail requirement. Requirement row: The deployment must produce an auditable record of every model-generated note reviewed by a licensed clinician, traceable to the specific interaction, because the workflow carries a formal proof obligation under a health-privacy regime. Assumption to document: scope confirmed with compliance before design.

**Decision 2 · Tradeoff framing.** The network asks for the lowest-latency design. Frame the tradeoff between trimming logging for latency and keeping the audit trail, in three elements including the reversal cost. (Applies the tradeoff translation map.)

Reveal model answer

Gain (trim logging): Faster perceived response; smoother clinician workflow. Give up: Per-interaction audit detail required to satisfy the health-privacy obligation. Reversal cost: Once the system is built around the latency gain, restoring logging requires a redesign of the interaction layer, and any gap period creates a compliance exposure that must be disclosed and remediated.

**Decision 3 · Feedback loop.** Define one governance-table row that maps the required output audit to a stakeholder-review trigger on schedule, independent of any metric. (Applies the feedback-loop governance table.)

Reveal model answer

Signal: Periodic output audit against health-privacy documentation standard. Trigger: Calendar-based (quarterly, per regulatory obligation), fires regardless of eval scores or error rates. Owner: Compliance lead. Action: Stakeholder review with audit record submitted to compliance officer.

**Decision 4 · Documentation.** Name the one decision-log row whose absence would let your successor reverse a compliance-load-bearing choice and state the rejected alternative it must carry. (Applies the documentation completeness checklist.)

Reveal model answer

Decision row: Context strategy, explicit in-region execution via Bedrock, not a global endpoint. Rejected alternative: Global Bedrock endpoint for simpler configuration. Tradeoff named: Simpler setup versus data-residency compliance. Why load-bearing: A successor who doesn't see this rationale will revert to global configuration to solve a performance issue and break residency, exactly as in the financial-services postmortem.

**Decision 5 · Entry-point selection.** Pick the primary and secondary entry points given AWS standardization, a strict obligation, and a residency rule, and name the configuration step that prevents the common residency failure. (Applies the entry-point decision matrix.)

Reveal model answer

Primary: AWS Bedrock, configured for explicit in-region execution (not global endpoint), because the partner is AWS-standardized and the residency rule governs. Verify the specific compliance requirement (HIPAA BAA or data sovereignty) is satisfied by the Bedrock configuration in use. Secondary: Direct API for non-regulated back-end tasks where newest features matter and no residency rule applies. Configuration step: Set the region parameter explicitly in the Bedrock client; do not rely on default endpoint resolution.

**Decision 6 · Outcome document.** Name the before-and-after business metric and the auditable control that make the document usable for the CFO's expansion case. (Applies the customer outcome documentation template.)

Reveal model answer

Before metric: Average time from nurse dictation to completed, clinician-authorized clinical note (baseline measured before deployment). After metric: Same metric post-deployment, using the same measurement definition. Auditable control: The clinician-authorization log; every note has a timestamped authorization record tying the clinician, note, and interaction, making the before-and-after comparison auditable rather than asserted.

**Decision 7 · Phase transition.** Name the artifact that gates the next phase transition for this brief and judge whether that gate is satisfied. (Applies lifecycle-phase gating.)

Reveal model answer

Gate artifact: The outcome document with before-and-after metric, auditable control, and measurement owner named; this gates the transition from the current deployment phase to the expansion decision the CFO is being asked to make. Judgment: The gate is not yet satisfied at week four; the before metric exists from baseline, but the after metric requires enough post-deployment runtime to measure. The outcome document cannot be completed until sufficient data has accumulated. The correct action: name the measurement owner, confirm the control is logging, and schedule the outcome document completion at a defined post-launch milestone.

Mark all decisions complete
← Previous
Screen 17 of 20
☰ CONTENTS
Next →
