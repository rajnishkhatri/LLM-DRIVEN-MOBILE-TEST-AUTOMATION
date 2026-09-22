# Claim document processor — PoC

Offline-first implementation of the insurance-claim kata. Real AWS calls
are **gated** (`CLAIM_PROCESSOR_REAL_AWS=1`) and belong to
`aws-ai-validate`, not this README.

## What this is

A modular monolith matching `../components/`:

| Component | Module |
|---|---|
| Land / Record | `store.py` (`LocalDocumentStore` / `S3DocumentStore`) |
| Render Prompt | `prompts.py` (`PromptTemplateManager`) |
| Invoke Foundation Model | `invoker.py` (`ModelInvoker.converse`) |
| Retrieve Policy Context | `rag.py` (keyword RAG over `samples/policies/`) |
| Validate Extracted Content | `validator.py` |
| Workflow | `pipeline.py` |

It **does not** copy the exam snippet's `invoke_model` +
`max_tokens_to_sample` + `response["completion"]` contract. That path is
a correctness bug against current-gen models. Default is
`bedrock-runtime.converse`. Model ids in code are **examples to
re-verify**.

## Run without AWS

```bash
cd insurance-claim-processor/build
python3 -m unittest discover -s tests
python3 -m claim_processor --fake --key claims/auto-fl-collision.txt
python3 -m claim_processor --fake --key claims/home-tx-water.txt
python3 -m claim_processor --fake --key claims/incomplete-claim.txt
```

## Gated real AWS (do not run until validate)

```bash
# throwaway sandbox only
aws s3 mb s3://claim-documents-poc-<initials>
export CLAIM_PROCESSOR_REAL_AWS=1
python3 -m claim_processor --s3 --bucket claim-documents-poc-<initials> --key claims/claim1.txt
```

IAM must allow `bedrock:InvokeModel` on **both** `foundation-model/*` and
`inference-profile/*`. Resolve model ids with
`list_foundation_models` / `list_inference_profiles` before passing
`--extract-model` / `--summary-model`.
