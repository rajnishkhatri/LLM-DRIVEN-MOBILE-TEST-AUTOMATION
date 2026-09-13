---
type: reference
title: 'API contracts (REST, gRPC, GraphQL)'
description: >-
  Evolve published contracts while old and new clients and servers coexist:
  REST/JSON, proto3/gRPC, and GraphQL compatibility rules; URI vs query vs
  header vs media-type vs package-major selection; concurrent-version fan-out;
  mismatch errors; gateway version routing; RFC 8594/9745; Pact verification
  of the current provider; and when not to version.
tags: [system-design-patterns, communication, api-contracts, versioning, graphql, grpc, rest]
---

# API contracts (REST, gRPC, GraphQL)

**See also:** [request–response](RequestResponse.md) · [API gateway](ApiGateway.md) · [encoding & evolution (DDIA)](../data-intensive-design/encoding-overview.md) · [REST/RPC dataflow (DDIA)](../data-intensive-design/rest-rpc-dataflow.md) · [protobuf evolution](../data-intensive-design/protobuf-schema-evolution.md) · [avro evolution](../data-intensive-design/avro-schema-evolution.md) · [graphql (DDIA)](../data-intensive-design/graphql.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/a6-api-contracts-external-research.md)

An API is a promise to code you cannot redeploy. Compatibility of the *bytes* — field tags, skip-unknown, writer/reader schemas — is the [encoding layer's](../data-intensive-design/encoding-overview.md) problem; [GraphQL as a query contract](../data-intensive-design/graphql.md) is already owned there. This Concept owns the **published contract over time**: what is wire-safe versus breaking on REST, gRPC, and GraphQL; how a client *names* the surface it wants; how many of those surfaces you can afford to run; what a selector miss returns; and how a proxy routes the choice. Quality attributes: **evolvability** without a flag day, **independent deployability** (the contract that makes [microservices](../data-intensive-design/distributed-vs-single-node.md) possible). Costs: every live version is a transform, a test matrix, and a route you operate until usage is gone. Architecturally the contract *is* the module boundary: coupling across teams is connascence of name and of meaning; a version selector is how you pay that connascence down over time instead of in a lockstep deploy.

[Request–response](RequestResponse.md) owns the *call* (status, deadlines, unary framing). [The gateway](ApiGateway.md) owns the *product surface* that often implements the routing below. CQRS/event-sourced *payload* schemas belong with the Avro/protobuf notes, not here. This page owns the *shape* of that call as it changes.

## Lineage and vocabulary

[Encoding-overview](../data-intensive-design/encoding-overview.md) defines the pair: **backward** = newer code reads older data; **forward** = older code reads newer data. For APIs the pair flips by role. An older client calling a newer service needs backward compatibility on the *request* and forward compatibility on the *response*. [REST/RPC dataflow](../data-intensive-design/rest-rpc-dataflow.md) adds the operational assumption: **servers upgrade first, clients second**. Cross-organization APIs cannot force that, so multiple versions run side by side.

Google AIP-185 (fetched 2026-09-13): a major is the last protobuf-package segment and the first URI-path segment; Google APIs **must not** expose minor or patch in the URL (`v1`, not `v1.0`). A new major **must not** depend on a previous major. Different majors of the same API must work in one client for a documented transition; an older major goes through communicated deprecation before shutdown.

**Breaking vs additive** (GitHub REST, fetched 2026-09-13). Breaking: remove or rename an operation, parameter, or response field; add a required parameter; make an optional parameter required; change a type; remove enum values; add a validation rule; change auth. Additive (available in all supported versions): add an operation, optional parameter, optional request header, response field, response header, or enum value.

**Who names the version.** [REST/RPC dataflow](../data-intensive-design/rest-rpc-dataflow.md) cites the two poles: a *client-sent selector* (Troy Hunt, 2014) versus a *server-remembered pin* (Brandur Leach / Stripe, 2017). Every strategy below is one of those two.

**Deprecate ≠ sunset.** RFC 8594 §1.4 (Informational, May 2019): `Sunset` is the *second* stage — the resource will become unresponsive — not “no longer preferred.” RFC 9745 (Standards Track, March 2025) fills the first stage with `Deprecation`. GitHub’s REST docs use both: `Deprecation` = closing-down date; `Sunset` = retirement, after which requests return `410 Gone`.

## Wire semantics — compatibility by protocol

### REST / JSON

Compatible by convention, not by codec. Additive: new optional request fields (the server must succeed when they are absent) and new response fields (clients must ignore unknowns). Breaking: rename or remove, type change, newly required input, newly non-null output that can be absent, enum *removal*. Azure Architecture Center treats “no versioning” as viable for internal APIs *if* clients ignore unrecognized fields; field removal or rename is the point at which a version selector is required. The consumer half of that bargain is Fowler’s tolerant reader — consume what you need, ignore the rest, and **preserve unknowns on round-trip writes**; a read-modify-PUT that drops fields it never understood is the Figure 5-1 silent loss in [encoding-overview](../data-intensive-design/encoding-overview.md).

### gRPC / proto3

Field-tag mechanics live in [protobuf-schema-evolution](../data-intensive-design/protobuf-schema-evolution.md); do not re-derive them here. What the contract layer must remember (Language Guide, proto3, fetched 2026-09-13):

- **Wire-safe:** add a field (old binaries skip it; new code sees the proto3 default when old writers omit it); remove a field *if* the number is reserved; add an enum value (unknown values are preserved; representation is language-dependent).
- **Wire-unsafe:** change a field number; move fields into an existing `oneof`.
- **Conditionally compatible** (lossy if values exceed the old type): `int32`/`uint32`/`int64`/`uint64`/`bool`; `sint32`↔`sint64`; `string`↔`bytes` when UTF-8; `fixed32`↔`sfixed32`; `enum`↔ integer types.
- Field numbers `1`–`15` encode in one byte; `16`–`2047` in two; legal range `1`–`536,870,911`; **`19,000`–`19,999` reserved for the implementation**. `reserved 2, 15, 9 to 11;` and `reserved "foo", "bar";` cannot be mixed in one statement; ranges are inclusive.
- Proto3 **preserves unknown fields** on binary parse/serialize; they are **lost** on JSON serialize and on field-by-field copy. That is why a transcoding gateway can turn a binary-safe rename into a REST break. The Figure 5-1 round-trip in [encoding-overview](../data-intensive-design/encoding-overview.md) is this loss in story form — do not re-derive it; preserve unknowns, or do not round-trip through a model that cannot hold them.

Microsoft’s gRPC versioning page (ASP.NET Core 10) splits three planes: *protocol* vs *binary* (generated stubs) vs *behavior*. Adding a request field is protocol-safe **unless** the server errors when the field is unset. Renaming a field is not a protobuf-protocol break (identity is the number) but **is** a break under JSON transcoding. Renaming package, service, or method changes the HTTP/2 path (`/{package}.{Service}/{Method}`) and yields `UNIMPLEMENTED`.

### GraphQL

[graphql.md](../data-intensive-design/graphql.md) owns what GraphQL *is* — an untrusted-client query contract over any store, not a graph database. This paragraph owns evolution. graphql.org “Schema Change Management” (fetched 2026-09-13): prefer *one* evolving schema; `/graphql/v2` is allowed but “sacrifices GraphQL’s benefits.”

| Class | Changes |
|---|---|
| **Safe additive** | New fields, types, queries/mutations, optional arguments; making a required field optional |
| **Breaking** | Remove/rename fields or types; change a field type; remove/rename enum values; make an optional argument required; change argument types; make a non-null field nullable **or** a nullable field non-null (existing nulls become errors) |
| **Dangerous but structurally additive** | New enum values (exhaustive switches); new interface implementations (`__typename` surprises) |

Optional arguments must default to the previous behavior. `@deprecated` is the removal mechanism; the September 2025 spec places it on `FIELD_DEFINITION | ARGUMENT_DEFINITION | INPUT_FIELD_DEFINITION | ENUM_VALUE` and **forbids** it on required (non-null without default) arguments or input fields. Introspection `includeDeprecated` defaults **false**. Apollo GraphOS waits until field usage is zero, or “minimally acceptable” for an unsupported mobile build.

The restriction in [graphql.md](../data-intensive-design/graphql.md) — no recursive queries, no arbitrary search from untrusted clients — is why a versionless schema is even possible: the SDL is a closed, declared join surface, so “add a field” is invisible to clients that do not ask for it, and “remove a field” is a validation error for those that still do. That is evolution by *selection*, not by URL.

### Avro (contrast only)

Avro is two-schema resolution by *name* plus reader defaults — [avro-schema-evolution](../data-intensive-design/avro-schema-evolution.md). Relevant here only as the contrast: protobuf is self-skipping tags; Avro needs the writer’s schema (registry, file header, or handshake). Event *payload* evolution on the bus is [pub/sub](PubSubQueues.md), not this page.

## Version-selection lifecycle

A contract has no TCP handshake. The lifecycle that plays the same role:

1. **Publish** a machine-readable artifact (OpenAPI / AsyncAPI / `.proto` / GraphQL SDL).
2. **Select** a version (or “latest additive surface”) on each request, or pin it to an account.
3. **Evolve additively** in place on that major / date / schema.
4. **Deprecate** (signal: still works).
5. **Sunset** (signal: will become unresponsive at a time).
6. **Remove** (mismatch becomes a hard error). Clients that cannot update — mobile stores, partner ISVs — stay on an older pin until sunset.

**Publish is the handshake.** OpenAPI 3.1.2 (`spec.openapis.org/oas/v3.1`, 19 September 2025): `info.version` is the **document** version, not the API version and not the OAS version; the Schema Object is a superset of JSON Schema Draft 2020-12; `deprecated` on Operation / Parameter / Header defaults **`false`**. AsyncAPI 3.1.0 (released 2026-01-31) is the same contract for the message API (`channels` + `operations`). The spec is the artifact the [diff gates](#pact-verifies-the-current-provider) need; author and lint it before implementing. Design-first is not ceremony — a reviewed contract is the only thing `oasdiff`, `buf breaking`, or GraphQL Inspector can diff.

**Deprecate, then sunset, then measure.** RFC 9745 `Deprecation` is an Item Structured Field whose value **MUST** be an RFC 9651 Date (`@` + Unix seconds) — example `Deprecation: @1688169599` (2023-06-30 23:59:59 UTC). It **does not change resource behavior**. RFC 8594 `Sunset` is an HTTP-date and **SHOULD** be in the future; if both are sent, Sunset **MUST NOT** precede Deprecation. The two headers use different date formats “for historical reasons.” GitHub emits both around version retirement — in the pre-RFC HTTP-date format, a live reminder that standards outrun deployments. Removal without a measuring step (usage → zero) is a breaking change with extra paperwork; Apollo GraphOS gates GraphQL field removal on usage, not a calendar.

| Strategy | How it selects | Character |
|---|---|---|
| **URI / path** (`/v2/customers/3`) | First path segment is the major. AIP-185 *requires* `/v1/...`. Stripe keeps `/v1/` as a reserved major and does the real work in date versions; the 2017 post said `/v1` was “not likely to change for some time” after ~100 incompatible upgrades in six years. | Cheap for a reverse proxy; HATEOAS links must carry the version; REST purists object that resource identity should not change. |
| **Query string** | Azure Architecture: `?version=2`, default if omitted. Azure *service* guidelines go further: **required** `api-version` on *every* operation (`YYYY-MM-DD`, `-preview` suffix); omit → HTTP 400 `MissingApiVersionParameter`; unknown → 400 `UnsupportedApiVersionValue` listing still-supported stables plus the latest public preview; **DO NOT** put a version segment in the path. Preview retirement ≥ 90 days notice; a preview must GA or be removed within 1 year; preview date and GA date must differ. | Explicit; no silent omit. Every `nextLink` / `Operation-Location` must carry the parameter. Some older caches skip query-string URIs (Azure Architecture’s wording). |
| **Header** | GitHub REST: `X-GitHub-Api-Version: 2026-03-10`; omit → default **`2022-11-28`**; unsupported → `410 Gone`. Supported as of fetch: `2026-03-10` (EOS not scheduled) and `2022-11-28` (EOS **10 March 2028**). Previous version kept **at least 24 months** after a newer version ships. Stripe: first request pins the account; override with `Stripe-Version`; `/v2` *requires* the header. Google IBV (AIP-185): `X-Goog-Api-Version` **or** `$apiVersion` query; omit is configuration-dependent (configured default, consumer override, or reject — no single Google-wide omit behavior). Azure Architecture’s `Custom-Header: api-version=2` is an *example name*, not a registered field; production Azure services use the query parameter. | Stable URIs; incremental dates. L7 required. A silent default (GitHub) surprises unversioned clients when the default jumps. |
| **Media type** | `Accept: application/vnd.contoso.v1+json`; `Content-Type` echoes the choice. Unknown Accept → **406** or a default media type. | Best fit for HATEOAS. Requires `Vary: Accept` (and any custom version header) at caches. |
| **GraphQL / don’t version** | One schema; `@deprecated`; remove when usage is gone. Some orgs announce three months ahead and change only at quarter boundaries (graphql.org example, not a default). | Lowest URI friction, highest removal discipline. |
| **gRPC package major** | `package greet.v1;` → `greet.v1.Greeter` beside `greet.v2.Greeter`. Microsoft: do not bump the package unless the change is breaking; share business logic behind both; generated types differ so you map to a common model. | Two services, one process. Mis-pointed clients get `UNIMPLEMENTED`. |

## Concurrent surfaces (fan-out)

Fan-out here is **how many contract surfaces you run**, not HTTP/2 streams.

- **N majors × M date/channel pins.** Each surface is a transform, a test matrix, and a gateway route. Stripe’s 2017 design encapsulates each incompatible change as a *backwards* transform from “current” to the pinned version so core code stays on one shape — the cost is a growing transform chain and `has_side_effects` leaks. Google’s channel model caps this: at most one alpha, one beta, one stable per major; beta ⊇ stable, alpha ⊇ beta; IBV scopes a version as small as one RPC group.
- **Mobile / store-lag consumers.** Pact’s `--all TAG` / “all prod” selector exists so a provider verifies against *every* still-installed consumer version, not just `latest`. GraphQL removal gated on usage, not a calendar, is the same force.
- **Response-shape fan-out at the edge.** Azure Architecture on header/media-type versioning: many versions in a shared cache → duplicated entries; a cache that keys only on URI can serve the wrong version (or the wrong *tenant*). Path versioning avoids that because the URI *is* the cache key.
- GraphQL query fan-out (N fields → M resolvers) is an *execution* concern, not a versioning concern — do not treat it as this pattern.

No vendor publishes a numeric “max live API versions” default. The verified *policy* numbers are support windows (GitHub ≥ 24 months; Azure preview ≥ 90 days / ≤ 1 year; AIP-185 *recommends* 180 days before removing deprecated beta functionality). Those are policies, not protocol limits.

## Mismatch and migration (“reconnect”)

| Selector miss | Verified behavior | Source (2026-09-13) |
|---|---|---|
| Missing Azure `api-version` | 400 `MissingApiVersionParameter` | Azure API guidelines |
| Unknown Azure `api-version` | 400 `UnsupportedApiVersionValue` + list | Azure API guidelines |
| Unknown GitHub `X-GitHub-Api-Version` | `410 Gone` | GitHub REST |
| GitHub header omitted after a version closes | default becomes the *next oldest supported*, not the closed one | GitHub REST |
| Accept matches nothing | 406 or a default media type | Azure Architecture; HTTP content negotiation |
| Unsupported request media type | 415 | Azure Architecture |
| gRPC package/service/method renamed or removed | `UNIMPLEMENTED` | Microsoft gRPC versioning |
| GraphQL removed field still queried | validation error | graphql.org |
| After advertised sunset | RFC 8594: likely 4xx, 3xx, or no interaction; **not specified which** | RFC 8594 §3 |

**Reconnect** is client migration, not a socket retry: pin/header/path change, regenerate stubs, drop deprecated GraphQL fields. RFC 8594: clients **SHOULD** treat `Sunset` as a *hint* — availability until or after the timestamp is not guaranteed. Clients that ignore it “operate as usual and simply may experience the resource becoming unavailable.”

**Behavior breaks that look like wire-safe adds.** Microsoft gRPC: new request field + server rejects default = break. GraphQL: new enum value + client exhaustive match = runtime miss. Proto3: new code treats default `0` / `""` as “user said zero” (protobuf Best Practices: “Almost never change the default value”; proto3 removed the ability).

## Proxy / gateway version routing

Version selection is an L7 concern. L4 balancers cannot see it. [The gateway](ApiGateway.md) is the usual place this lands; this section is the *contract* that hop implements.

- **AWS API Gateway** custom-domain routing rules (REST APIs): up to **two** header conditions and **one** base-path condition, combined with AND; header match is literal + value glob; base-path match is case-sensitive; action is `InvokeApi` to an API id + **stage**; optional `stripBasePath`; priority **1–1,000,000**, lowest first; mode `ROUTING_RULE_THEN_API_MAPPING` evaluates all rules before mappings; target API and domain must be same account; no mixing public and private.
- **Kong Gateway** Routes: match on protocols, hosts, methods, **headers**, paths, port, SNI. Expressions router recommended from **3.4.x**; if an `expression` Route matches, the JSON router does not run. Traditional JSON priority is computed from how many criteria are set.
- **Envoy** HTTP router: prefix/exact/regex path match plus arbitrary header match; the generic match tree can key on any request header (including `:path`). Place the more specific version route before the catch-all.
- **Cache / intermediary interactions** (Azure Architecture): URI and query-string versioning are cache-friendly *if* the cache keys the full URI. Header and media-type versioning require the cache to vary on those headers; otherwise one version’s (or one tenant’s) representation is reused. Preserve `Host` / `X-Forwarded-Host` when the version or tenant is hostname-based.
- **Google’s published pattern** (“Versioning APIs at Google”): one backend serves multiple majors; the **proxy** uses the path version to choose the surface and to report per-version usage so you can tell when an old major is empty enough to retire.

**Trade-off.** Path versioning is the cheapest thing for an off-the-shelf reverse proxy (prefix route). Header / media-type versioning keeps one resource URI and needs L7 inspection, `Vary`, and more careful cache keys. Query `api-version` (Azure) is explicit, forbids silent defaults, and forces every follow-up link to carry the parameter.

## Verified defaults (fetched 2026-09-13)

| Artifact | Version / date | Default that matters |
|---|---|---|
| OpenAPI Specification | **3.1.2**, 19 September 2025 | `openapi` = spec feature set; tooling **SHOULD** treat all `3.1.*` alike. `info.version` = **document** version, *not* the API version and *not* the OAS version. Schema Object is a superset of JSON Schema Draft 2020-12. Operation / Parameter / Header `deprecated` default **`false`**. |
| AsyncAPI | **3.1.0**, released 2026-01-31 | Protocol-agnostic message API (`channels` + `operations`). Schema `deprecated` default **`false`**. |
| Protocol Buffers proto3 | Language Guide | `deprecated = true` on a field: Java `@Deprecated`; C++ clang-tidy; “most languages: no actual effect.” |
| GraphQL | **September 2025** edition (`spec.graphql.org/September2025/`) | Built-in `directive @deprecated(reason: String! = "No longer supported")` on `FIELD_DEFINITION \| ARGUMENT_DEFINITION \| INPUT_FIELD_DEFINITION \| ENUM_VALUE`. **Must not** appear on required (non-null without default) arguments or input fields. Introspection `includeDeprecated` defaults **false**. Expanded input-value deprecation is new in this edition; `reason` became non-null. |
| HTTP Sunset | RFC **8594**, Informational, May 2019 | `Sunset: HTTP-date`; **SHOULD** be in the future; treat as a hint. Link relation `rel="sunset"`. |
| HTTP Deprecation | RFC **9745**, Standards Track, March 2025 | `Deprecation` is an Item Structured Field; value **MUST** be an RFC 9651 Date (`@` + Unix seconds). Example: `Deprecation: @1688169599`. If `Sunset` is also sent, its timestamp **MUST NOT** be earlier than `Deprecation`. The two headers use *different date formats* “for historical reasons.” Deprecation **does not change resource behavior**. |

**GitHub vs RFC 9745.** GitHub documents `Deprecation` as an **HTTP-date per RFC 7231**, not `@seconds`. Do not assume GitHub implements RFC 9745. Azure’s in-version break uses a vendor header `azure-deprecating` (semicolon-delimited, “purely informational to a human”) — also not RFC 9745.

**Industry selectors** (not universal defaults): Google AIP-185 path `/v1` + proto package, IBV omit is configuration-dependent, beta removal *recommended* 180 days; Azure required `?api-version=YYYY-MM-DD`, none if omitted; GitHub header default `2022-11-28`, ≥ 24 months; Stripe `Stripe-Version` date with account pin on first request and `/v1` reserved (2017). Stripe’s 2026 docs also describe named majors (Acacia, Dahlia, …) with monthly compatible releases; treat the changelog, not this page, as SoT for “what is current.”

### Pact verifies the *current* provider

Pact is consumer-driven: the consumer writes the assumptions; the **provider’s current code** (the commit under test) verifies those pacts. It does not replay an old provider binary. Recommended provider-change verification (branches/environments; tags are superseded):

```js
consumerVersionSelectors: [
  { mainBranch: true },
  { matchingBranch: true },
  { deployedOrReleased: true },
]
enablePending: true
// on provider main only:
includeWipPactsSince: "2020-01-01"
publishVerificationResult: process.env.CI === "true"
```

- `{ latest: true }` is **explicitly not recommended** (race when many branches publish).
- **Pending pacts** stop a newly changed consumer contract from breaking the provider’s main build.
- **WIP pacts** pull newly changed contracts without editing selectors; typically enable only on provider main.
- When a pact *changes*, a broker webhook should run the provider with `pactUrls: [process.env.PACT_URL]` only — do **not** also set broker URL / selectors / pending / WIP in that mode.
- **can-i-deploy**: `pact-broker can-i-deploy --pacticipant P --version V --to-environment ENV` (exit 0 = yes). After deploy: `record-deployment`. The matrix is consumer version × provider version × verification success against *whatever is already in that environment*.
- Mobile: `--pacticipant Consumer --all prod` so the provider stays compatible with every still-tagged production client.

Pact is complementary to OpenAPI: OpenAPI is the producer’s catalog; a pact is *what this consumer actually calls*. Neither replaces proto/SDL compatibility rules. The killer property vs schema diffs: removing a field nobody consumes verifies green — the contract encodes *usage*, which schema rules cannot see.

graphql-js v17: `findBreakingChanges()` / `findDangerousChanges()` remain but are **deprecated for removal in v18** in favor of `findSchemaChanges()`. They compare `GraphQLSchema` objects, not SDL strings. Breaking examples: remove field/type/enum value; add a required argument. Dangerous: add an enum value; add an optional argument.

## When not to version

- Internal APIs with lockstep deploys and clients that ignore unknown JSON fields (Azure “No versioning”).
- GraphQL public or BFF schemas — version the *field*, not the endpoint (graphql.org; Apollo).
- proto3 / Avro additive changes that stay within the encoding’s compatibility rules — do **not** bump `package …v2` or `/v2` for a new optional field (Microsoft gRPC: “Don’t update the version number unless making breaking changes”).
- Preview/visibility labels (AIP-185 visibility) instead of a new major for incremental preview.
- When the platform already pins the consumer (Stripe-style account pin) — do not *also* require a path major for every compatible add.
- When you cannot operate two surfaces (tiny team, no transform layer) — freeze the contract and add *new resources* rather than `/v2`.

A new version *is* the tool for: cross-org public HTTP APIs with breaking shape changes; a gRPC package rename required by a protocol break; a date pin so each incompatible change is small; a required `api-version` so two Azure resources never silently disagree; a gateway stage so v1 and v2 scale and fail independently.

## Failure modes

- **Major-version trap.** Stripe 2017: `/v2` upgrades are “almost as painful as re-integrating from scratch”; users stick; you maintain the old surface forever or cut them off.
- **Silent default.** GitHub’s omitted-header default plus “after close, default jumps to the next oldest supported” means unversioned clients observe a behavior change without sending a new header. Azure’s required `api-version` is the opposite failure mode (more 400s, no surprise).
- **Wrong granularity.** One “v2 for the whole estate” either never ships or breaks healthy resources. AIP-185 IBV and GraphQL field-level deprecation exist to avoid that.
- **JSON / TextProto vs binary protobuf.** Rename is wire-safe in binary and breaking in JSON. Transcoding gateways hide this until a REST client appears.
- **Unknown-field loss.** Proto3 JSON or field-by-field DTO mapping drops tags — the Figure 5-1 round-trip in [encoding-overview](../data-intensive-design/encoding-overview.md).
- **Cache poisoning / cross-version bleed.** Header or media-type version without `Vary`.
- **Hint-as-guarantee.** Automating cutover on `Sunset` against RFC 8594’s “hint” will strand clients if the date moves.
- **CDC against the wrong pact.** `{ latest: true }` or unpublished verification results make `can-i-deploy` lie.
- **Schema rollback.** graphql.org: rolling back a published GraphQL schema can break clients that already adopted the new field; fix forward except when you control every client and nothing has adopted.

## Trade-offs

| Strategy | Buy | Pay |
|---|---|---|
| Additive only / GraphQL `@deprecated` | One surface; clients adopt at their pace | Cannot change meaning; removal waits on the slowest client |
| Path `/vN` | Cheap proxy routing; obvious cache key | URI identity split; HATEOAS duplication; coarse majors |
| Query `api-version` | Explicit; Azure-standard; no silent omit | Every link must carry it; some caches skip query URIs |
| Header / account pin | Stable URIs; incremental dates (Stripe, GitHub) | L7 required; `Vary`; defaults surprise unversioned clients |
| Media type | Content negotiation + HATEOAS | Custom `vnd.` types; 406; cache duplication |
| gRPC package major | Two services, one process; proto rules intact | Generated-type duplication; `UNIMPLEMENTED` on mis-pointed clients |
| Pact CDC | Verifies *current* provider vs real consumers | Not a schema language; needs broker + `can-i-deploy` discipline |

The contract is the *what*; the [gateway](ApiGateway.md) often carries the *where*; the [encoding notes](../data-intensive-design/encoding-overview.md) carry the *how* of the bytes underneath.

## Sources

Verified 2026-09-13; full URLs, fetch dates, and exclusions in the [external research note](../../docs/research/sysdesign/a6-api-contracts-external-research.md). Do not treat §8 of that note as fact.

Key primaries: Google AIP-185 and “Versioning APIs at Google”; Azure Architecture Center API design plus Microsoft/api-guidelines Azure `api-version` rules; GitHub REST api-versions; Stripe 2017 versioning post and current versioning docs; Troy Hunt 2014 (via [encoding-references](../data-intensive-design/encoding-references.md)); protobuf proto3 Language Guide and Best Practices; Microsoft gRPC versioning (ASP.NET Core 10); graphql.org schema-change-management, September 2025 spec §3.13.3, and Apollo GraphOS deprecations; OpenAPI 3.1.2 and AsyncAPI 3.1.0; Pact recommended configuration, consumer-version selectors, and `can-i-deploy`; RFC 8594, RFC 9745, RFC 9651; AWS API Gateway routing rules, Kong Routes, Envoy HTTP router. Compatibility vocabulary cited via [encoding-overview](../data-intensive-design/encoding-overview.md); GraphQL-as-query-contract via [graphql.md](../data-intensive-design/graphql.md).
