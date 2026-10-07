---
name: downstream-exports
description: >
  How our content reaches hosts that are not Codex: the host adapters, what each
  host expects a package to look like, how the compiler renders harnesses from templates,
  how a neutral policy gets a host implementation, when a fingerprinted semantic override is
  the right answer, and the content that deliberately keeps host-as-subject vocabulary.
  TRIGGER WHEN: changing an adapter layout, capability binding, coordination strategy,
  harness template, policy implementation or override, or diagnosing why one host's package
  came out differently from another's.
  DO NOT TRIGGER WHEN: pulling content IN from an external repo (use `external-repo-intake`
  or `upstream-sync`), or editing plugin behaviour, which lives in the kernel under
  `plugins/` and is host-neutral by rule.
---

# Downstream exports

The mirror image of the `external-repo-intake` skill. That skill covers content flowing *in* from other repos; this one covers our content flowing *out* to the other hosts.

**Nothing under `exports/` is edited by hand, ever.** Every file there is compiler output from `plugins/` plus `adapters/`, and `python scripts/daodan_build.py --check` fails the build the moment a committed package stops reproducing from its source. If an export looks wrong, the bug is in the kernel, the adapter, or the compiler. Fixing the export directly produces a change that the next build silently deletes.

## The split that decides where a change goes

The core owns roles, workflow dependencies, required context isolation, joins and observable contracts. A harness owns host APIs, dispatch, scheduling, retries and result collection.

| The change is about | It belongs in |
|---|---|
| what a reviewer looks for, what a workflow means, what a report must contain | `plugins/<name>/` (Markdown for behaviour, TOML for structure) |
| which host tool satisfies a neutral capability | `adapters/<host>/capabilities.toml` |
| which coordination strategies a host supports, and in what order | `adapters/<host>/coordination.toml` |
| where a component lands in a host's package | `adapters/<host>/layout.toml` |
| the wrapper text that tells a host harness how to dispatch | `adapters/<host>/templates/` |
| how one host enforces a neutral policy | `adapters/<host>/policies/<name>/` with `policy.toml` naming what it `implements` |
| a meaning that genuinely cannot be rendered from the generic templates | `adapters/<host>/overrides/<plugin>/<workflow>/` |

**Never name a host tool, team API or dispatch primitive in neutral content.** That is the rule the whole split rests on: the moment a kernel says `Agent` or `runCommands`, one host's vocabulary has become everyone's contract.

## What each host expects

| | claude | copilot | codex | pi | opencode |
|---|---|---|---|---|---|
| catalog | `.claude-plugin/marketplace.json` | `.github/plugin/marketplace.json` | `.agents/plugins/marketplace.json` | the root `package.json` | `exports/opencode/package.json` |
| plugin manifest | `.claude-plugin/plugin.json` | `plugin.json` | `.codex-plugin/plugin.json` | none | none |
| roles | `agents/<role>.md` | `agents/<role>.agent.md` | `roles/<role>.md` | `skills/<plugin>-<role>/SKILL.md` | `agents/<role>.md`, registered as agent `<plugin>:<role>` |
| workflows | `commands/<workflow>.md` | `prompts/<workflow>.prompt.md` | `skills/<workflow>-workflow/SKILL.md` | `prompts/<plugin>-<workflow>.md` | `commands/<workflow>.md`, registered as `/<plugin>:<workflow>` |
| skills | `skills/<skill>/SKILL.md` | same | same | same | same, registered as `<plugin>:<skill>` |
| source reference | `./exports/claude/plugins/<name>` | `./exports/copilot/plugins/<name>` | `./exports/codex/plugins/<name>` in `source` | a glob, not a reference | `root` in the manifest's `daodan` key |

Pi and OpenCode are the hosts with no marketplace and no per-plugin manifest. On Pi three of those
cells are unlike the others and each is load-bearing. Its catalog is an npm-shaped `package.json` at the
**repository root**, because `pi install git:` reads the manifest from the root of the clone, and it
registers by globbing `./exports/pi/plugins/*/skills` and `.../prompts` rather than by naming
anything. `plugin_manifest` is absent from its layout, which is what makes that key optional in the
renderer. And its roles render as skills carrying `disable-model-invocation: true`: Pi lists every
registered skill's name and description in the system prompt, so the flag is what keeps role bodies
from costing that budget in every session while staying loadable, and it is also what makes a
role-only plugin such as `app-analyzer` exist at all on a host with no agent concept.

Two mechanisms Pi's core omits on purpose arrive from companion packages the user installs,
`pi-subagents` for an isolated worker context and `pi-mcp-adapter` for MCP. Both are named in the
binding's `package` field rather than in template prose, which is why that field exists and why it
is separate from `value`: `value` names a host tool and feeds the Copilot coordinator's derived
`tools` line, so a package name there would read as a tool that does not exist.

OpenCode V2 is the host where nothing exists until code registers it. It has no marketplace and no
static package format: a package arrives as a plugin, an ES module whose default export's `setup`
calls the V2 transform hooks for skills, agents, commands and MCP servers. Directory discovery of
`skills/`, `agents/` and `commands/` applies to config directories only, never to a plugin package.
So the package is one npm-shaped directory, `exports/opencode/`, installed through npm's `::path:`
selector into the tagged repository, which is why its catalog sits under `exports/` and the root
`package.json` stays Pi's. The catalog is that package's own `package.json`, and its `daodan` key
carries, per plugin, the local dependencies and every component with its ID, description, file and,
for agents, a V2 permission list. `index.js` beside it is the loader: one fixed file under
`adapters/opencode/templates/`, copied verbatim by the layout's `package_files` key and covered by
the drift gate. **It is never generated per plugin**: anything plugin-specific is computed in Python
and written into the manifest, which keeps the toolchain stdlib Python and keeps the loader
reviewable as a single file. It imports nothing outside Node's standard library and never throws out
of `setup` or a transform callback, because a plugin failing there can disable the host's whole
plugin generation. `tests/opencode/loader.test.mjs` pins it, run from the Python suite.

Three decisions in that loader are contracts. **IDs follow Claude** (`senior-review:code-auditor`),
because V2 registers commands and agents by free string and the kernels already write that form; a
probe item records whether the `skill` and `subagent` tools accept the colon. **Selection is a loader
option that the dependency policy outranks**: `options.plugins` brings its transitive closure of local
dependencies and `options.exclude` never removes a plugin a selected one needs, both logged. **A role
with declared tools starts its permission list with deny-all, then allows those tools and skill
loading. Every role ends with an `external_directory` allowance scoped to `<package-root>/**`**.
A role without a tools restriction retains host defaults plus that package allowance. The loader
resolves it: the package lives in OpenCode's cache, outside every project, so without it a role is
refused the references its body tells it to read. Roles carry
neither `model` (V2's subagent default already inherits) nor `color` (V2 takes hex, the kernels names).

Codex suffixes workflow directories with `-workflow` on purpose: it is the one host that renders both skills and workflows as skills, and before marketplace 29.0.0 a plugin could have a skill and a workflow of the same name (`digital-marketing:brand-naming` did), which would have collided on disk. The frontmatter `name` carries the same suffix, through the layout's `workflow_name` key, because Codex resolves a skill by that name rather than by its directory: until marketplace 28.5.0 the directory was suffixed and the name was not, so `brand-naming` registered two skills under one name.

Codex's catalog `source` is the relative package path itself. Do not restore the older
`source = "local"` plus `path` object: `scripts/daodan/catalogs.py` records that the native
catalog accepted the marketplace but could not find its plugins with that shape.

Since marketplace 29.0.0 a name may not repeat across kinds at all: `validate_component_kinds` fails the build on a skill, role or workflow sharing a name inside one plugin. OpenCode is what forced it, because its `@` menu lists skills and agents together. A role beside a same-topic skill takes `-agent`, a skill beside a same-topic workflow takes `-method`. The Codex suffix is now redundant and stays anyway: removing it would rename every Codex workflow skill a user already has installed.

## Harness rendering

A workflow receives a harness when its sidecar declares `[dispatch].roles`, permits
`[dispatch].inline_workers`, or has a phase with `fanout` or `fanout_from`. A composed method
therefore receives its worker bindings even when the scheduling graph has no fan-out. The host
template wraps the neutral body with isolated worker contexts, the delivery barrier, the
single-writer rule for the final report, and a **dispatch plan**. The templates are
`claude/templates/team-workflow.md.tmpl`, `copilot/templates/coordinator.agent.md.tmpl` (plus
`worker.agent.md.tmpl` for roles), `codex/templates/subagent-workflow.SKILL.md.tmpl`,
`pi/templates/team-prompt.md.tmpl` (plus `role.SKILL.md.tmpl`) and
`opencode/templates/team-command.md.tmpl` (plus `agent.md.tmpl`). OpenCode names the native
`subagent` tool and `background: true` for one phase's workers. An unknown agent stops the run
as a broken install.

`[dispatch].isolated` and `inline_workers` also feed coordination selection, independently of
phase isolation. `inline_workers` exposes only `project-protocol/isolated-worker` for a full
method-owned task, scope, authorization, budget and report path; it never exposes the entire
role registry. Extra named workers use `plugin/role` references and must have a direct required
provider dependency. The registry validates the provider and role before rendering.

Named-agent adapters (Claude, Copilot, OpenCode) bind installed owner-qualified agent IDs.
Inline-prompt adapters (Codex, Pi) load local roles from their rendered role location and ship
referenced external role bodies under `contracts/dispatch/<owner>/<role>.md`. Those are generated
resources, with owner, provider version and source digest, never registered skills or agents.
Their helper references resolve against the owning plugin's installed skill, not against the
coordinator or the generated resource's directory. Edit the owner's canonical role to change one.

The wrapper requires each worker's recorded `delivered` or `failed` outcome before a phase can
close. Independent reviewers receive coordinator-declared inputs and cannot read peer results
before their own delivery. Intermediate report paths are assigned explicitly; the final report
has one exclusive owner in its declaring phase.

The Pi template is the one that branches, and the branch is a contract rather than a courtesy. Its `subagent` tool is not part of Pi's core, so the template states what to do when none is available and makes the answer depend on the isolation the workflow declared: `required` stops and asks for `pi install npm:pi-subagents`, `shared` may run the phases in one context and say so. Running a review pipeline serially in one context is the loss of isolation rather than a lesser form of it, so collapsing those two branches would produce a report claiming a contract it did not meet.


The dispatch plan (`${dispatch_plan}`) is one numbered line per phase of the sidecar, in order: how many workers (once each for a static `fanout`, one per item for a `fanout_from` selection, one for a single `role`, none for a shared phase), in what context, at what concurrency, behind which barrier, and what the phase needs, consumes and produces. It replaced a header that said "dispatch the selected roles, once each", which was right for one wave of reviewers and wrong for `codebase-xray:team-analyze`, which fans out one worker per partition across three waves: on Codex and Copilot that header was the only dispatch guidance, and read literally it produced one structure worker for the whole codebase.

The Copilot coordinator's `tools` line is derived, not fixed: every capability the plugin requires whose binding carries a `value` contributes that tool, and `repository.read` and `roles.dispatch` are always included. That is why `roles.dispatch` carries `value = "agent"` in the Copilot bindings. A coordinator that writes run state, runs a detection script and publishes a mirror gets `edit` and `runCommands` because its kernel declared `repository.write` and `shell.execute`, and a hand-written `['agent', 'search']` would have left it unable to do any of that.

Copilot and OpenCode are the hosts that rewrite role frontmatter. OpenCode's `agent.md.tmpl` replaces `tools`, `model` and `color` with `mode: subagent` and a V2 permission list derived from `tools` (see the OpenCode paragraph above). For Copilot the compiler maps Claude-shaped tool names onto Copilot's (`Read`/`Glob`/`Grep` to `search`, `Write`/`Edit` to `edit`, `Bash` to `runCommands`, `WebFetch`/`WebSearch` to `fetch`, `Agent`/`Task` to `agent`) and flattens the description to a quoted one-liner. Frontmatter scalars are rendered inline, so a description carrying a colon or a stray quote is what breaks a whole block: that failure mode is the reason `_one_line` exists.

Substitution is `string.Template` with an allowlisted context (`scripts/daodan/templates.py`). An unknown placeholder is an error, never an empty string, and a layout path that escapes its package is refused.

## The two Claude placeholders a kernel may write

A kernel body says `${CLAUDE_PLUGIN_ROOT}/skills/x/scripts/y.py` because the bundled-path linter requires that form: it is what survives installation on Claude. It says `$ARGUMENTS` because that is what a Claude command expands. Neither is defined on Copilot or Codex, so the renderer rewrites both per host from four layout keys, and inserts the host's explanation once, after the frontmatter, in every Markdown file that uses the reference:

| key | claude | copilot | codex | pi | opencode |
|---|---|---|---|---|---|
| `plugin_root_reference` | `${CLAUDE_PLUGIN_ROOT}` (itself) | `${PLUGIN_ROOT}`, which Copilot CLI documents for paths inside the plugin directory | `<plugin-root>`, a marker the agent resolves once: Codex hands `PLUGIN_ROOT` to hook commands only | `<plugin-root>`, same marker: a prompt template gets no variable | `<plugin-root>`, which the loader substitutes with the absolute plugin directory in every body it registers |
| `plugin_root_note` | none | names `plugin.json` as the directory to find | names `.codex-plugin/plugin.json` | names the directory holding the plugin's `skills/` and `prompts/` | names the directory holding `skills/`, `agents/` and `commands/`, for files the loader does not register |
| `arguments_reference` | `$ARGUMENTS` (itself) | `<arguments>` | `<arguments>` | `$ARGUMENTS` (itself) | `$ARGUMENTS` (itself) |
| `arguments_note` | none | "substitute what the user typed after the prompt name" | "... after the skill name" | none | none |

Pi and OpenCode are the hosts besides Claude whose arguments placeholder maps onto itself. A Pi prompt template expands `$ARGUMENTS`, `$@`, `$1` and `${1:-default}` natively. On OpenCode a plugin's command is an `execute` function, so the loader expands `$ARGUMENTS` and `$1` itself, with a line-for-line port of V2's own `evaluateTemplate` minus the shell-output blocks no kernel uses.

Claude's keys map each placeholder onto itself and carry no note, so its packages are unchanged by this pass. Only the `${CLAUDE_PLUGIN_ROOT}` form is rewritten; a bare `$CLAUDE_PLUGIN_ROOT` would pass through and fail `tests/test_daodan_host_rendering.py`.

A workflow without declared dispatch workers or phase fan-out is rendered under host frontmatter
from the `workflow_frontmatter` layout key: Claude has none and gets the kernel file verbatim;
Codex gets `name` and `description` with the argument hint moved into the body as an `Arguments:`
line; Copilot gets `name`, `description` and `argument-hint`. For a dispatched Copilot workflow,
the prompt remains the entry point and the compiler also registers its `*-coordinator` agent.

Which strategy each host selected is recorded per package in `.daodan-provenance.json`, together with the kernel digest and any overrides applied. Topology names may differ between hosts; contract assertions may not.

## Shared contracts and composition

`[contracts].exports` declares a kernel's public `contracts/` files. Local
`[contract].schemas` still refers to a workflow's own plugin. A shared reference such as
`project-protocol/contracts/work.toml` belongs in `[contract].shared_schemas`; its provider must
be a direct required dependency and the target must be explicitly exported. The provider package
carries the canonical file. Consumers' shipped `contracts/<workflow>.workflow.toml` sidecars
retain the qualified reference; the compiler does not create another hand-authored schema copy.

Project-protocol owns work records and project results. Senior-review's domain contracts remain
in senior-review. Shared operational records do not replace native findings and review ledgers.

The compiler renders entry-point methods and dispatch instructions; it does not execute a
workflow from another workflow. Nonempty `invoke` is rejected. A coordinator loads the canonical
specialist skill and binds its declared workers. The existing X-ray entry is an explicitly
documented same-context method step, not a general-purpose `invoke` executor.

## Installation and mandatory dependencies

Register the repository root on Claude, Copilot or Codex and install `<plugin>@daodan`. Their
generated catalogs declare required dependencies and derive the foreign-marketplace trust
allowlist from qualified `plugin@marketplace` references. Local dependencies are always required,
never optional, with no runtime installed-check fallback. Installation must provide the complete
transitive dependency closure before an entry runs.

Pi installs the repository package at a released tag. Settings may filter prompt and skill globs,
but the root manifest has no per-plugin dependency solver: include the complete local closure
when selecting plugins. OpenCode installs `exports/opencode` at the same tag. Its loader computes
the local closure of `options.plugins` and prevents `options.exclude` from removing required
providers. Neither package installs plugins from external marketplaces automatically; those
qualified dependencies must be provisioned in a form the host can load. Pi's companion packages
are an additional runtime requirement, not local Daodan plugin dependencies.

The user-facing installation, command mapping and environment limits live in
[`docs/hosts.md`](../../../docs/hosts.md). It describes repository implementation; fixture probes
recorded under `tests/host-probes/` do not prove a new lifecycle run on an installed host.

## Overrides are a last resort, and they expire

An override replaces one rendered file for one host, and it carries the digest of the neutral source it was reviewed against. When that source moves, the override is reported `stale-override` and the build fails until a human re-reads it. An override may select a different declared mechanism; it may never add a tool, MCP server, LSP server, hook or capability the kernel did not declare (`override-capability-escalation`), and it may not quietly drop a contract the workflow declares (`override-drops-contract`).

Generic templates express the shipped host differences. Reach for an override only after
establishing that a *behavioural contract* cannot be rendered generically. A different topology
is not a reason; a different meaning is.

## MCP servers: a manifest where the host starts them, a note where it does not

A kernel that ships an MCP server declares it in `plugin.toml`, with the server file under one of its skills so every package carries it, and requires the `mcp.servers` capability:

```toml
[[mcp.servers]]
name = "peer-review"
command = "uv"
args = ["run", "--script", "${CLAUDE_PLUGIN_ROOT}/skills/cross-model-peer-review/scripts/server.py"]
```

The validator refuses a server without the capability, the capability without a server, and an argument that names a file outside `skills/` (the compiler copies nothing else, so the server would exist in the checkout only). What the binding decides per host:

| strategy | host | what the package gets |
|---|---|---|
| `mcp-manifest` | claude | a plugin-root `.mcp.json`, auto-discovered on install, with `${CLAUDE_PLUGIN_ROOT}` left for the host to expand, and `"mcpServers": "./.mcp.json"` in the catalog entry, derived from the package like every other component |
| `mcp-registration` | codex, copilot, pi | the server file, and one note per server at the top of every workflow giving the exact command (with the host's own plugin-root reference) to register under that name in the host's MCP configuration |
| `mcp-manifest` (adapted) | opencode | the same `.mcp.json`, plus the server in the manifest's `daodan` key, which the loader registers through the V2 MCP transform. The host reads neither file itself, so the binding is `adapted`, and a server name the user already configured is left alone |

The `mcp-registration` bindings are `adapted`, not `native`, because no probe has shown Codex, Copilot or Pi starting a server declared by an installed plugin. Promote one to `mcp-manifest` only after such a probe, and record it in the evidence table. OpenCode's `mcp-manifest` binding is `adapted` for a different reason: the server is started because the loader registers it, not because the host read a file. `tests/test_daodan_mcp.py` pins the rendering on the `valid-mcp` fixture.

## Policies: what is enforced where

A neutral policy under `plugins/<name>/policies/` says what must hold. An adapter's `policies/<name>/policy.toml` says how one host makes it hold, and the compiler ships that implementation inside the package. Only one such implementation exists, `copilot/policies/xray-guard` for `codebase-xray`'s `write-confinement`, and it is shipped but not wired, for reasons that bind any future policy:

- **A plugin-level hook is session-global.** `hooks/hooks.json`, which Claude Code and Codex both read, fires for every tool call of every agent while the plugin is enabled. A confinement rule there would refuse every write outside `.codebase-xray/` in every session. A confinement policy can never ship as a plugin hook, on any host.
- **Per-agent hooks are the right mechanism and are not yet safe to generate.** Claude agent frontmatter and VS Code custom agents accept a `hooks:` block scoped to that agent. A hook command that fails to find its script does not fail open: a non-zero exit blocks that worker's every tool call, and `${CLAUDE_PLUGIN_ROOT}` is not reliably expanded in agent-frontmatter hook commands. Copilot CLI does not run plugin hooks at all (github/copilot-cli#2540).
- **Agent-tool confinement stays prompt-level on all five hosts**, carried by worker prompts,
  ownership contracts and the policy's `[enforcement]` table. The shipped Copilot guard is not
  wired. Wire a mechanism only after a host probe shows a per-agent hook running from an
  installed plugin, and wrap the command so a missing script allows rather than blocks.

Project-lifecycle's `run-write-confinement` is also prompt-level (`mechanical_wired = false`).
Project-protocol's run-state helper and lifecycle artifact helpers independently reject escaping
paths, links and unsafe output identities mechanically. That enforcement covers operations
performed through those helpers, not arbitrary writes by other agent tools, semantic truth of a
report, or the provenance of human permission.

Project run output defaults to `.daodan/runs/<id>/`. A dedicated alternative root is allowed
only inside the identified project, is not the project root, and carries `.daodan-root`.
Tri-Tech Code is an external OpenCode consumer, not a sixth adapter. Private app storage outside
the project is unsupported until a separate permission binding is proved: generated OpenCode
role allowances cover the installed package, not an arbitrary app data directory.

## Content that deliberately keeps host-as-subject vocabulary

`marketplace-ops` and `ai-tooling`'s `agent-sdk-builder` are *about* the agent tooling, so their tool names and trigger labels are content rather than accidental host coupling. Never de-brand or tool-rename them.

## Verification

```bash
python scripts/daodan_build.py                 # publish every host
python scripts/daodan_build.py --check --support   # drift gate plus the per-host support table
python -m unittest discover -s tests           # compiler, port and parity contracts
python adapters/copilot/policies/xray-guard/test_xray_guard.py
```

A plugin reported `unsupported` on any host blocks the release: it means a required capability has no binding, or no coordination strategy satisfies its workflow. Fix the binding or the workflow. Never soften the contract to make a host pass.

## What this skill used to cover, and why it no longer does

Until the universal cutover this repository hand-mirrored a per-plugin VS Code bundle catalog, generated an extension manifest, packaged a `.vsix` and released it on a tag. All of it is gone: the bundles, `mirror_export.py`, the export structural checker, the manifest generator, and both workflows that served them. The compiler replaced the obligation with a gate, which is the point. Do not rebuild any of it, and do not reintroduce a second hand-maintained copy of a plugin for any host.
