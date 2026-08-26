# Reference — Amazon Bedrock (Converse, tool use, RAG, guardrails, embeddings)

> Cited by **aws-ai-assess / design / build / validate**. Corpus:
> `{{methodology_source}}` (modern lineage ch01–07; legacy ch08–10 is flagged and
> corrected, never copied). External depth and confidence labels live in
> `{{research_home}}/aws-ai-bedrock-sagemaker-research.md` §1 — re-verify anything
> version-specific there before treating it as constant. Region in examples:
> `{{region_default}}`. Every runtime snippet here is contract-testable **offline**
> with `botocore` Stubber; `moto` cannot mock `bedrock-runtime`, so Stubber is the
> only pure-unit path for §§2–4 and §6 apply (see `{{test_stack}}`).

Why this file exists: the seed corpus reaches Bedrock either through raw
`invoke_model` (legacy, `cases/aws-ai/ch09.md:686-712` — with a real completion-format
bug) or hidden behind framework abstractions (Strands `BedrockModel`; LangChain
`init_chat_model(model_provider="bedrock_converse")`, `cases/aws-ai/ch03.md:655`). The
native `bedrock-runtime.converse()` call — the default the family builds on — never
appears directly. This reference supplies it, correctly, and marks every fast-moving
fact so the stages don't hard-code drift.

## Contents
1. [The six clients — control vs runtime](#1-the-six-clients)
2. [Converse — call shape, response parsing, streaming](#2-converse)
3. [The tool-use loop (and why the legacy completion format is wrong)](#3-the-tool-use-loop)
4. [invoke_model — when Converse is not enough](#4-invoke_model)
5. [Knowledge Bases / RAG — retrieve & retrieve_and_generate](#5-knowledge-bases--rag)
6. [Guardrails — apply_guardrail, Converse-native, contextual grounding](#6-guardrails)
7. [Embeddings — Titan v2, Cohere v3/v4, choosing dims](#7-embeddings)
8. [Inference profiles & model-ID resolution — do not hard-code](#8-inference-profiles--model-id-resolution)

---

## 1. The six clients

Bedrock splits **control plane** (manage resources) from **runtime/data plane**
(invoke them) *strictly*, and each half is split again by feature. Reaching for the
wrong client is the #1 beginner error — `converse` does not exist on `bedrock`, and
`list_foundation_models` does not exist on `bedrock-runtime`. Pick by the verb you
need, not by the word "Bedrock".

| `boto3.client(...)` | Plane | You use it for |
|---|---|---|
| `bedrock` | control | `list_foundation_models`, model-access, guardrail **authoring** (`create_guardrail`, `create_guardrail_version`), inference-profile CRUD (`list_inference_profiles`), fine-tuning/customization, batch (`create_model_invocation_job`), eval jobs |
| `bedrock-runtime` | runtime | `converse`, `converse_stream`, `invoke_model`, `invoke_model_with_response_stream`, standalone **`apply_guardrail`**, `start_async_invoke` |
| `bedrock-agent` | control | classic Agents (`create_agent`, `prepare_agent`), **Knowledge Base authoring** (`create_knowledge_base`, `create_data_source`, `start_ingestion_job`), Flows, Prompt Management |
| `bedrock-agent-runtime` | runtime | `invoke_agent`, **KB retrieval** (`retrieve`, `retrieve_and_generate`, `retrieve_and_generate_stream`), `rerank`, agent sessions |
| `bedrock-agentcore-control` | control | AgentCore CRUD (`create_agent_runtime`, `create_memory`, `create_gateway`, …) — GA 2025-10 [re-verify] |
| `bedrock-agentcore` | data | `invoke_agent_runtime`, Memory events, code-interpreter/browser sessions |

Everything in this file lives on `bedrock` (authoring) and `bedrock-runtime`
(inference), except RAG retrieval (§5), which is on `bedrock-agent` /
`bedrock-agent-runtime`. AgentCore depth is in `references/agents.md`, not here.

---

## 2. Converse

Use **Converse as the default** for text/chat/vision/tool-use, because it is
provider-agnostic: the request and response shapes stay identical whether `modelId`
points at Claude, Nova, Llama, Mistral, or Cohere, so swapping models is a one-line
change instead of a rewrite. `invoke_model` (§4) is the exception, not the rule.

The three things people get wrong: `system` is a **separate top-level parameter**,
not a message with `role: "system"`; every message's `content` is a **list of
typed blocks** (`{"text": ...}`), never a bare string; and the reply is nested at
`output.message.content` — you must index into it.

```python
import boto3

brt = boto3.client("bedrock-runtime", region_name="us-east-1")
MODEL = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"  # EXAMPLE id (older-gen, dated) — do NOT copy; resolve a CURRENT-gen id at runtime per §8

resp = brt.converse(
    modelId=MODEL,
    messages=[{"role": "user", "content": [{"text": "Summarize CQRS in one line."}]}],
    system=[{"text": "You are terse."}],            # top-level, NOT a message role
    inferenceConfig={"maxTokens": 512},             # current-gen Claude: maxTokens only — no temperature/topP/topK (§3)
)

msg = resp["output"]["message"]                     # {"role": "assistant", "content": [...]}
text = "".join(b["text"] for b in msg["content"] if "text" in b)
stop = resp["stopReason"]   # end_turn | tool_use | max_tokens | stop_sequence
                            #   | guardrail_intervened | content_filtered
usage = resp["usage"]       # {inputTokens, outputTokens, totalTokens}  -> cost/telemetry
```

Iterate `content` rather than assuming `content[0]["text"]`: a single reply can
interleave `text`, `toolUse`, and `reasoningContent` blocks, and reasoning/tool
blocks precede text. Block types (one key per block): `text`, `image`, `document`,
`video`, `toolUse`, `toolResult`, `guardContent`, `cachePoint`, `reasoningContent`.
`cachePoint` (prompt caching), `performanceConfig`, and structured-output
`outputConfig` are newer add-ons [2025–2026; re-verify in research §1.2].

**Streaming** (`converse_stream`) trades one blocking call for an event iterator —
use it for perceived latency on long generations. Concatenate deltas yourself:

```python
stream = brt.converse_stream(modelId=MODEL, messages=messages)["stream"]
for event in stream:
    if "contentBlockDelta" in event:
        delta = event["contentBlockDelta"]["delta"]
        if "text" in delta:
            print(delta["text"], end="", flush=True)
    elif "messageStop" in event:
        stop = event["messageStop"]["stopReason"]
    elif "metadata" in event:
        usage = event["metadata"]["usage"]
# other events: messageStart, contentBlockStart, contentBlockStop
```

For tool use over the stream, the arguments arrive as **partial JSON string
fragments** in successive `contentBlockDelta.delta.toolUse.input` events — buffer
them per content block and `json.loads` once at `contentBlockStop`, or you will try
to parse half an object. Raise the client `read_timeout` to 300s+ for streaming
(default 60s can cut long generations) — see `references/boto3-foundations.md`.

---

## 3. The tool-use loop

Function calling in Converse is a **round-trip you drive**, not a callback. You send
a `toolConfig`; if the model wants a tool it stops with `stopReason == "tool_use"`
and its turn carries one or more `toolUse` blocks; you run the tool and send the
answer back as a `toolResult` block that **echoes the same `toolUseId`**; you repeat
until `stopReason == "end_turn"`. The echo is how the model matches a result to the
call it made — mismatched or missing IDs are a `ValidationException`. Always
**bound the loop** with a max-turn count so a stuck or misbehaving model cannot
spin forever (and burn tokens) — see `MAX_TURNS` below.

```python
tool_config = {
    "tools": [{"toolSpec": {
        "name": "get_weather",
        "description": "Current weather for a city.",
        "inputSchema": {"json": {                     # JSON Schema wrapped under literal "json"
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"]}}}}],
    "toolChoice": {"auto": {}},                        # or {"any": {}} | {"tool": {"name": ...}}
}

messages = [{"role": "user", "content": [{"text": "Weather in Paris?"}]}]

MAX_TURNS = 10                                          # bound the loop — a stuck/looping model must not spin forever
for _turn in range(MAX_TURNS):
    # MODEL is an example id to RE-VERIFY (list_foundation_models / inference profiles),
    # never a constant: most current models are inference-profile-only, so a bare id
    # throws ValidationException, and the us./eu./global. prefix is part of the id.
    resp = brt.converse(modelId=MODEL, messages=messages, toolConfig=tool_config)
    assistant = resp["output"]["message"]
    messages.append(assistant)                          # (1) echo the assistant turn back VERBATIM
    if resp["stopReason"] != "tool_use":
        break

    tool_results = []
    for block in assistant["content"]:                  # (2) a turn may hold MANY toolUse blocks
        if "toolUse" not in block:
            continue
        call = block["toolUse"]                          #   call["input"] is already a dict — no json.loads
        result = run_tool(call["name"], call["input"])   #   your dispatch
        tool_results.append({"toolResult": {
            "toolUseId": call["toolUseId"],              # (3) echo the id; one result per call
            "content": [{"json": result}],               #   content is a LIST of blocks; {"json":...} | {"text":...}
            "status": "success"}})                        #   "error" lets the model self-correct

    messages.append({"role": "user", "content": tool_results})  # results ride a USER turn
else:
    raise RuntimeError(f"tool-use loop did not converge within {MAX_TURNS} turns")

final_text = "".join(b["text"] for b in assistant["content"] if "text" in b)
```

Ordering is load-bearing: append the assistant's `toolUse` turn **before** the user
`toolResult` turn, keep `toolUseId`s paired one-to-one, and make `toolResult.content`
a list of blocks — a bare string is rejected. On a tool exception, send
`status: "error"` with the message in a `text` block instead of crashing the loop;
the model will typically apologize or retry.

**Why not the legacy path.** `cases/aws-ai/ch09.md:686-712` invokes a
`claude-sonnet-4` id through `invoke_model` with the deprecated text-completions
contract — `format_claude_prompt` wraps the prompt in `"\n\nHuman: … \n\nAssistant:"`,
the body uses `max_tokens_to_sample`, and it reads `response["completion"]`. Against a
current model on `bedrock-runtime` that is a genuine bug: today's messages/Converse
API expects `max_tokens` (`maxTokens` in Converse), structured message roles, and
returns `output.message.content`, with `"\n\nHuman:"` no longer a required framing.
Never reproduce that shape — it is the corpus's clearest legacy trap.

**Sampling params are removed on current-generation Claude models (VERIFIED against the authoritative Claude API reference, 2026-08).** On Bedrock Converse, do NOT set `inferenceConfig.temperature`, `topP`, or `topK` for a current-generation Claude model: Opus 4.7+/Opus 5 and Fable 5 REMOVE them (sending any returns a 400), and Sonnet 5 rejects a non-default value with a 400. Omit `inferenceConfig` entirely, or pass only `maxTokens`. They remain valid on older Claude models (Sonnet 4.5 / Opus 4.5 and earlier), so the guard is model-generation-specific — when the resolved model id is a current-gen Claude, drop the sampling params. Treat this as a deprecated-parameter trap symmetric with the legacy `\n\nHuman:` / `max_tokens_to_sample` completion format: both silently break against current Claude models, and the skill should warn against both the same way.

---

## 4. invoke_model

`invoke_model` is the lower-level, **model-specific** call: you hand-build the JSON
body for one provider and parse its bespoke response. Reach for it only where
Converse genuinely cannot go:

- **Embeddings** (§7) — Titan and Cohere embed models have no Converse surface.
- **Image / video generation** — e.g. Titan Image Generator returns base64 images in
  a provider-specific body, not `output.message`.
- **Model-specific knobs** Converse does not expose — though most now belong under
  Converse's `additionalModelRequestFields`, which is preferable to dropping to
  `invoke_model` because you keep the portable envelope.

```python
import json
resp = brt.invoke_model(modelId=EMBED_MODEL, body=json.dumps({"inputText": "hello"}))
payload = json.loads(resp["body"].read())    # body is a StreamingBody -> .read() then json.loads
```

If you find yourself building `"\n\nHuman:"` prompts or reading
`response["completion"]`, stop — that is the §3 legacy contract, not modern
`invoke_model` usage. For anything conversational, use Converse.

---

## 5. Knowledge Bases / RAG

Managed RAG on Bedrock is two runtime calls on `bedrock-agent-runtime` (authoring —
`create_knowledge_base`/`create_data_source`/`start_ingestion_job` — is on
`bedrock-agent`; see §1 and `references/research-2026.md`). Choose by who owns
generation:

- **`retrieve`** — returns ranked chunks only. Use it when *your* Converse call
  (§2) does the generation, so you keep full control of the prompt, tools, and model.
- **`retrieve_and_generate`** — one managed call that retrieves *and* writes the
  answer with citations. Use it for a fast, batteries-included RAG endpoint.

```python
rt = boto3.client("bedrock-agent-runtime", region_name="us-east-1")

# Retrieve-only: feed chunks into your own Converse prompt.
hits = rt.retrieve(
    knowledgeBaseId=KB_ID,
    retrievalQuery={"text": q},
    retrievalConfiguration={"vectorSearchConfiguration": {
        "numberOfResults": 5, "overrideSearchType": "HYBRID"}},  # HYBRID = vector + keyword
)
chunks = [r["content"]["text"] for r in hits["retrievalResults"]]

# Managed generate-with-citations.
out = rt.retrieve_and_generate(
    input={"text": q},
    retrieveAndGenerateConfiguration={
        "type": "KNOWLEDGE_BASE",                 # or EXTERNAL_SOURCES (inline docs, no KB)
        "knowledgeBaseConfiguration": {
            "knowledgeBaseId": KB_ID,
            "modelArn": MODEL_ARN,                # a model *ARN*, not a bare id (see §8)
            "generationConfiguration": {          # optional guardrail on the generated answer
                "guardrailConfiguration": {"guardrailId": GID, "guardrailVersion": "1"}}}},
)
answer = out["output"]["text"]
# pass out["sessionId"] back on the next call for multi-turn RAG
```

**Citation parsing** — always surface sources; an un-cited RAG answer is
indistinguishable from a hallucination. The shape (verified against
`cases/aws-ai/ch09.md:656-683`) is `citations[] -> retrievedReferences[] ->
content.text` (plus `location` for the source URI):

```python
for citation in out.get("citations", []):
    for ref in citation.get("retrievedReferences", []):
        text = ref.get("content", {}).get("text", "")
        src = ref.get("location", {})                 # e.g. {"type":"S3","s3Location":{"uri":...}}
```

Corpus note: ch09 pairs a *correct* `retrieve_and_generate` + citation-extraction
loop with the *broken* completion-format generator from §3 in the same file — cite
the RAG shape, not the generator. Vector-store and chunking choices
(`S3_VECTORS`, OpenSearch Serverless, Aurora pgvector; `FIXED_SIZE`/`SEMANTIC`/
`HIERARCHICAL`) are design-stage concerns in `references/research-2026.md` §1.6.
`retrieve_and_generate_stream` exists for token streaming; AgentCore's June-2026
Managed Knowledge Base is a separate, newer offering [re-verify].

---

## 6. Guardrails

A guardrail is a **content filter that runs beside the model**, screening input
and/or output for denied topics, harmful-content categories, PII, and
hallucination. It is not a policy engine: it inspects *text*, so it cannot see or
stop a tool call the agent decides to make ("guardrails filter text… they don't
intercept tool calls," `cases/aws-ai/ch07.md:755-758`). Tool-level authorization
belongs to AgentCore Policy / Cedar (`references/agents.md`); pair the two.

Authoring is on `bedrock` (`create_guardrail` → DRAFT, `create_guardrail_version`
publishes an immutable version). There are then **two ways to enforce** one at
runtime — pick by whether Bedrock is generating the text:

**(a) Converse-native `guardrailConfig`** — Bedrock applies the guardrail to the
model's own I/O in the same call. This is the default for anything you generate:

```python
resp = brt.converse(
    modelId=MODEL,
    messages=messages,
    guardrailConfig={"guardrailIdentifier": GID, "guardrailVersion": "1",
                     "trace": "enabled"},        # trace tells you WHICH rule fired
)
# stopReason == "guardrail_intervened" when the guardrail blocked/altered the turn
```

Strands wires the same thing through the model object —
`BedrockModel(model_id=…, guardrail_id=…, guardrail_version="1",
guardrail_trace="enabled")`, evaluating both the user input and the model output
(`cases/aws-ai/ch07.md:764-781`).

**(b) Standalone `apply_guardrail`** (on `bedrock-runtime`) — screen text Bedrock
did *not* generate: user input before it reaches any model, or output from a
non-Bedrock model, or an agent's final answer. This is the only way to guard a
system whose generation is elsewhere:

```python
r = brt.apply_guardrail(
    guardrailIdentifier=GID, guardrailVersion="1",
    source="INPUT",                                  # INPUT | OUTPUT
    content=[{"text": {"text": user_text, "qualifiers": ["query"]}}],
    outputScope="FULL",
)
# r["action"] in {NONE, GUARDRAIL_INTERVENED} — there is no separate ANONYMIZED action;
# PII anonymization returns the masked text in r["outputs"], with r["assessments"] holding per-policy detail
```

Content filters cover `HATE | INSULTS | SEXUAL | VIOLENCE | MISCONDUCT |
PROMPT_ATTACK` at `NONE|LOW|MEDIUM|HIGH`; plus denied topics (`DENY`), word filters,
and PII (`piiEntitiesConfig`, action `BLOCK|ANONYMIZE`). Legacy authoring in
`cases/aws-ai/ch08.md:637-644` uses `botocore.session.Session().create_client('bedrock')` —
the API calls are still valid but prefer a plain `boto3.client("bedrock")`.

**Contextual grounding** is the anti-hallucination check specifically for RAG: it
scores the answer for **grounding** (is it supported by the source?) and
**relevance** (does it answer the query?) against thresholds, e.g. 0.70, and
flags/blocks below them (`cases/aws-ai/ch08.md:541-542`). You tell the guardrail
which text is the source vs the question two ways:

- **Tag-based**, inside an `invoke_model` body — wrap the source in
  `<amazon-bedrock-guardrails-groundingSource_xyz>…</…>` and the question in
  `<amazon-bedrock-guardrails-query_xyz>…</…>`, with a matching
  `"amazon-bedrock-guardrailConfig": {"tagSuffix": "xyz"}`
  (`cases/aws-ai/ch08.md:544-556`).
- **Block-based**, the modern Converse form — pass `guardContent` blocks with
  `qualifiers` marking each piece: `["grounding_source"]`, `["query"]`, and the
  answer block unqualified as the text to evaluate (`cases/aws-ai/ch08.md:558-600`).

```python
messages = [{"role": "user", "content": [
    {"guardContent": {"text": {"text": retrieved_context, "qualifiers": ["grounding_source"]}}},
    {"guardContent": {"text": {"text": user_question,    "qualifiers": ["query"]}}},
]}]
# with guardrailConfig set, Bedrock scores the generated answer against source + query
```

Guardrails bill per ~1000-character text unit per policy — factor it into cost.

---

## 7. Embeddings

Embeddings turn text into vectors for retrieval; they are `invoke_model`-only (no
Converse, no streaming). The one decision that matters is **dimensions**: smaller
vectors cost less to store and search and are faster, at some recall cost — pick the
smallest dimension that holds your retrieval quality, and keep it **consistent
between indexing and querying** (mismatched dims or models make similarity
meaningless).

- **Titan Text Embeddings V2** — `amazon.titan-embed-text-v2:0`, dims **256 / 512 /
  1024** (1024 default). In-region only (no cross-region inference profile).

```python
body = {"inputText": "vector databases on AWS", "dimensions": 512, "normalize": True}
resp = brt.invoke_model(modelId="amazon.titan-embed-text-v2:0", body=json.dumps(body))
vec = json.loads(resp["body"].read())["embedding"]
```

- **Cohere Embed** — `cohere.embed-english-v3` / `-multilingual-v3` (1024); v4
  `cohere.embed-v4:0` is multimodal with dims 256–1536 [Oct 2025; re-verify]. Cohere
  **requires `input_type`** and it is a correctness knob, not a formality: index
  documents with `"search_document"` and embed the user's query with
  `"search_query"`. Mismatching them silently degrades retrieval.

```python
body = {"texts": ["…"], "input_type": "search_document", "embedding_types": ["float"]}
```

Rule of thumb: default to Titan v2 at 512 or 1024 for English; use Cohere for
multilingual or when you have measured it wins on your corpus. Whatever you choose,
record the model id **and** dimension next to the index — re-embedding to change
either means rebuilding it.

---

## 8. Inference profiles & model-ID resolution

**Do not hard-code model IDs as if permanent.** Bedrock ids drift constantly — the
corpus alone spans Sonnet 4, Sonnet 4.5, and Haiku 4.5 across four chapters — and
many current models are **inference-profile-only**: passing a bare foundation-model
id returns `ValidationException` ("on-demand throughput isn't supported… use an
inference profile"). Every literal id in this file is an *example to re-verify*, not
a constant.

A **cross-region inference profile** is an id that routes a request across a set of
regions for ~2× throughput and better availability. You invoke the *profile* id, not
the model id, and it carries a geography prefix: `us.`, `eu.`, `apac.`, or the newer
`global.` (e.g. `us.anthropic.claude-sonnet-4-5-…`, `global.anthropic.claude-haiku-4-5-…`).
IAM consequence: the execution role must allow **both** the `foundation-model/*`
resource ARN **and** the `inference-profile/*` ARN — allowing only one yields
`AccessDenied`. A profile that spans regions needs `foundation-model/*` permitted in
*every* region it touches (see `references/boto3-foundations.md` for the policy).

Resolve at runtime instead of guessing:

```python
bedrock = boto3.client("bedrock", region_name="us-east-1")

# What foundation models can I actually call here, and how?
for m in bedrock.list_foundation_models(byOutputModality="TEXT")["modelSummaries"]:
    modes = m.get("inferenceTypesSupported", [])   # ["ON_DEMAND"] and/or ["INFERENCE_PROFILE"]
    # m["modelId"], m["modelLifecycle"]["status"] (ACTIVE | LEGACY)

# Which cross-region profile ids exist? Invoke THESE, not bare ids.
for p in bedrock.list_inference_profiles()["inferenceProfileSummaries"]:
    pid = p["inferenceProfileId"]                  # e.g. "us.anthropic.claude-sonnet-4-5-…"
```

Practical recipe for the build stage: resolve the id once at startup (or read it
from config/env), prefer an inference-profile id, assert it is `ACTIVE`, and fail
loudly with a resolved-alternatives list rather than 500-ing on a `ValidationException`
mid-request. Also handle `AccessDeniedException` (model access not granted — fix
access, not retryable) distinctly from `ThrottlingException` (429 — retryable with
adaptive backoff). For the current picture of profile prefixes, on-demand-vs-profile
support, and exception semantics, defer to
`{{research_home}}/aws-ai-bedrock-sagemaker-research.md` §1.2 / §1.9 and re-research —
these move monthly.
