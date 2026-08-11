# ADR template + status rules

From `cases/ArchitectureBook/arch-decisions.md` (ch21). A worked exemplar
is sealed in `worked-answers.SEALED.md` — open it only AFTER your ADRs are
drafted, as a shape/reasoning self-check (it is a kata worked answer;
named here unfenced it leaked the decision — SD1 class, 2026-07-25).

```markdown
# ADR <N>. <Short imperative decision phrase>

## Status
Proposed | Accepted | Superseded by <M>
<!-- If this supersedes: "Accepted, supersedes <M>" -->

## Context
<The forces at play: what situation compels this decision. Name the
alternatives considered in one or two sentences each. Concise; move deep
per-option analysis to an Alternatives section if truly needed.>

## Decision
We will <decision, affirmative commanding voice>.

<Justification — the why, before any how. Technical justification AND
business justification (cost | time to market | user satisfaction |
strategic positioning). Bullet the specific reasons, as the sealed
exemplar does.>

## Consequences
<Impacts good and bad; the trade-off analysis outcome, including what the
losing options would have given us and why we passed. Constraints this
imposes on future work. Note stakeholder sign-offs on accepted downsides.>

## Compliance
<How this will be measured and governed: automated fitness function
(specify tool + rule sketch, e.g. ArchUnit layer/annotation checks) or
manual review (specify cadence + who).>

## Notes
Author: <name>
Approved by / date:
Superseded date:
Last modified / by / what:
```

## Status flow rules (`arch-decisions.md:88-110`)

- Proposed → Accepted by the agreed authority; Proposed is never superseded
  — it gets modified until Accepted.
- Superseding links go **both ways** (42 ⇄ 68 example, `:94-104`).
- Approval-criteria conversation (first run): thresholds for cost (estimate:
  hours × FTE rate), cross-team impact, and security that escalate an ADR
  beyond self-approval (`:106-110`).

## Storage (`arch-decisions.md:221-248`)

`{{adr_home}}` with subdirectories: `common/` (applies to all apps),
`application/<app>/`, `integration/` (cross-system communication),
`enterprise/` (global). One file per ADR. Prefer a home everyone can access.

## Decision antipatterns (`arch-decisions.md:10-49`)

| Antipattern | Tell | Counter |
|---|---|---|
| Covering Your Assets | decision endlessly avoided/deferred | last-responsible-moment test; collaborate with implementers |
| Analysis Paralysis | deferral past the cost/risk crossover | same test, opposite edge |
| Groundhog Day | same debate recurs, no resolution | full technical + business justification in the ADR |
| Email-Driven Architecture | decisions lost in inboxes / multiple copies | single system of record; link, don't paste |
