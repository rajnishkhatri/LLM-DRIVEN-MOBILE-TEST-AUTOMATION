---
type: reference
title: 'Glossary'
description: 'Module 2 key terms from 5xx errors through transient error: evals, caching, circuit breaker, data-residency pinning, RAG, p95, SSO, and related production vocabulary.'
tags: [claude, certification, enterprise-integration-production]
---

Glossary
The key terms used across this module, in alphabetical order. Click a term to expand its definition.

5xx errors
The class of HTTP status codes (500–599) indicating a server-side failure to fulfill an otherwise valid request. Common examples include 500 (Internal Server Error), 503 (Service Unavailable) and 529 (Overloaded Error). Usually transient and resolvable with retry and backoff, distinct from 4xx codes which indicate a client-side problem.
BAA (Business Associate Agreement)
A contract required under HIPAA between a covered entity (or business associate) and a vendor that handles protected health information on its behalf. The BAA specifies the safeguards the vendor will apply to PHI. For Claude deployments, BAA coverage is configuration-specific: the same surface may be BAA-covered on one delivery route and not on another. Check coverage by configuration, not by product.
Caching
Caching stores reusable prompt content so the system does not need to reprocess it on every request. It is most effective when the system prompt is long and stable, reducing both token cost and response latency; the response you receive is identical to what you would get without caching.
Circuit breaker
A reliability control that monitors the error rate on a downstream dependency and, when errors exceed a defined threshold, blocks further requests to that dependency for a cooldown window so that one degraded component does not consume the calling system's capacity. Sits at the service boundary, distinct from retries (close to the API call) and fallback chains (in the orchestration layer).
Data-residency pinning
Configuring the integration so that model execution happens in a specified geographic region, typically to satisfy sectoral regulations, or internal data-residency policy. Pinning is implemented at the delivery route level on CSP-mediated integrations. The pin must be set at the integration layer and verified at request time, not assumed by the entry point choice alone.
DPA (Data Processing Agreement)
A contract between a data controller and a data processor defining how personal data may be handled on the controller's behalf, including processing scope, security obligations, sub-processor terms, and breach notification.
Eval
A structured test set used to measure whether a model is performing well enough on a defined task. An eval pairs inputs with expected outputs or quality criteria, runs them against the model, and produces a score you can compare across model versions, prompts, or configurations. Evals are how teams decide whether a change is an improvement or a regression before it reaches production.
Exponential backoff
Exponential backoff is a retry strategy where, after a failed request, the system waits before trying again and each successive wait is longer than the last, typically doubling each time.
GDPR (General Data Protection Regulation)
The European Union (EU) regulation governing the processing of personal data of individuals in the EU and European Economic Area (EEA). Establishes lawful-basis requirements, data subject rights, controller and processor obligations, and fines up to 4% of global annual turnover.
Generator-verifier loop
A two-stage pattern in which a model-generated output is checked by a second pass before being used downstream. The verifier may be a deterministic code-based check (schema validation, comparison against an authoritative value) or a second model call scoped to evaluation. Used as a compensating control where the underlying task requires more precision than single-pass generation reliably provides.
Hallucination rate
The percentage of responses in which the model invented, inferred, or stated information that was not supported by the input, source data, or allowed logic.
Live state
Data that changes during the lifetime of a conversation or process: an order status, an inventory count, a price, a calendar slot, a user's current session. Live state is distinct from static reference material because the correct answer at 10:00 a.m. may be wrong by 10:05. Systems that need live state require a direct lookup against the source of truth, not a stored snapshot.
Median latency
Median latency is the time it takes to complete the middle request in the distribution, which means 50% of requests are faster and 50% are slower. It is also called p50 latency.
p95 (95th-percentile latency)
The latency value below which 95% of requests complete, with the slowest 5% falling above it. Used as a production design target because SLA breaches and user abandonment are driven by the slow tail of the distribution rather than the median.
PHI (Protected Health Information)
Individually identifiable health information held or transmitted by a covered entity or business associate under the US Health Insurance Portability and Accountability Act (HIPAA). Processing PHI requires a Business Associate Agreement with any third party that handles it.
RAG (retrieval-augmented generation)
A pattern in which a knowledge corpus is chunked and indexed in a preprocessing step, and at query time the chunks most relevant to the user input are retrieved and passed into the model's context. Suited to static or slow-moving knowledge such as manuals, internal documentation, and regulatory text. Not suited to live transactional state, where retrieval returns a snapshot that may already be stale and a tool call to the system of record is the correct mechanism.
Rate limit
A server-enforced cap on the number of requests a client may make within a defined time window. When the cap is exceeded, the server rejects further requests (typically with HTTP 429) until the window resets. A rate-limit response indicates throttling rather than failure and is a transient condition that resolves with backoff.
Regex
Regex stands for regular expression. It is a rule-based pattern used to find or validate text that matches a specific format, such as email addresses, phone numbers, Social Security numbers, or credit card patterns.
Schema
The required structure, format, and rules for the output. This defines what fields must appear, their data types, allowed values, and how the response should be organized.
SSO (single sign-on)
An authentication arrangement in which a user signs in once to a central identity provider and gains access to multiple downstream applications without re-authenticating.
Structured fields
Structured fields are those which require specific outputs that must be populated in a defined format, such as customer name, invoice number, date, amount, or policy ID. These are discrete data elements, not free-form narrative text.
Timeout
A failure mode in which a request does not receive a response within the client's or server's configured wait period and is terminated. Typically caused by transient server load, network latency, or a downstream dependency under stress, rather than a permanent fault.
Tool use
The capability that lets Claude call external functions, APIs, or services during a response instead of only generating text. The model decides when to invoke a tool, what arguments to pass, and how to use the result in its next step. Tool use is what turns Claude from a text generator into a system that can read files, query databases, search the web, or take action in other software.
Transient error
A transient error is a temporary failure that is expected to resolve on its own without any permanent fix, meaning if you try the same request again after a short wait, it will likely succeed.
← Previous
Screen 19 of 21
☰ CONTENTS
