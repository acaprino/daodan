# Daodan documentation

Daodan coordinates development with AI across project intent, code, tests,
durable knowledge and experimental artifacts. One source is compiled for Claude
Code, GitHub Copilot, Codex, Pi and OpenCode V2.

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

Shared records and recovery belong to [project-protocol](plugins/project-protocol.md).
Instructions, guides and README belong to [project-knowledge](plugins/project-knowledge.md).
[senior-review](plugins/senior-review.md) provides one correctness review, selecting
React, TypeScript and platform dimensions when the target warrants them.
[testing](plugins/testing.md) owns test quality, authoring and remediation.
Language, framework, infrastructure and product extras remain independently useful
and are listed in the catalog.

The names above are neutral workflow IDs. Use the corresponding entry syntax in
the host reference; Codex workflow skills and Pi prompts have different names from
Claude and OpenCode commands.

## Installation and migration

- [Main README](../README.md): introduction and installation.
- [Hosts and exports](hosts.md): packages, environments and runtime requirements.
- [Migration to the coherent harness](migration-to-coherent-harness.md): retired IDs,
  replacements and review coverage changes.
- [Universal host migration](migration-from-claude-code-daodan.md): installation,
  generated catalogs and supported distribution paths.

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
