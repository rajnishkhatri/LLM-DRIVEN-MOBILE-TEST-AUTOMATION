---
type: analysis
title: 'Hot spots'
description: 'Uniform keys are not uniform load. A celebrity key saturates one shard. Isolate it, or split writes with a random suffix and pay on read. Load also moves with time.'
tags: [data-intensive-design, sharding, hot-spot, skew, heat-management]
---

# Hot spots

**See also:** [chapter overview](sharding-overview.md) · [key-range sharding](key-range-sharding.md) · [hash sharding](hash-sharding.md) · [home timelines](home-timeline-case-study.md) · [rebalancing](rebalancing.md) · [references](sharding-references.md)

[Consistent hashing](hash-sharding.md#consistent-hashing) spreads
keys evenly. It does not spread **load**. Much more data under some
partition keys, or a much higher request rate to some keys, still
leaves some servers overloaded and others idle.

On a social media site, a celebrity post with millions of followers
can storm one key — the celebrity’s user ID, or the ID of the action
people are commenting on ([22](sharding-references.md)). Same
shape as the
[home-timeline celebrity problem](home-timeline-case-study.md).

A more flexible policy is required
([23](sharding-references.md), [24](sharding-references.md)).
Range-of-keys or range-of-hashes sharding can put an individual hot
key in a shard by itself, even on a dedicated machine
([25](sharding-references.md)).

## Application-level split

If a key is known to be hot, append (or prepend) a random number.
Two random digits split writes across 100 keys, which can land on
different shards.

Reads then have more work: read all 100 keys and combine. **Write**
load splits; **read** volume to each piece of the hot key does not.
You also need bookkeeping: only a few keys deserve the suffix; most
keys would pay overhead for nothing. Track which keys are split, and
a process to convert a regular key into a managed hot key.

Load changes over time. A viral post may be hot for two days, then
quiet. Some keys are hot for writes, others for reads — different
strategies.

Some large-scale cloud services automate this. Amazon calls it
**heat management** ([26](sharding-references.md)) or **adaptive
capacity** ([17](sharding-references.md)). Details are beyond this
chapter.

**Architect takeaway:** hashing does not save you from a hot key.
Either isolate it, or accept read amplification from a write split.
Treat virality as temporary; have a path back to a single key.
