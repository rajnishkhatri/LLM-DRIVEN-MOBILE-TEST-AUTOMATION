---
unit: "sdd-roles"
stamp: "sdd-roles 1.3.0 catalog:82918d939c48"
---

# sdd-roles kernel

SDD role conveyer catalog; roles: 3; arms: 1

## Console scripts

- contract-lint: validate artifacts and run the corpus selftest gate
- gate-wrap: translate gate tool exits through descriptor exit maps
- gate-runner: run the between-run conveyor (sole ledger writer)
- write-guard: live write decisions (decide) and hook mounting (mount)
- role-emit: project the catalog into harness layouts (project / verify)

## Roles

- em-planner: maker role; gates: none; writes: plans/
- em-builder: maker role; gates: build, tests; writes: src/, tests/
- em-reviewer: checker role; gates: tests; writes: none; diagnostic-capable
