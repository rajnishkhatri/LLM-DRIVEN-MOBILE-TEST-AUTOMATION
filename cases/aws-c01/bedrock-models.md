---
type: overview
title: 'What Are Foundation Models in Amazon Bedrock?'
description: 'Explore the role of foundation models in Amazon Bedrock and understand how they enable scalable generative AI applications on AWS.'
tags: [aws-c01, bedrock-models, genai]
---

# What Are Foundation Models in Amazon Bedrock?

Explore the role of foundation models in Amazon Bedrock and understand how they enable scalable generative AI applications on AWS. Learn to select appropriate models, configure inference parameters, and apply orchestration patterns to optimize cost, latency, and accuracy in AI architectures.

Foundation models are the main building blocks behind generative AI. In AWS-based AI systems, Amazon Bedrock provides a managed way to consume them at scale. In the AWS Certified Generative AI Developer – Professional (AIP-C01) exam, foundation models are rarely tested as isolated concepts. Instead, they appear embedded within architectural scenarios that require careful reasoning about design decisions, trade-offs, and constraints, with clear expectations around cost, speed, accuracy, and reliability.

For the AWS Certified Generative AI Developer Professional exam, candidates should approach foundation models the same way they approach core AWS services, such as databases, compute, and networking. This means clearly understanding what these models are capable of, their limitations, how they perform, and the scenarios in which they are most effective to use.

Foundation models and their role in Amazon Bedrock
Foundation models are large, pretrained models that learn general patterns from massive datasets and can be adapted to many downstream tasks without retraining from scratch. These tasks include text generation, summarization, classification, question answering, and embedding creation. In practice, foundation models act as reusable cognitive engines that applications can invoke on demand, rather than assets that each team must train and maintain independently.


Amazon Bedrock provides a managed layer on top of multiple foundation model providers

Amazon Bedrock provides a managed layer on top of multiple foundation model providers
Amazon Bedrock abstracts access to these models through a fully managed service. AWS manages the underlying infrastructure and operations for the service, handling provisioning, scaling, availability, and security. This abstraction allows teams to focus on application design instead of model hosting. Teams, however, are still responsible for securing their application data and access.

Think of it like a secure, managed kitchen (AWS) versus the recipe and ingredients you bring (your team). While AWS maintains the kitchen itself, you are responsible for safeguarding your secret recipes (data) and deciding who can use them (access).

For the exam, this distinction is critical because model training and development are explicitly out of scope. The candidate is evaluated as a GenAI integrator who selects, configures, and orchestrates models within an AWS architecture, not as a machine learning researcher.

To understand our operational responsibilities when working with foundation models on AWS, it’s important to know how to choose an appropriate model for a given task, configure inference parameters, design effective prompts, integrate models with services such as AWS Lambda or Amazon API Gateway, and ensure alignment with business constraints. As a result, the focus shifts from managing infrastructure to selecting models, organizing workflows, and planning how to use them effectively.

Types of foundation models
Amazon Bedrock provides access to several categories of foundation models. Each model family in Amazon Bedrock is designed for specific tasks and types of data. Different models perform better on different workloads, so it is important to choose the right one for our needs. By aligning model capabilities with our workload, we can get the best performance and results from our AI system.

Embedding models
Embedding models, such as Amazon Titan Embedding, turn text into numerical vector representations. They are essential for systems that use:

Semantic search
Vector similarity queries
Retrieval-augmented generation (RAG)
Any system that gets context from a vector store before generating a response needs an embedding model. The system first converts input text into vector embeddings using an embedding model. These vectors are used to retrieve relevant context from a vector store, which is then provided to a language model to generate the final response.


Embedding models power context retrieval for AI responses

Embedding models power context retrieval for AI responses
Architects must include embedding models as a core part of the architecture to achieve accurate context retrieval and improved response relevance.

Generative models
Generative models create new content based on input prompts or data, rather than only analyzing or classifying information. They form the foundation for applications that produce content and perform reasoning tasks. Understanding the distinction between text-focused and multimodal generative models is essential for selecting the right model family for a given workload.

Text generation models
Text generation models, such as Amazon Titan, are designed to create, transform, or summarize text. They are ideal for tasks such as:

Conversational agents and chatbots
Content creation or summarization
Instruction following and multi-step reasoning
These models take text inputs and produce coherent outputs directly, making them the core of any language-focused AI system.

Multimodal models
Amazon Bedrock supports multimodal models, such as the Amazon Nova family, that can process and reason over combinations of text, images, and audio.

Common use cases for multimodal models include:

Extracting or interpreting information from documents that contain both text and images.
Understanding or describing visual content alongside textual context.
Transcribing and analyzing audio inputs, such as speech or recorded conversations.
Combining multiple input types to produce more accurate or context-aware outputs.
Quick Check: Apply What You Learned

1.
A company wants to build a system that, when a user types a question, can quickly find the most relevant documents from a large database before generating an answer.

Which type of AI model should the company use to convert the user’s query into a format suitable for searching the database?

A.
Text generation model

B.
Embedding model

C.
Image generation model

D.
Model supporting text, embeddings, and image generation

1 / 1
Submit Answer
Model inference configuration
Foundation models are probabilistic by nature, which means their outputs can vary even when given the same input. Production-grade architectures, therefore, require explicit control over inference behavior to ensure consistency, predictability, and safety.

We do not require a deep understanding of how models generate tokens internally. Instead, it expects candidates to have a practical understanding of how inference parameters influence output characteristics. In exam scenarios, a question may describe a task, such as producing highly structured responses, generating creative content, or ensuring deterministic behavior, and ask which configuration best meets those requirements. The goal is to recognize the effect of changing a parameter, not to explain the underlying algorithms.

In production-grade architectures, teams use inference configuration to guide model behavior and achieve consistent, predictable, and safe results.

Here are the inference parameters to serve as output-governance mechanisms:

Temperature: This controls the randomness of token selection; lower values produce deterministic outputs, while higher values enable creative generation. Generally, low-temperature inference is the default choice for enterprise and automation workloads.
Top-p: Top-p limits token selection to the smallest set of tokens whose combined probability exceeds a threshold (for example, 0.9). This allows the model to choose among likely options while excluding rare or unexpected words. It is useful when responses must stay natural but controlled.
Top-k: Top-k restricts generation to the top k most likely tokens at each step (for example, the top 50). Unlike top-p, it uses a fixed cutoff. This is effective when you want to strongly constrain outputs in structured or regulated responses.
Stop sequences: Stop sequences define exact strings that tell the model when to stop generating text (for example, stopping at } in a JSON response). They are commonly used to enforce response boundaries in structured outputs.
Choosing a foundation model based on the task
Effective model selection begins with a clear understanding of the task and its constraints. Rather than defaulting to the most capable model, architects must evaluate what level of capability is actually required. Factors such as acceptable latency, budget sensitivity, required accuracy, determinism, and maximum context window all influence the choice.

Strategic model selection framework
Foundation model selection is governed by a three-way trade-off between accuracy, latency, and cost. For example, near-real-time chat applications prioritize low latency and predictable response times, even if that means slightly lower linguistic richness. Batch document summarization jobs, by contrast, can tolerate higher latency in exchange for better reasoning and accuracy. Cost considerations further refine the decision, as more capable models generally consume more tokens and incur higher per-request charges.

Model selection should follow these decision principles:

Simple tasks: Tasks like classification, extraction, or short responses work best with smaller models that are optimized for speed and lower cost.
High-reasoning task: Analytical tasks require large models with advanced reasoning capabilities, accepting higher latency and cost.
Context-heavy tasks: Large documents or multi-turn conversations require models with extended context windows, which increases latency and leads to higher per-request costs due to the greater number of tokens processed.

Graph showing GenAI Iron Triangle task trade-offs

Graph showing GenAI Iron Triangle task trade-offs
The exam frequently contrasts powerful models with smaller, faster alternatives. Keywords such as “cost-sensitive,” “high-volume,” or “strict latency requirements” indicate that a lighter-weight model may be more appropriate, as per-request cost and throughput efficiency become critical at scale. Conversely, phrases like “high accuracy,” “complex reasoning,” or “regulatory impact” suggest that response quality outweighs cost, because errors carry higher business or compliance risk than increased latency or spend. Performance benchmarks and proof-of-concept testing are part of this reasoning process, even if not explicitly mentioned in the question.

Ultimately, architectural correctness depends on matching the model’s performance envelope to the workload’s functional and non-functional requirements.

Evaluation note: To decide between a simpler or more advanced model, benchmark them directly on your own data and workloads.
The following model families are commonly used in Bedrock, with selection driven by task requirements.

Provider
Model Family
Architectural Fit
Amazon
Titan
General-purpose text generation, embeddings for RAG pipelines, and image generation. Common default for AWS-native architectures.
Nova
Advanced multimodal generation for text, images, and audio. Specializes in document analysis, image understanding, and complex multi-data-type workflows.
Anthropic
Claude
High-reasoning workloads, complex instruction following, and large-context inference (200k+ tokens). Suitable for analytical and multi-step tasks.
Meta
Llama
Open-weights text generation models, frequently used for general text generation and fine-tuning.
Cohere
Command/Embed
Enterprise-focused conversational workloads, reranking, and retrieval-augmented generation.
Mistral AI
Mistral/Mixtral
Latency-optimized text generation with strong cost-performance characteristics, generally good for instruction tasks and smaller footprint inference.
Stability AI
Stable Diffusion
Image generation and visual content (graphic design, imaging, etc.) workloads.
Visit the supported foundation models in Amazon Bedrock to see the latest changes and updates.

Choose models based on task complexity, response time needs, and cost limits. Avoid selecting models just because they are popular or seem intelligent. Focus on what works best for the specific workload.

Model orchestration and routing patterns
In production architectures, a single foundation model rarely satisfies all workload requirements. Advanced systems employ multi-model orchestration patterns, assigning specialized roles to different models to optimize cost, latency, and accuracy simultaneously.

Routing pattern: Routing directs requests to different models based on intent or complexity classification. A lightweight classifier evaluates the request and selects an appropriate model tier. Simple requests are handled by cost-efficient models, while complex requests are routed to higher-capability models. It can significantly reduce operational costs while preserving response quality.
Cascading pattern: Cascading introduces a fallback mechanism between models of progressively higher capability. Requests are first processed by a smaller model. If output quality does not meet predefined criteria, the request is escalated to a larger model. This pattern prioritizes cost efficiency without compromising correctness in edge cases.

Cascading fallback mechanism

Cascading fallback mechanism
Aggregation pattern: Aggregation distributes a single request across multiple models and synthesizes the final response using voting or a judge model. Requests are first processed by a smaller, faster, and more cost-efficient model. This pattern is reserved for high-stakes decision systems where accuracy outweighs cost and latency considerations. For example, a medical diagnosis app sends a patient’s symptoms in parallel to three AI models: a small model (fast, low cost), a medium model, and a large model (highest capability). Each model independently generates a diagnosis. An aggregation layer then uses a dedicated judge model to evaluate the three responses and select the most accurate final answer.
Amazon Bedrock supports these patterns by abstracting provider differences and enabling consistent invocation through a unified API. This abstraction plays an important role here.

Answers that highlight flexibility, future-proofing, or the ability to switch models without code changes are usually strong, because they align with Bedrock’s design philosophy. Conversely, options that suggest deep coupling to a specific model provider or imply custom training should raise caution.