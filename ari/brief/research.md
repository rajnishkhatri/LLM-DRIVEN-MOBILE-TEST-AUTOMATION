# Ripple Treasury "Ari" Craft Exercise: Panel Defense Research Brief

Your best defense is to present Ari as a deterministic, auditable routing and governance layer, not a chatbot. Ripple Treasury's own September 2026 GSmart launch says "financial calculations are handled by deterministic software" with AI used to interpret and explain, every agent action is approval-gated, and Jonathan Lange's public line is that "80–90% of AI work is Data Engineering."\[1\] Build the design around that philosophy, with BI answer accuracy named as the main risk and the 80% deflection target reframed into a phased, honestly measured goal.

## TL;DR

- **Match their philosophy.** Ripple Treasury (GTreasury, bought by Ripple for $1B; announced October 16, 2025; closed December 4, 2025, when Ripple's own post called it the "now-closed $1B acquisition") markets GSmart as "treasury-native AI." That means deterministic numbers, policy-cited recommendations, human approval gates and full audit logs. So make Ari's routing a pure, testable function over structured intent, with GPT-4o only at the edges (slot extraction and answer phrasing). Treat the user's entitlements as the core design constraint.
- **BI is the risky backend.** On enterprise schemas, GPT-4o's text-to-SQL success rate is about 10.1% on Spider 2.0, versus 86.6% on Spider 1.0. Even the top BIRD system (81.95%) trails human experts (92.96%). Omni's own AI avoids raw text-to-SQL and generates "semantic queries" through its semantic layer, which respects row-level security. Lean on that, show provenance, and eval numeric answers with exact-match checks, not an LLM judge.
- **80% deflection is a top-vendor ceiling, not a 6-week target.** Intercom Fin's 76% average across 12,000 customers took years (it started at 23%). In Gartner's survey of 5,728 customers (released August 2024), "only 14% of customer service and support issues are fully resolved in self-service." Complex B2B programs sit in the bottom quartile (about 22%). Propose roughly 25–35% verified resolution at 90 days on scoped tier-1 intents, rising toward 50%+. Measure "resolved with no ticket or reopen within 7 days," not "conversations that didn't escalate."

## 1. Company and business context

**Deal facts (quote these):**

- **Announcement.** Ripple announced the GTreasury acquisition on October 16, 2025 for $1 billion. It was Ripple's third major deal that year, after Hidden Road ($1.25B) and Rail ($200M).\[2\] Hg fully exited, and minority investor Mainsail Partners also sold.\[3\]
- **Close.** The deal closed December 4, 2025. That day Ripple's own post called it "Ripple's now-closed $1B acquisition of GTreasury," and GTreasury posted "We're officially part of Ripple!"
- **Ripple Treasury launch.** Ripple Treasury, "Powered by GTreasury," launched in late January 2026 (CoinDesk, January 30, 2026).\[4\] It is the first TMS with native digital-asset handling: digital-asset platforms are treated as "digital banks," RLUSD moves money cross-border in 3–5 seconds, and there is access to tokenized money-market funds such as BlackRock's BUIDL.\[4\]\[5\]\[6\]
- **Follow-on acquisitions.** Ripple Treasury acquired Solvexia (financial automation and reconciliation) in January 2026. Around March 11–12, 2026, Ripple announced it would buy BC Payments Australia Pty Ltd from Banking Circle to secure an Australian Financial Services Licence (The Paypers; DL News). Close was expected in April 2026 and the price was not disclosed.
- **Scale.** GTreasury was founded in 1986. Hg and Architect Partners cite 1,000+ customers across 160+ countries. Ripple's homepage cites 13,000 connected banks and $12.5T in payments volume (the $12.5T is GTreasury's own figure). The company is headquartered in Chicago, with EMEA (Dublin, London) and APAC (Sydney, Singapore, Manila) locations. Leadership: Renaat Ver Eecke (formerly GTreasury CEO, now SVP of Ripple Treasury) and Mark Johnson (CPO).\[7\]\[8\]

**GSmart AI timeline:**

- **June 18, 2025: launch** as "a comprehensive and purpose-built AI platform" with "agentic" capabilities. It was built out of GTreasury's Dublin Development Hub and aligned to ISO/IEC 42001, ISO/IEC 27001, GDPR and "readiness" for the EU AI Act.\[9\]\[10\] Claims include "explainable outputs linked directly to source documentation, backed by automated security monitoring and audit logging."\[11\] It runs on Microsoft Azure and AWS with data residency controls. It is embedded in SmartLedger, Forecast Insights, Liquidity Scenarios, Connectivity and Risk Management.\[12\]
- **Late 2025: GSmart Risk Insights.** It interprets FX and interest-rate exposures, detects anomalies and policy breaches, and writes executive narratives.\[7\]
- **September 10, 2026: agent expansion.** Agents now cover forecasting, liquidity, reconciliation, risk and reporting.\[13\] They "propose every move, cite the exact policy clause behind it, and wait for your approval."\[14\] Knowledge Studio lets customers encode the policies agents must follow. Interactions are logged as an audit trail.\[15\] Ripple says "financial calculations are handled by deterministic software, while AI is used to interpret policies, find patterns and explain recommendations." Adoption: 60% of eligible customers enabled Risk Insights and 44% use Forecast Insights.\[1\] Ver Eecke's framing: "This isn't simply AI-native treasury, but rather treasury-native AI."\[8\]
- **Separate Ripple-level agent payments push.** On June 10, 2026, Ripple shipped an XRP Ledger AI Starter Kit so autonomous agents can pay in XRP or RLUSD via the x402 machine-to-machine standard.\[16\] Press coverage of the September GSmart release notes it does not say XRP or RLUSD is required for the treasury agents.\[17\] Don't conflate the two in the panel.

**What this means for you:** Ari should look like GSmart's design language: deterministic where numbers matter, cited, approval-gated for actions (ticket creation is an action), and logged. Saying "the router is deterministic for the same reason GSmart computes figures in deterministic code" connects your design directly to the company's public positioning.

**Jonathan Lange (hiring manager):**

- **Career path.** Public profile data (RocketReach, The Org) shows an all-internal GTreasury career: DevOps Analyst (2017–2021), Platform Engineer (2021), Team Lead, Platform Engineering (2021–22), Manager, Platform Engineering (2022–25), Lead Engineer & Technical Advisor (2025), Principal AI Solutions Architect (2025–26), then Senior Director, AI at Ripple (2026). BA in Political Science, Elmhurst University. Based in Chicago.\[18\]\[19\]
- **Public statements.** His LinkedIn headline reads "I turn AI vision into customer-facing features in months, not years." A LinkedIn post of his says "I can't repeat this enough: 80–90% of AI work is Data Engineering."\[20\]
- **Implication.** He came up through platform and DevOps engineering, so expect deep probing on operations, resiliency and plumbing, not model trivia.
- **Expected first-round questions (from your recruiter, not public):** "Name a generative AI feature you built that real customers used. Who used it, and what broke?"; "How did you know the output was good enough? If the answer is 'we reviewed it manually' they haven't done this at any scale."; "Tell me about a use case you talked a team out of because AI was the wrong tool."\[21\]
- **What the panel wants to explore (also from your recruiter).** Influence without authority across teams that don't report to you, and building a greenfield roadmap "while simultaneously delivering against it."\[21\]
- **Unverified.** I found no public articles, talks or posts by Lange on a "no central AI team" philosophy, embedded engagements or evals. Treat those as things to ask him about, not things to quote.

## 2. Competitors

**Kyriba is the main competitor.**

- **Who names them.** Architect Partners lists GTreasury's main competitors as Kyriba, FIS Treasury & Risk Manager, ION Treasury and Coupa Treasury (Bellin).\[2\] Blockworks frames the deal as positioning Ripple against "incumbents such as Kyriba and SAP Treasury."\[22\] Ripple's own comparison blog concedes "when enterprise treasurers evaluate solutions, it typically comes down to GTreasury or Kyriba" and that "Kyriba has a larger current client base and higher payment volume."\[23\]
- **Ripple's counter-pitch (vendor claim).** 90-day cash visibility, versus Kyriba implementations of 2–12 months.\[23\]
- **G2 ratings.** Kyriba 4.5/5 from about 122 reviews; Ripple Treasury 4.2/5 from 32. G2 lists Kyriba as Ripple Treasury's top alternative, then Coupa and Agicap; Trovata also appears.\[24\]\[25\]
- **Market share (low-quality data).** 6sense puts Kyriba at about 65.6% and GTreasury at about 9.5%.\[26\] This is based on web-tech detection; don't quote it as market share.
- **Valuation.** Bridgepoint took majority control of Kyriba by leading a $160M growth round that "value[d] Kyriba at $1.2 billion" (Bridgepoint press release, March 28, 2019). In October 2024 Bridgepoint reinvested alongside new minority investor General Atlantic, in a deal that "values the company at over $3 billion" (Kyriba/Business Wire release).

**Kyriba's AI stack (know this cold):**

- **TAI ("Trusted Agentic AI").** Part of Kyriba's "Trusted AI" portfolio alongside Cash AI, Invoice AI and Fraud Detection AI. Kyriba says TAI uses its own embedded LLM rather than third-party LLM integrations, drawing on 20+ years of liquidity data.\[27\]
- **Positioning.** It is pitched at the "Trust Gap." In Kyriba's own survey, 76% of CFOs and treasury leaders worry security or privacy risks could hurt them.\[27\]
- **KyribaLive 2026 (Las Vegas, April 28, 2026).** Announcements: Circle USDC settlement orchestrated by TAI, J.P. Morgan Asset Management money-market investing inside the TMS, and an AFP co-branded "Stablecoins & On-Chain Liquidity in Treasury" certificate. Kyriba claims 4,000 customers;\[28\]\[29\] Melissa Di Donato is CEO.\[30\]
- **Read-through.** Both vendors now sell the same story: governed agentic AI plus stablecoin rails. That makes governance, auditability and answer correctness the differentiators, which is exactly what your Ari design should demonstrate.
- **Kyriba's own guide (vendor-published survey).** It cites a 2026 AFP survey of 240 practitioners piloting AI agents, in which 58% reported 40%+ time savings on cash positioning and forecast preparation.\[31\]

**Startups:** Treasury4 (Spokane, "data-first") acquired TreasuryGo, a Redmond SaaS built by former Microsoft treasurers.\[32\] Trovata and Agicap show up as G2 alternatives.\[25\] The startup threat is speed and UX, which is why a credible six-week CAB demo matters.

**Kyriba billboard story: unverified.** Targeted searches found no evidence of a Kyriba campaign or billboards around Chicago mocking the deal, nor the phrase "don't let payments be a ripple in how you do business." Search results only surfaced Ripple's own ads (Times Square, Las Vegas).\[33\]\[34\] If you raise it, frame it as hearsay ("I heard there was some competitive marketing…") or leave it out.

## 3. Treasury domain fluency

These are standard TMS concepts, from domain knowledge rather than a single source.

**Users:**

- **Treasury analysts** run the daily cash position and payments.
- **The treasurer** owns liquidity, funding, FX and interest-rate risk.
- **The controller and accounting** own reconciliation and GL posting.
- **The CFO** consumes forecasts and board-level narratives.

**Core flows:**

- **Bank connectivity.** Prior-day and intraday statements arrive through SWIFT (MT940/MT942, moving to camt.053/052 under ISO 20022), BAI2 files (common in the US), host-to-host SFTP or bank APIs. GTreasury markets 13,000 connected banks.\[14\]
- **Bank account mapping.** Each external account (bank, BIC/ABA, account number, currency) is mapped to an internal entity, account record and GL. Transaction codes (BAI type codes, MT940 :86: narratives) are mapped through categorization rules to cash-flow categories. GSmart has an AI "Connectivity" module, which suggests mapping and classification are an AI target internally.\[35\]
- **Cash positioning:** opening balances plus expected flows, giving today's position by entity and currency.
- **Forecasting and variance analysis.** The system compares forecast to actuals by category and period. The actuals are built from categorized bank transactions.
- **Payments.** Payment runs (AP, treasury and intercompany) go out over ACH, wire/Fedwire or SWIFT MT103/pacs.008, with maker-checker approval workflows, segregation of duties and sanctions screening.
- **Reconciliation:** matching bank activity to the ledger and forecasts (now strengthened by the Solvexia acquisition).

**"March forecast variance jumped and I think bank mapping is wrong" — how to handle it live.** This one question touches all three backends.

- **Root causes in TMS terms:**
  - **Account-mapping errors.** A new or changed bank account was never mapped, or was mapped to the wrong entity or currency, so its transactions are missing from or misassigned in actuals.
  - **Categorization-rule misses.** A bank changed transaction narrative or BAI codes, or a new counterparty appeared, so flows land in "uncategorized" or the wrong category, inflating variance in one bucket and deflating another.
  - **Missing or late statement feeds.** A failed MT940/BAI2 file, or a bank connectivity outage for some March days, so actuals are understated.
  - **Duplicates.** Intraday (MT942) plus end-of-day (MT940) both loaded, so actuals are double counted.
  - **FX or period effects.** Rate source or cut-off changes, or month-end timing.
  - **Genuinely a forecast problem,** not a data problem.
- **Ari's correct behavior.** This is a compound, ambiguous intent. A deterministic router should classify it as a diagnostic intent with entity "March," metric "forecast variance" and suspected cause "bank mapping." Then Ari should:
  1. Ask a disambiguation question or confirm scope (which entity or currency, which forecast version).
  2. Call Omni for variance by category and account for March vs. February, plus a count of unmapped or uncategorized transactions and any statement-feed gaps.
  3. Retrieve the help-center article on bank account mapping and categorization rules.
  4. Offer to open a JSM ticket pre-filled with the evidence, behind an explicit confirm step.
- **The deliberate design point.** Ari should never assert "your mapping is wrong." It should show the numbers and the query behind them, and let the human decide. That matches GSmart's "it proposes, you decide."\[14\]

**CAB demo:**

- **What a CAB is.** A Customer Advisory Board is a small group of strategic customers (often treasurers or finance leaders at key accounts) who preview roadmap items and give structured feedback.
- **What a CAB demo implies.** It shapes roadmap credibility and renewal sentiment. It is not a production launch. Treat it as a fixed-date demo: real backends, scoped intents, a scripted-but-live path, honest failure handling shown on purpose, and no promises about GA dates or deflection numbers. A failure that degrades gracefully in front of treasurers builds more trust than a polished happy path.

## 4. Routing architecture (core topic)

**Separate intent routing from model routing.** RouteLLM (LMSYS/Berkeley, ICLR 2025) routes between cheap and strong *models*, not between *backends*. It reports over 85% cost reduction on MT Bench at 95% of GPT-4 quality, sending only 14% of queries to the strong model. MMLU savings were 45% and GSM8K 35%, and router overhead was no more than 0.4% of GPT-4 generation cost.\[36\]\[37\] It's relevant later for cost (for example, GPT-4o-mini for chit-chat and summarization), but it's the wrong tool for deciding Omni vs. Confluence vs. JSM. Panels notice when candidates conflate the two.

**The four intent-routing patterns and their trade-offs:**

| Pattern | How | Pros | Cons | Ari use |
|---|---|---|---|---|
| Rules / deterministic | Regex, keyword, entity and slot rules over structured intent | Inspectable, unit-testable, zero latency, auditable | Brittle to paraphrase | Final decision layer |
| Embedding similarity (Aurelio `semantic-router`) | Cosine similarity to example utterances per route, thresholded | Fast (no LLM generation), cheap, tunable\[38\] | Needs good utterance coverage; returns no match outside coverage | Candidate generation and confidence signal |
| Small classifier (BERT/logistic) | Supervised intent model | Calibrated probabilities, cheap | Needs labeled data | Phase 2 once logs exist |
| LLM / function-calling router | GPT-4o picks a tool via function calling | Handles paraphrase and compound intents | Non-deterministic, harder to test, adds latency and cost, injection-steerable | Slot extraction only, inside a schema |

**Aurelio semantic-router specifics:**

- **Routes.** `Route(name, utterances, score_threshold)` objects feed a `SemantiсRouter` or `HybridRouter` (dense plus sparse).\[39\]
- **Thresholds.** You can set a global `score_threshold` or per-route thresholds. A threshold of 0.0 means the route "will be returned no matter how low it scores," while 1.0 requires an exact utterance match.\[39\]\[40\]
- **Tuning.** `fit()` and `threshold_random_search` optimize thresholds from labeled examples. The docs say it "works best with a large number of examples for each route and with many None utterances."\[40\]
- **No-match behavior.** The router returns no match when nothing clears the threshold.\[41\] That is your built-in fallback signal.
- **Coverage risk.** A 2026 arXiv comparison of four open-source routers found Aurelio's fallback rate was high on prompts its utterance set didn't cover.\[42\] Utterance coverage is the main risk.

**Recommended Ari design ("LLM proposes, code disposes"):**

1. **Normalize and extract.** GPT-4o, using structured outputs or a function-call schema, extracts a typed `Intent{type, entities, time_range, action_requested, confidence}`. It does not choose the backend.
2. **Score candidates.** An embedding router scores the raw utterance against the route utterances and produces a second, independent confidence.
3. **Decide.** A pure function `route(intent, embedding_scores, user_entitlements, backend_health) -> RouteDecision{primary, secondary[], needs_confirmation, reason_codes}` encodes explicit rules:
   - Any action verb ("open/create/raise ticket") goes to JSM, behind a confirmation step.
   - A metric, entity and period with a numeric ask goes to Omni.
   - "How do I / what is" goes to Confluence.
   - Compound intents fan out to several backends.
   - If the top-two margin is below δ, or the LLM and embedding signals disagree, ask a disambiguation turn ("Do you want me to pull March variance numbers, or show how bank mapping works?").
   - If the user lacks entitlement to a backend, that route is removed before scoring.
4. **Log everything.** Every `RouteDecision` is logged with reason codes and is replayable.

**Testing routing without an LLM in the loop:**

- Because `route()` is a pure function over a typed intent, unit tests use fixtures such as `Intent(type=METRIC_QUERY, metric="forecast_variance", period="2026-03")` → expect `OMNI`. These run in CI in milliseconds, deterministically.
- **Golden routing set:** about 200–500 labeled utterances per route, built from the CAB customers' real support tickets and help-center search logs. Include adversarial, compound and out-of-scope ("None") utterances.
- **Contract tests** per backend adapter use recorded responses (Omni query results, Confluence search JSON, JSM create-request responses), so answer formatting is tested without live calls.
- **Record and replay** the LLM extraction step: cache GPT-4o's structured outputs for the golden set so routing regressions are isolated from model drift. Run a separate, scheduled job that re-extracts with the live model to detect drift.

**Keep routing accuracy and answer accuracy separate:**

- **Routing metrics:** top-1 route accuracy, per-route precision and recall, confusion matrix (Omni↔Confluence confusion is the most likely), compound-intent recall, clarification rate, and false-confirm rate on actions.
- **Answer metrics, per backend:**
  - Omni: exact-match on numbers.
  - Confluence: groundedness and citation correctness.
  - JSM: field-level correctness of the created ticket.
- **End-to-end:** task success, which is only meaningful once both of the above are known. A wrong answer with a correct route is a backend problem; a right answer from the wrong route is luck.
- I did not find published, independently audited routing-accuracy numbers for production enterprise assistants. Don't quote any; say you'd set targets from your golden set (for example, ≥95% top-1 on in-scope intents, with clarification preferred over misroutes).

**Azure and LangGraph patterns:** In LangGraph, routing is a conditional edge, a plain Python function over graph state. That is the same "routing as a pure function" idea and is easy to unit test. In a .NET/Azure stack, the same pattern works with Semantic Kernel or a plain C# router service. GPT-4o function calling is the extraction layer, not the decision layer.

## 5. Evals and quality

**BI answers are the high-risk backend (hard numbers):**

- **Spider 2.0 (ICLR 2025).** On 632 real enterprise workflows (databases often over 3,000 columns, BigQuery and Snowflake dialects), "GPT-4o… success rate is only 10.1%… compared to 86.6% on Spider 1.0."\[43\]\[44\] o1-preview solved 17.1–21.3%.\[43\]\[45\] Spider 2.0-lite best traditional method: 5.7%.\[46\] By 2026, GPT-5-based agents top the Spider 2.0-DBT leaderboard at about 39.7%, still failing most tasks.\[43\]
- **BIRD.** Human performance is 92.96% execution accuracy. The top listed system, AskData + GPT-4o, scores 81.95%. The original GPT-4 baseline scored 54.89% with domain hints and 34.88% without.\[47\]\[48\]
- **Caveat on BIRD scoring.** A 2025 study (FLEX metric) found BIRD's strict execution accuracy agrees with human experts only 62% of the time, mostly false negatives.\[49\] A benchmark score is not the same as user-perceived accuracy, in either direction.
- **Omni's mitigation.** Omni says its AI "does not generate raw SQL directly from text; we found that this process can produce inconsistent results." Instead it generates "semantic queries" through the semantic layer, which "will reuse existing data models, respect row-level security." Omni uses AWS Bedrock-hosted Claude for most tasks and OpenAI only for advanced visualizations.\[50\] Blobby shows its plan and task list visibly.\[51\] Omni can act as an MCP server (February 2026).\[52\] As of April 2026, Blobby can "weave together" governed queries with full SQL for complex questions, which is more power and more risk.\[53\]
- **Practical upshot for Ari.** Don't have GPT-4o write SQL against Ripple Treasury data. Delegate numeric questions to Omni's governed layer or a curated topic. Tune Blobby via `ai_context`, `ai_fields`, `sample_queries` and AI-specific topic extensions.\[54\] Display the semantic query and filters as provenance.

**Eval plan by route:**

- **Omni:** a golden set of (question, expected semantic query or fields, expected result value), scored by deterministic exact or tolerance match on numbers, with SQL or semantic-query equivalence as a secondary check. Don't use an LLM judge for numbers. A judge can be fooled by plausible formatting and can't verify arithmetic against the warehouse.
- **Confluence RAG:** groundedness (every claim supported by retrieved chunks), citation precision, and retrieval recall@k against labeled "correct article" IDs. An LLM judge is acceptable here, calibrated against about 100 human-labeled samples.
- **JSM:** action correctness, meaning the right request type and required `requestFieldValues` populated, the confirmation shown before creation, and no duplicate tickets. This is checked deterministically against a JSM sandbox.
- **Regression suite:** run on every prompt, model or router change in CI, with a release gate on routing accuracy and per-route answer metrics.
- **Rollout:** shadow mode first (Ari routes and answers silently next to existing support, compared offline), then a canary to CAB tenants, behind feature flags per route.

**Provenance UX:** Show the query or filters for numbers and citations for docs, collapsed by default and one click to expand. Treasury users are auditors by temperament, and GSmart's own positioning ("traceability of every AI-generated output back to its source data") makes exposing provenance the on-brand choice.\[55\] I did not find a rigorous published study quantifying provenance's trust effect for BI assistants. Present it as aligned with the company's and Omni's design choices, not as proven science.

## 6. Ticket deflection reality check

**Vendor and independent numbers:**

| Source | Figure | Caveat |
|---|---|---|
| Intercom/Fin (June 2026) | 76% average resolution, 12,000+ customers; started at 23%; "improving about 1% a month"; 65% enterprise guarantee | Vendor; mostly B2C and product-led SaaS; Salesforce acquired Fin for about $3.6B, closing September 10, 2026\[56\]\[57\]\[58\]\[59\] |
| Ada | About 52% average automated resolution across 550+ deployments | Vendor\[56\] |
| Decagon | 80% claimed average deflection | Vendor self-report\[60\] |
| Zendesk CX Trends 2026 (secondary) | Median tier-1 deflection 41.2%; bottom quartile 22.4% "dominated by complex B2B and healthcare" | Secondhand aggregation\[61\] |
| Gartner (released August 2024; 5,728 customers surveyed December 2023) | "Only 14% of customer service and support issues are fully resolved in self-service"; 36% even for "very simple" issues; 43% of failures were "couldn't find relevant content"; Eric Keller: "While 73% of customers use self-service at some point… it's concerning to see that so few fully resolve there" | Independent, customer-reported |
| Gartner forecast | Agentic AI will autonomously resolve 80% of *common* issues by 2029 | A forecast, not a measurement\[56\]\[62\] |
| Independent tests / B2B blogs | Fin 38% on a 500-ticket test;\[63\] B2B SaaS year-one "true deflection" 10–15% | Lower-quality sources; directional only\[64\] |

**Why 80% in six weeks is unrealistic for treasury SaaS:**

1. **Ticket mix.** Treasury tickets skew to tier-2 and tier-3 work: bank file failures, mapping, payment exceptions and configuration. These need system access and judgment, not article lookup.
2. **Knowledge base quality.** Fin's own trajectory, from 23% to 76% over years, shows the curve is driven by the knowledge base.\[56\]\[57\]
3. **Risk tolerance.** Payment and cash questions have asymmetric downside: a wrong deflection costs more than a ticket.
4. **Measurement inflation.** "Didn't escalate" is not "resolved."

**Reframe:**

- **Metric definition.** Define *verified resolution* as a conversation with no ticket created and no human contact on the same topic within 7 days, plus a positive or neutral CSAT. Report it next to the *containment* rate and the *ticket-creation quality* rate. Ari creating a well-formed ticket with the evidence already attached is a win: it cuts handle time even when it doesn't deflect.
- **Phased targets (my recommendation):** CAB demo shows the mechanics, with no deflection claim. At 90 days, 25–35% verified resolution on scoped tier-1 "how-to" intents. At 6–12 months, 50%+ as content and Omni topics mature. Keep 80% as the long-run aspiration for *tier-1 how-to intents only*.

## 7. Entitlements and governance

**The frame:** once Ari is the single entry point, it becomes the most privileged client of Omni, Confluence and JSM. A service-account design turns the assistant into a confused-deputy and data-exfiltration path. Governance is the architecture, not a feature.

**Patterns:**

- **On-behalf-of identity everywhere.** Confluence Cloud search is permission-trimmed to the caller: "only entities that the user has permission to view will be returned."\[65\] That works only if you call *as the user*, via OAuth 2.0 (3LO) or a forwarded identity. A single service account returns what *it* can see.\[66\]\[67\]
- **Omni.** Pass user attributes into Omni's embed or API session so its row-level security and topic access apply. Omni states its AI "respect[s] row-level security."\[50\]
- **JSM.** Raise requests as the customer. `raiseOnBehalfOf` is "not available to users who only have the Service Desk Customer permission," so design this explicitly.\[68\]
- **Azure AI Search (if you index help content yourself):**
  - Classic *security trimming* stores group IDs in a filterable field and filters with `group_ids/any(g:search.in(g, '…'))`.\[69\] This is string comparison that your app must keep in sync.\[70\]
  - The newer native Microsoft Entra ACL/RBAC enforcement validates the user's token, sent via the `x-ms-query-source-authorization` header, and trims results at query time. It also supports SharePoint ACLs and Purview sensitivity labels.\[70\]\[71\]
  - Watch the elevated-read option (`x-ms-enable-elevated-read`), which bypasses permission filters.\[72\] It must never be used on user paths.
  - Some of this is in preview, so confirm GA status for production.\[73\]
- **Tenant isolation:** hard multi-tenant boundaries on caches, vector indexes and conversation memory. This matters for SaaS serving 1,000+ corporate customers.

**OWASP Top 10 for LLM Applications (2025) items that matter here:**

- **LLM01 Prompt Injection.** Confluence pages and Jira ticket text are untrusted content that can carry indirect injection.\[74\]
- **LLM02 Sensitive Information Disclosure.**
- **LLM05 Improper Output Handling.**
- **LLM06 Excessive Agency.** Ticket creation must be schema-bound and user-confirmed.
- **LLM07 System Prompt Leakage.**
- **LLM08 Vector and Embedding Weaknesses.** Cross-tenant retrieval.
- **LLM09 Misinformation.**
- **LLM10 Unbounded Consumption.** Cost and denial-of-wallet.
- **Note:** OWASP's GitHub now labels a 2026 GenAI list as current and the 2025 list as "archived," while genai.owasp.org still shows 2025.\[75\]\[76\] Cite "2025" and acknowledge the 2026 update.
- **Key mitigation.** Because routing is deterministic code and ticket creation needs explicit confirmation, an injected instruction in retrieved text can't trigger an action on its own.

**Audit:** log user, tenant, intent, `RouteDecision` with reason codes, backend calls (query or CQL), retrieved document IDs, model version, prompt hash, output and confirmation events. That record matches GSmart's "automated security monitoring and audit logging" claim\[11\] and maps to SOC 2 change-management and logical-access controls. For SOX-relevant customers, it gives evidence that AI didn't alter financial data. Ari is read-only on financial data by design.

## 8. Resiliency and operations

**Azure OpenAI capacity (GPT-4o):**

- **Default quota.** GPT-4o DataZoneStandard defaults to 300,000 TPM per region per subscription, with "Enterprise" tiers higher.\[77\] RPM is set in proportion to TPM. The historic ratio is 6 RPM per 1,000 TPM, and some 2026 model versions use 10 RPM per 1,000 TPM.\[78\]\[79\] Azure evaluates RPM over 1- or 10-second windows, so bursts get 429s even under the per-minute limit.\[80\]\[81\]
- **Provisioned (PTU).** GPT-4o provisioned throughput gives 2,500 input TPM per PTU, with output tokens weighted separately.\[82\] Minimums are about 15 PTU for Global or Data Zone provisioned and 50 PTU for Regional. A Microsoft Q&A case shows a 450K TPM Global Standard deployment handling only about 20 RPM at about 21.5K tokens per request.\[83\] Token budget, not request count, is the binding constraint.
- **Illustrative sizing (my arithmetic).** 1,000 concurrent sessions, one turn per user every 2 minutes, gives about 500 RPM. At about 3K input tokens per turn (system prompt plus retrieved context), that is about 1.5M input TPM, or about 600 PTU of GPT-4o, or a multi-region Standard pool. That is why you should:
  - keep context small (route first, then retrieve only from the chosen backend);
  - use GPT-4o-mini for extraction where accuracy holds (the RouteLLM logic applied to cost);
  - cache frequent help answers;
  - consider PTU for the baseline plus Standard spillover, behind Azure API Management load balancing.

**Atlassian limits (Jira and Confluence Cloud):**

- **Points-based quota.** Enforcement for Forge, Connect and OAuth 2.0 (3LO) apps began March 2, 2026.\[84\] The default global pool is 65,000 points per hour shared across tenants. Per-tenant tiers are, for example, Enterprise 150,000 + 30 × users, capped at 500,000 points per hour. `POST /rest/api/3/issue` costs 1 point;\[84\] reads cost 1 point per object, and user or permission objects cost 2. "API token-based traffic is not affected," and stays under burst limits.\[84\]
- **Burst limits** are per tenant, per endpoint, via token bucket: GET 100 RPS, POST 100, PUT 50, DELETE 50. Some endpoints are far lower; the JSM `servicedeskapi/servicedesk/{id}/customer` GET is 5 RPS.\[84\]
- **429 handling.** Responses carry `Retry-After`, `X-RateLimit-Remaining` and `RateLimit-Reason` (for example `jira-burst-based`).\[84\] Atlassian advises retrying only idempotent calls and doubling the delay after successive 429s.\[84\]\[85\]
- **Design implications:**
  - Ticket creation (POST) is *not* idempotent, so use an idempotency key stored in your own system and check before retrying to avoid duplicate tickets.
  - Run per-backend circuit breakers with timeouts (for example, Confluence search 2–3 s, Omni query 10–20 s with streaming "working on it" status, JSM create 5 s).
  - Use bulkheads so a slow Omni doesn't starve help-center answers.

**Plumbing endpoints (for the "mostly plumbing" demo):**

- **JSM create request.** `POST /rest/servicedeskapi/request` with `serviceDeskId`, `requestTypeId` and `requestFieldValues` (a map of field ID to value). Optional: `raiseOnBehalfOf` and `requestParticipants`. Get the required fields per request type from `servicedesk/{serviceDeskId}/requesttype/{requestTypeId}/field`.\[68\]\[86\]
- **Confluence search.** `GET /wiki/rest/api/search?cql=...` (for example `type=page AND space=HELP AND text ~ "bank mapping"`), permission-trimmed to the caller. Scopes: `search:confluence` (classic) or `read:content-details:confluence` (granular). User-specific CQL fields are no longer supported on this endpoint.\[65\]

**Graceful degradation:**

- **Omni down:** answer with the help article plus "live numbers unavailable," and offer a ticket.
- **Confluence down:** fall back to a cached top-N article index.
- **JSM down:** queue the ticket with a durable outbox and tell the user plainly.
- **Azure OpenAI throttled:** fall back to the deterministic keyword router plus templated responses, or degrade to GPT-4o-mini.
- **Streaming:** stream tokens and stage updates ("Querying Omni…").

**First alerts and SLOs to propose:**

- Per-backend error rate and p95 latency.
- End-to-end p95 time-to-first-token.
- **Fallback/no-match rate** and **clarification rate**: a spike means utterance-coverage drift.
- **Routing-confidence distribution drift:** week-over-week shift in top-1 margin.
- 429 rate from Azure OpenAI and Atlassian.
- Ticket-creation failures and duplicates.
- Cost per conversation and tokens per turn.
- Thumbs-down rate per route.
- Page on backend outage and on error-budget burn; ticket on drift metrics.

## 9. Adding a source (Statuspage)

**Statuspage public JSON (no auth):**

- `GET /api/v2/status.json` returns an indicator of `none | minor | major | critical` plus a description such as "All Systems Operational" or "Partial System Outage."\[87\]
- `/api/v2/summary.json` returns components, unresolved incidents and maintenances.\[87\]
- `/api/v2/components.json` returns component statuses `operational | degraded_performance | partial_outage | major_outage`.\[87\]
- There is also an unresolved-incidents endpoint (conventionally `/api/v2/incidents/unresolved.json`; verify the exact path on Ripple's page).

**Config, not code surgery:**

- **Source registry.** Each source is a config entry: `{id, adapter_type: "http_json", auth: none, endpoint, schema_map, route_utterances[], route_rules, entitlement_policy: public, timeout, cache_ttl: 60s, circuit_breaker}`. Adding Statuspage means adding a registry entry, about 20–40 route utterances ("is the platform down", "bank connectivity outage"), and one rule: incident or outage intent goes to the status source *first*, before ticket creation.
- **Ticket suppression.** When status shows an active incident on a component, Ari suppresses duplicate ticket creation and links the incident instead. That is a direct deflection win, and a good demo moment.
- **Generic adapter.** The adapter interface (`search/query/act`, health check, normalized `Evidence{source, id, url, snippet, fetched_at}`) means new sources need no router-code change, only a golden-set update and an eval run. Omni's "Omni is your MCP" direction suggests MCP as a future common adapter protocol.\[52\]

## 10. Consolidation politics (four teams, four assistants)

I did not gather primary sources on platform consolidation case studies (Spotify golden paths and similar) in this research pass. Treat this section as a practitioner framework, not cited fact.

- **Paved road, not mandate.** Offer the shared pieces each team would otherwise rebuild: identity propagation, audit logging, eval harness, routing registry, Azure OpenAI quota pooling and cost dashboards. Let teams keep their domain prompts and tools as registered "sources" or "skills." Adoption comes from removing their toil, since the role has no direct authority, which matches your recruiter's note about leading teams that don't report to you.\[21\]
- **Make the existing assistants the first registry entries.** The four assistants become routes or sources in Ari, and their owners keep ownership of their golden sets and answer-quality metrics. The platform owns routing accuracy, governance and operations. This also settles "who owns quality" cleanly: routing metrics belong to the platform, answer metrics to the product teams.
- **Deprecation playbook:** shadow-compare each legacy assistant against Ari on its own golden set, migrate when Ari is at parity or better, freeze legacy features, publish a dated sunset, then redirect.
- **Governance as the forcing function.** One audit trail and one entitlement model is a requirement a regulated-finance security or compliance team will back. It's the most defensible reason to consolidate.

## Recommendations: 6-week CAB plan

- **Week 1:** intent taxonomy from real tickets and help-center search logs; golden routing set v0 (about 300 utterances); typed `Intent` schema; source registry; OAuth on-behalf-of to Atlassian; Omni embed session with user attributes.
- **Week 2:** pure `route()` function plus unit tests in CI; Confluence CQL adapter with citations; JSM create with confirmation and an idempotency key.
- **Week 3:** Omni adapter via governed topics only, plus a numeric golden set (about 50 questions with exact answers); provenance UI.
- **Week 4:** compound-intent fan-out (the March-variance scenario end to end); disambiguation turns; degradation paths; Statuspage source to prove the extension model.
- **Week 5:** evals (routing confusion matrix, numeric exact match, groundedness, ticket correctness); load test against the Azure quota; alerts.
- **Week 6:** CAB tenant shadow run, demo script with a deliberate failure path, and buffer.
- **Scope cuts to state openly:** no autonomous ticket creation, no free-form SQL, English only, CAB tenants only, and no deflection number promised. The statement for the panel: "the CAB sees the governed mechanics and the measurement plan; the 80% is a 12-month tier-1 goal, measured as verified resolution."

## Caveats

- **Unverified:** the Kyriba Chicago billboard story; any Lange writing on "no central AI team" or evals; Ari-specific internal facts. Lange's interview questions come from your recruiter, not public sources.
- **GSmart claims** (ISO alignment, adoption percentages) are company-reported. The September 2026 agent details come from press coverage of a Ripple release.
- **Deflection numbers** are mostly vendor self-reports. The Zendesk 41.2% figure and the B2B 10–15% figure come from secondary aggregator blogs.
- **Azure quotas and PTU ratios** change by model version and region. Re-check the Microsoft Learn quotas page before quoting exact figures, and confirm whether Ripple uses GPT-4o or a newer model in production.
- **Sizing math** in Section 8 is illustrative arithmetic, not a benchmark.

## Sources

1. [Ripple news: XRP-linked firm puts AI agents inside its \$1 billion corporate treasury bet](https://www.coindesk.com/markets/2026/09/11/ripple-puts-ai-agents-inside-its-usd1-billion-corporate-treasury-bet)
2. [Ripple Acquires GTreasury for \$1B](https://architectpartners.com/ripple-acquires-gtreasury-for-1b/)
3. [Ripple buys GTreasury in \$1bn deal](https://www.fintechfutures.com/m-a/ripple-to-acquire-gtreasury-for-1bn)
4. [Ripple news: XRP-linked firm rolls out platform after \$1 billion GTreasury deal](https://www.coindesk.com/business/2026/01/30/xrp-linked-ripple-rolls-out-treasury-platform-after-usd1-billion-gtreasury-deal)
5. [Introducing Ripple Treasury, Powered by GTreasury](https://treasury.ripple.com/posts/introducing-ripple-treasury-powered-by-gtreasury-the-future-of-cfo-operations-is-here)
6. [Ripple Labs](https://en.wikipedia.org/wiki/Ripple_Labs)
7. [GTreasury Launches GSmart Risk Insights to Turn Complex Exposure Data into Board-Ready Intelligence](https://finance.yahoo.com/news/gtreasury-launches-gsmart-risk-insights-090000940.html)
8. [Ripple Treasury closes the gap on ungoverned AI agents](https://fintech.global/2026/09/11/ripple-treasury-closes-the-gap-on-ungoverned-ai-agents/)
9. [GTreasury Launches GSmart AI, Setting the Standard for Secure, Adaptable, and Agentic AI in Treasury Operations](https://www.gtreasury.com/news/gsmart-ai-secure-adaptable-agentic-ai-in-treasury)
10. [GTreasury launches GSmart AI, setting the standard for secure, adaptable and agentic AI in treasury operations](https://www.intelligentfin.tech/2025/06/26/gtreasury-launches-gsmart-ai-setting-the-standard-for-secure-adaptable-and-agentic-ai-in-treasury-operations/)
11. [GTreasury unveils AI platform for treasury, finance operations - FutureCFO](https://futurecfo.net/gtreasury-unveils-ai-platform-for-treasury-finance-operations/)
12. [Introducing GSmart AI: Intelligence You Can Actually Use](https://treasury.ripple.com/posts/gsmartai-intelligence)
13. [Ripple Adds AI Agents to Its \$1B Treasury Platform](https://financefeeds.com/ripple-is-putting-ai-agents-into-the-1-billion-treasury-software-business-it-bought-last-year/)
14. [Ripple Treasury, Powered by GTreasury](https://treasury.ripple.com/)
15. [Ripple Is Putting AI Agents In Charge Of Corporate Cash. Humans Will Still Have The Final Say.](https://www.ibtimes.com/ripple-putting-ai-agents-charge-corporate-cash-humans-will-still-have-final-say-3807388)
16. [Ripple Is Bringing Agentic AI Payments to the XRP Blockchain. Is This a Game Changer for XRP?](https://www.fool.com/investing/2026/07/03/ripple-is-bringing-agentic-ai-payments-to-the-xrp/)
17. [Ripple Just Put AI Agents Inside Its Treasury Software. Here's What They Can and Can't Do. - 24/7 Wall St.](https://247wallst.com/investing/cryptocurrency/2026/09/11/ripple-just-put-ai-agents-inside-its-treasury-software-heres-what-they-can-and-cant-do/)
18. [Jonathan Lange - Principal AI Solutions Architect](https://theorg.com/org/gtreasury/org-chart/jonathan-lange)
19. [Jonathan Lange Email & Phone Number](https://rocketreach.co/jonathan-lange-email_860085350)
20. [Jonathan Lange - Former GTreasury (HG Capital)](https://www.linkedin.com/in/jonathan-lange-ai-architect/)
21. mcp\_\_Gmail\_\_get\_thread
22. [Ripple acquires GTreasury in \$1B deal to expand into corporate finance - Blockworks](https://blockworks.co/news/ripple-acquires-gtreasury)
23. [Top 10 Treasury Management Systems for 2026](https://treasury.ripple.com/posts/top-10-treasury-management-systems)
24. [Top 10 Ripple Treasury, powered by GTreasury Alternatives & Competitors in 2026](https://www.g2.com/products/ripple-treasury-powered-by-gtreasury/competitors/alternatives)
25. [Top 10 Kyriba Alternatives & Competitors in 2026](https://www.g2.com/products/kyriba/competitors/alternatives)
26. [Kyriba - Market Share, Competitor Insights in Treasury Management](https://6sense.com/tech/treasury-management/kyriba-market-share)
27. [Kyriba Announces New Agentic AI for Treasury and Finance](https://sapinsider.org/map/kyriba-announces-new-agentic-ai-for-treasury-and-finance/)
28. [KyribaLive 2026: AI-Orchestrated Treasury Platform — Kyriba](https://www.kyriba.com/news/kyribalive-2026-ai-orchestrated-treasury/)
29. [Kyriba Brings AFP, J.P. Morgan Asset Management and Circle Into a Single AI-Orchestrated Treasury Platform](https://www.einpresswire.com/article/908726315/kyriba-brings-afp-j-p-morgan-asset-management-and-circle-into-a-single-ai-orchestrated-treasury-platform)
30. [Kyriba KLX London 2026: AI-Orchestrated Treasury for European Enterprises — Kyriba](https://www.kyriba.com/news/kyriba-klx-london-2026-ai-orchestrated-treasury/)
31. [Agentic finance: a no-hype guide for treasury teams — Kyriba](https://www.kyriba.com/resources/insights/agentic-finance-guide/)
32. [Ripple Acquires GTreasury for \$1 Billion](https://www.privsource.com/acquisitions/deal/ripple-acquires-gtreasury-for-1-billion-ane_JOSXzq)
33. [Ripple Ad on XRP, RLUSD Payments Shine Bright in NYC Times Square](https://www.cryptotimes.io/2025/06/18/ripple-ad-on-xrp-rlusd-payments-shine-bright-in-nyc-times-square/)
34. [Ripple Unveils Major XRP Billboard Campaign in Las Vegas](https://phemex.com/news/article/ripple-launches-major-xrp-billboard-campaign-in-las-vegas-76885)
35. [Treasury AI Software](https://treasury.ripple.com/solutions/ai/treasury-ai-platform)
36. [RouteLLM: Learning to Route LLMs with Preference Data](https://arxiv.org/pdf/2406.18665)
37. [LLM Routing: Intelligent Model Selection for Cost and Performance Optimization](https://zylos.ai/research/2026-01-29-llm-routing-intelligent-model-selection/)
38. [GitHub - aurelio-labs/semantic-router: Superfast AI decision making and intelligent processing of multi-modal data. · GitHub](https://github.com/aurelio-labs/semantic-router)
39. [Routers - Aurelio AI](https://docs.aurelio.ai/semantic-router/user-guide/components/routers)
40. [semantic\_router.routers.base - Aurelio AI](https://docs.aurelio.ai/semantic-router/client-reference/routers/base)
41. [aurelio-labs/semantic-router architecture diagram](https://gitdiagram.com/aurelio-labs/semantic-router)
42. [Task- and Session-Level Model Routing: A Common-Interface Hybrid Evaluation of Four Open-Source Routers Across Four Benchmarks](https://arxiv.org/pdf/2608.14641)
43. [Spider 2.0](https://spider2-sql.github.io/)
44. [Text-to-SQL Accuracy: 91% on Benchmarks, 21% in Production](https://colrows.com/blogs/text-to-sql-benchmark/)
45. [Spider 2.0: Evaluating Language Models on Real-World Enterprise Text-to-SQL Workflows — Lacuna](https://lacuna.tiptreesystems.com/work/spider-2-0-evaluating-language-models-on-real-world-enterprise-text-to-sql/wrk_6cfd9bacc3599c103f7fba7e37ecd2cd)
46. [Spider 2.0: Evaluating Language Models on Real-World Enterprise Text-to-SQL Workflows](https://arxiv.org/html/2411.07763v2)
47. [BIRD Benchmark: The Real-Database Gap in LLM Text-to-SQL](https://beancount.io/bean-labs/research-logs/2026/06/06/bird-benchmark-text-to-sql-real-database-gap)
48. [BIRD-SQL Benchmark Scores & AI Model Leaderboard](https://benchmarklist.com/benchmarks/bird_sql/)
49. [Your Data Model Is the Semantic Layer](https://motherduck.com/blog/bird-bench-and-data-models/)
50. [AI analytics you can trust - Omni Analytics](https://omni.co/ai)
51. [Moving beyond simple questions with agentic AI - Omni Analytics](https://omni.co/blog/moving-beyond-simple-questions-with-agentic-ai)
52. [February 13, 2026 - Omni Docs](https://docs.omni.co/demos/2026/20260213)
53. [April 3, 2026 - Omni Docs](https://docs.omni.co/demos/2026/20260403)
54. [Skills](https://skills.lc/exploreomni/omni-cursor-plugin/exploreomni-omni-cursor-plugin-skills-omni-ai-optimizer-skill-md)
55. [GTreasury Launches GSmart AI, an Agentic AI FinTech Solution Built for CFOs and Complex Treasury Environments](https://ffnews.com/newsarticle/fintech/gtreasury-ai-powered-treasury-solutions/)
56. [What Resolution Rate Can AI Customer Support Achieve? (2026 Benchmarks)](https://www.lorikeetcx.ai/articles/resolution-rate-ai-customer-support-benchmarks-2026)
57. [How Much Does Intercom Fin Cost in 2026? \$0.99 per Outcome Explained](https://www.getmacha.com/blog/intercom-fin-ai-explained)
58. [From resolutions to outcomes: Evolving how Fin delivers value - The Intercom Blog](https://www.intercom.com/blog/from-resolutions-to-outcomes-evolving-how-fin-delivers-value/)
59. [Intercom Fin Pricing: The Per-Resolution Cost Breakdown ...](https://www.getmacha.com/blog/intercom-fin-pricing)
60. [AI Customer Support 2026: 50+ Adoption + ROI Data Points](https://www.digitalapplied.com/blog/ai-customer-support-statistics-2026-adoption-roi-data)
61. [Customer Service AI Agent Statistics 2026: 120+ Data](https://www.digitalapplied.com/blog/customer-service-ai-agent-statistics-2026-data)
62. [Customer Service and AI Statistics (2026), Source-Checked](https://getmacha.com/blog/customer-service-ai-statistics)
63. [Intercom Fin AI Review: We Tested It on 500 Tickets (2026)](https://builts.ai/blog/intercom-fin-ai-review/)
64. [Ticket Deflection Rate Benchmarks 2026: AI vs KB](https://happysupport.ai/blog/support-ticket-deflection-rate-benchmarks)
65. [Search... - The Confluence Cloud REST API](https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-search/)
66. [View-restricted pages cannot be found through AP.request('/rest/api/search') anymore - Confluence Cloud - The Atlassian Developer Community](https://community.developer.atlassian.com/t/view-restricted-pages-cannot-be-found-through-ap-request-rest-api-search-anymore/40301)
67. [Best way to check that a user has access to a Confluence page - Confluence Cloud - The Atlassian Developer Community](https://community.developer.atlassian.com/t/best-way-to-check-that-a-user-has-access-to-a-confluence-page/35803)
68. [The Jira Service Management REST API](https://developer.atlassian.com/server/jira-servicedesk/rest/v1005/api-group-customer-request/)
69. [Binary Republik: Security Trimming in Azure AI Search for Safe and Compliant RAG Pipelines](https://blog.binaryrepublik.com/2025/12/security-trimming-in-azure-ai-search.html?m=1)
70. [search document level access overview](https://learn.microsoft.com/en-us/azure/search/search-document-level-access-overview)
71. [azure-ai-docs/articles/search/search-document-level-access-overview.md at main · MicrosoftDocs/azure-ai-docs](https://github.com/MicrosoftDocs/azure-ai-docs/blob/main/articles/search/search-document-level-access-overview.md)
72. [Document Level Access in Azure AI Search: A Complete Guide to Secure RAG](https://deployedinazure.com/document-level-access-azure-ai-search-rag/)
73. [Microsoft Entra access control and security now available in Azure AI Search](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/announcing-enterprise-grade-microsoft-entra-based-document-level-security-in-azu/4418584)
74. [LLM security — prompt injection defense for production systems](https://introl.com/blog/llm-security-prompt-injection-defense-production-guide-2025)
75. [GitHub - OWASP/www-project-top-10-for-large-language-model-applications: OWASP Top 10 for Large Language Model Apps (Part of the GenAI Security Project) · GitHub](https://github.com/owasp/www-project-top-10-for-large-language-model-applications)
76. [LLMRisks Archive - OWASP Gen AI Security Project](https://genai.owasp.org/llm-top-10/)
77. [Azure OpenAI in Microsoft Foundry Models Quotas and Limits in Azure Government - Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/openai/quotas-limits-gov)
78. [Azure OpenAI in Microsoft Foundry Models Quotas and Limits - Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/openai/quotas-limits)
79. [Azure OpenAI Rate Limit Guide: TPM, PTU, and 429 Fixes](https://fast.io/resources/azure-openai-rate-limit/)
80. [Manage Azure OpenAI in Microsoft Foundry Models quota (classic) - Microsoft Foundry (classic) portal](https://learn.microsoft.com/en-us/azure/foundry-classic/openai/how-to/quota)
81. [Optimizing Azure OpenAI: A Guide to Limits, Quotas, and Best Practices](https://techcommunity.microsoft.com/blog/fasttrackforazureblog/optimizing-azure-openai-a-guide-to-limits-quotas-and-best-practices/4076268)
82. [Determine PTU sizing for a workload - Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/provisioned-throughput-sizing)
83. [GPT-4o Throughput Scaling for Production in East US: Cost-Optimized Approach to Achieve 50+ RPM - Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/5677348/gpt-4o-throughput-scaling-for-production-in-east-u)
84. [Rate limiting - Jira Cloud platform](https://developer.atlassian.com/cloud/jira/platform/rate-limiting/)
85. [Jira REST API Throttling.](https://jira.atlassian.com/browse/JRACLOUD-69262)
86. [How to define request type via API ticket creation? - Atlassian](https://community.atlassian.com/forums/discussion/2839098/how-to-define-request-type-via-api-ticket-creation)
87. [Atlassian Statuspage Status - API](https://metastatuspage.com/api)
