---
type: analysis
title: 'Stars, snowflakes, and one big table'
description: 'Warehouse schemas put events in a fact table and the who/what/where/when in dimensions. Star is simpler for analysts; snowflake normalizes dimensions; OBT precomputes the joins.'
tags: [data-intensive-design, data-models, analytics, star-schema, snowflake, obt]
---

# Stars, snowflakes, and one big table

**See also:** [chapter overview](data-models-overview.md) · [relational vs document](relational-vs-document.md) · [data warehousing](operational-vs-analytical.md#data-warehousing) · [MDW modeling hop](mdw-data-journey.md#4-data-modeling) · [Medallion Gold](medallion-gold.md) · [event sourcing](event-sourcing-cqrs.md) · [references](data-models-references.md)

[Data warehouses](operational-vs-analytical.md) are usually relational, and
there are a few widely used conventions for the structure of tables:
**star schema**, **snowflake schema**, dimensional modeling
([14](data-models-references.md)), and **one big table (OBT)**. These
structures are optimized for business analysts. ETL processes translate
data from operational systems into the selected schema.

## Star schema

At the center is a **fact table** (e.g. `fact_sales`). Each row represents
an event that occurred at a particular time — here, a customer’s purchase
of a product. If you were analyzing website traffic rather than retail
sales, each row might represent a page view or a click.

Facts are usually captured as individual events, because that allows
maximum flexibility of analysis later. The fact table can become extremely
large. A big enterprise may have many petabytes of transaction history in
its warehouse, mostly as fact tables.

Some columns in the fact table are attributes: the price at which the
product was sold, the cost of buying it from the supplier (so the profit
margin can be calculated). Other columns are foreign-key references to
**dimension tables**. As each fact row is an event, the dimensions
represent the who, what, where, when, how, and why of the event.

Example: one dimension is the product sold. Each row in `dim_product` is
one type of product — SKU, description, brand, category, fat content,
package size. Each `fact_sales` row uses a foreign key to indicate which
product was sold. Queries often join to multiple dimension tables.

Even date and time are often dimension tables, so additional information
about dates (public holidays) can be encoded, enabling queries that
differentiate holiday vs non-holiday sales.

The name **star schema** comes from the visualization: the fact table in
the middle, surrounded by dimension tables, connections like the rays of a
star.

In a typical warehouse, tables are often quite wide. Fact tables frequently
have over a hundred columns, sometimes several hundred. Dimension tables
can also be wide — all the metadata that may be relevant for analysis. The
`dim_store` table may include which services are offered, whether it has
an in-store bakery, square footage, opening date, last remodel, distance
from the nearest highway.

A star or snowflake schema consists mostly of **many-to-one**
relationships (many sales for one product, in one store), represented as
the fact table having foreign keys into dimensions, or dimensions into
subdimensions. Other relationship types could exist, but they are often
denormalized to simplify queries. If a customer buys several products at
once, that multi-item transaction is not represented explicitly; the fact
table has a separate row for each product purchased, and those facts
happen to share customer ID, store ID, and timestamp.

## Snowflake schema

A variation is the **snowflake schema**, where dimensions are further
broken into subdimensions. There could be separate tables for brands and
product categories; each row in `dim_product` references brand and
category as foreign keys rather than storing them as strings.

Snowflake schemas are more **normalized** than star schemas. Star schemas
are often preferred because they are simpler for analysts to work with
([14](data-models-references.md)).

## One big table (OBT)

Some warehouse schemas take denormalization further and leave out
dimension tables entirely, folding dimension information into denormalized
columns in the fact table — essentially precomputing the join between
facts and dimensions. This is **one big table (OBT)**. It requires more
storage space and sometimes enables faster queries
([15](data-models-references.md)).

In analytics, such denormalization is unproblematic: the data typically
represents a log of historical data that is not going to change (except
maybe for occasionally correcting an error). The consistency and write
overhead issues that occur with denormalization in
[OLTP](relational-vs-document.md#normalization-denormalization-and-joins)
are not as pressing here.

A similarity with [event sourcing](event-sourcing-cqrs.md): both are
collections of events that happened in the past. Differences: fact-table
rows all have the same columns; event sourcing may have many event types,
each with different properties. A fact table is an unordered collection;
in event sourcing the **order** of events matters.

**Architect takeaway:** warehouse layout is an analyst-ergonomics decision
on top of the OLTP/OLAP split. Star keeps dimensions easy to join; snowflake
normalizes them; OBT precomputes the joins. Historical, append-mostly data
makes denormalization cheap here in a way it is not in OLTP.
