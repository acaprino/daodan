# Codebase Map binary storage: release evidence

Map 7.0.0 / marketplace 35.0.0 ships in commit
`1434073fcb9c627a42e9127bf78f0b4d95646ddb`. The
[official release](https://github.com/acaprino/daodan/releases/tag/v35.0.0)
was published on 2026-10-16T20:21:00Z; tag, commit and publication time were
verified through GitHub's release API on 16 October 2026.

## Delivered contract

New snapshots default to SQLite; explicit JSON remains an upstream compatibility
option. Run state binds format, path and storage version. Legacy JSON and mixed
parent/child formats remain readable under their provenance rules, without
rewriting parent evidence. Binary storage does not replace the separate parser,
source-freshness and delivery checks.

`SnapshotStore` and the progressive writer persist records and release per-file
payloads. Semantic resolution, graph metrics and bounded source queries consume
persistent indexes. JSON queries may derive a temporary operation-owned index.
Logical digests preserve their historical canonical projections; artifact
SHA-256 identifies the actual file bytes. Reports remain Markdown and the model
receives selected text with totals, explicit truncation and coverage.

## Checks already executed

The local full suite ran 1,280 tests in 970.903 s, initially reporting 7 failures,
18 errors and 1 skip. Twenty-three outcomes came from JSON fixtures that had not
selected JSON explicitly; two came from incomplete Pi/OpenCode catalog
publication after a Windows file-sharing error. The fixtures were corrected,
all five hosts regenerated successfully, and `--check` passed.

Targeted reruns passed 40 storage/affected-fixture tests in 35.270 s and 88
query, run-control, MCP and export tests in 169.303 s. Decoder tests cover JSON
chunk boundaries, duplicate members, non-finite constants and numeric overflow.
Independent review found no remaining upstream finding in the reviewed change.

The published commit has successful
[consistency](https://github.com/acaprino/daodan/actions/runs/38961360006) and
[publish-marketplaces](https://github.com/acaprino/daodan/actions/runs/38961359992)
CI runs, including the publication workflow's full suite, documentation/instruction
parity and deterministic five-host reproduction. These runs are separate from
the earlier local results; the local skip is not represented as a passed test.

## Limits

Compiler/export checks do not prove that all five installed hosts executed an
analysis. No new LLM analysis or model-token saving is claimed. SQLite indexes
can increase disk size; storage bytes alone establish no token percentage or
latency improvement. Consumer applications still own importing this release,
adapting their bindings and qualifying their actual runtime/candidate.

Only narrative documentation is updated after this release. Generated reference
blocks, exports, package manifests and the release tag are not edited by hand.
