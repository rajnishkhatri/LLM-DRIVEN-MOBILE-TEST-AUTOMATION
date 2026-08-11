---
name: "sdd-roles"
description: "SDD role conveyor catalog; roles: 9; arms: 4"
stamp: "sdd-roles 1.4.0 catalog:cabd69051aa2"
---

# sdd-roles kernel

SDD role conveyor catalog; roles: 9; arms: 4

## Console scripts

- contract-lint: validate artifacts and run the corpus selftest gate
- gate-wrap: translate gate tool exits through descriptor exit maps
- gate-runner: run the between-run conveyor (sole ledger writer)
- write-guard: live write decisions (decide) and hook mounting (mount)
- role-emit: project the catalog into harness layouts (project / verify)
- kata: the deterministic kata study instrument (plan / analyze / report)

## Roles

- specifier: maker role; gates: none; writes: specs/
- coder: maker role; gates: build, tests, ir-gate; writes: src/, tests/
- cleaner: maker role; gates: build, tests, crap; writes: src/
- architect: maker role; gates: build; writes: src/, tests/, docs/adr/
- hardener: checker role; gates: tests, mutation; writes: src/test/, tests/, specs/
- qa: checker role; gates: build, tests, crap, ir-gate; writes: src/, tests/; diagnostic-capable
- solo: maker role; gates: build, tests, crap, mutation, ir-gate; writes: src/, tests/, specs/; diagnostic-capable
- maker3: maker role; gates: build, tests, crap, ir-gate; writes: src/, tests/
- checker3: checker role; gates: tests, mutation, ir-gate; writes: src/, tests/; diagnostic-capable
