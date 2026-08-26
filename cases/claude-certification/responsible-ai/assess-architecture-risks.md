---
type: validation-walkthrough
title: 'Checkpoint: assess the risks in a proposed architecture'
description: 'Name at least three risk categories in a support agent that retrieves from a knowledge base, issues refunds, and logs activity, and pair each with a workable mitigation.'
tags: [claude, certification, responsible-ai]
---

Assess the risks in a proposed architecture
Try it now. You are reviewing a proposed architecture: a customer-support agent that retrieves answers from a partner knowledge base and issues refunds through a connected tool, with all activity written to a request log. Identify at least three risk categories present in this design, and for each one name a workable mitigation. Both the risk and a mitigation that addresses it are required.

Identify the risk categories present in this design and pair each with a mitigation.

Reveal model answer
Skip for now
MODEL ANSWER
1. Indirect prompt injection via the knowledge base. Retrieved content can carry instructions; mitigation is to treat retrieved text as untrusted and screen tool/content inputs, not just user input.
2. Tool and action abuse on the refund tool. Mitigation is an action-authorization check that runs before the refund tool executes, independent of the model's output.
3. Token-budget exhaustion on large knowledge-base documents. Mitigation is chunking and input limits plus budget monitoring so a large document cannot truncate the work silently.
4. Data exposure in the request log. Mitigation is server-side redaction of sensitive fields before anything is logged.
← Previous
Screen 6 of 22
☰ CONTENTS
Next →
