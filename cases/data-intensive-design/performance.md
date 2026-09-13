---
type: analysis
title: 'Describing performance'
description: 'Throughput sets capacity and cost; response time is what the client sees. Report percentiles, never average them. Queueing links the two metrics.'
tags: [data-intensive-design, nfr, performance, latency, percentiles, slo]
---

# Describing performance

**See also:** [NFR overview](nfr-overview.md) · [home timelines](home-timeline-case-study.md) · [scalability](scalability.md) · [NFR references](nfr-references.md)

Most discussions of software performance consider two main metrics:

**Response time.** Elapsed time from the moment a user makes a request until
they receive the answer. Unit: seconds (or milli-/microseconds).

**Throughput.** Requests per second, or data volume per second, that the system
is processing. For a given allocation of hardware, there is a maximum
throughput. Unit: “somethings per second.”

In the [timeline case study](home-timeline-case-study.md), posts/second and
timeline writes/second are throughput; time to load a home timeline and time
until a post is delivered are response times.

The two are related. An online service typically has low response time when
request throughput is low; response time increases as load increases because of
**queueing**. When a request arrives on a highly loaded system, the CPU is
often already handling an earlier request, so the incoming request waits. As
throughput approaches the maximum the hardware can handle, queueing delays
increase sharply.

## When an overloaded system won’t recover

If a system is close to overload, it can enter a vicious cycle where it becomes
less efficient and hence even more overloaded. A long queue makes response
times so large that clients time out and **resend**, which increases the
request rate further — a **retry storm**. Even after load is reduced, the
system may stay overloaded until it is rebooted or otherwise reset. That is a
**metastable failure**, and it causes serious production outages
([7](nfr-references.md), [8](nfr-references.md), [9](nfr-references.md)).

Mitigations:

- Increase and randomize time between client retries (**exponential backoff**
  ([10](nfr-references.md), [11](nfr-references.md)))
- Temporarily stop sending to a service that has recently errored or timed out
  (**circuit breaker** ([12](nfr-references.md), [13](nfr-references.md)) or
  **token bucket** ([14](nfr-references.md)))
- Server detects approaching overload and **rejects** requests (**load
  shedding** ([15](nfr-references.md))) or asks clients to slow down
  (**backpressure** ([1](nfr-references.md), [16](nfr-references.md)))
- Queueing and load-balancing algorithm choice also matters
  ([17](nfr-references.md))

Users care most about response time. Throughput determines required computing
resources and hence **cost**. If throughput is likely to grow beyond current
hardware, capacity must expand; a system is **scalable** if its maximum
throughput can be significantly increased by adding computing resources (see
[scalability](scalability.md)).

## Latency and response time

“Latency” and “response time” are sometimes used interchangeably. These notes
use them specifically:

| Term | Meaning |
|---|---|
| **Response time** | What the client sees; includes all delays anywhere in the system |
| **Service time** | Duration for which the service is actively processing the request |
| **Queueing delay** | Waiting for a CPU, or for an outbound network buffer, etc. |
| **Latency** | Catch-all for time the request is *not* being actively processed (it is latent). **Network latency** / **network delay** is time spent traveling through the network |

Response time can vary significantly from one request to the next, even for the
same request repeated. Random delays include a context switch to a background
process, a lost packet and TCP retransmission, a garbage-collection pause, a
page fault forcing a disk read, or mechanical vibration in the rack
([18](nfr-references.md)).

Queueing delays often account for a large part of that variability. A server
can process only a small number of things in parallel (limited, for example, by
CPU cores). A small number of slow requests can hold up subsequent requests —
**head-of-line blocking**. Even if later requests have fast service times, the
client sees a slow overall response time. Queueing delay is **not** part of
service time, which is why response times must be measured **on the client
side**.

## Average, median, and percentiles

Because response time varies, treat it as a **distribution**, not a single
number. Most requests are reasonably fast; occasional outliers take much
longer. Variation in network delay is also called **jitter**.

The **average** (arithmetic mean: sum of response times divided by request
count) is useful for estimating throughput limits ([19](nfr-references.md)). It
is a poor metric for “typical” user experience, because it does not tell you
how many users actually experienced that delay.

**Percentiles** are usually better. Sort response times from fastest to
slowest. The **median** is the halfway point: if median response time is
200 ms, half of requests return in less than 200 ms and half take longer. The
median is the **50th percentile** (**p50**).

To see how bad the outliers are, look at higher percentiles: **p95**, **p99**,
**p999** (99.9th). If p95 is 1.5 seconds, 95 of 100 requests take less than
1.5 s, and 5 take 1.5 s or more.

High percentiles — **tail latencies** — directly affect user experience.
Amazon has described internal-service requirements in terms of the 99.9th
percentile, even though that is 1 in 1,000 requests: the slowest requests are
often the customers with the most data on their accounts — the most valuable
customers ([20](nfr-references.md)). Optimizing the 99.99th percentile (1 in
10,000) was deemed too expensive and not worth the benefit for Amazon’s
purposes. Very high percentiles are easily affected by random events outside
your control, and the benefits diminish.

### The user impact of response times

A fast service is better for users than a slow one ([21](nfr-references.md)),
but reliable data quantifying latency’s effect on behavior is surprisingly
hard to get.

Some often-cited statistics are unreliable. In 2006 Google reported that a
slowdown from 400 ms to 900 ms was associated with a 20% drop in traffic and
revenue ([22](nfr-references.md)). A 2009 Google study reported that a 400 ms
increase resulted in only 0.6% fewer searches per day
([23](nfr-references.md)); the same year Bing found a two-second increase in
load time reduced ad revenue by 4.3% ([24](nfr-references.md)). Newer data from
these companies appears not to be public.

An Akamai study claimed a 100 ms increase reduced ecommerce conversion by up
to 7% ([25](nfr-references.md)); the same study also found very fast loads
correlated with *lower* conversion — often 404 pages with no useful content.
The study did not separate page content from load time, so the result is
probably not meaningful.

A Yahoo study compared click-through on fast vs slow search results,
controlling for result quality ([26](nfr-references.md)): 20%–30% more clicks
on fast searches when the difference was 1.25 seconds or more.

## Use of response-time metrics

High percentiles matter especially in backend services called **multiple
times** as part of one end-user request. Even in parallel, the request waits
for the **slowest** call. One slow call makes the whole request slow. Even if
only a small percentage of backend calls are slow, the chance of hitting one
rises with the number of calls — **tail latency amplification**
([27](nfr-references.md)).

Percentiles are often used in **service level objectives (SLOs)** and
**service level agreements (SLAs)** to define expected performance and
availability ([28](nfr-references.md)). Example SLO: median response time under
200 ms, p99 under 1 second, and at least 99.9% of valid requests returning
non-error responses. An SLA is a contract for what happens if the SLO is not
met (e.g. a refund). Defining good availability metrics is not straightforward
in practice ([29](nfr-references.md), [30](nfr-references.md)).

### Computing percentiles

To put percentiles on dashboards, calculate them on an ongoing basis — for
example a rolling 10-minute window, plotted every minute.

The simplest implementation keeps a list of response times in the window and
sorts it every minute. If that is too expensive, approximation algorithms exist
at modest CPU and memory cost: HdrHistogram ([31](nfr-references.md)), t-digest
([32](nfr-references.md), [33](nfr-references.md)), OpenHistogram
([34](nfr-references.md)), DDSketch ([35](nfr-references.md)).

**Averaging percentiles** (to reduce time resolution or to combine machines) is
mathematically meaningless. Aggregate response-time data by **adding
histograms** ([36](nfr-references.md)).

**Architect takeaway:** measure response time at the client; use p50 for
typical experience and p99/p999 for the tail. Use the mean for capacity
planning, not for “how it feels.” Never average percentiles — merge
histograms. Design for queueing and retry storms before the system is at
capacity, not after.
