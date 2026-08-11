# ADR 2. Golden-run conformance for the gate orchestrator (stub-harness fixtures as the behavioral contract)

## Status

Accepted
<!-- Accepted at the sdd-roles-orchestrator PLAN-OK gate, 2026-08-07 (owner;
F1–F4 ratified as drafted, SPEC-OK granted at the same combined gate).
Drafted at the plan stage the same day (spec C3, clarify-locked by owner).
Second ADR of the tooling/sdd-roles series; extends ADR 0001
(corpus-as-contract) from validation to behavior. -->

## Context

Build item 2 ships the between-run gate orchestrator — the deterministic
gate-runner that invokes roles headlessly, runs gates between invocations, and
is the stage ledger's sole writer. Its acceptance gate must be **offline and
deterministic** (the item-1 bar, kept), but the orchestrator's whole job is to
drive *harness CLIs* that cannot exist inside an offline gate: `claude`,
`copilot`, and Cursor's `agent` are networked, non-deterministic, and absent
from a clean machine. So the question: **what executes when the gate proves the
orchestrator works?**

Alternatives considered:

- **Record-replay only** — commit recorded run directories, never execute the
  runner in the gate. The conveyor loop, template fill, exit-code branching,
  rework bounds, and resume logic all ship untested; the "orchestrator" would
  be judged by fixtures it never produced.
- **Live-harness smoke** — invoke a real harness CLI when credentials/network
  permit. Breaks offline + deterministic (the acceptance floor), makes the gate
  machine- and account-dependent, and imports every harness quirk into the
  build gate — the exact instability between-run gating exists to avoid.
- **Python-level mocks** (monkeypatched transport) — not expressible as corpus
  data, so alternate-language ports could not be conformance-gated on it;
  privileges the reference implementation, which ADR 0001 forbids.

## Decision

We will gate the orchestrator on **committed golden runs produced through stub
harnesses**: the corpus carries stub `InvocationDescriptor` sets whose command
templates invoke deterministic interpreter stubs (scenario-table-driven role
and gate-tool byte-writers), tiny workspace fixtures, and the **committed run
directories the pinned runner must reproduce byte-identically** (`--clock
fixed:…`, machine values injected only via `--bind`). The selftest executes
`gate-runner` end-to-end — real subprocesses, real template fill, real
exit-code branching, real ledger writing — twice, asserts byte-identity with
the committed goldens, and validates every produced run directory with
`contract-lint` under the full 26-check live suite. Ports of the runner are
admitted exactly like validator ports: reproduce the goldens byte-identically
under the pinned clock, or no admission.

- **Technical:** the transport boundary is descriptor data (spec S2), so
  substituting stub rows exercises every line of orchestrator code a real
  harness would touch except the harness binary itself — which is *deliberately*
  outside the contract (its quirks are runtime concerns, memo §1's whole point);
  byte-identity is the strongest equivalence that is still cheap to assert; the
  produced-run-validates-green assertion closes the loop where the checks and
  the runner share one formula source (`ledger_model`).
- **Business:** the gate stays runnable on any clean machine forever (no
  credentials, no network, no vendor availability), which is what makes the
  kata (item 6) and CI reruns viable; golden diffs make behavioral changes
  reviewable artifacts instead of anecdotes.

## Consequences

- **+** Orchestrator behavior is a committed, diffable artifact — any change to
  loop order, ledger composition, or serialization shows up as golden-run byte
  diffs in review.
- **+** Runner ports are conformance-gated with zero new mechanism (ADR 0001's
  admission procedure, extended by one artifact class).
- **+** Harness outages, auth, and nondeterminism can never flake the build
  gate.
- **−** Real-harness integration is *not* proven here — by design. First live
  contact happens where it belongs: item-6 kata runs (and item-3 hook wiring),
  against a runner whose deterministic core is already trusted.
- **−** Golden regeneration is a scripted, loud event (`regen_corpus.py`);
  editing goldens by hand is impossible in practice. Deliberate friction, same
  rationale as ADR 0001's corpus friction.
- What the losing options offered and why we passed: record-replay was cheaper
  to build but tests nothing that runs; live smoke offered "realism" at the
  cost of the gate's two defining properties — both trade the contract's
  permanence for a demo.

## Compliance

Automated — new selftest sections run by the same `contract-lint selftest`
gate: golden-run execution ×2 with byte-identity, resume-completion equality,
tamper-refusal (doctored ledger prefix ⇒ exit 2, nothing written), serialization
presence, and `contract-lint` green over every produced run directory with zero
DEFERRED rows. Port admission recorded in `docs/architecture/log.md` per
`kernel/docs/conformance.md`.

## Notes

Author: sdd-spec plan stage (drafted at plan time per spec C3)
Approved by / date: owner, 2026-08-07 (PLAN-OK — F1–F4 ratified as drafted)
Superseded date: —
Last modified / by / what: 2026-08-07 / plan stage / status Proposed → Accepted at PLAN-OK
