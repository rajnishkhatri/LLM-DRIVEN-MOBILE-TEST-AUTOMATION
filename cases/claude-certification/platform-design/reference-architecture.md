---
type: architecture
title: 'Reference architectures and retrieval vs live state'
description: 'Known-good Claude wiring patterns and the most common misapply: retrieval asked to own transactional state that a tool call to the system of record should own.'
tags: [claude, certification, platform-design, architecture]
---

The shapes the industry has already paid to learn
Choosing a pattern gets you the right structure. Patterns give you the shape. The next question to ask is how that structure connects to everything around it. Reference architectures will give you the wiring.

Reference architectures: what good looks like and where projects go wrong

Reference architectures are references, not blueprints to adhere to. The goal is not matching a problem to a fixed design and implementing it as drawn. Every partner workload is unique, so your goal here is to understand these common patterns well enough to generalize from them. Ultimately, you should be able to take the shape that fits, adapt it to the workload in front of you, and recognize when a workload draws on more than one pattern at once. Most partner problems map to one of a handful of reference architectures already proven in the Claude ecosystem: documented patterns for how to wire an LLM application together to solve a recurring class of problem. The table below covers common reference architectures, what they look like when they're built well, and the failure modes that show up repeatedly.

Expand each pattern to see what good looks like and where projects go wrong.

Agent (see S11)
Retrieval-augmented generation (RAG) (see S11)
Document processing pipeline → Evaluator-optimizer (see S11)
Customer-service / ticket triage → Routing (see S11)
Coding agent (agentic exploration with deterministic edit/test/review steps) (see S11)
Full RAG implementation depth, including chunking strategies, embedding approaches, hybrid lexical-plus-semantic retrieval, and reciprocal rank fusion, is covered in the RAG pipeline design screen that follows.

How to decide if a problem needs one or several patterns

Real partner problems frequently sit at the boundary between two architectures. A routing workflow might hand certain intents to an agentic investigation loop. A document processing pipeline might use RAG over policy text when it hits an exception case. Drawing on more than one pattern is sometimes the right answer.

What matters is why you are reaching for a second pattern. Don't think of patterns as pieces you snap together. Look at why each one works and shape the idea to fit your problem. Draw on a second pattern when the two parts of your problem break in different ways that are worth managing separately. If you are reaching for a second pattern because you haven't decided what problem you're solving, adapt a single pattern instead. That's a design decision you're deferring, not a pattern you're applying.

The most common mistake: retrieval applied to live state

The most common reference architecture mistake is using retrieval where a tool call belongs. You can recognize it by looking for these symptoms: stale chunks, results that shift with each index refresh, answers that contradict what's in the database. A better embedding model or a shorter refresh interval won't fix this issue. Instead, call the system that owns the live state directly rather than retrieving a cached version of it.

COST · COMPLEXITY · RISK
Cost: Composing two reference architectures roughly double the surface area you must maintain. When in doubt, pick one.
Complexity: Each reference architecture carries its own eval contract. You need separate eval sets per architecture, not a single eval set for the composed system. A system that looks healthy at the top level can be masking failures in one of its components.
Risk: Misapplying retrieval to live state produces stale but confident answers. The system looks healthy from the outside: normal latency, no errors. Detection cost is high because there's no signal that something is wrong until a user notices the answer doesn't match reality.
← Prev
Screen 16 of 34
☰ CONTENTS
Next →
When retrieval got reached for instead of a tool call
SETUP HOOK: HOW RAG FAILS WHEN APPLIED TO LIVE STATE
The broader underlying skill here is context engineering: deciding which mechanism is responsible for getting each kind of data in front of the model. Retrieval over a vector index is one example, and this trace shows what happens when it is asked to own data it cannot own. This often happens when a team reaches for RAG because it worked on a previous use case, without stopping to ask whether the new one shares the same properties. RAG works well when the answer lives in a body of reference material that remains stable between index refreshes, e.g., documentation, policy text, product manuals. It breaks for live state because retrieval treats your data as text snapshots, not as a system with current values. When those snapshots disagree, the model picks the most similar one and answers confidently. There is no way to know which snapshot is current. The trace below shows exactly how this plays out.
The trace: electronics retailer customer service assistant

User asks: "Where's my order?"

RETRIEVED CHUNK #1 (similarity 0.78): "Order #88412 was placed on the 11th of June and shipped on the 12th via standard courier. Tracking number AB123…"
RETRIEVED CHUNK #2 (similarity 0.74): "Order #88412 is currently being processed. Expected dispatch within 24 hours."

MODEL OUTPUT: "Your order shipped on the 12th of June via standard courier. Tracking: AB123…"
Both chunks were real strings that existed in the corpus at different points in time. The index conflated them. The order had shipped, been returned to depot due to a damaged label, and was awaiting re-dispatch. Note that this current state appears in neither chunk: the corpus held two stale snapshots and no record of where the order was, because an index captures what was true when it was written, not at the present. A customer service tool to fetch live order status existed in the partner's API. It was not called.

What broke and why

The category error
Retrieval is the right mechanism for knowledge: FAQs, policies, manuals. It's the wrong mechanism for transactional state. Order status wasn't failing because retrieval is broken. It was failing because current state had been represented as historical text snapshots in the first place.
A data-architecture failure, not a retrieval failure
Live state was indexed as text, so the system searched a corpus of past snapshots rather than querying the system of record.
Similarity is not truth
Embedding similarity confidently merged two stale snapshots into one answer. A higher similarity score does not mean a truer answer; it means the retrieved text was semantically close to the query, which is not the same thing when the underlying state has changed since the text was written.
The fix is a tool call
Not a better chunker, a shorter refresh interval, or a higher similarity threshold: a tool call to the order-status service. The knowledge base keeps the FAQ content. The transactional database keeps the orders. Two types of data, two access patterns, two mechanisms.
The retrieval principle

Retrieval is for stable knowledge: things that were true yesterday and will be true tomorrow. Tool use is for live state: things whose current value is owned by a system and changes independently of your index. Conflating them produces answers that are fluent, confident, and wrong in ways that are hard to detect because the system shows no error signal. The model returned a response. The response looked correct. The customer got false information about their own order.

← Prev
Screen 17 of 34
Critique the diagram
PRACTICE: REVIEW A PARTNER'S DRAFT ARCHITECTURE
Below is a reference-architecture sketch of a customer-service assistant. Six components are listed. Select the three that are misapplied for this routing design.
Select exactly 3 components that are misapplied.

1

Intent classifier (Claude call)
↓
↓
2

Retrieval over "Order Status Index"
3

Retrieval over "Product Manual Corpus"
↓
↓
4

Agent loop with tool entry point: refund, cancel, update-address
5

(missing) Escalation path to human agent
↓
↓
6

Response composer (Claude call)
Submit
Skip for now
You read the architecture cleanly. The three problems are a retrieval index standing in for live state, an unguarded high-consequence tool loop, and a missing escalation path, the failures that most often sink a routing design.
← Prev
