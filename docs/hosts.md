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

> [!WARNING]
> **Installed components and rendered packages do not establish a completed task.**
> Shared fixes belong in kernels, adapters or compiler source, followed by all five
> exports and their nested instruction paths; generated files are never a repair
> surface. Verify real tools and input fields, component kinds/IDs, single-worker
> isolation, models, permissions, required providers for the active host, browser
> stdin/stop/background control, and helper/contract/result-reader output binding.
> Agents perform and verify the task; the coordinator owns deliveries and the
> final report. The harness owns supported continuation and state; loading a skill
> supplies a method, not an executor. A finished turn, idle host or empty worker
> response cannot establish success. Keep structural registration, adaptation
> tests, installed-host fixtures and the affected live workflow as separate evidence.

## Installation and selection

The three marketplace hosts register the repository root and install a selected
plugin. `project-delivery` is the coordinated development entry; replace it with
`project-lifecycle` for assessment and maintenance, or another plugin ID for an
independent tool.

```bash
claude plugin marketplace add acaprino/daodan
claude plugin install project-delivery@daodan

copilot plugin marketplace add acaprino/daodan
copilot plugin install project-delivery@daodan

codex plugin marketplace add acaprino/daodan
codex plugin add project-delivery@daodan
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
    "plugins": ["project-delivery"]
  }
}
```

The loader adds all transitive local providers of selected plugins. An exclusion
cannot remove a provider that a selected plugin requires; the override is logged.
An omitted selection loads every local plugin. OpenCode Desktop uses the same
V2 plugin package as its CLI service; there is no separate Desktop export.

Pi and OpenCode package all local kernels but do not install plugins from foreign
marketplaces. Qualified dependencies such as `mattpocock-skills@mattpocock`
still have to be supplied in a form the host can load. Packaging the entire local
marketplace is not proof that every workflow's external inputs are available.

## Required dependency behavior

The canonical dependency declarations live in `plugins/<plugin>/plugin.toml`.
Every local runtime provider is mandatory, including shared-contract providers and
workers declared by a composed method. There are no optional local dependencies
or installed-check fallbacks. External references use `plugin@marketplace`.
External providers may instead be declared in `[dependencies].optional`; their
absence must leave the base workflow usable. Local providers cannot use this field.

The compiler validates provider references and the dependency linter checks
runtime use, missing declarations and unused local edges. The three generated
marketplace catalogs retain qualified required dependencies and list optional
external providers separately as `optionalDependencies`. OpenCode's loader
manifest retains the local graph for selection; Pi's glob manifest carries no
per-plugin graph. Neither host should silently continue a workflow with a missing
required external skill or worker.
Optional external selection is defined in the rendered method on all five hosts;
Pi and OpenCode do not install these providers through their package manifests.

Consult each [plugin page](plugins/) for direct requirements and the
[dependency catalog](catalog.md#mandatory-dependency-edges) for transitive
installation cost. Installing the core
lifecycle is a larger choice than installing a leaf tool such as repo-hygiene or
work-controller.

senior-review has one review engine across code, team and PR entries. Its React,
TypeScript and platform providers are mandatory installation dependencies; target
signals decide which workers run. The lifecycle's candidate reviews use that same
engine and expose those provider bindings on every host. Core harness commands live in
the `daodan` entry plugin; core specialist methods remain in their domain plugins,
where those entries load them by name. Independent domain verticals keep their own
workflow namespaces, such as `/research:team-research` and
`/trading-broker-integration:ibkr-audit`.
The `daodan` entries are the primary surface: start there for project work, and
call a vertical's own command directly when the request is already specific to
that domain.

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

Core harness workflows belong to the `daodan` entry plugin. For `check-health`, that
means `/daodan:check-health` on Claude and OpenCode, `check-health-workflow` on
Codex, and `/daodan-check-health` on Pi. Copilot exposes the `check-health`
prompt and generated `check-health-coordinator` agent.
The prompt loads the method; the coordinator agent carries the execution harness
and worker allowlist. Select that coordinator for the isolated dispatch contract.
Domain verticals instead register workflows in their own plugin namespace.

Codex keeps its `-workflow` suffix for stable installed names. Names cannot repeat
across component kinds within a kernel. The compiler does not turn generated
dispatch resources or contract files into extra user commands.

Claude's `/` menu also lists every knowledge skill as `/<plugin>:<skill>`, so a
specialist without commands still shows entries there. Selecting one loads that
skill's instructions into the conversation and starts no workflow; the user
entries are the workflow commands in the table above.

## Office entry points

The [Office plugin](plugins/office.md) provides editable PowerPoint presentations
through SlidePoise with creative specialists, DeckCraft editing and preview,
native Excel workbooks and native Word documents. Install `office@daodan` from
`acaprino/daodan`, or select Office in its Pi/OpenCode package, following the
[Office installation guide](plugins/office.md#install-office). Its
presentation, workbook, document, start, verify, fix and theme entries live in
the `daodan` plugin and follow the same adapter mapping as its other entries:

| Host | PowerPoint (PPTX) | Excel (XLSX) | Word (DOCX) |
|---|---|---|---|
| Claude | `/daodan:presentation` | `/daodan:workbook` | `/daodan:document` |
| Copilot | `presentation-coordinator` agent with `presentation.prompt.md` | `workbook.prompt.md` | `document-coordinator` agent with `document.prompt.md` |
| Codex | `presentation-workflow` | `workbook-workflow` | `document-workflow` |
| Pi | `/daodan-presentation` | `/daodan-workbook` | `/daodan-document` |
| OpenCode V2 | `/daodan:presentation` | `/daodan:workbook` | `/daodan:document` |

SlidePoise is an external runtime with its own Python and Node dependencies. Image
generation, inspection, fonts and a compatible presentation renderer must be
available in the active session. The packaged bridge discovers the runtime without
relying on upstream skill registration for a particular host. See the
[runtime reference](../plugins/office/skills/slidepoise/references/runtime.md) for
the inspected version, prerequisites and installation procedure.

DeckCraft is a separate external executable for targeted edits, previews and PDF
export; see its [runtime reference](../plugins/office/skills/deckcraft/references/runtime.md).
The presentation entry declares isolated designer/reviewer roles and consults no
external design provider. Actual
image generation must use the exposed harness tool in a context that can call it.
Role dispatch, image access and a visual reader need separate runtime checks.
Every selected creative provider receives the fixed-canvas and native-object
requirements from Office's [PPTX compatibility contract](../plugins/office/skills/pptx/references/pptx-compatibility.md).
Selected-engine previews do not establish fidelity in Microsoft PowerPoint;
that claim requires actual target-application rendering evidence.
For example, an explicit tool allowlist can exclude an image tool even when it
exists elsewhere in the host. Missing access blocks the dependent operation;
generated wrappers and successful compilation do not prove live availability.

Excel and Word work use an available compatible document engine. The methods
prefer a suitable host runtime; available `openpyxl` or `python-docx` can handle
supported files. The packaged standard-library inspectors read and compare file
content, but do not author documents, calculate formulas, update Word fields or
render pages. Those operations need an engine that supports the required features.
Existing advanced features require demonstrated preservation before rewriting.

Installing Office does not install these external runtimes or establish live
Microsoft Office application control. All five hosts receive the workflow and
skills; actual generation, editing, calculation and rendered review depend on the
capabilities available in the active session.

## Dispatch and isolation

The sidecar can describe workers in the phase graph and in `[dispatch].roles`.
The latter covers workers selected by a loaded canonical method, without invented
scheduling phases. Harness rendering activates for declared dispatch workers,
`inline_workers`, a single phase role, or phase fan-out. Coordination selection
also respects
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

`inline_workers = true` permits only work-controller's `isolated-worker` for a
method-owned task with explicit scope, permission, budget and report path. It does
not grant access to every role in the registry.

The coordinator records every dispatched worker as delivered or failed before
closing its phase. It continues authorized reachable work, diagnoses and
corrects tool failures before a verified retry, and inspects or resumes a missing
worker delivery before reporting a documented failure. Missing results remain
visible and the owned delivery ledger is preserved. A real blocker, missing
required capability, essential human decision or caller stop is reported with
obtained results and the concrete next requirement. This obligation does not
claim a cross-host autonomous scheduler or a measured mechanical gate.
Independent reviewers do not read peer results before their own delivery. Workers get assigned intermediate
report paths; the final report has one exclusive owner in its declaring phase.

Parallelism can vary according to the contract. Pi stops an isolation-required
workflow if its companion tool is missing. OpenCode stops on an unknown agent.
Neither condition permits a shorter report pretending the worker ran.

## Schemas, methods and shipped resources

Kernels export public schemas with `[contracts].exports`. A consumer's
`[contract].shared_schemas` references the required provider and exported
`contracts/` path. work-controller owns the work contract and its project-result envelope;
senior-review retains its native finding and delivery contracts.

Provider packages contain the canonical schema files. Consumer sidecars ship as
`contracts/<workflow>.workflow.toml`, preserving qualified shared references.
Local `[contract].schemas` remains available for a workflow's own domain schemas.
There is no second hand-authored operational schema under each consumer skill.

The coordinator loads canonical specialist methods and prepares their inputs.
The compiler supplies worker bindings; it is not a general workflow executor.
Nonempty `invoke` is rejected. In senior-review team-review Phase 1a, the review
coordinator reads the canonical analyze entry of `codebase-map:map-method`
(`references/entry-analyze.md`), then directly executes their phases in order in the
same context. Loading those bodies alone runs nothing. This direct composition
introduces no declarative executor or nested lifecycle scheduler. Review
preparation runs once, consolidation owns the final review report, and required
workers retain their declared isolated contexts and delivery gates.

## MCP and helper runtimes

A plugin-declared MCP server lives under a skill, requires `mcp.servers`, and is
declared through `[[mcp.servers]]` in the kernel. Codebase Map, peer-review and
moe declare stdio servers launched with `uv run --no-config --no-project --script`,
so the project under work cannot choose a server's package index or interpreter;
users need that executable and each server's documented requirements. Codebase Map's project-bound local
service exposes 19 tools: snapshots, verified source queries, edit impact and
stale-caller classification, bounded context packets, run controls and persistent
events; its [MCP contract](../plugins/codebase-map/skills/map-method/references/mcp.md)
keeps worker execution and native UI in the host. Existing shell analysis entries
remain usable without connecting the server.

To use the server by hand on a host that does not start it, run the declared command
with `--project <project root>` as one stdio server named `codebase-map`, keep both
`--no-config` and `--no-project`, and check that `codebase_map_scope` or
`codebase_map_status` returns the project root you expect before creating a run. The
context tool needs a retrieval index built beforehand for the run's manifest; the
[usage guide](plugins/codebase-map.md#using-the-context-path) lists the steps and the
limits measured so far.

Map 7.0.0 defaults to local SQLite snapshots and supports explicit JSON upstream.
The LLM receives selected text packets, not database or base64 dumps. Each host
still owns tool execution, isolation and native progress/UI. An embedding
application must import and qualify the release before its local format binding
is considered integrated; Tri-Tech Code's SQLite-only source changes do not
change the public upstream compatibility contract.

| Host | Generated MCP mechanism |
|---|---|
| Claude | Plugin-root `.mcp.json` and a catalog `mcpServers` pointer |
| Copilot, Codex | Shipped server and a note with the exact registration command on every workflow and skill entry of the declaring plugin |
| Pi | Shipped server and registration note; `pi-mcp-adapter` reads the configured `mcpServers` entry |
| OpenCode V2 | Loader registers declared servers from the package manifest through its MCP transform; existing user entries are preserved |

The Copilot, Codex and Pi bindings remain registration instructions, not a claim
that an installed plugin automatically starts its server. The OpenCode binding
is adapted because registration comes from the loader.

### Standalone Codebase Map consumption

Install `codebase-map@daodan` instead of `daodan@daodan` on a marketplace host,
or select `codebase-map` in the Pi or OpenCode package options. Its mandatory
dependency closure, including `report-rendering`, still applies; the `daodan`
entry plugin and its workflows are not required for read-only consumption.

The host must expose `codebase-map:map-method`. Its discovery description covers
ordinary project work, but does not prove unconditional automatic invocation on
every host or request. Register and connect MCP for the `codebase_map_*` tools.
Without MCP, an LLM can inspect `.codebase-map/runs.json`, published state, run
Markdown and artifacts through ordinary file and search tools.

Loading the skill starts no analysis. Create the first map through an explicitly
requested analyze entry, or `/daodan:map-code` when the entry plugin is installed.
Standalone consumption never bootstraps, updates, deepens, migrates or publishes
one implicitly. Analyze and composed workflows share the same navigation unit;
current source remains authoritative, read-only consumers fall back with a
declared evidence gap, and producer recovery and artifact-only input boundaries
remain with their owning methods.

Building Daodan needs Python 3.11 or later and uses the standard library. The
Codebase Map helper suite declares a harder floor of 3.12, because the Python
grammar it parses with is the running interpreter's: its entry scripts carry a
`requires-python` header for `uv run --script` and refuse to start below it, and
CI runs 3.12 so the suite is exercised on a compliant interpreter. Node is
needed to exercise the OpenCode loader tests. Runtime helpers use their documented
executables; optional tree-sitter parsers improve Codebase Map parsing, while its tested
fallback remains available. No Node build is required for the generated packages.

## Write boundaries and Tri-Tech Code

Run records and outputs belong in `.daodan/runs/<id>/` of the main checkout, the
project's one record home, which is dedicated and carries a `.daodan-root` sentinel.
Codebase Map's separate stable contract stays `.codebase-map/`.

Run-state and artifact helpers mechanically check their paths, link identities,
owned output scope and record transitions. Those checks apply to helper actions.
General agent-tool confinement stays prompt-level on all five hosts:
`run-write-confinement` and Codebase Map's policy both declare `mechanical_wired = false`.
The Copilot Codebase Map guard is shipped and tested but is not wired as a hook. A
session-global confinement hook would also block unrelated project writes.

OpenCode worker permissions are generated from declared role tools and include an
`external_directory` allowance confined to the installed package. This allows
reading bundled references outside the project; it grants no arbitrary private
app output directory. Tri-Tech Code is an external OpenCode consumer, not a sixth
Daodan adapter. Out-of-project private storage needs a separately proved permission
binding and is outside the implemented record-home contract.

JSON validation and helper checks cannot establish the truth of reported evidence
or that a human actually granted a permission. Runtime authorization and semantic
review remain separate responsibilities. Codebase Map remains static: inventory, depth
of reading and runtime exercise are distinct coverage claims.

## Operational compatibility review

An export must carry executable instructions for its host through the entire
entry, skill, role and bundled-reference path. Tool/frontmatter conversion,
registration and capability support are necessary checks, but they do not adapt
a nested dispatch example, a foreign installation command or an interactive
terminal requirement. Review a single isolated phase as well as fan-out, and
compare the worker's allowed tools with the actions its body requires.

Review each host against its adapter and runtime evidence:

| Host | Operational contracts to verify |
|---|---|
| Claude Code | Named-agent tool/schema, permitted workers, sidecar/body agreement, model inheritance or documented overrides, capture checkpoints and delivered artifacts |
| Copilot | `agent` dispatch, `search`/`edit`/`runCommands`/`fetch` bindings, worker allowlists, preservation of omitted tool restrictions and native dependency recovery |
| Codex | Inline delivery of role bodies and references, host tool/input schema, workflow skill identities, questions and required external providers |
| Pi | Role skills and prompt identities, `pi-subagents` isolation, core tool/input schema, `pi-mcp-adapter`, questions and capture lifecycle |
| OpenCode V2 | Registered qualified skill/agent/command IDs, native `subagent`/`shell`/`question` schemas, permission actions, registered references and dependency recovery |

The 2026-10-11 operational compatibility audit
records the pre-fix shared and host-specific defects and separately describes
the 32.10.0 source/rendering corrections and their compiler checks. Those checks
do not establish live runtime repair on every host. Historical successful fixture
probes do not cover every plugin workflow. Required isolation and capability
failures remain blockers; a shorter same-context workflow is not a valid substitute.

Fix shared semantics in `plugins/`, host mechanisms in `adapters/` or the
compiler, then regenerate all hosts and test the affected contracts through their
references. Preserve host-as-subject material and ordinary code examples rather
than renaming tokens globally. Keep source/export parity, operational rendering
checks and installed-host execution as separate reported results. Consumer
bindings such as Tri-Tech Code's storage, permissions, Gateway models and routing
also require checks in that consumer. A local registration workaround does not
repair the shared export for other hosts.

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
lifecycle. Consult the 2026-10-07 validation report
for the measured release evidence and its limits.

## Available knowledge inventory

Skill Catalog uses the active host's actual skill inventory and explicit resolved
provider roots. Its generated registry lists declarations, including plugins that
may be unselected or uninstalled. It is not availability evidence. The five adapter
inventory instructions ship as references/host-inventory.md inside the catalog
skill. Native/workflow/role wrappers retain their existing component boundaries.

External/project skills can join the same index with their own SKILL.toml metadata.
Unannotated relevant skills are searchable but stay classification gaps until a
reviewed owner classification exists. No automatic install or home/cache crawl is
performed. Selection is read-only, snapshot-bound and accounted for per worker in
the same review ledger. Python 3.11+ is required for the stdlib helper. Compiler and
fixture tests validate the port; they do not constitute installed-host runtime probes.

## Scientific lifecycle hooks

The research kernel declares optional session-start and user-prompt-submit hooks.
The compiler generates `hooks/hooks.json` for Claude and Codex, referring to the
Python helper bundled under the skill. Enabling the plugin makes registration
discoverable; the host retains its trust controls before execution. No global
settings are edited. Python must be available as `python` to the host process.

Copilot and Pi exports retain the explicit scientific checkpoints in
Daodan methods; they declare no native interception for this feature.
OpenCode adapts lifecycle callbacks through its plugin loader. SessionStart runs
on creation when observed, otherwise once at the first prompt; UserPromptSubmit
runs on prompt dispatch and feeds the primary model context via Python without
crashing the runtime. A callback
only emits routing context after reading Science Mode. It performs no research
or publication. See the [technical contract](plugins/research/technical-spec.md)
and [validation evidence](plugins/research/validation.md) for the distinction
between generated registration, subprocess tests and installed-host delivery.

### Chat entry routing

A plugin opts into chat entry routing with `[routing]` in its kernel rather than
with a hand-written hook; the compiler alone renders delivery, and no body
carries an entry note. Claude and Codex get a session-start hook named
`entry-routing` in the generated `hooks/hooks.json`, plus the rendered text at
`hooks/entry-routing.md`, read by one Python launcher that prints
`hookSpecificOutput.additionalContext` and exits 0 with no output on any error
(missing root, file or encoding). A plugin that also declares `[[hooks]]`
(`research`) gets both entries in the same `hooks/hooks.json`. OpenCode carries
no separate process: the manifest's `daodan` key names each selected plugin's
routing text file, and the loader reads it once per session into a routing slot
that, unlike the `startup` slot, is never cleared by a prompt
(`index.js:398-408,466-477`); the context hook that pushes it registers whenever routing
text or lifecycle hooks are selected. Copilot and Pi get no delivery for this
feature at all; the workflow and skill descriptions already in the catalog are
the only routing signal there.

Per INV-6, a claim that a host actually executes the routing hook, not merely
that the compiler generated it, rests on a passed installed-host probe.

- **Claude**: probed on 2026-10-28, measured results in
  [RESULTS.md](../evals/entry-routing/RESULTS.md). The hook delivers
  (`additionalContext` reaches the model: every with-hooks hit is evidence of
  it), but the full 65-case activation measurement did not meet the S-6 target
  at the tested scale (30 plugins); see that file for the honest result and
  why a disposable probe cannot settle the question at the user's real,
  larger scale.
- **Codex**: attempted the same day in an isolated `CODEX_HOME` with only the
  real `auth.json` copied in. The plugin installed cleanly into that isolated
  cache, but `codex exec` failed with `workspace routing discovery failed`
  before producing any model output, a backend/workspace error unrelated to
  hook rendering. Still marked "generated, not probed".
- **OpenCode**: attempted the same day with a project-local `opencode.json`
  (global config never touched). `opencode run --standalone` hung with no
  output for the full timeout. Its 2026-10-27 probe on record at
  [validation evidence](plugins/research/validation.md:46-66) covers the
  general session-start/prompt hook mechanism, predates this feature's
  routing-specific slot, and does not by itself prove routing delivery. Still
  marked "generated, not probed" for this feature.
- **Copilot**: not attempted; the local Copilot CLI installation is broken on
  the machine this probe ran from, unrelated to this work. Copilot renders
  nothing for chat entry routing, consistent with the design above; a separate
  probe (unattempted) would recheck only whether the
Copilot CLI runs a plugin's session-start hook mechanism at all, which this
feature does not depend on.

## Decision-record session hook

project-delivery declares one optional session-start hook, `decision-records`,
which runs `skills/adr-method/scripts/adr_hook.py` with a 10 second timeout. It
reads `adr_tool.py state` and adds decision-record context for the main model:
on an `active` project each settled product or feature decision becomes a
`Proposed` record, an `undecided` project is asked once at the first settled
decision, and a `declined` one gets no context. It writes nothing and names
only `project-delivery:adr-method` and `/daodan:record-decision`. Claude and Codex register it through the generated
`hooks/hooks.json`, OpenCode through its plugin loader with the session-start
timing above. Copilot and Pi declare no native interception: there the capture
rule lives only in the Daodan brainstorm, the task interview and adr-method, so
another plugin's brainstorming is not covered. `tests/test_adr_hook.py` runs the
helper as a subprocess; it is not installed-host evidence.
