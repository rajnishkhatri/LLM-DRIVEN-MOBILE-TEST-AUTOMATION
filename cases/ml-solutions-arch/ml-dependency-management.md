---
type: guide
title: 'Dependency management for ML microservices'
description: 'Pin and isolate per service: venv for the laptop, images for runtime, lock files for bits, orchestration for which image runs. Drift and diamond trees are the failure modes.'
tags: [ml-solutions-arch, dependencies, containers, kubernetes, reproducibility]
---

# Dependency management for ML microservices

**See also:** [microservices](microservices-in-ml.md) · [techniques](modular-implementation.md) · [challenges](microservices-challenges.md)

Each ML service carries its own stack: Python packages, CUDA, tokenisers, native wheels. Unpinned or shared environments are how “it worked last quarter” becomes a production incident. Reproducibility is the quality attribute; isolation is the tactic.

The source dump’s “container has no internet but my laptop does” story is the same lesson: **the runtime is not your laptop.** Design for the image, not for `pip install` on a developer machine.

## Layers (Table 4-4)

| Layer | Job | Named tools (source plate) | When it is enough |
|---|---|---|---|
| **Virtual environments** | Isolated *Python* deps on one machine | venv, Conda | Local experiment; not a deploy unit |
| **Package managers + lock files** | Exact versions, same install everywhere | pip, npm, yarn; `requirements.txt` / lockfiles | Reproducible *build*; still needs a runtime |
| **Containers** | Code + libs + runtime as one artefact | Docker, Podman | The deploy unit for a service |
| **Orchestration** | Run the *right image*, restart, balance | Kubernetes, Helm | Many containers; does not resolve pip itself |
| **Scanning** | Flag vulnerable or stale deps | Dependabot, Snyk | Hygiene on top of pins, not a substitute |

Kubernetes does not “manage dependencies.” It schedules images that already froze them. Helm packages those images with config.

## Failure modes

| Mode | What happens | Why ML hits it hard |
|---|---|---|
| **Version conflicts** | Two services need different numpy / CUDA | Heterogeneous stages are the [point](microservices-in-ml.md) |
| **Dependency drift** | Unpinned installs move under you | “Works then fails” after a base-image rebuild |
| **Diamond trees** | A needs B==1, C needs B==2 *inside one service* | ML stacks are deep; this is in-process, not cross-service |

Cross-service version skew is *expected* (that is isolation). In-process diamonds are a packaging bug: split the service or vendor one tree.

## Practices that actually hold the line

- **Immutable infrastructure:** do not `pip install` into a running container. Rebuild, ship a new tag, redeploy. In-place upgrades *are* drift.
- **Lock files** (`Pipfile.lock`, `package-lock.json`, hashed requirements): the bits you tested are the bits you serve.
- **Scan** as a gate, not a dashboard.

**Architect takeaway:** one image per [service](microservices-in-ml.md), one lock file per image, no shared site-packages. The container boundary is how you keep CUDA 11 and CUDA 12 on the same cluster without a diamond. If two stages cannot agree on a wheel, they were never one module.
