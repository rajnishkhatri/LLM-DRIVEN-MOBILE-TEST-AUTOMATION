---
type: reference
title: 'References — storage and retrieval'
description: 'Source citations for the storage-and-retrieval notes (indexes, LSM, B-trees, columnar, search). Dump ends at [7]; [8]–[104] are cited in the body but were not in the source file.'
tags: [data-intensive-design, storage, references]
---

# References — storage and retrieval

Citations used by the [storage overview](storage-overview.md) and the
chapter-4 Concepts. Numbering is **local to this chapter** — it is not
the same list as [trade-off references](references.md),
[NFR references](nfr-references.md), or
[data-model references](data-models-references.md).

The source dump ended at [7]. Body text still cites **[8]–[104]**
(LSM descendants, Bloom filters, compaction, B-tree variants, write
amplification, warehouses, Parquet/ORC, vectorization, cubes, R-trees,
Lucene, embeddings, IVF/HNSW). Those entries are not invented here;
treat those numbers as pointers into the book until a fuller
bibliography is filed.

[1] Nikolay Samokhvalov. “How Partial, Covering, and Multicolumn Indexes May Slow Down UPDATEs in PostgreSQL.” postgres.ai, October 2021. Archived at perma.cc/PBK3-F4G9

[2] Goetz Graefe. “Modern B-Tree Techniques.” Foundations and Trends in Databases, volume 3, issue 4, pages 203–402, August 2011. doi:10.1561/1900000028

[3] Evan Jones. “Why Databases Use Ordered Indexes but Programming Uses Hash Tables.” evanjones.ca, December 2019. Archived at perma.cc/NJX8-3ZZD

[4] Branimir Lambov. “CEP-25: Trie-Indexed SSTable Format.” cwiki.apache.org, November 2022. Archived at perma.cc/HD7W-PW8U (linked Google Doc archived at perma.cc/UL6C-AAAE)

[5] Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, and Clifford Stein. Introduction to Algorithms, 3rd edition. MIT Press, 2009. ISBN: 9780262533058

[6] Branimir Lambov. “Trie Memtables in Cassandra.” Proceedings of the VLDB Endowment, volume 15, issue 12, pages 3359–3371, August 2022. doi:10.14778/3554821.3554828

[7] Dhruba Borthakur. “The History of RocksDB.” rocksdb.blogspot.com, November 2013. Archived at perma.cc/Z7C5-JPSP
