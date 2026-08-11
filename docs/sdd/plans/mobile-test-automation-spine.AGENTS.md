# Spine repo `AGENTS.md` — T01 scaffold deliverable (DRAFT)

> **What this is.** The literal `AGENTS.md` that spine task **T01** creates at the
> root of the new `mobile-test-automation-spine` repository. It lives here, in the
> workspace, because the repo does not exist yet (T01–T04 unexecuted) — this
> workspace holds spec/plan/architecture artifacts, the repo holds implementation.
> **The file itself now lives at `spine-repo/AGENTS.md`** (with its `CLAUDE.md`
> companion and a README). This file keeps the provenance, status and change log
> only — it no longer carries a second copy of the body, and the `---8<---` marker
> convention is retired. Extracting a body from inside a wrapper is what made two
> drifting copies possible; there is now exactly one.
>
> **Provenance.** Derived from `docs/research/o7-agents-md-external-research.md` §8
> (14-agent external research, adversarially verified, 2026-08-09). Stack rows come
> from the **APPROVED** spine plan (PLAN-OK 2026-07-28, plan:64-73); dimensions the
> plan does not pin are marked `UNRESOLVED` rather than guessed.
>
> **Status.** DRAFT. The spine task board is still **awaiting TASKS-OK**, and the o7
> Stage-2 gate is open with two signatures pending — so the o7 section below is
> written as not-yet-binding. Neither gate is closed by this file.
>
> **Change log** (this wrapper only — none of it ships to the repo). Full record
> and rationale: `o7-agents-md-work-summary.md`; live tracker:
> `o7-agents-md-next-items-plan.md`.
> - **2026-08-09 (drafted)** — 211 lines / 11.4 KB. Stack rows from the approved
>   plan; everything the plan did not pin marked `UNRESOLVED`. Landed as T01
>   scope via **Amendment A1**.
> - **2026-08-09 (I1+I3)** — 218 / 11.9. B-5 named as the no-registry enforcer
>   (was "none today"); coding-rules pointers now installed by T01 (**A2**), so
>   the missing-bundle fallback reads as *scaffold incomplete*, not the norm;
>   spec-marker vs seed-id numbering note added.
> - **2026-08-09 (I4)** — 237 / 13.4. **The stack `UNRESOLVED` block is gone** —
>   JDK distribution, Spring Boot line, formatter, analysers, null safety and the
>   ArchUnit artifact are all pinned (**A5**), with the deferred set named so
>   nobody adds it speculatively. Only the attribution-trailer policy remains
>   `UNRESOLVED`.
>
> - **2026-08-09 (final, v1.0.0)** — 247 / 14.1. Corrected a line left stale by
>   A4 (the binding ships **resolved**, not placeholder-laden); added the standing
>   *do not commit to an Appium 3 pin* rule when I6 was parked; version stamp
>   `0.1.0-draft` → `1.0.0`. **Content is final; the board still awaits TASKS-OK,
>   so the file is final in content, not yet landed.**
>
> **Length accepted at 237→247** (I9): <200 is a soft guideline, not a model limit,
> and the only ceiling that truncates is Codex's 32 KiB. Most of the growth is the
> file replacing "ask the owner" with an answer — which removes a round trip on
> every read rather than adding cost.
>
> **Companion:** `CLAUDE.md` at the same root containing exactly `@AGENTS.md`
> (Claude Code reads `CLAUDE.md`, not `AGENTS.md`; import beats symlink on Windows).
> Do **not** add `.github/copilot-instructions.md` — it outranks `AGENTS.md` under
> Copilot. Audit the root for `.cursorrules` / `.rules` / `.windsurfrules` /
> `.clinerules` / `AGENT.md` before declaring this file canonical: Zed reads the
> first match and ranks `AGENTS.md` seventh.

---

## Where the file is

| | |
|---|---|
| **The file** | [`spine-repo/AGENTS.md`](spine-repo/AGENTS.md) — 247 lines / 14.1 KB, **v1.0.0** |
| Companion | [`spine-repo/CLAUDE.md`](spine-repo/CLAUDE.md) — one line, `@AGENTS.md` |
| How to use them | [`spine-repo/README.md`](spine-repo/README.md) |
| Full work record | [`o7-agents-md-work-summary.md`](o7-agents-md-work-summary.md) |
| Live tracker | [`o7-agents-md-next-items-plan.md`](o7-agents-md-next-items-plan.md) |

**Editing rule.** Change `spine-repo/AGENTS.md`, then add a line to the change log
above. Never the reverse, and never re-inline the body here — one copy is the whole
point of this split.
