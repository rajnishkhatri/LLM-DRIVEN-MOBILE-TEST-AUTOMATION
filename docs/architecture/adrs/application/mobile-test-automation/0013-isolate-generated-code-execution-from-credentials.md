---
type: architecture
title: ADR 0013 — Isolate generated-code execution from credentials; commit the process shape now, the sandbox technology later
description: 'The execution-isolation decision spun out of stage-5 risk mitigation M42 (P1 register entry P1-15), which found that ADR 0009''s untrusted-source-text premise and the unsandboxed credential-holding device-gate worker are two ends of one attack path: injected test content steers code generation, and the generated code executes on the host holding Perfecto, gateway, and test-account credentials. The chosen response removes the prize rather than building the cage — the execution context holds no long-lived credentials, receives a short-lived single-run device session token, and never holds the gateway credential at all — with separate-process execution committed as a shape requirement and the sandbox technology deferred to the last responsible moment. Static-gate rules on generated code are declared a supplement, not the control.'
tags: [architecture, mobile-test-automation, adr, arch-decide]
---

# ADR 0013. Isolate generated-code execution from credentials; commit the process shape now, the sandbox technology later

## Status

**Accepted** — 2026-07-27, at the combined gate that also re-signed-off the
spine spec (post-P1-mitigation baseline) and accepted ADR 0012. Accepted with
one assumption recorded rather than verified: that the device cloud can issue
**short-lived, single-run session credentials**. The decision direction does
not depend on the answer (see Consequences for the fallback); the assumption
rides the week-0 access request (M8) and the Perfecto MSA/DPA read (M1).
Last responsible moment for the sandbox *technology*: **before the first
generated script executes** (weeks 3–8). Last responsible moment for the
*shape* committed here: **now**, because it determines the worker's structure
and is the expensive retrofit. Per ADR 0010 as amended, the security review
runs as a parallel track and did not block acceptance; the queue entry stands.

## Context

**Forces.** ADR 0009 exists on an explicit premise: test steps ingested from
Octane, ALM/QC, and Excel are **untrusted input by the sources' own framing**,
which is why injection screening is mandated at three trust boundaries. Stage-5's
P1 pass followed that premise one step further than any prior artifact had, and
found the far end of it:

1. Untrusted source text drives code generation.
2. Generated code is compiled and executed by the device-gate worker.
3. That worker holds the Perfecto credential, the gateway credential, and —
   after M34's credential indirection — resolves the test-account credential.

So **injected content that can steer generation has a delivery vehicle, and the
vehicle executes on the host holding every credential in the system.** The blind
pass scored these as separate entries (ADR 0009's threat model; P1-15's
unsandboxed execution at 3×2 = 6); they are one path, and nothing in the design
connected them.

**Why E3 does not dispose of this.** The internal-network fact bounds who can
reach the system, and it was correctly used to reduce several P3 and P1 findings.
It cannot be used here: **E3 cannot dismiss the threat model that an accepted ADR
is built on.** If untrusted source text is a real premise — and ADR 0009 is
Accepted on it — then it is real all the way to execution. Invoking E3 at step 3
while relying on the premise at step 1 would be incoherent.

**What bounds the exposure today.** E2 (mock data) means an exfiltrated
credential reaches test accounts and a test app environment, not customer data.
That sets impact at 2 rather than 3 — but the credential also authorizes actions
attributable to the pipeline, and M8 already ruled attribution harm at impact 3
in its own right. The prize is therefore worth removing regardless of the data
class.

**Alternatives considered.**

- **Credential isolation + separate-process shape + static-gate rules, sandbox
  technology deferred** (chosen).
- **Commit a full sandbox technology now** (container-per-run, seccomp/gVisor, a
  dedicated unprivileged user) — stronger and eventually likely correct, but it
  decides at week 0 something better decided when the worker exists and its
  runtime constraints are known, and it does nothing that credential isolation
  does not already do about the *value* of a successful escape.
- **Static analysis of generated code only** — cheap and reuses the existing
  static gate, but allowlist-shaped analysis of generated code is
  false-negative-prone by nature; as the sole control it is a filter presented as
  a boundary.
- **Trust the screening library** — the implicit status quo. Makes ADR 0009's
  three call sites the single point of failure for an attack path that ends in
  credential compromise, and ADR 0009 itself already concedes that its boundary
  is invocation-dependent and structurally invisible.
- **Human review of every generated script before execution** — genuinely
  effective and genuinely fatal to the system's purpose: the throughput argument
  for automating conversion at all disappears if a human reads every artifact.

**Qualification.** Nygard test: passes — it changes the worker's structure, its
dependencies, and its credential topology, serving a top-3 characteristic.
Third-law test: passes — every option trades blast radius, retrofit cost,
schedule, throughput, or enforceability. Timing: the shape must be decided now
and the technology must not be.

### Trade-off matrix

| Contextual factor (weight) | Isolation + shape now, tech later (chosen) | Full sandbox now | Static analysis only | Trust screening | Human review each script |
|---|---|---|---|---|---|
| Blast radius if injection succeeds (5) | **++** one run's session token, no gateway credential | ++ same, plus contained escape | −− full credential set | −− full credential set | ++ |
| Cost if retrofitted after the worker exists (5) | **++** shape fixed now, cheapest moment | ++ | ++ nothing to retrofit | ++ | ++ |
| Schedule cost at week 0 (4) | **++** near-zero — credential topology is a design choice | −− sandbox hardening now | ++ | ++ | ++ |
| Throughput impact (4) | **+** one process start per run | + same | ++ none | ++ none | −− defeats the system's purpose |
| Enforceability / assertability (3) | **+** credential absence is assertable; static rules leak | ++ structurally enforced | − false negatives | −− invocation-dependent | + but unscalable |
| Defends when screening is bypassed (5) | **++** independent layer | ++ | − | −− single point of failure | ++ |

## Decision

**We will isolate generated-code execution from credentials: the execution
context holds no long-lived credentials, receives a short-lived single-run device
session token, and never holds the gateway credential at all; generated code runs
in a separate operating-system process from the orchestrating worker, with the
sandbox technology chosen at the last responsible moment; and generated code
passes static-gate capability rules before execution, declared a supplement
rather than the control.**

The why front and center: **remove the prize rather than build the cage.**
Sandboxing raises the difficulty of a successful escape, which lowers likelihood.
Credential isolation lowers what a successful escape is *worth*, which lowers
impact — and impact reductions survive the discovery of a new escape technique
while likelihood reductions do not. It is also nearly free at this moment,
because credential topology is a design choice and not yet a codebase.

**Technical justification:**

- **The gateway credential has no business in the execution context at all.**
  Executing a test script requires no model access; generation already happened.
  This is not a mitigation so much as a correction — the credential was going to
  be there only because one process was going to do both jobs.
- **A single-run device session token bounds the window to one run**, so an
  exfiltrated token buys what the run itself already had rather than standing
  access to the device cloud.
- **The separate-process requirement is a shape, not a product.** Committing that
  generated code never loads into the orchestrator's process or classloader keeps
  every sandbox option (container, dedicated user, seccomp profile, JVM-level
  restriction) open while making the retrofit — the expensive outcome — impossible
  by construction.
- **Static capability rules ride an existing gate.** No filesystem access outside
  the workspace, no arbitrary network egress, no process spawning, no reflection
  or dynamic class loading. A generated script failing these quarantines and does
  not execute (the M10a never-silent posture).

**Business justification:**

- **Cost:** near zero now — a credential-flow decision and a process boundary.
  The same controls added after a monolithic worker exists mean re-plumbing
  credential acquisition through a component that was built assuming ambient
  access.
- **Strategic positioning:** a bank asking "what happens if a malicious test step
  reaches your code generator" gets a two-layer answer (screening, then an
  execution context worth nothing) rather than a one-layer answer that ADR 0009
  already describes as structurally invisible.
- **Time to market:** no impact on the week-3 spine gate, which runs a
  hand-written reference test. The controls here bind when generated code first
  executes, in weeks 3–8.

## Consequences

- **Short-lived device session credentials are an unverified vendor capability.**
  If the device cloud issues only long-lived tokens, the credential-isolation
  half degrades: the executing process would hold a standing device credential,
  and the process-isolation half must then carry proportionally more weight — most
  likely promoting the deferred sandbox technology from "chosen later" to
  "required, and stronger." The fallback is named so the gate is not surprised;
  the *decision* to isolate does not change either way.
- **Static capability rules will produce false negatives**, and this ADR says so
  rather than implying coverage. They are a cheap filter that raises the cost of
  the obvious attempt; the boundary is the credential topology and the process
  edge.
- **Deferring the sandbox technology is a real bet**, not a free option: it
  assumes weeks 3–8 will have the schedule to choose and harden one. The shape
  commitment is what makes the bet survivable — if the schedule collapses, a
  separate process with a dedicated unprivileged user is a defensible floor that
  requires no new infrastructure.
- **One process start per run** is added latency on a path already dominated by
  device-session time. Acceptable, and measurable if it ever stops being.
- **Interaction with M41's advisory judge:** both decisions push the same
  direction — no autonomous authority for machine output. Generated code executes
  without ambient privilege; the judge's grade advises rather than certifies. That
  consistency is deliberate.
- **The red-team corpus gains a case class it did not have.** ADR 0009's corpus
  tested screening; it never tested injection *through* generation *into*
  execution. Now that the corpus has an owner (M36 — the security function),
  end-to-end injection-to-exfiltration cases are assignable rather than
  hypothetical.
- Losing options' trade-offs: a full sandbox now would have bought contained
  escape at a week-0 schedule cost and a premature technology choice; static
  analysis alone would have been a filter mislabeled as a boundary; trusting
  screening would have made three library call sites the single point of failure
  for credential compromise; per-script human review is effective and dissolves
  the system's reason to exist.
- Imposes on future work: no long-lived credential in an execution context; no
  gateway credential in the device-gate worker; generated code never loads into
  the orchestrator's process; new generated-artifact types pass the capability
  rules before execution.

## Compliance

- **Credential-absence assertion (automated, startup and test):** the execution
  process's resolved configuration and environment contain no gateway credential
  and no long-lived device credential; the check runs at startup and is covered by
  a test, so a regression fails the build rather than the audit.
- **Process-separation assertion (automated, CI-blocking):** an ArchUnit-style
  rule that generated-artifact loading and execution types are unreachable from
  the orchestrator's process boundary, completed by a runtime assertion — the same
  two-half construction ADR 0009 requires for F3, and for the same reason: a
  dependency rule proves structure, not behavior.
- **Static capability rules (automated, blocking before execution):** no
  filesystem access outside the workspace, no arbitrary network egress, no
  process spawning, no reflection or dynamic class loading; a failing script
  quarantines with an alert and does not execute.
- **Session-scope assertion (automated, per run):** the device credential used by
  an execution is single-run and expires with it; a run reusing a prior run's
  credential quarantines.
- **Red-team corpus case class (per release, owner: the security function per
  M36):** the corpus includes end-to-end cases attempting credential exfiltration
  via generated code, not only screening-bypass cases. A regression blocks the
  release.
- **Security-review queue entry (per ADR 0010):** untrusted-input execution and
  credential handling are both triggers; the review runs as parallel work,
  drained before first production release.

## Notes

Author: arch-decide, invoked from stage-5 arch-risk (P1 mitigation M42)
Date: 2026-07-27
Approved by / date: the owner / 2026-07-27, at the combined gate (spec
post-P1-mitigation re-sign-off + ADR 0012 + ADR 0013 + the ADR 0011 M39
amendment, one approve-all decision). The short-lived-session-credential
assumption was accepted as recorded with its fallback, not verified first.
Superseded date: —
Last modified / by / what: 2026-07-27 / arch-decide / Status flipped
Proposed → Accepted at the combined gate
