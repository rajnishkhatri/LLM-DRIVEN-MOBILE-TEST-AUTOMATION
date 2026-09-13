---
type: architecture
title: 'Integration and interfaces'
description: 'In, out, and across: vendor ingest, partner and regulator share, and internal exchange. APIs, virtualisation, ISO 20022/FIX, queues, and files are the mechanisms — the interface is the contract.'
tags: [financial-data-architecture, integration, apis, messaging]
---

# Integration and interfaces

**See also:** [components](architecture-components.md) · [data delivery](data-delivery.md) · [integration and aggregation](integration-aggregation.md) · [standardisation](standardisation.md)

This component is every mechanism that moves data: into the firm, out of the firm, and between departments and systems inside it.

| Direction | Examples in the chapter |
|---|---|
| **In** | Third-party vendors |
| **Out** | Fintech partners, regulators |
| **Across** | Department-to-department, system-to-system |

Key elements named: APIs, data virtualisation, standardised messaging (**ISO 20022**, **FIX**), and the [arrival mechanisms](data-delivery.md) already catalogued in Chapter 1.

An **interface** is how two systems exchange information despite different technology or representation. Implementations the chapter lists: REST APIs, message queues, file transfers, protocol-based formats.

The source book’s **Chapter 10** covers architecting systems that exchange financial data. Those notes are not in this bundle yet.

**Architect takeaway:** pick the interface for the hop (see [delivery](data-delivery.md)), then version it. A “we have Kafka” slide is infrastructure; the ISO 20022 dialect and the identifier map are the integration architecture. Watch the [standards cycle](standardisation.md).
