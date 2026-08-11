---
name: "sdd-roles"
description: "SDD role conveyor catalog; roles: 3; arms: 1"
stamp: "sdd-roles 1.4.0 catalog:6faa3f576a54"
---

# sdd-roles kernel

SDD role conveyor catalog; roles: 3; arms: 1

## Console scripts

- contract-lint: validate artifacts and run the corpus selftest gate
- gate-wrap: translate gate tool exits through descriptor exit maps
- gate-runner: run the between-run conveyor (sole ledger writer)
- write-guard: live write decisions (decide) and hook mounting (mount)
- role-emit: project the catalog into harness layouts (project / verify)
- kata: the deterministic kata study instrument (plan / analyze / report)

## Roles

- em-planner: maker role; gates: none; writes: plans/
- em-builder: maker role; gates: build, tests; writes: src/, tests/
- em-reviewer: checker role; gates: tests; writes: none; diagnostic-capable
