---
type: analysis
title: 'Language-specific and textual encodings'
description: 'Language pickles lock you in and are a deserialization RCE risk. JSON/XML/CSV interoperate but are vague on numbers and binary. Binary JSON still ships field names.'
tags: [data-intensive-design, encoding, json, json-schema, messagepack]
---

# Language-specific and textual encodings

**See also:** [chapter overview](encoding-overview.md) · [document-model schema flexibility](relational-vs-document.md#schema-flexibility-in-the-document-model) · [Protocol Buffers](protobuf-schema-evolution.md) · [Avro](avro-schema-evolution.md) · [references](encoding-references.md)

## Language-specific formats

Many languages ship a built-in encoder: Java `java.io.Serializable`,
Python `pickle`, Ruby `Marshal`, plus third-party libraries such as Kryo
for Java. They restore in-memory objects with little extra code. They
also have deep problems:

- **Language lock-in.** Reading the bytes in another language is hard.
  You commit to the current language and close off integration with
  organizations that use something else.
- **Security.** Restoring the same object types means instantiating
  arbitrary classes. If an attacker can feed you a byte sequence, that
  often becomes remote code execution
  ([1](encoding-references.md), [2](encoding-references.md),
  [3](encoding-references.md)).
- **Versioning as an afterthought.** Forward and backward compatibility
  were not the design goal ([4](encoding-references.md)).
- **Efficiency as an afterthought.** Java’s built-in serialization is
  notorious for CPU cost and bloat ([5](encoding-references.md)).

Use a language’s built-in encoding only for very transient purposes.

## JSON, XML, and CSV

For language-independent interchange, JSON and XML are the default. CSV
is common for tabular data without nesting. They are textual and somewhat
human-readable. Beyond syntax debates:

- XML is often called too verbose and complicated
  ([6](encoding-references.md)).
- **Numbers are ambiguous.** XML and CSV cannot tell a number from a
  digit-string without an external schema. JSON distinguishes strings
  from numbers but not integers from floats, and it does not specify
  precision. Integers greater than 2⁵³ cannot be represented exactly in
  IEEE 754 double; languages that parse JSON numbers as floats (notably
  JavaScript) lose accuracy ([7](encoding-references.md)). X works around
  this by returning post IDs twice — once as a JSON number and once as a
  decimal string ([8](encoding-references.md)).
- **No binary strings.** Unicode text is fine; raw bytes are not. The
  usual hack is Base64, which grows the payload by about a third and
  needs the schema to say “this string is actually bytes.”
- XML Schema and JSON Schema are powerful and hard to implement. Without
  them, applications hardcode encoding logic.
- CSV has no schema. Adding a column is a manual contract change. Escaping
  is specified in RFC 4180 ([9](encoding-references.md)); not every parser
  implements it.

Despite the flaws, these formats remain the default for **data interchange
between organizations**. Agreement on *any* format outweighs prettiness
or efficiency.

## JSON Schema

JSON Schema is widely used wherever JSON is exchanged or stored: OpenAPI
(see [web services](rest-rpc-dataflow.md#web-services)), Confluent Schema
Registry, Red Hat Apicurio, PostgreSQL `pg_jsonschema`, MongoDB
`$jsonSchema`.

Primitive types: `string`, `number`, `integer`, `object`, `array`,
`boolean`, `null`. A separate validation layer overlays constraints
(a `port` field between 1 and 65,535).

**Open versus closed content models.** Open (`additionalProperties: true`,
the default) allows any field not named in the schema. Closed allows only
the named fields. An open JSON Schema is usually a definition of what is
*not* permitted (invalid values on defined fields), not of what is.

JSON objects always use string keys. A map from integer IDs to strings
is expressed with `patternProperties` and a closed model:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "patternProperties": {
    "^[0-9]+$": {
      "type": "string"
    }
  },
  "additionalProperties": false
}
```

JSON Schema also supports conditional `if`/`else`, named types, and
remote schema references. Power makes evolution hard: remote resolution,
conditional rules, and forward/backward compatibility are all
non-trivial ([10](encoding-references.md), [11](encoding-references.md)).
XML Schema has the same class of problems ([12](encoding-references.md)).

## Binary encodings of JSON and XML

JSON is less verbose than XML; both still waste space versus a true
binary format. That observation produced MessagePack, CBOR, BSON,
BJSON, UBJSON, BISON, Hessian, Smile (JSON family) and WBXML, Fast
Infoset (XML family). They are more compact and sometimes faster to
parse; none displaced textual JSON/XML ([13](encoding-references.md)).

Most keep the JSON/XML data model. Without a prescribed schema they
must **include field names in the encoded data**. For this record:

```json
{
    "userName": "Martin",
    "favoriteNumber": 1337,
    "interests": ["daydreaming", "hacking"]
}
```

MessagePack spends a type/length nibble per value, then the ASCII field
name, then the value. The first byte `0x83` is “object with three
fields”; `0xa8` is “string of eight bytes” (`userName`); and so on.
The result is 66 bytes versus 81 for whitespace-stripped JSON. All
schema-less binary JSON encodings look like this. It is not obvious
that the small saving is worth losing human-readability.

[Protocol Buffers](protobuf-schema-evolution.md) and
[Avro](avro-schema-evolution.md) encode the same record in about half
as many bytes by dropping the field names.

**Architect takeaway:** do not persist pickles. Use JSON when the
consumers are humans or other organizations. Reach for a schema-driven
binary format when you control both ends and care about compatibility
rules or size.
