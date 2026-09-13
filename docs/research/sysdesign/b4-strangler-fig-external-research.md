---
type: research
title: 'Strangler fig — external research (2026-09-13)'
description: >-
  Source-verified research backing catalog B4: Fowler 2004/2024 strangler fig,
  incremental cutover via a façade, AWS Refactor Spaces / Strategy / Prescriptive
  Guidance, dual-write risks, routing and shadow knobs, rollback, dual-path
  observability, and Anticorruption Layer as a companion (not a second card).
tags: [research, system-design-patterns, B4, strangler-fig]
---

# Strangler fig — external research (2026-09-13)

> **What this is.** The evidence pass for catalog **B4** (Group B, full
> operational / CircuitBreaker depth bar). The Concept (when written) carries
> the distilled result; this note keeps verified facts, defaults, and URLs.
>
> **Method.** Primary pages fetched 2026-09-13. Paraphrase; numbers and
> identifiers reproduced exactly. Items that could not be verified are in
> **Uncertain / left out** and are **not** to be asserted in the Concept.
>
> **Existing notes in this tree** (cite; do not rewrite):
> [aws/ch08.md](../../../cases/aws/ch08.md)
> (one-paragraph Strangler fig + Anticorruption layer under *Other Cloud
> Architecture Patterns*), [C6 API gateway
> research](api-gateway-external-research.md) (the gateway as a routing
> façade), [B7 CDC / outbox](../../../cases/aws/ch08.md)
> (transactional outbox + CDC as the dual-write alternative).

---

## 1. Scope and non-goals

**This note owns** the incremental-replacement *mechanism*: a seam (usually an
HTTP façade, sometimes an in-process abstraction or an event interceptor)
that lets a new implementation grow around a live legacy system until the
legacy can be retired. Operational depth: cutover sequence, routing and
shadow knobs, rollback, dual-path observability, dual-write / data-sync
risks, and when the pattern is the wrong tool.

**Companion, not a second card — Anticorruption Layer (ACL).** Evans, *Domain-
Driven Design* (2003), named the isolating translation layer that speaks the
new model's language to callers and the legacy model's language to the old
system. Azure and AWS both prescribe an ACL *inside* a strangler when
unmigrated callers must reach a migrated service whose interface has
changed. ACL is **not** the façade, **not** hexagonal architecture (E8), and
**not** a gateway (C6). This note summarizes ACL only as far as the strangler
needs it; a full ACL card is out of scope.

**Stays in sibling catalog ids**

| Id | Why it is not this card |
|---|---|
| **E1 Monolith** | The *starting* style. B4 is a migration *from* a monolith (or any live system), not a style definition. |
| **E10 Modular monolith** | A cheaper *destination* or intermediate quantum; extract modules in-process before (or instead of) network-splitting. |
| **E2 Microservices** | A common *destination*. B4 does not decide how many quanta or how they talk. |
| **E8 Hexagonal / ports-and-adapters** | A style for keeping a domain independent of adapters. ACL *uses* adapters/facades/translators; it is a DDD strategic pattern at a bounded-context boundary, not Cockburn's hexagon. |
| **C6 API gateway / BFF** | The usual *physical* strangler façade. C6 owns routing / aggregation / offloading / BFF. B4 owns the incremental-cutover *use* of that façade. |
| **B7 Outbox & CDC** | The preferred way to sync data *without* dual writes. B4 names the risk and points here. |
| **C1 Circuit breaker / C2 Retry** | Resilience of the ACL hop and the proxy. Do not restack those cards. |

**Non-goals.** Greenfield service design; scoring monolith-vs-microservices
(arch-style's four determinations); rewriting [aws/ch08.md](../../../cases/aws/ch08.md);
a second full ACL / hexagonal / gateway Concept.

---

## 2. Lineage / vocabulary

**Fowler, original post (2004-06-29), preserved as *Original Strangler Fig
Application*.** https://martinfowler.com/bliki/OriginalStranglerFigApplication.html
— Queensland rain-forest metaphor (2001 trip): a fig seeds in the host, roots
down, and eventually stands in the host's shape. Applied to rewrites: do
**not** cut over on a big-bang date; grow a new system around the edges of
the old over years. Two strategies named: **Event Interception** (the
fundamental seam) and **Asset Capture**. Motivation: cut-over rewrites are
"overflowing with risk"; even old bugs often have to be re-implemented.
Chris Stevenson (with Andy Pols) had just published a first paper at **XP
2004** (Garmisch-Partenkirchen, 6–10 June 2004) — Springer lists it as *An
Agile Approach to a Legacy System*, pp. 123–129; the paper body was not
fetched (§8). Value even if you stop early: Stevenson’s team had already
delivered useful functionality and ROI "more than many cut-over rewrites
achieve." Cost objection: Fowler is "not convinced" a strangler costs more,
because shorter cycles avoid the unused features a rewrite invents. Closing
design rule: **design today's system so it can be strangled tomorrow** —
"all we are doing is writing tomorrow's legacy software today."

**Rename (2019-04-29).** Original title was *Strangler Application*. Fowler
added "Fig" so usage would keep the botanical root and drop the violent
connotation of "strangler."

**Fowler rewrite (2024-08-22), current *Strangler Fig* page.**
https://martinfowler.com/bliki/StranglerFigApplication.html — the 2004 post
is superseded as the living definition. Four high-level activities (Ian
Cartwright, Rob Horn, James Lewis; order is not a sequence): (1) understand
the outcomes, (2) break the problem into parts / find **seams**, (3) deliver
the parts so value arrives early, (4) change the organization (Conway) so
the new system does not calcify the same way. Transitional architecture that
will later be deleted is *not* waste: reduced risk and earlier value
outweigh it. Replacement-as-rewrite "go[es] down in flames most of the
time" because users cannot wait, existing behaviour is hard to specify, and
much of it is unwanted.

**Asset Capture (Fowler, same day 2004-06-29).**
https://martinfowler.com/bliki/AssetCapture.html — cut over by *asset*
(employee, trade, lease), starting with simple assets or ones the old
system handles badly. Requires **bi-directional** migration (new → old as
well as old → new) so an asset that outgrows the new system can move back.
Event Interception only for captured assets; a Content-Based Router keeps
the old system from seeing events it no longer owns. Fowler's regret: not
capturing at a finer grain, usually because reverse migration was missing.

**Event Interception (originally Fowler 2004 bliki; living text Cartwright /
Horn / Lewis, 2024-03-05).**
https://martinfowler.com/articles/patterns-legacy-displacement/event-interception.html
— "If you are using the Strangler Fig pattern then you will also be using
some form of Event Interception." Seams: message selectors / content-based
routers, reverse proxies, API gateways (coarse Branch-by-Abstraction or
payload routing), progressive enhancement in a legacy web template, pre-
commit DB triggers (change write behaviour only with extreme care), CDC
(Debezium → Kafka named), "swivel-chair" human interception. Case study
stages: dark-launch services to 100% datastore parity → intercept *reads*
(Branch by Abstraction at the persistence layer) → intercept *writes* (new
store becomes system of record) → migrate business rules behind a legacy
façade.

**Branch by Abstraction (Fowler, 2014-01-07).**
https://martinfowler.com/bliki/BranchByAbstraction.html — in-process cousin:
an abstraction over a supplier, a second implementation, feature-flagged
comparison (Steve Smith), then delete the old supplier and optionally the
abstraction. Named by Paul Hammant / Stacy Curl as a trunk-based alternative
to VCS branches. Use when the seam is a *module*, not an HTTP edge.

**Azure Architecture Center, *Strangler Fig Pattern*** (GitHub `ms.date`
2026-05-29; fetched 2026-09-13).
https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig
— four phases: (1) insert a façade, most traffic still legacy; (2)
incrementally shift requests; (3) decommission legacy, façade still in
front; (4) **remove the façade** (or keep it as a legacy-client adapter —
transitional architecture). Cross-system calls during coexistence: **use
ACL**. Database decomposition: new service still R/W the monolith DB → ETL
historical load + CDC sync + **validate consistency before cutover** → new
DB is system of record → drop legacy objects. Rollback is cheap in phase 2
and at the *start* of phase 3; after objects are dropped, rollback is
restore + replay — "significantly increases effort and risk."

**AWS Prescriptive Guidance.** Two pages, complementary:

- *Decomposing monoliths* (three verbs): **Transform / Coexist / Eliminate**.
  Coexist = keep the monolith for rollback; put an HTTP proxy (example:
  Amazon API Gateway) at the perimeter.
  https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-decomposing-monoliths/strangler-fig.html
- *Cloud design patterns* (implementation): proxy by URL; ACL as
  `UserServiceFacade` / `UserServiceAdapter` *inside* the monolith so
  unmigrated callers do not change; data sync via queue + agent
  (eventual consistency, "tactical… until you can establish a long-term
  solution such as a data lake"); Refactor Spaces as the AWS-shaped
  proxy. Closed-to-new-customers banner on Refactor Spaces: **2025-11-07**,
  successor named **AWS Transform**.
  https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html

**AWS Migration Hub — two different products (do not conflate).**

| Product | Role in a strangler | Status (fetched 2026-09-13) |
|---|---|---|
| **Strategy Recommendations** | *Planning*: analyze inventory / binaries / (optional) source + DB; recommend a 7-R strategy (rehost / replatform / refactor) and tools. Does **not** insert a façade or shift traffic. | "AWS Migration Hub is no longer open to new customers as of November 7, 2025… explore AWS Transform." https://docs.aws.amazon.com/migrationhub-strategy/latest/userguide/what-is-mhub-strategy.html |
| **Refactor Spaces** | *Runtime*: application = Strangler Fig proxy orchestrating API Gateway + VPC link + NLB + resource-based IAM; **DEFAULT** + **URI_PATH** routes; periodic DNS refresh. | Same 2025-11-07 new-customer close. https://docs.aws.amazon.com/migrationhub-refactor-spaces/latest/userguide/what-is-mhub-refactor-spaces.html |

**ACL lineage (companion).** Evans 2003 (strategic design / bounded
contexts). Azure *Anti-Corruption Layer* pattern (fetched 2026-09-13)
credits Evans by title; implement as in-process component *or* independent
service; latency, scale, transaction consistency, input validation at the
trust boundary, correlation IDs; retire after migration *or* keep if the
foreign model is permanent. AWS *ACL pattern* (same PG set):
`UserInMonolith` → `UserServiceACL` maps fields (e.g. two address lines +
string zip → one `Address` + `int ZipCode`) and POSTs through API Gateway;
sample at https://github.com/aws-samples/anti-corruption-layer-pattern.
https://learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer
· https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/acl.html

**Workspace one-liner (link only).** [aws/ch08.md](../../../cases/aws/ch08.md)
§ *Other Cloud Architecture Patterns*: ACL as translator that "preserv[es]
the integrity of an application’s core business model"; Strangler fig as
gradually replacing pieces until the old system is gone.

---

## 3. Mechanics (Group B depth)

### 3.1 What the pattern is

A **seam** intercepts work that used to go only to the legacy system and
sends a chosen slice to a new implementation. Clients keep one URL / one
API. The legacy stays up for unmigrated behaviour and as a rollback target.
The new system grows feature-by-feature (or asset-by-asset) until the
legacy is a skeleton and can be switched off. The seam itself is
transitional: Azure's last phase deletes it.

That is *migration*, not a runtime style. The destination can be E2
services, an E10 modular monolith, or even another monolith on a new stack.

### 3.2 Variants (where the seam lives)

| Variant | Seam | Typical cutover unit | Trade-off |
|---|---|---|---|
| **HTTP façade** (Azure / AWS PG / Refactor Spaces / C6 gateway) | Reverse proxy or API gateway in front of the monolith | Path, host, header, or weighted % of a route | Clients unchanged; proxy is a new SPoF / bottleneck (every official page warns). |
| **Branch by Abstraction** | In-process interface over a module | One supplier implementation | No extra hop; needs code access and tests; no independent scale. |
| **Event Interception** | Message router, reverse proxy, gateway, template script, trigger, CDC | Event type or asset id | Minimizes legacy edits; adds transitional components to operate. |
| **Asset Capture** | Content-based router + bi-directional migrator | One business asset | Fine-grained rollback; needs reverse migration or releases stall. |
| **Database strangler** (Azure example) | ETL + CDC, then SoR flip | One bounded-context schema | Avoids dual-write races if CDC is the *only* writer to the copy; validation is mandatory. |
| **ACL hop** (companion) | Adapter/facade/translator at a *model* boundary | One migrated capability's callers | Protects the new model; extra latency and a thing to decommission. |

These compose: a gateway façade for *external* calls + an in-monolith ACL
for *internal* leftover callers is the AWS PG worked shape.

### 3.3 Incremental cutover sequence (canonical)

1. **Identify outcomes and seams** (Fowler 2024; AWS: DDD / event storming
   before premature splits — "when the domain isn't clear… you [can] get
   the service boundaries wrong").
2. **Insert the façade, 100% to legacy.** Refactor Spaces: first route
   **must** be `DEFAULT`; it is created **ACTIVE**.
3. **Dark-launch / shadow** the new implementation (Event Interception case
   study: 100% parity checks with no consumers). Shadow is *not* cutover:
   responses are discarded (Istio / Envoy).
4. **Cut a slice.** Prefer a read path or a low-value asset first. Path-
   based 100% of `/users` is safer than 5% of *all* traffic if the new
   service only implements users.
5. **Canary %** on that slice (ALB weights, API Gateway canary,
   Istio `weight`) with an explicit rollback (weight 0 / canary 0 /
   route `INACTIVE`).
6. **Flip system of record** only after consistency checks (Azure). Until
   then the monolith DB or a CDC stream is SoR; the new DB is a follower.
7. **Rewire leftover callers** through ACL, then delete the ACL when the
   last caller has moved (AWS PG: ACL "must be decommissioned after all
   dependent services have been migrated").
8. **Eliminate** legacy objects (AWS verb) and then the façade (Azure
   phase 4).

### 3.4 Dual-write risks (do not treat as a first-class sync)

Two independent writes from application code to legacy DB *and* new DB
(or DB *and* a queue) look like a strangler shortcut. They are the
**dual-write problem**.

**Kleppmann (2015-05-27),**
https://martin.kleppmann.com/2015/05/27/logs-for-data-infrastructure.html
— two clients dual-writing key X: store 1 ends at B, store 2 ends at A;
**permanent** inconsistency (not eventual), no error, discovered months
later. Partial failure (one write succeeds) is the other failure mode.
Remedy: write *once* to an ordered log (or primary DB) and derive the
second store as a consumer. CDC / outbox (B7) is that shape.

**Azure strangler DB sequence** is CDC-shaped, not dual-write-shaped:
legacy remains writer during sync; new service writes the new DB only
after validation. The page still says "the new system writes to the new
domain database" *while* CDC is running — treat that as a **window to
keep as short as possible** and cover with reconciliation (§8 on whether
Azure intends application dual-write in that window).

**AWS PG** "synchronizing agent" (microservice emits to a queue; agent
updates the monolith DB) is eventual consistency and labelled **tactical**.
**AWS mainframe coexistence** (2024-era blog, fetched 2026-09-13) describes
an explicit *dual writes* variant: local + remote write in one application
transaction; "well suited for… infrequent writes and frequent reads";
"major drawback is the complexity… ensuring data integrity and
consistency."
https://aws.amazon.com/blogs/migration-and-modernization/integration-architectures-between-mainframe-and-aws-for-coexistence/

**Confluent (dual-write problem page).** Atomicity does not extend from a
DB transaction to Kafka / a second DB / email. Separate the writes: first
write triggers a retrying process for the second (outbox / CDC).
https://www.confluent.io/blog/dual-write-problem/

### 3.5 Placement

| Layer | What it intercepts | Rollback move |
|---|---|---|
| **Edge gateway** (C6; Refactor Spaces API GW; Azure APIM) | North-south HTTP | Deactivate route / set canary 0 / flip weight |
| **Mesh VirtualService / HTTPRoute** | East-west *or* north-south if the gateway is in-mesh | Weight / `RequestMirror` / route delete |
| **ALB weighted target groups** | L7 forward to ≤ 5 groups | Weight 0 on the new group |
| **In-process ACL / Branch by Abstraction** | Remaining monolith callers | Feature flag / swap implementation |
| **Messaging / CDC** | State-change events | Stop the consumer; reverse-migrate assets |

Do **not** put domain rules in the façade (C6 / ThoughtWorks "overambitious
API gateways" Hold). Translation belongs in the ACL; routing belongs in
the façade.

---

## 4. Verified defaults / standards (knobs)

Fetched 2026-09-13. These are *platform* defaults for the seam, not
"strangler library" defaults — there is no Resilience4j of stranglers.

### 4.1 Routing %

| Control | Verified numbers | Strangler use |
|---|---|---|
| **Istio `HTTPRoute` / VirtualService `weight`** | Docs example: 25% to one subset, remaining 75% to the other; mirroring task uses `weight: 100` on v1. | Canary a *migrated path's* two backends. Do not canary a path the new service cannot serve. https://istio.io/latest/docs/reference/config/networking/virtual-service/ |
| **ALB weighted target groups** | Weight **0–999** per group (botocore `modify_rule` / CLI `modify-listener`); **≤ 5** target groups per action (quota *Target Groups per Action per Application Load Balancer* = 5, not adjustable). Example 8+2 → 80/20; 9+1 → 90/10. "Slight delay" before the new weight is observed (AWS News Blog, 2019-11-19) — no ms figure published. Target-group stickiness (example 12 h = 43 200 s) **overrides** the new weight for already-stuck clients. | https://docs.aws.amazon.com/cli/latest/reference/elbv2/modify-listener.html · https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-limits.html · https://aws.amazon.com/blogs/aws/new-application-load-balancer-simplifies-deployment-with-weighted-target-groups/ |
| **API Gateway REST canary** | `percentTraffic` **0–100** (CloudFormation `AWS::ApiGateway::Stage` `CanarySetting`; *Required: No*). Example CLI: `path=/canarySettings/percentTraffic,value=25.0`. HTTP APIs: **no** canary (C6 research). | Version canary of the *proxy*, not a substitute for path-based extraction. https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-apigateway-stage-canarysetting.html · https://docs.aws.amazon.com/apigateway/latest/developerguide/update-canary-deployment.html |
| **Refactor Spaces routes** | Types `DEFAULT` \| `URI_PATH`. First route **must** be `DEFAULT`. Default route is created **ACTIVE**. No other route may be ACTIVE unless DEFAULT is ACTIVE; DEFAULT may go INACTIVE only when every other route is INACTIVE. `URI_PATH`: `SourcePath`, `Methods[]`, `IncludeChildPaths`, `AppendSourcePath`. Toggle via `UpdateRoute` `ActivationState` `ACTIVE` \| `INACTIVE`. DNS for service URLs: refresh at the name's TTL, or **every 60 s** when TTL < 60 s. | Path extraction with an instant traffic-off switch. https://docs.aws.amazon.com/migrationhub-refactor-spaces/latest/APIReference/API_CreateRoute.html · https://docs.aws.amazon.com/migrationhub-refactor-spaces/latest/userguide/welcome-concepts.html |

**Default routing % for a new strangler is not 50.** Official sequences
start at **0% new / 100% legacy**, then flip a *path* to 100% new, or
ramp a canary on that path. A 50/50 split of *all* URLs is a
misconfiguration unless both sides implement every URL.

### 4.2 Shadow traffic

| Control | Verified behaviour |
|---|---|
| **Istio `mirror` + `mirrorPercentage`** | Mirrored out-of-band; sidecar **does not wait**; responses discarded ("fire and forget"). Host/Authority gets **`-shadow`** (`cluster-1` → `cluster-1-shadow`). `mirrorPercentage.value` 0–100; **if the field is absent, 100% is mirrored.** Task example: `weight: 100` to v1 + `mirrorPercentage.value: 100.0` to v2. Stats are generated for the mirrored destination. https://istio.io/latest/docs/tasks/traffic-management/mirroring/ · VirtualService reference (same fetch). |
| **Envoy `RequestMirrorPolicy`** (docs 1.40.0-dev, 2026-09-13) | Same fire-and-forget; all normal stats on the shadow cluster. Host altered by appending **`-shadow`**; disable with `disable_shadow_host_suffix_append`; `host_rewrite_literal` implicitly disables the suffix. `runtime_fraction` is a `FractionalPercent` (numerator / denominator; **denominator default 100** when you set a numerator). Default fraction when the field is *omitted*: **not stated** (§8). https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/route/v3/route_components.proto |
| **Gateway API `HTTPRequestMirrorFilter`** | Response never comes from the mirror `backendRef`; multiple mirrors allowed; traffic split among main `backendRefs` is independent. Istio's mirroring task installs Gateway API **v1.6.0** experimental CRDs in the example `kubectl apply` (that version pin is the *task's*, not a platform default). |

Shadow **replays writes**. Only shadow idempotent / read paths, or put the
shadow backend in a sink that cannot mutate shared SoR (or cannot emit
user-visible side effects). The `-shadow` Host suffix is the log split;
the new service must tolerate it or you rewrite the host.

### 4.3 Rollback

| Mechanism | Verified rule |
|---|---|
| **Keep the monolith** | AWS PG *Coexist*: "Keep the monolith application for rollback." Disadvantage row: "Requires a rollback plan for each refactored service to revert… quickly and safely." |
| **Route / weight / canary** | Refactor Spaces `INACTIVE`; ALB weight 0; API Gateway `percentTraffic` 0; Istio weight 100 back to the legacy subset. |
| **Azure DB** | Rollback cheap while CDC and legacy tables exist; after drop, restore + replay. "Treat the removal of legacy objects as a deliberate final step." |
| **Asset Capture** | Reverse-migrate the asset (Fowler 2004). |
| **Sticky canaries** | ALB target-group stickiness keeps clients on the old weight until `DurationSeconds` expires — a rollback of weights is **not** instant for those clients. |

There is no vendor "default rollback timeout." The operational default is:
**do not delete the old path until the new SoR has passed a measured
consistency window.**

### 4.4 ACL (companion knobs)

No numeric library defaults. Verified *considerations*: extra latency
(load-test before production — AWS); scale the ACL with the target
(AWS: ACL can become the bottleneck); retries + breaker on the ACL hop
(AWS points at the retry and circuit-breaker patterns); record it as
technical debt if interim (AWS); correlation IDs + structured logs
(Azure); do not put business rules or orchestration in the layer
(Azure "not suitable" when semantics do not actually differ).

---

### 4.5 Observability of dual paths

A strangler without dual-path metrics is a silent split-brain. Emit at
least:

| Signal | Why |
|---|---|
| **Request rate, error rate, latency — tagged `backend=legacy\|new` (and `shadow=true`)** | The only way to know a canary is worse than the host. Istio / Envoy already generate stats for the mirrored cluster. |
| **Per-route activation / weight / canary %** | Config drift: a `URI_PATH` left `INACTIVE`, an ALB weight that never flipped. |
| **Shadow vs primary comparison** | Status-class and latency delta on the same correlation / trace id. Host `-shadow` is the join key in access logs. Do **not** wait on the shadow (it is fire-and-forget). |
| **ACL translation errors and latency** | Azure: "track the success and latency of the translation." Field-mapping bugs (AWS zip-code `int` parse) show up here, not as 5xx from the new service. |
| **SoR lag and mismatch rate** | Row counts, checksums, or sampled entity diffs between monolith DB and new DB during CDC. Azure: "Validate consistency between both databases before cutover." |
| **Correlation IDs across façade → ACL → both backends** | Azure ACL + Azure Gateway Aggregation (C6) both require them. |
| **Business KPI on the extracted slice** | Fowler 2024: early value is the point. A latency win that drops conversion is a failed cutover. |

Alert shapes (own formulations on documented functions — **not** vendor
PromQL; see §8): *new-backend error rate ≫ legacy on the same route for
N minutes*; *CDC lag above the validation window*; *ACL p99 above the
budget you load-tested*; *façade 5xx* (proxy as SPoF).

OpenTelemetry: use the normal HTTP server/client semantic conventions on
**both** backends and the façade; there is no strangler-specific OTel
signal. The design rule is **identical span names + a `backend` /
`shadow` attribute**, so a single trace shows façade → legacy and the
async shadow span.

---

### 4.6 Tuning

| Knob | Too aggressive | Too timid | Starting point (sourced) |
|---|---|---|---|
| Slice size | Whole checkout in one go | Endless "just the health check" | One bounded context or one asset class (Fowler 2024 seams; Asset Capture). |
| Shadow % | 100% of mutating traffic | 0% (first production is the canary) | 100% of a **read** path, 0% of writes (Istio default 100 if the field is absent — set it explicitly). |
| Canary % | 50% of all URLs | Perpetual 1% that never graduates | Path = 100% of that path after shadow parity; *then* 5–10% user canary if you need a live mix (ALB 9/1 example). |
| SoR flip | Same day as first 200s | Forever dual-running two writers | After ETL + CDC + **passing** consistency checks (Azure). |
| ACL lifetime | Permanent unowned adapter | Deleted while callers remain | Decommission when the last monolith caller is gone (AWS PG). |
| Façade lifetime | Eternal "temporary" gateway doing domain work | Yanked while legacy clients remain | Azure phase 4, or keep as a *thin* legacy adapter (C6). |

### 4.7 Worked calibration — storefront `/users` extract

Design drill (not a vendor SLA), matching the AWS PG storefront diagram
(user / cart / account on one RDS):

Constraints: 2 000 rps storefront, user reads ~400 rps, user writes ~20
rps; cart still in the monolith and calls user; reporting still reads the
monolith DB; rollback required within one change window.

| Step | Choice | Why |
|---|---|---|
| Seam | API Gateway (or leftover Refactor Spaces app) in front; `DEFAULT` → monolith; `URI_PATH` `/users` + child paths → new service | Clients unchanged; path match is the unit AWS documents. |
| Dark launch | CDC (Debezium-class) monolith `users` → new store; Event Interception stage 1 parity job | Avoids Kleppmann dual-write races. |
| Shadow | Istio/Envoy mirror **GET** `/users*` at 10% then 100%; `mirrorPercentage` set explicitly; writes not mirrored | Fire-and-forget + `-shadow` Host; writes would mutate. |
| Read cutover | Flip `/users` GET to 100% new; cart still hits monolith `UserService` | Read path is reversible by `INACTIVE`. |
| ACL | `UserServiceAdapter` in the monolith maps cart's old DTO → new API | Cart team does not change in the same release (AWS PG motivation). |
| Write cutover | After mismatch rate stays at 0 for the agreed window, redirect writes; stop CDC **to** the new store; start tactical queue+agent **back** to monolith for reporting | Azure SoR flip; AWS "tactical" reverse sync. |
| Canary of the write path | ALB 90/10 for one hour **only if** both sides can accept writes (they should not — prefer flag + 100% after rehearsal). If a live mix is required, it is a dual-write and needs an idempotency key + reconciliation, which this drill refuses. | Kleppmann. |
| Rollback | `URI_PATH` → `INACTIVE`; ACL still points at new until you swap the adapter back; do **not** drop monolith `users` tables in the same window | Azure "deliberate final step." |
| Eliminate | Cart rewritten to call the new service; ACL deleted; reporting reads the new store; monolith user code removed; consider removing the façade | AWS Transform / Eliminate. |

---

## 5. Failure modes and when-not-to-use

**Failure modes of the strangler itself**

- **Façade as SPoF / bottleneck** — Azure, AWS PG (both pages), C6. Mitigate
  with a Multi-AZ managed gateway (AWS: API Gateway called out as reducing
  that risk) and load tests; do not add business logic that makes it
  unscalable.
- **Façade falls behind the migration** — Azure "Make sure that the façade
  keeps up." Stale routes send users to deleted monolith methods.
- **Wrong granularity** — canary of *all* traffic when only `/users` is
  ready; or one ACL/breaker over many independent capabilities (C1 resource
  differentiation).
- **Dual-write split-brain** — Kleppmann permanent inconsistency; Azure
  expensive rollback after DROP.
- **Shadow side effects** — emails, charges, inventory decrements from
  mirrored POSTs.
- **ACL as a new monolith / bottleneck** — AWS scale warning; C6
  overambitious-gateway anti-pattern if the gateway *is* the ACL.
- **Sticky sessions hide a rollback** — ALB target-group stickiness.
- **DNS lag** — Refactor Spaces refreshes at TTL (floor 60 s). A service
  URL change is not instant.
- **Unchanged organization** — Fowler 2024: the new system becomes
  tomorrow's unstrangleable legacy.
- **Unclear domain** — AWS: premature microservice boundaries are expensive.
- **Code-access assumption** — Azure and AWS both: you cannot redirect
  *internal* leftover calls or disable migrated features without modifying
  the monolith. External-only façades still work if every client is HTTP
  and you never need to change the legacy.

**When not to use (sourced)**

| Situation | Source | Prefer |
|---|---|---|
| **Greenfield** — no live system to wrap | Implicit in every definition (legacy / monolith / brownfield). AWS *decomposing monoliths* contrasts "design patterns… for greenfield" with strangler for brownfield. | Design E10/E2/E8 directly; still make the new system strangleable (Fowler 2004 closing rule). |
| **Tiny / simple system** | Azure: "You migrate a small system and replacing the whole system is simple." AWS PG: "Isn't suitable for small systems where the complexity is low and the size is small" / "more efficient to rewrite." | Big-bang rewrite or replace. |
| **Requests cannot be intercepted** | Azure + AWS PG identical. | Branch by Abstraction (needs code) or accept a hard cutover. |
| **No source access, and you need to disable leftover internal calls** | Azure: "You can't access the legacy system's source code." AWS: "You cannot intercept calls without code base access." | External façade only, or a Legacy Mimic that *is* the old interface (Event Interception). |
| **Must fully decommission the original quickly** | Azure. | Planned cutover with a freeze, not a multi-year fig. |
| **No semantic gap** | Azure ACL "not suitable." | A dumb proxy, not an ACL. |

---

## 6. Cross-links

- **Catalog:** B4 in
  [system-design-patterns-catalog.md](system-design-patterns-catalog.md).
- **Siblings:** E1 monolith, E10 modular monolith (see also
  [ml-solutions-arch modular pipeline](../../../cases/ml-solutions-arch/modular-pipeline-exercise.md)
  — in-process modular monolith, not a network extract), E2 microservices,
  E8 hexagonal (ACL-related, not the same), C6 gateway as the strangler
  façade ([api-gateway-external-research.md](api-gateway-external-research.md)).
- **Existing mechanism notes (link, do not rewrite):**
  [aws/ch08.md](../../../cases/aws/ch08.md)
  (ACL + strangler fig + gateway + outbox + CDC);
  [event-driven-dataflow](../../../cases/data-intensive-design/event-driven-dataflow.md);
  [replication-logs](../../../cases/data-intensive-design/replication-logs.md)
  (CDC);
  [event-sourcing-cqrs](../../../cases/data-intensive-design/event-sourcing-cqrs.md).
- **Depth-bar examples (do not copy topics):**
  [CircuitBreaker.md](../../../cases/SystemDesignPatterns/CircuitBreaker.md),
  [RetryBackoff.md](../../../cases/SystemDesignPatterns/RetryBackoff.md).
- **ACL hop resilience:** C1 / C2 research notes.

---

## 7. Sources

Retrieved 2026-09-13.

**Canon.** martinfowler.com/bliki/OriginalStranglerFigApplication.html
(2004-06-29; rename note 2019-04-29) ·
martinfowler.com/bliki/StranglerFigApplication.html (2024-08-22) ·
martinfowler.com/articles/2024-strangler-fig-rewrite.html ·
martinfowler.com/bliki/AssetCapture.html (2004-06-29) ·
martinfowler.com/articles/patterns-legacy-displacement/event-interception.html
(2024-03-05) ·
martinfowler.com/articles/patterns-legacy-displacement/transitional-architecture.html
· martinfowler.com/bliki/BranchByAbstraction.html (2014-01-07) ·
link.springer.com/chapter/10.1007/978-3-540-24853-8_15 (Stevenson & Pols,
XP 2004; **title/pages only**) ·
learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig ·
learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer ·
docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html
· docs.aws.amazon.com/prescriptive-guidance/latest/modernization-decomposing-monoliths/strangler-fig.html
· docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/acl.html
· docs.aws.amazon.com/migrationhub-strategy/latest/userguide/what-is-mhub-strategy.html
· docs.aws.amazon.com/migrationhub-refactor-spaces/latest/userguide/what-is-mhub-refactor-spaces.html
· docs.aws.amazon.com/migrationhub-refactor-spaces/latest/userguide/welcome-concepts.html
· docs.aws.amazon.com/migrationhub-refactor-spaces/latest/userguide/how-it-works.html
· docs.aws.amazon.com/migrationhub-refactor-spaces/latest/APIReference/API_CreateRoute.html
· docs.aws.amazon.com/migrationhub-refactor-spaces/latest/APIReference/API_UpdateRoute.html
· aws.amazon.com/blogs/architecture/seamlessly-migrate-on-premises-legacy-workloads-using-a-strangler-pattern
· aws.amazon.com/blogs/migration-and-modernization/integration-architectures-between-mainframe-and-aws-for-coexistence

**Knobs and dual paths.**
istio.io/latest/docs/tasks/traffic-management/mirroring ·
istio.io/latest/docs/reference/config/networking/virtual-service ·
envoyproxy.io/docs/envoy/latest/api-v3/config/route/v3/route_components.proto
· docs.aws.amazon.com/cli/latest/reference/elbv2/modify-listener.html ·
docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-limits.html
· aws.amazon.com/blogs/aws/new-application-load-balancer-simplifies-deployment-with-weighted-target-groups
· aws.amazon.com/blogs/devops/blue-green-deployments-with-application-load-balancer
· docs.aws.amazon.com/apigateway/latest/developerguide/update-canary-deployment.html
· docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-apigateway-stage-canarysetting.html
· github.com/aws-samples/anti-corruption-layer-pattern

**Dual-write.** martin.kleppmann.com/2015/05/27/logs-for-data-infrastructure.html
· confluent.io/blog/dual-write-problem ·
(workspace) cases/aws/ch08.md transactional outbox + CDC

**Workspace.** cases/aws/ch08.md · docs/research/sysdesign/api-gateway-external-research.md
· docs/research/sysdesign/system-design-patterns-catalog.md

---

## 8. Uncertain / left out (excluded from the Concept)

- Stevenson & Pols XP 2004 paper **body** — Springer paywall; only title,
  pages 123–129, and Fowler's second-hand summary are used.
- Azure Learn HTML did not surface `ms.date`; **2026-05-29** is from the
  MicrosoftDocs/architecture-center GitHub copy of `strangler-fig.md`.
- Whether Azure phase-2 sentence "the new system writes to the new domain
  database" *and* CDC from the monolith is an intentional dual-write window
  or a documentation overlap — Concept should prescribe "CDC-only until
  SoR flip" and not claim Azure forbids the overlap.
- Envoy `RequestMirrorPolicy.runtime_fraction` **omitted** default (Istio
  *is* explicit at 100%).
- API Gateway canary `percentTraffic` default when the property is omitted
  (*Required: No*).
- ALB "slight delay" before weight change takes effect — no published bound.
- AWS Transform capabilities as a Refactor Spaces successor — banner only;
  no strangler-routing doc fetched.
- Migration Hub Strategy "7 Rs" glossary page returned 404 this fetch;
  the Strategy userguide itself names rehost / replatform / refactor and
  points at the glossary.
- Istio "latest" docs vs a pinned minor (mirroring task mentions Gateway
  API v1.6.0 experimental CRDs).
- PromQL dual-path alert recipes — none found; §4.5 shapes are this note's.
- OpenTelemetry strangler-specific semantic conventions — none; §4.5 is a
  design rule on existing HTTP conventions.
- Evans 2003 book text — not copied; ACL description is from Azure / AWS
  / Fowler Event Interception (ACL named there as Event Transformer).
- Paul Hammant *Legacy Application Strangulation* case studies (2013) —
  not used as a numeric source.
- Refactor Spaces pricing (hours + API requests) — out of scope.
- Whether HTTP APIs can be used as a Refactor Spaces proxy (C6: HTTP APIs
  lack canary); Refactor Spaces docs say "Amazon API Gateway" without
  REST-vs-HTTP.
- Course-dump JavaScript / class diagrams — none in this tree for B4.
