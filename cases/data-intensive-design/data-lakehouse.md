12. Data Lakehouse
I’ve touched briefly on the data lakehouse as a harmonization of the concepts of the data lake and data warehouse. The idea behind a data lakehouse is to simplify things by using just a data lake to store all your data, instead of also having a separate relational data warehouse. To do this, the data lake needs more functionality to replace the features of an RDW. That’s where Databricks’ Delta Lake comes into play.

Delta Lake is a transactional storage software layer that runs on top of an existing data lake and adds RDW-like features that improve the lake’s reliability, security, and performance. Delta Lake itself is not storage. In most cases, it’s easy to turn a data lake into a Delta Lake; all you need to do is specify, when you are storing data to your data lake, that you want to save it in Delta Lake format (as opposed to other formats, like CSV or JSON).

Behind the scenes, when you store a file using Delta Lake format, it is stored in its own specialized way, which consists of Parquet files in folders and a transaction log to keep track of all changes made to the data. While the actual data sits in your data lake in a format similar to what you’re used to, the added transaction log turns it into a Delta Lake, enhancing its capabilities. But this means that anything that interacts with Delta Lake will need to support Delta Lake format; most products do, since it has become very popular.

Delta Lake is not the only option to provide additional functionality to a data lake; two other popular choices are Apache Iceberg and Apache Hudi, which have very similar features. However, in this chapter I’ll focus on Delta Lake.

So far, you’ve learned about the relational data warehouse (Chapter 4), data lake (Chapter 5), modern data warehouse (Chapter 10), and data fabric (Chapter 11). This chapter adds the data lakehouse. Figure 12-1 shows these architectures on a historical timeline.


Figure 12-1. Historical timeline of data architectures

Delta Lake Features

Delta Lake adds several RDW-like features to a data lake. This section will walk you through some of them.

Perhaps the biggest reason companies use Delta Lakes is that they support data manipulation language (DML) commands, such as INSERT, DELETE, UPDATE, and MERGE. These commands simplify complex data management tasks, making data handling more flexible and reliable within Delta Lake. Data lakes do not provide native support for these operations, because data lakes are optimized for batch processing and storing large amounts of data, not for real-time updates.

Updating data in a data lake typically involves reading the entire file, making the necessary updates, and writing the entire updated file back to the data lake, which can take a long time, especially for large files. In contrast, when Delta Lake initially works with a table—essentially a file that is an organized collection of data in rows and columns—it breaks that table down into several smaller digital files for easier management. The result is a Delta Table. Delta Lake then uses a transaction log to track changes, which makes DML commands work much faster due to using optimized storage (columnar storage format), in-memory processing, and optimizations for batch processing. For example, with an UPDATE statement, Delta Lake finds and selects all files containing data that matches the predicate and that therefore need to be updated. It then reads each matching file into memory, updates the relevant rows, and writes out the result into new data files. This updates the data efficiently, without having to rewrite the entire Delta Table. The transaction log maintains a history of changes to the data and ensures that the data is always in a consistent state, even in the case of failures or system crashes.

A common acronym you will hear when dealing with databases is ACID, which stands for atomicity, consistency, isolation, and durability. These are the four properties that ensure the reliability and integrity of a database transaction. They guarantee that a transaction can be completed as a single, reliable operation, with its data changes either fully committed or fully rolled back. While Delta Lake can be said to support ACID transactions, that statement requires qualifying. Unlike processing ACID transactions in a relational database, such as SQL Server, Delta Lake ACID support is constrained to a single Delta Table. Executing DML over more than one Delta Table in a Delta Lake will not guarantee ACID integrity. With a relational database, ACID integrity works with DML transactions that span multiple tables.

Delta Lake also offers “time travel,” a feature that allows you to query data stored in Delta Tables as it existed at a specific point in time. A history of changes to the data is maintained in the Delta transaction log, along with metadata, such as when each change was made and by which user. Users can view and access previous versions of the data, and even revert it to a previous version if necessary. This can be useful for auditing, debugging, or recovering data in the event of unintended data changes or other issues (such as rollbacks).

The “small files” problem, where a large number of small files can slow down read and write operations and increase storage costs, is a common issue in data lakes. Delta Lakes solve this problem by using optimized compaction algorithms to efficiently merge small files into large ones. The compaction process is performed automatically in the background and can be configured to run on a schedule or triggered manually.

With Delta Lake, users can perform both batch processing and real-time streaming on the same data in a Delta Table, eliminating the need to maintain separate data pipelines and systems for batch and streaming processing. This unified solution makes it easier to manage and maintain pipelines and simplifies the data-processing architecture. This also means that Delta Lake supports the Lambda architecture (see Chapter 7).

Schema enforcement is a Delta Table feature that allows you to specify the expected schema for the data in a Delta Table and enforce rules such as nullable constraints, data type constraints, and unique constraints. This ensures that data written to the Delta Table conforms to the specified schema, which helps prevent data corruption. Without schema enforcement, a file with an invalid schema can be added to a folder, which can cause ELT jobs to error out. If incoming data does not match the schema, Delta Lake will reject the write operation and raise an error.

Performance Improvements

Using Delta Lake can improve data lake performance in several ways, including:

Data skipping
Delta Lake can skip over irrelevant data when reading from a Delta Table, which can greatly improve query performance.

Caching
Delta Lake supports data caching in Spark, which can significantly improve the performance of repeated queries.

Fast indexing
Delta Lake uses an optimized indexing structure to quickly locate data, reducing the time required to execute queries.

Query optimization
Delta Lake integrates with Spark SQL and can take advantage of Spark’s query optimization capabilities, resulting in faster and more efficient queries.

Predicate pushdown
Delta Lake supports predicate pushdown, which means that filter conditions are pushed down to the storage layer, reducing the amount of data that needs to be processed.

Column pruning
With column pruning, only the columns required for a specific query are read, reducing the amount of data that needs to be processed.

Vectorized execution
In vectorized execution, multiple data points are processed in a single CPU instruction, leading to improved performance.

Parallel processing
Delta Lake supports parallel processing, which means that multiple tasks can be executed in parallel, leading to improved performance.

Z-order
Z-order, also known as Morton order, is a data-indexing technique used in Delta Lake architectures to organize data for fast, efficient access and querying.

The Data Lakehouse Architecture

In a data lakehouse, data moves through the same five stages you saw with the MDW and data fabric architectures, as Figure 12-2 shows. These are (1) ingestion, (2) storage, (3) transformation, (4) modeling, and (5) visualization.


Figure 12-2. Data lakehouse architecture

As you can see in Figure 12-2, with a data lakehouse architecture, there’s only one repository for your data (the data lake that is using Delta Lake), rather than two (a data lake and a RDW). The RDW is replaced with an optional relational serving layer, described later in this chapter. This solves six problems commonly seen in the MDW and data fabric architectures:

Reliability
Keeping a data lake and an RDW consistent can be a problem, especially if large amounts of data frequently need to be copied from the data lake to the RDW. If the jobs to copy the data fail, do not copy the data accurately, or put the data in the wrong spot in the data lake, this can cause reliability issues. For instance, running reports against the RDW could return different results than running reports against the same data in the data lake. With a data lakehouse, since there is no RDW to copy data to, this is not an issue.

Data staleness
Data in an RDW will be older than the equivalent data in the data lake. How old will depend on how often data is copied from the data lake to the RDW—and to avoid affecting query and report performance, you don’t want to run those jobs too often. As with the reliability issues above, this can result in reports against the RDW and data lake returning different results. With a data lakehouse, since there is no RDW to copy data to, this is not an issue.

Limited support for advanced analytics
Few AI/ML systems and tools work well on RDWs, because data scientists usually prefer working with files in a data lake. They get this with a data lakehouse architecture.

Total cost of ownership
Even though storage is relatively cheap, there are extra costs for the compute needed to copy data to an RDW. Also, the result is two copies of the data, adding extra storage costs. By contrast, in a data lakehouse, there is only one copy of the data. Also, the compute used for queries and reporting in the RDW usually costs much more than the compute used with a data lake. In addition, managing a data lake and managing a RDW are different skill sets, and hiring for both can mean extra costs as well.

Data governance
Having two copies of the data in two different storage environments, possibly with two different types of security, increases the risk of someone seeing data that they should not see. It’s also challenging to ensure that both systems follow the same rules for data quality and data transformations. With a data lakehouse and its one copy of data, these problems do not exist.

Complexity
Managing both a data lake and an RDW can be complex, requiring specialized skills and resources. Since a data lakehouse doesn’t have a RDW, fewer specialized skills are required.

What If You Skip the Relational Data Warehouse?

Here is where we open a can of worms. Not long ago, I would have told you that skipping an RDW in your architecture was a very bad idea. Now, as Delta Lake continues adding RDW-like features to the data lake, I am starting to see more and more use cases where a data lakehouse is the best architecture. The case for using a data lakehouse is especially compelling with smaller datasets. Because most cloud vendors have serverless compute that you can use against a Delta Lake, you can save costs by paying per query. You also save costs by not having to copy data into relational storage, which is more expensive and uses more expensive relational compute. And if you use dedicated compute for an RDW instead of going serverless, you are paying even if you aren’t using that compute. As with any architecture, there are trade-offs and concerns, and it’s very important to be aware of them if you choose not to have an RDW in your architecture.

The first trade-off is that relational database queries are faster than queries against a Delta Lake, especially when your RDW uses MPP technology (see Chapter 7). RDWs have features to improve query performance that aren’t available in a Delta Lake, including:

Advanced indexing (such as clustered columnstore indexes and full-text indexes)

Advanced statistics

Caching (unless you’re using Spark)

Advanced query plan optimization

Materialized views

Advanced join optimization

Some Delta Lake performance features, such as Z-order, can alleviate some of these missing features.

Delta Lake also lacks some of the common staples of RDW security, such as row-level security, column-level security, data-at-rest encryption, column-level encryption, transparent data encryption (TDE), and dynamic data masking (which automatically replaces or obscures portions of the data so that unauthorized users see a masked version of the data instead of the actual sensitive information). Nor does it provide SQL views; referential integrity; workload management; or advanced auditing and compliance features, such as auditing trails, data retention policies, and compliance certifications. RDWs also support higher concurrency than Delta Lake, because they provide advanced features such as advanced locking, isolation levels, and transaction management.

Complexity is also an issue. With an RDW, you have a forced metadata layer—you must create a database, schema, and a table with fields that describe the data type and then load the data (schema-on-write). This means you always have the metadata sitting on top of the actual data. This requires up-front work, but the big benefit is that the metadata and data are always locked together, so it’s easy to use the metadata to find the data. You will never “lose” the metadata, and it will always accurately describe the data. This is hugely different from Delta Lake, which is a folder- and file-based world. That’s the main reason end users who are used to an RDW often struggle with Delta Lake.

In Delta Lake, metadata isn’t required to exist with the data. You might find it in one or more separate files, within the file that contains the data, within the same folder, in a separate folder, or not at all. To top it off, the metadata might be wildly inaccurate, since it doesn’t have the one-to-one relationship with the data that it has in an RDW. You can see how confusing this can be to end users, who might struggle to find the metadata, wrongly decide that there is no metadata, or even use the wrong metadata. Finally, the metadata can fall out of sync with the data when changes are made outside Delta Lake.

Using certain features of Delta Lake architectures could lock you into having to use Spark. Also, if you migrate from a product that uses a SQL version other than Spark SQL, prepare to rewrite your stored procedures, views, report, dashboards, and so on.

If you do need to use Spark SQL, that might mean retraining end users who are already used to interacting with RDWs and familiar with tools for doing so. They may be using ANSI-compliant SQL or an RDW product like T-SQL (which is used with Microsoft products). They are also used to the relational model and know how to quickly query and report off of it. Switching to a folder-file world would likely force them to learn to use new tools; get used to schema-on-read; and learn to handle the issues with the speed, security, missing features, complexity, and SQL changes described earlier. That’s a lot of training.

Existing technology can alleviate some of these concerns and could eventually render them irrelevant. But until that happens, consider them carefully in relation to your needs as you determine whether to use the data lakehouse architecture. For example, if queries to the data lake take an average of five seconds in the data lakehouse architecture, is that a problem? If end users are OK with that, you can ignore this concern, but if they’re using dashboards and need millisecond query response times, you would need to copy the data used for the dashboards into an RDW (meaning you’d end up using an MDW architecture). You could instead use a reporting product that allows you to import data into its memory for millisecond query response times, but the data would not be as updated as it is in Delta Lake, and you would need to refresh the data in the reporting tool’s memory at certain intervals.

Once again, we are talking about trade-offs. If you are an architect, a major part of your role will be identifying products that could be used in each architecture and determining and analyzing their trade-offs to choose the best architecture and products for your particular use case.

None of the above concerns is necessarily a showstopper in itself, but taken in combination, they could provide enough of a reason to use an RDW. A lot of companies start with some proofs of concept to determine whether any of the trade-offs of skipping the RDW will cause an issue. If not, they proceed with a data lakehouse.

Relational Serving Layer

Because Delta Lake is schema-on-read (see Chapter 2), the schema is applied to the data when it is read, not beforehand. Delta Lake is a file-folder system, so it doesn’t provide context for what the data is. (Contrast that with the RDW’s metadata presentation layer, which is on top of and tied directly to the data.) Defined relationships don’t exist within Delta Lake. Each file is in its own isolated island, so you need to create a “serving layer” on top of the data in Delta Lake to tie the metadata directly to the data. To help end users understand the data, you will likely want to present it in a relational data model, so that makes what you’re building a “relational serving layer.” With this layer on top of the data, if you need to join more than one file together, you can define the relationships between them. The relational serving layer can take many forms: a SQL view, a dataset in a reporting tool, an Apache Hive table, or in an ad hoc SQL query. If done correctly, the end user will have no idea they are actually pulling data from a Delta Lake—they will think it is from the RDW.

Many companies create SQL views on top of files in Delta Lake, then use a reporting tool to call those views. This makes it easy for end users to create reports and dashboards.

Even with a relational serving layer, Delta Lake still presents some challenges. The relational serving layer could portray the data incorrectly, for instance, or you could end up with two layers that point to the same data but have different metadata. Metadata not being tied to the data is an inherent problem with Delta Lake. RDWs avoid this problem by having a universal data model that everyone can use.

Summary

This chapter explored the concept of the data lakehouse, focusing on the role of Delta Lake as a transactional storage layer that significantly enhances existing data lakes’ reliability, security, and performance.

You learned about the potential drawbacks associated with bypassing a traditional RDW, with emphasis on challenges related to speed, security, and concurrency. Just be aware of the trade-offs, and if there are no immediate big concerns, then use a data lakehouse until you can’t. If one of those trade-offs becomes too much to overcome for a particular dataset, you can copy that data to an RDW (no need to copy all the data). As technology for Delta Lake, for similar technologies like Apache Iceberg and Apache Hudi, and for storage and compute continues to improve, there will be fewer and fewer reasons to maintain an RDW. Most new data architectures will be data lakehouses.

You saw the unique schema-on-read approach of Delta Lake, where data interpretation occurs at the point of reading, not in advance. You also learned about its file-folder structure, which is devoid of context and thus significantly deviates from the structured metadata presentation layer of an RDW. This necessitates a “relational server layer” for establishing a direct context-based link to the data in Delta Lake.

Rapid technological advancements continue to influence data architecture strategies. A few years ago, omitting an RDW from your architecture would have been considered a significant misstep, but current trends indicate an increasing number of use cases where data lakehouse emerges as the optimal architecture.

All of the architectures I’ve discussed so far are centralized solutions, meaning that source data is copied to a central location owned by IT. You’ll see a major difference in the next chapter, as we discuss the decentralized solution of the data mesh.