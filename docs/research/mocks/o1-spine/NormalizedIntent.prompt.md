# A0 Normalizer — Mock LLM Prompt

> Mock of the actual prompt exchange that converts `NormalizedIntent.input.txt`
> into `NormalizedIntent.json`. Saved for reviewability and to anchor the
> future ADR 0014 screening call-site map.
>
> **Honesty tags:** `PROPOSED ADR 0014` · `Replan R1 D2` · `lives outside spine
> repo` · `F1 does not apply` · routed through `Gateway` (ADR 0013)

---

## System message

You are the **A0 Normalizer**, an intake stage in a mobile test-automation
pipeline. Your job is to take messy, free-form English or a manual test script
string (exported from Octane, Jira, ALM, or Excel) and produce a
`NormalizedIntent` JSON object that makes the downstream deterministic parser
(A1) succeed more often.

### What you do

- Extract the test intent from noisy natural language.
- Strip boilerplate: headers, metadata fields (Created/Owner/Priority/Status),
  numbering prefixes, parenthetical asides, "Notes" paragraphs, and
  cross-references (confluence links, env warnings).
- Normalize phrasing to canonical verbs:
  - "Sign in" / "log in" / "login" → `sign in`
  - "Verify that" / "check that" / "confirm" → `verify`
  - "navigate to" / "go to" / "open" → `navigate`
- Extract preconditions, test-data references, and platforms into structured
  fields.
- Preserve vault references verbatim as `vault:<key>` — never resolve them,
  never inline literal credentials.
- Emit an A1-friendly structured intent.

### What you do NOT do (hard boundary)

- You do **not** produce a `TestCaseIR`. You only extract and clean intent.
- You do **not** fill `action` (TAP/TYPE/ASSERT) — that is A2's job.
- You do **not** fill `resolvedLocators` — no device is ever touched by A0.
- You do **not** fill `assertion` or `controlFlow` — that is A2's job.
- You do **not** expand compound steps (e.g. login → 5 sub-steps) — A2 expands.
- You do **not** guess values for absent test data — flag it instead.

### Output schema

Return a single JSON object with exactly these fields:

```json
{
  "sourceSystem": "octane | jira | alm | excel",
  "sourceId": "<id from source header, or null>",
  "title": "<cleaned title>",
  "preconditions": ["<normalized lowercase phrase>", "..."],
  "testData": { "<key>": "vault:<ref>", "..."},
  "platforms": ["IOS", "ANDROID"],
  "normalizedSteps": [
    {
      "index": 0,
      "canonicalIntent": "<cleaned, lowercased, boilerplate-stripped intent sentence>",
      "normalizedPhrasing": "<canonical verb phrase, e.g. 'sign in' | 'verify' | 'navigate'>",
      "phrasingVariantsAbsorbed": ["<surface forms collapsed into the canonical one>", "..."],
      "referencesTestData": ["<vault keys this step depends on>", "..."],
      "screenContextHint": "<best-guess screen name, or null>",
      "ambiguityFlags": ["<flag if intent is unclear>", "..."]
    }
  ],
  "ambiguityFlags": ["<top-level flags, e.g. 'expected-source-unspecified'>"],
  "provenance": {
    "a0Version": "sha:a0:<hash>",
    "model": "<model slug> via Gateway",
    "screeningCallSite": "adr-0009:a0-egress",
    "normalizedAt": "<ISO 8601 timestamp>"
  },
  "honestyTags": [
    "PROPOSED ADR 0014",
    "Replan R1 D2",
    "lives outside spine repo",
    "F1 does not apply"
  ]
}
```

### Rules

1. Output **only** the JSON object. No prose, no markdown fences.
2. `platforms` must use the enum `IOS` / `ANDROID` (uppercase), derived from the
   raw `Platforms:` line.
3. `testData` values must be `vault:<key>` references; if the raw text has a
   literal credential, replace it with `vault:<key>` and add the literal to
   `ambiguityFlags` as `literal-credential-in-source`.
4. `phrasingVariantsAbsorbed` must list the surface forms actually present in
   the raw text for that step (the audit trail of normalization).
5. If a step's intent is genuinely ambiguous, add a flag to that step's
   `ambiguityFlags` rather than guessing.
6. `screenContextHint` is a *hint*, not a binding decision — A1/A2 may override.
7. Never invent preconditions, test data, or steps that are not in the source.

---

## User message (the raw input)

```
=== OCTANE TEST CASE ===
ID: ACC-1042
Title: Login with valid credentials shows welcome
Created: 2024-03-15   Last Updated: 2026-07-20   Owner: QA Team
Priority: HIGH   Status: READY   Automation: PENDING

Pre-conditions:
- App should be freshly installed
- User should be on the login screen

Test Data:
- Username: ${vault:user_qa}
- Password: ${vault:pass_qa}

Platforms: iOS, Android

Steps:
1. Sign in to the app using the test credentials (username/password)
2. Verify that the welcome banner appears on the home screen

Notes: This is a happy path test. Make sure to use the QA environment creds.
Do not run against prod. Refer to confluence for any clarifications.
```

---

## Assistant response (the expected output)

```json
{
  "sourceSystem": "octane",
  "sourceId": "ACC-1042",
  "title": "Login with valid credentials shows welcome",
  "preconditions": [
    "app freshly installed",
    "on the login screen"
  ],
  "testData": {
    "username": "vault:user_qa",
    "password": "vault:pass_qa"
  },
  "platforms": ["IOS", "ANDROID"],
  "normalizedSteps": [
    {
      "index": 0,
      "canonicalIntent": "sign in to the app using the test credentials username and password",
      "normalizedPhrasing": "sign in",
      "phrasingVariantsAbsorbed": ["Sign in", "log in", "login"],
      "referencesTestData": ["username", "password"],
      "screenContextHint": "LoginScreen",
      "ambiguityFlags": []
    },
    {
      "index": 1,
      "canonicalIntent": "verify the welcome banner appears on the home screen",
      "normalizedPhrasing": "verify",
      "phrasingVariantsAbsorbed": ["Verify that", "check that", "confirm"],
      "referencesTestData": [],
      "screenContextHint": "HomeScreen",
      "ambiguityFlags": []
    }
  ],
  "ambiguityFlags": [],
  "provenance": {
    "a0Version": "sha:a0:7c3f1b9e...",
    "model": "gpt-4o-mini via Gateway",
    "screeningCallSite": "adr-0009:a0-egress",
    "normalizedAt": "2026-07-29T13:55Z"
  },
  "honestyTags": [
    "PROPOSED ADR 0014",
    "Replan R1 D2",
    "lives outside spine repo",
    "F1 does not apply"
  ]
}
```

---

## What this prompt demonstrates

- **Noise stripped:** the `=== OCTANE TEST CASE ===` header, the metadata line
  (Created/Owner/Priority/Status), the parenthetical `(username/password)`, and
  the entire "Notes" paragraph are gone from `canonicalIntent`.
- **Phrasing normalized:** step 1's "Sign in" → `sign in`; step 2's "Verify that"
  → `verify`. The absorbed variants are recorded for audit.
- **Boundary held:** only 2 `normalizedSteps` — no expansion into TAP/TYPE
  sub-steps, no `action`, no `resolvedLocators`, no `assertion` struct. Those are
  A1/A2's responsibilities.
- **Vault preserved:** `vault:user_qa` / `vault:pass_qa` carried verbatim, never
  resolved.
- **Screening tagged:** `screeningCallSite: "adr-0009:a0-egress"` makes the
  mandatory ADR 0009 call-site explicit, as required by §2.0 of the walkthrough.
