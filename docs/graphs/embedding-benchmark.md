<a id="embedding-benchmark"></a>

# Which local embedder finds the code a request needs?

[Back to graphs and prototypes](README.md)

Codebase Map can rank symbols with a local embedding model beside its full-text
index. Between 2026-10-23 and 2026-10-26 two models were compared on the same
three projects, queries, gold and delivery rule. EmbeddingGemma 2 (q4) won in
every project and replaced CodeRankEmbed, which was removed with its harnesses.
This page is the record of that comparison; the measurement harnesses are not
kept.

## Setup

- **Projects:** Starlette 1.9.0 (development set), click 8.1.8 and Jinja2 3.1.6
  (holdouts, each used once). 24 questions per project, half in English and half
  in Italian, with gold entities written blind and verified against source.
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

## Results

Gold delivered whole at 6k / 12k / 24k characters, and claims at 24k.

| Project | Path | CodeRankEmbed | EmbeddingGemma 2 |
|---|---|---|---|
| Starlette | hybrid, no model call | 0.47 / 0.55 / 0.74 | 0.63 / 0.81 / 0.94, 17/19 |
| Starlette | rewritten | 0.76 / 0.88 / 0.98 | 0.88 / 0.97 / 1.00, 17/19 |
| Starlette | two-pass rewritten | | 0.93 / 0.97 / 0.99, 17/19 |
| click | hybrid, no model call | 0.35 / 0.46 / 0.58, 16/19 | 0.54 / 0.73 / 0.85, 17/19 |
| click | rewritten | 0.64 / 0.77 / 0.84, 13/19 | 0.67 / 0.82 / 0.89, 19/19 |
| click | two-pass rewritten | | 0.69 / 0.83 / 0.94, 19/19 |
| Jinja2 | hybrid, no model call | 0.46 / 0.61 / 0.73, 14/18 | 0.49 / 0.69 / 0.83, 15/18 |
| Jinja2 | rewritten | 0.70 / 0.75 / 0.91, 16/18 | 0.68 / 0.82 / 0.98, 17/18 |
| Jinja2 | two-pass rewritten | | 0.67 / 0.86 / 0.94, 17/18 |

Claims for CodeRankEmbed on Starlette were not recorded. The planner and packet
path that the embedder first fed delivered 0.46 on Starlette and 0.29 on click.

## What it shows

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

## Not verified

- Three Python libraries, 72 questions: a direction, not a significance test.
- Click and Jinja2 were consumed by earlier rounds of the same redesign; their
  figures are diagnostic. A fourth unseen project is needed to confirm the
  two-pass rewrite.
- Other languages, monorepos and projects above a few thousand entities.
- Task success and whole-run tokens of an agent using the delivery.
