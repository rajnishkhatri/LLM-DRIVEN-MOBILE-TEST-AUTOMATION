# AWS Claude / Bedrock — bundle index

OKF bundle. Each entry is a typed Concept. See the convention in [CONVENTIONS.md](../../../docs/CONVENTIONS.md).

- [Agents and computer use — tool loops, environment, and risk](agents-and-computer-use.md) — An agent is a model in a tool loop until the goal is met. Computer use is that loop over screenshots and UI actions. Keep the toolset small and the failure cost bounded.
- [Bedrock Converse API — requests, conversation, and output control](bedrock-converse-api.md) — Stateless Converse calls on Bedrock: inference profiles, message history, system prompts, temperature, streaming, prefills, and stop sequences.
- [Claude Code — memory, MCP, worktrees, and automated debugging](claude-code.md) — Treat Claude Code as a teammate: CLAUDE.md memory, MCP add-ons, git worktrees for parallel agents, and a log-to-PR debugging loop that still needs human review.
- [Extended thinking and vision](extended-thinking-and-vision.md) — Extended thinking is eval-gated and billed as tokens. Vision needs the same prompt discipline as text — step-by-step and few-shot beat a one-line caption.
- [Model Context Protocol — tools, resources, prompts, and clients](mcp.md) — MCP moves tool authoring onto a server. Tools are model-controlled, resources app-controlled, prompts user-controlled. Covers the SDK, inspector, and Bedrock client wiring.
- [Prompt caching — cache points, identity, and reuse](prompt-caching.md) — A cache point stores work for five minutes when the prefix is identical and at least 1024 tokens. Cache system prompts and tool schemas; watch cache_read vs cache_write.
- [Prompt evaluation pipeline — dataset, run, grade, iterate](prompt-evaluation.md) — Measure prompts with a dataset, model and code graders, and an average score before iterating — do not ship on a couple of manual checks.
- [Prompt engineering techniques — clarity, specificity, XML, examples](prompt-techniques.md) — Four high-leverage prompt edits: lead with an action verb, add attributes or steps, wrap interpolated content in XML tags, and show desired outputs with examples.
- [RAG on Bedrock — chunking, embeddings, hybrid search, and rerank](rag.md) — Retrieve only relevant chunks: size, structure, or semantic chunking, embeddings, BM25 hybrid with RRF, LLM rerank, and contextual retrieval.
- [Tool use on Bedrock — schemas, the tool loop, and structured extraction](tool-use.md) — Claude requests tools; application code runs them and returns results. Covers schemas, the stop_reason loop, batching, the text-editor tool, and schema-as-extractor.
