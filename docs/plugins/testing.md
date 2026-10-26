# Testing Plugin

> Behavior-driven authoring and suite maintenance: review and update existing checks, add missing protection, diagnose failures and consolidate redundant tests without losing meaningful regressions.

The [plugin README](../../plugins/testing/README.md) indexes responsibilities,
upstream sources, inspected revisions and full license notices. TDD and browser
E2E remain delegated; the intake copies their MIT notices only.

Command examples and named tools in this guide use Claude notation. For other
hosts, use the entry points and bindings in the source-derived reference below
and [host setup](../hosts.md).

## Required dependencies

The required [work-controller](work-controller.md) plugin owns run identity,
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
| **Modes** | Generate (reuse/update existing checks and add justified protection) or explicitly selected Interactive TDD |

Search for the existing owner at the intended layer before writing. Unit ownership follows source; integration, contract and e2e ownership follows behavior. Oracles require a requirement or independent evidence. Parallel owners, skips to get green and unsupported weakened assertions are anti-patterns.

Before adding any case, read affected existing tests and map approved behavior
and independent failure modes to existing checks: reuse, update or justify an
addition. Zero new tests is a valid outcome. Deliver those decisions as well as
observed results. Changed contracts need revised checks; refactors preserve and
retarget their meaningful protection.

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

### Suite maintenance: `/daodan:maintain-tests`

This dedicated entry reviews existing protection, updates checks whose approved
contracts changed, consolidates duplicates and reorganizes ownership through
the canonical remediation method. It previews the inventory first, reuses
accepted scope and applies only authorized actions. Unknown causes and product
regressions remain open; lower counts alone do not establish success. Verification
maps protected behavior and distinct failure modes to surviving checks. Mutation
reports can support that assessment; no mutation runner or automatic job is added.

### Repository cleanup composition: `/daodan:tidy-repo`

`/daodan:tidy-repo` previews redundant or obsolete tests through mode `consolidate`, beside the other owners' detections, and applies only the groups the user authorizes. Consolidation inventories behavior, independent failure modes and regression provenance before rewriting. Every surviving protection has a justified owner at its layer. Replacement and retirement share one authorized candidate and commit; unresolved meaning remains open. Counts and line coverage guide investigation and do not prove equivalence. Refactors and migrations retarget meaningful protection instead of retiring it solely because its original file moved.

---

**Related:** [python-development](python-development.md) (Python-specific pytest techniques) | [senior-review](senior-review.md) (hard-depends on this plugin and dispatches `test-suite-auditor` for relevant test changes) | [project-knowledge](project-knowledge.md) (offers condensed rules for scoped project instructions, preserving equivalent existing policy)

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `4.5.0`. **Source:** [plugin.toml](<../../plugins/testing/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | [report-rendering](<report-rendering.md>), [work-controller](<work-controller.md>) |
| Direct external | `developer-essentials@claude-code-workflows`, `mattpocock-skills@mattpocock` |
| Local closure (3) | [report-rendering](<report-rendering.md>), [testing](<testing.md>), [work-controller](<work-controller.md>) |
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
| Skill | `testing:test-remediation-method` | Maintain existing test suites: diagnose failures, review and consolidate redundant tests, preserving behavior, independent failure modes and bugfix provenance. Load for suite audits, quarantine or rationalization through /daodan:maintain-tests (also composed by /daodan:tidy-repo). | [test-remediation-method](<../../plugins/testing/skills/test-remediation-method/SKILL.md>) |
| Role | `testing:test-suite-auditor` | Composed review of testing:test-suite-structure-auditor, testing:test-oracle-auditor, testing:test-reliability-auditor, testing:journey-protection-auditor, testing:contract-test-auditor, testing:capacity-test-auditor, testing:ai-evaluation-auditor. TRIGGER WHEN: a review coordinator dispatches this composition. DO NOT TRIGGER WHEN: no member applies; missing required input remains a coverage gap. | [test-suite-auditor](<../../plugins/testing/plugin.toml>) |
| Role | `testing:test-writer` | Reuses and updates existing behavior-driven tests before adding justified protection, or drives new behavior red-green. Detects the framework and follows test-hygiene ownership rules. TRIGGER WHEN: the user asks to write tests, add test coverage, or do TDD. | [test-writer](<../../plugins/testing/roles/test-writer.md>) |
| Role | `testing:test-suite-structure-auditor` | Review test ownership, layer fitness, retired behavior, disabled collection and duplicate failure-mode protection. TRIGGER WHEN: reviewing test ownership, layer fitness, retired behavior, disabled collection and duplicate failure-mode protection. DO NOT TRIGGER WHEN: implementing changes or applying remediation. | [test-suite-structure-auditor](<../../plugins/testing/roles/test-suite-structure-auditor.md>) |
| Role | `testing:test-oracle-auditor` | Review contradictory, implementation-coupled or vacuous assertions against independent product requirements. TRIGGER WHEN: reviewing contradictory, implementation-coupled or vacuous assertions against independent product requirements. DO NOT TRIGGER WHEN: implementing changes or applying remediation. | [test-oracle-auditor](<../../plugins/testing/roles/test-oracle-auditor.md>) |
| Role | `testing:test-reliability-auditor` | Review runner viability, isolation, intermittent failures and trustworthy timing or coverage evidence. TRIGGER WHEN: reviewing runner viability, isolation, intermittent failures and trustworthy timing or coverage evidence. DO NOT TRIGGER WHEN: implementing changes or applying remediation. | [test-reliability-auditor](<../../plugins/testing/roles/test-reliability-auditor.md>) |
| Role | `testing:journey-protection-auditor` | Review whether tests protect required entry, success, failure and recovery outcomes through the critical journey. TRIGGER WHEN: reviewing whether tests protect required entry, success, failure and recovery outcomes through the critical journey. DO NOT TRIGGER WHEN: implementing changes or applying remediation. | [journey-protection-auditor](<../../plugins/testing/roles/journey-protection-auditor.md>) |
| Role | `testing:contract-test-auditor` | Review whether producer and consumer contract tests detect real wire, schema, error and version drift. TRIGGER WHEN: reviewing whether producer and consumer contract tests detect real wire, schema, error and version drift. DO NOT TRIGGER WHEN: implementing changes or applying remediation. | [contract-test-auditor](<../../plugins/testing/roles/contract-test-auditor.md>) |
| Role | `testing:capacity-test-auditor` | Review workload, bottleneck reachability and latency, error or backlog assertions against declared capacity requirements. TRIGGER WHEN: reviewing workload, bottleneck reachability and latency, error or backlog assertions against declared capacity requirements. DO NOT TRIGGER WHEN: implementing changes or applying remediation. | [capacity-test-auditor](<../../plugins/testing/roles/capacity-test-auditor.md>) |
| Role | `testing:ai-evaluation-auditor` | Review AI or retrieval evaluation cases, independent oracles, leakage and stochastic coverage against required capabilities. TRIGGER WHEN: reviewing AI or retrieval evaluation cases, independent oracles, leakage and stochastic coverage against required capabilities. DO NOT TRIGGER WHEN: implementing changes or applying remediation. | [ai-evaluation-auditor](<../../plugins/testing/roles/ai-evaluation-auditor.md>) |

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
