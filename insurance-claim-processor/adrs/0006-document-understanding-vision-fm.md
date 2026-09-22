# ADR 0006. Read image packets with a vision FM; Textract/BDA as promote

## Status
Proposed

## Context
A3 puts **images** in scope (text + PDF + images). The Understand Document
component must turn image bytes into model-ready content before extraction.
The packets are **mostly photos and typed-text images** (damage photos, phone
snapshots, clean documents captured as images) — not dense scanned forms or
handwriting. Options: a multimodal **vision FM** (Amazon Nova or Claude image
content blocks, same Converse path) vs **managed OCR first** (Amazon Textract
or Bedrock Data Automation) that emits text/structured JSON, then extract.

## Decision
We will read images with a **vision FM directly** via the existing
`Invoke Foundation Model` (Converse) component — image content blocks, resolved
multimodal model id (Nova/Claude, **re-verify**). We will **not** add Textract
or BDA to the PoC.

**Textract / BDA is the named production promote**, adopted when packets shift
to scanned forms, tables, or handwriting, or when volume makes per-image FM
tokens expensive — because it adds two things that serve top-3 characteristics:
**per-field confidence scores** (route low-confidence fields to HITL) and an
**intermediate OCR artifact** (a "what we read" audit trail distinct from "what
we extracted"). The Understand Document component is the **swap seam**
(configurability), so the promote is additive.

Justification:

- Packets are photos / typed-text images — a vision FM reads these well; a
  dedicated OCR engine's form/handwriting strengths are not the need yet.
- **Minimal throwaway / fast:** reuses the existing invoker and Converse
  Stubber contract — no second AWS service to wire, stub, or deploy by hand.
- Keeps the zero-idle-cost property that chose Bedrock over SageMaker.

## Consequences
Good: one invoke contract; images ride the same audit/provenance path (model
id + image ref recorded); cheapest to stand up under a manual deploy.
Bad: no per-field confidence signal in the PoC (HITL routing leans on the
validator, not OCR confidence); image content blocks are token-heavy, so a
large/high-res packet costs more per claim — cap image size at ingest and
**re-verify** multimodal token rates; dense-form or handwriting accuracy will
be the trigger to promote to Textract/BDA.

## Compliance
Fitness: the Understand step records the resolved multimodal model id on every
image-bearing result; extraction of an image packet produces the same
schema-valid five-field JSON as a text packet (eval covers ≥1 image sample);
no OCR service in the PoC deploy graph. Image size bounded at ingest.

## Notes
Author: aws-ai-design (provisional kata run)
Approved by / date:
Last modified: 2026-09-21
