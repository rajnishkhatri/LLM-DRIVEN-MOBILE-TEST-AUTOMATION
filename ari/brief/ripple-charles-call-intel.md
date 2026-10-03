# Charles Call Intel — Ripple Craft Exercise
Call date: Fri Oct 2, 2026. Source: Charles (Judge Group), reading from the internal panel guide and grading packet. He could not share the documents, only highlights. Treat everything below as directional, not verbatim rubric.

---

## 1. Logistics (confirmed)
- Panel: **Tuesday, 10:00 AM, on site** (Northbrook). Hold confirmed. Formal email coming from Charles within hours.
- Charles will be **on site**: pre-brief before the session, debrief after. Arrive early.
- Charles is reachable by **text all weekend**.
- Plan agreed on the call: Rajnish sends Charles a **1-2 page direction check this weekend**. Charles will react on intent/context only, not technical content.

## 2. The core secret: the exercise is deliberately flawed
- "Dana Whitfield" is a fictional construct. The brief is **flawed on purpose**. There is no well-formed answer.
- It is **written to invite interrogation**. It asks what you *would* build, not what to build.
- The **questions-for-Dana section is the screen**. That deliverable is how they separate candidates.
- They will never tell you it's flawed. Noticing is the test.
- The deliverable includes **running code you will modify live in front of them**.
- The rubric requires evidence the writing and code are **yours**.

## 3. Session flow (from the panel guide)

### Part 1 — Cold open (highest-signal 5 minutes)
- First question, before any walkthrough, from Jon: **"What's the actual problem?"**
- No slides, no notes, no whiteboard. Cold. Five minutes.
- A strong answer **names the fragmentation**.
- They write down your phrasing **verbatim**. Word choice matters.

### Part 2 — The brief and your questions for Dana
- They pick the **two sharpest questions** you asked Dana.
- For each: *What answer were you expecting? What would you have done differently in each branch?*
- Known example probe: **"Which of the three backends worried you most, and why?"**
  - Trap read (per Charles + what Rajnish said live): none of the three individually. Omni, Jira, Confluence are just integration points. The real worry is **governance at the entry point**: user intent, entitlement/authorization (what data and apps is this user allowed to touch), and ambiguity resolution before routing. Plus **customer-facing consequences** — this is SaaS, errors reach customers.
  - Charles confirmed this direction on the call. Rajnish said it live; it landed.

### Part 3 — The 10 test cases
- Panel reads them **before** the session.
- Question: **"Why these 10? What made the cut and what didn't?"**
- The "what didn't make the cut" half is as important as the ten you chose.
- (Transcript garble: something about tier-one vs tier-two flaws. Likely meaning: cases should chase the serious flaws, not surface ones. Flag to clarify with Charles if needed.)

### Part 4 — Demo and code (you drive)
Known probes, near-verbatim from the guide:
- "Show me where the **routing decision** gets made."
- "How would you **test routing in isolation, without an LLM in the loop**?"
- "Omni returns a number. **What does the user see besides that number?**"
- "Why **this failure path**? Why not a different one?"
- "Where does this **fall over at 1,000 concurrent sessions**?"
- "What's the **first alert** you'd want? What would it measure?"
- Theme: resiliency, inspectability, testability.

### Part 5 — Live extension
- They pick one extension based on what you built. A real business need, **not a spec** — same style as the exercise.
- Known option: support wants a **fourth source, a public status page** ("is the platform down?") answered without a ticket. Their question: **how much of what's on screen has to change?** (Tests whether adding a source is config or surgery.)
- Known option: they ask a question **designed to route wrong** in your implementation. Example from the guide: *"My March forecast variance jumped and I think bank mapping is wrong. How do I fix it?"* (Ambiguous: BI question? Help-center question? Ticket? It straddles all three.)
- If the demo doesn't run, they don't block. They move to the whiteboard: "Walk me through the change you'd make." They are scoring how you think, not catching everything.

### Part 6 — The time question
- **"You had four hours. What would another 20 have brought?"**
- Rewards candidates who **respected the cap**. Do not hint you quietly went long.
- The answer sorts people: naming **more backends = feature thinker**. Naming **eval harness, disambiguation turn, permissions = platform thinker**. Be the second.

### Part 7 — Your questions for them
- Short window. High signal.
- Bad: reporting lines, title, scope of authority. ("That's a question for a different time" — Charles can get those answered.)
- Good: the team, the users, **what's actually broken**, what's exciting, what's emerging. Questions about **the work**.

## 4. Pressure moments (scripted)
- They will **push more than once**. Deliberate **silence and pauses** are in the script. Do not fill silence by backing down.
- Scripted objection, near-verbatim: Dana pushes on query prominence. *"Showing the query makes it look like a database tool instead of an assistant. Customers asked for something simple. She has the customer conversations and the CAB date. Why are you right?"*
  - Per Charles: **she isn't right**. The test is whether you can defend your work under an authority-plus-deadline objection.
- General pattern: "She's got customer research, you've got a hypothesis." Hold position with reasons, not volume.

## 5. Red flags (from the grading packet)
1. **Written quality far exceeds code quality.**
2. **Framework fluency with no incident in it.** Every answer is clean taxonomy, nothing ever broke.
3. **Vocabulary drift.** Claiming terms like "context engineering" while describing ordinary retrieval chunks. Claiming others' monitoring as your own. Words bigger than the substance.
4. **Every question is a scope question.**
5. **Timeline accepted without comment.** Six weeks for what Dana described is not real. A candidate who doesn't say so won't say so on the job.
6. **All "we," no "I."** They will ask what part was yours. (Matches our existing language rule: I for decisions, we for execution.)

## 6. Green flags (from the grading packet)
1. **Push back on whether one surface is even the right answer** — and make the case, not just object.
2. Reach **"own the conversational layer, govern execution"** independently.
3. Notice that **ticket creation is already a write action** — so "phase two" (actions) has already started, whatever the brief claims.
4. **Routing decision is inspectable and testable without an LLM.**
5. **Separate routing accuracy from answer accuracy** before being asked.
6. **Volunteer a weakness in your own submission** with a fix. "This part is weak, here's how I'd fix it."
7. Ask **what happens to the four teams already building their own chat services**. The brief never mentions this project cancels other people's work. That is the hardest part of shipping it.

## 7. Culture and business context
- Lean, greenfield environment. People who need every detail specified struggle here. They want: solution, admit a bad move fast, fix it fast.
- Jon demoed **agentic payment processing** (agents deployed with customers to process payments at scale). Weeks ago they believed human-in-the-loop was mandatory; they no longer do. High-level customer demo happened this week. Expect they may show Rajnish this demo.
- Sprint culture compressing: week-long sprints, Jon joking about "hour sprints." Speed pressure is real.
- Competitive fear: not the big incumbents, the **startups**. They want people who move like one.
- Business: treasury function. CFO/controller uses the platform to execute payments (Charles's example: paying Judge Group for placing Rajnish).
- One big direct competitor. Charles didn't recall the name on the call but said they put up **billboards around Chicago mocking the Ripple acquisition** ("don't let payments be a ripple in how you do business"). Homework: identify them (GTreasury's historical big rival is Kyriba — verify) and skim Ripple Treasury's site before Tuesday.

## 8. What this changes in our plan
1. **The cold open is now priority one.** The pending question "what is Dana actually asking for, in one sentence" is literally the first scored moment. Rehearse it spoken, no notes, 5 minutes max, naming the fragmentation.
2. **Write the questions-for-Dana section to be interrogated.** For each question, pre-build: expected answer, and what changes in the design per branch. Two of them will be picked.
3. **Comment on the six-week timeline in the brief.** Explicitly. It's a scored item.
4. **Add the four-existing-teams question** to the brief or the live questions. It's the top green flag.
5. **Design routing as deterministic and LLM-free testable.** Already Rajnish's instinct. Make it visible in code and tests.
6. **Split test cases: routing accuracy vs answer accuracy.** Label them that way.
7. **Name one weakness in the submission, with the fix.** Written into the brief.
8. **Keep code simple enough to modify live.** Plan the status-page extension as a near-config change.
9. **Prepare the query-prominence defense** against the scripted Dana objection.
10. **Prepare the "another 20 hours" answer**: eval harness, disambiguation turn, permissions model. Platform items only.
11. **Respect the 4-hour cap and say so honestly.**
12. **Weekend deliverable: 1-2 pager to Charles** for a direction check.
