---
type: handbook
title: 'Anatomy of a discovery session'
description: 'Discovery is for understanding the problem, not pitching a solution. Capture pain, workflow, data, success metric, and blockers — then test whether it is actually an AI problem.'
tags: [fde, handbook, discovery, ai-opportunity]
---

# Anatomy of a discovery session

**See also:** [scoping and solution architecture](scoping-sol-arch.md)

The structure of the session determines how much of the real picture actually surfaces.

The goal of a discovery session is to understand the problem, not to demonstrate how the FDE would solve it.

A discovery session has a predictable structure. Each part serves a specific purpose, and the order matters. Getting the setup, the opening, and the note-taking right determines how much of the real picture the FDE leaves with.

## Who to get in the room

A strong discovery group brings together three types of people, each contributing a different layer of the picture.

**Executive sponsor:** Owns the problem, controls the budget, and anchors the conversation to real organizational priorities. Their presence connects the session to what the organization will actually fund and act on.

**Ops person or domain expert:** Performs the actual work today and knows where the workflow breaks in practice. This is often the most informative person in the room, because they describe the system as it actually runs rather than as it is designed to run.

**Technical contact:** Knows which systems are involved, where the data lives, and what access actually looks like. Essential for evaluating whether the project is technically feasible before the scope document is written.

If only two of the three are available, note which perspective is missing and plan a targeted follow-up before finalizing the scope.

## How to open the session

Open by asking for a complete account of how the workflow breaks down: what triggers the failure, who gets involved, what work gets stuck, and how the team recovers. That kind of narrative reveals systems, handoffs, manual steps, and failure modes that a direct question about pain points rarely surfaces.

**Ask about the workaround:** After the team describes the official process, ask what they actually do when that process breaks down. The workaround is often the clearest signal of where the real operational pain is.

## What to listen for

Three categories of signals matter most during a discovery session.

**Data signals:** Every system name, file type, or data source the customer mentions is a building block of the technical scope. Note them all without interrupting.

**Volume and frequency:** Ask how often the task is performed and how long a typical run takes. Volume and frequency convert vague pain into a measurable baseline. Without those numbers, there is no basis for estimating the value of the project.

**Ownership gaps:** When no one can say who owns a step in the workflow, that step is a risk. It will surface again during the build, usually at the worst possible moment.

## The 5-column note framework

Capture every observation in five columns: the stated pain, the current workflow steps, the data available, a candidate success metric, and the blockers to accessing what is needed. This structure forces completeness and converts discovery notes directly into the building blocks of a scope document.

## Closing the session well

Before leaving, summarize back what was heard: here is the core problem, here is the data involved, and here is what success would look like. Misalignments surface immediately when the FDE speaks the problem back. Finding them in the session is far better than finding them after the scope document is written.

Use the closing to confirm that the session produced enough to move forward. A session that ends without answers to these four checks carries unresolved risk into the scope document.

### Checklist: before leaving the session

- Does the data required for the system exist, and is it accessible within the project timeline?
- Is there a specific, measurable success criterion that can be verified before the project ends?
- Is the customer’s timeline realistic given what actually needs to be built?
- Is there one person inside the organization who owns the problem, has authority to clear blockers, and will be the main contact throughout?

With a clear picture of the problem in hand, the next question is whether the problem is actually an AI problem.

## Recognizing real AI opportunities

Not every workflow problem is an AI problem. The FDE that treats every customer request as a candidate for AI ends up building systems that deliver little value, or solving problems a simpler tool would have handled in a day.

Modern AI systems, including generative models that produce language and code and agentic systems that execute multi-step tasks using tools, open a much wider range of use cases than earlier automation approaches. The question is whether the workflow problem actually benefits from what these systems do well.

Four signals indicate a use case is genuinely AI-addressable:

**Document-heavy synthesis and extraction:** The task involves reading, summarizing, extracting, or comparing information across large volumes of contracts, reports, emails, or policy documents. Generative models handle this at a scale no human team can match without high cost.

**Knowledge retrieval at scale:** The task requires answering questions from large knowledge bases, applying criteria from policy documents to incoming requests, or routing inputs based on content. Retrieval-augmented systems are a direct fit.

**Multi-step workflows with conditional logic:** The task involves a sequence of dependent steps with conditional decisions at each stage, for example, gathering inputs, applying rules, and routing the output. Agentic systems can coordinate this kind of workflow end to end, reducing what was previously a chain of manual handoffs.

**Repetitive judgment at throughput:** The task follows a consistent decision pattern, the criteria are relatively stable, and the value of automation scales with volume. Classification, prioritization, and routing problems fall here.
