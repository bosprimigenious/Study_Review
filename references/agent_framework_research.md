# Agent Framework Research

Last checked: 2026-06-27

This note records the practical direction for replacing Codex-only review behavior with reusable agent code that can call a configured model API. It is product and architecture guidance, not a dependency lock.

## Goal

Study Review needs a small agent system:

```text
StudyReviewOrchestrator
  -> KnowledgeAgent
  -> ReviewAgent
  -> ExamAnalysisAgent
  -> QuizGradingAgent
  -> MemoryAndScheduleAgent
  -> deterministic local tools
```

The agent runtime should let the maintainer plug in an API key and model name, then reuse the same review behavior outside Codex. It does not need to replace Codex's code-editing ability. It only needs to reproduce the study workflow:

```text
local materials
  -> evidence-grounded knowledge retrieval
  -> active recall
  -> grading
  -> mistake logging
  -> spaced follow-up
```

## Recommended Shortlist

| Framework | Fit for Study Review | Use when |
| --- | --- | --- |
| LangGraph | Best fit for durable review state, explicit graphs, tool nodes, human-in-the-loop checkpoints, and multi-agent routing. | Building the main reusable orchestrator. |
| OpenAI Agents SDK | Best fit for a compact Python-first implementation with agents, tools, handoffs, tracing, and simple model configuration. | Building a fast local prototype or OpenAI-model-first runtime. |
| AutoGen | Good fit for experimental multi-agent conversation patterns and agent teams. | Testing review-agent / knowledge-agent collaboration. |
| CrewAI | Good fit for role/task/process style multi-agent workflows. | Creating fixed pipelines such as "analyze materials -> plan -> generate quiz". |
| Semantic Kernel | Useful when the project becomes plugin-heavy or .NET/enterprise-integrated. | Later integration, not MVP. |

## Recommendation

Use this order:

1. **OpenAI Agents SDK prototype** for the smallest working model-connected agent bridge.
2. **LangGraph production path** when review state, retries, checkpoints, and multi-step routing need to be robust.
3. **AutoGen or CrewAI experiments** only for side-by-side comparisons of multi-agent collaboration quality.

Do not begin by installing a large framework into the core product. The existing deterministic tools and source policy are the asset. The runtime should wrap them, not replace them.

## Why LangGraph Is The Best Long-Term Fit

Study Review has a graph-shaped workflow:

```text
intent detection
  -> course snapshot
  -> source selection
  -> tool call
  -> validation
  -> user question / grading
  -> persistence
  -> next action
```

This maps cleanly to explicit graph nodes. It also keeps the system debuggable because every transition can record state and artifacts. That matters more than free-form agent chat for exam review.

Preferred LangGraph node split:

| Node | Responsibility |
| --- | --- |
| `classify_intent` | Map user request to `init_course`, `analyze_exam`, `generate_questions`, `make_plan`, `start_review`, `grade_answer`, or `due_review`. |
| `load_course_state` | Read `review/` files and summarize materials, plans, questions, mistakes, and due cards. |
| `select_sources` | Choose local evidence files by source priority. |
| `call_tool` | Run deterministic Python scripts or API service methods. |
| `validate_output` | Enforce source basis, labels, schema, and safety rules. |
| `route_agent` | Hand off to KnowledgeAgent, ReviewAgent, ExamAnalysisAgent, or QuizGradingAgent. |
| `persist_state` | Write only through approved tools. |
| `respond_next_action` | Return one concrete next action. |

## OpenAI Agents SDK Prototype Shape

The first prototype can stay small:

```python
from agents import Agent, Runner

knowledge_agent = Agent(
    name="KnowledgeAgent",
    instructions="Answer only from selected local course evidence.",
    tools=[search_local_materials, read_review_state],
)

review_agent = Agent(
    name="ReviewAgent",
    instructions="Run active recall before explanation. Ask one question at a time.",
    tools=[load_questions, grade_answer, append_mistake],
)

orchestrator = Agent(
    name="StudyReviewOrchestrator",
    instructions="Route study requests to the smallest useful next action.",
    handoffs=[knowledge_agent, review_agent],
    tools=[course_snapshot, analyze_exam, generate_questions, plan_review, due_today],
)

result = Runner.run_sync(orchestrator, user_input)
```

Model selection should be config-driven:

```yaml
provider: openai
model: gpt-4.1-mini
api_key_env: OPENAI_API_KEY
temperature: 0.2
```

## Agent Roles

### StudyReviewOrchestrator

Owns routing and state. It never invents course facts. It decides the next smallest action and calls one agent or tool.

### KnowledgeAgent

Answers course-content questions from selected local evidence. It should return:

```yaml
answer: string
source_basis:
  - file: string
    evidence: string
confidence: high | medium | low
```

If evidence is missing, it must say:

```text
仓库内资料不足，无法判断。
```

### ReviewAgent

Runs the study loop:

```text
ask one question
  -> wait for answer
  -> grade
  -> explain the gap
  -> optionally log mistake
  -> ask the next question
```

### ExamAnalysisAgent

Uses past-exam metadata and OCR/extraction outputs to identify patterns. It must label outputs as observed, inferred, or generated.

### QuizGradingAgent

Grades answers against local expected points. It should return score, missing points, misconception, and next review date.

### MemoryAndScheduleAgent

Maintains mistake logs, cards, and due items. It should be deterministic first; the model can explain priority but should not silently change schedules.

## Source Policy Still Wins

The framework may use web documentation for engineering decisions, but course facts must stay local-first:

```text
/Users/bosprimigenious/Important_FIles/2025-2026下
```

External model knowledge can help with phrasing, pedagogy, and generic explanation only when the output is clearly not presented as sourced course fact.

## MVP Implementation Plan

1. Keep the current CLI and FastAPI routes as deterministic tools.
2. Add a thin `AgentRuntime` adapter with provider/model configuration.
3. Implement OpenAI Agents SDK prototype around existing tools.
4. Add trace logging for intent, tool call, artifacts, and validation warnings.
5. Compare LangGraph for persistent state and multi-agent routing before making it the default runtime.
6. Keep AutoGen/CrewAI as research branches unless they outperform on measurable review tasks.

## Evaluation Questions

Use the same fixtures and real-course tests to compare frameworks:

- Can it enforce local source policy?
- Can it ask one active-recall question at a time?
- Can it grade consistently against expected points?
- Can it recover after a failed tool call?
- Can it preserve course state without hidden mutations?
- Can it explain why it chose the next action?
- Can it run with only provider/model/API-key changes?

## Decision

Do not replace Codex's coding workflow. Build Study Review as a reusable review-agent runtime with configurable model access. Start with the OpenAI Agents SDK for speed, design the state machine so it can graduate to LangGraph, and keep the multi-agent split small enough to test.
