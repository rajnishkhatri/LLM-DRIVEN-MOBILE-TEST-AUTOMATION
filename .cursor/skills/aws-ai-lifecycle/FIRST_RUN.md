# aws-ai-* family — first run

If `.aws-ai/binding.toml` does not exist when any aws-ai-* skill is invoked:

1. Inspect the workspace: is `cases/aws-ai` (the modern AI-agents corpus) present?
   `cases/aws` (system-design backdrop)? Are the `docs/research/` AWS-AI Concepts
   present? Is boto3 / AWS CDK / moto installed (probe, don't assume)?
2. Propose a binding from `binding.template.toml`, adapted to what was found —
   e.g. drop `methodology_secondary` if `cases/aws` is absent; set `localstack`
   only if Docker is running.
3. Human confirms (or edits) each key. **`aws_profile` stays `<none>`** at first
   run — real credentials are never bound until the gated `aws-ai-validate`
   real-path, and only then with throwaway sandbox creds.
4. Persist to `.aws-ai/binding.toml` with a `# confirmed <date>` header and
   create the five artifact-home directories.

Never silently invent a binding: the artifact homes decide where the capability
briefs, designs, and CDK apps accumulate, and the methodology source decides what
the stages cite. Never bind a live `aws_profile` or set `localstack = on` without
explicit human confirmation — both cross the line from offline reasoning into
real infrastructure.

Sibling aws-ai-* skills do not carry their own binding files — they resolve
through this skill's schema. If a sibling is invoked standalone in a workspace
with no binding, run this first-run flow before its stage work.
