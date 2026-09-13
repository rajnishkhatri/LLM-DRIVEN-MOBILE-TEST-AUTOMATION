---
type: analysis
title: 'AI adoption in financial data'
description: 'Models need governed, task-relevant data. Generative tools can also extract entities from messy text. Quality and governance decide whether AI helps or hallucinates.'
tags: [financial-data-architecture, ai, llm, data-quality]
---

# AI adoption in financial data

**See also:** [challenge map](management-challenges.md) · [data quality](data-quality.md) · [reference data](reference-data.md) · [security and privacy](security-privacy.md)

AI is general-purpose; finance is an early and intense adopter. The source chapter spans classical machine learning and generative / LLM tools.

## Where it shows up

| Mode | Examples in the source chapter |
|---|---|
| **Operational** | Task automation, fraud detection, product recommendation, compliance checks |
| **Analytical** | Summarisation, document processing, sentiment, market analysis, insight generation |

## The two-way dependency

Effectiveness hinges on data quality and governance. Training and fine-tuning need data that is high-quality *and relevant to the task*.

The other direction: generative tools can *improve* quality by extracting entities from unstructured text (prospectuses, filings, news) and turning them into a usable structure. That is why [reference data](reference-data.md) programs and AI extraction keep meeting.

This interplay — AI needs good data; AI can help make data good — is a central factor in the industry.

## Close of the chapter

The persistent challenges in this bundle are why a strategic shift is required. Collecting more information or buying a tool is not the fix. The foundation is a sound financial data architecture. The source chapter’s next section (architectures themselves) is not extracted here yet.

**Architect takeaway:** put AI on top of identifier maps, point-in-time quality, and access control — or it will scale the silo and the wrong join. Use generation where the job is extraction from prose; do not use it as a substitute for a reconciliation that must be exact.
