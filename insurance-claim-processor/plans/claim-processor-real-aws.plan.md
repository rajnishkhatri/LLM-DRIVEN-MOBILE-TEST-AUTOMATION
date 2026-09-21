# Plan — claim processor on real AWS (Step Functions + HITL)

**Stage:** sdd-spec (Plan). **Status:** DRAFT — plan gate (tasks next).
**Spec:** `../specs/claim-processor-real-aws.spec.md`. **ADRs:** 0004–0009.
**Constitution:** `.cursor/rules/architecture-principles.mdc` (SOLID, DI,
testability, coupling/cohesion, trade-off surfacing).

## Architecture stance (simplest thing — A1)

Keep the **modular monolith core** (`invoker`/`validator`/`rag`/`prompts`/
`store` — pure, DI, offline-tested) **unchanged in responsibility**; add the
real-AWS runtime as **thin layers around it**, not a rewrite:

- Orchestration lives in a **Step Functions Standard** state machine (ASL) +
  thin Lambda handlers that *call* the existing modules — the modules never
  import a client at module load (DI preserved, testability preserved).
- New behavior (routing, HITL record shaping, image understanding, config,
  safe logging) goes in **small single-responsibility modules** (SRP).
- One **new abstraction (G1)**: `RetrieverProtocol` so the pipeline is agnostic
  to keyword-RAG (PoC) vs KB-on-S3-Vectors (fast-follow). *Buys:* the KB promote
  without touching pipeline code. *Simpler thing rejected:* hardcode keyword now
  + rewrite for KB later (more churn, breaks AC-C4's clean swap).

No new ADR: the plan introduces no decision beyond ADRs 0004–0009.

## File-level touchpoints

**Change (existing):**

| File | Change | AC |
|---|---|---|
| `models.py` | extend `ProcessingResult`: `route`, `review`, `guardrail`, `sfn_execution_arn`, `schema_version`, `understand_model_id`, `embeddings` | F1, A4 |
| `invoker.py` | `converse` accepts content blocks (text+**image**) + optional `guardrailConfig`; return guardrail-intervention; keep timeouts/adaptive | A4,A5,D2,H2 |
| `pipeline.py` | split into invocable step units; explicit route; record after route/review (reuses all modules) | E,F,G |
| `store.py` | add `pending-review/` prefix get/put; reuse S3/local | E2,F |
| `__main__.py` | add `decide` subcommand (`SendTaskSuccess`) + pending inspect; keep `--real` gate | E3,J2 |
| `rag.py` | wrap behind `RetrieverProtocol` (logic unchanged) | C |
| `fake.py` | extend to cover image + guardrail paths offline | D1,A5 |
| `tests/` | add routing/review/config/log-shape/policy-lint/image/guardrail cases | all `[off]` |
| `requirements.txt` | confirm `moto` present; **no** Pillow (bound image by byte size) | — |

**New:**

| File | Purpose | AC |
|---|---|---|
| `config.py` | `EscalationPolicy` (**configurable** `amount_threshold`=10000), region, model/guardrail/kb ids | E1b,A4 |
| `routing.py` | pure `route_claim(...)` predicate | E1 |
| `review.py` | apply decision, `field_changes` diff, `review-expired` | E3,E4 |
| `understand.py` | image detect → content blocks; size bound | D1–D3 |
| `logging_safe.py` | redacting logger — no raw PII | H1 |
| `kb.py` *(fast-follow)* | KB `retrieve` + metadata filter behind `RetrieverProtocol` | C4 |
| `sfn/asl.json` | Standard state machine: steps + Retry/Catch (C2/C7/C11) + Choice + `waitForTaskToken` | E2,E4,G |
| `handler.py` | thin Lambda handler(s): SFN state I/O ↔ component calls | G |
| `iam/{sfn-exec,step-lambda,operator}.json` | 3 least-privilege roles | I |
| `DEPLOY.md` | manual deploy runbook | infra |
| `samples/claims/<image>` + gold | ≥1 image sample | D1 |

## Migration steps

**Step A — CLI feasibility spike (real Bedrock, behind `CLAIM_PROCESSOR_REAL_AWS`):**
A1 `config.py` (ids/region/threshold) · A2 `invoker` content-blocks +
`guardrailConfig` + resolved-id record · A3 `understand.py` (image path) ·
A4 run existing pipeline end-to-end via `--real` on 3 text + 1 image sample ·
A5 capture extraction accuracy, grounding, PII redaction, $/claim, latency.
*Proves the AI hypothesis; no orchestration yet.*

**Step B — Step Functions runtime + HITL + hardening:**
B1 `routing.py` + `models` fields · B2 `review.py` · B3 split `pipeline` into
step units · B4 `sfn/asl.json` + `handler.py` (Retry/Catch, Choice,
`waitForTaskToken`) · B5 CLI `decide` + pending inspect · B6 IAM role JSONs +
policy-lint test · B7 `logging_safe` + log-shape PII test · B8 offline tests
(routing/review/config/image/guardrail/policy-lint/log-shape) + SFN-Local for
the state machine · B9 `DEPLOY.md` manual runbook.

**Fast-follow (gated) — KB on S3 Vectors:**
F1 `RetrieverProtocol` · F2 `kb.py` + ingest-tagging script + embeddings
model/dims recorded (AC-C4).

## Constitution alignment

- **DI / testability:** clients stay injected; no import-time `boto3.client`;
  offline suite stays the gate (AC-J1).
- **SRP / cohesion:** routing, review, understand, config, logging are separate
  single-purpose modules; the god-object `ClaimProcessor` is still avoided.
- **Coupling:** `RetrieverProtocol` inverts the RAG dependency (DIP); the SFN
  handlers depend on modules, not vice-versa.
- **Trade-offs surfaced:** in ADRs 0004–0009; plan adds none silently.

## Grounding / dependencies (for Analyze)

- Probe that every touched path exists in `build/claim_processor/`.
- Confirm `moto` in `requirements.txt`; flag if missing (no other new pip dep).
- SFN-Local is test infra (not a pip dep); `[sfn]` criteria depend on it —
  offline unit tests still cover the step *logic*.

## Convergence (2026-09-21, append-only)

Wave 1 review classified under
[`claim-processor-real-aws.tasks.md`](./claim-processor-real-aws.tasks.md)
**Phase 1 — Convergence**. Stage 9 did not implement; T-01…T-19 rows are
unchanged.

- **sdd-replan before IAM product fixes:** F1 (`SendTaskSuccess`/`Failure`
  must be `Resource: "*"` per AWS, freeze/ADR 0009 say “on the SM”), F3
  (freeze/I2 `*` vs ADR 0009 `us.anthropic.claude-*`), F4b
  (`CLAIM_PROCESSOR_REGION` vs ViaService `us-east-1`; also named KMS key
  vs `key/*`). F8 (CRLF/injection) de-scope or spec. F9 (freeze §18
  `test_iam.py` / append `test_store.py` vs landed `test_iam_policy.py` /
  `test_store_pending.py`).
- **sdd-implement (unblocked):** C-01 H1 extra/exc_info/PAN; C-02 D3 5 MiB
  + non-UTF-8 bytes; C-03 I1 S3 prefix-split tests; C-04 ApplyGuardrail
  named ARN; C-05 empty threshold test.
- **Deferred:** F7 S3 Stubber `expected-params` for `pending_review_key`
  (low; Local roundtrip exists). Do not rewrite T-10.
- **Stage 10:** not signed off. Wave 2+ still pending; Phase 1
  missing/partial/contradicts remain.

## Replan (Stage 5)

**Date:** 2026-09-21. **Status:** PROPOSED — human gate open. Do **not**
apply spec / ADR / freeze / `build/` until the human approves.
**Binding (this pass):** `{{plan_home}}` for this kata =
`insurance-claim-processor/plans/` (`.sdd` `[roots]
claim-document-processor`); `{{constitution}}` =
`.cursor/rules/architecture-principles.mdc` (no Always-rules section);
`{{decision_log}}` = `docs/architecture/log.md`;
`{{methodology_source}}` = `<none>`; kata ADRs under
`insurance-claim-processor/adrs/` (workspace `{{adr_home}}` unused).

### Trigger

(c) Wave 1 review findings that invalidate a task (F1 / F3 / F4b
product IAM) **plus** (d) Stage 9 sent `contradicts` / `unrequested`
here (F1, F3, F4b, F8, F9). Source:
[`claim-processor-real-aws.tasks.md`](./claim-processor-real-aws.tasks.md)
**Phase 1 — Convergence**. T-01…T-19 rows are unchanged. C-01…C-05
rows are unchanged.

### Board — stay / slip / split / drop / amend-spec

| Item | Disposition | Reason |
|---|---|---|
| **F1** HITL `SendTaskSuccess`/`Failure` Resource | **amend-spec** (freeze §13 + ADR 0009 Decision §3 + Compliance; additive I1 clause). New task **C-06** only after spec lands — **not** C-03. | Freeze/ADR say “on the SM”; AWS those actions have empty Resource types → only `Resource: "*"`. Lint currently requires the broken ARN. Product IAM must not be implemented until the amend. |
| **F3** Bedrock invoke ARN width | **amend-spec** (freeze §13 + ADR 0009 Decision/Compliance + I2 model-id wording). New task **C-07** only after spec lands. | Freeze/lint pin bare `foundation-model/*` + `inference-profile/*`; ADR 0009 fitness names `us.anthropic.claude-*`; config defaults also include Nova. Pick one pattern; then lint+JSON. |
| **F4b** KMS ViaService vs `CLAIM_PROCESSOR_REGION` | **amend-spec** (freeze §13 + §4 IAM note + ADR 0009 + T-15/DEPLOY note). New task **C-08** only after spec lands. | Static IAM cannot follow env. Pin PoC IAM to `us-east-1`. Named CMK vs `key/*` rides this. Do not add a ViaService unit test that freezes `us-east-1` until the amend. |
| **F8** CRLF log injection | **drop** this iteration (tech-debt / deferred). | H1 is raw PII, not injection. Do not add an AC. |
| **F9** test path freeze drift | **amend-spec** (freeze §18 only; no EARS). | Landed names were collision-avoidance vs §1 “do not append to a shared monolith”. No code rename. |
| **C-01…C-05** | **stay** — unblocked → **sdd-implement** now. | `partial`/`missing` only; do not touch HITL Resource, model-id ARNs, or ViaService. |
| **T-06** `--real` vs `--s3` | **stay** (keep after T-09 + T-11). No new task. Do not spawn a Wave 2 duplicate. | Freeze §16: `--real` unowned until T-11; image-through-pipeline is T-09. Smaller than a T-11-early slice. |
| **T-17 `[P]`** | **stay** (record only). Not start-now. | Deps T-09. Already in freeze §15/§17. Do not spawn a duplicate Wave 2 task. |
| **F7** Stubber pending-review | **stay Deferred**. | Low; Local roundtrip covers E2 key shape. Do not rewrite T-10. |

### Recommended decisions (one sentence each)

- **F1:** Allow `Resource: "*"` **only** for `states:SendTaskSuccess` and
  `states:SendTaskFailure`; compensate with identity (operator role) and
  optional account/region conditions — never a `stateMachine:` ARN on
  those two actions.
- **F3:** Prefer least-privilege ADR 0009 — named model-id patterns
  covering the spike models actually used (`anthropic.claude-*` **and**
  `amazon.nova-*`, because `UNDERSTAND_MODEL_EXAMPLE` is Nova); amend
  freeze §13 to match; drop the lint’s exact bare `*` ARNs.
- **F4b:** PoC IAM is `us-east-1` only; `CLAIM_PROCESSOR_REGION` other
  than `us-east-1` is unsupported for IAM until T-15; `from_env` may keep
  reading the var (T-01 done); `key/*` stays (ADR 0009 scopes KMS by
  ViaService, not a named key).
- **F8:** De-scope; H1 stays PII-only.
- **F9:** Amend freeze §18 to `test_iam_policy.py` and
  `test_store_pending.py`; do not rename code.
- **T-06:** Keep T-06 after T-09 + T-11 (no T-11-early slice).

### Alternatives considered

**F1**

1. **Recommended** — `Resource: "*"` on those two actions only.
2. **Rejected** — keep the broken `stateMachine:` policy as
   docs-only PoC. HITL resume will `AccessDenied`; lint encodes the lie.
3. **Not instead of `*`** — extra conditions (`aws:SourceAccount`,
   `aws:RequestedRegion`) may ride *on top of* `*`. They cannot replace
   it: AWS documents empty Resource types for these actions (Stage 9
   finding). Do not invent a resource ARN that IAM will not evaluate.

**F3**

1. **Recommended** — named patterns for Claude + Nova (spike defaults).
2. **Rejected as default** — keep freeze/lint bare `*`. Weaker
   least-privilege; contradicts ADR 0009 Decision “resolved pattern
   (`inference-profile/us.anthropic.claude-*`)”.
3. **Rejected as default** — ADR-only `us.anthropic.claude-*`.
   `UNDERSTAND_MODEL_EXAMPLE = "us.amazon.nova-pro-v1:0"`
   (`models.py`) would `AccessDenied` on the image path.

**F4b**

1. **Recommended** — pin ViaService to `us-east-1`; document other
   regions unsupported for IAM until T-15. Smaller than templating.
2. **Rejected as default** — template `${Region}` in JSON. Static
   policy-lint cannot expand env; PoC has one region. Revisit at T-15
   if a second region is real.
3. **KMS resource:** `key/*` stays (ADR 0009 never names a CMK or
   alias). **Rejected as default:** pin `alias/claim-processor` —
   invents a key name the ADR does not evidence.

**F8** — de-scope (recommended) vs add an AC now (rejected: silently
widens H1). **F9** — amend freeze to landed names (recommended) vs
rename tests to §18 (rejected: would collide with §1 / extracted
`test_store.py`). **T-06** — keep after T-11 (recommended, smaller) vs
T-11-early slice (only if the spike is pulled forward before T-09/T-11).

### Routing after human approval

| After “yes” on the recommended set | Route |
|---|---|
| F1, F3, F4b (product IAM wording) + F9 (freeze §18) | **sdd-spec** first — amend freeze / ADR 0009 / spec I1·I2 as proposed below. **Do not implement** HITL `*`, model-id patterns, or ViaService pin until that amend lands. |
| F8 | No spec. No C-*. Deferred tech-debt. |
| C-01, C-02, C-03, C-04, C-05 | **sdd-implement** now — **unblocked**; no spec wait. |
| C-06 / C-07 / C-08 (placeholders below) | Appear **only after** the spec/ADR/freeze amend. Then sdd-implement. Not C-03. |
| Wave 2 (T-02, T-07, T-08) | May proceed in parallel with C-*, but **recommend C-* first** (small; same files as T-12 / T-03 / T-14 / T-01). Then Wave 2. |
| T-06, T-17 `[P]`, F7 | No new tasks. T-06 after T-09+T-11; T-17 after T-09; F7 stays Deferred. |

**Explicit:** C-01…C-05 remain unblocked. F1 / F3 / F4b **product IAM
must not be implemented** until spec + ADR 0009 + freeze §13 amend.
Do **not** silently put `Resource: "*"` in IAM JSON before that amend.

### Re-prioritization (proposed board order)

1. **Next implement (no spec wait):** C-01, C-02, C-03, C-04, C-05.
2. **Next after human yes + sdd-spec:** F1 HITL `*` (C-06), F3 model-id
   pattern (C-07), F4b ViaService pin (C-08) — listed as **blocked on
   spec**, not implemented.
3. **Then Wave 2:** T-02, T-07, T-08 (then hub T-09, then T-11, then
   T-06). Recommend C-* first.

### Placeholders (blocked on spec — do not implement)

| Id | Files (after spec) | Task | source-ref | Status |
|---|---|---|---|---|
| **C-06** | `build/iam/operator.json`, `build/tests/test_iam_policy.py` | HITL statement `Resource: "*"` for `states:SendTaskSuccess`/`SendTaskFailure` only; lint requires `*` on those actions and forbids `stateMachine:`/`execution:` on them. Optional account/region condition if the amend names one. | F1 | **blocked on spec** |
| **C-07** | `build/iam/step-lambda.json`, `build/iam/operator.json`, `build/tests/test_iam_policy.py` | Replace bare `foundation-model/*` + `inference-profile/*` with named patterns covering Claude + Nova; lint matches the amended I2. | F3 | **blocked on spec** |
| **C-08** | `build/iam/step-lambda.json`, `build/tests/test_iam_policy.py`, T-15 `DEPLOY.md` (when it exists) | Keep ViaService `s3.us-east-1` / `bedrock.us-east-1`; document IAM `us-east-1`-only until T-15; `key/*` stays. Then (and only then) a ViaService unit test may freeze `us-east-1`. | F4b | **blocked on spec** |

### Contradicting sentences (quoted — not invented)

**F1**

- Freeze §13 operator row: “`states:SendTaskSuccess` / `SendTaskFailure`
  on the SM”.
- ADR 0009 Decision §3: “`states:SendTaskSuccess` / `SendTaskFailure` on
  the state machine (HITL resume)”.
- Spec I1: “No role SHALL carry `AmazonBedrockFullAccess` or bucket-wide
  `s3:*`” — does **not** name an SFN resource.
- Spec I2: “Every Bedrock statement SHALL name BOTH `foundation-model/*`
  AND `inference-profile/*`, model-id segment as a pattern.” — Bedrock
  only; does **not** name an SFN resource.
- Landed `operator.json` HitlResume: `"Resource":
  "arn:aws:states:*:*:stateMachine:claim-processor"`.
- Landed lint (`test_iam_policy.py`): “operator states actions must be
  scoped to the state machine” (`stateMachine:` or `execution:`).
- Stage 9: “AWS service-auth: those two actions have **empty Resource
  types** — IAM supports only `Resource: "*"`.”

**F3**

- Freeze §13: “Every Bedrock statement names **both**
  `arn:aws:bedrock:*::foundation-model/*` **and**
  `arn:aws:bedrock:*:*:inference-profile/*`. Model-id segment is a
  **pattern** (ADR 0009).”
- Spec I2: same two families + “model-id segment as a pattern.”
- ADR 0009 Decision: “the model-id segment is a **resolved pattern**
  (`inference-profile/us.anthropic.claude-*`), marked *pattern, not a
  pinned constant*.”
- ADR 0009 Compliance: “every Bedrock statement names **both**
  `foundation-model/*` and `inference-profile/*`; the model-id segment
  is a pattern, not a constant”.
- Landed lint: `assertIn(FOUNDATION_MODEL_ARN, resources)` and
  `assertIn(INFERENCE_PROFILE_ARN, resources)` where those constants
  are the bare `*` ARNs.
- Spike defaults (`models.py`): extract/summary Claude;
  `UNDERSTAND_MODEL_EXAMPLE = "us.amazon.nova-pro-v1:0"`.

**F4b**

- Freeze §4: `CLAIM_PROCESSOR_REGION` default `"us-east-1"`;
  `from_env` reads the var. Landed test:
  `CLAIM_PROCESSOR_REGION="eu-west-1"` → `policy.region == "eu-west-1"`.
- Freeze §13: “`kms:Decrypt` / `GenerateDataKey` with
  `kms:ViaService`” — no named key, no region list.
- ADR 0009 Decision: “`kms:Decrypt` / `GenerateDataKey` scoped by
  `kms:ViaService`.” Consequences/KMS: “bucket default encryption +
  `kms:ViaService` key policy.” No CMK alias.
- Landed `step-lambda.json`: `Resource` `arn:aws:kms:*:*:key/*`;
  ViaService `s3.us-east-1.amazonaws.com` +
  `bedrock.us-east-1.amazonaws.com`.

**F8**

- Spec H1: “The system SHALL NOT write raw PII (e.g. an SSN) to
  application logs — log-shape test.”
- ADR 0008 Compliance: “**no raw PII (e.g. an SSN) appears in
  application logs** (log-shape test)”.
- Freeze §13: “an SSN-bearing packet produces **no** raw SSN in
  captured logs (AC-H1).”
- None of these name CRLF or log injection.

**F9**

- Freeze §18: T-10 → `tests/test_store.py` (append); T-14 →
  `tests/test_iam.py` (policy-lint).
- Freeze §1: “**Do not append** to a shared monolith test file.”
  Extracted home of `S3StubberTests` is already `tests/test_store.py`.
- Landed: `tests/test_iam_policy.py`, `tests/test_store_pending.py`.

**T-06 / T-17 (already known — no duplicate Wave 2 tasks)**

- Freeze §16: “There is **no `--real` flag**.” “`--real` is unowned
  until T-11.” “Image-through-pipeline is **T-09**.”
- Freeze §15/§17: T-17 is **NOT start-now**; deps T-09; `[P]` is false.

### Proposed exact deltas (do not apply until human yes → sdd-spec)

These are proposals. Spec / ADR / freeze files stay as they are.

#### Spec I1 — F1 additive (I1 does not today imply SM-scoped HITL)

**Before:**

> No role SHALL carry `AmazonBedrockFullAccess` or bucket-wide
> `s3:*` — policy-lint on the IAM JSON.

**After (proposed):**

> No role SHALL carry `AmazonBedrockFullAccess` or bucket-wide
> `s3:*` — policy-lint on the IAM JSON. WHERE the operator role grants
> `states:SendTaskSuccess` / `states:SendTaskFailure`, the Resource
> SHALL be `"*"` (AWS documents empty Resource types for those
> actions); no other statement in the three PoC roles SHALL use
> `Resource: "*"`.

I2 is **not** changed for F1 (it is Bedrock-only and does not imply
SM-scoped HITL).

#### Spec I2 — F3 named model-id pattern

**Before:**

> Every Bedrock statement SHALL name BOTH `foundation-model/*`
> AND `inference-profile/*`, model-id segment as a pattern.

**After (proposed):**

> Every Bedrock invoke statement SHALL name BOTH a
> `foundation-model/` ARN and an `inference-profile/` ARN. The
> model-id segment SHALL be a named pattern covering the spike
> models actually used (`anthropic.claude-*` and `amazon.nova-*`),
> not a pinned constant and not a bare `*`.

#### Freeze §13 — F1 / F3 / F4b

**Before (operator row):**
“`states:SendTaskSuccess` / `SendTaskFailure` on the SM; …”

**After (proposed):**
“`states:SendTaskSuccess` / `SendTaskFailure` with `Resource: "*"`
only (AWS empty Resource types; not a `stateMachine:` ARN); …”

**Before (Bedrock lead-in):**
“Every Bedrock statement names **both**
`arn:aws:bedrock:*::foundation-model/*` **and**
`arn:aws:bedrock:*:*:inference-profile/*`. Model-id segment is a
**pattern** (ADR 0009).”

**After (proposed):**
“Every Bedrock invoke statement names **both** a
`foundation-model/` ARN and an `inference-profile/` ARN. Model-id
segment is a **named pattern** covering spike models:
`…:foundation-model/anthropic.claude-*`,
`…:foundation-model/amazon.nova-*`,
`…:inference-profile/us.anthropic.claude-*`,
`…:inference-profile/us.amazon.nova-*` (ADR 0009; not a bare `*`).”

**Before (step-lambda KMS):**
“`kms:Decrypt` / `GenerateDataKey` with `kms:ViaService`”

**After (proposed):**
“`kms:Decrypt` / `GenerateDataKey` with `kms:ViaService`
`s3.us-east-1.amazonaws.com` + `bedrock.us-east-1.amazonaws.com`;
Resource `arn:aws:kms:*:*:key/*`. PoC IAM is **us-east-1 only** —
`CLAIM_PROCESSOR_REGION` other than `us-east-1` is unsupported for
IAM until T-15 (`DEPLOY.md`). `from_env` may still read the var.”

#### Freeze §4 — F4b IAM note (config behavior unchanged)

**Proposed add** under the `CLAIM_PROCESSOR_REGION` row (do not change
the default or `from_env` contract):

> IAM ViaService / key policy is pinned `us-east-1` for this PoC.
> A non-default region is readable by config (T-01) but is not a
> supported IAM deploy until T-15.

#### Freeze §18 — F9

**Before:** T-10 → `tests/test_store.py` (append); T-14 →
`tests/test_iam.py` (policy-lint).

**After (proposed):** T-10 → `tests/test_store_pending.py` (new file;
do not append `test_store.py`); T-14 → `tests/test_iam_policy.py`
(policy-lint). Reason: §1 collision-avoidance.

#### ADR 0009 Decision §2 (model-id) — F3

**Before:** “the model-id segment is a **resolved pattern**
(`inference-profile/us.anthropic.claude-*`), marked *pattern, not a
pinned constant*.”

**After (proposed):** “the model-id segment is a **resolved pattern**
covering the spike models (`inference-profile/us.anthropic.claude-*`
and `inference-profile/us.amazon.nova-*`, plus the matching
`foundation-model/` patterns), marked *pattern, not a pinned
constant*.”

#### ADR 0009 Decision §3 (operator HITL) — F1

**Before:** “`states:SendTaskSuccess` / `SendTaskFailure` on the
state machine (HITL resume)”

**After (proposed):** “`states:SendTaskSuccess` / `SendTaskFailure`
with `Resource: "*"` (HITL resume; AWS empty Resource types for
those actions — not scoped to a `stateMachine:` ARN). Identity
compensation: these actions live only on the operator role.
Optional conditions (`aws:SourceAccount`, `aws:RequestedRegion`)
may be added; they do not replace `*`.”

#### ADR 0009 Compliance / fitness — F1 + F3 + F4b

**Before:** “Fitness: no role carries `AmazonBedrockFullAccess` or
bucket-wide `s3:*`; every Bedrock statement names **both**
`foundation-model/*` and `inference-profile/*`; the model-id
segment is a pattern, not a constant; the operator role cannot
invoke models beyond the spike scope.”

**After (proposed):** “Fitness: no role carries
`AmazonBedrockFullAccess` or bucket-wide `s3:*`; every Bedrock
invoke names both a `foundation-model/` and an
`inference-profile/` ARN whose model-id segment is the Claude+Nova
pattern (not a bare `*`, not a pinned constant); operator HITL
`SendTaskSuccess`/`SendTaskFailure` is `Resource: "*"` and no other
PoC statement uses `*`; KMS is `key/*` + ViaService
`s3.us-east-1` / `bedrock.us-east-1` (PoC region pin).”

### Human ask

Approve the **recommended set** (F1 `*` HITL-only, F3 Claude+Nova
patterns, F4b us-east-1 pin + `key/*`, F8 drop, F9 freeze-§18
rename-in-docs, T-06 after T-11), **or name alternatives**. Until
then: implement C-01…C-05 only; do not edit spec/ADR/freeze/`build/`
IAM product for F1/F3/F4b.

## Spec amendment landed (Stages 2–4, 2026-09-21)

**Status:** recommended set **APPROVED** (human named no alternatives).
Spec I1/I2, freeze §4/§13/§18, and ADR 0009 Decision/Compliance are
amended. Placeholders C-06/C-07/C-08 are now tasks. **Do not implement**
product IAM (`operator.json` / `step-lambda.json` / lint) in this pass —
that is sdd-implement.

### A1 — least machinery

Static IAM JSON + `test_iam_policy.py` lint. **Rejected:** a new IAM
templating engine, CDK, and `${Region}` expansion (PoC has one region;
revisit at T-15). No new abstraction (not a G1).

### File-level touchpoints (C-06…C-08 only)

| Task | Files | Change |
|---|---|---|
| **C-06** | `build/iam/operator.json`, `build/tests/test_iam_policy.py` | HitlResume `Resource: "*"` for `states:SendTaskSuccess` / `SendTaskFailure` only; lint that currently requires `stateMachine:`/`execution:` must require `*` and forbid those ARNs on those two actions. Optional `aws:SourceAccount` / `aws:RequestedRegion` MAY ride on `*`, not instead. **AC-I1** |
| **C-07** | `build/iam/step-lambda.json`, `build/iam/operator.json`, `build/tests/test_iam_policy.py` | Replace bare `foundation-model/*` + `inference-profile/*` with Claude+Nova named patterns (freeze §13). Lint asserts the model-id segment is not a lone `*`. **AC-I2** |
| **C-08** | `build/iam/step-lambda.json`, `build/tests/test_iam_policy.py`; T-15 `DEPLOY.md` when it exists | Pin/lint ViaService literals `s3.us-east-1.amazonaws.com` + `bedrock.us-east-1.amazonaws.com`; `key/*` stays. Other `CLAIM_PROCESSOR_REGION` unsupported for IAM until T-15. |

Write-set overlap: C-03/C-04 and C-06…C-08 share `operator.json` /
`step-lambda.json` / `test_iam_policy.py`. Board: **C-01…C-05 first**,
then **C-06 → C-07 → C-08** (do not race), then Wave 2.

### Analyze (Stage 4 — this amendment)

See tasks **Analyze (Stage 4 — 2026-09-21 bounded IAM amendment)**.
CRITICAL count expected **0**. Baseline gates must stay green (no
`build/` product change this pass).
