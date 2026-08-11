# SEALED — worked ADR exemplar (post-draft self-check ONLY)

> ⚠⚠ **DO NOT OPEN this file until your own ADRs are DRAFTED.** The
> exemplar below is the book's worked answer to a GGG kata decision; read
> early during a kata run, it seeds the decision it demonstrates (defect
> class SD1; sealed 2026-07-25 after the GGG test-drive found it named
> unfenced in adr-template.md — latent that run, same class). Use it after
> drafting, as a fidelity self-check of section shape and reasoning style.

Worked exemplar: ADR 76 — Going, Going, Gone, separate point-to-point
queues between Bid Capture, Bid Streamer, and Bid Tracker (vs a single
pub/sub topic, vs REST), with trade-offs (Bid Streamer FIFO ordering
guarantee, one-way flow, heterogeneous consumer rates vs multi-queue send
duplication) and manual code-review compliance: `arch-decisions.md:184-219`.
