# EmbeddingGemma 2 indexing: validation of CPU cost, parallelism and long-run reliability

Date: 2026-10-26  
Status: validated with reservations; no product code was changed by this validation  
Scope: the optional EmbeddingGemma 2 provider of `codebase-map`, in particular
`plugins/codebase-map/skills/map-method/scripts/embedding_worker.py` and
`plugins/codebase-map/skills/map-method/references/embeddings.md`

Related documents:

- [EmbeddingGemma papers and repository configuration](../../references/embeddinggemma-papers.md)
- [Codebase Map embedding benchmark](../../plugins/codebase-map-research.md#embedding-benchmark)

## 1. Verdict

The current implementation is validated for its tested safety, cache and freshness
contracts, and for opt-in CPU indexing when a build fits within the configured
timeout and can finish in one run.

It is **not yet validated for unattended long-running indexing of very large
repositories on low-power laptops**. The blockers are operational rather than
model-quality problems:

1. One 300-second timeout covers a batch of up to 16 distinct pending inputs. Long
   inputs on slower hardware can exceed it and lose the run.
2. Interrupted work is not resumable. Only a complete published generation can be
   reused by the next run.
3. Abrupt termination of the parent can leave `index.lock` behind and block later
   refreshes.
4. Process sharding is compatible with vector and cache identity, but it is not an
   execution path in the current API. The local probe measured about 1.5x, not Nx,
   at a fixed thread budget.
5. The query scan is pure Python. NumPy acceleration is potentially large, but
   NumPy is not guaranteed in the parent process that executes `search()`.

**Recommended order:** reliability and resumability first, then token/thread
configuration with one reindex and a quality rerun, then optional process sharding
within an explicit memory budget.

## 2. Validation methods and environment

| Method | What was done | Result |
|---|---|---|
| Independent read-only code review | A separate reviewer checked ten claims against current source, bundled reference and tests | Main claims confirmed; NumPy, sharding and freshness claims qualified |
| Existing automated tests | `python -m unittest discover -s tests -p test_codebase_map_embeddings.py -v` | **26 tests passed in 54.144 s** |
| Real ONNX Runtime probes | Loaded the exact pinned local q4 graph and tokenizer with the same dependency versions used by the worker | Dynamic sequence axis confirmed; 4,096-token input completed; latency, memory and process scaling measured |
| Query-cost microbenchmark | Compared the current Python unpack/dot-product shape with a NumPy dot product on synthetic stored vectors | 98 ms vs 3.2 ms at 1,000 vectors; 443 ms vs 0.8 ms at 5,000 vectors |

Probe environment: Windows 10.0.26200, 22 logical cores, Python 3.11.15, CPU only,
`numpy==2.4.6`, `onnxruntime==1.31.0`, `tokenizers==0.23.3`. Model:
`onnx-community/embeddinggemma-2-ONNX`, revision
`daa72c51243991dfcaf9f9137d2c573d8f7790c0`, `onnx/model_q4.onnx`.

The absolute timings belong to that machine. They are not measurements of the
target laptop. The ratios and the code findings are the transferable evidence.
The process-scaling rows are short local probes, best of two where applicable,
not a statistically robust benchmark.

## 3. Claim-by-claim validation

| ID | Claim | Verdict | Evidence and qualification |
|---|---|---|---|
| V1 | The 2,048-token limit is not baked into the ONNX export | **Validated** | `input_ids` and `attention_mask` have shapes `['batch_size', 'sequence_length']`; a 4,096-token input completed. `MAX_TOKENS = 2048` is local at `embedding_worker.py:49` and is applied at `:356` |
| V2 | Each vector depends only on its own text | **Validated for the CLI/provider path** | No padding and one inference per text at `:354-356`, `:375-386`; at most 16 texts per request at `:194-198`, `:400-404` |
| V3 | Publication is single-writer and atomic | **Validated** | Exclusive lock at `:173-175`, temporary SQLite at `:206-216`, complete-file validation at `:217`, atomic `os.replace()` at `:223-224`. Previous generation remains available until replacement |
| V4 | Interrupted pending work is not resumable | **Validated** | New vectors accumulate in memory at `:190-202`; the temporary generation is created only after all encoding at `:203-217`; failure removes it at `:229-232`. Only the previously published generation is reloaded at `:183-191` |
| V5 | A slow batch can hit the 300-second timeout | **Validated as a code path; timing is hardware-dependent** | Default `timeout=300` at `:423-425`; every exchange uses it at `:449-458`; timeout kills the child and fails the run. One exchange can contain up to 16 distinct pending texts |
| V6 | Source or manifest changes are checked before publication | **Validated with a concurrency qualification** | Manifest digest before encoding at `:182`, source verification at `:179-180`, final checks at `:218-222`. The final manifest check and index swap are separate operations, not one atomic freshness transaction |
| V7 | The query scan is pure Python | **Validated** | `_load()` validates every stored vector at `:149-166`; `search()` unpacks and scores every vector with `struct` and `math.fsum` at `:235-260` |
| V8 | NumPy replacement is a drop-in change | **Refuted** | Module import contract is standard library only at `:5`; NumPy is imported only inside the isolated backend at `:347-353`; the parent interpreter and `--runtime-python` are separate at `:506-510`, `:525` and `embeddings.md:10-19`, `:71-76` |
| V9 | Provider-profile changes prevent vector reuse | **Validated** | Profile includes dimensions, `max_tokens`, inference batch, runtime versions and threads at `:366-373`; exact profile equality is required at `:186-190`, and queries reject a changed provider at `:241-242` |
| V10 | Multi-process sharding works without code changes | **Refuted** | `refresh_index()` accepts one provider and invokes it serially at `:169`, `:194-202`; `main()` constructs one provider at `:525-529`. Independent `refresh_index()` calls each publish a complete generation |
| V11 | Sharding is architecturally compatible with deterministic vectors and cache identity | **Validated as a design assessment** | Per-text inference independence, content-digest cache keys at `:122-127`, sorted metadata/vector writes at `:194`, `:203-215`. Requires identical profiles, parent-owned complete inventory and new orchestration |

## 4. Measured CPU evidence

### 4.1 Input tokens dominate encoder latency

One text per inference, pinned q4 graph, CPU provider, best of two runs:

| intra-op threads | 128 tokens | 512 tokens | 2,048 tokens |
|---|---|---|---|
| 1 | 604 ms | 2,448 ms | 18,313 ms |
| 2 | 587 ms | 3,430 ms | 11,308 ms |
| 4 | 324 ms | 1,628 ms | 11,908 ms |
| 8 | 277 ms | 1,244 ms | 5,411 ms |

A realistic short entity of 57 tokens encoded in about 125 ms at 4 threads, about
8 entities per second. Model load took 0.5 to 1.2 seconds per provider process.

The 2,048-token rows ranged from 5.4 to 18.3 seconds across probes and thread
counts. A batch of 16 such inputs therefore represents about 86 to 293 seconds on
this machine before tokenization and protocol overhead. On hardware three times
slower, the upper case is about 879 seconds, well beyond the 300-second exchange
timeout. This is why batch size and timeout must be considered together.

### 4.2 More processes beat more threads, but memory sets the ceiling

Fixed eight-thread budget, 512-token texts:

| processes x threads | texts encoded | wall | texts/s | resident per process |
|---|---|---|---|---|
| 1 x 8 | 4 | 6.6 s | 0.61 | 441 MB |
| 2 x 4 | 8 | 11.1 s | 0.72 | about 440 MB |
| 4 x 2 | 16 | 17.1 s | 0.93 | about 439 MB |
| 8 x 1 | not reached | allocation failure | not reached | about 3.5 GB in total |

Interpretation:

- Moving from one process to four at the same total thread budget improved
  aggregate throughput from 0.61 to 0.93 texts/s, about **1.5x**.
- Each process loaded its own model/session and used about **440 MB resident**.
- The eight-process case failed native allocations and broke the process pool.
  This is a local observation, not a universal eight-process threshold; other
  memory pressure on the machine was not isolated.
- A laptop rule of thumb from these probes is `processes <= usable_RAM / 0.5 GB`,
  with total worker threads also bounded by physical cores. It must be validated
  on the target machine.

### 4.3 Query scan cost

The current parent-side path unpacks and scores every stored vector in Python.
The microbenchmark measured:

| stored 768-dimensional vectors | current Python shape | NumPy dot product |
|---|---|---|
| 1,000 | 98 ms | 3.2 ms |
| 5,000 | 443 ms | 0.8 ms |

The speedup opportunity is real, but the integration constraint is decisive:
`embedding_worker.py` promises standard-library-only import in the parent, while
NumPy belongs to the optional isolated encoder runtime. A native query scan needs
one of these explicit designs:

1. an optional, validated parent-runtime NumPy dependency with a standard-library
   fallback; or
2. scoring inside an owned runtime through a changed protocol.

Neither is a dependency-free edit. Any implementation must preserve result
identity, ranking, freshness checks and the stdlib-only fallback where promised.

## 5. Reliability findings

| ID | Severity | Finding | Consequence on a weak laptop | Required mitigation |
|---|---|---|---|---|
| R1 | High | One 300-second timeout covers up to 16 distinct pending texts | Long inputs can cause provider kill and loss of the whole unpublished run | Configurable batch and timeout, or progress-based timeout with a stuck-provider guard |
| R2 | High | No pending-vector checkpoint | First full build restarts from the last complete generation after interruption | Parent-owned checkpoint keyed by provider profile and input digest, never served, removed after successful publication |
| R3 | Medium | No stale-lock recovery | Forced kill or power loss can block all later refreshes | Owner PID/timestamp and safe recovery, or an explicit actionable recovery error |
| R4 | Medium | Final freshness check and swap are separate | A narrow concurrent-change window is not excluded by the current code | Do not claim unconditional atomic freshness; consider locking or rechecking in the same critical section |
| R5 | Medium | Parent-side Python scan and full vector validation on every query | Query latency grows with entity count on CPU-only machines | Native scan design from section 4.3, preserving the runtime contract |
| R6 | Medium | About 440 MB per provider process in the local probe | Too many shard workers exhaust RAM before cores are fully used | Explicit worker/memory budget; no unbounded fan-out |
| R7 | Low | Bundled reference calls 2,048 an encoder limit | Misstates a local configuration choice as an artifact property | Correct wording on the next kernel change; graph was verified dynamic |

Existing tests already cover normal crash cleanup and preservation of the previous
generation, source changes during encoding, invalid-vector rejection, profile
invalidation, stale-artifact rejection, tampered vectors, destination confinement
and report non-overwrite. They do not cover abrupt parent termination, resumable
pending work, slow-batch timeout behavior or multi-provider orchestration.

## 6. Feasibility for large repositories with little compute

The following are **order-of-magnitude estimates**, not benchmarks. Assumptions:
first full build, average entity about 400 tokens, about 1 second per entity on
the probe machine at 4 threads, 1.5x from four-way sharding, target laptop three
times slower, stable snapshot, no timeout. Real entity-size distribution can move
these figures substantially.

| first full build | probe machine, 1 process | probe machine, 4 shards | 3x slower laptop, 1 process | 3x slower laptop, 4 shards |
|---|---|---|---|---|
| 10,000 entities | about 2.8 h | about 1.9 h | about 8.3 h | about 5.6 h |
| 50,000 entities | about 13.9 h | about 9.3 h | about 41.7 h | about 27.8 h |
| 100,000 entities | about 27.8 h | about 18.5 h | about 83.3 h | about 55.6 h |

Consequences:

- A large first build is feasible only as a **resumable multi-session job**, not
  as one unattended run with the current timeout/checkpoint behavior.
- Sharding alone does not solve the problem. It gives modest speedup and increases
  RAM pressure.
- Reducing embedded tokens per entity is the largest measured latency lever, but
  it changes the provider profile and can change retrieval quality. It requires a
  full reindex and a quality rerun.
- Incremental rebuilds are much cheaper because unchanged published inputs are
  reused. The high-cost case is the first build, a model/profile change, or a large
  content change.
- For very large repositories where embedding cost is unacceptable, the existing
  opt-in lexical path remains the safe fallback. A scoped subset such as active
  directories is another product-level option, but it requires its own contract
  and quality evaluation.

## 7. Recommended intervention and acceptance criteria

### Phase A: reliability and resumability, no provider-profile change

1. Make encode batch size and timeout configurable. Choose a default that cannot
   kill a slowly progressing batch on the target hardware, while still killing a
   stuck provider.
2. Add a parent-owned pending-vector checkpoint bound to provider profile and
   input digest. It must never be served as an index and must be removed only
   after successful complete publication.
3. Add stale-lock ownership/recovery or a precise recovery error.
4. Expose progress counts and elapsed time for long runs.

Acceptance:

- A slow fake provider can continue progressing without being killed; a genuinely
  stuck provider still times out.
- A killed build resumed later reuses exactly the checkpointed inputs, publishes a
  complete index identical to an uninterrupted build, and never serves partial
  state.
- Forced parent termination followed by rerun either recovers safely or reports a
  specific, actionable lock error.
- Existing 26 embedding tests still pass, with new tests for interruption,
  checkpoint tampering and stale locks.

### Phase B: CPU configuration and query cost

1. Make token budget and thread count configurable, with defaults selected for the
   target laptop. Group profile changes into one rebuild.
2. Re-run the project embedding benchmark and the gold evaluation in
   `evals/codebase-map/context-scope` before adopting a smaller token budget or
   vector dimension.
3. Implement native query scoring only through one of the explicit runtime designs
   in section 4.3.

Acceptance:

- Measured indexing-time reduction on the target laptop, with peak RSS recorded.
- No retrieval-quality regression beyond an agreed threshold on the project gold.
- Query ranks and scores match the current implementation within a stated numeric
  tolerance; the promised stdlib-only path still works.
- Provider-profile changes are shown to require and perform exactly one full
  reindex.

### Phase C: optional process sharding

1. Keep the parent as the only writer and owner of the complete inventory.
2. Route stable input-digest shards to N providers with identical profiles.
3. Bound N by measured RAM and total threads by physical cores.
4. Build on Phase A checkpoints so a failed shard does not discard other shards.

Acceptance:

- Serial and sharded builds produce identical vectors, inventory metadata and
  query results for the same inputs and profile.
- Peak aggregate RSS stays within the configured budget.
- A failed shard can be resumed without recomputing completed shards.
- The current single-provider path remains available and tested.

## 8. Coverage and limits

**Inspected:** `embedding_worker.py`, `references/embeddings.md`, and
`tests/test_codebase_map_embeddings.py`; independent read-only review of ten
claims.

**Executed:** all 26 existing embedding tests; real local ONNX Runtime inference
against the pinned graph; synthetic query-scan and process-scaling probes.

**Not executed:** a full Codebase Map indexing run on a large repository; a
multi-hour soak test; a target-laptop measurement; a successful eight-process run;
a post-change quality benchmark, because no product change was made; external
deep-research expansion, which remains blocked by the research-consent setting.

**Not established:** a universal repository-size threshold, a universal process
count, production reliability on other operating systems, or exact peak memory on
a clean target laptop. The local allocation failure is evidence of memory risk,
not a general hardware limit.

## 9. Reproduction

Unit tests:

```bash
python -m unittest discover -s tests -p test_codebase_map_embeddings.py -v
```

Local probes used during validation, on this machine:

```bash
uv run --no-config --no-project --script "C:\Users\alfio\AppData\Local\Temp\opencode\eg2_probe.py"
uv run --no-config --no-project --script "C:\Users\alfio\AppData\Local\Temp\opencode\eg2_probe2.py"
uv run --no-config --no-project --script "C:\Users\alfio\AppData\Local\Temp\opencode\eg2_probe3.py"
```

The probe scripts live in the approved temporary directory and are not repository
artifacts. Probe 1 and probe 3 intentionally reached configurations that failed
memory allocation; their completed rows and failures are reported above rather
than treated as passes.

## 10. Final assessment

**Validated:** the 2,048-token cut is a local worker choice; the graph accepts
longer dynamic inputs; per-text encoding supports deterministic shard-and-merge;
publication and cache tests pass; CPU cost is dominated by input tokens; process
count is RAM-bound; the current query scan is pure Python.

**Not validated:** unattended long-running first builds of very large repositories
on low-power laptops, resumability after interruption, unchanged multi-process
execution, or drop-in NumPy acceleration in the parent process.

**Decision supported by the evidence:** proceed with a small reliability patch
before tuning threads or adding shard workers. Without checkpointing and a
slow-batch timeout fix, additional parallelism can increase memory pressure while
still losing long runs.
