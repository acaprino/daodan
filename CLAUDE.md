# Daodan

The Daodan is the symbiote that augments its host. This repository is the Daodan of coding agents: a development harness, built on the static Meta-Code map of `codebase-map`, that coordinates project intent, code, meaningful tests, durable knowledge and experimental artifacts, alongside core language and stack specialists, Office methods, domain verticals and web research. The 24 domain, office, research and framework plugins extracted to `acaprino/shinatama` in marketplace 36.0.0 returned to this single marketplace, with `text-humanizer` back as a local dependency and `/daodan:humanize-text` restored to the `daodan` entry plugin while domain verticals keep their own workflow namespaces. `skill-catalog` discovers every plugin's knowledge sidecars and selects them per run. It ships to five hosts from one source. Remote: `acaprino/daodan` on GitHub.

## Development harness

codebase-map is the core of the harness. Its static analysis records a project as
Meta-Code: file and symbol inventory, body, interface and effects digests,
interconnections and persistent semantic cards with surgical freshness.
senior-review, abstraction-architect, project-knowledge, project-delivery and
project-lifecycle require it and build their understanding on its evidence rather than
rediscovering the project. The map supplies evidence and leads, never verdicts:
correctness, documentation, tests and cleanup stay with their owners, who confirm
a lead by reading source. Leaf and specialist plugins such as work-controller,
skill-catalog, repo-hygiene, testing, clean-code and the language plugins do not
depend on it.

Every core harness command lives in one entry plugin, `daodan`, since marketplace 38.0.0 (see
`docs/superpowers/specs/2026-10-19-command-set-design.md`): one command per
intention, no parameters, the only argument free text. Authorizations are asked
when a step needs them, once, and recorded in the run. Each command is a thin
entry into its owner's method; every core specialist plugin keeps skills, roles and
contracts and has no command. A specialist method a command used to carry lives
in its owner's skill, where the entry loads it by name. Independent domain verticals (`research`, `digital-marketing`, `trading-broker-integration`, `pwa-expert`, `browser-extensions`, `grabber-development`, `libgdx-development`, `marketplace-ops`, `opentelemetry`, `rag-development`, `stripe`, `system-utils`, `xterm`, `ai-tooling`, `frontend-review`, `learning`) keep their own workflow namespaces.

The `daodan` commands are the primary entry points: start there for project
work, whatever the stack or domain, and call a vertical's own command directly
only when the request is already specific to that domain.

Design and brainstorming requests use the delivery method without requiring a
command: clarify the approach, write the specification, obtain approval, then
plan from the same document. New specifications use `docs/specs/` without a plugin
brand in the path, unless the user explicitly selects another destination.
Supplied historical specifications remain valid inputs; do not move them implicitly.

`office` owns the editable Word, PowerPoint and Excel methods, shared intake and
design, format helpers and specialist roles. Its entries (`start`, `presentation`,
`document`, `workbook`, `verify`, `fix`, `theme`) belong to `daodan`, which declares
the local Office dependency and the capabilities those methods require. Native
construction and rendering use separately available DeckCraft, WordCraft and
GridCraft runtimes; Office does not ship their engines or MCP servers.

project-delivery owns ADR, FRD, evidence bootstrap and the methods behind the delivery commands: initialization,
the task cycle (change, repair, refactor), continue, status, finish, sync,
realignment and retention. project-lifecycle owns assessment, consultant handover
and the Senior Maintainer campaign, composing project-delivery for execution stages. Since the closed-loop redesign of
2026-10-18 (see `docs/superpowers/specs/2026-10-18-closed-loop-harness-design.md`),
change is the task cycle: a probed preflight with the workspace mode chosen by the
user (worktree, branch or in place), an interview grounded in the map and in the
active decision records, a project specification under `docs/specs/` reviewed and
approved before planning (the run's intent binds its path, digest and approval),
separate technical decisions under `docs/adr/` on projects that keep them, and waves of micro-tasks
checked mechanically by the protocol helper and written by the stack's specialist,
an adversarial review of the intent, of the exact plan, of each task before its
atomic commit and of each wave, plus a branch review of the whole candidate
through senior-review, then integration that verifies the
record when there is one and realigns map, documentation and the instruction loop block. The size of
every review is computed by `review_roster.py` from measured signals, never chosen
by the model. Initialization brings a project into that cycle; realignment alone
follows a merge made elsewhere. peer-review challenges a record or a plan with
another model on request; moe gives a second opinion on request; neither runs by
default. Handover supplies evidence without granting edits or automatically
starting maintenance.
It prepares inputs and composes canonical specialist methods rather than duplicating detection
prompts. work-controller is the shared leaf for run records, snapshots, delivery
accounting, candidate gates, recovery and the questions a run waits on: `ask`
records a question before it is asked, `answer` records the user's own words,
and a task that consumes the answer waits while independent work goes on.
project-knowledge owns instructions, guides, documentation and README. senior-review owns universal correctness and
application subtraction, selecting React, TypeScript and platform specialists
through the same methods and delivery ledger. skill-catalog selects available
knowledge for any evidenced stack, with per-run fingerprints and delivery accounting.
testing owns universal test governance;
Python contributes pytest-patterns, without a second test writer.

Work Controller's canonical owner is `work-controller@daodan`. Its process
runtime, console assets and read-only MCP interface live under
`plugins/work-controller/skills/work-record/`; no separate Deadly Brain
repository or installation supplies the engine. Shinatama, Mukade and other
consumers may require this provider; the engine depends on none of their plugins.
`model-routing@daodan` retains model selection and pricing as its own local owner.
The process runtime admits immutable YAML graphs, tracks attempts and artifacts
in SQLite, and supplies bounded views, decision tickets and conservative resume.
The coordinator takes the ready frontier and dispatches agent work through the
host's actual mechanism. A handoff packet is not an installed-host adapter or
proof that a requested model was applied. Archetypes and domain rules (branches,
worktrees, decision records, commits) stay with their consumers. The broader
capability contract is section 13 of
`docs/superpowers/specs/2026-10-24-conversational-decisions-and-work-graphs-design.md`
and ADR-0002; transferring the existing engine does not establish every specified
capability. Keep both local providers free of consumer dependencies. The process
store lives in `.daodan/processes` of the main checkout. Existing `daodan/work/v1`
records and their agenda retain their identities and authority: a bound process
cannot bypass their grants, deliveries, questions or candidate-bound gates.

Run state belongs in .daodan/runs/<id>/ of the repository's main checkout, found
through the Git common directory, so a worktree's records survive its removal and
every session reads one agenda (.daodan/agenda.json, one row per task with its
branch and holder); outside Git the project is its own home. Each record carries an
identified project/worktree, scope, snapshot, authorization, plan, deliveries and
checks. The home carries a .daodan-root sentinel. Tri-Tech Code is an
external OpenCode consumer; private app storage needs a separately proved permission
binding. Helper writes are mechanically confined; other agent tool confinement
remains prompt-level until a runtime host probe demonstrates enforcement.

A missing delivery or mandatory gate prevents completion. Static inventory, deep
reading and runtime exercise are different coverage facts. CI for an old SHA does
not verify uncommitted candidate changes. Gate failures preserve preexisting edits,
foreign paths and successful prior phases; recovery uses the captured pre-phase
state, never an assumed HEAD~1. Published changes use authorized revert.

Tests protect requirements and independent failure modes. Classify product defect,
wrong oracle, environment and flakiness before quarantine. Counts, coverage, age and
a refactor do not by themselves justify retirement. Consolidation preserves verified
outcomes, conditions and evidence before artifact disposition. Quarantine is not
deletion; permanent purge is a separate scoped authorization of owned concluded
outputs. Deleted content bytes are not a measurement of filesystem free space.

## Working discipline

Working assumptions: State material assumptions and unresolved alternatives before dependent work. Ask only for an essential decision that existing instructions or authorization cannot resolve; continue independent authorized work.

Working simplicity: Choose the simplest design that satisfies approved requirements and existing contracts. Prefer, in order, suitable project code and conventions, platform or standard-library facilities, dependencies already available, then the least new code. Explain an exception when an earlier option cannot meet the requirement or is more complex overall. Reuse existing owners; add no speculative features, abstractions or configuration. Preserve boundary validation, data-loss prevention, security and accessibility. Before recommending or adopting a dependency, verify maintenance and support status, fit, compatibility, license, security and total integration cost using current official sources. Disclose unverified status; do not recommend discontinued or unverified libraries by default.

Working scope: Limit edits to the task and owned files, match existing style and preserve unrelated work. Remove code made unused by your changes; remove preexisting code only when its removal is explicitly authorized and any required checks or approvals are satisfied.

Working verification: Define observable success criteria from approved requirements. Run meaningful checks on the actual candidate and preserve independent protection. Report unavailable checks; missing required checks or deliveries keep the task open. Finish when the criteria are met.

Working redesign: Fix the cause, never the symptom. When a defect shows that a script, skill, contract or workflow is shaped wrong for its problem, redesign that unit from the ground up so it solves the whole problem, instead of patching the case at hand. A patch that leaves the design wrong is debt, not a fix; record the redesign decision and its reason.

## Context and output economy

Mantra: write the least code and agent instructions that preserve or improve
verified effectiveness. Design workflows and requested outputs to save tokens
across the whole run, including preparation, tool calls, retries and verification.
Reduce duplication and unnecessary context while preserving evidence, coverage,
readability and every required check.

Apply this discipline and economy when authoring skills, agents, tools, workflows,
templates and specialist guidance for any language, framework or activity. Carry
applicable obligations into the produced components through the
[component-authoring method](plugins/work-controller/skills/work-record/SKILL.md#authoring-components).

Keep always-loaded instructions focused on durable obligations. Link detailed
procedures and templates, then load the references required by the active step.
Use targeted searches and bounded tool output; expand reads whenever necessary
to establish evidence. Required source reading and independent verification keep
their full scope.

Produce each result once in its owner's canonical format. Coordinators link
detailed artifacts rather than duplicating them. Reuse fixed renderers for
recurring human views: agents supply content, code supplies layout, interactions
and derived values. Presentation code stays out of worker handoffs unless the
task edits it. Generate a visual view when it helps comparison, navigation or a
decision; otherwise keep the simplest sufficient format. Preserve provenance,
uncertainty, coverage and completion gates in every view. Token budgets are
guidance, and savings require measurement.

The `report-rendering` leaf supplies optional offline HTML views of canonical
Markdown. Domain owners retain their reports, scoring and verdicts. See
[report rendering](docs/plugins/report-rendering.md) for the executable contract.

## Documentation ownership and destinations

Daodan documentation uses one dossier per plugin under `docs/plugins/<plugin>/`:
index, functional/technical specifications, use cases and tutorials, research, validation,
dependencies, intakes and licenses. The documentation organizer's canonical
contract is `plugins/project-knowledge/skills/project-knowledge/references/documentation-organization.md`.
Intake provenance covers copied sources and delegated tools, runtimes, models
and parsers, with evidence-backed dates and both Daodan and upstream revisions.

Never create files or make in-place edits under `docs/superpowers/`, including
plans, specifications, research, generated indexes, link repairs and staging.
Before an existing artifact there is moved, merged, archived or retired, ask the
user whether to keep that identified document and where to move it; record its
own explicit answer. Global reorganization authorization does not replace this
decision. Preserve unanswered source bytes and continue independent work. An
approved relocation may remove its exact verified source, but creates no
replacement or redirect under the forbidden root. Operational notes remain in
the owned run; historical references do not authorize new writes there.

## Project structure

`plugins/<name>/` is a plugin's **content kernel**, and it is the only hand-authored plugin source alongside `adapters/`. Each kernel holds `plugin.toml` (the neutral control plane), `roles/` (agent bodies), `workflows/` (entry-point bodies plus one TOML sidecar each), `skills/`, `contracts/` and `policies/`. Those are also the only directories the compiler ships: a `references/`, `scripts/` or `mcp/` directory at the kernel root reaches no host package, so anything a body reads at runtime lives under `skills/<name>/`, and `scripts/lint_bundled_paths.py` fails a `${CLAUDE_PLUGIN_ROOT}` reference that the generated package does not contain. A kernel that ships an MCP server declares it under `[[mcp.servers]]` in `plugin.toml` (name, command, args, the server file under a skill) and requires the `mcp.servers` capability; the Claude adapter renders it as the package's `.mcp.json` and the catalog entry's `mcpServers` pointer, the OpenCode loader registers it from the package manifest, and Codex, Copilot and Pi, where no probe has shown a host starting a plugin-declared server, ship the file and open every workflow and every skill's `SKILL.md` of that plugin with a note giving the exact command to register: a consumer reaches a provider's tools through its skill. `codebase-map`, `peer-review`, `moe` and `work-controller` declare their servers under their owning skills, launched with `uv run --no-config --no-project --script` so the project under work never chooses a server's package index or interpreter. Markdown is always the behaviour; TOML is always declarative metadata and never carries a prompt.

Lifecycle callbacks are declared as neutral `[[hooks]]` in plugin.toml: named
session-start or user-prompt-submit event, skill-local Python script, literal
arguments and bounded timeout, with `hooks.lifecycle` declared required or
optional. Adapters generate native registration where supported; unsupported
optional hooks retain method checkpoints. Raw hook manifests/frontmatter do not
bypass the compiler. Enabling a plugin does not waive the host's trust review.
See `docs/hosts.md` for registration and execution evidence boundaries.

`adapters/<host>/` is what one host can do: `capabilities.toml` binds every neutral capability to a host mechanism, `coordination.toml` orders the coordination strategies that host supports, `layout.toml` says where each component lands in its packages and what the two Claude placeholders a kernel may write (`${CLAUDE_PLUGIN_ROOT}`, `$ARGUMENTS`) become on that host, `templates/` holds the harness wrappers, `policies/` holds this host's implementation of a neutral policy, and `overrides/` holds fingerprinted semantic divergences.

**Everything under `exports/` and every root marketplace manifest is generated.** `scripts/daodan_build.py` compiles kernels plus adapters into `exports/claude/`, `exports/copilot/`, `exports/codex/`, `exports/pi/` and `exports/opencode/`, and into `.claude-plugin/marketplace.json`, `.github/plugin/marketplace.json`, `.agents/plugins/marketplace.json`, the root `package.json` and `exports/opencode/package.json`. The last two are the odd members and neither is a Node project. Pi has no marketplace, it installs a package and reads the manifest at that package's root, so the repository root is where its catalog has to live. OpenCode V2 has none either: a package reaches it only as a plugin, so its catalog is that plugin's own manifest, whose `daodan` key lists every skill, agent, command and MCP server, and the package carries `index.js`, a fixed loader copied verbatim from `adapters/opencode/templates/` that registers them from that key. The loader imports nothing outside Node's standard library, and its tests run under `node --test` from the Python suite. Report-rendering browser assets live under their owning skill and require no Node runtime in generated reports. Never hand-edit any of them; edit the kernel and rebuild.

`AGENTS.md` and the four repository workflow skills under `.agents/skills/` are native Codex adaptations of this file and `.claude/skills/`. Generate them with `python scripts/sync_codex_instructions.py`; `--check` is the parity gate. Edit the Claude-side canonical copies, then run the synchronizer. The transformation is deliberately limited to instruction paths, cache paths, install commands and the host-relative downstream description.

A kernel can export canonical contract files through `[contracts].exports`. Workflow `contract.shared_schemas` names a required provider and its exported `contracts/` path; schemas stay in one source location and are rendered by the compiler. Cross-plugin phase roles use `plugin/role` and are validated against the kernel registry. A role of another marketplace's plugin is declared by its qualified dependency: named-agent hosts dispatch its qualified identity and inline hosts read its body from the installed provider. A composed method's additional workers are declared in `[dispatch].roles` rather than fabricated scheduling phases. `isolated` declares context requirements; `inline_workers` explicitly permits task-specific work through work-controller's isolated-worker. Dispatch references require declared providers and actual roles. Inline adapters receive generated unregistered dispatch bodies from the canonical owner; named-agent adapters use owner-qualified IDs. `invoke` is rejected until an executor is implemented and proved.

The compiler is `scripts/daodan/`: `model.py` and `load.py` (strict TOML loading), `validate.py` and `trust.py` (semantic and secret validation), `adapter.py` (capability parity and strategy selection), `overrides.py` (the fingerprint gate), `render.py`, `templates.py`, `provenance.py`, `catalogs.py` and `report.py`. Standard library only, no third-party dependency anywhere in the toolchain.

`codebase-map` is the canonical static analysis plugin, formerly `codebase-xray`
(and `deep-dive-analysis` before marketplace 14.0.0). Its downstream artifact
contract is `.codebase-map/`, declared in its write-confinement policy. The
former compatibility plugin is retired: only `codebase-map` methods and worker
identities are registered, and its entry is `/daodan:map-code`. Before producer or consumer root lookup,
`map-method`'s project-bound migration helper moves an idle
`.codebase-xray/` archive without changing evidence bytes and leaves an explicit
relocation record. Historical analysis paths are resolved through that record;
new runs only write `.codebase-map/`. Active legacy runs and conflicting populated
roots block migration. Never merge archives, silently choose a competing root,
or rewrite stored snapshots and citations. See [migration](docs/codebase-map-migration.md).

The Codebase Map is static analysis and stays so: runtime evidence counts only when the user supplies it. Marketplace 28.3.0 drew the consequence after a Phazly incident of 2026-09-14: a global dark-theme rule in a `.css` file overrode a consent screen's positioning and locked users out on mobile, and the Codebase Map run that had the component in its inventory could not have cited the rule, because `snapshot.py` inventoried only parsed source and configuration and dropped every stylesheet. Presentation files now enter the manifest, paths that gate entry into the product are mandatory critical paths traced with their effective style cascade, `Usability-blocking` is a risk category, and the final report states three coverage figures: files in inventory, files read in depth, files exercised at runtime, the last always none. A file count is never coverage. Marketplace 28.4.0 made CSS, SCSS and LESS a parsed language, one symbol per applied rule, and added `cascade_scan.py`, which lists every rule whose selector reaches the document root or its untargeted children and sets a property that decides layout, with the rules it can override and what decides it. Its output is leads: whether two selectors match the same element is confirmed by reading, in Phase 5. Its Tailwind `@apply` expansion is load-bearing: on the incident's own stylesheets 90% of the applied rules used `@apply`, the consent modal's `fixed` included, and without it the scan found the culprit and missed the victim. Exercising those paths in a browser belongs to the project's own tests or to `frontend-review`; do not add a browser step to the Codebase Map on a later pass.

Marketplace 32.2.0 gave the Codebase Map a perimeter, by decision of 2026-10-08: below its target it never analyzes what Git ignores or any directory whose name starts with a dot, on top of the dependency and build directories it already skipped. `tree_scope.py` owns the rule and every script that walks a tree applies it (`snapshot.py`, `cascade_scan.py`, `usage_finder.py`, `rewrite_comments.py`, `doc_review.py`), so no script reads more than the snapshot records. The motivating case: a lifecycle campaign's own records under `.daodan/` and `.team-review/` entered the next snapshot as project files, and an incremental update of an untouched project asked for a full analysis. Two properties keep the rule from becoming the stylesheet blind spot again. The target is analyzed as given, so naming `.github/` is how a project's CI gets a Codebase Map. A target that an enclosing repository ignores, itself or through a directory above it, is not that repository's: since marketplace 36.0.1 it is its own root, analyzed whole, because a project kept under a tool's ignored run directory had taken that tool's paths, commit and dirty flag. And the exclusion is declared: `snapshot.py scope` prints it for the scope confirmation, the manifest's `scope` block keeps it, and the final report's inventory line repeats it. Do not narrow the rule to a list of known tool directories on a later pass: a list is what lets the next tool's output in.

## Operational compatibility of host exports

> [!WARNING]
> **Host exports are an execution contract, not proof of execution.** Fix shared
> behavior in `plugins/` and host mechanisms in `adapters/` or the compiler; never
> repair generated `exports/` or marketplace manifests by hand. Check all five
> hosts through entries, agent bodies, skills, nested references and dispatch
> resources, not just hashes, registration or frontmatter. Bind real tool names
> and input schemas, component kinds and IDs, isolation even for one required
> worker, inherited or available requested models, permissions and required
> providers on the active host. Verify browser capture, background lifetime,
> stdin and an explicit stop signal; bind output paths to helper arguments,
> contracts and result readers together.
> Agents execute and verify work; coordinators collect deliveries and own the
> final report. Harnesses own supported dispatch, continuation and state; skills
> supply methods and knowledge, not an executor or a persistence mechanism.
> A stopped turn, idle event or empty child response is not a delivered result.
> Keep registration, compiler/adaptation tests, installed-host probes and live
> workflow evidence separate; do not claim enforcement that has not been proved.

Host compatibility covers every instruction a worker consumes: entry bodies,
role bodies, skills, bundled references and generated dispatch resources.
Registration, matching digests, valid frontmatter and a supported capability row
prove their own structural contracts; they do not prove that the body can call
the host's tools or complete its workflow.

- Keep behavior in the neutral kernel and executable host mechanisms in adapters
  and the compiler. Fix the source and regenerate all five hosts. Never repair
  generated exports by hand or rely on a consumer-only workaround as the upstream fix.
- Review operational tool names, case, input fields, permissions, dispatch,
  model selection, user questions and dependency recovery on each host. A role
  with no source tool restriction must not silently become a read-only worker.
  Default models inherit; documented overrides need a binding to an available
  host model, rather than a foreign model alias copied into the body.
- Distinguish skills, roles and workflows using each host's registered identity.
  Loading a role as a skill is not dispatch. Inline-role adapters need the actual
  role body and its provider references, not an invented named-agent call.
- Inspect every phase and method-owned worker, including a single `phase.role`
  without fan-out. The rendered mechanism must preserve isolation, permitted
  workers, declared inputs, delivery accounting and the report owner. A wrapper
  cannot neutralize conflicting dispatch instructions nested in a skill.
- Verify terminal stdin, background execution, completion signals and browser/MCP
  availability before requiring an interactive checkpoint. When stdin is absent,
  bind a supported stop signal that preserves live capture. Do not substitute an
  unrelated browser skill or invent a tool because a required dependency is missing.
- Preserve required-provider failures and give recovery instructions for the
  active host. External marketplace names are dependency identities, not evidence
  that another host can execute the Claude installation command.
- Keep execution responsibility in agent bodies and coordinator harnesses. While
  the requested result remains reachable within existing authorization, continue
  the work and recovery. Diagnose tool errors, correct the cause, retry and verify
  the outcome; do not retry blindly or close with only a promise. Stop only for a
  documented blocker, a missing required capability, an essential human decision
  or the caller's stop, reporting obtained results and the concrete next requirement.
  The coordinator verifies expected artifacts and coverage, then inspects or
  resumes missing/partial deliveries or records failure. The harness preserves
  the owned delivery ledger and completion gates; a worker stop cannot mark the
  task successful. These are agent obligations unless a measured runtime gate
  demonstrates mechanical enforcement, not a claim of a universal scheduler.
- Scope adaptation to executable host instructions. Keep code examples, shell
  language labels and host-as-subject material intact. Do not use global token
  replacement to translate dispatch schemas or rewrite domain code.
- Add regressions for the affected operational contracts on all five rendered
  hosts, including referenced content and negative capability cases. Retained
  host-vocabulary baseline entries are debt, not compatibility evidence; never
  enlarge them to make a fix pass. Keep compiler checks and installed-host probes
  separate in verification reports, recording host version and exercised path.
  An empty worker response or a completed turn alone is not a delivered result.

Tri-Tech Code consumes the OpenCode export. Its app-specific permissions, Gateway
catalog, project paths and routing belong to its permanent integration; shared
host translation defects belong upstream. A project-output relocation must bind
helpers, contracts and result readers together, not change a path in prose alone.
See [host maintenance](docs/hosts.md#operational-compatibility-review) and the
repository `downstream-exports` workflow for the review procedure.

## Conventions

- Agent names: kebab-case matching the filename (e.g. `quick-searcher.md`)
- No name is shared across component kinds inside a plugin. `validate_component_kinds` fails the build when a skill, role or workflow repeats a name: OpenCode lists skills and agents in one `@` menu, and a name meaning two things in one plugin is ambiguous to every body that cites it. A role beside a same-topic skill takes `-agent` (`abstraction-architect-agent`), a skill beside a same-topic workflow takes `-method` (`brand-naming-method`, after `codebase-map`'s `map-method`). Marketplace 29.0.0 renamed the five components that broke this rule.
- Plugin names: kebab-case directory names
- Default model: `inherit` (agents follow the session model instead of pinning one). A user-requested override must resolve to a model available on the active host.
- Agent `color` must be one of: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`
- Agent body style: terse keyword lists, imperative tone, structured with markdown headers; simple agents ~50-200 lines, complex agents up to ~700 lines
- Long `description` frontmatter values use the YAML multiline `>` form
- Skills supplementary subdirs: `references/`, `scripts/`, `templates/`, `assets/`, `lib/` as needed
- No build step or runtime framework - plugins are markdown with optional helper scripts (Python, JS) in skills' `scripts/` subdirs
- Avoid the dash-aside construct anywhere (code, comments, commit messages, documentation). The rule targets the *rhetorical pattern* of bracketing a clause between dashes, in any form: `—` (em dash), `--` (double hyphen), or ` - ` (spaced hyphen). All three are banned when used to wrap a parenthetical aside (e.g., "lorem ipsum -- lorem ipsum -- lorem ipsum"). Substituting `--` for `—` is **not** the fix. Rewrite into separate sentences, parentheses, colons, or just delete the aside. Hyphenated compounds (`file-ownership`, `multi-agent`) are unrelated and fine.
- **CLAUDE.md never records transient, runtime, or temporary state.** Never. This file states durable facts: structure, conventions, policies, workflows, and the reasoning behind them. It is not a status board. Nothing goes in here that is true only until the next run, the next commit, or the next session: in-progress task lists, "currently", "pending", "as of today" notes, open branches, scratch paths, session findings, backlog items, or anything that would need editing merely because time passed. If a fact has an expiry, it belongs in the commit message, an issue, a design doc under `docs/`, or session memory. A stale claim in this file is worse than no claim, because everything here is read as ground truth.

## Marketplace update workflow

When changes modify a plugin kernel, update the marketplace **before committing**:

1. **Bump the plugin version** - increment `version` in that plugin's `plugins/<name>/plugin.toml`: patch for a fix or a fact update, minor for a new capability, section, file or reference
2. **Rebuild** - `python scripts/daodan_build.py`, then `python scripts/daodan_build.py --check`
3. **Commit together** - stage the kernel files and everything the build regenerated under `exports/` and the root manifests, in one commit
4. **Push to remote** - `git push` to `master`

`metadata.version` in `.claude-plugin/marketplace.json` is the release number, not a per-change counter: bump it only when the user asks for a release. `publish-marketplaces.yml` tags each new value `v<metadata.version>`, and Pi and OpenCode install that tag, so a plugin change reaches those two hosts at the next release; Claude Code, Copilot and Codex read the registered repository and follow the plugin version. A release takes a patch or minor increment like a plugin.

A major version, of a plugin or of the marketplace, needs the user's explicit request or a breaking change: a removed or renamed plugin, component or command, a changed contract or artifact path that a consumer reads, or a new dependency a user must install. Restructuring, new features and large changes that keep every existing entry working are minor. This is the decision of 2026-10-27, taken after the marketplace reached 42.x by bumping on every change.

There is no hand-mirroring step any more, and no per-host obligation to remember: the compiler writes every host, and `--check` fails the build when a committed package no longer reproduces from its kernel.

## Adding a new plugin

1. Create `plugins/<name>/plugin.toml` declaring `schema = "daodan/v1"`, identity, `[capabilities]`, `[dependencies]` and `[components]`
2. Add the component bodies: `roles/<role>.md`, `workflows/<workflow>.md` with a `workflows/<workflow>.toml` sidecar, `skills/<skill>/SKILL.md`, and any `contracts/` or `policies/`
3. Declare capabilities from the closed registry in `scripts/daodan/validate.py`. A capability outside it fails the build rather than being guessed at by an adapter. Local dependencies go in `[dependencies].required`, always: see the dependency policy below
4. Build every host and commit the kernel plus the generated output together

## Git workflow

- Single branch: `master`
- Commit style: imperative, descriptive (e.g. "Add high-value keywords to prompt-engineer agent")
- Primary workflow: direct push to master (PRs used occasionally)

## Build / CI

The build is `python scripts/daodan_build.py`. It loads every kernel, validates it, binds it to each adapter, renders every package into a temporary tree, and replaces the live output only after every validator passes. `--check` renders the same tree and reports drift instead of writing, and it is the gate CI runs. Exit codes: 0 clean, 1 drift or validation failure, 2 invocation error. Publication always builds every host; `--host` narrows the run and is accepted only under `--check`, because a marketplace where one host is a commit ahead of the others is the drift this compiler exists to prevent.

`.github/workflows/consistency.yml` runs on push to `master` and on PRs. Its checks run from the repository root. The compiler and tooling are stdlib-only; Work Controller behavioral tests use the runtime PyYAML dependency installed by CI:

1. `python scripts/lint_dependency_graph.py` — the dependency-graph linter. Extracts runtime cross-plugin references (agent spawns, skill loads) from plugin bodies and enforces: every runtime reference is declared in `dependencies`; bare dependency names must exist in this marketplace (cross-marketplace deps use the qualified `name@marketplace` form); the forbidden edge `codebase-map → senior-review` never reappears; **no plugin in this marketplace appears in another's `optionalDependencies`**; and **no plugin body makes something conditional on a hard local dependency being installed, or names a fallback for one**. Those two passes are the two halves of the dependency policy below, over declarations and over prose. A further pass enforces that **no hard local dependency goes unused**, which is the only check that notices a dependency silently reintroduced by a concurrent writer.
2. `python scripts/lint_bundled_paths.py` — the bundled-path linter. A body that says to read `plugins/<name>/skills/x/references/y.md` names a path that exists only in a checkout of this repo, so for an installed user that read silently fails. Self-references must use `${CLAUDE_PLUGIN_ROOT}/...` or a skill-relative `references/...` path inside that same skill, and no plugin may reach into another plugin's files by path. Its `GRANDFATHERED` map is empty: its first run found 40 such references across 26 files and they were fixed rather than baselined. Fix a reference, delete its entry; never add one to make a build pass. Its third pass, `shipped refs`, resolves every `${CLAUDE_PLUGIN_ROOT}/...` reference against the generated Claude package and fails the ones no package contains, because a well-formed path to a file the compiler never copies fails at runtime exactly as silently as a checkout path. Its motivating case was `ai-tooling`, whose reasoning-patterns reference sat at the kernel root, unshipped on every host, from the kernel neutralization until marketplace 27.1.0. Its `UNSHIPPED` baseline is empty too: its first run found 23 such references, `peer-review`'s protocol documents and MCP server and `research`'s two search scripts, all at kernel roots the compiler never copies, and marketplace 27.2.0 moved every one under its plugin's skill rather than baselining it. Move the file under a skill, fix the reference, never add an entry. Its fourth pass, `skill refs`, covers what the third cannot see: a role or workflow sits outside every skill, so a bare `references/<file>.md` in its body must name a file under a skill of its own plugin or of a local plugin it declares. Its motivating case was `app-analyzer`, whose role read `references/report-templates.md` from an `agents/` directory at the kernel root, unshipped on every host until marketplace 28.6.1.
3. `python scripts/lint_plugin_registration.py` — the registration linter. A component present in a package but missing from that plugin's catalog entry does not exist at runtime, so a spawn fails with "Agent type not found" and takes its phase down. It runs both directions over all three content kinds, against the **generated package** named by each catalog `source`. A neutral kernel is skipped as a package root on purpose: its bodies live under `roles/` and `workflows/` and the compiler decides their installed paths. A third pass covers Pi, whose catalog registers nothing by name and globs the tree instead: there the same invariant inverts into whether every generated component of a registered kind falls inside a declared glob, and whether every glob reaches anything at all. A fourth covers OpenCode, whose loader registers what the `daodan` key of `exports/opencode/package.json` names: every `file` there exists, and every rendered skill, agent and command is named by one. A fifth, `component refs`, reads kernels, adapters, these instructions, the README, docs and evals: every `plugin:name` naming a local plugin must be a skill or role it registers, and every `/plugin:workflow` a workflow it registers. Dated design records under `docs/superpowers/` and the migration notes keep retired names on purpose and are not read. It was added when marketplace 38.0.0 moved every command into `daodan`, and its first run found six references that already named nothing.
4. `python scripts/lint_fact_anchors.py` — the fact-anchor linter. A knowledge plugin states the same load-bearing fact in several artifacts on purpose, because each is loaded on its own. The redundancy is correct; what it costs is that a correction must land in every copy at once, so the linter compares them and fails the build naming both files. Its motivating case: a Web API rate limit sat wrong in one file for months because every copy was internally plausible and no two were ever compared. Add an anchor the second time you correct a fact; never delete one to go green.
5. `python -m unittest discover -s tests` — the compiler's own suite plus the port and parity contract tests: the neutral model, validation, adapter parity, the override fingerprint gate, deterministic rendering and transactional replacement, catalogs, the CLI, both canary ports, universal catalog parity, the publication workflow contract, the cutover identity gate, what each host package must say (`test_daodan_host_rendering.py`, on the real `codebase-map` and `senior-review` kernels) and the Codebase Map script suites (`test_xray_scripts.py`, `test_xray_snapshot.py`, `test_xray_stylesheet.py`), and the OpenCode loader's `node --test` suite through `test_opencode_loader.py`, which both workflows give a Node runtime so it runs rather than skips.
6. `python scripts/daodan_build.py --check --support` — the drift gate. Every committed package and catalog must reproduce byte-for-byte from the kernels and adapters in the same commit.
7. `python adapters/copilot/policies/xray-guard/test_xray_guard.py` — the Copilot write-confinement policy implementation, 36 cases.
8. `python scripts/check_version_bumps.py <base-rev> [<head-rev>]` — over the pushed or PR range, a change under `plugins/<name>/` or under `adapters/<host>/overrides/<name>/` must come with a bump of that plugin's version. `metadata.version` may stay as it is; when it changes it must increase, because a published release number is never reused. Generated packages under `exports/` never count: they are compiler output, and a rebuild is not a plugin change.
9. `python scripts/lint_host_vocabulary.py` rejects host-specific team primitives in neutral behavior. Kernels state delivery/ownership/barrier obligations and adapter wrappers supply their mechanisms. The baseline is empty. Operational tool names and dispatch fields in nested references are checked alongside team primitives; neutral frontmatter and host-as-subject examples are preserved. Never add a baseline to make a check pass. Marketplace operations and SDK knowledge retain host vocabulary when tooling is their subject; instruction examples belong to the knowledge owner's skill.

When a change legitimately trips a linter, fix the declaration or the reference, not the linter; heuristic misreads go in its `ALLOWLIST` with a reason.

### The publication workflow, which writes rather than checks

Both CI workflows also run the documentation and instruction parity gates:
`python scripts/sync_plugin_docs.py --check` and
`python scripts/sync_codex_instructions.py --check`. A source change that alters a
registered component, dependency closure, contract, adapter binding or repository
instruction must regenerate the corresponding documentation before publication.

`.github/workflows/publish-marketplaces.yml` is the only workflow here that pushes. On every push to `master` it rebuilds every marketplace, verifies the built tree reproduces, and commits the result as "Publish native Daodan marketplaces". It publishes every host or none, and the final `--check` runs before the commit rather than after it.

Its last step publishes a GitHub Release, `v<metadata.version>`, on the commit it just published. The step is keyed on the version rather than on the push, so it creates a release exactly once per marketplace version and does nothing on a push that bumps nothing. The release carries no asset, because the install path is the marketplace registration and always was: the tag exists so a version can be traced to a commit, and so a curated-directory submission has an immutable revision to pin.

It runs under a `concurrency` group so two pushes cannot each build against a different base and revert one another, and it skips any push whose head commit was authored by `github-actions[bot]`, which is what stops it answering its own commit. That guard is identity-based for a reason: its predecessor matched a marker string anywhere in the head commit message, which reads the body as well as the subject, so a commit that merely *mentioned* the marker in its prose silenced the job, and one did so within the hour. **Never gate a workflow on prose the author is free to write.**

It needs repository-level `default_workflow_permissions: write` (**Settings**, **Actions**, **General**, **Workflow permissions**). A workflow's own `permissions:` block cannot grant more than that ceiling, so without it `git push` and any release step answer 403 with no other symptom. That setting is invisible in every file here; check it before the workflow when publication starts failing on permissions.

GitHub does not start a workflow from a push made with `GITHUB_TOKEN`, so the bot's publication commit triggers nothing at all. **`consistency.yml` never sees a publication commit**. The publication job runs the unit suite, documentation and instruction parity gates, rebuild and deterministic drift check before committing. The remaining consistency linters are separate checks on the initiating source commit. A gate intended to validate the bot's published tree must also run in the publication workflow; adding it only to consistency does not provide that coverage.

### Distribution

Registering the repository root as a marketplace is the whole distribution story, on the three hosts that have marketplaces:

```bash
claude plugin marketplace add acaprino/daodan
copilot plugin marketplace add acaprino/daodan
codex plugin marketplace add acaprino/daodan
```

**Pi is the exception, and it is not a gap in the port.** Pi has no marketplace at all: `pi install` accepts npm, git or a local path, and nothing else. So the unit is the repository, pinned to a released tag, and the whole marketplace arrives at once:

```bash
pi install git:github.com/acaprino/daodan@v<metadata.version>
```

Three consequences bind anything done here later. **Selection is a settings concern on that host**, through the object form of `packages`, never a narrower install; a user picks plugins by filtering globs, and the choice survives updates. **Distribution is git only, deliberately**, because the tag already exists and the generated manifest is byte-identical to what an npm publication would carry, so adding npm later is additive and adding a release asset is not: Pi cannot install an archive, so an asset could only ever be unpacked by hand into `~/.pi/agent/skills/` as loose files with no ref, no `pi update` and no filtering. **Two companion packages carry mechanisms Pi's core omits on purpose**, `pi-subagents` for an isolated worker context and `pi-mcp-adapter` for MCP, both named in the bindings' `package` field so a harness template renders the install line from the adapter rather than from its own prose.

**OpenCode V2 is the second exception.** It has no marketplace either, and a package reaches it only as a plugin, installed by npm spec. The spec points at `exports/opencode/` inside the tagged repository through npm's `::path:` selector, which is what keeps the root `package.json` Pi's:

```bash
opencode plugin add 'github:acaprino/daodan#v<metadata.version>::path:exports/opencode'
```

OpenCode Desktop needs nothing of its own: it bundles the V2 CLI and runs it as a background service, and that service is what loads config and plugins, so one install serves both. Three consequences bind anything done here later. **The target is V2 only, by decision**: V1 has a different plugin API, agent schema, permission model and MCP shape, and a dual package would carry two implementations of every registration path for a line the vendor is replacing. **Selection is a loader option**, `{"package": "<spec>", "options": {"plugins": [...], "exclude": [...]}}`, and the dependency policy outranks it: a selection always brings its transitive closure of local dependencies, an exclusion never removes a plugin a selected one depends on, and both overrides are logged. **The loader is data-driven and never generated per plugin**: everything plugin-specific is computed in Python and written to the manifest, so the toolchain stays stdlib Python and the drift gate covers the loader like any other output. Its isolation is native, unlike Pi's: roles register as agents with `mode: subagent` and run through the built-in `subagent` tool, so the harness has no missing-tool branch, and a role's permission list ends with an `external_directory` allowance scoped to the installed package, because the package lives in OpenCode's cache, outside every project.

There is no extension, no `.vsix` and no packaging job. The VS Code extension that used to carry the Copilot port was a workaround from before Copilot read plugin marketplaces, and it was removed at the universal cutover along with its release workflow and its skill-copy lifecycle. Historical GitHub Release assets are left untouched and are unsupported: they predate the universal migration and nothing rebuilds them. What the Releases page carries now is one assetless tag per published marketplace version, `v<metadata.version>`, written by `publish-marketplaces.yml`. It is a record of which commit a version shipped from, never an install path, and it is never hand-created: bump `metadata.version`, push, and the workflow tags it. `docs/migration-from-claude-code-daodan.md` holds the one-time migration and the rollback rule: roll back with a revert plus a **new** patch version, never by reusing a published version and never by renaming the repository back.

## Documentation

`docs/catalog.md` and the marked reference blocks in every `docs/plugins/<name>.md`
are derived from kernel manifests, component frontmatter, workflow sidecars and
adapter bindings by `python scripts/sync_plugin_docs.py`. They cover the complete
component inventory, direct and transitive mandatory dependencies, workflow
contracts and host package paths. Edit explanations outside the markers, then
regenerate the references after changing their source facts. `--check` is a
read-only drift gate in both consistency and publication workflows, alongside
the Codex instruction parity gate. It fails when a plugin page is missing or a
generated reference is stale. `docs/hosts.md` explains installation, selection,
entry-point mapping, environments, MCP, dispatch and enforcement limits. These
references document compiled support; they do not establish live host behavior.

`docs/plugins/` contains per-plugin documentation. `docs/references/` holds cross-cutting knowledge bases that inform changes across multiple plugins — notably [`agent-teams-best-practices.md`](docs/references/agent-teams-best-practices.md), the source of truth when restructuring any plugin that spawns multi-agent teams or pipeline reviewers (`senior-review`, `project-knowledge`, `research`, `codebase-map`), and [`prompt-engineering-and-brevity.md`](docs/research/prompt-engineering-and-brevity.md), the research basis for concise, verifiable prompt and agent design. `evals/` holds eval harnesses: development assets, never shipped, not registered in `marketplace.json`. `evals/project-delivery/` covers pre-commit evidence, interrupted commits and independent delivery. `evals/senior-review/` measures review recall against ground-truth bugs (cases plus scoring protocol). `evals/ai-tooling/` is a different shape, because that plugin has no bugs to recall: its 15 cases assert **behavioral invariants** (the frontier is never auto-picked, a contract survives optimization, an installed SDK outranks a bundled reference, an every-call rule uses a `PreToolUse` hook) so that a later edit cannot quietly remove one. Assertions target the philosophy, never the wording, and a case that fails once keeps its case forever. `evals/research/` follows the `ai-tooling` shape for the deep-research pipeline (marketplace 25.0.0). `evals/codebase-map/` does the same for the Codebase Map pipeline (marketplace 26.4.0): twelve behavioural-invariant cases (Phase 0 at every depth, run isolation, parsers over hand reading, forbidden files never quoted, claims cite evidence and carry a status, partition ownership, scope authorization and mapper scope in team mode, incremental runs carry unaffected claims forward and re-derive only what changed, declared coverage with stylesheets parsed and scanned and the perimeter's exclusions named, standalone map consumption without Daodan commands with source verification and explicit fallback), the first nine written after the 2026-09-03 review; `evals/codebase-map/RESULTS.md` records which have run. The script half of that plugin is pinned mechanically instead: `tests/test_xray_scripts.py` runs the regex fallback on CI and the tree-sitter path wherever it is installed, `tests/test_xray_snapshot.py` pins the incremental snapshot, and `tests/test_xray_stylesheet.py` the stylesheet adapter and the cascade scan.

The review entries, `/daodan:review-changes` and `/daodan:review-branch`, are thin pointers to the canonical review-method, review-preparation and review-consolidation skills; the light review is its own unit and reads none of the variant references. Agent prompts, fix-loop and native output references remain under review-quality-gates. application-cleanup-method is the named Step 7c method, reached from `/daodan:tidy-repo`, and carries severity acceptance, exclusive-workspace/clean-tree prerequisites and snapshot-bound gates. A `fix` authorization edits and verifies without committing; a `commit` authorization additionally commits and is required for bulk application subtraction.

## Research technique: when a direct fetch is blocked, drive a browser

Many vendor documentation sites (IBKR's `interactivebrokers.com/docs/` among them) return **HTTP 403 to WebFetch** while serving the same pages fine to a real browser. A 403 is a bot-detection result, not evidence that the page is gone or that the fact is unverifiable. Never downgrade a claim to "unverified" on a 403 alone.

The escalation path, in order:

1. `WebFetch`. If it returns 403 or empty content, do not retry it and do not conclude anything from the failure.
2. **Drive a real browser with the Playwright MCP tools** of the `playwright` plugin (`playwright@claude-plugins-official`, Microsoft's Playwright MCP server, a hard dependency of `app-analyzer`, `digital-marketing`, `grabber-development` and `pwa-expert`; install with `claude plugin install playwright@claude-plugins-official`). `browser_navigate` opens a visible browser, which also passes bot detection that headless does not; `browser_snapshot` reads the page and `browser_run_code_unsafe` runs any Playwright extraction code.
3. Check whether the site publishes an **LLM-friendly index**. IBKR's docs expose `/llms.txt` at the root and serve clean Markdown for any page by appending `.md` to its URL, which is faster and cleaner than scraping rendered HTML. Look for that before writing extraction logic.

This is how the five "unverifiable" IBKR facts in the 2026-08-09 `ibkr-trading` refresh were actually resolved, one of which (a plugin claim that error code 10167 exists) turned out to be false rather than merely unconfirmed.

Production installations and their configuration are protected. Verification may reuse binaries only with an independently owned disposable configuration; it must never launch or edit production configuration. Record machine paths, installed builds and the permitted probe environment in the owning run.

## The characteristic defect here is cross-file contradiction

Almost nothing in this repository is stated once. A plugin's behaviour is described by its own kernel files, compiled into five host packages, summarized in `docs/plugins/`, asserted by an eval, and ruled on here. That redundancy is deliberate and mostly correct, since each artifact is loaded on its own. What it costs is that **the failure mode is almost never a broken file; it is two files that no longer agree**, and every mechanical guard this repo has grew from one instance of it: the fact-anchor linter, the registration linter, the version-bump check, and the drift gate that replaced hand-mirroring outright.

The compiler removed one whole class of it. A host package can no longer disagree with its source, because it is not written by hand: `--check` fails the build the moment a committed package stops reproducing from its kernel. What it cannot check is prose that describes behaviour, which is why the fact-anchor linter still earns its place.

The `research` 6.0.0 release is the worked example, and the lesson is about how to review rather than what to write. It ran as ten tasks under subagent-driven development, each with a fresh reviewer against its own diff, and **all ten came back clean**. The final whole-branch review then found one Critical and three Important, and every one of them was a cross-file contradiction: an export frontmatter broken in a way its own task's review had no reason to parse, and three tracked files elsewhere in the repo still describing the contract that branch had just replaced. A per-task review verifies the diff it is given; only a whole-branch pass asks what the diff invalidated somewhere else. Budget for that pass, and point it at the files the change makes stale rather than only at the files the change touched.

## Repo workflows

Four maintenance workflows live in `.claude/skills/` so they load only when the task calls for them. Load the matching skill before starting; do not improvise these from memory.

| Skill | Load it when |
|---|---|
| `external-repo-intake` | Evaluating a new external capability through declared delegation or original local inspiration. Covers canonical ownership, licensing, active-host availability, wiring and authorized delivery. |
| `upstream-sync` | Re-syncing a plugin already ported from an upstream repo, or answering "which plugins are upstream-synced". Holds the sync table, the merge strategy, and the per-plugin sync notes. |
| `custom-plugin-refresh` | Refreshing a hand-authored plugin that has no upstream. Holds the freshness risk classes, cadences, and the re-research protocol. |
| `downstream-exports` | Changing how a host package is shaped: an adapter layout, a harness template, a capability binding, a policy implementation, or a semantic override. Holds what each host expects, what the compiler generates for it, and the content that deliberately keeps host-as-subject vocabulary. Nothing under `exports/` is ever edited by hand. |

## Broker knowledge lives in one plugin

All broker and trading-platform knowledge lives in a single plugin, `trading-broker-integration`, with one skill per vendor (`ibkr`, `mt5`) alongside the vendor-neutral `broker-vocabulary` skill that supplies the shared terms every vendor skill is written in: the five archetypes, the single-broker/multi-broker-platform axis, the reference order-lifecycle model, and the evidence ladder.

That shape replaced one plugin per broker (`ibkr-trading`, `mt5-trading`, `trading-broker-connectivity`) in this consolidation. The reason is what research into a third broker, WH SelfInvest, established: the durable unit of knowledge is the platform, not the broker. WH SelfInvest's main account is contractually an Interactive Brokers account, its NanoTrader platform is a Fipertec product, and its futures run over CQG. A broker reselling three platforms does not produce one plugin, it touches three that already exist for other reasons. If the unit is not the broker, one plugin per broker was the wrong partition to begin with, and it is what made a per-plugin conformance contract look necessary: a contract exists to police a boundary, and the boundary here was drawn in the wrong place.

A two-level conformance contract (`base` and `verified`, each with its own declaration lines) and a linter enforcing it (`scripts/lint_broker_plugins.py`) existed for that old partition and were deliberately removed in this consolidation, along with `.claude/skills/broker-plugin-contract/`. This is recorded so nobody reintroduces them believing their absence was an oversight. A future broker or platform gets a new skill under `trading-broker-integration`, not a new plugin and not a revived contract.

## Deliberately not vendored

Ten areas were removed and delegated to their upstreams because maintaining the local copy cost more than it returned (most were vendored copies handed back; `git-worktrees` was locally authored content retired in favor of equivalent upstream coverage; `prompt-improver` was a local JS re-port handed back to its upstream in 17.0.0; `codebase-cleanup` was retired outright because its verified content defects made delegation undesirable). Do NOT re-import or re-create them, and do not add rows for them to the sync table in the `upstream-sync` skill on a future "upstream updates" pass. The delegation table below records their owners and retirement history.

Standing policy since 2026-08-04: this repository no longer maintains vendored copies of external repositories. New capability never gets vendored in; it gets delegated with a declared dependency.

One scoped exception is in force: `office` vendors the open-slide PPTX exporter subset (`plugins/office/skills/pptx/lib/open-slide-pptx/src/`, eleven files of `@open-slide/core`, MIT, at the pin recorded in that directory's `build.deps.json`), because the owner authorized that exact copy on 2026-10-27 to obtain mechanical HTML to PPTX conversion without a runtime dependency on the upstream package. The exception covers those files, their prebuilt bundle (which also compiles in `fflate` and `html-to-image`, both MIT, pinned in the same file) and their retained notices. It does not extend to the open-slide application, CLI, Vite plugin or React tree, nor to any other repository. The copy is hash-guarded by `manifest.json`, refreshed only through the protocol in that directory's `UPSTREAM.md`, and tracked as a copied-source row in the `upstream-sync` table. Every other new capability is still delegated.

| Area | Upstream | Removed in |
|---|---|---|
| Frontend and design (`frontend` plugin: 3 agents, 5 skills, 1 command) | `pbakaus/impeccable`, `nextlevelbuilder/ui-ux-pro-max-skill`, `paulirish/dotfiles` | marketplace 7.0.0 |
| Brainstorming, planning, execution (`ai-tooling` skills `brainstorming`, `writing-plans`, `executing-plans`) | `obra/superpowers` | marketplace 8.0.0, ai-tooling 3.0.0 |
| Multi-agent generic core (`agent-teams` plugin: 6 commands, 4 agents, 6 skills) | `wshobson/agents` | marketplace 9.0.0 |
| Browser automation (`playwright-skill` plugin: 1 skill) | `lackeyjb/playwright-skill` | marketplace 11.0.0 |
| Binary reverse engineering (`reverse-engineering` plugin: 3 agents, 4 skills) | `morluto/rea` (REA; originally `wshobson/agents`) | marketplace 12.0.0 |
| Git worktree parallel development (`git-worktrees` plugin: 1 agent, 1 skill, 1 command) | `obra/superpowers` (`using-git-worktrees` skill) | marketplace 13.0.0 |
| Prompt-improver hook (`prompt-improver` plugin: 1 skill, 4 hook handlers) | `severity1/claude-code-prompt-improver` | marketplace 17.0.0 |
| Language-agnostic TDD knowledge base (`testing` skill `tdd`) | `mattpocock/skills` | marketplace 18.0.0 |
| Browser E2E patterns (`testing` skill `e2e-testing-patterns`) | `wshobson/agents` | marketplace 18.0.0 |
| Cleanup command trio (`codebase-cleanup` plugin: 3 commands) | `wshobson/agents` | marketplace 19.0.0 |

Application and binary reverse engineering is delegated to [REA](https://github.com/morluto/rea),
with its upstream `reverse-engineer-anything` skill and `rea-agents` CLI/MCP runtime.
Follow its [installation contract](https://github.com/morluto/rea/blob/main/docs/installation.md)
for the active host and required analysis engines. A skill-only installation does
not provision MCP tools or engines. Verify the actual session tools and target
support before execution; configuration support alone is not a live host probe.
REA owns shipped-artifact and requested runtime investigations; codebase-map owns
source-repository mapping. This delegation does not assert equivalent coverage of
the retired `memory-forensics` or `anti-reversing-techniques` skills. Preserve the
original retirement history without restoring a local copy or a sync-table row.

No plugin of this marketplace depends on superpowers, by decision of 2026-10-26. `ai-tooling` declared `superpowers@claude-plugins-official` as a hard dependency from marketplace 8.2.0 until that date, although no skill, role or workflow of that plugin loaded a superpowers component. Do not declare the dependency again, do not point a body at a superpowers skill, and do not re-import those skills. The `obra/superpowers` rows of the table above record where retired content went, not a delegation that is still declared. Cross-marketplace dependencies MUST use the qualified `name@marketplace` form, because a bare name resolves against this marketplace and fails the whole plugin load, which is what silently broke `ai-tooling` until marketplace 12.0.2.

From 2026-07-30 until the universal cutover, `exports/vscode/` vendored 14 superpowers skills and the 6 agents that served them, because there was no Copilot install path for superpowers. The extension is gone, so the copy is gone with it.

The universal cutover also retired the whole hand-mirroring apparatus it depended on: the per-bundle catalog, the extension manifest generator, the export structural checker, the mirror workflow and the release workflow. Do not rebuild any of them. A host that needs a different shape gets an adapter; a host that needs different meaning gets a fingerprinted override; nothing gets a second hand-maintained copy of a plugin.

**`marketplace-ops` and `ai-tooling/agent-sdk-builder` keep their host-as-subject vocabulary.** Their subject matter *is* the agent tooling, so their tool names and trigger labels are content rather than accidental host coupling. Never de-brand or tool-rename them.

Team scheduling is adapter-owned in senior-review, codebase-map and
project-knowledge. These project pipelines do not depend on agent-teams for host
coordination. Generic team methods remain delegated upstream when a plugin actually
uses them. The host-vocabulary linter rejects tool primitives in neutral bodies.

## Dependency policy: methods and roles are mandatory

Every static runtime method/role dependency on a local plugin is declared in [dependencies].required.
Never add a local optional dependency, a not-installed skip, or a fallback reviewer.
A missing required component is a broken installation, reported as failure rather
than silently reduced coverage. Cross-marketplace dependencies remain qualified
name@marketplace and mandatory for their consumers.

A prose pointer is not a runtime dependency. Suggestions, routing hints and related
reading do not justify an installation edge. Spawning a role, loading a method or
consuming its runtime artifact does. No hard local dependency goes unused.

senior-review is the single correctness-review owner. React, TypeScript and platform
providers are mandatory; code signals select their execution within the same review.
This deliberately increases the installation closure of senior-review and its
consumers. Targeted work goes through the entry commands (`review-changes`,
`write-tests`, `map-code`, `write-docs`, `tidy-repo`), never through a
specialist's own command: specialists have none, by decision of 2026-10-19. Do
not give a specialist a command back, do not expose a second review bundle to
turn that installation detail into a user decision, and do not make required
specialist edges optional.

| Owner | Direct required local dependencies |
|---|---|
| work-controller | none |
| worktree-manager | work-controller |
| model-routing | none |
| skill-catalog | none |
| codebase-map | none |
| repo-hygiene | none |
| abstraction-architect | codebase-map |
| testing | work-controller, report-rendering |
| senior-review | work-controller, repo-hygiene, codebase-map, abstraction-architect, testing, react-development, typescript-development, platform-engineering, python-development, dependency-audit, skill-catalog, report-rendering |
| research | work-controller |
| project-knowledge | research, work-controller, codebase-map, text-humanizer, senior-review, report-rendering |
| project-delivery | research, model-routing, work-controller, worktree-manager, project-knowledge, senior-review, testing, abstraction-architect, codebase-map, repo-hygiene, clean-code, typescript-development, python-development, skill-catalog, peer-review, moe, report-rendering |
| project-lifecycle | project-delivery, work-controller, project-knowledge, senior-review, testing, abstraction-architect, codebase-map, repo-hygiene, clean-code, react-development, typescript-development, platform-engineering, python-development, dependency-audit, skill-catalog, peer-review, report-rendering |
| clean-code | work-controller |
| office | work-controller |
| text-humanizer | none |
| python-development | testing, work-controller |
| dependency-audit | none |
| peer-review | none |
| moe | peer-review |
| business | text-humanizer, research |
| digital-marketing | text-humanizer, report-rendering |
| frontend-review | react-development, typescript-development, pwa-expert, platform-engineering |
| daodan | every other plugin of the marketplace, directly or through its providers: what a command loads or dispatches, and every knowledge-only plugin (docker, kotlin-development, dependency-audit, moe) |


Resolved knowledge is a distinct per-run input contract. The required skill-catalog
provider discovers actual available skills, selects knowledge metadata and pins
provider/version, scope, assigned workers and content fingerprints before dispatch.
Every selected knowledge input is mandatory for that run; missing, changed or
undelivered content is failed coverage. This exception permits reading knowledge
through the catalog binding, never invoking an undeclared method/workflow/role,
optionalizing a required provider or substituting a generic worker for one.
Literal method/role loads and produced runtime artifacts still require static
dependencies. A generated metadata declaration does not prove installation.
The dependency linter preserves those static edges; catalog contracts and helper
tests enforce resolved knowledge identity, read confinement and delivery accounting.

The entry plugin requires every knowledge-only plugin of this marketplace (only
knowledge skills, no role, no workflow), by decision of 2026-10-19: knowledge
the catalog cannot find is a recorded gap, not a stop, so a Kotlin task with
kotlin-development disabled ran on a generic worker without Kotlin knowledge.
Required, it is installed with `daodan` and the preflight's provider probe stops
on it when disabled. The dependency linter accepts such an edge when the consumer
also requires skill-catalog, the channel that reads it. Domain verticals with their
own roles or workflows remain independent plugins in the same marketplace; any
plugin that loads or dispatches another local plugin's component declares that
plugin in `[dependencies].required`.

The manifests are the control plane; this table records the architectural boundary.
The dependency linter fails unresolved, undeclared and unused runtime edges.

codebase-map never calls senior-review at runtime. Context assets belong to their
producer, not a consumer. frontend-review remains a separate upstream design and
local frontend orchestrator and never calls senior-review at runtime. Its design
craft is not vendored here.

Three cleanup owners remain disjoint: application-cleanup-method understands
application source, testing understands executable protection, repo-hygiene uses
filesystem and Git evidence. cleanup-auditor is detection-only. Do not recreate a
standalone cleanup command or let readability become semantic removal.

repo-hygiene is a leaf permanently. Its catalog has full and lite profiles; the lite
profile stays diff-scoped and omits historical workspace checks. Git auxiliary state
is detection-only at every permission level: dropped stashes, deleted branches and
removed worktrees are not recoverable by a tracked-content phase commit. Untracked
removals are quarantined, never deleted. C5 protects .daodan/, .codebase-map/, .codebase-xray/ and
sentinel-marked run roots by name/presence, without interpreting protocol state.

Lifecycle consolidation manages only its own run's concluded artifacts, with
verified summaries, retained evidence, unchanged fingerprints and explicit purge
permission. It does not widen repo-hygiene or system-utils into arbitrary project
deletion. system-utils organizes personal folders and inactive archives.

research owns `science-based-approach`, Science Mode and the scientific archive,
using work-controller for run discipline and the common project home. Consult
`docs/research/README.md` for relevant academic, algorithmic and technological
evidence through that method when Science Mode permits automatic work; explicit
research remains available when OFF. Cite immutable research revisions and claim
identities, preserve uncertainty and supersession, and keep one canonical owner
under each plugin's research dossier. Search related existing Markdown, including
unindexed research, before creating documents. Reuse the same current file for
a returning topic; update timestamps, visibly strike through superseded claims
and keep a descriptive changelog. Ambiguous overlapping owners require a choice,
not another duplicate. Instructions never store the current mode.
The existing team-research pipeline and web researchers remain web-only: they
plan subquestions, verify contradictions and cite sources actually read. A
one-fact question uses quick-searcher and writes no report. The task owner and
testing execute local product experiments; research retains protocols/results. The research depth bands and backend/key rules
are load-bearing in its design and evals: no key in prompts, auto backend needs no
key, preflight never spends a search credit.

Browser-facing app-analyzer, digital-marketing, grabber-development and pwa-expert
declare Playwright MCP, not the retired playwright-skill CLI. A missing required
browser is an install failure, never a browserless successful audit. On hosts
without that marketplace server, register the same Microsoft MCP server through
the host's native configuration. Preserve concrete install instructions in the
consumer. Grabber's separately scoped Patchright technique remains local.

testing delegates TDD to mattpocock-skills@mattpocock and browser E2E mechanics to
developer-essentials@claude-code-workflows. project-delivery owns its task cycle
and declares no upstream development method since 2026-10-18: its interview, plan
and execution are shaped by the map, the decision records and the protocol's wave
rules, which the delegated planning skills did not have, so running both would
mean two methods for one step. peer-review carries its own review-reception
doctrine in its respondent role. Neither change reimports a retired skill; the
workspace procedure loads worktree-manager's original method and external
Worktrunk CLI. New managed checkouts live under the main checkout's
`.daodan/worktrees/`; the persistent catalog adds task descriptions and tags to
Git's complete inventory. The CLI's supported release is pinned and upgrades
require compatibility checks. Review, authorization and completion remain with
their existing owners. Do not vendor upstream methods, revive the retired generic
worktree implementation or restore the
flawed codebase-cleanup trio. Dependency audit is a separately
maintained tool-first capability, not forced package remediation.
