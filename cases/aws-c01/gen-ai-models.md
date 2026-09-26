---
type: overview
title: 'Introduction to Generative AI'
description: 'Explore the core concepts of generative AI, including how models are trained and fine-tuned to create new content.'
tags: [aws-c01, gen-ai-models, genai]
---

# Introduction to Generative AI

Explore the core concepts of generative AI, including how models are trained and fine-tuned to create new content. Understand key foundation models such as transformers, large language models, multimodal models, and diffusion models. Learn how these architectures work together to enable applications in various domains by generating diverse and contextually relevant outputs.

Generative artificial intelligence (AI) enables machines to create new content, such as images, text, or music, rather than just analyzing existing data. For instance, imagine a system that can generate lifelike artwork in seconds or write a personalized email draft based on minimal input. This groundbreaking technology is already transforming industries like health care, where it helps design new drugs, and entertainment, where it creates realistic visual effects. By bridging creativity and computation, Generative AI is reshaping our thinking about innovation and automation.




How does generative AI work?
Generative AI works by training large neural network models on vast amounts of data to learn patterns, relationships, and structures within the data. During training, the model adjusts its internal parameters to minimize the difference between its output and the actual data, effectively “learning” how to generate outputs that are contextually relevant to the input.

Here’s a breakdown of the process:

Data training: Generative AI models are trained on large datasets, such as text data, language models, or images for visual models. These datasets help the model recognize patterns, syntax, semantics, and even style.
Fine-tuning: After this initial training, the model can be fine-tuned on more specific datasets if needed. This step adjusts the model’s parameters to improve its performance in a particular domain or specific tasks (like medical text generation or creative writing), making it more precise or aligned with specialized use cases.
Generation: Once trained, the model uses probabilities to generate content by predicting the most likely next item in a sequence, like the next word in a sentence or the next pixel in an image. It does this iteratively, building outputs step by step based on prior steps.

How generative AI works

How generative AI works
Through these steps, generative AI can produce new content that resembles the original data it was trained on, making it powerful for creative and functional tasks across different fields. The workings and use cases of different generative AI models often depend on their architecture. Let’s analyze the foundation models of generative AI so that we can build up an understanding of how they work.

Foundation models
Foundation models serve as the base for various applications. These models are characterized by their large scale, pretraining, and adaptability. Foundation models are trained on vast amounts of data, enabling them to learn complex patterns and relationships. This initial training is often followed by fine-tuning for specific tasks, allowing the models to adapt to various domains. Several categories fall under the umbrella of foundation models:

Transformer-based models
Transformer-based models are a neural network architecture used in many foundation models. Introduced in 2017, the transformer architecture is a type of deep learning model architecture that has revolutionized the field of generative AI. They are the building blocks for many advanced AI models, including LLMs. Previously used models, such as RNNs, had difficulty retaining context when processing large inputs. Transformers eliminated this issue by introducing self-attention mechanism, which made them remember the context over a long range of inputs and use it to generate content relevant to the overall context.

Large language models
LLMs are essentially applications of transformer architecture, but they have additional scale, training, and natural language processing specialization, which makes them particularly effective for complex language tasks like language translation, text summarization, code generation, and creative writing. Some key characteristics of LLMs are listed below:

Scale and scope: LLMs are very large-scale implementations of transformers, typically trained with billions (or even trillions) of parameters on extensive text datasets. This scale enables LLMs to capture refined language patterns and general knowledge, making them adept at writing, translation, and reasoning tasks.
Training and adaptation: LLMs undergo extensive pretraining across diverse datasets, enabling them to develop a structural understanding of language. They can then be fine-tuned for various downstream tasks (e.g., summarization, translation) and are often optimized to perform many tasks without additional training.
General-purpose capability: LLMs are designed to be general-purpose models capable of understanding and generating human-like text across different tasks and domains. Due to their comprehensive pretraining, LLMs like ChatGPT can handle diverse language tasks out of the box.
LLMs highlight transformers’ incredible adaptability, showcasing their relevance in NLP.

Multimodal models
Multimodal models expand on LLMs by incorporating multiple data types, such as text-image and text-audio, as well as multimodal fusion. These models leverage the transformer architecture because they can handle large amounts of data and capture complex relationships within and across modalities, such as image-text matching and generating realistic images from text prompts.


Working of a multimodel models

Working of a multimodel models
Multimodal models come with different architecture components based on the task they need to perform:

Transformer-based architectures: Most multimodal models use transformer-based architectures as the backbone because of their flexibility and scalability, for example, Vision Transformers (ViT) for processing images and Text transformers like BERT, GPT, or T5 for processing text. These transformers first process each modality separately (e.g., one transformer for images, another for text) before integrating their outputs.
Modality-specific encoders: Each modality (text, image, or audio) has its own encoder. The text encoder might be based on models like BERT or GPT, while the image encoder might be a Vision Transformer (ViT) or a Convolutional Neural Network (CNN), such as ResNet.These encoders transform raw input (text, image, or other types) into a feature representation that captures the underlying structure of the data.
Fusion mechanisms: After encoding, the representations from each modality need to be fused or combined. This can be done at various stages:
Early fusion: Raw data from each modality is combined and fed into the model at the input level before the separate modality-specific encoders are applied.
Late fusion: Modalities are processed independently, and their representations are combined later in the model (after feature extraction). This approach is used in many multimodal models.
Hybrid fusion: A combination of early and late fusion, where certain features from different modalities are merged at various points during processing, an example of which is cross-modal attention.
Cross-modal attention: Some multimodal models use cross-modal attention mechanisms to allow information from one modality to influence the processing of another modality. For example, a model processing text and images may use attention mechanisms to allow textual information to guide how the image features are interpreted and vice versa. This cross-modal attention helps understand the relationships between the different data types and ensures that relevant features from each modality are properly integrated.
Joint embedding space: A common approach is mapping the different modalities (text, image, etc.) into a shared latent or joint embedding space. This means that features from different modalities are encoded into a common vector space, allowing them to be more easily compared and combined. This allows the model to learn multimodal representations that integrate features from multiple sources (e.g., associating a caption with an image or correlating a spoken question with a visual answer).
Diffusion models
Diffusion models are a distinct generative approach that iteratively refines noise signals until they produce realistic data samples. They are used in machine learning to generate complex data, such as images, audio, and more, by modeling the gradual process of noise removal. These models have recently gained popularity for their ability to generate high-quality, diverse, and detailed outputs and are often used in applications such as image synthesis.

The diffusion process involves a series of steps that refine the input noise. The noise schedule controls the progression of noise levels throughout the diffusion process.

Starting with clean data: The model is given clean data (e.g., an image) as its initial input.
Adding noise: During training, the model gradually adds noise to the clean data over multiple time steps, eventually reaching complete noise. This process is governed by a diffusion metric that controls how much noise to add at each step.
Learning to reverse: For each time step, the model learns to reverse this process by predicting and removing the noise to return to a clean state. After this, the model can effectively generate new data from scratch, guided by the learned patterns, by applying this reverse process to random noise.
Sampling: After training, the model can start with pure noise and apply its learned inverse process to generate new, original data, such as a new image that didn’t exist.

Overview of diffusion model's processing

Overview of diffusion model's processing