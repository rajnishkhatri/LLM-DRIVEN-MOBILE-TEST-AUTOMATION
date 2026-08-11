# Mobile Test Automation LLM Pipeline - Brainstorm

**Date:** 2026-07-26  
**Status:** Brainstorm / SDD Stage 1  
**Related:**  
- [Compass Research Artifact](compass_artifact_wf-d19f43b7-e322-5052-814e-7ba2d0682adb_text_markdown.md)  
- [Blueprint Revision v2](blueprint-revision-v2.md)

---

## Problem Statement

Convert existing manual test scripts (currently executed by human testers on Perfecto Mobile) into automated test scripts for native iOS and Android apps using an LLM-powered agentic pipeline.

### Current State
- Human testers execute manual test scripts on Perfecto Mobile cloud devices
- Manual tests exist in ALM systems (Octane, OpenText ALM/QC) and Excel
- No automation framework in place for these tests

### Target State
- Automated Appium 2 test scripts generated from manual test descriptions
- Scripts execute on Perfecto Mobile cloud infrastructure
- Self-healing capabilities for locator maintenance
- Deterministic, reproducible pipeline

---

## Team Constraints

| Constraint | Details |
|------------|---------|
| **Language/Stack** | Java / Spring Boot |
| **LLM Access** | Orchestrator AI (enterprise LLM gateway) |
| **Build Phases** | Phase 1: Copilot-driven reasoning; Phase 2: Direct LLM calls |
| **Replay** | Must be deterministic pipeline |

---

## Phase 1 vs Phase 2 Strategy

### Load-Bearing Insight: Phase 1 = Asset Factory

> **"Phase 1 is not a throwaway prototype, it is the asset factory and data flywheel for Phase 2."**

Design every Phase 1 asset as the literal artifact that Phase 2 consumes:
- Prompt files (`*.prompt.md`) → `PromptTemplate` resources
- `copilot-instructions.md` → System prompt template
- Workspace context over exemplars → RAG retrieval over indexed repo
- Human corrections → Preference pairs for prompt tuning
- ReplayReports → Failure-class calibration data

**Institutional benefit:** Copilot is typically already sanctioned in banking environments. Phase 1 needs no new model risk approval while accumulating evidence (accepted conversions, failure taxonomies, human corrections) for Phase 2 approval.

### Phase 1: Copilot-Driven Reasoning

The human is the orchestrator. Copilot is the reasoning engine. The repo is the context.

**Assets to build first:**
- `.github/copilot-instructions.md`: House rules (POM conventions, locator cascade, Perfecto capabilities, assertion mapping, when to emit `perfecto:ai:validation`)
- Prompt files (`*.prompt.md`): One per pipeline stage (`/parse-to-ir`, `/resolve-locators`, `/generate-test`, `/diagnose-replay`)
- Exemplar library: 3-5 gold conversions per screen family, committed to repo (free RAG via workspace context)

**Workflow per test:**
1. Engineer runs ingestion CLI → commits IR JSON
2. Engineer runs hierarchy-tool against live Perfecto device
3. Engineer invokes `/generate-test` in IDE → Copilot reads IR, hierarchy XML, instructions, exemplars → emits page objects + test class
4. Engineer reviews, adjusts, commits
5. CI triggers replay pipeline
6. On failure: feed ReplayReport to `/diagnose-replay`, apply fix
7. On certification: test + locators written to object repository, conversion joins exemplar set

### Phase 2: Direct LLM Pipeline

Phase 2 replaces the human driver with orchestration code. Nothing else moves.

| Phase 1 Asset | Phase 2 Equivalent |
|---------------|-------------------|
| copilot-instructions.md | System prompt template, versioned in Git |
| Prompt files | Spring AI `PromptTemplate` resources, same Git paths |
| Workspace context over exemplars | RAG retrieval over the same indexed repo |
| Human runs hierarchy-tool | Element Resolver service invokes it as a tool |
| Human review and approval | Confidence gates + HITL review queue for sub-threshold |
| Engineer triggers CI replay | Orchestrator triggers replay automatically |
| Engineer with /diagnose-replay | Healing service consuming ReplayReport, bounded to N cycles |

### Migration Path: Spring AI Abstraction

Use Spring AI's `ChatClient` and `ChatModel` as the abstraction layer:

```java
@Configuration
public class LLMConfig {
    
    @Bean
    @Profile("phase2")
    public ChatModel orchestratorChatModel(OrchestratorAIProperties props) {
        // If OpenAI-compatible, just configure base URL
        // If proprietary API, implement ChatModel interface
        return new OrchestratorAIChatModel(props);
    }
}

// Structured output via BeanOutputConverter
@Service
public class ParserAgent {
    private final ChatClient chatClient;
    private final BeanOutputConverter<TestCaseIR> converter;
    
    public TestCaseIR parse(String rawTest) {
        return chatClient.prompt()
            .system(loadPrompt("parse-to-ir"))
            .user(rawTest)
            .call()
            .entity(TestCaseIR.class);
    }
}
```

**Migration test:** Before cutover, run Phase 2 headless against the Phase 1 golden set. Certification-rate parity with human-driven conversion is the go/no-go gate.

---

## Candidate Frameworks & Tools

### Primary Test Framework: Appium 2

| Aspect | Details |
|--------|---------|
| **Why Appium 2** | Cross-platform (iOS/Android), driver-plugin architecture, W3C WebDriver compliance |
| **Perfecto Integration** | Native support via Perfecto's Appium 2 endpoint |
| **Language** | Java client (aligns with team capability) |
| **Drivers** | XCUITest (iOS), UiAutomator2 (Android) |

### Alternatives Considered

| Framework | Pros | Cons | Verdict |
|-----------|------|------|---------|
| **Appium 2** | Cross-platform, mature, Perfecto-native | Learning curve | **Selected** |
| **XCUITest native** | Apple-optimized | iOS-only | Reject (need both platforms) |
| **Espresso native** | Google-optimized | Android-only | Reject (need both platforms) |
| **Detox** | Fast, React Native | Limited native app support | Reject |
| **Perfecto Scriptless AI** | No-code | Less control, vendor lock-in | Complement, not replace |

### Orchestration Framework: Spring Services

The generation flow is a sequential pipeline with two bounded loops. Plain Spring services with explicit state transitions express this cleanly. Spring State Machine is optional; the pipeline does not require full graph semantics.

**LangGraph stays relevant only as a design vocabulary.** If graph semantics and checkpointing are wanted in Java, LangGraph4j is the port.

---

## Five-Module Decomposition

The schemas are the spine; every module is swappable as long as the schemas hold.

| Module | Description | Phase 1 | Phase 2 |
|--------|-------------|---------|---------|
| **ingestion** | Octane REST, ALM/QC REST, Excel via Apache POI → IR | Same | Same |
| **hierarchy-tool** | CLI + service: dumps Perfecto `getPageSource` XML and Object Spy output | Human runs, Copilot reads from workspace | Element Resolver invokes as tool |
| **conversion** | Manual test → automated code | Copilot workspace + prompt library | Spring AI service + Orchestrator AI |
| **replay** | Deterministic validation pipeline | Same (LLM-free) | Same (LLM-free) |
| **certification** | Quality gates + metrics publication | Same | Same |

### Three Schema Contracts

1. **TestCaseIR**: Ported from Pydantic to Java records with Jackson. JSON Schema exported via victools for sharing with Copilot and gateway.
2. **LocatorCandidate**: strategy, value, confidence, source.
3. **ReplayReport**: Feedback artifact consumed by both phases (see below).

### Stack Specifics

- Appium java-client 9.x with TestNG for execution
- Freemarker templates scaffold Page Object skeletons (LLM fills logic, not boilerplate)
- Static gate: google-java-format, Checkstyle, Error Prone, `mvn compile`
- Observability: OpenTelemetry with LLM spans exported to Langfuse
- Offline evaluation: Python tools (LangSmith, DSPy) acceptable since they don't ship to runtime

---

## Locator Strategy Priority

Based on stability and cross-platform compatibility:

| Priority | Strategy | iOS | Android | Notes |
|----------|----------|-----|---------|-------|
| 1 | Accessibility ID | `accessibilityIdentifier` | `content-desc` | Most stable, cross-platform |
| 2 | Resource ID | N/A | `resource-id` | Android-preferred |
| 3 | iOS Class Chain | `-ios class chain` | N/A | iOS-specific, performant |
| 4 | iOS Predicate | `-ios predicate string` | N/A | iOS-specific |
| 5 | UiAutomator | N/A | `UiSelector` | Android-specific |
| 6 | XPath | Supported | Supported | Last resort, brittle |

---

## Canonical Intermediate Representation (IR)

The IR is the structural contract between pipeline stages. Defined as Java records:

```java
public record TestCaseIR(
    String sourceSystem,          // "octane", "alm_qc", "excel"
    String sourceId,
    String title,
    List<String> preconditions,
    Map<String, String> testData, // keyed; secrets by vault key
    List<Step> steps,
    List<Platform> platforms,     // IOS, ANDROID
    Map<String, Object> provenance
) {}

public record Step(
    int index,
    String intent,                // normalized action intent
    ActionType action,            // TAP, TYPE, SWIPE, WAIT, ASSERT, LAUNCH, NAVIGATE
    TargetElement target,
    String inputData,
    Assertion assertion,
    ControlFlow controlFlow,      // loop/conditional/optional
    List<String> ambiguityFlags
) {}

public record TargetElement(
    String naturalReference,      // "the Login button"
    String elementType,           // button, field, toggle
    List<Locator> resolvedLocators,
    String screenContext          // screen/page name
) {}

public record Locator(
    LocatorStrategy strategy,
    String value,
    double confidence,            // 0.0 - 1.0
    LocatorSource source          // OBJECT_REPO, PAGE_SOURCE, VLM, LLM_GUESS
) {}

public record Assertion(
    AssertionKind kind,           // TEXT_EQUALS, ELEMENT_PRESENT, VALUE_CHECK, VISUAL, AI_VALIDATION
    String expected,
    String aiValidationPrompt     // for perfecto:ai:validation
) {}
```

---

## Agent Architecture (8-Agent Topology)

```
┌─────────────────────────────────────────────────────────────────┐
│                     INGESTION LAYER                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ ALM      │  │ Octane   │  │ Excel    │  │ Jira/    │        │
│  │ Adapter  │  │ Adapter  │  │ Adapter  │  │ Zephyr   │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       └─────────────┴─────────────┴─────────────┘               │
│                           │                                      │
│                           ▼                                      │
│              ┌────────────────────────┐                         │
│              │  Canonical IR (POJOs)  │                         │
│              └────────────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  AGENT ORCHESTRATION LAYER                       │
│                  (Spring State Machine)                          │
│                                                                  │
│   ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐         │
│   │ Parser │───▶│Planner │───▶│Element │───▶│ Code   │         │
│   │ Agent  │    │ Agent  │    │Resolver│    │  Gen   │         │
│   └────────┘    └────────┘    └────────┘    └────────┘         │
│        │             │             │             │               │
│        ▼             ▼             ▼             ▼               │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              Human-in-the-Loop Checkpoints              │   │
│   │         (Ambiguity resolution, approval gates)          │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐         │
│   │Self-   │◀───│Validator│◀───│Reviewer│◀───│ Style  │         │
│   │Healing │    │ Agent  │    │ Agent  │    │ Agent  │         │
│   └────────┘    └────────┘    └────────┘    └────────┘         │
│                                                                  │
│              ┌─────────────────────────────────────┐            │
│              │     LLM Client Abstraction          │            │
│              │   (Copilot ↔ Direct LLM swap)       │            │
│              └─────────────────────────────────────┘            │
│                           │                                      │
│                           ▼                                      │
│              ┌─────────────────────────────────────┐            │
│              │       Orchestrator AI Gateway       │            │
│              └─────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OUTPUT & EXECUTION                            │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ Appium 2 Scripts │  │ Perfecto Cloud   │                     │
│  │ (Java/TestNG)    │  │ Execution        │                     │
│  └──────────────────┘  └──────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Responsibilities

| Agent | Input | Output | LLM Tasks |
|-------|-------|--------|-----------|
| **Parser** | Raw manual test text | Structured IR steps | NLU, intent extraction |
| **Planner** | IR steps | Enriched IR with control flow | Sequence optimization, dependency detection |
| **Element Resolver** | IR target elements | Locators with confidence scores | Page source analysis, accessibility mapping |
| **Code Generator** | Complete IR | Appium Java/TestNG code | Template completion, assertion generation |
| **Style Agent** | Generated code | Style-matched code | RAG over existing test patterns |
| **Reviewer** | Generated code + IR | Review comments, score | Quality check, semantic fidelity |
| **Validator** | Code + device access | Pass/fail + diagnostics | Static analysis, optional device execution |
| **Self-Healing** | Failed locators | Updated locators | Re-resolution with new page source |

---

## Perfecto AI Integration

### AI Validation Commands

For brittle assertions (e.g., dynamic text, visual checks), use Perfecto's AI validation:

```java
Map<String, Object> params = new HashMap<>();
params.put("validation", "Is the account balance displayed correctly?");
params.put("reasoning", true);
Object result = driver.executeScript("perfecto:ai:validation", params);
```

### AI User-Action Commands

For natural language-driven actions:

```java
Map<String, Object> params = new HashMap<>();
params.put("action", "Scroll down until 'Settings' is visible, then tap it");
Object result = driver.executeScript("perfecto:ai:user-action", params);
```

### Perfecto MCP Server (Future)

Perfecto offers an MCP Server for AI-native integration, enabling:
- Direct device interaction through LLM tool calls
- Real-time page source retrieval
- Screenshot capture for vision-based locators

---

## Deterministic Replay Pipeline

The replay pipeline is boring on purpose. It is the instrument that makes LLM quality measurable, the audit surface for compliance, and the cost control on device minutes. **LLM output never touches it; it only consumes committed code.**

### Pipeline Stages

**Stage 1: Static Gate**
- Format check (google-java-format)
- `mvn compile`
- Checkstyle and Error Prone
- Rule: fail any locator not in object repository or LocatorCandidate manifest
- Runs in seconds, costs nothing, rejects most bad generations before device is touched

**Stage 2: Device Gate**
- Acquire device from pinned Perfecto pool by capability set
- Execute via TestNG with pinned Appium and driver versions
- Run K times (default 3 for conversion, 5 for certification)
- Pull Smart Reporting artifacts per run

**Stage 3: Verdict**
- Emit `ReplayReport` (schema below)
- Classification maps Appium exceptions and Perfecto failure reasons to failure classes

### ReplayReport Schema

```json
{
  "testId": "ACC-1042",
  "irVersion": "sha:4f2c...",
  "codeCommit": "sha:9be1...",
  "staticGate": { 
    "format": "PASS", 
    "compile": "PASS", 
    "findings": [] 
  },
  "deviceGate": {
    "device": { "platform": "iOS", "os": "17.5", "model": "iPhone 14" },
    "appVersion": "8.3.1",
    "appiumVersion": "2.19",
    "runs": [
      { 
        "run": 1, 
        "status": "FAIL", 
        "failedStep": 6,
        "failureClass": "LOCATOR_NOT_FOUND",
        "artifacts": { "report": "url", "video": "url", "pageSource": "url" } 
      }
    ],
    "passRatio": "2/3"
  },
  "verdict": "HEAL_REQUIRED",
  "pipelineVersion": "1.4.0"
}
```

### Failure Taxonomy (Rule-Based, Not LLM)

| Failure Class | Trigger | Action |
|---------------|---------|--------|
| `LOCATOR_NOT_FOUND` | Element not in DOM | Route to healing |
| `STALE_ELEMENT` | Element reference expired | Route to healing |
| `TIMEOUT_SYNC` | Wait exceeded | Check sync strategy |
| `ASSERTION_MISMATCH` | Expected vs actual mismatch | Review assertion logic |
| `APP_CRASH` | App terminated | Investigate app issue |
| `DATA_PRECONDITION` | Test data issue | Check data setup |
| `ENV_INFRA` | Device/lab infrastructure | Re-queue (never heal) |

### Determinism Controls

| Control | Implementation |
|---------|----------------|
| **Pinned tool versions** | Recorded in every ReplayReport |
| **Explicit waits only** | Lint rule banning `Thread.sleep` |
| **Fixed timeouts in config** | Not hardcoded in tests |
| **Single-writer discipline** | On object repository updates |
| **K-run flakiness policy** | Infrastructure failures = re-queue, not heal |

### LLM Determinism (Phase 2)

| Requirement | Implementation |
|-------------|----------------|
| **Temperature = 0** | Enforce in all Orchestrator AI calls |
| **Seed pinning** | Consistent seed values where supported |
| **Prompt versioning** | Prompts in Git with semantic versioning |
| **Response caching** | Cache by `hash(input + prompt_version)` |
| **Deterministic ordering** | Stable sort for locator ranking |

```java
@Service
public class DeterministicLLMClient {
    
    private final ChatClient chatClient;
    private final ResponseCache cache;
    
    public <T> T call(String promptId, String input, Class<T> outputType) {
        String cacheKey = hash(promptId, input, getPromptVersion(promptId));
        
        return cache.getOrCompute(cacheKey, () -> 
            chatClient.prompt()
                .system(loadPrompt(promptId))
                .user(input)
                .options(ChatOptions.builder()
                    .temperature(0.0)
                    .build())
                .call()
                .entity(outputType)
        );
    }
}
```

---

## Cost-Tiered Validation

| Tier | Scope | Cost | When to Use |
|------|-------|------|-------------|
| **Static** | Syntax check, linting, schema validation | Free | Every generation |
| **Dry-run** | Appium session init, element existence | Low | Before full execution |
| **Single-device** | Full execution on one platform | Medium | Certification gate |
| **Matrix** | Full execution on device matrix | High | Release certification |

---

## Certification Thresholds

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Pass rate** | ≥ 90% on first run | Automated tests passing without intervention |
| **Locator stability** | ≥ 85% survive 2 app versions | Locators still valid after app updates |
| **Semantic fidelity** | ≥ 95% steps match intent | Manual review sample |
| **Generation time** | < 30s per test case | End-to-end pipeline time |

---

## Risk Analysis

### Original Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Manual tests too ambiguous | High | High | Human-in-the-loop checkpoints, ambiguity flags |
| Locators break on app update | High | Medium | Self-healing agent, multi-locator strategy |
| LLM hallucination | Medium | High | Validator agent, static analysis gates |
| Perfecto API changes | Low | Medium | Abstraction layer for Perfecto commands |
| Orchestrator AI latency | Medium | Medium | Caching, async processing |

### Revision-Specific Risks (v2)

| Risk | Mitigation |
|------|------------|
| **Prompt drift between phases** | Copilot injects its own system scaffolding, so identical prompt text behaves differently through the gateway. Treat migration test against golden set as calibration exercise; budget a prompt-tuning sprint. |
| **Copilot context limits** | Large hierarchy XML files can blow context window. hierarchy-tool emits a pruned tree (interactive elements + ancestors) alongside full dump. |
| **Gateway constraints** | Rate limits, model deprecations, max-token ceilings outside team's control. ChatModel interface + retry/backoff at one choke point; smoke-test suite on every gateway model change. |
| **Determinism theater** | Deterministic pipeline over nondeterministic device lab can still flake. K-run policy and infra/heal separation are the honest handling; don't let pass-ratio thresholds slide to accommodate a flaky pool. |

---

## Phased Roadmap

### Weeks 0-3: Shared Spine
- [ ] IR records + JSON Schema export (victools)
- [ ] Ingestion connectors (Excel first)
- [ ] hierarchy-tool CLI
- [ ] Replay pipeline v1 (static gate + single-run device gate)

**Gate:** One hand-written Appium test flows end-to-end and yields a valid ReplayReport.

### Weeks 3-8: Phase 1 Live
- [ ] copilot-instructions.md
- [ ] Four prompt files (`/parse-to-ir`, `/resolve-locators`, `/generate-test`, `/diagnose-replay`)
- [ ] Exemplar seeding (3-5 per screen family)
- [ ] K-run policy implementation

**Gate:** 25 certified conversions, median under 2 hours of engineer time each.

### Weeks 8-14: Phase 1 at Scale + Flywheel
- [ ] Golden set to 50-100 conversions
- [ ] Failure-class base rates published
- [ ] Judge calibrated offline (TPR/TNR > 90%)
- [ ] ALM Octane adapter

**Gate:** First-replay pass rate of Copilot-generated code ≥ 60%.

### Weeks 14-22: Phase 2 Build
- [ ] Generation and resolver services on Orchestrator AI
- [ ] Spring AI integration with `BeanOutputConverter`
- [ ] Healing loop (bounded to N cycles)
- [ ] HITL queue for sub-threshold cases
- [ ] Confidence gates

**Gate:** Headless certification-rate parity with Phase 1 on the golden set.

### Week 22+: Cutover
- [ ] Autonomous conversion as default
- [ ] Humans on sub-threshold queue only
- [ ] Phase 1 tooling remains as manual escape hatch
- [ ] OpenText ALM/QC adapter
- [ ] Parallel test generation
- [ ] Vision-based locator support (VLM)

### Decision Triggers

| Condition | Action |
|-----------|--------|
| First-replay pass rate stalls below 40% | Invest in accessibility IDs in the app before scaling |
| Device minutes dominate cost | Tighten static gate, cut retries |
| Screen family resists hierarchy locators | Route assertions to `perfecto:ai:validation` |

---

## The Data Flywheel

Every Phase 1 conversion produces labeled data at no extra cost:

| Phase 1 Artifact | Phase 2 Use |
|------------------|-------------|
| Accepted code | Exemplars and golden set |
| Human corrections | Preference pairs for prompt optimization |
| Diagnose-and-fix sessions | Healing agent's few-shot library |
| ReplayReports | Failure-class base rates for LLM-as-judge calibration |

**Target:** 50-100 human-certified conversions before starting Phase 2 development. This corpus is the difference between tuning Phase 2 in a week and guessing for a month.

---

## Open Questions

1. **Copilot Skill Inventory:** What Copilot skills are currently available for test automation tasks?
2. **Orchestrator AI Capabilities:** What models are available? What's the latency/throughput?
3. **Existing Test Patterns:** Are there existing Appium tests to use for RAG/style matching?
4. **Object Repository:** Does the team maintain an element object repository for the apps?
5. **Test Data Management:** How is sensitive test data (credentials, PII) handled?

---

## References

- [Appium 2 Documentation](https://appium.io/docs/en/2.0/)
- [Perfecto Appium Integration](https://developers.perfectomobile.com/)
- [Spring AI Documentation](https://docs.spring.io/spring-ai/reference/)
- [Spring State Machine](https://spring.io/projects/spring-statemachine)
- [victools JSON Schema Generator](https://github.com/victools/jsonschema-generator)
- Compass Research Artifact (internal)
- Blueprint Revision v2 (internal)
