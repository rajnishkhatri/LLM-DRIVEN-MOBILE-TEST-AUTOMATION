---
type: reference
title: 'References — transactions'
description: 'Source citations for the transaction notes (ACID, isolation levels, MVCC, write skew, serializability, 2PC, XA). Numbering is local to this chapter; the dump included [1]–[87].'
tags: [data-intensive-design, transactions, references]
---

# References — transactions

Citations used by the [transactions overview](transactions-overview.md)
and the chapter-8 Concepts. Numbering is **local to this chapter**
— it is not the same list as [trade-off references](references.md),
[NFR references](nfr-references.md),
[data-model references](data-models-references.md),
[storage references](storage-references.md),
[encoding references](encoding-references.md),
[replication references](replication-references.md), or
[sharding references](sharding-references.md).

The source dump included the full set **[1]–[87]**.

[1] Steven J. Murdoch. “What Went Wrong with Horizon: Learning from the Post Office Trial.” benthamsgaze.org, July 2021. Archived at perma.cc/CNM4-553F

[2] Donald D. Chamberlin, Morton M. Astrahan, Michael W. Blasgen, James N. Gray, W. Frank King, Bruce G. Lindsay, Raymond Lorie, James W. Mehl, Thomas G. Price, Franco Putzolu, Patricia Griffiths Selinger, Mario Schkolnick, Donald R. Slutz, Irving L. Traiger, Bradford W. Wade, and Robert A. Yost. “A History and Evaluation of System R.” Communications of the ACM, volume 24, issue 10, pages 632–646, October 1981. doi:10.1145/358769.358784

[3] Jim N. Gray, Raymond A. Lorie, Gianfranco R. Putzolu, and Irving L. Traiger. “Granularity of Locks and Degrees of Consistency in a Shared Data Base.” In Modelling in Data Base Management Systems: Proceedings of the IFIP Working Conference on Modelling in Data Base Management Systems, edited by G. M. Nijssen, pages 364–394, Elsevier/North Holland Publishing, 1976. Also in Readings in Database Systems, 4th edition, edited by Joseph M. Hellerstein and Michael Stonebraker, MIT Press, 2005. ISBN: 9780262693141

[4] Kapali P. Eswaran, Jim N. Gray, Raymond A. Lorie, and Irving L. Traiger. “The Notions of Consistency and Predicate Locks in a Database System.” Communications of the ACM, volume 19, issue 11, pages 624–633, November 1976. doi:10.1145/360363.360369

[5] Rebecca Taft, Irfan Sharif, Andrei Matei, Nathan VanBenschoten, Jordan Lewis, Tobias Grieger, Kai Niemi, Andy Woods, Anne Birzin, Raphael Poss, Paul Bardea, Amruta Ranade, Ben Darnell, Bram Gruneir, Justin Jaffray, Lucy Zhang, and Peter Mattis. “CockroachDB: The Resilient Geo-Distributed SQL Database.” At ACM SIGMOD International Conference on Management of Data (SIGMOD), June 2020. doi:10.1145/3318464.3386134

[6] Dongxu Huang, Qi Liu, Qiu Cui, Zhuhe Fang, Xiaoyu Ma, Fei Xu, Li Shen, Liu Tang, Yuxing Zhou, Menglong Huang, Wan Wei, Cong Liu, Jian Zhang, Jianjun Li, Xuelian Wu, Lingyu Song, Ruoxi Sun, Shuaipeng Yu, Lei Zhao, Nicholas Cameron, Liquan Pei, and Xin Tang. “TiDB: A Raft-Based HTAP Database.” Proceedings of the VLDB Endowment, volume 13, issue 12, pages 3072–3084, August 2020. doi:10.14778/3415478.3415535

[7] James C. Corbett, Jeffrey Dean, Michael Epstein, Andrew Fikes, Christopher Frost, JJ Furman, Sanjay Ghemawat, Andrey Gubarev, Christopher Heiser, Peter Hochschild, Wilson Hsieh, Sebastian Kanthak, Eugene Kogan, Hongyi Li, Alexander Lloyd, Sergey Melnik, David Mwaura, David Nagle, Sean Quinlan, Rajesh Rao, Lindsay Rolig, Dale Woodford, Yasushi Saito, Christopher Taylor, Michal Szymaniak, and Ruth Wang. “Spanner: Google’s Globally-Distributed Database.” At 10th USENIX Symposium on Operating System Design and Implementation (OSDI), October 2012.

[8] Jingyu Zhou, Meng Xu, Alexander Shraer, Bala Namasivayam, Alex Miller, Evan Tschannen, Steve Atherton, Andrew J. Beamon, Rusty Sears, John Leach, Dave Rosenthal, Xin Dong, Will Wilson, Ben Collins, David Scherer, Alec Grieser, Young Liu, Alvin Moore, Bhaskar Muppana, Xiaoge Su, and Vishesh Yadav. “FoundationDB: A Distributed Unbundled Transactional Key Value Store.” At ACM International Conference on Management of Data (SIGMOD), June 2021. doi:10.1145/3448016.3457559

[9] Theo Härder and Andreas Reuter. “Principles of Transaction-Oriented Database Recovery.” ACM Computing Surveys, volume 15, issue 4, pages 287–317, December 1983. doi:10.1145/289.291

[10] Peter Bailis, Alan Fekete, Ali Ghodsi, Joseph M. Hellerstein, and Ion Stoica. “HAT, not CAP: Towards Highly Available Transactions.” At 14th USENIX Workshop on Hot Topics in Operating Systems (HotOS), May 2013.

[11] Armando Fox, Steven D. Gribble, Yatin Chawathe, Eric A. Brewer, and Paul Gauthier. “Cluster-Based Scalable Network Services.” At 16th ACM Symposium on Operating Systems Principles (SOSP), October 1997. doi:10.1145/268998.266662

[12] Tony Andrews. “Enforcing Complex Constraints in Oracle.” tonyandrews.blogspot.co.uk, October 2004. Archived at archive.org

[13] Philip A. Bernstein, Vassos Hadzilacos, and Nathan Goodman. Concurrency Control and Recovery in Database Systems. Addison-Wesley, 1987. ISBN: 9780201107159. Available online at microsoft.com.

[14] Alan Fekete, Dimitrios Liarokapis, Elizabeth O’Neil, Patrick O’Neil, and Dennis Shasha. “Making Snapshot Isolation Serializable.” ACM Transactions on Database Systems, volume 30, issue 2, pages 492–528, June 2005. doi:10.1145/1071610.1071615

[15] Mai Zheng, Joseph Tucek, Feng Qin, and Mark Lillibridge. “Understanding the Robustness of SSDs Under Power Fault.” At 11th USENIX Conference on File and Storage Technologies (FAST), February 2013.

[16] Laurie Denness. “SSDs: A Gift and a Curse.” laur.ie, June 2015. Archived at perma.cc/6GLP-BX3T

[17] Adam Surak. “When Solid State Drives Are Not That Solid.” blog.algolia.com, June 2015. Archived at perma.cc/CBR9-QZEE

[18] Hewlett Packard Enterprise. “Bulletin: (Revision) HPE SAS Solid State Drives—Critical Firmware Upgrade Required for Certain HPE SAS Solid State Drive Models to Prevent Drive Failure at 32,768 Hours of Operation.” support.hpe.com, November 2019. Archived at perma.cc/CZR4-AQBS

[19] Craig Ringer et al. “PostgreSQL’s Handling of fsync() Errors Is Unsafe and Risks Data Loss at Least on XFS.” Email thread on pgsql-hackers mailing list, postgresql.org, March 2018. Archived at perma.cc/5RKU-57FL

[20] Anthony Rebello, Yuvraj Patel, Ramnatthan Alagappan, Andrea C. Arpaci-Dusseau, and Remzi H. Arpaci-Dusseau. “Can Applications Recover from fsync Failures?” At USENIX Annual Technical Conference (ATC), July 2020.

[21] Thanumalayan Sankaranarayana Pillai, Vijay Chidambaram, Ramnatthan Alagappan, Samer Al-Kiswany, Andrea C. Arpaci-Dusseau, and Remzi H. Arpaci-Dusseau. “Crash Consistency: Rethinking the Fundamental Abstractions of the File System.” ACM Queue, volume 13, issue 7, pages 20–28, July 2015. doi:10.1145/2800695.2801719

[22] Thanumalayan Sankaranarayana Pillai, Vijay Chidambaram, Ramnatthan Alagappan, Samer Al-Kiswany, Andrea C. Arpaci-Dusseau, and Remzi H. Arpaci-Dusseau. “All File Systems Are Not Created Equal: On the Complexity of Crafting Crash-Consistent Applications.” At 11th USENIX Symposium on Operating Systems Design and Implementation (OSDI), October 2014.

[23] Chris Siebenmann. “Unix’s File Durability Problem.” utcc.utoronto.ca, April 2016. Archived at perma.cc/VSS8-5MC4

[24] Aishwarya Ganesan, Ramnatthan Alagappan, Andrea C. Arpaci-Dusseau, and Remzi H. Arpaci-Dusseau. “Redundancy Does Not Imply Fault Tolerance: Analysis of Distributed Storage Reactions to Single Errors and Corruptions.” At 15th USENIX Conference on File and Storage Technologies (FAST), February 2017.

[25] Lakshmi N. Bairavasundaram, Garth R. Goodson, Bianca Schroeder, Andrea C. Arpaci-Dusseau, and Remzi H. Arpaci-Dusseau. “An Analysis of Data Corruption in the Storage Stack.” At 6th USENIX Conference on File and Storage Technologies (FAST), February 2008.

[26] Richard van der Hoff. “How We Discovered, and Recovered from, Postgres Corruption on the matrix.org Homeserver.” matrix.org, July 2025. Archived at perma.cc/CDF5-NRBK

[27] Bianca Schroeder, Raghav Lagisetty, and Arif Merchant. “Flash Reliability in Production: The Expected and the Unexpected.” At 14th USENIX Conference on File and Storage Technologies (FAST), February 2016.

[28] Don Allison. “SSD Storage—Ignorance of Technology Is No Excuse.” blog.korelogic.com, March 2015. Archived at perma.cc/9QN4-9SNJ

[29] Gordon Mah Ung. “Debunked: Your SSD Won’T Lose Data If Left Unplugged After All.” pcworld.com, May 2015. Archived at perma.cc/S46H-JUDU

[30] Martin Kleppmann. “Hermitage: Testing the ‘I’ in ACID.” martin.kleppmann.com, November 2014. Archived at perma.cc/KP2Y-AQGK

[31] Vlad Mihalcea. “The Race Condition That Led to Flexcoin Bankruptcy.” vladmihalcea.com, February 2025. Archived at perma.cc/RRK5-TFAU

[32] Todd Warszawski and Peter Bailis. “ACIDRain: Concurrency-Related Attacks on Database-Backed Web Applications.” At ACM International Conference on Management of Data (SIGMOD), May 2017. doi:10.1145/3035918.3064037

[33] Tristan D’Agosta. “BTC Stolen from Poloniex.” bitcointalk.org, March 2014. Archived at perma.cc/YHA6-4C5D

[34] bitcointhief2. “How I Stole Roughly 100 BTC from an Exchange and How I Could Have Stolen More!” reddit.com, February 2014. Archived at archive.org

[35] Sudhir Jorwekar, Alan Fekete, Krithi Ramamritham, and S. Sudarshan. “Automating the Detection of Snapshot Isolation Anomalies.” At 33rd International Conference on Very Large Data Bases (VLDB), September 2007.

[36] Michael Melanson. “Transactions: The Limits of Isolation.” michaelmelanson.net, November 2014. Archived at perma.cc/RG5R-KMYZ

[37] Edward Kim. “How ACH Works: A Developer Perspective—Part 1.” engineering.gusto.com, April 2014. Archived at perma.cc/7B2H-PU94

[38] Hal Berenson, Philip A. Bernstein, Jim N. Gray, Jim Melton, Elizabeth O’Neil, and Patrick O’Neil. “A Critique of ANSI SQL Isolation Levels.” At ACM International Conference on Management of Data (SIGMOD), May 1995. doi:10.1145/568271.223785

[39] Atul Adya. “Weak Consistency: A Generalized Theory and Optimistic Implementations for Distributed Transactions.” PhD thesis, Massachusetts Institute of Technology, March 1999. Archived at perma.cc/E97M-HW5Q

[40] Peter Bailis, Aaron Davidson, Alan Fekete, Ali Ghodsi, Joseph M. Hellerstein, and Ion Stoica. “Highly Available Transactions: Virtues and Limitations.” Proceedings of the VLDB Endowment, volume 7, issue 3, pages 181–192, November 2013. doi:10.14778/2732232.2732237.

[41] Natacha Crooks, Youer Pu, Lorenzo Alvisi, and Allen Clement. “Seeing Is Believing: A Client-Centric Specification of Database Isolation.” At ACM Symposium on Principles of Distributed Computing (PODC), July 2017. doi:10.1145/3087801.3087802

[42] Bruce Momjian. “MVCC Unmasked.” momjian.us, July 2014. Archived at perma.cc/KQ47-9GYB

[43] Peter Alvaro and Kyle Kingsbury. “MySQL 8.0.34.” jepsen.io, December 2023. Archived at perma.cc/HGE2-Z878

[44] Egor Rogov. PostgreSQL 14 Internals. Postgres Professional, April 2023. Archived at perma.cc/FRK2-D7WB

[45] Hironobu Suzuki. “The Internals of PostgreSQL.” interdb.jp, 2017.

[46] Rohan Reddy Alleti. “Internals of MVCC in Postgres: Hidden Costs of Updates vs Inserts.” medium.com, March 2025. Archived at perma.cc/3ACX-DFXT

[47] Andy Pavlo and Bohan Zhang. “The Part of PostgreSQL We Hate the Most.” cs.cmu.edu, April 2023. Archived at perma.cc/XSP6-3JBN

[48] Yingjun Wu, Joy Arulraj, Jiexi Lin, Ran Xian, and Andrew Pavlo. “An Empirical Evaluation of In-Memory Multi-Version Concurrency Control.” Proceedings of the VLDB Endowment, volume 10, issue 7, pages 781–792, March 2017. doi:10.14778/3067421.3067427

[49] Nikita Prokopov. “Unofficial Guide to Datomic Internals.” tonsky.me, May 2014. Archived at perma.cc/ULM2-T2FW

[50] Daniil Svetlov. “A Practical Guide to Taming Postgres Isolation Anomalies.” dansvetlov.me, March 2025. Archived at perma.cc/L7LE-TDLS

[51] Nate Wiger. “An Atomic Rant.” nateware.com, February 2010. Archived at perma.cc/5ZYB-PE44

[52] James Coglan. “Reading and Writing, Part 3: Web Applications.” blog.jcoglan.com, October 2020. Archived at perma.cc/A7EK-PJVS

[53] Peter Bailis, Alan Fekete, Michael J. Franklin, Ali Ghodsi, Joseph M. Hellerstein, and Ion Stoica. “Feral Concurrency Control: An Empirical Investigation of Modern Application Integrity.” At ACM International Conference on Management of Data (SIGMOD), June 2015. doi:10.1145/2723372.2737784

[54] Jaana Dogan. “Things I Wished More Developers Knew About Databases.” rakyll.medium.com, April 2020. Archived at perma.cc/6EFK-P2TD

[55] Michael J. Cahill, Uwe Röhm, and Alan Fekete. “Serializable Isolation for Snapshot Databases.” At ACM International Conference on Management of Data (SIGMOD), June 2008. doi:10.1145/1376616.1376690

[56] Dan R. K. Ports and Kevin Grittner. “Serializable Snapshot Isolation in PostgreSQL.” Proceedings of the VLDB Endowment, volume 5, issue 12, pages 1850–1861, August 2012. doi:10.14778/2367502.2367523

[57] Douglas B. Terry, Marvin M. Theimer, Karin Petersen, Alan J. Demers, Mike J. Spreitzer and Carl H. Hauser. “Managing Update Conflicts in Bayou, a Weakly Connected Replicated Storage System.” At 15th ACM Symposium on Operating Systems Principles (SOSP), December 1995. doi:10.1145/224056.224070

[58] Hans-Jürgen Schönig. “Constraints over Multiple Rows in PostgreSQL.” cybertec-postgresql.com, June 2021. Archived at perma.cc/2TGH-XUPZ

[59] Michael Stonebraker, Samuel Madden, Daniel J. Abadi, Stavros Harizopoulos, Nabil Hachem, and Pat Helland. “The End of an Architectural Era (It’s Time for a Complete Rewrite).” At 33rd International Conference on Very Large Data Bases (VLDB), September 2007.

[60] John Hugg. “H-Store/VoltDB Architecture vs. CEP Systems and Newer Streaming Architectures.” At Data @Scale Boston, November 2014.

[61] Robert Kallman, Hideaki Kimura, Jonathan Natkins, Andrew Pavlo, Alexander Rasin, Stanley Zdonik, Evan P. C. Jones, Samuel Madden, Michael Stonebraker, Yang Zhang, John Hugg, and Daniel J. Abadi. “H-Store: A High-Performance, Distributed Main Memory Transaction Processing System.” Proceedings of the VLDB Endowment, volume 1, issue 2, pages 1496–1499, August 2008. doi:10.14778/1454159.1454211

[62] Rich Hickey. “The Architecture of Datomic.” infoq.com, November 2012. Archived at perma.cc/5YWU-8XJK

[63] John Hugg. “Debunking Myths About the VoltDB In-Memory Database.” dzone.com, May 2014. Archived at perma.cc/2Z9N-HPKF

[64] Xinjing Zhou, Viktor Leis, Xiangyao Yu, and Michael Stonebraker. “OLTP Through the Looking Glass 16 Years Later: Communication Is the New Bottleneck.” At 15th Annual Conference on Innovative Data Systems Research (CIDR), January 2025. Archived at perma.cc/Q33D-K9YE

[65] Xinjing Zhou, Xiangyao Yu, Goetz Graefe, and Michael Stonebraker. “Lotus: Scalable Multi-Partition Transactions On Single-Threaded Partitioned Databases.” Proceedings of the VLDB Endowment (PVLDB), volume 15, issue 11, pages 2939–2952, July 2022. doi:10.14778/3551793.3551843

[66] Joseph M. Hellerstein, Michael Stonebraker, and James Hamilton. “Architecture of a Database System.” Foundations and Trends in Databases, volume 1, issue 2, pages 141–259, November 2007. doi:10.1561/1900000002

[67] Michael J. Cahill. “Serializable Isolation for Snapshot Databases.” PhD thesis, University of Sydney, July 2009. Archived at perma.cc/727J-NTMP

[68] Cristian Diaconu, Craig Freedman, Erik Ismert, Per-Åke Larson, Pravin Mittal, Ryan Stonecipher, Nitin Verma, and Mike Zwilling. “Hekaton: SQL Server’s Memory-Optimized OLTP Engine.” At ACM SIGMOD International Conference on Management of Data (SIGMOD), June 2013. doi:10.1145/2463676.2463710

[69] Thomas Neumann, Tobias Mühlbauer, and Alfons Kemper. “Fast Serializable Multi-Version Concurrency Control for Main-Memory Database Systems.” At ACM SIGMOD International Conference on Management of Data (SIGMOD), May 2015. doi:10.1145/2723372.2749436

[70] D. Z. Badal. “Correctness of Concurrency Control and Implications in Distributed Databases.” At 3rd International IEEE Computer Software and Applications Conference (COMPSAC), November 1979. doi:10.1109/CMPSAC.1979.762563

[71] Rakesh Agrawal, Michael J. Carey, and Miron Livny. “Concurrency Control Performance Modeling: Alternatives and Implications.” ACM Transactions on Database Systems (TODS), volume 12, issue 4, pages 609–654, December 1987. doi:10.1145/32204.32220

[72] Marc Brooker. “Snapshot Isolation vs. Serializability.” brooker.co.za, December 2024. Archived at perma.cc/5TRC-CR5G

[73] B. G. Lindsay, P. G. Selinger, C. Galtieri, J. N. Gray, R. A. Lorie, T. G. Price, F. Putzolu, I. L. Traiger, and B. W. Wade. “Notes on Distributed Databases.” IBM Research, Research Report RJ2571(33471), July 1979. Archived at perma.cc/EPZ3-MHDD

[74] C. Mohan, Bruce G. Lindsay, and Ron Obermarck. “Transaction Management in the R* Distributed Database Management System.” ACM Transactions on Database Systems, volume 11, issue 4, pages 378–396, December 1986. doi:10.1145/7239.7266

[75] X/Open Company Ltd. “Distributed Transaction Processing: The XA Specification.” Technical Standard XO/CAE/91/300, December 1991. ISBN: 9781872630243, archived at perma.cc/Z96H-29JB

[76] Ivan Silva Neto and Francisco Reverbel. “Lessons Learned from Implementing WS-Coordination and WS-AtomicTransaction.” At 7th IEEE/ACIS International Conference on Computer and Information Science (ICIS), May 2008. doi:10.1109/ICIS.2008.75

[77] James E. Johnson, David E. Langworthy, Leslie Lamport, and Friedrich H. Vogt. “Formal Specification of a Web Services Protocol.” At 1st International Workshop on Web Services and Formal Methods (WS-FM), February 2004. doi:10.1016/j.entcs.2004.02.022

[78] Jim Gray. “The Transaction Concept: Virtues and Limitations.” At 7th International Conference on Very Large Data Bases (VLDB), September 1981.

[79] Dale Skeen. “Nonblocking Commit Protocols.” At ACM International Conference on Management of Data (SIGMOD), April 1981. doi:10.1145/582318.582339

[80] Gregor Hohpe. “Your Coffee Shop Doesn’t Use Two-Phase Commit.” IEEE Software, volume 22, issue 2, pages 64–66, March 2005. doi:10.1109/MS.2005.52

[81] Pat Helland. “Life Beyond Distributed Transactions: An Apostate’s Opinion.” At 3rd Biennial Conference on Innovative Data Systems Research (CIDR), January 2007. Archived at perma.cc/FC4F-AHGH

[82] Jonathan Oliver. “My Beef with MSDTC and Two-Phase Commits.” blog.jonathanoliver.com, April 2011. Archived at perma.cc/K8HF-Z4EN

[83] Oren Eini (Ahende Rahien). “The Fallacy of Distributed Transactions.” ayende.com, July 2014. Archived at perma.cc/VB87-2JEF

[84] Clemens Vasters. “Transactions in Windows Azure (with Service Bus)—An Email Discussion.” learn.microsoft.com, July 2012. Archived at perma.cc/4EZ9-5SKW

[85] Ajmer Dhariwal. “Orphaned MSDTC Transactions (-2 spids).” eraofdata.com, December 2008. Archived at perma.cc/YG6F-U34C

[86] Paul Randal. “Real World Story of DBCC PAGE Saving the Day.” sqlskills.com, June 2013. Archived at perma.cc/2MJN-A5QH

[87] Guozhang Wang, Lei Chen, Ayusman Dikshit, Jason Gustafson, Boyang Chen, Matthias J. Sax, John Roesler, Sophie Blee-Goldman, Bruno Cadonna, Apurva Mehta, Varun Madan, and Jun Rao. “Consistency and Completeness: Rethinking Distributed Stream Processing in Apache Kafka.” At ACM International Conference on Management of Data (SIGMOD), June 2021. doi:10.1145/3448016.3457556
