# Project Knowledge

Project Knowledge owns durable instructions, project guides, technical document
maintenance and README work. It updates existing authoritative documents before
creating parallel copies, distinguishes implemented behavior from approved
intent, and records execution state outside durable instructions.

Command examples and named tools in this guide use Claude notation. For other
hosts, use the entry points and bindings in the source-derived reference below
and [host setup](../hosts.md).

## Entry points

The plugin has no command of its own. `/daodan:write-docs` routes the request and loads the method it needs:

| Request | Method | Default |
|---|---|---|
| Nothing, or "update the docs" | `project-knowledge:project-knowledge`: generic and twenty-dimension documentation drift, then the authorized corrections | Audit-only |
| Reorganize Daodan documentation and plugin dossiers | `project-knowledge:documentation-organizer`, through the documentation method | Inventory and owned mapping before authorized edits |
| A guide, onboarding, architecture, flows, operations | `project-knowledge:project-knowledge`, its guide method: an audience/file plan, then the needed project guide | Plan before writing |
| The README | `project-knowledge:readme-craft`: check or author README while preserving facts and author voice | Audit-only |
| Instructions, CLAUDE.md, AGENTS.md | `project-knowledge:instructions-method`: audit host/project instructions; create or maintain the authoritative destination | Audit-only |

Decision records and the delivery cycle belong to `project-delivery`.
`/daodan:record-decision` loads `project-delivery:adr-method`; [Decision records](../decision-records.md)
explains their content, approval lifecycle and use during delivery.

## Documentation organization

The organizer uses a [common per-plugin dossier contract](../../plugins/project-knowledge/skills/project-knowledge/references/documentation-organization.md)
for functional/technical specifications, use cases and tutorials, research and papers,
validation, dependencies, intakes and licenses. It maps existing material to
owners and destinations while preserving evidence and meaningful content.

Provenance includes delegated runtimes, tools, models and parsers alongside
adapted source: for example Craft engines, Worktrunk, EmbeddingGemma and
tree-sitter. Records distinguish actual adoption date and Daodan/upstream
versions from a later check, available release or installation observed in a run.
Missing facts remain explicit gaps.

No new files or in-place edits belong under `docs/superpowers/`. Each existing
artifact considered for relocation or retirement needs its own recorded human
decision on retention and destination. Unanswered documents stay intact while
independent authorized work continues. Creating the organizer does not migrate
existing documents or grant new upstream adoptions.

The former flags are now the methods' modes: audit-only, plan-only where
supported, fix and commit. The audit comes first; creating a new instruction file
or README, applying authorized changes and committing are authorizations asked
when a step needs them, once, and recorded in the run. A caller's existing run and
authorization are reused. Reports belong to the owned `.daodan/runs/<id>/`;
application changes only the files in the authorized plan.

## Reusable methods and roles

The `project-knowledge` skill contains preparation, twenty-dimension drift audit,
guide and application methods, audience adaptation and diagram techniques.
`instructions-method` selects scoped authoritative instruction destinations and
holds working principles, condensed test rules and an instruction example.

Instruction maintenance checks the active host, configuration, scopes and loading
evidence. A present file, an import and a plain link have different effects;
regeneration and parity do not prove that an existing session loaded the update.
Project test policy records verified commands, prerequisites, isolation and oracle
authority using established local conventions. Templates supply examples rather
than universal coverage thresholds or mandatory directory layouts.
`readme-craft` holds README preparation, audit and application techniques.

`instructions-auditor`, `documentation-engineer` and `guide-reviewer` accept
explicit audit-only mode. They return evidence, provenance, scope and unavailable
checks rather than automatically editing their findings. The context explorer
prepares an identified run. Overview, technical, flow, onboarding and operational
writers receive exact owned files and readers. The operational writer owns both
reference and configuration how-to, sharing one verified input set.

Document structure editing belongs to `doc-humanizer`; voice editing belongs to
[text-humanizer](text-humanizer.md). A guide is not a
mandatory numbered package, and no minimum document, line or open-question count
is required. A missing or failed worker remains an explicit delivery failure.

## Dependencies and evidence

Required local dependencies are `work-controller`, `codebase-map`,
`text-humanizer`, `senior-review` and `report-rendering`. Dispatch and concurrency use host mechanisms
from the adapters; no team-only plugin is required merely to write a guide.

Codebase Map remains static. Its exact run, target and snapshot are bound before reuse;
an older mirror is not proof of current implementation. Claims preserve status
and premise provenance. A wrong document, a wrong implementation and unresolved
product intent remain different findings.

The explorer loads `codebase-map:map-method` by name for source-reading helper
commands and passes the identified run's exact `snapshot/manifest.json` onward.
It checks analysis changes with `snapshot.py diff --verify`, which normalizes
line endings. After each verified diff it always writes or obtains a current
owned source manifest with `snapshot.py write --reuse` before passing it to
readers, even for `none` or LF/CRLF-only differences. Supported parent claims
retain their evidence lineage; they do not prove the exact current bytes the
reader requires. The parent run is preserved. The
outline guides autonomous symbol selection; validated source blocks supply
definitions and shared file/class context. The explorer expands to callers,
callees, gates, invariants, configuration and applicable CSS/markup as each claim
requires. Outline metadata does not count as deep reading, and retained context
does not prove omitted function bodies irrelevant. Inventory, files/ranges read
and runtime evidence remain separate coverage facts. Generated bindings and
parity checks do not establish that a live host loaded the updated skill.

Successful application requires relevant source/link checks, current inputs and
accounted deliveries. Generated documents remain under their generator's
ownership. Commands copied from manifests are labelled unexercised unless an
allowed project verification actually ran.

**Related:** [codebase-map](codebase-map.md), [senior-review](senior-review.md),
[testing](testing.md), [text-humanizer](text-humanizer.md).

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `3.2.1`. **Source:** [plugin.toml](<../../plugins/project-knowledge/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | [codebase-map](<codebase-map.md>), [report-rendering](<report-rendering.md>), [research](<research.md>), [senior-review](<senior-review.md>), [text-humanizer](<text-humanizer.md>), [work-controller](<work-controller.md>) |
| Direct external | None |
| Local closure (16) | [abstraction-architect](<abstraction-architect.md>), [codebase-map](<codebase-map.md>), [dependency-audit](<dependency-audit.md>), [platform-engineering](<platform-engineering.md>), [project-knowledge](<project-knowledge.md>), [python-development](<python-development.md>), [react-development](<react-development.md>), [repo-hygiene](<repo-hygiene.md>), [report-rendering](<report-rendering.md>), [research](<research.md>), [senior-review](<senior-review.md>), [skill-catalog](<skill-catalog.md>), [testing](<testing.md>), [text-humanizer](<text-humanizer.md>), [typescript-development](<typescript-development.md>), [work-controller](<work-controller.md>) |
| External closure (2) | `developer-essentials@claude-code-workflows`, `mattpocock-skills@mattpocock` |

External bundles are separate upstream installations, not copied local skills.
See [host setup](<../hosts.md>) for selection and availability requirements.

**Required capabilities:** `network.fetch`, `repository.read`, `shell.execute`, `repository.write`, `contexts.isolate`, `roles.dispatch`.
**Optional capabilities:** `execution.parallel`.
Optional capabilities are host mechanisms, not optional local plugin dependencies.

### Registered components

Names below are kernel IDs. Host entry points and paths follow the adapter
mapping in [the host reference](<../hosts.md>).
The source links carry the complete instructions and accepted arguments.

| Kind | ID | Purpose and trigger | Source |
|---|---|---|---|
| Skill | `project-knowledge:project-knowledge` | Prepare, audit and maintain durable project documentation with a file/audience plan. Load when writing guides, reconciling document drift or coordinating knowledge work. | [project-knowledge](<../../plugins/project-knowledge/skills/project-knowledge/SKILL.md>) |
| Skill | `project-knowledge:instructions-method` | Create, audit and maintain durable project instructions in AGENTS.md, CLAUDE.md or the target host's instruction file. TRIGGER WHEN: auditing, creating or updating AGENTS.md, CLAUDE.md or durable project instruction files. | [instructions-method](<../../plugins/project-knowledge/skills/instructions-method/SKILL.md>) |
| Skill | `project-knowledge:readme-craft` | Create or audit README.md from verified project facts, retaining author voice and proportional information architecture. TRIGGER WHEN: creating, auditing or updating README.md. | [readme-craft](<../../plugins/project-knowledge/skills/readme-craft/SKILL.md>) |
| Role | `project-knowledge:codebase-explorer` | Prepare scoped project context and audience evidence for an identified knowledge run, preserving implemented behavior and approved intent separately. TRIGGER WHEN: spawned by project-knowledge methods to gather repository context before writing or auditing docs. | [codebase-explorer](<../../plugins/project-knowledge/roles/codebase-explorer.md>) |
| Role | `project-knowledge:doc-humanizer` | Restructure existing technical documents for their planned readers without changing facts, code examples or author voice. TRIGGER WHEN: spawned by project-knowledge methods to restructure technical documentation. DO NOT TRIGGER WHEN: editing prose voice (use text-humanizer). | [doc-humanizer](<../../plugins/project-knowledge/roles/doc-humanizer.md>) |
| Role | `project-knowledge:documentation-engineer` | Audit implementation drift across selected documentation dimensions or author scoped technical documentation; supports explicit audit-only mode. TRIGGER WHEN: dispatched by project-knowledge's documentation audit (/daodan:write-docs) or lifecycle knowledge phases to audit or repair documentation drift. | [documentation-engineer](<../../plugins/project-knowledge/roles/documentation-engineer.md>) |
| Role | `project-knowledge:documentation-organizer` | Organize Daodan plugin dossiers and trace dependency/intake provenance. TRIGGER WHEN: dispatched for documentation restructuring, per-plugin specifications or knowledge migration. DO NOT TRIGGER WHEN: auditing prose drift alone (use documentation-engineer). | [documentation-organizer](<../../plugins/project-knowledge/roles/documentation-organizer.md>) |
| Role | `project-knowledge:flow-writer` | Document scoped user and data flows from verified call paths and contracts. TRIGGER WHEN: dispatched by project-knowledge's guide method (/daodan:write-docs) to author user and data flow documentation. | [flow-writer](<../../plugins/project-knowledge/roles/flow-writer.md>) |
| Role | `project-knowledge:guide-reviewer` | Review planned guide files for factual contradictions, provenance, terminology and navigation; defaults to audit-only and does not become another writer. TRIGGER WHEN: dispatched by project-knowledge's guide method (/daodan:write-docs) to verify authored guide files. | [guide-reviewer](<../../plugins/project-knowledge/roles/guide-reviewer.md>) |
| Role | `project-knowledge:instructions-auditor` | Audit durable project instruction claims, scoped destinations, references and duplication; explicit audit-only mode never edits instruction files. TRIGGER WHEN: dispatched by project-knowledge:instructions-method (/daodan:write-docs) or lifecycle knowledge phases to audit AGENTS.md/CLAUDE.md. | [instructions-auditor](<../../plugins/project-knowledge/roles/instructions-auditor.md>) |
| Role | `project-knowledge:onboarding-writer` | Write verified reader-specific onboarding and real open questions. TRIGGER WHEN: dispatched by project-knowledge's guide method (/daodan:write-docs) to author onboarding documentation. | [onboarding-writer](<../../plugins/project-knowledge/roles/onboarding-writer.md>) |
| Role | `project-knowledge:ops-writer` | Own operational reference and configuration how-to, absorbing the former config writer's techniques. TRIGGER WHEN: dispatched by project-knowledge's guide method (/daodan:write-docs) to author operational and configuration documentation. | [ops-writer](<../../plugins/project-knowledge/roles/ops-writer.md>) |
| Role | `project-knowledge:overview-writer` | Explain the project and implemented features for planned audiences. TRIGGER WHEN: dispatched by project-knowledge's guide method (/daodan:write-docs) to author project overview documentation. | [overview-writer](<../../plugins/project-knowledge/roles/overview-writer.md>) |
| Role | `project-knowledge:tech-writer` | Document the verified stack, architecture and data model in planned files. TRIGGER WHEN: dispatched by project-knowledge's guide method (/daodan:write-docs) to author technical architecture and data-model documentation. | [tech-writer](<../../plugins/project-knowledge/roles/tech-writer.md>) |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/project-knowledge](<../../exports/claude/plugins/project-knowledge>) | `native` | No workflow entry points |
| copilot | [exports/copilot/plugins/project-knowledge](<../../exports/copilot/plugins/project-knowledge>) | `native` | No workflow entry points |
| codex | [exports/codex/plugins/project-knowledge](<../../exports/codex/plugins/project-knowledge>) | `adapted` | No workflow entry points |
| pi | [exports/pi/plugins/project-knowledge](<../../exports/pi/plugins/project-knowledge>) | `adapted` | No workflow entry points |
| opencode | [exports/opencode/plugins/project-knowledge](<../../exports/opencode/plugins/project-knowledge>) | `native` | No workflow entry points |

<!-- daodan:reference:end -->
