---
type: analysis
title: 'Characteristics of financial data'
description: 'Wide, hierarchical, semantic, many-identified, and fast-changing. The hard part is meaning and linkage, not row count.'
tags: [financial-data-architecture, characteristics, identifiers, semantics]
---

# Characteristics of financial data

**See also:** [types and formats](data-types-formats.md) · [reference data](reference-data.md) · [integration](integration-aggregation.md) · [data quality](data-quality.md)

Sources, types, formats, and delivery paths are not the whole difficulty. Financial data has intrinsic traits that break naive models.

## High dimensionality

Fundamentals, holdings, fund characteristics, and risk exposures routinely have hundreds or thousands of fields. A vendor fundamentals feed (FactSet, Bloomberg, S&P Global) may carry hundreds of accounting items (Total Revenue, Net Income) plus dozens of ratios (Debt-to-Equity, Current Ratio, Gross Margin).

Wide tables and “select *” pipelines will hurt. So will a schema that assumes a stable, short column list.

## Multiple hierarchies

The data is nested, not flat.

- A company owns subsidiaries, each with its own financials.
- A balance sheet decomposes: assets → current assets → cash.
- A portfolio is positions; each position is an instrument with price, market data, and risk.

A document model, a graph, or a carefully layered warehouse can express this. A single denormalised fact table usually cannot without losing a level.

## Domain semantics

Field *names* are not enough. Meaning depends on context:

| Context | Why the same label differs |
|---|---|
| **Accounting standard** | IFRS vs US GAAP |
| **Industry** | “R&D” at a manufacturer vs at a financial firm |
| **Time** | Point-in-time as originally reported vs later restated |

If you join two “Revenue” columns without recording the standard, sector, and vintage, you have invented a number.

## Entity resolution and identifiers

The same legal entity has many identifiers. Apple Inc. in the source chapter:

| Scheme | Value |
|---|---|
| Ticker | AAPL |
| ISIN | US0378331005 |
| CUSIP | 037833100 |
| LEI | HWUPKR0MPOU8FGXBT394 |

This is the default, not an edge case. Integration across systems is an identifier-mapping problem. See [reference data](reference-data.md) and [integration](integration-aggregation.md).

## Rapid change and lifecycle complexity

| Class | How it moves |
|---|---|
| **Market prices** | Many times per second (high-frequency trading, continuous books) |
| **Fundamentals** | Typically quarterly, then *revised* by restatement |
| **Corporate actions** | Mergers, acquisitions, spinoffs, ticker or name changes reshape entities and identifiers |

A store that only keeps “latest” loses the ability to answer “what did we know on date D?” Restatements and corporate actions are why point-in-time and as-of queries show up in this domain.

**Architect takeaway:** budget for identifier mapping, point-in-time versions, and hierarchical ownership *in the data model*, not as afterthoughts. A lake of latest snapshots will fail the first restatement and the first merger.
