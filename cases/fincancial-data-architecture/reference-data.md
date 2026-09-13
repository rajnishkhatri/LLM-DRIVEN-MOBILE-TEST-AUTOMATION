---
type: analysis
title: 'Reference data management'
description: 'Slow-changing identifiers, terms, and classifications underpin every trade and report. They are often extracted from prose and must be linked across identifier schemes.'
tags: [financial-data-architecture, reference-data, identifiers, entity-resolution]
---

# Reference data management

**See also:** [challenge map](management-challenges.md) · [characteristics](data-characteristics.md) · [finance basics](finance-basics.md) · [integration](integration-aggregation.md)

**Reference data** is static or slowly changing information used to identify, describe, and classify the entities in a transaction.

| Subject | Typical contents |
|---|---|
| **Instruments** | Identifiers, terms and conditions, asset class, valuation and pricing rules |
| **Organisations** | Legal names, form, structure, counterparty roles |
| **Markets** | Trading calendars, venues |
| **Individuals** | Account numbers, bank codes |

It looks routine. It is the most frequently accessed data in operations. Trade execution, payments, settlement, risk, and regulatory reporting all sit on it.

## Why it is hard

- Must be consistent, complete, accurate, and timely across fragmented systems.
- Often *not* delivered as structured fields. A lot of it is buried in unstructured text.
- **Cross-entity linkage** — the same real-world entity under many identifiers and names. See [entity resolution](data-characteristics.md#entity-resolution-and-identifiers).

## Worked example: the fund prospectus

A prospectus is a long regulatory document: objectives, strategies, risk, managers, history. Written for humans. It still contains a wealth of reference data — legal entities (managers, sub-funds, share classes), instruments, strategies, asset classes, sectors, geographies.

That information is narrative, not tables. Extraction needs parsing. Quality and structure vary by issuer. This is why NLP and, later, [AI](ai-adoption.md) show up in reference-data programs.

**Architect takeaway:** give reference data its own store, stewardship, and identifier map. Do not treat it as “the dimension tables we load last.” If the golden instrument record is wrong, every trade, risk number, and report that joins it is wrong.
