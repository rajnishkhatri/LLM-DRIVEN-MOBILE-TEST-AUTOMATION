# SDD Usage Guide — the human operator's manual

> **What this is.** The playbook for driving this workspace's four skill
> families from a coding-agent chat window. The governing decision
> (2026-08-10): the families stay **independent instruments** — no binding
> rewiring, no merged installs, no cross-skill code changes. **You are the
> integration layer.** This manual is the score: at each moment of the
> lifecycle it tells you which instrument to bring in and what to type.
>
> **Audience:** a competent engineer new to this workspace. **Primary
> harness:** Claude Code (Cursor/Copilot variances in Appendix C).

The four instruments:

| Family | What it is | Source of truth |
|---|---|---|
| **sdd-\*** (6 skills) | The 10-stage spec-driven-development lifecycle — your master workflow | `tooling/sdd-skills-bundle/` |
| **arch-\*** (7 skills) | The Richards/Ford architecture workflow (characteristics → components → style → ADRs → risk → validate) | `.cursor/skills/arch-*/` |
| **sdd-roles** (9 role cards + kernel) | Specialist role personas (specifier, architect, coder, …) with write-scope + gate contracts; also a headless conveyor (Appendix A) | `tooling/sdd-roles/` |
| **coding-rules** (1 skill + catalog) | The o1 pipeline's 18 binding rules (CR-01..CR-18) with ADR-backed trade-offs | `tooling/coding-rules-skill/` |

Plus one piece of **workspace machinery** (not an instrument you play — the
tuning check): **skill-sync** (`tooling/skill-sync/`), the manifest-driven
drift guard over every copy the table above implies. It is the bound
`check_gate` (Part 0.3), the one-command provisioner (Part 0.2), and the
Stage-8 gate here. Built 2026-08-10 by running this manual's own lifecycle
end-to-end (spec: `docs/sdd/specs/skill-sync.spec.md`).

**Two workspaces are in play — always know which one you're in:**

- **`LLM-DRIVEN-MOBILE-TEST-AUTOMATION/` (this repo)** — the design workspace
  for mobile-test-automation / spine / O7. Specs, plans, ADRs, and arch
  artifacts live here. Its `test_gate` is `<none>` (no build to run); its
  `check_gate` runs the **skill-sync drift guard** (see Part 0.3). The sdd
  lifecycle, the arch family, and the specifier/architect pairings run
  **here**.
- **Spine / o1 Java delivery repo (future code home)** — where code ships.
  The coding-rules catalog, the coder pairing, the Java gate tools, and the
  headless conveyor bite **there**. Install coding-rules into that repo when
  it exists (`tooling/coding-rules-skill/INSTALL.md`).

---

## Part 0 — One-time setup

### 0.1 What is installed where (verified 2026-08-10)

| Surface | sdd-\* | arch-\* | role cards | coding-rules |
|---|---|---|---|---|
| **Cursor** (this repo) | ✅ `.cursor/skills/` | ✅ `.cursor/skills/` | ❌ | ❌ (spine/o1-targeted) |
| **Claude Code** (this repo) | ✅ `.claude/skills/` | ✅ `.claude/skills/` | ✅ `.claude/agents/` | ❌ (spine/o1-targeted) |
| **Copilot** (this repo) | ❌ | ❌ | ❌ | ❌ (spine/o1-targeted) |
| **Committed, installable** | `tooling/sdd-skills-bundle/` | — | `tooling/sdd-roles/kernel/corpus/catalog-projections/{claude-code,cursor,copilot}/` | `tooling/coding-rules-skill/` |

Cursor and Claude Code are both fully provisioned. On a fresh clone — or
whenever the gate reports drift — **one command (re)provisions every
manifest family** (sdd → `.claude`+`.cursor`, arch → `.claude`, role
cards, kernel card, coding-rules dist):

```bash
python3 tooling/skill-sync/skill_sync.py fix
```

`fix` mirrors projections from their sources (creates missing, overwrites
changed, deletes strays — every action reported per projection) and re-checks
itself; exit 0 means provisioned-and-verified in one step.

### 0.2 What `fix` provisions (the manual equivalent, kept for transparency)

```bash
mkdir -p .claude/skills .claude/agents
cp -r tooling/sdd-skills-bundle/sdd-lifecycle tooling/sdd-skills-bundle/sdd-brainstorm \
      tooling/sdd-skills-bundle/sdd-spec tooling/sdd-skills-bundle/sdd-replan \
      tooling/sdd-skills-bundle/sdd-implement tooling/sdd-skills-bundle/sdd-converge \
      .claude/skills/
cp -r .cursor/skills/arch-lifecycle .cursor/skills/arch-characteristics \
      .cursor/skills/arch-components .cursor/skills/arch-style \
      .cursor/skills/arch-decide .cursor/skills/arch-risk \
      .cursor/skills/arch-validate .claude/skills/
cp tooling/sdd-roles/kernel/corpus/catalog-projections/claude-code/agents/*.md .claude/agents/
cp -r tooling/sdd-roles/kernel/corpus/catalog-projections/claude-code/skills/sdd-roles .claude/skills/
```

Notes:
- Copy **all seven** arch skills together — they cross-reference
  `../arch-lifecycle/references/`.
- Do **not** mount `catalog-projections/claude-code/hooks/hooks.json` into
  `.claude/settings.json`. That is the conveyor's fail-closed write-guard;
  it needs a live run directory and will block interactive work. Interactive
  role use has *no mechanical guard* — Part 3.0 tells you what to hold by
  review instead.
- `coding-rules` installs into the **spine/o1 Java delivery repo**, not
  here — follow `tooling/coding-rules-skill/INSTALL.md` (7 steps: catalog →
  binding → three front-ends → ArchUnit CI seeds → smoke-verify).
- **Drift guard:** the copies this section creates are watched by
  `tooling/skill-sync/` — `check` (the bound `check_gate`) detects drift
  between sources and projections, and also emits **advisory `SHADOW <name>`
  lines** when a `~/.claude/skills` entry collides with a project skill name
  (reported, never flips the exit — user scope isn't repo-governed). Spec:
  `docs/sdd/specs/skill-sync.spec.md`.
- **Registry freeze:** skills register at **session start** — after
  provisioning, open a fresh session; a mid-session install may not be
  discovered (or arrives late). Run Part 0.4's probes in that fresh session.

### 0.3 The bindings (already resolved for this repo)

| Binding file | Governs | Key values (this repo) |
|---|---|---|
| `.sdd/binding.toml` | sdd-\* skills | constitution `.cursor/rules/architecture-principles.mdc` · spec home `docs/sdd/specs/` · plan home `docs/sdd/plans/` · ADR home `docs/architecture/adrs/application/mobile-test-automation/` · **second ADR seam** `docs/architecture/adrs/tooling/sdd-roles/` (for work touching `tooling/sdd-roles/`) · decision log `docs/architecture/log.md` · test gate `<none>` · check gate `python3 tooling/skill-sync/skill_sync.py check` (drift guard over the skill-surface copies, bound 2026-08-10) |
| `.arch/binding.toml` | arch-\* skills | worksheets `.arch/worksheets/` · components `.arch/components/` · ADRs `.arch/adrs/` · risk `.arch/risk/` · mermaid diagrams · **per-target override:** target `mobile-test-automation` roots under `docs/architecture/` instead |
| spine/o1 `.sdd/binding.toml` `[coding-rules]` | coding-rules in delivery repo | `base_package`, module dirs, seam globs, thresholds — INSTALL.md step 2; **every placeholder must be resolved** or the skill degrades to asking |

Role cards need no binding for interactive use. The conveyor's configs live
at `tooling/sdd-roles/configs/` (Appendix A).

### 0.4 Verify it took

**First, the deterministic check** (instant, no session needed — from the
repo root; the tool resolves the manifest against CWD):

```bash
python3 tooling/skill-sync/skill_sync.py check
```

Expected: one `OK` line per family and `SUMMARY: 5 families, 0 drifted,
0 shadow -> exit 0`. Any `DRIFT` line → run `fix`; any `SHADOW` line →
advisory, see Appendix B.

**Then the discovery probes.** Ask in a fresh Claude Code session in this repo:

```text
What SDD stage are we in, and which skill owns each stage?
```

→ `sdd-lifecycle` should trigger and answer with the stage table, using
this repo's real paths (not `{{placeholders}}`). Then:

```text
Use the specifier subagent to summarize its own write scopes and doctrine.
```

→ the role card should load and answer "writes only under specs/". In spine/o1:
*"what does CR-14 require for lineage writes?"* → coding-rules triggers and
answers from the catalog.

---

## Part 1 — The map

### Golden rules (apply everywhere)

1. **One stage per invocation.** Every stage is a human↔agent micro-loop:
   you initiate → agent works → **you gatekeep** → re-enter or advance.
   Never say "run the whole lifecycle."
2. **You hold every gate.** No agent marks its own gate passed, its own ADR
   Accepted, or its own convergence done. Batch runs traverse gates
   *provisionally* and end with a ratification checklist for you.
3. **Fresh thread for review** (Stage 7). The reviewer must not inherit the
   implementer's context.
4. **Evidence, not summaries.** Failing output pasted before implementing;
   passing output pasted after; `file:line` citations for repo claims.
5. **Three strikes → replan.** A third failed attempt at the same task
   means route to sdd-replan, never a fourth variation.
6. **Precedence: ADR > catalog > book.** Never let an agent "fix" code
   toward a book against a decided ADR.
7. **Trivial changes skip the runbook, never the constitution.** Typos and
   throwaway spikes don't need the lifecycle; the binding rules still apply.
   Anything touching a decision-record seam is by definition non-trivial.

### The big map

| Moment | Skill(s) | Role pairing | You type (gist) |
|---|---|---|---|
| New non-trivial idea, no direction | sdd-brainstorm | — | "Brainstorm approaches for: \<problem\>" |
| Direction chosen → spec/plan/tasks | sdd-spec | **specifier** (§3.1) | "Spec this out: \<direction\>. Stop after the spec for my review." |
| Architecture-significant design | arch-\* (own 6-stage flow) | **architect** (§3.2) | "Run an architecture kata for \<system\>" / "Derive the -ilities" |
| Mid-flight change/blockage | sdd-replan | — | "Replan: \<what changed\>" |
| Approved tasks → code | sdd-implement (+ coding-rules in spine/o1) | **coder** (§3.3) | "Load coding-rules, then implement task \<N\>" |
| Diff done → review | code-review skill | — | fresh thread: "/code-review" |
| Review clean → gates | `{{check_gate}}`/`{{test_gate}}` | — | here: skill-sync check; spine/o1: `./mvnw verify` |
| Red findings / "is it done?" | sdd-converge | — | "Classify every gap vs the spec" |
| All green → ship | sdd-converge (Stage 10) | — | "Run the sign-off checklist" |

### Role quick reference (from the kernel catalog, v1.4.0)

| Role | Tag | Gates | Writes only | Use interactively for |
|---|---|---|---|---|
| specifier | maker | none | `specs/` | turning approved tasks into executable scenario law + QA procedures |
| architect | maker | build | `src/ tests/ docs/adr/` | structure work honoring ratified ADRs |
| coder | maker | build, tests, ir-gate | `src/ tests/` | TDD implementation of failing acceptance law |
| cleaner | maker | build, tests, crap | `src/` | behavior-preserving refactors |
| hardener | checker | tests, mutation | `src/test/ tests/ specs/` | killing surviving mutants by strengthening tests |
| qa | checker | build, tests, crap, ir-gate | `src/ tests/` | independent verification through the UI only |
| solo / maker3 / checker3 | — | (merged variants) | — | experiment arms; rarely used interactively |

---

## Part 2 — Stage-by-stage playbook

### Stage 1 — Brainstorm (`sdd-brainstorm`)

**When:** a non-trivial idea exists, no direction chosen.

```text
Run sdd-brainstorm on this problem: <problem statement — the problem, not
the solution>. Constraints: <any>. Validate every premise against the repo
before ideating.
```

**Agent should:** audit the premises (verified/refuted/unverifiable table),
generate ~6 directions (3 repo-patterned + 3 exploratory, incl. a
demand-side option where relevant), validate hypotheses with `file:line`
evidence, map dependency structure.

**Your gate:** pick the direction (by explicit id — a bare "yes" is not
valid multi-option consent). Refuted premise silently carried forward =
reject the whole output.

**Next:** sdd-spec with the chosen direction. **Mis-trigger check:** if a
direction is already chosen, skip to sdd-spec.

### Stages 2–4 — Specify · Clarify · Plan · Tasks · Analyze (`sdd-spec`)

**When:** direction chosen. Two hard gates inside: spec → (you) → plan →
(you) → tasks.

```text
Invoke sdd-spec for: <chosen direction + validated hypotheses from Stage 1>.
Write the EARS spec to docs/sdd/specs/ first, run the clarify pass (≤5
questions, one at a time), and STOP for my review before planning.
```

Then, after you approve the spec:

```text
Spec approved. Derive the plan and the task list (docs/sdd/plans/), with
dependency/parallelization markers and 1:1 EARS→pass/fail mapping. STOP
after each for my review.
```

Finally:

```text
Run the Stage-4 analyze pass: cross-check spec ↔ plan ↔ tasks ↔
constitution, ground every referenced path/API with a probe, and list
CRITICAL findings.
```

**Your gates:** spec approval (failure paths first, criteria testable);
plan approval (least machinery — a new abstraction must name what it buys
and the simpler thing rejected); task-list approval. A plan touching an
⚠️ Ask-first seam raises an ADR — in this repo that files under
`docs/architecture/adrs/application/mobile-test-automation/` (or the
`tooling/sdd-roles/` series for kernel work).

**Optional pairing:** hand the approved criteria to the **specifier** role
for executable scenario law — §3.1.

### The architecture interlude — arch-\* (its own 6-stage workflow)

**When:** the change is architecture-significant (new system, new style
question, structural risk, a "should we use X?" with real trade-offs) — or
you're designing before any sdd change exists. Not part of the sdd stage
numbering; you decide when to enter it. **Entry rules:**

- New design → stage 1 (or 1‖2). *Never start at style selection* — that's
  the Accidental Architecture antipattern.
- "Is this existing architecture sound?" → enter at arch-risk.
- A single stage you can name → invoke that skill directly.

| # | Stage | Skill | You type (gist) | Artifact lands in |
|---|---|---|---|---|
| 1 | Characteristics | arch-characteristics | "Derive and prioritize the -ilities for \<target\>" | `.arch/worksheets/<target>/` |
| 2 | Components | arch-components | "Run one component-design cycle for \<target\>" | `.arch/components/<target>/` |
| 3 | Quanta + style | arch-style | "How many quanta, and which style?" | `.arch/worksheets/<target>/style-decision.md` |
| 4 | Decisions | arch-decide | "Write the ADR for \<decision\>" | `.arch/adrs/<scope>/<target>/` |
| 5 | Risk | arch-risk | "Risk-storm \<criterion\> for \<target\>" | `.arch/risk/<target>/` |
| 6 | Validate | arch-validate | "Validate: diagrams, intersections, governance" | validation report |

(Target `mobile-test-automation` roots under `docs/architecture/` instead —
binding override.)

**Your gates per stage:** you are the stakeholder panel (top-3
characteristics, in any order — never fully rank seven); component
accept/redirect; **each style determination separately** (quanta, data,
sync/async, style — never one bundled yes); ADR Accepted (only you); risk
phase-2 arbiter + phase-3 mitigation cost calls; per-intersection sign-off.

**Batch mode** (for a whole kata in one run):

```text
Run the full arch lifecycle for <kata/system> in batch mode: traverse gates
provisionally, mark every artifact "GATE: PENDING HUMAN", queue gate-resident
duties, and end with the accumulated ratification checklist for me.
```

Nothing is Accepted until you ratify the checklist. **Handing design to
implementation:** §3.2 (the honor pattern).

### Stage 5 — Replan (`sdd-replan`)

**When:** blocked task · scope change · review finding invalidates a task ·
Stage-10 loop-back. **Never** for a new change (that's sdd-spec).

```text
Invoke sdd-replan. Trigger: <what changed / what's blocked>. Read the
current task list in docs/sdd/plans/, propose stay/slip/split/drop per
task with reasons, and if scope changed, update the spec FIRST.
```

**Your gate:** approve the replan. Routing: spec changed → sdd-spec;
ordering only → rewrite tasks; priorities only → back to sdd-implement.
State lives in the plan doc, not the chat — insist the doc is updated.

### Stage 6 — Implement (`sdd-implement`, + coding-rules in spine/o1)

**When:** approved task list exists. In **spine/o1, always preload the rules**
(don't trust auto-trigger — a missed trigger is a silent seam violation):

```text
Load the coding-rules skill and resolve its binding. This task touches
<model calls / storage / lineage / new packages / …>, so read catalog
groups <A structure | B seams | C core purity | D data&flow | E tests>.
Then invoke sdd-implement for task <N> from <tasks path>: red first — write
the failing test for its EARS criterion and paste the failing output — then
implement, paste the passing output, and verify the task's own pass/fail
criteria. Keep the diff small.
```

In this repo (`test_gate` `<none>`, doc/tooling tasks) the same without the preload:

```text
Invoke sdd-implement for task <N> from docs/sdd/plans/<name>-tasks.md. Red
first where testable; paste evidence; stop at the task boundary.
```

**Your gate per task:** failing-then-passing evidence shown; diff readable
end-to-end; defensive code names the failure it catches or gets deleted.
**Backpressure:** three strikes → sdd-replan; ballooning diff → split the
task. **Role pairing:** run the task *as* the coder role — §3.3.

### Stage 7 — Review (existing `code-review` skill — do not re-author)

**Fresh thread.** Then:

```text
/code-review
```

**This repo is not a git repository** — there is no diff/branch for
`/code-review` to target. The proven fresh-context variant (2026-08-10):
spawn a headless reviewer over the change's *file set*:

```bash
claude -p "You are a fresh-context reviewer (SDD Stage 7). You did NOT implement this change — review it cold, read-only, modify nothing. THE CHANGE: <spec path>, <plan/tasks paths>, <implementation files>, <config/doc edits>. REVIEW: implementation vs spec (every AC), correctness edge cases, config/manifest coverage, doc truthfulness. OUTPUT: top-3 triage frame first, then at most 8 findings, each: severity, file:line, what, why, suggested fix."
```

Add `security-review` when the change touches a security seam. In spine/o1, ask
for CR citations:

```text
Review this diff against the coding-rules catalog: cite rule IDs (CR-xx)
per finding, flag any mechanical-rule violation as TWO findings (the
violation + the missing/disabled ArchUnit gate), verify behavior not just
shape, and open with a top-3 triage frame.
```

**Your gate:** accept/reject findings; red findings route to Stage 9, not
to in-place patching.

### Stage 8 — Test (the executable constitution)

- **This repo:** `check_gate` is the skill-sync drift guard — run it **from
  the repo root** and paste the output (`test_gate` remains `<none>`):

```bash
python3 tooling/skill-sync/skill_sync.py check
```

  Reading the output: `DRIFT` lines are red (exit 2 — a Stage-9 input);
  `SHADOW` lines are **advisory only** (never flip the exit); green =
  `0 drifted` + exit 0. A wrong CWD fails loud with exit 1, never silently
  green.

- **spine/o1:** run the real gates and paste output —

```bash
./mvnw -q verify
```

ArchUnit seeds (the mechanical CR rules), PMD ceiling, migration checks run
here. A red gate is a Stage-9 input, not a thing to argue with. Threshold
edits "to make CI green" are the CR-18 anti-pattern — route to an ADR.

### Stages 9–10 — Converge · Sign-off (`sdd-converge`)

**When:** after review/test come back red, or "is this done?"

```text
Invoke sdd-converge. Spec: <path>. Classify every review finding / red gate
/ test failure as missing | partial | contradicts | unrequested, append a
"Phase N — Convergence" section to the task list (source-ref + gap-type per
task), and DO NOT touch code.
```

Routing: `missing`/`partial` → fix tasks → sdd-implement ·
`contradicts`/`unrequested` → sdd-replan (spec problem, not code).
Append-only — history is never rewritten. Bounded — at the agreed
max-iterations, it stops and forces your review.

**Stage 10, when convergence is claimed:**

```text
Run the Stage-10 sign-off checklist: every EARS criterion has a passing
test; gates green (paste real output); every ADR trigger hit has a filed
record; every comprehension gate answered by me in my own words; blast-radius
cleanup done (what did THIS change add that can now be deleted?).
```

You answer the checklist in your own words — the agent cannot self-sign.
Commit only when you say so.

---

## Part 3 — The role pairings (interactive mode)

### 3.0 How to invoke a role at all

Role cards are projected agent cards with a **contract** (write scopes,
gates), an **invocation prompt**, and a **doctrine**. Two ways to use one:

- **Path A — installed subagent** (after Part 0.2):
  `Use the <role> subagent for: <task>` — Claude Code delegates with the
  card as the persona's system prompt.
- **Path B — no install:** paste the card's invocation prompt + doctrine
  from `tooling/sdd-roles/kernel/corpus/catalog-projections/claude-code/agents/<role>.md`
  into chat, followed by your task.

**What YOU enforce by hand** (interactive mode has no write-guard, no
gate-runner — you are the guard):

1. The role reads the kernel skill card (`.claude/skills/sdd-roles/SKILL.md`)
   first — it is the constitution.
2. **Write scopes**: check the diff only touches the role's scopes
   (adapted to this repo's layout — say so explicitly in the prompt, e.g.
   "your specs/ scope is docs/sdd/specs/ here").
3. **Law permanence**: scenario files, once authored, are amended only by
   you — a maker caught "fixing" a test to go green is the failure mode the
   conveyor exists to prevent.
4. **Add-only tests**: makers may add tests, never modify or delete
   existing ones.
5. **One stage per session** + a **sparse handoff** at the end: decisions
   (choice, rationale, rejected alternatives), what moved, what stays red.
   This is the human-readable equivalent of the conveyor's handoff
   contract.
6. Gates: run the role's gate commands yourself where they exist (spine/o1);
   here, your review substitutes.

When you want these enforced *mechanically* instead — write-guard blocking
out-of-scope writes, gates deciding done, a tamper-evident ledger — use the
headless conveyor (Appendix A).

### 3.1 specifier + sdd-spec

**Division of labor:** sdd-spec authors the *documents* (EARS spec, plan,
tasks — stages 2–4, your gates). The **specifier** turns approved criteria
into *executable scenario law*: Given/When/Then feature files + end-to-end
QA procedures. EARS = the spec's notation; G/W/T = the law's notation.

**Drive mode** (after your task-list gate):

```text
Use the specifier subagent. Read the kernel skill card first. Your specs/
write scope is docs/sdd/specs/<change>/ in this workspace. Convert the
approved tasks at <tasks path> into scenario law: Given/When/Then feature
files with example tables for everything variable, plus end-to-end QA
procedures. The law must state how the product is launched and driven (the
entry command), and force real integration — green-in-isolation components
with no wiring is the known failure mode. You never write production code.
End with a sparse handoff: authored files, decisions encoded, what is
variable.
```

**Check mode** (audit an existing spec's testability):

```text
Use the specifier subagent to audit <spec path> as scenario law: which
criteria cannot be executed as written (no entry point, no example table,
ambiguity that a test cannot pin down)? Report gaps; change nothing.
```

**Your gate:** the law is complete (every criterion executable, entry
points stated) before you ratify. After ratification the files are **law**
— downstream roles never edit them; gaps route back to the specifier.

### 3.2 architect + arch-\* (the honor pattern)

**The pattern:** design decisions are made **human-gated in the arch
workflow** (where trade-off weighting belongs to you), *then* the architect
role does structural implementation **honoring** the ratified ADRs. The
role never invents architecture in-flight; the arch skills never write
code.

**Step 1 — design (this repo, arch-\* skills):** run the needed arch stages
(see interlude table). Ratify: characteristics worksheet confirmed, style
determinations confirmed one at a time, ADRs **Accepted by you** via
arch-decide.

**Step 2 — structural implementation (the code workspace):**

```text
Use the architect subagent. Read the kernel skill card first. Input: the
ratified ADRs at <paths> and the component design at <path>. Honor them —
do not re-decide them. Partition the modules accordingly, enforce the
dependency rule (IO-near code depends on IO-far policy, never the reverse),
add property tests on the partitioned modules (add-only), and record each
significant partition decision as a new Proposed ADR under docs/adr/.
Write only under src/, tests/, docs/adr/. Suites stay green throughout.
Structure only: a behavior gap goes backward through the handoff, not into
your diff. End with a sparse handoff: what moved, which rule motivated it,
which properties now hold, which new ADRs await my acceptance.
```

**Your gate:** new ADRs it drafted are **Proposed** — you accept them (or
route them through arch-decide's trade-off matrix if they're significant).
A structural decision that *contradicts* a ratified ADR is a stop-and-ask,
never a silent override.

### 3.3 coder + coding-rules (in spine/o1)

**The pattern:** the rules split three ways — **gates own the mechanical
subset** (ArchUnit seeds in CI), **in-context rules own the
behavioral/ADR-specific subset** (seam discipline, LLM-authority, lineage —
nothing catches these mechanically), **base reasoning owns generic craft**.
So: preload the rules, scope them to the task's groups, then run the coder.

```text
First load the coding-rules skill, resolve its binding, and read catalog
groups <B seams, D data&flow — pick per task> plus the override table.
Then use the coder subagent. Read the kernel skill card first. Implement
the failing acceptance law for task <N>: tests before code (red first —
paste the failing run), unit and acceptance suites separate, both green
before you stop. You never author or edit the law — a defective acceptance
test is reported backward, not patched. Add-only on existing tests. Write
only under src/ and tests/. No end-to-end verification — that is the
checker's job. Handoff: decisions, interfaces produced, what remains red
and why.
```

**Group map for the preload line:** any new class/package → **A** · model /
storage / external calls → **B** · `domain`/`usecase` code → **C** · state,
lineage, queues, LLM output → **D** · tests, metrics → **E**.

**Your gate:** red-then-green evidence; `./mvnw -q verify` green (the
mechanical rules); spot-check the behavioral rules the gates can't see —
model calls through the InvokeModels port, deterministic validation of
model output (never confidence scores), synchronous lineage, rejected
proposals recorded. A well-shaped no-op adapter passes every gate — only
you and the rules catch it.

---

## Part 4 — Appendices

### A — The headless conveyor (advanced)

**What it is:** `gate-runner` executes a whole arm of roles
(e.g. arm C: specifier → architect → coder → cleaner → hardener → qa)
headlessly against a **Java workspace**: per-stage role invocation via
`claude -p`, workspace scan, gate tools, handoff contracts, bounded rework
(max 3), an append-only tamper-evident ledger. Fail-closed everywhere.

**Use it when** you want mechanical enforcement and a ledger as evidence
(its green run is Stage-10 input), on real spine/o1 work. **Don't** use it for
this repo's doc/design work (gates are Java tools) or perturb the kata
arms/configs mid-study (`configs/o7*` are the pre-registered experiment).

**Setup once** (Python ≥3.11):

```bash
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -e tooling/sdd-roles/validator/ --no-deps --no-build-isolation
```

**Run** (all paths explicit by design; `ANTHROPIC_API_KEY` must be set;
machine-specific paths enter via `--bind`):

```bash
.venv/bin/gate-runner run \
  --kernel tooling/sdd-roles/kernel \
  --workspace <java-workspace> --run-dir <run-dir> \
  --config tooling/sdd-roles/configs/o7/kernel-config.json \
  --registry tooling/sdd-roles/kernel/catalog/role-registry.json \
  --descriptors tooling/sdd-roles/kernel/descriptors/invocation-descriptors.json \
  --harness claude-code --run-id <id> \
  --bind python=<python> --bind javac_build=<path> --bind junit_runner=<path> \
  --bind crap4java=<path> --bind mutate4java=<path> --bind sdd_roles_root=tooling/sdd-roles
```

Exit 0 = all green · 2 = red at the rework bound (ledger still validates).
`resume` continues an interrupted run and *refuses* a tampered one. Audit a
run dir: `.venv/bin/contract-lint validate <run-dir>`. Full flag reference:
`tooling/sdd-roles/validator/README.md`.

### B — Anti-patterns (the smell → the correct move)

| Smell | Correct move |
|---|---|
| "Take the spec and free-run" | One stage per invocation; you gate each |
| Style named before characteristics exist | arch-characteristics first (Accidental Architecture) |
| Agent marks its own ADR Accepted / gate passed | Only you ratify; batch runs end in a ratification checklist |
| Test edited to make a suite green | Law permanence: fix code, or route the law defect backward |
| Fourth attempt at the same failing task | Three strikes → sdd-replan |
| Convergence rewrites the task list history | Append-only Phase-N sections |
| Threshold loosened to pass CI | CR-18 anti-pattern → ADR or nothing |
| Rule text pasted into a front-end / second copy | One canonical catalog; front-ends are pointers |
| Review in the implementer's thread | Fresh thread for Stage 7 |
| "Trivial change" used to skip the constitution | Carve-out skips the *runbook* only |
| Mounting the conveyor's hooks.json for interactive work | Interactive = you are the guard; hooks belong to gate-runner runs |
| Same-name skill in user scope (`~/.claude/skills`) shadowing a project skill | Keep workspace-bound skills project-scoped; the gate's `SHADOW` advisory flags collisions; archive user-scope duplicates to `~/.claude/skills.archive/` (precedent: sdd-brainstorm, 2026-08-10) |
| An acceptance criterion silently pre-decides an OPEN clarify question | Specifier check-mode audit before the spec gate — contingent law is unratifiable (caught live in the skill-sync drive: AC-6 vs C2, AC-7+AC-11 vs C1) |
| An AC pins a point-in-time environmental fact (e.g. "the known SHADOW line") | ACs state repeatable behavior; environment facts are advisory expectations — when the world changes, record a dated amendment, don't leave the law stale |

### C — Per-harness variance

| | Claude Code | Cursor | Copilot |
|---|---|---|---|
| sdd-\* / arch-\* | `.claude/skills/` (Part 0.2) | ✅ already in `.cursor/skills/` — same prompts | copy bodies under `docs/skills/` + pointer files in `.github/instructions/` |
| Role cards | `.claude/agents/<role>.md` → "Use the \<role\> subagent" | cursor projection targets `.claude/agents/` (per descriptor contract) — same invocation | `.github/agents/<role>.agent.md` (30k char cap) + `.github/skills/<role>/` |
| coding-rules | `.claude/skills/coding-rules/` in spine/o1; on-demand trigger | `.cursor/skills/coding-rules/` in spine/o1 | `.github/instructions/` — **always-on condensed list**; regenerate from catalog on every catalog change |
| Invocation style | `/skill-name` or plain description | plain description | instructions auto-apply by path |

---

*Sources: `tooling/sdd-skills-bundle/` (INSTALL.md + 6 SKILL.md) ·
`.cursor/skills/arch-*` (7 SKILL.md) · `tooling/sdd-roles/` (catalog
v1.4.0, descriptors, validator README, claude-code projections) ·
`tooling/coding-rules-skill/` (README, INSTALL.md, catalog, evals) ·
`.sdd/binding.toml` · `.arch/binding.toml` · `tooling/skill-sync/` (spec:
`docs/sdd/specs/skill-sync.spec.md`). Decisions baked in: skills stay
independent (2026-08-10) · interactive-first roles · honor-pattern
architect · mandatory coding-rules preload in spine/o1 · first `check_gate` live
(skill-sync). **Validated end-to-end 2026-08-10:** the skill-sync change ran
all 10 stages through this manual — 6 human gates, specifier check-mode
audit, fresh-context review (8 findings converged), sign-off.*
