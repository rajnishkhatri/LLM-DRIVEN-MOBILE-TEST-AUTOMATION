---
type: overview
title: 'Financial data architectures'
description: 'Architecture is the fundamental concepts of an entity in its environment. Financial data architecture is the domain-specific blueprint for collecting, storing, sharing, and governing that data.'
tags: [financial-data-architecture, architecture, overview]
---

# Financial data architectures

**See also:** [chapter 1 map](introduction.md) · [definition](defining-financial-data-architecture.md) · [components](architecture-components.md) · [classifications](classifying-architectures.md)

Architecture is the art of designing and building — from idea to execution — under real constraints (budget, materials, regulation). Digital architectures do the same with code instead of concrete: plan, design, implement, optimise, improve.

This chapter is the *discipline*, not a target stack. Chapter 1 asked why financial data is hard. This chapter names what a financial data architecture is, when to invest, what it is made of, and how people classify it.

## Bundle map (chapter 2)

| Need | Concept |
|---|---|
| What “architecture” means in IT (ISO/IEC/IEEE) | [Architecture in IT](architecture-in-it.md) |
| Enterprise vs solution architecture; EA frameworks | [Enterprise architecture](enterprise-architecture.md) |
| TOGAF domains, ADM, continuum | [TOGAF](togaf.md) |
| Why standards (including TOGAF) fail in practice | [When standards fall short](standards-criticism.md) |
| The working definition | [Defining financial data architecture](defining-financial-data-architecture.md) |
| Management vs architecture vs engineering | [Three roles](management-architecture-engineering.md) |
| Why invest | [Why it is needed](why-needed.md) |
| When *not* to invest yet | [When it is not needed](when-not-needed.md) |
| Maturity as a staged investment | [Maturity](architecture-maturity.md) |
| The eight components | [Components](architecture-components.md) |
| What constrains the design | [Constraints](architecture-constraints.md) |
| Six classification lenses | [Classifying architectures](classifying-architectures.md) |
| Why the skill matters | [Why master it](why-master.md) |

Components, split for pull-one-file access: [models](financial-data-models.md) · [governance](financial-data-governance.md) · [integration](integration-interfaces.md) · [infrastructure](technological-infrastructure.md) · [transformation](processing-transformation.md) · [pipelines](pipelines-orchestration.md) · [access](access-layer.md) · [observability](monitoring-observability.md).

## Chapter figures

Plates live under [`figures/`](figures/). Open the Concept, not the JPEG.

| Figure | Concept |
|---|---|
| 2-1 TOGAF five-layer pyramid | [TOGAF](togaf.md) |
| 2-2 ADM cycle | [TOGAF](togaf.md) |
| 2-3 Architecture Continuum | [TOGAF](togaf.md) |
| 2-4 FDA as a discipline (Venn) | [Definition](defining-financial-data-architecture.md) |
| 2-5 Maturity (five named levels) | [Maturity](architecture-maturity.md) |
| 2-6 Component hub (plate ≠ body list) | [Components](architecture-components.md) |

## What this chapter is not

It does not pick a lakehouse or a mesh. The source book’s next chapter is **financial data modelling** (Chapter 3). Those notes are not in this bundle yet.

**Architect takeaway:** use this chapter as the vocabulary and the intake. The [definition](defining-financial-data-architecture.md) plus the [component map](architecture-components.md) and the [classification lenses](classifying-architectures.md) are enough to start a design conversation without collapsing “architecture” into a vendor product.
