# Ari build — session handover (implementation session)

**Session date:** 2026-09-30. **Owner:** Rajnish Khatri.
**Branch:** `ari-build` (off `cursor/skill-family-instructions`) — **committed, not
pushed.** **Status: COMPLETE** — all 12 release gates green, 3 code-review fixes
applied, stop-note written.

This is the completion handover for the session that executed
[HANDOVER.md](HANDOVER.md) (the pre-ratified build plan). It records what was
built, how, where, and what is left — enough for a fresh session or the owner to
pick up with zero prior context.

---

## 1. What this session delivered

A thin, running **Ari** demo in `ari/build/`: a hexagonal, one-quantum Python
pipeline, **fully offline-deterministic** (pytest, no network, no AWS
credentials), proven by the 12 release gates in
[../evals/eval-spec.md](../evals/eval-spec.md) §9.

```
identity gate → entitlement pre-check (before any data) → stage-0 deterministic
router → stage-1 classifier fallback → fixture-backed adapters (behind a guarded
wrapper) → synthesis with a full provenance tuple → append-only decision log
```

A live-Bedrock path exists behind a config toggle (ADR 0002, lazy `boto3`,
`guardrail_id` slot) and is **never exercised by the gates**.

### Run it

```bash
cd ari/build
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest          # 32 passed
python3 -m ari_demo "What is our current cash position across all accounts?" --persona treasurer
python3 -m ari_demo "What is our current cash position across all accounts?" --persona treasurer --inject-timeout
```

`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` is required only because the ambient anaconda
env ships a broken third-party `logfire` pytest plugin; the suite itself needs
only stdlib + pytest.

---

## 2. How it was built — the PW-1 three-wave model

Ratified plan: one contract commit, then three parallel worktree workers, then
one integration merge.

| Wave | What | Commit(s) |
|---|---|---|
| **0 — contract base** (serial) | Scaffolded `ari/build/`: frozen `domain/` types + HMAC token codec, `ports/` Protocols (identity on every method), the 72-row enum-validated golden loader, deterministic fixtures with all four canaries, and **all 12 gate tests** — collecting clean, failing only for the right reason (`NotImplementedError` / missing sweep report), never `ImportError`. | `d3fd088` |
| **1 — three workers** (parallel) | Three worktree-isolated subagents off `d3fd088`, add-only to disjoint dirs: **A** core/router, **B** adapters/resilience, **C** synthesis/model/evals. Each proved its own gates green in isolation. | A `32af9d7`, B `8692331`, C `7e9b906` |
| **2 — merge + integration** (serial) | Merged A→B→C (full pytest after each), built the composition root `app.py` + CLI. Turned gates **7** (injection canaries) and **11** (provenance completeness) green — the proof the pieces composed. | merges `c57b128`/`30b2dc9`/`c20fe70`, root `aaf504f` |
| **2b — code-review fixes** | Fixed the 3 highest-signal review findings; recorded the review in the stop-note. | `1fbde32`, `a65e88d` |

Worktrees were removed after merge; `ari-build-a/b/c` are merged into `ari-build`.

---

## 3. Gate status — all 12 green (`32 passed`)

| # | Gate | Result | Owner |
|---|---|---|---|
| 1 | Fast-path routing precision (swept θ/margin, report committed) | ✅ precision 1.000; `sweep-report.md` committed; **θ=0.8, margin=0.5** | A |
| 2 | Per-path routing accuracy | ✅ stage-0 coverage 0.953 (61/64), accuracy 1.000; classifier recovers 3/3 fall-throughs | A |
| 3 | Route-null rows: confident routes | ✅ 0 (all 8 ambiguous rows fall through) | A |
| 4 | How-to citation presence | ✅ 100% (versioned SourceRefs) | C |
| 5 | Judge faithfulness (stub + calibration guard) | ✅ uncalibrated offline → `CalibrationError`, no authority | C |
| 6 | Tenant + role canary probes | ✅ 0 violations (cross-tenant refuse, role narrow, audit events) | A |
| 7 | Injection canary probes | ✅ 0 obeyed (query / doc / data injection + phishing all inert) | Wave 2 |
| 8 | Duplicate-injection ticket write | ✅ exactly one ticket (C9) | B |
| 9 | ActionPort conformance | ✅ approval unbypassable though unimplemented | C |
| 10 | Injected Omni timeout | ✅ deterministic degrade + ticket offer, complete provenance | B |
| 11 | Provenance completeness | ✅ 100% of answers (incl. refusals, clarify, degraded) | Wave 2 |
| 12 | Structural: no-context-no-call · imports point inward | ✅ | A |

**End-to-end proofs** (captured in [WHERE-I-STOPPED.md](WHERE-I-STOPPED.md)):
TC-01 happy data path (full provenance tuple), TC-08 injected timeout
(deterministic degrade + ticket offer), TC-05 cross-tenant refusal (audit event,
canary absent), TC-07 doc-injection inert (answer cited, `CANARY-DOC-9147`
stripped, doc flagged).

---

## 4. Code-review pass (high effort) — 3 fixed, 5 known edges

All eight findings were outside the gated 72-row paths. **Fixed** (`1fbde32`,
gates still green):

- **F4 honesty** — a DATA query with no matching Omni row returned empty text at
  confidence 1.0 cited to a fabricated `:no-match` source → now answers honestly
  (no source, confidence 0.0, ticket offer).
- **F2 entitlement** — the cross-tenant check matched the token `acme` without
  comparing to `ctx.tenant`, refusing an Acme user their own data → now refuses
  only a tenant *other than* the caller's own.
- **F1 governance** — the `narrow` decision was declared but unenforced → the
  pipeline now short-circuits narrow (like refuse) *before* any adapter runs and
  returns a scoped answer + audit event.

**Documented known edges** (not bugs in the demo'd paths; good panel material):
keyword-based doc sanitization can strip legitimate how-to lines; the guarded
wrapper's timeout budget only labels *after* the call returns (can't bound a slow
sync call); the CLI ctx hardcodes `turn_id` (latent C9 collision if a Pipeline is
reused across turns); `verify_token` raises `AttributeError` not `IdentityError`
on a validly-signed non-dict payload; `stage0` THRESHOLD/MARGIN are hand-
duplicated vs the sweep report (gate 1 catches drift).

---

## 5. Layout and ownership

| Path | Owner | What |
|---|---|---|
| `ari_demo/domain/` | wave 0 (frozen) | shared types + HMAC signed-token codec |
| `ari_demo/ports/` | wave 0 (frozen) | port Protocols (hexagonal boundary) |
| `ari_demo/evals/golden_set.py` | wave 0 (frozen) | 72-row loader, enum-validated |
| `ari_demo/core/`, `router/` | worker A | identity gate, entitlement, stage-0, sweep |
| `ari_demo/adapters/`, `resilience/` | worker B | Omni/Docs/Jira adapters, guarded wrapper |
| `ari_demo/synthesis/`, `model/`, `evals/judge.py` | worker C | synthesis, ModelPort, classifier, judge stub, ActionPort |
| `ari_demo/app.py`, `__main__.py` | wave 2 | composition root + CLI |
| `fixtures/` | wave 0 (frozen) | deterministic Omni/Docs/Jira data + canaries |
| `tests/` | wave 0 (frozen) | the 12 gates (32 tests) |
| `sweep-report.md` | worker A | committed threshold-sweep output |

Design artifacts (ratified earlier, this repo): ADRs `../adrs/0001-0003`, eval
spec + golden set + 10 cases `../evals/`, characteristics worksheet
`../worksheets/`, C4 diagrams `../design/`.

---

## 6. Deliberately deferred (designed, not built)

Live judge calibration (needs the 20-row human-labeled slice, TPR/TNR ≥ 0.9);
live stage-1 classifier (offline deterministic stands in for the Agent Squad
adapter — referenced, **not installed**); live Bedrock (`BedrockModelAdapter`
behind the toggle); circuit breaker C1 (deferred behind its CloudWatch signal —
the guarded wrapper is its slot); SSE/streaming (CLI prints; edge transport is a
swappable adapter).

---

## 7. Next steps (separate work, per HANDOVER §10)

1. The **≤3-page brief** for the panel: six sections, 7 questions for Dana, a
   leadership coda, and the managed-substrate roadmap table.
2. Optional **≤5 slides**.
3. The panel talk-track already exists in `cases/ripple/eval-layer-talk-track.md`.

If hardening past the demo: close the five known edges in §4 (start with doc
sanitization — treat retrieved docs as never-executed data rather than editing
their text).

**Housekeeping:** `ari-build` is local only. Push / open a PR when ready. The
unrelated working-tree changes under `.okf/` and `cases/` were left untouched.
