<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

# Production RAG Guide

Evaluation, observability, semantic caching, security, and the framework-overhead matrix that drives "build vs adopt" decisions.

## When to use

Hardening a RAG pipeline for production -- adding evaluation cadence, observability, caching, security boundaries, or picking between LangChain/LlamaIndex/Haystack/DSPy/from-scratch.

## Evaluation cadence (the operational rule)

- **Baseline scoring**: weekly minimum.
- **Regression evaluation triggers**: model updates, embedding refreshes, corpus changes, reranker swaps.
- **Stack**: RAGAS during design → DeepEval gates in CI → TruLens / Langfuse in production. Detail: see `advanced-rag-patterns.md` § Evaluation frameworks.

Core metrics worth scoring: Faithfulness (answer grounded in context), Answer Relevancy, Context Precision (chunks relevant), Context Recall (chunks cover ground truth), Hallucination rate.

## Semantic caching (high-leverage local pattern)

Recognize semantically equivalent queries (cosine > 0.95) and serve cached answers.

**Reported impact** (the numbers worth keeping):
- p95 response time: **2.1s → 450ms**
- API cost reduction: **50-80%**
- Hit rate: **45-65% first week, 60-80% over time** as the cache warms.

**RAGCache** (advanced): caches intermediate KV-cache states in a knowledge tree across GPU/host memory; up to **4× TTFT reduction**.

## Cost optimization checklist

- Matryoshka embeddings for two-stage retrieval (cheap broad, expensive narrow)
- Vector quantization (INT8 = ~75% memory savings vs fp32)
- Semantic caching for repeats / near-duplicates
- Batch embedding requests at ingestion
- Smaller models for evaluator/grader roles
- Anthropic prompt caching for contextual retrieval (the contextual prompt has heavy doc reuse)

## Latency optimization checklist

- Pre-compute embeddings at ingestion, never at query time
- Scalar quantization + in-memory index for sub-ms vector search
- Cap retrieval at top-k 5-10 (diminishing returns past that)
- Stream LLM responses
- Async parallel retrieval across indexes
- Two-stage Matryoshka retrieval to skip the expensive embedding for early filtering

Target: see `retrieval-patterns.md` (< 200ms total for retrieve + rerank + fetch).

## Security

### Prompt injection

- Strict context adherence -- responses limited to specific tasks.
- Specify output format, **require source citations**.
- Input sanitization: strip control characters, detect known injection patterns.
- Multi-layer defense: input filters + structured templates + output validation.

### Data access control

- **Mandatory `tenant_id` filter on every query in multi-tenant systems** -- omitting this is the #1 security incident in production RAG. Make it impossible to skip at the framework / wrapper layer.
- Namespace boundaries scoped by role / purpose.
- Per-user / per-query namespace restrictions via payload filtering.
- Principle of least privilege for the RAG application's data permissions.

### PII

- Filter / redact PII at ingestion **before embedding** (embeddings can leak training data otherwise).
- NER (Named Entity Recognition) for names, emails, addresses, financial data.
- Sanitize both user prompts and final responses.
- Audit logging for all data access.

## Framework matrix (build vs adopt)

| Framework | Best for | Overhead | Connectors |
|-----------|----------|----------|-----------|
| **LlamaIndex** | Pure RAG, document Q&A | ~6 ms | 150+ data connectors |
| **LangChain** | Complex agentic workflows | ~10 ms | Broadest integrations |
| **LangGraph** | Stateful agent orchestration | ~14 ms | LangChain ecosystem |
| **Haystack** | Production NLP, regulated workloads | ~5.9 ms | Modular pipeline components |
| **DSPy** | Prompt optimization | ~3.5 ms | Programmatic prompt tuning |
| **From scratch** | Maximum control | 0 ms | Whatever you wire |

### When to build from scratch (the local heuristic)

- Maximum control over latency / cost is a hard requirement.
- Highly specialized retrieval pattern that doesn't fit framework abstractions.
- Avoiding framework lock-in is strategically important.
- You have a strong ML engineering team to maintain it.
- Pipeline is fundamentally simple (embed → search → generate).

A minimal RAG pipeline is **~50-100 lines of Python**. If your pipeline is genuinely simple, the framework adds more friction than value.

## Observability tooling (the production triad)

| Tool | Type | Key feature |
|------|------|-------------|
| **LangSmith** | Commercial | Deep LangChain integration, multi-step tracing |
| **Langfuse** | Open-source | Tracing + prompt versioning + dataset creation |
| **Arize Phoenix** | Open-source | Real-time observability + drift detection |

Pragmatic choice for new builds: **RAGAS / DeepEval for metrics + Langfuse for observability.**

## Official docs

- RAGAS: https://docs.ragas.io/
- DeepEval: https://docs.confident-ai.com/ (RAG metrics: https://deepeval.com/docs/metrics-ragas)
- Langfuse: https://langfuse.com/ (RAG eval cookbook: https://langfuse.com/guides/cookbook/evaluation_of_rag_with_ragas)
- TruLens: https://www.trulens.org/
- Arize Phoenix: https://phoenix.arize.com/
- LangSmith: https://docs.smith.langchain.com/
- LlamaIndex: https://docs.llamaindex.ai/
- LangChain: https://python.langchain.com/
- Haystack: https://haystack.deepset.ai/
- DSPy: https://dspy.ai/
- OWASP LLM Top 10: https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- OWASP LLM Prompt Injection Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html
- AWS securing RAG ingestion: https://aws.amazon.com/blogs/security/securing-the-rag-ingestion-pipeline-filtering-mechanisms/

## Related

- `advanced-rag-patterns.md` -- evaluation framework details
- `retrieval-patterns.md` -- the latency target this guide assumes
- `vector-databases.md` -- the storage layer's quantization options
- `embedding-models.md` -- the cost driver this guide caches
