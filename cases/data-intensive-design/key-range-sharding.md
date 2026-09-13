---
type: analysis
title: 'Key-range sharding'
description: 'A shard owns a contiguous key range, like an encyclopedia volume. Range scans are cheap. Sequential keys (timestamps) write to one hot shard. Growth is split and merge.'
tags: [data-intensive-design, sharding, key-range, range-scan, hot-spot]
---

# Key-range sharding

**See also:** [chapter overview](sharding-overview.md) · [hash sharding](hash-sharding.md) · [B-trees](b-trees.md) · [concatenated indexes](multidimensional-search.md#concatenated-indexes) · [hot spots](sharding-hot-spots.md) · [references](sharding-references.md)

How do you decide which records live on which nodes? The goal is an
even spread of data and query load. In theory, 10 fair nodes handle
10× the data and 10× the throughput of one (ignoring replication).
Add or remove a node and you want to
[rebalance](rebalancing.md) onto the new count.

**Skew** is an unfair split. Extreme case: all load on one shard,
nine of ten nodes idle. A shard with disproportionate load is a
**hot shard** or **hot spot**. One key with particularly high load
(a celebrity in a social network) is a **hot key** — see
[hot spots](sharding-hot-spots.md).

The algorithm takes a record’s **partition key** and returns a shard.
In a key-value store that is usually the key or its first part. In a
relational model it might be a column (not necessarily the primary
key). It must be rebalance-friendly.

## Encyclopedia ranges

Assign a contiguous range of partition keys (min to max) to each
shard, like the volumes of a paper encyclopedia (Figure 7-2). The
partition key is the title. Lookup finds the volume whose range
contains the title.

Ranges are not evenly spaced, because data is not. Volume 1 might
hold A–B; volume 12 might hold T–Z. One volume per two letters would
skew. Boundaries must **adapt to the data**.

Boundaries can be chosen by an administrator or by the database.
**Manual** key-range sharding: Vitess (MySQL). **Automatic:**
Bigtable and HBase, MongoDB’s range option, CockroachDB, RethinkDB,
FoundationDB ([6](sharding-references.md)). YugabyteDB offers both
manual and automatic tablet splitting.

Within a shard, keys stay in sorted order
([B-tree](b-trees.md) or [SSTables](log-structured-storage.md)).
Range scans are easy. Treat the key as a
[concatenated index](multidimensional-search.md#concatenated-indexes)
and fetch related records in one query. Sensor network: key =
timestamp of the measurement; a range scan fetches a month of
readings.

## Sequential keys and hot shards

Nearby keys writing at once produce a hot shard. Timestamp as key →
shards are time ranges (one per month). Live sensor writes all go to
*this* month’s shard; others sit idle ([13](sharding-references.md)).

Fix: put something other than the timestamp first. Prefix with sensor
ID so order is sensor, then time. Many sensors writing at once spread
the writes. Cost: a time range across sensors is now one range query
*per sensor*.

## Rebalancing key-range data

An empty database has no ranges to split. HBase and MongoDB let you
**pre-split** an initial set of shards — you need a guess at the key
distribution ([14](sharding-references.md)).

Growth: split an existing shard into two or more smaller shards, each
a contiguous subrange. Distribute those across nodes. Deletes may
require **merging** adjacent small shards. Same idea as the top of a
[B-tree](b-trees.md).

Automatic systems typically split when a shard hits a configured size
(HBase default 10 GB) or when write throughput stays above a
threshold. A hot shard may split even if it is not large, so its
write load can spread.

The number of shards follows the data volume: little data, few
shards, small overhead; huge data, each shard capped at a configurable
maximum ([15](sharding-references.md)).

Splitting is expensive: rewrite the data into new files, like
[compaction](log-structured-storage.md). The shard that needs
splitting is often already hot; the split can overload it.

**Architect takeaway:** key range is the right default when range
scans are the product. Do not use a monotonically increasing first
key. Pre-split if you know the distribution; budget the cost of
split under load.
