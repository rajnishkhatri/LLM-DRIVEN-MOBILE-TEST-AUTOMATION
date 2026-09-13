---
type: analysis
title: 'Multidimensional, full-text, and vector indexes'
description: 'Concatenated indexes fail when you need two ranges at once. R-trees, inverted indexes, and vector indexes (IVF, HNSW) each answer a different multi-condition query.'
tags: [data-intensive-design, storage, r-tree, full-text, inverted-index, vector-index, hnsw]
---

# Multidimensional, full-text, and vector indexes

**See also:** [chapter overview](storage-overview.md) · [B-trees](b-trees.md) · [LSM / SSTables](log-structured-storage.md) · [columnar bitmaps](columnar-analytics-storage.md#column-compression) · [query vectorization](query-execution-cubes.md) · [references](storage-references.md)

[B-trees](b-trees.md) and [LSM-trees](log-structured-storage.md) answer
range queries over **one** attribute (all usernames starting with L).
Sometimes one attribute is not enough.

## Concatenated indexes

The common multicolumn index **concatenates** fields into one key, in
an order you specify. Like a paper phone book: `(lastname, firstname)`
→ number. You can find a last name, or a last-name + first-name pair.
You cannot find everyone with a given first name.

## Multidimensional indexes

**Multidimensional** indexes query several columns at once. Geospatial
data is the usual example: restaurants by latitude and longitude. A
map viewport is a two-dimensional range:

```sql
SELECT * FROM restaurants
WHERE latitude  > 51.4946 AND latitude  < 51.5079
  AND longitude > -0.1162 AND longitude < -0.1004;
```

A concatenated index cannot answer that efficiently. It can give all
restaurants in a latitude band (any longitude) or a longitude band
(pole to pole), not both at once.

Options: map 2-D location to one number via a **space-filling curve**
and use a regular B-tree ([83](storage-references.md)); or use a
spatial index such as an **R-tree** or **Bkd-tree**
([84](storage-references.md)) that groups nearby points in the same
subtree. PostGIS implements geospatial indexes as R-trees on
PostgreSQL’s GiST ([85](storage-references.md)). Regular grids of
triangles, squares, or hexagons are another approach
([86](storage-references.md)).

Not only geography. Ecommerce: a 3-D index on `(red, green, blue)` for
a color range. Weather: `(date, temperature)` for observations in a
year between 25°C and 30°C. A one-dimensional index forces a scan of
one dimension and a filter on the other; two dimensions narrow both
at once ([87](storage-references.md)).

## Full-text search

Search a collection of documents by keywords that may appear anywhere
([88](storage-references.md)). Information retrieval is a specialist
field: languages without spaces between words, typos, grammatical
forms, synonyms. Those problems sit outside this note.

At its core, full-text search is another multidimensional query. Each
**term** is a dimension. A document that contains term *x* has 1 in
that dimension, else 0. “Red apples” is a 1 in `red` **and** a 1 in
`apples`. The number of dimensions can be huge.

The structure is an **inverted index**: term → postings list (IDs of
documents that contain the term). Sequential document IDs let the
list be a sparse bitmap
([column compression](columnar-analytics-storage.md#column-compression)):
the *n*th bit for term *x* is 1 if document *n* contains *x*
([89](storage-references.md)).

Documents containing both *x* and *y*: load two bitmaps, bitwise AND
— the same pattern as a
[vectorized warehouse predicate](query-execution-cubes.md#vectorized-processing),
and still cheap on run-length-encoded bitmaps.

Lucene (Elasticsearch, Solr) works this way
([90](storage-references.md)). Term → postings lives in SSTable-like
sorted files, merged in the background with the same
[log-structured](log-structured-storage.md) approach
([91](storage-references.md)). PostgreSQL GIN uses postings lists for
full-text and for indexing inside JSON
([92](storage-references.md), [93](storage-references.md)).

Alternative to words: **n-grams** — all substrings of length *n*.
Trigrams of `hello` are `hel`, `ell`, `llo`. An inverted index of
trigrams finds arbitrary substrings of length ≥ 3, and can even
support regular expressions; the index is large
([94](storage-references.md)).

For typos, Lucene searches within an **edit distance** (distance 1 =
one letter added, removed, or replaced)
([95](storage-references.md)). Terms are stored as a finite-state
automaton over characters (like a trie
([96](storage-references.md))) and transformed into a Levenshtein
automaton ([97](storage-references.md)).

## Vector embeddings

**Semantic search** goes past synonyms and typos toward meaning. It
is becoming central to AI applications such as
retrieval-augmented generation: a help page titled “canceling your
subscription” should still match “how to close my account” or
“terminate contract.”

An **embedding model** (often an LLM) turns a document into a
**vector embedding** — an array of floats, a point in a
high-dimensional space. Nearby points are semantically similar.

This “vector” is not
[vectorized processing](query-execution-cubes.md#vectorized-processing)
(a batch of bits). It is a location in an abstract space.

Toy 3-D example: agriculture `[0.38, 0.83, 0.41]`, vegetables
`[0.36, 0.64, 0.67]` (nearby), star schemas
`[0.85, 0.10, -0.52]` (far). Production models use 1,000+ numbers.
We do not interpret individual coordinates. Distance is
**cosine similarity** (angle) or **Euclidean** (straight-line).

Early models — Word2Vec ([98](storage-references.md)), BERT
([99](storage-references.md)), GPT
([100](storage-references.md)) — were text neural nets. Later work
added video, audio, and images. Recent architectures are
**multimodal**: one model embeds several modalities.

At query time the engine embeds the user’s text (plus context such as
location) and asks a **vector index** for the nearest document
vectors. R-trees degrade in very high dimensions, so specialist
indexes are used:

**Flat.** Store vectors as-is. Compare the query to every vector.
Accurate, slow.

**Inverted file (IVF).** Cluster the space into centroids so fewer
vectors are compared. Faster, **approximate**: a close document may
sit in another partition. A query’s **probes** are how many
partitions to check — more probes, more accuracy, more work.

**Hierarchical Navigable Small World (HNSW).** Layers of graphs:
nodes are vectors, edges are proximity. Start at a sparse top layer,
walk to a nearer neighbor, drop to a denser layer, repeat. Also
approximate.

Faiss implements several variants of each
([101](storage-references.md)); PostgreSQL `pgvector` supports both
([102](storage-references.md)). Algorithm detail is in the papers
([103](storage-references.md), [104](storage-references.md)).
