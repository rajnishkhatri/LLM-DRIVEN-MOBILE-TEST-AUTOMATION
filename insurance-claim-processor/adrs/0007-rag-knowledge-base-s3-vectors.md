# ADR 0007. Promote RAG to a Bedrock Knowledge Base on S3 Vectors

## Status
Proposed — depends on ADR 0002

## Context
ADR 0002 chose RAG (not fine-tuning) with `retrieve` + our own Converse prompt,
and named a Bedrock Knowledge Base with metadata filters as the production
store. The offline eval (`../validate/eval-report.md`) proved the metadata
filter is **load-bearing**: unfiltered keyword RAG cited a Florida auto clause
on a Texas homeowners claim. This ADR picks the vector store and the
embedding/chunking shape for the KB promote. Working assumption A5 stages the
KB as a **fast-follow** — the PoC first smoke keeps the in-process keyword RAG.

## Decision
The KB promote will use a **Bedrock Knowledge Base backed by S3 Vectors**:

- **Embeddings:** Amazon Titan Text Embeddings v2 at 512 or 1024 dims
  (**re-verify**); the model id **and dims are recorded next to the index** so
  re-embedding is unambiguous.
- **Chunking:** section/clause-aware (not blind fixed-size) so each retrieved
  chunk maps to a citable policy clause.
- **Metadata (stamped at ingest, not query-time regex):** `jurisdiction`,
  `line_of_business`, `policy_form`, `effective_date`. Retrieval filters on
  jurisdiction + line_of_business; **fail closed** — unknown jurisdiction
  retrieves nothing and the summary is flagged `ungrounded` (card C11).
- **Generation:** `retrieve` + our Converse prompt (we own schema, citations,
  provenance) — never `retrieve_and_generate` on the audited path.

Rejected: **OpenSearch Serverless** (mature, hybrid search, but a higher
idle-cost OCU floor — overkill until hybrid keyword+vector search or high-scale
filtering is a *measured* need); **Aurora pgvector** (co-locates vectors with
relational data, but the design deliberately deferred a relational DB).

Justification:

- **Idle-cheap** matches back-office batch with low/bursty query volume and
  preserves the zero-idle property that chose Bedrock over SageMaker.
- The metadata filter is a proven correctness lever, not a config footnote.
- `retrieve` keeps citations checkable — an un-cited summary is flagged, not
  trusted.

## Consequences
Good: cheap at idle; policy updates are ingest, not retraining; citations make
integrity auditable.
Bad: S3 Vectors is newer — **re-verify GA, limits, and quotas** at build time;
if hybrid keyword+vector search becomes the need, migrate to OpenSearch
Serverless (the metadata schema and `retrieve` contract carry over); the
embeddings model+dims must be recorded or a later re-embed is ambiguous.

## Compliance
Fitness: every KB chunk carries the four metadata tags; retrieval is filtered
on jurisdiction + line_of_business; unknown jurisdiction → no retrieval →
summary `ungrounded`; embeddings model + dims recorded next to the index; no
`retrieve_and_generate` on the audited path. (PoC keyword-RAG assertions in the
eval already prove the fail-closed behavior.)

## Notes
Author: aws-ai-design (provisional kata run)
Approved by / date:
Last modified: 2026-09-21
