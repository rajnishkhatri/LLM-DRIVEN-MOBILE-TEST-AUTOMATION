---
type: analysis
title: 'Graph-like data models'
description: 'When many-to-many is the common case, model vertices and edges. Cypher expresses variable-length traversal in a few lines; the same query in recursive SQL is an order of magnitude longer.'
tags: [data-intensive-design, data-models, graph, cypher, property-graph]
---

# Graph-like data models

**See also:** [chapter overview](data-models-overview.md) · [many-to-many](relational-vs-document.md#many-to-one-and-many-to-many-relationships) · [triples and Datalog](triple-stores-sparql-datalog.md) · [GraphQL](graphql.md) · [references](data-models-references.md)

If your application has mostly one-to-many relationships (tree-structured
data) and few other relationships between records, the
[document model](relational-vs-document.md) is appropriate.

If many-to-many relationships are very common, the relational model can
handle simple cases, but as connections become more complex it becomes
more natural to model the data as a **graph**.

A graph consists of two kinds of objects: **vertices** (nodes, entities)
and **edges** (relationships, arcs). Typical examples:

| Graph | Vertices | Edges |
|---|---|---|
| Social graphs | People | Who knows whom |
| The web graph | Web pages | HTML links |
| Road or rail networks | Junctions | Roads or railway lines |

Well-known algorithms operate on these graphs: map apps search for the
shortest path in a road network; PageRank on the web graph ranks pages in
search results ([34](data-models-references.md)).

Graphs can be represented in several ways. In the **adjacency list**
model, each vertex stores the IDs of its neighbor vertices one edge away.
Alternatively, an **adjacency matrix** is a two-dimensional array in which
each row and column is a vertex, 0 when there is no edge and 1 when there
is. Adjacency lists are good for traversals; matrices are good for machine
learning (see [DataFrames](dataframes.md)).

In the examples above, all vertices represent the same kind of thing
(people, pages, junctions). Graphs are not limited to homogeneous data. An
equally powerful use is a consistent way of storing completely different
types of objects in a single database:

- Facebook maintains a single graph with many types of vertices and edges.
  Vertices represent people, locations, events, check-ins, comments; edges
  indicate friendship, which check-in happened where, who commented, who
  attended which event ([35](data-models-references.md)).
- Search engines use **knowledge graphs** to record facts about entities
  that often occur in search queries — organizations, people, places
  ([36](data-models-references.md)). Obtained by crawling and analyzing
  website text; some sites (Wikidata) also publish graph data in structured
  form.

This section discusses the **property graph** model (Neo4j, Memgraph,
KùzuDB ([37](data-models-references.md)), and others
([38](data-models-references.md))) and, in a
[companion Concept](triple-stores-sparql-datalog.md), the **triple store**
model (Datomic, AllegroGraph, Blazegraph). The models are fairly similar
in what they can express; some graph databases (Amazon Neptune) support
both.

Query languages covered here: **Cypher** and **SQL** (recursive CTEs).
[SPARQL, Datalog](triple-stores-sparql-datalog.md), and
[GraphQL](graphql.md) are separate. Other languages exist, such as Gremlin
([39](data-models-references.md)).

Running example: two people, Lucy from Idaho and Alain from Saint-Lô,
France. They are married and living in London. Each person and each
location is a vertex; relationships are edges. Queries that are easy in
graph databases and difficult in other models.

## Property graphs

In the **property graph** (labeled property graph) model, each vertex
consists of:

- A unique identifier
- A **label** (string) describing the type of object
- A set of outgoing edges
- A set of incoming edges
- A collection of **properties** (key-value pairs)

Each edge consists of:

- A unique identifier
- The vertex at which the edge starts (the **tail** vertex)
- The vertex at which the edge ends (the **head** vertex)
- A label describing the kind of relationship
- A collection of properties (key-value pairs)

You can think of a graph store as two relational tables, one for vertices
and one for edges (PostgreSQL `jsonb` for properties). Head and tail are
stored for each edge; incoming or outgoing edges for a vertex are a query
on `head_vertex` or `tail_vertex`.

```sql
CREATE TABLE vertices (
    vertex_id   integer PRIMARY KEY,
    label       text,
    properties  jsonb
);

CREATE TABLE edges (
    edge_id     integer PRIMARY KEY,
    tail_vertex integer REFERENCES vertices (vertex_id),
    head_vertex integer REFERENCES vertices (vertex_id),
    label       text,
    properties  jsonb
);

CREATE INDEX edges_tails ON edges (tail_vertex);
CREATE INDEX edges_heads ON edges (head_vertex);
```

Important aspects:

- Any vertex can have an edge connecting it with any other vertex. No
  schema restricts which kinds of things can be associated.
- Given any vertex, you can efficiently find both incoming and outgoing
  edges and traverse the graph forward and backward (hence indexes on both
  `tail_vertex` and `head_vertex`).
- Different labels for different kinds of vertices and relationships let
  you store several kinds of information in a single graph.
- The edges table is like the many-to-many associative table in
  [relational many-to-many](relational-vs-document.md#many-to-one-and-many-to-many-relationships),
  generalized to allow many types of relationship in the same table.
  Indexes on labels and properties let you find vertices or edges with
  certain properties efficiently.

A limitation: an edge can associate only **two** vertices, whereas a
relational join table can represent three-way or higher-degree
relationships with multiple foreign keys on a single row. Those can be
represented in a graph by creating an additional vertex corresponding to
each join-table row, or by using a **hypergraph**.

Those features give graphs a great deal of flexibility. Things that would
be difficult in a traditional relational schema: different kinds of
regional structures in different countries (France has *départements* and
*régions*; the US has counties and states); quirks of history such as a
country within a country; varying granularity (Lucy’s current residence
specified as a city, her birthplace only at state level).

You could extend the graph with food allergies (a vertex per allergen, an
edge from person to allergen) and foods that contain those substances,
then query what is safe for each person to eat. Graphs are good for
**evolvability**: as you add features, a graph can be extended to
accommodate changes in the application’s data structures.

## The Cypher query language

Cypher is a query language for property graphs, originally created for
Neo4j and later developed into an open standard as openCypher
([40](data-models-references.md)). Also supported by Memgraph, KùzuDB,
Amazon Neptune, Apache AGE (storage in PostgreSQL), and others. Named
after a character in *The Matrix*, not related to ciphers in cryptography
([41](data-models-references.md)).

Inserting part of the Lucy/Idaho example. Each vertex gets a symbolic name
used only within the query. Arrow notation:
`(idaho) -[:WITHIN]-> (usa)` creates an edge labeled `WITHIN`.

```cypher
CREATE
  (namerica :Location {name:'North America',  type:'continent'}),
  (usa      :Location {name:'United States',  type:'country'  }),
  (idaho    :Location {name:'Idaho',          type:'state'    }),
  (lucy     :Person   {name:'Lucy' }),
  (idaho) -[:WITHIN ]-> (usa)  -[:WITHIN]-> (namerica),
  (lucy)  -[:BORN_IN]-> (idaho)
```

Find the names of all people who emigrated from the United States to
Europe: vertices with a `BORN_IN` edge to a location within the US and a
`LIVES_IN` edge to a location within Europe.

```cypher
MATCH
  (person) -[:BORN_IN]->  () -[:WITHIN*0..]-> (:Location {name:'United States'}),
  (person) -[:LIVES_IN]-> () -[:WITHIN*0..]-> (:Location {name:'Europe'})
RETURN person.name
```

Read: find any vertex (`person`) that has an outgoing `BORN_IN` edge from
which a chain of outgoing `WITHIN` edges reaches a `Location` named United
States, **and** an outgoing `LIVES_IN` edge from which a chain of
`WITHIN` edges reaches Europe. Return `person.name`.

There are several ways of executing this. Scan all people and examine
birthplace and residence. Equivalently, start from the two `Location`
vertices and work backward: if there is an index on `name`, find US and
Europe, follow incoming `WITHIN` edges to all locations in each, then look
for people via incoming `BORN_IN` or `LIVES_IN`.

## Graph queries in SQL

Graph data can be represented in a relational database (the schema
above). Can we also query it using SQL?

Yes, but with some difficulty. Every edge you traverse is effectively a
join with the `edges` table. In a relational database you usually know in
advance which joins you need. In a graph query you may need to traverse a
**variable number of edges** before you find the vertex you want — the
number of joins is not fixed in advance.

That happens in `() -[:WITHIN*0..]-> ()`. A person’s `LIVES_IN` edge may
point to a street, city, district, region, or state. A city may be
`WITHIN` a region, a region `WITHIN` a state, and so on. The edge may
point directly at the location you want, or be several levels away.

In Cypher, `:WITHIN*0..` expresses that concisely: “follow a `WITHIN`
edge, zero or more times.” Like `*` in a regular expression.

Variable-length traversal in SQL uses **recursive common table
expressions** (`WITH RECURSIVE`). The source dump omitted the 31-line SQL
listing (it printed a stray `1` instead of the SQL). The idea:

1. Find the vertex whose `name` is United States; make it the first
   element of `in_usa`.
2. Follow all incoming `within` edges from vertices in `in_usa` and add
   them, until all incoming `within` edges have been visited.
3. Do the same starting from Europe, building `in_europe`.
4. For each vertex in `in_usa`, follow incoming `born_in` edges to people
   born somewhere within the US.
5. Similarly, incoming `lives_in` edges from `in_europe`.
6. Intersect the two sets of people by joining them.

A 4-line Cypher query requiring 31 lines of SQL shows how much the right
data model and query language matter. Further details: handling cycles,
breadth-first vs depth-first traversal ([42](data-models-references.md)).
Oracle has a different SQL extension for recursive queries, called
**hierarchical** ([43](data-models-references.md)). Other graph query
languages include TigerGraph’s GSQL ([44](data-models-references.md)) and
PGQL ([45](data-models-references.md)).

The **Graph Query Language (GQL)** ISO standard, based on Cypher, was
published in 2024 ([46](data-models-references.md),
[47](data-models-references.md), [48](data-models-references.md)). Not
widely adopted yet; hopefully it leads to greater uniformity among graph
databases.

**Architect takeaway:** reach for a graph when many-to-many is the common
case and queries traverse a variable number of hops. Cypher (and GQL)
encode that traversal; recursive SQL can emulate it, awkwardly. An edge
is binary — n-ary relationships need an extra vertex or a hypergraph.
