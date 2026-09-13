---
type: overview
title: 'Encoding and evolution'
description: 'Rolling upgrades need old and new code plus old and new data to coexist. Backward and forward compatibility are properties of the encoding, not of the brand.'
tags: [data-intensive-design, encoding, evolvability, overview]
---

# Encoding and evolution

> Everything changes and nothing stands still.
>
> — Heraclitus of Ephesus, as quoted by Plato in *Cratylus* (360 BCE)

Applications change. Features are added, products launch, requirements
become clearer. [Evolvability](maintainability.md#evolvability-making-change-easy)
is the aim: make change easy at the *system* level, not just inside one
codebase.

A feature change usually changes stored data — a new field, a new record
type, a new presentation of old data. [Relational schemas](relational-vs-document.md)
assume one schema in force at a time (`ALTER` migrates everyone together).
[Schema-on-read](relational-vs-document.md#schema-flexibility-in-the-document-model)
stores a mixture of older and newer formats written at different times.

Code cannot change instantaneously either. Server-side **rolling upgrades**
(staged rollouts) deploy a few nodes at a time; client-side apps wait on
the user. Old and new code, and old and new data formats, coexist. The
system stays up only if the encoding is compatible **in both directions**.

Prior chapter: [storage and retrieval](storage-overview.md).

## Backward and forward compatibility

| Direction | Meaning |
|---|---|
| **Backward compatibility** | Newer code can read data written by older code |
| **Forward compatibility** | Older code can read data written by newer code |

For APIs the pair flips by role. An older client calling a newer service
needs backward compatibility on the *request* and forward compatibility on
the *response*. A newer client calling an older service needs the reverse.

Backward compatibility is usually the easier of the two: the author of the
newer code knows the old format and can handle it explicitly. Forward
compatibility asks older code to ignore additions it does not understand.

The hard case is Figure 5-1: new code writes a record with a new field
(say `photoURL`); old code reads it, updates something else, and writes
the record back. If the decode step drops unknown fields, the new field
is **silently lost**. Preserve unknown fields, or do not round-trip through
a model that cannot hold them.

## Encoding versus decoding

Programs keep data in two representations:

- **In memory:** objects, structs, lists, hash tables, trees — CPU-friendly,
  often using pointers.
- **On the wire or on disk:** a self-contained sequence of bytes. A pointer
  is meaningless to another process.

**Encoding** (serialization, marshaling) is the translation from memory
to bytes. **Decoding** (parsing, deserialization, unmarshaling) is the
reverse. This bundle uses *encoding* because *serialization* also means
something else in transactions.

Encoding is not always required. A warehouse may operate directly on
compressed on-disk data
([query compilation and vectorization](query-execution-cubes.md)).
Zero-copy formats such as Cap’n Proto and FlatBuffers are designed to
be used both at runtime and on disk or the network without a conversion
step. Most systems still convert.

## Topic map

| Topic | The question | Concept |
|---|---|---|
| Language-specific and textual | Pickle, JSON, XML, CSV, JSON Schema, MessagePack? | [Language-specific and textual encodings](textual-and-language-encodings.md) |
| Protocol Buffers | Field tags, skip unknown fields, reserve retired tags? | [Protocol Buffers and schema evolution](protobuf-schema-evolution.md) |
| Avro | Writer’s schema plus reader’s schema, no tag numbers? | [Avro and schema evolution](avro-schema-evolution.md) |
| Databases | Data outlives code; mix of schema versions on disk? | [Dataflow through databases](dataflow-databases.md) |
| REST and RPC | Location transparency is a lie; version the API? | [REST, RPC, and service dataflow](rest-rpc-dataflow.md) |
| Workflows | Exactly-once across services without a shared DB txn? | [Durable execution and workflows](durable-workflows.md) |
| Events and actors | Broker or actor mailbox; preserve unknown fields? | [Event-driven dataflow](event-driven-dataflow.md) |

Citations for this chapter live in
[encoding references](encoding-references.md). Earlier chapters keep
their own lists: [trade-off references](references.md),
[NFR references](nfr-references.md),
[data-model references](data-models-references.md),
[storage references](storage-references.md).

## The merits of schemas

[Protocol Buffers](protobuf-schema-evolution.md) and
[Avro](avro-schema-evolution.md) describe a binary encoding with a
schema language much simpler than XML Schema or JSON Schema — fields
and types, not regex-on-string or 0–100 range checks. That simplicity
is why they have wide language support.

The idea is old. ASN.1 (1984) defined network protocols; its DER encoding
still sits inside X.509 certificates
([24](encoding-references.md), [25](encoding-references.md),
[26](encoding-references.md)). ASN.1 evolves schemas with tag numbers,
like protobuf ([27](encoding-references.md)), but is complex and poorly
documented — not a good choice for new applications.

Relational databases also ship a proprietary binary protocol; the vendor
driver (ODBC/JDBC) decodes responses into in-memory structures.

Schema-driven binary encodings, versus “binary JSON”:

- More compact — field names are omitted from the bytes.
- The schema is documentation that cannot drift: you need it to decode.
- A schema registry lets you check forward and backward compatibility
  *before* deploy.
- Code generation gives compile-time type checking in statically typed
  languages.

Schema evolution gives the same *kind* of flexibility as
[schema-on-read](relational-vs-document.md#schema-flexibility-in-the-document-model)
with better guarantees and tooling. Keep the number of concurrent schema
formats small; operations stay simpler.

## Summary

Rolling upgrades (and clients that refuse to update) mean different nodes
run different code. Every byte that leaves a process — to disk, to a
service, to a queue — must be **backward compatible** (new code reads old
data) and **forward compatible** (old code reads new data).

Three families of encoding:

- **Language-specific** (Java `Serializable`, pickle, Marshal): convenient,
  language-locked, often insecure, weak on versioning. Transient use only.
- **Textual** (JSON, XML, CSV): widespread interchange. Compatibility
  depends on how you use them. Vague on numbers and binary strings.
- **Schema-driven binary** (Protocol Buffers, Avro): compact, well-defined
  compatibility rules, useful as documentation and for code generation.
  Not human-readable until decoded.

Four modes of dataflow, same compatibility problem, different who-encodes /
who-decodes:

| Mode | Who encodes | Who decodes |
|---|---|---|
| [Databases](dataflow-databases.md) | The writer | A later reader (maybe older code) |
| [REST / RPC](rest-rpc-dataflow.md) | Client encodes the request; server encodes the response | The other side |
| [Workflows](durable-workflows.md) | Each task’s RPC and state change, logged for replay | The engine on retry |
| [Events / actors](event-driven-dataflow.md) | The sender | The recipient, via a broker or mailbox |

**Architect takeaway:** compatibility is a property of the *encoding
contract* between two processes, not of the framework logo. Pick a format
whose evolution rules you can state; preserve unknown fields on
round-trip; prefer rolling upgrades over lockstep deploys.

Next chapter: [replication](replication-overview.md) — single-leader,
multi-leader, and leaderless copies, and what lag and conflicts
actually guarantee.
