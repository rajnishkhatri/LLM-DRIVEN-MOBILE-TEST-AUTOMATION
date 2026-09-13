---
type: architecture
title: 'Processing and transformation logic'
description: 'Business-driven conversion of raw data into usable data: validate, clean, harmonise, enrich, transform — rounding, internal IDs, and metric calculations included.'
tags: [financial-data-architecture, transformation, harmonisation]
---

# Processing and transformation logic

**See also:** [components](architecture-components.md) · [pipelines](pipelines-orchestration.md) · [reference data](reference-data.md) · [data quality](data-quality.md)

Driven by **business requirements**. Raw data becomes actionable through validation, cleaning, harmonisation, enrichment, and transformation.

Chapter examples: rounding rules on prices, assigning unique **internal identifiers**, defining calculations for key metrics. Downstream systems, reports, and consumers depend on this being accurate and consistent.

This is where [domain semantics](data-characteristics.md#domain-semantics) (IFRS vs GAAP, restatements) either get encoded or get lost.

**Architect takeaway:** treat transformation as governed logic with owners and tests, not as a notebook that “cleans the file.” Internal IDs created here must land in the [reference-data map](reference-data.md) or you have minted a ninth identifier.
