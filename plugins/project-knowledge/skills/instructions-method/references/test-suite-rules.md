# Condensed test-suite rules

Locally authored policy distilled from this marketplace's testing methods.
This block is self-contained for the target project. Procedure, runner choices,
quarantine and consolidation belong to testing, rather than instruction files.

Offer the block when tests exist or are explicitly planned. Preserve equivalent
project rules and flag inverted or weakened obligations. A project without tests
does not receive a finding solely because this block is absent.

## Project-derived policy completeness

Before publishing test guidance, confirm these facts from the project's approved
decisions, configured tooling and observed checks. Keep detailed procedures in the
existing testing guide and reference its actual owner. Missing information is a
gap to resolve, not permission to invent a default.

- Exact permitted commands, working directories, runner/configuration and required
  runtime versions; identify which are local checks and which are CI gates.
- Prerequisites for each lane: services, fixtures, migrations, browser/application
  startup and approved credentials. A local integration environment and production
  schema verification are distinct checks; inaccessible production remains open.
- Established test layers and placement conventions, behavior/oracle authority,
  boundary-double policy and the lanes that exercise real persistence or protocols.
- Isolation and cleanup obligations for resource-dependent tests, including clocks,
  randomness, environment, filesystem/database state and async work where relevant.
  Keep the detailed checklist and failure procedure with testing's canonical owner.
- Failure classification, approved quarantine/skip conditions, retained regression
  protection and verified equivalent replacement before consolidation or retirement.
- Measured runtime or coverage/mutation targets and their configured enforcement,
  when the project has approved them. Counts and a template threshold do not prove
  meaningful protection. Record commands not run and prerequisites not available.

## Reusable instruction block

```markdown
## Test-Suite Rules

Test ownership: source at unit; behavior at integration, contract and e2e.
Assertion protection: Preserve assertions for approved behavior; correct a wrong oracle only with independent authority and evidence, while keeping valid product protection active.
Test retirement: Retire tests only for retired behavior or verified equivalent replacement protection in the same candidate; counts, coverage, age and refactoring alone are insufficient.

1. Search before writing: find the existing owner for the intended layer and behavioral scope, and extend it. A parallel file for the same owner requires a justified scope split.
2. Unit tests mirror source ownership (for example `src/foo/bar.py` maps to `tests/unit/foo/test_bar.py`), following this project's convention. Integration, contract and e2e tests belong to a flow, endpoint or contract and may span several source modules.
3. Keep layers explicit through established directories, colocated paths or runner markers. Use measured runtime budgets. Choose the lowest layer that protects the required behavior; unit coverage does not replace a distinct integration or contract check.
4. Prefer observable contracts. Internal access, interaction/order assertions and boundary doubles require a meaningful boundary or diagnostic regression purpose; a repository-owned IO adapter may be such a boundary. A mocked adapter does not verify real persistence or wire behavior.
5. Classify product defects, wrong oracles, environment failures and intermittence before suppressing a test. Do not skip or weaken checks to make CI pass. Legitimate platform/feature conditions and quarantine follow the project's tracked policy, with active protection and restoration obligations preserved.
6. Derive expected results from independent approved authority. Follow Assertion protection when correcting an expectation; changing code and its oracle together cannot establish correctness.
7. Follow Test retirement before consolidation or removal. Refactors, renames and migrations preserve and retarget meaningful outcomes and independent failure modes.
8. Resource-dependent tests control incidental time, randomness and environment, isolate mutable filesystem/database state and release fixtures, async work and handles on every exit. The project's testing guide records permitted real services, setup and cleanup.
```
