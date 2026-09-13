---
type: research
title: 'API contracts & versioning — external research (2026-09-13)'
description: >-
  Source-verified research backing the API contracts & versioning Concept
  (A6): the AIP-180/181 breaking-change and stability canon, protobuf/gRPC
  evolution rules, four versioning strategies with verified precedents
  (AIP-185 URI, GitHub calendar headers, Stripe account-pinned rolling
  releases, GraphQL versionless), RFC 8594 Sunset and RFC 9745 Deprecation
  with Zalando/GitHub adoption, contract testing (Pact, BDCT, buf/oasdiff/
  GraphQL Inspector gates), spec formats, evolution discipline, and
  field-usage-driven removal.
tags: [research, api-versioning, contracts, deprecation, pact, system-design-patterns]
---

# A6 API contracts & versioning — external research (2026-09-13)

**Method.** Facts verified against primaries 2026-09-13; paraphrase; per-source dates in §Sources. This report adds the API-contract layer over the repo's wire-format notes — [encoding-overview](../../../cases/data-intensive-design/encoding-overview.md), [protobuf-schema-evolution](../../../cases/data-intensive-design/protobuf-schema-evolution.md), [avro-schema-evolution](../../../cases/data-intensive-design/avro-schema-evolution.md), [graphql](../../../cases/data-intensive-design/graphql.md), [rest-rpc-dataflow](../../../cases/data-intensive-design/rest-rpc-dataflow.md) — and does not re-derive them.

## 1. What is a breaking change

- **AIP-180** (upd. 2025-10-21): three planes — **source** (old code compiles), **wire** (old clients interoperate), **semantic** (behavior matches expectations). MAY add interfaces/methods/messages/fields/enum values — but "New required fields must not be added to existing request messages"; new fields need behavior-preserving defaults; formerly server-populated fields must keep being populated. MUST NOT within a major: remove or rename (rename ≡ remove; keep the old alongside), move components between proto files (C++/Python codegen) or into/out of `oneof` (Go), change a field's type **even when wire-compatible** (source compatibility binds), change resource-name formats (names persist across majors), change defaults or visible semantics.
- **AIP-181**: alpha (breaking expected), beta (public; incompatible changes after a declared deprecation window; ~90-day promotion guidance — approximate), stable (no breaking changes for the major's life; escapes: new major, governance-approved isolated change, security/legal).
- **Protobuf** (proto3 guide): never change field numbers; `reserved` removed numbers/names; adds are safe (unknown fields skipped and preserved). Wire fine print: int32/uint32/int64/uint64/bool interchange on the wire but 64→32 **truncates** (wire-parseable ≠ value-safe); sint* is its own group; string↔bytes only for valid UTF-8; enum ↔ int family; moving an existing field into an existing oneof is unsafe.
- **gRPC** (Microsoft versioning guide, 2024-09-27): non-breaking — add service/method/fields/enum values. Binary-breaking but wire-safe — remove field, rename message: old binaries fine, regeneration breaks compilation. Protocol-breaking — field-number change, incompatible types, **renaming package/service/method** (the request path is `package.Service/Method` → old clients get UNIMPLEMENTED). Behavior breakage: adding an optional field then rejecting its absence. Recommended: major version in the proto package (`greet.v1` → `v2`), hosted side by side.

## 2. Versioning strategies with precedents

- **URI major version** (AIP-185, 2024-10-22): major version ends the proto package and starts the REST path (`/v1/…`); no minor/patch; `v1beta`/`v1alpha` channels; a new major must not depend on the old. Counterpoint: **Zalando #115 forbids URL versioning** (#114 mandates media-type versioning when unavoidable; #113 avoid versioning) — the two most-cited guides disagree.
- **Header calendar versions** (GitHub): pre-2022 = a decade on "v3" via `Accept: application/vnd.github.v3+json`. Since 2022-11-28: `X-GitHub-Api-Version: <date>`; omitted → default `2022-11-28`; unsupported → **410 Gone**; breaking = remove/rename/require/auth changes; additive lands in **all** supported versions; ≥ 24-month support. Milestone: `2026-03-10` — "the first calendar version to include breaking changes" — with 2022-11-28 supported until 2028-03-10. Near retirement GitHub emits Deprecation + Sunset headers; **after sunset, unversioned requests silently roll to the next-oldest version**.
- **Account-pinned rolling versions** (Stripe): account default pinned at first API call; per-request `Stripe-Version` override; webhooks pin at endpoint creation; SDK releases pin the current version. Since 2024-10: **biannual majors with breaking changes, named alphabetically after plants** (acacia, basil, clover, dahlia — current `2026-08-26.dahlia`), plus compatible monthlies. Backward-compatible list: new resources/optional params/response properties, property reordering, opaque-string format changes (ids ≤ 255 chars), new event types. Upgrades **roll back within 72 h**, failed webhooks retried in the old shape.
- **Versionless evolution** (graphql.org governance-versioning): "GraphQL favors evolution over versioning" — clients request only needed fields, so additions are invisible. Safe: new fields/types/operations, optional args with behavior-preserving defaults, required→optional inputs. Breaking: remove/rename, type changes, enum-value removal, optional→required args, non-null→nullable.

## 3. Deprecation signaling

- **RFC 8594 Sunset** (2019, Informational): HTTP-date when the resource becomes unresponsive; a hint; per-resource scope; `sunset` link relation.
- **RFC 9745 Deprecation** (**March 2025, Standards Track — completed**): `Deprecation: @1688169599` — Structured-Field Date (@ + Unix seconds); deprecated = still works, stop depending; Sunset must not precede Deprecation; `deprecation` link relation → migration docs.
- **Adopters**: Zalando #189 prescribes the pair (discourages the link relations; notes the two headers' formats differ "due to historic reasons"; earliest timestamps win across multiple deprecated elements) with process rules #185 client approval before shutdown, #186 partner consent, #187 deprecation in the OpenAPI spec, #188 **monitor usage of deprecated elements**, #190 clients watch for the headers, #191 clients must not newly adopt deprecated APIs. GitHub documents emitting both — but its Deprecation value is an HTTP-date (pre-9745 draft format): a live example of standards outrunning deployments.

## 4. Contract testing

- **Pact**: consumer tests against a mock generate the pact file (exact request/response pairs the consumer uses); provider verification replays it; the Broker holds the compatibility matrix; **`can-i-deploy`** gates releases on verified compatibility with what is deployed. HTTP + message interactions. The contract covers only what consumers use — removing an unconsumed field verifies green, which is the discipline wire rules lack.
- **Bi-directional contract testing** (PactFlow): static comparison of a consumer contract vs a **provider OpenAPI contract** self-verified by the provider's own tests; nothing is replayed; for retrofits/gateways/many-consumer APIs; commercial; weaker than replay.
- **Schema-diff CI gates**: **buf breaking** — categories FILE (default; generated-code layout), PACKAGE (Go-friendly moves), WIRE_JSON (binary+JSON; the floor for transcoding), WIRE (binary only) — operationalizing AIP-180's source-vs-wire split; **oasdiff** (`breaking`, `changelog`; OAS 3.0/3.1/3.2; GitHub Action); **GraphQL Inspector** — breaking/dangerous/non-breaking, fails CI on breaking, `considerUsage` downgrades breaking changes no live client touches.

## 5. Spec formats as contracts

- **OpenAPI**: 3.0.0 2017; **3.1.0 2021-02-16** — Schema Object became "a superset of JSON Schema Draft 2020-12", ending the subset fork so API tooling and JSON Schema tooling share one validation semantics; 3.2.0 2025-09-19.
- **AsyncAPI**: the event-contract counterpart; **3.0.0 2023-12-05** (channel/operation decoupling, send/receive, request-reply), 3.1.0 2026-01-31 compatible.
- **Design-first** (Zalando #100 API-first MUST): spec authored and linted before implementation; #192 publish it. Design-first makes the spec the reviewed artifact diff gates and deprecation annotations attach to.

## 6. Evolution discipline

- **Additive-only by default**: AIP-180, Stripe, GitHub (additive → all versions), GraphQL all converge; Zalando #106/#107.
- **Tolerant reader** (Fowler 2011-05-09): consume only what you need, ignore the unknown, avoid rigid schema-bound deserialization, localize parsing; Zalando **#108 makes it MUST** — tolerate unknown fields, don't drop them on round-trip PUT, handle unknown enum values (#112 prefers open value lists).
- **Removal choreography** (composite of verified fragments; the dual-write framing itself is synthesis): deprecate in the spec (#187, @deprecated, AIP-181 windows) → signal at runtime (Deprecation/Sunset) → **measure** (#188; Apollo field usage) → consent where contractual (#185/#186) → remove only in a new major / after sunset (AIP-180; GitHub 410). AIP-180's keep-populating rule is the response-side dual-write obligation.
- **Support windows are time-based or pin-forever, not N-2**: GitHub ≥ 24 months (2022-11-28 → 2028-03-10); Stripe pins indefinitely with 72-h rollback; AIPs: major's lifetime + communicated deprecation.

## 7. GraphQL specifics

- `@deprecated` (Oct 2021 spec §3.13.3): FIELD_DEFINITION | ENUM_VALUE, Markdown reason, introspectable; the **working draft** extends to arguments/input fields (not yet a released edition).
- Persisted-query safelists (cite forward to the [gateway note](api-gateway-external-research.md) §6): a safelisted PQL is a closed enumeration of production operations — "is this breaking?" becomes a decidable diff against the manifest, the GraphQL analog of a Pact broker.
- **Field usage** (Apollo GraphOS Insights): per-field requests vs executions vs client versions (they diverge: list fields execute N× per request; federation `@requires` executes unrequested; null short-circuits to zero) — the measurement leg of removal, and what `considerUsage` consumes.

## Sources

aip.dev/180 (2025-10-21), /181, /185 (2024-10-22) · protobuf.dev proto3 updating · learn.microsoft.com grpc/versioning (2024-09-27) · docs.github.com api-versions + github.blog 2022-11-28 + changelog 2026-03-12 · docs.stripe.com versioning/upgrades/changelog + stripe.com blog 2024-10-01 · graphql.org/learn/governance-versioning · RFC 8594 · RFC 9745 · opensource.zalando.com/restful-api-guidelines (rules 100, 106–116, 185–193) · martinfowler.com TolerantReader (2011-05-09) · docs.pact.io · PactFlow BDCT overview · buf.build/docs/breaking/rules · github.com/oasdiff/oasdiff · the-guild.dev graphql/inspector diff · spec.openapis.org 3.1.0 §4.4 + OAI releases · asyncapi.com 3.0.0/3.1.0 notes · spec.graphql.org October2021 §3.13.3 + draft · apollographql.com GraphOS field-usage. Context (not re-verified): the four data-intensive-design notes + [api-gateway-external-research.md](api-gateway-external-research.md).

## Uncertain / could not verify (excluded from the Concept)

- Dual-write/dual-read choreography as a named sequence: synthesis over verified fragments.
- "N-2" support windows: folklore; no fetched policy is count-based.
- Stripe end-of-support for old pins: implied by the model, not guaranteed in writing.
- AIP-181 ~90-day beta promotion: approximate (summarized fetch).
- Zalando revision id: living doc, dated by newest content (≥ 2025-11-27).
- oasdiff rule count/release: existence + commands verified only.
- GitHub Deprecation header live format: docs say HTTP-date (pre-RFC); not captured on the wire.
- graphql.org pages undated post-restructure.
