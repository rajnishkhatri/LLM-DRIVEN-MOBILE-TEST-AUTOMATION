---
type: architecture
title: 'Access layer'
description: 'How people and systems reach financial data: dashboards, reports, APIs, cloud shares, semantic layers — plus access control for who, what, and when.'
tags: [financial-data-architecture, access, semantic-layer, apis]
---

# Access layer

**See also:** [components](architecture-components.md) · [security and privacy](security-privacy.md) · [governance](financial-data-governance.md) · [data delivery](data-delivery.md)

How people and systems interact with financial data: dashboards, reporting platforms, APIs, cloud-based sharing, and **semantic layers** that make complex sets readable.

Consumers named: analysts, developers, business teams, regulators. The goal is easy, secure access **without** requiring them to know the plumbing.

**Access control** is essential: who can see what, and when. The source repeats that sentence twice; once is enough.

**Architect takeaway:** the semantic layer is part of the architecture, not a BI convenience. If two dashboards compute “revenue” differently, you have failed [domain semantics](data-characteristics.md#domain-semantics) at the access hop. Controls belong here *and* in [governance](financial-data-governance.md); a dashboard that bypasses them is an unofficial interface.
