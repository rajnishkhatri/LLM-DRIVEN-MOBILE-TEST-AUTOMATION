---
type: architecture
title: 'ADR 3. Catalog-as-source: harness projections are build outputs, never sources'
description: 'Canonical role catalog is the source of truth; harness projections (Claude/Cursor/Copilot) are build outputs, never hand-edited.'
tags: [architecture, adr]
---

# ADR 3. Catalog-as-source: harness projections are build outputs, never sources

## Status

Accepted
<!-- Accepted at the sdd-roles-emitter build-gate close, 2026-08-07 (owner
ratified F4 at the combined SPEC-OK+PLAN-OK gate; build gate: selftest
18/18 ×2 byte-identical, acceptance PASS, tamper trio verified). Drafted at
the implementation stage the same day (spec C1–C4 owner-locked). Third ADR
of the tooling/sdd-roles series; executes the §7a gate rider ("the Claude
plugin is a projection, not the canonical source") and extends ADR
0001/0002 conformance to projections. -->

## Context

The §7a gate rider requires the role skills/agents to be first-class on
three harnesses at once. Each harness wants its own layout — plugin
directory, literal loose files, dual agent/skill trees — and the external
evidence (spec-kit, 50+ supported harnesses) shows those layouts differ only
in `{directory, file format, invocation prefix, argument token}`: a table,
not code. Two sources of truth (a canonical catalog *and* hand-maintained
per-harness files) would drift the moment either is edited; drift in an
agent definition is a D7 concern, not just a hygiene concern (a shadowed or
stale agent file changes what actually runs).

Alternatives considered:

- **Hand-authored per-harness files, linted for agreement** — the lint can
  only report drift after it happened; every role edit is N edits; the
  harness-specific knowledge lives in N files instead of one table.
- **One harness's format as canonical, others converted** — privileges one
  harness (exactly what the rider forbids), and conversion code embeds
  harness particulars in source.
- **Generated projections (chosen)** — one neutral catalog (registry +
  descriptor rows + doctrine bodies), a table-driven emitter, projections as
  reproducible build outputs.

## Decision

The canonical catalog — role registry, invocation-descriptor rows (whose
`projection` object IS the per-harness table), and doctrine bodies — is the
only authored source. Every harness-facing tree is `role-emit project`
output: byte-deterministic, clock-free, stamped with the kernel version and
a catalog digest. Hand-editing a projection is definitionally drift;
`role-emit verify` re-renders and byte-compares (exit 2 on any drifted,
missing, or extra path), and the committed projection trees are corpus
goldens reproduced ×2 by the selftest gate. Mount artifacts inside
projections byte-copy the shared `render_mount` output — one rendering
source across items 3 and 4. Ports conform via `kernel/docs/conformance.md`
rule #9.

## Consequences

- Adding a harness is a descriptor-row addition (projection + hooks + exit
  map) plus committed goldens — zero emitter source changes; CHK-NEUTRAL
  keeps harness tokens out of source.
- Role edits (item 5 doctrine bodies included) propagate to all harnesses by
  regeneration, never by parallel editing; the stamp digest makes stale
  projections mechanically detectable in CI.
- Projections may be regenerated wholesale at any version bump; nothing in a
  projection tree is authoritative, so no merge-back path exists or is
  wanted.
- The char-cap risk (harness file-size limits) lives as per-target data;
  cap overflow fails the render closed rather than truncating content.
