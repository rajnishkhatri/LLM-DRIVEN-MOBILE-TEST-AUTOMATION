---
type: reference
title: 'Enterprise and solution architecture'
description: 'EA designs the organisation’s IT, processes, and data toward strategy. Solution architecture delivers one problem. TOGAF is the common EA method; it is not the only framework.'
tags: [financial-data-architecture, enterprise-architecture, togaf, solution-architecture]
---

# Enterprise and solution architecture

**See also:** [architecture in IT](architecture-in-it.md) · [TOGAF](togaf.md) · [when standards fall short](standards-criticism.md) · [definition](defining-financial-data-architecture.md)

**Enterprise architecture (EA)** is a structured approach to designing, organising, and managing an organisation’s IT infrastructure, business processes, and data so they serve strategic goals. Doing that from scratch is hard, so the industry grew frameworks.

## EA frameworks named in the chapter

| Framework | Role in the source |
|---|---|
| **Zachman** | Classification scheme for descriptive representations of an enterprise |
| **ArchiMate** | Modelling language for describing and visualising EA |
| **EABOK** | Collection of practices, methods, and standards |
| **FEAF** | US federal EA framework |
| **DoDAF** | US Department of Defense EA models |
| **TOGAF** | Comprehensive framework for developing and managing EA — the chapter’s deep dive |

The source calls TOGAF the most prevalent of these. Details live in [TOGAF](togaf.md).

## Solution architecture

**Solution architecture** designs and delivers a *specific* solution to a particular business problem. The chapter’s example: a **cloud architecture** that moves applications, data, and services from on-premises to a cloud platform (AWS, Azure, or Google Cloud).

Solution architecture is typically aligned with the principles and framework set by the enterprise architecture. It is not a substitute for EA, and EA is not a substitute for a solution design.

**Architect takeaway:** EA is the constrained playing field; solution architecture is one play. A “cloud migration architecture” that ignores the [data domain](togaf.md#the-four-domains) will move compute and leave the identifier and governance problems on the floor.
