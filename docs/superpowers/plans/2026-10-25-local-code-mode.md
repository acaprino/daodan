# Local Code Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Add local progressive discovery and sandboxed JavaScript composition to Codebase Map's existing MCP service.

**Architecture:** An opt-in startup mode exposes two tools over the existing native registry. A Python broker runs a Deno Worker with denied I/O and dispatches permitted calls through the existing MCP validation path. MapService remains the canonical owner of operation semantics.

**Tech Stack:** Python 3.12 standard library, existing MCP Python SDK 2.x, Deno 2.4+.

**Spec:** `docs/superpowers/specs/2026-10-25-local-code-mode-design.md`

## Global Constraints

- No Cloudflare dependency, copied upstream code, compiler framework, GPU or extra model.
- Default native MCP interface remains compatible; Code Mode is explicit startup configuration.
- All runtime files ship under `plugins/codebase-map/skills/map-method/`.
- Use existing registered schemas and `MCPServer.call_tool`, never an alternate operation catalog or unrestricted MapService reflection.
- Write grants are immutable startup names, never a model-supplied authorization flag.
- Rebuild every host and update the changed plugin/marketplace versions together.

## Review Focus

- Project-controlled runtime paths or inherited Deno permission broker configuration must not grant code host access.
- Forged stdout and duplicate or malformed protocol requests must not be admitted as completed operations.
- Failed, timed-out or cancelled executions must report admitted operations and stop additional calls.
- Optional runtime absence must not break native startup or the standard-library build/test suite.
- Generated exports, installation guidance and actual MCP wire behavior must agree about the selected mode.

## Task 1: Bounded local executor

**Files:** create `plugins/codebase-map/skills/map-method/scripts/code_mode.py`, `code_mode_runner.js` beside it, and `tests/test_code_mode.py`.

**Interfaces:** `DenoExecutor(deno=None, limits=None)` validates its runtime;
`await executor.run(code, catalog=..., call_tool=..., allowed_tools=...)` returns
the selected value, broker receipts and measured counts. `CodeModeError` reports
failure and admitted call receipts. `Limits` pins runtime budgets and permits
smaller test limits.

- [x] Write tests for real two-call composition, intermediate exclusion, forbidden I/O and writes, explicit output/call limits, loops, protocol failures and independent executions. Run them before implementation and record the expected missing-feature failure.
- [x] Implement the fixed runner and standard-library broker with bounded streams, validated messages and cleanup. Reject unsafe runtime selection and inherited configuration.
- [x] Run `python -m unittest discover -s tests -p 'test_code_mode.py'`; repeat with the real Deno executable in `DAODAN_TEST_DENO`. Every runtime-dependent case must run in the provisioned verification environment.

## Task 2: Existing MCP registry integration

**Files:** modify `plugins/codebase-map/skills/map-method/scripts/mcp_server.py`; create `code_mode_mcp.py` beside it and `tests/test_code_mode_mcp.py`.

**Interfaces:** keep `create_server(project, store=None)` unchanged. The CLI
wraps its result with async `create_code_mode_server(native, executor,
allow_writes=())` only when requested. This keeps asynchronous SDK catalog loading
out of the synchronous native factory. Code Mode derives permitted descriptors
from `list_tools()` and dispatches through `call_tool()`. Its only public tools
are `search(code)` and `execute(code, tools)`.

- [x] Write real SDK tests for the two-tool surface, selected schemas, normal native startup, actual source-reading composition, validation/path failures, write denial and explicitly granted run creation/publication refusal. Run and observe failure before modifying the integration.
- [x] Implement the adapter and CLI options. Preserve upstream atomic-call behavior and account for caught failures. Add tests for timeout during an admitted operation and for missing Deno.
- [x] Run executor tests plus MCP tests and the existing `test_codebase_map_mcp_wire.py` with the real SDK environment.

## Task 3: Shipped contract and candidate verification

**Files:** owning skill/reference, `plugin.toml`, README inspiration, canonical upstream watch, host/plugin docs, generated catalogs and exports, and package contract tests.

- [x] Document the consumption path, install/startup commands, writes, limits and clear distinction between package checks and installed-host execution.
- [x] Add a packaging regression for runtime files in all five hosts. Record Cloudflare inspiration at the inspected commit without vendoring.
- [x] Bump Codebase Map minor and marketplace minor versions; regenerate all packages, plugin docs and native instruction copies.
- [x] Run the full suite, SDK wire checks, required repository linters, parity/build checks and scoped version checks. Record baseline failures separately.
- [x] Obtain an independent whole-candidate review and fix material defects with reproducing tests.
- [x] Preserve the complete candidate as one reviewable change; publish to a shared branch only with the task's authorization.

## Verification record

See [the candidate verification report](../reports/2026-10-25-local-code-mode.md)
for the tested runtimes, complete suite results, review fixes and the measured
catalog size comparison. Native installed-host execution remains a separate gate.
