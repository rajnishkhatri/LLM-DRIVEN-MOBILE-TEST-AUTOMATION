---
type: reference
title: 'References — data models and query languages'
description: 'Source citations for the data-models notes (Codd, Stonebraker, Cypher, RDF/SPARQL, Datalog, GraphQL, CQRS, DataFrames). Numbering is local to this chapter.'
tags: [data-intensive-design, data-models, references]
---

# References — data models and query languages

Citations used by the [data-models overview](data-models-overview.md) and
the chapter-3 Concepts. Numbering is **local to this chapter** — it is not
the same list as [trade-off references](references.md) or
[NFR references](nfr-references.md).

The source dump included [1]–[73] in full. Two SQL listings in the body
were omitted (stray `1` placeholders): the PostgreSQL sharks-per-month
aggregation and the recursive-CTE graph query. Those listings are not
invented here.

[1] Jamie Brandon. “Unexplanations: Query Optimization Works Because SQL Is Declarative.” scattered-thoughts.net, February 2024. Archived at perma.cc/P6W2-WMFZ

[2] Neel Krishnaswami. “What Declarative Languages Are.” semantic-domain.blogspot.com, July 2013. Archived at perma.cc/R4LP-T2RV

[3] Joseph M. Hellerstein. “The Declarative Imperative: Experiences and Conjectures in Distributed Logic.” Tech report UCB/EECS-2010-90, Electrical Engineering and Computer Sciences, University of California at Berkeley, June 2010. Archived at perma.cc/K56R-VVQM

[4] Edgar F. Codd. “A Relational Model of Data for Large Shared Data Banks.” Communications of the ACM, volume 13, issue 6, pages 377–387, June 1970. doi:10.1145/362384.362685

[5] Michael Stonebraker and Joseph M. Hellerstein. “What Goes Around Comes Around.” In Readings in Database Systems, 4th edition, MIT Press, 2005, pages 2–41. ISBN: 9780262693141

[6] Markus Winand. “Modern SQL: Beyond Relational.” modern-sql.com, 2015. Archived at perma.cc/D63V-WAPN

[7] Martin Fowler. “Orm Hate.” martinfowler.com, May 2012. Archived at perma.cc/VCM8-PKNG

[8] Vlad Mihalcea. “N+1 Query Problem with JPA and Hibernate.” vladmihalcea.com, January 2023. Archived at perma.cc/79EV-TZKB

[9] Jens Schauder. “This Is the Beginning of the End of the N+1 Problem: Introducing Single Query Loading.” spring.io, August 2023. Archived at perma.cc/6V96-R333

[10] Jamie Brandon. “SQL Needed Structure.” scattered-thoughts.net, September 2025. Archived at perma.cc/9EVK-HLVR

[11] William Zola. “6 Rules of Thumb for MongoDB Schema Design.” mongodb.com, June 2014. Archived at perma.cc/T2BZ-PPJB

[12] Sidney Andrews and Christopher McClister. “Data Modeling in Azure Cosmos DB.” learn.microsoft.com, February 2023. Archived at archive.org

[13] Raffi Krikorian. “Timelines at Scale.” At QCon San Francisco, November 2012. Archived at perma.cc/V9G5-KLYK

[14] Ralph Kimball and Margy Ross. The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling, 3rd edition. John Wiley & Sons, 2013. ISBN: 9781118530801

[15] Michael Kaminsky. “Data Warehouse Modeling: Star Schema vs. OBT.” fivetran.com, August 2022. Archived at perma.cc/2PZK-BFFP

[16] Joe Nelson. “User-defined Order in SQL.” begriffs.com, March 2018. Archived at perma.cc/GS3W-F7AD

[17] Evan Wallace. “Realtime Editing of Ordered Sequences.” figma.com, March 2017. Archived at perma.cc/K6ER-CQZW

[18] David Greenspan. “Implementing Fractional Indexing.” observablehq.com, October 2020. Archived at perma.cc/5N4R-MREN

[19] Martin Fowler. “Schemaless Data Structures.” martinfowler.com, January 2013.

[20] Amr Awadallah. “Schema-on-Read vs. Schema-on-Write.” At Berkeley EECS RAD Lab Retreat, May 2009. Archived at perma.cc/DTB2-JCFR

[21] Martin Odersky. “The Trouble with Types.” At Strange Loop, September 2013. Archived at perma.cc/85QE-PVEP

[22] Conrad Irwin. “MongoDB—Confessions of a PostgreSQL Lover.” At HTML5DevConf, October 2013. Archived at perma.cc/C2J6-3AL5

[23] “Percona Toolkit Documentation: pt-online-schema-change.” docs.percona.com, 2023. Archived at perma.cc/9K8R-E5UH

[24] Shlomi Noach. “gh-ost: GitHub’s Online Schema Migration Tool for MySQL.” github.blog, August 2016. Archived at perma.cc/7XAG-XB72

[25] Shayon Mukherjee. “pg-osc: Zero Downtime Schema Changes in PostgreSQL.” shayon.dev, February 2022. Archived at perma.cc/35WN-7WMY

[26] Carlos Pérez-Aradros Herce. “Introducing pgroll: Zero-Downtime, Reversible, Schema Migrations for Postgres.” xata.io, October 2023. Archived at archive.org

[27] James C. Corbett, Jeffrey Dean, Michael Epstein, Andrew Fikes, Christopher Frost, JJ Furman, Sanjay Ghemawat, Andrey Gubarev, Christopher Heiser, Peter Hochschild, Wilson Hsieh, Sebastian Kanthak, Eugene Kogan, Hongyi Li, Alexander Lloyd, Sergey Melnik, David Mwaura, David Nagle, Sean Quinlan, Rajesh Rao, Lindsay Rolig, Dale Woodford, Yasushi Saito, Christopher Taylor, Michal Szymaniak, and Ruth Wang. “Spanner: Google’s Globally-Distributed Database.” At 10th USENIX Symposium on Operating System Design and Implementation (OSDI), October 2012.

[28] Donald K. Burleson. “Reduce I/O with Oracle Cluster Tables.” dba-oracle.com. Archived at perma.cc/7LBJ-9X2C

[29] Fay Chang, Jeffrey Dean, Sanjay Ghemawat, Wilson C. Hsieh, Deborah A. Wallach, Mike Burrows, Tushar Chandra, Andrew Fikes, and Robert E. Gruber. “Bigtable: A Distributed Storage System for Structured Data.” At 7th USENIX Symposium on Operating System Design and Implementation (OSDI), November 2006.

[30] Priscilla Walmsley. XQuery, 2nd edition. O’Reilly Media, 2015. ISBN: 9781491915080

[31] Paul C. Bryan, Kris Zyp, and Mark Nottingham. “JavaScript Object Notation (JSON) Pointer.” RFC 6901, IETF, April 2013.

[32] Stefan Gössner, Glyn Normington, and Carsten Bormann. “JSONPath: Query Expressions for JSON.” RFC 9535, IETF, February 2024.

[33] Michael Stonebraker and Andrew Pavlo. “What Goes Around Comes Around… And Around….” ACM SIGMOD Record, volume 53, issue 2, pages 21–37, July 2024. doi:10.1145/3685980.3685984

[34] Lawrence Page, Sergey Brin, Rajeev Motwani, and Terry Winograd. “The PageRank Citation Ranking: Bringing Order to the Web.” Technical Report 1999-66, Stanford University InfoLab, November 1999. Archived at perma.cc/UML9-UZHW

[35] Nathan Bronson, Zach Amsden, George Cabrera, Prasad Chakka, Peter Dimov, Hui Ding, Jack Ferris, Anthony Giardullo, Sachin Kulkarni, Harry Li, Mark Marchukov, Dmitri Petrov, Lovro Puzar, Yee Jiun Song, and Venkat Venkataramani. “TAO: Facebook’s Distributed Data Store for the Social Graph.” At USENIX Annual Technical Conference (ATC), June 2013.

[36] Natasha Noy, Yuqing Gao, Anshu Jain, Anant Narayanan, Alan Patterson, and Jamie Taylor. “Industry-Scale Knowledge Graphs: Lessons and Challenges.” Communications of the ACM, volume 62, issue 8, pages 36–43, August 2019. doi:10.1145/3331166

[37] Xiyang Feng, Guodong Jin, Ziyi Chen, Chang Liu, and Semih Salihoğlu. “KÙZU Graph Database Management System.” At 13th Annual Conference on Innovative Data Systems Research (CIDR 2023), January 2023. Archived at perma.cc/PS6J-ZBZU

[38] Maciej Besta, Emanuel Peter, Robert Gerstenberger, Marc Fischer, Michał Podstawski, Claude Barthels, Gustavo Alonso, Torsten Hoefler. “Demystifying Graph Databases: Analysis and Taxonomy of Data Organization, System Designs, and Graph Queries.” arXiv:1910.09017, October 2019.

[39] “Apache TinkerPop. TinkerPop 3.6.3 Documentation.” tinkerpop.apache.org, May 2023. Archived at perma.cc/KM7W-7PAT

[40] Nadime Francis, Alastair Green, Paolo Guagliardo, Leonid Libkin, Tobias Lindaaker, Victor Marsault, Stefan Plantikow, Mats Rydberg, Petra Selmer, and Andrés Taylor. “Cypher: An Evolving Query Language for Property Graphs.” At International Conference on Management of Data (SIGMOD), May 2018. doi:10.1145/3183713.3190657

[41] Emil Eifrem. Twitter correspondence, January 2014. Archived at perma.cc/WM4S-BW64

[42] Francesco Tisiot. “Explore the New SEARCH and CYCLE Features in PostgreSQL® 14.” aiven.io, December 2021. Archived at perma.cc/J6BT-83UZ

[43] Gaurav Goel. “Understanding Hierarchies in Oracle.” towardsdatascience.com, May 2020. Archived at perma.cc/5ZLR-Q7EW

[44] Alin Deutsch, Yu Xu, and Mingxi Wu. “Seamless Syntactic and Semantic Integration of Query Primitives over Relational and Graph Data in GSQL.” tigergraph.com, November 2018. Archived at perma.cc/JG7J-Y35X

[45] Oskar van Rest, Sungpack Hong, Jinha Kim, Xuming Meng, and Hassan Chafi. “PGQL: A Property Graph Query Language.” At 4th International Workshop on Graph Data Management Experiences and Systems (GRADES), June 2016. doi:10.1145/2960414.2960421

[46] Philip Rathle and Brad Bebee. “GQL: The ISO Standard for Graphs Has Arrived.” aws.amazon.com, April 2024. Archived at perma.cc/5TEU-N2Y8

[47] Alin Deutsch, Nadime Francis, Alastair Green, Keith Hare, Bei Li, Leonid Libkin, Tobias Lindaaker, Victor Marsault, Wim Martens, Jan Michels, Filip Murlak, Stefan Plantikow, Petra Selmer, Oskar van Rest, Hannes Voigt, Domagoj Vrgoč, Mingxi Wu, and Fred Zemke. “Graph Pattern Matching in GQL and SQL/PGQ.” At International Conference on Management of Data (SIGMOD), June 2022. doi:10.1145/3514221.3526057

[48] Alastair Green. “SQL...And Now GQL.” opencypher.org, September 2019. Archived at perma.cc/AFB2-3SY7

[49] Amazon Web Services. “Neptune Graph Data Model.” Amazon Neptune User Guide, docs.aws.amazon.com. Archived at perma.cc/CX3T-EZU9

[50] Cognitect. “Datomic Data Model.” Datomic Cloud Documentation, docs.datomic.com. Archived at perma.cc/LGM9-LEUT

[51] David Beckett and Tim Berners-Lee. “Turtle—Terse RDF Triple Language.” W3C Team Submission, March 2011.

[52] Sinclair Target. “Whatever Happened to the Semantic Web?” twobithistory.org, May 2018. Archived at perma.cc/M8GL-9KHS

[53] Gavin Mendel-Gleason. “The Semantic Web Is Dead—Long Live the Semantic Web!” terminusdb.com, August 2022. Archived at perma.cc/G2MZ-DSS3

[54] Manu Sporny. “JSON-LD and Why I Hate the Semantic Web.” manu.sporny.org, January 2014. Archived at perma.cc/7PT4-PJKF

[55] University of Michigan Library. “Biomedical Ontologies and Controlled Vocabularies.” guides.lib.umich.edu/ontology. Archived at perma.cc/Q5GA-F2N8

[56] Facebook. “The Open Graph Protocol.” ogp.me. Archived at perma.cc/C49A-GUSY

[57] Matt Haughey. “Everything You Ever Wanted to Know About Unfurling but Were Afraid to Ask /or/ How to Make Your Site Previews Look Amazing in Slack.” medium.com, November 2015. Archived at perma.cc/C7S8-4PZN

[58] W3C RDF Working Group. “Resource Description Framework (RDF).” w3.org, February 2004.

[59] Steve Harris, Andy Seaborne, and Eric Prud’hommeaux. “SPARQL 1.1 Query Language.” W3C Recommendation, March 2013.

[60] Todd J. Green, Shan Shan Huang, Boon Thau Loo, and Wenchao Zhou. “Datalog and Recursive Query Processing.” Foundations and Trends in Databases, volume 5, issue 2, pages 105–195, November 2013. doi:10.1561/1900000017

[61] Stefano Ceri, Georg Gottlob, and Letizia Tanca. “What You Always Wanted to Know About Datalog (And Never Dared to Ask).” IEEE Transactions on Knowledge and Data Engineering, volume 1, issue 1, pages 146–166, March 1989. doi:10.1109/69.43410

[62] Serge Abiteboul, Richard Hull, and Victor Vianu. Foundations of Databases. Addison-Wesley, 1995. ISBN: 9780201537710. Available online at webdam.inria.fr/Alice.

[63] Scott Meyer, Andrew Carter, and Andrew Rodriguez. “LIquid: The Soul of a New Graph Database, Part 2.” engineering.linkedin.com, September 2020. Archived at perma.cc/K9M4-PD6Q

[64] Matt Bessey. “Why, After 6 Years, I’m over GraphQL.” bessey.dev, May 2024. Archived at perma.cc/2PAU-JYRA

[65] Dominic Betts, Julián Domínguez, Grigori Melnik, Fernando Simonazzi, and Mani Subramanian. Exploring CQRS and Event Sourcing. Microsoft Patterns & Practices, 2012. ISBN: 9781621140164. Archived at perma.cc/7A39-3NM8

[66] Greg Young. “CQRS and Event Sourcing.” At Code on the Beach, August 2014.

[67] Greg Young. “CQRS Documents.” cqrs.wordpress.com, November 2010. Archived at perma.cc/X5R6-R47F

[68] Brent Robinson. “Crypto Shredding: How It Can Solve Modern Data Retention Challenges.” medium.com, January 2019. Archived at perma.cc/4LFK-S6XE

[69] Devin Petersohn, Stephen Macke, Doris Xin, William Ma, Doris Lee, Xiangxi Mo, Joseph E. Gonzalez, Joseph M. Hellerstein, Anthony D. Joseph, and Aditya Parameswaran. “Towards Scalable Dataframe Systems.” Proceedings of the VLDB Endowment, volume 13, issue 11, pages 2033–2046, July 2020. doi:10.14778/3407790.3407807

[70] Stavros Papadopoulos, Kushal Datta, Samuel Madden, and Timothy Mattson. “The TileDB Array Data Storage Manager.” Proceedings of the VLDB Endowment, volume 10, issue 4, pages 349–360, November 2016. doi:10.14778/3025111.3025117

[71] Florin Rusu. “Multidimensional Array Data Management.” Foundations and Trends in Databases, volume 12, issues 2–3, pages 69–220, February 2023. doi:10.1561/1900000069

[72] Ed Targett. “Bloomberg, Man Group Team Up to Develop Open Source ‘ArcticDB’ Database.” thestack.technology, March 2023. Archived at perma.cc/M5YD-QQYV

[73] Dennis A. Benson, Ilene Karsch-Mizrachi, David J. Lipman, James Ostell, and David L. Wheeler. GenBank. Nucleic Acids Research, volume 36, issue suppl_1, pages D25–D30, January 2008. doi:10.1093/nar/gkm929
