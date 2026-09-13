---
type: guide
title: 'Prompt evaluation pipeline — dataset, run, grade, iterate'
description: 'Measure prompts with a dataset, model and code graders, and an average score before iterating — do not ship on a couple of manual checks.'
tags: [claude, bedrock, aws-claude, evaluation]
---

# Prompt evaluation pipeline — dataset, run, grade, iterate

Prompt engineering is writing and editing prompts so Claude understands the request and the desired response. **Prompt evaluation** is automated testing of those prompts against objective metrics.

After you write a prompt you can:

1. Test once or twice and ship — a trap.
2. Tweak against a few custom inputs — also a trap.
3. Run an evaluation pipeline that scores the prompt — the recommended path.

Serious applications need (3). Evaluation comes *before* optimization: establish a baseline, then iterate.

## A typical eval workflow

There is no single standard methodology. Open-source packages and paid tools exist; a lightweight custom pipeline is enough to start.

1. **Draft** a baseline prompt.
2. **Build a dataset** of test inputs (hand-crafted or model-generated; tens to thousands of records).
3. **Execute** — feed each input through the prompt and collect model outputs.
4. **Grade** each output (commonly 1–10, where 10 is perfect).
5. **Average** across the set for an overall score.
6. **Iterate** — change the prompt, repeat.

Compare prompt versions on the *same* pipeline. The point is a quantitative delta, not a gut feel.

## Generating test datasets

Worked example: a prompt that accepts a user task and must return one of Python, JSON, or a regular expression — no extra explanation.

- Dataset records are JSON objects with a `task` property.
- Generate them with a cheaper/faster model (Haiku) via an inference profile.
- Extract the JSON with the [prefill + stop-sequence](bedrock-converse-api.md) pattern, parse, and save to a file for reuse.

A demo might generate three cases; production needs many more. The dataset schema will grow (for example a `format` key once syntax grading exists).

## Running the eval

Three functions cover almost the whole pipeline:

- **run_prompt** — merge a test case into the template, call Claude, return the output. A V1 template such as "please solve the following task [task]" has no output-format constraint and tends to be verbose.
- **run_test_case** — call run_prompt, grade, return `{output, test_case, score}`. A hardcoded score of 10 is only a placeholder.
- **run_eval** — load the dataset, loop, assemble the results list.

Haiku over a small set can finish in tens of seconds; concurrency helps if rate limits allow. Next step after a green pipeline skeleton: real graders.

## Model-based grading

Three grader families:

| Grader | What it checks |
|---|---|
| Code | Programmatic: length, syntax, keywords, readability |
| Model | Another LLM scores quality, instruction-following, completeness |
| Human | Flexible, slow |

A model grader takes the original output, feeds it to an evaluation model with explicit criteria, and asks for reasoning plus a score (typically 1–10) as structured JSON (again, prefill + stop for clean parse). Asking for strengths and weaknesses avoids a default middling score.

Average model-grader scores across the set. Criteria worth naming up front: format compliance, syntax, task completion, general quality. Model graders cover subjective quality that code cannot.

## Code-based grading

For outputs that must be executable or parseable:

- `validate_json()` — `json.loads`; 10 on success, 0 on failure.
- `validate_python()` — AST parse; 10 or 0.
- `validate_regex()` — `re.compile`; 10 or 0.
- `grade_syntax()` — router on the test case's `format` key.

The dataset must carry `format`. The prompt should demand "respond only with Python, JSON, or a plain regex, no comments," with a code-fence prefill and a closing-backtick stop sequence. A combined score such as `(model_score + syntax_score) / 2` mixes quality with validity.

Mechanism: try/parse — success is full marks, a parse error is zero. That is the check that the model returned valid, executable content rather than an explanation.
