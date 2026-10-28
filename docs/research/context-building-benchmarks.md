<a id="code-context-benchmarks"></a>

# Code-context benchmark and test diary

[Back to Context-building research](context-building-research.md) · [Used by Codebase Map](../plugins/codebase-map.md)

> **This is the single canonical diary for local code-context experiments.**
> It tracks benchmark configurations, results, costs, rejected approaches and the
> best current candidate. Scientific papers and literature-derived findings stay
> in [Code-context retrieval: scientific research and findings](context-building-research.md).
> Snapshot: 2026-10-27. The end-to-end gate of 2026-10-27 is the only run added
> since the 2026-10-26 consolidation; see the [changelog](#changelog).

[Current assessment](#current-assessment) ·
[Approach ledger](#approach-ledger) ·
[Benchmark contract](#benchmark-contract) ·
[Test diary](#test-diary) ·
[Costs](#costs) ·
[Limits](#limits) ·
[Next decisions](#next-decisions) ·
[Evidence register](#evidence-register) ·
[Changelog](#changelog)

## Current assessment

1. **Best measured candidate on the latest unseen private set:** Sonnet 5.5 with
   A+D, arm C4, at 0.38 / 0.59 / 0.64 whole gold delivered at 6k / 12k / 24k.
   It is the strongest candidate at 12k and 24k, not a validated product default.
   The run was single, small and expensive relative to Haiku.
2. **Best supported architectural direction:** search first, use lexical and
   optional dense indexes as candidate generators, rewrite from grounded names,
   then deliver exact whole entities by rank. The old scope-planner plus packet
   direction failed its decision gate. This direction still has to prove value
   on completed agent tasks.
3. **Verified shipped core:** snapshot-bound SQLite FTS5, optional local
   EmbeddingGemma 2 q4 and hybrid rank fusion. The two-pass rewriter and the
   A/D/E/picks variants belong to the research harness. An inventory did not
   locate the two-pass prompt's executable owner in the kernel; do not describe
   it as shipped until that binding exists.
4. **Engineering priority:** reliability and resumability of semantic indexing,
   plus correct source reading and freshness checks. More workers or ranking
   variants do not fix those constraints.
5. ~~**Next decision:** test whether a static context packet improves real agent
   outcomes against bounded exploration with search tools. Do not start another
   ranking sweep on the consumed holdouts.~~ Superseded on 2026-10-27 by the
   [end-to-end gate](#2026-10-27-end-to-end-gate-on-modal).
6. **End-to-end gate (2026-10-27, measured):** on 23 fresh private tasks with
   hidden test oracles, Sonnet 5.5 solved 21 with lexical search (B0), 19 with
   hybrid EmbeddingGemma search (B1) and 19 with the static A+D packet (A2).
   No difference is significant; by the pre-registered rule the static packet
   is not adopted as default and EmbeddingGemma stays opt-in. The packet cost
   the most per solved task.

### Status vocabulary

- **Shipped:** bound to current product source.
- **Measured:** observed in a dated local run, with its stated population.
- **Candidate:** promising enough for a controlled next test, not adopted.
- **Rejected:** excluded for the measured configuration and reason stated.
- **Deferred:** not selected now; a different budget, hardware or design could
  justify another evaluation.
- **Not tested:** no local result exists.

## Approach ledger

| Approach or variant | Status | Recorded outcome and decision |
|---|---|---|
| Original scope planner + context packet | **Rejected as the context-construction direction** | Initially refused 72 of 72 attempts. After phases 1 and 2 it still trailed plain text at every budget; phases 3 and 4 stopped. Keep the verified correctness fixes, not the claim that this path saves context. |
| Plain lexical text retrieval | **Baseline and fallback** | Simple and cheap; Starlette 0.312 / 0.469 / 0.521. It remains the baseline every more complex path must beat at equal opportunity. |
| Hybrid FTS5 + EmbeddingGemma 2 | **Shipped opt-in core; quality selected** | Beat CodeRankEmbed in every no-call project and budget comparison by 3 to 27 points. Indexing cost and long-run reliability remain separate gates. |
| Two-pass grounded Haiku rewrite | **Measured benchmark baseline** | Large gain over the old packet and useful on public code, but unstable on private code. Not bound to an executable kernel owner in the inspected inventory. |
| Sonnet 5.5 + A+D | **Best current candidate** | Best 12k/24k averages on the 28-question private confirmation. C2/C4 is the cleaner model comparison because A+D is constant. Not replicated and not an end-to-end result. |
| A: average question and rewrites in one vector | **Not confirmed** | Small public gains, inconsistent private outcomes. Do not adopt independently of a fresh ablation. |
| D: graph-based rank boost | **Not confirmed** | Improved early budgets on public libraries, did not generalize cleanly to private code. The graph is not a universal ranking rule. |
| Uncapped picks delivered first | **Rejected in current form** | Helpful at 6k, but five-pick bundles occupied 20k to 190k characters in some questions and caused 24k losses. |
| Picks capped to a budget share or used as a rank boost | **Not tested; next candidate** | Targets the observed failure of uncapped picks without assuming that the correction works. |
| Hypothetical-code stubs, B | **Rejected on private code** | Invented 134 absent names on the trading core and lost 8 points at 24k. Public-code memorization made the public result misleading. |
| Graph neighbours as delivery filler | **Rejected** | Reduced delivery by 8 to 21 points at 6k in the semantic-card experiments. |
| Semantic cards and per-entity descriptions, E | **Deferred** | Some gains, including double-digit improvements at selected budgets, but they require model calls at indexing and showed inconsistent returns. Not refuted on every corpus or hardware. |
| Local cross-encoder rerankers | **Deferred for this CPU** | gte reached 0.99 at 24k on Starlette but cost about 26 CPU seconds per question; sno and Qwen were too heavy for the machine. |
| Generic Sonnet localization agent | **Rejected for cost** | Reached 0.92 at 24k on Starlette with about 825,000 billed tokens per question. |
| Slim CLI localization agent | **Deferred, unresolved** | Reached 0.99 at 24k on Starlette at 0.45 USD for 24 questions, then failed on click because a source-reader bug returned a whole file. It has not had a corrected cross-corpus evaluation. |
| Identifier router | **Not tested for quality** | Could avoid rewrite calls on explicit symbol lookups. Public inspection suggests savings, not a measured quality gain. Regex routing and private-code evaluation remain open. |
| CoIR/CosQA comparison | **Not tested** | Useful for comparable published retrieval numbers, but it does not replace repository-level or task-success evaluation. |
| End-to-end agent task success | **Not tested; highest priority** | No current result establishes completed tasks, total agent tokens and latency against autonomous exploration. |

## Benchmark contract

<a id="setup"></a>

### Metrics

- **Whole gold delivered:** for each question, the share of gold entities delivered
  complete, averaged over questions. Values appear at 6,000 / 12,000 / 24,000
  characters. This is the primary retrieval metric, not task success.
- **Claims:** public-gold scenario statements whose supporting lines are inside
  the delivery.
- **Recall@5 and Recall@20:** share of gold entities in the first 5 or 20 ranks.
- **Per-question wins and losses:** paired comparison used to expose averages
  driven by a few questions.
- **Cost and latency:** rewrite tokens and dollars, delivery tokens, indexing
  time, memory and query time where measured.

### Corpora and consumption state

| Corpus | Documents and questions | Role | Current evidentiary state |
|---|---|---|---|
| Starlette 1.9.0 | 669 documents, 24 questions, 19 claims | Development | Guided choices; not a holdout |
| click 8.1.8 | 566 documents, 24 questions, 19 claims | Initial public holdout | Consumed; later results diagnostic |
| Jinja2 3.1.6 | 945 documents, 24 questions, 18 claims | Initial public holdout | Consumed; later results diagnostic |
| httpx 0.28.1 | 544 documents, 24 questions, 18 claims in 5 scenarios | Frozen public confirmation | Used once; now diagnostic |
| Private trading core, snapshot 2026-01-14 | 3,116 documents, 24 questions from 29 commits | First private round | Consumed |
| Private meal-planning backend, snapshot 2026-04-15 | 1,130 documents, 23 questions from 24 commits | First private round | Consumed |
| Private trading core, snapshot 2026-08-13 | 3,348 documents, 19 questions from 21 commits | Private confirmation | Consumed |
| Private meal-planning backend, snapshot 2026-07-22 | 1,217 documents, 9 questions from 12 commits | Private confirmation | Consumed |

There are 96 public-library questions, evenly split between English and Italian,
and 75 private questions, alternating languages by numeric ID. No fresh set
remains from this collection.

### Private-question construction

A post-snapshot `fix`, `feat` or `perf` commit becomes a request written before
the change. Eligible gold contains one to three pre-existing functions, methods
or classes, at most 24,000 characters in total, with the same pre-commit text in
the snapshot. A model wrote requests without changed symbol, file or module
names; mechanical leak checks and independent review preceded freezing.

This measures localization for circumscribed pre-change work. It does not cover
new entities, large changes, every source file a developer would read or whether
an agent can complete the task.

## Test diary

New entries append a dated run with its frozen configuration and evidence. Do
not rewrite historical outcomes. Update the approach ledger separately and link
it to the entry that justifies the change.

### 2026-10-23 to 2026-10-25: context-packet redesign

The original scope-plus-packet path refused all 72 attempts. After the first two
redesign phases and the permitted format change:

| Budget | Plain text | Redesigned packet, natural query |
|---:|---:|---:|
| 6,000 | 0.312 | 0.208 |
| 12,000 | 0.469 | 0.375 |
| 24,000 | 0.521 | 0.458 |

The packet produced no additional supported claims. The predeclared gate was not
met, so phases 3 and 4 did not start. Useful verified outcomes were retained:
packets can refuse with explicit reasons, preserve obligations and run in
seconds rather than about 95 seconds per packet. They did not beat plain text on
coverage.

Evidence: [raw context-scope results](../../evals/codebase-map/context-scope/RESULTS.md)
and [decision specification](../superpowers/specs/2026-10-25-context-packet-redesign.md).

<a id="embedding-benchmark"></a>

### 2026-10-23 to 2026-10-26: embedder selection

The comparison used the same projects, queries, gold and whole-entity delivery
rule. EmbeddingGemma 2 q4 replaced CodeRankEmbed in commit `9adf340dd`,
codebase-map 8.10.0, marketplace 41.3.0.

| Artifact or cost | CodeRankEmbed | EmbeddingGemma 2 q4 |
|---|---|---|
| Artifact | Community INT8 ONNX, revision `e74f446d` | `onnx-community/embeddinggemma-2-ONNX`, revision `daa72c51` |
| Licence | MIT | Apache-2.0 |
| Files | 138.6 MB graph | 174 MB weights, 0.5 MB graph, 32 MB tokenizer |
| Input | 512 tokens | Worker profile: 2,048 tokens |
| Prefixes | Query only | Document and query |
| Starlette index, 669 entities, 4 threads | 126.5 seconds | About 12 minutes |

Whole gold delivered at 6k / 12k / 24k, then claims at 24k where recorded:

| Project | Retrieval path | CodeRankEmbed | EmbeddingGemma 2 |
|---|---|---|---|
| Starlette | Hybrid, no model call | 0.47 / 0.55 / 0.74 | 0.63 / 0.81 / 0.94, 17/19 |
| Starlette | Rewritten | 0.76 / 0.88 / 0.98 | 0.88 / 0.97 / 1.00, 17/19 |
| Starlette | Two-pass rewritten | Not recorded | 0.93 / 0.97 / 0.99, 17/19 |
| Starlette | Two-pass, EmbeddingGemma only | Not recorded | 0.85 / 0.97 / 1.00, 18/19 |
| click | Hybrid, no model call | 0.35 / 0.46 / 0.58, 16/19 | 0.54 / 0.73 / 0.85, 17/19 |
| click | Rewritten | 0.64 / 0.77 / 0.84, 13/19 | 0.67 / 0.82 / 0.89, 19/19 |
| click | Two-pass rewritten | Not recorded | 0.69 / 0.83 / 0.94, 19/19 |
| Jinja2 | Hybrid, no model call | 0.46 / 0.61 / 0.73, 14/18 | 0.49 / 0.69 / 0.83, 15/18 |
| Jinja2 | Rewritten | 0.70 / 0.75 / 0.91, 16/18 | 0.68 / 0.82 / 0.98, 17/18 |
| Jinja2 | Two-pass rewritten | Not recorded | 0.67 / 0.86 / 0.94, 17/18 |
| httpx | Hybrid, no model call | Not recorded | 0.83 / 0.90 / 0.91, 14/18 |
| httpx | Two-pass, EmbeddingGemma only, unseen single run | Not recorded | 0.90 / 0.95 / 0.96, 17/18 |

The first two-pass rows used CodeRankEmbed for the initial pass. Rows marked
`EmbeddingGemma only` used it for both passes, so the table does not attribute
every two-pass result to EmbeddingGemma alone.

**Decision:** EmbeddingGemma 2 won every no-call project and budget comparison by
3 to 27 points and was selected; individual rewritten cells vary. CodeRankEmbed
was removed. This is not evidence that first-build cost, unattended long runs or
large repositories are operationally acceptable.

<a id="rewrite-and-fusion-experiments"></a>

### 2026-10-26: public rewrite and fusion experiments

These runs reused cached vectors and rewrites. Starlette was the development
set; the other public projects were already consumed and are diagnostic here.

| Ranking | Starlette | httpx | click | Jinja2 | Mean |
|---|---|---|---|---|---|
| Rewritten rankings merged by reciprocal rank | 0.85 / 0.97 / 1.00 | 0.90 / 0.95 / 0.96 | 0.69 / 0.83 / 0.94 | 0.67 / 0.86 / 0.94 | 0.78 / 0.90 / 0.96 |
| A: question and rewrites averaged in one vector, terms in one lexical query | 0.91 / 0.97 / 1.00 | 0.91 / 0.94 / 0.96 | 0.68 / 0.85 / 0.94 | 0.65 / 0.86 / 0.95 | 0.79 / 0.91 / 0.96 |
| A+D: A plus graph-linked rank boost | 0.93 / 0.97 / 0.99 | 0.91 / 0.97 / 0.96 | 0.73 / 0.87 / 0.94 | 0.70 / 0.90 / 0.95 | 0.82 / 0.93 / 0.96 |
| A+D+E: per-entity one-line description averaged into each document | 0.94 / 0.99 / 1.00 | Not run | 0.74 / 0.90 / 0.96 | 0.71 / 0.90 / 0.95 | Not comparable |
| B: hypothetical-code stubs with A+D | 0.95 / 0.97 / 0.98 | Not run | Not run | Not run | Not comparable |

- A+D improved 6k delivery in all four projects and 12k in three. Recall@5 rose
  from 62% to 71%. Claims rose from 50 to 54 of 74 at 6k and 59 to 63 at 12k;
  71 stayed unchanged at 24k.
- E added about one point but requires a model call per entity at indexing.
- B raised Starlette Recall@5 to 88%, lost one question at 24k, cost 30% more
  and benefited from visible memorization of public code.
- Merging original and rewritten rankings lost in every public project. A router
  that skips rewriting when explicit identifiers are present was inspected as a
  possible saving, not measured as a quality improvement.

### 2026-10-26: semantic cards, graph filling and rerankers

| Project | Code only | Code + semantic cards | Code + graph as delivery filler |
|---|---|---|---|
| Starlette | 0.63 / 0.81 / 0.94 | 0.66 / 0.91 / 0.99 | 0.55 / 0.83 / 0.98 |
| click | 0.53 / 0.73 / 0.85 | 0.55 / 0.75 / 0.88 | 0.33 / 0.57 / 0.76 |
| Jinja2 | 0.49 / 0.68 / 0.83 | 0.58 / 0.72 / 0.84 | 0.28 / 0.59 / 0.82 |

Semantic cards for 2,103 entities cost 0.42 USD. Their gains were not uniformly
small, but the recurring indexing call and inconsistent return led to deferral.
Graph filling lost 8 to 21 points at 6k and was rejected. A gte cross-encoder
reached 0.99 at 24k on Starlette but took about 26 CPU seconds per question;
sno and Qwen exceeded the local machine's practical budget.

### 2026-10-26: agent localization comparisons

| Variant | Result | Cost and failure mode |
|---|---|---|
| Generic Sonnet subagent locating code | 0.92 at 24k on Starlette | 19.8 million billed tokens for 24 questions, about 825,000 per question; zero false ready states |
| Slim `claude -p` with Bash and a local locator | 0.71 at 12k, 0.99 at 24k on Starlette | 0.45 USD for 24 questions; one systematic false ready on q19 |
| Slim locator plus sufficiency control | 0.958 at 24k on Starlette | Zero false ready states in this run |
| Same slim path on click | 7 of 24 ready; 0.292 at 24k against 0.535 for text | Source reader returned 131,930 characters for an eight-line method because of an inexact `typing.overload` span |

**Decision:** the generic agent is not economically competitive. The slim agent
remains an unresolved alternative, not a rejected technique, until the reader
fix and cross-corpus end-to-end comparison exist.

<a id="2026-10-26-private-code-rounds"></a>

### 2026-10-26: private-code rounds

The first 47 questions were run once and then used for diagnosis. The later 28
questions came from new snapshots and subsequent commits and were unseen before
the confirmation run.

| Arm | First round, 47 questions | Confirmation, 28 unseen questions | Rewrite cost per question |
|---|---|---|---|
| Question as written | 0.34 / 0.51 / 0.56 | 0.21 / 0.38 / 0.43 | 0 |
| Two-pass Haiku baseline | 0.45 / 0.50 / 0.70 | 0.18 / 0.45 / 0.55 | 0.0008 USD |
| Haiku A+D on the same rewrites | 0.48 / 0.62 / 0.73 | 0.27 / 0.39 / 0.55 | 0.0008 USD |
| Haiku picks first, then A | 0.54 / 0.65 / 0.75, chosen on these questions | 0.36 / 0.41 / 0.48 | 0.0010 USD |
| Sonnet 5.5 A+D | 0.55 / 0.65 / 0.76, diagnostic | 0.38 / 0.59 / 0.64 | 0.016 to 0.017 USD |
| Sonnet rankings merged by reciprocal rank | Not run | 0.37 / 0.48 / 0.64 | 0.017 USD |
| C3 rewrites without picks | Not run | 0.25 / 0.38 / 0.41 | Already cached |

Paired outcomes on the confirmation set, wins / losses with other questions tied:

| Comparison | 6k | 12k | 24k |
|---|---|---|---|
| C3 Haiku picks versus C4 Sonnet A+D | 4 / 4 | 1 / 7 | 2 / 6 |
| C3 versus C2 Haiku A+D | 4 / 1 | 2 / 2 | 3 / 5 |
| C3 versus C1 Haiku baseline | 5 / 0 | 3 / 4 | 1 / 4 |

Interpretation:

- **C2 against C4 is the cleaner model comparison:** A+D stays constant.
  C3 against C4 also changes prompt, picks and ranking and cannot isolate the
  rewriter model.
- Sonnet's advantage at 12k and 24k survived the unseen set, but 0.64 at 24k is
  still far from complete context and costs roughly twenty times Haiku.
- At least one of five picks was gold in 14 of 28 questions. In five trading-core
  questions, the picks occupied 20,000 to 190,000 characters. This explains the
  early-budget gain and later-budget loss; it does not validate a cap.
- A+D helped in the first private round but did not confirm consistently against
  the Haiku baseline in the second. Its contribution remains entangled with the
  chosen rewriter.
- Three confirmation questions received no gold from any arm at any budget.
- Hypothetical-code stubs invented 134 absent names on the trading core against
  12 for search strings and lost 8 points at 24k. They are excluded on private
  code.

### 2026-10-26: EmbeddingGemma indexing and runtime validation

Detailed claims are consolidated in [Local embedding model](local-embedding-model.md).

| Check | Result | Decision or caveat |
|---|---|---|
| Existing embedding unit suite | 26 tests passed in 54.144 seconds | Covers normal publication, cache and freshness contracts, not every interruption or long-run case |
| ONNX sequence shape | Dynamic sequence axis; a 4,096-token input completed | The 2,048 cut is a worker choice, not a fixed export dimension |
| Four-thread CPU latency | 324 ms at 128 tokens, 1.628 s at 512, 11.908 s at 2,048 | Input tokens dominate encoder latency; values belong to the probe machine |
| Process scaling at a fixed eight-thread budget | 1 x 8: 0.61 texts/s; 4 x 2: 0.93 texts/s | About 1.5x, not Nx; each process held about 440 MB resident |
| Eight processes | Native allocation failure | Evidence of memory risk, not a universal process threshold |
| Query scan | Python: 98 ms at 1,000 and 443 ms at 5,000 vectors; NumPy probe: 3.2 ms and 0.8 ms | NumPy scoring is not shipped in the parent process; integration needs an explicit runtime design |
| Batch timeout | One 300-second timeout can cover up to 16 pending inputs | Slow long batches can lose the unpublished run |
| Resumability | Only a complete published generation can be reused | Pending vectors need an owned checkpoint before long unattended builds |
| Lock recovery | Abrupt parent termination can leave `index.lock` | Needs safe recovery or an actionable error |
| Large-build estimates | 10,000 entities: about 2.8 h on the probe machine and 8.3 h on a 3x slower laptop, one process | Estimates, not benchmarks; 100,000 entities: 27.8 h and 83.3 h under the same assumptions |

**Decision:** reliability and resumability first, then token/thread configuration
with a quality rerun, then optional bounded sharding. Process sharding is
architecturally compatible with deterministic vectors but is not a current API
execution path.

### 2026-10-27: end-to-end gate on Modal

Run `.daodan/runs/20261026-code-context-e2e-gate/` (local only; report in
Italian at `REPORT.md`, protocol `00-protocol.md`, reproducibility and failure
logs under `results/`). Measured, single replicate.

- **Design.** 24 unused commits from Jupiter and Phazly (12 each), stratified;
  requests written by Opus 5.5 and verified by Fable 5.1, naming no changed
  symbol or file; hidden oracle = the tests the commit changed, validated to fail
  before and pass after the gold patch. Same agent (Sonnet 5.5, Claude Code
  2.1.311), same prompt ("reproduce, then fix"), tools and limits (60 turns,
  2.00 USD, 1,500 s) in every arm. B0: lexical search plus file reads. B1: hybrid
  search (EmbeddingGemma 2 q4 0.75, lexical 0.25). A2: no search, a 24,000-char
  packet from a grounded Sonnet rewrite with A+D ranking.
- **Execution.** One Linux container per run on Modal (8 CPU, 16 GB), 69 runs.
  One task (`hp-132e2647`) was excluded before any run because its gold patch
  fails on Linux. Two harness defects found by a 3-run probe were fixed before
  the full run: Windows-built retrieval indexes on Linux, and a visible-suite
  reference measured on Windows (up to 80 Linux-only failures).
- **Success, 23 tasks:** B0 21, B1 19, A2 19. A2 vs B1: 0.00, 95% CI
  -0.17 to +0.17, exact McNemar 2/2, p = 1.0. B1 vs B0 and A2 vs B0: -0.09,
  CI -0.22 to 0.00, 0/2, p = 0.5. No tool or environment failure; one wall-time
  exhaustion (B0).
- **Cost and time (list price):** cost per solved task B0 0.268 USD (one unknown
  cost, lower bound), B1 0.307, A2 0.338; median wall time B0 240 s, B1 234 s,
  A2 190 s. The gold change appeared in some search result in 22 of 23 runs for
  both B0 and B1. The 23rd (`hp-c69ab2e5`) is a measurement gap, not a retrieval
  miss: the commit changes only a module-level dict (`DIETARY_SUBSTITUTES` in
  `app/services/food_pool.py`), the gold list counts functions and classes only,
  so it is empty and the hit can never register; both arms returned and edited
  that file. Read per file, retrieval located the right place in 23 of 23 runs.
- **Failures were rarely localization.** Of 10 unsolved runs, 9 edited at
  least one gold source file and missed part of the requested behavior or ran
  out of time; one A2 run edited an upstream handler although its packet
  contained the gold file.
- **Decision (pre-registered):** the static packet is not adopted as default and
  no further static-ranking sweep runs on these data; EmbeddingGemma stays
  opt-in. The result is inconclusive for effects under about 20 points and
  negative for larger ones; it is not evidence of equality.
- **Ceiling effect:** every arm solved over 80%. With a strong agent and read
  tools, context construction was not the bottleneck on these tasks. A test where
  context could matter needs a smaller model or vaguer requests and at least
  two replicates.
- **Separate record:** 38 local runs of the same holdout, stopped at the owner's
  request (B0 8/12, B1 7/13, A2 9/13), never pooled with the Modal runs.

## Costs

### Query-time model and delivery cost

| Item | Measured cost |
|---|---:|
| Haiku rewrite, public libraries | About 2,700 tokens and 0.00056 USD per question |
| Haiku rewrite, private code | 0.0008 to 0.0010 USD per question |
| Sonnet rewrite, private code | 0.016 to 0.017 USD per question |
| Delivery at 6k / 12k / 24k characters | About 2,100 / 4,100 / 8,100 tokens |
| Delivery to Opus at 4 USD/M input | About 0.008 / 0.016 / 0.032 USD |
| Delivery to Sonnet at 2 USD/M input | About 0.004 / 0.008 / 0.016 USD |

Token conversion was measured with Haiku on Starlette Python, about 2.9
characters per token. Opus and Sonnet tokenizers were not measured.

The generic Sonnet locator used about 825,000 billed tokens per Starlette
question for 0.92 at 24k. The measured rewrite pipeline used about 10,700 tokens
including delivery and rewriting. These figures establish a large efficiency
difference on that corpus, not equal end-to-end task value.

### Indexing and freshness

- Starlette, 669 entities: about 12 minutes with EmbeddingGemma 2 on four CPU
  threads; CodeRankEmbed took 126.5 seconds.
- Jinja2, 945 entities: about 31 minutes on four CPU threads.
- The private corpora were encoded remotely in the research harness in a few
  minutes per corpus, not precisely timed. Remote execution is not an approved
  product data path.
- A run observed 17 to 24 seconds per search on 268 files when freshness invoked
  one Git process per file, against 0.34 seconds after the harness cached the
  check. This is dated diagnostic evidence; current product behavior must be
  checked in source before claiming the fix state.

### Experiment expenditure recorded

- Haiku rewrites: 0.014 to 0.025 USD per project and variant.
- Sonnet rewrites: 0.36 to 0.39 USD per project in the diagnostic round and
  about 0.48 USD in the confirmation.
- Semantic cards: 0.42 USD for 2,103 entities.
- Slim localization agent: 0.45 USD for 24 Starlette questions.
- Not measured: supporting agents that read papers and wrote or verified
  questions, and remote compute expenditure.
- End-to-end gate (2026-10-27, list price, agent runs on a subscription):
  dataset requests 12.25 USD; pilots 4.17 USD; interrupted local holdout
  6.26 USD plus 6 unknown; Modal holdout 17.88 USD plus 1 unknown. Modal
  compute for encoding and runs is not included.

## Limits

1. **Small samples and no inferential statistics.** There are 9 to 24 questions
   per project, no confidence intervals and no significance tests. One question
   can move a project average materially.
2. **No repeated rewrites.** Haiku and Sonnet are non-deterministic and each
   variant ran once. Run-to-run variability is unknown.
3. **No fresh corpus remains.** Starlette guided development and every public
   and private holdout in this collection has been consumed.
4. **Public contamination.** The public libraries may be memorized. The stub
   experiment shows why public-only gains can be misleading.
5. **Gold is a proxy.** Private gold is changed code, not all necessary reading;
   public gold was model-written. The private selection favors small changes to
   existing Python entities and excludes new or larger work.
6. **Possible generator/rewriter bias.** Sonnet generated the private requests
   and is also evaluated as a rewriter. A style advantage is an open risk, not a
   demonstrated effect.
7. **The metric is not the task.** Whole-gold delivery does not establish a
   correct explanation, patch, test result or completed user request.
8. **Coverage is narrow.** Python only, at most about 3,300 entities, English
   and Italian questions, no monorepo and no repository above 10,000 entities.
9. **Operational incidents constrain interpretation.** Disk exhaustion, memory
   pressure, a modified running script, interrupted sessions and remote-service
   failures affected individual runs. Frozen scripts, cached vectors and
   reconstructed caches preserved some results, but they are not replications.
10. **Static inspection is not runtime proof.** Harness outcomes, product source
    status and installed-host execution remain different evidence classes.

## Next decisions

This is a **proposed sequence**, not a measured result.

1. **Stop rank-only tuning on all existing sets.** Do not try more prompts,
   fusion weights, graph boosts or stubs on consumed questions.
2. **Close correctness and reliability prerequisites.** Verify the source-reader
   fix, current freshness behavior, slow-batch timeout handling and resumable
   indexing before comparing performance again.
3. ~~**Run an end-to-end gate first.**~~ Done on 2026-10-27; see the
   [end-to-end gate](#2026-10-27-end-to-end-gate-on-modal). No arm improved task
   success, so step 4 does not start on these data. Original wording kept for
   the record: on fresh private tasks with executable or
   independently adjudicated outcomes, compare the same agent under equal total
   budgets using:
   - bounded exploration with ordinary lexical/source tools;
   - the hybrid index as an on-demand tool;
   - the best static-packet candidate.
   Primary outcome: task success. Secondary outcomes: total tokens, wall time,
   incomplete or false-ready results and human intervention. Pre-register the
   decision rule after a small instrumentation pilot, not after seeing the test.
4. **Only if a static packet shows task value, run the ranking factorial.** Use
   Haiku/Sonnet × picks absent/capped, constant prompt and ranking, the raw
   question as a no-call control, replications and a fresh private project.
   Keep A and D separately ablatable so their contributions are not inferred
   from a combined arm.
5. **Defer broader comparisons until the gate says they matter.** Other
   languages, monorepos, CoIR, remote rerankers and per-entity descriptions are
   later questions, not the next way to spend the remaining research budget.

## Evidence register

| Evidence | Role |
|---|---|
| [Context-building research](context-building-research.md) | Papers, primary sources and literature-derived hypotheses; no local test diary |
| [Context-scope raw results](../../evals/codebase-map/context-scope/RESULTS.md) | Early text/graph/packet baselines, refusal and packing evidence, impact and lifecycle checks |
| [Context-scope protocol](../../evals/codebase-map/context-scope/README.md) | Corpus, freezing, metrics and harness rules |
| [Local embedding model](local-embedding-model.md) | Model card, prompts, MRL, vendor guides, CPU and reliability probes |
| [Prompt engineering and brevity](prompt-engineering-and-brevity.md) | Evaluation methodology, independent verification and prompt/agent literature |
| `.daodan/runs/20261025-context-redesign/REPORT-ricerca-del-codice.md` | Archived narrative of the 2026-10-23 to 2026-10-26 research run; not the current tracker |
| `.daodan/runs/20261025-context-redesign/private-holdouts/` | Local-only private candidates, requests, verdicts, frozen questions and raw results; not for public release |
| `.daodan/runs/20261025-context-redesign/worktree/evals/codebase-map/context-scope/harness/` | Research harness on local branch `context-ablation`; experiment code, not shipped product |
| `.daodan/runs/20261025-context-redesign/logs/` and `vectors/` | Frozen run scripts, logs, cached vectors and manifests |
| `.daodan/runs/20261026-code-context-e2e-gate/` | Local-only end-to-end gate of 2026-10-27: protocol, harness, frozen private tasks, 69 Modal runs, `REPORT.md` (Italian), `results/summary-modal.json`; not for public release |

## Changelog

- **2026-10-27:** added the end-to-end gate on Modal (23 private tasks, three
  arms, one replicate); struck through the "next decision" it answers in the
  current assessment and step 3 of the next decisions; recorded its expenditure
  and evidence location; snapshot date moved to 2026-10-27. Later the same day:
  the one run where the gold change was absent from every search result was
  traced to an empty gold list (module-level dict change), not to retrieval.
  Evening: the result became product in codebase-map 8.12.0 (`codebase_map_search`,
  `codebase_map_index`, the lexical index built with every snapshot, the
  `locate.md` guide, bindings in project-delivery and senior-review; spec
  `docs/specs/2026-10-27-code-access-design.md`, run `.daodan/runs/20261027-code-access`);
  parity replay 136 of 137 recorded searches identical through the new path.
  2026-10-28 morning: acceptance 7 (instrumented consumer gate, run
  `.daodan/runs/20261027-acceptance7`): with the worker brief's `locate:` line and the
  real codebase-map 8.12.0 server, the agent called `codebase_map_search` before its
  first read and first edit in 21 of 21 judged tasks; 19 solved on the hidden oracle;
  median 5 searches, 0.25 USD per run; 6.43 USD known spend; two cells lost by a
  harness parser defect. A map built by another interpreter is `stale` for the server.
  2026-10-28: prompt test P1 (run `.daodan/runs/20261028-prompt-requirements`): the brief
  obliged a numbered requirement list before the first edit. 20 of 23 solved; on the
  21 tasks both arms judged, 19 against 19 (one gained, one lost); 0.34 against 0.25 USD
  per run; the list appeared before the first edit in only 6 of 23 runs. Inconclusive
  under the rule fixed beforehand; the requirement-list line stays a hypothesis.
- **2026-10-26:** consolidation into this single canonical diary.
