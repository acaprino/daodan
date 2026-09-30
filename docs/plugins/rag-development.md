# RAG Development Plugin

> Design, build, and audit Retrieval-Augmented Generation systems. Covers the full pipeline from document chunking to answer generation, with deep Qdrant expertise and advanced patterns.

## Agents

### `rag-architect`

Expert in RAG system design covering the full pipeline: ingestion, chunking, embeddings, vector storage, retrieval, re-ranking, and answer generation.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Pipeline design, chunking strategy selection, hybrid search, production optimization |

**Invocation:**
```
Use the rag-architect to design a RAG pipeline for our knowledge base
```

**Expertise:**
- Chunking strategies (recursive, semantic, markdown-aware, parent-child, agentic)
- Embedding model selection (OpenAI, Cohere, open-source)
- Advanced patterns: Graph RAG, CRAG, Self-RAG, Agentic RAG
- Evaluation with RAGAS and DeepEval
- Cost/latency/accuracy trade-offs

---

### `qdrant-expert`

Qdrant vector database specialist for collection configuration, HNSW tuning, quantization, and production deployment.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Qdrant setup, HNSW parameter tuning, quantization, hybrid search, multi-tenancy |

**Invocation:**
```
Use the qdrant-expert to optimize our collection for 10M documents
```

**Expertise:**
- Collection configuration (named vectors, distance metrics, sharding, WAL)
- HNSW index tuning (`m`, `ef_construct`, `ef`, `full_scan_threshold`)
- Scalar INT8 quantization (75% memory reduction)
- GPU-accelerated indexing and ACORN algorithm
- Payload indexing and filtering

---

## Skills

### `rag-development`

Knowledge base covering every stage of RAG development.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Building RAG pipelines, choosing components, implementing advanced patterns |

**Quick start recipe:**
1. Chunking: recursive character splitting at 512 tokens, 10-15% overlap
2. Embedding: OpenAI `text-embedding-3-small` or Cohere `embed-v4`
3. Vector DB: Qdrant with scalar INT8 quantization
4. Retrieval: hybrid search (dense + sparse + RRF)
5. Evaluation: RAGAS from day one

**Reference docs:**
- `references/chunking-strategies.md`: splitting approaches by document type
- `references/embedding-models.md`: model comparison and selection
- `references/retrieval-patterns.md`: search, re-ranking, and fusion
- `references/advanced-rag-patterns.md`: Graph RAG, CRAG, Self-RAG, Agentic RAG
- `references/vector-databases.md`: DB comparison and selection
- `references/production-guide.md`: evaluation cadence, observability tooling, semantic caching, security (prompt injection, data access control, PII), cost and latency optimization, and a build-versus-adopt framework matrix

---

## Commands

### `/rag-development:rag-audit`

Audit a RAG implementation for quality, performance, and best practices.

```
/rag-development:rag-audit src/rag/
/rag-development:rag-audit "our customer support chatbot pipeline"
```

**Audit dimensions:**
- Chunking (chunk size, overlap, preprocessing of tables, images and headers, strategy matching document structure)
- Embeddings (current model, dimensions, caching at ingestion)
- Vector Database (payload indexes, quantization, HNSW parameters, on-disk storage)
- Retrieval (hybrid search, re-ranking, metadata filtering, MMR or diversity)
- Generation (context use, source attribution, streaming)
- Production (evaluation, observability, semantic caching, error handling for embedding API failures, rate limits and cost controls)
- Security (tenant isolation through mandatory filters, PII filtering at ingestion, prompt-injection sanitization, output validation)

Produces an actionable report: current state, risk areas, improvements ordered by impact, and a code example for each recommendation.

---

**Related:** [python-development](python-development.md) (Python implementation)
