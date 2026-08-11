---
name: "em-builder"
description: "maker role; gates: build, tests; writes: src/, tests/"
stamp: "sdd-roles 1.4.0 catalog:4703ccfae8c6"
---

# em-builder

maker role; gates: build, tests; writes: src/, tests/

## Contract

- tag: maker
- gates: build, tests
- write scopes: `src/`, `tests/`
- diagnostic capability: no

## Invocation

- prompt: build {args}
- model: m-fast

## Doctrine

Write the smallest change that satisfies the failing gate, then stop.
Never touch a test to make it pass; a red gate is information, not an obstacle.
