---
type: guide
title: 'Bedrock Converse API — requests, conversation, and output control'
description: 'Stateless Converse calls on Bedrock: inference profiles, message history, system prompts, temperature, streaming, prefills, and stop sequences.'
tags: [claude, bedrock, aws-claude, converse-api]
---

# Bedrock Converse API — requests, conversation, and output control

AWS Bedrock hosts the same Claude models (Sonnet, Haiku, and peers) as the Anthropic API, but it is a different service with a different SDK and different docs. Use Bedrock-specific resources. The course focus is the path between a Bedrock runtime client and the service: requests, text access, and the design patterns around them.

Chatbot flow: user submits text → server receives the request → Bedrock client calls AWS Bedrock with the user message and a model ID → the model generates text → the assistant message returns → the server sends it to the browser.

## Making a request

Three requirements:

1. A **boto3 client** connected to the Bedrock runtime service in a region (for example `us-west-2`).
2. A **model ID** — or, more reliably, an **inference profile ID**.
3. A **user message** in the Converse shape.

Not every model is hosted in every region. A wrong region produces cryptic errors. Inference profiles route the request to a region where the model exists; find them in the AWS console under cross-region inference, not the model catalog.

Message shape:

```python
user_message = {"role": "user", "content": [{"text": "your input"}]}
response = client.converse(modelId="profile_id", messages=[user_message])
text = response["output"]["message"]["content"][0]["text"]
```

`content` is a list because a message can mix parts (text, images, tool use). The assistant message uses the same structure with `role="assistant"`.

## Multi-turn conversations

Bedrock and Claude APIs are **stateless**. They store no messages. Multi-turn context is your job:

1. Keep the complete list of exchanged messages in application code.
2. Send the entire history with every follow-up request.

Roles must alternate: user → assistant → user → assistant. Consecutive same-role messages are invalid. Helper functions that append user and assistant turns keep the list honest.

Without history, a follow-up such as "and three more" after "what's 1+1?" has no context and produces a nonsense answer.

## System prompts

A system prompt assigns a role so the model behaves as that role instead of obeying a long do/don't list. Pass it to `converse` via the `system` keyword: a list of dictionaries with a `text` field, at least one character long.

Example: "You are an AWS cloud support specialist" steers the model toward specialist answers, competitor-avoidance, and refusing off-topic questions — more naturally than an explicit rule list.

Make the system-prompt parameter optional on chat helpers and default it to none. An empty string is an error.

## Temperature

Temperature is a 0–1 decimal that controls randomness in next-token sampling.

1. Tokenization breaks the input into chunks.
2. Prediction assigns probabilities to possible next tokens.
3. Sampling selects a token from those probabilities.

Temperature 0 is deterministic (always the highest-probability token). Higher values raise the chance of lower-probability tokens. Default is 1.0 (maximum creativity). Pass it in `inferenceConfig` on `converse`.

Use near-0 for extraction, facts, and consistency; near-1 for creative writing, brainstorming, jokes, and marketing. Temperature is the creativity-versus-consistency lever.

## Streaming

Users expect immediate feedback; a full generation can take 3–30 seconds. `converse_stream` yields text as it is produced.

Flow: the server sends the request → an initial acknowledgment arrives with no text → a stream of events follows → each content-block delta is a small chunk for the UI.

Event types: message start, content block delta (the text), content block stop, message stop, metadata (last).

```python
for event in response["stream"]:
    if "content_block_delta" in event:
        chunk = event["content_block_delta"]["delta"]["text"]
        # Send chunk to the UI; also accumulate if you need the full message
        total_text += chunk
```

Only content-block-delta events carry generated text.

## Controlling output: prefills and stop sequences

**Prefilling** the assistant message: append a partial assistant turn to the message list. Claude continues from that endpoint rather than starting a new reply. Concatenate the prefill with the returned text for the complete output.

**Stop sequences**: strings that halt generation on first match, passed through `inferenceConfig`. The matching sequence itself is excluded from the response. Multiple sequences are allowed.

Both steer output more strongly than prompt wording alone.

## Structured data via prefill + stop

Claude likes to wrap JSON, Python, or lists with headers and commentary. Applications often need only the raw payload.

Pattern:

1. Prefill the assistant message with the opening delimiter (for example ` ```json `).
2. Set the stop sequence to the closing delimiter (` ``` `).
3. Claude assumes it already wrote the opener, emits only the content, and stops at the closer.

Works for any delimited format, not only JSON. Essential when the next step is parse-or-copy rather than a human reading the reply.
