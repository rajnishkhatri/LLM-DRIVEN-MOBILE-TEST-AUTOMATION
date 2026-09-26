---
type: overview
title: 'Fine-Tuning Foundation Models'
description: 'Explore the role of fine-tuning in generative AI architectures on AWS.'
tags: [aws-c01, fine-tuning, genai]
---

# Fine-Tuning Foundation Models

Explore the role of fine-tuning in generative AI architectures on AWS. Learn when fine-tuning is appropriate, how to apply parameter-efficient methods like LoRA with Amazon Bedrock, and how to design scalable, maintainable AI systems by separating concerns across model, application, security, and infrastructure layers.

A recurring architectural mistake is treating the foundation model as the center of the application. In reality, the model should be viewed as a replaceable, stateless component within a larger system. When architects overload the model with concerns such as memory, orchestration, retries, or business logic, the result is a brittle, expensive design that is difficult to evolve. When this approach fails to scale, teams often mistakenly look to fine-tuning as a remedy, and the exam consistently penalizes these poorly architected systems.

This lesson explains why fine-tuning exists, when it is appropriate, and how to recognize scenarios that justify it, while deliberately avoiding low-level training mechanics that are out of scope.

A sound GenAI architecture begins by clearly defining the model’s responsibilities and delegating all other concerns to surrounding AWS services.

The layered model for GenAI systems
A useful way to reason about GenAI systems on AWS is through a layered architectural mindset. Although it is not explicitly necessary to memorize layer names, it is rewarding to implicitly follow this separation of concerns. AWS organizes GenAI architecture into four essential layers. Each layer has distinct responsibilities that support scalable, secure, and maintainable GenAI solutions across the enterprise.


A typical GenAI stack on AWS

A typical GenAI stack on AWS
Below is a high-level breakdown of the layered architecture and the responsibilities of each layer.

Application layer: This layer provides reusable templates and blueprints for common AI applications, such as chatbots and document analysis. It helps teams build faster and more consistently by using proven, shared designs.
Security and governance: This layer wraps the entire system in consistent security, privacy, and ethical controls. It ensures AI is used responsibly and safely, protecting data and managing risks across all teams and projects.
Model layer: This layer offers access to ready-made AI models and the tools to customize them safely. It helps organizations choose and govern the right AI for their tasks, ensuring that models fit business needs and comply with compliance rules.
Data and compute infrastructure: This layer provides the essential building blocks: reliable storage, networks, and high-speed computing power. It’s the technical foundation that makes everything else possible, from experimenting with new ideas to running full-scale AI applications.
This separation between application, security, model, and infrastructure layers is essential, allowing each to scale and fail independently. At the heart of the model layer lies a fundamental principle: Amazon Bedrock foundation models are stateless. They do not retain memory or context between requests, even though they can process extensive data within a single session. Any conversational history, user preferences, or workflow state must be stored externally (in services like DynamoDB or Amazon S3) and explicitly re-supplied with each request, often injected via patterns such as retrieval-augmented generation (RAG), external orchestration, and event-driven pipelines.

This leads to a key architectural question: if models are stateless and supported by orchestration, retrieval, and governance layers, when should the model itself be changed?

The answer is narrow and deliberate. The model layer provides not only access to foundation models but also supports controlled specialization. It shapes how a model reasons, responds, and formats outputs, while data, security, and orchestration remain firmly in their respective layers.

When and why to use fine-tuning
Prompt engineering is often the first customization tool because it is flexible and inexpensive, but prompts can become fragile as requirements grow stricter (such as fixed schemas, regulated phrasing, or specialized terminology), making them harder to maintain and less reliable. Fine-tuning is used when prompt engineering and retrieval-augmented generation (RAG) no longer deliver consistent, domain-specific behavior, acting as a behavioral control mechanism rather than a way to inject frequently changing knowledge. It is applied when flexible techniques stop scaling, and a more rigid, reliable approach is needed.

Fine-tuning addresses the fragility and scaling limitations of prompts and RAG by modifying model behavior at the weight level. Instead of relying on long or complex prompts to enforce rules, the desired behavior is learned once and consistently applied across all invocations, improving reliability and reducing ongoing maintenance.

This leads to several architectural benefits:

Shorter runtime prompts, reducing context window pressure.
More consistent outputs across edge cases.
Lower prompt maintenance overhead.
Often improved latency, because less instruction text is processed.
How Fine-Tuning Reduces Context Window Pressure?
This benefit comes with trade-offs. Fine-tuning introduces an upfront training cost and requires provisioned throughput for inference. In exchange, prompts become shorter, latency typically improves, and outputs stabilize. Fine-tuning is not the default choice. It is the final step when flexibility must give way to reliability.

The following diagram represents the spectrum of model adaptation strategies, ordered from least to most invasive.


Model adaptation strategies

Model adaptation strategies
Fine-tuned models are static and slow to update. If a workload depends on frequently changing data, RAG or prompting is the correct choice, and fine-tuning is explicitly the wrong answer.

Parameter-efficient fine-tuning techniques
Full fine-tuning updates all parameters of a large language model. This approach requires significant compute resources, long training times, and introduces the risk of catastrophic forgetting, where the model’s general capabilities degrade as it overfits to a narrow task. In Bedrock-based scenarios, full fine-tuning is rarely the correct choice.

Parameter-efficient fine-tuning (PEFT) techniques are designed to adapt large foundation models without updating all of their parameters. It freezes the base model and trains only a small number of additional parameters. The original model weights remain intact, preserving general knowledge, while the new parameters learn task-specific behavior. This approach dramatically reduces training cost and time while achieving most of the benefits of full fine-tuning. Common PEFT methods include LoRA (Low-Rank Adaptation), adapter layers, and prefix-tuning, all of which introduce small trainable components to efficiently guide the model toward the desired behavior.

Low-Rank Adaptation (LoRA)
LoRA is the specific PEFT technique used by Amazon Bedrock. It introduces small, trainable components that influence model behavior in targeted ways. It injects small, low-rank matrices into selected layers of the model. These matrices capture the adjustments needed for the new task, while the original weights remain unchanged. The result is efficient training with minimal memory overhead.


LoRA adapts a model by adding small learned adjustments on top of frozen weights

LoRA adapts a model by adding small learned adjustments on top of frozen weights
The practical benefit of LoRA is efficiency. Training requires less compute, completes faster, and consumes fewer resources than full fine-tuning. This makes it particularly attractive for enterprise environments where cost control and iteration speed matter. From a life cycle perspective, parameter-efficient approaches also simplify versioning and rollback, because changes are more contained.

An additional architectural advantage of LoRA is adapter management. Each fine-tuning job produces a lightweight adapter that sits on top of a base model. Multiple adapters can be associated with the same foundation model, enabling reuse across teams or domains. This pattern supports scalable customization and is favored in design-focused exam questions.

For the exam, LoRA is among the most frequently referenced approaches in the AWS exam content. The reference to parameter-efficient techniques in the exam often signals best practice, especially when scenarios mention cost sensitivity, rapid iteration, or frequent updates to domain behavior. In contrast, full retraining or the development of an experimental model usually falls outside the expected scope.

Real-world use case and model choice
Consider, we are building a contract redaction and standardized summary service for a global financial services firm that must remove personally identifiable information, redact confidential clauses according to a firm-specific schema, and produce a short, structured executive summary for legal review. For initial evaluation, we select Anthropic Claude 3 Opus on Amazon Bedrock because it offers state-of-the-art reasoning and strong performance on complex language tasks, making it a suitable starting point for legal-style comprehension and synthesis.

Observed limitations in the chosen model
When tested in the Bedrock playground and through representative prompts, Claude 3 Opus demonstrates high-quality summarization, but two operational gaps emerge that violate the firm’s acceptance criteria.

Inconsistent redaction and schema adherence: The model doesn’t always hide private information correctly. Sometimes it misses part of a name or ID, or it changes the official labels for confidential sections instead of using the exact tags the firm needs. For legal compliance, the result must be formatted in a very specific way, with exact fields like redactions_added, redaction_count, and summary_length_category.
Hallucinations and overconfident language: When a legal clause is unclear, the model sometimes makes up references or states facts that aren’t actually in the original document. This is unacceptable for legal reviews.
These limitations show the model’s raw reasoning strength, but also that prompt-only controls and retrieval augmentation cannot reliably enforce the strict, repeatable behavior required for production compliance.

The exam-style judgment at this point is that the workload demands behavioral guarantees beyond prompting and RAG, which justifies a targeted fine-tune.

Implementing PEFT (LoRA) adapters
We have to teach a model two concrete behaviors:

Always create a final output in the required JSON format. This output must list all redactions made and include a clear error flag if the model was unsure about any part of the process, so its confidence level is transparent.
Always use careful and traceable language. If the text does not clearly support a statement, mark it with a source-not-found label instead of making up a reference or citation.
The model is trained using the firm’s own examples, which are stored in an internal data source. In these examples, human experts have highlighted exactly which information to hide and provided the correct, structured output for contracts such as NDAs and vendor agreements.

Using Amazon Bedrock’s customization workflow, the team initiated a fine-tuning job that attaches a LoRA adapter to the selected Claude 3 Opus base model, keeping the underlying foundation model frozen while training only the adapter parameters. This training teaches the model to take raw contract text and return a properly formatted result without changing how it thinks. Each example is stored in a simple data format that links input to output, enabling fully automated training.

Once validated, the adapter is registered and served alongside the base model with provisioned throughput to guarantee consistent latency for legal reviewers. Provisioned throughput is required for custom models or adapters when predictable performance is necessary, and it shifts cost from a variable token-based model to a fixed, predictable capacity purchase, a trade-off that the architecture team evaluates against SLA requirements.

Trade-offs and operational considerations
This targeted LoRA fine-tune resolves behavioral consistency and schema conformance, but it does not change the model’s base knowledge or its freshness. If the firm needs to absorb rapidly changing regulatory text or newly issued templates, RAG workflows that point to up-to-date retrieval stores remain necessary. In addition, fine-tuning introduces an upfront cost and makes the deployed behavior more static, so any significant changes to the redaction schema will require producing and validating a new adapter version. Finally, provisioned throughput provides dedicated capacity, helping stabilize latency per invocation but increasing the fixed monthly cost, which must be justified by the SLA and expected volume.