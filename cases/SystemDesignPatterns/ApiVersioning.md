---
type: reference
title: 'API contracts and versioning'
description: 'Evolve interfaces without breaking consumers: the AIP-180 breaking-change canon across source, wire, and semantic planes; four versioning strategies with real precedents (URI majors, GitHub calendar headers, Stripe pinned rolling releases, GraphQL versionless); RFC 9745 Deprecation and RFC 8594 Sunset; the tolerant reader; contract tests and schema-diff CI gates; and usage-measured removal.'
tags: [system-design-patterns, communication, api-versioning, contracts, deprecation]
---

# API contracts and versioning

**See also:** [request–response](RequestResponse.md) · [API gateway](ApiGateway.md) · [encoding & evolution (DDIA)](../data-intensive-design/encoding-overview.md) · [protobuf evolution](../data-intensive-design/protobuf-schema-evolution.md) · [avro evolution](../data-intensive-design/avro-schema-evolution.md) · [graphql (DDIA)](../data-intensive-design/graphql.md) · [external research note (2026-09-13)](../../docs/research/sysdesign/api-versioning-external-research.md)

An API is a promise to code you cannot redeploy. Wire-format evolution (field tags, schema resolution) is the [encoding layer's](../data-intensive-design/encoding-overview.md) problem; this Concept owns the **contract layer**: what counts as breaking, how versions are named and selected, how deprecation is signaled and measured, and which CI gates catch the break before a consumer does. Quality attributes: **evolvability** without flag days, **trust** (consumers upgrade on their schedule). Costs: every strategy is a standing tax — parallel versions, compatibility gates, deprecation bookkeeping — paid for as long as the API lives.

## What is breaking (the canon)

AIP-180 splits compatibility into three planes, and the split does work: **source** (old code still compiles), **wire** (old clients still interoperate), **semantic** (behavior still matches expectations). The condensed rules:

- **May add**: methods, messages, fields, enum values — but never a *required* field to an existing request; new fields need behavior-preserving defaults; fields the server used to populate must stay populated.
- **Must not, within a major**: remove or rename (rename ≡ remove — keep the old alongside); change a field's type **even when wire-compatible** (source compatibility binds — protobuf's int64→int32 parses and silently truncates); change resource names, defaults, or visible semantics.
- **gRPC adds path physics**: renaming a package, service, or method changes the request path — old clients get UNIMPLEMENTED. And the sneakiest class is behavioral: adding an optional field, then rejecting requests that omit it.
- GraphQL's versionless model has the same table with different names: additions invisible (clients pick their fields); removals, type changes, optional→required all breaking.

Stability channels (AIP-181): alpha may break; beta breaks only after a declared window; stable never breaks within the major. Name the channel, then obey it.

## Choosing a versioning strategy (all four have precedents)

| Strategy | Precedent (verified) | Character |
|---|---|---|
| **URI major** (`/v1/`) | Google AIPs: major in the proto package and the path; a new major must not depend on the old | Visible, cache-friendly, coarse — majors are expensive, so almost everything must be additive |
| **Header calendar versions** | GitHub since 2022: `X-GitHub-Api-Version: 2022-11-28`; unversioned = the old default; unsupported = 410; **first breaking calendar version only in 2026**, old default supported 24+ months | Fine-grained breaking changes without URI churn; the default version is a liability (after sunset, unversioned callers silently roll forward) |
| **Account-pinned rolling** | Stripe: version pinned per account at first call, per-request override, webhooks pinned per endpoint; biannual named majors (acacia → dahlia), compatible monthlies; 72-hour rollback | Consumers never move until they choose to; the provider carries every pinned behavior forever |
| **Versionless evolution** | GraphQL's official stance; `@deprecated` + additive-only | Lowest friction, highest discipline: the removal choreography below is the whole mechanism |

Note the style-guide schism: Google mandates URI majors; Zalando *forbids* URL versioning and mandates media-type versioning while advising you avoid versioning at all. The honest synthesis: **strategy matters less than the additive-by-default discipline all four share**; pick one selection mechanism, make the breaking path expensive on purpose.

## Deprecation is a protocol now

- **RFC 9745 `Deprecation`** (Standards Track, 2025): a structured-field date saying "still works — stop depending on it", past or future.
- **RFC 8594 `Sunset`**: an HTTP-date saying "will stop responding"; must not precede the deprecation date.
- Adoption is real but ragged: Zalando's guidelines prescribe the pair plus process (client approval before shutdown, usage monitoring of deprecated elements, clients must watch for the headers and must not newly adopt deprecated APIs); GitHub emits both around version retirement — in the pre-RFC date format, a live reminder that standards outrun deployments.

**The removal choreography** (fragments verified, sequence is the synthesis): deprecate in the spec (`@deprecated`, OpenAPI annotations) → signal at runtime (Deprecation, then Sunset) → **measure** until usage is zero (Zalando makes monitoring a MUST; Apollo's field-usage insights are the GraphQL instrument — requests, executions, and client versions per field) → obtain consent where contracts require it → remove only in a new major or after sunset. Removal without the measuring step is a breaking change with extra paperwork.

## The tolerant reader (the consumer's half)

Fowler's rule, made a MUST by Zalando: consume only what you need, ignore unknown fields, **preserve them on round-trip writes** (the read-modify-PUT that drops fields it never understood is the classic silent data loss), tolerate unknown enum values, and localize parsing so tolerance lives in one place. Providers can only be as additive as their least tolerant consumer allows; this rule is what makes "add a field" actually non-breaking.

## Gates: contracts and diffs in CI

- **Consumer-driven contracts (Pact)**: consumer tests generate a pact of exactly what that consumer uses; provider verification replays it; the broker's matrix plus `can-i-deploy` gates releases on verified compatibility with what is *deployed*. The killer property: removing a field nobody consumes verifies green — the contract encodes usage, which schema rules cannot see. Bi-directional contract testing (provider's OpenAPI vs consumer contract, statically compared) is the lighter retrofit variant.
- **Schema diffs**: `buf breaking` for protobuf (categories FILE / PACKAGE / WIRE_JSON / WIRE — operationalizing the source-vs-wire split; WIRE_JSON is the floor when JSON transcoding exists); `oasdiff breaking` for OpenAPI; GraphQL Inspector (breaking / dangerous / non-breaking, with `considerUsage` downgrading breaks no live client touches — the tool where diff gates meet usage data).
- **The spec is the artifact** (design-first): author and lint the OpenAPI/AsyncAPI/proto before implementing, publish it, attach deprecation annotations to it — the diff gates above need a reviewed contract to diff. OpenAPI 3.1 aligning its schemas with JSON Schema 2020-12 is what lets contract tools and validators share one semantics; AsyncAPI 3.x is the same contract for the [event bus](PubSubQueues.md), where the compatibility mode itself is registry-enforced.
- Persisted-query safelists ([gateway](ApiGateway.md)) close the GraphQL loop: a safelist is a complete enumeration of production operations, so "is this diff breaking?" becomes decidable.

## Failure modes

- **The wire-compatible source break**: a type change that parses fine and truncates values, or recompiles into a different generated API — why AIP-180 binds on source, and why buf's FILE vs WIRE categories both exist.
- **The behavioral break**: nothing in the schema changed; the server just started requiring what was optional. Only contract tests and semantic review catch it.
- **Default-version drift**: unversioned callers silently rolled to a newer version at sunset — the cost GitHub documents for defaulting; pin explicitly in every client.
- **Rename-as-improvement**: a "cleaner" field or method name is a removal wearing a refactor's clothes; keep both or don't.
- **Deprecated forever**: headers emitted, nothing measured, nothing removed — the parallel-version tax compounds until a "cleanup" breaks someone. Measurement (usage → zero) is what makes deprecation terminate.
- **Round-trip field loss**: intolerant readers dropping unknown fields on PUT — consumer-side, and the provider's additive guarantee dies with it.
- **Webhook version skew**: event payloads pinned to an old version while the API moved (Stripe pins per endpoint for exactly this reason); [webhook](Webhooks.md) consumers should fetch current state rather than trust payload shape.

## Trade-offs

| Buy | Pay |
|---|---|
| Consumers upgrade on their schedule | Every supported version is code you run and test forever |
| Additive-only keeps one codebase | Requires tolerant readers you don't control — and gates to prove it |
| Deprecation headers + usage data make removal safe | A bookkeeping process with owners, not a header you set once |
| Contract tests catch what schema diffs cannot | Contracts only cover consumers who write them |

The contract is the *what*; the [gateway](ApiGateway.md) often carries the *where* (version routing, header defaults); the [encoding notes](../data-intensive-design/encoding-overview.md) carry the *how* of the bytes underneath.

## Sources

Verified 2026-09-13; full URLs and exclusions in the [external research note](../../docs/research/sysdesign/api-versioning-external-research.md). Key primaries: Google AIP-180/181/185; the protobuf proto3 update rules; Microsoft's gRPC versioning guide; GitHub's calendar-versioning docs and the 2026-03-10 changelog; Stripe versioning/upgrade/changelog docs and the 2024 release-process post; graphql.org's schema-change-management page and the @deprecated spec; RFC 8594 and RFC 9745; the Zalando RESTful API guidelines (rules 100–116, 185–193); Fowler's TolerantReader; Pact and PactFlow docs; buf, oasdiff, and GraphQL Inspector; OpenAPI 3.1 and AsyncAPI 3.x release notes; Apollo field-usage insights.
