---
type: analysis
title: 'Log-structured storage'
description: 'Append a log, keep a memtable, flush sorted SSTables, compact in the background. Bloom filters skip the files that cannot contain the key.'
tags: [data-intensive-design, storage, lsm, sstable, bloom-filter, compaction]
---

# Log-structured storage

**See also:** [chapter overview](storage-overview.md) · [B-trees](b-trees.md) · [LSM vs B-tree](lsm-vs-btree.md) · [OLTP vs OLAP](operational-vs-analytical.md) · [references](storage-references.md)

Consider the world’s simplest database, two bash functions:

```bash
#!/bin/bash

db_set () {
    echo "$1,$2" >> database
}

db_get () {
    grep "^$1," database | sed -e "s/^$1,//" | tail -n 1
}
```

`db_set key value` appends a line. `db_get key` returns the most recent
value for that key. The value can be almost anything — a JSON document,
for example.

```
$ db_set 12 '{"name":"London","attractions":["Big Ben","London Eye"]}'
$ db_set 42 '{"name":"San Francisco","attractions":["Golden Gate Bridge"]}'
$ db_get 42
{"name":"San Francisco","attractions":["Golden Gate Bridge"]}
```

The storage format is a text file of comma-separated key-value pairs
(CSV-like, ignoring escaping). Updates do not overwrite: if you set key
42 again, the old line stays and `tail -n 1` picks the latest.

```
$ db_set 42 '{"name":"San Francisco","attractions":["Exploratorium"]}'
$ db_get 42
{"name":"San Francisco","attractions":["Exploratorium"]}
```

`db_set` is fast because **appending to a file is generally very
efficient**. Many databases internally use a **log**: an append-only
sequence of records on disk. It does not have to be human-readable; it
might be binary and intended only for the storage engine. Real engines
still have to handle concurrent writes, reclaim disk space so the log
does not grow forever, and recover partially written records after a
crash — but the principle is the same.

`db_get` is terrible at scale. Every lookup scans the whole file: **O(n)**.
To find a key efficiently you need an **index** — an additional structure
derived from the primary data. Adding or removing an index does not change
the contents of the database; it changes only query performance. That is
the first storage trade-off: well-chosen indexes speed up reads, but every
index consumes disk and **slows down writes**, sometimes substantially
([1](storage-references.md)). Databases therefore do not index everything
by default. You pick indexes from knowledge of typical query patterns.

## Hash map over a log

Keep an in-memory hash map from every key to the **byte offset** of its
most recent value in the append-only file. On write, append the pair and
update the map. On read, seek to the offset. If that part of the file is
already in the filesystem cache, the read needs no disk I/O.

Problems that remain:

- Old overwritten entries never free disk; the log grows forever.
- The hash map is not persisted, so restart rebuilds it by scanning the
  log.
- The table must fit in memory. An on-disk hash map is hard to make fast:
  lots of random I/O, expensive to grow when full, fiddly collision logic
  ([2](storage-references.md)).
- Range queries are not efficient. Keys 10000–19999 require one lookup
  each.

## The SSTable file format

In practice, hash tables are uncommon as database indexes. It is much more
common to keep data **sorted by key** ([3](storage-references.md)). A
**Sorted Strings Table** (SSTable) stores key-value pairs sorted, with
each key appearing only once.

You do not need every key in memory. Group pairs into blocks of a few
kilobytes and store the first key of each block in a **sparse index**
(an immutable B-tree, a trie, or similar
([4](storage-references.md))). Looking for `handiwork` when the index
has `handbag` then `handsome`: seek to `handbag` and scan that block.
A few kilobytes scan quickly. Blocks can also be compressed — less disk
and I/O bandwidth, more CPU.

## Constructing and merging SSTables

An SSTable is better for reading than an append-only log, but you cannot
simply append (the file would no longer be sorted). Rewriting the whole
file on every insert is far too expensive. The hybrid:

1. On write, insert into an in-memory ordered map — red–black tree, skip
   list ([5](storage-references.md)), or trie
   ([6](storage-references.md)). This is the **memtable**.
2. When the memtable exceeds a threshold (typically a few megabytes),
   write it out in sorted order as a new SSTable **segment**. Continue
   writes on a fresh memtable; free the old one after the flush.
3. To read a key, look in the memtable, then the most recent segment,
   then older segments. Missing from all of them means the key does not
   exist.
4. In the background, **merge and compact** segments, discarding
   overwritten or deleted values.

Merging is mergesort: read input files side by side, copy the lowest key
to the output, keep only the more recent value when a key appears more
than once. Memory use stays small because you iterate one key at a time.

To survive a crash, every write is also appended to a separate unsorted
**log**. Its only job is to restore the memtable. When the memtable
flushes to an SSTable, that part of the log can be discarded.

To delete a key, append a **tombstone**. Compaction discards previous
values for that key; once the tombstone reaches the oldest segment, it
can be dropped.

This is essentially RocksDB ([7](storage-references.md)), Cassandra,
ScyllaDB, and HBase ([8](storage-references.md)), all inspired by
Google’s Bigtable paper ([9](storage-references.md)), which introduced
the terms SSTable and memtable. The algorithm was published in 1996 as
the **Log-Structured Merge-tree** (LSM-tree)
([10](storage-references.md)), building on log-structured filesystems
([11](storage-references.md)). Engines that merge and compact sorted
files are **LSM storage engines**.

A segment is written in one pass (memtable flush or merge) and is then
**immutable**. Reads keep using the input segments until the merge
finishes, then switch to the new file and delete the inputs. Segments
need not live on a local disk; they suit object storage (SlateDB, Delta
Lake ([12](storage-references.md))).

Crash recovery is simpler with immutable files: delete an unfinished
SSTable and start again. Incomplete log records are typically caught
with checksums. Durability and crash recovery return under
[ACID](acid.md#durability).

## Bloom filters

Reading a key last updated long ago, or a key that does not exist, can
mean checking several segments. LSM engines often put a **Bloom filter**
([13](storage-references.md)) in each segment: a fast, approximate check
whether a key appears in that SSTable.

For every key, a hash produces indexes into a bit array
([14](storage-references.md)); those bits are set to 1. Query: hash the
key and check those bits. If any bit is 0, the key is **definitely
absent**. If all are 1, the key is **likely** present — or the bits were
set by other keys (a **false positive**).

Rule of thumb: 10 bits per key ≈ 1% false-positive probability; each
extra 5 bits per key cuts that probability tenfold
([15](storage-references.md)). False positives are acceptable here: a
“no” safely skips the SSTable; a “yes” still consults the sparse index
and decodes the block. A false positive is a bit of extra work, not a
wrong answer.

## Compaction strategies

When to compact, and which SSTables to include, is configurable
([16](storage-references.md), [17](storage-references.md)):

**Size-tiered.** Newer, smaller SSTables merge into older, larger ones
(four 256 MB files might become one 898 MB file — not 1,024 MB because
of deletions, overwrites, and TTLs). Old files get very large; merging
them needs a lot of temporary disk. Advantage: high write throughput,
because most data is rewritten only a few times in large sequential
merges.

**Leveled.** SSTable sizes stay fixed and are grouped into levels
(L0, L1, …). L0 is the most recently written data. Levels beyond L0
are key-range partitioned (L1 might hold `a–m` and `n–z`). Each level
has a size limit larger than the one before it. When a level overflows,
one or more SSTables from level *i* merge into level *i* + 1. Compaction
is more incremental and uses less disk. Reads check fewer SSTables than
under size-tiered.

Rule of thumb: size-tiered if the workload is mostly writes; leveled if
it is dominated by reads, or if a small set of keys is written often and
a large set rarely ([18](storage-references.md)). Most implementations
offer several strategies. Performance comparison with B-trees is in
[Comparing LSM-trees and B-trees](lsm-vs-btree.md).

## Embedded storage engines

Many databases are a network service. **Embedded** databases are
libraries in the same process as the application, talking through
function calls and files on local disk: RocksDB, SQLite, LMDB, DuckDB,
KùzuDB ([19](storage-references.md)).

Common on mobile for the local user’s data. On the backend they fit when
the data fits on one machine and concurrent transactions are few. In a
multitenant system where each tenant is small and isolated (no queries
that combine tenants), a separate embedded instance per tenant can work
([20](storage-references.md)).

The methods in this chapter apply to both embedded and client/server
engines. Scaling across machines is a later chapter.
