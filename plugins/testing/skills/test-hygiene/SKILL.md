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
2. **Deterministic ownership per layer.** Unit tests: one test file per source file, mirroring the source path (`src/foo/bar.py` maps to `tests/unit/foo/test_bar.py`), following the project's established convention. Integration, contract, and e2e tests are behavior-owned: one file per behavioral scope (a flow, an endpoint, a contract), legitimately spanning several source modules. The violation at those layers is an unexplained second file for the same scope, not multi-module reach.
3. **Explicit layers** (unit, integration, e2e), each in its own directory with a runtime budget. A new test goes in the lowest layer that can express the behavior.
4. **Behavior, not implementation.** Test through public interfaces. A refactor that preserves behavior must not break tests.
5. **No skip markers to get green.** Fix the test, or quarantine it with a tracked reason.
6. **Never weaken an assertion** to make a failing test pass. A failing assertion is a signal about the code, not an obstacle in the test.
7. **Retire tests only with retired behavior**, in the same commit. Refactors, renames and migrations preserve and retarget meaningful protection.

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
| `unit` | Pure logic, no I/O, no mocks of internal modules | Individual test under 100ms; whole layer under 60s |
| `integration` | Real boundaries (DB, HTTP, filesystem) via containers or fixtures | Whole layer under 5min |
| `e2e` | Critical user flows only | Project-defined runtime budget; justified critical flows and failure modes, no test quota |

A behavior's primary proof lives at ONE layer. Cross-layer overlap is duplication only when two tests protect substantially the same failure mode through the same observable contract without adding independent risk coverage; a calculation checked at unit, its persistence at integration, and the user flow at e2e are three behaviors, not one repeated. When a unit test needs a database, it is an integration test in the wrong directory; move it instead of mocking the database.

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
