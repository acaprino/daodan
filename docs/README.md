# Daodan documentation

Daodan coordinates development with AI across project intent, code, tests,
durable knowledge and experimental artifacts. One source is compiled for Claude
Code, GitHub Copilot, Codex, Pi and OpenCode V2.

> [!WARNING]
> **Export parity is not runtime success.** Shared behavior must be corrected in
> kernels, adapters or compiler source, never generated exports. Review all five
> hosts and the complete nested instruction path, with real tools, identities,
> isolation, permissions, dependencies, capture controls and output contracts.
> Agents/coordinators execute; harnesses own supported continuation and state;
> skills describe methods. Turn end and an empty worker are not a delivery.
> Keep registration, adaptation tests and live workflow evidence separate. Follow
> the [mandatory operational review](hosts.md#operational-compatibility-review).

## Find a tool

The [complete plugin catalog](catalog.md) lists every plugin, registered skill,
role and workflow. Each plugin page explains its behavior and includes a checked
reference for component sources, arguments, contracts, mandatory dependencies and
host exports. The [host reference](hosts.md) explains installation, command names,
selection, isolated workers, runtime requirements and enforcement limits.

The catalog is generated from the kernels. Its direct and transitive dependency
tables distinguish local plugins from required external bundles. External
availability and installed-host execution require their own verification.

## Complete project paths

Start with [project-lifecycle](plugins/project-lifecycle.md):

| Path | Result |
|---|---|
| assess | Diagnose incoherence and produce an evidenced plan |
| repair | Apply the identified plan with owned phases and checks |
| change | Develop a feature, fix, refactor, migration or new project |
| verify | Check the actual candidate and its consequences |
| consolidate | Preserve experiment outcomes and manage owned residual output |

Shared records and recovery belong to [work-controller](plugins/work-controller.md).
Instructions, guides and README belong to [project-knowledge](plugins/project-knowledge.md).
[senior-review](plugins/senior-review.md) provides one correctness review, selecting
React, TypeScript and platform dimensions when the target warrants them.
[testing](plugins/testing.md) owns test quality, authoring and remediation.
Language, framework, infrastructure and product extras remain independently useful
and are listed in the catalog.

The names above are neutral workflow IDs. Use the corresponding entry syntax in
the host reference; Codex workflow skills and Pi prompts have different names from
Claude and OpenCode commands.

## Graphs and prototypes

Start with [Understand Daodan's graphs and experiments](graphs/README.md).
Small diagrams explain the code graph (existing code relationships) and the work
graph (dependencies between development activities). Choose a question to find an
experiment, read a worked example, then follow its recorded results and limits.
The work graph is a simulated prototype. The reference sections retain the four
boundary interfaces, real and mocked implementations, and open integration points,
including the duplicated routing policy.

The [code context implementation plan](superpowers/plans/2026-10-23-code-context-and-scope.md)
connects semantic Markdown, Jedi graph evidence and local retrieval through a
progressive scope-selection algorithm. It records planned checkpoints, checks,
documentation updates and intermediate commits; implementation status remains
separate from the design. The [delivery report](superpowers/reports/2026-10-23-code-context-delivery.md)
states what the holdout measured, what the host exports were checked for and
which limits remain; the harness and frozen gold live in
[`evals/codebase-map/context-scope/`](../evals/codebase-map/context-scope/README.md).

## Installation and migration

- [Main README](../README.md): introduction and installation.
- [Hosts and exports](hosts.md): packages, environments and runtime requirements.
- [Migration to the coherent harness](migration-to-coherent-harness.md): retired IDs,
  replacements and review coverage changes.
- [Universal host migration](migration-from-claude-code-daodan.md): installation,
  generated catalogs and supported distribution paths.

## Export compatibility evidence

The [host reference](hosts.md#operational-compatibility-review) describes the
operational review for all five adapters. The
[2026-10-11 audit](superpowers/reports/2026-10-11-host-export-compatibility.md)
records identified instruction, dispatch and permission defects, with source
locations, the 32.10.0 source/rendering corrections, and the distinction between
static checks and live execution. Source and compiler verification do not close
an unmeasured affected runtime path; report that limit explicitly.

## Maintaining the documentation

Edit plugin explanations outside their generated reference markers. Change
component facts in `plugins/<name>/`, host bindings in `adapters/`, then regenerate:

```bash
python scripts/sync_plugin_docs.py
python scripts/sync_plugin_docs.py --check
python scripts/sync_codex_instructions.py
python scripts/sync_codex_instructions.py --check
```

Package behavior still requires rebuilding with `scripts/daodan_build.py`.
Exports and root marketplace catalogs are generated rather than maintained by hand.
See [CLAUDE.md](../CLAUDE.md) for version, dependency and publication rules.

[Agent coordination guidance](references/agent-teams-best-practices.md) combines
current Daodan contracts with explicitly dated vendor evidence. Dated designs,
research, plans and validation reports under `superpowers/` retain historical IDs
and record the evidence for their own versions.
