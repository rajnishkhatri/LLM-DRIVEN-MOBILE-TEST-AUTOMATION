# Amazon SageMaker AI — train → pipeline → endpoint → registry (CORE)

Cross-cutting depth for the `aws-ai-*` stages when the pick is **self-hosted**
rather than Bedrock-managed: custom training, MLOps pipelines, model governance,
and the four ways to serve a model. Cited by **aws-ai-assess** (Bedrock-vs-SageMaker
fork), **aws-ai-build** (this is where most of the fresh SageMaker code lands, in
`{{build_home}}`), **aws-ai-deploy**, and **aws-ai-validate** (offline harness in
`{{validate_home}}`). Fast-moving specifics (SDK version surface, endpoint limits,
new features) defer to `research-2026.md` §2 and its `{{research_home}}` source —
re-verify before treating any version-tagged fact here as a constant.

Scope is **SageMaker AI** — the build/train/deploy product
(`docs.aws.amazon.com/sagemaker/latest/dg/`) — *not* the "Amazon SageMaker" (no
*AI*) umbrella (Unified Studio + Lakehouse + governance). Treat that umbrella as
the surrounding data plane, out of scope here. HyperPod / large-scale distributed
training is a pointer only (§8), not core.

## Contents
1. [The SDK V2/V3 split — which to target](#1-the-sdk-v2v3-split--which-to-target)
2. [Training — ModelTrainer, channels, instances, spot](#2-training)
3. [Pipelines — `sagemaker.workflow` as the CI/CD spine](#3-pipelines)
4. [Model registry — register, groups, approval flow](#4-model-registry)
5. [The four endpoint types + inference components + scale-to-zero](#5-endpoints)
6. [JumpStart — pretrained / foundation models as a shortcut](#6-jumpstart)
7. [Corpus reality — only ch10 runs; everything else is fresh code](#7-corpus-reality)
8. [HyperPod — pointer only](#8-hyperpod-pointer-only)

---

## 1. The SDK V2/V3 split — which to target

The SageMaker Python SDK crossed a **hard, backward-incompatible boundary**:
**V3.0.0 shipped 2025-11-19**. It *removed* `Estimator`, `Model`, `Predictor`,
and every framework subclass (`PyTorch`, `HuggingFace`, `SKLearn`, `XGBoost`,
`TensorFlow`) with **no compatibility shim**. In their place: `ModelTrainer`
(`sagemaker.train`) replaces the estimator family, and `ModelBuilder`
(`sagemaker.serve`) replaces `Model`/`Predictor` for packaging and deploy.

Why this matters for the family: an example that imports `sagemaker.estimator`
is silently a **V2 example** and will `ImportError` in a fresh V3 install, and
vice-versa. So the rule is **version-pin every SageMaker example and say which
generation it is** — `pip install "sagemaker<3"` for the V2 baseline,
`pip install "sagemaker>=3"` for V3 — never leave the version floating. Target the
**V2-stable baseline as the default** (it is what nearly all live code, blogs, and
the corpus assume) and carry a **clearly-flagged V3 section** alongside it, because
V3 is only months old, its field names are still settling, and boto3 underneath is
identical either way. When a V3 field name here is not yet corroborated by
`research-2026.md`, treat it as *to-verify against the V3 reference*, not as fact.

The escape hatch that never breaks: the **boto3 `sagemaker` / `sagemaker-runtime`
clients** (`create_training_job`, `create_pipeline`, `create_model_package`,
`invoke_endpoint`, …) are unaffected by the SDK rewrite. When the SDK surface is in
doubt, the boto3 call is the stable contract — and it is also what the offline
harness stubs, so build/verify code against it where the SDK abstraction is thin.

## 2. Training

**V2 (default baseline):** an estimator wraps image + instance + hyperparameters;
`fit()` launches a managed training job and uploads artifacts to S3.

```python
# pip install "sagemaker<3"
from sagemaker.pytorch import PyTorch
est = PyTorch(entry_point="train.py", role=ROLE,
              instance_type="ml.g5.xlarge", instance_count=1,
              framework_version="2.3", py_version="py311",
              use_spot_instances=True, max_run=3600, max_wait=7200,   # managed spot
              checkpoint_s3_uri=f"s3://{BUCKET}/ckpt/")               # resume on interruption
est.fit({"train": "s3://.../train/", "validation": "s3://.../val/"}) # input channels
```

**V3 (forward path):** one universal `ModelTrainer` plus config objects.

```python
# pip install "sagemaker>=3"
from sagemaker.train import ModelTrainer
from sagemaker.train.configs import InputData
trainer = ModelTrainer(training_image=IMG, source_code=SRC, compute=COMPUTE,
                       input_data_config=[InputData(channel_name="train", data_source="s3://.../train/")])
trainer.train()
```
Field names on `ModelTrainer` (spot/compute/stopping config) are still stabilizing
— confirm against the V3 reference before relying on them (`research-2026.md` §2.2).

Three levers to reason about in **aws-ai-assess/design**, independent of SDK
generation:
- **Input channels** are named S3 (or FSx/EFS) mounts — `{"train": ..., "validation": ...}`
  in V2, `InputData(channel_name=...)` in V3. The training container reads each
  channel from a local path derived from its name; keep channel names stable, they
  are part of the job's contract.
- **Instance selection** is the main cost/throughput dial: `ml.m*`/`ml.c*` for
  classical ML, `ml.g*` (single-GPU, cheaper) vs `ml.p*` (multi-GPU, NVLink) for
  deep learning; scale out with `instance_count>1` only when the training script is
  genuinely distributed. Right-sizing here dominates training spend.
- **Managed spot training** trades interruptibility for up to ~90% off on-demand.
  The V2 knobs are `use_spot_instances=True`, `max_wait ≥ max_run`, and a
  `checkpoint_s3_uri` so an interrupted job resumes instead of restarting — spot
  without checkpointing is a false economy on any job longer than a few minutes.
  V3 expresses the same intent through its compute/stopping config; verify the
  surface. Use spot for tolerant, checkpointable training; keep on-demand for
  latency-bound or non-resumable jobs.

**Offline (`{{test_stack}}`):** `moto @mock_aws` mocks the `sagemaker` control
plane — `create_training_job` / `describe_training_job` — so job-submission logic
(role, channels, hyperparameters, spot config) is unit-testable with no AWS and no
GPU. boto3: `sagemaker.create_training_job` / `describe_training_job` is the stable
call underneath either SDK.

## 3. Pipelines

`sagemaker.workflow.*` is the **CI/CD spine for ML** — a directed graph of steps
that SageMaker executes as a managed, parameterized, versioned run. This is the
governance backbone the family should reach for rather than hand-orchestrating jobs
from a script.

```python
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.parameters import ParameterString, ParameterFloat
from sagemaker.workflow.steps import ProcessingStep, TrainingStep
from sagemaker.workflow.model_step import ModelStep
from sagemaker.workflow.condition_step import ConditionStep
from sagemaker.workflow.conditions import ConditionGreaterThanOrEqualTo

data_uri  = ParameterString(name="DataUri")
min_auc   = ParameterFloat(name="MinAuc", default_value=0.80)

step_process = ProcessingStep(name="Prep",   step_args=processor.run(...))
step_train   = TrainingStep(  name="Train",  step_args=estimator.fit(...))
# data flows by PROPERTY REFERENCE, not by value:
#   step_train.properties.ModelArtifacts.S3ModelArtifacts
step_eval    = ProcessingStep(name="Eval",   step_args=evaluator.run(...),
                              property_files=[eval_report])   # PropertyFile + JsonGet gate the metric
step_register = ModelStep(    name="Register", step_args=model.register(...))
gate = ConditionStep(name="AucGate",
    conditions=[ConditionGreaterThanOrEqualTo(left=JsonGet(step_name="Eval",
        property_file=eval_report, json_path="metrics.auc"), right=min_auc)],
    if_steps=[step_register], else_steps=[])

pipe = Pipeline(name="fraud-mlops", parameters=[data_uri, min_auc],
                steps=[step_process, step_train, step_eval, gate])
pipe.upsert(role_arn=ROLE)          # idempotent create-or-update — prefer over create
pipe.start(parameters={"DataUri": "s3://.../v3/"})
```

Load-bearing facts:
- **Parameters** (`ParameterString/Integer/Float/Boolean`) make one pipeline
  definition reusable across data versions and thresholds — parameterize instead of
  editing the graph.
- **Steps**: `ProcessingStep`, `TrainingStep`, `TransformStep`, `TuningStep`,
  `ModelStep` (the modern replacement for the older `CreateModelStep` /
  `RegisterModel`), `ConditionStep`, `FailStep`, plus `LambdaStep`, `CallbackStep`,
  `EMRStep`, `AutoMLStep`, `QualityCheckStep`, `ClarifyCheckStep`.
- **Data dependencies are property references** — `step.properties....` — which is
  also how the DAG's edges are inferred. `PropertyFile` + `JsonGet` expose a metric
  from an eval report so a `ConditionStep` can gate on it (the quality gate below).
- **Lifecycle**: prefer `pipeline.upsert(role_arn=...)` (idempotent) over a bare
  create; `pipeline.start(parameters=...)` to run; `pipeline.definition()` to emit
  the JSON for review or diffing.
- **Gotcha**: a step placed inside a `ConditionStep`'s `if_steps`/`else_steps` must
  **not** also appear in the top-level `Pipeline(steps=...)` list, or you get a
  duplicate-step error — pass only the entry/branch steps at top level.

**Offline (`{{test_stack}}`):** `moto` covers `create_pipeline` /
`start_pipeline_execution`, so pipeline assembly and parameter wiring are
unit-testable; `pipeline.definition()` is a pure-Python JSON emit you can assert on
with no AWS at all. (LocalStack does **not** cover Pipelines — Stubber/moto is the
path.)

## 4. Model registry

The registry turns a trained artifact into a **governed, versioned, approvable**
model. `model.register(...)` creates a versioned entry inside a
**`ModelPackageGroup`** (the named container that collects successive versions of
"the fraud model"):

```python
model.register(
    model_package_group_name="fraud-detector",
    content_types=["application/json"], response_types=["application/json"],
    inference_instances=["ml.m5.large"],       # effectively REQUIRED
    transform_instances=["ml.m5.large"],       # effectively REQUIRED
    approval_status="PendingManualApproval")   # start unapproved
```

Approval is a small state machine: **`PendingManualApproval` → `Approved` |
`Rejected`**, transitioned with `sagemaker.update_model_package(...)`. Deploy
tooling keys off `Approved` so a human (or a gated CI check) stands between "trained"
and "in production". The canonical MLOps shape ties §3 and §4 together:
**Processing → Training → Eval → `ConditionStep`(metric) → `ModelStep`(register,
gated)** — a model only enters the registry as `PendingManualApproval` if it clears
the metric gate, and only reaches an endpoint after approval. Lineage (which data,
code, and job produced each version) is tracked automatically.

Note `inference_instances` / `transform_instances` are **effectively required** —
omitting them is a common registration failure. In V3 the packaging path runs
through `ModelBuilder` (`sagemaker.serve`); the boto3 contract
(`create_model_package_group`, `create_model_package`, `update_model_package`) is
unchanged and is what the offline harness stubs.

## 5. Endpoints

Four ways to serve, chosen on **latency / throughput / payload / cost** — the
taxonomy comes straight from `{{methodology_secondary}}`
(`cases/aws/ch13.md:313`, the prepare→build→train→**deploy** feature walk at
`cases/aws/ch13.md:301-315`), with limits from `research-2026.md` §2.5:

| Type | Choose when | Cost model | Key limits |
|---|---|---|---|
| **Real-time** | interactive, steady traffic, low latency | per instance-hour (persistent) | 60 s / 6 MB request; **scale-to-zero only via inference components** |
| **Serverless** | spiky / intermittent, can tolerate cold start | pay-per-request, **no idle charge** | 1–6 GB mem, ~6 MB, ~60 s |
| **Asynchronous** | large payloads or long inference, near-real-time OK | per instance-hour, **scales to zero** | payload **≤ 1 GB**, up to 1 h; S3 in/out |
| **Batch transform** | score a whole dataset offline, no live endpoint | job duration only | no endpoint; results written to S3 |

Selection heuristic: **latency-critical + steady → real-time**; **bursty / unknown
load → serverless** (accept cold starts to kill idle cost); **big inputs or slow
models → async** (the ≤ 1 GB payload ceiling is the deciding constraint versus
real-time's 6 MB); **no live traffic at all → batch transform** (cheapest; no
endpoint to pay for or forget). The **real-time per-instance-hour bill is the
classic cost trap** — an idle real-time endpoint bills 24/7.

```python
# V2 deploy surfaces (one call, four shapes):
model.deploy(instance_type="ml.m5.large", initial_instance_count=1)          # real-time
model.deploy(serverless_inference_config=ServerlessInferenceConfig())        # serverless
model.deploy(async_inference_config=AsyncInferenceConfig(output_path="s3://.../out/"))  # async
model.deploy(endpoint_type=EndpointType.INFERENCE_COMPONENT_BASED)           # IC-based (enables scale-to-zero)
# runtime (sagemaker-runtime):
#   invoke_endpoint(EndpointName, Body, ContentType, InferenceComponentName=)
#   invoke_endpoint_with_response_stream(...)   invoke_endpoint_async(InputLocation=<s3>)
```

**Inference components** let you host **multiple models on one endpoint**, each
independently scalable — and they are the prerequisite for **scale-to-zero** (GA
2025): only an inference-component-based endpoint can set
`ManagedInstanceScaling.MinInstanceCount=0` and drop to no running instances between
requests. If a workload is bursty but you want single-digit-ms warm latency when it
is active, IC-based real-time with scale-to-zero is the middle ground between
serverless and always-on. In V3, `ModelBuilder` (`sagemaker.serve`) is the
recommended (and only) packaging-and-deploy path.

**Offline (`{{test_stack}}`):** SageMaker is *more* offline-testable than
`bedrock-runtime` — `moto` mocks both the **control plane** (`create_model`,
`create_endpoint_config`, `create_endpoint`) **and** `sagemaker-runtime.invoke_endpoint`,
so end-to-end serve-and-call logic runs with no AWS. Contrast Bedrock, where
`bedrock-runtime` is Stubber-only. Use Stubber for `invoke_endpoint` contract/error
cases (throttling, model-not-ready), moto for the assembly.

## 6. JumpStart

JumpStart is the **shortcut**: pretrained and foundation models you deploy (or
fine-tune) without authoring a training script or container.

```python
from sagemaker.jumpstart.model import JumpStartModel
predictor = JumpStartModel(model_id="...", instance_type="ml.g5.2xlarge").deploy(accept_eula=True)
# fine-tune instead: from sagemaker.jumpstart.estimator import JumpStartEstimator
```

`accept_eula=True` is mandatory for gated models. Use JumpStart when you need a
known open model on a **SageMaker endpoint you control** (cost/latency/VPC), rather
than per-token via Bedrock.

This is the **Bedrock-vs-SageMaker fork** that **aws-ai-assess** owns, and the
corpus states it directly (`cases/aws-ai/ch01.md:126-148`, Table 1.1): **Bedrock**
= rapid generative-AI development, managed serverless-style FM access, unified API,
multiple providers; **SageMaker AI** = advanced customization, training/fine-tuning,
deep control over hosting, tuning, and deployment architecture. They compose rather
than compete — a model fine-tuned/customized in SageMaker can be the reasoning
"brain" of a Bedrock agent via **Custom Model Import** (`cases/aws-ai/ch01.md:124`).
The progressive path to present as a spectrum (not a verdict): **Bedrock →
SageMaker serverless customization → full training / HyperPod**, escalating control
and cost as requirements demand.

## 7. Corpus reality

**The only runnable SageMaker code in either seed bundle is
`cases/aws-ai/ch10.md:306-419`** — a SageMaker Studio notebook that pulls sales
data through the `redshift-data` API and calls Bedrock. Treat it as *proof the
family must write its own SageMaker code*, not as a model to copy, for two reasons:
- It is **Studio-notebook + console-driven**, not the programmatic
  train→pipeline→endpoint→registry lifecycle this reference describes. None of
  `ModelTrainer`/`Estimator`, `sagemaker.workflow.*`, the registry, or endpoint
  deploy appears anywhere in the corpus.
- Its Bedrock call is **legacy Titan** — `amazon.titan-tg1-large` with the
  `inputText`/`parameters` request and `results[0].outputText` response shape
  (`cases/aws-ai/ch10.md:399-417`) — superseded by Converse (see `bedrock.md`).
  Cite ch10 for the redshift-data → model pattern only; do not carry its invoke
  shape forward.

The system-design bundle contributes **taxonomy, not code**: `cases/aws/ch13.md`
gives the four deploy modes (§5) and the SageMaker feature map (Data Wrangler,
Studio, Clarify, Pipelines, A/B testing) but contains **zero runnable AWS code**,
and never mentions Bedrock or foundation models. So everything in §§2–5 above is
**fresh, executed code the family supplies** in `{{primary_language}}` and verifies
in `{{validate_home}}` — the corpus is the decision frame, the family is the
implementation.

## 8. HyperPod — pointer only

**HyperPod** (resilient/elastic large-scale distributed training — checkpointless
recovery, task governance, KV caching) is **out of CORE scope**: it targets
multi-node foundation-model training, is not exercisable in the offline
Stubber/moto harness, and is not represented in the corpus. When a workload
genuinely needs it, escalate to the research picture rather than inlining specifics
here — see `research-2026.md` §2 (Amazon SageMaker AI), which defers to
`{{research_home}}` for the current HyperPod, serverless-MLflow, and serverless
model-customization (SFT/DPO/RLVR/RLAIF) surface. Re-verify at authoring time; this
area moves monthly.
