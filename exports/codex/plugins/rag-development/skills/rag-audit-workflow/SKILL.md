---
name: rag-audit-workflow
description: 'Report quality and best-practice gaps in an existing implementation. TRIGGER WHEN: the user asks to review, audit, or validate a RAG pipeline: chunking, embeddings, retrieval, reranking, or production readiness. DO NOT TRIGGER WHEN: building from scratch (use rag-architect), or auditing a pure vector database (use qdrant-expert).'
---

> Arguments: `[path-or-description]`. Wherever `<arguments>` appears below, substitute the text the user typed after the skill name.

<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

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

<!-- Generated by the Daodan compiler for codex. Edit the kernel, never this file. -->

# RAG Audit

Analyze an existing RAG implementation and produce an actionable audit report.

## Instructions

1. **Identify RAG components** in the codebase:
   - Document ingestion/chunking code
   - Embedding model usage
   - Vector database configuration
   - Retrieval/search logic
   - Re-ranking (if any)
   - Prompt construction for LLM generation
   - Evaluation setup (if any)

2. **Audit each component** against best practices:

### Chunking
- [ ] Chunk size appropriate for use case (400-512 tokens default)
- [ ] Overlap configured (10-20%)
- [ ] Document preprocessing handles tables, images, headers
- [ ] Chunking strategy matches document structure

### Embeddings
- [ ] Model is current (not deprecated)
- [ ] Dimensions appropriate (not over-provisioned)
- [ ] Embeddings cached at ingestion (not re-computed)

### Vector Database
- [ ] Payload indexes created on filtered fields
- [ ] Quantization enabled (INT8 minimum for production)
- [ ] HNSW parameters tuned (m >= 16, ef_construct >= 100)
- [ ] On-disk storage configured for large collections

### Retrieval
- [ ] Hybrid search implemented (dense + sparse)
- [ ] Re-ranking applied (cross-encoder or Cohere Rerank)
- [ ] Metadata filtering for multi-tenancy/access control
- [ ] MMR or diversity mechanism to avoid duplicate results

### Generation
- [ ] Context window usage efficient (not stuffing irrelevant chunks)
- [ ] Source attribution in responses
- [ ] Streaming enabled for user experience

### Production
- [ ] Evaluation metrics in place (RAGAS or equivalent)
- [ ] Observability/tracing configured
- [ ] Semantic caching for repeat queries
- [ ] Error handling for embedding API failures
- [ ] Rate limiting and cost controls

### Security
- [ ] Tenant isolation enforced via mandatory filters
- [ ] PII filtering at ingestion
- [ ] Input sanitization for prompt injection
- [ ] Output validation

3. **Generate report** with:
   - Current state assessment (what's implemented)
   - Risk areas (what's missing or misconfigured)
   - Priority improvements (ordered by impact)
   - Code examples for each recommendation
