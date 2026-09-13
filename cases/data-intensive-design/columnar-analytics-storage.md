---
type: analysis
title: 'Column-oriented storage for analytics'
description: 'Warehouses scan few columns over many rows. Store columns separately, compress with bitmaps, sort for runs, write in bulk via a log-structured path.'
tags: [data-intensive-design, storage, columnar, analytics, parquet, warehouse]
---

# Column-oriented storage for analytics

**See also:** [chapter overview](storage-overview.md) · [OLTP vs OLAP](operational-vs-analytical.md#characterizing-transaction-processing-and-analytics) · [data warehousing](operational-vs-analytical.md#data-warehousing) · [modern data warehouse](mdw-overview.md) · [stars and snowflakes](star-snowflake-analytics.md) · [cloud native](cloud-vs-self-hosting.md#cloud-native-system-architecture) · [references](storage-references.md)

The warehouse data model is usually relational: SQL fits analytical
queries, and graphical tools generate SQL for drill-down and slice-and-
dice.

On the surface a warehouse and an OLTP RDBMS both speak SQL. Internally
they are optimized for different access patterns. Many vendors now
focus on one or the other, not both.

Some products (Microsoft SQL Server, SAP HANA, SingleStore) still claim
both. Those **HTAP** systems
([introduced with warehousing](operational-vs-analytical.md#data-warehousing))
are increasingly **two engines behind one SQL interface**
([50](storage-references.md), [51](storage-references.md),
[52](storage-references.md), [53](storage-references.md)).

## Cloud data warehouses

Established vendors (Teradata, Vertica, SAP HANA) offer on-premises
and cloud. Cloud-only warehouses — BigQuery, Redshift, Snowflake —
became widely adopted as customers moved. They can use object storage
and serverless compute.

Cloud warehouses tend to integrate with the rest of the cloud (log
ingestion, Dataflow, Kinesis) and are more elastic because they
**decouple query compute from storage**
([54](storage-references.md)). Data lives in object storage, not on
local disks, so you scale capacity and query compute independently —
the [cloud-native](cloud-vs-self-hosting.md#cloud-native-system-architecture)
pattern.

Open-source warehouses (Hive, Trino, Spark) have followed data lakes
onto object storage and **broken apart**
([55](storage-references.md)). Pieces that used to be one system
(Hive) are now separate:

**Query engine.** Trino, Apache DataFusion, Presto parse SQL, plan,
and execute — usually as parallel distributed tasks. Some engines run
tasks themselves; others use Spark or Flink.

**Storage format.** How rows become bytes in a file, typically on
object storage or a distributed filesystem
([12](storage-references.md)). The lake can then be read by the query
engine *and* other apps. Parquet, ORC, Lance, Nimble — see below.

**Table format.** Parquet-like files are immutable once written.
Inserts and deletes need a table format (Apache Iceberg, Databricks
Delta) that says which files constitute a table and what the schema
is. Extra features: time travel, GC, even transactions.

**Data catalog.** Which tables are in the database — create, rename,
drop. Unlike storage and table formats, catalogs (Snowflake Polaris,
Databricks Unity Catalog) usually run as a standalone REST service.
Iceberg also offers a catalog (in-process or separate). Query engines
read the catalog on read/write. Decoupling catalogs from engines lets
discovery and governance
([law and society](law-and-society.md)) see the same metadata.

## Column-oriented storage

Warehouse schemas put events in a wide
[fact table](star-snowflake-analytics.md) with foreign keys into
dimensions. Facts can be trillions of rows; dimensions are usually
millions and more manageable. This section is about storing facts.

A typical warehouse query touches only four or five of a hundred-plus
columns (`SELECT *` is rare in analytics)
([52](storage-references.md)). Example: fruit vs candy by weekday in
2024 needs `date_key`, `product_sk`, and `quantity` from `fact_sales`
— nothing else.

```sql
SELECT
  dim_date.weekday, dim_product.category,
  SUM(fact_sales.quantity) AS quantity_sold
FROM fact_sales
  JOIN dim_date    ON fact_sales.date_key   = dim_date.date_key
  JOIN dim_product ON fact_sales.product_sk = dim_product.product_sk
WHERE
  dim_date.year = 2024 AND
  dim_product.category IN ('Fresh fruit', 'Candy')
GROUP BY
  dim_date.weekday, dim_product.category;
```

**Row-oriented** OLTP (and document stores) keep all values of one
row (or one document) together. An index on `date_key` or
`product_sk` finds the matching rows, but the engine still loads
every attribute of those rows, parses them, and filters. That is
slow at warehouse scale.

**Column-oriented** storage stores all values of each column together
instead ([56](storage-references.md)). The query reads and parses only
the columns it uses. Columns stay in the **same row order**, so the
23rd entry of each column is the 23rd row.

In practice the table is broken into **blocks** of thousands or
millions of rows, and within each block columns are stored separately
([60](storage-references.md)). Blocks are often one timestamp range,
so a date-filtered query loads only overlapping blocks.

Columnar storage is now the default in analytical systems
([60](storage-references.md)): Snowflake
([61](storage-references.md)), DuckDB
([62](storage-references.md)), Pinot
([63](storage-references.md)), Druid
([64](storage-references.md)); file formats Parquet, ORC
([65](storage-references.md), [66](storage-references.md)), Lance
([67](storage-references.md)), Nimble
([68](storage-references.md)); in-memory Arrow
([65](storage-references.md), [69](storage-references.md)) and
Pandas/NumPy ([70](storage-references.md)); time-series stores such as
InfluxDB IOx ([71](storage-references.md)) and TimescaleDB
([72](storage-references.md)).

Parquet is columnar and still supports a document model
([57](storage-references.md)) via Dremel-style shredding / striping
([58](storage-references.md), [59](storage-references.md)).

Do not confuse this with the **wide-column / column-family** model
(Bigtable, Accumulo, HBase): a row may have thousands of columns and
rows need not share the same set ([9](storage-references.md)). Despite
the name, those systems are **row-oriented** — they store a row’s
values together.

## Column compression

Columns compress well: lots of repetition
([73](storage-references.md)). **Bitmap encoding** is particularly
effective in warehouses.

When distinct values in a column are few relative to row count
(billions of sales, 100,000 products), turn the column into *n*
bitmaps — one per distinct value, one bit per row. Sparse bitmaps
(lots of 0s) can be **run-length encoded**. Roaring bitmaps switch
between representations, whichever is more compact
([74](storage-references.md)).

Warehouse predicates become bitwise ops on those bitmaps:

- `WHERE product_sk IN (31, 68, 69)` — load three bitmaps, OR them.
- `WHERE product_sk = 30 AND store_sk = 3` — AND the two bitmaps.
  This works because columns share row order, so the *k*th bit is
  the same row in every column.

Bitmaps can also answer some graph queries (users followed by X who
also follow Y ([75](storage-references.md))).

## Sort order in column storage

Row order does not have to be insertion order. You cannot sort each
column independently — then you would not know which items belong to
the same row. Sort **entire rows**, then store by column.

Pick sort keys from common queries. If queries target recent dates,
`date_key` first: scan last month, not all rows. A second key
(`product_sk`) groups same-product sales on the same day — good for
group/filter-by-product in a date range.

Sorting also helps compression. The first sort key, if low-cardinality,
becomes long runs of the same value — run-length encoding can shrink
it to kilobytes even on billions of rows. The effect is strongest on
the first key; later keys look more random and compress less.

## Writing to column-oriented storage

Warehouse reads are aggregations over many rows
([characterizing OLTP vs analytics](operational-vs-analytical.md#characterizing-transaction-processing-and-analytics)).
Columnar layout, compression, and sort all help those reads.

Writes tend to be **bulk ETL**. Inserting one row into the middle of
a sorted, compressed table means rewriting columns from that point
onward. A bulk write of many rows amortizes that cost.

A [log-structured](log-structured-storage.md) path is common: writes
land in a row-oriented, sorted in-memory store; when enough have
accumulated they merge into new column-encoded files. Old files stay
immutable, so object storage fits. Queries see both on-disk columns
and in-memory recent writes; the engine hides the split. Snowflake,
Vertica, Pinot, Druid, and others do this
([61](storage-references.md), [63](storage-references.md),
[64](storage-references.md), [76](storage-references.md)).
