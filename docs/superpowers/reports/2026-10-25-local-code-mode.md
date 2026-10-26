# Local Code Mode candidate verification

Original verification: 2026-10-25, based on
`b84d96e9c9c139be7010c09df0f8a849127cd6a5`.
Publication integration: 2026-10-26, based on
`75ab1b1f3b65ae8b6ecd540fa8da8d1ea2f89b71`.
Candidate branch: `feat/local-code-mode`.

## Delivered behavior

The existing Codebase Map stdio server accepts `--code-mode` and exposes
`search(code)` and `execute(code, tools)`. Both derive their operation catalog
from the native MCP registry. Execution dispatches through its public `call_tool`
method, preserving argument validation and the existing project, source and
publication checks. The executor and MCP facade are separate modules owned by
Codebase Map. There is no new cross-plugin dependency or copied Cloudflare code.

Only explicitly annotated read-only operations are available by default. The
startup owner can grant individual mutations with `--code-mode-allow-write NAME`.
Each execution supplies its own narrower list of operation names. Intermediate
results remain in the runtime; the response includes selected JSON, call receipts
and byte/time statistics. Deno is required only for this optional mode.

Codebase Map is prepared as version **8.11.0**, marketplace **42.1.0**. Canonical
source, all five host packages, catalogs and documentation were regenerated
together. The method index is **867 words**, below the current master's unchanged
927-word budget. Integration preserves master's standalone navigation guidance,
retrieval batching and EmbeddingGemma provider. The native MCP registry, service
and wire fixture were unchanged upstream; the Code Mode runtime needed no
adaptation.

## Publication candidate verification

The integrated candidate was checked against master at `75ab1b1f` with Python
3.12.14, Deno 2.9.6, MCP 2.3.0 and PyYAML 6.0.3 where required.

| Check | Observed result |
|---|---|
| Full suite with Deno available | 2,497 tests in 298.169 s; 24 failures, 81 skipped |
| Executor and Code Mode MCP suites | 26 tests in 18.330 s, OK |
| Existing native Codebase Map MCP wire suite | 10 tests in 13.513 s, OK |
| Copilot write-confinement policy | 36/36 passed |
| Dependency graph, bundled paths, host vocabulary, registration, fact anchors | Passed |
| Plugin documentation and Codex instruction parity | Passed |
| Universal build drift/support check | Passed |
| Independent integration review | No actionable findings |

The full suite is **not passing**. All 24 failing subtests were independently
reproduced on an unmodified archive of `75ab1b1f`, running the six affected test
methods (6 tests in 0.949 s, 24 failures). Failure labels and assertion messages
matched the integrated run exactly:

- Three catalog assertions fail because the base Copilot catalog still contains
  `drkerr` 16.7.0. It has 48 plugins while the other explicit catalogs have 47,
  and its marketplace metadata remains 41.3.0. The existing compiler preserves
  this legacy entry; rebuilding reproduces the inconsistency.
- Twenty instruction-budget assertions fail in project-delivery/work-controller
  units and their loop-step closures. None of those sources or caps changed in
  this candidate; Codebase Map's own budget checks pass.
- One Work Controller definition assertion fails because `C:\escape.md` is
  accepted where the test expects `DefinitionError`.

These existing baseline defects remain visible in the draft PR. No test was
weakened, skipped or reclassified to obtain a passing result, and no unrelated
catalog ownership or workflow behavior was changed. The original Code Mode
runtime, MCP adapter and transport tests are byte-identical to the reviewed
candidate below. Integration preserves the newer master runtime and guidance
and regenerates packages with its compiler.

To reproduce the baseline failures from an unmodified checkout of `75ab1b1f`:

```sh
PYTHONPATH=tests python -m unittest \
  test_cutover_identity.CutoverIdentityTests.test_versions_and_plugin_sets_match_across_hosts \
  test_skill_load_budget.SkillLoadBudgetTests.test_every_loop_step_holds_a_bounded_context \
  test_skill_load_budget.SkillLoadBudgetTests.test_every_unit_stays_under_its_cap \
  test_universal_catalog_parity.UniversalCatalogParityTests.test_every_core_plugin_is_in_every_catalog \
  test_universal_catalog_parity.UniversalCatalogParityTests.test_versions_are_identical_across_hosts \
  test_work_controller_definition.DefinitionTests.test_unsafe_paths_and_missing_write_set_are_rejected
```

## Original candidate verification

| Check | Observed result |
|---|---|
| Baseline full suite | 1,955 tests, OK, 70 skipped |
| Final full suite with Deno available | 1,982 tests in 255.394 s, OK, 80 skipped |
| Executor and Code Mode MCP suites with MCP 2.3.0 | 26 tests in 15.825 s, OK |
| Code Mode MCP suite with the declared minimum MCP 2.0.0 | 10 tests in 12.779 s, OK |
| Existing native Codebase Map MCP wire suite, MCP 2.3.0 | 10 tests in 11.063 s, OK |
| Copilot write-confinement policy | 36/36 passed |
| Dependency graph, bundled paths, registration, fact anchors, host vocabulary | All passed |
| Plugin documentation and Codex instruction parity | Passed |
| Universal build drift/support check | Passed |
| Independent review | Material findings fixed and rechecked |

Python was **3.12.14**; the actual JavaScript runtime was **Deno 2.9.6**.
The default suite skips SDK-dependent cases when MCP is absent; the dedicated
SDK runs above exercise those transport cases rather than counting skips as
successful execution. Other optional dependencies remain represented by the
full suite's recorded skips.

The execution tests cover discovery, dependent calls, omission of intermediate
payloads, denied direct filesystem/network/environment/process/FFI access,
forged protocol output, exact capabilities, write denial and startup grants,
schema/path/publication errors, deadlines, limits, fresh state, environment
scrubbing, cancellation and atomic-call completion.

Adversarial review exposed pipe backpressure during process cleanup and after a
final result, plus Unicode serialization errors that could omit earlier call
receipts. Reproducing tests first failed, then passed after draining/reaping was
made cancellation-safe and serialization failures retained the broker ledger.
An actual MCP mutation followed by an invalid Unicode result is also covered:
the error retains its successful receipt and the persisted run remains visible.

The local execution sandbox used for development delayed thread-to-event-loop
wakeups even in a minimal MCP server. The same minimal probe worked immediately
outside that sandbox; real MCP tests therefore ran there. No workaround or SDK
pin was added to Daodan for this environment-specific behavior.

## Catalog size comparison

Measured with MCP 2.3.0 using compact UTF-8 JSON arrays of `list_tools()`
descriptors, serialized with aliases and omitted nulls. All 19 operations were
granted for the comparison so both interfaces could reach the same catalog.

| Interface | Initially exposed tools | Serialized catalog |
|---|---:|---:|
| Native MCP | 19 | 10,552 bytes |
| Code Mode | 2 | 1,473 bytes |

This is an **86.0% reduction in the measured initial descriptor payload**.
It is not a billed-token benchmark or an end-to-end task saving: generated code,
discovery, receipts, final output, retries and host-specific wrapping also count.

## Practical boundaries

The runtime denies permission-gated host I/O and grants only the selected Python
operations. It is not a complete OS sandbox or a multi-tenant execution service;
the V8 old-space setting is not a total process-memory or disk quota. The
30-second JavaScript deadline may be exceeded while an already admitted atomic
operation finishes. Completed writes are not rolled back when later code fails.

The 64 KiB result bound applies to the selected value; receipts are additional,
separately measured output. Host approval of `execute` covers the program as one
call, without separate approvals for its internal operations.

All five host packages were inspected and tested as generated files. No
installed Claude, Codex, Copilot, Pi or OpenCode UI session was exercised. The
tested interaction surface is the real MCP stdio transport. Runtime-dependent
suites remain optional in the repository's standard CI environment;
their explicit reproduction commands are below.

```sh
# Run from the repository, with Deno on PATH or DAODAN_TEST_DENO set.
python -m unittest discover -s tests
# In an environment containing the MCP SDK:
python -m unittest discover -s tests -p 'test_code*mode*.py'
python -m unittest discover -s tests -p 'test_codebase_map_mcp_wire.py'
python scripts/daodan_build.py --check --support
```

Startup and usage examples are in the
[MCP guide](../../../plugins/codebase-map/skills/map-method/references/mcp.md#local-code-mode-opt-in).
