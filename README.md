# Daodan

Daodan is a development harness for projects built with AI. It augments your coding
agent with a coherent way to understand a project, make changes, verify their
consequences and preserve what was learned.

Its job is to keep behavior, code, tests, instructions, documentation and artifacts
in agreement. It helps recover fragmented projects and avoid adding another layer
of duplication, dead code, misleading tests or forgotten experimental output.

One hand-authored source ships to Claude Code, GitHub Copilot, Codex, Pi and
OpenCode V2. Useful language, framework and domain specialists remain independent.

## Start with the project outcome

| Command | Use it for | Result |
|---|---|---|
| /project-lifecycle:assess | Understand incoherence and accumulated debt | Evidence, coverage and an actionable plan with owners and dependencies |
| /project-lifecycle:repair | Apply an identified plan | Scoped remedies, verified phases and visible open decisions |
| /project-lifecycle:change | Bootstrap, feature, bugfix, refactor or migration | Working behavior and coherent code, tests and knowledge |
| /project-lifecycle:verify | Check a candidate revision and its consequences | Snapshot-bound checks, review and honest limitations |
| /project-lifecycle:consolidate | Close experiments and reduce residual output | Verified conclusions, retained evidence and artifact disposition |

These entries use the same specialist methods as their standalone commands.
Choose a focus (knowledge, structure, tests, artifacts or all) and a depth
(quick, standard or deep). Assessment starts with one scoped pass. Development work
uses checks proportional to its risk, rather than launching every auditor each time.

Run records live in .daodan/runs/<id>/ inside the project. Resume by exact run ID.
The record identifies intent, scope, file snapshots, authorization, plan, deliveries
and checks. A missing worker or an unexecuted gate remains visible.

Preview is the default for repair and retention. --fix applies authorized edits;
--commit adds commits and enables commit-only application cleanup. --purge is a
separate explicit grant for concluded, owned experimental output. Quarantine moves
preserve data and do not count as bytes deleted.

## One request for an architectural refactor

With `project-lifecycle` and its required dependencies installed, paste this prompt
into your project chat. Daodan supplies the workflow; Claude Code, Codex, GitHub
Copilot, Pi and OpenCode V2 expose it through different native entries:

| Host | Change entry |
|---|---|
| Claude Code / OpenCode V2 | `/project-lifecycle:change` |
| Codex | `change-workflow` skill |
| GitHub Copilot | `change` prompt with the `change-coordinator` agent selected |
| Pi | `/project-lifecycle-change` |

The prompt names the workflow rather than a host-specific command. On Copilot,
select the coordinator agent before pasting it. See [host setup](docs/hosts.md)
for required worker and external-method support. One request covers the complete
outcome; execution still proceeds through plans, edits and verification gates.
The instruction and testing clauses follow the [source-backed research note](docs/references/project-instructions-and-test-practices.md),
including Anthropic's prompting guidance and the detected stack's own documentation.

```text
Use Daodan's project-lifecycle change workflow to rationalize this project,
using its native entry on this host. Use focus all, depth deep and --fix.

Read the project instructions, requirements, code, tests and guides. Identify
the actual instruction files and scopes loaded by this harness, the authoritative
sources and any synchronization rules. Define observable success criteria and
record baseline checks against approved requirements.
State material assumptions and unresolved alternatives. Choose the simplest
design that satisfies current requirements. Keep every change traceable to this
authorized objective; avoid speculative features and unrelated cleanup.

Before proposing or applying refactors, run codebase-xray's analyze workflow at
full depth. Reuse a completed run only after validating its current snapshot,
scope and depth. Keep X-ray static and report inventory, files read in depth and
runtime exercise separately. Use its evidence to map responsibilities,
dependencies, duplicated domain rules, critical paths and fragile flows.
Review relevant security, data-integrity, concurrency and resource-lifecycle
risks. Prioritize evidenced severe defects before optional cleanup.
Build an evidence-based plan and implement it incrementally:

- Give each shared rule a canonical owner. Consolidate services and interfaces
  only where their contracts and ownership justify sharing.
- Choose classes where state and lifecycle justify them, and functions for
  pure calculations and transformations. Reuse sound existing implementations.
- Simplify proven redundant layers, aliases and wrappers through their owning
  methods. Keep readability work separate from behavior changes.
- Investigate relevant concurrency, cancellation, interrupted streams, stale
  responses, transactions and UI state. Fix evidenced defects without imposing
  a framework, database or architecture in advance.

Audit the entire existing test suite and rationalize it in scoped batches through
testing's canonical audit and consolidation methods. Inventory protected behaviors,
distinct failure modes, expected-result sources and bugfix history. Identify proven
duplication, contradictions, ineffective assertions, excessive implementation
coupling, over-mocking, uncontrolled state and flakiness. Derive expected results
from approved requirements, explicit examples, independent calculations or
justified invariants. Preserve relevant test layers and exercise real integrations
when database, transaction, concurrency or external-contract semantics matter.
Classify failures as product defects, wrong expectations, environment problems,
intermittent behavior or unknown causes before deciding their treatment.
Repair incorrect or brittle tests. Apply consolidation, retirement or quarantine
only to accepted inventory entries; reuse existing scope-specific approvals and
retain unresolved entries. Verify remaining protection on the exact candidate
before completing each phase, including regressions from real bugs.
Investigate state leaks, ordering, clocks, randomness and asynchronous cleanup.
Fix root causes rather than weakening assertions, blindly refreshing snapshots,
adding retries or suppressing failures to obtain a green suite.
Test counts, coverage, age and refactoring alone never justify removal.
Record which surviving tests protect each retained behavior and failure
mode, and report the before/after suite structure and checks actually executed.

Audit and maintain AGENTS.md, CLAUDE.md and all applicable nested or host-specific
project instructions through project-knowledge's instructions method. Verify
claims, paths, commands, ownership and architecture against their sources.
Preserve approved intent and justified exceptions. Edit the canonical owner,
regenerate derived copies and check parity; retain unresolved claims explicitly.
Document verified build/test commands and prerequisites, test-layer ownership,
fixtures and isolation, cleanup, mocking boundaries, deterministic time/randomness,
failure diagnosis, regression protection and required verification gates.
Adapt stack practices to installed versions using available knowledge and current
primary sources where needed. Translate recommendations into justified local
rules or executable checks. Keep durable instructions concise and applicable;
link detailed procedures in existing guides or reusable skills. Keep session
status, temporary results and open task lists in the run record. Verify which
instruction files the current harness loads rather than assuming identical rules.
Record any required reload or fresh-session step after changing instructions.

Preserve required behavior, preexisting edits and meaningful test protection.
Add or adapt tests for independent failure modes. Review the exact candidate
through senior-review's canonical method with isolated reviewers and applicable
stack specialists. Resolve evidenced correctness defects and unmet requirements.
Run the relevant checks and exercise affected product paths when the required
environment is available. Recheck affected guides and instruction consumers,
then consolidate this run's conclusions and owned experimental output.

Proceed autonomously within this scope until the requested outcome is complete.
Involve me only for conflicting requirements, essential product decisions,
missing access or additional authorization. Report changes, checks actually
executed, coverage, unresolved decisions and unavailable mandatory gates.
Do not claim completion while a required delivery or gate is missing.
Never report an unexecuted database, browser or production check as passed.
```

This prompt authorizes scoped edits. Replace `--fix` with `--commit` to also
authorize local commits and commit-only application cleanup, subject
to its exclusive-workspace and clean-tree prerequisites. Push, deployment and
permanent artifact purge require their own explicit authorization. Preserve a
blocked or interrupted run for resumption when a required gate is unavailable.

## Install

Register the repository marketplace on the corresponding host:

```bash
claude plugin marketplace add acaprino/daodan
copilot plugin marketplace add acaprino/daodan
codex plugin marketplace add acaprino/daodan
```

Install project-lifecycle@daodan for the complete project paths, or individual
specialists for a narrower task. Required local dependencies form the mandatory
closure; external dependencies must also be available on the host.

The lifecycle uses upstream development methods from
superpowers@claude-plugins-official. Testing uses
mattpocock-skills@mattpocock and developer-essentials@claude-code-workflows.
The [dependency catalog](.claude-plugin/marketplace.json) records the exact declarations.
No upstream method is copied into a second local implementation.

Pi installs the tagged repository as one package:

```bash
pi install git:github.com/acaprino/daodan@v<metadata.version>
```

Select components through package globs in Pi settings. Isolated workers use
pi-subagents; MCP uses pi-mcp-adapter, as declared by the adapter.

OpenCode V2 installs the generated package through npm's repository-path selector:

```bash
opencode plugin add 'github:acaprino/daodan#v<metadata.version>::path:exports/opencode'
```

OpenCode Desktop uses its bundled V2 service. Loader options select plugins and
close mandatory local dependencies; exclusions cannot remove a required dependency.
Use an existing released tag in place of <metadata.version>.

See [host distribution and migration](docs/migration-from-claude-code-daodan.md)
and [the harness migration](docs/migration-to-coherent-harness.md).

The [complete plugin catalog](docs/catalog.md) lists every registered skill, role
and workflow through its plugin page, with mandatory direct and transitive
dependencies. The [host reference](docs/hosts.md) explains the corresponding
commands, paths, installation requirements and runtime limits on each host.

## Canonical owners

| Plugin | Responsibility |
|---|---|
| [project-lifecycle](docs/plugins/project-lifecycle.md) | Complete project work and coordination |
| [project-protocol](docs/plugins/project-protocol.md) | Run identity, snapshots, state, verification and recovery |
| [project-knowledge](docs/plugins/project-knowledge.md) | Durable instructions, guides, documentation and README |
| [senior-review](docs/plugins/senior-review.md) | Unified correctness review, automatic stack specialists and application subtraction |
| [testing](docs/plugins/testing.md) | Meaningful test authoring, suite diagnosis and protection-preserving remediation |
| [abstraction-architect](docs/plugins/abstraction-architect.md) | Concept ownership, duplication and design diagnosis |
| [codebase-xray](docs/plugins/codebase-xray.md) | Static structure, behavior and interconnection evidence |
| [repo-hygiene](docs/plugins/repo-hygiene.md) | Filesystem/Git hygiene and reversible workspace operations |
| [clean-code](docs/plugins/clean-code.md) | Readability with behavior preserved |
| [text-humanizer](docs/plugins/text-humanizer.md) | Voice and clarity of written content |

Knowledge offers instructions, guide, maintain and readme. It distinguishes
approved intent from observed implementation and updates existing documents first.
Operational state never belongs in AGENTS.md or CLAUDE.md.

A failed test can expose a product bug, wrong oracle, environment problem or
flakiness. Testing classifies the cause before quarantine. Refactoring alone does
not retire behavioral protection; count and coverage do not prove equivalence.

The three cleanup owners have different evidence: senior-review understands
application source, testing understands protection, repo-hygiene understands
filesystem and Git. Consolidation manages a run's owned evidence and retention.
It does not grant arbitrary repository deletion.

## Specialist extras

| Area | Independent plugins |
|---|---|
| Languages | [python-development](docs/plugins/python-development.md), [typescript-development](docs/plugins/typescript-development.md), [kotlin-development](docs/plugins/kotlin-development.md) |
| UI and desktop | [react-development](docs/plugins/react-development.md), [frontend-review](docs/plugins/frontend-review.md), [pwa-expert](docs/plugins/pwa-expert.md), [browser-extensions](docs/plugins/browser-extensions.md), [tauri-development](docs/plugins/tauri-development.md), [xterm](docs/plugins/xterm.md) |
| Architecture and infrastructure | [platform-engineering](docs/plugins/platform-engineering.md), [docker](docs/plugins/docker.md), [messaging](docs/plugins/messaging.md), [opentelemetry](docs/plugins/opentelemetry.md), [dependency-audit](docs/plugins/dependency-audit.md) |
| AI and evidence | [ai-tooling](docs/plugins/ai-tooling.md), [rag-development](docs/plugins/rag-development.md), [research](docs/plugins/research.md), [peer-review](docs/plugins/peer-review.md), [app-analyzer](docs/plugins/app-analyzer.md) |
| Product and business | [business](docs/plugins/business.md), [digital-marketing](docs/plugins/digital-marketing.md), [stripe](docs/plugins/stripe.md) |
| Specialized development | [grabber-development](docs/plugins/grabber-development.md), [trading-broker-integration](docs/plugins/trading-broker-integration.md), [libgdx-development](docs/plugins/libgdx-development.md), [obsidian-development](docs/plugins/obsidian-development.md), [csp](docs/plugins/csp.md) |
| Supporting tools | [marketplace-ops](docs/plugins/marketplace-ops.md), [learning](docs/plugins/learning.md), [system-utils](docs/plugins/system-utils.md) |

Extra outputs can be evidence for a project run. Automatic composition requires a
consumer with an explicit hard dependency; the core does not install every domain.
Playwright is required by the browser-facing plugins that declare it. Design
specialists used by frontend-review remain upstream.

## What is verified

The compiler validates kernels, bindings, contracts and generated packages.
Atomic helpers mechanically protect their own records and retained artifacts.
Semantic truth, test oracles and permission provenance still require evidence and
the coordinator's judgment. Prompt obligations are identified as such.

X-ray is static: inventory, files read in depth and runtime-exercised paths are
reported separately. A generated package test is distinct from an installed-host
execution probe. External private app storage is not a supported run root until
its permission binding is demonstrated.

Tri-Tech Code can consume these OpenCode packages and run contracts as an external
application. The marketplace stays public and neutral.

## Contributing

Edit kernels under plugins/ and host mechanisms under adapters/. All exports and
root catalogs are generated. Runtime resources belong under skills/. The toolchain
is stdlib Python; OpenCode's fixed loader uses Node's standard library.

```bash
python scripts/daodan_build.py
python scripts/daodan_build.py --check --support
python -m unittest discover -s tests
python scripts/sync_codex_instructions.py --check
python scripts/sync_plugin_docs.py --check
```

Follow [CLAUDE.md](CLAUDE.md) for dependency, version and publication rules.
[Architecture](docs/superpowers/specs/2026-10-07-daodan-coherent-harness-design.md)
and [implementation plan](docs/superpowers/plans/2026-10-07-daodan-coherent-harness.md)
record this migration. [Behavioral evals](evals/) complement deterministic compiler
and helper tests.

MIT licensed. The Daodan is the symbiote that augments its host.


## Scope-aware knowledge selection

The shared [Skill Catalog](docs/plugins/skill-catalog.md) selects knowledge from
actual available host/project skills for each evidenced task scope. Senior Review
uses it across languages and frameworks with one preparation, delivery ledger,
verification panel and report. Skills declare their own SKILL.toml metadata; adding
a competence needs no new reviewer or central stack table. Selected inputs carry
content fingerprints and per-worker delivery accounting. External unclassified
skills and unavailable inventory remain explicit coverage gaps.
