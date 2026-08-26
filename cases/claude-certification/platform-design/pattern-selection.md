---
type: architecture
title: 'Pattern selection: augmented call, workflow, or agent'
description: 'Choose Claude''s involvement shape on predictability vs autonomy. Walk five factors in sequence; the first that rules a pattern out is the deciding one.'
tags: [claude, certification, platform-design, architecture]
---

Composing primitives into augmented call, workflow, agent
Once you've established which parts of a task Claude owns versus what your systems and people own, the next decision is structural: what shape does Claude's involvement take?

There are three patterns to choose from: an augmented LLM, a workflow, and an agent. Each one takes a different position on two axes: predictability (how predictable the path through the work is) and model autonomy (how much autonomy you're willing to hand to the model).

Three patterns for structuring Claude's involvement

Augmented LLM
Workflow
Agent
A single model invocation: you send the request, the model completes the task, and your code handles the wiring around it. You can add tool use, retrieval, or extended thinking to that call, but the model is still doing one bounded job in one pass. The control flow never branches based on what the model decides. Use this when the task is well-defined, the output is something you can verify, and there's no reason to split the work across multiple steps.
Mapping use cases by predictability and autonomy

Plot any use case on two axes: how predictable the path is, and how much autonomy you are willing to grant the model.

HIGH
LOW
LOW PREDICTABILITY
HIGH PREDICTABILITY
MODEL AUTONOMY
AGENT
High autonomy, low predictability. The model owns the trajectory.
WORKFLOW
Predictable shape; bounded model judgment inside each step.
AUGMENTED LLM
High predictability, low autonomy. One bounded model call.
Augmented LLMs sit in the high-predictability, low-autonomy quadrant. You know the task, you know what good looks like, and the model executes it once.

Workflows occupy the middle band. The overall shape is predictable, but each step may involve model judgment in a contained way.

Agents sit in the high-autonomy, low-predictability corner. This is the pattern to reach for when enumerating the steps in advance and is the expensive part of the problem: open-ended investigation, long-horizon work, and tasks where the next move depends on what the last one turned up. Claude Code is a production-proven example: it explores an unfamiliar codebase, decides which files to read based on what it has already found, and runs multi-step engineering work that no one could script ahead of time. That is the capability agents unlock, but the associated cost is just as real. This is where non-deterministic failures concentrate in production, because the model's trajectory is the control flow and there's no code boundary where a guard can sit.

Sub-patterns within workflows

Choosing a workflow doesn't fully specify the design. There are four shapes a workflow can take, and each reflects a different assumption about how the steps relate to each other.

Sub-pattern	Shape	When it earns its place	Examples
Chaining	Step 2 takes step 1's output as its input, working sequentially and linearly.	Use this when the task naturally decomposes into stages with clear handoffs, such as extract, then classify, then summarize. Each stage has a defined output that the next stage consumes.	A contract review pipeline: the first call extracts all obligations and deadlines from the raw document, the second classifies each by risk level, and the third drafts a summary memo for the lawyer. Each stage has a clean output the next stage consumes.
Routing	A classifier, often Claude itself, decides which downstream path to take.	Use this when inputs vary in kind and different kinds require different handling.	An incoming support ticket arrives: A classifier reads it and routes billing questions to a retrieval index over account data, technical issues to a retrieval index over product documentation, and escalations directly to a human queue. The same input entry point, three different handling paths.
Parallelization	Multiple model calls run concurrently; results are aggregated or voted on.	Use this when sub-tasks are independent and can run at the same time. Reviewing multiple files or reviewing distinct sections of a long document fits this shape because neither sub-task depends on the other's output.	A due diligence review across twelve supplier contracts: Each contract is sent to a separate model call simultaneously. All twelve results are returned and aggregated into a single risk report. No call depends on another's output, so there's no reason to run them sequentially.
Evaluator-optimizer	One model call produces a first attempt at the output. A second call evaluates it and requests revision. The loop repeats until a quality criterion is met or a retry limit is reached.	Use this when quality is verifiable but a single attempt isn't reliable enough. Code generation ran against a test suite, or structured-output extraction with a strict schema, are common applications.	A model drafts a response to a customer complaint. A second model call grades the draft against a rubric (does it name the specific issue, take ownership, offer concrete next steps in the brand's tone) and checks whether the output matches the expected structure. If it doesn't, the evaluator returns specific feedback and the generator rewrites. The loop exits when every rubric item passes or hits a retry limit.
These four patterns aren't mutually exclusive. Most production workflows combine more than one pattern, and the right choice is usually the simplest one that meets the error tolerance and observability requirements of the task, and revisit that choice once you have production data; escalate only when measurement shows the simpler pattern falling short.

A framework for choosing the right pattern: five factors in sequence

Walk through these five factors in sequence. For each one, ask whether the factor rules out any of the three patterns – Augmented LLM, Workflows, Agent. The first factor that rules out a pattern is the deciding one. The table below shows what each pattern costs you on each factor, so you can see exactly where the tradeoffs land.

Factor	The question to answer	Augmented LLM	Workflow	Agent
Predictability	Can you enumerate the steps in advance?	Low: single bounded task.	Low: you wrote the path.	High: trajectory is unpredictable by design.
Error cost	What does a wrong answer cost: a retry, an audit, a lawsuit?	Medium: exposes you to the model's output distribution without step-level guards.	Low: deterministic guards sit between steps.	High: exposes you to the full output distribution across multiple turns.
Observability	Can your operations team see what happened and reconstruct why?	Medium: a single call is easy to log but opaque inside.	Low: steps log as code does, with standard tooling.	High: the trajectory reads like a transcript; most current observability tooling isn't built to alert on this.
Latency budget	What is the user-visible deadline?	Low: fastest in standard configurations, though extended thinking or retrieval adds time.	Medium: predictable but additive in duration.	High: runtime is open-ended; budget for the worst case, not the median.
Cost	What's the per-request token cost at your expected volume?	Low: fewest tokens per request.	Medium: scales with step count.	High: iterative reasoning, multi-turn tool use, retries, and growing context can materially increase token usage and latency. Poorly bounded agents are often the most expensive pattern.
Try prompting before you consider fine-tuning

If prompting feels unreliable, the instinct for many engineers is to reach for fine-tuning. On Claude, that's usually the wrong first move. Work through this sequence first:

Optimize the prompt. Most reliability problems are prompt problems.
Add tool use or retrieval if the prompt alone isn't enough.
Move to a stronger pattern like an evaluator-optimizer if quality still isn't where it needs to be.
Only then consider fine-tuning.
Fine-tuning does have a place, but in specific situations:

The task runs at very high volume and inference cost is the real constraint.
Latency is critical and a smaller specialized model will outperform a prompted general one.
The output needs to follow a consistent format and prompting hasn't solved it reliably.
Outside those situations, fine-tuning locks you to a fixed model version and narrows your options without much to show for it. Treat it as the last step in a deliberate progression, not a quick fix for a prompt that isn't working yet.

NOTE ON AVAILABILITY
Fine-tuning Claude is not broadly available. Access is limited, varies by model and delivery route, and changes as Anthropic expands the program. Confirm current options with the Anthropic account team before recommending this path to a partner.
These three patterns are not abstract categories. Each is an assembly of the primitives you inventoried in the foundations section: an augmented call is the model plus tools; a workflow is primitives wired together in your own code; an agent is the model choosing its own sequence of tool calls. Choosing a pattern is choosing how to compose those parts.

Skills-based architecture as a packaging option

Alongside choosing a pattern, decide how the capability is packaged. Three options sit on a spectrum: a prompt-only solution (instructions alone), direct tool use (the model calls functions in your code), and a Skills-based architecture (a versioned, reusable Skill that packages the procedure, its instructions, and any scripts as one governed unit). Reach for a Skill when the same procedure runs repeatedly, needs to be distributed across teams or products, or must be versioned and governed.

Apply the Delegation lens to the pattern itself: does this pattern grant Claude appropriate or excessive decision authority for the risk profile in front of you? An agent that can act autonomously is the right choice only when the stakes and reversibility of its actions justify the autonomy it is given.

COST · COMPLEXITY · RISK
Cost: Agents don't automatically cost more than workflows. What drives cost is how much context accumulates across the conversation and how many model calls are made. A poorly designed workflow can cost more than a well-designed agent. Design matters more than the pattern label.
Complexity: Workflows and agents fail in different ways. A workflow fails when a step in your code fails. An agent fails when the model makes a bad decision somewhere in a sequence of turns. That second type of failure is harder to spot and harder to diagnose, and your standard debugging tools won't catch it the same way.
Risk: An agent's autonomy is your liability surface. An agent can do anything its tools allow, including combinations you didn't test for. The broader the tool permissions, the larger the space of things that can go wrong. Keep the tool entry point as narrow as the task allows.
← Prev
Screen 11 of 34
☰ CONTENTS
Next →