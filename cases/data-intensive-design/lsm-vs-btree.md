---
type: analysis
title: 'Comparing LSM-trees and B-trees'
description: 'LSM-trees win on sequential writes and write amplification; B-trees win on predictable point and range reads. Test your workload; hybrids exist.'
tags: [data-intensive-design, storage, lsm, b-tree, write-amplification]
---

# Comparing LSM-trees and B-trees

**See also:** [chapter overview](storage-overview.md) · [log-structured storage](log-structured-storage.md) · [B-trees](b-trees.md) · [performance](performance.md) · [law and society](law-and-society.md) · [references](storage-references.md)

Rule of thumb: **LSM-trees for write-heavy** applications, **B-trees
faster for reads** ([27](storage-references.md),
[28](storage-references.md)). Benchmarks are sensitive to workload
detail. Test with *your* workload. It is also not a strict either/or:
some engines blend both — multiple B-trees merged LSM-style.

## Read performance

In a B-tree, a lookup reads one page per level. Levels are few, so
reads are generally fast and **predictable**. In an LSM engine, a read
often checks several SSTables at different compaction stages; Bloom
filters cut the disk I/O. Which is faster depends on the engine and the
workload.

**Range queries** are simple on B-trees (walk the sorted leaves). LSM
range queries also use SSTable sort order, but they must scan segments
in parallel and merge. Bloom filters do not help: you would need to
hash every possible key in the range ([29](storage-references.md)).
Range queries are therefore more expensive than point queries on LSM.

High write throughput can spike latency if the memtable fills and
compaction cannot keep up. Many engines, including RocksDB, apply
**backpressure**: they suspend reads and writes until the memtable
flushes ([30](storage-references.md), [31](storage-references.md)).

Modern NVMe SSDs (PCIe, not SATA) can issue many independent reads in
parallel. Both designs can deliver high read throughput if the engine
is built to use that parallelism ([32](storage-references.md)).

## Sequential versus random writes

If the application writes keys scattered across the key space, a B-tree
issues **random writes**: the pages to overwrite can sit anywhere on
disk. An LSM engine writes whole segment files (memtable flush or
compaction), much larger than a B-tree page — **sequential writes**.

Disks have higher sequential than random write throughput, so
log-structured engines generally handle more writes on the same
hardware. The gap is largest on spinning disks; on the SSDs most
databases use today it is smaller but still noticeable.

### Sequential versus random writes on SSDs

On HDDs, a random write waits for the head to seek and the platter to
rotate — milliseconds. SSDs have no such mechanics, but they still
prefer sequential writes.

Flash reads and writes a **page** (typically 4 KiB) and erases a
**block** (typically 512 KiB). Before a block can be erased, the
controller must copy still-valid pages elsewhere — **garbage
collection** ([33](storage-references.md)).

A sequential workload writes large chunks, so a whole 512 KiB block
often belongs to one file. When that file is deleted, the block erases
with no GC. A random workload mixes valid and invalid pages in a
block, so GC does more work ([34](storage-references.md),
[35](storage-references.md), [36](storage-references.md)). Bandwidth
spent on GC is unavailable to the application, and the extra writes
**wear the flash**. Random writes wear the drive out faster.

## Write amplification

One application write becomes multiple disk I/O operations.

LSM: write to the durability log, again when the memtable flushes,
again on every compaction that includes the pair. If values are much
larger than keys, store values separately and compact only
key-and-reference SSTables ([37](storage-references.md)).

B-tree: at least twice — WAL, then the tree page. Sometimes the whole
page must be written even if only a few bytes changed, so the tree
can recover after a crash ([38](storage-references.md),
[39](storage-references.md)).

**Write amplification** is bytes written to disk divided by bytes you
would have written as a bare append-only log (sometimes counted in I/O
operations instead). In write-heavy apps the bottleneck is disk write
rate; higher amplification means fewer application writes per second
inside the same bandwidth.

Which design amplifies less depends on key/value length and overwrite
versus insert mix. For typical workloads LSM-trees tend to be lower:
they do not rewrite whole pages and they can compress SSTable chunks
([40](storage-references.md)). Lower amplification also wears SSDs
more slowly.

Measure write throughput long enough for amplification to show. An
empty LSM-tree has no compaction yet, so all bandwidth goes to new
writes. As the database grows, new writes share the disk with
compaction.

## Disk space usage

B-trees **fragment**. After many deletes, the file still holds unused
pages in the middle; they cannot easily be returned to the OS.
Subsequent inserts can reuse them, but a background process (PostgreSQL
`VACUUM` ([25](storage-references.md))) must move pages to reclaim
space.

Fragmentation is less of a problem in LSM-trees: compaction rewrites
files, and SSTables do not have leftover page holes. Compressed
key-value blocks often make smaller files than B-trees. Overwritten
keys still occupy space until compaction removes them; that overhead
is low with leveled compaction ([40](storage-references.md),
[41](storage-references.md)). Size-tiered uses more disk, especially
temporarily during a merge.

Multiple on-disk copies also matter when you must **prove a delete**
(data-protection rules — see [law and society](law-and-society.md)).
In most LSM engines a deleted record can linger in higher levels until
the tombstone has propagated through every compaction level. Specialist
designs propagate deletions faster ([42](storage-references.md)).

The flip side: immutable SSTable files make **snapshots** cheap (backup,
or a copy for testing). Flush the memtable and record which segment
files existed. As long as those files are not deleted, you need not
copy them. Overwriting B-tree pages makes an efficient snapshot harder.
