# Ari build — the running demo

A thin, hexagonal, **offline-deterministic** implementation of the Ari pipeline
(identity gate → deterministic stage-0 router → stage-1 classifier fallback →
fixture-backed adapters behind a guarded wrapper → synthesis with a full
provenance tuple), proven by the 12 release gates in
[../evals/eval-spec.md](../evals/eval-spec.md) §9.

Design is ratified in [HANDOVER.md](HANDOVER.md) — the execution contract.

## Run the gates

```bash
cd ari/build
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q
```

(`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` sidesteps an unrelated third-party pytest
plugin in the ambient environment; the suite itself needs only stdlib + pytest,
no network and no AWS credentials.)

## Layout

| Path | Owner | What |
|---|---|---|
| `ari_demo/domain/` | wave 0 (frozen) | shared types + signed-token codec |
| `ari_demo/ports/` | wave 0 (frozen) | port Protocols (hexagonal boundary) |
| `ari_demo/evals/golden_set.py` | wave 0 (frozen) | 72-row loader, enum-validated |
| `ari_demo/core/`, `router/` | worker A | identity gate, entitlement, stage-0, sweep |
| `ari_demo/adapters/`, `resilience/` | worker B | Omni/Docs/Jira adapters, guarded wrapper |
| `ari_demo/synthesis/`, `model/`, `evals/judge.py` | worker C | synthesis, ModelPort, classifier, judge stub |
| `ari_demo/app.py` | wave 2 | composition root + CLI |
| `fixtures/` | wave 0 (frozen) | deterministic Omni/Docs/Jira data + canaries |
| `tests/` | wave 0 (frozen) | the 12 gates |

## Live toggle

A `BedrockModelAdapter` exists behind a config toggle (ADR 0002), with a
`guardrail_id` slot (HANDOVER §9 B1). `boto3` is imported lazily and is never
touched by the gates. The demo runs entirely on the `OfflineModel`.
