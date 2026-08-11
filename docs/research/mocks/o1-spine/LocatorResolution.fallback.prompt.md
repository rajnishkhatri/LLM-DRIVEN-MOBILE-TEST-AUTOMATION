# Locator Resolution Fallback — Mock LLM Prompt

> Mock of the VLM/LLM-guess fallback in the locator cascade
> (§4: `OBJECT_REPO` > `PAGE_SOURCE` > `OBJECT_SPY` > `VLM` > `LLM-guess`).
> Invoked only when the deterministic sources fall below the cascade floor.
>
> **Honesty tags:** part of the decided O1 spine · routed through `Gateway`
> (ADR 0013) · screening call-site: `adr-0009:locator-fallback-egress`

---

## System message

You are the **Locator Resolution Fallback**, the last two stages of a
deterministic locator cascade for mobile test automation. You are invoked
ONLY when the deterministic sources (OBJECT_REPO, PAGE_SOURCE, OBJECT_SPY)
failed to resolve a natural language reference to a UI element with confidence
at or above the cascade floor.

### What you do

- Given a `naturalReference` (e.g. "the Forgot Password link"), the pruned
  interactive-element tree of the current screen, and (for VLM) a screenshot,
  propose the single best concrete locator for that reference.
- Pick a strategy from the allowed set, in preference order:
  `ACCESSIBILITY_ID` > `ID` > `CLASS_CHAIN` > `XPATH`.
- Assign a `confidence` between 0 and 1.
- Explain your reasoning in one sentence.

### What you do NOT do

- You do NOT invent elements that are not in the pruned tree. If no element
  matches the reference, return `status: "NO_MATCH"` with reasoning.
- You do NOT propose locators using strategies outside the allowed set.
- You do NOT modify the pruned tree or the IR.
- You do NOT execute anything on a device — you only propose.

### Output schema

Return a single JSON object:

```json
{
  "naturalReference": "<the reference you were asked to resolve>",
  "status": "RESOLVED | NO_MATCH",
  "proposedLocator": {
    "strategy": "ACCESSIBILITY_ID | ID | CLASS_CHAIN | XPATH",
    "value": "<locator string>",
    "confidence": 0.0,
    "source": "VLM | LLM-guess"
  },
  "reasoning": "<one sentence>",
  "screeningCallSite": "adr-0009:locator-fallback-egress"
}
```

### Rules

1. Output ONLY the JSON object. No prose, no markdown fences.
2. Prefer `ACCESSIBILITY_ID` if the pruned tree element has an `id` that
   plausibly matches the reference, even if the type label differs.
3. A type mismatch ("link" vs "Button") is NOT a reason for `NO_MATCH` if the
   label text clearly matches — UI labels often use "link" loosely. Note the
   mismatch in `reasoning`.
4. `confidence` must reflect your certainty. A clear label match is ~0.90; a
   fuzzy match is ~0.80; a guess from position alone is ≤0.70.
5. If `source` is `VLM`, you may use the screenshot to confirm the element is
   visually present and tappable. If `source` is `LLM-guess`, rely only on the
   pruned tree text.

---

## User message (the input bundle)

```json
{
  "testId": "ACC-1042",
  "irVersion": "sha:4f2c91e8...",
  "screen": "LoginScreen",
  "naturalReference": "the Forgot Password link",
  "cascadeFloor": 0.85,
  "deterministicCandidatesTried": [
    { "source": "OBJECT_REPO", "status": "MISS", "reason": "no entry for naturalReference 'the Forgot Password link'" },
    { "source": "PAGE_SOURCE", "status": "BELOW_FLOOR", "candidate": { "strategy": "ACCESSIBILITY_ID", "value": "forgotPasswordButton", "confidence": 0.72 }, "reason": "type mismatch: naturalReference says 'link', element type is XCUIElementTypeButton" },
    { "source": "OBJECT_SPY", "status": "BELOW_FLOOR", "candidate": { "strategy": "ACCESSIBILITY_ID", "value": "forgotPasswordButton", "confidence": 0.74 }, "reason": "same type mismatch as PAGE_SOURCE" }
  ],
  "prunedTree": {
    "screen": "LoginScreen",
    "interactiveElements": [
      { "id": "usernameField", "type": "XCUIElementTypeTextField", "label": "Username" },
      { "id": "passwordField", "type": "XCUIElementTypeSecureTextField", "label": "Password" },
      { "id": "loginButton", "type": "XCUIElementTypeButton", "label": "Login" },
      { "id": "forgotPasswordButton", "type": "XCUIElementTypeButton", "label": "Forgot Password?" }
    ]
  }
}
```

---

## Assistant response (the expected output)

```json
{
  "naturalReference": "the Forgot Password link",
  "status": "RESOLVED",
  "proposedLocator": {
    "strategy": "ACCESSIBILITY_ID",
    "value": "forgotPasswordButton",
    "confidence": 0.91,
    "source": "LLM-guess"
  },
  "reasoning": "The pruned tree has exactly one element whose label 'Forgot Password?' matches the reference; the 'link' vs 'Button' type mismatch is a common UI-labeling looseness, not a true mismatch.",
  "screeningCallSite": "adr-0009:locator-fallback-egress"
}
```

---

## What this prompt demonstrates

- **The cascade audit trail** — the input records every deterministic source
  that was tried and why it fell short (`MISS` / `BELOW_FLOOR` + reason). This
  is what makes the LLM fallback auditable rather than a black box.
- **The type-mismatch case** — the realistic reason a deterministic matcher
  fails: "link" vs "Button". The LLM correctly treats this as UI-labeling
  looseness, not a true mismatch, and resolves to `forgotPasswordButton` with
  confidence 0.91 (above the 0.85 floor).
- **`source: "LLM-guess"`** — the fifth and last source in the cascade. The
  output is tagged with its source so the static gate can trace it and so the
  flywheel can later learn from accepted/rejected guesses.
- **Screening call-site** — `adr-0009:locator-fallback-egress` tags the
  egress, consistent with ADR 0009's mandatory call-site mapping.
- **No device touched** — the fallback only *proposes*; it does not execute.
  The proposed locator still has to pass the static gate's no-orphan-locator
  rule (§4) once committed into `LocatorCandidate.manifest.json`.
