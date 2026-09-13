---
type: analysis
title: 'Event-driven dataflow'
description: 'A broker buffers, retries, fans out, and decouples sender from recipient. Actors make the same bet inside the process. Unknown fields must survive republish.'
tags: [data-intensive-design, encoding, events, message-broker, actors]
---

# Event-driven dataflow

**See also:** [chapter overview](encoding-overview.md) · [REST and RPC](rest-rpc-dataflow.md) · [event sourcing](event-sourcing-cqrs.md) · [Avro](avro-schema-evolution.md) · [Protocol Buffers](protobuf-schema-evolution.md) · [unknown-field loss](encoding-overview.md#backward-and-forward-compatibility) · [exactly-once](distributed-transactions.md#exactly-once-message-processing) · [references](encoding-references.md)

A request here is an **event** or **message**. Unlike RPC, the sender
usually does not wait for the recipient. Delivery goes through a
**message broker** (event broker, message queue, message-oriented
middleware) that stores the message for a while
([51](encoding-references.md)).

Compared with direct RPC, a broker:

- Buffers when the recipient is down or overloaded (reliability).
- Redelivers to a process that crashed (less message loss).
- Removes the need for the sender to know the recipient’s address
  (no service discovery at the publisher).
- Lets one message reach several recipients.
- Decouples sender from recipient: publish, do not name the consumer.

Communication is asynchronous: send and forget. A synchronous,
RPC-like pattern is still possible if the sender waits on a reply
channel.

## Message brokers

The old landscape was commercial (TIBCO, IBM WebSphere, webMethods).
Open source (RabbitMQ, ActiveMQ, HornetQ, NATS, Redpanda, Kafka) and
cloud services (Kinesis, Azure Service Bus, Pub/Sub) took most of the
new work. Delivery semantics differ by product and config; two
distribution patterns dominate:

| Pattern | Delivery |
|---|---|
| **Queue** | One producer, one consumer receives each message (competing consumers share the work) |
| **Topic** | One publisher, every subscriber receives the message |

Brokers typically do not enforce a data model. A message is bytes plus
metadata; use protobuf, Avro, or JSON, and put a
**schema registry** next to the broker to store versions and check
compatibility ([20](encoding-references.md),
[22](encoding-references.md)). AsyncAPI is the messaging counterpart
of OpenAPI.

Durability varies. Many write to disk so a broker crash does not lose
the queue. Unlike databases, many **delete after consume**. Some can
retain indefinitely — required if you want
[event sourcing](event-sourcing-cqrs.md).

If a consumer republishes to another topic, **preserve unknown
fields** or you recreate the
[Figure 5-1](encoding-overview.md#backward-and-forward-compatibility)
loss.

## Distributed actor frameworks

The **actor model** is a concurrency model for one process. Instead of
threads, locks, and deadlocks, logic lives in actors. An actor usually
represents one client or entity, holds private state, and talks only
by asynchronous messages. Delivery is not guaranteed; messages can be
lost. Each actor handles one message at a time, so it does not need
locks, and the runtime can schedule actors independently.

Distributed frameworks (Akka, Orleans [52](encoding-references.md),
Erlang/OTP) stretch that model across nodes. The same send path is
used whether the recipient is local or remote; a remote send is
transparently encoded, shipped, and decoded.

Location transparency fits actors better than RPC because the model
already assumes messages may be lost *inside* one process. Network
latency is higher, but the failure story matches.

A distributed actor runtime is a message broker plus the actor
programming model in one framework. Rolling upgrades still need
forward and backward compatibility: a new node may send to an old
node and the other way around. Use one of the encodings in this
chapter.

**Architect takeaway:** a broker buys time and fan-out; it does not
buy a schema. Put a registry beside the topic, keep unknown fields
on republish, and treat actor messages as just another encoding
boundary.
