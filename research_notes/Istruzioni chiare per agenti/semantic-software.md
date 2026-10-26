# Semantic code retrieval and prompt/agent design inventory

## What is actually used in the repository versus only read as background?

### Takeaway

The shipped retrieval core is snapshot-bound SQLite FTS5 plus optional, offline EmbeddingGemma 2 q4 inference and hybrid rank fusion. Most named papers are design evidence, not bundled algorithms; NumPy scoring and several rewrite/graph variants are measurements or proposals, not current shipped behavior. ([retrieval.py](../../plugins/codebase-map/skills/map-method/scripts/retrieval.py), [embedding_worker.py](../../plugins/codebase-map/skills/map-method/scripts/embedding_worker.py), [research page](../../docs/plugins/codebase-map-research.md))

### Cited Findings

#### Shipped software and prompt/agent behavior

| Item | Repository status verified in this task | Evidence |
|---|---|---|
| SQLite FTS5 | **Shipped.** `retrieval.py` builds whole-entity documents from path, name, signature and source, subtokens CamelCase/snake_case, and runs BM25 with column weights `0/10/5/3/1` for unindexed ID, name, path, signature and body. Exact entity/path/range/traceback anchors retain priority. The index is incremental, snapshot-bound and atomically published. | [retrieval.py, lines 18-29 and 73-105](../../plugins/codebase-map/skills/map-method/scripts/retrieval.py); [provider documentation](../../docs/plugins/codebase-map.md#local-retrieval-retrievalpy); [SQLite FTS5 primary documentation](https://www.sqlite.org/fts5.html) |
| EmbeddingGemma 2 | **Shipped as an opt-in provider.** It runs locally without model downloads or LLM calls during indexing/querying. Text documents and queries use different prefixes, and stale/incompatible generations cannot silently serve current results. | [embedding_worker.py](../../plugins/codebase-map/skills/map-method/scripts/embedding_worker.py); [embeddings contract](../../plugins/codebase-map/skills/map-method/references/embeddings.md); [Google model card](https://huggingface.co/google/embeddinggemma-2) |
| ONNX Runtime and tokenizers | **Shipped runtime dependencies**, pinned with NumPy at `onnxruntime==1.31.0`, `tokenizers==0.23.3`, `numpy==2.4.6`. Native inference runs in an isolated Python process with the CPU execution provider, four intra-op threads, one inter-op thread, one text per inference and no padding. | [worker metadata and GemmaProvider](../../plugins/codebase-map/skills/map-method/scripts/embedding_worker.py); [ONNX Runtime primary site](https://onnxruntime.ai/docs/) |
| Hybrid dense/lexical ranking | **Shipped.** Below exact anchors, the policy is `exact-rrf75-25-k60-v1`: reciprocal-rank fusion with dense weight `0.75`, lexical weight `0.25`, rank offset `60`, and missing-list rank `1000`. | [retrieval.py, lines 282-305](../../plugins/codebase-map/skills/map-method/scripts/retrieval.py); [embeddings contract](../../plugins/codebase-map/skills/map-method/references/embeddings.md#cache-and-consumption) |
| NumPy scoring | **Not shipped as the query scorer.** NumPy is used for ONNX input/output arrays, but `search()` unpacks vectors and computes every dot product with `math.fsum` in pure Python. A local probe recommends NumPy dot scoring as a cheap future optimization, without cache invalidation. | [current pure-Python scorer](../../plugins/codebase-map/skills/map-method/scripts/embedding_worker.py); [local probe and recommendation](../../docs/references/embeddinggemma-papers.md#measured-cpu-cost-local-probe-2026-10-26) |
| Two-pass grounded query rewriting | **Documented and locally measured; executable ownership not located in this inventory.** The recorded design searches the original question, gives the rewriter at most 40 discovered symbols plus graph neighbours of the first five, allows only names from the question/list, mechanically removes absent names, and merges rewritten rankings. A repository search found the detailed prompt only in the research document, not in the Codebase Map kernel. | [rewrite setup](../../docs/plugins/codebase-map-research.md#setup); [Codebase Map research basis](../../docs/plugins/codebase-map.md#research-basis-for-code-search) |
| Model routing | **Shipped generic routing machinery.** An LLM may classify bounded task signals, but `task_router.py` deterministically selects the model using actual host inventory, catalog tiers, capability/risk gates and request-specific confirmation. Tier1 and tier2 default to `cheapest`; tier3 defaults to `best`. It is not an embedding runtime or a model-call executor. | [task_router.py](../../plugins/model-routing/skills/model-routing/scripts/task_router.py); [task-routing contract](../../plugins/model-routing/skills/model-routing/references/task-routing.md) |
| Benchmark rewriter identity | **Benchmark configuration, not a universal hard-coded tier1 identity.** The retrieval experiments used `claude-haiku-5-5`; the current catalog declares `anthropic/claude-haiku-5-5` as tier1, but actual selection remains inventory- and request-dependent. | [benchmark setup](../../docs/plugins/codebase-map-research.md#setup); [catalog entry](../../plugins/model-routing/skills/model-routing/references/model-catalog.json); [routing rules](../../plugins/model-routing/skills/model-routing/references/task-routing.md#route-each-llm-node) |

#### Current q4 artifact/configuration, verified against the kernel

| Field | Current value | Evidence |
|---|---|---|
| Model/artifact | `onnx-community/embeddinggemma-2-ONNX`, q4 text graph, based on `google/embeddinggemma-2`; revision `daa72c51243991dfcaf9f9137d2c573d8f7790c0` | [worker constants](../../plugins/codebase-map/skills/map-method/scripts/embedding_worker.py); [pinned ONNX revision](https://huggingface.co/onnx-community/embeddinggemma-2-ONNX/tree/daa72c51243991dfcaf9f9137d2c573d8f7790c0) |
| Files and integrity | `onnx/model_q4.onnx`, `onnx/model_q4.onnx_data`, `tokenizer.json`; weights exactly `174,028,800` bytes; graph SHA-256 `f9eeba97acddf139b8ee2ddf04bc30dceafa88de93fadf74d7644e0d61a477a9`; weights SHA-256 `c3975f2d1ab7a1878ae31a7d7a9b7804a827aff3800b60dfceafce21cac3df49`; tokenizer SHA-256 `4d777ef5bdc1aa36227abdfb77c3e49e7b9c892d16e1b6bda41c393504828be4`. The documented total is about 206 MB. | [worker](../../plugins/codebase-map/skills/map-method/scripts/embedding_worker.py); [artifact contract](../../plugins/codebase-map/skills/map-method/references/embeddings.md#runtime-and-artifacts) |
| Documents and vectors | Encoded text is path + name + signature + body; document prefix `title: none \| text: `; query prefix `task: code retrieval \| query: `; output `sentence_embedding`, 768 dimensions, float32 storage after normalization; `MAX_TOKENS=2048`; no Matryoshka truncation in the shipped profile. | [worker constants/input/packing](../../plugins/codebase-map/skills/map-method/scripts/embedding_worker.py); [Google prompt and MRL rules](https://huggingface.co/google/embeddinggemma-2) |
| Multimodal inputs | The exported graph can accept image/video/audio features, but this provider passes empty arrays and ships only the text path. | [GemmaProvider](../../plugins/codebase-map/skills/map-method/scripts/embedding_worker.py); [ONNX model card](https://huggingface.co/onnx-community/embeddinggemma-2-ONNX) |
| Input-limit caveat | The `2048` cut is a worker choice, not a fixed sequence dimension in this ONNX export. The local reference records dynamic `batch_size`/`sequence_length` inputs and a successful 4096-token probe; the bundled contract still calls it an “encoder limit” and flags that wording for correction. | [evidence and wording caveat](../../docs/references/embeddinggemma-papers.md#use-in-this-repository); [current worker truncation](../../plugins/codebase-map/skills/map-method/scripts/embedding_worker.py) |

#### Background reading versus implemented algorithms

- **HyDE, ReCo, rewriting strategies, query-optimization survey and MadAppGang:** background for when/how to rewrite, not imported libraries. HyDE/ReCo-inspired single-vector fusion was measured as experiment A; code-stub rewriting B and per-entity corpus descriptions E were not adopted. The documented shipped comparison still uses merged rewritten rankings. ([Sources and experiments](../../docs/plugins/codebase-map-research.md#sources), [Rewrite and fusion experiments](../../docs/plugins/codebase-map-research.md#rewrite-and-fusion-experiments))
- **RepoGraph:** background for bounded graph context. Daodan already has its own static graph, not RepoGraph's implementation. Experiment D applied reference-based re-ranking; A+D improved early-budget delivery, while adding graph neighbours to final delivery had previously lost. Do not present RepoGraph or A+D as shipped without separate source evidence. ([research page](../../docs/plugins/codebase-map-research.md), [local graph/retrieval boundary](../../docs/plugins/codebase-map.md#local-retrieval-retrievalpy))
- **Beyond Function-Level Search:** background supporting whole-function/entity units and dependency features. Daodan ships parsed whole-entity retrieval, but not that paper's trained dual encoder or adversarial verifier. ([paper row](../../docs/plugins/codebase-map-research.md#sources), [retrieval documents](../../plugins/codebase-map/skills/map-method/scripts/retrieval.py))
- **CoIR, CodeRAG-Bench, RepoCoder, SWE-bench and repository-level neural retrieval:** evaluation/design background. None is the current local retrieval harness. RepoGraph used SWE-bench Lite; RepoCoder concerns iterative completion; the local gold harness instead measures whole gold entities and claim support under character budgets. ([EmbeddingGemma reference](../../docs/references/embeddinggemma-papers.md#from-a-question-to-the-files-it-uses), [local limits](../../docs/plugins/codebase-map-research.md#limits), [local harness](../../evals/codebase-map/context-scope/README.md))
- **Matryoshka Representation Learning:** a capability of the selected model and a possible future storage/scan lever. Current local inference remains 768d, so vendor MRL numbers are not measurements of the shipped q4 configuration. ([worker dimensions](../../plugins/codebase-map/skills/map-method/scripts/embedding_worker.py), [MRL paper](https://arxiv.org/abs/2205.13147), [model card](https://huggingface.co/google/embeddinggemma-2))

### Inferences

- The official page should use three explicit labels: **shipped**, **experimentally measured locally**, and **background only**. This avoids turning a paper-inspired experiment or a benchmark rewriter into a claimed production component. ([current source](../../plugins/codebase-map/skills/map-method/scripts/embedding_worker.py), [experiments](../../docs/plugins/codebase-map-research.md#rewrite-and-fusion-experiments))
- The most important current discrepancy to surface is NumPy: it is a pinned inference dependency and a measured optimization opportunity, but not the present dense-scan implementation. ([worker](../../plugins/codebase-map/skills/map-method/scripts/embedding_worker.py), [probe](../../docs/references/embeddinggemma-papers.md#measured-cpu-cost-local-probe-2026-10-26))

### Gaps

- The two-pass rewriter's executable prompt/owner was not found in the paths searched. The documentation calls its configuration shipped, but this inventory cannot independently bind that statement to a current kernel implementation. ([documentation](../../docs/plugins/codebase-map-research.md#setup))
- No retrieval benchmarks or runtime probes were rerun in this task; all measurements below are attributed to existing repository records or vendor pages. ([research page](../../docs/plugins/codebase-map-research.md), [EmbeddingGemma reference](../../docs/references/embeddinggemma-papers.md))

## Which existing documentation already covers these papers and should be linked rather than repeated?

### Takeaway

`docs/plugins/codebase-map-research.md` is already the canonical research-and-local-benchmark page for the eight collected papers and MadAppGang. `docs/references/embeddinggemma-papers.md` is the canonical EmbeddingGemma/model/MRL guide and additionally links CoIR, CodeRAG-Bench, RepoCoder and SWE-bench. The official page should deepen cross-links and provenance labels, not create a second bibliography or restate every result. ([research page](../../docs/plugins/codebase-map-research.md), [EmbeddingGemma reference](../../docs/references/embeddinggemma-papers.md))

### Cited Findings

#### Existing document ownership

| Existing document | Reuse it for | Do not duplicate |
|---|---|---|
| [Codebase Map: research and benchmarks behind code search](../../docs/plugins/codebase-map-research.md) | Eight-paper + MadAppGang evidence table; design synthesis; CodeRankEmbed versus EmbeddingGemma 2 local benchmark; rewrite/fusion experiments; limitations. | Paper abstracts, all local result tables, or another account of the same experiments. |
| [EmbeddingGemma: papers, guides and use for code search](../../docs/references/embeddinggemma-papers.md) | Model facts/prompts; vendor benchmarks; MRL; indexing guidance; ONNX Runtime threading; local CPU, NumPy and reliability probes; primary guide links; CodeRAG-Bench/RepoCoder/SWE-bench bibliography. | Vendor benchmark tables, prompt tables, thread/process probe tables, or primary-link lists. |
| [Optional local embeddings](../../plugins/codebase-map/skills/map-method/references/embeddings.md) | Shipped artifact, provisioning, runtime isolation, request interface, cache/freshness and fusion contract. | A prose description that can drift from worker constants. |
| [Codebase Map plugin documentation](../../docs/plugins/codebase-map.md#local-retrieval-retrievalpy) | Current retrieval behavior and research-basis links. | A second architecture description detached from the plugin owner. |
| [Model routing task contract](../../plugins/model-routing/skills/model-routing/references/task-routing.md) and [task_router.py](../../plugins/model-routing/skills/model-routing/scripts/task_router.py) | Actual prompt/agent routing responsibilities, deterministic selection, confirmation and resume. | Treating a benchmark model name as the router's permanent configuration. |
| [Context-scope results](../../evals/codebase-map/context-scope/RESULTS.md) | Older context-packet baselines, refusal/packing evidence and explicit note that CodeRankEmbed artifacts were removed. | Presenting its removed embedding arm as the current embedder benchmark. |
| [2026-10-23 research input](../../docs/superpowers/reports/2026-10-23-code-context-research-input.md) | Wider architecture/background, RepoCoder pseudocode, software licenses/maintenance observed on that date, evidence boundaries. | Current shipped-status claims or current dependency versions without revalidation. |

#### Canonical bibliography already linked by those documents

| Work | Exact title and publication year to link | Primary URL |
|---|---|---|
| HyDE | *Precise Zero-Shot Dense Retrieval without Relevance Labels*, ACL 2023; arXiv submission 2022 | https://arxiv.org/abs/2212.10496 |
| ReCo | *Rewriting the Code: A Simple Method for Large Language Model Augmented Code Search*, ACL 2024 | https://arxiv.org/abs/2401.04514 |
| Rewriting strategies | *Do not copy and paste! Rewriting strategies for code retrieval*, 2026 | https://arxiv.org/abs/2605.08299 |
| Query optimization survey | *A Survey of Query Optimization in Large Language Models*, 2024, revised 2026 | https://arxiv.org/abs/2412.17558 |
| RepoGraph | *RepoGraph: Enhancing AI Software Engineering with Repository-level Code Graph*, ICLR 2025 | https://arxiv.org/abs/2410.14684 |
| Repository-aware dual encoder | *Beyond Function-Level Search: Repository-Aware Dual-Encoder Code Retrieval with Adversarial Verification*, Findings of EMNLP 2025 | https://aclanthology.org/2025.findings-emnlp.1147/ |
| CoIR | *CoIR: A Comprehensive Benchmark for Code Information Retrieval Models*, ACL 2025 | https://arxiv.org/abs/2407.02883 |
| Repository-level neural retrieval | *Repository-level Code Search with Neural Retrieval Methods*, 2025 | https://arxiv.org/abs/2502.07067 |
| MadAppGang engineering report | *LLM Query Expansion Made Our Code Search Worse. Here's What Didn't*, engineering report, no peer-reviewed venue claimed | https://madappgang.com/blog/llm-query-expansion-made-our-code-search-worse.-he/ |
| CodeRAG-Bench | *CodeRAG-Bench: Can Retrieval Augment Code Generation?*, arXiv 2024, revised 2025; Findings of NAACL 2025 in the existing repository reference | https://arxiv.org/abs/2406.14497 |
| RepoCoder | *RepoCoder: Repository-Level Code Completion Through Iterative Retrieval and Generation*, EMNLP 2023 | https://arxiv.org/abs/2303.12570 |
| SWE-bench | *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?*, arXiv 2023; ICLR 2024 | https://arxiv.org/abs/2310.06770 |
| MRL | *Matryoshka Representation Learning*, NeurIPS 2022 in the existing repository reference | https://arxiv.org/abs/2205.13147 |

The first nine entries and their measured takeaways are already tabulated in the research page. CoIR, CodeRAG-Bench, RepoCoder, SWE-bench and MRL are also already linked in the EmbeddingGemma reference's “Papers and guides” table. ([research source table](../../docs/plugins/codebase-map-research.md#sources), [papers and guides](../../docs/references/embeddinggemma-papers.md#papers-and-guides))

### Inferences

- Make the official page a hub with deep links to `#sources`, `#embedding-benchmark`, `#rewrite-and-fusion-experiments`, `#limits`, the EmbeddingGemma reference's `#papers-and-guides` and `#use-in-this-repository`, and the shipped embeddings contract. This preserves one owner for each fact. ([docs navigation](../../docs/README.md#graphs-and-prototypes))
- Add CodeRAG-Bench, RepoCoder and SWE-bench to the official page only as a short “adjacent repository-level evaluation” link group pointing to the EmbeddingGemma reference. They do not need new summaries unless the page explains why their tasks differ from Daodan's whole-entity delivery metric. ([existing adjacency note](../../docs/references/embeddinggemma-papers.md#from-a-question-to-the-files-it-uses), [local limits](../../docs/plugins/codebase-map-research.md#limits))

### Gaps

- The existing reference's statement that no EmbeddingGemma 2 technical report or independent code-retrieval evaluation existed is explicitly a **2026-10-26 snapshot**, not a timeless fact. Re-check before presenting it as current later. ([snapshot and caveat](../../docs/references/embeddinggemma-papers.md))
- The older research-input document contains dated dependency/release observations and a proposed architecture. It should be linked as historical research, not silently merged with current implementation documentation. ([historical report](../../docs/superpowers/reports/2026-10-23-code-context-research-input.md))

## What do the collected folder README and the eight PDF filenames contribute, and what can we honestly say without rereading every PDF?

### Takeaway

The folder is a collection manifest and design rationale whose eight filenames correspond one-to-one to papers 1-8 in the existing research source table. It supplies provenance and the user's original reasons for collecting them; it does not provide new executable software. In this task I read only the README and directory listing, not the PDF bodies. ([Desktop README](file:///C:/Users/alfio/Desktop/Daodan%20research/README.md), [research source table](../../docs/plugins/codebase-map-research.md#sources))

### Cited Findings

#### Eight filenames and their contribution

| Collected filename | What it establishes without opening the PDF |
|---|---|
| `2022 HyDE, hypothetical document embeddings (arXiv 2212.10496).pdf` | Identifies HyDE by arXiv ID and its 2022 preprint year; the publication year in the repository bibliography is ACL 2023. |
| `2024 Rewriting the Code, generation-augmented code search (arXiv 2401.04514).pdf` | Identifies ReCo by arXiv ID and a descriptive shorthand, not the full paper title. |
| `2024 Survey of query optimization in LLMs (arXiv 2412.17558).pdf` | Identifies the survey and its initial 2024 year. |
| `2025 Beyond Function-Level Search, repository-aware dual encoder (EMNLP Findings).pdf` | Identifies the Findings paper and its dual-encoder topic. |
| `2025 CoIR benchmark for code information retrieval (ACL, arXiv 2407.02883).pdf` | Identifies CoIR, ACL and arXiv provenance. |
| `2025 RepoGraph, repository-level code graph (ICLR, arXiv 2410.14684).pdf` | Identifies RepoGraph, ICLR and arXiv provenance. |
| `2025 Repository file retrieval for bug questions, BM25 plus CodeBERT (arXiv 2502.07067).pdf` | Identifies the neural repository-search paper by arXiv ID and summarizes its BM25/CodeBERT approach; its filename is not the exact title. |
| `2026 Rewriting strategies for code retrieval (arXiv 2605.08299).pdf` | Identifies the 2026 rewriting-strategies paper by arXiv ID. |

Source for all eight filenames: [collected folder directory](file:///C:/Users/alfio/Desktop/Daodan%20research/). Exact canonical titles and URLs should come from the primary links in the previous section, not from these abbreviated filenames. ([research source table](../../docs/plugins/codebase-map-research.md#sources))

#### README-specific evidence

- The README is dated **2026-10-26** and explicitly frames the collection as “search-first code context” research for the Codebase Map redesign. ([Desktop README](file:///C:/Users/alfio/Desktop/Daodan%20research/README.md))
- It records design motivations: rewriting level must be measured; generated code can fail when unlike repository code; RepoGraph filters ubiquitous/library edges; Beyond Function-Level Search suggests dependencies plus intent expansion; CoIR offers comparable embedder/reranker evaluation; HyDE and the survey are background; repository neural retrieval uses commit-message BM25 plus CodeBERT reranking. These are **README assertions to link and compare with the canonical research table**, not findings independently verified from PDFs in this task. ([Desktop README](file:///C:/Users/alfio/Desktop/Daodan%20research/README.md), [canonical source table](../../docs/plugins/codebase-map-research.md#sources))
- It calls rewriting strategies “our arm 1,” says the current graph step lacks RepoGraph-style edge filtering, and reports “+12% Top-5” for Beyond Function-Level Search. Those details can be quoted only with attribution to the README unless checked against the experiment/paper. ([Desktop README](file:///C:/Users/alfio/Desktop/Daodan%20research/README.md))
- MadAppGang is explicitly “Not a PDF” in the collection. The README supplies its URL and repeats the 26-32% MRR@10 decrease over 860 queries/12 repositories; the canonical research page adds that model conditions ran on two repositories and that the regex routing classifier improved MRR@10 by 21.8%. ([Desktop README](file:///C:/Users/alfio/Desktop/Daodan%20research/README.md), [research source table](../../docs/plugins/codebase-map-research.md#sources))
- The repository research page independently states that all eight papers and the engineering report were read in full on 2026-10-26. That is a documented prior evidence claim, not a claim that this subagent reread them. ([research page](../../docs/plugins/codebase-map-research.md#sources))

### Inferences

- The folder adds collection provenance and rationale, while the existing research page already provides the more precise bibliographic and measurement synthesis. The official page should link the README as an internal collection note only if user-local paths are acceptable; otherwise record its role without exposing a machine-specific link. ([Desktop README](file:///C:/Users/alfio/Desktop/Daodan%20research/README.md), [research page](../../docs/plugins/codebase-map-research.md))
- Filename years and titles are discovery aids, not citation authority. In particular, use “ACL 2023” for HyDE and the exact title *Repository-level Code Search with Neural Retrieval Methods* rather than the filename paraphrase. ([primary HyDE record](https://arxiv.org/abs/2212.10496), [primary repository-search record](https://arxiv.org/abs/2502.07067))

### Gaps

- No PDF was opened or reread in this task. Therefore this inventory cannot independently verify page-level claims, the README's `+12% Top-5` figure, paper versions contained in the local files, or whether each PDF matches its filename. ([task evidence limited to README/listing](file:///C:/Users/alfio/Desktop/Daodan%20research/README.md))
- The folder contains no PDF for MadAppGang, EmbeddingGemma 2, CodeRAG-Bench, RepoCoder, SWE-bench or MRL; their evidence must come from their primary web records and existing repository documentation, not be attributed to this eight-PDF collection. ([directory listing](file:///C:/Users/alfio/Desktop/Daodan%20research/), [EmbeddingGemma reference](../../docs/references/embeddinggemma-papers.md#papers-and-guides))

## Which primary model/embedding documents and measurements should be linked from the official research page?

### Takeaway

Link both the Google base-model documentation and the ONNX Community artifact card/revision, then send readers to the repository's separate local benchmark and runtime probes. Vendor full-precision MTEB figures, ONNX quantization-similarity figures and Daodan q4 CPU/delivery measurements are different evidence classes and must not be blended. ([Google card](https://huggingface.co/google/embeddinggemma-2), [ONNX card](https://huggingface.co/onnx-community/embeddinggemma-2-ONNX), [local measurements](../../docs/references/embeddinggemma-papers.md#use-in-this-repository))

### Cited Findings

#### Primary links to feature

1. **Google EmbeddingGemma 2 model card:** architecture, 8,192-token model context, code-retrieval prefixes, full-precision MTEB results, MRL truncation and normalization, precision rules. https://huggingface.co/google/embeddinggemma-2
2. **Official Gemma documentation/model card and inference guide:** vendor-maintained usage and prompt API. https://ai.google.dev/gemma/docs/embeddinggemma/model_card_2 and https://ai.google.dev/gemma/docs/embeddinggemma/inference-embeddinggemma-with-sentence-transformers
3. **Google launch/developer guides:** release positioning and worked local-codebase example, dated 2026-10-06 in the existing reference. https://blog.google/innovation-and-ai/technology/developers-tools/embeddinggemma-2 and https://developers.googleblog.com/embeddinggemma-2-the-developer-guide/
4. **ONNX Community model card plus the exact pinned revision:** q4 artifact behavior/size and quantization-similarity table; the revision link prevents “latest” drift. https://huggingface.co/onnx-community/embeddinggemma-2-ONNX and https://huggingface.co/onnx-community/embeddinggemma-2-ONNX/tree/daa72c51243991dfcaf9f9137d2c573d8f7790c0
5. **Runtime and lexical primitives:** ONNX Runtime documentation, SQLite FTS5 documentation and NumPy dot documentation for implementation details; Daodan's own worker remains authoritative for the actual configuration. https://onnxruntime.ai/docs/ , https://www.sqlite.org/fts5.html , https://numpy.org/doc/stable/reference/generated/numpy.dot.html

These primary model/guide links are already collected in the EmbeddingGemma reference's “Papers and guides” table, so the official page can link that table and spotlight only the base card and pinned ONNX revision. ([existing guide inventory](../../docs/references/embeddinggemma-papers.md#papers-and-guides))

#### Measurements to link with explicit provenance

| Evidence class | Measurement worth linking | Required caveat |
|---|---|---|
| **Google vendor, full-precision checkpoint** | MTEB Code v1 NDCG@10: 78.68 for EmbeddingGemma 2 versus 68.76 for v1. MRL MTEB Code: 78.68 at 768d, 77.24 at 512d, 76.18 at 256d, 71.41 at 128d. | Not local, not specific to Daodan, and not a q4 quality benchmark. ([Google model card](https://huggingface.co/google/embeddinggemma-2)) |
| **ONNX Community artifact card** | q4 text model listed at 175 MB; worst-case cosine similarity to fp32 listed as 0.975 overall and 0.988 for text. | Vendor/exporter artifact data, not Daodan's measured end-to-end retrieval quality; the local three-file footprint is about 206 MB. ([ONNX card](https://huggingface.co/onnx-community/embeddinggemma-2-ONNX), [local artifact contract](../../plugins/codebase-map/skills/map-method/references/embeddings.md#runtime-and-artifacts)) |
| **Daodan local retrieval benchmark** | Same questions/gold/delivery comparison across Starlette, click, Jinja2 and a single unseen httpx confirmation; EmbeddingGemma 2 replaced CodeRankEmbed. Rewrite/fusion results and development/holdout caveats are on the same page. | Four Python libraries, 96 questions, character-budget whole-entity/claim delivery, not task success or statistical significance. ([local benchmark](../../docs/plugins/codebase-map-research.md#embedding-benchmark), [limits](../../docs/plugins/codebase-map-research.md#limits)) |
| **Daodan local q4 CPU probe** | Four-thread examples: 324 ms at 128 tokens, 1,628 ms at 512, 11,908 ms at 2,048; about 125 ms for a realistic 57-token entity. A separate process-shape probe found about 440 MB resident per provider process at 512 tokens. | Windows machine with 22 logical cores, best of two runs; not a general laptop or vendor figure. ([CPU/process probes](../../docs/references/embeddinggemma-papers.md#measured-cpu-cost-local-probe-2026-10-26)) |
| **Daodan local scoring probe** | Pure Python unpacking/scoring: 98 ms for 1,000 and 443 ms for 5,000 stored 768d vectors, versus single-digit milliseconds for NumPy dot in that probe. | Optimization evidence only; current source still uses pure Python scoring. ([probe](../../docs/references/embeddinggemma-papers.md#measured-cpu-cost-local-probe-2026-10-26), [worker](../../plugins/codebase-map/skills/map-method/scripts/embedding_worker.py)) |
| **External benchmark background** | CoIR for comparable code retrieval; CodeRAG-Bench for RAG generation; RepoCoder/RepoEval for iterative repository completion; SWE-bench for issue-to-patch evaluation; repository-level neural retrieval for commit-derived search questions. | Their tasks and metrics are not interchangeable with Daodan's character-budget delivery. ([existing reference](../../docs/references/embeddinggemma-papers.md#from-a-question-to-the-files-it-uses), [CodeRAG-Bench](https://arxiv.org/abs/2406.14497), [RepoCoder](https://arxiv.org/abs/2303.12570), [SWE-bench](https://arxiv.org/abs/2310.06770)) |

### Inferences

- A concise official-page evidence block should contain only three links labelled **vendor model quality**, **pinned q4 artifact**, and **Daodan local delivery/runtime**. Detailed tables already have canonical owners and should stay there. ([Google card](https://huggingface.co/google/embeddinggemma-2), [ONNX revision](https://huggingface.co/onnx-community/embeddinggemma-2-ONNX/tree/daa72c51243991dfcaf9f9137d2c573d8f7790c0), [local reference](../../docs/references/embeddinggemma-papers.md#use-in-this-repository))
- Where q4 quality matters, prioritize the local end-to-end benchmark over full-precision MTEB or cosine-to-fp32 alone. Those measures answer different questions. ([local benchmark](../../docs/plugins/codebase-map-research.md#embedding-benchmark), [vendor sources](https://huggingface.co/onnx-community/embeddinggemma-2-ONNX))

### Gaps

- No independent EmbeddingGemma 2 code-retrieval evaluation was identified by the existing 2026-10-26 reference; this task did not perform a new exhaustive literature search for one. ([existing caveat](../../docs/references/embeddinggemma-papers.md#benchmarks))
- Linux runtime support is documented upstream, but the shipped contract says Windows CPU inference was exercised and Linux still needs its own live probe. No new cross-platform probe was run here. ([embeddings contract](../../plugins/codebase-map/skills/map-method/references/embeddings.md#runtime-and-artifacts))
- The local benchmark establishes ranking/delivery behavior, not end-user task success, whole-run agent token consumption, monorepo/other-language generalization or significance. Those remain explicit limitations. ([research limits](../../docs/plugins/codebase-map-research.md#limits))
