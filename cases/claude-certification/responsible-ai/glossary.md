---
type: reference
title: 'Glossary'
description: 'Module 3 key terms from BAA through training-time alignment versus inference-time control: fail closed, injection points, judge model, control register, and related safety vocabulary.'
tags: [claude, certification, responsible-ai]
---

Glossary
The key terms used across this module, in alphabetical order. Click a term to expand its definition.

BAA (Business Associate Agreement)
A contract under HIPAA that permits a vendor to process protected health data on a covered entity's behalf, defining each party's safeguards and liabilities. Without it, handling that data through the vendor is non-compliant regardless of the technical controls.
Consent fatigue
The breakdown of oversight when a reviewer is asked to approve too many actions, so they approve almost everything without real review. It is the failure mode of routing every decision to a human. Verify Anthropic's current framing against anthropic.com.
Constitution
The written document Anthropic uses during training to shape Claude's values and behavior, stating a priority order of broadly safe, ethical, compliant with guidelines, and genuinely helpful. It shapes the model's trained behavior but does not encode any one deployment's domain policy. Verify the current version against anthropic.com.
Control register
A table that maps each compliance obligation to its technical control, an accountable owner, and an evidence artifact, so a regulated deployment can be audited as a register rather than asserted as a narrative.
Data residency
The requirement that data is processed and stored within a specified geographic region, including copies in logs and caches. It is the control behind many data-sovereignty obligations.
Decision logging
Capturing the inputs, retrieved context, model output, and routing for each decision, keyed so one decision can be replayed and explained later. It is the same observability instrumentation pointed at the question of why a specific decision happened.
Evidence artifact
The concrete proof a security and legal reviewer accepts that a control is live: a signed agreement, a configuration screen, an authorization record, or a returning log query. A control named in a design document with no artifact is a claim, not proof.
Fail open vs fail closed
How a guardrail behaves when it itself errors. Fail open passes traffic through unscreened, while fail closed blocks until the control is healthy. For safety controls, failing closed is the deliberate choice, because a control that silently passes traffic offers no protection.
FedRAMP
The FedRAMP classification (low, moderate, or high) that sets the security controls a cloud service must meet to handle US government workloads of a given sensitivity. The required level is set by the workload, and the delivery route must be authorized at or above it.
GDPR
The EU's data protection law regarding how organizations collect, process, store, and transfer the personal data of people in the EU and EEA. It grants individuals rights over their data and requires a lawful basis for processing, data minimization, and protection.
HIPAA
A US federal law setting standards for protecting individuals' health information. It governs how protected health information (PHI) is used, disclosed, and safeguarded by covered entities and their business associates. When a vendor processes PHI on a covered entity's behalf, HIPAA requires a Business Associate Agreement (BAA) defining each party's safeguards and liabilities. In this module it drives the requirement to deliver through a HIPAA-ready plan or first-party API under a signed BAA.
Human-in-the-loop routing
A rule that sends decisions to a person based on confidence, reversibility, and the cost of a wrong answer, rather than by volume, with the reviewer placed pre-action, post-action, or in a sample.
Injection point (fairness)
A specific place where unequal outcomes can enter a system: the retrieval corpus, the prompt framing, the chosen examples, or the downstream routing. Naming them makes fairness an architecture property you can instrument rather than a model attribute you assume.
Input screening
A check that runs before the model call to decide whether a request should reach the model, using a model-based classifier for fuzzy intent like jailbreaks or a deterministic rule for crisp patterns.
Judge model
A model used to score or classify another model's output, for qualities like toxicity or policy compliance that a deterministic rule cannot reliably encode. It can be evaded, which is why it is chained with deterministic checks.
Output screening
A check that runs before the response reaches the user, judging the generated content with a model for qualities like toxicity or a validator for known strings and schema violations.
Tool-call authorization
A check before any action with a side effect that decides whether this caller may perform this action in this context. It should be deterministic, an allowlist plus identity and scope, so the decision is provable and auditable.
Training-time alignment vs inference-time control
Training-time alignment is the safe behavior baked into the model for every user. Inference-time control is the screening and authorization you add at request time to enforce rules specific to your deployment. Conflating the two leaves deployment-specific rules unenforced.
← Previous
Screen 20 of 22
☰ CONTENTS
Next →
