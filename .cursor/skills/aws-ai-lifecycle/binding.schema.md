# `.aws-ai/binding.toml` schema

One shared binding for the whole aws-ai-* family, at the repo root. All keys are
strings; `<none>` disables the seam and dependent steps are skipped.

| Key | Meaning | Default |
|---|---|---|
| `methodology_source` | Path to the modern AWS-AI corpus (Strands + Bedrock AgentCore) that stage skills cite by `file.md:line`. | `cases/aws-ai` |
| `methodology_secondary` | Path to the system-design corpus used as concept/decision backdrop (networking, storage, IAM, Step Functions, SageMaker taxonomy). | `cases/aws` |
| `research_home` | Directory of external-research OKF Concepts the stages defer to for fast-moving facts. | `docs/research` |
| `constitution` | Workspace AI principles file consulted before every human gate (model-access policy, data-residency, cost ceilings). | `<none>` |
| `primary_language` | Implementation language for build/deploy code. | `python` |
| `iac_tool` | Infrastructure-as-code surface the deploy stage emits and validates. | `cdk-python` |
| `region_default` | Default AWS region for examples and synth. | `us-east-1` |
| `aws_profile` | Named AWS credentials profile. Stays `<none>` until the gated `aws-ai-validate` real-path; never used for design/build. | `<none>` |
| `test_stack` | Offline verification stack. `stubber+moto` is pure-Python and always available; `bedrock-runtime` contract tests need Stubber (moto cannot mock it). | `stubber+moto` |
| `localstack` | Opt-in LocalStack integration layer (`on`/`off`). Needs Docker running; leave `off` for the pure-Python default. | `off` |
| `assess_home` | Directory for capability briefs and service-selection matrices. | `.aws-ai/assess/` |
| `design_home` | Directory for solution designs (agent topology, RAG shape, memory, guardrail/IAM boundaries). | `.aws-ai/design/` |
| `build_home` | Directory for implementation scaffolds, tool code, and notebooks. | `.aws-ai/build/` |
| `deploy_home` | Directory for CDK apps and `cdk synth` output. | `.aws-ai/deploy/` |
| `validate_home` | Directory for offline-harness and evaluation reports. | `.aws-ai/validate/` |
| `diagram_notation` | Notation for emitted diagrams (`mermaid` recommended; C4-flavored). | `mermaid` |
| `breadth_read_tool` | Read-only exploration tool used for review-mode evidence sweeps. | `explore subagent` |

First-run resolution order: `.aws-ai/binding.toml` → propose from this schema's
defaults → human confirms → persist with a `# confirmed <date>` header.
