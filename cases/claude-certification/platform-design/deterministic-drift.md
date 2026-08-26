---
type: failure-taxonomy
title: 'Watch-out: when the deterministic check quietly drifted'
description: 'Failure trace: a claims-routing threshold that had to be right every time was folded into Claude. Forty-one misroutes surfaced in an audit, not in monitoring.'
tags: [claude, certification, platform-design, failure-taxonomy]
---

When the deterministic check quietly drifted
SETUP HOOK
When the team is excited about Claude, putting a deterministic check inside the model provides a cleaner design: one component, fewer integrations, and easier to demo. It is the type of move a senior Architect makes when a team is moving fast and the rule looks "easy enough" for the model.
A scoping call, transcribed

The conversation below is a real scoping exchange. Two people make a reasonable call to simplify a design, and in the moment it looks like a clean win. What they've actually done is hand a deterministic business rule, one that has to be right every time, to the model, a probabilistic system, which is right most of the time but not all of the time. That gap didn't surface during development, instead it surfaced three months later, in an audit.

This section explores a failure mode where the goal is to show you what went wrong so you can recognize the pattern early and make a different decision.

Partner: "We have a rule that any claim over £5,000 needs a senior adjuster. Today we're doing an SQL check against the claims table. Can Claude handle that instead?"
Architect: "We can prompt Claude to extract the amount and route accordingly if it's over 5K. That keeps it in one step instead of reaching out to a separate system to check, so it's way simpler."
Partner: "Perfect, that works for me."
[Three months later, in production]

OF 14,000 CLAIMS PROCESSED, 41 ROUTED INCORRECTLY
All 41 shared the same problem. The amount was not written as a clean number. It was tucked inside a sentence, like 'damages estimated around five thousand pounds.' The model treated 'around five thousand' as a loose estimate rather than a figure that should trigger senior review, so those claims went to standard handling. The rule was precise. The information it had to work with was not, and the model followed the letter of the rule instead of its intent.
What broke: a deterministic rule handed to a probabilistic system

The threshold didn't change, but what enforced the rule did. A deterministic rule that needs to be correct every time was folded into Claude, which is right most of the time. The gap between them is where the 41 misroutes lived.

The team never built a set of test cases to check the routing, because they had treated routing as something the model would just handle rather than a rule the business was counting on. That difference is the crux of the problem. A rule the business is counting on must be tested, watched, and owned by a human. Something you assume the model will handle is left alone until it breaks.

The misroutes were caught by an audit, not by the system's own monitoring. The kind of logging that would have caught a broken SQL check does not record the choices a model makes inside a single request, so nothing flagged the drift. The failure remained invisible until someone went looking for it.

WHY THIS BROKE
A rule that needs to be right every time was handed to a system that is right most of the time. That tradeoff is easy to miss during scoping because the model handles the clean cases correctly, and clean cases are what you see in demos and early testing. The cost of "most of the time" doesn't reveal itself until you audit and by then the partner is calling.
← Prev
Screen 8 of 34
☰ CONTENTS
Next →