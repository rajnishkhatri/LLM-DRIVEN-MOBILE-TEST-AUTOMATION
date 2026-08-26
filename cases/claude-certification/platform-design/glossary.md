---
type: reference
title: 'Glossary'
description: 'Module 1 key terms from Adaptive thinking through Wrapper: API and SDK, Claude.ai vs Claude Code vs Agent SDK, MCP, live state vs corpus, progressive vs monolithic context, evals, and related platform vocabulary.'
tags: [claude, certification, platform-design]
---

Glossary
The key terms used across this module, in alphabetical order. Click a term to expand its definition.

Adaptive thinking
Extended thinking where the model itself, rather than you, decides whether to think and how much, based on the complexity of each request. It can reason at length on a hard problem and skip thinking entirely on a trivial one. You steer it with an effort level rather than configuring a token budget. On current Claude models it is the recommended control, and on the newest models it is the only one.
API
Application Programming Interface. The direct way to send requests to Claude from your own code, with full control over the prompt, the model, the parameters, and how the response is handled. Using the API means you are building the surrounding application yourself: the user interface, the conversation history, the error handling, the logging. The tradeoff is maximum flexibility in exchange for owning the infrastructure around it.
Authoritative
Authoritative means the source you have agreed to treat as correct: the partner's system of record, the live policy table, the current price list. When an answer is authoritative, it comes from that trusted source rather than from the model's recollection, so you can stand behind it.
Claude Agent SDK
A managed agent runtime distributed as the @anthropic-ai/claude-agent-sdk package for TypeScript and Python. It gives a partner programmatic access to the same agent loop that powers Claude Code: iteration, tool execution, observation, termination, so the partner can embed an agent inside their own product instead of running Claude Code in a terminal. Distinct from the Anthropic SDK, which is a thin convenience wrapper over the API and does not run an agent loop.
Claude Code
An agentic coding tool that reads files, edits code, runs commands, and executes multi-step engineering tasks under configurable permission boundaries. Distributed as a CLI, IDE plugins (VS Code, JetBrains, and others), a desktop application, and a web product at claude.ai/code. Claude Code is the entry point engineers use to do real development work, and it is customizable through CLAUDE.md, skills, subagents, hooks, MCP servers, and permission settings.
Claude.ai
The end-user chat product hosted by Anthropic. Reached through the web, the mobile apps, and Claude Desktop. Users sign in, open conversations, upload files, share context through Projects, and connect external services through built-in connectors. No code is written. Claude.ai is the entry point for users, not builders, which is why a partner's engineering team usually does not consume Claude.ai when embedding Claude in their own product.
Corpus
The body of documents a retrieval system searches over. A corpus might be a knowledge base, a set of policy documents, a product manual, or a collection of past tickets. The corpus is loaded and indexed ahead of time, which is why it works for stable reference material and not for live state.
CSP delivery route
Cloud Service Provider delivery route: The path that API traffic takes to reach Claude. Anthropic offers a direct route at api.anthropic.com, and the same Claude models are also available through AWS Bedrock, GCP Vertex AI, and Microsoft Foundry on Azure. The route you choose determines where the spend is billed, how the call is authenticated, which region the traffic terminates in, and which contract covers it. It does not affect how the model behaves.
Deterministic rule
A deterministic rule is a rule that always produces the same output for the same input. Same in, same out, every single time, with no variation.
Eval
Eval short for evaluations is a structured test set used to measure whether a model is performing well enough on a defined task. An eval pairs inputs with expected outputs or quality criteria, runs them against the model, and produces a score you can compare across model versions, prompts, or configurations. Evals are how teams decide whether a change is an improvement or a regression before it reaches production.
Extended thinking
The capability where the model works through a problem in a separate block of thinking tokens before it commits to a final answer, rather than responding in one pass. It helps on tasks where a one-shot answer would skip steps. Thinking tokens are billed as output tokens and add latency. How much thinking happens depends on the control mode: a thinking-token budget you configure yourself on older models, or adaptive thinking (see Adaptive thinking) on current ones.
IDE
Integrated Development Environment. A software application that bundles a code editor, debugger, and other tools into one place for writing and running code (e.g., VS Code, PyCharm, Xcode).
Live state
Data that changes during the lifetime of a conversation or process: an order status, an inventory count, a price, a calendar slot, a user's current session. Live state is distinct from static reference material because the correct answer at 10:00 a.m. may be wrong by 10:05. Systems that need live state require a direct lookup against the source of truth, not a stored snapshot.
MCP
Model Context Protocol. An open standard that lets Claude connect to external tools and data sources through a dedicated server, instead of requiring you to write a custom integration for each one. An MCP server exposes tools, prompts, and resources that any MCP-compatible client can use, which means a single integration written once can be reused across applications. MCP shifts the work of building and maintaining tool definitions away from your application code and into reusable servers.
Monolithic
The opposite of progressive: everything the model might need is loaded into context up front, in one block. Monolithic context is simpler to set up and fine for short, contained tasks, but it grows over time, pushes against the context window, and forces the model to attend to material that may not be relevant to the current step. Long-lived deployments built monolithically tend to degrade as the conversation accumulates.
Observability
Ability to see what your system is doing, reconstruct why it behaved a certain way, and detect when something goes wrong.
Parametric knowledge
Parametric knowledge means whatever the model learned during training and carries in its weights (its parameters). It is the model answering from memory, with no outside lookup. The opposite is knowledge the model pulls in at the moment of the request, like a document you hand it or a web search result.
Progressive
An approach where context, instructions, or capabilities are loaded in stages as the work requires them, rather than all at once at the start. Progressive context gives the model only what it needs at each step, which keeps the working set focused and the cost of each call lower. The pattern shows up in skills that load reference files on demand and in agents that gather information through tool calls instead of receiving everything in the initial prompt.
Prompt caching
Prompt caching is a feature that lets you store frequently used parts of a prompt, typically a long system prompt or a large document, so the model doesn't have to reprocess them from scratch on every request. The cached portion is computed once and reused across multiple calls.
Retrieval
Fetching relevant information from an outside source at the moment of the request and handing it to the model along with the question. Instead of relying on what the model learned in training, you pull the current document, record, or passage and put it in front of the model so the answer is grounded in that source.
SDK
Software Development Kit. A language-specific library (Python, TypeScript, and others) that wraps the API in idiomatic code for that language. The SDK handles the request formatting, authentication, retries, and response parsing so you can call Claude with a few lines of code instead of constructing HTTP requests by hand. The SDK is built on top of the API, so anything the API can do, the SDK can do, with less boilerplate. When an engineer says "SDK" they may mean this Anthropic SDK (a wrapper over the API) or the Claude Agent SDK (a managed agent runtime); however, these are two different things.
Shippable
Ready for production use, not just a working demo. Shippable output meets the bar for accuracy, latency, cost, and reliability that the deployment actually requires, and it has passed the evals and review gates the team uses to release changes. The distinction matters because a prototype that handles the happy path is not the same as a system that handles the long tail of real user inputs.
Terminal
A text-based interface for interacting with your computer's operating system by typing commands. Also called a command line or shell (e.g., Terminal on Mac, Command Prompt on Windows).
Tool use
The capability that lets Claude call external functions, APIs, or services during a response instead of only generating text. The model decides when to invoke a tool, what arguments to pass, and how to use the result in its next step. Tool use is what turns Claude from a text generator into a system that can read files, query databases, search the web, or take action in other software.
Wrapper
Code that surrounds or encapsulates another piece of code, library, or API to make it easier to use, add functionality, or translate between interfaces. For example, a Python wrapper around a C library lets you call C functions as if they were native Python.
← Prev
Screen 32 of 34
