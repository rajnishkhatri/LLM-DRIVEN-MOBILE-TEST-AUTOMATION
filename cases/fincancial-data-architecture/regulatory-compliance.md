---
type: analysis
title: 'Regulatory compliance as a data problem'
description: 'Market rules are data-architecture requirements: aggregation, lineage, auditability, privacy, and a file you can produce in 72 hours. Fragmented regimes make rigidity fatal.'
tags: [financial-data-architecture, regulation, compliance, reporting]
---

# Regulatory compliance as a data problem

**See also:** [challenge map](management-challenges.md) · [integration and aggregation](integration-aggregation.md) · [data quality](data-quality.md) · [security and privacy](security-privacy.md)

Regulation is the referee: rules, fairness, intervention. Finance is among the most heavily regulated industries. The goals are transparency, consumer protection, and systemic-risk management. The side effect is a data-management problem: quality, aggregation, integration, reporting, lineage, auditability, and privacy.

The source chapter’s examples (not exhaustive):

| Regime | Data demand |
|---|---|
| **BCBS 239** | Better data architecture and aggregation for risk reporting |
| **MiFID II** (EU) | Detailed records of trades, client communications, and market data for reporting and surveillance |
| **EMIR** (EU) | OTC derivatives reported to trade repositories |
| **GDPR** (EU) | How personal data is handled and stored — consent, retention |
| **CCAR** (US) | Granular data for stress testing and capital adequacy |
| **Dodd-Frank** (US) | Mandatory swaps and derivatives reporting |
| **PSD2** (EU) | Open payment-data infrastructure to third parties via APIs, with security and consent |
| **FSCS** (UK) | A Single Customer View sample of each customer’s aggregated holdings, plus how SCV was planned, implemented, and tested — within **72 hours** of request |

Frameworks are getting more complex and more fragmented across jurisdictions. Compliance is no longer “file the report.” It is a flexible data foundation that can track regulatory change. Without strong management and automated compliance, expanding into a new market is nearly impossible.

**Architect takeaway:** treat named regimes as *capability tests* on the architecture (can we aggregate risk? can we produce SCV in 72 hours? can we open APIs without leaking?). A warehouse that cannot answer lineage will fail the next exam even if yesterday’s report was on time.
