# Execution Plan — ACC-2087

> **E2 evidence artifact.** Deterministically rendered from the committed IR
> (`irDigest sha:ir:2087:d41c9a...`). Attached to the ReplayReport as **evidence,
> never as the audit pin** — the pin is the `irDigest` this plan is derived from.
> A compliance officer reads this; it cannot drift from what ran.

irDigest: `sha:ir:2087:d41c9a...` · interpreter: `sha:interp:9f0c22...` · test: ACC-2087

```
 0. TAP    "username field"       → ACCESSIBILITY_ID=usernameField           (budget 7000ms, then WAIT_FOR_IDLE)
 1. TYPE   ${testData.username}   → usernameField                            (budget 7000ms)
 2. TYPE   ${testData.password}   → passwordField                            (budget 7000ms)
 3. TAP    "Sign In button"       → loginButton                              (budget 7000ms, then WAIT_FOR_IDLE)
 4. ASSERT home dashboard present → homeDashboard  [ELEMENT_PRESENT]         (budget 8000ms)
 5. TAP    "Pay & Transfers"      → payTransfersTab                          (budget 7000ms, then WAIT_FOR_IDLE)
 6. TAP    "Zelle"                → zelleMenuItem                            (budget 7000ms, then WAIT_FOR_IDLE)
 7. TAP    "recipient Alex Rivera"→ recipient_AlexRivera                     (budget 7000ms, then WAIT_FOR_IDLE)
                                    fallback: XPATH //XCUIElementTypeCell[@name='recipient_AlexRivera'] (committed, order fixed)
 8. TYPE   ${testData.amount}     → amountField                              (budget 7000ms)
 9. TAP    "Send"                 → zelleSendButton                          (budget 7000ms, then WAIT_FOR_IDLE)
10. ASSERT confirmation           → zelleConfirmationBanner                  (budget 10000ms)
           [TEXT_EQUALS "$25.00 sent to Alex Rivera"]

healPolicy = NONE for every step — a locator miss is a red build, never a runtime repair.
```

**Screen path:** LoginScreen → HomeScreen → PayTransfersScreen → ZelleScreen → ZelleSendScreen → ZelleConfirmationScreen.
