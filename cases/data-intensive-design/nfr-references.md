---
type: reference
title: 'References — nonfunctional requirements'
description: 'Source citations for the NFR notes (timelines, percentiles, metastable failure, SLOs, chaos engineering). Dump ends at [41]; [42]–[100] are cited in the body but were not in the source file.'
tags: [data-intensive-design, nfr, references]
---

# References — nonfunctional requirements

Citations used by the [NFR overview](nfr-overview.md) and the chapter-2
Concepts. Numbering is **local to this chapter** — it is not the same list as
[trade-off references](references.md).

The source dump ended at [41]. Body text still cites **[42]–[100]**
(hardware failure rates, software-fault examples, human/operability sources,
scalability and maintainability literature). Those entries are not invented
here; treat those numbers as pointers into the book until a fuller bibliography
is filed.

[1] Mike Cvet. “How We Learned to Stop Worrying and Love Fan-in at Twitter.” At QCon San Francisco, December 2016.

[2] Raffi Krikorian. “Timelines at Scale.” At QCon San Francisco, November 2012. Archived at perma.cc/V9G5-KLYK

[3] Twitter. “Twitter’s Recommendation Algorithm.” blog.x.com, March 2023. Archived at perma.cc/L5GT-229T

[4] Raffi Krikorian. “New Tweets per Second Record, and How!” blog.x.com, August 2013. Archived at perma.cc/6JZN-XJYN

[5] Jaz Volpert. “When Imperfect Systems Are Good, Actually: Bluesky’s Lossy Timelines.” jazco.dev, February 2025. Archived at perma.cc/2PVE-L2MX

[6] Samuel Axon. “3% of Twitter’s Servers Dedicated to Justin Bieber.” mashable.com, September 2010. Archived at perma.cc/F35N-CGVX

[7] Nathan Bronson, Abutalib Aghayev, Aleksey Charapko, and Timothy Zhu. “Metastable Failures in Distributed Systems.” At Workshop on Hot Topics in Operating Systems (HotOS), May 2021. doi:10.1145/3458336.3465286

[8] Marc Brooker. “Metastability and Distributed Systems.” brooker.co.za, May 2021. Archived at perma.cc/7FGJ-7XRK

[9] Lexiang Huang, Matthew Magnusson, Abishek Bangalore Muralikrishna, Salman Estyak, Rebecca Isaacs, Abutalib Aghayev, Timothy Zhu, and Aleksey Charapko. “Metastable Failures in the Wild.” At 16th USENIX Symposium on Operating Systems Design and Implementation (OSDI), July 2022.

[10] Marc Brooker. “Exponential Backoff and Jitter.” aws.amazon.com, March 2015. Archived at perma.cc/R6MS-AZKH

[11] Marc Brooker. “What Is Backoff For?” brooker.co.za, August 2022. Archived at perma.cc/PW9N-55Q5

[12] Michael T. Nygard. *Release It!*, 2nd edition. Pragmatic Bookshelf, 2018. ISBN: 9781680502398

[13] Frank Chen. “Slowing Down to Speed Up—Circuit Breakers for Slack’s CI/CD.” slack.engineering, August 2022. Archived at perma.cc/5FGS-ZPH3

[14] Marc Brooker. “Fixing Retries with Token Buckets and Circuit Breakers.” brooker.co.za, February 2022. Archived at perma.cc/MD6N-GW26

[15] David Yanacek. “Using Load Shedding to Avoid Overload.” Amazon Builders’ Library, aws.amazon.com. Archived at perma.cc/9SAW-68MP

[16] Matthew Sackman. “Pushing Back.” wellquite.org, May 2016. Archived at perma.cc/3KCZ-RUFY

[17] Dmitry Kopytkov and Patrick Lee. “Meet Bandaid, the Dropbox Service Proxy.” dropbox.tech, March 2018. Archived at perma.cc/KUU6-YG4S

[18] Haryadi S. Gunawi, Riza O. Suminto, Russell Sears, Casey Golliher, Swaminathan Sundararaman, Xing Lin, Tim Emami, Weiguang Sheng, Nematollah Bidokhti, Caitie McCaffrey, Gary Grider, Parks M. Fields, Kevin Harms, Robert B. Ross, Andree Jacobson, Robert Ricci, Kirk Webb, Peter Alvaro, H. Birali Runesha, Mingzhe Hao, and Huaicheng Li. “Fail-Slow at Scale: Evidence of Hardware Performance Faults in Large Production Systems.” At 16th USENIX Conference on File and Storage Technologies, February 2018.

[19] Marc Brooker. “Is the Mean Really Useless?” brooker.co.za, December 2017. Archived at perma.cc/U5AE-CVEM

[20] Giuseppe DeCandia, Deniz Hastorun, Madan Jampani, Gunavardhan Kakulapati, Avinash Lakshman, Alex Pilchin, Swaminathan Sivasubramanian, Peter Vosshall, and Werner Vogels. “Dynamo: Amazon’s Highly Available Key-Value Store.” At 21st ACM Symposium on Operating Systems Principles (SOSP), October 2007. doi:10.1145/1294261.1294281

[21] Kathryn Whitenton. “The Need for Speed, 23 Years Later.” nngroup.com, May 2020. Archived at perma.cc/C4ER-LZYA

[22] Greg Linden. “Marissa Mayer at Web 2.0.” glinden.blogspot.com, November 2005. Archived at perma.cc/V7EA-3VXB

[23] Jake Brutlag. “Speed Matters for Google Web Search.” services.google.com, June 2009. Archived at perma.cc/BK7R-X7M2

[24] Eric Schurman and Jake Brutlag. “Performance Related Changes and Their User Impact.” Talk at Velocity 2009.

[25] Akamai Technologies, Inc. “The State of Online Retail Performance.” akamai.com, April 2017. Archived at perma.cc/UEK2-HYCS

[26] Xiao Bai, Ioannis Arapakis, B. Barla Cambazoglu, and Ana Freire. “Understanding and Leveraging the Impact of Response Latency on User Behaviour in Web Search.” *ACM Transactions on Information Systems*, volume 36, issue 2, article 21, April 2018. doi:10.1145/3106372

[27] Jeffrey Dean and Luiz André Barroso. “The Tail at Scale.” *Communications of the ACM*, volume 56, issue 2, pages 74–80, February 2013. doi:10.1145/2408776.2408794

[28] Alex Hidalgo. *Implementing Service Level Objectives: A Practical Guide to SLIs, SLOs, and Error Budgets*. O’Reilly Media, 2020. ISBN: 9781492076813

[29] Jeffrey C. Mogul and John Wilkes. “Nines Are Not Enough: Meaningful Metrics for Clouds.” At 17th Workshop on Hot Topics in Operating Systems (HotOS), May 2019. doi:10.1145/3317550.3321432

[30] Tamás Hauer, Philipp Hoffmann, John Lunney, Dan Ardelean, and Amer Diwan. “Meaningful Availability.” At 17th USENIX Symposium on Networked Systems Design and Implementation (NSDI), February 2020.

[31] Gil Tene. “HdrHistogram: A High Dynamic Range Histogram.” hdrhistogram.github.io/HdrHistogram

[32] Ted Dunning. “The t-digest: Efficient Estimates of Distributions.” *Software Impacts*, volume 7, article 100049, February 2021. doi:10.1016/j.simpa.2020.100049

[33] David Kohn. “How Percentile Approximation Works (and Why It’s More Useful than Averages).” timescale.com, September 2021. Archived at perma.cc/3PDP-NR8B

[34] Heinrich Hartmann and Theo Schlossnagle. “Circllhist—A Log-Linear Histogram Data Structure for IT Infrastructure Monitoring.” arXiv:2001.06561, January 2020.

[35] Charles Masson, Jee E. Rim, and Homin K. Lee. “DDSketch: A Fast and Fully-Mergeable Quantile Sketch with Relative-Error Guarantees.” *Proceedings of the VLDB Endowment*, volume 12, issue 12, pages 2195–2205, August 2019. doi:10.14778/3352063.3352135

[36] Baron Schwartz. “Why Percentiles Don’t Work the Way You Think.” solarwinds.com, November 2016. Archived at perma.cc/469T-6UGB

[37] Walter L. Heimerdinger and Charles B. Weinstock. “A Conceptual Framework for System Fault Tolerance.” Technical Report CMU/SEI-92-TR-033, Software Engineering Institute, Carnegie Mellon University, October 1992. Archived at perma.cc/GD2V-DMJW

[38] Felix C. Gärtner. “Fundamentals of Fault-Tolerant Distributed Computing in Asynchronous Environments.” *ACM Computing Surveys*, volume 31, issue 1, pages 1–26, March 1999. doi:10.1145/311531.311532

[39] Algirdas Avižienis, Jean-Claude Laprie, Brian Randell, and Carl Landwehr. “Basic Concepts and Taxonomy of Dependable and Secure Computing.” *IEEE Transactions on Dependable and Secure Computing*, volume 1, issue 1, pages 11–33, January 2004. doi:10.1109/TDSC.2004.2

[40] Ding Yuan, Yu Luo, Xin Zhuang, Guilherme Renna Rodrigues, Xu Zhao, Yongle Zhang, Pranay U. Jain, and Michael Stumm. “Simple Testing Can Prevent Most Critical Failures: An Analysis of Production Failures in Distributed Data-Intensive Systems.” At 11th USENIX Symposium on Operating Systems Design and Implementation (OSDI), October 2014.

[41] Casey Rosenthal and Nora Jones. *Chaos Engineering*. O’Reilly Media, 2020. ISBN: 9781492043867
