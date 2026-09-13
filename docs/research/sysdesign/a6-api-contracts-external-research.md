---
type: research
title: 'API contracts & versioning — external research (2026-09-13)'
description: >-
  Source-verified research on REST/gRPC/GraphQL contract evolution: compatibility
  rules, URI vs header vs media-type versioning, proto3 and GraphQL additive
  change, OpenAPI 3.1 / AsyncAPI artifacts, Pact current-provider verification,
  RFC 8594 / RFC 9745 deprecation headers, and gateway version routing.
tags: [research, system-design-patterns, a6, api-contracts]
---

# API contracts & versioning — external research (2026-09-13)

> **What this is.** The evidence pass for catalog id **A6** (API contracts & versioning). Group A depth bar is mapped onto *contract evolution*: wire compatibility, version-selection lifecycle, concurrent-version fan-out, mismatch failure, proxy/gateway routing, verified defaults, and when not to version. This note does **not** rewrite [encoding-overview](../../../cases/data-intensive-design/encoding-overview.md) or [graphql](../../../cases/data-intensive-design/graphql.md); it links them. Proto3 / Avro field-level rules are owned by [protobuf-schema-evolution](../../../cases/data-intensive-design/protobuf-schema-evolution.md) and [avro-schema-evolution](../../../cases/data-intensive-design/avro-schema-evolution.md) — cited, not re-derived.
>
> **Method.** Primary pages fetched 2026-09-13. Numbers and identifiers are reproduced exactly. Claims that could not be pinned to a primary page sit in §8 and are **not** implied as fact.

---

## 1. Scope and non-goals

**Owns.** How a published API *contract* evolves while old and new clients and servers coexist: backward/forward compatibility of the request/response (or schema), how a client *names* the version it wants, deprecation and sunset signaling, consumer-driven verification of the *current* provider, and how a proxy or gateway routes by version.

**Does not own.**

| Sibling | Boundary |
|---|---|
| **A1** Request–response | HTTP/gRPC *call* semantics (idempotency, timeouts, status mapping). A6 owns the *shape* of that call over time. |
| **E2** Microservices | Independent deployability as a style. A6 is the contract that makes that deployability possible. |
| **C6** API gateway / BFF | Gateway as a product surface. A6 owns *version routing* as a contract concern the gateway implements. |
| **E12** CQRS | Command/query split and event-sourced models. Event *schema* evolution belongs with Avro/protobuf notes, not here. |

Also out of scope: auth/identity, rate limits, and A1 retry/circuit-breaker policy.

---

## 2. Lineage / vocabulary

**Compatibility directions** (from [encoding-overview](../../../cases/data-intensive-design/encoding-overview.md), do not re-derive): *backward* = newer code reads older data; *forward* = older code reads newer data. For APIs the pair flips by role. An older client calling a newer service needs backward compatibility on the *request* and forward compatibility on the *response*. [rest-rpc-dataflow](../../../cases/data-intensive-design/rest-rpc-dataflow.md) adds the operational assumption: **servers upgrade first, clients second**. Cross-organization APIs cannot force that, so multiple versions often run side by side.

**Semantic versioning, applied loosely.** Google AIP-185 (fetched 2026-09-13): a major version is encoded at the end of the protobuf package and as the first URI-path segment for REST; Google APIs **must not** expose minor or patch in the URL (`v1`, not `v1.0` / `v1.1`). Minor-equivalent changes land in place. A new major **must not** depend on a previous major. Different majors of the same API must work in one client for a documented transition; an older major must go through a communicated deprecation before shutdown.

**Breaking vs additive (REST, GitHub REST, fetched 2026-09-13).** Breaking: remove/rename an operation, parameter, or response field; add a required parameter; make an optional parameter required; change a type; remove enum values; add a validation rule; change auth. Additive (available in all supported versions): add an operation, optional parameter, optional request header, response field, response header, or enum value.

**Who names the version.** [rest-rpc-dataflow](../../../cases/data-intensive-design/rest-rpc-dataflow.md) cites Troy Hunt (2014) that there is no agreement, and Brandur Leach / Stripe (2017) that an account can pin a version server-side. Both remain the two poles: *client-sent selector* vs *server-remembered pin*.

**Deprecate ≠ sunset.** RFC 8594 §1.4 (Informational, May 2019): Sunset is for the *second* stage — the resource will become unresponsive — not for “no longer preferred.” RFC 9745 (Standards Track, March 2025) fills that first stage with `Deprecation`. GitHub’s REST docs (fetched 2026-09-13) use both headers together: `Deprecation` = closing-down date; `Sunset` = retirement, after which requests return `410 Gone`.

---

## 3. Mechanics (Group A bar, mapped onto contract evolution)

### 3.1 Wire semantics — compatibility rules

**REST / JSON.** Compatible by convention, not by codec. Additive: new optional request fields (server must succeed when absent), new response fields (clients must ignore unknowns). Breaking: rename/remove, type change, newly required input, newly non-null output that can be absent, enum *removal*. Azure Architecture Center (ms.date on the “Implement versioning” section; page fetched 2026-09-13) treats “no versioning” as viable for internal APIs *if* clients ignore unrecognized fields; field removal/rename is the point at which a version selector is required.

**gRPC / proto3 binary** (protobuf Language Guide, proto3, fetched 2026-09-13; do not re-state the field-tag essay in [protobuf-schema-evolution](../../../cases/data-intensive-design/protobuf-schema-evolution.md)).

Wire-safe: add a field (old binaries skip it; new code sees the proto3 default when old writers omit it); remove a field *if* the number is reserved; add an enum value (numeric; unknown values are preserved, representation is language-dependent). Wire-unsafe: change a field number; move fields into an existing `oneof`. Conditionally compatible (lossy if values exceed the old type): `int32`/`uint32`/`int64`/`uint64`/`bool`; `sint32`↔`sint64`; `string`↔`bytes` when UTF-8; `fixed32`↔`sfixed32`; `enum`↔ integer types. Field numbers `1`–`15` encode in one byte; `16`–`2047` in two; legal range `1`–`536,870,911`; **`19,000`–`19,999` reserved for the protobuf implementation**. Proto3 messages **preserve unknown fields** on binary parse/serialize; they are **lost** on JSON serialize and on field-by-field copy. `reserved 2, 15, 9 to 11;` and `reserved "foo", "bar";` cannot be mixed in one statement. Ranges are inclusive.

Microsoft’s gRPC versioning page (ASP.NET Core 10, fetched 2026-09-13) splits further: *protocol* non-breaking vs *binary* (generated stubs) vs *behavior*. Adding a request field is protocol-safe **unless** the server errors when the field is unset. Renaming a field is not a protobuf-protocol break (identity is the number) but **is** a break under JSON transcoding. Renaming package, service, or method changes the HTTP/2 path (`/{package}.{Service}/{Method}`) and yields `UNIMPLEMENTED`. Removing a method likewise.

**GraphQL** ([graphql](../../../cases/data-intensive-design/graphql.md) owns “what GraphQL is”; this paragraph owns evolution). graphql.org “Schema Change Management” (fetched 2026-09-13): prefer *one* evolving schema; `/graphql/v2` is allowed but “sacrifices GraphQL’s benefits.” Safe additive: new fields, types, queries/mutations, optional arguments, making a required field optional. Breaking: remove/rename fields or types; change a field type; remove/rename enum values; make an optional argument required; change argument types; make a non-null field nullable (the page also lists the inverse — making a nullable field non-null — as breaking, because existing nulls become errors). Dangerous-but-structurally-additive: new enum values (exhaustive switches); new interface implementations (`__typename` surprises). Optional arguments must default to the previous behavior.

**Avro** is two-schema resolution by *name* plus reader defaults — see [avro-schema-evolution](../../../cases/data-intensive-design/avro-schema-evolution.md). Relevant here only as the contrast: protobuf is self-skipping tags; Avro needs the writer’s schema (registry / file header / handshake).

### 3.2 Version-selection lifecycle (the “connection” of a contract)

A contract does not have a TCP handshake. The lifecycle that plays the same role:

1. **Publish** a machine-readable artifact (OpenAPI / AsyncAPI / `.proto` / GraphQL SDL).
2. **Select** a version (or “latest additive surface”) on each request, or pin it to an account.
3. **Evolve additively** in place on that major / date / schema.
4. **Deprecate** (signal: still works).
5. **Sunset** (signal: will become unresponsive at a time).
6. **Remove** (mismatch becomes a hard error). Clients that cannot update (mobile stores, partner ISVs) stay on an older pin until sunset.

**URI / path versioning.** `/v2/customers/3`. Azure Architecture Center: simple to route; HATEOAS links must carry the version; REST purists object that the resource identity should not change. Google AIP-185 *requires* the major in the first path segment (`/v1/...`). Stripe (Leach, 2017-08-05) keeps `/v1/` as a reserved major and does the real work in date versions; the 2017 post says `/v1` was “not likely to change for some time” after ~100 incompatible upgrades in six years.

**Query-string versioning.** Azure Architecture: `?version=2` keeps one URI; default if omitted (their example: `1`). HATEOAS still needs the parameter. **Cache caveat:** “Some older web browsers and web proxies don’t cache responses for requests that include a query string.” Azure *service* guidelines (Microsoft/api-guidelines `azure/Guidelines.md`, fetched 2026-09-13) go further: **required** `api-version` on *every* operation (`YYYY-MM-DD`, `-preview` suffix); omit → HTTP 400 `MissingApiVersionParameter`; unknown → 400 `UnsupportedApiVersionValue` listing all still-supported stables plus the latest public preview; **DO NOT** put a version segment in the path; preview retirement ≥ 90 days notice; a preview must GA or be removed within 1 year; preview date and GA date must differ.

**Header versioning.** Azure Architecture example: `Custom-Header: api-version=2` (illustrative name, not a standard). GitHub REST (fetched 2026-09-13): `X-GitHub-Api-Version: 2026-03-10`; omit → default **`2022-11-28`**; unsupported → `410 Gone`. Supported as of fetch: `2026-03-10` (EOS not scheduled) and `2022-11-28` (EOS **10 March 2028**). Support window: previous version kept **at least 24 months** after a newer version ships. Stripe: first request pins the account to the then-current date version; override with `Stripe-Version`; `/v2` *requires* the header. Google IBV (AIP-185): `X-Goog-Api-Version` **or** `$apiVersion` query; stable versions are `YYYY-MM-DD`, previews `YYYY-MM-DD-preview`; omit → configured default, consumer override, or reject.

**Media-type versioning.** `Accept: application/vnd.contoso.v1+json`; response `Content-Type` echoes the chosen type. Unknown Accept → **406 Not Acceptable** or a default media type (Azure Architecture). Best fit for HATEOAS (links can carry the MIME type). Requires `Vary: Accept` (and any custom version header) at caches — see §3.5.

**GraphQL / “don’t version.”** One schema; `@deprecated`; remove when usage is gone. graphql.org: some orgs announce three months ahead and change only at quarter boundaries (example, not a default). Apollo GraphOS (fetched 2026-09-13): wait until field usage is zero, or “minimally acceptable” for an unsupported mobile build.

**gRPC package majors.** `package greet.v1;` → service address `greet.v1.Greeter` beside `greet.v2.Greeter`. Microsoft: do not bump the package unless the change is breaking; share business logic behind both implementations; generated types differ so you map to a common model.

### 3.3 Scaling limits and fan-out

Fan-out here is **concurrent contract surfaces**, not HTTP/2 streams.

- **N majors × M date/channel pins.** Each surface is a transform, a test matrix, and a gateway route. Stripe’s 2017 design encapsulates each incompatible change as a *backwards* transform from “current” to the pinned version so core code stays on one shape — the cost is a growing transform chain and `has_side_effects` leaks. Google’s channel model caps this: at most one alpha, one beta, one stable per major; beta ⊇ stable, alpha ⊇ beta; IBV scopes a version as small as one RPC group.
- **Mobile / store-lag consumers.** Pact’s `--all TAG` / “all prod” selector exists specifically so a provider verifies against *every* still-installed consumer version, not just `latest`. GraphQL removal gated on usage, not on a calendar, is the same force.
- **Response-shape fan-out at the edge.** Azure Architecture on header/media-type versioning: many versions in a shared cache → duplicated entries; a cache that keys only on URI can serve the wrong version (or the wrong *tenant* — same page’s header-tenancy warning). Path versioning avoids that because the URI *is* the cache key.
- **GraphQL query fan-out** (N fields → M resolvers) is a GraphQL *execution* concern, not a versioning concern; do not treat it as A6.

No vendor publishes a numeric “max live API versions” default. The verified *policy* numbers are support windows (GitHub ≥ 24 months; Azure preview ≥ 90 days / ≤ 1 year; Google AIP-185 *recommends* 180 days before removing deprecated beta functionality). Those are policies, not protocol limits.

### 3.4 Failure and “reconnect” (mismatch and migration)

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

**Reconnect** is client migration, not a socket retry: pin/header/path change, regenerate stubs, drop deprecated GraphQL fields. RFC 8594: clients **SHOULD** treat `Sunset` as a *hint* — availability until/after the timestamp is not guaranteed. Clients that ignore it “operate as usual and simply may experience the resource becoming unavailable.”

**Behavior breaks that look like wire-safe adds.** Microsoft gRPC: new request field + server rejects default = break. GraphQL: new enum value + client exhaustive match = runtime miss. Proto3: new code treats default `0` / `""` as “user said zero” (no proto3 custom defaults — protobuf Best Practices, fetched 2026-09-13: “Almost never change the default value”; proto3 removed the ability).

### 3.5 Proxy / LB / gateway version routing

Version selection is an L7 concern. L4 balancers cannot see it.

**AWS API Gateway** custom-domain routing rules (REST APIs; fetched 2026-09-13): up to **two** header conditions and **one** base-path condition, combined with AND; header match is literal + value glob; base-path match is case-sensitive; action is `InvokeApi` to an API id + **stage**; optional `stripBasePath`; priority **1–1,000,000**, lowest first; mode `ROUTING_RULE_THEN_API_MAPPING` evaluates all rules before mappings; target API and domain must be same account; no mixing public and private.

**Kong Gateway** Routes (docs fetched 2026-09-13): match on protocols, hosts, methods, **headers**, paths, port, SNI. Expressions router recommended from **3.4.x**; if an `expression` Route matches, the JSON router does not run. Traditional JSON priority is computed from how many criteria are set (`hosts`+`headers` beats `hosts` alone).

**Envoy** HTTP router (latest docs fetched 2026-09-13): prefix/exact/regex path match plus arbitrary header match; generic match tree can key on any request header (including `:path`). Place the more specific version route before the catch-all.

**Cache / intermediary interactions** (Azure Architecture, fetched 2026-09-13): URI and query-string versioning are cache-friendly *if* the cache keys the full URI (query-string caching is historically uneven). Header and media-type versioning require the cache to vary on those headers; otherwise one tenant’s or one version’s representation is reused. Preserve `Host` / `X-Forwarded-Host` when the version or tenant is hostname-based.

**Google’s published pattern** (“Versioning APIs at Google”, Cloud Blog): one backend serves multiple majors; the **proxy** uses the path version to choose the surface and to report per-version usage so you can tell when an old major is empty enough to retire.

**Trade-off.** Path versioning is the cheapest thing for an off-the-shelf reverse proxy (prefix route). Header / media-type versioning keeps one resource URI and needs L7 inspection, `Vary`, and more careful cache keys. Query `api-version` (Azure) is explicit, forbids silent defaults, and forces every `nextLink` / `Operation-Location` to carry the parameter.

---

## 4. Verified defaults / standards (versions + fetch dates)

### 4.1 Protocol and spec artifacts

| Artifact | Version / date | Default that matters for contracts |
|---|---|---|
| OpenAPI Specification | **3.1.2**, 19 September 2025 (`spec.openapis.org/oas/v3.1`; 3.2.0 exists and is newer — this note targets 3.1 as requested) | `openapi` = spec feature set (`3.1`); tooling **SHOULD** treat all `3.1.*` alike. `info.version` = **document** version, *not* the API version and *not* the OAS version. Schema Object is a superset of **JSON Schema Draft 2020-12**. Operation / Parameter / Header `deprecated` default **`false`**. |
| AsyncAPI | **3.1.0**, released 2026-01-31 (minor, no breaking change from 3.0.0; bump `asyncapi: '3.1.0'`) | Protocol-agnostic message API (`channels` + `operations`). Schema `deprecated` default **`false`**. Default schema media type `application/vnd.aai.asyncapi;version=3.1.0`. |
| Protocol Buffers proto3 | Language Guide, fetched 2026-09-13 | See §3.1. `deprecated = true` on a field: Java `@Deprecated`; C++ clang-tidy; “most languages: no actual effect.” |
| GraphQL | **September 2025** edition (`spec.graphql.org/September2025/`, announced 2025-09-08; first edition since October 2021) | Built-in `directive @deprecated(reason: String! = "No longer supported") on FIELD_DEFINITION \| ARGUMENT_DEFINITION \| INPUT_FIELD_DEFINITION \| ENUM_VALUE`. **Must not** appear on required (non-null without default) arguments or input fields. Introspection `includeDeprecated` defaults **false**. Expanded input-value deprecation is new in this edition (RFCs #805, #1040, #1053, #1142). `reason` became non-null (`#1040`). |
| HTTP Sunset | RFC **8594**, Informational, May 2019 | `Sunset: HTTP-date` (RFC 7231 §7.1.1.1); **SHOULD** be in the future; treat as a hint. Link relation `rel="sunset"`. Header status in the registry: informational. |
| HTTP Deprecation | RFC **9745**, Standards Track, March 2025 (datatracker last-updated 2026-05-20) | `Deprecation` is an Item Structured Field; value **MUST** be an RFC 9651 Date (`@` + Unix seconds). Example: `Deprecation: @1688169599` (2023-06-30 23:59:59 UTC). Optional `rel="deprecation"` link. If `Sunset` is also sent, its timestamp **MUST NOT** be earlier than `Deprecation`. RFC 9745 notes the two headers use *different date formats* “for historical reasons.” Deprecation **does not change resource behavior**. |
| RFC 9651 Dates | Structured Fields | Date = seconds from 1970-01-01T00:00:00Z, leading `@`. Parsers MUST cover years 1–9999. |

**GitHub vs RFC 9745.** GitHub’s REST versioning page (fetched 2026-09-13) documents `Deprecation` as an **HTTP-date per RFC 7231** (`Wed, 27 Nov 2019 14:34:29 GMT`), not `@seconds`. That is the pre-9745 / Sunset-style date, not RFC 9745’s Structured Field. Do not assume GitHub implements RFC 9745. Azure’s approved in-version break uses a vendor header `azure-deprecating` (semicolon-delimited, “purely informational to a human,” not a parse contract) — also not RFC 9745.

### 4.2 Industry selectors (not universal defaults)

| Producer | Selector | Pin / default | Support window (as documented) |
|---|---|---|---|
| Google AIP-185 | Path `/v1` + proto package; IBV: `X-Goog-Api-Version` or `$apiVersion` | IBV omit: configured | Beta removal **recommended 180 days** after deprecation; alpha may vanish without notice |
| Azure services | Required `?api-version=YYYY-MM-DD` | None — 400 if omitted | Preview ≥ 90 days notice; preview ≤ 1 year |
| GitHub REST | `X-GitHub-Api-Version` | **`2022-11-28`** if omitted | ≥ 24 months after successor; then `410` |
| Stripe | `Stripe-Version` date (e.g. docs page title `2026-03-25.dahlia`; changelog “current” cited on that page as **`2026-08-26.dahlia`**) | Account pin on first request | Rolling date versions; `/v1` major reserved (2017 post) |

Stripe docs vs blog: the 2017 post describes pin-on-first-request and backwards transforms. The 2026 docs page additionally describes named major releases (Acacia, Dahlia, …) with monthly compatible releases sharing the last major’s name. Both were fetched 2026-09-13; the pin algorithm in current production code was **not** re-verified from source (§8).

### 4.3 Consumer-driven contracts — Pact verifies the *current* provider

Pact (docs.pact.io, fetched 2026-09-13) is CDC: the consumer writes the assumptions; the **provider’s current code** (the commit under test) verifies those pacts. It does not replay an old provider binary.

Recommended provider-change verification (branches/environments, **tags superseded**):

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
providerVersion: process.env.GIT_COMMIT
providerVersionBranch: process.env.GIT_BRANCH
```

- `{ latest: true }` is **explicitly not recommended** (race when many branches publish).
- **Pending pacts** stop a newly changed consumer contract from breaking the provider’s main build.
- **WIP pacts** pull newly changed contracts without editing selectors; typically enable only on provider main.
- When a pact *changes*, a broker webhook should run the provider with `pactUrls: [process.env.PACT_URL]` only — do **not** also set broker URL / selectors / pending / WIP in that mode.
- **can-i-deploy**: `pact-broker can-i-deploy --pacticipant P --version V --to-environment ENV` (exit 0 = yes). After deploy: `record-deployment`. The matrix is consumer version × provider version × verification success against *whatever is already in that environment*.
- Mobile: `--pacticipant Consumer --all prod` so the provider stays compatible with every still-tagged production client.

Pact is complementary to OpenAPI: OpenAPI is the producer’s catalog; a pact is *what this consumer actually calls*. Neither replaces proto/SDL compatibility rules.

### 4.4 GraphQL comparison helpers

graphql-js v17 (docs fetched 2026-09-13): `findBreakingChanges()` / `findDangerousChanges()` remain but are **deprecated for removal in v18** in favor of `findSchemaChanges()`. They compare `GraphQLSchema` objects, not SDL strings. Breaking examples: remove field/type/enum value; add a required argument. Dangerous: add an enum value; add an optional argument.

---

## 5. Failure modes and when-not-to-use

**Failure modes of versioning itself.**

- **Major-version trap.** Stripe 2017: `/v2` upgrades are “almost as painful as re-integrating from scratch”; users stick; you maintain the old surface forever or cut them off.
- **Silent default.** GitHub’s omitted-header default (`2022-11-28`) plus “after close, default jumps to the next oldest supported” means unversioned clients observe a behavior change without sending a new header. Azure’s required `api-version` is the opposite failure mode (more 400s, no surprise).
- **Wrong granularity.** One breaker-like “v2 for the whole estate” (Brooker's shard lesson, applied to contracts) either never ships or breaks healthy resources. AIP-185 IBV and GraphQL field-level deprecation exist to avoid that.
- **JSON / TextProto vs binary protobuf.** Rename is wire-safe in binary and breaking in JSON. Transcoding gateways hide this until a REST client appears.
- **Unknown-field loss.** Proto3 JSON or field-by-field DTO mapping drops tags — the Figure 5-1 round-trip in encoding-overview.
- **Cache poisoning / cross-version bleed.** Header or media-type version without `Vary` (Azure Architecture).
- **Hint-as-guarantee.** Automating cutover on `Sunset` against RFC 8594’s “hint” will strand clients if the date moves.
- **CDC against the wrong pact.** `{ latest: true }` or unpublished verification results make `can-i-deploy` lie.
- **Schema rollback.** graphql.org governance-tooling: rolling back a published GraphQL schema can break clients that already adopted the new field; fix forward except when you control every client and nothing has adopted.

**When not to version (prefer additive / no selector).**

- Internal APIs with lockstep deploys and clients that ignore unknown JSON fields (Azure “No versioning”).
- GraphQL public or BFF schemas — version the *field*, not the endpoint (graphql.org; Apollo).
- proto3 / Avro additive changes that stay within the encoding’s compatibility rules — do **not** bump `package …v2` or `/v2` for a new optional field (Microsoft gRPC: “Don’t update the version number unless making breaking changes”).
- Preview/visibility labels (AIP-185 visibility; Google Cloud often uses this instead of a new major for incremental preview).
- When the platform already pins the consumer (Stripe-style account pin, API key → stored version) — do not *also* require a path major for every compatible add.
- When you cannot operate two surfaces (tiny team, no transform layer) — freeze the contract and add *new resources* rather than `/v2`.

**When a new version *is* the tool.** Cross-org public HTTP APIs with breaking shape changes; gRPC package rename required by a protocol break; a date pin so each incompatible change is small (Stripe); a required `api-version` so two Azure resources never silently disagree; a gateway stage so v1 and v2 scale and fail independently (C6 implements, A6 specifies).

**Trade-off summary.**

| Strategy | Pro | Con |
|---|---|---|
| Additive only / GraphQL `@deprecated` | One surface; clients adopt at their pace | Cannot change meaning; removal waits on the slowest client |
| Path `/vN` | Cheap proxy routing; obvious cache key | URI identity split; HATEOAS duplication; coarse majors |
| Query `api-version` | Explicit; Azure-standard; no silent omit | Every link must carry it; some caches skip query URIs |
| Header / account pin | Stable URIs; incremental dates (Stripe, GitHub) | L7 required; `Vary`; defaults surprise unversioned clients |
| Media type | Content negotiation + HATEOAS | Custom `vnd.` types; 406; cache duplication |
| gRPC package major | Two services, one process; proto rules intact | Generated-type duplication; `UNIMPLEMENTED` on mis-pointed clients |
| Pact CDC | Verifies *current* provider vs real consumers | Not a schema language; needs broker + `can-i-deploy` discipline |

---

## 6. Cross-links

**Catalog siblings.** A1 (call semantics, not shape-over-time). E2 (why independent deployability needs these rules). C6 (gateway/BFF that *implements* §3.5 routing). E12 (CQRS/event-sourcing style — event schemas, not HTTP/RPC version selectors).

**Existing notes (link, do not rewrite).**

- [encoding-overview](../../../cases/data-intensive-design/encoding-overview.md) — compatibility vocabulary, unknown-field round-trip.
- [graphql](../../../cases/data-intensive-design/graphql.md) — GraphQL as an untrusted-client query contract.
- [protobuf-schema-evolution](../../../cases/data-intensive-design/protobuf-schema-evolution.md) — tags, reserve, skip.
- [avro-schema-evolution](../../../cases/data-intensive-design/avro-schema-evolution.md) — writer/reader schemas, defaults.
- [rest-rpc-dataflow](../../../cases/data-intensive-design/rest-rpc-dataflow.md) — servers-first, OpenAPI vs protobuf IDL, Hunt/Stripe citations [43]/[44] in encoding-references.
- Catalog of record: [system-design-patterns-catalog.md](system-design-patterns-catalog.md).

---

## 7. Sources

All retrieved **2026-09-13**.

**Compatibility and REST selectors.** google.aip.dev/185 · cloud.google.com/apis/design/versioning · cloud.google.com/blog/products/gcp/versioning-apis-at-google · learn.microsoft.com/azure/architecture/best-practices/api-design · github.com/Microsoft/api-guidelines/blob/HEAD/azure/Guidelines.md · docs.github.com/en/rest/about-the-rest-api/api-versions · stripe.com/blog/api-versioning (2017-08-05) · docs.stripe.com/api/versioning · troyhunt.com “Your API Versioning Is Wrong…” (2014; encoding-references [43]).

**gRPC / protobuf.** protobuf.dev/programming-guides/proto3 · protobuf.dev/best-practices/dos-donts · learn.microsoft.com/aspnet/core/grpc/versioning (aspnetcore-10.0).

**GraphQL.** spec.graphql.org/September2025/ §3.13.3 · graphql.org/blog/2025-09-08-september-edition · graphql.org/learn/governance-versioning · graphql.org/learn/governance-tooling · graphql-js.org/docs/schema-evolution · apollographql.com/docs/graphos/platform/production-readiness/change-management · apollographql.com/docs/graphos/schema-design/guides/deprecations.

**Contract artifacts.** spec.openapis.org/oas/v3.1 (v3.1.2, 2025-09-19) · spec.openapis.org/oas/ · github.com/asyncapi/spec/releases/tag/v3.1.0 · asyncapi.com/blog/release-notes-3.1.0 · asyncapi.com/docs/reference/specification/v3.1.0.

**CDC.** docs.pact.io/provider/recommended_configuration · docs.pact.io/pact_broker/advanced_topics/consumer_version_selectors · docs.pact.io/pact_broker/can_i_deploy · docs.pact.io/getting_started/versioning_in_the_pact_broker · docs.pact.io/implementation_guides/javascript/docs/provider.

**Deprecation headers.** rfc-editor.org/rfc/rfc8594 · datatracker.ietf.org/doc/rfc9745/ · rfc-editor.org/info/rfc9745 · httpwg.org/specs/rfc9651.html §3.3.7.

**Proxy / gateway.** docs.aws.amazon.com/apigateway/latest/developerguide/rest-api-routing-rules.html · docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-routing-rules-use.html · docs.aws.amazon.com/apigatewayv2/latest/api-reference/domainnames-domainname-routingrules-routingruleid.html · developer.konghq.com/gateway/entities/route · envoyproxy.io/docs/envoy/latest/intro/arch_overview/http/http_routing.

---

## 8. Uncertain / left out

- RFC 9745 HTML on rfc-editor.org returned **HTTP 409** to this agent; syntax and the Sunset-ordering rule are from datatracker / rfc-editor info snippets plus the RFC 8594 full text. Re-fetch the RFC 9745 HTML before quoting additional sections.
- Whether GitHub will migrate `Deprecation` from HTTP-date to RFC 9745 `@seconds` is not stated.
- Stripe’s *current* pin-on-first-request behavior and the exact `2026-08-26.dahlia` “current” string were read from docs pages that also show other date versions in the URL; treat the changelog, not this note, as SoT for “what is current.”
- AIP-185 IBV “must be rejected if no default” vs “may default” is configuration-dependent; no single Google-wide omit behavior.
- Azure Architecture `Custom-Header: api-version=2` is an *example name*, not a registered field. Production Azure services use `api-version` on the query string (guidelines) or `azure-deprecating` for in-version breaks.
- “Older browsers and proxies don’t cache query strings” is Azure Architecture’s wording; no current cache-product matrix was fetched.
- Envoy / Kong / API Gateway have **no** documented default named `x-api-version`. Routing examples above are capabilities, not presets.
- graphql-js v17 deprecation-of-helpers → v18 removal date is “in v18,” not a calendar day.
- Pact Broker / client library versions in the reader’s estate were not pinned; pending/WIP semantics assume a broker that implements “pacts for verification.”
- OpenAPI Overlay, Spectral rulesets, buf breaking-change linters, and GraphQL Inspector were not version-pinned; they are tooling, not contract semantics.
- Fielding’s mailing-list remarks on URI versioning were not re-fetched; the REST-purist objection is given via Azure Architecture’s own “purist” sentence.
- No controlled measurement of “how many concurrent versions is too many” was found.

---
