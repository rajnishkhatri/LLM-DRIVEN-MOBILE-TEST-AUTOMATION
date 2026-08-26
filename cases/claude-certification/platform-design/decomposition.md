---
type: guide
title: 'Decomposition: Claude vs systems vs humans'
description: 'Assign each part of a partner request to Claude, an existing system, or a human. Over-assigning to Claude is the most common and expensive early mistake.'
tags: [claude, certification, platform-design, guide]
---

Where Claude fits (Claude / systems / humans)
When you're architecting a solution for a partner, you're already making three kinds of decisions: what the ask is, which systems you have available to address it, and where human judgment needs to be involved. This module adds a fourth decision: determining where Claude can help.

That fourth decision is one architects get wrong because they lack deep understanding of Claude's predictable strengths and failure modes. The goal of this module is to give you a concrete decision framework to determine where "Claude can help" with specificity.

Who does what? Every solution has three owners: assigning them early sets you up for success

Every solution you architect with Claude lands in one of three buckets:

Owner	What belongs here
What Claude does	The work that benefits from language understanding, summarization, planning, drafting, or tool-mediated action.
What existing systems do	Anything your partner has already paid to make reliable: the order-status service, the policy engine, the rules table, the database of record.
What humans do	The judgment calls, the exception paths, the approvals, the moments where being right matters more than being fast.
Architects sometimes collapse all three into "what Claude does", but over-assigning tasks to Claude almost always makes the process more expensive, slower, and harder. The key is knowing what Claude does best and what it should be responsible for in your solution.

Delegation: deciding what Claude is trusted to own

Decomposition produces a delegation map. For each part of the request you decide not just whether Claude can do it, but whether Claude should own it: AI-appropriate work, human-retained work, or collaborative work where Claude drafts and a person decides. Justify each assignment through:

Reversibility: Can a wrong call be undone?
Stakes: What does a wrong call cost?
Accountability: Who must answer for it?
This screen will teach you the discipline of delegation, the first of the four AI Fluency competencies. The four behavior properties that tell you what Claude can be trusted with were taught in the foundations section; here you will apply them.

SCENARIO: DECOMPOSING A PARTNER REQUEST, ASSIGNING EACH STEP TO THE RIGHT OWNER
A partner asks for a "claims triage assistant that reads a claim, decides priority, looks up policy coverage, and emails the adjuster." An architect's first instinct might be to put all four steps in the "What Claude does" bucket, but the four-properties lens stops this from happening:
"Read the claim." This is squarely in Claude's capability zone. Reading and interpreting a claim is pattern-rich language work, and if the output schema is constrained, both next-token prediction and steerability are working in your favor. This is work that Claude does.
"Decide priority." This step may appear like a language task, but it isn't. Priority is a deterministic rule your partner already defines and maintains. What counts as priority in the partner's organization lives in a rule engine, not in Claude's training data. Routing this to Claude introduces an unnecessary knowledge limitation. Instead, Claude calls the rule engine and the existing system does the work to decide priority.
"Look up policy coverage." This runs into the same problem as priority, but with higher stakes. Policies change and coverage tables get updated, and the model has no reliable way to know when the version it learned during training stopped being current. The answer must come from the system that holds the live coverage data, retrieved through tool use or an MCP server.
"Email the adjuster." This step needs to be split up. Drafting the message is language work and is something for Claude to do. Sending the message belongs to the email system. A human should review and approve anything above a value threshold, because if Claude decides on its own, its working-memory and steerability limitations both become risks.
Decomposition should be driven by answering the question "where do the four properties argue for Claude over the system that already does this right?" rather than "Where can Claude help?" Pay close attention to this shift in framing, it the key concept this module is building towards.
COST · COMPLEXITY · RISK
Cost: Every lookup that a simple deterministic system could have handled gets sent to Claude instead. You end up paying for the model to do work that a database query or a rules table could have done for a fraction of the cost, and across thousands of requests that can add up fast.
Complexity: When you move logic out of a table-driven system and into the model, errors stop being traceable. A deterministic rule fails in a predictable, debuggable way. A model handling the same job produces variable outputs that are much harder to observe and diagnose.
Risk: The model has no reliable way to know when its information is out of date, and it will not flag the gap. When the model becomes the source of truth instead of the partner's actual system, authoritative answers can drift quietly, with no error thrown and no warning raised.
← Prev
Screen 7 of 34
☰ CONTENTS
Next →