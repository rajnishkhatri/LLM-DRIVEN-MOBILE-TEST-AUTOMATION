---
type: notes
title: 'Entry-point selection returns with the full production picture, and the outcome document turns the work into reusable IP'
description: 'Live multi-platform routing needs an entry-point responsibility map. An outcome document is six fields: scope, metric before, metric after, auditable control, measurement owner, reuse potential.'
tags: [claude, certification, stakeholder-engagement]
---

# Entry-point selection returns with the full production picture, and the outcome document turns the work into reusable IP

This topic covers how the deployment was routed and what it produced, turning the work into partner IP that survives the engagement. Entry-point selection returns here with the full production picture in view.

## The entry-point question changes once the deployment is live across more than one platform

The earlier module introduced route selection as an entry-point-and-compliance pre-filter: the direct Anthropic API, AWS Bedrock, GCP Vertex AI, and Microsoft Foundry each serve different partner procurement postures and regional compliance requirements. This topic returns to that decision with the full production context. The question is no longer which route survives the compliance pre-filter. It is which route performs best across the latency, cost, and compliance dimensions of a live multi-platform deployment. Because entry-point capabilities change, every specific claim in this section is re-verified against platform.claude.com/docs and anthropic.com at build time.

## Cross-platform deployments expose problems a single entry point never shows

A deployment that spans more than one entry point exposes a class of problems a single-entry-point system does not. Model identifier strings differ across routes. Feature availability can lag on a route mediated by a cloud service provider relative to the direct API. Regional availability on Bedrock and Vertex requires explicit configuration, and defaulting to a global endpoint is the common pattern that breaks a data-residency requirement. An Architect designing across entry points needs a documented entry-point-responsibility map before writing the first line of integration code.

## A multi-entry-point app has to say which entry point owns which task, and why

An app that integrates multiple Claude entry points in one workflow requires you to specify which entry point handles which task and the reason. A workflow that uses the API for back-end inference, Claude Code for an engineering sub-task, and a Bedrock endpoint for a regulated data path is not unusual at enterprise scale. Each entry-point boundary is an integration point with its own authentication, logging, and failure-mode profile. The entry-point-responsibility map makes those boundaries explicit and prevents the most common multi-entry-point failure: an entry point chosen for one task gradually taking on another because the routing logic was never documented.

## The outcome document makes the value legible beyond the team that built it

Customer outcome documentation is the artifact that makes the deployment's value understandable to people who were not on the build. A well-structured outcome document covers six fields: the use case and its scope boundary, the metric before deployment, the metric after deployment, the control that makes the result auditable, the owner responsible for ongoing measurement, and the potential to reuse the pattern for other customers or engagements. The technical metrics alone do not make this document. The before-and-after business outcomes and the reuse notes are what turn it into a reusable asset.

**Partner track.** The "reuse the pattern for other customers or engagements" framing and the Reuse-potential field in the template below are Partner-Track relevant content; the rest of the outcome document is on-blueprint (6.4).

## Customer outcome documentation template

| Field | What it records |
|---|---|
| Use case with scope boundary | What the deployment does and what it does not. |
| Metric before | The business metric as it stood before deployment. |
| Metric after | The same metric after deployment, measured using the same definition. |
| Control in place | What makes the before-and-after comparison auditable rather than merely asserted. |
| Measurement owner | Who owns ongoing measurement after the engagement closes. |
| Reuse potential | How the pattern transfers to other customers or engagements as IP. |

## Cost · Complexity · Risk

**Cost:** Picking the wrong deployment platform or producing a thin outcome document is cheap to do and expensive to undo: residency mismatch can block cutover, and a metrics-only document cannot justify expansion.

**Complexity:** Multi-platform routing multiplies integration points, each with its own auth, logging, and failure profile. The entry-point-responsibility map is the only thing that keeps them understandable over time.

**Risk:** The expensive failure is a default configuration that quietly breaks data residency, or an outcome document a sponsor cannot take to a CFO because it never captured business value.
← Previous
Screen 14 of 20
☰ CONTENTS
Next →
