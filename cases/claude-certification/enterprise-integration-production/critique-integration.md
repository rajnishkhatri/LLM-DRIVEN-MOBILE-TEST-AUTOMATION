---
type: validation-walkthrough
title: 'Checkpoint: critique the integration diagram'
description: 'Find the identity, data-handling, observability, and entry-point problems in a multi-tenant customer-service diagram. Leave sound components unselected.'
tags: [claude, certification, enterprise-integration-production]
---

Critique the integration diagram
The diagram below shows a Claude deployment for a customer-service agent at a multi-tenant SaaS company. Review the labeled components and connections, and select every one that represents an integration problem.

Select all problems. Leave sound components unselected.

✓
PROBLEM
Claude Code used as the backend for the customer-facing chat product
↓
↓
↓
✓
PROBLEM
Shared API key used for all tenants
✓
PROBLEM
Capability check based on "I am a premium customer" in the user message
✓
PROBLEM
Account number and email passed in the user message and appearing in request logs
↓
↓
↓
✓
SOUND
Server-side authentication layer in front of the API
↓
✓
SOUND
Tenant data isolated per tenant at the storage layer
↓
✓
PROBLEM
Claude response passed to the downstream CRM with no logging at the integration layer
Check answers
Skip for now
ALL CORRECT.
You read the integration cleanly. The five problems span the layers the decision table covers: identity (shared key, forged role), data handling (PII in the message, unlogged response), and entry-point selection (Claude Code as a product backend). Each has a server-side pattern that fixes it.
← Previous
Screen 13 of 21
☰ CONTENTS
