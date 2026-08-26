---
type: guide
title: 'Evals as acceptance criteria: building quality into the build process'
description: 'Write the eval suite before production code. Distinguish code-based, model-based, and human-review evals, and use the suite as the gate for every production change.'
tags: [claude, certification, enterprise-integration-production]
---

Evals as acceptance criteria: building quality into the build process
In the first module, you made architecture decisions: patterns, integration points, and how your system should respond to different inputs. What you don't have yet is confidence that those decisions hold when the inputs are real and the users are unpredictable.

This is where evals come into the picture. Evals are short for evaluations, and they let you test your system's behavior before it goes to production or after model updates, so you discover problems before they occur. This section explains what evals are, why they matter, and how to use them to get ahead of issues before your users find them for you.

Evals before code: why the order matters
An eval, or evaluation, is a structured test that checks whether your system returns the expected and accurate output. Although it sounds straightforward, the timing is extremely important. The standard approach is to build the system, see if it looks right, and conduct tests later. This isn't always the best approach.

Writing your eval suite before you write production code forces three things to happen that are otherwise easy to defer:

First, state what success means in measurable terms
Second, expose design assumptions early, when changing them is still cheap
Third, give yourself a gate that can determine whether a model swap, a prompt change, or a new retrieval strategy measurably improved the system
An eval suite belongs at the beginning of your build, defined before production code is written, rather than at the end as a QA step. In fact, if you cannot write an eval for behavior, then you have no reliable way to measure whether that behavior is present. This means that every change you make to the system isn't verifiable. Adding an eval suite at the beginning allows you to verify throughout the entire build.

How the eval workflow runs: from task definition to result
A well-constructed eval workflow runs sequentially through the stages below. Each stage produces an artifact that feeds into the next stage:

Stage	What happens	Output
1. Define the task	State the behavior you are evaluating in specific, measurable terms, and write the prompt you will use to test it. A vague definition produces a vague eval. The level of concreteness of both the behavioral specification and the prompt is what makes the result meaningful.	Task specification with prompt to test and pass criteria
2. Build the golden dataset	Assemble the inputs that your system will encounter, including edge cases and counterexamples. This dataset is what your eval runs against. If the dataset is not representative, then the scores are not meaningful.	Labeled dataset with expected outputs
3. Run automated checks	Pass each prompt through the system and compare the output against your expected result. Automated checks are fast and cheap. Use them for behaviors that are unambiguous: format compliance, schema validation, and factual lookups against authoritative data.	Pass/fail record per item
4. Score with a judge	For behaviors that require interpretation, such as tone, accuracy of reasoning, and appropriateness of edge-case responses, a model-based judge can assess the outputs at scale.	Score per item with reasoning
5. Interpret and act	Aggregate scores tell you where the system is and whether a change moved it in the right direction. A change that raises the mean score while quietly degrading performance on edge cases or adversarial inputs doesn't make the system better.	Overall score, per-category breakdown
Model-based vs. code-based evals: when to use each
Not every behavior you need to evaluate can be checked the same way. Some behaviors have a single correct answer: the output is either a valid JSON, or it isn't. A second category is whether the output matches the expected tone or style of language. These two categories of behavior need different evaluation tools, and choosing the right one for a given behavior is important to ensure accuracy and save costs.

The three types of evals have different speed-versus-flexibility tradeoffs:

Code-based evals run deterministic checks in milliseconds and cost almost nothing.
Model-based evals use a judge model to assess outputs that require interpretation and cost roughly as much as the model call itself.
Human-review evals rely on human judgment for high-stakes or novel behaviors where neither code nor a model judge can be trusted to evaluate reliably. Human-review evals are the slowest and most expensive option.
Eval type	How it works	When to use it	Cost	Limitation
Code-based eval	A function checks the output programmatically: schema validation, regex match, JSON parse, length check, assertion against authoritative data.	Any behavior that is unambiguous. Format compliance, schema correctness, lookup accuracy, length constraints.	Very low: milliseconds per check, no API call.	Can't assess behaviors that require interpretation. Tone, helpfulness, reasoning quality, and edge-case appropriateness all require judgment that a function cannot supply.
Model-based eval	A judge model receives the original prompt, the system output, and a scoring rubric. The judge returns a score and reasoning. The judge prompt is itself a prompt that needs to be engineered and tested.	Any behavior that requires interpretation: response quality, instruction following, reasoning accuracy, safety, and handling of ambiguous inputs.	Medium to high: one API call per item evaluated, at the judge model's per-token rate at scale, this adds up.	Judge models can be inconsistent in borderline cases. Without forcing the judge to produce reasoning alongside the score, that inconsistency is difficult to detect
Human-review	A human evaluator reads the output and scores it against a rubric or set of criteria. This may be structured (a scoring sheet) or unstructured (open annotations and feedback).	High-stakes or novel behaviors where neither a function nor a judge model can be trusted: safety-critical edge cases, new capability areas without established rubrics, or any output where a wrong evaluation carries significant risk. Also useful for calibrating and validating model-based evals.	High: human time is the most expensive resource, and throughput is limited. Not viable at scale without sampling.	Slow, expensive, and not scalable beyond sampled subsets. Human evaluators also introduce their own inconsistency.
The grading ladder: choosing how to grade
Not every behavior should be graded the same way, and the choice of grading method follows a deliberate ladder. Reach for the cheapest reliable method first and climb only when the behavior demands it.

Code-based grading, wherever the behavior allows it. Deterministic checks, including schema validation, exact match, length, and presence, run in milliseconds, cost almost nothing, and never drift. If a behavior can be checked in code, then it should be.
LLM-as-judge, when the behavior needs interpretation. Use a judge model for outputs that require judgment. Make the judging rigorous by using detailed rubrics, constrained verdicts (a small fixed set of labels rather than free-form scores), calibration against human-labeled examples, and grading with a different model than the one whose outputs you're evaluating, to avoid self-preference.
Human grading, as the last resort. Reserve human review for high-stakes or novel behaviors where neither code nor a calibrated judge is trustworthy yet. It is the most expensive and least scalable option.
JUDGE CALIBRATION: THE STEP MANY TEAMS SKIP
An LLM judge is itself a system that can be wrong. Before you trust its verdicts, make sure to calibrate it. To do this, run it against a set of human-labeled outputs and confirm its similarity with human judgment is high enough to rely on. An uncalibrated judge produces confident scores that may not be high quality at all. This is worse than no automated grade, because it seems trustworthy.
Favor volume over perfection. Many automatically gradable cases beat a handful of manually-graded ones: broad, cheap coverage catches more regressions than a small, painstaking set, and it can run on every change.

Defining success criteria: turning a business requirement into a measurable threshold
A business requirement like "summarize claims accurately" does not really tell you what to measure. The process of turning it into an eval criterion has the following steps:

Identify the behavior specifically: "Summarize claims accurately" should be updated to "extract the filer's name, claim number, incident date, and claimed amount from each document."
Set the threshold: Decide what counts as passing. If, for example, your thresholds are 100% accuracy on structured fields, less than 2% hallucination rate, and response within schema 99.5% of the time, those numbers should come from the business requirement. Don't just choose what your first prototype happens to achieve; find guidance on setting eval thresholds at platform.claude.com/docs/en/test-and-evaluate/develop-tests.
Identify the failure modes: Continuing with the same example, an output that might not be acceptable can include a fake claim number, a missing incident date, or a value from the wrong claim. Each failure mode is a category in your eval dataset.
Include adversarial inputs: It should include documents with missing fields, handwritten sections, unusual formatting, and non-standard layouts. If your golden dataset contains only clean inputs, then your eval scores will not predict production performance.
Evals as the gating mechanism for change
Every change to a production Claude system, whether it is a model swap, a prompt revision, a context strategy change, or a retrieval configuration update, should run through the eval suite during development before it moves to production. This is the only reliable way to know whether a change has improved the system.

A single-turn eval set will not tell you how the system holds up across a conversation. Multi-turn evals are a separate category that scores the system over a sequence of exchanges rather than on a single prompt and response. A multi-turn eval checks a few criteria: whether the system keeps prior context straight across turns, whether it answers a follow-up prompt without inventing details that were never said earlier in the conversation, and whether output quality holds as the conversation runs longer. Because the unit being scored is a whole conversation, this category needs its own golden dataset. This consists of full conversation transcripts with known high quality responses at each turn, covering the follow-ups, topic shifts, and conversation lengths the system will see in production.

Consider a team building a document summarization workflow that revised their summarization prompt but did not update their eval suite to match. The eval suite passed all required checks. Two days after the swap went to production, field reports showed that multi-clause legal sentences were being truncated into summaries. The root cause was that the eval set predated the prompt change and didn't match the behavior that changed.

In short, you should run evals before every change to keep the eval set current with the system it is measuring.

COST · COMPLEXITY · RISK
Cost: Every model-based eval is an API call. Although cost is worth keeping in mind, don't let it drive you toward a smaller eval set than your use case warrants. The bigger risk is under-evaluating: a production-breaking change that slips through an undersized eval suite costs far more than a few extra API calls. Size your dataset against what gives you confidence in your results and treat cost as a secondary constraint.
Complexity: Eval infrastructure adds a parallel system to maintain. The golden dataset must be kept current, the judge prompts must be engineered and tested, and the pass thresholds must be revisited when the system's requirements change. Where to go next: For working implementation patterns, including a walkthrough of grading designs and golden-answer comparison, see the Claude Cookbooks at github.com/anthropics/claude-cookbooks/blob/main/misc/building_evals.ipynb.
Risk: An out-of-date eval suite provides false confidence. It creates the misleading impression that a change is safe when the checks are measuring behavior that no longer exists in the system. The highest risk moment for a regression is when evals are present and out of date.
← Previous
Screen 2 of 21
☰ CONTENTS
Next →
