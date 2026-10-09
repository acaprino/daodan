# Project Lifecycle

Five operations coordinate the same canonical owners used by standalone specialists:
assess, repair, change, verify and consolidate. Their entry points load
`project-lifecycle:lifecycle-method`, which prepares inputs, dispatches existing
roles and builds the plan. Specialist methods retain detection and remediation
ownership; lifecycle does not maintain parallel auditor prompts.

Two separate entries serve project takeover and subsequent maintenance.
`handover` loads `handover-method` and produces an incoming consultant's dossier
inside an owned assess run. It explains purpose, modules and critical flows,
setup and test procedures, constraints, evidenced risks, real unknowns and a first
scoped work plan. It uses project-knowledge's explorer, onboarding writer and
guide reviewer, with semantic mapping only when needed. No project files or durable
guides are changed. `--checks=none` is the default; explicitly selected local checks
retain their environment, authorization and exact-candidate gates.

`maintain` loads `maintainer-method` and coordinates the complete Senior Maintainer
campaign: baseline team review, coherence assessment and roadmap, product
corrections, rationalization, final verification and consolidation. Defaults are
focus all, depth deep, guided pace and dry-run. Guided pace waits at the initial
brief and roadmap; dry-run ends at that roadmap. Fix and commit retain every
canonical owner's scope, acceptance, recovery and verification requirements.

Handover never starts maintain automatically. An explicit maintain request can
name `--from-handover RUN_ID`; that dossier must match its current project and
scope before its evidence is reused, and transfers no permission to edit.
Maintain records its resolved request and chain in each active stage run, carries
exact run IDs forward and resumes only named identities. Earlier completed stages
validate historically; the final verify result must validate against the current
project. Neither new entry adds a protocol operation or a TOML workflow executor.
Their coordinators and specialist bindings render through every host adapter.

assess produces evidence and a dependency-aware plan across knowledge, structure,
tests and workspace artifacts. repair validates an exact run/plan and applies only
authorized compatible remedies. change covers bootstrap, feature, bugfix, refactor
and migration. verify binds checks to the actual candidate. consolidate preserves
verified experiment conclusions before retaining or disposing of owned output.

A requested project-wide architectural rationalization starts with full static
X-ray context, or a validated matching run. Suite rationalization uses the testing
owner across the declared layers; instruction consequences use project-knowledge
for canonical updates, regeneration and loading evidence. Severe evidenced defects
take priority over cosmetic cleanup. Small scoped changes retain proportional
checks, and static context never establishes runtime behavior.

Use --focus=knowledge|structure|tests|artifacts|all and
--depth=quick|standard|deep. Default assessment is one initial quick pass.
The plan discloses expensive context steps, unavailable dimensions and commit-only
cleanup before application. Unknown token consumption stays unknown.

State belongs in .daodan/runs/<id>/. Resume an exact run ID; alternative dedicated
roots must stay inside the project. The project-protocol helper validates identity,
snapshots, revisions, deliveries and required gates. No arbitrary workflow executor
or automatic optional-specialist registry is introduced.

--fix permits scoped edits, --commit additionally permits commits; application
subtraction retains its commit-only prerequisite. Structural findings that require
a design choice stay open until that choice has an accepted implementation plan.
--purge requires a separate explicit grant for concluded owned artifacts. Retention is confined, fingerprinted
and resumable, preserving necessary evidence and rejecting links or changed paths.

Native specialist reports remain intact and are referenced by the common work
record and result envelope. A failed delivery or unavailable mandatory check
prevents a successful completion claim. Default quick assessment selects at most
five workers, including workers from reused documentation methods, and declares
what it did not examine.

change, repair and verify review their exact candidates through the same
senior-review engine, including applicable React, TypeScript and platform workers.
The preparation receives this run's scope, baseline and candidate before dispatch,
including new untracked files. The assessment's quick worker cap does not silently
remove required correctness dimensions from a candidate gate. Mandatory providers
and their installation closure are listed in the generated reference below.

Static evidence, runtime exercise and installed-host probes are distinct.
Read [the migration](../migration-to-coherent-harness.md) and
[architecture](../superpowers/specs/2026-10-07-daodan-coherent-harness-design.md).

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `1.3.0`. **Source:** [plugin.toml](<../../plugins/project-lifecycle/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | [abstraction-architect](<abstraction-architect.md>), [clean-code](<clean-code.md>), [codebase-xray](<codebase-xray.md>), [platform-engineering](<platform-engineering.md>), [project-knowledge](<project-knowledge.md>), [project-protocol](<project-protocol.md>), [react-development](<react-development.md>), [repo-hygiene](<repo-hygiene.md>), [senior-review](<senior-review.md>), [testing](<testing.md>), [text-humanizer](<text-humanizer.md>), [typescript-development](<typescript-development.md>) |
| Direct external | `superpowers@claude-plugins-official` |
| Local closure (14) | [abstraction-architect](<abstraction-architect.md>), [clean-code](<clean-code.md>), [codebase-xray](<codebase-xray.md>), [platform-engineering](<platform-engineering.md>), [project-knowledge](<project-knowledge.md>), [project-lifecycle](<project-lifecycle.md>), [project-protocol](<project-protocol.md>), [react-development](<react-development.md>), [repo-hygiene](<repo-hygiene.md>), [senior-review](<senior-review.md>), [skill-catalog](<skill-catalog.md>), [testing](<testing.md>), [text-humanizer](<text-humanizer.md>), [typescript-development](<typescript-development.md>) |
| External closure (3) | `developer-essentials@claude-code-workflows`, `mattpocock-skills@mattpocock`, `superpowers@claude-plugins-official` |

External bundles are separate upstream installations, not copied local skills.
See [host setup](<../hosts.md>) for selection and availability requirements.

**Required capabilities:** `repository.read`, `repository.write`, `shell.execute`, `contexts.isolate`, `roles.dispatch`.
**Optional capabilities:** `execution.parallel`.
Optional capabilities are host mechanisms, not optional local plugin dependencies.

### Registered components

Names below are kernel IDs. Host entry points and paths follow the adapter
mapping in [the host reference](<../hosts.md>).
The source links carry the complete instructions and accepted arguments.

| Kind | ID | Purpose and trigger | Source |
|---|---|---|---|
| Skill | `project-lifecycle:lifecycle-method` | Coordinate complete AI development work across code, tests, project knowledge and artifacts. TRIGGER WHEN: running project-lifecycle assess, repair, change, verify or consolidate, or explicitly taking responsibility for project coherence. DO NOT TRIGGER WHEN: an isolated specialist audit or a single factual answer is sufficient. | [lifecycle-method](<../../plugins/project-lifecycle/skills/lifecycle-method/SKILL.md>) |
| Skill | `project-lifecycle:maintainer-method` | Coordinate the complete Senior Maintainer rationalization campaign. TRIGGER WHEN: running project-lifecycle maintain or leading its complete staged outcome. DO NOT TRIGGER WHEN: an intake dossier is sufficient (use handover-method), or an individual lifecycle operation covers the request. | [maintainer-method](<../../plugins/project-lifecycle/skills/maintainer-method/SKILL.md>) |
| Skill | `project-lifecycle:handover-method` | Coordinate an evidence-based consultant intake dossier. TRIGGER WHEN: running project-lifecycle handover or preparing to take responsibility for an unfamiliar project. DO NOT TRIGGER WHEN: correcting and rationalizing the project (use maintainer-method). | [handover-method](<../../plugins/project-lifecycle/skills/handover-method/SKILL.md>) |
| Workflow | `project-lifecycle:assess` | Assess project coherence and produce a scoped evidence-based repair plan. TRIGGER WHEN: the user requests lifecycle assess or its complete project outcome. DO NOT TRIGGER WHEN: a narrower specialist task already covers the requested outcome. | [assess](<../../plugins/project-lifecycle/workflows/assess.md>) |
| Workflow | `project-lifecycle:repair` | Apply an identified repair plan through canonical owners and verified phase gates. TRIGGER WHEN: the user requests lifecycle repair or its complete project outcome. DO NOT TRIGGER WHEN: a narrower specialist task already covers the requested outcome. | [repair](<../../plugins/project-lifecycle/workflows/repair.md>) |
| Workflow | `project-lifecycle:change` | Develop a complete change with discovery, meaningful tests and coherent closure. TRIGGER WHEN: the user requests lifecycle change or its complete project outcome. DO NOT TRIGGER WHEN: a narrower specialist task already covers the requested outcome. | [change](<../../plugins/project-lifecycle/workflows/change.md>) |
| Workflow | `project-lifecycle:verify` | Verify an exact candidate snapshot and account for checks, coverage and remaining gaps. TRIGGER WHEN: the user requests lifecycle verify or its complete project outcome. DO NOT TRIGGER WHEN: a narrower specialist task already covers the requested outcome. | [verify](<../../plugins/project-lifecycle/workflows/verify.md>) |
| Workflow | `project-lifecycle:consolidate` | Consolidate experiment outcomes, durable conclusions and retention of owned artifacts. TRIGGER WHEN: the user requests lifecycle consolidate or its complete project outcome. DO NOT TRIGGER WHEN: a narrower specialist task already covers the requested outcome. | [consolidate](<../../plugins/project-lifecycle/workflows/consolidate.md>) |
| Workflow | `project-lifecycle:handover` | Prepare an evidence-based consultant intake dossier without changing the project. TRIGGER WHEN: the user requests lifecycle handover or needs to take responsibility for an unfamiliar project. DO NOT TRIGGER WHEN: the user requests correction and rationalization (use maintain). | [handover](<../../plugins/project-lifecycle/workflows/handover.md>) |
| Workflow | `project-lifecycle:maintain` | Lead the complete Senior Maintainer campaign through canonical owners and separate stage runs. TRIGGER WHEN: the user requests a complete guided project rationalization, or lifecycle maintain. DO NOT TRIGGER WHEN: orientation for a new consultant is sufficient (use handover), or one specialist task covers the requested outcome. | [maintain](<../../plugins/project-lifecycle/workflows/maintain.md>) |

### Workflow contracts

Contracts describe observable outputs; Markdown bodies define decisions,
flags, safety gates and execution. Declared `invoke` execution is unsupported.

#### `project-lifecycle:assess`

**Arguments:** <code>[target] [--focus=all&#124;knowledge&#124;structure&#124;tests&#124;artifacts] [--depth=quick&#124;standard&#124;deep] [--run-id ID] [--out INTERNAL_ROOT] [--dry-run&#124;--fix&#124;--commit]</code>

| Contract | Value |
|---|---|
| Inputs | `project`, `objective`, `scope`, `authorization` |
| Outcomes | `scope-and-candidate-identified`, `deliveries-and-required-gates-accounted`, `limits-and-open-actions-visible` |
| Artifacts | `result` |
| Schemas | [project-protocol/contracts/work.toml](<../../plugins/project-protocol/contracts/work.toml>), [project-protocol/contracts/project-result.toml](<../../plugins/project-protocol/contracts/project-result.toml>) |
| Declared workers | `abstraction-architect/abstraction-architect-agent`, `project-knowledge/documentation-engineer`, `project-knowledge/guide-reviewer`, `project-knowledge/instructions-auditor`, `project-protocol/isolated-worker`, `repo-hygiene/workspace-auditor`, `senior-review/cleanup-auditor`, `testing/test-suite-auditor` |
| Composed worker isolation | Required |
| Task-specific isolated workers | Allowed through the protocol role |
| Sidecar | [assess.toml](<../../plugins/project-lifecycle/workflows/assess.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `prepare` | None | None | `shared` | None declared | `preferred` |
| `audit-cleanup` | `prepare` | `senior-review/cleanup-auditor`, `per item in selection:cleanup` | `required` | `all-delivered` | `preferred` |
| `audit-tests` | `prepare` | `testing/test-suite-auditor`, `per item in selection:tests` | `required` | `all-delivered` | `preferred` |
| `audit-structure` | `prepare` | `abstraction-architect/abstraction-architect-agent`, `per item in selection:structure` | `required` | `all-delivered` | `preferred` |
| `audit-instructions` | `prepare` | `project-knowledge/instructions-auditor`, `per item in selection:instructions` | `required` | `all-delivered` | `preferred` |
| `audit-workspace` | `prepare` | `repo-hygiene/workspace-auditor`, `per item in selection:workspace` | `required` | `all-delivered` | `preferred` |
| `plan` | `audit-cleanup`, `audit-tests`, `audit-structure`, `audit-instructions`, `audit-workspace` | None | `shared` | None declared | `preferred` |

#### `project-lifecycle:repair`

**Arguments:** <code>[target] [--focus=all&#124;knowledge&#124;structure&#124;tests&#124;artifacts] [--depth=quick&#124;standard&#124;deep] [--run-id ID] [--out INTERNAL_ROOT] [--dry-run&#124;--fix&#124;--commit]</code>

| Contract | Value |
|---|---|
| Inputs | `project`, `objective`, `scope`, `authorization` |
| Outcomes | `scope-and-candidate-identified`, `deliveries-and-required-gates-accounted`, `limits-and-open-actions-visible` |
| Artifacts | `result` |
| Schemas | [project-protocol/contracts/work.toml](<../../plugins/project-protocol/contracts/work.toml>), [project-protocol/contracts/project-result.toml](<../../plugins/project-protocol/contracts/project-result.toml>) |
| Declared workers | `abstraction-architect/abstraction-architect-agent`, `codebase-xray/semantic-interconnect-mapper`, `platform-engineering/platform-reviewer`, `project-knowledge/codebase-explorer`, `project-knowledge/doc-humanizer`, `project-knowledge/documentation-engineer`, `project-knowledge/flow-writer`, `project-knowledge/guide-reviewer`, `project-knowledge/instructions-auditor`, `project-knowledge/onboarding-writer`, `project-knowledge/ops-writer`, `project-knowledge/overview-writer`, `project-knowledge/tech-writer`, `project-protocol/isolated-worker`, `react-development/react-performance-optimizer`, `repo-hygiene/workspace-auditor`, `senior-review/cleanup-auditor`, `senior-review/code-auditor`, `senior-review/data-integrity-auditor`, `senior-review/premise-auditor`, `senior-review/resource-lifecycle-auditor`, `senior-review/security-auditor`, `senior-review/temporal-resilience-auditor`, `senior-review/ui-race-auditor`, `testing/test-suite-auditor`, `testing/test-writer`, `text-humanizer/text-humanizer`, `typescript-development/type-safety-auditor` |
| Composed worker isolation | Required |
| Task-specific isolated workers | Allowed through the protocol role |
| Sidecar | [repair.toml](<../../plugins/project-lifecycle/workflows/repair.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `prepare` | None | None | `shared` | None declared | `preferred` |
| `execute` | `prepare` | None | `shared` | None declared | `preferred` |

#### `project-lifecycle:change`

**Arguments:** <code>[target] [--focus=all&#124;knowledge&#124;structure&#124;tests&#124;artifacts] [--depth=quick&#124;standard&#124;deep] [--run-id ID] [--out INTERNAL_ROOT] [--dry-run&#124;--fix&#124;--commit]</code>

| Contract | Value |
|---|---|
| Inputs | `project`, `objective`, `scope`, `authorization` |
| Outcomes | `scope-and-candidate-identified`, `deliveries-and-required-gates-accounted`, `limits-and-open-actions-visible` |
| Artifacts | `result` |
| Schemas | [project-protocol/contracts/work.toml](<../../plugins/project-protocol/contracts/work.toml>), [project-protocol/contracts/project-result.toml](<../../plugins/project-protocol/contracts/project-result.toml>) |
| Declared workers | `abstraction-architect/abstraction-architect-agent`, `codebase-xray/semantic-interconnect-mapper`, `platform-engineering/platform-reviewer`, `project-knowledge/codebase-explorer`, `project-knowledge/doc-humanizer`, `project-knowledge/documentation-engineer`, `project-knowledge/flow-writer`, `project-knowledge/guide-reviewer`, `project-knowledge/instructions-auditor`, `project-knowledge/onboarding-writer`, `project-knowledge/ops-writer`, `project-knowledge/overview-writer`, `project-knowledge/tech-writer`, `project-protocol/isolated-worker`, `react-development/react-performance-optimizer`, `senior-review/cleanup-auditor`, `senior-review/code-auditor`, `senior-review/data-integrity-auditor`, `senior-review/premise-auditor`, `senior-review/resource-lifecycle-auditor`, `senior-review/security-auditor`, `senior-review/temporal-resilience-auditor`, `senior-review/ui-race-auditor`, `testing/test-suite-auditor`, `testing/test-writer`, `text-humanizer/text-humanizer`, `typescript-development/type-safety-auditor` |
| Composed worker isolation | Required |
| Task-specific isolated workers | Allowed through the protocol role |
| Sidecar | [change.toml](<../../plugins/project-lifecycle/workflows/change.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `prepare` | None | None | `shared` | None declared | `preferred` |
| `execute` | `prepare` | None | `shared` | None declared | `preferred` |

#### `project-lifecycle:verify`

**Arguments:** <code>[target] [--focus=all&#124;knowledge&#124;structure&#124;tests&#124;artifacts] [--depth=quick&#124;standard&#124;deep] [--run-id ID] [--out INTERNAL_ROOT] [--dry-run&#124;--fix&#124;--commit]</code>

| Contract | Value |
|---|---|
| Inputs | `project`, `objective`, `scope`, `authorization` |
| Outcomes | `scope-and-candidate-identified`, `deliveries-and-required-gates-accounted`, `limits-and-open-actions-visible` |
| Artifacts | `result` |
| Schemas | [project-protocol/contracts/work.toml](<../../plugins/project-protocol/contracts/work.toml>), [project-protocol/contracts/project-result.toml](<../../plugins/project-protocol/contracts/project-result.toml>) |
| Declared workers | `abstraction-architect/abstraction-architect-agent`, `platform-engineering/platform-reviewer`, `project-knowledge/documentation-engineer`, `project-knowledge/guide-reviewer`, `project-knowledge/instructions-auditor`, `project-protocol/isolated-worker`, `react-development/react-performance-optimizer`, `senior-review/code-auditor`, `senior-review/data-integrity-auditor`, `senior-review/premise-auditor`, `senior-review/resource-lifecycle-auditor`, `senior-review/security-auditor`, `senior-review/temporal-resilience-auditor`, `senior-review/ui-race-auditor`, `testing/test-suite-auditor`, `typescript-development/type-safety-auditor` |
| Composed worker isolation | Required |
| Task-specific isolated workers | Allowed through the protocol role |
| Sidecar | [verify.toml](<../../plugins/project-lifecycle/workflows/verify.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `prepare` | None | None | `shared` | None declared | `preferred` |
| `execute` | `prepare` | None | `shared` | None declared | `preferred` |

#### `project-lifecycle:consolidate`

**Arguments:** <code>[target] [--focus=all&#124;knowledge&#124;structure&#124;tests&#124;artifacts] [--depth=quick&#124;standard&#124;deep] [--run-id ID] [--out INTERNAL_ROOT] [--dry-run&#124;--fix&#124;--commit] [--purge]</code>

| Contract | Value |
|---|---|
| Inputs | `project`, `objective`, `scope`, `authorization` |
| Outcomes | `scope-and-candidate-identified`, `deliveries-and-required-gates-accounted`, `limits-and-open-actions-visible` |
| Artifacts | `result` |
| Schemas | [project-protocol/contracts/work.toml](<../../plugins/project-protocol/contracts/work.toml>), [project-protocol/contracts/project-result.toml](<../../plugins/project-protocol/contracts/project-result.toml>) |
| Declared workers | `codebase-xray/semantic-interconnect-mapper`, `project-knowledge/codebase-explorer`, `project-knowledge/doc-humanizer`, `project-knowledge/documentation-engineer`, `project-knowledge/flow-writer`, `project-knowledge/guide-reviewer`, `project-knowledge/instructions-auditor`, `project-knowledge/onboarding-writer`, `project-knowledge/ops-writer`, `project-knowledge/overview-writer`, `project-knowledge/tech-writer`, `project-protocol/isolated-worker`, `text-humanizer/text-humanizer` |
| Composed worker isolation | Required |
| Task-specific isolated workers | Allowed through the protocol role |
| Sidecar | [consolidate.toml](<../../plugins/project-lifecycle/workflows/consolidate.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `prepare` | None | None | `shared` | None declared | `preferred` |
| `execute` | `prepare` | None | `shared` | None declared | `preferred` |

#### `project-lifecycle:handover`

**Arguments:** <code>[target] [--depth=quick&#124;standard&#124;deep] [--checks=none&#124;local] [--run-id ID] [--out INTERNAL_ROOT]</code>

| Contract | Value |
|---|---|
| Inputs | `project`, `scope`, `authorizations`, `audience`, `depth`, `checks` |
| Outcomes | `consultant-dossier-delivered`, `observed-and-exercised-evidence-separated`, `first-scoped-work-plan-visible`, `project-unchanged`, `deliveries-and-required-gates-accounted` |
| Artifacts | `handover-dossier`, `result` |
| Schemas | [project-protocol/contracts/work.toml](<../../plugins/project-protocol/contracts/work.toml>), [project-protocol/contracts/project-result.toml](<../../plugins/project-protocol/contracts/project-result.toml>) |
| Declared workers | `codebase-xray/semantic-interconnect-mapper`, `project-knowledge/codebase-explorer`, `project-knowledge/guide-reviewer`, `project-knowledge/onboarding-writer` |
| Composed worker isolation | Required |
| Task-specific isolated workers | Not declared |
| Sidecar | [handover.toml](<../../plugins/project-lifecycle/workflows/handover.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `prepare` | None | None | `shared` | None declared | `preferred` |
| `explore` | `prepare` | `project-knowledge/codebase-explorer` | `required` | None declared | `preferred` |
| `map-contracts` | `explore` | `codebase-xray/semantic-interconnect-mapper`, `per item in selection:contracts` | `required` | `all-delivered` | `preferred` |
| `local-checks` | `explore` | None | `shared` | None declared | `preferred` |
| `prepare-dossier` | `map-contracts`, `local-checks` | None | `shared` | None declared | `preferred` |
| `write-dossier` | `prepare-dossier` | `project-knowledge/onboarding-writer` | `required` | None declared | `preferred` |
| `review-dossier` | `write-dossier` | `project-knowledge/guide-reviewer` | `required` | None declared | `preferred` |
| `close` | `review-dossier` | None | `shared` | None declared | `preferred` |

#### `project-lifecycle:maintain`

**Arguments:** <code>[target] [--exclude PATH] [--focus=all&#124;knowledge&#124;structure&#124;tests&#124;artifacts] [--depth=quick&#124;standard&#124;deep] [--pace=guided&#124;autonomous] [--dry-run&#124;--fix&#124;--commit] [--resume RUN_ID] [--from-handover RUN_ID] [--out INTERNAL_ROOT]</code>

| Contract | Value |
|---|---|
| Inputs | `project`, `campaign-request`, `scope`, `authorization`, `resume-identities` |
| Outcomes | `guided-checkpoints-preserved`, `one-active-lifecycle-operation-at-a-time`, `canonical-methods-and-declared-workers-only`, `stage-results-bound-to-exact-runs-and-candidates`, `final-verification-matches-current-project`, `missing-deliveries-and-required-gates-prevent-completion` |
| Artifacts | `campaign-request`, `campaign-brief`, `stage-results`, `campaign-report` |
| Schemas | [project-protocol/contracts/work.toml](<../../plugins/project-protocol/contracts/work.toml>), [project-protocol/contracts/project-result.toml](<../../plugins/project-protocol/contracts/project-result.toml>) |
| Declared workers | `abstraction-architect/abstraction-architect-agent`, `clean-code/clean-code-agent`, `codebase-xray/semantic-interconnect-mapper`, `platform-engineering/platform-reviewer`, `project-knowledge/codebase-explorer`, `project-knowledge/doc-humanizer`, `project-knowledge/documentation-engineer`, `project-knowledge/flow-writer`, `project-knowledge/guide-reviewer`, `project-knowledge/instructions-auditor`, `project-knowledge/onboarding-writer`, `project-knowledge/ops-writer`, `project-knowledge/overview-writer`, `project-knowledge/tech-writer`, `project-protocol/isolated-worker`, `react-development/react-performance-optimizer`, `repo-hygiene/workspace-auditor`, `senior-review/api-contract-auditor`, `senior-review/chicken-egg-detector`, `senior-review/cleanup-auditor`, `senior-review/code-auditor`, `senior-review/data-integrity-auditor`, `senior-review/distributed-flow-auditor`, `senior-review/logic-integrity-auditor`, `senior-review/premise-auditor`, `senior-review/resource-lifecycle-auditor`, `senior-review/security-auditor`, `senior-review/temporal-resilience-auditor`, `senior-review/ui-race-auditor`, `testing/test-suite-auditor`, `testing/test-writer`, `text-humanizer/text-humanizer`, `typescript-development/type-safety-auditor` |
| Composed worker isolation | Required |
| Task-specific isolated workers | Allowed through the protocol role |
| Sidecar | [maintain.toml](<../../plugins/project-lifecycle/workflows/maintain.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `orientation` | None | None | `shared` | None declared | `preferred` |
| `coordinate` | `orientation` | None | `shared` | None declared | `preferred` |
| `report` | `coordinate` | None | `shared` | None declared | `preferred` |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/project-lifecycle](<../../exports/claude/plugins/project-lifecycle>) | `native` | `assess: native-team`, `repair: native-team`, `change: native-team`, `verify: native-team`, `consolidate: native-team`, `handover: native-team`, `maintain: native-team` |
| copilot | [exports/copilot/plugins/project-lifecycle](<../../exports/copilot/plugins/project-lifecycle>) | `native` | `assess: parallel-subagents`, `repair: parallel-subagents`, `change: parallel-subagents`, `verify: parallel-subagents`, `consolidate: parallel-subagents`, `handover: parallel-subagents`, `maintain: parallel-subagents` |
| codex | [exports/codex/plugins/project-lifecycle](<../../exports/codex/plugins/project-lifecycle>) | `adapted` | `assess: parallel-subagents`, `repair: parallel-subagents`, `change: parallel-subagents`, `verify: parallel-subagents`, `consolidate: parallel-subagents`, `handover: parallel-subagents`, `maintain: parallel-subagents` |
| pi | [exports/pi/plugins/project-lifecycle](<../../exports/pi/plugins/project-lifecycle>) | `adapted` | `assess: parallel-subagents`, `repair: parallel-subagents`, `change: parallel-subagents`, `verify: parallel-subagents`, `consolidate: parallel-subagents`, `handover: parallel-subagents`, `maintain: parallel-subagents` |
| opencode | [exports/opencode/plugins/project-lifecycle](<../../exports/opencode/plugins/project-lifecycle>) | `native` | `assess: parallel-subagents`, `repair: parallel-subagents`, `change: parallel-subagents`, `verify: parallel-subagents`, `consolidate: parallel-subagents`, `handover: parallel-subagents`, `maintain: parallel-subagents` |

### Additional shipped contracts and mechanisms

- Neutral policy: [run-write-confinement](<../../plugins/project-lifecycle/policies/run-write-confinement.toml>). Enforcement is documented in the policy and host reference.

<!-- daodan:reference:end -->
