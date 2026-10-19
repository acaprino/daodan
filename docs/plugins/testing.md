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
| **Wired into** | the suite audit of `/daodan:check-health`, and senior-review's testing-quality dimension (the branch review of `/daodan:review-branch`, Agent F of the code-review variant), which runs whenever the change touches test files |

Nine detection dimensions: inventory and layer distribution, orphan tests, skipped and disabled, failing and flaky, duplicate coverage, contradictory tests, implementation-coupled tests, never-failing tests, runtime and coverage distribution. Every finding carries evidence (`file:line` or command output) and a cause-specific fix owner: implementation, oracle/authoring, environment, accepted consolidation or eligible temporary quarantine.

---

## Skills

### `test-hygiene`

The plugin's knowledge base: why suites degrade under agentic coding, binding rules, the remediation ladder, and the layer model with runtime budgets.

| | |
|---|---|
| **Trigger** | Creating or placing test files, auditing suite health, quarantining, consolidating |

**Reference docs included:**

| Reference | Content |
|-----------|---------|
| `prevention-rules.md` | Search before writing; one deterministic unit-test owner per source file; integration, contract and e2e owners by behavioral scope; layer budgets, behavioral oracles, no skip markers and assertion integrity |
| `remediation-workflow.md` | TEST_AUDIT.md format, quarantine protocol and lifecycle, per-module consolidation, safety-net e2e tests, mutation-testing guidance with project-defined cadence (no runner shipped) |
| `runner-playbook.md` | Per-runner detection and measurement commands (pytest, Vitest, Jest, Mocha, go test, cargo test, JUnit, dotnet, RSpec, PHPUnit) plus flaky-detection methods |

`test-preparation` exposes runner/configuration/source mapping to coordinators.
Missing runners or suites produce diagnosis and configuration/authoring actions.
`test-remediation-method` classifies product defect, disproven oracle, environment,
flakiness and unknown causes before selecting a remedy. Quarantine records evidence,
owner, residual protection and return condition. A green suite is not sufficient
evidence of a trustworthy suite.

Established colocated layouts remain valid when layer ownership is clear. Boundary
doubles require a reason; integration claims need evidence from the intended real
boundary. A wrong expected result can be corrected using independent authority,
while valid product protection remains active. Retirement requires retired behavior
or verified equivalent replacement in the same candidate. Resource isolation covers
clocks, randomness, environment, fixtures and asynchronous cleanup. Surviving mutants
are investigated for equivalence, reachability and meaningful missing protection.

---

## Entry points and methods

The plugin has no command of its own. `testing:test-remediation-method` runs in mode `audit`, `quarantine` or `consolidate`; audit is report-only, and quarantine and consolidation apply only explicitly accepted actions.

### Suite audit: `/daodan:check-health`

`/daodan:check-health` runs the method in mode `audit` for its tests dimension. The whole-suite health audit produces a versioned `TEST_AUDIT.md`: inventory, runtime, skipped, failing, flaky, orphan and layer evidence, with unavailable measurements declared. A later quarantine uses the canonical diagnosis and remediation method, rather than treating a failing test as automatically disposable. Actual product regressions stay protected. Authorized quarantine records risk and return conditions; failure recovery preserves existing and foreign edits.

### Consolidation: `/daodan:tidy-repo`

`/daodan:tidy-repo` previews redundant or obsolete tests through mode `consolidate`, beside the other owners' detections, and applies only the groups the user authorizes. Consolidation inventories behavior, independent failure modes and regression provenance before rewriting. Every surviving protection has a justified owner at its layer. Replacement and retirement share one authorized candidate and commit; unresolved meaning remains open. Counts and line coverage guide investigation and do not prove equivalence. Refactors and migrations retarget meaningful protection instead of retiring it solely because its original file moved.

---

**Related:** [python-development](python-development.md) (Python-specific pytest techniques) | [senior-review](senior-review.md) (hard-depends on this plugin and dispatches `test-suite-auditor` for relevant test changes) | [project-knowledge](project-knowledge.md) (offers condensed rules for scoped project instructions, preserving equivalent existing policy)

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `4.0.0`. **Source:** [plugin.toml](<../../plugins/testing/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | [project-protocol](<project-protocol.md>), [report-rendering](<report-rendering.md>) |
| Direct external | `developer-essentials@claude-code-workflows`, `mattpocock-skills@mattpocock` |
| Local closure (3) | [project-protocol](<project-protocol.md>), [report-rendering](<report-rendering.md>), [testing](<testing.md>) |
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
| Skill | `testing:test-hygiene` | Test placement rules and the measure, quarantine, consolidate remediation ladder for degraded test suites. TRIGGER WHEN: creating or placing test files, deciding whether to extend an existing test or add a new file, auditing test-suite health, quarantining flaky tests, or consolidating redundant tests. DO NOT TRIGGER WHEN: TDD workflow mechanics (use mattpocock-skills:tdd) or browser E2E page objects/waiting (use developer-essentials:e2e-testing-patterns). | [test-hygiene](<../../plugins/testing/skills/test-hygiene/SKILL.md>) |
| Skill | `testing:test-preparation` | Prepare existing test-auditor inputs, runner/configuration diagnosis and snapshot-bound baseline evidence. Load before dispatching testing:test-suite-auditor. | [test-preparation](<../../plugins/testing/skills/test-preparation/SKILL.md>) |
| Skill | `testing:test-remediation-method` | Classify test failures before gated quarantine or consolidation, preserving behavior, independent failure modes and bugfix provenance. Load when auditing a suite, quarantining tests or consolidating a module's tests (consolidation through /daodan:tidy-repo). | [test-remediation-method](<../../plugins/testing/skills/test-remediation-method/SKILL.md>) |
| Role | `testing:test-suite-auditor` | Runs as the testing-quality dimension of senior-review's team-review and code-review variants (/daodan:review-branch), and as the engine of the audit mode of testing:test-remediation-method. TRIGGER WHEN: auditing a test suite, reviewing test hygiene, detecting flaky or dead tests, or assessing test redundancy, layer distribution or placement. DO NOT TRIGGER WHEN: tests should be written (use test-writer), or quarantine or consolidation applied (use testing:test-remediation-method in quarantine or consolidate mode). | [test-suite-auditor](<../../plugins/testing/roles/test-suite-auditor.md>) |
| Role | `testing:test-writer` | Authors behavior-driven suites for existing code, or drives new ones red-green. Auto-detects the framework, and follows the test-hygiene search-before-write protocol instead of creating parallel files. TRIGGER WHEN: the user asks to write tests, add test coverage, or do TDD. | [test-writer](<../../plugins/testing/roles/test-writer.md>) |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/testing](<../../exports/claude/plugins/testing>) | `native` | No workflow entry points |
| copilot | [exports/copilot/plugins/testing](<../../exports/copilot/plugins/testing>) | `native` | No workflow entry points |
| codex | [exports/codex/plugins/testing](<../../exports/codex/plugins/testing>) | `adapted` | No workflow entry points |
| pi | [exports/pi/plugins/testing](<../../exports/pi/plugins/testing>) | `adapted` | No workflow entry points |
| opencode | [exports/opencode/plugins/testing](<../../exports/opencode/plugins/testing>) | `native` | No workflow entry points |

<!-- daodan:reference:end -->
