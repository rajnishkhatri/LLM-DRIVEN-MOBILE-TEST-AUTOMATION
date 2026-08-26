---
type: architecture
title: 'ADR 0001 — Serve the study-cluster HTML from GitHub Pages as a static origin'
description: >-
  New public HTTP origin for the D2 allowlist (prep-guide v3 + M1 atlas +
  catalog). GitHub Pages, static files, layout-preserving sibling URLs. Not a
  SPA, not Vercel, not all of docs/. First ADR of the application/html-site
  series — distinct from mobile-test-automation 0001–0017.
tags: [architecture, adr, html-site, github-pages]
---

# ADR 0001. Serve the study-cluster HTML from GitHub Pages as a static origin

## Status

Accepted
<!-- Accepted at the html-site-hosting PLAN-OK gate, 2026-08-26 (owner;
F1–F3 ratified as drafted). First ADR of application/html-site; this
series is distinct from application/mobile-test-automation (ADRs
0001–0017 there) and tooling/sdd-roles. -->

## Context

Authored HTML in this repo is readable on `atlas-docs` (`127.0.0.1:8123`) or
`file://`, but a reader cannot be sent a URL. Prep-guide C4 had locked
publication to “repo file only.” Spec `html-site-hosting` overrides that for
**v3 + atlas** only (v1/v2 stay repo-only).

The documents’ integration contract is **relative URLs**. v3’s footer is
`href="claude-architect-m1-atlas.html"`; that works only if the two files are
siblings on the origin. A SPA, a slug-flattening rewrite, or copying one file
out of tree breaks that contract.

Alternatives considered:

- **No public origin** (brainstorm D3) — keeps prep-guide C4. Does not meet
  “a URL a reader can be sent.”
- **Vercel static** (clarify C1 option B) — extra vendor for three static
  files. Preview deploys are unused. The GitHub repo is already public.
- **Serve all of `docs/`** (brainstorm D1) — relative links work, but the
  origin leaks research mocks, eval HTML, and v1/v2 provenance.
- **React/hash catalog** (brainstorm D4) — new npm stack; does not fix
  in-document relative `href`s.

## Decision

We will publish a **static GitHub Pages origin** whose URL space is the D2
allowlist: catalog `index.html`, `ccar-p-prep-guide-v3.html`, and
`claude-architect-m1-atlas.html` as **siblings**. Canonical HTML stays under
`docs/`; a stdlib copy script materializes the two documents into a generated
publish tree. No application framework, no SPA rewrite, no new runtime
dependency.

- **Technical:** Pages is the matching architectural style for static files
  already hosted on GitHub. Sibling layout preserves the existing relative
  graph with zero rewrite (Open/Closed on the documents). A commit-time
  manifest + closure check is the fitness function for the “shipped v3,
  forgot atlas” defect class.
- **Business:** one vendor the repo already uses; a URL that can be sent
  without a clone; allowlist honesty so research/eval HTML does not leak.

## Consequences

- **+** Relative `href`/`src` keep working; documents are copied, not wrapped
  (`file://` and `atlas-docs` stay valid for the canonicals).
- **+** Adding a cluster later is a later spec + a manifest row, not a host
  change.
- **+** No npm, no Vite, no Vercel account.
- **−** Generated copies are not on the branch, so Pages **cannot** be
  “deploy from a folder.” Deploy is GitHub Actions that runs the copy script
  then uploads the publish tree. First live URL appears after merge to
  `main` **and** a one-time repo Settings → Pages → Source = GitHub Actions.
- **−** The origin is public (the repo is public). Accepted at clarify C3
  (collapsed into C1).
- **−** Prep-guide C4 is overridden for v3 + atlas only; that override is
  this ADR plus the spec plus one architecture-log line.
- What the losing options offered: Vercel would have given preview URLs we
  do not need; D1 would have skipped the copy step at the cost of leaking
  `docs/`; D3 would have avoided a new service and left the actual need
  unmet.

## Compliance

Automated — `python3 apps/html-site/publish.py` (copy + link-closure check)
is the fitness function: non-zero exit if a shipped HTML’s relative `href`/
`src` is missing from the publish tree, or if a published copy is not
byte-identical to its `docs/` canonical. GitHub Actions runs that script
before uploading the Pages artifact, so a dangling companion link cannot
reach the origin. Manual — architecture log records that a public origin
exists (spec FR-7).

## Notes

Author: sdd-spec plan stage (Ask-first: new public HTTP service)
Approved by / date: owner, 2026-08-26 (PLAN-OK — F1–F3 ratified as drafted)
Superseded date:
Last modified / by / what: 2026-08-26 / PLAN-OK / Status Proposed → Accepted
