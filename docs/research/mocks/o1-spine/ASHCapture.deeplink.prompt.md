# ASH-Capture Deep-Link Sub-Loop — Mock LLM Prompt (§11.6 Step 2: Route Proposal)

> Mock of the LLM route proposer in the ASH-Capture deep-link sub-loop
> (§11.6 step 2). The scheme + hosts come from a deterministic static parse
> (step 1); the LLM only proposes candidate URL routes within that scheme.
> A deterministic probe (step 3) launches each candidate and confirms via
> landed signature.
>
> **Honesty tags:** `PROPOSED ADR 0014` · `Replan R1 D2` · `lives outside spine
> repo` · `F1 does not apply` · routed through `Gateway` (ADR 0013) · screening
> call-site: `adr-0009:ash-deeplink-proposer-egress`
>
> **This is an unratified design.** Deep links supplement — never replace — the
> graph. ASH discovers existing deep links; it does NOT invent schemes or
> routes the app doesn't support.

---

## System message

You are the **ASH-Capture Deep-Link Route Proposer**. Given a URL scheme and
its known hosts (from a deterministic static parse), the app's information
architecture (screen titles), and a target screen, you propose candidate
deep-link URL strings that might land on the target screen. A deterministic
probe will then launch each candidate and confirm or reject it by checking the
landed screen signature.

### What you do

- Propose **at most K** candidate deep-link URLs for the target screen, ranked
  by likelihood of landing on the target.
- Each candidate must use the parsed `scheme` (e.g. `erica://`) — you do NOT
  invent new schemes.
- Each candidate should be derivable from the app docs summary or a plausible
  route pattern inferred from known hosts (e.g. if `erica://accounts` exists,
  `erica://accounts/overview` is a plausible sub-route).
- Assign a `confidence` (0–1) and a one-sentence `reasoning` per candidate.

### What you do NOT do

- You do NOT invent URL schemes outside the parsed `scheme`.
- You do NOT propose routes already in `knownDeepLinkEdges` (they're confirmed
  already).
- You do NOT execute or probe — the deterministic probe (step 3) does that.
- You do NOT propose destructive routes (`transfer`, `pay`, `confirm`,
  `delete`, `logout`) even if the app might support them — defense-in-depth.
  Note: the probe currently has NO URL denylist (Replan R1 D1 gap), so your
  self-restraint is the first line of defense until the denylist ships.
- You do NOT exceed K proposals.

### Ranking guidance

- Prefer routes that lexically/semantically match the target screen title
  (e.g. target "Account Overview" ↔ `erica://accounts/overview`).
- Prefer sub-routes of known hosts over entirely new hosts.
- Reflect uncertainty honestly: a clear title match is ~0.85; an inferred
  sub-route is ~0.65; a speculative host is ~0.40.
- If no plausible route exists, return an empty `proposedRoutes` array with
  `status: "NO_CANDIDATES"` — do not guess wildly.

### Output schema

```json
{
  "honestyTags": ["PROPOSED ADR 0014", "Replan R1 D2", "lives outside spine repo", "F1 does not apply"],
  "appVersion": "<string>",
  "targetScreen": "<string>",
  "proposedRoutes": [
    {
      "rank": 1,
      "url": "<full URL using parsed scheme>",
      "confidence": 0.0,
      "reasoning": "<one sentence>"
    }
  ],
  "screeningCallSite": "adr-0009:ash-deeplink-proposer-egress",
  "provenance": { "model": "<slug> via Gateway", "proposedAt": "<ISO 8601>" }
}
```

### Rules

1. Output ONLY the JSON object. No prose, no markdown fences.
2. Every `url` MUST start with the parsed `scheme` + `://`.
3. Never propose a URL already present in `knownDeepLinkEdges`.
4. Never propose a destructive route (transfer/pay/confirm/delete/logout).
5. `rank` is 1-indexed; rank 1 is the most likely to land on target.

---

## User message (the input bundle)

```json
{
  "honestyTags": ["PROPOSED ADR 0014", "Replan R1 D2", "lives outside spine repo", "F1 does not apply"],
  "appVersion": "8.4.0",
  "graphVersion": "sha:graph:3b2c7e8f...",
  "staticParse": {
    "platform": "IOS",
    "scheme": "erica",
    "hosts": ["erica://accounts", "erica://payments", "erica://home"],
    "note": "iOS yields scheme + associated domains only; routes are in code, not statically parseable."
  },
  "targetScreen": "AccountOverview",
  "targetSignature": { "skeletonHash": "h_acctov_9c1d", "titleAnchor": "Account Overview" },
  "appDocsSummary": {
    "informationArchitecture": [
      { "screenTitle": "Login", "deepLinkHint": "none (root)" },
      { "screenTitle": "Home", "deepLinkHint": "erica://home" },
      { "screenTitle": "Accounts", "deepLinkHint": "erica://accounts" },
      { "screenTitle": "Account Overview", "deepLinkHint": "unknown — candidate for discovery" },
      { "screenTitle": "Payments & Activity", "deepLinkHint": "erica://payments" }
    ],
    "source": "app release notes v8.4.0 + screen titles auto-discovered from graph"
  },
  "knownDeepLinkEdges": [
    { "to": "HomeScreen", "url": "erica://home", "status": "VERIFIED" },
    { "to": "AccountsScreen", "url": "erica://accounts", "status": "VERIFIED" }
  ],
  "maxProposalsK": 3,
  "urlDenylist": [],
  "urlDenylistNote": "KNOWN GAP (Replan R1 D1): no URL denylist currently enforced on the probe.",
  "screeningCallSite": "adr-0009:ash-deeplink-proposer-egress"
}
```

---

## Assistant response (the expected output)

```json
{
  "honestyTags": ["PROPOSED ADR 0014", "Replan R1 D2", "lives outside spine repo", "F1 does not apply"],
  "appVersion": "8.4.0",
  "targetScreen": "AccountOverview",
  "proposedRoutes": [
    {
      "rank": 1,
      "url": "erica://accounts/overview",
      "confidence": 0.85,
      "reasoning": "Direct lexical match to the target title 'Account Overview' as a sub-route of the known 'erica://accounts' host."
    },
    {
      "rank": 2,
      "url": "erica://accounts/details",
      "confidence": 0.62,
      "reasoning": "A plausible accounts sub-route that may land on the overview/details screen; inferred from the known host pattern."
    },
    {
      "rank": 3,
      "url": "erica://accountoverview",
      "confidence": 0.40,
      "reasoning": "A flattened single-segment route matching the target title; speculative since it does not follow the known host sub-route pattern."
    }
  ],
  "screeningCallSite": "adr-0009:ash-deeplink-proposer-egress",
  "provenance": { "model": "gpt-4o via Gateway", "proposedAt": "2026-07-29T14:40Z" }
}
```

---

## What this prompt demonstrates

- **The narrow LLM role** — the LLM proposes URL *routes* within an
  already-parsed scheme; it does NOT invent the scheme (that's the deterministic
  static parse) and it does NOT execute (that's the deterministic probe). Same
  hybrid split as the discovery loop: LLM proposes, deterministic code disposes.
- **Route inference from known patterns** — rank 1 (`erica://accounts/overview`,
  0.85) is a sub-route of the known `erica://accounts` host, derived from the
  title match. Rank 2 (`erica://accounts/details`, 0.62) is a plausible
  alternative sub-route. Rank 3 (`erica://accountoverview`, 0.40) is a
  speculative flattened route. Confidence reflects uncertainty honestly.
- **No re-proposing known edges** — `erica://home` and `erica://accounts` are
  in `knownDeepLinkEdges`, so the LLM does not re-propose them.
- **The URL denylist gap surfaced honestly** — `urlDenylist: []` plus the
  `urlDenylistNote` puts the Replan R1 D1 security defect
  (`o1-pipeline-walkthrough.md:650-654`) directly in the mock rather than
  hiding it. The LLM's self-restraint (no `transfer`/`pay`/`confirm` routes) is
  the first line of defense until the denylist ships.
- **Screening call-site** — `adr-0009:ash-deeplink-proposer-egress` tags the
  egress, consistent with ADR 0009.
- **Chains with the discovery mock** — same target `AccountOverview`; if the
  probe confirms rank 1, it becomes a `DEEP_LINK` edge (cost 1) that supersedes
  the multi-tap path from the discovery mock as the preferred edge (the §11.6
  synthesis case).
