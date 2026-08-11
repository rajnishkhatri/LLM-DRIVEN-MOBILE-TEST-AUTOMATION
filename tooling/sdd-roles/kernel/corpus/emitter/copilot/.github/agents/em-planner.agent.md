---
name: "em-planner"
description: "maker role; gates: none; writes: plans/"
stamp: "sdd-roles 1.4.0 catalog:4703ccfae8c6"
---

# em-planner

maker role; gates: none; writes: plans/

## Contract

- tag: maker
- gates: none
- write scopes: `plans/`
- diagnostic capability: no

## Invocation

- prompt: plan $ARGUMENTS
- model: m-large
- arguments token: $ARGUMENTS

## Doctrine

<!-- doctrine: pending (build item 5) -->
