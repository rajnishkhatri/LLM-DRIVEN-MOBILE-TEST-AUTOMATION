# Inside Ari - gate first, rules before models, receipts on every answer — detail tables

> Opened from the Context view: every turn passes the gate, the two-stage router spends a model only on ambiguity, and every answer leaves a provenance record. Module-coloured elements run in the one Ari quantum.

**Locator:** this view opens `ARI` from `01-context`. It is a **completeness reference** at this grain.

## Node explainer (numbered — matches the `[n]` on the canvas)

| # | Node | Detail the short label hides |
|---|------|------------------------------|
| 1 | SURF | thin embed; SSE over HTTP; per-request auth (no long-lived socket) |
| 2 | GATE | validates signed token {user, tenant, role}; stamps immutable RequestContext structural test: no adapter callable without RequestContext output screen on the way back; control errors fail closed ADR 0003 ACCEPTED |
| 3 | RTR | rule ladder: tier + weighted score + margin threshold and margin derived from the golden-set sweep, committed with their eval report ADR 0001 ACCEPTED (deterministic-first; reversal = a dial, road back = shadow + policy canary) |
| 4 | SQD | Agent Squad classifier behind the model seam |
| 5 | SYN | tuple: route, sources + versions, confidence, model + prompt version, entitlement scope |
| 6 | MP | typed outcomes: ok / throttled / timed-out / invalid / guardrail-intervened model = config; every model or prompt change is a release today: Claude on AWS Bedrock; temperature 0 + recorded fixtures offline ADR 0002 ACCEPTED |
| 7 | OA | on failure the model does NOT answer the data question - honest degrade + ticket offer FIXTURE-BACKED in demo |
| 8 | CA | (Confluence) static how-to docs FIXTURE-BACKED in demo |
| 9 | JA | idempotency key = conversation + turn id (C9) the floor under every other capability FIXTURE-BACKED in demo |
| 10 | AP | PLANNED - contract only, no implementation in v1 contract: pre-action approval (routed by stakes) + idempotency key + audit event |
| 11 | DLOG | the record IS the truth: a stochastic answer cannot be reconstructed by replay |
| 12 | EVAL | every failure-taxonomy class carries at least one eval cross-tenant probes must stay at zero violations |
| 16 | BR | today: Claude on AWS Bedrock; GPT-4o as config (ADR 0002) live toggle only; demo runs offline on fixtures |
| 17 | OBS | today: CloudTrail + CloudWatch; portable to any cloud PLANNED - not in demo scope |

## Edge detail

| # | Edge | Mode | Claim |
|---|------|------|-------|
| 24 | JA → JIRA | sync | creates idempotent tickets in Support desk (as-the-user; idempotency key = conversation + turn id) |
| 21 | OA → SYN | sync | returns governed data to Answer synthesis (source + version ids feed the provenance tuple) |
| 22 | CA → SYN | sync | returns cited passages to Answer synthesis (citation ids feed the provenance tuple) |
| 23 | JA → SYN | sync | returns ticket receipt to Answer synthesis (ticket id + idempotency key recorded) |

## Not shown for brevity

- **Guarded-call wrapper** — every adapter call passes one wrapper (timeout C7, degrade C11, retry-reads-only C2, idempotent write C9); carried in adapter detail rows, not drawn as a box

## Key

- rectangle = a grouping of code inside a container (C4 component)
- double-bordered rectangle, `EXT:` = an external system we don't own
- cylinder = a data store (used for datastores ONLY)
- dash-bordered rectangle = a runtime process, not a deployable
- orange fill = unresolved production evidence (provisional/pending)
- module-a colour = the same module tracked by colour across every view
- module-b colour = the same module tracked by colour across every view
- solid arrow = synchronous call
- dashed arrow = asynchronous message/event
- `[Type]` under a name = the element's C4 type (container/component)

