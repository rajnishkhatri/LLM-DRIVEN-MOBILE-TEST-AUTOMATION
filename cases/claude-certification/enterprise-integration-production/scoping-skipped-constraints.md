---
type: failure-taxonomy
title: 'Watch-out: the scoping call that skipped the constraints'
description: 'Failure trace: capability was confirmed before volume, document length, and latency were gathered. The verdict was issued before the design was possible.'
tags: [claude, certification, enterprise-integration-production]
---

The scoping call that skipped the constraints
THE DEMO TRAP
When a business owner is excited about a use case and the initial demo works, confirming feasibility before gathering the volume and SLA constraints feels like the efficient path. The capability is there, the prototype is working, and slowing down to ask about constraints can feel like looking for reasons to say no. The problem is that "technically feasible" is meaningless if the constraints aren't applied to the expected scale.
A scoping conversation: Commitment made too early
The following is an extract of a pattern that surfaces in discovery calls when the capability question is answered before the constraint questions are asked.

Partner: "We need a document review assistant that can process our legal contracts and flag non-standard clauses."
Architect: "We can do that. The model is good at reading contracts and identifying clause patterns. Let me put together a feasibility write-up."
Partner: "Great, how long will the build take?"
Architect: "Six weeks for the initial version."
[Two weeks into the build]
Partner: "I should mention: we process about 800 contracts a day. Some of them are framework agreements that run to 300 pages. And we need results in under 30 seconds."
What went wrong
The feasibility verdict was issued before three essential constraints were gathered: call volume (800 per day), input size (up to 300 pages), and latency requirement (30 seconds).

Whether a lengthy contract fits within the context window depends on the model tier selected. Models with a 1 million token context window can handle a 300-page contract without chunking; a model with a 200k token window may require a chunking strategy for the longest documents. Context window capacity is therefore part of the model tier decision, not a settled assumption.

At 800 requests per day, the 30-second latency requirement is not as limiting as it seems. This averages out to one request every 108 seconds. Sequential processing is viable at that volume without running requests in parallel. At that request rate, volume pressures cost, not latency. Latency is driven by task complexity, model size, and output length. Those are the variables the model tier decision needs to be built around.

The architect confirmed capability as a necessary first step, but it was also the last step, which meant the commitment was made before the design was possible.

WHAT TO WATCH OUT FOR
The capability question was answered before the questions were even asked. The volume, latency, and input-size constraints are inputs to the feasibility verdict. The verdict is only as sound as the constraints gathered before it.
← Previous
Screen 9 of 21
☰ CONTENTS
Next →
