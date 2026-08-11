# 6. Live invocation carries the runner contract in the command template

Date: 2026-08-09
Status: Accepted

## Context

The 2026-08-09 live harness-leg probe
(`docs/skills/sdd-roles/evals/live-leg-probe-report.md`) drove the first
real LLM CLI through `gate-runner run` and pinned why no live harness could
ever complete a stage:

1. `Runner._stage` requires the role to leave `<run_dir>/handoff.draft`,
   but the three live descriptor rows' `command_template` values passed
   neither `{run_dir}` nor any equivalent — while the orchestrator corpus'
   STUB descriptors always did (`--run-dir {run_dir}`). The channel existed
   in the deterministic goldens and was never carried into the live rows.
2. No doctrine surface states the draft obligation: `handoff.draft`
   appears only in the stub. Role cards speak of "the handoff" as an
   artifact of record, never of where or how the draft is written.
3. `{args}` — the stage-task channel named by the registry invocation
   prompts ("Work only your stage for: {args}") — is never substituted by
   the runner: `_fill` is single-pass over template tokens, so the literal
   token reached the live model.
4. On claude-code CLI 2.1.185, `--agents` takes an inline JSON object, not
   a file path — the `{agents_file}` token binds a JSON value there.

Constraints on any fix: the registry invocation prompts are **kata-frozen
bytes** (ADR 0004 — any registry edit invalidates the instrument); the
kernel skill card body is **emitter-generated code**, not catalog data; and
descriptor `command_template` content is validated only as a string (no
check or projection embeds it — confirmed by coupling probe: projections
carry only the hooks-side template; the valid-corpus descriptor set is an
independent example, not a synced copy).

## Decision

**The runner contract rides the invocation channel itself.** One atomic
change:

1. **Descriptor amendment (all three live rows, uniformly):** the
   `command_template` prompt argv becomes a quoted composite token —
   `"{prompt} {args}\n\nRunner contract (mechanical): …"` — delivering, at
   every live invocation: the stage task (`{args}`, now a **required bind**
   for live runs), the stage id (`{role}`), the run directory
   (`{run_dir}`), the successor (`{next_role}`), and the exact
   `handoff.draft` shape (field-by-field, matching
   `kernel/schemas/handoff-contract.schema.json` and the orchestrator
   corpus drafts: `gate_outcomes` empty for the runner to fill,
   `completion_evidence` empty, provenance `role_authored`). Single-pass
   `_fill` substitutes every token in the composite because they all live
   in one template token — **no recursive fill was added**.
2. **Runner capability (validator 0.7.0 → 0.7.1, additive):**
   `_invoke_role` now exposes `next_role` — the arm successor; the final
   stage points back to the arm's entry stage, the convention the
   orchestrator corpus already uses (green scenario: final checker hands to
   the entry coder). Purely additive fill key; no schema, check, or golden
   changes (`to_role` remains schema-constrained only — CHK-CHAIN verifies
   the ledger hash chain, not handoff role sequences).
3. **Doctrine placement:** the delivered composite IS the doctrine line.
   Rejected placements, and why: registry prompts (kata-frozen bytes);
   kernel skill body (emitter code — a validator content change with
   42-golden blast radius for one line); role cards/bodies (nine
   duplicated mechanical lines for a conveyor-wide obligation). The ADR
   plus the descriptor text are the durable record.

Known accepted quirk: the frozen registry prompt ends with a literal
`{args}` that survives fill (replacement text is never re-scanned); the
composite places the real task text immediately after it, so the delivered
prompt reads "…for: {args} <task>". Cosmetic, recorded here, fixable only
by a registry edit (deliberately not taken — kata pin).

Rejected alternatives: a recursive/two-pass `_fill` (kernel code growing an
injection surface — bind values could then smuggle tokens); passing the
run-dir as a CLI flag per harness (no uniform flag exists across the three
CLIs; the prompt channel is harness-neutral); a wrapper script per harness
(equipment standing between descriptor and CLI — the descriptor IS the
binding layer).

## Consequences

- The handoff leg is mechanically completable by any live harness; the
  claude-code leg re-drive is recorded in the live-leg probe report
  (part 2). cursor/copilot rows carry the same contract but remain
  live-unverified until their CLIs exist (R-COPILOT-LIVE / R-CURSOR-LEG
  stay open on CLI absence alone).
- `args` joins the live-run bind set (`configs/o7/README.md` token map);
  omitting it fails fast at fill time — a task-less live stage can no
  longer run silently, which the probe showed produces plausible unasked
  work.
- `{agents_file}` semantics on claude-code 2.1.185 (inline JSON derived
  from the projection card) are recorded in the config README as a
  binding note; a future CLI accepting file paths changes the binding
  value, not the descriptor.
- Emitter and catalog projection goldens regenerate (the projection stamp
  hashes the descriptor row — `role-emit project` ×3 each, selftest 20/0
  ×2 after); orchestrator goldens and the kata instrument stay
  byte-untouched (the kata stamp depends on registry bytes, which this
  decision deliberately never touches).

## Notes added during the same-day landing (2026-08-09)

- **Token-regex fix (validator 0.7.2):** the first full-conveyor re-drive
  hit a latent runner bug — `_TOKEN` matched `[a-z_]+` only, so the canon
  config's digit-bearing binds `{crap4java}`/`{mutate4java}` were
  unfillable by the runner that ships them. Class widened to `[a-z0-9_]`;
  only `configs/o7` carries digit tokens, zero golden exposure; selftest
  20/0 ×2.
- **Contract text vs the decision law:** two iterations of the composite's
  decision clause were needed before it stated `chk_decisions_v1` exactly
  (≥1 decision per completed handoff; each with non-empty
  `rejected_alternatives` or the `alternatives_considered: none` sentinel
  plus rationale). Lesson recorded in the probe report: text delivered to
  live roles must state the validator's laws verbatim — approximations
  cost one live attempt each.
- **Outcome:** first live green stage, then first fully-green live
  conveyor run (`live-full-001`, exit 0 — evidence in the evals bundle).

## Amendment 2026-08-09 (third session) — the decision-law clause names the item type

**Third instance of the same lesson.** The first kata pilot cell
(greenfield-1 × arm B, live) failed BETWEEN-RUN validation with CHK-SCHEMA:
the specifier's handoff was well-formed in every other respect — three
decisions, correct roles, correct envelope — but it wrote
`rejected_alternatives` as an array of **objects**
(`{alternative, reason}`) where `handoff-contract.schema.json` requires an
array of non-empty **strings**.

The composite's clause said only "a non-empty rejected_alternatives array".
That is true and useless: it constrains the array and says nothing about its
items, so a capable model supplies the richer structure it would naturally
prefer. The two earlier iterations of this same clause (recorded above) fixed
*which* decisions are required and *when*; this one fixes the item TYPE.

**Change:** in all three descriptor rows, the clause now reads "EITHER a
non-empty rejected_alternatives array whose every item is a plain non-empty
STRING (one sentence of prose per rejected option — never an object, never a
nested field) OR …". Nothing else in the template moved (diff: exactly three
lines, one per row).

**Tax paid:** the projection stamp hashes the descriptor row, so the six-regen
ran (`role-emit project` ×3 for both golden sets); projection stamp
`catalog:b2b1edd94ec0` → **`catalog:1d520797652a`**; selftest 20/0 ×2
byte-identical; `contract-lint validate configs/o7` 29/0. The kata
workspaces carry a copy of the projection skill card and were regenerated so
their stamp matches.

**Standing lesson, now with three data points:** every clause of the runner
contract must state the validator's law at the granularity the law is
enforced at — including element types, not just container shapes. Each
approximation costs exactly one live attempt to discover.

## Amendment 2026-08-10 (fourth session) — reconcile the D7 write-guard with the draft obligation

**The obligation this ADR introduced collided with the D7 write-guard.** The
Decision above made every role write `<run_dir>/handoff.draft` or fail its
stage (`runner.py`, "wrote no handoff draft"). But the write-guard's
writer-only law — pinned by guard corpus `writer-only-run-dir` — blocks *any*
role write into the run directory: "only the gate-runner writes the run
directory and ledger". The two accepted laws are in direct conflict, so a
hook-mounted run dies at stage one. Proven on the bench (scripted probe) and
live (`live-hooks-001`: the draft write was blocked at t≈106 s and the run
died). It stayed invisible because the retro `chk_scope` lint resolves writes
from the runner's *workspace* scan, and the run dir is not in the workspace —
so retro enforcement never saw the draft, while live PreToolUse enforcement
intercepts by path and does.

A correction to the fix originally sketched in the kata-study plan: because
copy-per-cell isolation puts the run dir *beside* the workspace (not inside),
the guard rejects the draft at the **containment** check (`REPO_SCOPE`, path
escapes the workspace root), which fires *before* the `WRITER_ONLY` raise. An
exemption placed only ahead of `WRITER_ONLY` would never be reached.

**Change (validator, owner-approved):** in `guard._evaluate`, before the
containment check, the current stage role may **create or modify exactly
`<run_dir>/handoff.draft`** and nothing else in the run directory. The
carve-out is:

- **one filename wide** — every other run-dir path still blocks (`WRITER_ONLY`
  inside the workspace, `REPO_SCOPE` outside it);
- **create/modify only** — `delete` is never exempt (the runner owns the
  `unlink` after it reads the draft);
- **symlink-safe** — the candidate is symlink-resolved (`_canonical_abs`,
  factored out of `_contained_rel`) and compared to the *lexical* draft path,
  so a `handoff.draft` that is really a symlink resolves *away* from the
  literal path, misses the exemption, and falls through to normal evaluation
  (a link onto a protected test is caught as `TESTS_PROTECTED`).

The exempt surface is a transient note that does not survive its own stage:
the runner reads it, seals the durable `handoff-<run_id>-NNN.json` (still
guard-blocked, runner-written), then unlinks the draft.

**Tax paid (corpus, invariant 7):** five new guard decision cases —
`handoff-draft-allow` (outside-workspace run dir, the live case),
`handoff-draft-allow-inside`, `handoff-draft-delete-block` (delete still
`WRITER_ONLY`), `run-dir-other-block` (a different run-dir path still blocks),
and `handoff-draft-symlink-block` (the laundering attack, blocked
`TESTS_PROTECTED`). The selftest harness gained one `handoff-symlink-escape`
setup; `GUARD_DECISION_CASES` 23 → **28**. Validator **0.7.2 → 0.7.3**.
Selftest 20/0 ×2 byte-identical; `contract-lint validate` 29/0 on all four
arm configs; ir-gate selftest 8/8; workspace lint clean. Neither stamp moved
(`kata:73fca8cae0f6`, `catalog:1d520797652a`) — the change is validator code
plus guard corpus, and feeds neither digest.

**Acceptance still open:** the unit cases prove the decision; the real
acceptance is a hook-mounted live run reaching `passed` on every stage with
the guard still blocking protected tests. That is the guarded pilot cell of
the kata-study pricing pass and is executed there, not here.

**Standing lesson:** an obligation added to one accepted law (the runner
contract) must be reconciled against every other accepted law it touches (the
D7 guard) *in the same decision*. This one was not, and the gap was only found
when a live run exercised both at once — the exact cost the digest triangle
and the corpus exist to avoid.
