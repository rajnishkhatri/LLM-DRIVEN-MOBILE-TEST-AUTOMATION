# Where I stopped — Ari build

**Written:** 2026-09-30, end of the implementation session.
**Status: COMPLETE — all 12 release gates green, `32 passed`, fully offline.**
Built per [HANDOVER.md](HANDOVER.md) (PW-1: contract-first wave 0 → three
parallel worktree workers → single integration merge).

## What's green

`cd ari/build && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest` → **32 passed in ~0.08s**, no network, no AWS credentials.

| # | Gate | Result |
|---|---|---|
| 1 | Fast-path routing precision (swept θ/margin, report committed) | ✅ precision 1.000; `sweep-report.md` committed; θ=0.8 margin=0.5 |
| 2 | Per-path routing accuracy | ✅ stage-0 coverage 0.953 (61/64), accuracy 1.000; classifier recovers 3/3 fall-throughs |
| 3 | Route-null rows: confident routes | ✅ 0 (all 8 ambiguous rows fall through) |
| 4 | How-to citation presence | ✅ 100% (versioned SourceRefs) |
| 5 | Judge faithfulness (stub + calibration guard) | ✅ uncalibrated offline → `CalibrationError`; no authority |
| 6 | Tenant + role canary probes | ✅ 0 violations (cross-tenant refuse, role narrow, audit events) |
| 7 | Injection canary probes | ✅ 0 obeyed (query/doc/data injection + phishing all inert) |
| 8 | Duplicate-injection ticket write | ✅ exactly one ticket (C9, key = conversation+turn) |
| 9 | ActionPort conformance | ✅ approval unbypassable even though unimplemented |
| 10 | Injected Omni timeout | ✅ deterministic degrade + ticket offer, complete provenance |
| 11 | Provenance completeness | ✅ 100% of answers (incl. refusals, clarify, degraded) |
| 12 | Structural: no-context-no-call · imports point inward | ✅ |

The `θ=0.8 / margin=0.5` values are outputs of `sweep.py` over the golden set,
not opinions — regenerate with `python3 -m ari_demo.router.sweep`.

## End-to-end proofs (via the CLI)

```
python3 -m ari_demo "What is our current cash position across all accounts?" --persona treasurer
python3 -m ari_demo "What is our current cash position across all accounts?" --persona treasurer --inject-timeout
```

- **TC-01 (happy data path):** stage-0 routes DATA on the fast path (rule
  `d-cash-position`), the answer is built from the Omni fixture, and the
  decision log carries the full provenance tuple (route · source+version ·
  confidence · model+prompt version · entitlement scope · rule ids).
- **TC-08 (injected timeout):** the guarded wrapper raises `GuardTimeout`, the
  DATA path degrades deterministically — honest copy, no invented numbers, a
  ticket offer — and provenance stays complete. The conversation survives.
- **TC-05 (cross-tenant):** refused by the pre-model entitlement check with
  `entitlement.cross-tenant.refused`; `CANARY-ACME-7719` never appears.
- **TC-07 (doc-injection):** the how-to answer is cited; the embedded
  `CANARY-DOC-9147` instruction is stripped as inert data; the doc is flagged
  for human review.

## Architecture as built

One-quantum hexagon (ADR 0001). The composition root `app.py` wires:
`gate → entitlement pre-check → stage-0 router → stage-1 classifier fallback →
adapter via the guarded wrapper → synthesis (full provenance) → decision log`.
Everything depends only on ports + domain; imports point inward (gate 12).

- **Worker A** (`core/`, `router/`): identity gate (signed token → frozen
  RequestContext, fail closed), deterministic entitlement pre-check, stage-0
  rule ladder (HANDOVER §8), threshold sweep + committed report.
- **Worker B** (`adapters/`, `resilience/`): tenant-scoped Omni, Docs (with
  injection flagging), idempotent Jira (C9); guarded wrapper (C7 timeout budget,
  C2 single jittered retry, C11 deterministic degrade + ticket floor).
- **Worker C** (`synthesis/`, `model/`, `evals/judge.py`): synthesis with a
  complete provenance tuple for every route, ModelPort (offline deterministic +
  lazy-boto3 Bedrock adapter with a `guardrail_id` slot), deterministic
  classifier, judge stub behind the calibration gate, ActionPort (contract-only).

## Deliberately deferred (designed, not built — by decision, not omission)

- **Judge verdict quality** — stub only; live verdicts require the 20-row
  human-labeled calibration slice (TPR/TNR ≥ 0.9) per eval-spec §7.
- **Live stage-1 classifier** — the offline deterministic classifier stands in
  for the Agent Squad adapter (referenced in `classifier.py`, **not installed**).
- **Live Bedrock** — `BedrockModelAdapter` exists behind the config toggle
  (lazy boto3, guardrail slot); never exercised by the gates.
- **Circuit breaker (C1)** — deferred behind its CloudWatch signal; the guarded
  wrapper is the one-place slot for it later (ADR 0001).
- **SSE/streaming** — out of demo scope; the CLI prints. The edge transport is a
  swappable adapter per ADR 0001.

## Environment note

The ambient (anaconda) Python has an unrelated third-party pytest plugin
(`logfire`) that fails to import; every pytest invocation therefore uses
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`. The suite itself needs only stdlib + pytest.

## Next (separate work, per HANDOVER §10)

The ≤3-page brief (six sections, 7 questions for Dana, leadership coda,
managed-substrate roadmap table), optional ≤5 slides, and the panel talk-track
in `cases/ripple/eval-layer-talk-track.md`.
