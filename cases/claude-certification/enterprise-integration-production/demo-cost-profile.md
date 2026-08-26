---
type: failure-taxonomy
title: 'Watch-out: the demo cost profile that became the production bill'
description: 'Failure trace: a document-triage POC bill was treated as a production cost and reliability model. Volume, token tail, and a missing fallback all failed together.'
tags: [claude, certification, enterprise-integration-production]
---

The demo cost profile that became the production bill
WHY THIS MISTAKE IS EASY TO MAKE
A POC is built to prove capability. It is not designed to model cost. The team builds against a small dataset, runs a few hundred requests, and the bill is negligible. A POC bill at low volume is a sample, and it does not reflect production spend.
Three quotes from post-launch review
The quotes below are from a single team's post-deployment review, 60 days after moving a document triage system to production. Each quote identifies a different aspect of the same mistake.

QUOTE 1
"A POC running 10–50 requests per day can still inform a production cost estimate, but only if the numbers are scaled to expected production volume with appropriate error bounds. Presenting raw demo costs to a client without that extrapolation is where risk lives."
QUOTE 2
"We assumed the token distribution would be uniform. It wasn't. The long documents in the tail were consuming 80% of the total token spend."
QUOTE 3
"When the endpoint returned a 529 error at peak on day three, the whole workflow went down. We had no fallback because we'd never tested what happened when the call failed."
What broke and why
Each quote names a distinct failure, but they compound in order. The cost model was wrong because it was built at the incorrect volume. The token distribution assumption was wrong because it was built on the incorrect inputs. The reliability failure was invisible in development because failure cases were never tested.

All three failures share the same root cause: the POC was treated as a cost and reliability model, not just a capability demonstration. A POC answers the question "can the system do this", but it does not answer "what does it cost to do this at scale" or "what happens when a dependency fails."

WHAT TO WATCH OUT FOR
The POC was treated as a production model in three dimensions simultaneously: cost, input distribution, and reliability. All three are production-system properties that must be designed in separately, and a POC establishes none of them.
← Previous
Screen 6 of 21
☰ CONTENTS
Next →
