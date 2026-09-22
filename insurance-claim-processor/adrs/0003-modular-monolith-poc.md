# ADR 0003. Ship a modular monolith; defer event-driven ingest

## Status
Proposed

## Context
Skill 1.1.1 asks for a processing workflow. Alternatives: one Python
package invoked by CLI, S3→SQS→Lambda, Step Functions, per-component
microservices, AgentCore.

## Decision
We will implement the workflow as a modular monolith (one package, DI
clients) for the PoC, with module boundaries matching the logical
components. We will not introduce a queue, Step Functions, or extra
network hops until volume or HITL makes in-process failure loss
unacceptable.

Justification:

- **Testability / time to market:** three sample docs do not amortize a
  state machine.
- **Integrity:** validator and cascade stay in-process, visible.
- **Last responsible moment:** the same pipeline function can become the
  SQS worker without rewriting Extract/Validate.

## Consequences
Good: offline tests cover the real path.
Bad: a crashed CLI loses in-flight work (S3 packet remains — Land is
durable; Record may be missing). Production must add the queue + DLQ
(style-decision hybridization). Flask UI is an optional extra, not this
ADR.

## Compliance
Package layout matches the component table. No `boto3.client` at import
time (aws-ai-build DI rule).

## Notes
Author: arch-decide (provisional kata run)
Approved by / date:
Last modified: 2026-09-20
