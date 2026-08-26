---
type: notes
title: 'Turning each compliance obligation into a control with evidence'
description: 'A regulation states an outcome; you supply the control, a named owner, and a living evidence artifact. A compliant entry point is a prerequisite, not proof the rule is being followed.'
tags: [claude, certification, responsible-ai]
---

Turning each compliance obligation into a control with evidence
The compliance layer of the integration model used the governing obligation as a pre-filter: HIPAA, GDPR, FedRAMP, attorney-client privilege, or a data-residency policy each ruled delivery routes and entry points in or out before cost or engineering preference entered the conversation. That work gets you to an entry point and a route that survives the obligation, but the next step is narrower and harder. Each surviving obligation must now become a control with a named owner. A reviewer does not treat a compliant entry point alone as proof that the rule is being followed. They also ask who owns the control and what evidence shows its holding in practice.

A regulation states an outcome, but you supply the control and the proof it is operating
Frameworks such as GDPR, HIPAA, and FedRAMP state outcomes, not implementations. They say what must be true: that protected data must be handled a certain way, that access must be controlled, and that processing must happen in an authorized environment, but they leave the technical control to you. Each obligation becomes three things you own: a specific technical control that achieves the outcome, an owner accountable for it, and an evidence artifact that shows it is live. Always remember to include the evidence artifact; this is what the reviewer will check and is the most often missed.

Mapping obligations to controls, owners, and evidence
Mapping obligations to controls, owners, and evidence
Obligation (framework)	Technical control	Evidence a reviewer accepts	Owner
Protected health data handled under an agreement (HIPAA)	Use only a HIPAA-ready Enterprise plan or first-party API configuration covered by a signed Business Associate Agreement, with HIPAA compliance enabled and only eligible features in scope.	The signed BAA and the admin setting showing HIPAA compliance enabled, plus the eligible-feature list.	Security lead
US government workload at the required impact level (FedRAMP)	Deliver through an Anthropic-documented authorized route that meets the required impact level, not a non-authorized entry point.	The authorization record for the chosen route and confirmation that the workload runs exclusively on it.	Platform owner
Data handled and stored in an approved region (data residency)	Configure supported regional processing and storage for the approved region, and validate whether logs, caches, monitoring, and retention paths remain within the approved boundary.	The residency configuration and a data-flow record showing where every copy lives.	Data owner
Decisions reconstructable on demand (transparency, cross-framework)	The decision logging built in the fairness cluster, retained and queryable for the required period.	A sample reconstruction of one decision from the live log.	Architect
TRAINING USE VS RETENTION, TWO DISTINCT CLAIMS
Do not collapse training use and retention into the same claim: data may be excluded from model training by default while still being retained or monitored for logging, abuse prevention, legal compliance, or configured audit purposes.
The evidence artifact is what makes the handoff effective
The constraint-elimination reasoning from the integration work carries forward here. Back then you eliminated delivery routes that could not survive a constraint. Now you record, for each obligation, the control that satisfies it and the artifact that proves it.

A security and legal reviewer accepts proof that a control is live: a signed agreement, a configuration screen, an authorization record, or a returned log query. What they do not accept is a design document that identifies a control with no owner and no evidence; a control no one can demonstrate is indistinguishable from one that is not running.

COST · COMPLEXITY · RISK
Cost: Producing and maintaining evidence for every obligation is ongoing work. Configurations drift and artifacts go stale, so the register is revalidated on a regular cadence.
Complexity: A control, an owner, and a living evidence artifact per obligation is more governance than an entry point choice, and it spans security, legal, and platform owners who each must agree on who holds what.
Risk: A control specified with no owner and no evidence is invisible at the audit. It can stop operating with no one accountable, and the gap surfaces in review rather than in design, which is the most expensive place to find it.
← Previous
Screen 16 of 22
