# Gutsy Modal CPU Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Execute the approved preliminary routing, compaction and tool-selection cases on Modal CPU and retain reproducible raw responses and measured limits.

**Architecture:** New evaluation-only modules under `evals/gutsy-decision-pilot/` prepare hidden-oracle fixtures locally, submit model inputs to one ephemeral Modal Function running the pinned official Gutsy HTTP service, and score downloaded responses locally. Compaction reconstruction uses the actual pinned upstream library installed in run-owned scratch, not copied into a kernel. Existing task_router remains the selection authority.

**Tech Stack:** Python standard library, existing Modal client 1.5.5, Node.js for upstream fast-jev, remote Gutsy 0.4 and llama-cpp-python CPU runtime.

**Spec:** [Preliminary protocol](gutsy-preliminary-tests-2026-10-26.md) and the user's explicit request to use modal.com on 26 October 2026.

## Global Constraints

- Only new evaluation files, this plan, owned research documents and the owned run may change. Preserve all preexisting unrelated edits. No commits or pushes.
- CPU only; one Q4 model, four threads, four requested/maximum cores, one request at a time. Diagnostic memory cap 2 GiB; report the 1 GiB target separately.
- At most 500 attempted questions and 30 minutes corpus execution. Ephemeral job timeout and max-containers=1 bound remote compute. Record preparation time separately.
- Do not send oracle keys, case IDs or titles to Gutsy. Synthetic operations are data, not executed external actions.
- Use official `/v1/systemone`, verify response.model, preserve raw distributions and failures. Keep raw decisions separate from deterministic protection/fallback.

## Review Focus

- An answer missing or outside its schema must not become a negative classification.
- C01/C02 must have identical upstream state despite different result content, and candidates must not be pinned.
- Tool OR requirements, renamed IDs and deterministic discovery must preserve sufficiency without masking raw omissions.
- A cloud timeout, memory cap or partial output must preserve evidence and remain incomplete.
- A configured model or cache flag is not proof of the model/cache path actually used.

### Task 1: Materialize and verify the three case families

**Files:** Create `routing_cases.py`, `tool_cases.py`, `compaction_cases.py`, `compaction_bridge.mjs` and corresponding focused tests under `evals/gutsy-decision-pilot/`.

**Interfaces:** `build_cases() -> list[dict]` returns id/domain/split/state/questions/oracle. `score_case(case, response) -> dict` scores saved answers, keeping oracle outside inference. Domain-specific `deterministic_checks()` exercises actual owners with fake answers where required.

- [x] Implement fixtures and meaningful checks for partial labels, invalid answers, OR alternatives, aliasing, compaction pairing and pinning.
- [x] Run the new unit checks; verify exact case coverage and the state collision.
- [x] Review the exact frozen model-input bundle before remote execution.

### Task 2: Execute through the official service on Modal

**Files:** Create `pilot.py`, `modal_pilot.py`, and `test_pilot.py` in the evaluation directory.

**Interfaces:** preparation writes immutable input and oracle artifacts separately; the Modal Function consumes only state/questions/model plus opaque response-routing IDs outside the model body and returns raw HTTP responses, timings, runtime identities and memory. The local scorer consumes these records and the frozen cases.

- [x] Implement input/response validation, count/time bounds, scoped artifact writes and raw-output preservation.
- [x] Build the CPU-only image using pinned upstream sources and weights; start the service only on container loopback.
- [x] Execute R01/C01/T01 first; after successful service checks continue the frozen corpus within the same bounded run.
- [x] Save failed attempts explicitly and diagnose environment errors without altering the test oracle.

### Task 3: Verify and report

**Files:** Create evaluation README and run-owned `REPORT.md`, raw result JSON and reproducibility manifest; update owned research links/status only as supported by evidence.

- [x] Score each domain separately with actual task_router and fast-jev reconstruction.
- [x] Review case coverage, critical omissions, fallback contribution and complete-decision latency/RAM.
- [x] Report limits and incomplete checks candidly; retain the ephemeral Modal app identifier and confirm it stopped.

Execution is authorized by the user's current request. The earlier analysis-only restriction is superseded for this bounded evaluation; training and production integration remain outside scope.
