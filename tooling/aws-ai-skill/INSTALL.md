# Installing the aws-ai-* skill family

The `aws-ai-*` family is **six interdependent skills**: a router
(`aws-ai-lifecycle`) that carries the shared `references/` + binding, and five
stage skills (`aws-ai-assess/design/build/deploy/validate`) that cite the
router's references by **relative sibling path** (`../aws-ai-lifecycle/…`).

**Consequence:** always install **all six as siblings** under one `skills/`
parent. A lone stage skill has dangling references. This is the single rule that
governs every install form below.

Build the bundles first if `dist/` is empty:

```bash
tooling/aws-ai-skill/package.sh
```

---

## Form 1 — In this repo (recommended; already done)

Nothing to install. The family is provisioned into both surfaces and
drift-guarded by skill-sync:

```bash
python3 tooling/skill-sync/skill_sync.py check   # expect: OK aws-ai (29 file-pairs / 1 projection)
```

- **Claude Code** discovers `.claude/skills/aws-ai-*/` automatically.
- **Cursor** discovers `.cursor/skills/aws-ai-*/` automatically.

Use the bundles below only to run the family **outside** this repo.

---

## Form 2 — Another repo (portable, one shot)

Extract the family bundle into the target repo's skill dir — pick the surface
for your IDE (or both). All six land as siblings:

```bash
export TARGET=/path/to/other-repo        # CHANGE ME

# Claude Code:
mkdir -p "$TARGET/.claude/skills"
unzip -o tooling/aws-ai-skill/dist/aws-ai-family.zip -d "$TARGET/.claude/skills"

# Cursor (same bytes, different dir):
mkdir -p "$TARGET/.cursor/skills"
unzip -o tooling/aws-ai-skill/dist/aws-ai-family.zip -d "$TARGET/.cursor/skills"
```

Verify the sibling references resolve:

```bash
test -f "$TARGET/.claude/skills/aws-ai-assess" && \
  ls "$TARGET/.claude/skills/aws-ai-lifecycle/references/bedrock.md"   # must exist
```

If the target repo also uses skill-sync, register an `aws-ai` family in its
manifest (source `.cursor/skills`, the six members, projection `.claude/skills`)
so the two surfaces stay in sync — see this repo's
`tooling/skill-sync/manifest.toml` for the shape.

---

## Form 3 — Claude profile / claude.ai (works in any repo)

Profile skills live at `~/.claude/skills/` (or upload via the claude.ai "add
skill" button). Install **all six** `.skill` files so they sit as siblings:

```bash
mkdir -p ~/.claude/skills
for s in tooling/aws-ai-skill/dist/aws-ai-*.skill; do
  unzip -o "$s" -d ~/.claude/skills
done
ls ~/.claude/skills/aws-ai-lifecycle/references/bedrock.md   # sibling ref resolves
```

Profile install is global (every project sees it). Prefer Form 1/2 (in-repo) when
you want the skill scoped to a specific project.

---

## First run — the binding

The first time any `aws-ai-*` skill is invoked with no `.aws-ai/binding.toml`, it
runs the first-run flow (`aws-ai-lifecycle/FIRST_RUN.md`): it inspects the
workspace, proposes a binding from `binding.template.toml`, **you confirm each
key**, and it persists `.aws-ai/binding.toml` + the five artifact-home dirs.

**`aws_profile` stays `<none>` at first run** — real AWS credentials are never
bound until the gated `aws-ai-validate` real-path, and only then as throwaway
sandbox creds with explicit per-action approval. See
[../../docs/skills/aws-ai-lifecycle-instructions.md](../../docs/skills/aws-ai-lifecycle-instructions.md)
for the full workspace runbook (stages, per-axis gates, the credential gate).

---

## Verify the install

1. **Trigger check** — ask the agent (in a repo where the family is installed):
   *"which AWS AI service should we use for an internal-document Q&A portal, and
   do we need to fine-tune?"* — `aws-ai-lifecycle` should route to
   `aws-ai-assess`.
2. **Offline harness** — the bundled proof runs with no network, no creds. Run
   it from a **copy** (running in-place regenerates `__pycache__`/`.pytest_cache`):

   ```bash
   cp -R <skills>/aws-ai-validate/scripts /tmp/aws-ai-harness && cd /tmp/aws-ai-harness
   python -m pip install -r requirements-dev.txt
   python verify.py                       # expect: 8 passed → RESULT: PASS (OFFLINE)
   ```

3. **Negative check** — ask the agent to summarize a cloud-architecture article;
   the family should **not** trigger (the router's description skips non-AWS-AI
   and pure knowledge-curation work).

---

## What's included / excluded

- **Included:** each `SKILL.md`; the router's `FIRST_RUN.md`,
  `binding.template.toml`, `binding.schema.md`, all six `references/*.md`; the
  bundled runnable `scripts/` (deploy `sample_cdk_app/`, validate pytest harness).
- **Excluded:** `evals/` (dev-only benchmark rubric), `__pycache__`,
  `.pytest_cache`, `*.pyc`, `.DS_Store`.

## Troubleshooting

| Symptom | Cause → fix |
|---|---|
| Stage skill can't find `references/…` | Not installed as a sibling of `aws-ai-lifecycle` — install all six under one `skills/` parent (the family rule) |
| Family doesn't trigger | Skill dirs not at `<skills>/aws-ai-*/SKILL.md` (exact path), or you're outside the repo/profile where they're installed |
| Agent claims it ran the harness but shows no output | The harness must be executed (`python verify.py`); "I ran it / N passed" without real output is a defect the validate skill forbids |
| `bundle drifts from the skill I edited` | Rebuild: edit `.cursor` source → `skill_sync.py fix` → `tooling/aws-ai-skill/package.sh` |
| Real AWS call happens before the validate gate | A defect — `aws_profile` stays `<none>` through assess→deploy; offline Stubber/moto is the default everywhere else |
