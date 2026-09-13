---
type: guide
title: 'Tool use on Bedrock — schemas, the tool loop, and structured extraction'
description: 'Claude requests tools; application code runs them and returns results. Covers schemas, the stop_reason loop, batching, the text-editor tool, and schema-as-extractor.'
tags: [claude, bedrock, aws-claude, tool-use]
---

# Tool use on Bedrock — schemas, the tool loop, and structured extraction

Tool use is how Claude reaches information and actions outside its training data (current weather, the real clock, a reminder API).

Logical flow:

1. Send the user request plus tool instructions.
2. Claude requests specific external data (a `tool_use` part).
3. The server runs code against the real API.
4. Tool results go back to Claude.
5. Claude writes the final answer with that data.

Implementation order in code is usually the reverse of that story (function → JSON schema → result handling → include schema in the request). Keep the logical diagram in view so you know which piece you are wiring.

## Tool functions

Write ordinary Python functions Claude cannot do natively. A reminders project used three: `get_current_datetime`, `add_duration_to_date`, `set_reminder`.

Practices: descriptive argument names (Claude reads them), validate inputs and raise on garbage, return useful data.

```python
def get_current_datetime(date_format="%Y%m%d%H%M%S"):
    return datetime.now().strftime(date_format)
```

Creation is four steps: write the function, write the JSON schema, register it on the request, test the integration.

## JSON schema for tools

A schema is a general validation format, not LLM-specific. Two parts: name/description at the top, then a JSON object of parameters.

A practical authoring path: dict of sample arguments → JSON (`True` → `true`) → a JSON-to-schema converter → drop `$schema` → add a `description` on every property. Claude can draft those descriptions from the function source.

The overall tool description should be 3–4 sentences: what it does, when to use it, what it returns. Property descriptions explain each argument. The schema travels with the request so Claude can call the function with the right types.

## Handling tool-use responses

The response dictionary includes `stop_reason`. `stop_reason == "tool_use"` means Claude wants a tool run.

The assistant `content` list has multiple parts: a text part (optional user-facing note) and one or more `tool_use` parts (`toolUseId`, `name`, `input`). Follow-up requests must send the full history: original user message, the complete assistant message (all parts), then tool-result parts.

Chat helpers should return both text and parts. `add_assistant_message` / `add_user_message` should accept a string or a list of parts.

**toolChoice:** `auto` (Claude decides, default), `any` (must use some tool), or a named tool (useful for tests).

## Running tool functions

Filter message parts for `tool_use`. Claude may request several tools in one message. For each: extract id, name, input; dispatch by name; splat `**tool_input`; JSON-serialize the return value.

Tool-result part shape: `{tool_result: {tool_use_id, content: [text], status: success|error}}`. The id links a result to its request when several tools run together.

Wrap execution in try/except and return `status: error` with the message rather than crashing. Claude can retry with corrected arguments.

## Sending tool results

Append the assistant message (the tool requests), then a user message of tool-result parts, then call Converse again with the **same tool schemas**. Omitting schemas on the follow-up confuses Claude about the tool definitions.

Conversation shape: user → assistant (tool requests) → user (tool results) → assistant (final). Success looks like Claude using data it could not have known (current time, not just a date).

## Multi-turn conversations with tools

Loop until the model stops asking for tools:

```
run_conversation(messages):
  while True:
    result = chat(messages, tools)
    add assistant_message(result.parts) to messages
    if result.stop_reason != "tool_use": break
    tool_results = run_tools(result.parts)
    add user_message(tool_results) to messages
  return messages
```

Only process tools when `stop_reason` says so — otherwise you append empty tool-result turns. The same loop handles conversations that never need a tool.

## Adding multiple tools

After the first tool works, more tools are cheap: register the schema and add a dispatch case. Example: "Set a reminder for a doctor appointment in 100 days" → get current date → add 100 days → set reminder, three sequential calls.

## Batch tool use

Claude *can* emit several `tool_use` parts in one message but often serializes independent calls. A `batch_tool` whose input is a list of `{name, arguments}` invocations lets Claude group parallel-eligible work into one request. `run_batch` parses each invocation and delegates to the existing `run_tool`. Claude treats the batch as a single tool turn.

## Structured data with tools

Instead of [prefill + stop](bedrock-converse-api.md) for JSON, define a *fake* tool whose inputs *are* the desired structure. Force it with `toolChoice` set to that tool name. Claude "calls" the tool; you take the arguments as the extracted JSON and **stop** (do not continue the conversation).

More reliable than prompt-only extraction; heavier to set up. Example: a finance extractor with `balance` (int) and `key_insights` (string array).

## Flexible tool extraction

To avoid large rigid schemas, one `toJSON` tool with a free-form object input lets the **prompt** name the properties. Faster to iterate (edit the prompt, not the schema); slightly lower quality than a dedicated schema. Use flexible extraction for general work and dedicated schemas when accuracy is critical.

## The text editor tool

Claude ships a built-in schema for file editing. **You** still implement the commands. Exact Bedrock tool names:

- Claude 3.7: `str_replace_editor`
- Claude 3.5: `str_replace_based_edit_tool`

Five commands: `view`, `str_replace`, `create`, `insert`, `undo_edit`. Flow is the ordinary tool loop. That is how Claude acts as a software engineer against a real filesystem — refactor, add a feature, generate tests.
