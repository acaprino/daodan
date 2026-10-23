# Python resolver delivery verification

Date: 2026-10-22. Verification updated: 2026-10-23. Scope: the Python prerequisite and optional Jedi engine in
[design §3.2.2](../specs/2026-10-19-graph-grounded-economy-routing-design.md#322-livello-di-risoluzione-engine-opzionali-sondati-identità-del-resolver-e-parser-dichiarati).
The user selected stopping at the Python delivery. Changes remain uncommitted;
no push was performed. Concurrent work in other plugins is outside this delivery.

The [sequential retry](#sequential-retry-on-2026-10-23) below records the final
live-tree verification. It supersedes the earlier incomplete test runs and live
documentation/export drift. The isolated candidate's historical results remain
separate.

## Delivered behavior

- Python keeps stdlib `ast`, requires Python 3.12 or newer at its entry points,
  records nested and conditional definitions, and recovers only definitions
  closed by a parseable prefix. Recovered files retain `parse-error` status.
- `resolution.py` owns the policy shared by the in-memory and SQLite graphs
  (`RESOLVER_VERSION = 3`). Python inheritance uses C3 over a wholly known,
  bounded project hierarchy. The earlier breadth-first search could choose the
  wrong method under multiple inheritance, so the rule was redesigned. Unknown
  bases, conflicting bindings, decorators and attribute writes prevent false
  confirmation. Module attributes require verified project module bindings.
- `resolve_edges.py` probes Jedi readiness, distinguishes selected references
  from actual requests, and confirms only a unique declaration with matching
  name, kind and exact name position. Unicode and multiline callees are covered.
  Divergent answers remain candidates. Every inventoried source must match its
  snapshot hash both before inference and before publication.
- Derived edges remain separate from the read-only snapshot and are bound to
  its digest, parser fingerprint and resolver version. Output aliases cannot
  overwrite the snapshot or inventoried sources; failed writes preserve prior
  output. Environment selection prefers populated offers over installer-only
  stubs, reports interpreter/package evidence, and confines fallback paths to
  the selected environment.

The [measurement ledger](../../../evals/codebase-map/resolver-spike/RESULTS.md)
also publishes retained cross-language campaign results and their limits. This
does not integrate those engines or decide Rust/Go OP-1 and OP-2.

## Real engine exercise

The final local pass used CPython 3.13.14 for snapshot and helper, Jedi 0.20.1,
and an explicitly offered cached environment running Python 3.11.15 with Jedi
and Parso. The engine environment is distinct from the helper's required
interpreter. These are static definition queries, not application runtime or
installed-host workflow coverage. Other verification processes were running,
so the timings do not represent isolated performance measurements.

| Observation | Result |
|---|---:|
| Inventoried source files / hash checks before and after | 40 / 40 / 40 |
| Python unresolved population / selected / actual requests | 6,107 / 200 / 158 |
| Dynamic callees excluded from requests | 42 |
| Confirmed / candidates / unverified positions | 2 / 0 / 0 |
| External definitions / unresolved answers | 141 / 15 |
| Probe and initialization / inference / total elapsed | 4.16 s / 59.84 s / 68.32 s |
| Mean / nearest-rank p95 request latency | 378.7 ms / 776.7 ms |
| Snapshot bytes unchanged; derived store binding accepted | Yes |

Both confirmed edges were read at source and target:

- `analyze_file.py:117`, `manifest.has_file(relative_path)`, reaches
  `snapshot_store.py:168`, `SnapshotStore.has_file`.
- `ast_parser.py:53`, `adapter.parse(content, str(file_path))`, reaches
  `languages/base.py:270`, `LanguageAdapter.parse`. This is a protocol contract;
  it does not identify a concrete implementation.

A separate two-file fixture also resolved an annotated receiver to
`tool.py::function@2:4`, accepted the derived-store binding and preserved all
snapshot bytes.

The report's inference-only extrapolation is 38.55 minutes, assuming one request
per population reference at the observed mean cost. References are sorted by
identifier, selected with stride 1, and truncated at 200. This deterministic
sample favors its first files and call shapes; 42 selected dynamic calls receive
no request. The estimate excludes readiness, source validation, grading and
writing, and is not a representative population forecast.

## Verification

Final scoped and repository check results are recorded below. Native grammar
checks used the existing Tree-sitter language-pack 1.13.5 cache; no dependency
installation was required.

| Check | Result |
|---|---|
| `test_xray_*.py` | 486 tests; one temporary-path false failure, then that exact test passed with neutral TEMP |
| Final Python extraction cases | 8 passed |
| `test_codebase_map_*.py` | Resumed shard interrupted after Windows resource exhaustion stalled it; no final test result |
| Final `test_codebase_map_resolve_edges.py` | 42 tests in 72.739 s, OK, one platform hardlink skip; includes final timing and extrapolation assertions |
| Five-host build | Exit 0 |
| Five-host reproducibility check | Exit 1: only concurrent `senior-review` drift in all five exports; no Codebase Map drift |
| Dependency graph, bundled paths, plugin registration, host vocabulary, fact anchors | Passed |
| Codex instruction parity | Passed |
| Generated plugin documentation | Drift in catalog and daodan/platform-engineering/project-protocol/react-development/senior-review/testing guides; no Codebase Map guide drift |
| Remaining repository tests (`other`) | Incomplete: Windows memory exhaustion interrupted unittest while formatting an error; no final test count or identifiable originating test |

The xray failure came from placing TEMP beneath `.daodan`: an existing test
rejects any result path containing `/.daodan/`, including the fixture's absolute
parent. Its focused rerun passed after changing TEMP. The resumed repository
shard used neutral TEMP; its `MemoryError` is a separate environment failure.
The stalled Codebase Map rerun was stopped without terminating unrelated
processes. The final focused resolver suite then passed in a sequential run.
Neither interrupted broad suite is reported as passing. These results do not establish
repository-wide publication readiness or live execution on the five hosts.

Local raw evidence remains under `.daodan/resume-code-graph/`, including
`plugin-engine-report.json`, `real-engine-report.json`, `live-engine-final.log`,
`xray-final.log`, `codebase-map-final-resumed.log` and `other-resumed.log`.
Those ignored files are not available in a fresh clone. The checked-in tests
retain the reproducible behavioral cases.

| Final source | SHA-256 |
|---|---|
| `scripts/resolution.py` | `fb21e988d802f590b15aca567292b50b94e37d465b3389b854e9e2181d26980d` |
| `scripts/resolve_edges.py` | `202e3896dde85103f7be8c2b544c87dc6ff62dbaf7635f507cc7e427e18cda43` |
| `scripts/languages/python.py` | `154196a737d880518322ba071fb653a0e401b484407f9bb7652247f436c2eaab` |

Paths in the identity table are relative to
`plugins/codebase-map/skills/map-method/`.

## Remaining boundaries

`edit-impact` and `stale-callers` still consume the lexical graph; no map
consumer reads `engine-edges.sqlite` yet. Parser-unavailable status and labeled
parser exceptions remain future work. No TypeScript, JavaScript, Rust, Go or
Java engine is integrated. The hardlink-alias regression can be skipped when
the Windows sandbox denies creating a hardlink; such a skip is not execution
evidence for that platform operation.

## Isolated publication check on Python 3.12

The publication candidate was reconstructed from `849797ac` with only the Python
changes, preserving concurrent work in other plugins and shared documents.
`analyze_file.py` and `doc_review.py` now also carry the PEP 723 interpreter
requirement. A regression checks the five entry scripts' managed-interpreter
metadata.

The Python 3.12 parser suite passed 32 tests with 18 optional-parser skips; the
lexical resolver suite passed 36 tests with four optional-parser skips; the Jedi
engine suite passed all 42 tests. Sandbox attempts affected by temporary-file
permissions, memory exhaustion and thread creation are excluded from these pass
results. Resolver suites were rerun sequentially outside the sandbox.

The isolated five-host build and reproducibility check passed. Dependency graph,
bundled paths, host vocabulary, registration, fact anchors, generated plugin docs
and Codex instruction parity passed. The fact check required a local Git inventory
for the isolated copy, then scanned 3,285 files and verified all ten anchors.

Four budget assertions still fail on the candidate's unchanged senior-review
sources: preparation/dispatch (8,329 words versus 7,985), consolidation (2,124
versus 2,020), verification-panel (640 versus 535), and team-review preparation
(3,474 versus 3,130). Git comparison confirmed no candidate changes to those
sources or `test_skill_load_budget.py` relative to `849797ac`. These required
failures block publication; no commit or push was performed. The broader suite
was stopped after this blocker was confirmed and is not reported as passing.

Concurrent timing-report changes arrived after the isolated candidate was frozen.
They were preserved; their updated timing/extrapolation regression passed on the
live source under Python 3.12. The live analyze-file, documentation-review and
engine scripts match their compiler-generated copies on all five hosts. The
isolated suite results above do not certify unrelated concurrent edits.

## Sequential retry on 2026-10-23

The retry exercised the live working tree based on `849797ac`, using CPython
3.13.14 and the existing native grammar cache. The three core source hashes in
the identity table above are unchanged. No kernel or test correction was needed.
No commit or push was performed.

A single-process Codebase Map attempt reproduced `MemoryError` in a subprocess
reader thread and was stopped. Verification then ran each of the 88 test files
in a fresh process, sequentially. Every module completed; its test-file hash
matched before and after execution. This establishes the per-module results
below; the single-process attempt remains a recorded environment failure.

| Group | Collected | Final passed | Final skipped |
|---|---:|---:|---:|
| `test_codebase_map_*.py`, 17 modules | 303 | 295 | 8 |
| `test_xray_*.py`, 17 modules | 488 | 488 | 0 |
| Remaining `test_*.py`, 54 modules | 808 | 806 | 2 |
| Total distinct unittest cases | **1,599** | **1,589** | **10** |

The initial per-module run had six failures and three errors in temporary-fixture
setup: the sandbox denied hardlinks, junctions or Node temporary-directory
creation. Nine affected cases and five permission-related skips were rerun
together outside the sandbox: **14 tests passed, no failures, errors or skips**.
These tests use newly created owned temporary fixtures; transport calls are
mocked, and no external model, network request or real MCP server is invoked.
The table counts these cases once, using their verified final outcome. The
OpenCode wrapper also passed its JavaScript loader suite on that rerun.

The remaining skips are eight Codebase Map wire tests and one MoE MCP test
requiring the actual MCP SDK runtime, plus one POSIX executable-mode test that
does not apply on Windows. They are not execution evidence. The Codebase Map
output-hardlink regression was successfully exercised in this retry.

All nine repository gates passed, each in its own sequential process:

- Dependency graph, bundled paths, host vocabulary, plugin registration and
  fact anchors.
- `sync_plugin_docs.py --check` and `sync_codex_instructions.py --check`.
- `daodan_build.py --check --support` for all five hosts, with no drift.
- `adapters/copilot/policies/xray-guard/test_xray_guard.py`: 36/36 policy cases.

The live tree's four skill-budget tests and all 57 task-router tests also passed.
Those fresh results supersede the earlier live blockers; the older isolated
candidate still has its separately recorded failures. Compiler and contract
tests do not establish installed-host workflow execution.

Local evidence under `.daodan/resume-code-graph/`:

- `retry-20261023-codebase-map.log`: interrupted single-process attempt.
- `retry-20261023-modules/{codebase-map,xray,other}/summary.json`: per-module
  results, counts, durations and test-file hashes, with adjacent logs.
- `retry-20261023-permissions.log`: the 14 successful scoped reruns.
- `retry-20261023-gates/summary.json`: exact gate commands and exit codes, with
  adjacent logs.

The ignored verification helpers and logs remain local. The checked-in test
files are the reproducible cases; no test assertion or required gate was removed
or weakened to obtain these results.
