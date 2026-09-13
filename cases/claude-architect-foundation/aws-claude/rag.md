---
type: guide
title: 'RAG on Bedrock — chunking, embeddings, hybrid search, and rerank'
description: 'Retrieve only relevant chunks: size, structure, or semantic chunking, embeddings, BM25 hybrid with RRF, LLM rerank, and contextual retrieval.'
tags: [claude, bedrock, aws-claude, rag]
---

# RAG on Bedrock — chunking, embeddings, hybrid search, and rerank

Retrieval Augmented Generation queries large documents (hundreds to thousands of pages) without stuffing the whole corpus into the prompt.

**Direct approach:** put the full document in the prompt with the question. Hits token limits, degrades quality on long prompts, costs more, runs slower.

**RAG approach:**

1. Break the document into chunks (preprocessing).
2. For each question, retrieve the most relevant chunks and send *only those* with the question.

Advantages: the model focuses on relevant text; scales to very large or multiple documents; smaller prompts are faster and cheaper. Disadvantages: more moving parts, a search mechanism, a definition of "relevance," no guarantee a chunk has complete context, and many chunking strategies. RAG is complexity in exchange for documents that would otherwise not fit.

## Text chunking strategies

Bad chunking creates context errors — a medical sentence containing "bug" retrieved for a software question because of word overlap without surrounding meaning.

Three families:

1. **Size-based** — equal-length strings. Easiest and common in production. Cuts mid-sentence. **Overlap** with neighboring characters restores some context at the cost of duplication.
2. **Structure-based** — headers, paragraphs, sections (for example split on markdown `##`). Well-formed when the document has structure; fails on unformatted PDFs.
3. **Semantic-based** — NLP groups consecutive sentences by similarity. Most advanced; many variants.

Selection: structured docs with a format guarantee → structure-based; unstructured → sentence-oriented; code or mixed formats → character-based as the reliable fallback. Parameters: chunk size, overlap, split criteria. Character-based chunking is the default that works across types even when it is not optimal.

## Text embeddings

An embedding model maps text to a vector (often ~1024 floats in roughly -1..+1). Individual dimensions are opaque; treat them as scores on unknown features. Purpose in RAG: **semantic** search by comparing vectors instead of exact strings. Implementation is an API call (for example Titan Embed Text V2) that returns the vector.

## The full RAG flow

1. Chunk source documents.
2. Embed each chunk (same model you will use on queries).
3. Normalize magnitudes to 1.0 (usually the API's job).
4. Store vectors in a vector database.
5. Embed the user question with the same model.
6. Similarity search for nearest stored vectors.

**Cosine similarity** is the cosine of the angle between vectors, range -1..1 (closer to 1 = more similar). **Cosine distance** is `1 - similarity` (closer to 0 = more similar).

7. Build a prompt from the question plus retrieved chunk text.
8. Generate with the LLM.

## Implementing the flow

A five-step sketch:

1. `chunk_by_section` on a markdown report.
2. `generate_embedding` per chunk.
3. A `vector_index` stores `{embedding, text}` pairs (keep the original text — raw vectors are useless at read time).
4. Embed the user question.
5. `store.search` for the top-k chunks by cosine distance.

A toy query might return Section 2 at distance 0.71 and Methodology at 0.72. The workflow runs; production still needs hybrid search and rerank.

## BM25 lexical search

**BM25** (Best Match 25) is keyword matching. Pure semantic search misses exact identifiers ("incident 2023") even when they are the right document.

Algorithm sketch: tokenize the query → term frequencies across chunks → rare terms weigh more than "the"/"a" → rank chunks that contain high-weight terms often.

**Hybrid search:** run semantic and lexical in parallel, then merge. Give both indexes the same `add_document()` / `search()` surface so they compose.

## A multi-search RAG pipeline

Components: vector index, BM25 index, a retriever wrapper with a unified API.

**Reciprocal Rank Fusion (RRF)** merges ranked lists:

`score = Σ 1/(1 + rank)` across methods. Higher is better.

Example: 1st in vector and 2nd in BM25 → `1/(1+1) + 1/(1+2) = 0.83`. Collect unique documents, score, sort. Modular enough to add a third method later. RRF is the defensible default merge when you do not have a learned fusion model — the same conclusion as the [certification RAG notes](../../claude-certification/platform-design/rag-pipeline.md).

## Reranking results

After hybrid retrieval, an LLM reorders the candidates. Assign temporary IDs, present documents in XML, ask for the top-N IDs in decreasing relevance, and parse with [prefill + stop](bedrock-converse-api.md). Extra latency; often a large accuracy gain. Example: "What did the engineering team do with incident 2023?" surfaces the software-engineering section first after rerank when hybrid had it second.

## Contextual retrieval

Chunks lose document-level context. Before indexing, ask an LLM to situate each chunk in the source, then store `context + chunk`.

If the source is too large for one prompt, send the opening (abstract) plus the chunks immediately before the target and skip distant middle. Example context: "This is section X of a report covering Y, after methodology Z, before financials." `add_context(chunk, source)` is the hook. Retrieval then sees cross-references and section role, not an isolated paragraph.
