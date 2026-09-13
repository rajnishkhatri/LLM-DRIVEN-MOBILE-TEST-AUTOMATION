---
type: analysis
title: 'Scalability and performance'
description: 'Population, cards, cross-border, and instant-payment rules raise volume. Speed without weaker AML is the trade-off, not a free upgrade.'
tags: [financial-data-architecture, scalability, performance, payments]
---

# Scalability and performance

**See also:** [challenge map](management-challenges.md) · [data-delivery](data-delivery.md) · [legacy systems](legacy-systems.md) · [security and privacy](security-privacy.md)

Markets grow with customer demand, technology, globalisation, and socio-economic change. Data volume and the need for real-time completion grow with them. Infrastructure must hold performance and scale without sacrificing speed, accuracy, quality, or security.

## What drives the load

| Driver | Effect on data and compute |
|---|---|
| **Population and inclusion** | More customers, more payments and transfers |
| **Card payments as default** | Once reserved for large purchases; now coffee and everyday commerce |
| **Globalisation** | More cross-border payments |
| **Regulation** | e.g. the EU Instant Payments Regulation — banks must be able to *receive* instant payments, which raises transactions per second |

## Speed versus risk

Faster payment processing requires faster fraud and AML checks. Over-prioritising speed in those checks weakens them and raises fraud and compliance failure.

This is the same family of trade-off as in data-intensive design: you cannot maximise throughput, latency, and assurance independently. Name the load parameters (payments per second, cross-border share, peak vs mean) and the checks that must still pass.

**Architect takeaway:** write the load model and the *checks that are allowed to add latency*. Instant payment with a best-effort AML screen is a different architecture from T+1 settlement with a full batch review. Do not hide that choice in a “real-time platform” label.
