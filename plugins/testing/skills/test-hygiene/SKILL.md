---
name: test-hygiene
description: >
  Binding placement rules, plus the measure, quarantine, consolidate remediation ladder for degraded suites.
  TRIGGER WHEN: creating or placing any test file, choosing between extending an existing test and writing a new one, auditing test-suite health, quarantining failing or flaky tests, or consolidating redundant tests.
  DO NOT TRIGGER WHEN: writing the test content itself (use mattpocock-skills:tdd), browser E2E mechanics like page objects and waiting (use developer-essentials:e2e-testing-patterns).
---

# Test-Suite Hygiene

Rules and workflows that keep a test suite small, trustworthy, and navigable while agents and humans keep adding to it.

## Why suites degrade under agentic coding

For an agent, writing a new test file costs nearly nothing; understanding the existing suite costs context. The dominant strategy becomes "create a new one", and the implicit goal is "task closed, CI green", never "suite healthy". Nobody measures suite health, so nobody optimizes it. The result compounds fast: parallel test files for the same module, the same behavior asserted at three layers, implementation-coupled tests that break on every refactor and get replaced instead of repaired, and skip markers that quietly turn the safety net into decoration. These rules exist to make the healthy move the cheap move.

## The binding rules

Test ownership: source at unit; behavior at integration, contract and e2e.

Full protocol with per-rule detail in `references/prevention-rules.md`. The condensed form:

1. **Search before writing.** Locate the existing owner for the intended layer and behavioral scope, and extend it. A parallel file for the same owner requires a justified scope split.
2. **Deterministic ownership per layer.** Unit tests: one primary test file per source file, mirroring the source path (`src/foo/bar.py` maps to `tests/unit/foo/test_bar.py`), following the project's established convention and documenting justified scope splits. Integration, contract, and e2e tests are behavior-owned: one primary file per behavioral scope (a flow, an endpoint, a contract), legitimately spanning several source modules. The violation at those layers is an unexplained second file for the same scope, not multi-module reach.
3. **Explicit layers** (unit, integration, contract, e2e) with runtime budgets, identified through the project's directories, colocated paths or runner markers. A new test goes in the lowest layer that can prove its contract without hiding the relevant boundary.
4. **Behavior through justified interfaces.** Prefer observable contracts. Internal access, boundary doubles and ordering checks require a named boundary or diagnostic regression; inspect their purpose before rewriting them.
5. **No skip markers to get green.** Classify product, oracle, environment and intermittent failures before repair or accepted temporary quarantine. A tracked reason alone does not justify losing regression protection.

Assertion protection: Preserve assertions for approved behavior; correct a wrong oracle only with independent authority and evidence, while keeping valid product protection active.

Test retirement: Retire tests only for retired behavior or verified equivalent replacement protection in the same candidate; counts, coverage, age and refactoring alone are insufficient.

Refactors, renames and migrations preserve and retarget meaningful protection.
Resource-dependent tests follow the isolation and reproduction checklist in
`references/prevention-rules.md`, rule 9.

## The remediation ladder

When the suite has already degraded, rules alone do not repair it. Bonify in layers, opportunistically, alongside normal development. Full mechanics in `references/remediation-workflow.md`.

1. **Measure first.** `/testing:test-audit` produces a versioned `TEST_AUDIT.md`: counts, runtime, skipped, failing, flaky, orphans, layer distribution, slowest tests, per-module coverage. Metrics guide investigation; they do not establish behavioral value or correctness.
2. **Classify before quarantine.** Load the `testing:test-remediation-method` skill: product defects, wrong oracles, environment failures, intermittence and unknown causes have different owners. Temporary quarantine has explicit evidence, remaining risk, return condition and owner; a green suite alone does not become trustworthy.
3. **Consolidate per module.** Inventory protected behavior, independent failure modes and bugfix provenance before rewrite. Accepted replacements and removal share one candidate and authorized commit.
4. **Verify.** Every protected inventory row maps to a justified surviving check. Coverage and counts support the assessment but cannot prove equivalence.

Order remediation by risk (production bugs, then churn from git log), not by how messy a module looks.

## Layer model and budgets

Defaults; a project's own convention overrides them.

| Layer | Contains | Budget (default) |
|---|---|---|
| `unit` | Isolated behavior, controlled doubles at justified boundaries, no real external I/O | Individual test under 100ms; whole layer under 60s |
| `integration` | Real boundaries (DB, HTTP, filesystem) via containers or fixtures | Whole layer under 5min |
| `e2e` | Critical user flows only | Project-defined runtime budget; justified critical flows and failure modes, no test quota |

A behavior's primary proof lives at ONE layer. Cross-layer overlap is duplication only when two tests protect substantially the same failure mode through the same observable contract without adding independent risk coverage; a calculation checked at unit, its persistence at integration, and the user flow at e2e are three behaviors, not one repeated. A test that crosses a real database boundary belongs in integration. A controlled database-port double can isolate service behavior at unit, but cannot prove SQL, transactions or persistence; those contracts require the real boundary in an appropriate test lane.

## Related knowledge

Required upstream skills need a capability preflight on the active host: resolve
and load the actual installed skill before accepting an action that needs it.
Dependency metadata and five-host rendering do not establish that an external
marketplace runs on all five hosts. If unavailable, record the affected action
open and give the current host's supported installation guidance; do not substitute
another prompt or claim the upstream method ran. Claude-specific install examples
below apply only on that host.

- Writing the test content (red-to-green workflow, behavior-first design, mocking discipline): load the `mattpocock-skills:tdd` skill. It ships in the upstream mattpocock/skills plugin, a hard dependency of this plugin; if it is unavailable, stop and tell the user to install it (`claude plugin marketplace add mattpocock/skills`, then `claude plugin install mattpocock-skills@mattpocock`).
- Browser E2E patterns (page objects, fixtures, waiting, network mocking): load the `developer-essentials:e2e-testing-patterns` skill. It ships in the upstream wshobson/agents marketplace, a hard dependency of this plugin; if it is unavailable, stop and tell the user to install it (`claude plugin marketplace add wshobson/agents`, then `claude plugin install developer-essentials@claude-code-workflows`).
- Runner detection and measurement commands for the audit workflows: `references/runner-playbook.md`.
