---
type: failure-taxonomy
title: 'Watch-out: when passing entry point selection feels like finishing compliance'
description: 'Failure trace: a compliant route was treated as settled. No owner, no living artifact. A later logging change wrote metadata to a second region and the gap surfaced at audit.'
tags: [claude, certification, responsible-ai]
---

When passing entry point selection feels like finishing compliance
SETUP HOOK
Passing the constraint pre-filter and being able to prove compliance are two different things. The pre-filter gives you a clean signal. Choosing a delivery route that survives HIPAA, GDPR, or FedRAMP produces an immediate, visible result: the route is allowed, the entry point is cleared, the design can move. Proving that each obligation is being met produces nothing visible at design time, because the proof is an artifact you must build, attach to an owner, and keep alive as configurations change. That gap is easy to miss, because the moment that feels like a finish line and the moment a reviewer checks are often months apart.
A deployment that chose the right route but produces no proof
A team selected a compliant delivery route for a regulated workload and treated compliance as settled. They had mapped obligations to controls once, at design time, in a document. No owner was attached to the controls, and no logging was wired to show any control was operating.

The data residency obligation is where the failure concentrated. The control was correct on paper: processing pinned to the approved region. However, months later a logging configuration changed and started writing request metadata to a store in a second region. Nothing identified the change, because no one owned residency control and no artifact tracked where data was landing. The gap surfaced at the audit, not at design, when a reviewer asked for evidence that data stayed in-region and the team had a design document instead of a data-flow record.

WHY THIS BROKE
Surviving the pre-filter was mistaken for establishing compliance. A compliant route is a prerequisite, not proof. Each obligation needs a control, a named owner, and a living evidence artifact that is revalidated as the deployment changes. The residency control in this story was real at design time and silently false in production, and nothing caught the difference because no artifact was watching it.
← Previous
