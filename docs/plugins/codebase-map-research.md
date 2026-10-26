<a id="codebase-map-research"></a>

# Codebase Map: research and benchmarks behind code search

[Back to the Codebase Map plugin](codebase-map.md)

Codebase Map finds the code a request needs in four steps: it searches the
question as written, a small model rewrites the question using only names that
search found, EmbeddingGemma 2 (q4) and the FTS5 index rank whole entities for the
rewrites, and the ranked entities fill a character budget. This page keeps the
evidence behind those steps in one place: the published work they were checked
against, the comparison that chose the embedder, and what the Daodan harness
measured in response.

[Sources](#sources) ·
[What the sources agree on](#what-the-sources-agree-on) ·
[Embedder benchmark](#embedding-benchmark) ·
[Rewrite and fusion experiments](#rewrite-and-fusion-experiments) ·
[Limits](#limits)

## Sources

Eight papers and one engineering report, read in full on 2026-10-26. Their
numbers come from other corpora, tasks and models. None of them tests a grounded
rewrite over a hybrid of lexical and dense ranking at repository scale, so each
claim taken from them is a hypothesis until the harness measures it here.

| # | Work | What it measured | What Codebase Map takes from it |
|---|---|---|---|
| 1 | Gao, Ma, Lin, Callan. [Precise Zero-Shot Dense Retrieval without Relevance Labels](https://arxiv.org/abs/2212.10496) (HyDE). ACL 2023. | A model writes a hypothetical answer document; the document encoder embeds it and the vectors of several such documents and the query are averaged. Web search and low-resource retrieval. | Keep the question inside the dense vector instead of ranking it separately, and embed generated text as a document. With an encoder already trained on relevance pairs, its effect shrank to -1.9 to +5.3 nDCG@10. |
| 2 | Li, Zhou, Shen. [Rewriting the Code: A Simple Method for Large Language Model Augmented Code Search](https://arxiv.org/abs/2401.04514) (ReCo). ACL 2024. | Rewriting queries into code and code into a common style, natural language to code, over pools of 500 to 1 000 snippets. | Generated code helps when it resembles the repository's code. Original plus generated beat generated alone in 8 of 8 settings. Code Llama rewrites pushed BM25 below its baseline. |
| 3 | Gurioli, Pennino, Gabbrielli. [Do not copy and paste! Rewriting strategies for code retrieval](https://arxiv.org/abs/2605.08299). 2026. | Query and corpus rewriting at several abstraction levels, six CoIR tasks, several encoders. | The rewrite level has to be measured. Natural-language rewrites lowered a strong encoder (Qwen3-Embedding-0.6B, mean of four tasks 0.56 to 0.52). Rewriting the corpus alone fell below the baseline in 56 of 90 configurations; rewriting query and corpus beat the corpus alone in 78 of 90. On one task a 3B rewriter matched a 14B one. |
| 4 | Song, Zheng. [A Survey of Query Optimization in Large Language Models](https://arxiv.org/abs/2412.17558). 2024, revised 2026. | Taxonomy of expansion, decomposition, disambiguation and abstraction. It reports no comparable numbers and covers no code retrieval. | Decide before rewriting: the surveyed work calls expansion of explicit, single-target queries counterproductive. Spread several rewrites over different readings of the question, not paraphrases. |
| 5 | Ouyang, Yu et al. [RepoGraph: Enhancing AI Software Engineering with Repository-level Code Graph](https://arxiv.org/abs/2410.14684). ICLR 2025. | A tree-sitter graph of a repository; agents receive the neighbourhood of one named symbol. SWE-bench Lite. | One hop and names only: a flat two-hop context of about 10 500 tokens fell below the baseline, one hop of about 2 300 tokens rose above it. Gains were 2 to 2.7 points on 300 issues, one run, and the edge filter was not ablated. |
| 6 | Liu, Song, Li, Yang, Qi. [Beyond Function-Level Search: Repository-Aware Dual-Encoder Code Retrieval with Adversarial Verification](https://aclanthology.org/2025.findings-emnlp.1147/). Findings of EMNLP 2025. | A trained dual encoder with dependency features and model verification, on change requests mapped to functions. | Function-level units beat file and module units. Training is required and two of its three result tiers are scaled rather than measured, so it is a source of hypotheses, not evidence. |
| 7 | Li, Dong, Lee et al. [CoIR: A Comprehensive Benchmark for Code Information Retrieval Models](https://arxiv.org/abs/2407.02883). ACL 2025. | Ten code retrieval datasets, NDCG@10, BM25 and dense models. | Size is not quality: a 110M encoder beat a 567M one. Dense models beat BM25 two to three times on natural language to code. CosQA is the subset closest to a request against Python functions. |
| 8 | Gandhi, Gao, Callan. [Repository-level Code Search with Neural Retrieval Methods](https://arxiv.org/abs/2502.07067). 2025. | BM25 over commit messages, then fine-tuned CodeBERT rerankers, on 7 repositories. | Evaluation questions can be built from history (a commit becomes a masked issue, its changed files the gold). On one repository, reranking only the first 20 results recovered 57% of the gain of reranking 100. Its rerankers need a GPU. |
| 9 | Rudenko (MadAppGang). [LLM Query Expansion Made Our Code Search Worse. Here's What Didn't](https://madappgang.com/blog/llm-query-expansion-made-our-code-search-worse.-he/). Engineering report. | 860 queries against a hybrid local code search for coding agents, 12 repositories; the model conditions ran on 2 of them. | Three small expanders lowered MRR@10 by 26 to 32%, a fine-tuned one included. The only component that helped (+21.8% MRR@10) was a regular-expression classifier that sends symbol lookups (CamelCase, snake_case, quoted identifiers) to keyword search and the rest to hybrid search. |

## What the sources agree on

1. **Keep the question in the representation.** HyDE and ReCo add generated text
   to the original inside one vector and one lexical query. The harness had found
   that merging the question's ranking with the rewritten rankings loses; no
   source merges rankings.
2. **Rewrite in the code's vocabulary, from real names.** Generated text that does
   not look like the repository's code helps little, and small code models made
   lexical search worse. The two-pass rewrite gives the model only names the
   first search found, and a filter removes absent ones.
3. **Do not rewrite every question.** A question that already names symbols of
   the project is a lookup; expanding it costs a call and can lose.
4. **Use the graph to choose, not to fill.** One hop of names helps a model; two
   hops of context hurt. The harness had found that graph neighbours appended to
   the delivery lose at 6 000 and 12 000 characters.
5. **Rewrite the corpus beside the code, never instead of it.** A one-line
   statement of each entity's purpose, indexed with the code, carries most of
   ReCo's gain. It costs one small-model call per entity, once.
6. **Small models are enough.** Neither a larger encoder nor a larger rewriter is
   indicated for quality alone.

<a id="embedding-benchmark"></a>

## Which local embedder finds the code a request needs?

Codebase Map can rank symbols with a local embedding model beside its full-text
index. Between 2026-10-23 and 2026-10-26 two models were compared on the same
projects, queries, gold and delivery rule. EmbeddingGemma 2 (q4) won in every
project and replaced CodeRankEmbed, which was removed with its harnesses.

### Setup

- **Projects:** Starlette 1.9.0 (development set), click 8.1.8 and Jinja2 3.1.6
  (holdouts, each used once), and httpx 0.28.1, frozen afterwards to confirm the
  shipped configuration in a single run. 24 questions per project, half in English
  and half in Italian, with gold entities written blind and verified against source.
- **Delivery:** whole entity bodies in rank order until the budget (6 000, 12 000
  or 24 000 characters) is full. The figure is the mean share of gold entities
  delivered whole. Claims are the gold scenario statements whose supporting lines
  the delivery contains, at 24 000 characters.
- **Ranking:** the shipped hybrid policy, dense 0.75 and lexical 0.25, reciprocal
  rank with k 60, over the same embedding documents (path, name, signature, body).
- **Rewriting:** one call per question to the model-routing tier1 model
  (`claude-haiku-5-5`) that turns the question into one to three code-search
  queries; the rewritten rankings are merged. About 0.0002 to 0.0007 USD per question.
- **Two-pass rewriting:** the question is first searched as written; the model
  then sees up to 40 symbols found (name, file, signature, first docstring line,
  graph neighbours of the first five) and may use a code name only from the
  question or that list. A mechanical filter removes any name absent from the source.

| | CodeRankEmbed | EmbeddingGemma 2 |
|---|---|---|
| Artifact | community INT8 ONNX, revision `e74f446d` | `onnx-community/embeddinggemma-2-ONNX` q4, revision `daa72c51` |
| Licence | MIT | Apache-2.0 |
| Files | 138.6 MB graph | 174 MB weights, 0.5 MB graph, 32 MB tokenizer |
| Input limit | 512 tokens | 2048 tokens |
| Prompts | query prefix only | document and query prefixes |
| Index build, Starlette (669 entities, 4 CPU threads) | 126.5 s | about 12 min |

### Results

Gold delivered whole at 6k / 12k / 24k characters, and claims at 24k.

| Project | Path | CodeRankEmbed | EmbeddingGemma 2 |
|---|---|---|---|
| Starlette | hybrid, no model call | 0.47 / 0.55 / 0.74 | 0.63 / 0.81 / 0.94, 17/19 |
| Starlette | rewritten | 0.76 / 0.88 / 0.98 | 0.88 / 0.97 / 1.00, 17/19 |
| Starlette | two-pass rewritten | | 0.93 / 0.97 / 0.99, 17/19 |
| Starlette | two-pass, EmbeddingGemma 2 only | | 0.85 / 0.97 / 1.00, 18/19 |
| click | hybrid, no model call | 0.35 / 0.46 / 0.58, 16/19 | 0.54 / 0.73 / 0.85, 17/19 |
| click | rewritten | 0.64 / 0.77 / 0.84, 13/19 | 0.67 / 0.82 / 0.89, 19/19 |
| click | two-pass rewritten | | 0.69 / 0.83 / 0.94, 19/19 |
| Jinja2 | hybrid, no model call | 0.46 / 0.61 / 0.73, 14/18 | 0.49 / 0.69 / 0.83, 15/18 |
| Jinja2 | rewritten | 0.70 / 0.75 / 0.91, 16/18 | 0.68 / 0.82 / 0.98, 17/18 |
| Jinja2 | two-pass rewritten | | 0.67 / 0.86 / 0.94, 17/18 |
| httpx | hybrid, no model call | | 0.83 / 0.90 / 0.91, 14/18 |
| httpx | two-pass, EmbeddingGemma 2 only | | 0.90 / 0.95 / 0.96, 17/18 |

Claims for CodeRankEmbed on Starlette were not recorded. The planner and packet
path that the embedder first fed delivered 0.46 on Starlette and 0.29 on click.
The first two-pass rows searched the question with CodeRankEmbed before the
rewrite; the rows marked "EmbeddingGemma 2 only" are the shipped configuration,
and httpx ran it once, unseen.

### What it shows

- Without any model call, EmbeddingGemma 2 beats CodeRankEmbed without a model
  call in every project and budget, by 3 to 27 points; at 24k it matches
  CodeRankEmbed with rewriting on click (0.85 against 0.84).
- Rewriting helps both models; with it EmbeddingGemma 2 reaches 0.89 to 1.00 at
  24k. Merging the original query's ranking with the rewritten ones scored lower
  than the rewritten ones alone in every project.
- The first rewrite prompt invented 9 to 13 code names per project. The two-pass
  prompt with the absent-name filter left 0 to 2, and improved 6k on Starlette
  and click; on Jinja2 it gained at 12k and lost at 24k.
- The cost moved from tokens to indexing time: EmbeddingGemma 2 builds its index
  about six times slower, once per project, then refreshes only changed entities.

## Rewrite and fusion experiments

Each experiment tests one claim from the [sources](#sources), on the cached
EmbeddingGemma 2 vectors and the same delivery rule. Gold delivered whole at
6k / 12k / 24k, then claims at the same budgets.

| Experiment | Project | Before | After |
|---|---|---|---|
| Two-pass rewrite, frozen configuration, single run | httpx, unseen | no model call: 0.83 / 0.90 / 0.91, claims 12, 13, 14 of 18 | 0.90 / 0.95 / 0.96, claims 15, 15, 17 of 18; 1 absent name removed; 0.00057 USD per question |

Then four changes taken from the sources were measured on the same rewrites, with
no extra model call except where stated. Starlette is the development set; the
other three projects had already been used, so their figures are diagnostic.

| Ranking of the rewritten question | Starlette | httpx | click | Jinja2 | Mean |
|---|---|---|---|---|---|
| Shipped: the rewrites' rankings merged by reciprocal rank | 0.85 / 0.97 / 1.00 | 0.90 / 0.95 / 0.96 | 0.69 / 0.83 / 0.94 | 0.67 / 0.86 / 0.94 | 0.78 / 0.90 / 0.96 |
| A: question and rewrites averaged in one vector, their terms in one lexical query (HyDE, ReCo) | 0.91 / 0.97 / 1.00 | 0.91 / 0.94 / 0.96 | 0.68 / 0.85 / 0.94 | 0.65 / 0.86 / 0.95 | 0.79 / 0.91 / 0.96 |
| A and D: an entity among the first 60 linked by references to k ≥ 2 of the first 10 has its rank divided by k (RepoGraph's one hop, used to re-rank) | 0.93 / 0.97 / 0.99 | 0.91 / 0.97 / 0.96 | 0.73 / 0.87 / 0.94 | 0.70 / 0.90 / 0.95 | 0.82 / 0.93 / 0.96 |
| A, D and E: a one-line description of every entity averaged into its document vector (ReCo's corpus rewrite) | 0.94 / 0.99 / 1.00 | | 0.74 / 0.90 / 0.96 | 0.71 / 0.90 / 0.95 | |
| A and D with the rewrite written as code stubs, embedded as documents (B) | 0.95 / 0.97 / 0.98 | | | | |

- A and D together raised delivery at 6k in all four projects (1 to 8 points) and
  at 12k in three; the first five results held 71% of the gold entities instead of
  62%. Claims rose from 50 to 54 of 74 at 6k and from 59 to 63 at 12k, and stayed
  at 71 at 24k. Neither costs a model call.
- E added about one point. It needs a small-model call per entity at every
  indexing, the cost already rejected for semantic cards, so it is not adopted.
- B raised the first five results to 88% on Starlette but lost one question at
  24k and costs 30% more per question. The model reproduced Starlette's code
  almost verbatim from memory, so this figure overstates what a stub achieves on
  code the model has never seen.

## Limits

- The papers measure web search, question answering, small snippet pools,
  SWE-bench issues or commit messages; none measures delivery of whole entities
  under a character budget.
- Four Python libraries, 96 questions: a direction, not a significance test. One
  question moves a project's figure by 2 to 4 points.
- Starlette is the development set. Click, Jinja2 and httpx have each been used
  for their single confirmation run; later figures on them are diagnostic.
- Other languages, monorepos and projects above a few thousand entities.
- Task success and whole-run tokens of an agent using the delivery.
