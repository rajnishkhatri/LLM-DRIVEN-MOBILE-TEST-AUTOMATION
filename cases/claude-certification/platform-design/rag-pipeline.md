---
type: architecture
title: 'RAG pipeline: chunking, indexing, and hybrid retrieval'
description: 'Chunk by corpus structure (fixed-size, semantic, hierarchical); index by query pattern (dense, sparse, hybrid). Reciprocal rank fusion is the defensible merge default.'
tags: [claude, certification, platform-design, architecture]
---

Chunking and indexing
The previous screen on reference-architectures named RAG as a known-good shape and showed where it is misapplied. This screen goes one level deeper, into the design of the retrieval pipeline itself: how a corpus is broken into chunks, how those chunks are indexed, and how the retrieval strategy is matched to the query patterns the system will see.

Chunking: how you break the corpus, by what the corpus is

A chunk is the unit that gets retrieved. The chunking approach is chosen by the structure of the source material, not by a default size.

Chunking approach	How it works	When it earns its place
Fixed-size	Split into uniform spans (with overlap) regardless of structure.	Homogeneous, unstructured text where natural boundaries are weak; simplest to operate.
Semantic	Split on meaning boundaries, topic shifts, sentence groups that hang together.	Prose where a retrieved chunk must be self-contained to answer well; reduces mid-idea cuts.
Hierarchical	Preserve document structure, sections, subsections, and retrieve at the level that fits.	Structured documents (contracts, manuals, policies) where section context carries meaning.
Indexing: how you make chunks findable, by how queries are phrased

Indexing decides what "similar" means when a query arrives. The strategy is chosen by the query pattern.

Indexing strategy	What it matches	When it earns its place
Dense (embeddings)	Semantic similarity, meaning, not words.	Queries phrased differently from the source; paraphrase, intent, concept matching.
Sparse (keyword, e.g. BM25)	Exact terms, identifiers, codes, names.	Queries that hinge on specific tokens: part numbers, statute citations, error codes.
Hybrid	Both, with the results combined.	Mixed query patterns, the common production case; recovers the exact-match results dense retrieval misses.
When a hybrid index returns two ranked lists, they must be merged into one. Reciprocal rank fusion is the standard, low-tuning way to do it: each result is scored by its rank in each list, and the combined score favors items that rank well in both. The point for an architect is combining dense and sparse results is a design decision with a known, defensible default.

Articulating the trade-off

Every retrieval design makes trade-offs among three things:

Retrieval quality: Does the right chunk come back?
Latency: How long does retrieval add to each request?
Maintenance: How much does the pipeline cost to keep correct as the corpus grows and changes?
Smaller chunks and hybrid indexing tend to raise quality and latency together; larger chunks and dense-only indexing lower latency and maintenance but miss exact-match queries. There is no universally right point, only the point that fits this corpus and these queries, stated as a trade-off you can defend.

COST · COMPLEXITY · RISK
Cost: Hybrid indexing and smaller chunks raise both retrieval compute and per-request latency. Size the pipeline to the query patterns you actually have, not to the most thorough one imaginable.
Complexity: Every chunking and indexing choice is something to maintain as the corpus changes. A pipeline that was correct at launch can degrade silently as documents are added.
Risk: The failure mode is a confident answer built on the wrong chunk. Retrieval quality is not visible in the output, it has to be measured against a labeled set, which is why this work ties straight to evaluation.
← Prev
Screen 19 of 34
☰ CONTENTS
Next →
Design the RAG pipeline
THE BRIEF
A professional-services partner has a corpus of roughly 4,000 documents: client engagement contracts (highly structured, section-numbered), past project write-ups (long-form prose), and a methodology handbook (structured, with defined procedures). Their team asks three kinds of question: "what does our methodology say about X?" (concept lookup), "find the clause about termination in the Acme contract" (exact-target lookup), and "summarize how we've handled engagements like this one" (broad synthesis across write-ups).
Draft your pipeline design. For each of the three document types, name the chunking approach you would use and explain why. Then name the indexing strategy for the full corpus and state the trade-off you are making. Write your answer before clicking to reveal the model answer.

Feel free to ask Claude to compare what you've written with the provided answer.

Your pipeline design

Reveal the model answer
Skip for now
Contracts and methodology handbook: Hierarchical chunking that preserves section and subsection structure. Both sources are structured and section-numbered, so retrieving at the section level keeps the clause or procedure intact and self-contained. Fixed-size chunking cuts across section boundaries and loses the structural context the query depends on.

Project write-ups: Semantic chunking on meaning boundaries so each retrieved chunk is self-contained. Long-form prose has no section numbers to anchor hierarchical chunking, and fixed-size chunks cut mid-idea. Semantic chunking keeps each retrieved passage coherent enough to answer the question on its own.

Indexing strategy: Hybrid dense-plus-sparse. The query set mixes exact-clause lookups ("find the termination clause in the Acme contract") with open-ended conceptual questions ("how did we approach X?"). Sparse handles exact-target lookups where specific identifiers matter; dense handles concept-lookup and synthesis queries where meaning, not exact terms, drives the match. Neither alone covers both patterns.

The dominant trade-off: query variety is the load-bearing constraint. The hybrid index adds retrieval compute and a rank-fusion step, but those costs earn their place because the query set genuinely needs both modes.
How did your design compare?

Correct: my design matched
Partial: close, but off on one piece
Incorrect: I missed the structure
← Prev
