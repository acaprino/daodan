<daodan_host_binding host="opencode">
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

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network fetch uses webfetch, network search uses
websearch, and a user question uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
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

# Vector Databases

## Comparison

| Database | Best For | Language | Hosting | Key Strength |
|----------|---------|---------|---------|-------------|
| **Qdrant** | Complex filtered search, production RAG | Rust | Self-host / Cloud | Payload filtering, quantization, hybrid search |
| **Pinecone** | Turnkey managed, enterprise | - | Managed only | Zero-ops, serverless, fastest time-to-production |
| **Weaviate** | Knowledge graph + vectors, GraphQL | Go | Self-host / Cloud | Schema-aware, built-in vectorizers, multi-modal |
| **Milvus** | Billion-scale, GPU-accelerated | Go/C++ | Self-host / Zilliz Cloud | Most index types (IVF, HNSW, DiskANN), GPU support |
| **ChromaDB** | Prototyping, small projects | Python | Self-host | Simplest API, in-process mode, fast setup |
| **pgvector** | Existing Postgres stack, mixed workloads | C | Self-host (ext) | SQL integration, no new infra, ACID transactions |

## Decision Framework

- **Prototyping**: ChromaDB (simplest) or pgvector (if already using Postgres)
- **Production RAG with filtering**: Qdrant or Weaviate
- **Managed/zero-ops**: Pinecone
- **Billion-scale**: Milvus with GPU
- **Existing Postgres**: pgvector
- **Knowledge graphs + vectors**: Weaviate

## Qdrant Deep Dive

See the `qdrant-expert` agent for comprehensive Qdrant configuration. Key highlights:

### Quantization Options
- **Scalar INT8**: 75% memory reduction, ~1% accuracy loss. Best default.
- **Binary**: 32x compression, 40x speedup. Best for >1024 dim models (OpenAI, Cohere).
- **Product Quantization**: Highest compression, higher accuracy trade-off.

### HNSW Parameters
- `m=16` (default) -- connections per node; 16-32 for text
- `ef_construct=100` (default) -- build quality; higher = better index
- `ef` (search-time) -- tune for recall/speed trade-off

### 2025 Features
- GPU-accelerated HNSW indexing
- Inline storage (quantized vectors embedded in graph)
- ACORN algorithm for filtered HNSW
- Score-Boosting Reranking
- Native MMR support

## Scaling Strategies

### Sharding
Distribute vectors across nodes by collection or hash. Milvus and Qdrant support automatic sharding.

### Replication
Read replicas for high-throughput scenarios. Qdrant supports configurable replication factor.

### Tiered Storage
- Hot: RAM (quantized vectors + HNSW graph)
- Warm: SSD with mmap (on-disk vectors)
- Cold: Disk with quantization (archive)

### Index-on-Disk
For cost-sensitive deployments: on-disk HNSW with quantized vectors in RAM for rescoring.

## pgvector Notes

Best for teams already running Postgres who want to avoid new infrastructure:
- `ivfflat` index: faster build, lower recall
- `hnsw` index: slower build, better recall (recommended)
- Limitations: no native sparse vectors, no built-in hybrid search, no quantization
- Use with `pgvector-scale` or `pgvectorscale` for improved performance

## References
- https://qdrant.tech/documentation/
- https://qdrant.tech/documentation/guides/optimize/
- https://qdrant.tech/articles/vector-search-resource-optimization/
- https://liquidmetal.ai/casesAndBlogs/vector-comparison/
- https://www.firecrawl.dev/blog/best-vector-databases
