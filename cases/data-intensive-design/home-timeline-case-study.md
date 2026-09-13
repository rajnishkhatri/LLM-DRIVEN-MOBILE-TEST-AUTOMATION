---
type: analysis
title: 'Case study — social network home timelines'
description: 'Fan-out and materialized timelines trade write amplification for read speed. Average-case math fails on celebrities and heavy follow graphs.'
tags: [data-intensive-design, nfr, case-study, fan-out, materialization]
---

# Case study — social network home timelines

**See also:** [NFR overview](nfr-overview.md) · [performance](performance.md) · [scalability](scalability.md) · [systems of record vs derived data](operational-vs-analytical.md#systems-of-record-and-derived-data) · [hot spots](sharding-hot-spots.md) · [NFR references](nfr-references.md)

A simplified social network in the style of X (formerly Twitter): users post
messages and follow other users. This is a huge simplification of how such a
service actually works ([1](nfr-references.md), [2](nfr-references.md),
[3](nfr-references.md)), but it illustrates issues that arise in large-scale
systems.

Assumed load (book figures, not measurements from this workspace):

- 500 million posts per day, or **5,800 posts per second** on average
- Occasional spikes to **150,000 posts per second** ([4](nfr-references.md))
- Average user follows 200 people and has 200 followers, with a very wide
  range: most people have a handful of followers; a few celebrity accounts have
  over 100 million

## Representing users, posts, and follows

A simple relational schema: one table for users, one for posts, one for follow
relationships.

The main read is the **home timeline**: recent posts by people the user is
following (ignoring ads and suggestions). One SQL shape:

```sql
SELECT posts.*, users.* FROM posts
  JOIN follows ON posts.sender_id = follows.followee_id
  JOIN users   ON posts.sender_id = users.id
  WHERE follows.follower_id = current_user
  ORDER BY posts.timestamp DESC
  LIMIT 1000
```

The database uses `follows` to find everybody `current_user` is following,
looks up recent posts by those users, and sorts by timestamp.

Posts are supposed to be timely: after somebody posts, followers should see it
within **five seconds**. One approach is for the client to repeat the query
every five seconds while online (**polling**). If 10 million users are online,
that is **2 million queries per second**. Even polling less often, this is a
lot.

The query is also expensive. If a user follows 200 people, it fetches recent
posts from each of those 200 and merges them. Two million timeline queries per
second × 200 followed accounts = **400 million lookups per second** in the
average case. Some users follow tens of thousands of accounts; for them the
query is very expensive and hard to make fast.

## Materializing and updating timelines

Two improvements:

1. Instead of polling, the server **pushes** new posts to followers who are
   currently online.
2. **Precompute** the query so a home-timeline request is served from a cache.

For each user, store a data structure containing their home timeline (recent
posts by people they follow). Every time a user posts, look up all their
followers and insert that post into each follower’s home timeline — like
delivering a message to a mailbox. When a user logs in, give them this
precomputed timeline. To notify them of new posts, the client subscribes to the
stream of posts being added to their home timeline.

The downside: more work on every post, because home timelines are **derived
data** that must be updated (see [systems of record vs derived
data](operational-vs-analytical.md#systems-of-record-and-derived-data)). When
one initial request results in several downstream requests, **fan-out** is the
factor by which the number of requests increases.

At 5,800 posts per second and a fan-out factor of 200, that is just over
**1 million home-timeline writes per second**. Still a significant saving
compared with 400 million per-sender lookups per second.

If the post rate spikes because of a special event, timeline deliveries need
not happen immediately — enqueue them and accept that posts take longer to
show up. Even during spikes, timelines remain fast to load, because they are
served from a cache.

This precompute-and-update process is **materialization**; the timeline cache
is a **materialized view**. It speeds up reads; in return we do more work on
writes. Cost is modest for most users, but a social network has extreme cases:

- If a user follows a very large number of high-volume accounts, their
  materialized timeline has a high write rate. They are not likely reading
  every post, so it can be acceptable to **drop some timeline writes** and show
  only a sample ([5](nfr-references.md)).
- When a celebrity with millions of followers posts, dropping writes is **not**
  OK. One approach is to handle celebrity posts separately: store them apart
  and merge them with the materialized timeline at read time, rather than
  inserting into millions of timelines. Even with that optimization, celebrities
  can require a lot of infrastructure ([6](nfr-references.md)).

In performance terms: “posts per second” and “timeline writes per second” are
**throughput**; “time to load the home timeline” and “time until a post is
delivered” are **response times**. See [describing performance](performance.md).

**Architect takeaway:** the average-case design (fan-out on write into a
materialized timeline) is a derived-data cache. The architecture has to name
the tails — heavy follow graphs and celebrity fan-out — and treat them as
different workloads, not as the same query with worse constants.
