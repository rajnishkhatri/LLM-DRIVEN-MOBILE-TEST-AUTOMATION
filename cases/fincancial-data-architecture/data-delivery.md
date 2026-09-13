---
type: reference
title: 'Financial data arrival and exchange'
description: 'APIs, feeds, webhooks, files, terminals, queues, cloud shares, and ledgers are different contracts. Pick the mechanism for latency, volume, and control — not habit.'
tags: [financial-data-architecture, delivery, apis, feeds, messaging]
---

# Financial data arrival and exchange

**See also:** [ecosystem](data-ecosystem.md) · [sources](data-sources.md) · [types and formats](data-types-formats.md) · [scalability](scalability-performance.md)

How data *arrives* is a separate design from who produces it. Mechanisms are chosen for use case, technical constraints, and commercial terms.

## Programmatic and automated

| Mechanism | Fit |
|---|---|
| **API** | Real-time or historical data by request. Integration between apps, platforms, analytics |
| **Web services** | HTTP/HTTPS, typically XML or JSON |
| **Data feeds** | Continuously updated stream (news, market data) |
| **Webhooks** | Push when something changes (trading, payments) |
| **Direct database access** | SQL or ODBC/JDBC against a relational store |

## Bulk and file-based

| Mechanism | Fit |
|---|---|
| **Bulk data** | Periodic large dumps, often compressed — history, static data, regulatory reporting |
| **Onsite / deployed servers** | Vendor delivers into the client’s infrastructure |
| **Desktop applications** | Licensed terminals (Bloomberg, LSEG Eikon) |
| **File download** | CSV, JSON, XML, Parquet, Excel |
| **Excel add-ins** | Live, historical, and fundamental data inside a spreadsheet |
| **FTP** | Batch structured files |
| **SFTP** | Encrypted FTP — common for regulatory and sensitive batches |

## Specialised and alternative

| Mechanism | Fit |
|---|---|
| **Cloud delivery** | AWS, Google Cloud, Azure, Snowflake — scalable store and compute |
| **Message queues** | Async between independent services; producers publish, consumers pull |
| **Data marketplaces** | Buy/sell datasets, often in-cloud, without a file download |
| **Blockchain / distributed ledgers** | Crypto and some settlement records live on-chain |

## Design notes

- A **feed** and an **API** are not interchangeable. Feeds assume you can keep up; APIs assume you will ask.
- **SFTP of a daily file** is still the honest path for a lot of reference and regulatory data. Do not force it through a streaming bus because streaming is fashionable.
- **Terminal vs API vs cloud share** are commercial and control decisions as much as technical ones. The same vendor may offer all three with different latency and terms.
- Queues decouple producers from consumers. They do not remove the need for a schema and an identifier story — see [standardisation](standardisation.md) and [characteristics](data-characteristics.md).

**Architect takeaway:** list each inbound dataset with *mechanism, cadence, format, and who can replay it*. Mixing a real-time market feed with a T+1 reference file without saying so is how “the price is wrong” incidents start.
