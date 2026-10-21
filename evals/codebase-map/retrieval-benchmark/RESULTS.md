# Retrieval benchmark results

## Run

- **Date:** 2026-10-21
- **Corpus:** this repository's `plugins/` tree, one Codebase Map SQLite snapshot
- **Symbols:** 1,079
- **Gold queries:** 36 (12 exact, 4 traceback, 8 natural-language English, 6 natural-language Italian, 6 code-to-code)
- **Machine path:** local Windows workstation, CPU ONNX Runtime
- **Raw output:** retained outside the repository with the run; the tables below are the recorded result

The snapshot itself was reused for all candidates, so its build time is not
attributed to any candidate. Corpus extraction plus the FTS5 index took about
1.1 seconds for candidate A after the snapshot existed.

## Overall

| Candidate | Symbol Recall@20 | MRR@10 | nDCG@10 | Dependency Recall@15 | Mean latency | P95 latency | Index/encode time |
|---|---:|---:|---:|---:|---:|---:|---:|
| A: exact + code-aware FTS5 + graph | 0.778 | 0.572 | 0.580 | 1.000 | 0.009 s | 0.011 s | 1.13 s |
| B: Jina v2 code ONNX INT8 + FTS5 + graph | 0.722 | 0.551 | 0.546 | 1.000 | 0.071 s | 0.136 s | 136.3 s total sidecar; 124.8 s document encoding |
| C: CodeRankEmbed ONNX INT8 + FTS5 + graph | 0.778 | 0.560 | 0.560 | 1.000 | 0.076 s | 0.145 s | 107.0 s total sidecar; 93.1 s document encoding |

Model files: B used the official Jina ONNX INT8 file (161,895,621 bytes,
SHA-256 `ed45870251c9f0cf656e78aab0d37a23489066df8a222bb1c8caf8a45f2cb16d`).
C used the pinned community INT8 export of CodeRankEmbed (138,619,279 bytes,
SHA-256 `4eae31d09b1843103a1ebd5e2b2e24b5a5cad441a33906b35b12b1e2ed91d1db`),
because the official CodeRankEmbed repository ships no ONNX graph.

## By query kind

| Kind | A Recall / MRR | B Recall / MRR | C Recall / MRR |
|---|---:|---:|---:|
| Exact | 1.000 / 0.958 | 1.000 / 0.958 | 1.000 / 0.958 |
| Traceback | 1.000 / 0.786 | 1.000 / 0.786 | 1.000 / 0.800 |
| Natural language, English | 0.750 / 0.080 | 0.625 / 0.149 | 0.875 / 0.181 |
| Natural language, Italian | 0.333 / 0.050 | 0.000 / 0.000 | 0.167 / 0.000 |
| Code-to-code | 0.667 / 0.667 | 0.833 / 0.667 | 0.667 / 0.667 |

## Reading

- Exact and traceback retrieval is already solved by anchors plus FTS5: every
  candidate reaches Recall@20 1.000 on both kinds.
- CodeRankEmbed is the strongest embedding candidate on English natural
  language, but its advantage is confined to that slice. Jina v2 does not beat
  candidate A overall and finds none of the Italian gold symbols in the top 20.
- Italian natural language is weak for every candidate. Neither embedding
  model justifies treating Italian paraphrases as covered.
- Dependency Recall@15 is 1.000 for all candidates, but only five queries carry
  declared dependencies. That result says the graph expansion works on those
  cases; it is not evidence that the candidates differ there.
- The cost gap is decisive at this corpus scale: A answers in about 9 ms with
  a one-second index, while B and C need roughly 100 seconds to encode 1,079
  short symbol documents and answer 8 times slower.

## Decision

Do not add a default embedder to Codebase Map. Keep exact anchors, code-aware
FTS5 and graph expansion as the retrieval path. An embedder remains an
optional experiment for English natural-language seed discovery only, and any
future adoption needs a larger gold set, especially Italian queries and
queries whose answers share no identifier vocabulary with the target symbol.
