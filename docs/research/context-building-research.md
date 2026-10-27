<a id="code-context-research"></a>

# Code-context retrieval: scientific research and findings

[Used by Codebase Map](../plugins/codebase-map.md) · [Test diary](context-building-benchmarks.md)

## TL;DR

- **Problem:** Providing a coding agent with the context needed to resolve a request without consuming hundreds of thousands of tokens and without hallucinating identifiers.
- **Tested approach:** Hybrid retrieval (lexical FTS5 + dense EmbeddingGemma 2) with grounded query rewriting based on discovered symbols, delivering whole entities in rank order under budget constraints (6k / 12k / 24k characters).
- **Scientific findings:** Literature and empirical tests converge on a few stable principles: (1) keep the original question in the representation; (2) rewrite using only real codebase identifiers; (3) avoid indiscriminate graph expansion beyond 1 hop; (4) do not replace the query with fabricated code stubs.
- **Reference to local tests:** Experimental measurements, C1-C4 comparisons on private code, costs and rejected approaches are tracked in the [test diary](context-building-benchmarks.md).

## Why we conducted the research

1. **Failure of the legacy static-packet approach:** The previous Codebase Map context path (scope planner + static packet) yielded 72 refusals out of 72 attempts. Even after two redesign phases, it delivered only 21/38/46% of required code on Starlette compared to 31/47/52% for plain BM25 lexical search.
2. **Unsustainable cost of unguided autonomous exploration:** A generalist Sonnet agent exploring the codebase independently achieves 92% at 24k characters but consumes roughly 825,000 tokens per single request. A targeted pipeline was needed to supply relevant code using under 11,000 total tokens.
3. **Risk of hallucination and drift:** Naive query expansion or hypothetical code generation (stubs) invents non-existent symbols (up to 134 hallucinated names on private codebases), degrading correct rankings. Literature verification was required to identify repository-level code search architectures backed by empirical evidence.

## Links to cited papers

| # | Work / Paper | Link | What it measures | Relevant hypothesis |
|---|---|---|---|---|
| 1 | Gao, Ma, Lin, Callan. *Precise Zero-Shot Dense Retrieval without Relevance Labels* (HyDE). ACL 2023. | [arXiv:2212.10496](https://arxiv.org/abs/2212.10496) | Hypothetical document generation with LLMs; average of query and generated document vectors. | Keep the question within the dense vector rather than replacing it, encoding generated text as a document. |
| 2 | Li, Zhou, Shen. *Rewriting the Code: A Simple Method for Large Language Model Augmented Code Search* (ReCo). ACL 2024. | [arXiv:2401.04514](https://arxiv.org/abs/2401.04514) | Query rewriting into code and standard-style code across pools of 500–1,000 snippets. | Generated code helps only when resembling real codebase style. Original query + generated query beats generated alone in 8 out of 8 configurations. |
| 3 | Gurioli, Pennino, Gabbrielli. *Do not copy and paste! Rewriting strategies for code retrieval*. 2026. | [arXiv:2605.08299](https://arxiv.org/abs/2605.08299) | Rewriting across multiple abstraction levels on six CoIR tasks with different encoders. | The level of abstraction must be calibrated: prose rewrites can degrade strong encoders (Qwen3-Embedding-0.6B drops from 0.56 to 0.52). |
| 4 | Song, Zheng. *A Survey of Query Optimization in Large Language Models*. 2024, rev. 2026. | [arXiv:2412.17558](https://arxiv.org/abs/2412.17558) | Taxonomy of expansion, decomposition, disambiguation and abstraction. | Do not expand targeted queries that already specify exact symbols. Distribute rewrites across distinct interpretations of the request. |
| 5 | Ouyang, Yu et al. *RepoGraph: Enhancing AI Software Engineering with Repository-level Code Graph*. ICLR 2025. | [arXiv:2410.14684](https://arxiv.org/abs/2410.14684) | Tree-sitter repository graph; 1-hop vs 2-hop neighbourhood context on SWE-bench Lite. | One hop and names only: flat 2-hop context (~10,500 tokens) degrades resolve rate compared to 1-hop (~2,300 tokens). The graph must be filtered. |
| 6 | Liu, Song, Li, Yang, Qi. *Beyond Function-Level Search: Repository-Aware Dual-Encoder Code Retrieval*. Findings of EMNLP 2025. | [EMNLP 2025 Findings](https://aclanthology.org/2025.findings-emnlp.1147/) | Dual-encoder trained with dependency features and function-level adversarial verification. | Function/method-level units outperform file- or module-level units for targeted maintenance tasks. |
| 7 | Li, Dong, Lee et al. *CoIR: A Comprehensive Benchmark for Code Information Retrieval Models*. ACL 2025. | [arXiv:2407.02883](https://arxiv.org/abs/2407.02883) | 10 code retrieval datasets, NDCG@10, dense vs BM25. | Model parameter scale does not dictate quality (110M outperforms 567M). Dense models outperform BM25 by 2x to 3x on natural language queries. |
| 8 | Gandhi, Gao, Callan. *Repository-level Code Search with Neural Retrieval Methods*. 2025. | [arXiv:2502.07067](https://arxiv.org/abs/2502.07067) | BM25 on commit messages and CodeBERT reranker across 7 repositories. | Formulating realistic questions from Git history (pre-change commits). Reranker on top 20 candidates recovers 57% of the gain achieved by 100 candidates. |
| 9 | Rudenko (MadAppGang). *LLM Query Expansion Made Our Code Search Worse. Here's What Didn't*. 2026. | [MadAppGang Report](https://madappgang.com/blog/llm-query-expansion-made-our-code-search-worse.-he/) | 860 queries on local hybrid search for agents across 12 repositories. | Expansion with small LLMs degrades MRR@10 by 26–32%. The sole improvement (+21.8%) came from a regex router that isolates identifier searches. |
| 10 | Xia et al. *Agentless: Demystifying LLM-based Software Engineering*. 2024. | [arXiv:2407.01489](https://arxiv.org/abs/2407.01489) | File localization and hierarchical patch repair on SWE-bench Lite. | Combine lexical selection and embeddings prior to narrowing down to functions/classes. |
| 11 | Zhang et al. *LocAgent: Graph-Guided LLM Agent for Code Localization*. ACL 2025. | [ACL Anthology](https://aclanthology.org/2025.acl-long.426/) | Function-level localization guided by dependency graph. | Function-level Acc@10 benefits from combining BM25 and graph; selective expansion outperforms blind expansion. |
| 12 | *Skip the Compressor: Verbatim Context Selection for Code Repair*. 2026. | [arXiv:2610.21073](https://arxiv.org/abs/2610.21073) | Selection of verbatim source file excerpts without lossy compression. | Preserving intact, uncompressed source retains syntax and contracts compared to synthetic compression. |

## Content summary and findings

### 1. What holds and what literature supports

1. **Search-first with whole-entity ranking:** Splitting code into syntactic entities (functions, methods, classes) and delivering them intact in reciprocal rank order (RRF) outperforms chunk fragmentation and heuristic compression.
2. **Strict grounding of terms:** Query rewriting must rely exclusively on identifiers already present in the request or uncovered during the initial search pass. Unconstrained code fabrication degrades ranking on unseen private code.
3. **Preserving the original query:** As demonstrated by ReCo and HyDE, user queries must remain in the dense vector (or lexical channel) rather than being substituted entirely by generated rewrites.
4. **Graph as a filter or controlled boost, not an accumulator:** The call graph is valuable at 1 hop for rank boosting or suggesting related candidates (RepoGraph, LocAgent). Crowding context with 2+ hop neighbourhoods consumes token budget and reduces success rates.

### 2. What was refuted or downscaled

- **Hypothetical code stubs:** In empirical testing on private codebases, generating hypothetical stubs causes the LLM to hallucinate missing symbols, reducing code delivery by 8 percentage points at 24k characters.
- **Heavy rerankers on local CPU:** Cross-encoders (such as gte, sno or Qwen) achieve high recall but demand dozens of CPU seconds per query, making them unviable for interactive local execution without a GPU.
- **Unfiltered expansion for all queries:** For requests that directly name an exact symbol, any rewriting or expansion is redundant or counterproductive (MadAppGang, Song & Zheng).

### 3. Connection to the experimental diary

For quantitative benchmark breakdowns (C1–C4 comparisons on public and private datasets, recall@5/@20 tables, measured token consumption and dollar costs), see the dedicated document:
👉 [Context-building benchmark and test diary](context-building-benchmarks.md).
