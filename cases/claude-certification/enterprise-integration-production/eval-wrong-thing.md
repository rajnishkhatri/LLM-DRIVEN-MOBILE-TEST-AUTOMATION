---
type: failure-taxonomy
title: 'Watch-out: the eval suite that measured the wrong thing'
description: 'Failure trace: a contract-review assistant shipped on ten familiar contracts. The suite was not representative and was never updated after the prompt changed.'
tags: [claude, certification, enterprise-integration-production]
---

The eval suite that measured the wrong thing
WHY THIS MISTAKE HAPPENS
When a demo is working, declaring it "good enough" feels like a reasonable call. Manual spot-checks take time, and the system seems to respond correctly on every input tested. What makes this an issue is that teams can only test inputs they thought of, whereas production surfaces the rest.
A partner postmortem that needs to be reconstructed
The following is a composite postmortem representing a pattern that appears repeatedly in field deployments. The team built a contract review assistant for a professional services firm. They manually tested the assistant against ten contracts their team knew well, declared the system ready, and then moved to production. The regression arrived two weeks later.

What the postmortem found
The system was failing on a class of contracts it had never been tested against, namely those with non-standard obligation structures. The model was extracting obligations from the wrong section.
The eval suite existed. It was built at the start of the project and had been built from the ten contracts the team used during development. This was not a representative sample of the full contract population.
When the prompt changed, the eval suite kept passing, but only because the golden dataset still reflected the old prompt's expected outputs. It had never been updated to account for the new behavior.
The decisions that led us here
The eval dataset was built from convenient inputs rather than a representative sample. An eval suite that does not cover the input distribution it will face in production is measuring a different system than the one you are shipping.
The eval input set was not updated after the prompt was changed. The eval was still passing every time because it was assessing behavior the prompt no longer produced. The scores looked stable because nothing was testing what had changed.
Manual spot-checks were treated as an eval substitute. Spot-checks can confirm that a specific input produces a specific output, but they cannot tell you whether the system behaves correctly on unknown inputs.
WHAT TO WATCH OUT FOR
The eval suite was present but misconfigured in two ways: the dataset was not representative, and it was not kept current. Both problems are invisible until production exposes the gap. The system looked healthy in development because it was only tested on inputs it was already optimized for.
← Previous
Screen 3 of 21
☰ CONTENTS
Next →
