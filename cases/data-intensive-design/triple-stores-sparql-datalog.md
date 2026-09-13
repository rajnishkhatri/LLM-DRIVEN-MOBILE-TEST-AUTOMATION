---
type: analysis
title: 'Triple stores, SPARQL, and Datalog'
description: 'Property graphs and triples are the same ideas in different words. SPARQL matches Cypher for path queries; Datalog builds recursive graph queries as stacked rules.'
tags: [data-intensive-design, data-models, rdf, sparql, datalog, triples]
---

# Triple stores, SPARQL, and Datalog

**See also:** [chapter overview](data-models-overview.md) · [property graphs and Cypher](graph-data-models.md) · [GraphQL](graphql.md) · [references](data-models-references.md)

The **triple store** model is mostly equivalent to the
[property graph](graph-data-models.md) model, using different words to
describe the same ideas. It is nevertheless worth discussing, because
tools and languages for triple stores can be valuable additions to the
toolbox.

In a triple store, all information is stored as very simple three-part
statements: **(subject, predicate, object)**. In `(Jim, likes, bananas)`,
Jim is the subject, likes is the predicate (verb), and bananas is the
object.

Databases that offer a triple-like data model often store extra metadata
on each tuple. AWS Neptune uses **quads** (4-tuples) by adding a graph ID
([49](data-models-references.md)); Datomic uses 5-tuples, extending each
triple with a transaction ID and a Boolean to indicate deletion
([50](data-models-references.md)). Since they retain the basic
subject-predicate-object structure, these notes still call them triple
stores.

The subject of a triple is equivalent to a vertex in a graph. The object
is one of two things:

- A **primitive value** (string or number). Then the predicate and object
  are equivalent to the key and value of a property on the subject vertex.
  `(lucy, birthYear, 1989)` is like a vertex `lucy` with properties
  `{"birthYear": 1989}`.
- **Another vertex.** Then the predicate is an edge, the subject is the
  tail, and the object is the head. In `(lucy, marriedTo, alain)`, both
  `lucy` and `alain` are vertices and `marriedTo` is the edge label.

The same Lucy/Idaho data as Turtle, a subset of Notation3 (N3)
([51](data-models-references.md)):

```turtle
@prefix : <urn:example:>.
_:lucy     a       :Person.
_:lucy     :name   "Lucy".
_:lucy     :bornIn _:idaho.
_:idaho    a       :Location.
_:idaho    :name   "Idaho".
_:idaho    :type   "state".
_:idaho    :within _:usa.
_:usa      a       :Location.
_:usa      :name   "United States".
_:usa      :type   "country".
_:usa      :within _:namerica.
_:namerica a       :Location.
_:namerica :name   "North America".
_:namerica :type   "continent".
```

Vertices are written as `_:someName`. The name means nothing outside this
file; it exists so we know which triples refer to the same vertex. When
the predicate is an edge, the object is a vertex (`_:idaho :within _:usa`).
When the predicate is a property, the object is a string literal
(`_:usa :name "United States"`).

More compact: semicolons say multiple things about the same subject.

```turtle
@prefix : <urn:example:>.
_:lucy     a :Person;   :name "Lucy";          :bornIn _:idaho.
_:idaho    a :Location; :name "Idaho";         :type "state";   :within _:usa.
_:usa      a :Location; :name "United States"; :type "country"; :within _:namerica.
_:namerica a :Location; :name "North America"; :type "continent".
```

## The RDF data model

Turtle is a way of encoding data in the **Resource Description Framework
(RDF)** ([58](data-models-references.md)), a data model designed for the
Semantic Web. RDF can also be encoded more verbosely as XML. Tools like
Apache Jena convert between encodings.

```xml
<rdf:RDF xmlns="urn:example:"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">

  <Location rdf:nodeID="idaho">
    <name>Idaho</name>
    <type>state</type>
    <within>
      <Location rdf:nodeID="usa">
        <name>United States</name>
        <type>country</type>
        <within>
          <Location rdf:nodeID="namerica">
            <name>North America</name>
            <type>continent</type>
          </Location>
        </within>
      </Location>
    </within>
  </Location>

  <Person rdf:nodeID="lucy">
    <name>Lucy</name>
    <bornIn rdf:nodeID="idaho"/>
  </Person>
</rdf:RDF>
```

RDF has quirks because it is designed for internet-wide data exchange.
Subject, predicate, and object of a triple are often **URIs**. A predicate
might be `<http://my-company.com/namespace#within>` rather than just
`WITHIN`. The reasoning: you should be able to combine your data with
someone else’s, and if they attach a different meaning to `within`, you
won’t get a conflict because their predicate is actually
`<http://other.org/foo#within>`.

The URL `http://my-company.com/namespace` doesn’t necessarily need to
resolve to anything — from RDF’s point of view it is simply a namespace.
To avoid confusion with `http://` URLs, these examples use nonresolvable
URIs such as `urn:example:within`. Specify the prefix once at the top of
the file and then forget about it.

## The SPARQL query language

SPARQL is a query language for triple stores using the RDF data model
([59](data-models-references.md)). Recursive acronym: SPARQL Protocol and
RDF Query Language, pronounced “sparkle.” It predates Cypher; Cypher’s
pattern matching is borrowed from SPARQL, so they look similar.

The same “people who moved from the US to Europe” query is similarly
concise:

```sparql
PREFIX : <urn:example:>

SELECT ?personName WHERE {
  ?person :name ?personName.
  ?person :bornIn  / :within* / :name "United States".
  ?person :livesIn / :within* / :name "Europe".
}
```

Equivalent path patterns (variables start with `?` in SPARQL):

```text
(person) -[:BORN_IN]-> () -[:WITHIN*0..]-> (location)   # Cypher
?person :bornIn / :within* ?location.                   # SPARQL
```

Because RDF doesn’t distinguish properties from edges — both are
predicates — you use the same syntax for matching properties:

```text
(usa {name:'United States'})   # Cypher
?usa :name "United States".    # SPARQL
```

SPARQL is supported by Amazon Neptune, AllegroGraph, Blazegraph, OpenLink
Virtuoso, Apache Jena, and various other triple stores
([38](data-models-references.md)).

## Datalog: recursive relational queries

Datalog is much older than SPARQL or Cypher, from academic research in the
1980s ([60](data-models-references.md), [61](data-models-references.md),
[62](data-models-references.md)). It is less well-known among software
engineers and not widely supported in mainstream databases, but it is a
very expressive language, especially powerful for complex queries. Niche
databases including Datomic, LogicBlox, CozoDB, and LinkedIn’s LIquid
([63](data-models-references.md)) use it. It is based on a **relational**
data model, not a graph; it appears here because recursive queries on
graphs are a particular strength.

The contents of a Datalog database are **facts**, each corresponding to a
row in a relational table. A `location` table with columns ID, name, and
type: the US as a country is `location(2, "United States", "country")`. In
general, `table(val1, val2, …)` means `table` contains a row where the
first column is `val1`, and so on.

The Lucy/Idaho data. Edges (`within`, `born_in`, `lives_in`) are
two-column join tables. Lucy has ID 100, Idaho has ID 3, so “Lucy was
born in Idaho” is `born_in(100, 3)`.

```datalog
location(1, "North America", "continent").
location(2, "United States", "country").
location(3, "Idaho", "state").

within(2, 1).    /* US is in North America */
within(3, 2).    /* Idaho is in the US     */

person(100, "Lucy").
born_in(100, 3). /* Lucy was born in Idaho */
```

The same query as a set of **rules**. Datalog is a subset of Prolog.

```datalog
within_recursive(LocID, PlaceName) :- location(LocID, PlaceName, _). /* Rule 1 */

within_recursive(LocID, PlaceName) :- within(LocID, ViaID),          /* Rule 2 */
                                      within_recursive(ViaID, PlaceName).

migrated(PName, BornIn, LivingIn)  :- person(PersonID, PName),       /* Rule 3 */
                                      born_in(PersonID, BornID),
                                      within_recursive(BornID, BornIn),
                                      lives_in(PersonID, LivingID),
                                      within_recursive(LivingID, LivingIn).

us_to_europe(Person) :- migrated(Person, "United States", "Europe"). /* Rule 4 */
/* us_to_europe contains the row "Lucy". */
```

Cypher and SPARQL jump in with `SELECT`. Datalog takes a small step at a
time. We define rules that derive new **virtual tables** from the
underlying facts — like (virtual) SQL views: not stored, but queryable
the same way as a table of stored facts.

Three derived tables: `within_recursive`, `migrated`, and `us_to_europe`.
Names and columns are defined by what appears before `:-` in each rule.
`migrated(PName, BornIn, LivingIn)` is a virtual table with three
columns.

The content of a virtual table is defined after `:-`, matching a pattern
in the tables. `person(PersonID, PName)` matches `person(100, "Lucy")`,
binding `PersonID` to 100 and `PName` to `"Lucy"`. A rule applies if the
system can find a match for all patterns on the right. When it applies,
it is as though the left-hand side was added to the database (variables
replaced by the values they matched).

One possible application of the rules:

1. `location(1, "North America", "continent")` exists, so rule 1 applies.
   It generates `within_recursive(1, "North America")`.
2. `within(2, 1)` exists and the previous step generated
   `within_recursive(1, "North America")`, so rule 2 applies. It generates
   `within_recursive(2, "North America")`.
3. `within(3, 2)` exists and the previous step generated
   `within_recursive(2, "North America")`, so rule 2 applies. It generates
   `within_recursive(3, "North America")`.

By repeated application of rules 1 and 2, `within_recursive` can tell us
all locations in North America (or any other location) in the database.

Rule 3 then finds people born in some `BornIn` and living in some
`LivingIn`. Rule 4 invokes rule 3 with `BornIn = 'United States'` and
`LivingIn = 'Europe'`. Querying `us_to_europe` yields the same answer as
the Cypher and SPARQL queries.

Datalog requires a different kind of thinking. Complex queries are built
up rule by rule, one rule referring to others, similarly to breaking code
into functions. Just as functions can be recursive, Datalog rules can
invoke themselves — rule 2 — which enables graph traversals.

**Architect takeaway:** triples are property graphs with different
vocabulary; SPARQL is Cypher’s older cousin. Datalog is the one to reach
for when the query is a stack of recursive derivations, not a single path
pattern — at the cost of a smaller ecosystem.
