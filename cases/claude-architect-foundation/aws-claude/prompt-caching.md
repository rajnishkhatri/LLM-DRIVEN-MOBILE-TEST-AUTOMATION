---
type: guide
title: 'Prompt caching — cache points, identity, and reuse'
description: 'A cache point stores work for five minutes when the prefix is identical and at least 1024 tokens. Cache system prompts and tool schemas; watch cache_read vs cache_write.'
tags: [claude, bedrock, aws-claude, caching]
---

# Prompt caching — cache points, identity, and reuse

Without caching, every request rebuilds internal structures on the input, generates, returns, and **discards** that work. Repeated identical prefixes (system prompts, tool schemas, a large document) pay that cost every time.

**Prompt caching** keeps the work in a temporary cache and reuses it when a follow-up request has the same prefix. Faster responses and lower generation cost on repeated content.

## Rules

A **cache point** is a message part that marks the boundary: everything *before* it is eligible to cache; everything *after* is never cached. Cache lifetime is **five minutes** of inactivity.

Requirements:

- At least **1024 tokens** before the cache point.
- Bytes before the cache point must be **exactly identical** across requests. Any difference invalidates the cache.

Cache points apply to text parts, tool-definition lists, system prompts, and multi-message conversations. Highest leverage: tool JSON schemas (often large and stable) and system prompts (rarely change).

## In action

- Add a `cache_point` with `type="default"` on system-prompt parts.
- Concatenate a cache point onto the tools list.
- Read the response `usage` field.

First request: `cache_write` (tokens stored). Later identical prefixes: `cache_read` (tokens retrieved). After five idle minutes the cache expires. Changing cached content triggers a new write.

Watch `cache_write_input_tokens` and `cache_read_input_tokens` to confirm it is actually hitting. Text *below* the cache point can change without busting the cache; text *above* it cannot.
