# ML solutions architecture — bundle index

OKF bundle. Each entry is a typed Concept. See the convention in [CONVENTIONS.md](../../docs/CONVENTIONS.md).

- [Big data and GPUs in ML microservices](big-data-microservices.md) — Four data-path techniques — partition, stream, shared store, batch — plus putting GPUs only on the services that burn them.
- [Cloud scaling for ML microservices](cloud-scaling-ml.md) — Rent compute, functions, and orchestration per stage. The source vendor plate is a catalogue, not a support matrix. Mis-sized GPUs dominate the bill.
- [Challenges of ML microservices](microservices-challenges.md) — The split costs complexity, network latency, and model-version skew. If the project is not large enough, do not pay it.
- [Microservices in ML](microservices-in-ml.md) — An ML microservice is one pipeline stage as a self-contained deployable: own runtime, own scale, API or events to neighbours. Heterogeneous stacks are the point.
- [Dependency management for ML microservices](ml-dependency-management.md) — Pin and isolate per service: venv for the laptop, images for runtime, lock files for bits, orchestration for which image runs. Drift and diamond trees are the failure modes.
- [Design patterns for ML microservices](ml-microservices-patterns.md) — Five patterns that absorb the distributed-system bill: saga, circuit breaker, API gateway, events, sidecar. They do not make a bad cut good.
- [Modular design principles for ML systems](modular-design-principles.md) — Five properties — SoC, high cohesion, low coupling, reuse, abstraction — plus independent scale. They apply inside a process before they apply across a network.
- [Techniques for modular ML systems](modular-implementation.md) — Seven implementation styles — pipelines, containers, microservices, serverless, libraries, cloud orchestration, FaaS — each with a different operational bill.
- [Worked exercise — in-process modular ML pipeline](modular-pipeline-exercise.md) — Five classes (load, preprocess, train, predict, orchestrate) prove cohesion, not distribution. Fit the scaler on train only. This is a modular monolith, not microservices.
- [Building scalable and modular ML systems](modular-scalar.md) — Modularity is independent change and independent scale. Microservices are one style of that, not the only one — and they buy a distributed system.
