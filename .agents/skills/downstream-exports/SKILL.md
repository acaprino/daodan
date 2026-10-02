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
| source reference | `./exports/claude/plugins/<name>` | `./exports/copilot/plugins/<name>` | `source = "local"` plus `path` | a glob, not a reference | `root` in the manifest's `daodan` key |

Pi is the one host with no marketplace and no per-plugin manifest, so three of those cells are
unlike the others and each is load-bearing. Its catalog is an npm-shaped `package.json` at the
**repository root**, because `pi install git:` reads the manifest from the root of the clone, and it
registers by globbing `./exports/pi/plugins/*/skills` and `.../prompts` rather than by naming
anything. `plugin_manifest` is absent from its layout, which is what makes that key optional in the
renderer. And its roles render as skills carrying `disable-model-invocation: true`: Pi lists every
registered skill's name and description in the system prompt, so the flag is what keeps 76 roles
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
dependencies and `options.exclude` never removes a plugin a selected one needs, both logged. **A role's
permission list starts with a deny-all and ends with an `external_directory` allowance scoped to
`<package-root>/**`**, which the loader resolves: the package lives in OpenCode's cache, outside every
project, so without it a role is refused the very references its body tells it to read. Roles carry
neither `model` (V2's subagent default already inherits) nor `color` (V2 takes hex, the kernels names).

Codex suffixes workflow directories with `-workflow` on purpose: it is the one host that renders both skills and workflows as skills, and before marketplace 29.0.0 a plugin could have a skill and a workflow of the same name (`digital-marketing:brand-naming` did), which would have collided on disk. The frontmatter `name` carries the same suffix, through the layout's `workflow_name` key, because Codex resolves a skill by that name rather than by its directory: until marketplace 28.5.0 the directory was suffixed and the name was not, so `brand-naming` registered two skills under one name.

Since marketplace 29.0.0 a name may not repeat across kinds at all: `validate_component_kinds` fails the build on a skill, role or workflow sharing a name inside one plugin. OpenCode is what forced it, because its `@` menu lists skills and agents together. A role beside a same-topic skill takes `-agent`, a skill beside a same-topic workflow takes `-method`. The Codex suffix is now redundant and stays anyway: removing it would rename every Codex workflow skill a user already has installed.

## Harness rendering

A workflow whose phases fan out is not copied, it is rendered through that host's harness template, which wraps the neutral body with the dispatch obligations the contract requires: isolated worker contexts, the delivery barrier, the single-writer rule for the report, and a **dispatch plan**. The templates are `claude/templates/team-workflow.md.tmpl`, `copilot/templates/coordinator.agent.md.tmpl` (plus `worker.agent.md.tmpl` for the roles), `codex/templates/subagent-workflow.SKILL.md.tmpl`, `pi/templates/team-prompt.md.tmpl` (plus `role.SKILL.md.tmpl`) and `opencode/templates/team-command.md.tmpl` (plus `agent.md.tmpl`). The OpenCode harness names the native `subagent` tool and `background: true` for one phase's workers, and has no missing-tool branch: isolation is native there, so a `subagent` call that answers with an unknown agent is a broken install, stopped and reported.

The Pi template is the one that branches, and the branch is a contract rather than a courtesy. Its `subagent` tool is not part of Pi's core, so the template states what to do when none is available and makes the answer depend on the isolation the workflow declared: `required` stops and asks for `pi install npm:pi-subagents`, `shared` may run the phases in one context and say so. Running a review pipeline serially in one context is the loss of isolation rather than a lesser form of it, so collapsing those two branches would produce a report claiming a contract it did not meet.


The dispatch plan (`${dispatch_plan}`) is one numbered line per phase of the sidecar, in order: how many workers (once each for a static `fanout`, one per item for a `fanout_from` selection, one for a single `role`, none for a shared phase), in what context, at what concurrency, behind which barrier, and what the phase needs, consumes and produces. It replaced a header that said "dispatch the selected roles, once each", which was right for one wave of reviewers and wrong for `codebase-xray:team-analyze`, which fans out one worker per partition across three waves: on Codex and Copilot that header was the only dispatch guidance, and read literally it produced one structure worker for the whole codebase.

The Copilot coordinator's `tools` line is derived, not fixed: every capability the plugin requires whose binding carries a `value` contributes that tool, and `repository.read` and `roles.dispatch` are always included. That is why `roles.dispatch` carries `value = "agent"` in the Copilot bindings. A coordinator that writes run state, runs a detection script and publishes a mirror gets `edit` and `runCommands` because its kernel declared `repository.write` and `shell.execute`, and a hand-written `['agent', 'search']` would have left it unable to do any of that.

Copilot is the only host that rewrites role frontmatter: the compiler maps Claude-shaped tool names onto Copilot's (`Read`/`Glob`/`Grep` to `search`, `Write`/`Edit` to `edit`, `Bash` to `runCommands`, `WebFetch`/`WebSearch` to `fetch`, `Agent`/`Task` to `agent`) and flattens the description to a quoted one-liner. Frontmatter scalars are rendered inline, so a description carrying a colon or a stray quote is what breaks a whole block: that failure mode is the reason `_one_line` exists.

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

A workflow that does not fan out is rendered under host frontmatter from the `workflow_frontmatter` layout key, which lists the keys the host reads in order: Claude has none and gets the kernel file verbatim, Codex gets `name` and `description` with the argument hint moved into the body as an `Arguments:` line, Copilot gets `name`, `description` and `argument-hint`, which its prompt files support.

Which strategy each host selected is recorded per package in `.daodan-provenance.json`, together with the kernel digest and any overrides applied. Topology names may differ between hosts; contract assertions may not.

## Overrides are a last resort, and they expire

An override replaces one rendered file for one host, and it carries the digest of the neutral source it was reviewed against. When that source moves, the override is reported `stale-override` and the build fails until a human re-reads it. An override may select a different declared mechanism; it may never add a tool, MCP server, LSP server, hook or capability the kernel did not declare (`override-capability-escalation`), and it may not quietly drop a contract the workflow declares (`override-drops-contract`).

There are currently no overrides at all. Every host divergence so far was expressible through the generic templates, which is the outcome the gate exists to make visible rather than to encourage. Reach for one only after establishing that a *behavioural contract* cannot be rendered generically. A different topology is not a reason; a different meaning is.

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

Both non-Claude bindings are `adapted`, not `native`, because no probe has shown either host starting a server declared by an installed plugin. Promote a binding to `mcp-manifest` only after such a probe, and record it in the evidence table. `tests/test_daodan_mcp.py` pins the rendering on the `valid-mcp` fixture.

## Policies: what is enforced where

A neutral policy under `plugins/<name>/policies/` says what must hold. An adapter's `policies/<name>/policy.toml` says how one host makes it hold, and the compiler ships that implementation inside the package. Only one such implementation exists, `copilot/policies/xray-guard` for `codebase-xray`'s `write-confinement`, and it is shipped but not wired, for reasons that bind any future policy:

- **A plugin-level hook is session-global.** `hooks/hooks.json`, which Claude Code and Codex both read, fires for every tool call of every agent while the plugin is enabled. A confinement rule there would refuse every write outside `.codebase-xray/` in every session. A confinement policy can never ship as a plugin hook, on any host.
- **Per-agent hooks are the right mechanism and are not yet safe to generate.** Claude agent frontmatter and VS Code custom agents accept a `hooks:` block scoped to that agent. A hook command that fails to find its script does not fail open: a non-zero exit blocks that worker's every tool call, and `${CLAUDE_PLUGIN_ROOT}` is not reliably expanded in agent-frontmatter hook commands. Copilot CLI does not run plugin hooks at all (github/copilot-cli#2540).
- **So the policy is prompt-level everywhere**, carried by the worker prompts and the ownership contracts in the roles, and the kernel's `write-confinement.toml` says so in its `[enforcement]` table. Wire a mechanism only after a host probe shows a per-agent hook running from an installed plugin, and wrap the command so a missing script allows rather than blocks.

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
