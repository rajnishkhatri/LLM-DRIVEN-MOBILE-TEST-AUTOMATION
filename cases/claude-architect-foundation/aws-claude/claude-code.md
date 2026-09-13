---
type: guide
title: 'Claude Code — memory, MCP, worktrees, and automated debugging'
description: 'Treat Claude Code as a teammate: CLAUDE.md memory, MCP add-ons, git worktrees for parallel agents, and a log-to-PR debugging loop that still needs human review.'
tags: [claude, bedrock, aws-claude, claude-code]
---

# Claude Code — memory, MCP, worktrees, and automated debugging

Claude Code is an AI coding assistant that behaves as another engineer on the team, not a snippet generator. Small effort directing it pays disproportionately — an effort multiplier, not an autopilot.

## In action

Typical first session: open the project → `claude` in the terminal → ask it to read the README and follow setup → `/init` so it scans the tree and writes `CLAUDE.md` (architecture and style notes). That file is included as context on later turns.

Three memory scopes: project, local, user. `#` plus a note appends to `CLAUDE.md`. You can edit the file by hand or rerun init.

Two workflows for a non-trivial feature:

**Plan then implement**

1. Identify relevant files; have Claude read them.
2. Describe the feature; ask for a plan with no code yet.
3. Ask Claude to implement the plan.

**Test-driven**

1. Read relevant context.
2. Ask for suggested tests (no implementation).
3. Keep the relevant tests; ask Claude to write them.
4. Ask Claude to implement until the tests pass.

Commands: `claude` launches; `init` generates `CLAUDE.md`; `/clear` resets history; `# [note]` appends memory.

## Enhancements with MCP servers

Claude Code embeds an MCP client. `claude mcp add [name] [startup-command]` (example: `claude mcp add documents "uv run main.py"`), then restart with `claude`.

A documents MCP lets Claude Code read PDF/Word and convert to Markdown. Other servers: Sentry (production errors), Jira (ticket body), Slack (completion pings). MCP is how you extend the agent without forking Claude Code.

## Parallelizing Claude Code

Several Claude instances on one developer only work if they do not share a working tree. **Git worktrees** give each instance an isolated checkout on its own branch.

Workflow: create a worktree → assign a task → commit on that branch → merge to main (Claude can resolve conflicts) → remove the worktree.

Custom slash commands: markdown files under `.claude/commands` with `$ARGUMENTS`, invoked as `/project:command-name`. Delegate worktree create/merge/cleanup to Claude rather than driving Git by hand. Throughput scales with how many isolated instances you can actually review.

## Automated debugging

A scheduled GitHub Action: pull CloudWatch (or similar) logs → filter and dedupe → Claude analyzes each error → proposes a fix → commits → opens a PR.

That loop catches production-only failures (an invalid model id that never showed up locally). It still requires a human on the PR. You need CI, log access, an AI coding assistant, and version-control automation. The architectural property is **fail-visible plus human merge**, not unattended production writes.
