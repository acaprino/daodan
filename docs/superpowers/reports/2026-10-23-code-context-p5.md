# P5: optional local embeddings and incremental cache

Date: 2026-10-23. Base: `681ccc57a24af82398fff5c0dbc3cf047289d85e`.

P5 implements an optional offline CodeRank provider, an atomic derived SQLite
index and explicit fusion with the existing local retrieval API. Indexing,
ranking and navigation make no paid LLM calls. Whole-flow token savings remain
unmeasured. The provider stays **opt-in**.

## Provider and runtime decision

Reuse [CodeRankEmbed](https://huggingface.co/nomic-ai/CodeRankEmbed), via its
[community INT8 conversion](https://huggingface.co/mrsladoje/CodeRankEmbed-onnx-int8)
at `e74f446dc6e67e29fcee77213472c142f73a6bbb` (MIT). The corrected
reduce-range artifact is 138,619,279 bytes, with graph SHA-256
`4eae31d09b1843103a1ebd5e2b2e24b5a5cad441a33906b35b12b1e2ed91d1db`
and tokenizer SHA-256
`91f1def9b9391fdabe028cd3f3fcc4efd34e5d1f08c3bf2de513ebb5911a1854`.

The map interpreter reads the existing snapshot and verifies source freshness.
A separate explicitly selected Python runs encoding only, with `-I`, the owned
helper and pinned local bytes. It imports no project or map/parser modules.
The parent closes the process using an explicit stop, with timeout/kill recovery.
Vectors remain in owned temporary/derived files; ordinary output is compact.

The already installed encoder runtime is Python 3.11.15, NumPy 2.4.6,
ONNX Runtime 1.31.0 and tokenizers 0.23.3 on Windows CPU. Dependency release and
platform information was checked against the publishers' pages for
[ONNX Runtime](https://pypi.org/project/onnxruntime/1.31.0/),
[tokenizers](https://pypi.org/project/tokenizers/0.23.3/) and
[NumPy](https://pypi.org/project/numpy/2.4.6/).
[Runtime compatibility](https://onnxruntime.ai/docs/reference/compatibility.html)
covers Windows/Linux distributions; only Windows execution was exercised.
[Security guidance](https://github.com/microsoft/onnxruntime/security) informs
pinned trusted artifacts, built-in CPU kernels and no custom model code.
This is not a comprehensive vulnerability-free or installed-host claim.

Reusing the existing model avoids a new download and conversion. Other
benchmark models have no demonstrated integration or quality advantage for
this increment and are not adopted.

Weights can be shared across projects through the optional `model_dir` or the
default per-user cache: `%LOCALAPPDATA%/Daodan/models/CodeRankEmbed/REVISION/`
on Windows, `$XDG_CACHE_HOME/daodan/models/CodeRankEmbed/REVISION/` on Linux
(default `~/.cache`). Cache lookup never downloads weights. Each project retains
its own derived vectors; native weights stay loaded for one provider session.

## Cache and retrieval behavior

The exact encoded input includes path, name, signature and source. Its hash,
model/tokenizer identity, runtime, document schema and encoder settings govern
reuse. Changed bodies, renames, deleted entities and configuration changes are
covered by tests. Complete generations publish atomically under a lock;
exceptions preserve the previous generation. Checksums, dimensions and norms
protect persisted vectors. The manifest is immutable.

Native inference encodes one input at a time. A real probe exposed batch-dependent
INT8 activation scales: the same input changed when another input joined its
batch. Encoder version 2 declares single-input inference in its fingerprint
and invalidates version 1 vectors. The corrected native probe is byte-identical.

The textual search consumes an explicitly supplied result bound to query,
snapshot, document inventory, provider, actual index artifact and immutable
query receipt. Receipts cover the complete ordered ranks and counts; relabeling
a query or reordering rows fails validation. Report publication never replaces
existing bytes and uses atomic exclusive hard links, failing closed when the
filesystem lacks that operation. Verified
exact anchors retain precedence. Remaining candidates use the benchmark's
unchanged `exact-rrf75-25-k60-v1` policy. Stale results produce an explicit gap
and textual fallback; malformed or out-of-inventory results are rejected.
No query implicitly installs, downloads, refreshes or starts an encoder.

The public file request interface and Python API are documented in the
[owning runtime reference](../../../plugins/codebase-map/skills/map-method/references/embeddings.md).
Actual index and query CLI paths passed with the separate local runtime.

## Frozen separate evaluation

The [fixture](../../../evals/codebase-map/retrieval-benchmark/p5_holdout.json)
contains 8 Python files, 24 indexed documents and 20 queries: 8 English,
8 Italian and 4 exact references. Fixture SHA-256:
`7647622bec4220de06eae782b898075603f4fab0bab562cedf04ff10d220eb9b`.
The source and gold were frozen before inference; no ranking parameter was
tuned on this set. Gold and evaluation metadata are outside runtime inventory.

| Query group | Text Recall@5 | Fused Recall@5 | Text MRR@10 | Fused MRR@10 |
| --- | ---: | ---: | ---: | ---: |
| All 20 | 0.8000 | 0.9500 | 0.6367 | 0.8083 |
| English, 8 | 1.0000 | 1.0000 | 0.8000 | 0.8542 |
| Italian, 8 | 0.5000 | 0.8750 | 0.2917 | 0.6667 |
| Exact, 4 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

Mean validated query latency is 0.550 seconds for text and 2.275 seconds for
the composed provider plus text retrieval, with a warm persistent encoder.
Startup takes 2.041 seconds separately. Initial document encoding/indexing
takes 3.692 seconds; unchanged refresh takes 1.490 seconds and encodes **zero**
documents. All 24 cached vectors are reused. A separately rebuilt complete
inventory and every replayed query match, not just a top-k subset.

A separate native incremental exercise changes a function body, renames one
file and deletes another. It encodes 4 inputs, reuses 17, removes 6 old entity
identities and yields 21 documents. Its complete document/vector inventory
and full ranked replay equal a clean rebuild. The original batch-dependent
probe and earlier evaluation are retained; the table reports encoder version 2.

The Italian overdue-invoice request remains at rank 12. Improvement on this
small synthetic corpus does not establish real-project quality. The earlier
development corpus showed a regression with full bodies; both outcomes remain
part of the evidence. R9's whole-flow token/task measurements belong to P10.
Default adoption is therefore not justified.

## Verification and recovery record

The frozen candidate passes 1,537 repository tests, including 26 embedding
regressions, plus common gates, instruction budgets and the five-host build
and reproducibility check. The default interpreter reports 11 expected skips:
9 Codebase Map SDK checks and 1 MOE SDK check pass separately in the prepared
SDK runtime; the POSIX executable-bit check remains unavailable on Windows.
The 3,963 inputs stayed byte-identical through testing; final changes affect
documentation only.
These checks do not establish live execution in all installed hosts.

The independent candidate review found an existing-report overwrite and
acceptance of relabeled/reordered query results. Both were reproduced before
the fixes. Independent premise and reachability checks confirmed the HIGH
overwrite finding. The fixes use exclusive report publication and immutable
query receipts; the regressions and complete suite pass afterward. The original
BLOCK report remains intact beside its separate disposition, preserving the
one-review, one-fix-pass sequence.

The actual shared checkout also passes affected embedding/retrieval suites,
common gates, budgets and the all-host build check. Its first documentation
generation stopped while the other active chat had registered role bodies
that were not yet written. Normal generation succeeded once they existed.
Canonical compiler inputs stayed unchanged during that build; three unrelated
reviewer evaluation scenario files changed concurrently and were preserved.
The complete repository suite certifies the isolated owned candidate. No full
suite or completion claim is made for the other chat's changing feature.

The first evaluation attempt stopped before indexing because root-level
fixture metadata changed the inventory. A regression now excludes all gold and
evaluation metadata. The second attempt correctly rejected an encoder
interpreter with a different parser fingerprint. The final design keeps
snapshot validation in the original map interpreter and isolates only numeric
encoding; it preserves the fingerprint gate.

Run artifacts: `.tritech/daodan/runs/code-context-p5-20261023/`, including
`provider-assessment.json`, `holdout-final-result.json`, public CLI reports, test logs,
source fingerprints and final review. The parent run links this broader-scope
P5 record without changing its immutable original scope. Concurrent edits and
the no-push boundary are preserved.
