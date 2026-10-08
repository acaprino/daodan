# Marketplace Ops Plugin

> Audit, scaffold and maintain plugin marketplaces, using the target's source model. Project conventions (author, license, categories and upstream sources) are read from that marketplace.

The first step distinguishes compiler-managed `daodan/v1` kernels from legacy Claude packages authored directly. In a kernel checkout, `kernel-marketplace` owns the procedure: edit neutral source and adapter declarations, then compile every host. Generated exports and root catalogs are inspected as output and never repaired by hand. Native `agents/`, `commands/` and catalog-registration procedures below apply only to the legacy profile.

Command examples and named tools in this guide use Claude notation. For other
hosts, use the entry points and bindings in the source-derived reference below
and [host setup](../hosts.md).

## Agents

### `marketplace-manager`

Marketplace operations manager that identifies the target's source profile before selecting its audit, scaffold or publication procedure.

| | |
|---|---|
| **Model** | inherit |
| **Color** | yellow |
| **Tools** | Read, Write, Edit, Bash, Glob, Grep, WebFetch |
| **Use for** | Adding, auditing, reorganizing, versioning, or syncing plugins |

**Capabilities:**
- **Audit & Validation**: For kernels, check compiler validation, drift and source declarations; for legacy packages, cross-reference catalog entries, files and frontmatter
- **Plugin Scaffolding**: Create the source layout appropriate to the detected profile and validate its registration through that profile's mechanism
- **Version Management**: Semantic versioning for plugins and marketplace
- **Upstream Sync**: Fetch and merge upstream changes while preserving local additions
- **AI Quality Review**: Score descriptions, prompts, and trigger accuracy (1-5 scale)
- **Consolidation Analysis**: Identify overlapping plugins and suggest reorganization

---

## Skills

### `kernel-marketplace`

Canonical maintenance procedure for compiler-managed neutral kernels. It reads `plugin.toml`, durable project instructions and adapters, then routes health checks, content authoring, scaffolding, versioning and publication through their source boundary. On Daodan, the drift command is `python scripts/daodan_build.py --check --support`; source validation includes dependency, registration, bundled-path, fact-anchor and host-vocabulary gates. A new plugin starts at `1.0.0` with explicit capabilities, required dependencies and distinct component names. Workflow source includes its body and TOML sidecar; runtime helper files live under a skill. Source changes and regenerated host packages are reviewed and published together according to the target's authorization and version policy.

### `marketplace-audit`

Native-package structural validation. It can inspect compiled package integrity, but a generated-output finding must be fixed in the kernel declaration or compiler and rebuilt. It is not authority to rewrite a generated catalog.

| | |
|---|---|
| **Invoke** | Skill reference; closest command is `/marketplace-ops:marketplace-health` for structural JSON validation |
| **Use for** | Pre-commit validation, detecting orphaned files, frontmatter checks, color harmony |

**Checks:**
- File existence vs marketplace.json references
- Orphaned files not registered in any plugin
- Frontmatter field validation (agents, skills, commands)
- Color consistency and harmony across plugins
- Naming conventions (kebab-case, filename/name match)
- Version sanity (valid semver)
- marketplace.json schema and duplicate keywords
- Dependency resolution and acyclicity, including the qualified `name@marketplace` form for cross-marketplace entries
- Documentation count drift: the docs index, README counts and every "N plugins" phrase

The audit script takes `--fix` and `--project-root`. Its direct registration fixes belong to the legacy profile; use read-only output checks plus source correction and rebuild for neutral kernels.

### `skills-creator`

Guided creation of plugin components using the detected source profile.

| | |
|---|---|
| **Invoke** | Skill reference or "create a new skill/agent/plugin" |
| **Use for** | Creating skills, agents, commands, or full plugins with real content |

**Workflow:**
1. **Requirements Gathering**: Ask targeted questions about purpose, triggers, plugin placement
2. **Content Generation**: Write production-ready files (not placeholders)
3. **Source Registration**: For kernels, declare components and dependencies in `plugin.toml` and bump source versions; for legacy packages, update the native catalog
4. **Validation**: Verify source declarations, paths, frontmatter and naming, then compile all hosts when the target uses a compiler

Includes a conventions reference with color palette, categories, agent structure patterns, and naming rules, a skills-versus-agents reference, and `scripts/validate_skills.py`, the engine behind `/marketplace-ops:skills-validate` (16 deterministic checks plus a per-component activation score).

---

## Commands

### `/marketplace-ops:marketplace-health`

Quick marketplace health check. For neutral kernels it runs the source/compiler validation and drift procedure. For legacy Claude packages it validates `marketplace.json`, file references, counts and version status.

```
/marketplace-ops:marketplace-health [--fix] [--verbose]
```

In the legacy profile, `--fix` offers catalog repairs with confirmation and a version bump. In the kernel profile, fixes target source declarations and require regeneration; it never adds catalog entries by hand. `--verbose` prints a per-plugin breakdown.

### `/marketplace-ops:marketplace-scaffold-plugin`

Scaffold according to the target's source profile. A neutral plugin gets `plugin.toml`, roles, skills and workflow bodies with sidecars, followed by compiler validation and all-host rendering. A legacy Claude plugin gets native package directories and catalog registration.

```
/marketplace-ops:marketplace-scaffold-plugin my-plugin --with-agent --with-skill --with-command --category development --author "Name"
```

### `/marketplace-ops:marketplace-review`

AI-powered quality review of plugin descriptions, trigger keywords, agent prompts, skill instructions, and command definitions. Writes `.marketplace-review/REPORT.md`.

```
/marketplace-ops:marketplace-review [plugin-name] [--all] [--fix]
```

### `/marketplace-ops:skills-validate`

Deterministic activation-quality checks plus AI-powered body review for all skills and agents.

```
/marketplace-ops:skills-validate my-plugin
/marketplace-ops:skills-validate --all
/marketplace-ops:skills-validate my-plugin --skip-ai
```

**Deterministic checks (script):**
- Directive voice, TRIGGER WHEN / DO NOT TRIGGER WHEN clauses
- Passive pattern detection, description length (hard limit 1024 chars)
- Token budget (total description chars vs 15,000 char budget)
- SKILL.md body size (warn >300 lines, flag >500 lines)
- Agent body size (flag >800 lines)
- Em dash detection, example tags, context: fork, allowed-tools

**AI review dimensions (optional, skip with `--skip-ai`):**
- Structure, Clarity, Redundancy, Progressive disclosure, Tool restrictions, Isolation needs
- Each scored 1-5 with specific fix recommendations

---

**Related:** [project-knowledge](project-knowledge.md) (CLAUDE.md management)

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `2.4.1`. **Source:** [plugin.toml](<../../plugins/marketplace-ops/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | None |
| Direct external | None |
| Local closure (1) | [marketplace-ops](<marketplace-ops.md>) |
| External closure (0) | None |

External bundles are separate upstream installations, not copied local skills.
See [host setup](<../hosts.md>) for selection and availability requirements.

**Required capabilities:** `repository.read`, `shell.execute`, `repository.write`, `network.fetch`, `contexts.isolate`, `roles.dispatch`.
**Optional capabilities:** None.
Optional capabilities are host mechanisms, not optional local plugin dependencies.

### Registered components

Names below are kernel IDs. Host entry points and paths follow the adapter
mapping in [the host reference](<../hosts.md>).
The source links carry the complete instructions and accepted arguments.

| Kind | ID | Purpose and trigger | Source |
|---|---|---|---|
| Skill | `marketplace-ops:marketplace-audit` | Validates the integrity of any Claude Code plugin marketplace. Use PROACTIVELY before any commit that modifies plugin files or marketplace.json. TRIGGER WHEN: verifying marketplace.json integrity, finding orphan plugins/skills/agents/commands, checking dependency resolution or cycles, confirming documented plugin counts still match README and docs tables, or checking naming conventions. DO NOT TRIGGER WHEN: content quality review (use marketplace-review) or scaffolding new plugins (use marketplace-scaffold-plugin / skills-creator). | [marketplace-audit](<../../plugins/marketplace-ops/skills/marketplace-audit/SKILL.md>) |
| Skill | `marketplace-ops:skills-creator` | Creates new Claude Code plugin components: skills, agents, commands, full plugins. Also decides skill vs agent architecture. TRIGGER WHEN: the user asks to create, add, scaffold or build a new skill, agent, command or plugin, or says "new skill", "new agent", "new plugin", "skills-creator", "skills-hammer". DO NOT TRIGGER WHEN: editing or updating an existing component, or auditing marketplace integrity (use marketplace-audit instead). | [skills-creator](<../../plugins/marketplace-ops/skills/skills-creator/SKILL.md>) |
| Skill | `marketplace-ops:kernel-marketplace` | Maintain neutral multi-host plugin kernels through their compiler instead of editing generated host packages. TRIGGER WHEN: marketplace operations target daodan/v1 kernels or compiler-managed exports. DO NOT TRIGGER WHEN: the target is a legacy Claude marketplace with hand-authored native packages. | [kernel-marketplace](<../../plugins/marketplace-ops/skills/kernel-marketplace/SKILL.md>) |
| Role | `marketplace-ops:marketplace-manager` | Maintains any Claude Code plugin marketplace end to end. TRIGGER WHEN: adding, auditing, reorganizing, versioning or syncing plugins, skills, agents and commands; marketplace.json consistency; plugin scaffolding; structural validation. DO NOT TRIGGER WHEN: working on an individual plugin's internal logic (route to the plugin's own agents/skills) or on a non-Claude-Code project. | [marketplace-manager](<../../plugins/marketplace-ops/roles/marketplace-manager.md>) |
| Workflow | `marketplace-ops:marketplace-health` | Quick health check for any Claude Code plugin marketplace. TRIGGER WHEN: the user asks to validate marketplace.json, check plugin file references, report plugin counts and version status, or audit structural integrity. DO NOT TRIGGER WHEN: reviewing plugin content quality (use /marketplace-ops:marketplace-review) or authoring new plugins. | [marketplace-health](<../../plugins/marketplace-ops/workflows/marketplace-health.md>) |
| Workflow | `marketplace-ops:marketplace-review` | Quality review of the content of any Claude Code plugin marketplace. TRIGGER WHEN: the user asks to review plugin, agent or skill quality, audit descriptions or trigger keywords, or evaluate activation accuracy and cross-plugin coherence. DO NOT TRIGGER WHEN: just validating marketplace.json structure (use /marketplace-ops:marketplace-health) or authoring new components (use /marketplace-ops:marketplace-scaffold-plugin). | [marketplace-review](<../../plugins/marketplace-ops/workflows/marketplace-review.md>) |
| Workflow | `marketplace-ops:marketplace-scaffold-plugin` | Scaffold a new plugin for any Claude Code plugin marketplace. TRIGGER WHEN: the user asks to create a new plugin, bootstrap plugin structure, or add a new entry to marketplace.json. DO NOT TRIGGER WHEN: adding a skill or agent to an existing plugin (use skills-creator). | [marketplace-scaffold-plugin](<../../plugins/marketplace-ops/workflows/marketplace-scaffold-plugin.md>) |
| Workflow | `marketplace-ops:skills-validate` | Validate skill and agent quality: deterministic activation checks plus AI body review. TRIGGER WHEN: the user asks to validate skill/agent quality, enforce trigger patterns, check description token budgets, or run pre-commit marketplace checks. DO NOT TRIGGER WHEN: checking structural JSON references only (use /marketplace-ops:marketplace-health) or doing an AI-only content review (use /marketplace-ops:marketplace-review). | [skills-validate](<../../plugins/marketplace-ops/workflows/skills-validate.md>) |

### Workflow contracts

Contracts describe observable outputs; Markdown bodies define decisions,
flags, safety gates and execution. Declared `invoke` execution is unsupported.

#### `marketplace-ops:marketplace-health`

**Arguments:** `[--fix] [--verbose]`

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `marketplace-health-completed` |
| Artifacts | `marketplace-health-report` |
| Schemas | None declared |
| Declared workers | `marketplace-ops/marketplace-manager` |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [marketplace-health.toml](<../../plugins/marketplace-ops/workflows/marketplace-health.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `scope` | None | None | `shared` | None declared | `preferred` |
| `review` | `scope` | `marketplace-manager` | `required` | None declared | `preferred` |

#### `marketplace-ops:marketplace-review`

**Arguments:** `[plugin-name] [--all] [--fix]`

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `marketplace-review-completed` |
| Artifacts | `marketplace-review-report` |
| Schemas | None declared |
| Declared workers | `marketplace-ops/marketplace-manager` |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [marketplace-review.toml](<../../plugins/marketplace-ops/workflows/marketplace-review.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `scope` | None | None | `shared` | None declared | `preferred` |
| `review` | `scope` | `marketplace-manager` | `required` | None declared | `preferred` |

#### `marketplace-ops:marketplace-scaffold-plugin`

**Arguments:** <code>&lt;plugin-name&gt; [--with-agent] [--with-skill] [--with-command] [--category &lt;cat&gt;] [--author &lt;name&gt;]</code>

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `marketplace-scaffold-plugin-completed` |
| Artifacts | `marketplace-scaffold-plugin-report` |
| Schemas | None declared |
| Declared workers | `marketplace-ops/marketplace-manager` |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [marketplace-scaffold-plugin.toml](<../../plugins/marketplace-ops/workflows/marketplace-scaffold-plugin.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `scope` | None | None | `shared` | None declared | `preferred` |
| `review` | `scope` | `marketplace-manager` | `required` | None declared | `preferred` |

#### `marketplace-ops:skills-validate`

**Arguments:** `[plugin-name] [--all] [--skip-ai]`

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `skills-validate-completed` |
| Artifacts | `skills-validate-report` |
| Schemas | None declared |
| Declared workers | `marketplace-ops/marketplace-manager` |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [skills-validate.toml](<../../plugins/marketplace-ops/workflows/skills-validate.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `scope` | None | None | `shared` | None declared | `preferred` |
| `review` | `scope` | `marketplace-manager` | `required` | None declared | `preferred` |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/marketplace-ops](<../../exports/claude/plugins/marketplace-ops>) | `native` | `marketplace-health: native-team`, `marketplace-review: native-team`, `marketplace-scaffold-plugin: native-team`, `skills-validate: native-team` |
| copilot | [exports/copilot/plugins/marketplace-ops](<../../exports/copilot/plugins/marketplace-ops>) | `native` | `marketplace-health: parallel-subagents`, `marketplace-review: parallel-subagents`, `marketplace-scaffold-plugin: parallel-subagents`, `skills-validate: parallel-subagents` |
| codex | [exports/codex/plugins/marketplace-ops](<../../exports/codex/plugins/marketplace-ops>) | `adapted` | `marketplace-health: parallel-subagents`, `marketplace-review: parallel-subagents`, `marketplace-scaffold-plugin: parallel-subagents`, `skills-validate: parallel-subagents` |
| pi | [exports/pi/plugins/marketplace-ops](<../../exports/pi/plugins/marketplace-ops>) | `adapted` | `marketplace-health: parallel-subagents`, `marketplace-review: parallel-subagents`, `marketplace-scaffold-plugin: parallel-subagents`, `skills-validate: parallel-subagents` |
| opencode | [exports/opencode/plugins/marketplace-ops](<../../exports/opencode/plugins/marketplace-ops>) | `native` | `marketplace-health: parallel-subagents`, `marketplace-review: parallel-subagents`, `marketplace-scaffold-plugin: parallel-subagents`, `skills-validate: parallel-subagents` |

<!-- daodan:reference:end -->
