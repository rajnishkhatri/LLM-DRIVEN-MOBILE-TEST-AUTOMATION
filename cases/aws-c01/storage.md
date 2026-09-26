---
type: overview
title: 'AWS Storage Services'
description: 'Explore the key AWS storage services essential for generative AI development, including Amazon S3, EFS, and DynamoDB.'
tags: [aws-c01, storage, genai]
---

# AWS Storage Services

Explore the key AWS storage services essential for generative AI development, including Amazon S3, EFS, and DynamoDB. Understand how to manage large datasets, enable distributed training, and maintain real-time conversational memory to build resilient and efficient AI systems on AWS.

In generative AI (GenAI) development, our models are only as good as the data that feeds them and the context they can remember. Therefore, it’s important to choose the right storage layer that matches the data’s access pattern to the speed and cost requirements of our application. As we build GenAI systems, we have to manage large training datasets, shared configuration files across distributed compute clusters, and efficient state management for user conversations.

In this lesson, we will examine how we use the AWS storage services to create a resilient, context-aware AI infrastructure.

Building a data foundation with Amazon S3
Amazon Simple Storage Service (S3) is an object storage service designed to store and retrieve any amount of data from anywhere. A single bucket can store any type of data, including files, images, videos, and more.




Each bucket is assigned a globally unique name and tied to a specific AWS Region. Therefore, it provides a secure, structured namespace for managing everything from raw datasets to finalized model artifacts.

Amazon S3 offers several advanced features:

Storage classes: We use S3 Standard for frequently accessed training data, while S3 Intelligent-Tiering can automatically move aging datasets to lower-cost tiers like Glacier without impacting retrieval speed when we need to re-run an experiment.
S3 Express One Zone: This is a high-performance storage class we use for our most latency-sensitive ML/AI training jobs. It provides single-digit millisecond data access, which is critical when we are saturating thousands of GPUs during a large-scale fine-tuning run.
Object versioning: We enable this to track changes to our model checkpoints. If a new fine-tuning run results in a degraded model, versioning allows us to quickly roll back to a good set of weights.
In addition to these, S3 also offers S3 vector buckets for GenAI applications. It enables a bucket to act as a native vector store, allowing us to store and query vector embeddings directly in S3. This reduces the complexity of our architecture by allowing us to manage our knowledge base and its mathematical representations within a single service.


Storing vector embeddings in S3 vectors bucket

Storing vector embeddings in S3 vectors bucket
We use S3’s virtually unlimited scalability to ensure that as our foundation models (FMs) become more data-hungry, our infrastructure never becomes a bottleneck. Within the AI ecosystem, S3 is typically used for:

Data lake staging: We use buckets to ingest and store the vast amounts of raw text, images, or video required for pre-training or fine-tuning.
Model registry: S3 serves as the authoritative repository for our model weights and checkpoints, enabling us to version and track model evolution.
RAG knowledge bases: With recent innovations, S3 integrates directly with GenAI workflows as a source for retrieval-augmented generation (RAG), storing documents that provide real-time context for our models.
Enabling distributed training with Amazon EFS
Amazon Elastic File System (EFS) is a serverless, fully managed, and elastic file system that provides a shared storage layer accessible via the standard Network File System (NFSv4) protocol. It enables thousands of compute instances, including EC2, ECS, and EKS, to concurrently read and write to the same data while automatically replicating it across multiple Availability Zones for high availability and durability.




Many distributed compute workloads require a traditional file system structure. This is particularly useful to run distributed training across a cluster of G5 or P5 instances.

To understand how EFS powers our AI workflows, we must look at its core operational components:

Mount targets and VPC integration: EFS volumes are created within a VPC and connect to our compute resources using mount targets. A mount target provides a specific IP address for the NFS endpoint. To maintain high availability across multiple Availability Zones (AZs), we create a mount target in each AZ where our compute resources reside.
Parallel access and consistency: One of the most critical features for AI is that EFS allows multiple services to connect simultaneously. Because distributed training involves many nodes writing logs or reading checkpoints simultaneously, EFS implements a file-locking mechanism to ensure data consistency across all connected resources.
Linux compatibility: It is important to remember that EFS is specifically designed to be mounted to Linux-based EC2 instances, which aligns perfectly with the vast majority of deep learning environments and containers.
As AI practitioners, we often choose Amazon EFS because it is designed for high concurrency and shared access across multiple compute resources. EFS allows multiple instances or nodes to read from and write to the same file system simultaneously, making it ideal for distributed training and collaborative environments. In practice, we commonly use EFS to store shared codebases, configuration files, and Python virtual environments, ensuring that every worker node in a training cluster runs an identical software stack without requiring manual file synchronization.

This shared file system approach simplifies cluster management, reduces configuration drift, and improves reproducibility across training jobs. It is particularly effective in managed machine learning environments such as Amazon SageMaker, where multiple users or workloads may need consistent access to the same resources.

The illustration below demonstrates how Amazon EFS can be mounted across multiple user profiles within a SageMaker domain, or shared across multiple SageMaker domains within the same VPC, enabling secure and consistent access to common data and environments.


Using EFS for shared development environment

Using EFS for shared development environment
In addition to this, EFS is preferred by AI developers due to its ability to:

Provide Elastic throughput: AI workloads spike quite frequently. EFS can automatically scale throughput to handle high-demand data-loading periods and scale back down when our models are just processing, helping us manage costs effectively.
Mounting to containers: When we use Amazon ECS or EKS for our GenAI microservices, we mount EFS volumes directly into our containers. This provides a persistent storage layer that survives even if a container crashes or is rescheduled.
Using EFS eliminates data duplication. Instead of copying a 50GB dataset to every local EBS volume across 10 EC2 instances, we store it once in EFS and mount it on all instances. This not only saves money but also simplifies our data management and synchronization logic.

Managing conversation state with Amazon DynamoDB
Amazon DynamoDB is a NoSQL key-value database that provides single-digit millisecond performance at any scale. DynamoDB automatically replicates our data across three Availability Zones within an AWS Region, ensuring the high availability and durability necessary for production-grade AI systems.

To effectively manage and structure our data, we work with three primary components:

Tables: This is the top-level entity that stores related data, such as all conversations for a specific chatbot.
Items: These represent the individual records within a table. Each item is unique and can have a different set of attributes, allowing us to store diverse interaction types in a single table.
Attributes: These are the basic building blocks of an item. These are similar to columns in a relational database, but do not need to be predefined across all items.
Beyond simple storage, DynamoDB provides built-in encryption and the ability to scale up or down without downtime.

Organizing data with keys and secondary indexes
In a professional GenAI pipeline, we must be able to retrieve user history with extreme efficiency to provide real-time context to our AI models. DynamoDB uses primary keys to uniquely identify each item and manage data distribution. A primary key can be a simple partition key (using a single attribute like a UserID) or a composite key (combining a partition key with a sort key, such as SessionID and Timestamp).

When our access patterns become more complex, for example, if we need to search for conversations by intent rather than just by user, we utilize secondary indexes:

Global Secondary Indexes (GSI): These allow us to query data using partition and sort keys that are different from the base table’s primary keys. This is useful for cross-session analytics or searching by specific AI-generated metadata.
Local Secondary Indexes (LSI): These maintain the same partition key as the table but use a different sort key, which is helpful for alternative sorting within a single session (e.g., sorting by sentiment score instead of timestamp).
For truly global AI applications, we can use DynamoDB global tables. This feature provides a multi-region, multi-active database that automatically replicates our data across the AWS Regions of our choice.

DynamoDB in GenAI applications
The most powerful GenAI applications are those that feel interactive and personal. To achieve this, our applications must maintain memory of previous user interactions. DynamoDB is typically used to store the state of our application, specifically, the conversation history and user session metadata.

In a professional GenAI pipeline, we use DynamoDB to build short-term memory for our agents:

Conversation history storage: Every turn in a chat, the user’s prompt and the model’s response are stored as an item in a DynamoDB table. We typically use a SessionID as the partition key and a Timestamp as the sort key to quickly retrieve the last few messages to provide as context in the next model call.

A Lambda function based chat bot by storing chat history in DynamoDB table

A Lambda function based chat bot by storing chat history in DynamoDB table
Time to live (TTL): To keep our database lean and comply with privacy regulations, we use TTL to automatically delete old conversation histories after a set period (e.g., 30 days), ensuring we don’t pay for data we no longer need.
Low latency at scale: When millions of users interact with our bot simultaneously, DynamoDB ensures that retrieving the conversation context doesn’t become a bottleneck, preventing the model from lagging in its responses. However, certain real-time AI use cases, such as high-frequency trading bots, may require even faster performance. Amazon DynamoDB Accelerator (DAX) is an in-memory caching solution that sits between our application and our database. By bringing frequently accessed data into memory, DAX delivers microsecond response times, even at millions of requests per second.
To maintain context, we often use AWS Step Functions to create workflows that fetch history from DynamoDB, send it to Amazon Comprehend to detect the user’s intent or sentiment, and then feed that enriched context into our FM. This multi-service memory enables an AI application to handle complex, multi-step user requests without losing the thread of the conversation.

Bringing it together
Amazon S3, DynamoDB, and Amazon EFS are highly scalable, highly available, and highly resilient AWS storage services. However, each is optimized for different access patterns and workloads. The table below summarizes when to choose each service based on your use case:

Storage Service
Use Case
Explanation
Amazon S3
Training datasets, fine-tuning data, model artifacts, RAG knowledge bases, vector embeddings
Provides virtually unlimited scalability, high durability, cost-efficient storage, and is optimized for large, immutable datasets and retrieval-based workflows
Amazon S3 Vector Buckets
Vector embeddings for RAG and semantic search
Native vector storage and querying simplifies GenAI architectures by keeping documents and embeddings in a single service
Amazon EFS
Shared codebases, configuration files, checkpoints, distributed training environments
Provides a shared, POSIX-compliant file system with high concurrency and consistent access across multiple compute nodes
Amazon DynamoDB
Conversation state, session metadata, short-term memory for agents
Delivers single-digit millisecond latency at scale for predictable, key-based access patterns
Amazon DynamoDB + DAX
Ultra-low-latency conversational memory
In-memory caching enables microsecond reads for high-throughput, latency-sensitive AI applications

