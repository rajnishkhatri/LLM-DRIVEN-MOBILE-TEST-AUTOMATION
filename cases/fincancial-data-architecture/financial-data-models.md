---
type: architecture
title: 'Financial data models'
description: 'Models define accounts, instruments, transactions, customers, and events — and how they relate. Conceptual, logical, and physical layers give business and systems a shared language.'
tags: [financial-data-architecture, data-modeling, conceptual, logical, physical]
---

# Financial data models

**See also:** [components](architecture-components.md) · [finance basics](finance-basics.md) · [characteristics](data-characteristics.md) · [classifying — modeling](classifying-architectures.md#classification-by-data-modeling-approach)

Financial data models define how data is organised and how pieces relate to each other and to real-world concepts. They capture core entities — accounts, instruments, transactions, customers, events — plus attributes, meanings, and connections.

| Layer | Question it answers |
|---|---|
| **Conceptual** | What the data *means* (business conversations) |
| **Logical** | How it is *structured* |
| **Physical** | How it is *implemented* in systems |

This is where Chapter 1 complexity gets unpacked: business requirements, jargon, and messy market data become something humans and systems can share. A solid model is a common language for engineers, analysts, and compliance — consistency and meaning across the organisation.

The source book’s **Chapter 3** is dedicated to financial data modelling. Those notes are not in this bundle yet.

**Architect takeaway:** do not jump to a physical schema. If the conceptual model cannot say what an [instrument vs security](finance-basics.md) is, the warehouse will invent two of them. Modelling approach (normalised, dimensional, Data Vault) is a [classification lens](classifying-architectures.md), not a substitute for the entity list.
