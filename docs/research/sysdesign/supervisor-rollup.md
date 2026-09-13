---
type: analysis
title: 'Sysdesign catalog research — supervisor rollup'
description: >-
  Wave-3 close-out for the 2026-09-13 one-shot run: file-measured inventory
  of 41 notes, mega-topic splits (B2, C3), and owner-relevant findings.
tags: [system-design-patterns, supervisor]
---

# Supervisor rollup — 2026-09-13 (wave 3 closed)

## What this is

- **Home after merge:** `docs/research/sysdesign/`. Written in the 2026-09-13 worktree `research/sysdesign-catalog-notes`, then grouped here.
- **Contents:** research notes plus this rollup. Concepts live in `cases/SystemDesignPatterns/` (written in the main workspace after the research wave).
- **Skipped:** C1 Circuit breaker, C2 Retry/backoff (already gold-standard Concepts).
- **Assigned / written:** **41 / 41** files matching `docs/research/sysdesign/*-external-research.md` (catalog-wave ids).
- **Relaunch:** none. No wave-1 (or later) id failed to land.

## Waves launched

| Wave | Count | Topics |
|---|---|---|
| 1 | 16 | A1–A6, D1–D5, C7, B1–B4 |
| 2 | 16 | B5–B8, C3–C6, C8–C11, E1–E4 |
| 3 | 9 | E5–E13 |

Wave-2/3 agents all reported the depth bar hit. This rollup **measured the files** instead of trusting those reports.

## Inventory vs the depth bar

Every expected id exists, is ≥150 lines (`wc -l`), and has the eight required headings (numbered `## 1. Scope…` style counts). E-group notes use Mechanics + when-to-use / worked example / trade-off (or a dated-facts heading) in place of a library-defaults section, as the brief requires.

**Thin notes:** none. **Missing notes:** none.

Shortest files that still clear the bar (owner visibility only — not thin):

| Id | Lines | Path |
|---|---|---|
| E6 | 231 | `docs/research/sysdesign/e6-soa-external-research.md` |
| A2 | 258 | `docs/research/sysdesign/a2-pubsub-queues-external-research.md` |
| A6 | 288 | `docs/research/sysdesign/a6-api-contracts-external-research.md` |
| C11 | 291 | `docs/research/sysdesign/c11-graceful-degradation-external-research.md` |
| D4 | 292 | `docs/research/sysdesign/d4-tracing-external-research.md` |

## Mega-topic split recommendations

### B2 — split when Concepts are cut; keep one research file

The note recommends a split. From [b2-partition-replicate-external-research.md](b2-partition-replicate-external-research.md) §10:

> This file stays one deep research note. When Concepts are cut, do **not** ship B2 as a single card — the CircuitBreaker bar applied to five mechanisms produces an unreadable Concept.

| Future id | Title |
|---|---|
| **B2a** | Partitioning (key-range, hash, composite, hot keys) |
| **B2b** | Single-leader replication |
| **B2c** | Multi-leader replication |
| **B2d** | Leaderless replication |
| **B2e** | Rebalance & request routing (key-aware; C5 stays L4/L7) |

Supervisor agrees: partitioning cards and replication-family cards should be separate Concepts. Do not split the research file.

### C3 — keep split-brain on C3; do not spin a fencing card yet

Wave-2 C3 note, “Recommended split”:

> **Keep on C3 (this card):** health-check taxonomy and K8s mapping; fail-open vs fail-closed; active/passive vs active/active; RTO/RPO + DR tiers; DNS TTL + LB failover; verified engine timings; split-brain **as the failure mode** (GitHub 2018 + “name the fence”).
>
> **Do not duplicate on C3:** fencing tokens, leases, sequencers/epochs/terms — already a complete case in [quorums-and-fencing.md](../../../cases/data-intensive-design/quorums-and-fencing.md).
>
> **Future card (only if a Concept cannot stay near CircuitBreaker length):** “Fencing & HA-cluster failover” … **Do not split yet.**

Supervisor: accept that. Split-brain stays a C3 failure mode. Tokens stay in `cases/data-intensive-design/quorums-and-fencing.md`. Do not launch a fencing card in this run.

## Other owner-relevant findings

- **E9 catalog meaning = enterprise integration hub**, not WAN hub-spoke. The note owns Hohpe Message Broker / EAI broker as meaning (1). Azure VNet / AWS Transit Gateway is a lookalike, not the style. `style-selection.md` has **no hub-and-spoke row** — no invented FSA stars.
- **E1 ↔ E10 pointers.** E1: “E1 must point at E10. Domain modules + published interfaces + enforced seams on one deployable is a modular monolith — E10's card.” E10: “E1 points here; this card points back.” E1 owns the family; E10 owns the modular variant, ch11 ratings, and too-big signs.
- **C8 tactic vs E13 architecture.** C8 owns cells as a *blast-radius tactic* (N cells → ~1/N) and keeps Azure’s “bulkhead = cell-based architecture” wording as Azure’s. E13 owns cell-based *architecture* (quantum count, router, zonal vs regional). Do not collapse the two cards.

## Recurring gaps (do not block this close-out)

- **Missing `cases/ArchitectureBook/` chapter files** in the main-repo tree on 2026-09-13. Agents cited style-selection only. Named absences include `ArchCharScope.md`, `Modular-monolith-arch.md`, `LayeredArchStyle.md`, `choosing-appropriate-arch.md`, `microservices-arch.md`, `service-based-arch-style.md`, `orchestration-driven-service-or-arch.md`, `event-driven-arch-style.md`, `microkernel-arch-style.md`.
- **Style-selection `—` stars left honest.** Group E notes treat a missing matrix cell as not-a-rating (E3 layered `—`; E5/E8/E9/E11/E13 have no row or no invented card). Do not fill stars at Concept time.
- **Some HTTP 409 / 403 fetches.** Recurring: `rfc-editor.org` 409 (C4 RFC 6585 / RFC 9110; B8 RFC 5861); AWS Builders’ Library / `builder.aws.com` 409 (C8, C11, E13); `akfpartners.com` 409 (B1 Scale Cube); `developertoarchitect.com/books.html` 409 (E2); FSA 2nd-ed chapter HTML 403 (E4); ACM Queue *Fail at Scale* 403 (C10); first-pass Netflix/Vimeo 403s left on C5. Agents fell back to datatracker, archives, or sibling notes and parked unverified numbers in Uncertain.

## Missing / thin paths

None.

## Out of scope (honoured)

- Research wave itself wrote no Concepts and did not edit the catalog of record (those landed later in the main workspace).
- Skill family not started.
