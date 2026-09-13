---
type: reference
title: 'Financial data types, formats, and structures'
description: 'Structure is how you organise (series, panel, graph). Type is what it means (market, reference, transaction). Format is how it travels (CSV, FIX, Parquet).'
tags: [financial-data-architecture, types, formats, structures]
---

# Financial data types, formats, and structures

**See also:** [ecosystem](data-ecosystem.md) · [delivery](data-delivery.md) · [characteristics](data-characteristics.md) · [standardisation](standardisation.md)

Three words get collapsed in conversation. Keep them apart:

| Word | Question it answers |
|---|---|
| **Structure** | How is it organised and processed? |
| **Type** | What financial meaning does it carry? |
| **Format** | How is it encoded on disk or on the wire? |

Structures drive access patterns. Types drive products and analytics. Formats drive storage cost, speed, and interoperability.

## Structures

| Structure | Shape | Typical use |
|---|---|---|
| **Time series** | Points in time order (daily prices, monthly GDP) | Trends, forecasts, volatility |
| **Cross-sectional** | Many entities at one time (year-end ratios) | Comparison, benchmarking |
| **Panel** | Time series × cross-section (quarterly earnings for many firms) | Relationships over time |
| **Text** | News, social, filings — unstructured | NLP extraction |
| **Graph** | Relationships (inter-bank lending, alliances) | Systemic risk, interdependency |
| **Vector embeddings** | Item as a numeric array encoding words, images, or other entities | Similarity, retrieval, model input |

## Types

| Type | Contents |
|---|---|
| **Fundamentals** | Statements and accounting (income, balance sheet) — firm health |
| **Market data** | Price and volume, real-time and historical |
| **Alternative data** | Satellite, card spend, social — novel signals; see [sources](data-sources.md#alternative-data) |
| **Reference data** | Identifiers and classifications for instruments and entities; see [reference data](reference-data.md) |
| **Transaction data** | Structured records of purchases, payments, transfers, trades — accounting, audit, compliance |
| **Sentiment / analyst / news** | Ratings, earnings-call text, social sentiment |

## Formats

| Format | Why it shows up |
|---|---|
| **CSV** | Simple tabular exchange; spreadsheets and databases eat it |
| **JSON** | APIs and web apps |
| **XML** | Hierarchical; common in messaging (ISO 20022) |
| **Parquet** | Columnar; compression and analytics at volume |
| **TXT** | Reports, logs, fixed-width |
| **Excel (XLS/XLSX)** | Analysis and reporting; still a production interface |
| **Market / message standards** | FIX, ISO 20022, FpML, XBRL, SWIFT MT |

**Architect takeaway:** pick structure for the query, type for the product, format for the hop. A “JSON API of market data” has decided format and type, not structure — you can still serve a time series or a cross-section through it. Do not store a graph as a wide CSV and hope joins reconstruct the network.
