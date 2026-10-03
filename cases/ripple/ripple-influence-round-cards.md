---
type: notes
title: 'Ripple influence rounds: five story cards'
description: >-
  Leadership-story cards for the influence/behavioral rounds — governing
  sentence, scene, three moves, result, lesson per card, plus the
  memorization and trigger rules.
tags: [ripple, interview, leadership, stories]
---

# Ripple Influence Rounds: Five Story Cards

Format per card: governing sentence (verbatim), scene (one sentence), three moves, result, lesson (verbatim).
Memorize only: governing sentence, three move labels, one number, lesson. Never the prose.

Trigger rule: past-tense question = STORY card. Present-tense question = STANCE (principle, three reasons, one-line example).
Bridge phrase: "Short answer first, then the story."
Language rule: "I" for decisions and judgment. "We" for execution and credit.

---

## Card 1: Influence without authority

**Governing sentence:** "A delivery squad brought a copilot that hit their committed date by bypassing the platform. I couldn't block them. So I made the reference path the cheaper way to hit their own goals, and they adopted it on the next services without me in the room."

**Scene:** Architecture Review: their sponsor had already sold a date to the steering committee, and the design bolted an LLM onto the existing eight-step dispute handoff, skipping the platform contract entirely.

**Three moves:**
1. **Sponsor: protect their number, not mine.** Two weeks of zero-based analysis showing most of the path is deterministic policy. A copilot on that flow is a faster wrong process they'd have to explain upstairs. My line: "I can build the copilot. I won't recommend it to a committee you have to defend."
2. **Delivery lead: their checklist, then their name.** Side-by-side on the ARB checklist they already had to pass: IAM, DLQ, schema, eval gate, evidence pack. Their design left a remediation backlog; the reference construct was self-service. Then I asked their lead to co-author the next version, so the path was theirs in front of their org, not Infosys IP.
3. **Compliance and security: make them the reason.** Fail-closed and the audit log are how they pass the exam. Once they prefer the golden path, ARB stops being my opinion.

**Result:** They used the path on the next services when I wasn't in the room, extended it instead of forking, and owned lifecycle after onboarding. 500+ engineers pulled the standards without sitting in my organization.

**Lesson:** "I don't win by being right. I win by making each seat's motive cheaper to satisfy on the path than off it."

**Notes:** No percentages on this card. Seat-motive table and the five closing questions stay in the follow-up arsenal, not the 90-second answer. Never open with "poorest-armed person in the room."

### Plain English (study note, not the 90-second answer)

You cannot stop the product team. You win when the safe path is the easiest way for them to hit the date they already promised.

1. **Protect their date, not your standard.** Show that the shortcut creates a problem they will have to defend upstairs.
2. **Use their checklist, then put their name on the fix.** The governed path should clear the review they already must pass, with less leftover work. Let their lead co-author it so it is their pattern.
3. **Let privacy or security be the reason.** Once those reviewers prefer the governed path, adoption is no longer your opinion.

Each person's own goal should be cheaper to satisfy on your path than off it.

**Example.** You sit on the AI council and cannot block releases. Product has already told the board that "Ask AI" ships in three weeks inside the claims app. Engineering plans to call a public model from the app and paste the full claim into the prompt.

1. **Product VP.** Their number is the three-week date. A raw call looks fast, then stalls in privacy review, or ships and they own a wrong claim answer. You tell them: "You keep the date. Ship only the 'explain this denial' step on the council path. I will not stand next to you if the board asks why full claim data left the company."
2. **Engineering lead.** Their release list already requires privacy review, a rollback, and an on-call owner. The direct call leaves them to build redaction, logging, a kill switch, and an eval set. The council SDK already has those. You ask the lead to co-write the integration note, so the product org sees their name on it.
3. **Privacy.** The SDK refuses the call when claim data is not redacted and writes an audit log. Privacy signs that path faster. The next squad uses the SDK to get the signature, without you in the room.

---

## Card 2: Alignment across stakeholders

**Governing sentence:** "Compliance said no to autonomous Zelle labels. Instead of negotiating the no, I turned it into a signed promotion rule all three groups co-own."

**Scene:** Expanding the classifier from shadow toward autonomous: compliance objected that a wrong label turning unauthorized into sender-error is a Reg E denial a model must never close, legal stood behind them on letters, ops on losing the queue without a kill switch.

**Three moves:**
1. **One sheet, not a workshop.** A confidence, blast-radius, reversibility matrix signed as the promotion rule. Example row: liability-changing labels and denials are never autonomous, human or abstain. Reversible internal scores can run in shadow.
2. **Each group co-owns a cell, with a right that needs no meeting.** Compliance: shadow can't route, fail closed. Legal: letters are templates plus claims trace, QA blocks and never edits. Ops: they own the shadow switch, and a sustained override rate demotes the node automatically.
3. **Nothing needs a meeting.** Promotion and demotion run off the sheet automatically, so the deal executes itself.

**Result:** The 2am Zelle miss proved it. Six of 80 disagreements, abstention flat. Nobody reopened the matrix or the automation rate or whether AI should exist. We ran the sheet: shadow, rollback, hold letters, failure pair into the eval set. The incident didn't test the deal. It executed it.

**Lesson:** "Alignment isn't agreement in a meeting. It's a signed rule that survives its first bad night."

**Notes:** Number options if asked: override threshold 12% over four weeks, set by ops, not me; or zero steering-committee escalations after signing. If Card 5 was already told in the same room, compress the result to one line: "When the 2am miss came, nobody reopened the deal. We ran the sheet."

### Plain English (study note, not the 90-second answer)

When compliance says no, turn that no into one signed rule that compliance, legal, and product all own. The rule still runs at 2am, with no meeting.

1. **One signed sheet.** Each row says what the model may do alone and what must stay with a human. Split by how sure the model is, how bad a wrong answer is, and whether a person can undo it.
2. **Each group owns one cell, and can use that right without a meeting.** Compliance: a shadow score cannot close the case; if the check fails, the case stays human. Legal: the customer letter is a fixed template plus the claim id; review can block it and cannot rewrite it. Product ops: they hold the off switch, and a high override rate sends the feature back to shadow by itself.
3. **The sheet runs the deal.** Promote and demote from the numbers on the sheet.

Alignment is a signed rule that still holds on the first bad night.

**Example.** You sit on the AI council and cannot force a yes. Product wants the claims classifier to stop suggesting and start closing cases. Compliance refuses, because a wrong "customer error" label can deny a valid claim. Legal will not let a model write the denial letter. Ops will not give up the queue without a kill switch.

You put one page in front of them:

- Denial and payout labels stay human. The model abstains.
- Internal priority scores may run in shadow. A person can reverse them.

Each group signs one cell:

1. **Compliance.** A shadow score cannot route or close a claim. On a failed check, the case stays in the human queue.
2. **Legal.** The customer letter is a fixed template plus the claim id. Review can block the letter. Review cannot change the wording.
3. **Product ops.** They own the shadow switch. They set the override line, for example 12% over four weeks. Cross it, and the feature drops back to shadow with no meeting.

At 2am the model is sure and wrong on 6 of 80 claims. The sheet already says what to do: turn on shadow, roll back, hold the letters, and add those six cases to the eval set. Nobody reopens the question of whether the model should exist.

---

## Card 3: Coaching and mentoring through challenges

**Governing sentence:** "Our prompt bank had every prompt engineers needed, and nobody used it. I turned prompts into invocable skills with the guardrails inside, and adoption turned around."

**Scene:** Early 2025, the Software Engineering Practices group pushed GenAI adoption through a prompt bank; engineers tried a prompt once, got mediocre results, and reverted to their own.

**Three moves:**
1. **Diagnose, not blame.** Handing people prompt text is documentation, not capability. Every engineer was re-solving quality and compliance alone.
2. **Skills, not prompts.** Each prompt became an invocable workflow skill with deterministic rules enforced underneath: bank policy, output structure, validation baked in. One or two word command plus inputs.
3. **Feedback loop.** Friction engineers reported went directly into which skills we built next. Fortnightly open floor.

**Result:** Adoption turned around because using AI correctly became the path of least resistance. Autonomy inside globally defined boundaries. The pattern became 15+ internal tutorials and evaluation standards adopted by 500+ engineers.

**Lesson:** "Capability transfers as working tooling, not as documentation. Guardrails belong in the tool, not in the engineer."

**Notes:** Told to Jonathan in round one as the hub-and-spoke answer. New panels can hear it fresh. Governing thought to keep: autonomy inside globally defined boundaries.

### Plain English (study note, not the 90-second answer)

A prompt library nobody uses is a document. Turn each prompt into a skill people can call, with the rules already inside it. Correct use becomes the easy path.

1. **Find the real gap.** People received prompt text. Each engineer still had to solve quality and compliance alone, tried once, got a weak answer, and went back to their own prompt.
2. **Ship a skill.** One or two words plus the inputs. Bank policy, output shape, and validation run underneath the call.
3. **Build the next skill from their friction.** What they report as slow or awkward is the next skill. Hold an open floor every two weeks.

Capability transfers as working tooling. The guardrails live in the tool. People keep autonomy inside boundaries you already set.

**Example.** You sit on the AI council and cannot make product engineers use your prompt bank. You published prompts for claims "Ask AI": redact personal data, cite the policy clause, abstain on denials. Engineers tried one, got a messy answer, and went back to their own prompt.

1. **The gap.** The bank listed the right words. It did not do the work. Every squad re-solved redaction and citation on its own.
2. **The skill.** You ship `/explain-denial` plus a claim id. It redacts the payload, forces the output shape, refuses payout language, and checks the policy citation before the engineer sees the draft.
3. **The loop.** Every two weeks you ask what still feels slow. The next skills are the ones they name, such as `/hold-letter` and `/shadow-score`.

Product still chooses what to ship. Using the council path is now less work than writing another prompt.

---

## Card 4: Conflicting priorities across organizations

**Governing sentence:** "Business wanted the automation number to grow faster. I held the release gates, and gave them a defensible number instead of a fast one."

**Scene:** Dispute platform rollout: ops leadership measured on automation rate and backlog, my team accountable for every wrong denial under Reg E.

**Three moves:**
1. **Shared scoreboard.** Same canary metrics visible to both groups. No private tech data, no private business data. One set of numbers to argue from.
2. **Held the gate.** 1% shadow, 5% semi-autonomous, expansion only on human-agreement data. Not negotiable on dates, negotiable on scope.
3. **Traded scope, not quality.** When a date pressed, business got a smaller slice earlier instead of a bigger slice unverified.

**Result:** At 5% the gates caught the regulatory-clock failure before one wrong denial reached a customer. That incident flipped the conversation: the gates stopped being tech friction and became business protection.

**Lesson:** "Neither group got what it asked for. Both got what they could defend. The customer is the tiebreaker nobody can argue against."

**Notes:** Recurring theme behind it: when a deadline presses against unfinished evals, cut scope, never quality. 73% belongs to this card only.

---

## Card 5: Driving outcomes through communication

**Governing sentence:** "At 2am the model was confident and wrong. No customer ever knew, because everyone inside heard the same facts in the right order."

**Scene:** Overnight board showed 6 of 80 Zelle cases where the model said sender error and humans said unauthorized, with abstention flat, so it was sure and wrong; I shadowed the classifier, rolled back, held six letters.

**Three moves:**
1. **Sequence.** Ops leadership at 7am with the numbers. Compliance in writing: letters hold until they release. Prompt owners before standup, so they never heard it as gossip.
2. **One version of facts.** Every audience got the same five items: 6 of 80, abstention unchanged, rollback done, classifier shadowed, letters held.
3. **Blameless frame.** The control worked on a pair the eval set had never seen. Not a bad prompt, an eval gap. The failure pair went into the golden set, so the next change is scored on it.

**Result:** Zero customer impact. Cases re-scored on the old prompt by morning. Compliance released the letters. Prompt owners stayed engaged instead of defensive.

**Lesson:** "Incidents don't break trust. Inconsistent stories do."

**Notes:** Shares the incident with Card 2. In the same room, tell it fully only once.

---

## Pre-round protocol (locked, from round one)

1. Breathing: 6:2:7.
2. Identity anchor: 20 years designing systems, nothing to prove. Silence is mastery.
3. One page, handwritten, on what you built recently.
4. 48-hour rule: no new material in the last two days. Cards only, spoken aloud.

## Post-round protocol

1. 24-hour no-send rule on any message to interviewers.
2. One structured debrief: what was asked, what I said, what I'd change. Then closed.
