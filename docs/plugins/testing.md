# Testing Plugin

> Test-suite hygiene and generation toolkit: binding rules for where tests go and when to create them, a whole-suite auditor, gated quarantine and consolidation workflows, and a behavior-driven test-writer.

## Required dependencies

The shared local protocol owns run identity, snapshots, delivery accounting and
candidate gates. The two upstream methods below must resolve on the active host
before an action needs them. The install examples apply to Claude; generated
packages alone do not establish upstream availability on every host.

Both are upstream plugins, delegated as of marketplace 18.0.0 (the local vendored copies of `tdd` and `e2e-testing-patterns` were removed):

```bash
claude plugin marketplace add mattpocock/skills
claude plugin install mattpocock-skills@mattpocock

claude plugin marketplace add wshobson/agents
claude plugin install developer-essentials@claude-code-workflows
```

| Dependency | Provides | Referenced as |
|---|---|---|
| [mattpocock/skills](https://github.com/mattpocock/skills) | Language-agnostic TDD methodology (red-to-green workflow, behavior-first tests, mocking discipline) | `mattpocock-skills:tdd` |
| [wshobson/agents](https://github.com/wshobson/agents) | Playwright/Cypress E2E patterns (page objects, fixtures, waiting, network mocking, visual regression) | `developer-essentials:e2e-testing-patterns` |

Both upstreams are multi-skill bundles, so the install brings companion skills along.

## Agents

### `test-writer`

Generates focused, behavior-driven test suites or guides interactive TDD sessions. Works with any language and test framework.

| | |
|---|---|
| **Model** | inherit |
| **Use for** | Writing tests for existing code, TDD for new features |
| **Modes** | Generate (write complete test suite) or Interactive TDD (guide red-green-refactor cycle) |

Search for the existing owner at the intended layer before writing. Unit ownership follows source; integration, contract and e2e ownership follows behavior. Oracles require a requirement or independent evidence. Parallel owners, skips to get green and unsupported weakened assertions are anti-patterns.

### `test-suite-auditor`

Adversarial whole-suite hygiene auditor. Report-only: it never edits, moves, or deletes.

| | |
|---|---|
| **Model** | inherit |
| **Use for** | Test-suite audits, flaky/dead test detection, redundancy and layer assessment |
| **Wired into** | `/testing:test-audit`, and senior-review's testing-quality dimension (`/senior-review:team-review`, `/senior-review:code-review` Agent F), which runs whenever the change touches test files |

Nine detection dimensions: inventory and layer distribution, orphan tests, skipped and disabled, failing and flaky, duplicate coverage, contradictory tests, implementation-coupled tests, never-failing tests, runtime and coverage distribution. Every finding carries evidence (`file:line` or command output) and a fix path pointing at the quarantine or consolidation workflow.

---

## Skills

### `test-hygiene`

The plugin's knowledge base: why suites degrade under agentic coding, the 7 binding rules, the remediation ladder, and the layer model with runtime budgets.

| | |
|---|---|
| **Trigger** | Creating or placing test files, auditing suite health, quarantining, consolidating |

**Reference docs included:**

| Reference | Content |
|-----------|---------|
| `prevention-rules.md` | The full ruleset: search-before-write protocol, mirror-the-source placement, one file per source, layers with budgets, behavior over implementation, no skip markers, assertion integrity, delete with the feature |
| `remediation-workflow.md` | TEST_AUDIT.md format, quarantine protocol and lifecycle, per-module consolidation, safety-net e2e tests, mutation-testing guidance (weekly job, no runner shipped) |
| `runner-playbook.md` | Per-runner detection and measurement commands (pytest, Vitest, Jest, Mocha, go test, cargo test, JUnit, dotnet, RSpec, PHPUnit) plus flaky-detection methods |

`test-preparation` exposes runner/configuration/source mapping to coordinators.
Missing runners or suites produce diagnosis and configuration/authoring actions.
`test-remediation-method` classifies product defect, disproven oracle, environment,
flakiness and unknown causes before selecting a remedy. Quarantine records evidence,
owner, residual protection and return condition. A green suite is not sufficient
evidence of a trustworthy suite.

---

## Commands

### `/testing:test-audit`

Whole-suite health audit producing a versioned `TEST_AUDIT.md`: inventory, runtime, skipped, failing, flaky, orphan and layer evidence, with unavailable measurements declared. `--fix` uses the canonical diagnosis and remediation method, rather than treating a failing test as automatically disposable. Actual product regressions stay protected. Authorized quarantine records risk and return conditions; failure recovery preserves existing and foreign edits.

```
/testing:test-audit [path] [--fix] [--yes] [--no-run] [--runner <cmd>] [--scope <subpath>]
```

### `/testing:test-consolidate`

Consolidation inventories behavior, independent failure modes and regression provenance before rewriting. Every surviving protection has a justified owner at its layer. Replacement and retirement share one authorized candidate and commit; unresolved meaning remains open. Counts and line coverage guide investigation and do not prove equivalence. Refactors and migrations retarget meaningful protection instead of retiring it solely because its original file moved.

```
/testing:test-consolidate <module-path> [--runner <cmd>] [--coverage-cmd <cmd>] [--dry-run]
```

---

**Related:** [python-development](python-development.md) (Python-specific pytest techniques) | [senior-review](senior-review.md) (hard-depends on this plugin and dispatches `test-suite-auditor` for relevant test changes) | [project-knowledge](project-knowledge.md) (offers condensed rules for scoped project instructions, preserving equivalent existing policy)
