# Codebase Map MCP Implementation Plan

> **For agentic workers:** Use the native session with parallel ownership of the service and export tests, then independent whole-change review.

**Goal:** Provide the Daodan-side local Codebase Map MCP for native Tri-Tech integration.

**Architecture:** One project-bound standard-library service reuses canonical helpers and state. A thin official SDK stdio server exposes typed tools and request progress. Tri-Tech remains the executor and UI owner.

**Tech Stack:** Python 3.11+, standard library service, official `mcp>=2.0.0,<3` runtime SDK.

**Spec:** `docs/superpowers/specs/2026-10-16-codebase-map-mcp-design.md`.

## Global constraints

- Keep the compiler and default unit suite standard-library-only.
- Preserve canonical `.codebase-map/` artifacts, migration and delivery gates.
- Add no autonomous LLM runner or application-specific storage path.
- Update the kernel and regenerate all five hosts together.
- Preserve preexisting untracked outputs and unrelated work.

## Review focus

- Foreign project, path traversal and symlink/junction requests must fail before I/O.
- Concurrent mutations must not lose events or overwrite run state.
- Failed/partial operations must never claim a completed analysis.
- Direct worker changes remain visible in canonical status.
- MCP stdout carries protocol traffic only, and context is absent from tool schemas.

## Task 1: Reusable project service

**Files:** `plugins/codebase-map/skills/map-method/scripts/mcp_service.py`, `tests/test_codebase_map_mcp.py`.

- [ ] Write failing behavioral tests for binding, run preparation, source queries,
  freshness, phase checkpoints, cursor replay, resume and publication.
- [ ] Implement `MapService(project_root)` using existing snapshot/source helpers.
- [ ] Verify realistic invalid inputs and concurrent event writes.
- [ ] Deliver the service interface and test results to the coordinator.

## Task 2: MCP transport and five-host distribution

**Files:** `plugins/codebase-map/skills/map-method/scripts/mcp_server.py`,
`plugins/codebase-map/plugin.toml`, `tests/test_daodan_mcp.py`,
`tests/test_codebase_map_mcp_wire.py`.

- [ ] Add failing rendering tests for all five hosts and negative capabilities.
- [ ] Bind typed tools to the service through the official SDK; offload blocking
  work and emit request-scoped progress without persisting another run status.
- [ ] Exercise the actual SDK server over stdio, including error and progress paths.
- [ ] Declare the server, bump versions and regenerate packages and documentation.

## Task 3: Candidate verification and delivery

**Files:** method reference, generated plugin docs, host docs and canonical repository instructions.

- [ ] Document the exact startup, API, event and ownership contracts.
- [ ] Run full unit suite, repository linters, guard, parity and version checks.
- [ ] Review the candidate independently and repair verified findings.
- [ ] Commit and push the verified kernel, generated output and documentation
  together, following the repository publication instructions.
