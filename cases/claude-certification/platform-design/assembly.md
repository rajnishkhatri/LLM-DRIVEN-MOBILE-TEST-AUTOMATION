---
type: analysis
title: 'Cumulative assembly: contract-review architectures'
description: 'Four complete architectures for a mid-market law-firm contract-review brief. Only one holds on entry point, pattern, split of work, model/context, and human-in-the-loop.'
tags: [claude, certification, platform-design, analysis]
---

A contract-review system for a mid-market law firm
Four complete architectures are described below. Each one commits to all five design decisions the module covered: the platform entry point, the pattern, how the work is split across Claude, existing systems, and humans, the model and context strategy, and the human-in-the-loop posture. Only one holds up against the brief. The other three each look reasonable but fail on a single decision. Pick the one you would put in front of a partner-side review committee.

THE BRIEF
A 180-lawyer mid-market law firm wants to speed up contract review. Their senior associates currently spend an estimated 12 to 18 hours per week reading vendor and partnership contracts to flag clauses that conflict with the firm's standard playbook. Average contract length is 35 pages. The current output is a redlined PDF with margin comments. The firm uses iManage for document storage, has a private LLM gateway approved by their CIO, and is bound by attorney-client privilege requirements that exclude consumer-grade tools. The target is to cut associate time per contract by 60% while keeping the senior associate as the final reviewer.
Step 1: draft your architecture

Before reading the four options, draft your own architecture for the law firm. In one paragraph, cover all five decisions: the platform entry point, the pattern, how the work is split across Claude and existing systems, the model and context strategy, and the human-in-the-loop posture.

Click-to-reveal an answer to compare with your response; feel free to ask Claude to compare what you've written with the provided answer.

Your architecture

Reveal the model answer
Build on the direct API or SDK, embedded in a thin internal web app that authenticates via the firm's SSO and routes through the approved LLM gateway. A parallelized workflow reviews the contract section by section, with an evaluator pass enforcing a strict schema on the flagged-clauses output. Claude handles extraction, classification against the playbook, and draft redlines. The playbook stays in the firm's systems as a versioned source of truth, retrieved per clause at call time. iManage handles document fetch. Sonnet is the default with progressive context, extended thinking enabled per clause only where an eval set justifies it. The senior associate signs off on every output, and low-confidence clauses are flagged for attention.
Step 2: which of the four options matches your design most closely?


Option A. Build on Claude.ai, with associates uploading each contract into a Project that holds the playbook as reference files. A parallelized workflow reviews the contract section by section and aggregates the flagged clauses. Sonnet is the default model with progressive context. The senior associate reviews every output before anything goes to a client.

Option B. Build on the direct API or the SDK, embedded in a thin internal web app that authenticates via the firm's SSO and routes through the approved LLM gateway. The playbook is loaded into the system prompt in full on every call so the model always has the firm's standard in context. A parallelized workflow reviews the contract by section and aggregates results. Sonnet is the default. The senior associate reviews every output.

Option C. Build on the direct API or the SDK, embedded in a thin internal web app behind SSO and the approved gateway. An open-ended agent is given the contract and the iManage tools and left to decide for itself how to work through the document. The playbook is retrieved per clause at call time. Opus runs on every call for maximum accuracy. The senior associate reviews every output.

Option D. Build on the direct API or the SDK, embedded in a thin internal web app that authenticates via SSO and routes through the approved gateway. A parallelized workflow reviews the contract section by section, with an evaluator pass enforcing a strict schema on the flagged-clauses output. Claude handles extraction, classification against the playbook, and draft redlines. The playbook stays in the firm's systems as a versioned source of truth, retrieved per clause at call time. iManage handles document fetch. Sonnet is the default with progressive context, extended thinking enabled per clause only where an eval set justifies it. The senior associate signs off on every output, and low-confidence clauses are flagged for attention.
Option A: Claude.ai is the privilege failure. The firm is bound by attorney-client privilege requirements that exclude consumer-grade tools, so the entry point is wrong before any of the downstream choices matter. The pattern, model, and human gate in this option are all reasonable, which is what makes the entry point mistake easy to miss. Re-read the entry point-selection section, then choose again.

Option B: This one gets the entry point, pattern, model, and human gate right, but it loads the entire playbook into the system prompt on every call. That is the knowledge-limitation failure: the playbook changes and a copy frozen in the prompt goes stale, and it pays to reprocess the whole playbook on every request. The fit move is to keep the playbook in the firm's systems as a versioned source of truth and retrieve the relevant sections per clause. Re-read the decomposition section, then choose again.

Option C: The entry point and the human gate are right, but two decisions break it. An open-ended agent here is the "we want flexibility" failure: the work decomposes cleanly into independent sections, so a parallelized workflow fits and the agent's open-endedness is paid for and never used. Running Opus on every call is the bill-arrived failure: Sonnet is the default, and you move up only when an eval set says you have to. Re-read the pattern and model-selection sections, then choose again.

Option D (correct): This architecture would hold up to a partner-side review committee. The entry point respects privilege and fits the users, the parallelized workflow matches work that splits cleanly by section, the playbook stays where it can be versioned and is retrieved per clause, Sonnet with progressive context holds the cost line as document volume grows, and the senior associate stays the final reviewer with low-confidence clauses surfaced for attention. Every decision constrains the next, and this is the only option where all five hold together.

Submit
Skip for now
Correct, Option D. The only option where all five decisions hold together.
← Prev
Screen 31 of 34
☰ CONTENTS
Next →

See also: [Glossary](glossary.md) · [Key takeaways](takeaways.md)