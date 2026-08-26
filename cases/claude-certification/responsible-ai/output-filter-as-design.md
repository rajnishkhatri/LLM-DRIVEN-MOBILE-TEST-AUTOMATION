---
type: failure-taxonomy
title: 'Watch-out: when a single output filter looks like a finished design'
description: 'Failure trace: a refund tool ran before anything checked the request. The output filter inspected generated text after the money had already moved.'
tags: [claude, certification, responsible-ai]
---

When a single output filter looks like a finished design
SETUP HOOK
Output filtering is a clear control you can point to; it shows up as a clean box on the architecture diagram, it fires where a reviewer can watch it work, and it sits at the end of the path where the risk feels most concrete, right before the user sees a response. So, if you add one classifier on the output, the diagram looks complete, and the review passes. The problem is that the most important thing the system does may have happened before that classifier ran.
A trace excerpt where the side-effecting tool ran before anything checked the request
The model received a request, called a tool that issued a refund, and the tool ran. A refund is a financial action: the tool reverses a charge and returns money from the company to the customer's account. Only after the money moved did the output filter look at anything. It inspected the text the model generated, found nothing unsafe, and passed. The refund had already happened. A control could have sat in three places on this path: screening the request on the way in, authorizing the tool call before it executed, and filtering the response on the way out. This system only had the last one, and it sat downstream of the only action on the path that could not be undone.

A customer service agent has access to an issue_refund tool. A user submits a request.

1 request received (no input screening configured)
2 model emits tool_use: issue_refund(order=…)
3 tool executes, refund issued (no authorization gate before the side effect)
4 output filter inspects generated text (it passes, because the action it described had already happened)
WHY THIS BROKE
A control was placed at one point but was treated as covering three points. Output screening judges text, not actions. A side-effecting tool needs authorization before it runs, and an unscreened input has no gate. One filter at the end is not a guarded path, you should be adding all three filters when necessary.
← Previous
Screen 8 of 22
☰ CONTENTS
Next →
