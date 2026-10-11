---
name: rag-development
description: >
  Knowledge base for production question-answering pipelines.
  TRIGGER WHEN: building, optimizing, or auditing RAG systems, including Graph RAG, CRAG, Self-RAG,
  and Agentic RAG.
---

<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
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

# RAG Development

Comprehensive knowledge base for building production-grade Retrieval-Augmented Generation systems.

## When to Use

- Building a new RAG pipeline from scratch
- Choosing chunking strategy, embedding model, or vector database
- Implementing hybrid search, re-ranking, or contextual retrieval
- Evaluating RAG quality with RAGAS or DeepEval
- Optimizing production RAG for cost, latency, or accuracy
- Designing multi-tenant RAG with access control
- Upgrading from naive RAG to advanced patterns

## Quick Start Recommendation

For 80% of use cases, start with:
1. **Chunking**: Recursive character splitting at 512 tokens, 10-15% overlap
2. **Embedding**: OpenAI `text-embedding-3-small` (best value) or Cohere `embed-v4` (best accuracy)
3. **Vector DB**: Qdrant with scalar INT8 quantization
4. **Retrieval**: Hybrid search (dense + sparse + RRF)
5. **Evaluation**: RAGAS metrics from day one

Then upgrade incrementally based on measured failures:
- Keyword misses -> add sparse vectors (SPLADE/BM25)
- Ambiguous chunks -> add contextual retrieval (Anthropic pattern)
- Irrelevant results -> add cross-encoder re-ranking
- Multi-hop failures -> upgrade to agentic RAG

## Reference Materials

Detailed reference documents are in the `references/` directory:

- `chunking-strategies.md` -- all chunking approaches with code, benchmarks, and selection guide
- `embedding-models.md` -- model comparison, Matryoshka embeddings, fine-tuning, sparse/dense/multi-vector
- `retrieval-patterns.md` -- hybrid search, HyDE, contextual retrieval, re-ranking, MMR
- `advanced-rag-patterns.md` -- Graph RAG, RAPTOR, CRAG, Self-RAG, Agentic RAG, multi-modal RAG
- `vector-databases.md` -- Qdrant deep dive, database comparison, scaling strategies
- `production-guide.md` -- evaluation, observability, caching, security, cost optimization

## Pipeline Architecture

```
Document Ingestion:
  Raw Docs -> Preprocessing (Unstructured.io) -> Chunking -> Context Enrichment -> Embedding -> Vector DB

Query Pipeline:
  User Query -> Query Transform -> Encode (Dense + Sparse) -> Hybrid Search -> Re-rank -> LLM Generation

Evaluation Loop:
  Ground Truth + Predictions -> RAGAS/DeepEval -> Faithfulness, Relevancy, Precision, Recall
```

## Key Decision Points

| Decision | Default | Upgrade When |
|----------|---------|-------------|
| Chunking | Recursive 512 tok | Structured docs -> markdown-aware; cross-refs -> late chunking |
| Embedding | text-embedding-3-small | Need accuracy -> embed-v4; self-hosted -> NV-Embed-v2 |
| Vector DB | Qdrant + INT8 | Already on Postgres -> pgvector; need managed -> Pinecone |
| Search | Dense only | Keyword misses -> add sparse hybrid; poor diversity -> add MMR |
| Re-ranking | None | Top-k results contain irrelevant items -> add Cohere Rerank |
| Caching | None | Production latency/cost concerns -> semantic cache |
| Evaluation | Manual spot checks | Any production use -> RAGAS automated metrics |
