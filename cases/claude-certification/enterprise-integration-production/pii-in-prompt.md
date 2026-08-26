---
type: failure-taxonomy
title: 'Watch-out: the PII field that went straight into the prompt'
description: 'Failure trace: a clinical intake summarizer put SSN and insurance ID in the user message. Application request logs captured PHI that the language task did not need.'
tags: [claude, certification, enterprise-integration-production]
---

The PII field that went straight into the prompt
THE DEMO TRAP FOR SKIPPING SECURITY
When the goal is to get a demo working quickly, the fastest path to a working Claude integration is to pass the data you have directly into the prompt. Adding a PII redaction layer, building a server-side identity injection, and instrumenting the observability stack all add time. They also add no visible capability, as the system works without them. The cost of skipping them does not appear until the first audit.
A trace excerpt from a regulated-industry deployment
The trace below is a composite of a field pattern in a healthcare-adjacent deployment. The team built a patient intake summarization tool. The summarization worked correctly. The data handling did not.

API request: captured in the application layer's request logs
Model: claude-sonnet-4-6
System: "You are a clinical intake summarizer. Extract key presenting concerns, medications, and allergies from the intake form."
User: "Patient: Jane Doe, DOB: 1978-04-12, SSN: 123-45-6789, Insurance ID: BCB-88712. Chief complaint: chest pain, onset 3 days ago..."
The SSN and Insurance ID are in the user message and therefore travel with the API request, exposed to any application-layer request logging, despite not being needed to produce the summary. The system prompt asks for presenting concerns, medications, and allergies. None of those require the patient's SSN or Insurance ID to be in the context window.

What broke
The tool worked as designed, but the data handling was wrong. Several fields that qualify as Protected Health Information (PHI) under HIPAA, the patient's name, date of birth, SSN, Insurance ID, chief complaint, medications, and allergies, were passed into the API call and captured in plaintext in the application layer's request logs. These were not necessary for the language task. When the deployment was reviewed prior to production certification, the application layer's request logs contained thousands of entries with patient SSNs in the user message field.

The fix was a data architecture change: a server-side redaction step that strips non-essential PII fields before the Claude call, and a retrieval function that supplies only the fields the language task needs. Both should have been in the original design.

WHAT TO WATCH OUT FOR
The data handling architecture was designed around what was convenient to pass, not around what was necessary to pass. Necessity is the correct filter: if the field is not required for the language task Claude is performing, it should not be in the context window.
← Previous
Screen 12 of 21
☰ CONTENTS
Next →
