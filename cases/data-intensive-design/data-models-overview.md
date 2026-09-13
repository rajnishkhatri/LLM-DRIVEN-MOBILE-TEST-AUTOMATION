---
type: overview
title: 'Data models and query languages'
description: 'Data models shape how we think about the problem. Match the model to the relationship shape — tree, graph, event log, or matrix — then pick a query language that fits.'
tags: [data-intensive-design, data-models, overview]
---

# Data models and query languages

> The limits of my language mean the limits of my world.
>
> — Ludwig Wittgenstein, *Tractatus Logico-Philosophicus* (1922)

Data models are perhaps the most important part of developing software,
because of the profound effect they have not only on how the software is
written, but also on how we think about the problem that we are solving.

Most applications are built by layering one data model on top of another.
For each layer, the key question is how it is represented in terms of the
next-lower layer. From highest to lowest:

1. **Application objects and APIs.** You look at the real world (people,
   organizations, goods, actions, money flows, sensors) and model it in
   objects or data structures and APIs that manipulate them.
2. **General-purpose data model.** When you store those structures, you
   express them as JSON or XML documents, tables in a relational database,
   or vertices and edges in a graph. Those models are this chapter.
3. **Bytes in memory, on disk, or on the network.** The engineers who built
   the database decided how to represent the document, relational, or graph
   data. Storage-engine designs are a later chapter.
4. **Hardware.** Bytes as electrical currents, pulses of light, magnetic
   fields.

In a complex application there may be more intermediary levels (APIs built
upon APIs), but the idea is the same: each layer hides the complexity of
the layers below it by providing a clean data model. These abstractions
allow different groups — for example, the engineers at the database vendor
and the application developers using their database — to work together
effectively.

Several data models are widely used, often for different purposes. Some
types of data and some queries are easy to express in one model and awkward
in another. This chapter compares the relational model, the document model,
graph-based data models, event sourcing, and DataFrames, and briefly looks
at query languages for each.

Prior chapter: [defining nonfunctional requirements](nfr-overview.md).

## Topic map

| Model | The question | Concept |
|---|---|---|
| Relational vs document | Is the data a tree of one-to-many, or does it need joins? | [Relational versus document models](relational-vs-document.md) |
| Analytics schemas | How do warehouses lay out facts and dimensions? | [Stars, snowflakes, and one big table](star-snowflake-analytics.md) |
| Graphs | Are many-to-many connections the common case? | [Graph-like data models](graph-data-models.md) |
| Triples and Datalog | Same graph, different words — RDF, SPARQL, Datalog | [Triple stores, SPARQL, and Datalog](triple-stores-sparql-datalog.md) |
| GraphQL | Client query contract, not a graph database | [GraphQL](graphql.md) |
| Events | Write as an append-only log, read from derived views | [Event sourcing and CQRS](event-sourcing-cqrs.md) |
| DataFrames | Relational-like wrangling into matrices for ML | [DataFrames, matrices, and arrays](dataframes.md) |

Citations for this chapter live in
[data-model references](data-models-references.md). Earlier chapters keep
their own lists: [trade-off references](references.md),
[NFR references](nfr-references.md).

## Summary

The relational model, despite being more than half a century old, remains
important — especially in data warehousing and business analytics, where
star or snowflake schemas and SQL are ubiquitous. Alternatives have become
popular in other domains:

- The **document model** targets self-contained JSON documents where
  relationships between one document and another are rare.
- **Graph data models** go the opposite way: anything is potentially
  related to everything, and queries may traverse multiple hops (Cypher,
  SPARQL, or Datalog).
- **DataFrames** generalize relational data to large numbers of columns,
  bridging databases and the multidimensional arrays that underpin much
  machine learning and scientific computing.

One model can often be emulated in another — graph data in a relational
database, for example — but the result can be awkward, as with recursive
queries in SQL. Specialist databases exist for each model. There is also a
trend for databases to expand into neighboring niches: relational databases
added JSON columns, document databases added joins, and graph support
within SQL is gradually improving.

**Event sourcing** represents data as an append-only log of immutable
events and can be advantageous in complex business domains. An append-only
log is good for writing; to support efficient queries, the log is
translated into read-optimized materialized views through CQRS.

Nonrelational models typically do not enforce a schema, which can make it
easier to adapt to changing requirements. The application still assumes a
structure; it is just a question of whether the schema is **explicit**
(enforced on write) or **implicit** (assumed on read).

Some models remain outside this map: genome sequence similarity (GenBank),
double-entry ledgers (TigerBeetle, blockchains), and full-text / vector
search.

**Architect takeaway:** pick the model that matches the relationship shape
you actually have. Query language follows the model; forcing a graph query
through recursive SQL, or a document tree through shredded tables, is the
cost of picking the wrong abstraction.

Next chapter: [storage and retrieval](storage-overview.md) — LSM vs
B-tree, columnar analytics, and multi-condition indexes.
