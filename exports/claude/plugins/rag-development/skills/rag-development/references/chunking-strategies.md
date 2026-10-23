<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
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

# Chunking Strategies for RAG

Recursive 512-token splitting is the right default. Everything else is a specialization with measurable tradeoffs.

## When to use

Picking the right splitter for an ingestion pipeline. For semantic-similarity-based parent/child patterns that interact with retrieval, see `retrieval-patterns.md`.

## Default: Recursive Character Splitting at 512 tokens

**Benchmark**: a Feb 2026 study of 7 strategies across 50 academic papers placed recursive 512-token splitting first at **69% accuracy**; semantic chunking scored **54%**. Use recursive 512 unless you have a specific reason not to.

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=64,                                   # ~12% overlap
    separators=["\n\n", "\n", ". ", " ", ""],
)
```

## Optimal chunk sizes by use case

| Use case | Chunk size | Overlap | Notes |
|----------|-----------|---------|-------|
| General Q&A | 400-512 tok | 10-20% | Best default |
| Code search | 256-512 tok | 15-25% | Preserve function boundaries |
| Legal / compliance | 512-1024 tok | 20% | Larger context needed |
| Conversational | 128-256 tok | 10% | Precise, focused answers |
| Summarization | 1024-2048 tok | 10% | Broader context |

## Gotchas

- **Semantic chunking is rarely worth its compute cost.** NAACL 2025 Findings paper concluded computational costs aren't justified by consistent gains -- fixed 200-word chunks matched or beat semantic chunking across retrieval and generation tasks. Use only when documents have highly variable topic density AND budget allows it.
- **Overlap > 25% wastes index space without measurable recall gain.** 10-20% is the sweet spot.
- **Markdown-aware splitting** (`MarkdownHeaderTextSplitter` from LangChain) is much better for documentation than recursive char -- preserves header hierarchy as metadata.
- **Parent-child (small-to-big)**: index small chunks (128-256 tok) for precise retrieval, return parent chunks (1024-2048 tok) for LLM context. LlamaIndex has `SentenceWindowNodeParser` (sentence-level children with window) and `HierarchicalNodeParser` (multi-level).
- **Late chunking** (Jina, 2024): embed the full document with a long-context model first, THEN split (mean-pool token embeddings within chunk boundaries). Preserves cross-chunk context like pronouns, headers. Available in `jina-embeddings-v3`.
- **Agentic chunking** (LLM picks boundaries): expensive at indexing time but highest quality for heterogeneous documents -- worth it for small high-value corpora, not for wikipedia-scale.

## Document preprocessing tools (which one for what)

| Tool | Strength | License | Notes |
|------|----------|---------|-------|
| **Unstructured.io** | Element-level extraction (Title / NarrativeText / ListItem / Table / Image) | Apache 2.0 | Table extraction score 0.844, hallucination 0.036 |
| **LlamaParse** | PDF + LlamaIndex integration | Commercial | Best PDF accuracy in the LlamaIndex ecosystem |
| **Docling (IBM)** | Open-source, good accuracy | MIT | Strong on technical PDFs |
| **Apache Tika** | Broadest format support | Apache 2.0 | Lower extraction accuracy; use as fallback |

## Official docs

- LangChain text splitters: https://python.langchain.com/docs/concepts/text_splitters
- LlamaIndex node parsers (parent-child): https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/
- Jina late chunking: https://jina.ai/news/late-chunking-in-long-context-embedding-models/ (paper https://arxiv.org/pdf/2409.04701, code https://github.com/jina-ai/late-chunking)
- Unstructured.io: https://docs.unstructured.io/open-source/introduction/overview
- Docling: https://github.com/DS4SD/docling
- LlamaParse: https://docs.llamaindex.ai/en/stable/llama_cloud/llama_parse/

## Related

- `retrieval-patterns.md` -- how chunk size interacts with reranker context windows
- `embedding-models.md` -- max-token limits per embedding model
- `advanced-rag-patterns.md` -- RAPTOR / contextual retrieval / parent-child interplay
