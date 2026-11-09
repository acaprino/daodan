# Daodan

<p align="center">
  <img src="docs/assets/branding/daodan-logo-xenotron-glow.png" alt="Daodan logo" width="560">
</p>

<p align="center">
  <strong>Plugin harness for LLM coding agents: a verifiable map of the code and a composed, evidence-bound review.</strong>
</p>

Daodan gives a coding agent two things it cannot get from a prompt: a local,
refreshable understanding of the repository, and a review whose findings cite
source and survive independent verification. Everything is static analysis
plus instructions; sources remain the authority and runtime behavior needs the
project's tests.

## Plugins

| Plugin | Responsibility | Entry |
|---|---|---|
| [Codebase Map](plugins/codebase-map/README.md) | Inventory, symbols, relationships, semantic descriptions with provenance, build units and modules, served to the agent on demand | `skills/map`, MCP tools `codebase_map_*` |
| [senior-review](plugins/senior-review/README.md) | Review of a change, branch, PR, plan or document: measured roster, focused auditors composed per review, evidenced findings, adversarial verification, coverage gaps | `skills/review-method` |

senior-review depends on Codebase Map; Codebase Map stands alone.

## How it works

1. **Map.** `snapshot.py write` records files, symbols, imports, calls and
   manifests in a local SQLite snapshot and derives the module graph; semantic
   cards and the interconnect map are produced by the map method and bound to the
   snapshot digest, so a stale description is detectable.
2. **Ask.** The agent queries the map through the MCP tools (`codebase_map_search`,
   `_outline`, `_read`, `_edit_impact`, `_modules`, …) or `snapshot.py` instead of
   reading the tree; results carry `file:line` and status.
3. **Review.** The model reads the request and decides the rigor (`quick`,
   `standard`, `deep`); `review_roster.py` adds a floor from risk signals and fixes
   the verification level. The coordinator understands the object and chooses the
   reviewers by reading their mandates; `composition.py` binds the chosen reviewers
   into isolated jobs made of focused role files; each finding declares premise,
   provenance, trigger and evidence class; a verification panel scaled to the rigor
   tries to falsify it; the report lists findings, questions for the author and
   coverage gaps.

Roles cover one defect class each (authorization, transaction integrity,
temporal resilience, …) and are composed into larger reviewers in
`plugins/senior-review/plugin.toml`; the light review and the quick and standard
automatic rosters use the `code-auditor` composition.

## Install

```text
claude plugin marketplace add acaprino/daodan
claude plugin install codebase-map@daodan
claude plugin install senior-review@daodan
```

From a checkout, `claude plugin marketplace add <path>` registers the folder
instead. The map entry is the skill `/codebase-map:map <request>`; the
`codebase-map` MCP server starts with the plugin under `uv`. `/reload-plugins`
re-reads the plugin files but does not restart that server.

## Requirements

- Python ≥ 3.12, standard library for the scripts; the MCP server runs under
  `uv`, which provisions `mcp`. `tree-sitter`, `sqlglot`, `scip`/`jedi` optional
  for higher-fidelity parsing and resolution.
- A host that can run shell commands and dispatch isolated agent contexts.
  Plugin content is host-generic; command and worker bindings come from the host.

## Documentation

- [Design: Codebase Map and semantic review](docs/specs/2026-11-03-semantic-review-foundation.md)
- [Codebase Map reference](docs/plugins/codebase-map.md)
- [Research: context building](docs/research/context-building-research.md) · [Research: prompt design and brevity](docs/research/prompt-engineering-and-brevity.md)
- Flows, in three phases: [1, working run and review rules](docs/specs/2026-11-09-working-run-and-review-fixes.md) · [2, flows and units](docs/specs/2026-11-09-flow-model.md) · [3, do they help review](docs/specs/2026-11-09-flows-in-review.md) · [literature](docs/research/2026-11-09-flow-reconstruction-literature.md)
- [Working rules for agents in this repository](AGENTS.md)

## License

[MIT](LICENSE)
