---
type: analysis
title: 'Constraints and influences on financial data architectures'
description: 'Business needs, technology limits, cost, internal policy, and regulation bound the blueprint. Ignore them and the design is a drawing, not a building.'
tags: [financial-data-architecture, constraints, nfrs, regulation]
---

# Constraints and influences on financial data architectures

**See also:** [components](architecture-components.md) · [why it is needed](why-needed.md) · [regulatory compliance](regulatory-compliance.md) · [classifying architectures](classifying-architectures.md)

Design is shaped by organisational, technological, and external factors. Ignore them and you waste effort. A building blueprint that ignores materials and physics is not buildable; a data architecture that ignores these is the same.

## Business requirements

The strongest driver. In finance they often cluster on **scalability, performance, security, and compliance**:

- Rapid, secure transaction processing; low-latency access; high availability
- Both structured (e.g. market data) and unstructured (e.g. regulatory documents)
- Turn operational data into insight (analytics platforms, warehouses) for investment, risk, compliance, reporting
- **Separate transactional data** (trades) from **reference data** (instruments, counterparties)
- Different pathways for **real-time** vs **analytical** retrieval (batch queries, dashboards)

(The source writes “real real-time”; treat it as real-time.)

## Technology drivers

Enablers: cloud and similar innovations — scalable store, process, analytics; a path to modernise [legacy](legacy-systems.md).

Limits to fold into the design: latency and throughput for real-time; concurrency and scale at high volume; CPU and storage for analytics and history; integration with legacy.

Existing reality also binds: legacy frameworks, house standards, budget, **vendor lock-in**, licences and subscriptions to data providers, interoperability with payment networks and trading platforms.

## Economics

High-performance options can lose on cost. Worse in the cloud: misunderstand the pricing model or the usage pattern and the bill surprises you.

## Business policies

Internal rules on privacy, security, access, retention, archive, and usage — from products, client/market segmentation, regulation, audit, or cross-department controls. Example: segregate client data across legal entities or affiliates; limit data movement across jurisdictions.

## Regulatory requirements

What and how data must be stored, processed, accessed, and reported. The chapter’s named example: **Principles for Effective Risk Data Aggregation and Risk Reporting** (the [BCBS 239](regulatory-compliance.md) family) — a bank must collect, aggregate, and report risk data in normal times *and* in stress or crisis.

**Architect takeaway:** write the constraint set *before* the component diagram. A real-time trade path that cannot be segregated by legal entity has already failed policy. A cheap lake that cannot aggregate risk under stress has already failed BCBS 239.
