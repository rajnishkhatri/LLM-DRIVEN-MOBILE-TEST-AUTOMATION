---
type: analysis
title: 'Avro and schema evolution'
description: 'No tag numbers. Decode with the writer’s schema and the reader’s schema; match fields by name. Defaults make add/remove safe. Dynamic schemas are the design goal.'
tags: [data-intensive-design, encoding, avro, schema-evolution, schema-registry]
---

# Avro and schema evolution

**See also:** [chapter overview](encoding-overview.md) · [Protocol Buffers](protobuf-schema-evolution.md) · [textual encodings](textual-and-language-encodings.md) · [dataflow through databases](dataflow-databases.md) · [event-driven dataflow](event-driven-dataflow.md) · [references](encoding-references.md)

Apache Avro is a schema-driven binary encoding started in 2009 as a
Hadoop subproject, because Protocol Buffers did not fit Hadoop’s use
cases ([16](encoding-references.md)). Two schema languages: Avro IDL
for humans, JSON for machines. Like protobuf, fields and types only —
no JSON Schema–style validators.

Avro IDL for the running record:

```
record Person {
    string               userName;
    union { null, long } favoriteNumber = null;
    array<string>        interests;
}
```

Equivalent JSON schema:

```json
{
    "type": "record",
    "name": "Person",
    "fields": [
        {"name": "userName",       "type": "string"},
        {"name": "favoriteNumber", "type": ["null", "long"], "default": null},
        {"name": "interests",      "type": {"type": "array", "items": "string"}}
    ]
}
```

No tag numbers. The same record encodes in **32 bytes** — the most
compact of the formats in this chapter. The byte sequence is values
concatenated: a string is a length prefix plus UTF-8; an integer is
variable-length. Nothing in the bytes says which field or type this is.
Decoding walks the schema in order. **Writer and reader must agree on
the writer’s schema**, or the bytes are misparsed.

## The writer’s schema and the reader’s schema

The application encodes with whatever schema it knows — often compiled
in. That is the **writer’s schema**.

Decoding uses *two* schemas: the writer’s (identical to the one used
to encode) and the **reader’s schema** (the fields the application
expects). If they match, decoding is straightforward. If they differ,
Avro resolves by comparing them and translating writer-shaped data
into reader-shaped data ([17](encoding-references.md),
[18](encoding-references.md)).

Resolution matches fields **by name**, so field order may differ. A
field in the writer’s schema but not the reader’s is ignored. A field
the reader expects but the writer did not write is filled from the
**default declared in the reader’s schema**.

In Avro terms: **forward compatibility** means the writer may use a
newer schema than the reader; **backward compatibility** means the
writer may use an older schema than the reader.

## Schema evolution rules

You may add or remove a field only if it has a default (like
`favoriteNumber` above).

- Add a field with a default: new readers fill the default when reading
  old bytes. Backward compatible.
- Add a field *without* a default: new readers cannot read old writers.
  Breaks backward compatibility.
- Remove a field *without* a default: old readers cannot read new
  writers. Breaks forward compatibility.

Null is not an implicit default. To allow null you need a union, and
null may be the default only if it is the **first** branch:
`union { null, long, string }`. Verbosity is the point — it makes
nullability explicit ([19](encoding-references.md)).

Datatype changes are allowed when Avro can convert. Renaming a field
is backward compatible but not forward compatible: the reader’s schema
can list **aliases** for old writer names. Adding a union branch is
likewise backward compatible, not forward compatible.

## How the reader finds the writer’s schema

You cannot attach the full schema to every record — it would dwarf the
payload. The answer depends on context:

| Context | Where the writer’s schema lives |
|---|---|
| Large file, many records, one schema | Once at the front of an Avro **object container file** |
| Database, records written over years | Version number per record; schema versions in a store. Confluent Schema Registry for Kafka ([20](encoding-references.md)) and LinkedIn Espresso ([21](encoding-references.md)) work this way |
| Bidirectional network connection | Negotiate on setup; use that schema for the connection. Avro RPC does this (see [REST and RPC](rest-rpc-dataflow.md)) |

A database of schema versions is useful even without Avro: documentation
plus a place to check compatibility before deploy
([22](encoding-references.md)). Version numbers can be incrementing
integers or a hash of the schema.

## Dynamically generated schemas

No tag numbers is the feature, not a omission. Avro is friendly to
**schemas generated at export time**. Dump a relational database to a
binary file: generate an Avro schema from the SQL schema, one record
type per table, one field per column, and write an object container
file ([23](encoding-references.md)). When a column is added or dropped,
regenerate and export again. Readers match fields by name, so the new
writer’s schema still resolves against an old reader’s schema.

Protocol Buffers would need hand-assigned tags (or a generator that
never reuses a tag). That mapping was not a protobuf design goal; it
was an Avro design goal.

**Architect takeaway:** Avro trades self-describing bytes for a
two-schema contract. Use it when schemas are generated or when a
registry already sits next to the log. Use protobuf when you want
self-skipping tags and compiled stubs without a registry lookup.
