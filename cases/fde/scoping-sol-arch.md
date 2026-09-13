---
type: handbook
title: 'Scoping and solution architecture'
description: 'Six scope elements, a five-level translation ladder from business pain to a minimal AI component, and a scoping spike when data is still unclear. Architecture selection belongs in the scope document.'
tags: [fde, handbook, scoping, architecture]
---

# Scoping and solution architecture

**See also:** [discovery session](foundations.md)

Discovery produces the problem picture. The scope document is the contract that keeps that picture from drifting during the build.

## What a scope document does

Six elements belong in every scope document. Each one answers a question that will otherwise remain ambiguous during the build:

**Problem statement:** One or two sentences describing the specific workflow problem the system will address, written in the customer’s own language.

**Success metric:** A specific, measurable criterion that determines whether the project succeeded. For AI systems, this means a quality threshold, such as a precision or recall rate, an error reduction percentage, or a processing speed target, that the team can evaluate against a defined test set before the demonstration.

**Data sources:** What data the system reads from, where it lives, and who controls access to it.

**Technical dependencies:** The internal APIs, data storage systems, authentication services, and external model APIs that the build requires. For AI projects, this includes the language model provider, any retrieval or vector storage infrastructure, and the customer’s internal systems the component needs to read from or write to.

**Out of scope:** An explicit list of what will not be built in this version.

**Timeline:** The date by which something demonstrable will be ready.

The out-of-scope section is load-bearing. When a customer asks to add a requirement mid-build, the out-of-scope section is what the FDE points to. Without it, every new request is a reasonable one.

With the document structure clear, the next step is deciding what actually goes in it.

## Translating the problem into a solution

The translation ladder is a five-level framework that converts a business problem into a buildable AI component. Each level narrows the problem by answering a more specific question about the workflow, the data, and the technical environment. Working through all five levels before writing the scope document prevents two common failures: building the wrong thing because the business pain was taken at face value, and building too much because the AI component was not isolated from surrounding workflow steps that do not need to change.

### Scenario: contract review for a legal firm

To illustrate how the five levels work in practice, consider a legal team that currently spends three hours reviewing each incoming vendor contract against the firm’s standard terms.

| Level | Question the level answers | In this scenario |
|---|---|---|
| Business pain | What is failing for the organization? | A legal-team review bottleneck is delaying vendor onboarding by days and creating a backlog the team cannot clear. |
| User workflow | What does the person actually do? | A lawyer reads each contract, checks it against the firm’s standard terms, flags deviations, and routes it to the appropriate approver. |
| Data flow | What moves, in what form, where? | Contracts arrive by email as PDFs. Standard terms live in a shared drive. Approvals are tracked in a spreadsheet. |
| System integration | What must the solution touch? | The solution needs to interact with the email inbox, the document storage, and the approval workflow. |
| AI component | Where does the model add value? | A system that extracts key clauses from incoming contracts, compares them against the standard terms, and produces a structured deviation report for the lawyer to review. |

### The minimal AI component

The minimal AI component principle identifies where the model adds the most value without requiring the most integration work. In the example above, clause extraction and comparison do the heaviest lift. The approval routing and email integration can remain manual in the first version. Targeting the highest-effort step first produces the most measurable improvement with the least build complexity.

### Scoping spike

When the data situation remains unclear after discovery, a scoping spike resolves it before the scope document is finalized. A scoping spike is a one-to-two-day investigation: confirm what data is accessible, what format it is in, and whether it is clean enough to work with. It is the final information-gathering step before committing to a scope.

With the problem translated into a specific AI component, the FDE selects the architecture that fits it.

## Selecting the right AI architecture

The architecture selection is one of the most consequential decisions in an FDE project. It determines build complexity, data requirements, latency, evaluation methodology, and operating cost. The right architecture is the one that fits the problem and can be delivered within the constraints of the customer environment. This decision belongs in the scope document.

Four common patterns and the signals that point to each:
