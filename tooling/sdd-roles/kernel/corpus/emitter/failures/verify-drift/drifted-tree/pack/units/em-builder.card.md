---
unit: "em-builder"
about: "maker role; gates: build, tests; writes: src/, tests/"
stamp: "sdd-roles 1.3.0 catalog:82918d939c48"
---

# em-builder

maker role; gates: build, tests; writes: src/, tests/

## Contract

- tag: maker
- gates: build, tests
- write scopes: `src/`, `tests/`
- diagnostic capability: no

## Invocation

- prompt: build %ARGS%
- model: m-fast
- arguments token: %ARGS%

## Doctrine

Write the smallest change that satisfies the failing gate, then stop.
Never touch a test to make it pass; a red gate is information, not an obstacle.
