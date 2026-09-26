---
type: overview
title: 'AWS Compute Services'
description: 'Explore the key AWS compute services essential for building scalable generative AI solutions.'
tags: [aws-c01, compute, genai]
---

# AWS Compute Services

Explore the key AWS compute services essential for building scalable generative AI solutions. Learn about EC2 instance types, GPU-powered hardware, networking security, and container orchestration to design efficient and secure AI applications on AWS.

As we build generative AI (GenAI) solutions on AWS, the choice of compute service directly impacts the performance, scalability, and cost of our models. While managed services handle these requirements, professional developers often need more control over their environment for custom model hosting, complex RAG (Retrieval-augmented generation) pipelines, or specialized fine-tuning tasks.

Amazon Elastic Compute Cloud (EC2) is a resizable cloud computing capacity. It allows users to run virtual servers, known as instances, for various computing tasks. EC2 offers a secure, flexible, and scalable solution that enables developers to easily deploy, manage, and scale applications without the need for physical hardware investment.

Core concepts of EC2 instances
Amazon Elastic Compute Cloud (EC2) offers various benefits beyond providing flexible computing capacity. It enables us to deploy instances across multiple Availability Zones (AZs) within a region, integrated with services such as Elastic Load Balancing and Auto Scaling groups, to provide high availability within a region.

Here are some core concepts of Amazon Elastic Compute Cloud.

What is an EC2 instance?
An EC2 instance is a virtual server in the cloud. It can run different operating systems, including Linux, Windows, and CentOS. Instances are categorized by their computing power, memory, and networking capabilities. We can select any instance type based on our requirements.

Each instance contains a root volume that is used to boot the instance. After launching, an instance operates similarly to a server and continues running until it is stopped, hibernated, terminated, or fails.

To launch an EC2 instance, we must define its core configuration, including:

Amazon Machine Image (AMI): An AMI is a preconfigured template that includes the operating system and required software, serving as a blueprint for launching EC2 instances. Multiple instances can be created from the same AMI, enabling consistent environments and easy scaling.
Instance types: Instance types define the hardware configuration of an EC2 instance, including CPU, memory, storage, and networking capacity. AWS provides a wide range of instance types optimized for different workloads, such as general-purpose, compute-optimized, memory-optimized, and accelerated computing instances.



Another customizable option in EC2 is the placement groups. Placement groups influence how EC2 instances are placed within AWS infrastructure to optimize performance or resilience. They are commonly used to achieve low-latency, high-throughput networking between instances or to distribute instances across underlying hardware for fault tolerance.

Networking and security of EC2
When working with Amazon EC2, security and networking are built on the shared responsibility model.

AWS is responsible for securing the underlying cloud infrastructure, including physical data centers, hardware, and the virtualization layer.
We are accountable for how resources are configured, networked, and protected within that infrastructure.
Here’s a quick review of networking components associated with EC2:

Virtual Private Cloud (VPC): EC2 instances are launched within a VPC, which provides logical isolation from other AWS environments. By placing instances in private subnets, we can prevent direct internet access and reduce the attack surface at the network level.
Elastic Network Interface (ENI): Each EC2 instance is connected to the VPC through one or more ENIs, which provide network connectivity. ENIs have private IP addresses, can be assigned public IPs when needed, and serve as the attachment point for security rules and routing.
Security groups: Security groups function as stateful virtual firewalls attached to ENIs. They define inbound and outbound rules that control which IP addresses, protocols, and ports are allowed to communicate with the EC2 instance, enforcing instance-level network security.

The hierarchical structure of an EC2 instance deployment within the AWS Cloud ecosystem

The hierarchical structure of an EC2 instance deployment within the AWS Cloud ecosystem
Together, VPC isolation and security groups form the foundation of EC2 networking and security, allowing us to control access, reduce attack surfaces, and build secure cloud environments.

Using Amazon EC2 for high-performance AI workloads
Amazon Elastic Compute Cloud (EC2) provides the raw processing power required to handle the computational demands of large language models (LLMs) and other foundation models. It allows us to select the required hardware configuration needed for self-hosting models and data preprocessing, and utilizes specialized hardware accelerators

In the context of generative AI development, we primarily focus on three categories of EC2 instances:

GPU-powered instances: Utilizing NVIDIA hardware (such as the P5 or G5 families), these instances are the industry standard for general-purpose model training and high-performance inference.
AWS Trainium: These are purpose-built chips designed specifically for high-performance deep learning training, offering a more cost-effective alternative to GPUs for large-scale model optimization.
AWS Inferentia: Designed specifically for model inference, these instances (such as Inf2) provide high throughput and the lowest cost per inference in the cloud, making them ideal for serving production-ready GenAI applications.
Elastic Fiber Adapter
For high-performance computing and large-scale machine learning workloads, tasks are often distributed across multiple EC2 instances that must exchange data frequently and efficiently. In a traditional EC2 software stack, networking traffic passes through the standard operating system network stack and the virtualized network interface, which can introduce additional latency and limit throughput for tightly coupled workloads.

When EC2 instances are configured with Elastic Fabric Adapter (EFA), the networking stack changes significantly. EFA enables instances to bypass parts of the operating system’s networking stack and communicate directly with the underlying network hardware using a specialized interface. This results in much lower latency and higher bandwidth, which is critical for workloads such as distributed model training, parallel simulations, and MPI-based applications. By allowing data to flow between instances almost as fast as the processors can consume it, EC2 with EFA delivers the performance needed for scalable, compute-intensive applications.


Traditional EC2 software stack compared with EC2 using Elastic Fabric Adapter (EFA)

Traditional EC2 software stack compared with EC2 using Elastic Fabric Adapter (EFA)
Orchestrating generative AI with containers and microservices
While EC2 provides the raw power, containerization offers the portability and consistency necessary for modern software development. In a generative AI architecture, we rarely run a model in isolation; instead, we build microservices that handle everything from prompt orchestration to vector database queries. By using containers, we ensure that our AI application runs the same way in our development environment as it does in production.

AWS offers two primary paths for orchestrating our GenAI containers:

Amazon Elastic Container Service (ECS): A highly simplified, powerful orchestration service that is excellent for developers who want a “serverless” experience via AWS Fargate. It is often our go-to for standard RAG applications and API wrappers.
Amazon Elastic Kubernetes Service (EKS): The choice for teams that require the flexibility of the Kubernetes ecosystem. We use EKS when we need to leverage open-source tools such as Ray for distributed training or Kubeflow for end-to-end ML pipelines.

Deploying containerized ML application using ECS

Deploying containerized ML application using ECS
Using containers also allows us to use AWS Deep Learning Containers (DLCs). These are pre-configured Docker images provided by AWS that come pre-installed with deep learning frameworks (such as PyTorch or TensorFlow) and the necessary drivers for NVIDIA GPUs or AWS Neuron (for Trainium/Inferentia). This significantly reduces the time we spend on environment setup and installing dependencies.

Practical applications of compute in GenAI development
To see these concepts in action, we can look at a typical production-grade generative AI workflow. Consider building a custom document analysis tool that uses a self-hosted Llama 3 model for sensitive data processing. We design a resilient system using EC2 and containers to meet performance and security requirements.


Production-grade generative AI workflow

Production-grade generative AI workflow
In this scenario, we follow these steps:

Model hosting: We deploy our model using a Deep Learning Container on an Amazon EC2 Inf2 instance, ensuring the lowest possible latency for our end users.
API orchestration: We wrap the model in a Python-based API (such as FastAPI) and run it on Amazon ECS with Fargate, allowing us to scale the API layer independently of the heavy model compute.
Networking: We place all resources in a private subnet within our VPC, using VPC Endpoints to securely communicate with other services such as Amazon S3 or Bedrock without ever touching the public internet.
By separating the model on EC2 from the API on containers, we create a modular architecture that is easier to debug, update, and scale.