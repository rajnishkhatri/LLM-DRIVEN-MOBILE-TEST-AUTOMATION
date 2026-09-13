---
type: analysis
title: 'Management vs architecture vs engineering'
description: 'Management sets the objective. Architecture is the blueprint. Engineering builds and runs the infrastructure. Do not hire one title and expect all three.'
tags: [financial-data-architecture, roles, data-management, data-engineering]
---

# Management vs architecture vs engineering

**See also:** [definition](defining-financial-data-architecture.md) · [why master it](why-master.md) · [components](architecture-components.md)

The chapter’s workflow:

| Role | Job |
|---|---|
| **Data management** | Sets the *strategic goals* for how the organisation handles data |
| **Data architecture** | Creates the *blueprint* — systems and structure that achieve those goals |
| **Data engineering** | *Builds and maintains* the infrastructure that makes data accessible and usable |

Short form: management is the objective, architecture is the plan, engineering is the execution.

This is why the later [skill note](why-master.md#a-skill-rather-than-a-job-title) treats architecture as a capability many engineers already exercise, not only a job title.

**Architect takeaway:** if “we have no data architect” is the complaint, ask which of the three is missing. A lake with no policies is a management gap. A policy with no store-and-pipeline design is an architecture gap. A beautiful ADR with nobody to run Airflow is an engineering gap.
