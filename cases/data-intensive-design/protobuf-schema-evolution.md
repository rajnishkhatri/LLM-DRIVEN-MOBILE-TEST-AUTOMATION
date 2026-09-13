---
type: analysis
title: 'Protocol Buffers and schema evolution'
description: 'Field tags, not names, identify fields. Add only new tags; never reuse a retired tag. Unknown fields can be skipped and preserved. Thrift is the same idea.'
tags: [data-intensive-design, encoding, protobuf, thrift, schema-evolution]
---

# Protocol Buffers and schema evolution

**See also:** [chapter overview](encoding-overview.md) · [textual encodings](textual-and-language-encodings.md) · [Avro](avro-schema-evolution.md) · [REST and RPC](rest-rpc-dataflow.md) · [references](encoding-references.md)

Protocol Buffers (protobuf) is a schema-driven binary encoding from
Google. Apache Thrift, originally from Facebook
([14](encoding-references.md)), is the same idea; most of this note
applies to both.

The schema is an IDL. For the running record
([Example 5-2](textual-and-language-encodings.md#binary-encodings-of-json-and-xml)):

```protobuf
syntax = "proto3";

message Person {
    string user_name = 1;
    int64 favorite_number = 2;
    repeated string interests = 3;
}
```

A code generator produces classes in various languages. The schema
language is simple compared to JSON Schema: fields and types, no
value-range or regex constraints.

The same record encodes in **33 bytes** ([15](encoding-references.md)).
Each field carries a type annotation and, where needed, a length. String
*values* are still UTF-8. Field *names* are absent. The encoded data
holds **field tags** — the numbers `1`, `2`, `3` in the schema. Tags
are compact aliases.

Protobuf packs type and tag into a single byte and uses variable-length
integers: 1337 takes two bytes, with the top bit of each byte meaning
“more bytes follow.” Numbers from –64 to 63 take one byte; bigger
numbers take more.

There is no explicit list type. `repeated` means “this tag may appear
more than once in the record.” List elements are repeated occurrences
of the same tag.

## Field tags and schema evolution

An encoded record is the concatenation of its encoded fields. Unset
fields are omitted. **You can rename a field; you cannot change its
tag.** Changing a tag makes existing bytes meaningless.

**Adding a field.** Give it a new tag. Old code that does not know the
tag skips it. The type annotation tells the parser how many bytes to
skip, and unknown fields can be preserved — that is how you avoid the
round-trip data loss in
[Figure 5-1](encoding-overview.md#backward-and-forward-compatibility).
Old code reading new data is **forward compatible**.

**Backward compatibility.** Tags keep their meaning, so new code always
reads old data. A field present in the new schema but missing from old
bytes is filled with a default (empty string, 0, …).

**Removing a field** is adding with the compatibility directions
reversed. Never reuse a tag: old data may still contain it, and new
code must ignore it. Reserve retired tags in the schema so they are
not forgotten.

**Changing a datatype** is possible for some types (see the docs) and
risks truncation. Widening a 32-bit integer to 64-bit is backward
compatible (new code zero-fills missing bits). The reverse is not: old
code still holds a 32-bit variable and truncates values that do not
fit.

**Architect takeaway:** the tag number *is* the field identity. Treat
tag assignment as an append-only log. Rename freely; never renumber;
reserve what you delete.
