# Retrieval benchmark: exact/FTS/graph versus code embeddings

This harness answers one narrow question for Codebase Map: does a local code
embedder improve symbol seed discovery enough to justify its download, index
time and query latency, after exact anchors and the graph are already used?

It is a development eval under `evals/`. It is never shipped in a plugin
package and it does not change Codebase Map runtime behaviour.

## Candidates

| Candidate | Ranking |
|---|---|
| A | Exact symbol anchors, code-aware SQLite FTS5 (`bm25(fts,10,5,3,1)` over exact name, identifier subtokens, signature and document columns), then one-hop graph expansion for dependency scoring |
| B | `jinaai/jina-embeddings-v2-base-code`, official `onnx/model_quantized.onnx` at pinned revision `516f4baf13dec4ddddda8631e019b5737c8bc250`, Apache-2.0 |
| C | `nomic-ai/CodeRankEmbed` through the pinned community INT8 ONNX export `mrsladoje/CodeRankEmbed-onnx-int8@e74f446dc6e67e29fcee77213472c142f73a6bbb`; the official repository ships no ONNX graph. The query prefix is `Represent this query for searching relevant code: ` |

For B and C, exact anchors stay first. Without an anchor, dense and FTS ranks
are fused with dense weight 0.75 and lexical weight 0.25. The same symbol
document is used for every candidate: kind, qualified name, rendered full
signature, file path and resolved caller/callee names from one snapshot.

## Corpus and gold set

The default corpus is this repository's `plugins/` tree. Generated host
exports are excluded by that target choice, so the same source is not indexed
five times. `queries.json` contains 36 hand-written queries: exact names,
traceback text, natural language in English, natural language in Italian, and
code-to-code snippets. Gold symbol ids are validated against the corpus; a
missing gold symbol fails the run instead of silently scoring zero.

Dependency Recall uses the one-hop expansion of the top 20 seeds. The expanded
ranking interleaves each seed with its resolved neighbours, so dependencies
of high seeds can enter the first 15 positions.

## Run

Candidate A is stdlib-only:

```text
python evals/codebase-map/retrieval-benchmark/run_benchmark.py --models A --out <output-dir>
```

All candidates use `uv` for the ONNX sidecar dependencies
(`numpy`, `onnxruntime`, `tokenizers`, `huggingface_hub`). Model files are
downloaded into `<output-dir>/models` and their SHA-256 is recorded:

```text
python evals/codebase-map/retrieval-benchmark/run_benchmark.py --models A,B,C --out <output-dir>
```

Use `--manifest <manifest.sqlite>` to reuse a snapshot, or `--target <tree>`
to build one for another corpus. Outputs are `corpus.jsonl`, `adjacency.json`,
`rankings-*.json` and `results.json` with per-query rankings and timings.

## Metrics

- Symbol Recall@20 and MRR@10 over the gold expected symbols.
- nDCG@10 with expected symbols at grade 3 and declared dependencies at grade 2.
- Dependency Recall@15 after one-hop expansion of the top 20 seeds.
- Mean and P95 query latency, corpus/FTS build time, embedding document
  encode time and total model index time.

Latency excludes model download. Index build time for B and C includes the
sidecar process after its dependencies and model are available; the recorded
run notes in `RESULTS.md` state when downloads were cold.
