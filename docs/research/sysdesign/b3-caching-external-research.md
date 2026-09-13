---
type: research
title: 'Caching (aside/through/behind, invalidation, stampede) — external research (2026-09-13)'
description: >-
  Source-verified Group B research for B3: cache-aside / read-through /
  write-through / write-behind, TTL vs explicit invalidation vs versioned
  keys, stampede/dogpile (locks, XFetch, Facebook leases), Redis and
  Memcached eviction defaults, RFC 9111 as a related HTTP layer, and
  hit-rate vs origin-QPS calibration.
tags: [research, system-design-patterns, B3, caching]
---

# Caching — external research (2026-09-13)

> **What this is.** The evidence pass for catalog id **B3** (slug `b3-caching`),
> at the CircuitBreaker.md operational depth bar. This note is research, not a
> Concept. Primary pages fetched **2026-09-13**. Paraphrase; numbers and
> identifiers reproduced exactly. Items that could not be verified are in §8
> and are **not** to be asserted as fact later.
>
> **Owns.** Application / data-plane caches: aside, through, behind;
> invalidation; stampede after expiry *and* after eviction; Redis / Memcached
> eviction defaults; HTTP `Cache-Control` only as a *related* layer.
>
> **Does not own.** Edge / CDN cache keys, `stale-while-revalidate` as a CDN
> product feature, and dynamic acceleration (**B8**). Breaker + cache-down
> fallback loops (**C1**). Serving stale as a degradation mode (**C11**).
> Request–response wire semantics (**A1**).

---

## 1. Scope and non-goals

**This note owns** the cache that sits *next to* an origin (database, service,
or computed view): how the application or cache library reads and writes it,
how entries die (TTL, delete, version bump, eviction), and how a popular key
that expires or is evicted can stampede the origin.

**Non-goals (sibling ids):**

| Id | What they own; do not re-derive here |
|---|---|
| **B8** | CDN / edge: cache keys at the HTTP edge, CDN `stale-while-revalidate`, dynamic acceleration. RFC 9111 is cited here only to mark the boundary. |
| **C1** | Circuit breaker. The cache-down → origin flood → cache cannot refill loop is already in the C1 research (Gabrielson fallback; Bronson look-aside 10×; Slack 2022-02-22). |
| **C11** | Graceful degradation and kill switches — including *deliberately* serving stale while the origin is unhealthy. |
| **A1** | REST / gRPC request–response wire semantics. HTTP caching headers ride on A1 responses; they are not the Redis/Memcached contract. |

**Existing notes to link, not rewrite:** the home-timeline case study (a
materialized derived-data cache) and the performance note (throughput vs
response time; queueing; metastable retry loops) in the main-repo
`cases/data-intensive-design/` tree.

---

## 2. Lineage / vocabulary

Named sources (all fetched 2026-09-13). Mechanics in §3 reuse these facts; do
not treat this list as a second home for the tables.

| Source | Vocabulary / claim that matters |
|---|---|
| Azure **Cache-Aside Pattern** | Commercial caches may offer **read-through** and **write-through / write-behind**. Cache-aside **emulates** read-through: GET cache → miss → GET store → SET cache. On update: write the store, **then** invalidate. That window is **not** write-through (store+cache in one write). https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside |
| Azure **Caching Guidance** | Private vs shared cache; invalidate-on-write vs write-through (both must succeed). Write-through only for read-heavy paths that need read-after-write; else invalidate or bypass. Cache is not the authoritative store. Large startup **seeding** can stampede the origin. Replica lag can re-cache a stale row. AP over C for typical Redis. The page's "`volatile-lru` default" is **Azure Cache for Redis**, not OSS (§4). https://learn.microsoft.com/en-us/azure/architecture/best-practices/caching |
| AWS **Caching patterns** (historical whitepaper) + live **ElastiCache Strategies** | **Cache-aside / lazy loading** (reactive) vs **write-through** (proactive). Write-through is "almost always" paired with lazy loading. Lazy-load miss = three trips; empty replacement node is non-fatal. Write-through: current on write; empty nodes stay empty until the next write; never-read keys bloat RAM. **Adding TTL** is the documented combination. Sample TTL **300 s**. Memcached TTL is seconds; Valkey/Redis may use s or ms. https://docs.aws.amazon.com/whitepapers/latest/database-caching-strategies-using-redis/caching-patterns.html · https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/Strategies.html |
| Ehcache 3 **Writers** | **Write-behind** = async `CacheLoaderWriter` wrapper. Knobs: `queueSize` (then back pressure), `concurrencyLevel` (in-flight = concurrency × queue; × batch size if batched), `enableCoalescing`. Docs' `3` / `1` / `1 s` are **examples**, not defaults. https://www.ehcache.org/documentation/3.9/writers.html |
| Caffeine **Refresh** wiki | In-process read-through. `refreshAfterWrite`: first stale get → async `reload`, **old value returned**. `expireAfterWrite`: entry unusable, **sync** load. Refresh starts only on a query. https://github.com/ben-manes/caffeine/wiki/Refresh |
| Wikipedia **Cache stampede** (oldid 1330515031) | Also **dog-piling**. Hit rate can fall to zero if recompute never finishes. Illustration: **3 s** render × **10 rps** → **30** concurrent recomputes. Families: **locking**, **external recompute**, **probabilistic early expiration**. https://en.wikipedia.org/wiki/Cache_stampede |
| Vattani et al., *PVLDB* 8(8):886–897 (2015) | **XFetch** (verified in the PDF + Wikipedia + `xfetch` crate): `time() - δ·β·ln(rand()) ≥ expiry`. **β = 1** practical default; `δ` = last recompute time. Store `δ` (and expiry if the engine cannot return TTL). https://vldb.org/pvldb/vol8/p886-vattani.pdf |
| Nishtala et al., **Scaling Memcache at Facebook**, NSDI 2013 | **Leases** (64-bit token): block stale sets + herds. Default: one token **per 10 s per key**; others wait. Measured **17K/s → 1.3K/s** peak DB QPS on herd-prone keys. https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf |
| Google SRE book ch. 22 | **Latency cache** (origin can take expected load empty) vs **capacity cache** (cannot — hard dependency). Warm by **slowly increasing load**; keep clusters at nominal load. https://sre.google/sre-book/addressing-cascading-failures |
| Redis **Key eviction** + `redis.conf` | OSS default policy **`noeviction`**. Redis *advice* for Pareto access: **`allkeys-lru`** (not the binary default). LRM in **Redis 8.6.0 (GA 2026-02-10)**. https://redis.io/docs/latest/develop/reference/eviction/ |
| **RFC 9111** (STD 98, June 2022; obsoletes 7234) | HTTP intermediary/UA cache: `max-age`, `no-store`, `no-cache`, `must-revalidate`, `private`/`public`, `s-maxage`. **`stale-while-revalidate` / `stale-if-error` are RFC 5861** (2010), not 9111. RFC 5861 example: `max-age=600, stale-while-revalidate=30`. **B8** owns CDN behavior. https://www.rfc-editor.org/rfc/rfc9111.html · https://www.rfc-editor.org/rfc/rfc5861.html |
| Nygard *Release It!* 2nd ed. | **Dogpile** antipattern (already in C1). Synchronized expiry / close / deploy are the same family. |

---

## 3. Mechanics

### 3.1 The four patterns (and who owns the I/O)

| Pattern | Read path | Write path | Who loads the origin | Freshness after a write | Failure / cost |
|---|---|---|---|---|---|
| **Cache-aside** (lazy loading) | App: GET cache → on miss GET origin → SET cache | App: write origin, then **delete** (or overwrite) the key | Application | Invalidate-on-write: next reader misses (or briefly sees stale if a race re-caches the old store row). Azure: **update the store before deleting the cache key** — delete-first lets a concurrent reader miss, load the *old* store row, and put staleness back. | Miss penalty = cache + origin + cache write (AWS). Only requested keys occupy memory. |
| **Read-through** | App talks only to the cache; the cache/library loads the store on miss | Usually paired with write-through or write-behind | Cache / loader (`CacheLoaderWriter`, Caffeine `LoadingCache`) | Same as whichever write mode is configured | Azure: cache-aside *emulates* this when the cache has no native loader. In-process refresh (Caffeine `refreshAfterWrite`) hides miss latency by serving the old value during reload. |
| **Write-through** | Hit as usual; miss still lazy-loads (AWS: "almost always" combined) | Store **and** cache in the same write; return only after both succeed (Azure) | Cache or application | Readers see the new value after a successful write | Higher write latency; writes of never-read keys bloat the cache (AWS). Empty new nodes stay empty until the next write unless lazy-load is also present. |
| **Write-behind** (write-back) | Same as read-through / aside | Cache (or write buffer) accepts the write; SoR is updated **asynchronously**, optionally batched and coalesced (Ehcache 3) | Cache / writer | Readers of the cache see the write immediately; the SoR lags | Write latency drops; **durability is the SoR lag**. A crash of the cache or an unbounded/lost queue loses acknowledged writes. Ehcache applies **back pressure** when `queueSize` is exceeded. |

**Write-around** is cache-aside's write half (AWS stale-data disadvantage of
lazy loading): the write skips the cache; the next read fills it.

**Trade-off.** Aside is the default because a cache outage degrades to a
slower origin (AWS: node failure is non-fatal) — *if* the origin can take
the miss load (SRE latency cache). Write-through buys read-after-write at
the price of write RTT and cache size. Write-behind buys write throughput
at the price of a durable-queue problem. Read-through moves loader/stampede
policy into the library; aside leaves them at every call site.

### 3.2 Invalidation: TTL vs explicit delete vs versioned keys

Three independent mechanisms; production systems usually combine two.

1. **TTL (time-to-live).** AWS: an integer; expired key is treated as not
   found; does **not** guarantee the value was never stale, only that it
   cannot be *arbitrarily* stale. Azure: too short → perpetual reload; too
   long → long-lived staleness. Best for data that is relatively static or
   frequently read. Synchronized TTLs (every key written at t=0 with the
   same TTL) recreate a stampede at t=TTL — Wikipedia's 30-recompute
   example is exactly that.
2. **Explicit invalidation.** Azure Cache-Aside: after the store write,
   `DEL` the key. Precise, but every writer must know every derived key
   (fan-out of invalidation). Missed invalidation = silent staleness until
   TTL. **Order matters** (store first, then delete).
3. **Versioned / generation keys.** Application convention (not a vendor
   primitive): put a generation in the key (`entity:{id}:v{n}`, or a
   namespace prefix `catalog:v17:...`). Bumping `n` makes old keys
   unreachable; they die by TTL or eviction. Trade-off: **memory** until
   the orphans leave; **readers must agree** on the current generation
   (itself a cached value — a meta-stampede risk). HTTP cache-busting
   query strings are the same idea at the edge — **B8**.

Negative caching is a product decision. Azure's sample **avoids caching
null**. Short-TTL negative entries stop a missing-key stampede but cache
absence through a concurrent create unless invalidation is wired.

### 3.3 Stampede, dogpile, and thundering herd after eviction

A **stampede / dogpile** is many concurrent missers recomputing one key
(Wikipedia). A **thundering herd after eviction** is the same shape with a
different trigger: LRU/LFU under `maxmemory`, a flush, a failover to an
empty node, or a deploy onto a cold process. Facebook's leases exist
because *writes that invalidate* a hot key produce the herd, not only TTL.

**Mitigations (verified families):**

| Family | Mechanism | Trade-off |
|---|---|---|
| **Per-key lock / mutex / single-flight** | One worker recomputes. Wikipedia options for lock losers: wait; return not-found; serve **stale**. Redis idiom: `SET lock:{key} {token} NX PX {ms}` (atomic acquire + TTL so a dead holder releases). Release must be token-checked (Lua compare-and-delete); a bare `DEL` can delete a successor's lock if the first holder overran `PX`. | Extra write; lock-TTL tuning (too short → duplicate compute; too long → stuck miss); lock service is a new dependency. |
| **Leases (Facebook memcache)** | 64-bit token; only the lease holder may `SET`; deletes invalidate the token (blocks stale sets). Token rate-limit **10 s/key** default. Measured **17K → 1.3K** peak DB QPS on herd-prone keys. | Requires cache-server support (or an emulation). Waiters add latency. |
| **Probabilistic early expire (XFetch)** | Independent per-request coin flip; no lock. `β=1` default. Needs `delta` stored with the value. | Some wasted early recomputes; not a hard cap of "exactly one" recompute. Complementary with a lock on the hard miss. |
| **External / refresh-ahead recompute** | A dedicated process refreshes before expiry, periodically, or on miss (Wikipedia). Caffeine `refreshAfterWrite` is the in-process form (triggered by a query, old value served). Azure "background process that periodically updates reference data" is the same family. | Another moving part; fits **static** key sets better than per-id keys (Wikipedia). |
| **Stale-while-revalidate** | Serve stale, refresh in the background. HTTP: RFC 5861 (B8 at the edge). App cache: keep the old value until the single recompute finishes (Wikipedia lock option 3; Caffeine refresh). | Freshness contract is a product decision — **C11** when this is the *degraded* path. |
| **Warm / ramp** | SRE: add load slowly so the first small rate fills the cache; keep clusters at nominal load. Azure: priming at startup; Cache-Aside still needed after expiry/eviction. Seeding a *large* cache can itself stampede the origin. | Warm time vs deploy velocity. A capacity cache that is flushed is an incident, not a toggle. |

TTL **jitter** has no first-party numeric formula in this pass (§8); XFetch
is the sourced probabilistic alternative.

### 3.4 Knobs

| Knob | Role | Too low | Too high |
|---|---|---|---|
| **TTL** | Bound on staleness; also the stampede period if synchronized | Origin QPS ≈ client QPS; cache is ornamental | Long-lived wrong answers; a forgotten invalidation lasts the TTL |
| **Explicit invalidate on write** | Freshness without waiting for TTL | Missed paths → stale | High write fan-out (every derived key) |
| **Generation / version in key** | Cheap "invalidate the world" of a namespace | Readers split across versions | Orphaned keys consume `maxmemory` until eviction |
| **`maxmemory` + policy** | What dies when RAM is full | OOM / write errors (`noeviction` / empty `volatile-*`) | Evicting the hot set → herd (see calibration) |
| **Stampede lock TTL (`PX`)** | Dead-holder safety | Duplicate recomputes | Missers wait on a ghost lock |
| **XFetch `β`, `delta`** | How early refresh starts | Stampede at expiry | Constant early refresh (origin load in the "hit" window) |
| **Facebook lease interval** | Token issue rate (default 10 s/key) | Herd returns | Waiters pile up |
| **Write-behind queue / concurrency / batch / coalesce** | SoR lag vs write RTT (Ehcache 3) | Back pressure on the write path | Lost writes on crash; SoR far behind |
| **Caffeine `refreshAfterWrite` vs `expireAfterWrite`** | Hidden reload vs hard miss | Expire wins → sync load (issue #930 confirmation) | Refresh without expire keeps unused keys forever |

### 3.5 Observability

**Redis `INFO stats` (official eviction docs):**

```
hit_rate = keyspace_hits / (keyspace_hits + keyspace_misses) * 100
```

`EXISTS` reporting absence counts as a miss. Also watch `evicted_keys`,
`expired_keys`, `used_memory_dataset` vs `maxmemory`,
`current_eviction_exceeded_time`, and `commandstats` rejections under
`noeviction` / `volatile-*`. High `evicted_keys` + low hit rate → wrong
policy or undersized cache. High `expired_keys` + low evictions → TTL too
short or wrong keys expiring.

**Memcached:** `stats items` per slab: `evicted`, `evicted_nonzero` (evicted
with a finite expiry), `evicted_time` (seconds since the evicted item was
last fetched — small means you are evicting recently used items). Global
`evictions`. Docs: memcached is **many small caches** (one LRU per slab
class); pages do not move between classes.

**Application-level (needed; Redis keyspace counters are not per prefix):**
hit/miss **by key class**; miss-penalty (p95 miss − p95 hit — ties to the
performance note: measure response time on the client); **origin QPS** next
to cache QPS; stampede signals (lock acquires vs waiters, XFetch early
recomputes, lease "wait" notifications); write-behind queue depth
(Ehcache 2 exposed `getWriterQueueLength`; Ehcache 3: back pressure when
the configured queue is full).

**OpenTelemetry:** no *stable* application-cache semantic convention as of
this fetch. Collector `memcachedreceiver` metrics
(`memcached.operations` with `type=hit|miss`,
`memcached.operation_hit_ratio`) are marked **Development**. GitHub
`open-telemetry/semantic-conventions` issue #1747 proposed `cache.hit` span
attributes — still a proposal. Redis spans today are **database** spans, not
cache spans.

### 3.6 Tuning

Start from **access pattern + freshness contract + origin headroom**, not
from a library default.

- **Pure cache, rebuildable keys:** OSS Redis advice is `allkeys-lru` (or
  `allkeys-lfu` when frequency beats recency). Managed Redis that defaults
  to `volatile-lru` **requires a TTL on every cache key** or it behaves like
  `noeviction` and writes start failing.
- **Mixed persistent + cache keys on one instance:** `volatile-*` (Redis
  docs still prefer two instances). Azure and ElastiCache default here —
  easy to misconfigure as a "cache" that never evicts.
- **Read-hot, write-cold keys (e.g. semantic cache):** Redis 8.6 LRM — LRU
  would keep them forever because reads refresh recency.
- **Stampede on a few hot keys:** lock or lease on that key class only;
  XFetch if lock contention itself is the cost; do not wrap every cheap key.
- **Cold start / failover:** treat as a capacity event (SRE). Ramp traffic;
  prime only the hot set (Azure: seeding the *entire* large cache can be the
  stampede). Pair with C1 so "cache down → query origin" is not an unbounded
  fallback (Gabrielson).
- **In-process + distributed:** Azure: private caches diverge; shorten
  private TTL or invalidate via pub/sub. Caffeine in front of Redis is two
  stampede domains.

### 3.7 Worked calibration — hit rate vs origin QPS

Identity (from the definition of hit rate, and Redis's `INFO` formula):

```
origin_qps ≈ client_read_qps × (1 − hit_rate)
```

A look-aside cache that loses a **90%** hit rate multiplies origin load by
**10×** (Bronson et al., HotOS 2021 — already [7] in
`nfr-references.md`; do not re-derive). That is the capacity-cache
definition from SRE ch. 22.

| Client read QPS | Hit rate | Origin QPS | Notes |
|---|---|---|---|
| 10 000 | 95% | 500 | Origin provisioned for 500 must **not** be expected to absorb a flush. |
| 10 000 | 90% | 1 000 | Bronson's 10×: drop to 0% hit → 10 000 origin QPS. |
| 10 000 | 50% | 5 000 | Cache is already a modest win; stampede protection still matters on the hot keys. |
| 10 000 | 0% (flush / cold) | 10 000 | Empty-node AWS lazy-loading story; SRE "slowly increase the load." |
| Wikipedia example | 1 popular key, 10 rps, 3 s recompute | 30 concurrent origin computes at expiry | Lock/lease/XFetch target this key, not the fleet average. |
| Facebook NSDI 2013 | herd-prone key set | 17 000 → 1 300 peak DB QPS with leases | ~13× peak reduction on that set; not a global SLA. |

**Home timeline (link, do not rewrite):**
`/Users/rajnishkhatri/Code/LLM-DRIVEN-MOBILE-TEST-AUTOMATION/cases/data-intensive-design/home-timeline-case-study.md`
— 10 M online users polling every 5 s = **2 M QPS** × 200 followees =
**400 M** lookups/s; materializing the timeline (derived-data cache) trades
that for ~**1 M** writes/s at 5 800 posts/s × 200 fan-out. Celebrity /
heavy-follow tails are a different workload. Vocabulary:
`/Users/rajnishkhatri/Code/LLM-DRIVEN-MOBILE-TEST-AUTOMATION/cases/data-intensive-design/performance.md`.

**Provisioning rule.** Size the origin for **miss QPS at the worst hit rate
you will actually hit** (deploy, failover, flush, eviction of the hot set),
or classify the cache as a **capacity cache** and engineer warming +
stampede control + a C1/C11 path that does *not* "just hit the database."
Measure p99 of the *client* (performance.md); the mean hit rate hides a
single hot key that is 100% miss for 3 s.

### 3.8 Placement

| Layer | Typical mechanism | State scope | Trade-off |
|---|---|---|---|
| **In-process** (Caffeine, Guava, Ehcache heap) | Read-through / refresh-ahead; TinyLFU / heap LRU | Per process | Lowest latency; Azure: instances diverge; process restart = cold. |
| **Distributed data cache** (Redis, Memcached, ElastiCache, Azure Managed Redis) | Cache-aside by default; write-through in the app; write-behind in a library or queue | Shared (clustered) | Cross-instance consistency of *cached* bytes; network RTT; eviction defaults **differ by vendor** (§4). |
| **Materialized / derived view** | Fan-out on write into a precomputed structure | Per user / per query | Home-timeline case: write amplification for read speed. |
| **HTTP / CDN** | RFC 9111 + RFC 5861 | Browser, proxy, edge | **B8.** Different key space, different invalidation (purge, `s-maxage`). |

---

## 4. Verified defaults / standards (fetched 2026-09-13)

**OSS Redis (`redis.conf` HEAD + eviction docs).**

| Knob | Documented default | Notes |
|---|---|---|
| `maxmemory` | Unset / 0 = **no limit** on 64-bit; **implicit 3 GB** on 32-bit | Eviction does nothing until a limit is set. |
| `maxmemory-policy` | **`noeviction`** | Writes that need memory error; reads continue. |
| `maxmemory-samples` | **5** | Approximated LRU/LFU/LRM sample size; 10 ≈ true LRU, more CPU; max 64. Azure Cache for Redis documents **3**. |
| `maxmemory-eviction-tenacity` | **10** | 0 = min latency, 100 = ignore latency. |
| `lfu-log-factor` | **10** | Saturates the Morris counter around **1 M** requests at factor 10. |
| `lfu-decay-time` | **1** (minute) | 0 = never decay. |
| LRM policies | **Redis 8.6.0, GA 2026-02-10** | `allkeys-lrm`, `volatile-lrm`. |
| `volatile-*` with no TTLs | Behaves like **`noeviction`** | Official: "if no keys have an associated expiration." |
| Replica `maxmemory` | Since Redis 5, replica **ignores** `maxmemory` unless promoted | Eviction is master's job (DEL replicated). |

Policies: `noeviction`, `allkeys-lru`, `allkeys-lfu`, `allkeys-random`,
`allkeys-lrm` (8.6+), `volatile-lru`, `volatile-lfu`, `volatile-random`,
`volatile-ttl`, `volatile-lrm` (8.6+). Replication/AOF buffers are **not**
counted toward `maxmemory` (`mem_not_counted_for_evict`) so eviction does
not fight the replica backlog.

**Managed Redis (different from OSS).**

| Product | `maxmemory-policy` default | Other documented defaults |
|---|---|---|
| **Azure Cache for Redis** | **`volatile-lru`** | `maxmemory-reserved` and `maxfragmentationmemory-reserved` default to **10%** of `maxmemory` each (allowed range 10–60%). `maxmemory-samples` **3**. |
| **ElastiCache Valkey / Redis OSS** | **`volatile-lru`** | `reserved-memory-percent` default **25%** (ElastiCache-specific; AWS: do not reduce). r6gd data-tiering: only `noeviction`, `volatile-lru`, `allkeys-lru`. |

**Memcached.** 1.5.0 (2017-07-21) made `-o modern` the default, including
**segmented LRU** (HOT / WARM / COLD) with a background LRU maintainer.
Pre-1.5: flat doubly-linked LRU, bump on access, evict from tail (search a
few tail items for an expired one first). **TEMP LRU is not default-on**
(Dormando, 2018-10-15). Slab classes: a page assigned to a class never
moves. Eviction when the slab is out of free chunks **and** no free pages
**and** no expired item found in the tail.

**Caffeine.** No default `expireAfterWrite` or `refreshAfterWrite` — both
off until configured. Semantics as §2.

**Ehcache 3 write-behind.** No sourced numeric *default* queue size; the
docs' `3` / `1` / `1 s` are examples. Failed writes are **not** retried by
the wrapper (docs: implement retries in `CacheLoaderWriter`).

**HTTP.** RFC 9111 (June 2022). RFC 5861 extensions are optional (`MAY`
serve stale). A cache **MUST NOT** serve stale under `must-revalidate` /
`no-cache` / applicable `s-maxage` or `proxy-revalidate` (RFC 9111
§4.2.4). `must-revalidate` + disconnected cache → error, **SHOULD** be 504.

**Azure Cache-Aside sample TTL.** **5 minutes** — an example in the
pattern page, not a standard.

**AWS strategies sample TTL.** **300 s** — same caveat.

**Facebook leases.** **10 s** per key between tokens — Facebook's
production default as published, not a Memcached OSS default.

---

## 5. Failure modes and when-not-to-use

**Failure modes of the cache itself**

- **Capacity-cache collapse.** Hit-rate loss × origin overload × timeouts ×
  retries × cache cannot refill (Bronson; Slack 2022-02-22; C1). The
  sustaining loop is the outage, not the flush.
- **"Query the origin if the cache is down."** Gabrielson (AWS Builders'
  Library, *Avoiding fallback*): a 2001 shipping-speed cache whose fallback
  turned a partial outage into a site-wide one. Pair with C1; prefer a
  continuously exercised path.
- **Stampede at TTL, at eviction, at deploy, at failover.** Same shape;
  different trigger. Synchronized TTLs and `FLUSHALL` are self-inflicted.
- **Stale-set / reorder.** Writer A reads old, writer B writes new +
  invalidates, A SETs old. Facebook leases exist for this. Azure
  store-then-delete closes a different race (delete-first).
- **`volatile-*` without TTLs.** Writes fail with OOM; `evicted_keys` stays
  0 — looks healthy.
- **OSS `noeviction` + `maxmemory` on a "cache."** Same OOM-on-write. OSS
  default is this policy; a cache that was never `CONFIG SET` will not evict.
- **Memcached slab imbalance.** 80% of pages in one class starves another;
  per-slab LRU cannot borrow.
- **Write-behind acknowledged, SoR never sees it.** Process crash, queue
  drop, or writer bug. Not a latency cache problem — a durability problem.
- **Private-cache split brain.** Azure diagram: instance A at time X,
  instance B at time Y.
- **Replicated origin + cache-aside.** Populating from a lagging replica
  re-caches the past (Azure).
- **Caching null / not caching null.** Azure sample: do not cache null
  (avoids poisoning). Opposite failure: missing-key stampede.
- **Semantic cache (Azure).** Only when answers are actually equivalent and
  contain no per-user secrets. Wrong hit is a correctness bug, not a miss.

**When not to use (Azure Cache-Aside "not suitable" + this pass)**

- Sensitive / security-related data in a **shared** cache — read the
  primary.
- Static dataset that **fits** — prime once, disable expiry (Azure).
- Hit rate so low that cache + load overhead exceeds a direct origin read.
- Session state that implies **sticky** web-farm affinity (Azure).
- Write-heavy, constantly changing data where synchronization cost exceeds
  the win (Azure guidance).
- Origin already a **latency cache** situation (SRE): if the origin can take
  full load, a capacity cache is optional complexity.
- Write-behind for data you cannot afford to lose.
- HTTP `Cache-Control` as a substitute for Redis invalidation — different
  layer (B8 / A1).

---

## 6. Cross-links

| Target | Why |
|---|---|
| **B8 CDN & edge** | HTTP freshness, CDN keys, `stale-while-revalidate` as an *edge* product. This note stops at RFC 9111 / 5861 as the boundary. |
| **C1 Circuit breaker** | Cache-down fallback, half-open stampede, metastability. Research: `docs/research/sysdesign/circuit-breaker-external-research.md`. Concept: `cases/SystemDesignPatterns/CircuitBreaker.md`. |
| **C11 Graceful degradation** | Serving stale *on purpose* while origin or cache is unhealthy; kill switches that disable a cache class. |
| **A1 Request–response** | `Cache-Control` rides on HTTP responses; it is not the Redis GET/SET contract. |
| **Home timeline case study** | `/Users/rajnishkhatri/Code/LLM-DRIVEN-MOBILE-TEST-AUTOMATION/cases/data-intensive-design/home-timeline-case-study.md` — materialized derived-data cache; fan-out math; celebrity tail. |
| **Performance** | `/Users/rajnishkhatri/Code/LLM-DRIVEN-MOBILE-TEST-AUTOMATION/cases/data-intensive-design/performance.md` — throughput vs response time; percentiles; queueing; retry storms. |
| **nfr-references [7]** | Bronson HotOS 2021 — 90% hit-rate loss → 10× origin. |

---

## 7. Sources

Retrieved 2026-09-13.

**Patterns.** https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside · https://learn.microsoft.com/en-us/azure/architecture/best-practices/caching · https://docs.aws.amazon.com/whitepapers/latest/database-caching-strategies-using-redis/caching-patterns.html · https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/Strategies.html · https://www.ehcache.org/documentation/3.9/writers.html · https://www.ehcache.org/apidocs/3.10.0/org/ehcache/spi/loaderwriter/WriteBehindConfiguration.html · https://github.com/ben-manes/caffeine/wiki/Refresh · https://github.com/ben-manes/caffeine/issues/930

**Stampede.** https://en.wikipedia.org/wiki/Cache_stampede · https://vldb.org/pvldb/vol8/p886-vattani.pdf · https://doi.org/10.14778/2757807.2757813 · https://docs.rs/xfetch/latest/xfetch/ · https://github.com/internetarchive/xfetch · https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf · https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala · https://engineering.fb.com/2013/04/15/core-infra/scaling-memcache-at-facebook/

**Eviction / engines.** https://redis.io/docs/latest/develop/reference/eviction/ · https://github.com/redis/redis/blob/HEAD/redis.conf · https://redis.io/docs/latest/develop/whats-new/8-6/ · https://github.com/redis/redis/releases/tag/8.6.0 · https://learn.microsoft.com/en-us/azure/azure-cache-for-redis/cache-configure · https://learn.microsoft.com/en-us/azure/azure-cache-for-redis/cache-best-practices-memory-management · https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/ParameterGroups.Engine.html · https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/RedisConfiguration.html · https://docs.aws.amazon.com/whitepapers/latest/database-caching-strategies-using-redis/evictions.html · https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/redis-memory-management.html · https://memcached.org/blog/modern-lru · https://github.com/memcached/memcached/wiki/ReleaseNotes150 · https://docs.memcached.org/serverguide/maintenance/ · https://docs.memcached.org/serverguide/performance/ · https://github.com/memcached/memcached/blob/master/doc/protocol.txt

**HTTP / SRE / metastability.** https://www.rfc-editor.org/rfc/rfc9111.html · https://www.rfc-editor.org/rfc/rfc5861.html · https://sre.google/sre-book/addressing-cascading-failures · https://sre.google/sre-book/reliable-product-launches · https://sigops.org/s/conferences/hotos/2021/papers/hotos21-s11-bronson.pdf

**OTel (negative result).** https://github.com/open-telemetry/semantic-conventions/issues/1747 · https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/receiver/memcachedreceiver/documentation.md

---

## 8. Uncertain / left out

- Azure Cache-Aside and Caching Guidance **`ms.date` / last-updated** banners were not present in the fetched HTML; pages were live 2026-09-13.
- AWS Redis caching-patterns whitepaper is marked **historical**; live ElastiCache Strategies page was used as the current twin. The Strategies URL title says "Memcached" but the TTL paragraph discusses Valkey/Redis OSS as well.
- **TTL jitter formulas** (e.g. "±20% of TTL") appear in secondary posts only; no Azure / AWS / Redis / SRE numeric jitter default was found. Not asserted.
- **Versioned keys** as a named vendor pattern: described as an application convention; no first-party "do this" page with a default scheme.
- Redis official **cache-stampede** page: community/antirez mirrors exist; not treated as current redis.io product docs.
- Whether **Ehcache 3 persists** the write-behind queue across process death — not stated on the writers page; durability risk is asserted only as the generic async-write hazard.
- **Caffeine latest registry version** as of 2026-09-13 not pinned; refresh/expire *semantics* taken from the wiki + issue #930, which are version-stable.
- **golang.org/x/sync/singleflight** and Redis `SET` NX/PX command page: lock *shape* is industry-standard; this pass did not re-fetch those two primary pages (Facebook leases and Wikipedia locking are the sourced lock family).
- OpenTelemetry cache span `cache.hit` — **proposal only** (issue #1747).
- Azure "semantic caching" guidance is product-adjacent (LLM gateways); no numeric hit-rate claim.
- No controlled public experiment isolating **close-time / deploy-time** herd size beyond Facebook's 17K→1.3K lease study and Wikipedia's 30-recompute illustration.
- Valkey-vs-Redis eviction drift beyond ElastiCache's published parameter table was not independently audited.
- Home-timeline 5 800 posts/s and 150 000 spike figures are **book figures** in that case study, not measurements from this workspace.
