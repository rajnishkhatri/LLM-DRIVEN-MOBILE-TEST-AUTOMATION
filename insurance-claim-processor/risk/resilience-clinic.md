# Resilience clinic — claim document processor

Clinic loop for the Bedrock/S3 path. Cards cited by id. **Recommend, then
the operator decides.** Confirming metrics are named *before* knobs.

**Symptom (anticipated, not yet measured):** a slow or throttled Bedrock
call hangs the CLI; a naive retry loop turns a regional blip into a token
storm; a retried summarize double-writes a result; a dead policy KB
either 500s the whole claim or silently hallucinates coverage.

---

## 1. Diagnose → candidates

| Failure | Card |
|---|---|
| Hung Converse / no bound | **TimeoutsDeadlines (C7)** |
| `ThrottlingException` / blip | **RetryBackoff (C2)** |
| Retry of Record after a timeout | **Idempotency (C9)** |
| Policy retrieve down, extract already succeeded | **GracefulDegradation (C11)** |
| Storm of claims, Bedrock TPM exceeded | **LoadShedding (C10)** — production queue |
| Bedrock error rate high, retries still firing | **CircuitBreaker (C1)** — only after a metric exists |
| Extract vs summary sharing one thread pool under load | **Bulkhead (C8)** — production concurrency |

Style (monolith vs queue) is **not** this clinic — see
`../worksheets/style-decision.md`.

---

## 2. Confirm the metric first

Do **not** drop a breaker on Bedrock because "LLMs fail." Measure:

- Raw Bedrock error rate split by code (`ThrottlingException` vs 4xx vs
  timeout).
- p50 / p99 / p99.9 of Converse (extract vs summary separately).
- Duplicate result objects per `s3_key` (C9).
- Fraction of summaries with `ungrounded=true` (C11).

A breaker whose "failures" are actually **slow successes** converts a
slowdown into an outage (C1 doctrine). For the PoC, the only honest
metrics are the Stubber-injected cases + wall time of compare_models.

---

## 3. Select the combination (control loop)

PoC pack: **C7 + C2 (SDK layer only) + C9 + C11**.

- C7 defines failure-fast so C2 has something to retry.
- C2: botocore `retries.mode=adaptive`, `max_attempts=5`. **No**
  application `for model in models: retry` around that — nested retries
  are the 243× amplification story.
- C9: result key = `results/{claim_key}.json`; put is overwrite of the
  same object (naturally idempotent for this PoC). Production: include
  template version in the key or a condition.
- C11: RAG is **soft** — extract still records; summary either cites or
  is flagged. S3 is **hard** — no packet, no claim.
- C1 / C8 / C10: named, **not applied** until the metrics above exist
  (PoC volume cannot fill a breaker window honestly).

---

## 4. Apply knobs (defaults, not policy)

| Card | Starting knobs | Bound to this kata |
|---|---|---|
| C7 | connect 10s, read 300s on Bedrock; connect 10s, read 60s on S3 | Batch docs; 300s is the streaming/agent floor from boto3-foundations — extract of a short text claim should finish far sooner; **recalibrate from p99.9 once measured** |
| C2 | adaptive, max_attempts 5; honour `Retry-After`; do not retry 4xx / `AccessDenied` | One layer = the SDK |
| C9 | one key per `bucket/key` | Re-running the CLI replaces the result, does not append |
| C11 | omit policy grounding; never fabricate a coverage decision | Core function = **durable extraction**; summary is additive |

---

## 5. Verify (fitness)

| Card | Metric → assertion |
|---|---|
| C7 | Stubber hang is not possible in unit tests; Config carries connect/read timeouts — assert on the client Config |
| C2 | Inject `ThrottlingException` then success; exactly one app-level call, SDK retries internally; no second nested loop |
| C9 | Process the same key twice → one result object |
| C11 | Empty retrieve → `ungrounded=true`, extraction still present |
| C1 | Not in PoC; production: trip rate vs raw error rate dashboard |

Regression: removing timeouts or adding `for _ in range(3): converse()`
around the SDK fails the C2 assertion.
