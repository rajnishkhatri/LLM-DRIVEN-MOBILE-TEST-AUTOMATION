---
type: analysis
title: 'Legacy systems'
description: 'Mainframes and COBOL still clear high-volume payments. They are reliable and siloed. Migration is costly; not everything should move.'
tags: [financial-data-architecture, legacy, mainframes, cloud]
---

# Legacy systems

**See also:** [challenge map](management-challenges.md) · [data silos](data-silos.md) · [scalability](scalability-performance.md) · [security and privacy](security-privacy.md)

A **legacy system** is hardware, software, or an entire stack built with technologies the current market calls old — still running because it still does the job it was designed for.

Large institutions, especially banks, still run **mainframes** on-site for volume and security. ATM traffic is a common example. Many of those machines still run **COBOL**.

## What they are good at

Reliability, security, and billions of transactions. That is why they survive.

## What they cost

- Hard to integrate with modern stacks
- Hard to add features
- They generate vast data (petabyte scale at large firms) that stays siloed inside the legacy estate, so analytics and product development cannot reach it

## Migration, with a brake

Many firms are moving, often toward **hybrid cloud**: on-prem / private cloud for the regulated core, public cloud for analytics flexibility.

The source chapter’s caution: migration is complex, costly, and can backfire. Do not assume everything must be replaced. Mainframes still excel at high-volume work such as ATM authorisation. Prioritise modernisation where the impact is highest.

**Architect takeaway:** treat the mainframe as a bounded context with an anti-corruption layer, not as a shame to be rewritten in one program. Move *access* to the data (CDC, controlled APIs) before you move the ledger. Hybrid is a strategy, not a halfway failure.
