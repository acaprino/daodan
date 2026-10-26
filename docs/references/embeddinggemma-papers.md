# EmbeddingGemma: papers, guides and use for code search

> Cross-cutting knowledge base for using Google's EmbeddingGemma 2 as a local
> embedder for source code and for answer-style retrieval over a repository. It
> records vendor documentation and published research. The project's own
> measurements stay in the
> [Codebase Map research page](../plugins/codebase-map-research.md#embedding-benchmark),
> and the shipped provider contract stays in the bundled reference
> `codebase-map/skills/map-method/references/embeddings.md`.
>
> **Snapshot date: 2026-10-26.** The model launched 2026-10-06. Re-verify when a
> successor ships, when the pinned ONNX export changes revision, or when an
> independent code-retrieval evaluation of version 2 appears.

Sections:
[TL;DR](#tldr) ·
[Model facts](#model-facts) ·
[Task prompts](#task-prompts) ·
[Parameters and API](#parameters-and-api) ·
[Benchmarks](#benchmarks) ·
[Indexing source code](#indexing-source-code) ·
[From a question to the files it uses](#from-a-question-to-the-files-it-uses) ·
[Threading and performance](#threading-and-performance) ·
[Storage and vector stores](#storage-and-vector-stores) ·
[Fine-tuning](#fine-tuning) ·
[Pitfalls](#pitfalls) ·
[Papers and guides](#papers-and-guides) ·
[Use in this repository](#use-in-this-repository)

## TL;DR

1. **What it is.** EmbeddingGemma 2 is an Apache-2.0, 740M-parameter multimodal
   embedder from Google DeepMind, built on the Gemma 4 decoder. Text and code
   alone load as a 270M core; vision adds 170M and audio 300M. One 768-dimensional
   space, 8,192-token context, Matryoshka truncation to 512/256/128.
2. **Code is the headline improvement.** MTEB Code 78.68 against 68.76 for
   EmbeddingGemma 1 (+9.92 points, about +14% relative). Google positions it for
   local codebase indexing, semantic code search and coding-agent retrieval.
3. **The prompts carry the quality.** Code search is an asymmetric task: queries
   take `task: code retrieval | query: …`, documents take
   `title: {filename} | text: {code}`. `prompt_name="CodeRetrieval"` applies the
   query side. The built-in `Document` prompt applies `title: none | text: `, so a
   document with a real title must be formatted by hand.
4. **Two hard parameter rules.** Never run `float16` (the activations overflow and
   you get NaNs or silently degraded vectors). Re-normalize after any Matryoshka
   truncation, and use the same dimension for queries and documents.
5. **Dimensions for code.** MTEB Code falls 78.68 (768d) to 77.24 (512d), 76.18
   (256d) and 71.41 (128d). 512 is the balanced choice; 128 is for text-only
   shortlisting.
6. **It is not a retriever on its own.** It ranks similarity. Turning that into
   "which files does this question touch" needs chunking, hybrid lexical plus
   dense fusion, chunk-to-file aggregation and, optionally, a reranker.

## Model facts

| Item | Value |
|---|---|
| Weights | `google/embeddinggemma-2` on Hugging Face and Kaggle, Apache 2.0 |
| Released | 2026-10-06, Google DeepMind |
| Parameters | 740M total. Text/code 270M (130M transformer, 140M embedder), vision 170M, audio 300M |
| Backbone | Gemma 4 decoder: 24 layers, model dimension 512, hidden 2048, GQA/MQA, mean pooling, 512 to 768 projection. The model card's table says a 1024-token sliding window; the published `config.json` declares `sliding_window: 512` with five sliding layers to one full layer |
| Context | 8,192 tokens shared across modalities (EmbeddingGemma 1: 2,048) |
| Output | 768 dimensions natively; Matryoshka truncation to 512/256/128 (any value 128 to 768 works, these four are recommended) |
| Precision | `bfloat16` or `float32`. `float16` is incompatible |
| Quantization | Quantization-aware training; INT4 and INT8 builds for edge (LiteRT) |
| Memory | About 191 MB active RAM text-only and 567 MB full multimodal, quantized, on a Pixel 11 Pro |
| Languages | 100+; pre-training cutoff January 2025 |
| Modalities | Text, code, images, video frames, audio, and interleaved combinations |

Encoder loading is modular at load time, from one checkpoint and one shared space:

| Active modalities | `config_kwargs` | Effective size |
|---|---|---|
| Text and code | `{"vision_config": None, "audio_config": None}` | 270M |
| Text and image | `{"audio_config": None}` | 440M |
| Text and audio | `{"vision_config": None}` | 570M |
| Full multimodal | `{}` | 740M |

A vector produced by the text-only setup can be compared directly with one
produced by the full model, so an index can start text-only and add modalities
later without re-embedding what already exists.

## Task prompts

Text inputs are steered by a short task instruction. Media inputs (image, video,
audio) take no prefix. Omitting the prefix still works and lowers precision.

| Use case | Type | Query instruction | Document instruction |
|---|---|---|---|
| Code search | asymmetric | `task: code retrieval \| query: {query}` | `title: {title or filename} \| text: {code}` |
| Web or document search | asymmetric | `task: search result \| query: {query}` | `title: {title} \| text: {content}` |
| Question answering | asymmetric | `task: question answering \| query: {question}` | `title: {title} \| text: {passage}` |
| Fact checking | asymmetric | `task: fact checking \| query: {claim}` | `title: {title} \| text: {evidence}` |
| Classification | symmetric | `task: classification \| query: {content}` | not applicable |
| Clustering | symmetric | `task: clustering \| query: {content}` | not applicable |
| Similarity | symmetric | `task: sentence similarity \| query: {content}` | not applicable |

Three ways to apply a prompt, in the order the vendor recommends:

1. `prompt_name`, selecting a registered prompt: `model.encode(text, prompt_name="CodeRetrieval")`.
2. `prompt`, passing the prefix string yourself. This is how a document title is
   injected per item: `model.encode(code, prompt=f"title: {path} | text: ")`.
3. `default_prompt_name`, if the model was configured with one.

Registered prompt names worth knowing (`model.prompts`): `CodeRetrieval` and
`InstructionRetrieval` both map to `task: code retrieval | query: `; `SearchQuery`,
`Retrieval-query` and `Retrieval` map to `task: search result | query: `;
`Document`, `Retrieval-document` and `document` map to `title: none | text: `;
plus `QuestionAnswering`, `FactChecking`, `STS`, `SentenceSimilarity`,
`Classification`, `Clustering`.

Two consequences for a code index:

- `prompt_name="Document"` emits `title: none`, so a filename has to be inserted
  by hand, either by building the string (`f"title: {path} | text: {chunk}"`) or
  with a per-document `prompt`.
- The vendor guide states that including titles significantly improves retrieval
  accuracy. For code the title is the repository-relative path, optionally with
  the symbol: `src/search/index.py::build_index`.

## Parameters and API

Minimal setup with `sentence-transformers` 6.1.0 or later:

```python
import torch
from sentence_transformers import SentenceTransformer

MODEL_ID = "google/embeddinggemma-2"

dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float32
model = SentenceTransformer(
    MODEL_ID,
    config_kwargs={"vision_config": None, "audio_config": None},  # text and code only, 270M
    model_kwargs={"torch_dtype": dtype},                          # never float16
    truncate_dim=512,                                             # 512 or 768 for code
)
```

Indexing a repository and answering a natural-language question:

```python
from collections import defaultdict

# Documents: path in the title, code in the text. Batched manual formatting.
chunks = [
    {"path": "src/search/index.py", "code": "<chunk source>"},
    {"path": "src/api/routes.py", "code": "<chunk source>"},
]
docs = [f"title: {c['path']} | text: {c['code']}" for c in chunks]
doc_vectors = model.encode(docs, batch_size=64, normalize_embeddings=True)

# Query: the code-retrieval task instruction.
query = "where is the vector search index built?"
query_vector = model.encode(query, prompt_name="CodeRetrieval", normalize_embeddings=True)

scores = model.similarity(query_vector, doc_vectors)[0]

# Chunk-to-file aggregation: max score per file.
best = defaultdict(float)
for chunk, score in zip(chunks, scores.tolist()):
    best[chunk["path"]] = max(best[chunk["path"]], score)
print(sorted(best.items(), key=lambda item: -item[1])[:5])
```

The arguments that matter:

| Argument | Where | Notes |
|---|---|---|
| `prompt_name` / `prompt` | `encode()` | Task instruction, see the table above |
| `truncate_dim` | constructor or `encode()` | 512, 256 or 128; set once at load to keep every call consistent |
| `normalize_embeddings=True` | `encode()` | Required after truncation; a sliced unit vector is no longer unit length |
| `batch_size` | `encode()` | No vendor figure. Practical range: 32 to 64 on CPU, 128 to 256 on GPU |
| `similarity_fn_name="dot"` | constructor | With normalized vectors, dot product equals cosine and is cheaper |
| `config_kwargs` | constructor | Disable unused encoders (see the table above) |
| `model_kwargs={"torch_dtype": ...}` | constructor | `bfloat16` on supported GPUs, `float32` elsewhere |

Runtime matrix with day-one support: `sentence-transformers` (6.1.0+,
`pip install -U "sentence-transformers[image,audio,video]" transformers`),
`transformers` (`AutoModel`, `AutoProcessor`), vLLM, SGLang, llama.cpp GGUF,
Ollama (`ollama.com/library/embeddinggemma-2`), LM Studio, MLX, LiteRT
(`.litertlm` bundles for mobile and web WASM), MediaPipe Universal Embedder and
Semantic Retriever, and transformers.js or WebGPU for the browser.

## Benchmarks

Published on the model card, full-precision checkpoint:

| Metric | EmbeddingGemma 1 | EmbeddingGemma 2 |
|---|---|---|
| MTEB Code (v1), NDCG@10 | 68.76 | **78.68** |
| MTEB Multilingual (v2) | 61.15 | 61.36 |
| MTEB English (v2) | 69.67 (v1 card) | 68.46 |
| Context window | 2,048 | 8,192 |

Matryoshka truncation, MTEB Code and the multimodal overall:

| Output dimension | Storage ratio | MTEB Code | MMEB v2 overall |
|---|---|---|---|
| 768d | 1:1 | 78.68 | 59.01 |
| 512d | 1:1.5 | 77.24 | 58.38 |
| 256d | 1:3 | 76.18 | 56.24 |
| 128d | 1:6 | 71.41 | 45.65 |

Vendor guidance: quality is close to lossless down to 256 dimensions, 128
dimensions is for text-only workloads, and multimodal quality degrades sharply
below 256. For code, one independent analysis recommends staying at 512 or 768
because code loses quality faster than other modalities when truncated.

Caveats on these numbers:

- They are vendor self-reported. The model card carries no head-to-head table
  against named competitors, and no independent code-retrieval evaluation of
  version 2 had been published at the snapshot date.
- Text parity, not text gain. On MTEB English, version 2 is slightly below
  version 1; the gains are code, a four times longer context and the licence.
- On-device vision latencies (one image at a 70-token budget): 37.3 ms on a
  MacBook M5 Pro GPU (26.9 images/s), 48.9 ms on a Pixel 11 Pro XL NPU, 49.8 ms
  on a Dell XPS 16 NPU, 69.8 ms on an iPhone 18 Pro GPU (191 ms on its CPU),
  1,761 ms on a Raspberry Pi 5 CPU. Text embedding is faster than these figures.

## Indexing source code

1. **Respect the input limit.** The exported graph's sequence axis is dynamic,
   but the worker truncates at its own 2,048-token `MAX_TOKENS` (see
   [Use in this repository](#use-in-this-repository)), and the loss is silent.
   Chunk to that figure until the constant is deliberately raised and measured.
2. **Split on symbols, not on characters.** One chunk per top-level definition
   (function, class, method) from a real parser gives the encoder a coherent unit;
   keep the signature and docstring with the body. Fixed windows with about 10 to
   20% overlap are the fallback for files with no parseable structure.
3. **Put identity in the title.** `title: {repo-relative path}` at minimum;
   `title: {path}::{symbol}` when one file produces many chunks. The vendor
   reports that including titles significantly improves retrieval, and the format
   exists for exactly this.
4. **Exclude what is not source.** Vendored code, lockfiles, generated and
   minified output pollute the index. This is an indexing decision, not a model
   limitation: the model covers 100+ languages and mixed-language repositories.
5. **Deduplicate.** Identical chunks (copied files, generated duplicates) collapse
   into one vector and one rank entry.

## From a question to the files it uses

The pipeline that turns a natural-language question into a ranked file list:

1. **Dense retrieval.** Embed the question with the code-retrieval query prefix
   and take the top 30 to 50 chunks by similarity.
2. **Chunk-to-file aggregation.** Max score per file is the simple default; a
   weighted sum rewards files with several relevant chunks.
3. **Hybrid lexical retrieval.** BM25 or FTS over identifiers catches exact names
   (CamelCase, snake_case, quoted strings) that dense vectors blur. Fuse the two
   rankings with reciprocal rank fusion.
4. **Rerank.** A cross-encoder over the top 50 chunks before returning files.
   Shortlisting at 128 dimensions and reranking afterwards is the pattern the
   vendor itself suggests.
5. **Measure file recall.** Build a question-to-expected-file set over your own
   repository and track file Recall@k and MRR@k. Published benchmarks do not
   transfer without this local check.

Evidence from the literature behind these choices:

- **CoIR** (ACL 2025) is the reference code-retrieval benchmark: 10 datasets,
  2 million documents, four task families (text-to-code, code-to-code,
  code-to-text, hybrid). It finds that size is not quality (a 110M encoder beat a
  567M one) and that dense models beat BM25 two to three times on natural
  language to code.
- **CodeRAG-Bench** (Findings of NAACL 2025) reports that for code, dense neural
  embedding models more often beat BM25 than in general text retrieval, and that
  code-specific embedders outperform general-purpose ones.
- **RepoCoder** (EMNLP 2023) and **SWE-bench** (ICLR 2024) are the repository-level
  substrate: iterative retrieve-then-generate, and issue-to-patch localization.
- The rewriting, fusion and graph-navigation literature (HyDE, ReCo, RepoGraph,
  dual-encoder repository search and one engineering report on query expansion)
  is already tabulated with the project's reading of it in the
  [research page's Sources section](../plugins/codebase-map-research.md#sources);
  it is not repeated here.

## Threading and performance

The general rules:

1. **The GIL blocks thread-based parallelism.** Embedding is CPU-bound, so
   parallel speedup on one machine comes from processes, not threads.
2. **`sentence-transformers` ships a multi-process pool**:
   `pool = model.start_multi_process_pool()` then
   `model.encode_multi_process(texts, pool, batch_size=…)`, stopped with
   `stop_multi_process_pool(pool)`. One process per core, or per GPU.
3. **Torch on CPU**: set `torch.set_num_threads(n)` or `OMP_NUM_THREADS` to the
   physical core count, and avoid oversubscribing when a process pool is also
   running.
4. **ONNX Runtime**: `SessionOptions.intra_op_num_threads` (parallelism inside an
   operator) and `inter_op_num_threads` (across operators). The usual shape is
   intra at the physical core count and inter at 1 for a single request stream.
5. **Server-side batching**: Text Embeddings Inference, vLLM and SGLang handle
   dynamic batching and request concurrency behind an HTTP API. Use threads or
   async on the client only for I/O, never to parallelize the math.

Observed throughput, for order of magnitude only: about 78 embeddings per second
on small texts, 4 images per second and 0.2 video embeddings per second per minute
of footage on an M3 Pro, from a single community measurement. The vendor's own
figures are the on-device vision latencies listed under
[Benchmarks](#benchmarks). None of these is a measurement of this project's
corpus; the local cost is on the research page.

## Storage and vector stores

- **Vector size.** In `bfloat16`, one million 768-dimensional vectors take about
  1.5 GB; at 128 dimensions the same million take about 250 MB. Truncation is the
  storage lever, and the quality cost is in the table under
  [Benchmarks](#benchmarks).
- **Stores.** FAISS or HNSW for an in-process index; Qdrant, LanceDB, pgvector or
  sqlite-vec for a database that owns persistence, filtering and metadata. The
  vendor's own on-device demo uses a local SQLite database, and Qdrant published a
  launch-day integration guide.
- **Metadata.** Keep path, language, symbol name and line range beside each
  vector. Retrieval is only useful if a hit can be opened.
- **On-device.** MediaPipe Semantic Retriever performs approximate nearest
  neighbour search on-device in single-digit milliseconds; the text-only model
  fits in about 191 MB of RAM quantized.

## Fine-tuning

The official guide uses `sentence-transformers` with contrastive triplets
`(anchor, positive, negative)` and `MultipleNegativesRankingLoss`, trained by
`SentenceTransformerTrainer`. Two details are load-bearing:

- Pass `prompts=model.prompts[task_name]` in the training arguments, so training
  uses the same task prefix as inference.
- Use hundreds to thousands of domain triplets; the guide's three-triplet example
  is a demonstration, and its effect is a wider margin between the target and its
  hard negatives, not a headline accuracy gain.

For a code index the triplets are natural: the anchor is a developer question,
the positive is the chunk that answers it, the negative is a semantically close
chunk from the same repository. Unsloth publishes a cheaper fine-tuning path.
Fine-tuning is worth it for private vocabulary and internal module names; the base
model is already strong on public code retrieval, so measure before adopting it.

## Pitfalls

1. `float16` produces NaN or silently degraded embeddings. Use `bfloat16` or
   `float32`.
2. Truncating without re-normalizing degrades ranking in silence: the scores look
   plausible rather than failing.
3. Queries and documents must share a dimension. A 768-dimension query cannot be
   scored against a 128-dimension corpus.
4. `prompt_name="Document"` writes `title: none`. Forgetting the manual title
   format discards a documented accuracy gain.
5. Prefixes apply to text only. Do not prefix images, video or audio.
6. Cosine scores are compressed: even unrelated sentences can score around 0.69,
   and scores are not calibrated across modalities. Read the ranking, not the
   absolute value.
7. The vendor benchmarks are self-reported; the "best in class for its size"
   claim has no head-to-head table on the card.
8. A community report had the vendor's own zero-shot classification example
   misclassify a refund request. Test on your own labels before relying on it.
9. The model ranks similarity; it does not answer, cite or verify. Everything
   above the ranking, aggregation and reranking is application code.

## Papers and guides

| Work | What it provides |
|---|---|
| [EmbeddingGemma 2 model card](https://huggingface.co/google/embeddinggemma-2) (Google) | Architecture, parameters, prompt table, benchmark tables, precision and MRL rules |
| [Launch post](https://blog.google/innovation-and-ai/technology/developers-tools/embeddinggemma-2) (Google, 2026-10-06) | Positioning, code improvement, on-device memory figures |
| [Gemma documentation](https://ai.google.dev/gemma/docs/embeddinggemma) and [v2 model card page](https://ai.google.dev/gemma/docs/embeddinggemma/model_card_2) (Google) | Official overview, links to every guide |
| [Inference guide](https://ai.google.dev/gemma/docs/embeddinggemma/inference-embeddinggemma-with-sentence-transformers) (Google) | Task prompts, `prompt_name` versus `prompt`, MRL usage, zero-shot classification |
| [Multimodal guide](https://ai.google.dev/gemma/docs/embeddinggemma/multimodal-embeddinggemma-with-sentence-transformers) (Google) | Image, video and audio inputs, token budgets, cross-modal calibration note |
| [Fine-tuning guide](https://ai.google.dev/gemma/docs/embeddinggemma/fine-tuning-embeddinggemma-with-sentence-transformers) (Google) | Contrastive triplets, `SentenceTransformerTrainer`, prompt alignment during training |
| [Developer guide](https://developers.googleblog.com/embeddinggemma-2-the-developer-guide/) (Google, 2026-10-06) | Worked example: a whole open-source codebase indexed with the 270M text setup, then agent-driven search |
| [Google AI Edge post](https://developers.googleblog.com/google-ai-edge-with-embeddinggemma-2) (Google, 2026-10-06) | On-device numbers, LiteRT, MediaPipe Embedder and Semantic Retriever, ML Kit roadmap |
| [RAG with EmbeddingGemma notebook](https://github.com/google-gemma/cookbook/blob/main/tutorials/RAG_with_EmbeddingGemma.ipynb) (Gemma cookbook) | End-to-end retrieval example |
| [Unsloth fine-tuning docs](https://unsloth.ai/docs/models/embeddinggemma-2) | Efficient fine-tuning recipe |
| [Qdrant integration guide](https://qdrant.tech/blog/embeddinggemma-2/) | Vector-store side of the launch |
| [Independent analysis](https://www.eesel.ai/blog/embeddinggemma-2) (eesel, 2026-10-09) | Specs, storage figures, the English-MTEB dip, community throughput data |
| [CoIR: A Comprehensive Benchmark for Code Information Retrieval Models](https://arxiv.org/abs/2407.02883) (ACL 2025) | Code-retrieval benchmark and leaderboard; dense versus BM25 on code |
| [CodeRAG-Bench: Can Retrieval Augment Code Generation?](https://arxiv.org/abs/2406.14497) (Findings of NAACL 2025) | Dense retrieval for code, code-specific embedders versus general ones |
| [CodeRAG: Finding Relevant and Necessary Knowledge for Retrieval-Augmented Repository-Level Code Completion](https://arxiv.org/abs/2509.16112) (2025) | Sparse, dense and dataflow retrieval paths with reranking at repository level |
| [RepoCoder](https://arxiv.org/abs/2303.12570) (EMNLP 2023) | Iterative retrieval and generation for repository-level completion |
| [SWE-bench](https://arxiv.org/abs/2310.06770) (ICLR 2024) | Issue-to-patch benchmark; the substrate for file localization |
| [Matryoshka Representation Learning](https://arxiv.org/abs/2205.13147) (NeurIPS 2022) | The truncation method this model is trained with |
| [CodeBERT](https://arxiv.org/abs/2002.08155), [GraphCodeBERT](https://arxiv.org/abs/2009.08366), [UniXcoder](https://arxiv.org/abs/2203.03850), [CodeT5+](https://arxiv.org/abs/2305.07922), [CodeSearchNet](https://arxiv.org/abs/1909.09436) | Historical code encoders and the retrieval dataset they were measured on; background, not competitive baselines for an embedder today |

There is no technical report for version 2 at the snapshot date. The authoritative
sources are the model card, the Gemma documentation and the guides above; an
independent code-retrieval evaluation is still awaited.

## Use in this repository

The Codebase Map's optional embedding provider ships the text path of this model
as a pinned local artifact. Its contract is the bundled reference
`codebase-map/skills/map-method/references/embeddings.md`, its implementation is
`embedding_worker.py`, and its measured behaviour is on the
[research page](../plugins/codebase-map-research.md#embedding-benchmark).

| Aspect | Shipped configuration |
|---|---|
| Artifact | q4 text graph of `onnx-community/embeddinggemma-2-ONNX`, revision `daa72c51243991dfcaf9f9137d2c573d8f7790c0`, about 206 MB on disk, verified by SHA-256 before loading |
| Prefixes | Documents `title: none \| text: `, queries `task: code retrieval \| query: `, both part of the provider fingerprint |
| Effective input limit | 2,048 tokens, set by the worker's `MAX_TOKENS` constant, not by the export: the graph's sequence axis is dynamic |
| Vector | Pooled `sentence_embedding`, 768 dimensions |
| Inference | ONNX Runtime, CPU provider, `intra_op_num_threads` 4, `inter_op_num_threads` 1, one input per inference, no padding |
| Fusion with the lexical index | Versioned policy `exact-rrf75-25-k60-v1`: dense weight 0.75, lexical weight 0.25, reciprocal-rank offset 60 |
| Cost model | Indexing time, not tokens; the provider is opt-in and makes no LLM call |

Resolved 2026-10-26 by loading the pinned graph with the runtime the worker pins:
`input_ids` and `attention_mask` carry shapes `['batch_size', 'sequence_length']`,
so the export bakes in no fixed length, and a 4,096-token input ran to completion.
The 2,048 cut is the worker's own constant. The bundled reference's phrase "this is
an encoder limit" therefore describes a local choice rather than a property of the
artifact, and the same wording is worth correcting on the next kernel change.

### Measured CPU cost (local probe, 2026-10-26)

One text per inference, Windows, 22 logical cores, the pinned q4 graph, best of two
runs. The absolute values belong to that machine and are not a laptop figure; the
ratios are the transferable part.

| intra-op threads | 128 tokens | 512 tokens | 2,048 tokens |
|---|---|---|---|
| 1 | 604 ms | 2,448 ms | 18,313 ms |
| 2 | 587 ms | 3,430 ms | 11,308 ms |
| 4 | 324 ms | 1,628 ms | 11,908 ms |
| 8 | 277 ms | 1,244 ms | 5,411 ms |

- A realistic short entity (57 tokens: prefix, path, name, signature, small body)
  encodes in about 125 ms at 4 threads, about 8 entities per second. Model load is
  0.5 to 1.2 seconds per provider process.
- Input tokens dominate: four times the tokens (512 to 2,048) costs roughly four to
  seven times the time. Bounding what is embedded per entity is the largest single
  lever on a CPU-only machine.
- Threads help long inputs (8 threads was 1.2 to 3.4 times faster than 4 at 2,048
  tokens) and barely help short ones.
- With three sessions alive at once, the 8-thread configuration failed to allocate a
  100 MB buffer: threads cost memory as well as time, so one session and a bounded
  thread count is the safe laptop shape.
- The query path is pure Python: unpacking and scoring 1,000 stored
  768-dimension vectors took 98 ms and 5,000 took 443 ms, against single-digit
  milliseconds for a numpy dot product. numpy is pinned only for the isolated
  encoder backend; the parent process running `search()` is stdlib-only by
  contract. Using numpy there needs an optional parent dependency with a stdlib
  fallback, or a protocol change that moves scoring into an owned runtime. The
  speedup is real, but it is not a dependency-free drop-in change.

Levers, cheapest first: make the query scan native where the selected runtime
allows it; bound the tokens embedded per entity; set intra-op threads to the
machine's physical cores within a memory cap; truncate to 256 or 512 dimensions
for storage and scan cost, which needs re-normalization after the slice. Every
change that touches the provider profile (tokens, threads, dimensions) rebuilds
the index, so group them into one rebuild.

### Process shape and long-run reliability (local probe, 2026-10-26)

Same machine, same pinned graph, a fixed eight-thread budget split between
processes instead of threads, 512-token texts.

| processes x threads | texts encoded | wall | texts/s | resident per process |
|---|---|---|---|---|
| 1 x 8 | 4 | 6.6 s | 0.61 | 441 MB |
| 2 x 4 | 8 | 11.1 s | 0.72 | about 440 MB |
| 4 x 2 | 16 | 17.1 s | 0.93 | about 439 MB |
| 8 x 1 | not reached | allocation failure | not reached | about 3.5 GB in total |

- **More processes beat more threads** at the same thread budget: ONNX Runtime's
  intra-op scaling on this graph is poor, so spare cores are best used by separate
  provider processes. Each vector depends only on its own text (batch 1, no
  padding), so a sharded build can produce the same vectors as a serial build when
  every worker has an identical provider profile and runtime behavior.
- **The bound is memory, not cores**: about 440 MB resident per provider process
  with the model loaded and 512-token buffers. The vendor's ~191 MB describes
  LiteRT and MediaPipe on a phone, not ONNX Runtime on Windows.
- **Single writer by construction**: one lock file plus an atomic replace, and the
  previous generation stays served until the swap, so a failed build cannot corrupt
  an index.
- **Sharding is compatible, not built in**: the parent must remain the only writer,
  all providers must report the same profile, and metadata must cover the complete
  inventory. The current `refresh_index()` accepts one provider and needs new
  orchestration before this becomes an execution path.
- **What a long run does not survive today**: a killed run loses every vector it had
  not yet published, because only a complete generation is ever written; one batch
  of up to 16 distinct pending texts is answered under a single 300-second timeout,
  which slow hardware can exceed on long inputs; an abrupt termination can leave
  the lock file behind and block the next refresh. Checked source or manifest
  changes reject publication, but the final manifest check and index swap are
  separate operations rather than one atomic freshness guarantee.

The independent code review, test run and probe evidence are consolidated in
[the dated validation report](../superpowers/reports/2026-10-26-embeddinggemma-indexing-validation.md).

## Sources

Vendor pages and the independent analysis were read on 2026-10-26. Repository-internal
figures are cited from the pages and files linked above and are not restated here.
Community measurements (the M3 Pro throughput, the zero-shot misclassification)
are single unreplicated reports and are labelled as such in the text.
