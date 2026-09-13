---
type: analysis
title: 'Secondary indexes and in-memory stores'
description: 'A secondary index is a derived key-value map. Clustered stores the row in the index; a heap stores it elsewhere; covering indexes sit in between. In-memory engines drop the on-disk encoding tax.'
tags: [data-intensive-design, storage, secondary-index, clustered-index, in-memory]
---

# Secondary indexes and in-memory stores

**See also:** [chapter overview](storage-overview.md) · [log-structured storage](log-structured-storage.md) · [B-trees](b-trees.md) · [relational vs document](relational-vs-document.md) · [sharding and secondary indexes](sharding-secondary-indexes.md) · [references](storage-references.md)

So far we have discussed only **key-value indexes**, like primary-key
indexes in the relational model. A primary key uniquely identifies one
row, document, or vertex. Other records refer to it by that ID; the
index resolves the reference.

## Secondary indexes

A **secondary index** lets you search by something other than the
primary key. In SQL, `CREATE INDEX` on the same table. On the
[relational schema](relational-vs-document.md) you would most likely
index `user_id` so you can find every row belonging to one user.

A secondary index is a key-value index with one extra property: values
need not be unique. Many rows can share an index entry. Two ways to
handle that:

- Store a **list of matching row IDs** (a postings list, as in
  [full-text search](multidimensional-search.md#full-text-search)).
- Make each entry unique by **appending a row identifier** to the key.

Both [B-trees](b-trees.md) and [log-structured](log-structured-storage.md)
engines can implement either.

## Storing values within the index

The key is what queries search by. What else lives in the index:

**Clustered index.** The actual row (document, vertex) is stored inside
the index structure. InnoDB always clusters on the primary key; SQL
Server lets you pick one clustered index per table
([43](storage-references.md)).

**Heap file.** The index value is a reference: the primary key (InnoDB
secondary indexes) or a disk location. The heap stores rows in no
particular order — append-only, or reuse deleted slots. Postgres uses
this approach ([44](storage-references.md)).

**Covering index** (index with included columns). A middle ground:
some columns live in the index, the full row still lives on the heap
or in the clustered primary key
([45](storage-references.md)). Queries that need only those columns
are answered from the index alone — the index **covers** the query.
Faster reads; more disk; slower writes.

Updating a value without changing the key: a heap can overwrite in
place if the new value is not larger. If it is larger, the record
moves, and **every index** must be updated to the new location — or a
forwarding pointer is left behind
([2](storage-references.md)). Multi-column queries that need several
fields at once are
[multidimensional indexes](multidimensional-search.md).

## Keeping everything in memory

The structures above are answers to the awkwardness of disks. We
tolerate that awkwardness because disks are **durable** (survive power
loss) and cheaper per gigabyte than RAM.

As RAM gets cheaper, many datasets simply fit in memory — possibly
spread across machines. Hence **in-memory databases**.

Some in-memory stores (Memcached) are caches: loss on restart is
acceptable. Others aim for durability: battery-backed RAM, a change
log on disk, periodic snapshots, or replicas. They are still called
in-memory because the disk is an append-only durability log; **reads
are served entirely from RAM**. Files on disk also make backup and
external inspection easier.

Relational in-memory products include VoltDB, SingleStore, and Oracle
TimesTen; vendors claim large gains from dropping on-disk encoding
([46](storage-references.md), [47](storage-references.md)). RAMCloud is
an open-source durable key-value store (log-structured in memory and
on disk ([48](storage-references.md))). Redis and Couchbase write to
disk asynchronously — weaker durability.

The performance win is **not** “we never read disk.” A disk-based
engine with enough RAM may never read disk either: the OS caches
recent blocks. In-memory engines are faster because they skip
**encoding in-memory structures into a disk form**
([49](storage-references.md)).

A second use: data models that are painful with disk indexes. Redis
exposes priority queues and sets through a database-like interface;
keeping everything in RAM keeps the implementation comparatively
simple.
