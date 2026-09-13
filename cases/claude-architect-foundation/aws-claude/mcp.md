---
type: guide
title: 'Model Context Protocol — tools, resources, prompts, and clients'
description: 'MCP moves tool authoring onto a server. Tools are model-controlled, resources app-controlled, prompts user-controlled. Covers the SDK, inspector, and Bedrock client wiring.'
tags: [claude, bedrock, aws-claude, mcp]
---

# Model Context Protocol — tools, resources, prompts, and clients

MCP is a client-server protocol that gives Claude tools, resources, and prompts without each application authoring every JSON schema and adapter. The server wraps an outside service (GitHub, AWS, a document store). Tool definition and execution move onto that server.

MCP and [tool use](tool-use.md) are complementary: tool use is the mechanism Claude uses to call functions; MCP decides *who authored and who runs* those functions. Anyone can write an MCP server; service providers often ship official ones. Direct API calls still work — MCP saves the schema-and-wrapper tax.

## MCP clients

The client talks to the server over a transport (stdio, HTTP, WebSockets, …). A common teaching setup is client and server on one machine over stdin/stdout.

Message types: list-tools request/result, call-tool request/result.

Typical round-trip: user query → app asks the MCP client for the tool list → tools go to Claude with the query → Claude returns `tool_use` → app asks the client to execute → MCP server runs the real API → results flow back → Claude writes the final answer.

## Project setup (teaching shape)

A CLI chatbot that implements **both** client and server in one repo (real projects usually pick one side). Fake in-memory documents; two tools (read, update). Configure Bedrock region and model ID, install with uv or pip, run `uv run main.py` / `python main.py`.

## Defining tools with MCP

The Python MCP SDK replaces hand-written JSON schemas. `@mcp.tool` plus typed parameters and Pydantic `Field` descriptions; the SDK emits the schema.

Examples: `read_doc_contents(doc_id)` and `edit_document(doc_id, old_string, new_string)`. Raise `ValueError` when `doc_id` is missing. That is the same contract as a hand-rolled tool, with less schema ceremony.

## The server inspector

`mcp dev [server.py]` opens a browser debugger: Connect, list tools, fill parameters, Run Tool. Use it to prove the server before wiring a client. The UI moves during development; Connect / Tools / Run stays the idea.

## Implementing a client

Wrap a client session for lifecycle (`async` enter/exit). Expose `list_tools()` and `call_tool(name, input)`. MCP tool shapes are not Bedrock's — convert with a `to_bedrock_tools()` helper before Converse. Test the client against the server in isolation, then plug it into the Claude loop: list tools for the model, execute when the model requests, tear the session down.

## Defining resources

Resources are **read** surfaces, not actions.

- **Static:** fixed URI, e.g. `docs://documents`.
- **Templated:** URI with parameters, e.g. `docs://documents/{doc_id}`.

`@mcp.resource` with a URI and MIME type (`application/json`, `text/plain`). Templated parameters become function kwargs. The SDK stringifies returns. One resource per distinct read. Example: list document names for autocomplete; fetch one document by id for `@`-mention injection without a tool call.

## Accessing resources

`read_resource(uri)` → `session.read_resource` → take `contents[0]`. If `mime_type == "application/json"`, `json.loads`; else use `text`. The app fetches, the user picks, content is inserted into the prompt. No tool call — the data is already in context.

## Defining prompts

MCP prompts are **pre-tested templates** the server exposes for a domain task. `@prompt` with name/description, returning a list of user/assistant messages. Example: "format this document to markdown using the edit tools." Parameters (a document id) interpolate into the template. Inspect them in the MCP inspector the same way as tools.

## Prompts in the client

- `list_prompts()` → `session.list_prompts()`
- `get_prompt(name, arguments)` → `session.get_prompt` → `result.messages`

The client supplies an arguments dict; the server interpolates; the returned messages go straight to Claude. CLI apps can surface prompts as slash commands.

## MCP review — who controls what

| Primitive | Controlled by | Purpose | Example |
|---|---|---|---|
| Tools | Model | Add capabilities Claude can choose | Run JavaScript, edit a doc |
| Resources | App | Data for UI or prompt augmentation | Drive file list, `@` inject |
| Prompts | User | Predefined workflows | Chat-starter buttons, `/format` |

Need a capability Claude should invoke → tool. Need data for the app or the prompt → resource. Need a canned workflow a human starts → prompt. In Claude.ai: buttons under the input are prompts; a Google Drive listing is resources; automatic code execution is a tool.
