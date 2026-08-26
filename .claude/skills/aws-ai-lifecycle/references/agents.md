# Agent frameworks — Strands, multi-agent, MCP/A2A, Bedrock AgentCore

Shared depth for the `aws-ai-*` family's agent work. The stage skills
(`aws-ai-design` for topology, `aws-ai-build` for code, `aws-ai-deploy` for the
runtime, `aws-ai-validate` for the offline harness) cite this file rather than
re-deriving the APIs. It is the corpus's richest, most code-rich area — most of
what follows is lifted and line-cited from `cases/aws-ai` ch01–07, the **modern
Strands + AgentCore lineage**.

Two things frame everything below:

- **Two lineages, one bundle.** `cases/aws-ai` ch01–07 is the modern spine
  (Strands SDK + Bedrock AgentCore, Claude Sonnet 4 / Haiku 4.5). ch08–10 is a
  grafted **legacy** book (classic *Agents for Amazon Bedrock*, raw `botocore`,
  console click-through). Treat them as different generations — §6 shows the
  legacy `create_agent` path so you recognize it, not so you copy it.
- **Fast-moving facts live in research, not here.** Model IDs, AgentCore CLI
  verbs, and AgentCore service GA dates drift monthly. This file gives the stable
  shapes; defer version-specific specifics to the external research doc
  (`{{research_home}}/aws-ai-bedrock-sagemaker-research.md`, §3 *Agent frameworks +
  CDK-Python deployment*) and re-verify before treating any id or verb as constant.

## Contents

1. [Strands — the authoring layer](#1-strands--the-authoring-layer)
2. [Multi-agent orchestration](#2-multi-agent-orchestration)
3. [Agent communication — MCP and A2A](#3-agent-communication--mcp-and-a2a)
4. [Bedrock AgentCore — the runtime & ops layer](#4-bedrock-agentcore--the-runtime--ops-layer)
5. [The two conflicting `agentcore` CLIs](#5-the-two-conflicting-agentcore-clis)
6. [Classic *Agents for Amazon Bedrock* — the legacy path](#6-classic-agents-for-amazon-bedrock--the-legacy-path)

---

## 1. Strands — the authoring layer

Strands is where you *write* agent logic; AgentCore (§4) is where you *run* it.
The two are orthogonal choices — a Strands agent deploys to Lambda, ECS, or
AgentCore Runtime unchanged. Strands drives a **model-in-the-loop** cycle: the LLM
decides each step, picks tools, and stops when it has an answer. You do not
hand-roll the Bedrock Converse tool-use loop (`toolConfig` → `stopReason:
"tool_use"` → echo `toolResult` → repeat); Strands hides it. When you need the raw
loop — no framework — see the research doc §1.3 and the sibling `bedrock.md`.

### 1.1 The `@tool` decorator contract — the atomic building block

A Python function becomes an agent tool with three things and nothing more: the
`@tool` decorator, type hints, and a docstring. The decorator registers it; the
type hints tell the model the argument types; the docstring is what the model
reads to decide *when* to call it. This recurs in every modern chapter — standardize
on it (`cases/aws-ai/ch02.md:89-104`):

```python
from strands import Agent, tool

@tool
def check_server_status(server_url: str) -> str:
    """Check if a server is responding by making an HTTP request.
    Args:
        server_url: The URL of the server to check
    Returns:
        A message indicating whether the server is up or down
    """
    ...

agent = Agent(tools=[check_server_status])
```

The docstring is not decoration — it is the tool's selection prompt. A vague
docstring means the model calls the tool at the wrong time. Build **focused,
single-purpose tools** and give the agent several rather than one mega-tool: the
model composes them itself, in an order you never program
(`cases/aws-ai/ch02.md:126-140`). For strict input validation beyond type hints,
Strands supports an explicit `TOOL_SPEC` schema — advanced, rarely needed.

### 1.2 `Agent` and `BedrockModel` — the model provider

Zero-config `Agent()` defaults to Amazon Bedrock with a current Claude model, so
the smallest possible agent is three lines (`cases/aws-ai/ch01.md:433-438`; the
default provider is confirmed at `cases/aws-ai/ch05.md:794`). To pin the model or
switch providers, pass a model object or an inference-profile id string:

```python
from strands import Agent
from strands.models.bedrock import BedrockModel

model = BedrockModel(model_id="us.anthropic.claude-sonnet-4-20250514-v1:0")  # example id — re-verify
agent = Agent(model=model, system_prompt="You are concise.")
```

(`cases/aws-ai/ch07.md:514-521`; the bare-string form `Agent(model="us.anthropic…")`
appears at `cases/aws-ai/ch04.md:388`.) `strands.models` also carries Anthropic,
OpenAI, Gemini, LiteLLM, Ollama, and Mistral providers, so the same agent code
targets non-Bedrock models.

**Model-ID drift is real and in-corpus.** ch02/ch05 use Sonnet 4, ch03 uses Haiku
4.5, ch04 uses Sonnet 4.5 — three chapters, three ids. Do not hard-code an id as
if permanent. Resolve the current one at runtime via
`bedrock.list_foundation_models` / `list_inference_profiles`, and note the
`us.`/`eu.`/`apac.`/`global.` inference-profile prefixes (many newer models are
profile-only — a bare id raises `ValidationException`). Every `model_id` in this
file is an example to re-verify.

### 1.3 Prebuilt tools — `strands_tools`

The `strands-agents-tools` package ships dozens of ready tools, so common
capabilities need no code. Import and hand them to the agent
(`cases/aws-ai/ch02.md:274-283`, `cases/aws-ai/ch02.md:363-374`):

```python
from strands_tools import use_aws, calculator, http_request, file_write
agent = Agent(tools=[http_request, calculator, file_write])
```

- **`use_aws`** — the AWS bridge. It translates natural-language requests into AWS
  CLI/API calls under your configured credentials, so one tool reaches S3,
  DynamoDB, Lambda, and more without hand-written boto3
  (`cases/aws-ai/ch02.md:384-416`). Powerful and correspondingly broad: it inherits
  whatever the caller's IAM allows, so scope the execution role tightly and treat
  it as a design-time trust decision (a natural `aws-ai-design` guardrail/IAM-boundary
  item), not a default grant.
- **`calculator`** — precise arithmetic the model would otherwise fumble
  (`cases/aws-ai/ch02.md:274-283`).
- **`http_request`** — outbound HTTP; pairs with `calculator`/`file_write` for
  fetch-compute-save workflows the agent sequences on its own
  (`cases/aws-ai/ch02.md:363-374`).

### 1.4 Class-based and async tools — resource and latency escape hatches

Start with the decorator; reach for these only when a real problem shows up
(`cases/aws-ai/ch02.md:579-583`).

**Class-based tools** share state (a DB connection, an API client with a pool)
across several tools instead of opening and closing a connection per call. Group
related `@tool` methods in a class, construct once, pass the bound methods
(`cases/aws-ai/ch02.md:516-532`):

```python
class InventoryTools:
    def __init__(self):
        self.db = connect_to_database()   # one connection, reused
    @tool
    def check_stock(self, product_id: str) -> str:
        """Check product stock."""
        ...

inventory = InventoryTools()
agent = Agent(tools=[inventory.check_stock, inventory.update_stock])
```

**Async tools** let independent I/O run concurrently. Mark the tool `async` and
Strands runs parallel calls together; drive the agent with `invoke_async`
(`cases/aws-ai/ch02.md:556-572`):

```python
@tool
async def check_warehouse_inventory(product_id: str, warehouse: str) -> int:
    """Check inventory at a specific warehouse."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://api.warehouse-{warehouse}.com/inventory/{product_id}")
        return r.json()["quantity"]

response = await agent.invoke_async("Check all warehouses for PROD-123.")
```

Async earns its complexity only for real external I/O; a sub-100 ms or
pure-compute tool gains nothing.

---

## 2. Multi-agent orchestration

All four patterns live in `strands.multiagent` (Swarm, Graph) or fall out of §1's
tool mechanism (agent-as-tool). Choose by **who decides the path**. Read §2.5
before reaching for any of them — the corpus is emphatic that most problems do not
need multiple agents.

### 2.1 Supervisor–worker — centralized coordination

One supervisor agent delegates to specialist workers and synthesizes their
answers. The mechanism is `Agent.as_tool()`: wrap each worker as a tool the
supervisor can call (`cases/aws-ai/ch04.md:100-140`):

```python
supervisor = Agent(
    name="research_supervisor",
    system_prompt="Delegate to specialists, then synthesize a recommendation.",
    tools=[news_agent.as_tool(), financial_agent.as_tool(), sentiment_agent.as_tool()],
)
```

Failures stay isolated (a bad number → check `financial_agent`), and adding a
capability means adding a worker, not editing existing ones. The cost: the
supervisor is a bottleneck and a single point of failure, and workers cannot talk
to each other directly — everything routes through the center. It is the most
common production pattern precisely because that simplicity is usually what you
want (`cases/aws-ai/ch04.md:160-168`).

### 2.2 Agent-as-tool — reuse across systems

A generalization of §2.1: build a specialist once, give it a `description`, and
any orchestrator can discover and call it like any other tool. The teacher agent
below never solves problems itself; it routes to the tutor whose description
matches (`cases/aws-ai/ch04.md:185-214`). Trade-off: agents communicate only
through the orchestrator, and nested agent calls add latency
(`cases/aws-ai/ch04.md:580-586`).

### 2.3 Swarm — autonomous handoffs

When you cannot predict the path — specialists collaborate and each decides who
goes next — use `Swarm`. Every member automatically gets a `handoff_to_agent` tool
and they share one context (`cases/aws-ai/ch04.md:384-434`):

```python
from strands.multiagent import Swarm
swarm = Swarm(
    [level_designer, game_designer, narrative_designer, difficulty_balancer],
    entry_point=level_designer,
    max_handoffs=20, max_iterations=20,
    repetitive_handoff_detection_window=8,
    repetitive_handoff_min_unique_agents=3,
)
result = swarm("Design a stealth mission level ...")
```

The limits are load-bearing, not boilerplate: without `max_handoffs`/
`max_iterations` agents loop forever, and the `repetitive_handoff_*` window breaks
the classic **ping-pong** failure where two agents bounce a task back and forth
without progress (`cases/aws-ai/ch04.md:435-441`). The upside — no fixed sequence —
is also the downside: execution order varies between runs, so it is harder to
debug.

### 2.4 Graph (DAG) — deterministic, auditable flow

When the path *must* be fixed and provable — compliance, approval chains, content
moderation — use `GraphBuilder`. You define nodes and edges (with optional
conditions) in code; each node is still an LLM-backed agent, but the routing is
deterministic and inspectable (`cases/aws-ai/ch04.md:528-557`):

```python
from strands.multiagent import GraphBuilder
builder = GraphBuilder()
builder.add_node(risk_analyzer, "risk_analysis")
builder.add_node(fraud_detection_agent, "fraud_check")
builder.add_edge("risk_analysis", "fraud_check", condition=is_suspicious)
builder.add_edge("risk_analysis", "inventory_check", condition=is_low_risk)
builder.set_entry_point("risk_analysis")
graph = builder.build()
result = graph("Order #12345: $1,500 laptop from new customer")
```

"Directed acyclic" means arrows point one way and there are no loops, so every run
provably terminates and a given input always follows the same path — you can point
an auditor at the graph. The cost is that every possible path must be enumerated
up front (`cases/aws-ai/ch04.md:520-522`).

### 2.5 Choosing — and when NOT to go multi-agent

The corpus's own comparison (`cases/aws-ai/ch04.md:562-604`):

| Pattern | Who decides the path | Best for | Trade-off |
|---|---|---|---|
| Supervisor–worker | Supervisor agent | Centralized coordination, one synthesized answer | Supervisor is bottleneck + SPOF |
| Agent-as-tool | Orchestrator picks from tools | Reusable agents across systems | Communicate only via orchestrator; nested-call latency |
| Swarm | Agents decide autonomously | Collaborative work, unpredictable path | Harder to debug; order varies |
| Graph (DAG) | You, in code | Compliance, auditable pipelines | All paths defined upfront |

**Default to one agent with good tools.** The chapter is blunt: a single
well-equipped agent beats a poorly designed multi-agent system, and rebuilding a
working single agent as five coordinating ones typically triples latency,
multiplies failure points, and turns debugging into archaeology
(`cases/aws-ai/ch04.md:608-618`). Reach for multiple agents only when you hit a
genuine wall — context window truly overflowing, real need for parallelism, or
expertise that provably will not fit one prompt. In `aws-ai-design`, treat
"why not one agent?" as a required justification before any topology is drawn.

---

## 3. Agent communication — MCP and A2A

Two protocols, two jobs. **MCP** (Model Context Protocol) connects an agent to
*tools/data* — a client-server integration layer. **A2A** (Agent-to-Agent)
connects an agent to *other agents* as open-ended peers. They compose: an A2A
agent can itself use MCP tools.

### 3.1 MCP — tools and data over a standard protocol

**Consume a prebuilt server.** Launch it as a subprocess and hand its tools to a
Strands agent. Prebuilt AWS servers run via `uvx` with no local code
(`cases/aws-ai/ch05.md:367-381`):

```python
from mcp import stdio_client, StdioServerParameters
from strands.tools.mcp import MCPClient

mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="uvx", args=["awslabs.aws-documentation-mcp-server@latest"])))
```

**Author a server with FastMCP.** FastMCP is the MCP-native, low-boilerplate way
to expose three primitives — **tools** (actions), **resources** (read-only data,
REST-GET-like), and **prompts** (reusable templates) — over stdio transport
(`cases/aws-ai/ch05.md:433-478`):

```python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("WeatherServer")

@mcp.tool()
def get_weather(city: str) -> str:
    """Get the current weather for a given city."""
    ...

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Return a personalized greeting."""
    ...

@mcp.prompt()
def weather_report(city: str) -> str:
    """Generate a prompt asking for a weather report."""
    ...

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

Prefer FastMCP over FastAPI when the service exists *to be* an MCP server; FastAPI
is the better base only when MCP is one slice of a larger web app
(`cases/aws-ai/ch05.md:390-398`). A raw async client (`ClientSession` +
`stdio_client` from the MCP SDK) spawns the server and drives it directly when you
are not going through Strands (`cases/aws-ai/ch05.md:485-546`). On AWS, AgentCore
**Gateway** (§4.4) is the managed way to turn Lambdas/OpenAPI specs into MCP tools
without hosting a server yourself.

### 3.2 A2A — agents as first-class peers

A2A lets independent agents discover and call each other. The hinge is the **agent
card** — a JSON document at `/.well-known/agent-card.json` advertising the agent's
skills — which a caller fetches *first* to learn what the agent can do
(`cases/aws-ai/ch05.md:631`, card body at `cases/aws-ai/ch05.md:811`).

Two layers (`cases/aws-ai/ch05.md:727-738`):

- **`a2a-sdk`** — the low-level protocol library: data types (`Message`,
  `TextPart`, `AgentSkill`, `AgentCapabilities`) and client utilities
  (`A2ACardResolver`, `ClientFactory`, `ClientConfig`).
- **`strands-agents[a2a]`** — the framework integration: `A2AServer` exposes a
  Strands agent as an A2A server; `A2AAgent` consumes a remote one as if local.

Serve an agent (skills published into the card via `AgentSkill`,
`cases/aws-ai/ch05.md:774-808`):

```python
from a2a.types import AgentSkill
server = A2AServer(agent=weather_agent, host="127.0.0.1", port=9001,
                   skills=WEATHER_SKILLS, version="1.0.0",
                   enable_a2a_compliant_streaming=True)
server.serve()
```

Call it from an orchestrator — resolve the card, build a client, send a message,
extract text from the returned task's artifacts
(`cases/aws-ai/ch05.md:886-917`):

```python
resolver = A2ACardResolver(httpx_client=hc, base_url=base_url)
card = await resolver.get_agent_card()
client = ClientFactory(ClientConfig(httpx_client=hc, streaming=False)).create(card)
async for event in client.send_message(make_message(text)):
    ...
```

A2A systems run as separate processes/services (the corpus demo uses three
terminals — two agent servers plus an orchestrator,
`cases/aws-ai/ch05.md:928-939`), which is the natural seam where `aws-ai-deploy`
takes over.

---

## 4. Bedrock AgentCore — the runtime & ops layer

AgentCore is the framework-agnostic **production platform** for agents — it hosts
and operates *any* agent code (Strands, LangGraph, CrewAI, LlamaIndex, Google ADK,
OpenAI Agents SDK, Claude Agent SDK), unlike classic Bedrock Agents which only run
a managed Bedrock-model agent (§6). Its services are **composable**: adopt Runtime
alone, or Memory alone, or wire several together (`cases/aws-ai/ch06.md:197-211`).
Service GA dates and the newer additions (Policy, Evaluations, Managed Knowledge
Base, Payments) move fast — confirm status in the research doc §3 before you rely
on one.

### 4.1 Runtime — serverless, session-isolated hosting

Runtime gives each session its own microVM with no shared state, then sanitizes it
at session end — the isolation story that matters for regulated data
(`cases/aws-ai/ch06.md:228-231`). Turning local agent code into a Runtime service
changes only four lines: import `BedrockAgentCoreApp`, create the app, decorate the
entrypoint, call `app.run()`. The SDK then serves `/invocations` and `/ping` for
you (`cases/aws-ai/ch06.md:243-263`):

```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp
app = BedrockAgentCoreApp()

@app.entrypoint
async def handler(request):
    prompt = request.get("prompt")
    if not isinstance(prompt, str):     # guard: a toolUse block sneaked in as prompt bypasses guardrails
        raise ValueError("prompt must be a string")
    async for event in MyAgent().stream_async(prompt):
        yield event

app.run()
```

**ARM64/Graviton is required** for the container path — build accordingly or the
deploy fails (`cases/aws-ai/ch06.md:307`). Invoke in production with
`boto3.client("bedrock-agentcore").invoke_agent_runtime(...)`. Match the workload
to the host (`cases/aws-ai/ch06.md:513-526`): multi-turn, per-user sessions →
Runtime; a never-ending monitoring loop with no distinct sessions → ECS (Runtime's
per-session model does not fit, and Lambda's 15-min ceiling rules it out).

### 4.2 Starter-toolkit deploy

For SDK-driven deploys, the AgentCore Starter Toolkit's `Runtime` class handles the
full lifecycle — `configure` generates a Dockerfile, an IAM execution role, and an
ECR repo; `launch` builds the image, pushes to ECR, and creates the endpoint;
`invoke` tests it (`cases/aws-ai/ch06.md:288-305`):

```python
from bedrock_agentcore_starter_toolkit import Runtime
runtime = Runtime()
runtime.configure(entrypoint="agent.py", auto_create_ecr=True)
launch_result = runtime.launch()   # build → ECR → Runtime endpoint
```

Note the package name: this pip toolkit is the **legacy** CLI/SDK surface — see §5.

### 4.3 Memory — short/long-term with namespaces and strategies

AgentCore Memory persists context across sessions with managed extraction, so you
do not hand-roll storage (`cases/aws-ai/ch03.md:488-494`). Create a resource with
`MemoryClient` (`cases/aws-ai/ch03.md:638-639`):

```python
from bedrock_agentcore.memory import MemoryClient
client = MemoryClient(region_name=region)
memory = client.create_memory(name="MathLanggraphAgent")
```

Two concepts do the real work (`cases/aws-ai/ch03.md:545-572`):

- **Namespaces** partition memory so the agent does not blur unrelated facts —
  e.g. strategy-level (`/strategy/{strategyId}`, shared domain knowledge) vs
  actor-level (`/actor/{actorId}`, per-user preferences)
  (`cases/aws-ai/ch03.md:555-561`).
- **Strategies** decide *what* gets extracted into long-term memory and how it is
  organized. Three kinds: **built-in** (managed extraction for summaries,
  preferences, semantic knowledge), **built-in overrides** (limited customization,
  managed pipeline kept), and **self-managed** (full control). Configure none and
  long-term memory is simply not extracted (`cases/aws-ai/ch03.md:565-572`).

Memory also plugs into other frameworks: `AgentCoreMemorySaver` is a LangGraph
checkpointer backed by AgentCore Memory, letting a LangGraph agent persist and
resume state (`cases/aws-ai/ch03.md:652`), and that example is the one place the
corpus reaches Bedrock's **Converse** API — via LangChain's
`init_chat_model(MODEL_ID, model_provider="bedrock_converse", ...)`
(`cases/aws-ai/ch03.md:655`). The lighter-weight `Mem0` layer appears earlier as a
gentler intro to persistent, per-user memory (`cases/aws-ai/ch03.md:275-341`).

### 4.4 Gateway — turn APIs into MCP tools

Gateway takes an API definition (OpenAPI spec, Smithy model, Lambda, API Gateway
stage, or a remote MCP server) as a **target**, reads it, and generates an
MCP-compatible tool per operation — no per-API integration code. The agent sees one
unified tool catalog regardless of what each tool hits underneath
(`cases/aws-ai/ch06.md:398-431`). Author it with the control-plane client
(`cases/aws-ai/ch06.md:403-424`):

```python
import boto3
client = boto3.client("bedrock-agentcore-control")
gateway = client.create_gateway(...)
client.create_gateway_target(...)   # register each API/Lambda/MCP server as a target
```

Inbound auth is IAM (simplest when the agent already has an AWS role) or JWT via
Cognito/Okta/any OAuth 2.0 provider; outbound auth is per-target, with credentials
stored in Secrets Manager and tokens refreshed for you
(`cases/aws-ai/ch06.md:449-451`).

### 4.5 Identity

AgentCore Identity vaults OAuth2/API-key credentials and injects them at call time.
In agent code it surfaces as decorators — `@requires_access_token` /
`@requires_api_key` — with built-in providers for Google, GitHub, Slack,
Salesforce, Atlassian, and custom OAuth 2.0 providers for anything else
(`cases/aws-ai/ch06.md:465`). Identity is what lets end-user context flow through
Gateway to the tools, which is also what makes attribute-based Cedar policies
(§4.7) enforceable.

### 4.6 Observability

Instrument with OpenTelemetry/ADOT and AgentCore emits sessions, traces, spans,
tool-call spans, and — uniquely — **policy-evaluation spans** to CloudWatch, which
Langfuse and LangSmith cannot capture because they have no policy engine
(`cases/aws-ai/ch07.md:647-649`). From Strands, one call wires up OTLP export
(`cases/aws-ai/ch07.md:515-519`):

```python
from strands.telemetry import StrandsTelemetry
StrandsTelemetry().setup_otlp_exporter()
```

### 4.7 Policy (Cedar) — the layer guardrails cannot reach

Distinguish two controls (`cases/aws-ai/ch07.md:736-758`): **Guardrails** filter
*text* — the model's inputs and outputs (toxicity, PII, denied topics, RAG
grounding). **Policy** governs *actions* — which tool the agent may call, with what
parameters, for which user. Guardrails never see a tool call; if the agent decides
to invoke a $50,000 refund, the guardrail only sees the resulting text, after the
tool ran (`cases/aws-ai/ch07.md:755`).

AgentCore Policy closes that gap by intercepting every tool call *before* it
executes and evaluating it against **Cedar** rules — a declarative, deterministic
policy language that returns permit/deny regardless of prompt phrasing or model
mood (`cases/aws-ai/ch07.md:787-810`):

```cedar
// Deny refunds over $1,000, no matter what the agent reasons
forbid (
    principal,
    action == Action::"InvokeTool",
    resource == Tool::"process_refund"
)
when { context.toolParameters.amount > 1000 };
```

Because Cedar can read the authenticated user's attributes (via Identity, §4.5), it
enforces context-dependent rules guardrails cannot express — "a physician may read
a patient record only in their own department," and per-tenant data boundaries in
multi-tenant systems (`cases/aws-ai/ch07.md:814-841`). The agent's reasoning is not
overridden; the platform simply refuses the action, the way a DB permission stops
an app from dropping a table (`cases/aws-ai/ch07.md:810`).

**In compliance/regulated domains, default to the `forbid (…) unless { … }` style**
rather than `permit (…) when { … }`: an explicit-deny-with-narrow-carve-out policy
fails closed, so anything the carve-out does not name stays denied. Prefer it
consistently — a fail-closed default is safer than an allow-rule you might forget to
scope.

**Host note — which Cedar service.** AgentCore Policy is the enforcement point when
the agent runs on **AgentCore Runtime**. For a **Lambda- or ECS-hosted** agent
(no AgentCore Runtime), use **Amazon Verified Permissions** — the *same* Cedar
policies, evaluated in-process by calling `verifiedpermissions:IsAuthorized` before
each tool dispatch. Pick the one that matches the host rather than assuming
AgentCore Policy; the policy language and the permit/deny model are identical.

Apply model-level
Guardrails to a Strands agent through the model config
(`cases/aws-ai/ch07.md:762-781`):

```python
model = BedrockModel(model_id="...", guardrail_id="your-guardrail-id",
                     guardrail_version="1", guardrail_trace="enabled")
```

### 4.8 Evaluations

AgentCore Evaluations is a managed, serverless service that scores agents on any
framework by running LLM-as-judge (or code-based) evaluators over collected traces,
at **session**, **trace** (per-turn), or **span** (within-turn, tool-call) level
(`cases/aws-ai/ch07.md:261`, `cases/aws-ai/ch07.md:232-236`). Built-in evaluators
(e.g. `GoalSuccessRate`, `Correctness`, `Helpfulness`) cover general quality;
custom LLM-judge or code-based evaluators capture domain rules built-ins miss
(`cases/aws-ai/ch07.md:126-135`). Run them by name against traces
(`cases/aws-ai/ch07.md:387-422`):

```python
eval_client.run(evaluators=["Builtin.GoalSuccessRate"])                 # session-level
eval_client.run(evaluators=["Builtin.Correctness", "Builtin.Helpfulness"])  # trace-level
eval_client.run(evaluators=[custom_evaluator_id])                       # your domain rule
```

This is the natural source for `aws-ai-validate`'s eval criteria and for the GenAI
intersection handed back to `arch-validate`.

---

## 5. The two conflicting `agentcore` CLIs

A live footgun: **two different tools both register the `agentcore` command.**

- **`bedrock-agentcore-starter-toolkit`** (pip) — verbs `agentcore
  configure / launch / invoke`; the SDK form is the `Runtime` class in §4.2. The
  corpus uses this (`cases/aws-ai/ch06.md:288-305`). It is now **legacy**.
- **`@aws/agentcore`** (npm, `github.com/aws/agentcore-cli`) — verbs `agentcore
  create / dev / deploy / invoke` plus `agentcore add memory|identity|gateway`.
  This is the **forward** path (research doc §3, §1.5).

They collide on the same command name, and the verbs drifted (`launch` ↔ `deploy`).
Uninstall the pip toolkit before installing the npm CLI, pin the version you
target, and check `agentcore --help` to confirm which one is on `PATH`. Do not
assume a tutorial's verbs match your installed tool — this is exactly the kind of
fast-moving fact to re-verify against the research doc, not to hard-code.

---

## 6. Classic *Agents for Amazon Bedrock* — the legacy path

Flagged, secondary, not the default. The older "Agents for Amazon Bedrock" model
builds a managed agent through the `bedrock-agent` control-plane API. You will meet
it in existing code and in `cases/aws-ai` ch08–10, so recognize it — but new work
uses the Strands + AgentCore spine above. The legacy chapter drives it through a
raw `botocore` session and `create_agent` (`cases/aws-ai/ch08.md:605-676`):

```python
from botocore.session import Session       # legacy lineage
session = Session()
client = session.create_client("bedrock-agent", ...)
create_agent_response = client.create_agent(...)   # classic managed agent
```

The full classic lifecycle (from the research doc §1.4) is `create_agent` →
`create_agent_action_group` (Lambda executor or `RETURN_CONTROL`) →
`[associate_agent_knowledge_base]` → `prepare_agent` (recompile the DRAFT after
*every* change) → `create_agent_alias` → runtime `invoke_agent`. `invoke_inline_agent`
needs no pre-created resource.

**Why it is legacy, not just older.** Classic Agents pin you to a Bedrock-hosted
model with managed action groups; AgentCore hosts *any* agent code with modular
services (§4). And the same legacy chapters carry a genuine correctness bug to
avoid inheriting: ch09 sends the deprecated text-completions format
(`\n\nHuman:` / `\n\nAssistant:` + `max_tokens_to_sample` + `response["completion"]`)
against a Sonnet-4 model id (`cases/aws-ai/ch09.md:686-712`). The modern default is
the **Converse** API (`converse` / `converse_stream`) — never the completion format,
never `invoke_model` for chat. Treat ch08's `create_guardrail`/`create_agent` via
bare `botocore` (`cases/aws-ai/ch08.md:637-676`) as a separate generation, useful
mainly for its version-agnostic IAM/KMS JSON, not as a code model.

---

*Cross-links: raw Converse tool-use loop, Knowledge Bases/RAG, and Guardrails
authoring → `bedrock.md` and research doc §1. SageMaker-endpoint-as-tool →
`sagemaker.md`. CDK/Lambda/ECS/AgentCore deployment mechanics → `boto3-foundations.md`
and research doc §3. Offline verification of everything here (botocore `Stubber` for
`bedrock-runtime`, `moto` for the AgentCore/SageMaker control plane) is the
`aws-ai-validate` harness — remember `moto` cannot mock `bedrock-runtime`, so Stubber
is the only pure-unit path for the model calls these agents make.*
