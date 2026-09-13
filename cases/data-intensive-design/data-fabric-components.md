---
type: analysis
title: 'Data fabric extras'
description: 'Eight add-ons on the MDW path. Virtualization is optional. The catalog is named but the dump has no section. Requests go through APIs, drivers, or a virtual layer — not connection strings.'
tags: [data-intensive-design, data-fabric, mdm, data-virtualization, apis, governance]
---
# Data fabric extras

**See also:** [chapter overview](data-fabric-overview.md) · [trade-offs](data-fabric-tradeoffs.md) · [MDW journey](mdw-data-journey.md) · [REST and RPC](rest-rpc-dataflow.md) · [event-driven dataflow](event-driven-dataflow.md) · [law and society](law-and-society.md)

These eight sit on the
[MDW path](mdw-data-journey.md), they do not replace it. The
source’s fabric test is “at least three.” Virtualization is the
one some vendors treat as mandatory; here it is optional.
[Figure 11-1](data-fabric-overview.md) draws five of the eight
(policies, catalog, MDM, real-time ingest, APIs). The other
three stay in the prose.

## Data access policies

Policies are the governance surface: who may access what, how it
may be used, and when access is granted or denied. Typical
contents are classification, authentication and authorization,
encryption, retention, backup and recovery, and disposal. The
named legal hooks are
[GDPR](law-and-society.md) and HIPAA.

Every request is supposed to go through a mechanism that can
enforce those rules — APIs, drivers, or
[virtualization](#data-virtualization) — not a connection string
to the lake or the RDW. The healthcare sketch: only authorized
medical staff see a record; the API checks credentials against
the policy before it returns anything.

On Figure 11-1 the policies are the orange **locks** on Raw,
Cleaned, and Presentation. Without them, “the fabric weaves
data to everyone who needs it” is an open share.

## Metadata catalog

Named as one of the eight and as a common MDW-upgrade add-on
(with real-time and policies). The dump has **no standalone
section**. Do not invent capabilities. From the surrounding
prose the catalog is the discoverability half of the fabric
claim — find the data, then apply a policy to it.

On Figure 11-1 it is the red **Meta** box. Step **(2) Store**
is drawn as arrows from Meta into the lake, the RDW, and
analytics — metadata as a cross-cutting store, not a folder
inside one zone.

A warehouse already wants a metadata layer for
[self-service BI](mdw-tradeoffs.md). The fabric claim is that
the catalog covers the lake, the RDW, and anything still sitting
in a source — not only the star schema.

## Master data management

**MDM** collects, consolidates, and maintains consistent data
from several sources so the company has one authoritative record
for its key **nontransactional** entities: customers, products,
suppliers, employees. The point is to stop duplicate, conflicting,
and wrong reference rows from driving decisions.

Source Chapter 6 introduced MDM; that chapter is not filed here.
Treat this as the reminder, not the full design.

On Figure 11-1 MDM is a folder in the **Cleaned** zone.
Enriched flows into it, then into **Curated**. It is not a
fourth store beside the lake and the RDW.

MDM is not a transactional store and not a substitute for the
[systems-of-record vs derived](operational-vs-analytical.md#systems-of-record-and-derived-data)
split. It is a curated reference the fabric can point at.

## Data virtualization

A logical layer that lets applications and people query several
sources as if they were one store. No required copy; the
virtualization product is the intermediary. Combine sources in
real time without physically integrating them.

It does **not** mean every source is connected. The usual
deployment is a few cases; most data is still centralized in the
lake or RDW. That is why the source refuses the industry line
that “no virtualization, no fabric.” Optional extra, not the
definition.

Gartner’s fabric leans on this extra to avoid copies. The
[MDW](mdw-overview.md) *requires* a copy into the RDW. A fabric
can keep that copy *and* virtualize the leftovers. Those are
different bets; do not sell them as the same slide.

## Real-time processing

Process the data and produce a result as soon as it arrives,
with no noticeable delay — traffic while driving is the source’s
example. Source Chapter 9 is not filed here; the mechanics in
this bundle are
[event-driven dataflow](event-driven-dataflow.md) and stream
ingest on the [MDW journey](mdw-data-journey.md#1-ingestion).

On Figure 11-1 this is a fourth source column — **Streaming**
(IoT devices and big-data streams) — with its own **Ingest
(real-time)** arrow into the lake, next to **(1) Ingest
(batch)**. Figure 10-2 had three source shapes and one ingest
arrow.

“We have a lake” is not real-time. Real-time is a path you keep
warm. Stock trading and ecommerce are the industries the
[trade-offs](data-fabric-tradeoffs.md) name as needing it.

## APIs

An API publishes data from the lake, the RDW, or a source
without handing out a connection string or a location. If the
data moves, you change the API’s internals; callers stay put.
That is the same compatibility bet as
[REST / RPC](rest-rpc-dataflow.md): the contract outlives the
store.

On Figure 11-1 the API is a gear on the RDW → analytics
path, beside **(5) Visualize**. The prose also allows an API
in front of the lake; the plate only draws the warehouse one.

APIs are also where
[access policies](#data-access-policies) become code: authn,
and fine-grained filters for which user sees which rows.

## Services

The fabric can be built as reusable **blocks**. Ingest and clean
are the examples: another team may not want the whole fabric
but does want the generic pipeline. Encapsulate that code as a
service anyone in the company can call.

This is composition, not a product SKU. The failure mode is a
private script that only the fabric team can run.

## Products

The whole fabric can be packaged and sold — especially if it is
built for one industry (healthcare is the source’s example). One
sentence in the dump. No vendor list, no packaging advice.

**Architect takeaway:** pick three extras and put a mechanism
behind each. Policies without an API (or a virtual layer) are a
document. A catalog that only sees the RDW is an MDW catalog
with a new name. Virtualization that tries to replace the RDW
copy has left the MDW and should say so.
