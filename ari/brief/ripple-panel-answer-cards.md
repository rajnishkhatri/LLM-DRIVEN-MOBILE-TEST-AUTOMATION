# Panel Answer Cards — Ripple Craft Exercise
Pattern: say the answer sentence first. Then give 2 or 3 anchors. Stop. Let them pull.
Memorize anchors, never prose. One number per card, no more.
Language rule: "I" for decisions. "We" for execution.

---

## CARD 1 — "What's the actual problem?" (cold open, 5 min, no notes)

**Answer sentence:**
"The problem is not a missing chat window. The problem is that the customer has to know where the answer lives. Three systems, three behaviors, and now four teams building four more front doors. Dana is really asking for one governed front door."

**Anchors:**
1. **Fragmentation.** The user carries the routing burden today. Ari moves that burden into the product.
2. **Governance at the door.** Before any answer: who is asking, what are they allowed to see, what do they actually mean. Intent, entitlement, ambiguity.
3. **Trust is the product.** These are treasury users. A wrong number is worse than no answer. So numbers stay exact and every answer shows where it came from.
4. **Phase two already started.** Creating a ticket is a write action. So the approval and audit pattern gets built now, not later.

**One number:** none. Keep the cold open clean.

---

## CARD 2 — "What answer were you expecting to this question?"
(asked about your two sharpest Dana questions)

**Pattern, not prose:**
"I expected [answer A]. I wrote the question because the design forks on it."

**Rule:** every question in the brief must carry a fork. If a question has no fork behind it, cut it from the brief before Tuesday.

**Example shape:**
"I asked which request types make up the top 80% of tickets. I expected how-to questions to dominate. If yes, the help center route earns the most test cases. If it's bank file failures, deflection is the wrong goal and ticket quality is the right one."

---

## CARD 3 — "What would you have done differently in each branch?"

**Pattern:**
"Branch one: [design stays, scope X]. Branch two: [one component changes, name it]."

**Rule:** the branches change scope or one component. They never change the architecture. That is the point to land: "The front door design survives both answers. That's why it's the design."

---

## CARD 4 — "Which of the three backends worried you most, and why?"

**Answer sentence:**
"None of the three alone. They're integration points. What worries me is the front door: did we understand the question, is this user allowed to see this, and what happens when a wrong number reaches a treasury customer."

**Anchors:**
1. **The worry is governance, not plumbing.** Intent, entitlement, ambiguity, in that order.
2. **If you force me to pick one: Omni.** Numbers must be exact. Models writing raw SQL solve about 10% of real enterprise warehouse tasks on Spider 2.0. That's why Ari never writes SQL. It asks Omni's governed semantic layer.
3. **Customer-facing consequences.** This is SaaS. Errors don't hit an intranet. They hit a treasurer.

**One number:** ~10% (GPT-4o class on Spider 2.0).

---

## CARD 5 — "Why these 10 test cases?"

**Answer sentence:**
"Each one guards a failure that costs money or trust. I picked by blast radius, not by variety."

**Anchors:**
1. **Routing cases,** including one compound question and one ambiguous one. Wrong room means wrong answer, every time.
2. **Exactness cases.** A number from Omni checked by exact match, never by a model grading a model.
3. **Boundary cases.** A user asking for data they can't see. An action needing confirmation. A backend that's down.

---

## CARD 6 — "What didn't make the cut?"

**Answer sentence:**
"Phrasing variety and happy-path repeats. Ten slots are too scarce for a tenth way to ask the same safe question."

**Anchors:**
1. Paraphrase coverage lives in the golden set behind the router, hundreds of utterances, not in the showcase ten.
2. More backends didn't make the cut. The registry makes a new backend cheap. A missed failure mode is expensive.
3. Load and latency testing is a harness job, not a test-case job.

---

## CARD 7 — "Show me where the routing decision gets made."

**Answer sentence:**
"One place. A plain function in one file. The model extracts what the user meant. The code decides where it goes."

**Anchors:**
1. **LLM proposes, code disposes.** GPT-4o fills a typed intent: type, entities, period, action. It never picks the backend.
2. **route() is pure.** Same intent in, same decision out. Every decision logged with reason codes.
3. **Same reason GSmart computes figures in deterministic code.** The decision that carries risk lives where it can be inspected.

---

## CARD 8 — "How would you test that without an LLM in the loop?"

**Answer sentence:**
"Routing is a pure function over a typed intent. So I test it like one: fixtures in, expected route out, runs in CI in milliseconds."

**Anchors:**
1. Build the intent by hand in the test. No model call needed to test the decision.
2. **Golden set** of labeled utterances with the model's extractions recorded and replayed. Routing regressions get isolated from model drift.
3. A separate scheduled job re-extracts with the live model. If extraction drifts, that alarm fires on its own, not inside my routing tests.

---

## CARD 9 — "Omni returns a number. What does the user see besides the number?"

**Answer sentence:**
"Where it came from. The filters, the period, the entity, when it was pulled, and a link to open it in Omni. Collapsed by default, one tap to expand."

**Anchors:**
1. Treasury users are auditors by temperament. An unverifiable number is a liability, not an answer.
2. This is the company's own brand. GSmart promises every output traces back to source.
3. Simple and traceable are not opposites. Provenance is folded away until wanted.

---

## CARD 10 — "Why this failure path? Why not a different one?"
(update the specifics after the build)

**Answer sentence:**
"I handled the failure that lies, not the one that crashes. A crash is honest. A stale or missing number presented as fine is not."

**Anchors:**
1. When a backend is down, Ari says so, serves what it still can, and offers a ticket. Degrade loudly, never silently.
2. The other paths aren't ignored. They're in the test list. This one got code because it has the worst blast radius per hour of build time.

---

## CARD 11 — "Where does this fall over at a thousand concurrent sessions?"

**Answer sentence:**
"Not in my code. In the token budget. A thousand sessions is roughly 500 requests a minute, and at a few thousand tokens each that's around 1.5 million tokens a minute against a default Azure quota of 300 thousand."

**Anchors:**
1. **Route first, retrieve second.** Small context per call. Never stuff all three backends into one prompt.
2. Cheap model for extraction, big model only where it earns it. Cache the common help answers.
3. Backends have their own ceilings. Atlassian throttles with 429s, and ticket creation is not idempotent. So: idempotency key, retry only reads, circuit breaker per backend.

**One number:** 300K TPM default vs ~1.5M needed.

---

## CARD 12 — "What's the first alert you'd want? What does it measure?"

**Answer sentence:**
"No-match rate on the router. It's the earliest signal that users are asking things we didn't anticipate, and it moves before accuracy visibly drops."

**Anchors:**
1. It rises with every new customer, new feature, new phrasing. It's a demand signal and a drift alarm in one metric.
2. Pages go to backend error rate and latency. Tickets go to confidence drift. No-match gets watched daily.
3. Same instinct as my production incident: the model stayed confident while being wrong. Flat confidence plus shifting traffic is the pattern to catch early.

---

## CARD 13 — "Support wants a fourth source, a public status page. How much changes on screen?"

**Answer sentence:**
"Almost nothing on screen. One new evidence card. Underneath, it's a config entry, not surgery: a registry row, twenty route phrases, one rule."

**Anchors:**
1. Sources are registry entries behind one adapter shape. The router code doesn't change.
2. **The rule is the good part:** outage intent checks status first, before a ticket. Active incident means no duplicate ticket, link the incident instead. That's deflection you can see.
3. The status page needs no auth, so it's the cheapest possible proof that the extension model works.

---

## CARD 14 — "My March forecast variance jumped and I think bank mapping is wrong. How do I fix it?"
(the question built to break your routing)

**Answer sentence:**
"Ari shouldn't answer that in one shot, and that's by design. It straddles all three backends, so the right first move is one clarifying turn, then fan out."

**Anchors:**
1. **Confirm scope first.** Which entity, which currency, which forecast version.
2. **Then evidence from all three.** Omni: variance by category plus unmapped and uncategorized counts for March. Confluence: the bank mapping article. Jira: an offered ticket, pre-filled with the evidence, behind a confirm.
3. **Ari never declares the mapping wrong.** It shows the numbers and the query. The human decides. Propose, don't decide, exactly the GSmart pattern.
4. If pushed on causes, name them plainly: unmapped new account, categorization rule missed a changed bank code, missing statement file, duplicate intraday plus end-of-day load.

---

## CARD 15 — Demo breaks: "Walk me through the change you'd make."

**Answer sentence:**
"Same discipline as any incident. Reproduce it, isolate the layer, make the smallest fix, add the regression test."

**Anchors:**
1. Isolate by layer: route decision, adapter, or model call. The logs with reason codes say which in one look.
2. Fix the smallest thing that restores the path. Resist the rewrite.
3. Say what test now exists so this never breaks silently again.
4. Tone is the test here. Calm, curious, no apology spiral.

---

## CARD 16 — "You had four hours. What would another 20 have brought?"

**Answer sentence:**
"I kept the four hours, so there's a real list. Twenty more hours go to the platform, not to more backends."

**Anchors:**
1. **Eval depth.** A routing confusion matrix and a bigger numeric golden set with exact-match checks.
2. **The disambiguation turn.** Making the clarifying question feel natural instead of robotic. That one turn protects everything downstream.
3. **Entitlements end to end.** Every backend called as the user, never as a service account, proven with a denied-access test.
4. More backends didn't make the list. The registry already makes those cheap.

---

## CARD 17 — "What questions do you have for us?"

**Ask these, about the work:**
1. "What happens to the four teams already building their own chat surfaces? Nothing in the brief says this cancels anyone's work, and that's the hardest part of shipping it."
2. "What do the real tickets look like? Which request types are the top five?"
3. "Where does GSmart end and this begin? Is Ari a GSmart surface or a sibling?"
4. "What's most broken today in how teams here ship AI features?"

**Never ask:** reporting lines, title, scope of authority. Charles can get those answered later.

---

## PRESSURE CARDS

### P1 — Dana: "Showing the query makes it look like a database tool. Customers asked for simple. I have the research and the CAB date. Why are you right?"

**Answer sentence:**
"Your research and my design don't conflict. Customers asked for one simple window, and that's what they see. They didn't ask for numbers nobody can verify."

**Anchors:**
1. Provenance is collapsed by default. The window is simple. The proof is one tap away.
2. Her own customers are treasurers. They audit for a living. And the company's own promise is that every AI output traces to source. Hiding the query breaks our own brand.
3. **Offer the test, don't win the argument:** "Show the CAB both versions. Measure which one they trust. I'll take that bet."

### P2 — "She's got customer research. You've got a hypothesis."

**Answer sentence:**
"Right, and my hypothesis is cheap to test before the CAB date. Hers was about wanting one window. Mine is about trusting the numbers in it. Different questions. Both can be true."

### P3 — Silence after your answer.

Finish the sentence. Stop. Three slow breaths. Silence is their script, not your cue to soften or backfill. If it stretches past comfort: "Happy to go deeper on any part of that."

### P4 — "What part of this was yours?" (implied all day)

"I decided [the architecture call]. We built [the pieces]." Name one decision you'd defend alone. Have it loaded before you walk in.

---

## After the build, update these:
- Card 2 and 3: fill with your two actual sharpest Dana questions and their real forks.
- Card 10: name the actual failure path you coded.
- Card 16: confirm the honest leftovers list matches what you really cut.
