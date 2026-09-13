---
type: analysis
title: 'Operational versus analytical systems'
description: 'OLTP serves interactive point queries on current state; OLAP scans history for aggregates. Split them so analytics cannot starve production.'
tags: [data-intensive-design, trade-offs, oltp, olap, data-warehouse, data-lake]
---

# Operational versus analytical systems

**See also:** [chapter overview](overview.md) · [systems of record vs derived data](#systems-of-record-and-derived-data) · [modern data warehouse](mdw-overview.md) · [Medallion](medallion-overview.md) · [law and society](law-and-society.md) · [references](references.md)

If you are working on data systems in an enterprise, you will encounter several
types of people who work with data.

**Backend engineers** build services that handle requests for reading and
updating data. These services often serve external users, either directly or
indirectly via other services (see [microservices](distributed-vs-single-node.md#microservices-and-serverless)). Sometimes services are for internal use by other parts of the organization.

Two other groups typically require access to an organization’s data:

- **Business analysts** generate reports about the activities of the
  organization to help management make better decisions (business intelligence,
  or BI).
- **Data scientists** look for novel insights in data, or create user-facing
  product features enabled by data analysis and machine learning (ML)/AI —
  recommendations, risk scoring, spam filtering, search ranking.

Although business analysts and data scientists tend to use different tools,
they share practices: both perform **analytics** on data that users and backend
services have generated, and they generally do not modify this data (except
perhaps for fixing mistakes), although they might create derived datasets.

This has led to a split used throughout these notes:

- **Operational systems** are the backend services and data infrastructure
  where data is created — for example, by serving external users. Application
  code both reads and modifies the data in its databases, based on user
  actions.
- **Analytical systems** serve business analysts and data scientists. They
  contain a read-only copy of the data from the operational systems, and they
  are optimized for the types of data processing needed for analytics.

As these systems have matured, two specialized roles have emerged: **data
engineers**, who integrate operational and analytical systems and take
responsibility for the organization’s data infrastructure more widely
([3](references.md)), and **analytics engineers**, who model and transform data
to make it more useful for analysts and data scientists ([4](references.md)).

Many engineers specialize in either the operational or the analytical side.
Both play an important role in the lifecycle of data within an organization.

## Characterizing transaction processing and analytics

In the early days of business data processing, a write to the database
typically corresponded to a commercial transaction: making a sale, placing an
order, paying a salary. As databases expanded into areas that didn’t involve
money changing hands, the term **transaction** nevertheless stuck, referring to
a group of reads and writes that form a logical unit. (Used loosely here for
low-latency reads and writes;
[transactions](transactions-overview.md) treat the real isolation
and atomic-commit design.)

Even though databases started being used for posts on social media, moves in a
game, contacts in an address book, and much more, the basic access pattern
remained similar. An operational system typically looks up a small number of
records by a key (**point query**). Records are inserted, updated, or deleted
based on the user’s input. Because these applications are interactive, this
access pattern became known as **online transaction processing (OLTP)**.

Analytics has a very different access pattern. An analytical query usually
scans a huge number of records and calculates aggregate statistics (count, sum,
average) rather than returning individual records. Example questions for a
supermarket chain:

- What was the total revenue of each of our stores in January?
- How many more bananas than usual did we sell during our latest promotion?
- Which brand of baby food is most often purchased together with brand X
  diapers?

To differentiate this pattern from transaction processing, it has been called
**online analytical processing (OLAP)** ([5](references.md)). The difference is
not always clear-cut; typical characteristics:

| Property | Operational systems (OLTP) | Analytical systems (OLAP) |
|---|---|---|
| Main read pattern | Point queries (fetch individual records by key) | Aggregate over a large number of records |
| Main write pattern | Create, update, and delete individual records | Bulk import (ETL) or event stream |
| Human user example | End user of web/mobile application | Internal analyst, for decision support |
| Machine use example | Checking if an action is authorized | Detecting fraud/abuse patterns |
| Type of queries | Fixed, predefined by application | Arbitrary, ad-hoc exploration by analysts |
| Query volume | Lots of small queries | Few queries, each complex |
| Data represents | Latest state (current point in time) | History of events over time |
| Dataset size | Gigabytes to terabytes | Terabytes to petabytes |

*Online* in OLAP is unclear; it probably indicates that queries are not just
for predefined reports, but that analysts use the system interactively for
explorative queries.

With operational systems, users are generally not allowed to construct custom
SQL queries and run them on the database: that would potentially allow them to
read or modify data they do not have permission to access, and they might write
queries expensive enough to affect other users. OLTP systems mostly run fixed
sets of queries baked into application code, with one-off custom queries used
only occasionally for maintenance. Analytical databases usually give users
freedom to write arbitrary SQL by hand, or to generate queries with a
visualization or dashboard tool (Tableau, Looker, Microsoft Power BI).

Another type of system is designed for analytical workloads (aggregates over
many records) but embedded into user-facing products. Systems designed for this
use, known as **product analytics** or **real-time analytics**, include Pinot,
Druid, and ClickHouse ([6](references.md)). They ingest data in real time and
are optimized for low-latency query responses. Traditional OLAP systems
typically ingest data in batches and are optimized for high-throughput query
processing.

## Data warehousing

At first, the same databases were used for both transaction processing and
analytical queries. SQL turned out to be quite flexible in this regard. In the
late 1980s and early 1990s, a trend arose for companies to stop using their
OLTP systems for analytics and to run analytics on a separate database instead.
That separate database was called a **data warehouse**.

A large enterprise may have dozens, even hundreds, of OLTP systems: the
customer-facing website, point-of-sale, inventory, vehicle routing, suppliers,
employees, and many other tasks. Each is complex and needs a team to maintain
it, so they end up operating mostly independently from one another.

It is usually undesirable for business analysts and data scientists to query
these OLTP systems directly:

- The data of interest may be spread across multiple operational systems,
  making it difficult to combine those datasets in a single query (**data
  silos**).
- Schemas and data layouts that are good for OLTP are less well suited for
  analytics.
- Analytical queries can be expensive, and running them on an OLTP database
  would impact performance for other users.
- The OLTP systems might reside in a separate network that users are not
  allowed to access, for security or compliance reasons.

A data warehouse is a separate database that analysts can query without
affecting OLTP operations ([7](references.md)). Warehouses often store data
very differently from OLTP databases, to optimize for analytical queries.

The warehouse contains a read-only copy of the data from all the various OLTP
systems. Data is extracted from OLTP databases (periodic dump or continuous
stream of updates), transformed into an analysis-friendly schema, cleaned up,
and loaded into the warehouse. This process is **extract–transform–load
(ETL)**. Sometimes transform and load are swapped (transformation after
loading), resulting in **ELT**.

In some cases the data sources are external SaaS products (CRM, email
marketing, credit card processing). You do not have direct access to the
original database, only the vendor’s API. Bringing that data into your own
warehouse can enable analyses that are not possible via the SaaS API. ETL for
SaaS APIs is often implemented by specialist data connector services such as
Fivetran, Singer, or Airbyte.

Some database systems offer **hybrid transactional/analytical processing
(HTAP)**, which aims to enable OLTP and analytics in a single system without
requiring ETL ([8](references.md), [9](references.md)). Many HTAP systems
internally consist of an OLTP system coupled with a separate analytical system,
hidden behind a common interface — so the distinction remains important for
understanding how they work.

Even though HTAP exists, it is common to keep transactional and analytical
systems separate because of different goals and requirements. In particular, it
is considered good practice for each operational system to have its own
database (see [microservices](distributed-vs-single-node.md#microservices-and-serverless)), leading to potentially hundreds of separate operational
databases; an enterprise usually has a **single data warehouse**, so that
analysts can combine data from several operational systems in one query.

HTAP therefore does not replace data warehouses. It is useful when the same
application needs both analytical queries that scan a large number of rows
*and* low-latency reads and updates of individual records. Fraud detection can
involve such workloads ([10](references.md)).

The separation between operational and analytical systems is part of a wider
trend. As workloads have become more demanding, systems have become more
specialized and optimized for particular workloads. General-purpose systems can
handle small data volumes comfortably, but the greater the scale, the more
specialized systems tend to become ([11](references.md)).

### From data warehouse to data lake

A data warehouse often uses a relational data model queried through SQL,
perhaps using specialized BI software. That model works well for business
analysts, but it is less well suited to data scientists who need to:

- Transform data into a form suitable for training an ML model — turning rows
  and columns into a vector or matrix of numerical **features**. **Feature
  engineering** commonly requires custom code that is difficult to express in
  SQL.
- Use NLP on textual data (e.g. product reviews) to extract structured
  information (sentiment, topics), or computer vision on photos.

Although there have been efforts to add ML operators to a SQL data model
([12](references.md)) and to build efficient ML systems on a relational
foundation ([13](references.md)), many data scientists prefer Python libraries
such as Pandas and scikit-learn, statistical languages such as R, and
distributed analytics frameworks such as Spark ([14](references.md)).

The answer is a **data lake**: a centralized repository that holds a copy of
any data that might be useful for analysis, obtained from operational systems
via ETL. The difference from a warehouse is that a lake simply contains files,
without imposing a particular file format, data model, or schema
([15](references.md)). Files might be collections of database records encoded
as Avro or Parquet, but a lake can equally well contain text, images, videos,
sensor readings, sparse matrices, feature vectors, genome sequences, or any
other kind of data ([16](references.md)). Besides being more flexible, a lake
is often cheaper than relational storage, since it can use commoditized file
storage such as object stores (see [cloud-native architecture](cloud-vs-self-hosting.md#cloud-native-system-architecture)).

ETL processes have been generalized to **data pipelines**, and in some cases
the lake has become an intermediate stop on the path from operational systems
to the warehouse. The lake contains data in the “raw” form produced by
operational systems, without transformation into a relational warehouse schema.
Each consumer can then transform the raw data into the form that best suits
their needs. It’s sometimes called the **sushi principle**: “raw data is
better” ([17](references.md)). The enterprise composition of that path — lake
for ingest and transform, RDW for serving, a required copy between them — is
the [modern data warehouse](mdw-overview.md).

### Beyond the data lake

As analytics practices have matured, organizations have been paying attention
to the management and operations of analytical systems and data pipelines, as
captured for example in the DataOps Manifesto ([18](references.md)). This has
been driven partly by governance, privacy, and compliance with regulations such
as GDPR and CCPA (see [law and society](law-and-society.md)).

Another factor is that data for analytics is increasingly made available not
only as files and relational tables, but as **streams of events**. With
file-based analysis you can rerun periodically (e.g. daily); stream processing
allows analytical systems to respond on the order of seconds — for example, to
identify and block potentially fraudulent or abusive activity.

In some cases the outputs of analytical systems are made available to
operational systems (**reverse ETL** ([19](references.md))). For example, an ML
model trained on data in an analytical system may be deployed to production so
it can generate recommendations for end users. Specialized tools for this
include TFX, Kubeflow, and MLflow.

## Systems of record and derived data

Related to the operational/analytical split, these notes also distinguish
**systems of record** from **derived data systems**. The terms clarify the flow
of data through a system.

**Systems of record** (also **source of truth**) hold the authoritative or
canonical version of data. When new data comes in — for example, as user input
— it is first written here. Each fact is represented exactly once (the
representation is typically normalized). If there is any discrepancy between
another system and the system of record, the value in the system of record is
(by definition) the correct one.

**Derived data systems** hold the result of taking existing data from another
system and transforming or processing it. If you lose derived data, you can
re-create it from the original source. A classic example is a **cache**: serve
from the cache if present, otherwise fall back to the underlying database.
Denormalized values, indexes, materialized views, transformed representations,
and models trained on a dataset also fall into this category.

Technically, derived data is redundant — it duplicates existing information.
It is often essential for getting good performance on read queries. You can
derive several datasets from a single source, enabling different points of
view.

Analytical systems are usually derived data systems, because they consume data
created elsewhere. Operational services may contain a mixture: the systems of
record are the primary databases to which data is first written; the derived
data systems are the indexes and caches that speed up common reads, especially
queries the system of record cannot answer efficiently.

Most databases, storage engines, and query languages are not inherently systems
of record or derived systems. A database is just a tool; how you use it is up
to you. The distinction depends not on the tool, but on the way you use it in
the application. Being clear about which data is derived from which other data
brings clarity to an otherwise confusing system architecture.

When data in one system is derived from data in another, you need a process for
updating the derived data when the original in the system of record changes.
Unfortunately, many databases assume the application will always use only that
one database, and they do not make it easy to propagate updates across systems.
**Data pipelines** are one approach to composing multiple data systems to
achieve things that one system alone cannot do.

**Architect takeaway:** split OLTP and OLAP by access pattern and audience;
HTAP hides the seam, it does not erase it. Name the system of record
explicitly, and treat caches, indexes, warehouses, and trained models as
derived — rebuildable, and never the place new facts are born.
