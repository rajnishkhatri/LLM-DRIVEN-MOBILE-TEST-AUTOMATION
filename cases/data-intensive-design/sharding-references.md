---
type: reference
title: 'References — sharding'
description: 'Source citations for the sharding notes (key-range, hash, consistent hashing, hot spots, routing, local and global secondary indexes). Numbering is local to this chapter; the dump included [1]–[33].'
tags: [data-intensive-design, sharding, references]
---

# References — sharding

Citations used by the [sharding overview](sharding-overview.md)
and the chapter-7 Concepts. Numbering is **local to this chapter** —
it is not the same list as [trade-off references](references.md),
[NFR references](nfr-references.md),
[data-model references](data-models-references.md),
[storage references](storage-references.md),
[encoding references](encoding-references.md), or
[replication references](replication-references.md).

The source dump included the full set **[1]–[33]**.

[1] Claire Giordano. “Understanding Partitioning and Sharding in Postgres and Citus.” citusdata.com, August 2023. Archived at perma.cc/8BTK-8959

[2] Brandur Leach. “Partitioning in Postgres, 2022 Edition.” brandur.org, October 2022. Archived at perma.cc/Z5LE-6AKX

[3] Raph Koster. “Database ‘Sharding’ Came from UO?” raphkoster.com, January 2009. Archived at perma.cc/4N9U-5KYF

[4] Garrett Fidalgo. “Herding Elephants: Lessons Learned from Sharding Postgres at Notion.” notion.com, October 2021. Archived at perma.cc/5J5V-W2VX

[5] Ulrich Drepper. “What Every Programmer Should Know About Memory.” akkadia.org, November 2007. Archived at perma.cc/NU6Q-DRXZ

[6] Jingyu Zhou, Meng Xu, Alexander Shraer, Bala Namasivayam, Alex Miller, Evan Tschannen, Steve Atherton, Andrew J. Beamon, Rusty Sears, John Leach, Dave Rosenthal, Xin Dong, Will Wilson, Ben Collins, David Scherer, Alec Grieser, Young Liu, Alvin Moore, Bhaskar Muppana, Xiaoge Su, and Vishesh Yadav. “FoundationDB: A Distributed Unbundled Transactional Key Value Store.” At ACM International Conference on Management of Data (SIGMOD), June 2021. doi:10.1145/3448016.3457559

[7] Marco Slot. “Citus 12: Schema-Based Sharding for PostgreSQL.” citusdata.com, July 2023. Archived at perma.cc/R874-EC9W

[8] Robisson Oliveira. “Reducing the Scope of Impact with Cell-Based Architecture.” AWS Well-Architected White Paper, Amazon Web Services, September 2023. Archived at perma.cc/4KWW-47NR

[9] Gwen Shapira. “Things DBs Don’t Do—But Should.” thenile.dev, February 2023. Archived at perma.cc/C3J4-JSFW

[10] Malte Schwarzkopf, Eddie Kohler, M. Frans Kaashoek, and Robert Morris. “Position: GDPR Compliance by Construction.” At Towards Polystores That Manage Multiple Databases, Privacy, Security and/or Policy Issues for Heterogenous Data (Poly), August 2019. doi:10.1007/978-3-030-33752-0_3

[11] Gwen Shapira. “Introducing pg_karnak: Transactional Schema Migration Across Tenant Databases.” thenile.dev, November 2024. Archived at perma.cc/R5RD-8HR9

[12] Arka Ganguli, Guido Iaquinti, Maggie Zhou, and Rafael Chacón. “Scaling Datastores at Slack with Vitess.” slack.engineering, December 2020. Archived at perma.cc/UW8F-ALJK

[13] Ikai Lan. “App Engine Datastore Tip: Monotonically Increasing Values Are Bad.” ikaisays.com, January 2011. Archived at perma.cc/BPX8-RPJB

[14] Enis Soztutar. “Apache HBase Region Splitting and Merging.” cloudera.com, February 2013. Archived at perma.cc/S9HS-2X2C

[15] Eric Evans. “Rethinking Topology in Cassandra.” At Cassandra Summit, June 2013. Archived at perma.cc/2DKM-F438

[16] Martin Kleppmann. “Java’s hashCode Is Not Safe for Distributed Systems.” martin.kleppmann.com, June 2012. Archived at perma.cc/LK5U-VZSN

[17] Mostafa Elhemali, Niall Gallagher, Nicholas Gordon, Joseph Idziorek, Richard Krog, Colin Lazier, Erben Mo, Akhilesh Mritunjai, Somu Perianayagam, Tim Rath, Swami Sivasubramanian, James Christopher Sorenson III, Sroaj Sosothikul, Doug Terry, and Akshat Vig. “Amazon DynamoDB: A Scalable, Predictably Performant, and Fully Managed NoSQL Database Service.” At USENIX Annual Technical Conference (ATC), July 2022.

[18] David Karger, Eric Lehman, Tom Leighton, Rina Panigrahy, Matthew Levine, and Daniel Lewin. “Consistent Hashing and Random Trees: Distributed Caching Protocols for Relieving Hot Spots on the World Wide Web.” At 29th Annual ACM Symposium on Theory of Computing (STOC), May 1997. doi:10.1145/258533.258660

[19] Damian Gryski. “Consistent Hashing: Algorithmic Tradeoffs.” dgryski.medium.com, April 2018. Archived at perma.cc/B2WF-TYQ8

[20] David G. Thaler and Chinya V. Ravishankar. “Using Name-Based Mappings to Increase Hit Rates.” IEEE/ACM Transactions on Networking, volume 6, issue 1, pages 1–14, February 1998. doi:10.1109/90.663936

[21] John Lamping and Eric Veach. “A Fast, Minimal Memory, Consistent Hash Algorithm.” arXiv:1406.2294, June 2014.

[22] Samuel Axon. “3% of Twitter’s Servers Dedicated to Justin Bieber.” mashable.com, September 2010. Archived at perma.cc/F35N-CGVX

[23] Gerald Guo and Thawan Kooburat. “Scaling Services with Shard Manager.” engineering.fb.com, August 2020. Archived at perma.cc/EFS3-XQYT

[24] Sangmin Lee, Zhenhua Guo, Omer Sunercan, Jun Ying, Thawan Kooburat, Suryadeep Biswal, Jun Chen, Kun Huang, Yatpang Cheung, Yiding Zhou, Kaushik Veeraraghavan, Biren Damani, Pol Mauri Ruiz, Vikas Mehta, and Chunqiang Tang. “Shard Manager: A Generic Shard Management Framework for Geo-Distributed Applications.” At 28th ACM SIGOPS Symposium on Operating Systems Principles (SOSP), October 2021. doi:10.1145/3477132.3483546

[25] Scott Lystig Fritchie. “A Critique of Resizable Hash Tables: Riak Core & Random Slicing.” infoq.com, August 2018. Archived at perma.cc/RPX7-7BLN

[26] Andy Warfield. “Building and Operating a Pretty Big Storage System Called S3.” allthingsdistributed.com, July 2023. Archived at perma.cc/6S7P-GLM4

[27] Rich Houlihan. “DynamoDB Adaptive Capacity: Smooth Performance for Chaotic Workloads (DAT327).” At AWS re:Invent, November 2017.

[28] Kostja Osipov. “ScyllaDB’s Safe Topology and Schema Changes on Raft.” scylladb.com, June 2024. Archived at perma.cc/4S82-M277

[29] Christopher D. Manning, Prabhakar Raghavan, and Hinrich Schütze. Introduction to Information Retrieval. Cambridge University Press, 2008. ISBN: 9780521865715. Available online at nlp.stanford.edu/IR-book.

[30] Michael Busch, Krishna Gade, Brian Larson, Patrick Lok, Samuel Luckenbill, and Jimmy Lin. “Earlybird: Real-Time Search at Twitter.” At 28th IEEE International Conference on Data Engineering (ICDE), April 2012. doi:10.1109/ICDE.2012.149

[31] Nadav Har’El. “Indexing in Cassandra 3.” github.com, April 2017. Archived at perma.cc/3ENV-8T9P

[32] Zachary Tong. “Customizing Your Document Routing.” elastic.co, June 2013. Archived at perma.cc/97VM-MREN

[33] Andrew Pavlo. “H-Store Documentation: Frequently Asked Questions.” hstore.cs.brown.edu, October 2013. Archived at perma.cc/X3ZA-DW6Z
