# Testing Plugin

> Test-suite hygiene and generation toolkit: binding rules for where tests go and when to create them, a whole-suite auditor, gated quarantine and consolidation workflows, and a behavior-driven test-writer.

Command examples and named tools in this guide use Claude notation. For other
hosts, use the entry points and bindings in the source-derived reference below
and [host setup](../hosts.md).

## Required dependencies

The required [project-protocol](project-protocol.md) plugin owns run identity,
snapshots, delivery accounting and candidate gates. The two upstream methods below must resolve on the active host
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
| `prevention-rules.md` | Search before writing; one deterministic unit-test owner per source file; integration, contract and e2e owners by behavioral scope; layer budgets, behavioral oracles, no skip markers and assertion integrity |
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

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `3.0.1`. **Source:** [plugin.toml](<../../plugins/testing/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | [project-protocol](<project-protocol.md>) |
| Direct external | `developer-essentials@claude-code-workflows`, `mattpocock-skills@mattpocock` |
| Local closure (2) | [project-protocol](<project-protocol.md>), [testing](<testing.md>) |
| External closure (2) | `developer-essentials@claude-code-workflows`, `mattpocock-skills@mattpocock` |

External bundles are separate upstream installations, not copied local skills.
See [host setup](<../hosts.md>) for selection and availability requirements.

**Required capabilities:** `repository.read`, `shell.execute`, `repository.write`, `contexts.isolate`, `roles.dispatch`.
**Optional capabilities:** `execution.parallel`.
Optional capabilities are host mechanisms, not optional local plugin dependencies.

### Registered components

Names below are kernel IDs. Host entry points and paths follow the adapter
mapping in [the host reference](<../hosts.md>).
The source links carry the complete instructions and accepted arguments.

| Kind | ID | Purpose and trigger | Source |
|---|---|---|---|
| Skill | `testing:test-hygiene` | Binding placement rules, plus the measure, quarantine, consolidate remediation ladder for degraded suites. TRIGGER WHEN: creating or placing any test file, choosing between extending an existing test and writing a new one, auditing test-suite health, quarantining failing or flaky tests, or consolidating redundant tests. DO NOT TRIGGER WHEN: writing the test content itself (use mattpocock-skills:tdd), browser E2E mechanics like page objects and waiting (use developer-essentials:e2e-testing-patterns). | [test-hygiene](<../../plugins/testing/skills/test-hygiene/SKILL.md>) |
| Skill | `testing:test-preparation` | Prepare existing test-auditor inputs, runner/configuration diagnosis and snapshot-bound baseline evidence. | [test-preparation](<../../plugins/testing/skills/test-preparation/SKILL.md>) |
| Skill | `testing:test-remediation-method` | Classify test failures before gated quarantine or consolidation, preserving behavior, independent failure modes and bugfix provenance. | [test-remediation-method](<../../plugins/testing/skills/test-remediation-method/SKILL.md>) |
| Role | `testing:test-suite-auditor` | Runs as the testing-quality dimension of /senior-review:team-review and /senior-review:code-review, and as the engine of /testing:test-audit. TRIGGER WHEN: auditing a test suite, reviewing test hygiene, detecting flaky or dead tests, or assessing test redundancy, layer distribution or placement. DO NOT TRIGGER WHEN: tests should be written (use test-writer), or quarantine or consolidation applied (use /testing:test-audit --fix or /testing:test-consolidate). | [test-suite-auditor](<../../plugins/testing/roles/test-suite-auditor.md>) |
| Role | `testing:test-writer` | Authors behavior-driven suites for existing code, or drives new ones red-green. Auto-detects the framework, and follows the test-hygiene search-before-write protocol instead of creating parallel files. TRIGGER WHEN: the user asks to write tests, add test coverage, or do TDD. | [test-writer](<../../plugins/testing/roles/test-writer.md>) |
| Workflow | `testing:test-audit` | Writes a versioned TEST_AUDIT.md; with --fix, quarantines the rot in gated, revertible commits. TRIGGER WHEN: auditing a test suite, measuring test health, finding dead or flaky or redundant tests, or diagnosing failure causes and proposing temporary quarantine. DO NOT TRIGGER WHEN: one module's tests are consolidated (use /testing:test-consolidate), or new tests written (use the test-writer agent). | [test-audit](<../../plugins/testing/workflows/test-audit.md>) |
| Workflow | `testing:test-consolidate` | Turns overlapping suites into one clean file per source file: BEHAVIOR inventory approved first, originals deleted in the same commit, behavioral protection verified before commit. TRIGGER WHEN: consolidating, deduping or rewriting the tests of a module, or processing quarantined tests for code being touched. DO NOT TRIGGER WHEN: whole-suite health is measured or quarantined (use /testing:test-audit), or tests written for untested code (use the test-writer agent). | [test-consolidate](<../../plugins/testing/workflows/test-consolidate.md>) |

### Workflow contracts

Contracts describe observable outputs; Markdown bodies define decisions,
flags, safety gates and execution. Declared `invoke` execution is unsupported.

#### `testing:test-audit`

**Arguments:** <code>[path] [--fix] [--yes] [--no-run] [--runner &lt;cmd&gt;] [--scope &lt;subpath&gt;]</code>

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `test-audit-completed` |
| Artifacts | `test-audit-report` |
| Schemas | [project-protocol/contracts/work.toml](<../../plugins/project-protocol/contracts/work.toml>), [project-protocol/contracts/project-result.toml](<../../plugins/project-protocol/contracts/project-result.toml>) |
| Declared workers | None |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [test-audit.toml](<../../plugins/testing/workflows/test-audit.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `run` | None | None | `shared` | None declared | `preferred` |

#### `testing:test-consolidate`

**Arguments:** <code>&lt;module-path&gt; [--runner &lt;cmd&gt;] [--coverage-cmd &lt;cmd&gt;] [--dry-run]</code>

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `test-consolidate-completed` |
| Artifacts | `test-consolidate-report` |
| Schemas | [project-protocol/contracts/work.toml](<../../plugins/project-protocol/contracts/work.toml>), [project-protocol/contracts/project-result.toml](<../../plugins/project-protocol/contracts/project-result.toml>) |
| Declared workers | None |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [test-consolidate.toml](<../../plugins/testing/workflows/test-consolidate.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `run` | None | None | `shared` | None declared | `preferred` |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/testing](<../../exports/claude/plugins/testing>) | `native` | `test-audit: native-team`, `test-consolidate: native-team` |
| copilot | [exports/copilot/plugins/testing](<../../exports/copilot/plugins/testing>) | `native` | `test-audit: parallel-subagents`, `test-consolidate: parallel-subagents` |
| codex | [exports/codex/plugins/testing](<../../exports/codex/plugins/testing>) | `adapted` | `test-audit: parallel-subagents`, `test-consolidate: parallel-subagents` |
| pi | [exports/pi/plugins/testing](<../../exports/pi/plugins/testing>) | `adapted` | `test-audit: parallel-subagents`, `test-consolidate: parallel-subagents` |
| opencode | [exports/opencode/plugins/testing](<../../exports/opencode/plugins/testing>) | `native` | `test-audit: parallel-subagents`, `test-consolidate: parallel-subagents` |

<!-- daodan:reference:end -->
