# Wave 0 — contract freeze (claim processor real AWS)

**Stage:** sdd-implement Wave 0. **Status:** FROZEN — amended 2026-09-21
(F1 HITL `*`, F3 Claude+Nova invoke patterns, F4b us-east-1 ViaService +
`key/*`, F9 landed test paths; ApplyGuardrail named ARN aligned with C-04).
**Spec:** `../specs/claim-processor-real-aws.spec.md` · **Plan:**
`./claim-processor-real-aws.plan.md` · **Tasks:**
`./claim-processor-real-aws.tasks.md`.
**Design:** `../design/solution-design.md` §7 · **ADRs:** 0004–0009.

This document freezes **names, signatures, defaults, and file paths** — not
implementations. Later waves (2–3 worktrees) fork from this file. Product
modules (`config.py`, `understand.py`, IAM JSON, ASL, `ProcessingResult`
fields, …) are **not** created here; they land in the owning task.

**Binding (resolved 2026-09-21):**

| Placeholder | Value |
|---|---|
| `{{constitution}}` | `.cursor/rules/architecture-principles.mdc` (SOLID / DI / testability; no TDD Always-rules section — red/green + demand-evidence come from `sdd-implement`) |
| `{{check_gate}}` | `python3 tooling/skill-sync/skill_sync.py check` (repo root; not kata-specific) |
| `{{test_gate}}` | workspace `<none>`; **kata gate** = `python3 -m unittest discover -s tests` from `insurance-claim-processor/build/` |
| `{{methodology_source}}` | `<none>` |
| `{{adr_home}}` | workspace `docs/architecture/adrs/application/mobile-test-automation/`; **this kata** files ADRs under `insurance-claim-processor/adrs/` |

---

## 1. TDD convention

- Each task adds **`insurance-claim-processor/build/tests/test_<area>.py`**
  named after the module it owns (`test_config.py`, `test_understand.py`,
  `test_models.py`, `test_routing.py`, …).
- **Do not append** to a shared monolith test file. Wave 0 extracted the
  former `tests/test_claim_processor.py` 1:1 (assertions unchanged):

  | Class (unchanged) | File |
  |---|---|
  | `ValidatorTests` | `tests/test_validator.py` |
  | `PromptTests` | `tests/test_prompts.py` |
  | `RagTests` | `tests/test_rag.py` |
  | `PipelineFakeTests` | `tests/test_pipeline.py` |
  | `InvokerStubberTests` | `tests/test_invoker.py` |
  | `S3StubberTests` | `tests/test_store.py` |
  | `CompareTests` | `tests/test_compare.py` |

- **T-09** is the only task that extends pipeline tests: append to
  **`tests/test_pipeline.py`** (the extracted home of `PipelineFakeTests`).
  The old `test_claim_processor.py` is gone so Wave 1 forks do not share it.
- Gate remains:

  ```bash
  cd insurance-claim-processor/build
  python3 -m unittest discover -s tests
  ```

  No credentials. Stubber + `LocalDocumentStore` only — **do not add moto**
  (Analyze finding; `requirements.txt` is boto3/botocore only).
- Red first: write the task's EARS test, paste the failing output, then
  implement. A test that never failed proves nothing.
- Do not delete `def test_*` or add skip/xfail without a waiver.

---

## 2. Pinned paths

All paths are relative to `insurance-claim-processor/`.

| Path | Owner | Notes |
|---|---|---|
| `build/claim_processor/config.py` | T-01 | new |
| `build/claim_processor/invoker.py` | T-02 | existing; backward-compatible `converse` |
| `build/claim_processor/understand.py` | T-03 | new |
| `build/claim_processor/models.py` | T-04 | existing; additive fields only |
| `build/claim_processor/fake.py` | T-05 | existing; image + guardrail offline |
| `build/claim_processor/routing.py` | T-07 | new |
| `build/claim_processor/review.py` | T-08 | new |
| `build/claim_processor/pipeline.py` | T-09 | existing; step-unit split |
| `build/claim_processor/store.py` | T-10 | existing; `pending_review_key` |
| `build/claim_processor/__main__.py` | T-11 | existing; `decide` + `--real` gate |
| `build/claim_processor/logging_safe.py` | T-12 | new |
| `build/claim_processor/handler.py` | T-13 | new; thin SFN ↔ module adapter |
| `build/sfn/asl.json` | T-13 | new |
| `build/iam/sfn-exec.json` | T-14 | new |
| `build/iam/step-lambda.json` | T-14 | new |
| `build/iam/operator.json` | T-14 | new |
| `build/DEPLOY.md` | T-15 | new; not an impl worktree |
| `build/claim_processor/rag.py` | T-17 | existing; extract `RetrieverProtocol` |
| `build/claim_processor/kb.py` | T-18 | new; fast-follow |
| `build/scripts/tag_ingest.py` | T-19 | **freeze** — task list had `(script)` unnamed |
| `build/tests/test_<area>.py` | owning task | see §1 |

Do not invent extra product tasks or extra modules to host these paths.

---

## 3. File ownership (collision map)

One writer per production file per wave. Read-only imports of a frozen type
are allowed; editing another task's file is not.

| File | Writer | Readers (import only) |
|---|---|---|
| `config.py` | T-01 | T-02, T-07, T-09, T-11 |
| `invoker.py` | T-02 | T-09, compare.py (no edit), existing Stubber tests |
| `understand.py` | T-03 | T-09 |
| `models.py` | T-04 | everyone; T-04 does **not** touch `pipeline._as_record` |
| `fake.py` + image sample/gold | T-05 | CLI / eval |
| `routing.py` | T-07 | T-09, T-13 |
| `review.py` | T-08 | T-09, T-11, T-13 |
| `store.py` | T-10 first, then T-09 | T-09 may **add** `get_bytes` *after* T-10 merges; T-10 does not add it |
| `pipeline.py` | T-09 | T-13 handler, T-17 (annotation widen only in T-17) |
| `__main__.py` | T-11 | — |
| `logging_safe.py` | T-12 | handlers / pipeline (T-09/T-13 import) |
| `sfn/asl.json`, `handler.py` | T-13 | — |
| `iam/*.json` | T-14 | T-15 runbook |
| `rag.py` | T-17 | T-09 keeps `PolicyRetriever` annotation until T-17 |

---

## 4. `EscalationPolicy` (T-01)

**File:** `build/claim_processor/config.py`.

```python
from dataclasses import dataclass
from claim_processor.models import (
    EXTRACT_MODEL_EXAMPLE,
    SUMMARY_MODEL_EXAMPLE,
    UNDERSTAND_MODEL_EXAMPLE,
)

@dataclass(frozen=True)
class EscalationPolicy:
    amount_threshold: float = 10000.0
    region: str = "us-east-1"
    extract_model_id: str = EXTRACT_MODEL_EXAMPLE
    summary_model_id: str = SUMMARY_MODEL_EXAMPLE
    understand_model_id: str = UNDERSTAND_MODEL_EXAMPLE
    guardrail_id: str | None = None
    kb_id: str | None = None
    force_review_flags: tuple[str, ...] = ()

    @classmethod
    def from_env(cls) -> EscalationPolicy: ...
```

`amount_threshold` is configuration, not a constant in routing (AC-E1b).
Model-id fields are **examples to re-verify** (same stance as `models.py`);
results record the *resolved* id from `converse`, never these defaults as
provenance.

### Frozen env var names

Existing code uses **`CLAIM_PROCESSOR_*`** (`CLAIM_PROCESSOR_REAL_AWS` in
`__main__.py`). New names follow that prefix. **Do not rename** the gate.

| Env var | Field | Default if unset |
|---|---|---|
| `CLAIM_PROCESSOR_REAL_AWS` | *(gate, not a policy field)* | unset → refuse real clients. Value `"1"` required. **Existing — do not rename.** |
| `CLAIM_PROCESSOR_AMOUNT_THRESHOLD` | `amount_threshold` | `10000.0` |
| `CLAIM_PROCESSOR_REGION` | `region` | `"us-east-1"` (matches `__main__.py` `boto3.Session`) |
| `CLAIM_PROCESSOR_EXTRACT_MODEL_ID` | `extract_model_id` | `EXTRACT_MODEL_EXAMPLE` |
| `CLAIM_PROCESSOR_SUMMARY_MODEL_ID` | `summary_model_id` | `SUMMARY_MODEL_EXAMPLE` |
| `CLAIM_PROCESSOR_UNDERSTAND_MODEL_ID` | `understand_model_id` | `UNDERSTAND_MODEL_EXAMPLE` |
| `CLAIM_PROCESSOR_GUARDRAIL_ID` | `guardrail_id` | `None` (empty/unset) |
| `CLAIM_PROCESSOR_KB_ID` | `kb_id` | `None` (empty/unset; used T-18) |
| `CLAIM_PROCESSOR_FORCE_REVIEW_FLAGS` | `force_review_flags` | `()` — comma-separated extra flag prefixes that force `human_review`. Built-in AC-E1 predicates always apply. |

`from_env()` reads only these names. CLI flags `--extract-model` /
`--summary-model` already exist on `__main__.py`; **T-01 does not edit
`__main__.py`**. T-11 wires `CLI flag > env > example default`.

IAM ViaService / key policy is pinned `us-east-1` for this PoC. A
non-default region is readable by config (T-01) but is not a supported
IAM deploy until T-15.

---

## 5. `ProcessingResult` (T-04)

**File:** `build/claim_processor/models.py`. Additive fields **all defaulted**
so the current `ClaimPipeline.process` constructor and the existing 17 tests
stay green. Place new fields **after** `usage`.

Current required fields (do not change):

```python
extracted_info: dict[str, Any] | str
summary: str
citations: list[str]
ungrounded: bool
validation: ValidationResult
extract_model_id: str
summary_model_id: str
prompt_versions: dict[str, str]
usage: dict[str, Any] = field(default_factory=dict)
```

Add:

```python
route: str | None = None
# "auto_approve" | "human_review"
review: dict[str, Any] | None = None
# {decision, reviewer_id, timestamp, field_changes[]}
# field_changes[] item: {field, from, to}   # "from" is a dict key, not a Python identifier
guardrail: dict[str, Any] | None = None
# {intervened: bool, actions: list}
sfn_execution_arn: str | None = None
schema_version: str = "1.0"
understand_model_id: str | None = None
embeddings: dict[str, Any] | None = None
# {model_id: str, dims: int} — populated when KB is live (T-18)
```

Aligns with design §7 provenance tuple.

**Serialization (T-04):** lives on the dataclass in `models.py`.

```python
def to_record(self, claim_key: str | None = None) -> dict[str, Any]:
    """§7-shaped dict: validation flattened to {accepted, flags};
    includes new defaulted fields. Optional claim_key."""
```

Unit test: `dataclasses.asdict(result)` and/or `result.to_record(...)`
include the new keys with defaults. **`pipeline._as_record` stays T-09** —
T-04 must not edit `pipeline.py`. T-09 may later delegate `_as_record` to
`to_record`.

---

## 6. `ModelInvoker.converse` (T-02)

**File:** `build/claim_processor/invoker.py`. Backward compatible.

Keep:

```python
def converse(
    self,
    prompt: str,
    *,
    model_id: str | None = None,
    system: str | None = None,
    max_tokens: int = 1000,
    content: list[dict] | None = None,
    guardrail_config: dict | None = None,
) -> dict[str, Any]:
```

- `prompt` stays required (positional) so `compare.py` and existing Stubber
  tests call `converse(prompt, model_id=..., max_tokens=...)` unchanged.
- If `content is not None`, the user message body **is** `content`.
  `prompt` is ignored for the body (callers may pass `""`).
- If `content is None`, keep today's body: `[{"text": prompt}]`.
- If `guardrail_config is None`, **omit** `guardrailConfig` from the boto3
  kwargs (existing Stubber expected-params stay exact).
- If `guardrail_config` is a dict, pass it through as AWS
  `guardrailConfig` (camelCase at the wire; snake_case in Python).
- Timeouts / adaptive retries stay in `bedrock_client_config`
  (connect=10 s, read=300 s, adaptive `max_attempts=5`). No app-level retry
  loop. No legacy completions contract.

**Return keys** (existing four stay; add `guardrail`):

```python
{
    "text": str,
    "model_id": str,          # id actually sent (resolved)
    "stop_reason": Any,
    "usage": dict,
    "guardrail": {"intervened": bool, "actions": list},
}
```

When no intervention / no config: `{"intervened": False, "actions": []}`.
Adding the key is backward compatible — existing tests assert `text` and
forbid `completion`, they do not freeze the key set.

**Do not edit** `compare.py`. **Do not require** `fake.py` edits: today's
`FakeModelInvoker.converse(..., **_)` already swallows new kwargs. T-05
owns fake's image/guardrail behavior.

---

## 7. `understand` (T-03)

**File:** `build/claim_processor/understand.py`. No Pillow. Bound by **byte
size**, not pixels.

```python
MAX_IMAGE_BYTES = 5_242_880  # 5 MiB — ingest cap (AC-D3 / ADR 0006)

class OversizeDocumentError(ValueError):
    """Image payload exceeds max_bytes."""

def to_content_blocks(
    payload: bytes | str,
    *,
    media_type: str | None = None,
    filename: str | None = None,
    max_bytes: int = MAX_IMAGE_BYTES,
) -> list[dict]:
    """Detect image vs text → Converse content blocks.

    Text  → [{"text": <str>}]
    Image → [{"image": {"format": "png"|"jpeg"|"gif"|"webp",
                        "source": {"bytes": <bytes>}}}]
    Oversize image → raise OversizeDocumentError.
    """
```

Detection: magic bytes and/or `media_type` / `filename`. No image library.
`max_bytes` applies to **image** payloads; text is not rejected by this
cap.

T-03 does **not** edit `pipeline.py` or `store.py`. It converts bytes/str
the caller already has. Image-through-pipeline (how a claim key becomes
those bytes) is **T-09**.

---

## 8. `route_claim` (T-07)

**File:** `build/claim_processor/routing.py`. Pure function; no I/O.

```python
from typing import Literal

def route_claim(
    result: ProcessingResult,
    policy: EscalationPolicy,
) -> Literal["auto_approve", "human_review"]:
    ...
```

**Auto-approve iff all of:**

1. schema-valid — `result.validation.accepted` is True **and** no flag
   starts with `missing_keys:` / equals `invalid_json` / equals `not_an_object`
2. required fields present — no flag starts with `empty_fields:`
   (today's validator can accept empty fields; the predicate must not)
3. grounded — `result.ungrounded is False` **and** `"ungrounded"` not in
   flags **and** `"missing_citations"` not in flags
4. amount ≤ threshold — `extracted_info["claim_amount"]` is numeric and
   `<= policy.amount_threshold`; missing/non-numeric amount → review
5. no PII — no flag starts with `pii_` (`pii_ssn`, `pii_pan`, …)

Plus: any `validation.flags` entry that equals or starts with a member of
`policy.force_review_flags` → `human_review`.

Otherwise → `"human_review"`. Threshold comes from `policy`, never a
module constant.

---

## 9. `review` (T-08)

**File:** `build/claim_processor/review.py`.

```python
def apply_decision(
    pending: dict,
    *,
    decision: str,           # "approve" | "correct" | "reject" | "review-expired"
    reviewer_id: str,
    timestamp: str | None = None,   # ISO-8601; default utc-now
    corrections: dict | None = None,  # field → new value; required for "correct"
) -> dict:
    """Apply a HITL decision to a pending-review record.

    correct         → reviewer's values are the final extracted_info;
                      no re-summarize / re-validate / re-retrieve (AC-E3).
                      field_changes[] = [{field, from, to}, ...]
    approve/reject  → record decision; extracted_info unchanged
    review-expired  → mark review.decision = "review-expired" and escalate
                      (never auto-approve)
    """
```

Returned record includes `review: {decision, reviewer_id, timestamp,
field_changes[]}` and is the **final** result for `correct`. T-13's 7-day
Catch calls this with `decision="review-expired"` (system `reviewer_id`).

---

## 10. `store` (T-10)

**File:** `build/claim_processor/store.py`.

```python
def pending_review_key(claim_key: str) -> str:
    return f"pending-review/{claim_key}.json"
```

Mirror of `pipeline.result_key_for` → `results/<key>.json`.

- **Put:** existing `put_json(bucket, pending_review_key(claim_key), payload)`
- **Get:** existing `get_text` + `json.loads`. Optional thin `get_json`
  wrapper is allowed; **not** required on `DocumentStore`.
- **Do not change `get_text` semantics** (still UTF-8 decode of the object
  body). Binary image packets must not be forced through `get_text`.
- **Do not add `get_bytes` in T-10.** If the image path needs it, **T-09**
  adds `get_bytes` to `DocumentStore` / Local / S3 *after* T-10 merges.

`DocumentStore` protocol stays:

```python
def get_text(self, bucket: str, key: str) -> str: ...
def put_json(self, bucket: str, key: str, payload: dict[str, Any]) -> None: ...
```

---

## 11. `ClaimPipeline` step units (T-09 → T-13)

**File:** `build/claim_processor/pipeline.py` (T-09). ASL +
`handler.py` (T-13) call these names.

Keep `process(self, bucket: str, key: str) -> ProcessingResult` as the
offline/CLI facade that *composes* the steps (existing 4 pipeline tests
stay green).

Frozen step names (Understand/Extract → Validate → Retrieve/Summarize →
Route → AwaitReview → Record):

| ASL state | Python | Kind |
|---|---|---|
| `UnderstandExtract` | `ClaimPipeline.understand_extract(...)` | Lambda via `handler.understand_extract` |
| `Validate` | `ClaimPipeline.validate(...)` | Lambda via `handler.validate` |
| `RetrieveSummarize` | `ClaimPipeline.retrieve_summarize(...)` | Lambda via `handler.retrieve_summarize` |
| `Route` | `ClaimPipeline.route(...)` → `route_claim` | SFN **Choice** (no wait) |
| `AwaitReview` | *(none — SFN `waitForTaskToken`)* | T-13 only |
| `Record` | `ClaimPipeline.record(...)` | Lambda via `handler.record` |

- Record after route(auto) **or** after review(human). Idempotent: same
  key → one `results/<key>.json` (overwrite). Flagged →
  `pending-review/<key>.json` + route.
- T-09 injects `EscalationPolicy` (from T-01); does not construct boto3
  clients (DI).
- T-09 may add `get_bytes` on the store **after T-10**. Retriever
  annotation stays `PolicyRetriever` until T-17.
- `_as_record` is T-09's to update (may delegate to
  `ProcessingResult.to_record`).

`handler.py` (T-13): thin functions, one per Lambda state, mapping SFN
event I/O ↔ the step methods. Modules never import a client at load.

---

## 12. `RetrieverProtocol` (T-17)

**File:** `build/claim_processor/rag.py`. Matches today's
`PolicyRetriever.retrieve` exactly so the keyword retriever implements it
with no behavior change.

```python
class RetrieverProtocol(Protocol):
    def retrieve(
        self,
        query: str,
        top_k: int = 2,
        *,
        jurisdiction: str | None = None,
        line_of_business: str | None = None,
    ) -> list[PolicyChunk]: ...
```

T-17 widens `ClaimPipeline.__init__(..., retriever: RetrieverProtocol)`.
**T-17 is NOT start-now** — depends on T-09 (see §15). `[P]` on the task
list does not override that dep.

---

## 13. IAM (T-14) and logging (T-12)

Three JSON files, **no** `AmazonBedrockFullAccess`, **no** bucket-wide
`s3:*`. Every Bedrock **invoke** statement names **both** a
`foundation-model/` ARN and an `inference-profile/` ARN. Model-id
segment is a **named pattern** covering spike models (from
`EXTRACT_MODEL_EXAMPLE` / `SUMMARY_MODEL_EXAMPLE` /
`UNDERSTAND_MODEL_EXAMPLE` — not a bare `*`):

- `arn:aws:bedrock:*::foundation-model/anthropic.claude-*`
- `arn:aws:bedrock:*::foundation-model/amazon.nova-*`
- `arn:aws:bedrock:*:*:inference-profile/us.anthropic.claude-*`
- `arn:aws:bedrock:*:*:inference-profile/us.amazon.nova-*`

(`ApplyGuardrail` is not an invoke statement — see C-04 named guardrail
ARN below.)

| File | Role | Actions (frozen intent) |
|---|---|---|
| `build/iam/sfn-exec.json` | SFN execution | `lambda:InvokeFunction` on step Lambdas + logs. Nothing else. |
| `build/iam/step-lambda.json` | shared step-Lambda | `bedrock:InvokeModel` + `InvokeModelWithResponseStream` on the Claude+Nova named patterns above; `bedrock:ApplyGuardrail` on a **named** guardrail ARN (e.g. `arn:aws:bedrock:*:*:guardrail/claim-processor*`), not `guardrail/*` (C-04); `s3:GetObject` on `claims/*`; `s3:PutObject` on `results/*` + `pending-review/*`; `kms:Decrypt` / `GenerateDataKey` with `kms:ViaService` `s3.us-east-1.amazonaws.com` + `bedrock.us-east-1.amazonaws.com`; Resource `arn:aws:kms:*:*:key/*`. PoC IAM is **us-east-1 only** — `CLAIM_PROCESSOR_REGION` other than `us-east-1` is unsupported for IAM until T-15 (`DEPLOY.md`). `from_env` may still read the var. Fast-follow `bedrock:Retrieve` on `knowledge-base/*`. |
| `build/iam/operator.json` | operator / CLI | `states:SendTaskSuccess` / `SendTaskFailure` with `Resource: "*"` only (AWS empty Resource types; not a `stateMachine:` ARN); optional `aws:SourceAccount` / `aws:RequestedRegion` MAY ride on top of `*`, not instead; `s3:GetObject` on `pending-review/*`; `bedrock:InvokeModel` for the spike (same Claude+Nova named patterns). |

`logging_safe.py` (T-12): redacting logger. Minimal freeze —

```python
def redact(text: str) -> str: ...
def get_logger(name: str) -> logging.Logger: ...  # emits only redacted messages
```

Log-shape test: an SSN-bearing packet produces **no** raw SSN in captured
logs (AC-H1).

---

## 14. Wave plan

| Wave | Tasks | Worktrees? |
|---|---|---|
| **0** | this freeze + optional test split | **base branch only** |
| **1** | **T-01, T-03, T-04, T-10, T-12, T-14** | 2–3 forks from this freeze; no shared production file |
| hub | **T-09** | sequential; after Wave 1 + T-02/T-07/T-08 |
| later | T-02, T-05, T-07, T-08, T-11, T-13, T-17… | respect deps |
| not impl worktrees | **T-06** (run/`[gate]`), **T-15** (doc-review), **T-16** (offline sweep) | operators / later stage |

T-09 is the **sequential hub**: Understand/Extract → Validate →
Retrieve/Summarize → Route → AwaitReview → Record.

---

## 15. Do-not-parallelize pairs

Do not fork these as concurrent writers:

| Pair | Why |
|---|---|
| T-02 ∥ T-01 | T-02 deps T-01 (policy / ids). |
| T-05 ∥ T-02 | **[P] correction:** T-05 also depends on T-02 `converse`/`fake` (image content + guardrail kwargs). Task list only lists T-03, T-04. |
| T-07 ∥ T-01 or T-04 | T-07 deps both. |
| T-08 ∥ T-04 | T-08 deps T-04 review/route fields. |
| T-09 ∥ T-02, T-03, T-04, T-07, T-08, T-10 | T-09 deps all six; sequential hub. |
| T-09 ∥ T-10 on `store.py` | T-10 first (`pending_review_key`); T-09 may add `get_bytes` after merge. |
| T-04 ∥ T-09 on `pipeline.py` / `_as_record` | T-04 = dataclass + `to_record` only. |
| T-11 ∥ T-08, T-10 | T-11 deps both; T-11 owns `__main__.py`. |
| T-13 ∥ T-08, T-09 | ASL/handler after step units + review. |
| T-17 ∥ T-09 | **[P] correction:** T-17 is **NOT start-now**. Deps T-09. |
| T-18 ∥ T-17; T-19 ∥ T-18 | fast-follow chain. |
| T-03 ∥ T-09 on `pipeline.py` / `store.py` | T-03 = `to_content_blocks` only. Image-through-pipeline = T-09. |

---

## 16. T-06 plan-vs-task gap (sdd-replan if the spike needs it)

Evidence from `__main__.py` (do not stealth-edit):

- Real AWS is gated by **`CLAIM_PROCESSOR_REAL_AWS=1`** plus **`--s3`**
  (or `--compare`). There is **no `--real` flag**.
- Task T-06 says “spike via `--real`”. Task T-11 says “keep `--real`
  gate”. Plan Step A says “run existing pipeline end-to-end via `--real`”.
- **`--real` is unowned until T-11.** Wave 1 must not add it.
- Image-through-pipeline is **T-09**. T-03 only builds content blocks from
  bytes it is given. Today's `store.get_text` is UTF-8 and will not carry
  image packets.

**If the feasibility spike needs `--real` or image-through-pipeline before
T-11 / T-09 land → stop and `sdd-replan`.** Do not stealth-edit
`__main__.py`, `pipeline.py`, or `store.py` to unblock T-06.

Text-only spike on the *current* CLI (`CLAIM_PROCESSOR_REAL_AWS=1` +
`--s3`) does not require those files.

T-19's ingest script was unnamed in the task list. Wave 0 freezes
`build/scripts/tag_ingest.py`. That is the freeze, not a new product task.

---

## 17. Backward-compat conflicts (code wins)

| Topic | Freeze / plan | Actual code | Resolution |
|---|---|---|---|
| Real-AWS CLI | `--real` (T-06/T-11/plan) | `--s3` + `CLAIM_PROCESSOR_REAL_AWS=1` | Keep `--s3` working. `--real` is T-11. See §16. |
| `converse` | add `content`, `guardrail_config` | `converse(prompt, *, model_id, system, max_tokens)` | Additive kwargs only; default path unchanged. |
| `ProcessingResult` | new provenance fields | 9 fields; `usage` defaulted | New fields defaulted after `usage`. |
| `PolicyRetriever.retrieve` | T-17 protocol | already matches the frozen signature | T-17 is a Protocol extract, not a behavior change. |
| moto | plan “confirm moto present” | not in `requirements.txt`; suite uses Stubber | **Do not add moto** (Analyze). |
| Constitution TDD Always rules | skill points at `{{constitution}}` | bound file is architecture principles (no Always-rules) | Follow skill red/green + SOLID/DI. Not a replan. |
| T-17 `[P]` | listed parallelizable | deps T-09 | NOT start-now. |
| T-05 deps | listed T-03, T-04 | needs T-02 converse/fake | extra dep. |

---

## 18. Ready for Wave 1 forks?

**Yes** — after this freeze and a green kata test gate. Wave 1 worktrees
may implement T-01, T-03, T-04, T-10, T-12, T-14 in parallel. They do not
share a production file or (after the test split) a test file:

| Task | New/owned file | Test file |
|---|---|---|
| T-01 | `config.py` | `tests/test_config.py` |
| T-03 | `understand.py` | `tests/test_understand.py` |
| T-04 | `models.py` (additive) | `tests/test_models.py` |
| T-10 | `store.py` (`pending_review_key`) | `tests/test_store_pending.py` (new file; do not append `test_store.py`) |
| T-12 | `logging_safe.py` | `tests/test_logging_safe.py` |
| T-14 | `iam/*.json` | `tests/test_iam_policy.py` (policy-lint) |

§1 collision-avoidance: landed names stay. Do not rename code to the
pre-amend §18 paths.
