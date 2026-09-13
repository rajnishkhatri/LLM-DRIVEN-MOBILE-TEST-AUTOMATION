---
type: reference
title: 'Financial data sources'
description: 'Exchanges, OTC venues, regulators, vendors, institutions, FMIs, and alternative data each own a different slice. There is no single central repository.'
tags: [financial-data-architecture, sources, vendors, fmi, alternative-data]
---

# Financial data sources

**See also:** [ecosystem](data-ecosystem.md) · [generation](data-generation.md) · [delivery](data-delivery.md) · [value chain](value-chain.md) · [reference data](reference-data.md)

Variety of *owners* is the second reason the ecosystem is hard. Each source class has a different commercial model, latency, and quality bar.

## Exchanges and alternative venues

Exchanges (NYSE, LSE, NASDAQ) collect and disseminate prices, volumes, quotes, and transaction details — typically as paid subscriptions.

Many trades never sit in that central book:

| Venue class | What it is |
|---|---|
| **OTC** | Decentralised, bilateral. Data is dispersed across private venues |
| **ATS** (Alternative Trading System) | Private platform that matches buy and sell orders |
| **MTF** (Multilateral Trading Facility) | Facilitates exchange of securities between counterparties |

If your design assumes “we will take the exchange feed,” you have already dropped OTC, ATS, and MTF flow.

## Regulatory filings and public data

Trusted, often cheap, rarely analysis-ready.

- **SEC EDGAR** (US): 10-K (annual, comprehensive), 10-Q (quarterly, unaudited), 8-K (material events — mergers, leadership). All via EDGAR.
- **Central banks:** monetary policy, interest rates.
- **Macro indicators:** GDP, inflation, employment.
- **International and national agencies:** IMF, World Bank, US BEA, China’s NBS — GDP, inflation, trade, labour, monetary statistics.

Public data is usually unstructured or not analysis-ready. Budget the standardisation work; do not treat “free” as “cheap to use.”

## Commercial data providers

Vendors gather, clean, structure, and distribute. Named in the source chapter: Bloomberg, LSEG, FactSet, Morningstar, Moody’s, S&P Global Market Intelligence, MSCI. Typical coverage: market data, reference data, news, analytics, history, standardised identifiers. Proprietary; subscription and terms of use are load-bearing.

See [distribution](value-chain.md#distribution) for why firms buy a vendor instead of going to every exchange.

## Financial institutions

Banks, asset managers, funds, FinTechs, insurers generate transaction and client data as a side effect of doing business. Proprietary; privacy and internal-use rules apply. Some of it must be shared for reporting and AML.

This is the source class behind [silos](data-silos.md) and [legacy systems](legacy-systems.md).

## Financial market infrastructures (FMIs)

FMIs are the plumbing: they clear, settle, and record. They are also significant data sources (volumes, values, fund flows, settlement outcomes, counterparties).

| FMI class | Example role |
|---|---|
| **Payment systems** | SWIFT — information and instruction exchange |
| **Central Securities Depositories** | Euroclear — registration and safekeeping of securities |
| **Central Counterparties** | CME Clearing — intermediary that mitigates counterparty risk |

## Alternative data

Non-traditional sources used for earlier signals: social posts, sentiment, news, satellite imagery, card-spend trends, web scrape.

Examples from the source chapter: tanker and pipeline activity can move weeks before official oil numbers; parking-lot fullness can precede a retail earnings release.

The list is not closed. New source types keep appearing because the market for financial data is lucrative.

**Architect takeaway:** write a source inventory with owner, commercial terms, venue class, and whether the data is consolidated or dispersed. “We subscribe to Bloomberg” is not a source architecture. OTC and internal books will still be missing.
