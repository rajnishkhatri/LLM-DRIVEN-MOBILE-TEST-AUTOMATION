---
type: analysis
title: 'Relational versus document models'
description: 'Trees of one-to-many fit documents; many-to-one and many-to-many need joins. Schema-on-read vs schema-on-write is a type-checking debate, not schemaless vs schema.'
tags: [data-intensive-design, data-models, relational, document, orm, normalization]
---

# Relational versus document models

**See also:** [chapter overview](data-models-overview.md) · [stars and snowflakes](star-snowflake-analytics.md) · [OLTP vs OLAP](operational-vs-analytical.md) · [home timelines](home-timeline-case-study.md) · [references](data-models-references.md)

The best-known data model today is probably that of SQL, based on the
relational model proposed by Edgar Codd in 1970 ([4](data-models-references.md)).
Data is organized into **relations** (tables in SQL), where each relation is
an unordered collection of **tuples** (rows).

The relational model was originally a theoretical proposal, and many people
doubted whether it could be implemented efficiently. By the mid-1980s,
RDBMSs and SQL had become the tools of choice for data with some kind of
regular structure. Many data-management use cases — for example, business
analytics ([stars and snowflakes](star-snowflake-analytics.md)) — are still
dominated by relational data decades later.

Over the years there have been many competing approaches. In the 1970s and
early 1980s, the **network model** and the **hierarchical model** were the
main alternatives; the relational model came to dominate them. Object
databases (not to be confused with object storage for large files) came and
went in the late 1980s and early 1990s. XML databases appeared in the early
2000s and saw only niche adoption. Each competitor generated a lot of hype;
none lasted ([5](data-models-references.md)). Instead, SQL has grown to
incorporate other types of data — XML, JSON, and graph data
([6](data-models-references.md)).

In the 2010s, **NoSQL** was the latest buzzword that tried to overthrow
relational databases. NoSQL is not a single technology but a loose set of
ideas around new data models, schema flexibility, scalability, and open
source licensing. Some databases branded themselves as **NewSQL**, aiming
to provide the scalability of NoSQL with the data model and transactional
guarantees of traditional RDBMSs. Those ideas have been influential; as the
principles became widely adopted, use of the terms faded.

One lasting effect of the NoSQL movement is the popularity of the
**document model**, usually representing data as JSON. Specialized document
databases such as MongoDB and Couchbase popularized it; most relational
databases have now added JSON support. Compared to relational tables, often
seen as having a rigid schema, JSON documents are thought to be more
flexible.

## The object-relational mismatch

Much application development today is done in object-oriented languages,
which leads to a common criticism of SQL: if data is stored in relational
tables, an awkward translation layer is required between objects in
application code and tables, rows, and columns. The disconnect is sometimes
called an **impedance mismatch** (borrowed from electronics: power transfer
is maximized when output and input impedances match).

**Object-relational mapping (ORM)** frameworks like ActiveRecord and
Hibernate reduce the boilerplate for this translation, but they are often
criticized ([7](data-models-references.md)):

- ORMs are complex and cannot completely hide the differences, so
  developers still think about both representations.
- ORMs are generally used only for OLTP app development (see
  [characterizing OLTP and analytics](operational-vs-analytical.md#characterizing-transaction-processing-and-analytics)).
  Data engineers making data available for analytics work with the
  underlying relational representation, so the schema still matters.
- Many ORMs work only with relational OLTP databases. Organizations with
  search engines, graph databases, and NoSQL systems may find ORM support
  lacking.
- Some ORMs auto-generate schemas that are awkward for users accessing the
  relational data directly, and inefficient on the database. Customizing
  schema and query generation can negate the benefit.
- ORMs make it easy to write inefficient queries. The classic example is
  the **N+1 query problem** ([8](data-models-references.md)): fetch N
  comments, then one query per comment to look up the author, instead of a
  single join. Avoiding this often means telling the ORM to fetch the
  related rows at the same time.

ORMs also have advantages: some translation is inevitable for relational
data, and ORMs reduce boilerplate for the simple cases; some help with
query-result caching; some help with schema migrations and other
administrative work.

## The document model for one-to-many relationships

Not all data lends itself well to a relational representation. A résumé
(a LinkedIn profile) is a common example.

The profile as a whole is identified by `user_id`. Fields like
`first_name` and `last_name` appear once per user, so they can be columns
on a `users` table. Most people have had more than one job, and varying
numbers of education periods and contact details. One way of representing
those **one-to-many** relationships is separate tables (`positions`,
`education`, `contact_info`), each with a foreign-key reference to
`users`.

Another way, closer to an object structure in application code, is a JSON
document:

```json
{
  "user_id":     251,
  "first_name":  "Barack",
  "last_name":   "Obama",
  "headline":    "Former President of the United States of America",
  "region_id":   "us:91",
  "photo_url":   "/p/7/000/253/05b/308dd6e.jpg",
  "positions": [
    {"job_title": "President", "organization": "United States of America"},
    {"job_title": "US Senator (D-IL)", "organization": "United States Senate"}
  ],
  "education": [
    {"school_name": "Harvard University",  "start": 1988, "end": 1991},
    {"school_name": "Columbia University", "start": 1981, "end": 1983}
  ],
  "contact_info": {
    "website": "https://barackobama.com",
    "x": "https://x.com/barackobama"
  }
}
```

Some developers feel that JSON reduces the impedance mismatch. The lack of
a schema is often cited as an advantage too (see
[schema flexibility](#schema-flexibility-in-the-document-model)). There
are also problems with JSON as an encoding format (see
[language-specific and textual encodings](textual-and-language-encodings.md)).

The JSON representation has better **locality** than the multi-table
schema (see [data locality](#data-locality-for-reads-and-writes)). To
fetch a profile in the relational example you need multiple queries or a
messy multiway join ([9](data-models-references.md),
[10](data-models-references.md)). In JSON, all the relevant information is
in one place.

The one-to-many relationships imply a **tree** structure, and JSON makes
that tree explicit.

A one-to-many relationship is sometimes called **one-to-few**, since a
résumé typically has a small number of positions
([11](data-models-references.md), [12](data-models-references.md)). If you
have a genuinely large number of related items — comments on a celebrity
post, of which there could be many thousands — embedding them all in the
same document may be too unwieldy, so the relational approach is
preferable.

## Normalization, denormalization, and joins

In the résumé JSON, `region_id` is an ID, not the plain-text string
“Washington, DC, United States.” Why?

If the UI has a free-text field, storing a string makes sense. Standardized
lists (drop-down or autocompleter) have advantages: consistent spelling;
avoiding ambiguity (Washington, DC vs the state); ease of updating the
name in one place; localization; better search (a search for the US East
Coast can match because the region list encodes that Washington is on the
East Coast).

Whether you store an ID or a text string is a question of
**normalization**. With an ID, the human-meaningful information is stored
in only one place and everything that refers to it uses an ID. Storing the
text directly **denormalizes**: you duplicate the human-meaningful
information in every record.

The advantage of an ID is that it has no meaning to humans, so it never
needs to change even if the information it identifies changes. Anything
meaningful to humans may need to change — and if it is duplicated, all
redundant copies need updating. That is more code, more writes, more disk,
and a risk of inconsistency.

The downside of a normalized representation is that every time you display
a record containing an ID, you do an additional lookup. In a relational
model this is a **join**:

```sql
SELECT users.*, regions.region_name
FROM users
JOIN regions ON users.region_id = regions.id
WHERE users.id = 251;
```

Document databases can store both normalized and denormalized data, but
they are often associated with denormalization — partly because JSON makes
it easy to store extra fields, and partly because weak join support makes
normalization inconvenient. Some document databases don’t support joins at
all, so you perform them in application code. In MongoDB you can join with
`$lookup` in an aggregation pipeline:

```javascript
db.users.aggregate([
  { $match: { _id: 251 } },
  { $lookup: {
      from: "regions",
      localField: "region_id",
      foreignField: "_id",
      as: "region"
  } }
])
```

### Trade-offs of normalization

In the résumé example, `region_id` is a reference, but organization and
school names are just strings. Many people may have worked at the same
company, but there is no ID linking them.

Should organization and school be entities referenced by ID? The same
arguments for region IDs apply. If you want to include a company logo:

- **Denormalized:** put the image URL on every profile. The document is
  self-contained, but changing the logo means finding every old URL
  ([11](data-models-references.md)).
- **Normalized:** an organization entity holds name, logo URL, and other
  attributes once. Every résumé references its ID.

As a general principle: **normalized data is usually faster to write**
(one copy) **but slower to query** (joins); **denormalized data is usually
faster to read** (fewer joins) **but more expensive to write** (more
copies, more disk). Denormalization is a form of
[derived data](operational-vs-analytical.md#systems-of-record-and-derived-data):
you need a process for updating the redundant copies.

Besides update cost, consider consistency if a process crashes halfway.
Databases that offer atomic transactions make it easier to remain
consistent, but not all databases offer atomicity across multiple
documents. Stream processing is another way to keep copies consistent.

Normalization tends to be better for **OLTP**, where both reads and
updates need to be fast. Analytical systems often fare better with
denormalized data: they update in bulk and read-only query performance is
the dominant concern. At small to moderate scale, a normalized model is
often best. At very large scale, the cost of joins can become problematic.

### Denormalization in the social-network case study

In the [home-timeline case study](home-timeline-case-study.md) we compared
a normalized representation and a denormalized one (precomputed,
materialized timelines). The join between posts and follows was too
expensive; the materialized timeline is a cache of that join. Fan-out that
inserts a new post into followers’ timelines keeps the denormalized
representation consistent.

The implementation of materialized timelines at X (formerly Twitter) does
**not** store the actual text of each post. Each entry stores only the
post ID, the sender ID, and a little extra to identify reposts and replies
([13](data-models-references.md)). Approximately:

```sql
SELECT posts.id, posts.sender_id FROM posts
  JOIN follows ON posts.sender_id = follows.followee_id
  WHERE follows.follower_id = current_user
  ORDER BY posts.timestamp DESC
  LIMIT 1000
```

Whenever the timeline is read, the service still performs two joins: look
up the post ID for content and stats (likes, replies), and look up the
sender’s profile (username, picture). Looking up human-readable
information by ID is called **hydrating** the IDs — a join in application
code ([13](data-models-references.md)).

The reason for storing only IDs is that the referred data is
fast-changing. Like counts may change multiple times per second on a
popular post; users change username or photo. The timeline should show the
latest values when viewed, so denormalizing them into the materialized
timeline would not make sense, and the storage cost would jump.

Having to perform joins when reading is not, as sometimes claimed, an
impediment to high-performance scalable services. Hydrating post and user
IDs parallelizes well, and the cost does not depend on follow-graph size.

The most scalable approach may denormalize some things and leave others
normalized. Consider how often the information changes and the cost of
reads and writes (often dominated by outliers). Normalization and
denormalization are not inherently good or bad — they are read/write and
implementation-effort trade-offs.

## Many-to-one and many-to-many relationships

`positions` and `education` are one-to-many (or one-to-few): one résumé
has several positions, each belonging to only one résumé. `region_id` is
**many-to-one**: many people live in the same region, each person in one
region at a time.

If organizations and schools become entities referenced by ID, you also
have **many-to-many** relationships (one person, several organizations; one
organization, several employees). In a relational model this is usually an
**associative table** (join table): each position associates one user ID
with one organization ID.

Many-to-one and many-to-many do not easily fit in one self-contained JSON
document; they lend themselves more to a normalized representation. In a
document model you can group related fields into one document, but links
to organizations and schools are best as references to other documents:

```json
{
  "user_id":    251,
  "first_name": "Barack",
  "last_name":  "Obama",
  "positions": [
    {"start": 2009, "end": 2017, "job_title": "President",         "org_id": 513},
    {"start": 2005, "end": 2008, "job_title": "US Senator (D-IL)", "org_id": 514}
  ]
}
```

Many-to-many relationships often need to be queried in **both
directions** — all organizations a person has worked for, and all people
who have worked at an organization. Storing ID references on both sides is
denormalized: the relationship lives in two places and can become
inconsistent.

A normalized representation stores the relationship in only one place and
relies on **secondary indexes** to query it in both directions. In the
relational join table you index both `user_id` and `org_id`. In the
document model the database needs to index `org_id` inside the `positions`
array; many document databases and relational databases with JSON support
can do that.

Warehouse layouts for these relationship types are covered separately:
[stars, snowflakes, and one big table](star-snowflake-analytics.md).

## When to use which model

The main arguments for the document model are schema flexibility, better
performance due to locality, and closeness to the application object model.
The relational model counters with better support for joins and many-to-one
/ many-to-many relationships.

If the data has a document-like structure (a tree of one-to-many
relationships, typically loaded at once), use a document model. The
relational technique of **shredding** — splitting a document-like
structure into multiple tables — can lead to cumbersome schemas and
unnecessarily complicated application code.

The document model has limitations. You cannot refer directly to a nested
item within a document; you have to say something like “the second item in
the list of positions for user 251.” If you need to reference nested
items, a relational approach works better: any item has its own ID.

Some applications let the user choose the order of items (a to-do list or
issue tracker with drag-and-drop). The document model supports this well:
items (or their IDs) live in a JSON array. Relational databases have no
standard way to represent reorderable lists; tricks include sorting by an
integer column (renumber on insert-in-the-middle), a linked list of IDs,
or fractional indexing ([16](data-models-references.md),
[17](data-models-references.md), [18](data-models-references.md)).

### Schema flexibility in the document model

Most document databases, and JSON support in relational databases, do not
enforce a schema on documents. XML support in relational databases usually
comes with optional schema validation. No schema means arbitrary keys and
values can be added, and readers have no guarantees about which fields a
document contains.

Document databases are sometimes called **schemaless**, but that’s
misleading: the code that reads the data usually assumes some structure —
an implicit schema, not enforced by the database
([19](data-models-references.md)). A more accurate pair of terms:

| Term | Meaning |
|---|---|
| **Schema-on-read** | Structure is implicit and interpreted when the data is read |
| **Schema-on-write** | Schema is explicit; the database ensures all data conforms when written ([20](data-models-references.md)) |

Schema-on-read is similar to **dynamic (runtime) type checking**;
schema-on-write is similar to **static (compile-time) type checking**. The
relative merits are as contentious as in programming languages
([21](data-models-references.md)); there is no clear winner.

The difference is particularly noticeable when changing format. Say you
currently store each user’s full name in one field and want first and last
name separately ([22](data-models-references.md)). In a document database
you start writing new documents with the new fields and handle old
documents in application code:

```javascript
if (user && user.name && !user.first_name) {
    // Documents written before Dec 8, 2023 don't have first_name
    user.first_name = user.name.split(" ")[0];
}
```

The downside: every reader must deal with old formats that may have been
written a long time ago. In a schema-on-write database you typically
migrate:

```sql
ALTER TABLE users ADD COLUMN first_name text DEFAULT NULL;
UPDATE users SET first_name = split_part(name, ' ', 1);      -- PostgreSQL
UPDATE users SET first_name = substring_index(name, ' ', 1); -- MySQL
```

In most relational databases, adding a column with a default is fast even
on large tables. Running the `UPDATE` is likely slow (every row rewritten);
other schema operations (changing a column’s datatype) typically copy the
entire table. Tools exist to perform such changes in the background without
downtime ([23](data-models-references.md)–[26](data-models-references.md)),
but migrations on large databases remain operationally challenging. A
common compromise: add `first_name` as `NULL` (fast) and fill it in at
read time, as you would with a document database.

Schema-on-read is advantageous when items in the collection do not all
have the same structure:

- Many types of objects, and it is not practicable to put each type in its
  own table.
- Structure is determined by external systems you do not control and that
  may change at any time.

When all records are expected to have the same structure, schemas are a
useful mechanism for documenting and enforcing that structure. Schema
evolution is a later chapter.

### Data locality for reads and writes

A document is usually stored as a single continuous string, encoded as
JSON, XML, or a binary variant (MongoDB’s BSON). If the application often
needs the entire document (e.g. to render a page), this storage locality
has a performance advantage. Split across multiple tables, multiple index
lookups are required, which may mean more disk seeks.

The locality advantage applies only if you need large parts of the
document at the same time. The database typically loads the entire
document, which is wasteful if you need only a small part of a large one.
On updates, the entire document usually needs to be rewritten. Keep
documents fairly small and avoid frequent small updates.

Storing related data together for locality is not limited to the document
model. Google’s Spanner can declare that a table’s rows should be
**interleaved** (nested) within a parent table
([27](data-models-references.md)). Oracle has multi-table index cluster
tables ([28](data-models-references.md)). The wide-column model
popularized by Bigtable (HBase, Accumulo) has **column families** with a
similar purpose ([29](data-models-references.md)).

### Query languages for documents

Most relational databases are queried using SQL. Document databases vary:
some allow only key-value access by primary key; others offer secondary
indexes inside documents; some provide rich query languages.

XML databases are often queried with XQuery and XPath, including joins
across documents ([30](data-models-references.md)). JSON Pointer
([31](data-models-references.md)) and JSONPath
([32](data-models-references.md)) provide an XPath equivalent for JSON.
MongoDB’s aggregation pipeline (`$lookup` above) is a query language for
collections of JSON documents.

A feel for the language, using an aggregation needed for analytics:
marine-biology observations, sharks sighted per month. The source dump
omitted the PostgreSQL listing (it printed a stray `1` instead of the
SQL). `date_trunc('month', observation_timestamp)` rounds a timestamp down
to the beginning of that month; the query filters to the Sharks family,
groups by calendar month, and sums animals seen. The MongoDB equivalent:

```javascript
db.observations.aggregate([
    { $match: { family: "Sharks" } },
    { $group: {
        _id: {
            year:  { $year:  "$observationTimestamp" },
            month: { $month: "$observationTimestamp" }
        },
        totalAnimals: { $sum: "$numAnimals" }
    } }
]);
```

The aggregation pipeline is similar in expressiveness to a subset of SQL,
with JSON-based syntax rather than SQL’s English sentence style. A matter
of taste.

### Convergence of document and relational databases

Document and relational databases started as very different approaches and
have grown more similar ([33](data-models-references.md)). Relational
databases added JSON types, query operators, and indexes on properties
inside documents. Some document databases (MongoDB, Couchbase, RethinkDB)
added joins, secondary indexes, and declarative query languages.

That convergence is good news: the two models work best when you can
combine both in the same database. Many document databases need
relational-style references; many relational databases have sections where
schema flexibility helps. Relational–document hybrids are a powerful
combination.

Codd’s original description of the relational model
([4](data-models-references.md)) allowed something similar to JSON within
a relational schema: **nonsimple domains**. A value in a row need not be a
primitive; it can be a nested relation (table), so you can have an
arbitrarily nested tree as a value. Comparable to the JSON and XML support
added to SQL over 30 years later.

**Architect takeaway:** match the model to the relationship shape. A tree
of one-to-few that you load together belongs in a document; many-to-one
and many-to-many belong in joins (or a
[graph](graph-data-models.md)). Treat denormalization as derived data with
an update process. “Schemaless” is schema-on-read — the schema still
exists, just in the application.
