# ADR 0005. HITL review as a Step Functions wait, resumed by CLI (PoC)

## Status
Proposed — depends on ADR 0004

## Context
Not every claim should auto-record. Insurance requires a human gate on
material or uncertain decisions, and the validator already produces the
signals to route on. `../components/logical-components.md` reserved a
"Review Flagged Claim" component as an extension; this ADR promotes it.

The PoC must prove the *review mechanism* — pause, present, decide, resume,
and record the human decision with provenance — without building a reviewer
UI or a managed review workforce first.

## Decision
HITL is a **`waitForTaskToken` state** after a routing (Choice) state:

- **Routing / escalation policy** (redline-able defaults):
  | Signal | Route |
  |---|---|
  | Schema-invalid / empty required field(s) | Human review |
  | `ungrounded=true` (no policy citation) | Human review |
  | PII leaked into summary (`pii_*`) | Block → human review (never auto-approve) |
  | `claim_amount` > **$10,000** | Human review (material-payout gate) |
  | Clean: schema-valid, all fields, grounded, ≤ threshold, no PII | Auto-approve → Record |
- **PoC mechanism = manual token-resume via CLI.** Flagged results land under
  a `pending-review/` S3 prefix; an operator inspects the extracted JSON +
  summary + citations + flags, then runs a `decide` CLI command that calls
  `SendTaskSuccess` with `approve` / `correct` / `reject` and a `reviewer_id`.
- **Timeout:** a 7-day heartbeat/timeout on the token; on expiry the claim is
  marked `review-expired` and surfaced for manual escalation.
- **Audit:** the provenance tuple gains
  `review: {decision, reviewer_id, timestamp, field_changes[]}` — the model's
  output and the human's correction are recorded **distinctly**.

Rejected for the PoC: **notification + approval UI** (SNS/web form) and
**Amazon A2I** (managed review workforce) — both are named production
promotes; the CLI uses the **same** `SendTaskSuccess(taskToken, decision)`
contract they would, so the promote is additive, not a rewrite.

Justification:

- Same token contract as a real UI/A2I ⇒ minimal throwaway.
- Near-zero infra; manual-deploy friendly.
- A Step Functions task token is single-use, so a double resume cannot
  double-record (idempotency, card C9).

## Consequences
Good: cheap, audit-rich, on the production path.
Bad: no reviewer UX in the PoC (operator-run CLI); no per-reviewer authz yet
(the operator is trusted) — production scopes review with **Amazon Verified
Permissions / Cedar** ("only an examiner in the matching line-of-business /
jurisdiction may review"); the review worklist is an S3 prefix, not a
queryable queue (production → a DynamoDB worklist behind the UI/A2I).

## Compliance
Fitness: every human-reviewed claim records `reviewer_id`, `decision`,
`field_changes`, and `timestamp`; auto-approve fires **only** on the clean-path
predicate above; the token timeout is enforced; no claim is recorded as
approved without either the clean-path predicate or a human `approve`.

## Notes
Author: aws-ai-design (provisional kata run)
Approved by / date:
Last modified: 2026-09-21
