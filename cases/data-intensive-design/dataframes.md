---
type: analysis
title: 'DataFrames, matrices, and arrays'
description: 'DataFrames are an analytical wrangling model: relational-like operators plus a path into sparse matrices and arrays that ML and scientific computing expect.'
tags: [data-intensive-design, data-models, dataframes, matrices, analytics, ml]
---

# DataFrames, matrices, and arrays

**See also:** [chapter overview](data-models-overview.md) · [OLTP vs OLAP](operational-vs-analytical.md) · [graph adjacency matrices](graph-data-models.md) · [references](data-models-references.md)

The data models in this chapter are generally used for both transaction
processing and analytics (see
[operational versus analytical systems](operational-vs-analytical.md)).
A few models you are likely to encounter in an **analytical or scientific**
context, but that rarely feature in OLTP systems, include **DataFrames**
and multidimensional arrays of numbers such as **matrices**.

The DataFrame data model is supported by the R language, the Pandas
library for Python, Apache Spark, ArcticDB, Dask, and other systems.
DataFrames are a popular tool for data scientists preparing data for
training ML models, and are also widely used for data exploration,
statistical analysis, visualization, and similar purposes.

At first glance, a DataFrame is similar to a table in a relational
database or a spreadsheet. It supports relational-like operators that
perform bulk operations: applying a function to all rows, filtering by a
condition, grouping by some columns and aggregating others, joining
(typically called **merge**) rows in one DataFrame with another based on a
key.

Instead of a declarative query language such as SQL, a DataFrame is
generally manipulated through a series of commands that modify its
structure and content. This matches the typical workflow of data
scientists, who incrementally **wrangle** the data into a form that
answers the questions they are asking. These manipulations usually take
place on a private copy of the dataset, often on a local machine, although
the end result may be shared.

DataFrame APIs also offer operations that go far beyond what relational
databases offer, and the data model is often used in ways very different
from typical relational modeling ([69](data-models-references.md)). A
common use is to transform data from a relational-like representation into
a **matrix or multidimensional array**, the form in which many ML
algorithms expect their input.

## From ratings table to sparse matrix

A simple example: a relational table of users’ ratings of movies (scale of
1 to 5) transformed into a matrix where each column is a movie and each
row is a user (similar to a pivot table). The matrix is **sparse** — no
data for many user–movie combinations, which is fine. The matrix may have
many thousands of columns and would not fit well in a relational database;
DataFrames and libraries that offer sparse arrays (NumPy for Python) can
handle it easily.

A matrix can contain only numbers. Techniques for turning nonnumerical
data into numbers:

- **Dates** can be scaled to floating-point numbers within a suitable
  range.
- For columns that take one of a small, fixed set of values (movie genre),
  **one-hot encoding** is often used: a column per possible value
  (“comedy,” “drama,” “horror”); each movie row has a 1 in its genre
  column and 0 in the others. This also generalizes to movies that fit
  several genres.

Once the data is a matrix of numbers, it is amenable to **linear algebra**
operations, which form the basis of many ML algorithms. The ratings matrix
could be part of a system for recommending movies the user might like.
DataFrames are flexible enough to let data evolve gradually from a
relational form into a matrix, while giving the data scientist control
over the representation most suitable for the analysis or training goal.

## Array databases and other uses

Some databases, such as TileDB ([70](data-models-references.md)),
specialize in storing large multidimensional arrays of numbers. They are
called **array databases** and are most commonly used for scientific
datasets: geospatial measurements (raster data on a regularly spaced
grid), medical imaging, observations from astronomical telescopes
([71](data-models-references.md)). DataFrames are also used in finance for
time-series data such as asset prices and trades over time
([72](data-models-references.md)). Because of their popularity with data
scientists, DataFrames have been added to batch-processing frameworks such
as Spark and Flink (a later chapter).

**Architect takeaway:** DataFrames are not an OLTP store. They are the
bridge from relational-shaped data into the matrices that ML and
scientific computing consume. Reach for them on the analytical side of the
[OLTP/OLAP split](operational-vs-analytical.md), not as a substitute for
the system of record.
