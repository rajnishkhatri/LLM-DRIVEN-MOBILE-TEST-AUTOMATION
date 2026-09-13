---
type: research
title: 'Publisher–subscriber, queues & streams — external research (2026-09-13)'
description: >-
  Source-verified Group A note on broker vs mediator, queues vs topics vs
  logs, delivery claims (Kafka / SQS / Pub/Sub / RabbitMQ / SNS / Service
  Bus), competing consumers, fan-out, ordering, DLQ, consumer groups,
  reconnect, poison messages, and proxy/LB interactions.
tags: [research, system-design-patterns, A2, pubsub, queues, streams]
---

# Publisher–subscriber, queues & streams — external research (2026-09-13)

> **What this is.** The evidence pass for catalog id **A2** (Group A — Communication). Mechanisms live here; **E4** is style-level event-driven architecture only. Owner note already in the tree — link, do not rewrite: [event-driven-dataflow](../../../cases/data-intensive-design/event-driven-dataflow.md) (main repo: `cases/data-intensive-design/event-driven-dataflow.md`).
>
> **Method.** Vendor and canon pages fetched 2026-09-13. Kafka numbers are from the 4.1 configuration pages (`kafka.apache.org/41/configuration/{producer,consumer,broker}-configs/`); latest stable Kafka on the downloads page that day was **4.3.1** (released 2026-06-25). 4.3 consumer-config pages still default `group.protocol=classic` with the same session / poll / isolation numbers cited below. Everything is paraphrase; identifiers and defaults are reproduced exactly. Items that could not be verified are in §8 and are **not** to be implied as fact.

---

## 1. Scope and non-goals

**Owns.** Wire semantics of queues, topics, and append-only logs/streams; broker vs mediator; at-most-once / at-least-once / exactly-once *as vendors actually state them*; competing consumers vs fan-out; partition / group / session ordering; dead-letter channels (SQS, SNS, Kafka Connect, RabbitMQ DLX, Pub/Sub DLT, Service Bus); consumer-group and session lifecycle; reconnect and poison-message behaviour; proxy and load-balancer interactions; verified defaults; when-not-to-use.

**Does not own.**

| Sibling | Why it stays there |
|---|---|
| **A1** request–response | Sync REST/gRPC call/reply. Pub/sub reply channels are named here only as the Azure *Request-Reply* escape hatch. |
| **B7** transactional outbox / CDC | How a write becomes an event *atomically*. A2 starts once the event is on a channel. |
| **B5** saga | Multi-step compensation over these channels. |
| **C9** idempotency | How a consumer survives the duplicates A2's at-least-once path *will* produce. |
| **C10** backpressure / load shedding | Broker flow-control knobs are named; the policy lives in C10. |
| **E4** event-driven style | Style, quanta, migration. Mechanisms stay here. |
| **E12** CQRS / event sourcing | Retention-forever logs as a source of truth — pointer only. |

The existing [event-driven-dataflow](../../../cases/data-intensive-design/event-driven-dataflow.md) note already states the broker's job (buffer, redeliver, hide addresses, fan-out, decouple) and the queue-vs-topic table. This note verifies vendor claims around those two rows and adds the log/stream third row, delivery guarantees, and the Group A connection/LB bar.

---

## 2. Lineage / vocabulary

**Hohpe & Woolf, *Enterprise Integration Patterns* (Addison-Wesley, 2003).** The vocabulary this catalog inherits:

- **Point-to-Point Channel** — one consumer receives each message. **Competing Consumers** (same book) are multiple receivers on that channel; the implementation picks a winner. Extra consumers on a *Publish-Subscribe Channel* just make more copies.
- **Publish-Subscribe Channel** — one input splits into one output channel per subscriber; each subscriber consumes its copy once.
- **Dead Letter Channel** — where the system puts a message it cannot or should not deliver. The web pattern page adds modern examples (SQS `maxReceiveCount`; Kafka Connect sink DLQ).
- **Message Broker** — hub-and-spoke *architecture* pattern: a central component receives, routes, and (typically) transforms so senders do not name destinations. Hohpe's ch. 3 extract (PDF on enterpriseintegrationpatterns.com) calls it **the integration equivalent of the GoF Mediator**. The 2003 rambling *Hub and Spoke* adds protocol translation and a Message Translator; without translation, location transparency is an illusion.
- **Message Bus** — a shared infrastructure plus a common command set and (usually) a canonical data model. Participants speak the bus; the bus is not an active per-message mediator.

**Broker vs mediator, operationally.** A *dumb broker* (Kafka log, SQS standard queue) stores and forwards bytes; routing is key/partition or “whoever receives.” A *mediating broker* (classic EAI broker, RabbitMQ with bindings and content routers, SNS filter policies, Service Bus SQL filters) inspects and decides. Trade-off: the mediator centralises routing and becomes a change hotspot and a throughput bottleneck (Hohpe's own warning); the dumb broker pushes routing into keys, consumer groups, and application code. Products mix both — SNS is a mediating fan-out in front of dumb SQS queues.

**Azure Architecture Center, “Publisher-Subscriber” and “Competing Consumers”** (fetched 2026-09-13). Azure's distinction is the same as Hohpe's: competing consumers = one consumer per message on a queue; pub/sub = every subscriber gets a copy. A *subscription* is itself a queue and can have competing consumers. Azure's when-not-to-use list is the one used in §5.

**Kleppmann / this tree.** [event-driven-dataflow](../../../cases/data-intensive-design/event-driven-dataflow.md) already records: brokers buffer and redeliver; they do not enforce a data model; many *delete after consume*; some retain indefinitely (required for event sourcing). [distributed-transactions.md](../../../cases/data-intensive-design/distributed-transactions.md) already owns the “exactly-once processing” construction (idempotent consumer + ack-after-commit) and names Kafka Streams. Do not re-derive either.

**Jay Kreps (2015)** — “Putting Apache Kafka to Use” ([22] in encoding-references): the log as a durable, replayable, multi-subscriber stream. That is the third distribution pattern next to queue and topic.

---

## 3. Mechanics (Group A depth bar)

### 3.1 Three channel kinds (queues vs topics vs logs)

| Kind | Delivery | After consume | Scale-out unit | Fan-out |
|---|---|---|---|---|
| **Queue** (SQS, Service Bus queue, RabbitMQ queue) | One consumer per message (competing consumers share work) | Typically deleted / acked away | More consumers (and, for FIFO, more group IDs) | None — add a topic or a fan-out exchange in front |
| **Topic / pub-sub** (SNS, Service Bus topic, RabbitMQ fanout/topic exchange, Pub/Sub topic) | Every *subscription* gets a copy | Per-subscription queue semantics | More subscriptions (fan-out) and more consumers *per* subscription | First-class |
| **Log / stream** (Kafka topic, Azure Event Hubs) | Consumer *groups* independently replay the same log; within a group, partitions are exclusive | Offset advances; records stay until retention | Partitions; consumers in a group **cannot usefully exceed partition count** (EIP Kafka example, fetched 2026-09-13) | Extra consumer groups, not extra copies at produce time |

A Pub/Sub *subscription* is Hohpe's output channel: two subscriptions = pub/sub; two pullers on *one* subscription = competing consumers (EIP's own GCP example). Kafka inverts that: one topic + N groups = pub/sub; one group + N members = competing consumers *per partition*, not per message.

### 3.2 Wire semantics and connection lifecycle

Four on-the-wire shapes. Do not treat them as interchangeable “messaging.”

**Kafka protocol (persistent TCP, broker-aware).** Client bootstraps from `bootstrap.servers`, fetches metadata, then opens **per-broker** connections to the leaders named in `advertised.listeners`. Produce and fetch are request/response on those sockets; the consumer-group coordinator is a specific broker. Idle: client `connections.max.idle.ms` **540000 (9 minutes)**; broker **600000 (10 minutes)**. Reconnect: `reconnect.backoff.ms` **50**, `reconnect.backoff.max.ms` **1000**, plus **20% jitter** on the max (4.1 consumer configs). Classic group protocol (default `group.protocol=classic` on 4.1 and 4.3 pages): heartbeat **3000 ms**, session **45000 ms**, `max.poll.interval.ms` **300000 (5 minutes)**. If `poll()` is late, the member is failed and partitions reassigned (static members with `group.instance.id` wait out the session timeout first). The new `group.protocol=consumer` (opt-in since 4.0; KIP-1274 proposes flipping the default later) moves heartbeat/session to broker configs (`group.consumer.session.timeout.ms` default still **45000**). `enable.auto.commit` defaults **true** every **5000 ms** — that is *at-most-once* if you process after the commit, *at-least-once* if you process before it and crash.

**AMQP 0-9-1 (RabbitMQ).** Long-lived TCP → protocol negotiate → authenticate → **channels** multiplexed on one connection (channel max negotiated). Consume is push (`basic.consume`) or get. Heartbeat timeout **suggested default 60 s**, frames about every `timeout/2`; two missed heartbeats close the TCP connection; the client must reconnect and re-open channels (RabbitMQ *Connections* and *Heartbeats*, fetched 2026-09-13). Automatic ack = at-most-once (broker forgets on deliver). Manual ack = at-least-once (redeliver on channel/connection death). Prefetch (`basic.qos`) caps unacked deliveries; quorum queues reject global QoS and cap prefetch at **2000**.

**AMQP 1.0 (Service Bus; RabbitMQ also speaks it).** Connection → session → link. Service Bus peek-lock is a broker-side lease: default **lock duration 1 minute**, max **5 minutes**, renewable; settlement (complete / abandon / defer / dead-letter) is tied to **that receiver and connection**. Docs (fetched 2026-09-13): close the receiver before settle and the settlement never arrives; the lock expires; delivery count increments; repeated hits → DLQ `MaxDeliveryCountExceeded`. The service **closes an idle connection after 10 minutes**.

**HTTPS / gRPC APIs (SQS, SNS, Pub/Sub).** No AMQP session. SQS `ReceiveMessage` + optional long poll (`WaitTimeSeconds`); visibility timeout is the lease (default **30 s**, max **12 h** from first receive). SNS *pushes* (HTTP POST, SQS send, Lambda invoke). Pub/Sub: pull, **streaming pull** (long-lived gRPC), or **push** (HTTPS POST to your endpoint). Ack deadline default **10 s**, min 10, max **600 s**; `ModifyAckDeadline` extends it. Push uses the ack deadline as the HTTP request timeout.

### 3.3 Delivery claims — what the vendors actually guarantee

The three textbook words do not mean the same thing on each product. **Exactly-once of an external side effect is C9 + B7, not a broker switch.**

| Product | Vendor wording | What a fetch of the primary page actually says | Default if you change nothing |
|---|---|---|---|
| **Kafka produce** | Idempotent producer writes “exactly one copy” | `enable.idempotence` default **true** (4.1); requires `acks=all` (default **all**), `retries>0`, `max.in.flight.requests.per.connection≤5` (default **5**). Dedup is `(producerId, epoch, sequence)` **per partition, per producer session**. Not a cross-system EOS. | Idempotent produce on; **no** transactions (`transactional.id` unset) |
| **Kafka consume–transform–produce** | “Exactly-once semantics” (KIP-98 / Streams `exactly_once_v2`) | Atomic write of output records **and** input offsets in one transaction; fencing via `transactional.id`. Consumers must set `isolation.level=read_committed` or they see aborted records. Default isolation is **`read_uncommitted`**. Side effects outside Kafka are not in the transaction. | At-least-once (auto-commit + read_uncommitted) |
| **SQS standard** | At-least-once; best-effort order | FAQ (fetched 2026-09-13): each message is delivered at least once; occasionally a duplicate; order not guaranteed. Visibility timeout is **not** an exclusive lock against a second delivery. | At-least-once, unordered |
| **SQS FIFO** | “Exactly-once processing” | FAQ: duplicates are **not introduced into the queue**; producer retries inside a **5-minute** `MessageDeduplicationId` window are collapsed (or content-hash if that feature is on). The message stays until `DeleteMessage`. **Visibility timeout expiry still redelivers** to a consumer (FIFO “Preventing duplicate processing” page). That is *producer-side dedup + at-least-once consume*, not end-to-end EOS. | Dedup window 5 min; consume still leases |
| **Pub/Sub (default)** | At-least-once | Redelivery on expired ack deadline or nack. Ordering off unless `enableMessageOrdering` + `orderingKey`. | At-least-once, unordered |
| **Pub/Sub “exactly-once delivery”** | Named feature, default **false** | Official page: for a given `messageId`, no resend *before* the ack deadline expires, and an **acknowledged** message is not resent. **Publisher retries create new `messageId`s** and are distinct. Combined with ordering, acks must be in order or the service fails them with temporary errors; throughput “an order of thousands of messages per second.” | Off |
| **RabbitMQ** | Manual ack = at-least-once | Unacked messages return on consumer death. Auto-ack = at-most-once. DLX default republish is **at-most-once** (no publisher confirms); quorum queues offer opt-in `dead-letter-strategy=at-least-once`. | Classic: at-most-once DLX |
| **SNS** | Push with retries, then drop or DLQ | AWS-managed (SQS/Lambda): **100,015** attempts over **23 days**. HTTP/S: customisable; example policy **50** attempts; total retry time **≤ 3600 s** hard cap. 5xx and 429 retry; other HTTP is permanent failure. After the policy, the message is discarded unless the *subscription* has a DLQ. | No subscription DLQ |

`acks=0` is the Kafka at-most-once produce path (no server ack, retries do not apply). `acks=1` can lose the record if the leader dies before followers catch up. `acks=all` waits for the ISR; `min.insync.replicas` default **1** (so `acks=all` with RF=3 and minISR=1 still accepts a lone leader). `unclean.leader.election.enable` default **false**.

### 3.4 Competing consumers, fan-out, ordering

**Competing consumers.** Azure: multiple workers pull one queue; each message is processed by one worker; the queue is the load-leveler. Kafka: EIP's Kafka example is explicit that members of a group do **not** compete per message — a router (the key) pins a record to a partition, and the assignor pins that partition to one member. A slow partition cannot be helped by an idle member. **Hard cap:** consumers-in-group ≤ partitions. SQS FIFO: one in-flight batch per `MessageGroupId`; other groups proceed in parallel. Service Bus sessions: accepting a session takes an exclusive lock on that `SessionId` (and later arrivals with it).

**Fan-out.** SNS topic → N subscriptions (SQS, Lambda, HTTP/S, Firehose, SMS, email). Quotas page (fetched 2026-09-13): **12,500,000** subscriptions per *standard* topic; FIFO topic subscription cap is **100**; standard topics **100,000** / account, FIFO topics **1,000** / account. Pub/Sub: N subscriptions per topic; each is an independent cursor. Kafka: N consumer groups, each with its own offsets — the log is not copied at produce time. RabbitMQ: a fanout/topic exchange plus a queue per subscriber.

**Ordering.** Kafka: **total order per partition only**. Key → partition (unless a custom partitioner). Cross-partition order is not a Kafka guarantee. SQS standard: best-effort / “loose FIFO.” SQS FIFO: order **per `MessageGroupId`**; a batch may include several groups, but a group is blocked until its in-flight messages are deleted or become visible. Pub/Sub: same `orderingKey`, **same publish region**, subscription `enableMessageOrdering=true`; redelivery of message *k* redelivers *k+1…* for that key (unless a dead-letter topic is also on — then the docs say the behaviour “might not be true,” best-effort). Service Bus: FIFO is **sessions**, not the default queue. Azure Publisher-Subscriber: “order … isn't guaranteed”; ordered delivery “constrains scalability.”

**Poison messages.** A payload that crashes every consumer. Without a receive-count cap it loops forever (queue) or stalls a partition/session (Kafka / FIFO / Service Bus sessions). DLQ is the isolation mechanism; C9 (idempotency) does not help a message that *cannot* be applied.

### 3.5 Dead-letter channels (verified)

**SQS.** Redrive policy: `maxReceiveCount` on the source; destination DLQ must be **same account and Region** and the **same type** (standard↔standard, FIFO↔FIFO). After `ReceiveCount > maxReceiveCount`, SQS moves the message (original message id). **Do not attach a DLQ to a FIFO queue if you need exact order** — AWS's own warning (EDL / video-edit example). Standard: enqueue timestamp is **kept** on the move, so DLQ retention must be **longer** than the source or the message dies early. FIFO: enqueue timestamp **resets** on the move. Standard queues with `maxReceiveCount > 3` move a 3×-received message to the back of the source before DLQ. Default redrive-allow policy: all sources may use the DLQ.

**SNS.** DLQ is on the **subscription**, not the topic (delivery happens per subscription). Target is an SQS queue of the matching type; SNS needs `sqs:SendMessage` on it. This catches *delivery* failure after the retry policy, **not** consumer processing failure — that needs a second DLQ on the subscribed SQS queue. Recommended SQS retention on the DLQ: **14 days** (SNS docs).

**Kafka Connect (KIP-298, Kafka 2.0+; sink only).** Defaults from the KIP and the Connect user guide: `errors.tolerance=none` (fail the task), `errors.retry.timeout=0`, `errors.deadletterqueue.topic.name=""` (disabled), `errors.deadletterqueue.topic.replication.factor=3`, `errors.deadletterqueue.context.headers.enable=false`. The DLQ receives the **original consumed record** that failed in converter / SMT / sink. **Source connectors have no framework DLQ.** Application consumers have no broker-native DLQ — Spring Kafka's `DeadLetterPublishingRecoverer` → `<topic>-dlt` is an application convention (already cited from the circuit-breaker research note).

**RabbitMQ DLX.** Triggers: `basic.reject`/`nack` with `requeue=false` (or AMQP 1.0 `rejected`); per-message TTL; queue length overflow; quorum `delivery-limit`. A whole-queue expiry does **not** dead-letter. Default republish is **without** publisher confirms (lossy if the target cannot accept). Quorum opt-in: `dead-letter-strategy=at-least-once` **and** `overflow=reject-publish` **and** a configured DLX; internal consumer prefetch default **32**. Cycle detection drops a looping message if the cycle had no rejection. Missing DLX at dead-letter time = **silent drop**. Reasons recorded in `x-death` / `x-opt-deaths`: `rejected`, `expired`, `maxlen`, `delivery_limit`.

**Pub/Sub dead-letter topic.** Set on the **subscription**. `maxDeliveryAttempts` **5–100**, default **5** (0 in the API means 5). Count is approximate; forwarding is **best-effort** (may go early or late). Needs a subscription on the DLT or the forwarded message is lost (topic-with-no-subscribers). Service account must be able to publish to the DLT. Combined with ordering, DLT writes may **break** key order.

**Service Bus.** Every queue and subscription has a `$deadletterqueue` subqueue (not created separately; no TTL on it; cannot dead-letter *from* the DLQ). Default `MaxDeliveryCount` **10**, not disableable. System reasons: `MaxDeliveryCountExceeded`, `TTLExpiredException` (if dead-letter-on-expiration is on; otherwise drop), `HeaderSizeExceeded`, `Session ID is null`, `MaxTransferHopCountExceeded` (auto-forward hop cap **4**). Transfer failures land on `$Transfer/$DeadLetterQueue` of the **source**. No automatic DLQ cleanup.

### 3.6 Proxy / load-balancer interactions

**Kafka is allergic to a naive L4 VIP.** Clients must dial the **advertised** host of the leader, not “any broker.” A load balancer that (a) hides brokers behind one address, (b) picks a random backend per connection, or (c) idles out TCP before Kafka does, produces `NETWORK_EXCEPTION` / connection-reset mid-request. Official broker config: `advertised.listeners` “can be useful in some cases where external load balancers are used” — that is *advertise the LB address of that broker*, not *share one pool*. Align timeouts: broker idle **10 min**, client idle **9 min**; many cloud LBs idle at **60–350 s**. Either raise the LB idle or lower `connections.max.idle.ms` so the *client* recycles first. Azure Event Hubs' Kafka surface is the documented case of an LB that silently drops idle sockets (librdkafka #3109: set `connections.max.idle.ms` below the Azure timeout; a commonly cited value is **3 m 30 s**).

**RabbitMQ / AMQP.** Heartbeats exist in part to keep proxies from classifying the socket as idle. Official guidance: activity in the **5–15 s** range “satisfies the defaults of most popular proxies and load balancers”; a 30 s heartbeat timeout produces traffic ~every 15 s. HAProxy / AWS ELB / hardware LBs are named. TCP keepalives are a second defence but need kernel tuning (Linux default dead-peer detection ~**11 minutes** — RabbitMQ heartbeats page).

**SQS / SNS.** Client talks HTTPS to AWS; you do not load-balance the broker. SNS *outbound* HTTP/S *is* a reverse-direction call onto *your* endpoint: put that endpoint behind an LB that can absorb the retry schedule; `maxReceivesPerSecond` is an **average** throttle, not a hard cap (SNS retry docs).

**Pub/Sub push.** Google POSTs to your HTTPS URL. Your LB, TLS cert (not self-signed), and idle/request timeouts must outlive the subscription ack deadline (default 10 s, max 600 s). Pull/streaming-pull keep the long-lived connection on the subscriber side — corporate proxies that buffer or cap HTTP/2 streams break streaming pull; use pull or a sidecar that owns the stream.

**Service Bus.** AMQP through Azure's front-end; idle connection close **10 minutes** releases locks. Do not put a user-space proxy in front that is shorter.

---

## 4. Verified defaults / standards (fetched 2026-09-13)

| Knob | Default | Source (version / page) |
|---|---|---|
| Kafka `acks` | `all` | 4.1 producer configs |
| Kafka `enable.idempotence` | `true` (disabled if conflicting configs and not explicitly enabled) | 4.1 producer configs |
| Kafka `max.in.flight.requests.per.connection` | `5` | 4.1 producer configs |
| Kafka `isolation.level` | `read_uncommitted` | 4.1 / 4.3 consumer configs |
| Kafka `enable.auto.commit` / interval | `true` / `5000` ms | 4.1 consumer configs |
| Kafka `auto.offset.reset` | `latest` | 4.1 consumer configs |
| Kafka `max.poll.records` | `500` | 4.1 consumer configs |
| Kafka `max.poll.interval.ms` | `300000` (5 min) | 4.1 / 4.3 consumer configs |
| Kafka `session.timeout.ms` / `heartbeat.interval.ms` | `45000` / `3000` (classic protocol) | 4.1 / 4.3 consumer configs |
| Kafka `group.protocol` | `classic` | 4.1 and 4.3 consumer configs |
| Kafka `connections.max.idle.ms` (client / broker) | `540000` / `600000` | 4.1 consumer / broker configs |
| Kafka `reconnect.backoff.ms` / max | `50` / `1000` (+ 20% jitter on max) | 4.1 consumer configs |
| Kafka `min.insync.replicas` | `1` | 4.1 broker configs |
| Kafka `unclean.leader.election.enable` | `false` | 4.1 broker configs |
| Kafka `transaction.state.log.replication.factor` / `min.isr` | `3` / `2` | 4.1 broker configs |
| Kafka Connect `errors.tolerance` | `none` | KIP-298; Connect user guide |
| Kafka Connect DLQ topic / RF / headers | `""` / `3` / `false` | KIP-298 (sink only) |
| SQS visibility timeout | 30 s (0–12 h) | SQS Developer Guide + message quotas |
| SQS retention | 4 days (60 s–14 days) | SQS message quotas |
| SQS max body | 1 MiB (Extended Client → S3, 2 GB) | SQS message quotas |
| SQS standard in-flight | ~120,000 (`OverLimit` on short poll) | Visibility-timeout page |
| SQS FIFO (no high-throughput) | 300 TPS / action; 3,000 msg/s with batch of 10 | FAQ + quotas |
| SQS FIFO high-throughput (us-east-1 / us-west-2 / eu-west-1) | 70,000 TPS; 700,000 msg/s batched | Message quotas (other regions lower — see that page) |
| SQS FIFO dedup window | 5 minutes | FAQ + “Exactly-once processing” page |
| SNS standard subscriptions / topic | 12,500,000 | SNS endpoints and quotas |
| SNS FIFO subscriptions / topic | 100 | SNS endpoints and quotas |
| SNS → SQS/Lambda retries | 100,015 over 23 days | SNS delivery retries |
| SNS HTTP/S retry-time cap | 3,600 s | SNS delivery retries |
| Pub/Sub ack deadline | 10 s (10–600) | Subscription properties + REST resource |
| Pub/Sub `enableExactlyOnceDelivery` | `false` | REST resource; exactly-once page |
| Pub/Sub DLT `maxDeliveryAttempts` | 5 (range 5–100) | Subscription properties + handling-failures |
| Pub/Sub pull throughput (large region) | 4 GB/s subscriber + 4 GB/s ack | Pub/Sub quotas |
| Pub/Sub push throughput (large region) | 440 MB/s | Pub/Sub quotas |
| RabbitMQ heartbeat (server-suggested) | 60 s (frames ~30 s) | Heartbeats guide |
| RabbitMQ DLX strategy | `at-most-once`; quorum opt-in `at-least-once` | DLX + quorum-queue docs |
| RabbitMQ quorum DL-worker prefetch | 32 | Quorum queues / 2022-03-29 blog |
| Service Bus lock duration | 1 min (max 5 min) | Message transfers / locks |
| Service Bus `MaxDeliveryCount` | 10 | Dead-letter queues page |
| Service Bus idle connection | 10 min | Dead-letter queues page |
| Service Bus auto-forward hop cap | 4 | Dead-letter queues page |

AMQP 0-9-1 is an OASIS standard (RabbitMQ's native protocol). AMQP 1.0 is ISO/IEC 19464 — Service Bus and (separately) RabbitMQ's AMQP 1.0 plugin. Kafka's protocol is Apache-project-specific. SQS/SNS/Pub/Sub are HTTPS/gRPC APIs, not AMQP.

---

## 5. Failure modes and when-not-to-use

**Failure modes of the mechanism itself.**

- **Duplicate side effects.** Every at-least-once path (SQS visibility expiry, Kafka crash after process-before-commit, Pub/Sub expired ack, RabbitMQ redelivery, SNS + SQS double hop) will redeliver. FIFO/Pub/Sub/Kafka “exactly-once” flags do **not** cover a non-idempotent HTTP call or email. That is C9.
- **Poison stall.** One bad key/session/group blocks that ordered stream; competing consumers on *other* keys continue. Without a DLQ the partition or session stops making progress.
- **DLQ as a black hole.** Pub/Sub DLT with no subscription; RabbitMQ DLX missing at dead-letter time; SNS subscription DLQ without `SendMessage`; Kafka Connect source errors; SQS FIFO + DLQ silently reorders. Unwatched DLQs are silent data loss.
- **False EOS.** Default Kafka `read_uncommitted` + transactional produce = aborted records visible. SQS FIFO still redelivers on lease expiry. Pub/Sub exactly-once still accepts publisher duplicates as new ids.
- **Rebalance / session storms.** Kafka `max.poll.interval.ms` (5 min) vs a slow batch of `max.poll.records` (500); static membership forgotten (`group.instance.id` null) → shuffle on every deploy. Service Bus lock lost on the 10-minute idle close. RabbitMQ missed heartbeats behind a proxy → reconnect storm (C2).
- **Head-of-line / hot partition.** Kafka key cardinality too low; SQS FIFO few `MessageGroupId`s; Pub/Sub hot `orderingKey`. Fan-out does not fix a single hot key.
- **Retention vs delete-on-ack.** A queue cannot rewind a new subscriber. A log with `auto.offset.reset=latest` *looks* like a queue and drops history for a new group.
- **Mediator hotspot.** A content-routing broker that every team must change (Hohpe's über-broker) fails the reason you bought pub/sub.
- **LB / advertised-listener split brain.** Clients that can bootstrap but cannot reach `advertised.listeners` (or that share one VIP) fail after metadata.

**When to use (Azure Publisher-Subscriber + Competing Consumers, fetched 2026-09-13).** Broadcast to many independently deployed consumers; sender must not block on a reply; consumers have different uptime than the publisher; workload splits into independent parallel tasks; volume is bursty and a buffer is the load-leveler.

**When not to use.**

- A handful of consumers that each need *different* information — broker overhead without fan-out benefit; use dedicated queues or A1.
- The publisher needs a **synchronous** result — use A1 request–response (Azure: pub/sub “introduces latency through the broker”).
- **Global total order** across all messages — partitions/sessions/groups restore order only by *reducing* parallelism.
- A **single atomic transaction** across publisher and consumers — pub/sub is eventually consistent; use a local transaction + **B7** outbox, or **B5** saga, not a broker ack.
- You need **replay / event sourcing** — a delete-on-consume queue is the wrong primitive; use a log (E12), not SQS/RabbitMQ classic.
- In-process calls, or a platform that already buses the same event (don't double-publish).
- FIFO + DLQ when order *is* the product (SQS explicit warning).

Trade-off on every recommendation: a log buys replay and multi-group fan-out and spends operational complexity (partitions, rebalances, retention, EOS config). A queue buys simple competing consumers and spends replay and independent subscribers. A mediating topic (SNS, Service Bus filters) buys subscriber isolation and spends a second hop and a second failure mode (delivery DLQ ≠ processing DLQ).

---

## 6. Cross-links

- **This tree (do not rewrite):** [event-driven-dataflow](../../../cases/data-intensive-design/event-driven-dataflow.md) — broker job, queue vs topic, schema registry, actor-as-broker. [distributed-transactions.md](../../../cases/data-intensive-design/distributed-transactions.md) — exactly-once *processing* via idempotent consume. [encoding-overview.md](../../../cases/data-intensive-design/encoding-overview.md) / [encoding-references.md](../../../cases/data-intensive-design/encoding-references.md) — unknown fields on republish; [22] Kreps. [event-sourcing-cqrs.md](../../../cases/data-intensive-design/event-sourcing-cqrs.md) — retain-forever logs.
- **Catalog siblings:** A1 request–response · B5 saga · B7 outbox/CDC · C9 idempotency · C10 backpressure · E4 event-driven *style* (no mechanisms) · E12 CQRS/event sourcing.
- **Catalog of record:** [system-design-patterns-catalog.md](system-design-patterns-catalog.md) row A2.

---

## 7. Sources

**Canon.** enterpriseintegrationpatterns.com/patterns/messaging/{PublishSubscribeChannel,MessageBroker,MessageBus,CompetingConsumers,DeadLetterChannel,PointToPointChannel}.html · enterpriseintegrationpatterns.com/docs/EnterpriseIntegrationPatterns_HohpeWoolf_ch03.pdf · enterpriseintegrationpatterns.com/ramblings/03_hubandspoke.html · learn.microsoft.com/azure/architecture/patterns/{publisher-subscriber,competing-consumers} · learn.microsoft.com/azure/architecture/guide/technology-choices/messaging · [event-driven-dataflow](../../../cases/data-intensive-design/event-driven-dataflow.md) · encoding-references [22], [51].

**Kafka (4.1 pages; 4.3.1 current on 2026-09-13).** kafka.apache.org/41/configuration/{producer,consumer,broker}-configs/ · kafka.apache.org/43/configuration/consumer-configs/ · kafka.apache.org/41/operations/consumer-rebalance-protocol/ · kafka.apache.org/community/downloads/ · kafka.apache.org/blog/2026/06/25/apache-kafka-4.3.1-release-announcement/ · cwiki.apache.org/confluence/display/KAFKA/KIP-298 · kafka.apache.org/28/kafka-connect/user-guide/ · cwiki.apache.org/confluence/display/KAFKA/KIP-1274 (default-protocol flip; **not shipped** as of the 4.3 pages).

**AWS.** docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/{sqs-visibility-timeout,sqs-dead-letter-queues,quotas-messages,FIFO-queues-exactly-once-processing,FIFO-queues-understanding-logic,avoding-processing-duplicates-in-multiple-producer-consumer-system}.html · aws.amazon.com/sqs/faqs/ · docs.aws.amazon.com/sns/latest/dg/{sns-dead-letter-queues,sns-message-delivery-retries,sns-sqs-as-subscriber,fifo-message-durability}.html · docs.aws.amazon.com/general/latest/gr/sns.html.

**GCP.** docs.cloud.google.com/pubsub/docs/{exactly-once-delivery,ordering,handling-failures,subscription-properties,subscriber} · docs.cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions · docs.cloud.google.com/pubsub/quotas.

**RabbitMQ / Azure Service Bus.** rabbitmq.com/docs/{dlx,confirms,quorum-queues,connections,heartbeats,reliability} · rabbitmq.com/blog/2022/03/29/at-least-once-dead-lettering · learn.microsoft.com/azure/service-bus-messaging/{service-bus-queues-topics-subscriptions,service-bus-dead-letter-queues,message-sessions,message-expiration,message-transfers-locks-settlement}.

**Proxy / LB.** kafka.apache.org/41/configuration/broker-configs/ (`advertised.listeners`, `connections.max.idle.ms`) · rabbitmq.com/docs/heartbeats (HAProxy, AWS ELB) · github.com/confluentinc/librdkafka/issues/3109 (Event Hubs idle LB).

---

## 8. Uncertain / left out

- Kafka 4.3.1 *producer/broker* config HTML was not fetched (4.1 pages used; 4.3 consumer pages confirmed the consumer defaults above). A silent default flip on `acks` / idempotence between 4.1 and 4.3 was **not** re-verified.
- Kafka's marketing / wiki “exactly-once” pages (`documentation.html#semantics`) returned **422** to the fetcher; EOS description is from 4.1 config text + KIP-298 + the Streams `exactly_once_v2` name as used on secondary pages. The precise KIP-98 wording was not re-read from an Apache HTML guide.
- Kafka Connect **4.x** user-guide URL was not fetched; DLQ defaults are from KIP-298 and the 2.8 user guide. Unconfirmed whether 4.x added a source-connector DLQ.
- `errors.retry.timeout` default **0** is from KIP-298 / 2.8 guide; not re-read from 4.3 Connect source.
- SQS “approximately 120,000” in-flight: AWS's own hedge; FIFO in-flight cap *per active group* was not given as a single number on the fetched pages.
- SNS per-account **publish** messages/second (300–30,000 by region in search snippets) — the quotas table was only partially extracted; **do not** treat a single global publish TPS as fact.
- Pub/Sub “thousands of messages per second” under ordered + exactly-once is the vendor's order-of-magnitude, not a quota row.
- RabbitMQ *current* latest version number on 2026-09-13 was not pinned (docs paths `/docs/` and `/docs/4.2/` both served). Quorum prefetch cap 2000 and DL-worker prefetch 32 are from the fetched pages.
- AMQP 1.0 ISO date and Azure Service Bus *Premium vs Standard* size quotas beyond the 256 KB Standard remark were not fully tabulated.
- NATS JetStream, Apache Pulsar, Amazon Kinesis, Redpanda: out of scope this pass (named in event-driven-dataflow; not re-verified).
- Spring Kafka `DeadLetterPublishingRecoverer` / `<topic>-dlt` — convention cited via the existing circuit-breaker note, not re-fetched.
- No controlled measurement of rebalance-induced duplicate windows or SNS `maxReceivesPerSecond` spike size.
- Hohpe book-body text beyond the public pattern pages and ch. 3 PDF extract was not copied (and must not be).

---
