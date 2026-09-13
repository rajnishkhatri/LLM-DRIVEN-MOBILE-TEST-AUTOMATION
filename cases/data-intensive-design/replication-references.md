---
type: reference
title: 'References — replication'
description: 'Source citations for the replication notes (single-leader, lag, multi-leader, CRDTs, Dynamo-style quorums, version vectors). Numbering is local to this chapter; the dump included [1]–[65].'
tags: [data-intensive-design, replication, references]
---

# References — replication

Citations used by the [replication overview](replication-overview.md)
and the chapter-6 Concepts. Numbering is **local to this chapter** —
it is not the same list as [trade-off references](references.md),
[NFR references](nfr-references.md),
[data-model references](data-models-references.md),
[storage references](storage-references.md), or
[encoding references](encoding-references.md).

The source dump included the full set **[1]–[65]**.

[1] B. G. Lindsay, P. G. Selinger, C. Galtieri, J. N. Gray, R. A. Lorie, T. G. Price, F. Putzolu, I. L. Traiger, and B. W. Wade. “Notes on Distributed Databases.” IBM Research, Research Report RJ2571(33471), July 1979. Archived at perma.cc/EPZ3-MHDD

[2] Kenny Gryp. “MySQL Terminology Updates.” dev.mysql.com, July 2020. Archived at perma.cc/S62G-6RJ2

[3] Oracle Corporation. “Oracle (Active) Data Guard 19c: Real-Time Data Protection and Availability.” White Paper, oracle.com, March 2019. Archived at perma.cc/P5ST-RPKE

[4] Microsoft. “What Is an Always On Availability Group?” learn.microsoft.com, September 2024. Archived at perma.cc/ABH6-3MXF

[5] Mostafa Elhemali, Niall Gallagher, Nicholas Gordon, Joseph Idziorek, Richard Krog, Colin Lazier, Erben Mo, Akhilesh Mritunjai, Somu Perianayagam, Tim Rath, Swami Sivasubramanian, James Christopher Sorenson III, Sroaj Sosothikul, Doug Terry, and Akshat Vig. “Amazon DynamoDB: A Scalable, Predictably Performant, and Fully Managed NoSQL Database Service.” At USENIX Annual Technical Conference (ATC), July 2022.

[6] Rebecca Taft, Irfan Sharif, Andrei Matei, Nathan VanBenschoten, Jordan Lewis, Tobias Grieger, Kai Niemi, Andy Woods, Anne Birzin, Raphael Poss, Paul Bardea, Amruta Ranade, Ben Darnell, Bram Gruneir, Justin Jaffray, Lucy Zhang, and Peter Mattis. “CockroachDB: The Resilient Geo-Distributed SQL Database.” At ACM SIGMOD International Conference on Management of Data (SIGMOD), June 2020. doi:10.1145/3318464.3386134

[7] Dongxu Huang, Qi Liu, Qiu Cui, Zhuhe Fang, Xiaoyu Ma, Fei Xu, Li Shen, Liu Tang, Yuxing Zhou, Menglong Huang, Wan Wei, Cong Liu, Jian Zhang, Jianjun Li, Xuelian Wu, Lingyu Song, Ruoxi Sun, Shuaipeng Yu, Lei Zhao, Nicholas Cameron, Liquan Pei, and Xin Tang. “TiDB: A Raft-Based HTAP Database.” Proceedings of the VLDB Endowment, volume 13, issue 12, pages 3072–3084, August 2020. doi:10.14778/3415478.3415535

[8] Mallory Knodel and Niels ten Oever. “Terminology, Power, and Inclusive Language in Internet-Drafts and RFCs.” IETF Internet-Draft, August 2023. Archived at perma.cc/5ZY9-725E

[9] Buck Hodges. “Postmortem: VSTS 4 September 2018.” devblogs.microsoft.com, September 2018. Archived at perma.cc/ZF5R-DYZS

[10] Gunnar Morling. “Leader Election with S3 Conditional Writes.” www.morling.dev, August 2024. Archived at perma.cc/7V2N-J78Y

[11] Vignesh Chandramohan, Rohan Desai, and Chris Riccomini. “SlateDB Manifest Design.” github.com, May 2024. Archived at perma.cc/8EUY-P32Z

[12] Stas Kelvich. “Why Does Neon Use Paxos Instead of Raft, and What’s the Difference?” neon.tech, August 2022. Archived at perma.cc/SEZ4-2GXU

[13] Dimitri Fontaine. “An Introduction to the pg_auto_failover Project.” tapoueh.org, November 2021. Archived at perma.cc/3WH5-6BAF

[14] Jesse Newland. “GitHub Availability This Week.” github.blog, September 2012. Archived at perma.cc/3YRF-FTFJ

[15] Mark Imbriaco. “Downtime Last Saturday.” github.blog, December 2012. Archived at perma.cc/M7X5-E8SQ

[16] John Hugg. “‘All In’ with Determinism for Performance and Testing in Distributed Systems.” At Strange Loop, September 2015.

[17] Hironobu Suzuki. “The Internals of PostgreSQL.” interdb.jp, 2017. Archived at archive.org

[18] Amit Kapila. “WAL Internals of PostgreSQL.” At PostgreSQL Conference (PGCon), May 2012. Archived at perma.cc/6225-3SUX

[19] Amit Kapila. “Evolution of Logical Replication.” amitkapila16.blogspot.com, September 2023. Archived at perma.cc/F9VX-JLER

[20] Aru Petchimuthu. “Upgrade Your Amazon RDS for PostgreSQL or Amazon Aurora PostgreSQL Database, Part 2: Using the pglogical Extension.” aws.amazon.com, August 2021. Archived at perma.cc/RXT8-FS2T

[21] Yogeshwer Sharma, Philippe Ajoux, Petchean Ang, David Callies, Abhishek Choudhary, Laurent Demailly, Thomas Fersch, Liat Atsmon Guz, Andrzej Kotulski, Sachin Kulkarni, Sanjeev Kumar, Harry Li, Jun Li, Evgeniy Makeev, Kowshik Prakasam, Robbert van Renesse, Sabyasachi Roy, Pratyush Seth, Yee Jiun Song, Benjamin Wester, Kaushik Veeraraghavan, and Peter Xie. “Wormhole: Reliable Pub-Sub to Support Geo-Replicated Internet Services.” At 12th USENIX Symposium on Networked Systems Design and Implementation (NSDI), May 2015.

[22] Douglas B. Terry. “Replicated Data Consistency Explained Through Baseball.” Microsoft Research, Technical Report MSR-TR-2011-137, October 2011. Archived at perma.cc/F4KZ-AR38

[23] Douglas B. Terry, Alan J. Demers, Karin Petersen, Mike J. Spreitzer, Marvin M. Theher, and Brent B. Welch. “Session Guarantees for Weakly Consistent Replicated Data.” At 3rd International Conference on Parallel and Distributed Information Systems (PDIS), September 1994. doi:10.1109/PDIS.1994.331722

[24] Werner Vogels. “Eventually Consistent.” ACM Queue, volume 6, issue 6, pages 14–19, October 2008. doi:10.1145/1466443.1466448

[25] Simon Willison. Reply to: “My thoughts about Fly.io (so far) and other newish technology I’m getting into”. news.ycombinator.com, May 2022.

[26] Nithin Tharakan. “Scaling Bitbucket’s Database.” atlassian.com, October 2020. Archived at perma.cc/JAB7-9FGX

[27] Terry Pratchett. *Reaper Man: A Discworld Novel.* Victor Gollancz, 1991. ISBN: 9780575049796

[28] Peter Bailis, Alan Fekete, Michael J. Franklin, Ali Ghodsi, Joseph M. Hellerstein, and Ion Stoica. “Coordination Avoidance in Database Systems.” Proceedings of the VLDB Endowment, volume 8, issue 3, pages 185–196, November 2014. doi:10.14778/2735508.2735509

[29] Yaser Raja and Peter Celentano. “PostgreSQL Bi-Directional Replication Using pglogical.” aws.amazon.com, January 2022. Archived at perma.cc/BUQ2-5QWN

[30] Robert Hodges. “If You *Must* Deploy Multi-Master Replication, Read This First.” scale-out-blog.blogspot.com, April 2012. Archived at perma.cc/C2JN-F6Y8

[31] Lars Hofhansl. “HBASE-7709: Infinite Loop Possible in Master/Master Replication.” issues.apache.org, January 2013. Archived at perma.cc/24G2-8NLC

[32] John Day-Richter. “What’s Different About the New Google Docs: Making Collaboration Fast.” drive.googleblog.com, September 2010. Archived at perma.cc/5TL8-TSJ2

[33] Evan Wallace. “How Figma’s Multiplayer Technology Works.” figma.com, October 2019. Archived at perma.cc/L49H-LY4D

[34] Tuomas Artman. “Scaling the Linear Sync Engine.” linear.app, June 2023.

[35] Amr Saafan. “Why Sync Engines Might Be the Future of Web Applications.” nilebits.com, September 2024. Archived at perma.cc/5N73-5M3V

[36] Isaac Hagoel. “Are Sync Engines the Future of Web Applications?” dev.to, July 2024. Archived at perma.cc/R9HF-BKKL

[37] Sujay Jayakar. “A Map of Sync.” stack.convex.dev, October 2024. Archived at perma.cc/82R3-H42A

[38] Alex Feyerke. “Designing Offline-First Web Apps.” alistapart.com, December 2013. Archived at perma.cc/WH7R-S2DS

[39] Martin Kleppmann, Adam Wiggins, Peter van Hardenberg, and Mark McGranaghan. “Local-First Software: You Own Your Data, in Spite of the Cloud.” At ACM SIGPLAN International Symposium on New Ideas, New Paradigms, and Reflections on Programming and Software (Onward!), October 2019. doi:10.1145/3359591.3359737

[40] Martin Kleppmann. “The Past, Present, and Future of Local-First.” At Local-First Conference, May 2024.

[41] Conrad Hofmeyr. “API Calling Is to Sync Engines as jQuery Is to React.” powersync.com, November 2024. Archived at perma.cc/2FP9-7WJJ

[42] Peter van Hardenberg and Martin Kleppmann. “PushPin: Towards Production-Quality Peer-to-Peer Collaboration.” At 7th Workshop on Principles and Practice of Consistency for Distributed Data (PaPoC), April 2020. doi:10.1145/3380787.3393683

[43] Leonard Kawell, Jr., Steven Beckhardt, Timothy Halvorsen, Raymond Ozzie, and Irene Greif. “Replicated Document Management in a Group Communication System.” At ACM Conference on Computer-Supported Cooperative Work (CSCW), September 1988. doi:10.1145/62266.1024798

[44] Ricky Pusch. “Explaining How Fighting Games Use Delay-Based and Rollback Netcode.” words.infil.net and arstechnica.com, October 2019. Archived at perma.cc/DE7W-RDJ8

[45] Giuseppe DeCandia, Deniz Hastorun, Madan Jampani, Gunavardhan Kakulapati, Avinash Lakshman, Alex Pilchin, Swaminathan Sivasubramanian, Peter Vosshall, and Werner Vogels. “Dynamo: Amazon’s Highly Available Key-Value Store.” At 21st ACM Symposium on Operating Systems Principles (SOSP), October 2007. doi:10.1145/1323293.1294281

[46] Marc Shapiro, Nuno Preguiça, Carlos Baquero, and Marek Zawirski. “Conflict-Free Replicated Data Types.” At 13th International Symposium on Stabilization, Safety, and Security of Distributed Systems (SSS), October 2011. doi:10.1007/978-3-642-24550-3_29

[47] Chengzheng Sun and Clarence Ellis. “Operational Transformation in Real-Time Group Editors: Issues, Algorithms, and Achievements.” At ACM Conference on Computer Supported Cooperative Work (CSCW), November 1998. doi:10.1145/289444.289469

[48] Joseph Gentle and Martin Kleppmann. “Collaborative Text Editing with Eg-walker: Better, Faster, Smaller.” At 20th European Conference on Computer Systems (EuroSys), March 2025. doi:10.1145/3689031.3696076

[49] Dharma Shukla. “Azure Cosmos DB: Pushing the Frontier of Globally Distributed Databases.” azure.microsoft.com, September 2018. Archived at perma.cc/UT3B-HH6R

[50] David K. Gifford. “Weighted Voting for Replicated Data.” At 7th ACM Symposium on Operating Systems Principles (SOSP), December 1979. doi:10.1145/800215.806583

[51] Marc Brooker. “Dynamo, DynamoDB, and Aurora DSQL.” brooker.co.za, August 2025. Archived at perma.cc/XG3C-ALDQ

[52] Heidi Howard, Dahlia Malkhi, and Alexander Spiegelman. “Flexible Paxos: Quorum Intersection Revisited.” At 20th International Conference on Principles of Distributed Systems (OPODIS), December 2016. doi:10.4230/LIPIcs.OPODIS.2016.25

[53] Joseph Blomstedt. “Bringing Consistency to Riak.” At RICON West, October 2012. Archived at archive.org

[54] Peter Bailis, Shivaram Venkataraman, Michael J. Franklin, Joseph M. Hellerstein, and Ion Stoica. “Quantifying Eventual Consistency with PBS.” The VLDB Journal, volume 23, issue 2, pages 279–302, April 2014. doi:10.1007/s00778-013-0330-1

[55] Colin Breck. “Shared-Nothing Architectures for Server Replication and Synchronization.” blog.colinbreck.com, December 2019. Archived at perma.cc/48P3-J6CJ

[56] Jeffrey Dean and Luiz André Barroso. “The Tail at Scale.” Communications of the ACM, volume 56, issue 2, pages 74–80, February 2013. doi:10.1145/2408776.2408794

[57] Peng Huang, Chuanxiong Guo, Lidong Zhou, Jacob R. Lorch, Yingnong Dang, Murali Chintalapati, and Randolph Yao. “Gray Failure: The Achilles’ Heel of Cloud-Scale Systems.” At 16th Workshop on Hot Topics in Operating Systems (HotOS), May 2017. doi:10.1145/3102980.3103005

[58] Leslie Lamport. “Time, Clocks, and the Ordering of Events in a Distributed System.” Communications of the ACM, volume 21, issue 7, pages 558–565, July 1978. doi:10.1145/359545.359563

[59] D. Stott Parker Jr., Gerald J. Popek, Gerard Rudisin, Allen Stoughton, Bruce J. Walker, Evelyn Walton, Johanna M. Chow, David Edwards, Stephen Kiser, and Charles Kline. “Detection of Mutual Inconsistency in Distributed Systems.” IEEE Transactions on Software Engineering, volume SE-9, issue 3, pages 240–247, May 1983. doi:10.1109/TSE.1983.236733

[60] Nuno Preguiça, Carlos Baquero, Paulo Sérgio Almeida, Victor Fonte, and Ricardo Gonçalves. “Dotted Version Vectors: Logical Clocks for Optimistic Replication.” arXiv:1011.5808, November 2010.

[61] Giridhar Manepalli. “Clocks and Causality—Ordering Events in Distributed Systems.” exhypothesi.com, November 2022. Archived at perma.cc/8REU-KVLQ

[62] Sean Cribbs. “A Brief History of Time in Riak.” At RICON, October 2014. Archived at perma.cc/7U9P-6JFX

[63] Russell Brown. “Vector Clocks Revisited Part 2: Dotted Version Vectors.” riak.com, November 2015. Archived at perma.cc/96QP-W98R

[64] Carlos Baquero. “Version Vectors Are Not Vector Clocks.” haslab.wordpress.com, July 2011. Archived at perma.cc/7PNU-4AMG

[65] Reinhard Schwarz and Friedemann Mattern. “Detecting Causal Relationships in Distributed Computations: In Search of the Holy Grail.” Distributed Computing, volume 7, issue 3, pages 149–174, March 1994. doi:10.1007/BF02277859
