# Hosts, exports and runtime requirements

Daodan has one content source and five host adapters: Claude Code, GitHub Copilot,
Codex, Pi and OpenCode V2. The project lifecycle and specialists keep the same
meaning across hosts; entry names, registration and worker dispatch follow each
adapter. This page documents the implementation in this repository. A rendered
package or passing compiler test does not prove that a newly installed host has
executed the workflow successfully.

Start with the [plugin and dependency catalog](catalog.md) and
[lifecycle migration guide](migration-to-coherent-harness.md) to choose tools.
Required providers are part of each plugin's installation, including providers
used by composed methods. Domain specialists can also be used independently.

## Installation and selection

The three marketplace hosts register the repository root and install a selected
plugin. `project-lifecycle` is the coordinated development entry; replace it with
another plugin ID for an independent tool.

```bash
claude plugin marketplace add acaprino/daodan
claude plugin install project-lifecycle@daodan

copilot plugin marketplace add acaprino/daodan
copilot plugin install project-lifecycle@daodan

codex plugin marketplace add acaprino/daodan
codex plugin install project-lifecycle@daodan
```

The generated marketplace catalogs contain required dependency declarations and
an `allowCrossMarketplaceDependenciesOn` list derived from qualified foreign
dependencies. Register or provision the required foreign marketplaces as part of
installation. The declarations do not prove upstream availability or installation
in a particular user profile.

Pi installs the repository package from a released tag. Replace
`<metadata.version>` with a published release version.

```bash
pi install git:github.com/acaprino/daodan@v<metadata.version>
```

Pi's root `package.json` discovers the rendered prompts and skills through globs.
Selection belongs in the object form of its package settings, through prompt and
skill filters. Filtering does not resolve plugin dependencies: keep the complete
local dependency closure, including role skills and provider skills. An isolated
workflow also needs the companion package named by the adapter:

```bash
pi install npm:pi-subagents
```

Install `pi-mcp-adapter` when using a declared MCP server and configure that server
as described below. Companions are host mechanisms, separate from the Daodan
plugin graph.

OpenCode V2 installs the generated package inside the tagged repository:

```bash
opencode plugin add 'github:acaprino/daodan#v<metadata.version>::path:exports/opencode'
```

Its loader accepts `options.plugins` and `options.exclude` in the plugin
configuration:

```json
{
  "package": "github:acaprino/daodan#v<metadata.version>::path:exports/opencode",
  "options": {
    "plugins": ["project-lifecycle"]
  }
}
```

The loader adds all transitive local providers of selected plugins. An exclusion
cannot remove a provider that a selected plugin requires; the override is logged.
An omitted selection loads every local plugin. OpenCode Desktop uses the same
V2 plugin package as its CLI service; there is no separate Desktop export.

Pi and OpenCode package all local kernels but do not install plugins from foreign
marketplaces. Qualified dependencies such as `superpowers@claude-plugins-official`
still have to be supplied in a form the host can load. Packaging the entire local
marketplace is not proof that every workflow's external inputs are available.

## Required dependency behavior

The canonical dependency declarations live in `plugins/<plugin>/plugin.toml`.
Every local runtime provider is mandatory, including shared-contract providers and
workers declared by a composed method. There are no optional local dependencies
or installed-check fallbacks. External references use `plugin@marketplace`.

The compiler validates provider references and the dependency linter checks
runtime use, missing declarations and unused local edges. The three generated
marketplace catalogs retain qualified required dependencies. OpenCode's loader
manifest retains the local graph for selection; Pi's glob manifest carries no
per-plugin graph. Neither host should silently continue a workflow with a missing
required external skill or worker.

Consult each [plugin page](plugins/) for direct requirements and the
[dependency catalog](catalog.md#mandatory-dependency-edges) for transitive
installation cost. Installing the core
lifecycle is a larger choice than installing a leaf tool such as repo-hygiene or
project-protocol.

senior-review has one review engine across code, team and PR entries. Its React,
TypeScript and platform providers are mandatory installation dependencies; target
signals decide which workers run. The lifecycle's candidate reviews use that same
engine and expose those provider bindings on every host. Independently callable
specialist commands remain in their domain plugins.

## Component and entry mapping

Paths below are relative to a generated `exports/<host>/plugins/<plugin>/` package,
except the catalogs. A workflow becomes the user entry shown here; a knowledge
skill remains a skill, and a role remains a worker body even on hosts that render
it as a skill file.

| Host | Catalog | Workflow entry | Worker role | Knowledge skill |
|---|---|---|---|---|
| Claude | `.claude-plugin/marketplace.json` | `commands/<workflow>.md`, `/<plugin>:<workflow>` | `agents/<role>.md` | `skills/<skill>/SKILL.md` |
| Copilot | `.github/plugin/marketplace.json` | `prompts/<workflow>.prompt.md`; dispatched entries also get `agents/<workflow>-coordinator.agent.md` | `agents/<role>.agent.md` | `skills/<skill>/SKILL.md` |
| Codex | `.agents/plugins/marketplace.json` | `skills/<workflow>-workflow/SKILL.md`, named `<workflow>-workflow` | `roles/<role>.md`, passed inline to a runtime subagent | `skills/<skill>/SKILL.md` |
| Pi | root `package.json` | `prompts/<plugin>-<workflow>.md`, `/<plugin>-<workflow>` | `skills/<plugin>-<role>/SKILL.md`, hidden from automatic model invocation and passed inline | `skills/<skill>/SKILL.md` |
| OpenCode V2 | `exports/opencode/package.json` | `commands/<workflow>.md`, registered as `/<plugin>:<workflow>` | `agents/<role>.md`, registered as `<plugin>:<role>` | `skills/<skill>/SKILL.md`, registered as `<plugin>:<skill>` |

For `project-lifecycle:assess`, that means `/project-lifecycle:assess` on Claude
and OpenCode, `assess-workflow` on Codex, and `/project-lifecycle-assess` on Pi.
Copilot exposes the `assess` prompt and generated `assess-coordinator` agent.
The prompt loads the method; the coordinator agent carries the execution harness
and worker allowlist. Select that coordinator for the isolated dispatch contract.

Codex keeps its `-workflow` suffix for stable installed names. Names cannot repeat
across component kinds within a kernel. The compiler does not turn generated
dispatch resources or contract files into extra user commands.

## Dispatch and isolation

The sidecar can describe workers in the phase graph and in `[dispatch].roles`.
The latter covers workers selected by a loaded canonical method, without invented
scheduling phases. Harness rendering activates for declared dispatch workers,
`inline_workers`, or phase fan-out. Coordination selection also respects
`[dispatch].isolated` and required phase isolation. A shared coordinator phase does
not authorize a required worker to run in the coordinator's context.

| Host | Rendered worker mechanism | Runtime requirement |
|---|---|---|
| Claude | Installed named agents; Agent Teams when enabled, otherwise isolated subagents | An available isolated worker mechanism |
| Copilot | Named custom agents behind the generated coordinator allowlist | Agent dispatch and the required custom agents |
| Codex | Full role body in an isolated runtime subagent prompt | Runtime subagent support; role files alone are not registered native agents |
| Pi | Full role body in a companion subagent prompt | `pi-subagents` for required isolation |
| OpenCode V2 | Loader-registered agents with `mode: subagent`, dispatched through `subagent` | The generated loader must register each required agent |

On Codex and Pi, referenced roles owned by another plugin are generated under
`contracts/dispatch/<owner>/<role>.md`. Each resource records owner, provider
version and canonical source digest. It is not registered as a skill or agent.
Helper paths and unqualified skill loads belong to the original provider, whose
root is resolved from its installed skill, never from the generated resource.

`inline_workers = true` permits only project-protocol's `isolated-worker` for a
method-owned task with explicit scope, permission, budget and report path. It does
not grant access to every role in the registry.

The coordinator records every dispatched worker as delivered or failed before
closing its phase. Missing results remain visible. Independent reviewers do not
read peer results before their own delivery. Workers get assigned intermediate
report paths; the final report has one exclusive owner in its declaring phase.

Parallelism can vary according to the contract. Pi stops an isolation-required
workflow if its companion tool is missing. OpenCode stops on an unknown agent.
Neither condition permits a shorter report pretending the worker ran.

## Schemas, methods and shipped resources

Kernels export public schemas with `[contracts].exports`. A consumer's
`[contract].shared_schemas` references the required provider and exported
`contracts/` path. Project-protocol owns work and project-result contracts;
senior-review retains its native finding and delivery contracts.

Provider packages contain the canonical schema files. Consumer sidecars ship as
`contracts/<workflow>.workflow.toml`, preserving qualified shared references.
Local `[contract].schemas` remains available for a workflow's own domain schemas.
There is no second hand-authored operational schema under each consumer skill.

The coordinator loads canonical specialist methods and prepares their inputs.
The compiler supplies worker bindings; it is not a general workflow executor.
Nonempty `invoke` is rejected. The existing same-context X-ray method step does
not create a general mechanism for one workflow to execute another.

## MCP and helper runtimes

A plugin-declared MCP server lives under a skill, requires `mcp.servers`, and is
declared through `[[mcp.servers]]` in the kernel. Peer-review declares its server
with `uv run --script .../server.py`; users need that executable and the server's
own documented requirements.

| Host | Generated MCP mechanism |
|---|---|
| Claude | Plugin-root `.mcp.json` and a catalog `mcpServers` pointer |
| Copilot, Codex | Shipped server and workflow note with the exact registration command |
| Pi | Shipped server and registration note; `pi-mcp-adapter` reads the configured `mcpServers` entry |
| OpenCode V2 | Loader registers declared servers from the package manifest through its MCP transform; existing user entries are preserved |

The Copilot, Codex and Pi bindings remain registration instructions, not a claim
that an installed plugin automatically starts its server. The OpenCode binding
is adapted because registration comes from the loader.

Building Daodan needs Python 3.11 or later and uses the standard library. Node is
needed to exercise the OpenCode loader tests. Runtime helpers use their documented
executables; optional tree-sitter parsers improve X-ray parsing, while its tested
fallback remains available. No Node build is required for the generated packages.

## Write boundaries and Tri-Tech Code

Run records and outputs belong in `.daodan/runs/<id>/` inside an identified
project/worktree. An alternative output root must be dedicated, remain inside that
project, not equal the project root, and carry a `.daodan-root` sentinel. X-ray's
separate stable contract stays `.codebase-xray/`.

Run-state and artifact helpers mechanically check their paths, link identities,
owned output scope and record transitions. Those checks apply to helper actions.
General agent-tool confinement stays prompt-level on all five hosts:
`run-write-confinement` and X-ray's policy both declare `mechanical_wired = false`.
The Copilot X-ray guard is shipped and tested but is not wired as a hook. A
session-global confinement hook would also block unrelated project writes.

OpenCode worker permissions are generated from declared role tools and include an
`external_directory` allowance confined to the installed package. This allows
reading bundled references outside the project; it grants no arbitrary private
app output directory. Tri-Tech Code is an external OpenCode consumer, not a sixth
Daodan adapter. Out-of-project private storage needs a separately proved permission
binding and is outside the implemented `--out` contract.

JSON validation and helper checks cannot establish the truth of reported evidence
or that a human actually granted a permission. Runtime authorization and semantic
review remain separate responsibilities. X-ray remains static: inventory, depth
of reading and runtime exercise are distinct coverage claims.

## Export maintenance and verification

Author plugin content under `plugins/` and host mechanisms under `adapters/`.
Everything under `exports/`, all marketplace catalogs and both package manifests
are generated. The builder validates and stages all five hosts before publishing
the new tree. It recognizes retired generated plugin trees by validated provenance;
unknown trees and links block removal rather than becoming cleanup targets.

```bash
python scripts/daodan_build.py
python scripts/daodan_build.py --check --support
python scripts/sync_plugin_docs.py --check
python scripts/sync_codex_instructions.py --check
python scripts/lint_dependency_graph.py
python scripts/lint_bundled_paths.py
python scripts/lint_plugin_registration.py
python scripts/lint_host_vocabulary.py
python -m unittest discover -s tests
python adapters/copilot/policies/xray-guard/test_xray_guard.py
```

`--host` may narrow only a check. Publication always builds all five hosts.
Required capability gaps or an impossible coordination contract block publication.
Each package records kernel digest, selected strategies and applied overrides in
`.daodan-provenance.json`. A semantic override is fingerprinted against its source
and fails when that source changes.

Compiler tests prove rendering, registration, confinement helpers and parity.
[Historical host probes](../tests/host-probes/README.md) describe the fixtures they
measured; they do not establish installed-host behavior for the redesigned
lifecycle. Consult the [validation report](superpowers/reports/2026-10-07-daodan-harness-validation.md)
for the measured release evidence and its limits.
