---
type: notes
title: 'Present a tradeoff the stakeholder can act on, and design a demo that moves the deal'
description: 'Frame every choice as gain, give-up, and reversal cost. A capabilities demo creates interest; only a scenario-specific demo creates confidence. Partner-track demo, scoping, and objections sit on the same structure.'
tags: [claude, certification, stakeholder-engagement]
---

# Present a tradeoff the stakeholder can act on, and design a demo that moves the deal

Discovery told you what the buyer needs. Turning those requirements into a decision a stakeholder can make is the next work.

The Architect is now helping the stakeholder understand the tradeoff, see the business consequences, and approve a path forward with confidence.

Your job is not to resolve the tradeoff before the meeting. Your job is to make decisions possible. Describe the options clearly enough that the stakeholder can make an informed choice.

Every meaningful design decision has a tradeoff. One option may reduce cost or complexity but increase latency, risk, or compliance burden. Another may improve the user experience or scale better but require more effort upfront. If you present only the conclusion, the decision may look clear, but it is weak. When the downside appears later, the stakeholder may feel they approved a recommendation without understanding what came with it. Use a simple decision frame:

1. What do we gain?
2. What do we give up?
3. What happens if we choose this now but have to reverse it later?
4. In regulated environments, what does this do to our compliance posture?

That third question is the one most people skip, and it is often the one that changes the meeting. It turns the discussion from "what is the better technical answer?" into "what is the better business choice?"

Technical precision is necessary, but it is not sufficient. In architecture reviews, the recommendation is often technically correct but still not understandable to the person who must approve it. The Architect may explain the options in technical vocabulary (latency, logging depth, context size, retrieval pattern, deployment route) while the executive is asking a simpler question: "What happens to the business if we make the wrong choice?" At that point the room does not need more detail; it needs translation into something a person can understand. When you do this well, the stakeholder is not just hearing your recommendation. They are making an informed decision they can defend later.

## Frame the decision as a package, rather than as a verdict

Present the decision as a package the stakeholder can act on: the options you considered, the criteria you weighed them against, your recommendation, and the risks that remain. The stakeholder is not adopting your architecture; they are accepting a decision they will have to defend to their own leadership.

## Description is the competency that makes the package land

Description is one of the four AI Fluency competencies: communicating effectively with AI. Extended to the stakeholder side of the work, the same discipline means telling the audience precisely what they need, in terms they can understand. Applied to stakeholder communication, Description means framing the system's behavior, its limits, and the oversight around it in the stakeholder's goal terms. The framing should match their AI familiarity without sacrificing accuracy. Three rules apply in practice: lead with the business outcome rather than the architecture; frame limitations honestly, since a security stakeholder trusts a system whose limits are clearly stated; and anticipate the peer-proof demand, since the stakeholder will need to justify the choice to others and should leave the conversation with that justification in hand.

Use the tradeoff translation map to shift from architecture framing to stakeholder decision language.

| Architectural decision | What you gain | What you give up | What a wrong, reversed choice costs |
|---|---|---|---|
| Larger context window per call versus retrieval over chunks | Simpler initial design, the full document in view, and fewer moving parts to manage early on. | Higher per-call cost and slower response times as production volume grows. Prompt caching can recover a significant portion of the input cost for static content like policy documents held in context across calls, so evaluate caching before treating per-call cost as fixed. | Reworking the architecture after cost spikes in production, plus the credibility hit of explaining an avoidable expense surprise. |
| Trade logging detail for lower latency | Faster perceived response and a smoother end-user experience. | Reduced visibility into what happened in each interaction. | In a regulated workload, a potential compliance gap requiring remediation. |
| Single delivery route versus multi-platform | Lower build complexity and one consistent authentication and logging profile. | Less flexibility to meet different regional, compliance, or procurement needs. | A delayed or blocked production cutover if the chosen route cannot satisfy a late-emerging data residency or deployment requirement. |

The map exists to help the stakeholder see the consequence of their choice clearly enough to decide.

## Demo design is a distinct skill, and a weak demo can undo what discovery earned

Picture the buyer meeting where discovery went well. The team aligned on the problem, the use case, and the value at stake. Then the demo begins. Instead of showing the buyer's world, it shows a polished but generic set of features. The reaction is usually polite: the demo was interesting, but not quite what they envisioned.

A weak demo can make the buyer question whether the team understood the core problem. This happens when teams confuse two different jobs. A capabilities demo answers, "What can this system do?" A scenario-specific demo answers, "What does this system do with my problem, my workflow, and my constraints?"

The first creates interest; only the second creates confidence. Design proof that the solution fits the buyer's context is part of the demo's job. A well-designed demo advances the opportunity while a weak one can undo the trust discovery built.

**Partner track** (not tested by the Architect exam).

Before building any screens, make four design decisions. Those decisions determine whether the demo feels tailored and credible or generic and easy to dismiss.

| Design decision | What the Architect decides | Why it determines the outcome |
|---|---|---|
| Scenario selection | Choose a workflow the buyer will immediately recognize from their own operations, including familiar data shapes, approval steps, and edge cases. Avoid a generic document task or abstract query flow. | Buyers trust what feels familiar. When they see their own vocabulary and failure points on the screen, the demo feels relevant and credible. Recognition is often more persuasive than a polished but generic feature tour. |
| Limit placement | Decide in advance which one or two limitations the demo will identify, and frame them as intentional scope boundaries. State what the system does not do and why. | If a buyer discovers a limitation halfway through the demo, confidence drops. If you name the limitation early, it reads as discipline and honesty. In regulated settings, upfront disclosure of boundaries is often a positive signal. |
| Sales team collaboration | Shape the demo narrative with the sales team before building anything. They know what the buyer raised in earlier conversations, and you know what the system can realistically show under production conditions. | A demo built without sales may answer questions the buyer never asked. A demo built without the Architect may overpromise. Either way, the demo loses credibility and slows the opportunity. |
| Data preparation | Use information that resembles the buyer's data in structure and volume. For regulated buyers, use anonymized data that still reflects the same structural constraints as the real environment. | Buyers judge the demo by the data in it. Realistic field names and data patterns make the scenario feel real. When the data looks like theirs, the demo argues for itself. |

### Limit placement deserves deliberate attention

Of the four demo-design decisions, limit placement is the one that most often runs against instinct. In practice, naming a weakness can feel risky, so the temptation is to hide it or soften it. This usually backfires.

Imagine the moment where the buyer asks, "What does this not handle well?" If the answer is vague, confidence drops. If the answer is clear and scoped, the buyer sees discipline instead of defensiveness.

That is why you should decide in advance which one or two constraints you will name and how you will frame them. Show that the boundary is deliberate: this is what the solution is built to do, and this is what it is not built to do.

This matters even more in regulated industries such as healthcare, financial services, and the public sector. In those settings, a clear boundary often signals rigor, while a deflection signals risk.

A simple way to prepare is to ask:

- What is the limit?
- Why does it exist?
- What happens if the use case needs to go beyond it?

## Successful joint scoping starts before the session begins

**Partner track** (not tested by the Architect exam).

That same discipline carries directly into joint scoping with the Applied AI team. A good scoping session is not a place to figure out the basics for the first time. It is a place to refine choices, test assumptions, and resolve the questions that need specialist input.

If the demo proves you understand the buyer's problem, the scoping session proves you are ready to shape a credible solution around it. That only works if you arrive with three things prepared:

1. A documented view of the customer's requirements and constraints. This captures what came out of discovery: the use case, workflow, stakeholders, data conditions, technical environment, compliance concerns, and success criteria. This gives the session a shared starting point.
2. A proposed pattern or small set of candidate patterns, with tradeoffs already named. Walk in with a point of view. Show the likely options, what each gives you, what each gives up, and where the risks sit.
3. A short list of open questions the Applied AI team is best positioned to answer. These are the questions worth spending the session on: model behavior, architecture implications, scaling constraints, evaluation approach, safety considerations, or pattern fit.

In the demo, you earn trust by identifying limitations clearly. In joint scoping, you keep that trust by bringing a structured view of the problem, the options, and the unanswered questions.

## Objections fall into different categories, and each requires a different response

Technical objections in a sales cycle usually fall into three categories. Capability objections ask whether the system can do the thing at all. Governance and compliance objections ask whether the deployment can be trusted, controlled, and evidenced in a way the buyer can defend. Design-choice objections ask why you made this choice instead of another. Those require more than just justification. You need to explain the tradeoff the choice makes and what the alternative would have cost, using the same translation structure you used when you presented the tradeoff in the first place.

**Partner track** (not tested by the Architect exam).

The go-to-market engagement map should treat demo design as a tracked workstream. That is why it includes a demo-design column with scenario, identified limitations, confirmed data source, and sales-team sign-off as explicit deliverables. This matters most when a partner is running parallel opportunities or when Architects hand off mid-cycle, because continuity depends on what is documented.

## Cost · Complexity · Risk

**Cost:** Preparing a tradeoff presentation and a scenario-specific demo takes real Architect time, but it is far less expensive than a stalled opportunity or an approval a stakeholder later withdraws.

**Complexity:** Three distinct skills sit underneath this work, and two of them often go against instinct: naming reversal cost and placing limits clearly. Both require deliberate practice to improve.

**Risk:** The expensive failure is false alignment. When a decision looks approved in the room, but the reversal cost was never made explicit, and the consequence arises later.
← Previous
Screen 5 of 20
☰ CONTENTS
Next →
