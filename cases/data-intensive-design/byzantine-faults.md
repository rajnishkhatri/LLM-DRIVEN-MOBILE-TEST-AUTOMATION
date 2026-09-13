---
type: analysis
title: 'Byzantine faults'
description: 'Crash, pause, and lie are different models. Datacenter nodes are assumed honest-but-faulty. BFT is for aerospace, mutually untrusting parties, and some peer-to-peer systems — not a substitute for authn.'
tags: [data-intensive-design, distributed-systems, byzantine, bft, honesty]
---

# Byzantine faults

**See also:** [chapter overview](distributed-systems-overview.md) · [quorums and fencing](quorums-and-fencing.md) · [system models](system-models.md) · [reliability](reliability.md) · [references](distributed-systems-references.md)

[Fencing tokens](quorums-and-fencing.md#fencing-tokens) stop a
node that is *wrong* — lease expired, it has not noticed. A
node that *wants* to break the protocol sends a fake token.

These notes assume nodes are **unreliable but honest**. Slow,
silent, stale — but if they speak, they tell the truth as they
know it and follow the protocol.

**Byzantine** faults are arbitrary: contradictory votes in one
election, corrupted replies, malice. Reaching agreement then
is the **Byzantine Generals Problem**
([94](distributed-systems-references.md)).

The two-generals problem
([95](distributed-systems-references.md)) is the honest
version: two camps, messengers that get lost, agreement on a
plan — consensus, next chapter. The Byzantine version adds
traitors among *n* generals. You do not know who they are.
The name is “byzantine” as in excessively complicated, not a
claim about Istanbul
([96](distributed-systems-references.md),
[97](distributed-systems-references.md)).

## When BFT is the model

A system is **Byzantine fault-tolerant** if it stays correct
when some nodes misbehave or an attacker tampers with the
network. That matters in narrow places:

- Aerospace: radiation flips registers; a wrong actuator
  command kills people or hits the ISS
  ([98](distributed-systems-references.md),
  [99](distributed-systems-references.md)). Hardware-level
  support is normal.
- Mutually untrusting parties. Bitcoin and other chains are
  a way to agree that a transaction happened without a
  central authority
  ([100](distributed-systems-references.md)).
- Some peer-to-peer networks with no trusted server
  ([103](distributed-systems-references.md),
  [104](distributed-systems-references.md)).

In a datacenter you run, nodes are yours. Radiation is low
(orbital DCs are a research idea
([101](distributed-systems-references.md))). Multi-tenant
isolation is firewalls, VMs, and IAM — not BFT. BFT protocols
are expensive
([102](distributed-systems-references.md)). For most
server-side data systems they are not practicable.

Web apps already expect malicious *clients*. Validate,
sanitize, escape. The **server** is the authority on what is
allowed. That is not a BFT protocol.

A software bug is Byzantine-shaped, but deploying the same
binary everywhere means BFT cannot save you. Typical BFT
needs a supermajority (more than two-thirds correct — four
nodes, at most one bad). Using that against bugs means four
independent implementations and a hope the bug is in only
one.

Compromise of one node usually implies compromise of the
others: same software. Authentication, access control,
encryption, and firewalls remain the main defense.

## Weak forms of lying

Honest-node systems still gain from cheap guards against
*accidental* lies — hardware glitches, bugs, misconfig. Not
BFT; still worth doing:

- Packets corrupt. TCP/UDP checksums miss some
  ([105](distributed-systems-references.md),
  [106](distributed-systems-references.md),
  [107](distributed-systems-references.md)). Application
  checksums and TLS catch more.
- Sanitize untrusted input (SQL injection, huge allocations).
  Internal services can be looser; protocol parsers still
  need basic checks
  ([105](distributed-systems-references.md)).
- NTP from several servers; drop outliers
  ([39](distributed-systems-references.md)). One wrong time
  source should not steer the cluster.

**Architect takeaway:** pick the honesty model on purpose.
“Unreliable but honest” is the default for a service you
operate; then fencing, checksums, and multi-source NTP are
the tools. BFT is a different product (safety-critical
hardware, untrusted participants), a supermajority, and a
cost you will feel. It is not a patch for “we all run the
same JVM.”
