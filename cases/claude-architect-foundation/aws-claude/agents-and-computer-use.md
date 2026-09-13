---
type: overview
title: 'Agents and computer use — tool loops, environment, and risk'
description: 'An agent is a model in a tool loop until the goal is met. Computer use is that loop over screenshots and UI actions. Keep the toolset small and the failure cost bounded.'
tags: [claude, bedrock, aws-claude, agents]
---

# Agents and computer use — tool loops, environment, and risk

An **agent** is a language model with tool access, run repeatedly until the goal is reached or it fails. That is the same [tool loop](tool-use.md) as a single weather call, left running.

## Qualities of agents

- **Tool-centric** — tools in a loop until done or error, not a one-shot completion.
- **Mostly inspection** — most calls gather environment data; fewer mutate it.
- **Context from tools** — the model does not "know" the world; it inspects via tools rather than a giant RAG dump or a novel-length system prompt.
- **Small toolset** — few tools, each with a clear job.
- **High value, bounded downside** — useful work where a mistake is not catastrophic.

Patterns: Claude Code reads files, writes files, runs tests. Computer use takes screenshots as the environment signal. Design principle: **context is king** — no inherent world knowledge, only what tools return. [Evals](prompt-evaluation.md) are how you know the loop works. Suitability is a risk assessment: valuable task, failure cost you can absorb.

Core loop: execute tool → inspect environment → judge progress → repeat.

## Computer use

Computer use is Claude driving a UI: screenshots, mouse, keyboard, scroll, multi-step workflows. Primary uses: QA (run cases, find UI bugs, report), web-app testing (navigate, fill, assert), general desktop automation. It runs in an isolated Docker container; a chat interface supplies instructions; visual feedback chooses the next action.

Benefit: existing apps, no instrumentation. Cost: you are granting UI-level autonomy, so isolation and review matter.

## How computer use works

It is **tool use with a fat action schema**: move mouse, left click, screenshot, type, and so on. Anthropic's reference implementation expands a small schema into that action surface. Claude never touches the host OS — a Docker environment executes the requested key/mouse events and returns a new screenshot as the tool result.

Setup: Docker, a local AWS profile, the vendor's pre-built container. Same contract as any other tool: Claude decides; your (or Anthropic's) runtime executes.
