<a id="embeddinggemma-research"></a>

# EmbeddingGemma: papers, guides and use for code search

[Used by Codebase Map](../plugins/codebase-map.md) · [Context-building benchmarks](context-building-benchmarks.md)

## TL;DR

- **What it is:** EmbeddingGemma 2 is an open-weights multimodal embedding model (Apache-2.0, 740M total parameters, 270M for the text/code core) released by Google DeepMind in October 2026, based on the Gemma 4 decoder.
- **Choice in Daodan:** Selected as the local offline embedder for Codebase Map because it decisively outperforms CodeRankEmbed (+3 to +27 recall points across all local benchmarks without LLM calls).
- **Usage rules:** Requires asymmetric prompts (`task: code retrieval | query: ...` and `title: {filename} | text: {code}`); `float16` prohibited (activation overflow); native 768d dimension with Matryoshka down to 512d/256d/128d.
- **Local validation limits:** CPU indexing is slow (~12 min for 669 entities, estimated over 2.8h for 10,000 entities on 4 threads). Unattended long runs require timeout handling on slow batches and checkpoints for resumability.

## Why we conducted the research

1. **Replacing the legacy embedder:** The previous model, CodeRankEmbed (INT8 ONNX with 512 tokens), consistently failed in semantic Python code retrieval and could not handle wider context.
2. **Requirement for 100% offline, local embeddings:** Daodan users and agents require indexing and mapping proprietary codebases without transmitting source code to third-party services or external APIs. An execution model running on standard CPU with ONNX Runtime was essential.
3. **Evaluating CPU feasibility and scalability:** Before integrating the model into standard workflows, it was necessary to measure:
   - indexing throughput and multithreading vs multiprocessing impact;
   - RAM consumption (OOM risk with excessive parallel workers);
   - vector scan query latency;
   - reliability during abrupt process termination.

## Links to cited papers

| # | Paper / Resource | Link | Primary topic |
|---|---|---|---|
| 1 | Google DeepMind. *EmbeddingGemma 2 Model Card & Weights*. 2026. | [HuggingFace: google/embeddinggemma-2](https://huggingface.co/google/embeddinggemma-2) | Gemma 4 decoder architecture, quantization, 768-dimensional space, and MTEB benchmarks. |
| 2 | Kusupati et al. *Matryoshka Representation Learning* (MRL). NeurIPS 2022. | [arXiv:2205.13147](https://arxiv.org/abs/2205.13147) | Training technique to truncate vectors (768 → 512 → 256 → 128) while preserving similarity and reducing storage. |
| 3 | Li et al. *CoIR: A Comprehensive Benchmark for Code Information Retrieval Models*. ACL 2025. | [arXiv:2407.02883](https://arxiv.org/abs/2407.02883) | Standard benchmark for code retrieval: demonstrates dense models outperform BM25 by 2x to 3x. |
| 4 | Wang et al. *CodeRAG-Bench: Can Retrieval Augment Code Generation?*. Findings of NAACL 2025. | [arXiv:2406.14497](https://arxiv.org/abs/2406.14497) | Evaluating dense retrieval impact on code generation and patching. |
| 5 | Zhang et al. *RepoCoder: Repository-Level Code Completion Through Iterative Retrieval and Generation*. EMNLP 2023. | [arXiv:2303.12570](https://arxiv.org/abs/2303.12570) | Iterative repository-level code retrieval and completion. |
| 6 | Jimenez et al. *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?*. ICLR 2024. | [arXiv:2310.06770](https://arxiv.org/abs/2310.06770) | Issue resolution benchmark; standard foundation for code localization tasks. |
| 7 | ONNX Community. *EmbeddingGemma-2 ONNX Quantized Weights (q4)*. 2026. | [HuggingFace: onnx-community/embeddinggemma-2-ONNX](https://huggingface.co/onnx-community/embeddinggemma-2-ONNX) | INT4 ONNX version optimized for local CPU execution. |

## Content summary and findings

### 1. Architectural characteristics and parameters

- **Weights and export:** Quantized q4 ONNX version (`onnx-community/embeddinggemma-2-ONNX`, rev `daa72c51`). 174 MB weights, 0.5 MB graph, 32 MB tokenizer.
- **Input context:** The ONNX export features a dynamic sequence axis (a 4,096-token probe succeeded); the Codebase Map worker applies a policy cap of 2,048 tokens per document.
- **Query/document asymmetry:** Omitting task prefixes degrades similarity. Queries use `task: code retrieval | query: `, documents use `title: {file} | text: `.

### 2. Local CPU validation results (Report 2026-10-26)

Local engineering validation (26 unit tests passed in 54.1s) highlighted:

1. **Latency dominated by input tokens:**  
   On a 4-thread CPU:
   - 128 tokens: 324 ms
   - 512 tokens: 1.628 s
   - 2,048 tokens: 11.908 s
2. **Parallelism and RAM limits:**  
   At a fixed budget of 8 threads, 4 processes with 2 threads offer ~1.5x throughput compared to 1 process with 8 threads (0.93 texts/s vs 0.61 texts/s). However, each process consumes ~440 MB resident memory: 8 parallel processes caused an out-of-memory crash on Windows. The recommendation is not to exceed 2 parallel processes on standard desktop machines.
3. **Query vector scanning:**  
   Pure Python calculation over 5,000 768d vectors requires ~443 ms. A prototype using NumPy dot products reduces latency to 0.8 ms, but is not yet integrated into production code.
4. **Mandatory resumability:**  
   Because indexing a 10,000-symbol codebase requires ~2.8 hours on a high-spec CPU and over 8 hours on a standard laptop, losing progress on process interruption is unacceptable. The index must record partial checkpoints and safely recover orphan `index.lock` files.

### 3. Product integration status

- **Available as opt-in:** The EmbeddingGemma 2 semantic index is an optional local provider alongside SQLite FTS5.
- **Confirmed decision:** CodeRankEmbed has been removed; current priority is indexer robustness (resumability, timeouts, lock recovery) before scaling to large monorepos.
