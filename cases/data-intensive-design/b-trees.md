---
type: analysis
title: 'B-trees'
description: 'Fixed-size pages overwritten in place. A write-ahead log makes page splits crash-safe. The standard OLTP index in almost every relational database.'
tags: [data-intensive-design, storage, b-tree, wal, oltp]
---

# B-trees

**See also:** [chapter overview](storage-overview.md) · [log-structured storage](log-structured-storage.md) · [LSM vs B-tree](lsm-vs-btree.md) · [ACID durability](acid.md#durability) · [references](storage-references.md)

The log-structured approach is popular, but it is not the only form of
key-value storage. The most widely used structure for reading and writing
database records by key is the **B-tree**.

Introduced in 1970 ([21](storage-references.md)) and called “ubiquitous”
less than 10 years later ([22](storage-references.md)), B-trees remain
the standard index in almost all relational databases, and many
nonrelational databases use them too.

Like SSTables, B-trees keep key-value pairs **sorted by key**, so
lookups and range queries are efficient. That is where the similarity
ends.

Log-structured indexes break the database into variable-size segments
(typically several megabytes or more) that are written once and then
immutable. B-trees break the database into **fixed-size blocks or
pages** and may overwrite a page in place. A page is traditionally
4 KiB; PostgreSQL now defaults to 8 KiB and MySQL to 16 KiB.

Each page has a **page number**, a disk pointer. If all pages live in
one file, `page_number × page_size` is the byte offset. Those references
build a tree of pages.

One page is the **root**. A lookup always starts there. The page holds
keys and child references. Each child owns a continuous key range; the
keys between references are the boundaries. (This structure is sometimes
called a B+ tree; the distinction does not matter here.)

Example: looking up key 251. From the root, follow the reference between
boundaries 200 and 300, then the page for 250–270, and so on down to a
**leaf page** that either stores the value inline or points at the page
that does.

The number of child references in one page is the **branching factor**
— typically several hundred, depending on how much space page references
and range boundaries take. A tree of *n* keys always has depth
**O(log *n*)**. Most databases fit in three or four levels. A four-level
tree of 4 KiB pages with branching factor 500 can store up to 250 TB.

To **update** an existing key: find the leaf and overwrite that page. To
**insert**: find the page whose range covers the new key and add it. If
the page is full, **split** it into two half-full pages and update the
parent with the new boundary. If the parent is also full, splits can
cascade to the root; splitting the root creates a new root above it.
Deletes (which may merge nodes) are more complex
([5](storage-references.md)).

## Making B-trees reliable

The basic write is: overwrite a page **in place**. The page’s location
does not change, so all references to it stay valid. That is the opposite
of LSM-trees, which only append (and eventually delete obsolete files).

Overwriting several pages at once, as in a split, is dangerous. A crash
after only some of the pages are written leaves a corrupted tree (an
orphan page with no parent). If the hardware cannot atomically write a
whole page, you can also get a **torn page**
([23](storage-references.md)).

The usual defence is a **write-ahead log** (WAL): an append-only file
to which every B-tree modification is written **before** it is applied
to the tree. After a crash, the log restores a consistent tree
([2](storage-references.md), [24](storage-references.md)). Filesystems
call the same idea **journaling**.

Implementations typically buffer modified pages in memory rather than
writing every page immediately. The WAL still protects durability: once
the change is in the WAL and flushed with `fsync`, the database can
recover it ([25](storage-references.md)).

## Using B-tree variants

A few of the variants that have accumulated over decades:

- **Copy-on-write** instead of overwrite-plus-WAL (LMDB
  ([26](storage-references.md))): write the modified page elsewhere and
  create new parent pages pointing at it. Also useful for concurrency
  control (snapshot isolation, a later topic).
- **Abbreviated keys** on interior pages: store only enough to act as
  range boundaries. More keys per page → higher branching factor →
  fewer levels.
- **Sequential leaf layout** to speed sorted scans by reducing seeks.
  Hard to maintain as the tree grows.
- **Sibling pointers** on leaf pages so a scan can walk left/right
  without jumping back to parents.

Trade-offs against LSM-trees are in
[Comparing LSM-trees and B-trees](lsm-vs-btree.md).
