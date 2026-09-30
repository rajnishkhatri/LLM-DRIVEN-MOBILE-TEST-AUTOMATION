# Ari - one governed assistant across Ripple Treasury's four modules — detail tables

> One front door: every treasury question answered with the asker's own entitlements - data, how-to, or a human ticket. The Ari box opens in the Container view.

## Node explainer (numbered — matches the `[n]` on the canvas)

| # | Node | Detail the short label hides |
|---|------|------------------------------|
| 1 | USR | multi-tenant customers volume/SLO: UNKNOWN (needs-input, question for Dana) |
| 2 | SURF | thin embed passes a signed user token all trust stays server-side |
| 3 | ARI | ACCEPTED: one architecture quantum, hexagonal modular monolith (ADR 0001) pillars: router reliability, evals as acceptance, central governance (opened in the Container view) |
| 4 | OMNI | NL compiled to governed queries on the semantic layer (live state, not RAG) FIXTURE-BACKED in demo |
| 5 | CONF | (Confluence) static how-to docs, retrieved with citations FIXTURE-BACKED in demo |
| 6 | JIRA | (Jira Service Management) ticket creation - the degradation floor FIXTURE-BACKED in demo |
| 7 | BR | today: Claude on AWS Bedrock; GPT-4o as config (ADR 0002) offline fixtures by default; live toggle only |
| 8 | OBS | today: CloudTrail (infra audit) + CloudWatch (decision log, metrics, alarms, dashboards) portable to any cloud; PLANNED - not in demo scope |

## Edge detail

| # | Edge | Mode | Claim |
|---|------|------|-------|
| 11 | ARI → BR | sync | invokes eval-gated models on Model inference (model = config behind the ModelPort; every swap gated by the golden set) |
| 12 | ARI → OBS | async | ships audit records + metrics to Audit & telemetry (async; decision log + metrics/alarms/dashboards; PLANNED) |

## Key

- stadium/pill = a person or role (actor)
- heavy-stroke rectangle = the software system in focus
- double-bordered rectangle, `EXT:` = an external system we don't own
- solid arrow = synchronous call
- dashed arrow = asynchronous message/event

