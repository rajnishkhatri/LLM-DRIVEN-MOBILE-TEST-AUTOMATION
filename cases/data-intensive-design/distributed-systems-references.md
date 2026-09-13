---
type: reference
title: 'References — the trouble with distributed systems'
description: 'Source citations for the distributed-systems notes (partial failure, networks, timeouts, clocks, pauses, quorums, fencing, Byzantine faults, system models, DST). Numbering is local to this chapter; the dump included [1]–[136].'
tags: [data-intensive-design, distributed-systems, references]
---

# References — the trouble with distributed systems

Citations used by the [distributed-systems overview](distributed-systems-overview.md)
and the chapter-9 Concepts. Numbering is **local to this chapter**
— it is not the same list as [trade-off references](references.md),
[NFR references](nfr-references.md),
[data-model references](data-models-references.md),
[storage references](storage-references.md),
[encoding references](encoding-references.md),
[replication references](replication-references.md),
[sharding references](sharding-references.md), or
[transaction references](transactions-references.md).

The source dump included the full set **[1]–[136]**.

[1] Mark Cavage. “There’s Just No Getting Around It: You’re Building a Distributed System.” ACM Queue, volume 11, issue 4, pages 80–89, April 2013. doi:10.1145/2466486.2482856

[2] Jay Kreps. “Getting Real About Distributed System Reliability.” blog.empathybox.com, March 2012. Archived at perma.cc/9B5Q-AEBW

[3] Coda Hale. “You Can’t Sacrifice Partition Tolerance.” codahale.com, October 2010. Archived at perma.cc/6GJU-X4G5

[4] Jeff Hodges. “Notes on Distributed Systems for Young Bloods.” somethingsimilar.com, January 2013. Archived at perma.cc/B636-62CE

[5] Van Jacobson. “Congestion Avoidance and Control.” At ACM Symposium on Communications Architectures and Protocols (SIGCOMM), August 1988. doi:10.1145/52324.52356

[6] Bert Hubert. “The Ultimate SO_LINGER Page, or: Why Is My TCP Not Reliable.” blog.netherlabs.nl, January 2009. Archived at perma.cc/6HDX-L2RR

[7] Jerome H. Saltzer, David P. Reed, and David D. Clark. “End-To-End Arguments in System Design.” ACM Transactions on Computer Systems, volume 2, issue 4, pages 277–288, November 1984. doi:10.1145/357401.357402

[8] Peter Bailis and Kyle Kingsbury. “The Network Is Reliable.” ACM Queue, volume 12, issue 7, pages 48–55, July 2014. doi:10.1145/2639988.2639988

[9] Joshua B. Leners, Trinabh Gupta, Marcos K. Aguilera, and Michael Walfish. “Taming Uncertainty in Distributed Systems with Help from the Network.” At 10th European Conference on Computer Systems (EuroSys), April 2015. doi:10.1145/2741948.2741976

[10] Phillipa Gill, Navendu Jain, and Nachiappan Nagappan. “Understanding Network Failures in Data Centers: Measurement, Analysis, and Implications.” At ACM SIGCOMM Conference, August 2011. doi:10.1145/2018436.2018477

[11] Urs Hölzle. “But recently a farmer had started grazing a herd of cows nearby. And whenever they stepped on the fiber link, they bent it enough to cause a blip.” x.com, May 2020. Archived at perma.cc/WX8X-ZZA5

[12] CBC News. “Hundreds Lose Internet Service in Northern B.C. After Beaver Chews Through Cable.” cbc.ca, April 2021. Archived at perma.cc/UW8C-H2MY

[13] Will Oremus. “The Global Internet Is Being Attacked by Sharks, Google Confirms.” slate.com, August 2014. Archived at perma.cc/P6F3-C6YG

[14] Jess Auerbach Jahajeeah. “Down to the Wire: The Ship Fixing Our Internet.” continent.substack.com, November 2023. Archived at perma.cc/DP7B-EQ7S

[15] Santosh Janardhan. “More Details About the October 4 Outage.” engineering.fb.com, October 2021. Archived at perma.cc/WW89-VSXH

[16] Tom Parfitt. “Georgian Woman Cuts off Web Access to Whole of Armenia.” theguardian.com, April 2011. Archived at perma.cc/KMC3-N3NZ

[17] Antonio Voce, Tural Ahmedzade and Ashley Kirk. “‘Shadow Fleets’ and Subaquatic Sabotage: Are Europe’s Undersea Internet Cables Under Attack?” theguardian.com, March 2025. Archived at perma.cc/HA7S-ZDBV

[18] Shengyun Liu, Paolo Viotti, Christian Cachin, Vivien Quéma, and Marko Vukolić. “XFT: Practical Fault Tolerance Beyond Crashes.” At 12th USENIX Symposium on Operating Systems Design and Implementation (OSDI), November 2016.

[19] Mark Imbriaco. “Downtime Last Saturday.” github.blog, December 2012. Archived at perma.cc/M7X5-E8SQ

[20] Tom Lianza and Chris Snook. “A Byzantine Failure in the Real World.” blog.cloudflare.com, November 2020. Archived at perma.cc/83EZ-ALCY

[21] Mohammed Alfatafta, Basil Alkhatib, Ahmed Alquraan, and Samer Al-Kiswany. “Toward a Generic Fault Tolerance Technique for Partial Network Partitioning.” At 14th USENIX Symposium on Operating Systems Design and Implementation (OSDI), November 2020.

[22] Marc A. Donges. “Re: bnx2 Cards Intermittantly Going Offline.” Message to Linux netdev mailing list, spinics.net, September 2012. Archived at perma.cc/TXP6-H8R3

[23] Troy Toman. “Inside a CODE RED: Network Edition.” signalvnoise.com, September 2020. Archived at perma.cc/BET6-FY25

[24] Kyle Kingsbury. “Jepsen: Elasticsearch.” aphyr.com, June 2014. Archived at perma.cc/JK47-S89J

[25] Salvatore Sanfilippo. “A Few Arguments About Redis Sentinel Properties and Fail Scenarios.” antirez.com, October 2014. Archived at perma.cc/8XEU-CLM8

[26] Nicolas Liochon. “CAP: If All You Have Is a Timeout, Everything Looks Like a Partition.” blog.thislongrun.com, May 2015. Archived at perma.cc/FS57-V2PZ

[27] Matthew P. Grosvenor, Malte Schwarzkopf, Ionel Gog, Robert N. M. Watson, Andrew W. Moore, Steven Hand, and Jon Crowcroft. “Queues Don’t Matter When You Can JUMP Them!” At 12th USENIX Symposium on Networked Systems Design and Implementation (NSDI), May 2015.

[28] Theo Julienne. “Debugging Network Stalls on Kubernetes.” github.blog, November 2019. Archived at perma.cc/K9M8-XVGL

[29] Guohui Wang and T. S. Eugene Ng. “The Impact of Virtualization on Network Performance of Amazon EC2 Data Center.” At 29th IEEE International Conference on Computer Communications (INFOCOM), March 2010. doi:10.1109/INFCOM.2010.5461931

[30] Brandon Philips. “etcd: Distributed Locking and Service Discovery.” At Strange Loop, September 2014.

[31] Steve Newman. “A Systematic Look at EC2 I/O.” blog.scalyr.com, October 2012. Archived at perma.cc/FL4R-H2VE

[32] Naohiro Hayashibara, Xavier Défago, Rami Yared, and Takuya Katayama. “The ϕ Accrual Failure Detector.” Japan Advanced Institute of Science and Technology, School of Information Science, Technical Report IS-RR-2004-010, May 2004. Archived at perma.cc/NSM2-TRYA

[33] Jeffrey Wang. “Phi Accrual Failure Detector.” ternarysearch.blogspot.co.uk, August 2013. Archived at perma.cc/L452-AMLV

[34] Srinivasan Keshav. An Engineering Approach to Computer Networking: ATM Networks, the Internet, and the Telephone Network. Addison-Wesley Professional, 1997. ISBN: 9780201634426

[35] Othmar Kyas. ATM Networks. International Thomson Publishing, 1995. ISBN: 9781850321286

[36] Jialin Li, Naveen Kr. Sharma, Dan R. K. Ports, and Steven D. Gribble. “Tales of the Tail: Hardware, OS, and Application-level Sources of Tail Latency.” At ACM Symposium on Cloud Computing (SOCC), November 2014. doi:10.1145/2670979.2670988

[37] Mellanox Technologies. “InfiniBand FAQ, Rev 1.3.” network.nvidia.com, December 2014. Archived at perma.cc/LQJ4-QZVK

[38] Jose Renato Santos, Yoshio Turner, and G. (John) Janakiraman. “End-to-End Congestion Control for InfiniBand.” At 22nd Annual Joint Conference of the IEEE Computer and Communications Societies (INFOCOM), April 2003. Also published by HP Laboratories Palo Alto, Tech Report HPL-2002-359. doi:10.1109/INFCOM.2003.1208949

[39] Ulrich Windl, David Dalton, Marc Martinec, and Dale R. Worley. “The NTP FAQ and HOWTO.” ntp.org, November 2006. Archived at archive.org

[40] John Graham-Cumming. “How and Why the Leap Second Affected Cloudflare DNS.” blog.cloudflare.com, January 2017. Archived at archive.org

[41] David Holmes. “Inside the Hotspot VM: Clocks, Timers and Scheduling Events—Part I—Windows.” blogs.oracle.com, October 2006. Archived at archive.org

[42] Joran Dirk Greef. “Three Clocks Are Better than One.” tigerbeetle.com, August 2021. Archived at perma.cc/5RXG-EU6B

[43] Oliver Yang. “Pitfalls of TSC Usage.” oliveryang.net, September 2015. Archived at perma.cc/Z2QY-5FRA

[44] Steve Loughran. “Time on Multi-Core, Multi-Socket Servers.” steveloughran.blogspot.co.uk, September 2015. Archived at perma.cc/7M4S-D4U6

[45] James C. Corbett, Jeffrey Dean, Michael Epstein, Andrew Fikes, Christopher Frost, JJ Furman, Sanjay Ghemawat, Andrey Gubarev, Christopher Heiser, Peter Hochschild, Wilson Hsieh, Sebastian Kanthak, Eugene Kogan, Hongyi Li, Alexander Lloyd, Sergey Melnik, David Mwaura, David Nagle, Sean Quinlan, Rajesh Rao, Lindsay Rolig, Dale Woodford, Yasushi Saito, Christopher Taylor, Michal Szymaniak, and Ruth Wang. “Spanner: Google’s Globally-Distributed Database.” At 10th USENIX Symposium on Operating System Design and Implementation (OSDI), October 2012.

[46] M. Caporaloni and R. Ambrosini. “How Closely Can a Personal Computer Clock Track the UTC Timescale Via the Internet?” European Journal of Physics, volume 23, issue 4, pages L17–L21, June 2012. doi:10.1088/0143-0807/23/4/103

[47] Nelson Minar. “A Survey of the NTP Network.” alumni.media.mit.edu, December 1999. Archived at perma.cc/EV76-7ZV3

[48] Viliam Holub. “Synchronizing Clocks in a Cassandra Cluster Pt. 1—The Problem.” blog.rapid7.com, March 2014. Archived at perma.cc/N3RV-5LNL

[49] Poul-Henning Kamp. “The One-Second War (What Time Will You Die?)” ACM Queue, volume 9, issue 4, pages 44–48, April 2011. doi:10.1145/1966989.1967009

[50] Nelson Minar. “Leap Second Crashes Half the Internet.” somebits.com, July 2012. Archived at perma.cc/2WB8-D6EU

[51] Christopher Pascoe. “Time, Technology and Leaping Seconds.” googleblog.blogspot.co.uk, September 2011. Archived at perma.cc/U2JL-7E74

[52] Mingxue Zhao and Jeff Barr. “Look Before You Leap—The Coming Leap Second and AWS.” aws.amazon.com, May 2015. Archived at perma.cc/KPE9-XMFM

[53] Darryl Veitch and Kanthaiah Vijayalayan. “Network Timing and the 2015 Leap Second.” At 17th International Conference on Passive and Active Measurement (PAM), April 2016. doi:10.1007/978-3-319-30505-9_29

[54] VMware, Inc. “Timekeeping in VMware Virtual Machines.” vmware.com, October 2008. Archived at perma.cc/HM5R-T5NF

[55] Victor Yodaiken. “Clock Synchronization in Finance and Beyond.” yodaiken.com, November 2017. Archived at perma.cc/9XZD-8ZZN

[56] Mustafa Emre Acer, Emily Stark, Adrienne Porter Felt, Sascha Fahl, Radhika Bhargava, Bhanu Dev, Matt Braithwaite, Ryan Sleevi, and Parisa Tabriz. “Where the Wild Warnings Are: Root Causes of Chrome HTTPS Certificate Errors.” At ACM SIGSAC Conference on Computer and Communications Security (CCS), October 2017. doi:10.1145/3133956.3134007

[57] European Securities and Markets Authority. “MiFID II / MiFIR: Regulatory Technical and Implementing Standards—Annex I.” esma.europa.eu, Report ESMA/2015/1464, September 2015. Archived at perma.cc/ZLX9-FGQ3

[58] Luke Bigum. “Solving MiFID II Clock Synchronisation with Minimum Spend (Part 1).” catach.blogspot.com, November 2015. Archived at perma.cc/4J5W-FNM4

[59] Oleg Obleukhov and Ahmad Byagowi. “How Precision Time Protocol Is Being Deployed at Meta.” engineering.fb.com, November 2022. Archived at perma.cc/29G6-UJNW

[60] John Wiseman. “GPSJAM: Daily Maps of GPS Interference.” gpsjam.org

[61] Josh Levinson, Julien Ridoux, and Chris Munns. “It’s About Time: Microsecond-Accurate Clocks on Amazon EC2 Instances.” aws.amazon.com, November 2023. Archived at perma.cc/56M6-5VMZ

[62] Kyle Kingsbury. “Jepsen: Cassandra.” aphyr.com, September 2013. Archived at perma.cc/4MBR-J96V

[63] John Daily. “Clocks Are Bad, or, Welcome to the Wonderful World of Distributed Systems.” riak.com, November 2013. Archived at perma.cc/4XB5-UCXY

[64] Marc Brooker. “It’s About Time!” brooker.co.za, November 2023. Archived at perma.cc/N6YK-DRPA

[65] Kyle Kingsbury. “The Trouble with Timestamps.” aphyr.com, October 2013. Archived at perma.cc/W3AM-5VAV

[66] Leslie Lamport. “Time, Clocks, and the Ordering of Events in a Distributed System.” Communications of the ACM, volume 21, issue 7, pages 558–565, July 1978. doi:10.1145/359545.359563

[67] Justin Sheehy. “There Is No Now: Problems with Simultaneity in Distributed Systems.” ACM Queue, volume 13, issue 3, pages 36–41, March 2015. doi:10.1145/2733108

[68] Murat Demirbas. “Spanner: Google’s Globally-Distributed Database.” muratbuffalo.blogspot.co.uk, July 2013. Archived at perma.cc/6VWR-C9WB

[69] Dahlia Malkhi and Jean-Philippe Martin. “Spanner’s Concurrency Control.” ACM SIGACT News, volume 44, issue 3, pages 73–77, September 2013. doi:10.1145/2527748.2527767

[70] Franck Pachot. “Achieving Precise Clock Synchronization on AWS.” yugabyte.com, December 2024. Archived at perma.cc/UYM6-RNBS

[71] Spencer Kimball. “Living Without Atomic Clocks: Where CockroachDB and Spanner Diverge.” cockroachlabs.com, January 2022. Archived at perma.cc/AWZ7-RXFT

[72] Murat Demirbas. “Use of Time in Distributed Databases (Part 4): Synchronized Clocks in Production Databases.” muratbuffalo.blogspot.com, January 2025. Archived at perma.cc/9WNX-Q9U3

[73] Cary G. Gray and David R. Cheriton. “Leases: An Efficient Fault-Tolerant Mechanism for Distributed File Cache Consistency.” At 12th ACM Symposium on Operating Systems Principles (SOSP), December 1989. doi:10.1145/74850.74870

[74] Daniel Sturman, Scott Delap, Max Ross, et al. “Roblox Return to Service.” corp.roblox.com, January 2022. Archived at perma.cc/8ALT-WAS4

[75] Todd Lipcon. “Avoiding Full GCs with MemStore-Local Allocation Buffers.” slideshare.net, February 2011. Archived at perma.cc/CH62-2EWJ

[76] Christopher Clark, Keir Fraser, Steven Hand, Jacob Gorm Hansen, Eric Jul, Christian Limpach, Ian Pratt, and Andrew Warfield. “Live Migration of Virtual Machines.” At 2nd USENIX Symposium on Symposium on Networked Systems Design & Implementation (NSDI), May 2005.

[77] Mike Shaver. “fsyncers and Curveballs.” shaver.off.net, May 2008. Archived at archive.org

[78] Zhenyun Zhuang and Cuong Tran. “Eliminating Large JVM GC Pauses Caused by Background IO Traffic.” engineering.linkedin.com, February 2016. Archived at perma.cc/ML2M-X9XT

[79] Martin Thompson. “Java Garbage Collection Distilled.” mechanical-sympathy.blogspot.co.uk, July 2013. Archived at perma.cc/DJT3-NQLQ

[80] David Terei and Amit Levy. “Blade: A Data Center Garbage Collector.” arXiv:1504.02578, April 2015.

[81] Martin Maas, Tim Harris, Krste Asanović, and John Kubiatowicz. “Trash Day: Coordinating Garbage Collection in Distributed Systems.” At 15th USENIX Workshop on Hot Topics in Operating Systems (HotOS), May 2015.

[82] Martin Fowler. “The LMAX Architecture.” martinfowler.com, July 2011. Archived at perma.cc/5AV4-N6RJ

[83] Joseph Y. Halpern and Yoram Moses. “Knowledge and Common Knowledge in a Distributed Environment.” Journal of the ACM (JACM), volume 37, issue 3, pages 549–587, July 1990. doi:10.1145/79147.79161

[84] Chuzhe Tang, Zhaoguo Wang, Xiaodong Zhang, Qianmian Yu, Binyu Zang, Haibing Guan, and Haibo Chen. “Ad Hoc Transactions in Web Applications: The Good, the Bad, and the Ugly.” At ACM International Conference on Management of Data (SIGMOD), June 2022. doi:10.1145/3514221.3526120

[85] Flavio P. Junqueira and Benjamin Reed. ZooKeeper: Distributed Process Coordination. O’Reilly Media, 2013. ISBN: 9781449361303

[86] Enis Söztutar. “HBase and HDFS: Understanding Filesystem Usage in HBase.” At HBaseCon, June 2013. Archived at perma.cc/4DXR-9P88

[87] SUSE LLC. “SUSE Linux Enterprise High Availability 15 SP6 Administration Guide, Section 12: Fencing and STONITH.” documentation.suse.com, March 2025. Archived at perma.cc/8LAR-EL9D

[88] Mike Burrows. “The Chubby Lock Service for Loosely-Coupled Distributed Systems.” At 7th USENIX Symposium on Operating System Design and Implementation (OSDI), November 2006.

[89] Kyle Kingsbury. “etcd 3.4.3.” jepsen.io, January 2020. Archived at perma.cc/2P3Y-MPWU

[90] Ensar Basri Kahveci. “Distributed Locks Are Dead; Long Live Distributed Locks!” hazelcast.com, April 2019. Archived at perma.cc/7FS5-LDXE

[91] Martin Kleppmann. “How to Do Distributed Locking.” martin.kleppmann.com, February 2016. Archived at perma.cc/Y24W-YQ5L

[92] Salvatore Sanfilippo. “Is Redlock Safe?” antirez.com, February 2016. Archived at perma.cc/B6GA-9Q6A

[93] Gunnar Morling. “Leader Election with S3 Conditional Writes.” morling.dev, August 2024. Archived at perma.cc/7V2N-J78Y

[94] Leslie Lamport, Robert Shostak, and Marshall Pease. “The Byzantine Generals Problem.” ACM Transactions on Programming Languages and Systems (TOPLAS), volume 4, issue 3, pages 382–401, July 1982. doi:10.1145/357172.357176

[95] Jim N. Gray. “Notes on Data Base Operating Systems.” In Operating Systems: An Advanced Course, Lecture Notes in Computer Science, volume 60, edited by R. Bayer, R. M. Graham, and G. Seegmüller, pages 393–481, Springer-Verlag, 1978. ISBN: 9783540087557. Archived at perma.cc/7S9M-2LZU

[96] Brian Palmer. “How Complicated Was the Byzantine Empire?” slate.com, October 2011. Archived at perma.cc/AN7X-FL3N

[97] Leslie Lamport. “My Writings.” lamport.azurewebsites.net, December 2014. Archived at perma.cc/5NNM-SQGR

[98] John Rushby. “Bus Architectures for Safety-Critical Embedded Systems.” At 1st International Workshop on Embedded Software (EMSOFT), October 2001. doi:10.1007/3-540-45449-7_22

[99] Jake Edge. “ELC: SpaceX Lessons Learned.” lwn.net, March 2013. Archived at perma.cc/AYX8-QP5X

[100] Shehar Bano, Alberto Sonnino, Mustafa Al-Bassam, Sarah Azouvi, Patrick McCorry, Sarah Meiklejohn, and George Danezis. “SoK: Consensus in the Age of Blockchains.” At 1st ACM Conference on Advances in Financial Technologies (AFT), October 2019. doi:10.1145/3318041.3355458

[101] Ezra Feilden, Adi Oltean, and Philip Johnston. “Why We Should Train AI in Space.” White Paper, starcloud.com, September 2024. Archived at perma.cc/7Y3S-8UB6

[102] James Mickens. “The Saddest Moment.” USENIX ;login, May 2013. Archived at perma.cc/T7BZ-XCFR

[103] Martin Kleppmann and Heidi Howard. “Byzantine Eventual Consistency and the Fundamental Limits of Peer-to-Peer Databases.” arXiv:2012.00472, December 2020.

[104] Martin Kleppmann. “Making CRDTs Byzantine Fault Tolerant.” At 9th Workshop on Principles and Practice of Consistency for Distributed Data (PaPoC), April 2022. doi:10.1145/3517209.3524042

[105] Evan Gilman. “The Discovery of Apache ZooKeeper’s Poison Packet.” pagerduty.com, May 2015. Archived at perma.cc/RV6L-Y5CQ

[106] Jonathan Stone and Craig Partridge. “When the CRC and TCP Checksum Disagree.” At ACM Conference on Applications, Technologies, Architectures, and Protocols for Computer Communication (SIGCOMM), August 2000. doi:10.1145/347059.347561

[107] Evan Jones. “How Both TCP and Ethernet Checksums Fail.” evanjones.ca, October 2015. Archived at perma.cc/9T5V-B8X5

[108] Cynthia Dwork, Nancy Lynch, and Larry Stockmeyer. “Consensus in the Presence of Partial Synchrony.” Journal of the ACM, volume 35, issue 2, pages 288–323, April 1988. doi:10.1145/42282.42283

[109] Richard D. Schlichting and Fred B. Schneider. “Fail-Stop Processors: An Approach to Designing Fault-Tolerant Computing Systems.” ACM Transactions on Computer Systems (TOCS), volume 1, issue 3, pages 222–238, August 1983. doi:10.1145/357369.357371

[110] Thanh Do, Mingzhe Hao, Tanakorn Leesatapornwongsa, Tiratat Patana-anake, and Haryadi S. Gunawi. “Limplock: Understanding the Impact of Limpware on Scale-out Cloud Systems.” At 4th ACM Symposium on Cloud Computing (SoCC), October 2013. doi:10.1145/2523616.2523627

[111] Josh Snyder and Joseph Lynch. “Garbage Collecting Unhealthy JVMs, a Proactive Approach.” netflixtechblog.medium.com, November 2019. Archived at perma.cc/8BTA-N3YB

[112] Haryadi S. Gunawi, Riza O. Suminto, Russell Sears, Casey Golliher, Swaminathan Sundararaman, Xing Lin, Tim Emami, Weiguang Sheng, Nematollah Bidokhti, Caitie McCaffrey, Gary Grider, Parks M. Fields, Kevin Harms, Robert B. Ross, Andree Jacobson, Robert Ricci, Kirk Webb, Peter Alvaro, H. Birali Runesha, Mingzhe Hao, and Huaicheng Li. “Fail-Slow at Scale: Evidence of Hardware Performance Faults in Large Production Systems.” At 16th USENIX Conference on File and Storage Technologies, February 2018.

[113] Peng Huang, Chuanxiong Guo, Lidong Zhou, Jacob R. Lorch, Yingnong Dang, Murali Chintalapati, and Randolph Yao. “Gray Failure: The Achilles’ Heel of Cloud-Scale Systems.” At 16th Workshop on Hot Topics in Operating Systems (HotOS), May 2017. doi:10.1145/3102980.3103005

[114] Chang Lou, Peng Huang, and Scott Smith. “Understanding, Detecting and Localizing Partial Failures in Large System Software.” At 17th USENIX Symposium on Networked Systems Design and Implementation (NSDI), February 2020.

[115] Peter Bailis and Ali Ghodsi. “Eventual Consistency Today: Limitations, Extensions, and Beyond.” ACM Queue, volume 11, issue 3, pages 55–63, March 2013. doi:10.1145/2460276.2462076

[116] Bowen Alpern and Fred B. Schneider. “Defining Liveness.” Information Processing Letters, volume 21, issue 4, pages 181–185, October 1985. doi:10.1016/0020-0190(85)90056-0

[117] Flavio P. Junqueira. “Dude, Where’s My Metadata?” fpj.me, May 2015. Archived at perma.cc/D2EU-Y9S5

[118] Scott Sanders. “January 28th Incident Report.” github.com, February 2016. Archived at perma.cc/5GZR-88TV

[119] Jay Kreps. “A Few Notes on Kafka and Jepsen.” blog.empathybox.com, September 2013. Archived at perma.cc/XJ5C-F583

[120] Marc Brooker and Ankush Desai. “Systems Correctness Practices at AWS.” ACM Queue, volume 22, issue 6, pages 79–96, November/December 2024. doi:10.1145/3712057

[121] Andrey Satarin. “Testing Distributed Systems: Curated list of Resources on Testing Distributed Systems.” asatarin.github.io. Archived at perma.cc/U5V8-XP24

[122] Phil Eaton and Joran Dirk Greef. “We Put a Distributed Database in the Browser—And Made a Game of It!” tigerbeetle.com, June 2023. Archived at perma.cc/L7M7-X4HD

[123] Apple, Inc. and the FoundationDB project authors. “FoundationDB—Simulation and Testing.” apple.github.io. Archived at perma.cc/4C4L-AUH3

[124] Jack Vanlightly. “Verifying Kafka Transactions—Diary Entry 2—Writing an Initial TLA+ Spec.” jack-vanlightly.com, December 2024. Archived at perma.cc/NSQ8-MQ5N

[125] Siddon Tang. “From Chaos to Order—Tools and Techniques for Testing TiDB, A Distributed NewSQL Database.” pingcap.com, April 2018. Archived at perma.cc/5EJB-R29F

[126] Nathan VanBenschoten. “Parallel Commits: An Atomic Commit Protocol for Globally Distributed Transactions.” cockroachlabs.com, November 2019. Archived at perma.cc/5FZ7-QK6J

[127] Jack Vanlightly. “Paper: VR Revisited—State Transfer (Part 3).” jack-vanlightly.com, December 2022. Archived at perma.cc/KNK3-K6WS

[128] Hillel Wayne. “What If the Spec Doesn’t Match the Code?” buttondown.com, March 2024. Archived at perma.cc/8HEZ-KHER

[129] Lingzhi Ouyang, Xudong Sun, Ruize Tang, Yu Huang, Madhav Jivrajani, Xiaoxing Ma, Tianyin Xu. “Multi-Grained Specifications for Distributed System Model Checking and Verification.” At 20th European Conference on Computer Systems (EuroSys), March 2025. doi:10.1145/3689031.3696069

[130] Yury Izrailevsky and Ariel Tseitlin. “The Netflix Simian Army.” netflixtechblog.com, July, 2011. Archived at perma.cc/M3NY-FJW6

[131] Kyle Kingsbury. “Jepsen: On the Perils of Network Partitions.” aphyr.com, May, 2013. Archived at perma.cc/W98G-6HQP

[132] Kyle Kingsbury. Analyses. jepsen.io, 2024. Archived at perma.cc/8LDN-D2T8

[133] Rupak Majumdar and Filip Niksic. “Why Is Random Testing Effective for Partition Tolerance Bugs?” Proceedings of the ACM on Programming Languages (PACMPL), volume 2, issue POPL, article no. 46, December 2017. doi:10.1145/3158134

[134] FoundationDB project authors. “Simulation and Testing.” apple.github.io. Archived at perma.cc/NQ3L-PM4C

[135] Alex Kladov. “Simulation Testing for Liveness.” tigerbeetle.com, July 2023. Archived at perma.cc/RKD4-HGCR

[136] Alfonso Subiotto Marqués. “(Mostly) Deterministic Simulation Testing in Go.” polarsignals.com, May 2024. Archived at perma.cc/ULD6-TSA4
