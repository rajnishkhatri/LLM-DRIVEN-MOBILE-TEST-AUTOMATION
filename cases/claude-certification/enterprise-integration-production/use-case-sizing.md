---
type: guide
title: 'Use-case sizing and feasibility'
description: 'Size call volume, token budget, model tier, and sensitivity. Scope capabilities to owners, then issue feasible / feasible-with-constraints / not-feasible plus an ROI map.'
tags: [claude, certification, enterprise-integration-production]
---

Use-case sizing and feasibility
The production readiness checklist tells you what a system must achieve to be viable. It covers both the quality of the model's outputs and the reliability of the system around it. Output quality is validated through evals, and system reliability is validated through architecture controls like retries, fallbacks, and circuit breakers. Meeting both bars is what production readiness means.

Sizing tells you whether a specific business problem can meet that bar, and what constraints govern the design. Feasibility fits into one of three states: feasible as scoped, feasible with constraints, and not feasible. Identifying the state correctly is what makes a scoping document useful.

How to size a use case
Sizing a use case means producing a cost model before any code is written. The model does not have to be precise, but it must be accurate enough to validate the architecture against the budget and surface token distribution assumptions before they are formalized.

Four inputs drive the model: call volume, token budget per request, model tier, and sensitivity parameters.

Step 1: Estimate call volume. How many requests are made per day or per month? This number comes from the business requirement, not from the developer's intuition. A customer service agent that handles 1,000 conversations per day produces 1,000 Claude calls per day, plus any multi-turn continuation calls. Get this number from the business owner. A sample dataset will not give you an accurate figure.
Step 2: Set the token budget per request. The token budget has two components: input tokens (system prompt, retrieved context, and user message) and output tokens (expected response length). Model the distribution rather than just the average. If document lengths vary widely, the cost model should account for the typical cases as well as the extremes. If the system prompt is long and stable, prompt caching can meaningfully reduce input costs. Caching requires explicit cache_control markers in the request. Cache writes incur a higher per-token cost than standard input, so the cost model must account for the write cost on first use. The default cache TTL is 5 minutes; workloads with request frequency lower than TTL will not realize consistent caching savings.
Step 3: Project the monthly cost. Multiply call volume by the input token count at the input token rate. Separately, multiply the output token count at the output token rate. Then, add both figures. Input and output tokens are priced at different rates on all model tiers. If prompt caching applies, use the cache read rate for cached input tokens, not the standard input rate. Verify current rates at platform.claude.com/docs/en/about-claude/pricing before finalizing the model. Add caching savings if applicable. Compare the result to the cost ceiling from the production readiness checklist. If the projection exceeds the ceiling, the architecture needs to change before a line of code is written. If, for example, Batch API provides a 50% price reduction relative to standard API pricing and supports up to 100,000 requests per batch, model it as a cost alternative for any workload where the SLA permits asynchronous processing. For regulated workloads, verify whether batch processing is covered under the partner's BAA and compliance configuration before routing PHI or similarly governed data through it. Find the most current Batch API discount rate and batch size limit at platform.claude.com/docs/en/about-claude/pricing.
Step 4: Run sensitivity analysis. What happens to cost if call volume doubles? What if the token distribution shifts toward the tail? Sensitivity analysis tells you how fragile the cost model is and where the assumptions need to be verified with the business owner before committing to the design.
How to scope a use case
The discovery sequence for turning a business requirement into a scoped architecture runs in four steps. Skipping any step produces a commitment that will not survive the next conversation with the business owner.

Step 1: Business requirement to capability list. What does the system need to do? Name each capability separately. "Process insurance claims" is a goal. The capabilities might include extracting structured fields from the claim document, looking up policy coverage from the policy database, routing the claim to the appropriate adjuster queue based on claim type and value, and drafting the adjuster notification. Identify them separately so you can assign each to the appropriate owner.
Step 2: Capability list to architecture sketch. For each capability, decide where it belongs. Which capabilities does Claude own? Which belong to existing systems? Which require a human in the loop? This is the decomposition step from Module 1, applied to a specific use case.
Step 3: Architecture sketch to boundary conditions. State the conditions under which the architecture works and the conditions under which it does not. Feasibility is a verdict plus the constraints that make the verdict true. An architecture that works for documents up to 20 pages but fails for longer documents has a boundary condition that must be documented.
Step 4: Boundary conditions to scope in the SOW. The statement of work contains the boundary conditions. This ensures that the development team and the business owner both understand what the system is designed to handle and what it is explicitly out of scope.
How to conduct a technical feasibility assessment
A feasibility assessment that only asks "can Claude do this" is a capability check. The four AI properties give you a structured way to identify where the design will require compensating controls, and what those controls should be.

Select each property to see the feasibility question it raises and where the design compensates.

Next-token prediction
Knowledge
Working memory
Steerability
The feasibility question to ask: Are the instructions specific, concrete, and verifiable? Abstract or ambiguous instructions, long reasoning chains, and tasks that require precise numerical or logical computation are all places where the model can drift from intent.

Where design compensates: System prompts with explicit output schemas; structured outputs; code execution for numerical precision; evaluator-optimizer loops.
Feasibility verdicts
Once the scoping sequence and technical assessment are complete, the architecture is ready for a feasibility assessment. There are three possible outcomes.

Verdict	What it means	What to document
Feasible as scoped	The arguments across the four AI properties favor Claude for each capability. The cost model is within the ceiling. The latency p95 is within the SLA. No capability requires a compensating control that changes the architecture.	State the assumptions clearly. Feasible-as-scoped verdicts become infeasible-with-constraints when assumptions change.
Feasible with constraints	The design works under specific conditions that must be enforced. The document length must stay under a threshold. The retrieval index must be refreshed on a defined schedule. A human review gate must exist for outputs above a confidence threshold. The constraints are part of the architecture.	Document each constraint explicitly. For each violated constraint, identify the failure mode. The development team needs to know what they are designing for, not just what they are building.
Not feasible	At least one capability faces an AI property limitation that cannot be compensated for within the scope and budget. The cost model exceeds the ceiling by a margin that cannot be closed by model tier, caching, or architecture changes. A not-feasible verdict is a correct assessment that saves the engagement from a more expensive failure later.	State which constraint is disqualifying and why. Where a scope reduction would change the verdict, name it and present the business owner with a choice.
Business value and ROI mapping: turning a feasible design into a justified investment
A feasibility verdict tells the business owner that the system can be built within the budget and the constraints. It does not tell them whether building it is worth doing. Determining business value and ROI mapping are the steps that answer that second question. They connect the scoped architecture to the financial and operational outcomes the business expects, expressed in terms the business owner already uses: hours saved, error rates reduced, cycle time shortened, or revenue protected. The mapping turns a technical design into a decision a budget holder can defend.

The business case rests on five main pillars, and identifying them keeps the ROI conversation in the language the blueprint and the business owner both use: efficiency (the same work done faster or cheaper), transformation (work that was not feasible before becoming possible), productivity (more output from the same people), solution cost (the run cost of the system itself), and performance SLAs (the service levels the deployment must hold). Map each ROI claim to the pillar it advances so the value statement captures both the number and the kind of value it represents.

The mechanism is a comparison between two states. The baseline state is how the work is done today, measured in the unit the business cares about. The projected state is how the work is done once Claude is in the workflow, measured in the same unit. The value is the difference between the two states, minus the cost of running the system. The cost figure comes directly from the sizing model produced earlier in this cluster, so the ROI calculation reuses work you have already done rather than starting over.

The mapping is built in four steps, and each step must be grounded in a number the business owner will recognize:

Step 1: Name the baseline in a business unit. Start from how the task is performed today and measure it in the unit the business already tracks. For a claims review workflow that is the analyst hours per claim or the average days to resolution. The baseline must come from the business owner's own operational data, because every later number is compared against it. A baseline pulled from intuition produces an ROI figure no finance team will accept.
Step 2: Predict the post-deployment state in the same unit. Estimate how the same task performs once Claude is in the workflow, measured in the identical unit as the baseline. Where the feasibility verdict requires human review, the projection must include that cost. Routing low-confidence output to a reviewer reduces labor, but it does not eliminate it entirely. When the design specifies human-in-the-loop review, projecting full automation overstates the value and produces a number operations will reject.
Step 3: Subtract the run cost from the sizing model. Take the projected monthly cost produced during sizing and treat it as the recurring cost of the new state. The value of the deployment is the operational gain from Step 2 minus this run cost. This step isolates recurring run cost only. Build cost is treated separately and is accounted for in the payback period calculation in Step 4. Including the sizing output in the ROI calculation keeps the two analyses consistent. A change to the token budget or model tier then updates both the cost ceiling and the value case together.
Step 4: State the payback period and the sensitivity. Express the result as a payback period, which is the time it takes for the accumulated operational gain to cover the build cost and the run cost. Then state how that period moves if the volume assumptions or the gain-per-task assumptions are wrong. Quoting a payback period without sensitivity analysis invites decisions based on a single optimistic scenario, one that often fails when the business case meets real volumes after launch.
The output of the mapping is a short value statement the Architect hands to the business owner alongside the feasibility verdict. It ties the answers to "Can we build this?" and "Is it worth building?" back to numbers the business already owns. The two artifacts travel together into the statement of work.

These are the most common ROI map errors, what causes them, and where they tend to appear.

Risk	Why it happens and where it shows up
The baseline is estimated rather than measured.	When the business owner does not have clean operational data, the baseline gets filled in from intuition. This makes the apparent gain misleading. The error stays hidden until the finance team asks for the source of the baseline number during business case review. At this point the whole case must be rebuilt.
The projection assumes full automation when the design requires human review.	A feasibility verdict that requires a human review gate means the labor is reduced, not fully eliminated. The value case often misleadingly models it as eliminated. The gap surfaces in the first operational period after launch, when actual analyst hours fail to fall as far as the business case promised.
The run cost is taken from an average rather than the sizing distribution.	Reusing an average token cost instead of the distribution from the sizing model understates the recurring cost, which overstates net value. This concentrates on workflows with heavy-tailed inputs, where a small fraction of large requests drives most of the cost.
COST · COMPLEXITY · RISK
Cost: Sizing based on average token counts will underestimate cost when some requests are much larger than others. Getting this wrong means renegotiating the architecture after the contract is already signed.
Complexity: A feasibility assessment that skips any of the four AI properties risks missing a constraint that changes the design. Working memory is the most overlooked, since it rarely shows up during development on small, clean inputs, but it will surface in production.
Risk: A feasible-with-constraints verdict that is not documented becomes an infeasible system when the constraints are violated in production. The constraints are part of the design and carry the same weight as the architecture they qualify.
← Previous
Screen 8 of 21
☰ CONTENTS
Next →
