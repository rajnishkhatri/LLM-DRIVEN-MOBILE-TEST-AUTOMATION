---
type: runbook
title: AWS-AI lifecycle — how to use in this workspace
description: >-
  Workspace-resolved instructions for driving the aws-ai-* capability family
  (Bedrock / SageMaker / agents on AWS) in LLM-DRIVEN-MOBILE-TEST-AUTOMATION —
  the AI/ML arm that supplements the arch-* architect family. Binding paths,
  the per-axis human gates, the offline-first credential gate, and copy-paste
  prompts.
tags: [aws, bedrock, sagemaker, aws-ai, lifecycle, instructions, cursor]
---

# AWS-AI lifecycle — instructions for this workspace

Use this when the work touches **AWS AI/ML** — Amazon Bedrock, Amazon SageMaker,
Bedrock AgentCore, Strands agents, RAG/Knowledge Bases, guardrails, or shipping
an agent / AI pipeline to AWS with **boto3 + AWS CDK (Python)**. The `aws-ai-*`
family is the **capability arm of `arch-*`**: it lets the architect workflow
reason about Bedrock/SageMaker as concrete options *and* actually build and ship
the result. This is the short, path-resolved playbook.

| Need | Doc |
|---|---|
| Clone / provision skills | [../SETUP.md](../SETUP.md) |
| Architect workflow (characteristics → validate) | [arch-lifecycle-instructions.md](arch-lifecycle-instructions.md) |
| SDD how-to (spec-driven code/docs changes) | [sdd-lifecycle-instructions.md](sdd-lifecycle-instructions.md) |
| What the seed corpus contains + citation map | `.claude/skills/aws-ai-lifecycle/references/corpus-map.md` |
| Externally verified 2025–2026 AWS-AI evidence | `.claude/skills/aws-ai-lifecycle/references/research-2026.md` |
| Install the family **outside this repo** (portable `.skill` bundle) | [../../tooling/aws-ai-skill/INSTALL.md](../../tooling/aws-ai-skill/INSTALL.md) |
| Agent pointers | [../../AGENTS.md](../../AGENTS.md) |

**This repo is the design + capability workspace.** The gated real-AWS path is
reached only at the very end (stage 5), with throwaway sandbox credentials and
explicit per-action approval. Everything before it is offline.

---

## 0. Before you start

1. Open **this folder** as the Cursor / Claude Code workspace root.
2. From repo root, confirm the family is provisioned (drift guard):

```bash
python3 tooling/skill-sync/skill_sync.py check
```

Expected: `SUMMARY: 6 families, 0 drifted, 0 shadow -> exit 0`, including the line
**`OK aws-ai (29 file-pairs / 1 projection)`**. The aws-ai↔arch handoff pointers
(in `arch-style` and `arch-validate`) live in the `.cursor` source of truth, so a
later `skill_sync.py fix` won't wipe them.

3. Prefer a **fresh chat** after provisioning (skills register at session start).
4. Tell the agent to **load `aws-ai-lifecycle`** (the router) and let it route to
   the stage skill — do not say "ship the whole thing" in one shot. **You hold
   every gate**, and the credential gate is yours alone.

### First run creates the binding (`.aws-ai/binding.toml`)

Unlike `arch`, the aws-ai binding is **not committed yet** — the first time any
`aws-ai-*` skill is invoked with no `.aws-ai/binding.toml`, it runs the first-run
flow (`.claude/skills/aws-ai-lifecycle/FIRST_RUN.md`): it inspects the workspace,
proposes a binding from the template, **you confirm each key**, and it persists
`.aws-ai/binding.toml` + the five artifact-home dirs. `aws_profile` **stays
`<none>`** at first run — real creds are never bound until stage 5.

### Binding (proposed defaults — `.aws-ai/binding.toml`)

| Key | This workspace |
|---|---|
| methodology_source | `cases/aws-ai` (modern *AI Agents on AWS*: Strands + AgentCore) |
| methodology_secondary | `cases/aws` (*System Design on AWS* — concept backdrop) |
| research_home | `docs/research` (external-research OKF Concepts) |
| constitution | `<none>` (set to a principles file to enforce model-access / residency / cost rules at gates) |
| primary_language | `python` |
| iac_tool | `cdk-python` (deploy surface: boto3 + AWS CDK) |
| region_default | `us-east-1` |
| aws_profile | `<none>` — **set ONLY at the gated aws-ai-validate real-path** |
| test_stack | `stubber+moto` (offline default) |
| localstack | `off` (opt-in; needs Docker up) |
| assess/design/build/deploy/validate_home | `.aws-ai/<stage>/` |
| diagram_notation | `mermaid` |
| breadth_read_tool | `explore subagent` |

Skill bodies: `.cursor/skills/aws-ai-*` (**Cursor source of truth**) and
`.claude/skills/aws-ai-*` (**Claude projection** via skill-sync). Edit the Cursor
copy, then re-project with `skill_sync.py fix`.

---

## 1. Which skill owns which stage

| # | Stage | Skill | You are here when… | Artifact home |
|---|---|---|---|---|
| — | Router / "which stage?" | `aws-ai-lifecycle` | Starting, reached from `arch-*`, or "which AWS AI service?" | — |
| 1 | Assess (frame need + pick service) | `aws-ai-assess` | Bedrock vs SageMaker vs Q Business; fine-tune vs RAG; rough cost | `.aws-ai/assess/` |
| 2 | Design (topology, RAG, memory, guardrail/IAM) | `aws-ai-design` | Single vs multi-agent; vector store; where guardrails + IAM sit | `.aws-ai/design/` |
| 3 | Build (boto3 · Converse · Strands/AgentCore · SageMaker) | `aws-ai-build` | Writing the Python that realizes the design | `.aws-ai/build/` |
| 4 | Deploy (CDK-Python → synth) | `aws-ai-deploy` | CDK app + `cfn-lint`/`cdk-nag`-clean template on disk | `.aws-ai/deploy/` |
| 5 | Validate (offline harness → gated real-AWS) | `aws-ai-validate` | Prove it offline; then the one credential gate | `.aws-ai/validate/` |

Stages **1–2** are the design-time join with `arch-*`; **3 → 4 → 5** is the
delivery run. Stages **re-enter freely** (models, costs, APIs move). Never start
at build/deploy without a capability decision on file (Accidental Architecture in
AWS clothing). A failing gate loops back to *that* stage, never to stage 1.

**Two modes**

- **Design-time (supplement, default when reached from `arch-*`)** — the family
  *informs* an architecture decision (which AWS AI capability fits, feasibility,
  trade-offs). No credentials, no calls. Output flows back into
  `arch-style` / `arch-decide`.
- **Deploy-time (delivery)** — actually build and ship. Offline harness runs
  always; a **real account is touched only at the gated stage-5 real-path**.

---

## 2. Golden rules (short)

1. **Offline-first, credentials-gated** — no real AWS call until the stage-5
   real-path; nothing that costs money without explicit human approval. Default
   everywhere else: botocore `Stubber` (only pure-unit path for `bedrock-runtime`)
   + `moto` for supporting infra. (Human hand-poking the Bedrock **console
   playground** to feel out a model is fine — the gate is on *automated* calls.)
2. **Per-axis gates, not one bundled "yes"** — each stage's human gate confirms
   *separate* axes (see [§5](#5-the-human-gates-per-axis)). A single "go" hides
   which axis you actually agreed to.
3. **Trade-offs, not advocacy** (inherits arch-*'s first law) — managed (Bedrock)
   vs self-hosted (SageMaker) vs framework (Strands/AgentCore) is a spectrum; you
   place the cursor.
4. **Don't hardcode fast-moving facts** — resolve model IDs via
   `list_foundation_models` / inference profiles; defer version-specific facts to
   `references/research-2026.md` and **re-verify**.
5. **Cite, don't paraphrase** — modern patterns from `cases/aws-ai` ch01–07; the
   legacy lineage (ch08–10, e.g. the `\n\nHuman:` completion format) is flagged
   and corrected, never copied.
6. **Fill real gaps with executed code** — SageMaker train→endpoint, CDK deploy,
   the native Converse tool-use loop, and the test harness are supplied as code
   the family actually runs (the stage-5 harness is the proof).
7. **Durable state in files** — under the `.aws-ai/<stage>/` homes, not only chat.

---

## 3. Copy-paste prompts (Cursor)

Paste one block at a time. Replace `<…>` placeholders.

### Router

```text
Load aws-ai-lifecycle from .cursor/skills/. Using .aws-ai/binding.toml (not
placeholders — run first-run if it doesn't exist), summarize the five stages,
artifact homes, the two modes, and the credential gate for this repo.
Frame first: what's the cost of being wrong for <one-line need>?
Name the owning skill and its human gate before we advance. Do not start yet.
```

### Stage 1 — Assess

```text
Load aws-ai-assess. Need: <what the AI/ML feature must do; volume; data;
constraints>. Frame the AI/ML need, then produce the capability brief in
.aws-ai/assess/: capability class, the AWS service pick (Bedrock vs SageMaker vs
Q Business …), fine-tune-vs-RAG call, and a rough run-cost shape. Surface any
antipattern (self-hosting a plain FM job, DIY-ing Q Business, fine-tuning for
low volume) with its cost. STOP for my per-axis confirmation.
```

Your reply confirms **each axis separately**: capability class · service ·
model/approach · cost ceiling. → Advance to `arch-decide` (record ADRs) then
`aws-ai-design`.

### Stage 2 — Design

```text
Load aws-ai-design. Using the assess brief, design the solution in
.aws-ai/design/: agent topology (justify any multi-agent — "why not one?"),
knowledge/memory shape (vector store, RAG), guardrail + Cedar placement, and the
IAM boundary the Lambda actually needs. TL;DR first. STOP for per-axis confirm.
```

Your reply confirms **separately**: topology · knowledge/memory · guardrail+Cedar
placement · IAM boundary. → ADR candidates to `arch-decide`; advance to build.

### Stage 3 — Build

```text
Load aws-ai-build. Implement the design in Python (boto3 + Converse tool-use
loop / Strands / AgentCore / SageMaker) under .aws-ai/build/. Every AWS call
behind an injectable seam so the stage-5 offline harness can reach it. On
current-gen Claude, omit temperature/top_p/top_k. STOP — I review against the
design before we deploy.
```

Your reply confirms the code realizes topology, RAG shape, guardrail/IAM
boundaries, model choice, **and** the injectable seam. → Advance to deploy.

### Stage 4 — Deploy

```text
Load aws-ai-deploy. Produce the AWS CDK (Python) app under .aws-ai/deploy/ that
provisions this as a Lambda with the right Bedrock permissions. Grant BOTH ARNs
(foundation-model + inference-profile) for us.-prefixed models. End at a
cfn-lint-clean, cdk-nag-reviewed synth on disk — NO cdk deploy here.
STOP for per-axis confirm.
```

Your reply confirms **separately**: deploy-target · the two-ARN execution policy ·
packaging/architecture (container + ARM64 for AgentCore Runtime). → The real
deploy is requested at stage 5, never here.

### Stage 5 — Validate (offline; then the credential gate)

```text
Load aws-ai-validate. First the OFFLINE proof: run the bundled Stubber+moto
harness and report PASS/FAIL and what each test pins. Produce the eval + cost +
security + guardrail checklist in .aws-ai/validate/. Do NOT touch a real account
yet — stop at the credential gate and tell me exactly which cost-bearing actions
you'd run.
```

Only after a green offline run do you decide whether to open the credential gate
(next section). A green real run hands the cost/security checklist back to
`arch-validate` (design-time mode); a red run loops to build or deploy.

---

## 4. Artifact homes

| Kind | Home (default binding) |
|---|---|
| Capability brief + service-selection matrix | `.aws-ai/assess/<slug>/` |
| Solution design (topology, RAG, IAM boundaries) | `.aws-ai/design/<slug>/` |
| Implementation scaffold / notebook | `.aws-ai/build/<slug>/` |
| CDK app + `cdk synth` output | `.aws-ai/deploy/<slug>/` |
| Test / eval / harness report | `.aws-ai/validate/<slug>/` |

ADR candidates surfaced by assess/design are recorded through `arch-decide`
(under `docs/architecture/adrs/…`), not in the `.aws-ai/` homes. Brief = *what
capability + why*; ADR = *the decision of record*.

---

## 5. The human gates (per-axis)

Every gate confirms **separate axes** — never one bundled "yes" (the
conflated-axes rule inherited from `arch-style`).

| Stage | Axes you confirm separately |
|---|---|
| Assess | capability class · service · model/approach · cost ceiling |
| Design | topology (esp. any multi-agent) · knowledge/memory · guardrail + Cedar placement · IAM boundary |
| Build | code realizes the design **and** every AWS call is behind an injectable seam |
| Deploy | deploy-target · two-ARN execution policy · packaging/architecture |
| Validate | **the credential gate** + each cost-bearing action approved individually |

If your choice contradicts a determination, the agent surfaces it as a **named
antipattern with its cost**, then defers — it is your call, recorded with
consequences in the ADR.

---

## 6. The credential gate (stage 5 only)

This is the **only** place in the family that asks for real AWS access, and the
discipline is strict:

- `aws_profile` stays `<none>` through assess → design → build → deploy **and
  steps 1–5 of validate**. The offline harness runs with ambient creds scrubbed
  and bogus static creds injected, so a mis-written test fails *signing* rather
  than reaching an account.
- Real creds are requested **now, from you, as throwaway sandbox creds** — never
  reused from an earlier stage, never inferred from the environment.
- The gated real-path needs **both** latches, by design:

```bash
AWS_AI_ALLOW_ONLINE=1 python verify.py --online   # from the harness dir
```

  Passing only one keeps the run offline and warns. Real calls may incur cost and
  need **explicit human approval per action** (step 6). An unapproved
  cost-bearing call is a defect, not a shortcut.

---

## 7. Offline smoke (prove the family is ready)

The offline harness needs **no network and no credentials**. Run it from a
**workspace copy** of the bundled scripts (running in-place under
`.claude/skills/…` generates gitignored `__pycache__`/`.pytest_cache` that will
show as skill-sync drift until cleaned):

```bash
cp -R .claude/skills/aws-ai-validate/scripts /tmp/aws-ai-harness && cd /tmp/aws-ai-harness
python -m pip install -r requirements-dev.txt
python verify.py            # OFFLINE (default) — Stubber + moto, no AWS
```

Expected: pytest discovers `./tests`, all pass, exit 0. `verify.py -k converse -v`
filters/forwards to pytest. This is the always-on gate before the stage-5 real
path.

Or, in chat, without a new run:

```text
Load aws-ai-lifecycle. Confirm .aws-ai/binding.toml + skill paths for this repo,
run skill_sync check (confirm the aws-ai OK line), and summarize whether aws-ai-*
is ready — do not start a real build or open the credential gate.
```

---

## 8. Known warts

- **Bundled harness pollutes the projection if run in-place.** The stage-5 pytest
  harness and the deploy CDK app ship as authored source under the guarded skill
  tree. Running pytest/`cdk synth` inside `.claude/skills/…` creates
  `__pycache__`/`.pytest_cache` (gitignored, but skill-sync byte-compares
  everything → transient `EXTRA` drift). Run from a workspace copy (§7), or
  `skill_sync.py fix` to clean the projection.
- **The arch handoff lives in two skills, not the aws-ai tree.** The loose
  coupling adds a pointer line to `arch-style` (AWS AI/ML style candidates →
  `aws-ai-assess`) and `arch-validate` (GenAI intersection → `aws-ai-validate`'s
  GenAI+ML Lens). These are promoted to the `.cursor` source of truth, so
  `skill_sync.py fix` preserves them. `arch-decide` and `arch-risk` are named
  handoff points in the router but do **not** yet carry an explicit pointer line
  — add one if you want full symmetry.

---

## 9. What not to do here

- Do not open the credential gate before a **green offline harness run**.
- Do not bind a live `aws_profile` or set `localstack = on` without explicit
  confirmation — both cross from offline reasoning into real infrastructure.
- Do not run `cdk deploy` / `cdk bootstrap` in the deploy stage — it ends at a
  synthesized template on disk. The deploy is requested at stage 5.
- Do not hardcode model IDs as permanent — resolve them; note the SageMaker SDK
  **V2/V3** split and the **two conflicting `agentcore` CLIs**.
- Do not jump to build/deploy without an assess decision (Accidental
  Architecture).
- Do not copy the legacy `invoke_model` `\n\nHuman:` completion format — the
  default is `bedrock-runtime.converse`.
- Do not run `skill_sync.py check` from a subdirectory (fails loud).
