---
type: reference
title: 'Strangler fig'
description: 'Incrementally replace a live system through a seam — usually an HTTP façade, sometimes an in-process abstraction or event interceptor — until the legacy can be retired. Covers cutover sequence, verified routing/shadow/rollback knobs, dual-write vs CDC, ACL as a companion, dual-path observability, and when a rewrite or a dumb proxy is the better tool.'
tags: [system-design-patterns, scaling, strangler-fig, migration, anticorruption-layer]
---

# Strangler fig

**See also:** [scaling strategies](ScalingStrategies.md) · [API gateway](ApiGateway.md) · [load balancing](LoadBalancing.md) · [sharding (B2)](../data-intensive-design/sharding-overview.md) · [replication logs / CDC](../data-intensive-design/replication-logs.md) · [event-driven dataflow](../data-intensive-design/event-driven-dataflow.md) · [idempotency](Idempotency.md) · [circuit breaker](CircuitBreaker.md) · [retry, backoff, and retry budgets](RetryBackoff.md) · [cloud patterns: gateway, ACL, strangler, outbox](../aws/ch08.md) · [catalog research (2026-09-13)](../../docs/research/sysdesign/b4-strangler-fig-external-research.md)

The Strangler Fig pattern is an **incremental-replacement mechanism**. A seam intercepts work that used to go only to a live legacy system and sends a chosen slice to a new implementation. Clients keep one URL. The legacy stays up for unmigrated behaviour and as a rollback target. The new system grows feature-by-feature (or asset-by-asset) until the legacy is a skeleton and can be switched off. The seam itself is transitional: Azure's last phase deletes it.

That is *migration*, not a runtime style. The destination can be microservices, a modular monolith, or another monolith on a new stack. [Scaling strategies (B1)](ScalingStrategies.md) add capacity; this card decides **how to leave a live system without a big-bang date**. [The gateway (C6)](ApiGateway.md) is the usual *physical* façade; this card owns the incremental-cutover *use* of that façade. Data extract is [sharding / SoR flip (B2)](../data-intensive-design/sharding-overview.md), not a second write from application code.

Quality attributes: **evolvability** (replace without a freeze), **risk** (rollback stays cheap while both paths exist), and **time-to-value** (a captured slice ships before the rewrite would). Costs: two systems to operate, a façade that is a new SPOF, dual-path observability you must invent, and a standing temptation to dual-write.

## Lineage and vocabulary

- **Fowler, original post (2004-06-29).** Queensland rain-forest metaphor: a fig seeds in the host, roots down, and eventually stands in the host's shape. Do **not** cut over on a big-bang date; grow the new system around the edges of the old. Cut-over rewrites overflow with risk; even old bugs often have to be re-implemented. Two named strategies: **Event Interception** (the fundamental seam) and **Asset Capture**. Closing design rule: **design today's system so it can be strangled tomorrow**. Renamed from *Strangler Application* to *Strangler Fig* on 2019-04-29 so usage kept the botanical root.
- **Fowler rewrite (2024-08-22)** is the living definition. Four activities (Ian Cartwright, Rob Horn, James Lewis; not a sequence): understand outcomes; break the problem into parts / find **seams**; deliver the parts so value arrives early; change the organization (Conway) so the new system does not calcify the same way. Transitional architecture that will later be deleted is *not* waste. Replacement-as-rewrite "go[es] down in flames most of the time."
- **Asset Capture (Fowler, same day 2004).** Cut over by *asset* (employee, trade, lease), starting with simple assets or ones the old system handles badly. Requires **bi-directional** migration so an asset that outgrows the new system can move back. Event Interception only for captured assets.
- **Event Interception (living text Cartwright / Horn / Lewis, 2024-03-05).** "If you are using the Strangler Fig pattern then you will also be using some form of Event Interception." Seams: message selectors, reverse proxies, API gateways, progressive enhancement in a legacy template, pre-commit DB triggers (extreme care), CDC, "swivel-chair" human interception. Case-study stages: dark-launch to datastore parity → intercept *reads* → intercept *writes* (new store becomes system of record) → migrate rules behind a legacy façade.
- **Branch by Abstraction (Fowler, 2014-01-07).** In-process cousin: an abstraction over a supplier, a second implementation, feature-flagged comparison, then delete the old supplier. Use when the seam is a *module*, not an HTTP edge.
- **Azure Architecture Center (GitHub `ms.date` 2026-05-29).** Four phases: insert a façade (most traffic still legacy); incrementally shift requests; decommission legacy (façade still in front); **remove the façade** (or keep it as a thin legacy-client adapter). Cross-system calls during coexistence: **use an ACL**. Database decomposition is ETL + CDC + **validate consistency before cutover**, then flip SoR — not two application writers.
- **AWS Prescriptive Guidance.** *Transform / Coexist / Eliminate.* Coexist = keep the monolith for rollback; put an HTTP proxy at the perimeter. Refactor Spaces was the AWS-shaped proxy (application = API Gateway + VPC link + NLB + resource-based IAM; `DEFAULT` + `URI_PATH` routes). Closed to new customers **2025-11-07**; the banner names **AWS Transform** as successor. Strategy Recommendations *plans* a 7-R move; it does not insert a façade.
- **Anticorruption Layer — companion, not a second card.** Evans (2003) named the isolating translation that speaks the new model's language to callers and the legacy model's language to the old system. Azure and AWS both prescribe an ACL *inside* a strangler when unmigrated callers must reach a migrated service whose interface has changed. ACL is **not** the façade, **not** hexagonal architecture, and **not** a gateway. [ch08](../aws/ch08.md) one-liner: the translator "preserv[es] the integrity of an application’s core business model."

## What the pattern is

```
client ──same URL──► seam (façade / abstraction / interceptor)
                         │
                         ├── slice still legacy ──► old system (rollback target)
                         └── captured slice     ──► new implementation
```

A **seam** chooses, per request or asset, which implementation owns the work. Clients do not change. The new system is allowed to be incomplete. Rollback is a routing change, not a restore, until you drop legacy objects.

## Variants (where the seam lives)

| Variant | Seam | Typical cutover unit | Trade-off |
|---|---|---|---|
| **HTTP façade** (Azure / AWS PG / C6 gateway) | Reverse proxy or API gateway in front of the monolith | Path, host, header, or weighted % of a *ready* route | Clients unchanged; proxy is a new SPOF / bottleneck (every official page warns). |
| **Branch by Abstraction** | In-process interface over a module | One supplier implementation | No extra hop; needs code access and tests; no independent scale. |
| **Event Interception** | Message router, reverse proxy, gateway, template script, trigger, CDC | Event type or asset id | Minimizes legacy edits; adds transitional components to operate. |
| **Asset Capture** | Content-based router + bi-directional migrator | One business asset | Fine-grained rollback; needs reverse migration or releases stall. |
| **Database strangler** (Azure) | ETL + CDC, then SoR flip | One bounded-context schema | Avoids dual-write races if CDC is the *only* writer to the copy; validation is mandatory. |
| **ACL hop** (companion) | Adapter / façade / translator at a *model* boundary | One migrated capability's leftover callers | Protects the new model; extra latency and a thing to decommission. |

These compose: a gateway façade for *external* calls + an in-monolith ACL for *internal* leftover callers is the AWS PG worked shape. Routing belongs in the façade; translation belongs in the ACL; domain rules belong in neither ([C6](ApiGateway.md) / ThoughtWorks overambitious-gateway Hold).

## Incremental cutover sequence

1. **Identify outcomes and seams** (Fowler 2024). AWS: DDD / event storming before premature splits — "when the domain isn't clear… you [can] get the service boundaries wrong."
2. **Insert the façade, 100% to legacy.** Refactor Spaces: the first route **must** be `DEFAULT`; it is created **ACTIVE**.
3. **Dark-launch / shadow** the new implementation to datastore parity. Shadow is *not* cutover: Istio / Envoy discard the mirrored response.
4. **Cut a slice.** Prefer a read path or a low-value asset first. Path-based 100% of `/users` is safer than 5% of *all* traffic if the new service only implements users.
5. **Canary %** on that slice (ALB weights, API Gateway canary, Istio `weight`) with an explicit rollback (weight 0 / canary 0 / route `INACTIVE`).
6. **Flip system of record** only after consistency checks (Azure). Until then the monolith DB or a CDC stream is SoR; the new DB is a follower. [Replication logs](../data-intensive-design/replication-logs.md) own the CDC mechanism.
7. **Rewire leftover callers** through ACL, then delete the ACL when the last caller has moved (AWS PG: ACL "must be decommissioned after all dependent services have been migrated").
8. **Eliminate** legacy objects (AWS verb) and then the façade (Azure phase 4).

Default routing % for a new strangler is **not 50**. Official sequences start at **0% new / 100% legacy**, then flip a *path* to 100% new, or ramp a canary on that path. A 50/50 split of *all* URLs is a misconfiguration unless both sides implement every URL.

## Dual-write is not a sync

Two independent writes from application code to legacy DB *and* new DB (or DB *and* a queue) look like a strangler shortcut. They are the **dual-write problem**.

Kleppmann (2015-05-27): two clients dual-writing key X leave store 1 at B and store 2 at A — **permanent** inconsistency (not eventual), no error, discovered months later. Partial failure (one write succeeds) is the other mode. Remedy: write *once* to an ordered log or primary DB and derive the second store as a consumer. That shape is transactional outbox + CDC (catalog ⊕B7; [ch08](../aws/ch08.md); [replication-logs](../data-intensive-design/replication-logs.md)).

Azure's DB sequence is CDC-shaped: legacy remains writer during sync; the new service writes the new DB only after validation. Keep any overlap window as short as possible and cover it with reconciliation — do not treat the overlap as a first-class design. AWS PG's "synchronizing agent" (microservice emits to a queue; agent updates the monolith DB) is eventual and labelled **tactical**. AWS mainframe coexistence describes an explicit dual-writes variant as suited to infrequent writes and frequent reads, with "ensuring data integrity and consistency" as the major drawback.

If a live mix of two writers is unavoidable, that is an [idempotency](Idempotency.md) problem plus reconciliation, not a routing problem.

## Placement

| Layer | What it intercepts | Rollback move |
|---|---|---|
| **Edge gateway** (C6; leftover Refactor Spaces; Azure APIM) | North–south HTTP | Deactivate route / set canary 0 / flip weight |
| **Mesh VirtualService / HTTPRoute** | East–west, or north–south if the gateway is in-mesh | Weight / `RequestMirror` / route delete |
| **ALB weighted target groups** | L7 forward to ≤ 5 groups | Weight 0 on the new group |
| **In-process ACL / Branch by Abstraction** | Remaining monolith callers | Feature flag / swap implementation |
| **Messaging / CDC** | State-change events | Stop the consumer; reverse-migrate assets |

[Load balancing (C5)](LoadBalancing.md) picks a *host* among healthy peers of one service. A strangler canary picks a *implementation* of a slice. Do not canary a path the new service cannot serve.

## Configuration

There is no Resilience4j of stranglers. The knobs are **platform** defaults for the seam, verified 2026-09-13.

### Routing %

| Control | Verified numbers | Strangler use |
|---|---|---|
| **Istio `HTTPRoute` / VirtualService `weight`** | Docs example: 25% / 75%; mirroring task uses `weight: 100` on v1 | Canary a *migrated path's* two backends |
| **ALB weighted target groups** | Weight **0–999** per group; **≤ 5** target groups per action (quota, not adjustable). Example 8+2 → 80/20; 9+1 → 90/10. "Slight delay" before the new weight is observed — no ms figure published. Target-group stickiness (example 12 h = 43 200 s) **overrides** the new weight for already-stuck clients | Instant-looking rollback is not instant for sticky clients |
| **API Gateway REST canary** | `percentTraffic` **0–100**. HTTP APIs: **no** canary | Version canary of the *proxy*, not a substitute for path-based extraction |
| **Refactor Spaces routes** | Types `DEFAULT` \| `URI_PATH`. First route **must** be `DEFAULT`. No other route may be ACTIVE unless DEFAULT is ACTIVE; DEFAULT may go INACTIVE only when every other route is INACTIVE. DNS refresh at the name's TTL, or **every 60 s** when TTL < 60 s | Path extraction with an instant traffic-off switch |

### Shadow traffic

| Control | Verified behaviour |
|---|---|
| **Istio `mirror` + `mirrorPercentage`** | Fire-and-forget; sidecar **does not wait**; responses discarded. Host/Authority gets **`-shadow`**. `mirrorPercentage.value` 0–100; **if the field is absent, 100% is mirrored.** |
| **Envoy `RequestMirrorPolicy`** (docs 1.40.0-dev) | Same fire-and-forget; all normal stats on the shadow cluster. Host altered by appending **`-shadow`** (disable with `disable_shadow_host_suffix_append`). `runtime_fraction` is a `FractionalPercent`; **denominator default 100** when you set a numerator. Omitted-fraction default is **not stated** — set the fraction explicitly. |
| **Gateway API `HTTPRequestMirrorFilter`** | Response never comes from the mirror `backendRef`; split among main `backendRefs` is independent |

Shadow **replays writes**. Only shadow idempotent / read paths, or put the shadow backend in a sink that cannot mutate shared SoR. The `-shadow` Host suffix is the log split; the new service must tolerate it or you rewrite the host.

### Rollback

| Mechanism | Verified rule |
|---|---|
| **Keep the monolith** | AWS PG *Coexist*: "Keep the monolith application for rollback." |
| **Route / weight / canary** | Refactor Spaces `INACTIVE`; ALB weight 0; API Gateway `percentTraffic` 0; Istio weight 100 back to the legacy subset |
| **Azure DB** | Cheap while CDC and legacy tables exist; after drop, restore + replay. "Treat the removal of legacy objects as a deliberate final step." |
| **Asset Capture** | Reverse-migrate the asset (Fowler 2004) |
| **Sticky canaries** | ALB target-group stickiness keeps clients on the old weight until `DurationSeconds` expires |

There is no vendor "default rollback timeout." The operational default is: **do not delete the old path until the new SoR has passed a measured consistency window.**

### ACL companion knobs

No numeric library defaults. Verified *considerations*: extra latency (load-test before production — AWS); scale the ACL with the target (AWS: ACL can become the bottleneck); [retries](RetryBackoff.md) + [breaker](CircuitBreaker.md) on the ACL hop; record it as technical debt if interim; correlation IDs + structured logs (Azure); do not put business rules or orchestration in the layer (Azure "not suitable" when semantics do not actually differ).

## Observability

A strangler without dual-path metrics is a silent split-brain. Emit at least:

| Signal | Why |
|---|---|
| **Request rate, error rate, latency — tagged `backend=legacy\|new` (and `shadow=true`)** | The only way to know a canary is worse than the host. Istio / Envoy already generate stats for the mirrored cluster. |
| **Per-route activation / weight / canary %** | Config drift: a `URI_PATH` left `INACTIVE`, an ALB weight that never flipped. |
| **Shadow vs primary comparison** | Status-class and latency delta on the same correlation / trace id. Host `-shadow` is the join key. Do **not** wait on the shadow. |
| **ACL translation errors and latency** | Azure: "track the success and latency of the translation." Field-mapping bugs show up here, not as 5xx from the new service. |
| **SoR lag and mismatch rate** | Row counts, checksums, or sampled entity diffs during CDC. Azure: "Validate consistency between both databases before cutover." |
| **Correlation IDs across façade → ACL → both backends** | Azure ACL + Azure Gateway Aggregation both require them. |
| **Business KPI on the extracted slice** | Fowler 2024: early value is the point. A latency win that drops conversion is a failed cutover. |

Alert shapes (own formulations on documented functions — **not** vendor PromQL): *new-backend error rate ≫ legacy on the same route for N minutes*; *CDC lag above the validation window*; *ACL p99 above the budget you load-tested*; *façade 5xx* (proxy as SPOF).

OpenTelemetry: use the normal HTTP server/client semantic conventions on **both** backends and the façade; there is no strangler-specific OTel signal. The design rule is **identical span names + a `backend` / `shadow` attribute**, so a single trace shows façade → legacy and the async shadow span.

## Tuning

| Knob | Too aggressive | Too timid | Starting point (sourced) |
|---|---|---|---|
| Slice size | Whole checkout in one go | Endless "just the health check" | One bounded context or one asset class (Fowler 2024 seams; Asset Capture) |
| Shadow % | 100% of mutating traffic | 0% (first production is the canary) | 100% of a **read** path, 0% of writes (Istio defaults to 100 if the field is absent — set it explicitly) |
| Canary % | 50% of all URLs | Perpetual 1% that never graduates | Path = 100% of that path after shadow parity; *then* 5–10% user canary if you need a live mix (ALB 9/1 example) |
| SoR flip | Same day as first 200s | Forever dual-running two writers | After ETL + CDC + **passing** consistency checks (Azure) |
| ACL lifetime | Permanent unowned adapter | Deleted while callers remain | Decommission when the last monolith caller is gone (AWS PG) |
| Façade lifetime | Eternal "temporary" gateway doing domain work | Yanked while legacy clients remain | Azure phase 4, or keep as a *thin* legacy adapter ([C6](ApiGateway.md)) |

## Worked calibration — storefront `/users` extract

Design drill (not a vendor SLA), matching the AWS PG storefront diagram (user / cart / account on one RDS):

Constraints: 2 000 rps storefront, user reads ~400 rps, user writes ~20 rps; cart still in the monolith and calls user; reporting still reads the monolith DB; rollback required within one change window.

| Step | Choice | Why |
|---|---|---|
| Seam | API Gateway in front; `DEFAULT` → monolith; `URI_PATH` `/users` + child paths → new service | Clients unchanged; path match is the unit AWS documents |
| Dark launch | CDC (Debezium-class) monolith `users` → new store; Event Interception stage-1 parity job | Avoids Kleppmann dual-write races |
| Shadow | Istio/Envoy mirror **GET** `/users*` at 10% then 100%; `mirrorPercentage` set explicitly; writes not mirrored | Fire-and-forget + `-shadow` Host; writes would mutate |
| Read cutover | Flip `/users` GET to 100% new; cart still hits monolith `UserService` | Read path is reversible by `INACTIVE` |
| ACL | `UserServiceAdapter` in the monolith maps cart's old DTO → new API | Cart team does not change in the same release (AWS PG motivation) |
| Write cutover | After mismatch rate stays at 0 for the agreed window, redirect writes; stop CDC **to** the new store; start tactical queue+agent **back** to monolith for reporting | Azure SoR flip; AWS "tactical" reverse sync |
| Canary of the write path | Prefer flag + 100% after rehearsal. A live mix of two writers is a dual-write and needs an idempotency key + reconciliation, which this drill refuses | Kleppmann |
| Rollback | `URI_PATH` → `INACTIVE`; do **not** drop monolith `users` tables in the same window | Azure "deliberate final step" |
| Eliminate | Cart rewritten to call the new service; ACL deleted; reporting reads the new store; monolith user code removed; consider removing the façade | AWS Eliminate |

## Testing and operating

- **Shadow before canary.** Assert status-class and latency delta on the `-shadow` join, then flip a *path*, not the whole URL space.
- **Rollback drill.** `INACTIVE` / weight 0 / canary 0 in the same change window as the flip. Time the sticky-session tail (ALB `DurationSeconds`) — those clients will not move with the weight.
- **SoR rehearsal.** Run the ETL + CDC + checksum / sampled-diff job to green *before* the write flip. After objects are dropped, rollback is restore + replay.
- **ACL load test.** AWS: the hop can become the bottleneck. Exercise retries and the [breaker](CircuitBreaker.md) on the ACL, not only the new service.
- **Kill the façade's domain logic.** If a route starts composing or mapping fields, that work belongs in the ACL or a domain service ([C6](ApiGateway.md)).
- **Watch the organization.** Fowler 2024: an unchanged Conway structure is how the new system becomes tomorrow's unstrangleable legacy.

## Failure modes of the strangler itself

- **Façade as SPOF / bottleneck** — Azure, AWS PG (both pages), C6. Mitigate with a Multi-AZ managed gateway and load tests; do not add business logic that makes it unscalable.
- **Façade falls behind the migration** — Azure "Make sure that the façade keeps up." Stale routes send users to deleted monolith methods.
- **Wrong granularity** — canary of *all* traffic when only `/users` is ready; or one ACL/breaker over many independent capabilities ([C1](CircuitBreaker.md) resource differentiation).
- **Dual-write split-brain** — Kleppmann permanent inconsistency; Azure expensive rollback after DROP.
- **Shadow side effects** — emails, charges, inventory decrements from mirrored POSTs.
- **ACL as a new monolith / bottleneck** — AWS scale warning; C6 overambitious-gateway if the gateway *is* the ACL.
- **Sticky sessions hide a rollback** — ALB target-group stickiness.
- **DNS lag** — Refactor Spaces refreshes at TTL (floor 60 s). A service URL change is not instant.
- **Unchanged organization** — Fowler 2024: the new system becomes tomorrow's legacy.
- **Unclear domain** — AWS: premature microservice boundaries are expensive. Extracting first, then discovering the bounded context, is how you buy a distributed monolith.
- **Code-access assumption** — Azure and AWS both: you cannot redirect *internal* leftover calls or disable migrated features without modifying the monolith. External-only façades still work if every client is HTTP and you never need to change the legacy.

## When not to use

| Situation | Source | Prefer |
|---|---|---|
| **Greenfield** — no live system to wrap | Implicit in every definition. AWS contrasts greenfield design patterns with strangler for brownfield | Design the destination style directly; still make the new system strangleable (Fowler 2004 closing rule) |
| **Tiny / simple system** | Azure: replacing the whole system is simple. AWS PG: "more efficient to rewrite" | Big-bang rewrite or replace |
| **Requests cannot be intercepted** | Azure + AWS PG identical | Branch by Abstraction (needs code) or accept a hard cutover |
| **No source access, and you need to disable leftover internal calls** | Azure / AWS | External façade only, or a Legacy Mimic that *is* the old interface |
| **Must fully decommission the original quickly** | Azure | Planned cutover with a freeze, not a multi-year fig |
| **No semantic gap** | Azure ACL "not suitable" | A dumb proxy, not an ACL |

## Trade-offs

| Buy | Pay |
|---|---|
| Incremental value; rollback is a route flip while both paths exist | Two systems to operate; transitional architecture you must later delete |
| Clients keep one URL | Façade is a new SPOF / bottleneck; stale routes after extract |
| Shadow + path canary before SoR flip | Shadow replays writes; sticky sessions hide a rollback |
| ACL protects the new model from leftover callers | Extra hop; field-mapping bugs; a thing that becomes a monolith if you leave it |
| CDC / outbox instead of dual-write | SoR flip is a deliberate event, not a Tuesday deploy |
| Design today's system to be strangleable tomorrow | Seams and Conway changes you would rather skip on a greenfield |

The [gateway](ApiGateway.md) decides **where the seam lives**. This card decides **what traffic moves, when SoR flips, and how you roll back**. [CDC](../data-intensive-design/replication-logs.md) decides **how the second store is derived**. [Idempotency](Idempotency.md) is what you need if you ignore that and write twice. Coordinate all four; do not treat "put a gateway in front" as a complete migration strategy.

## Sources

Verified 2026-09-13; the full URL list, per-claim provenance, and the items deliberately left out are in the [external research note](../../docs/research/sysdesign/b4-strangler-fig-external-research.md).

- Canon: Fowler *Original Strangler Fig Application* (2004-06-29; rename 2019-04-29); Fowler *Strangler Fig* (2024-08-22); *Asset Capture* (2004-06-29); Cartwright / Horn / Lewis *Event Interception* (2024-03-05); Fowler *Branch by Abstraction* (2014-01-07); Stevenson & Pols, XP 2004 (title/pages only).
- Cloud checklists: Azure *Strangler Fig Pattern* and *Anti-Corruption Layer* (2026-05-29); AWS PG *Decomposing monoliths* (Transform / Coexist / Eliminate) and *Strangler fig* / *ACL* cloud-design-pattern pages; Migration Hub Strategy Recommendations and Refactor Spaces (new-customer close 2025-11-07).
- Dual-write: Kleppmann, *Logs for Data Infrastructure* (2015-05-27); Confluent dual-write problem; [ch08](../aws/ch08.md) transactional outbox + CDC.
- Knobs: Istio VirtualService / mirroring; Envoy `RequestMirrorPolicy` 1.40.0-dev; ALB weighted target groups + load-balancer limits; API Gateway REST canary; Refactor Spaces `CreateRoute` / `UpdateRoute`.
- This tree: [ApiGateway.md](ApiGateway.md) (façade only — not rewritten); [ch08.md](../aws/ch08.md); [replication-logs.md](../data-intensive-design/replication-logs.md); [sharding-overview.md](../data-intensive-design/sharding-overview.md).
