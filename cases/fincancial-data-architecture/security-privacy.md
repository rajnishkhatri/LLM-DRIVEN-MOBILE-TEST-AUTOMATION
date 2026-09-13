---
type: analysis
title: 'Data security and privacy'
description: 'Financial data reveals behaviour and vulnerability. Cloud, open banking, and privacy law make protection a design constraint, not a perimeter product.'
tags: [financial-data-architecture, security, privacy, open-banking]
---

# Data security and privacy

**See also:** [challenge map](management-challenges.md) · [regulatory compliance](regulatory-compliance.md) · [legacy systems](legacy-systems.md) · [AI adoption](ai-adoption.md)

Financial data is linked to investments, transactions, and funds. It reveals behaviour, strength, and vulnerability. That makes it a target for fraud, cyberattack, and unauthorised access. Privacy law also constrains how it is collected, stored, processed, and shared.

Security and privacy protect users *and* trust in the system. The landscape has made that harder:

- **Cloud** moves the questions of ownership, attack surface, and access control.
- **Open banking** shares data between banks and fintechs and needs strong security plus privacy-preserving techniques (the source chapter names anonymization).

The source chapter points at a later “Chapter 4” on financial data governance. That chapter is not in this bundle yet. Concrete regulations that already bite are listed under [regulatory compliance](regulatory-compliance.md) (GDPR, PSD2).

**Architect takeaway:** put classification, access, residency, and retention in the architecture, not in a bolt-on tool. Open-banking APIs and cloud analytics are new *trust boundaries*. Anonymization and consent are product features, not legal footnotes.
