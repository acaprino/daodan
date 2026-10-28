---
name: rag-development
description: >
  Knowledge base for production question-answering pipelines.
  TRIGGER WHEN: building, optimizing, or auditing RAG systems, including Graph RAG, CRAG, Self-RAG,
  and Agentic RAG.
---

<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Claude binding: repository read, file discovery and content search use Read, Glob
and Grep; repository write and repository edit use Write and Edit; shell execution
uses Bash; network fetch uses WebFetch and network search uses WebSearch; a user
question uses AskUserQuestion. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

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
