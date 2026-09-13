---
type: analysis
title: 'Unreliable clocks'
description: 'Monotonic clocks measure duration. Time-of-day clocks jump, drift, and disagree. LWW by timestamp silently drops data. A clock reading is a confidence interval; Spanner waits out the uncertainty.'
tags: [data-intensive-design, distributed-systems, clocks, ntp, truetime]
---

# Unreliable clocks

**See also:** [chapter overview](distributed-systems-overview.md) · [timeouts](timeouts-and-delays.md) · [process pauses](process-pauses.md) · [conflict resolution](conflict-resolution.md) · [detecting concurrent writes](detecting-concurrent-writes.md) · [references](distributed-systems-references.md)

Applications ask clocks two kinds of question.

**Duration:** has this request timed out; 99th-percentile response
time; queries per second over five minutes; time on site. Use a
**monotonic** clock.

**Point in time:** published-at; send the reminder at 09:00; cache
expiry; the timestamp on a log line. Use a **time-of-day**
(wall-clock) clock — and treat it as suspect.

A message is always received after it is sent. Variable
[network delay](unreliable-networks.md) hides *how much* after,
so wall-clock order across machines is not causal order. Each
machine has its own quartz oscillator. NTP steers those clocks
toward a set of servers, themselves usually GPS-backed
([39](distributed-systems-references.md)).

## Time-of-day versus monotonic

`clock_gettime(CLOCK_REALTIME)` / `System.currentTimeMillis`:
seconds since 1970-01-01 UTC, Gregorian, no leap seconds. NTP
can **step** the clock backward if it is too far ahead. Leap
seconds and DST (avoid DST: use UTC) also jump. Unsuitable for
elapsed time ([40](distributed-systems-references.md)). Older
Windows stepped in 10 ms increments
([41](distributed-systems-references.md)).

`CLOCK_MONOTONIC` / `CLOCK_BOOTTIME` /
`System.nanoTime`: a stopwatch
([42](distributed-systems-references.md)). Always moves forward.
The absolute value is meaningless (ns since boot, or similar).
**Do not compare monotonic values across machines.** Multi-socket
servers have a timer per CPU
([43](distributed-systems-references.md)); the OS tries to
present one monotonic view — take that with salt
([44](distributed-systems-references.md)). NTP may **slew** the
rate by up to 0.05%; it does not jump a monotonic clock.

Timeouts and response times: monotonic is fine. No cross-node
sync required.

## Synchronization is worse than you hope

Quartz drifts with temperature. Google budgets 200 ppm
([45](distributed-systems-references.md)): 6 ms after 30 s, or
17 s after a day, even when everything works.

- Too far from NTP: refuse to sync, or force-reset — time jumps
  ([39](distributed-systems-references.md)).
- Firewalled off NTP: unnoticed drift. Happens.
- Accuracy is limited by network delay. One internet experiment:
  35 ms best case, ~1 s spikes
  ([46](distributed-systems-references.md)). Large delay can
  make the client give up.
- Some NTP servers are hours wrong
  ([47](distributed-systems-references.md),
  [48](distributed-systems-references.md)). Query several;
  ignore outliers. You are still betting correctness on
  strangers.
- Leap seconds (59- or 61-second minutes) have crashed large
  systems ([40](distributed-systems-references.md),
  [50](distributed-systems-references.md)). **Smearing** spreads
  the second over a day
  ([51](distributed-systems-references.md),
  [52](distributed-systems-references.md)); server behavior
  varies ([53](distributed-systems-references.md)). Leap seconds
  stop in 2035.
- A VM’s clock jumps forward after a hypervisor pause
  ([29](distributed-systems-references.md),
  [54](distributed-systems-references.md)). The guest NTP client
  does not know it paused
  ([55](distributed-systems-references.md)).
- Phones and embedded devices: users set the clock to cheat
  ([56](distributed-systems-references.md)). Do not trust them.

MiFID II wants 100 µs of UTC for HFT
([57](distributed-systems-references.md)): GPS and/or atomic
clocks, PTP, monitoring
([58](distributed-systems-references.md),
[59](distributed-systems-references.md)). GPS jams near military
sites ([60](distributed-systems-references.md)). Some clouds now
offer high-accuracy VM clocks
([61](distributed-systems-references.md)). A misconfigured NTP
daemon still ruins it.

A bad CPU or NIC fails loudly. A bad quartz or NTP config looks
fine while the clock walks away. Software that trusts the clock
tends to **silent data loss**, not a crash
([62](distributed-systems-references.md),
[63](distributed-systems-references.md)). Monitor offsets; fence
nodes that drift too far.

## Timestamps are not an event order

Figure 9-3 ([multi-leader](multi-leader-replication.md), same
shape as Figure 6-8): client A writes `x = 1` on node 1
(timestamp 42.004); the write replicates to node 3; client B
increments to `x = 2` on node 3 (timestamp 42.003). Causally
later, earlier timestamp. Clock skew under 3 ms — better than
you should expect.

[Last-write-wins](conflict-resolution.md#last-write-wins-discarding-concurrent-writes)
keeps the greater timestamp. Node 2 drops `x = 2`. The increment
is gone. Cassandra and ScyllaDB use the client clock plus LWW
and skip the extra read that would bump the timestamp
([62](distributed-systems-references.md)):

- A lagging clock cannot overwrite a faster node’s value until
  the skew elapses. Arbitrary silent loss
  ([63](distributed-systems-references.md),
  [65](distributed-systems-references.md)).
- LWW cannot tell sequential-but-fast from truly concurrent.
  Need [version vectors](detecting-concurrent-writes.md).
- Millisecond clocks collide. A random tiebreak can still
  violate causality
  ([62](distributed-systems-references.md)).

Even tight NTP can deliver a packet that arrives *before* it was
sent on the receiver’s clock. NTP error is itself limited by
RTT plus quartz drift. You cannot make clock error much smaller
than network delay, which is what a correct physical order
would need.

**Logical clocks** (Lamport
([66](distributed-systems-references.md))) increment counters.
They order events; they do not tell the time of day. Physical
clocks measure elapsed time. ID generators that mix the two
are a later chapter.

## A reading is a confidence interval

Microsecond resolution is not microsecond accuracy. Local NTP
every minute: milliseconds of quartz drift. Public NTP: tens of
milliseconds, 100 ms+ under congestion. Think
`now ± error`, not a point
([67](distributed-systems-references.md)). Most APIs
(`clock_gettime`) omit the error.

Google **TrueTime** and Amazon **ClockBound** return
`[earliest, latest]`. Interval width grows with time since the
last accurate sync ([45](distributed-systems-references.md)).

### Global snapshots

[Snapshot isolation](snapshot-isolation.md) needs a
monotonically increasing transaction ID that respects causality.
On one node, a counter. Across shards and DCs, a global counter
is a coordination bottleneck.

Spanner uses TrueTime as the ID
([68](distributed-systems-references.md),
[69](distributed-systems-references.md)). If two intervals do
not overlap (`A.latest < B.earliest`), B is definitely after A.
On overlap, order is unknown. Spanner **waits out** the
uncertainty before committing a read/write transaction so a
later reader’s interval cannot overlap. GPS or atomic clocks
per DC keep the wait ~7 ms
([45](distributed-systems-references.md)). The clocks are not
the insight; the **interval** is. Accurate sources only shrink
it. YugabyteDB can use ClockBound on AWS
([70](distributed-systems-references.md)); others lean on sync
to varying degrees
([71](distributed-systems-references.md),
[72](distributed-systems-references.md)).

**Architect takeaway:** monotonic for durations; never for
cross-node order. Do not LWW on wall-clock timestamps. If you
need a global snapshot ID from time, you need an explicit
uncertainty interval and you will wait. Monitor NTP; a drifted
clock looks healthy until it has already dropped writes.
