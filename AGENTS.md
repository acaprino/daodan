# Daodan

The Daodan is the symbiote that augments its host. This repository is the Daodan of coding agents: a development harness that coordinates project intent, code, meaningful tests, durable knowledge and experimental artifacts. Domain specialists remain independent tools alongside the coherent project lifecycle. It ships to five hosts from one source. Remote: `acaprino/daodan` on GitHub.

## Development harness

project-lifecycle owns assess, repair, change, verify and consolidate. It prepares
inputs and composes canonical specialist methods rather than duplicating detection
prompts. project-protocol is the shared leaf for run records, snapshots, delivery
accounting, candidate gates and recovery. project-knowledge owns instructions,
guides, documentation and README. senior-review owns universal correctness and
application subtraction; review-plus adds mandatory React, TypeScript and platform
dispatch through the same senior methods. testing owns universal test governance;
Python contributes pytest-patterns, without a second test writer.

Run state belongs in .daodan/runs/<id>/ with an identified project/worktree, scope,
snapshot, authorization, plan, deliveries and checks. Dedicated alternative roots
remain inside the project and carry a .daodan-root sentinel. Tri-Tech Code is an
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

## Project structure

`plugins/<name>/` is a plugin's **content kernel**, and it is the only hand-authored plugin source alongside `adapters/`. Each kernel holds `plugin.toml` (the neutral control plane), `roles/` (agent bodies), `workflows/` (entry-point bodies plus one TOML sidecar each), `skills/`, `contracts/` and `policies/`. Those are also the only directories the compiler ships: a `references/`, `scripts/` or `mcp/` directory at the kernel root reaches no host package, so anything a body reads at runtime lives under `skills/<name>/`, and `scripts/lint_bundled_paths.py` fails a `${CLAUDE_PLUGIN_ROOT}` reference that the generated package does not contain. A kernel that ships an MCP server declares it under `[[mcp.servers]]` in `plugin.toml` (name, command, args, the server file under a skill) and requires the `mcp.servers` capability; the Claude adapter renders it as the package's `.mcp.json` and the catalog entry's `mcpServers` pointer, the OpenCode loader registers it from the package manifest, and Codex, Copilot and Pi, where no probe has shown a host starting a plugin-declared server, ship the file and open every workflow with a note giving the exact command to register. `peer-review` is the one plugin that declares one. Markdown is always the behaviour; TOML is always declarative metadata and never carries a prompt.

`adapters/<host>/` is what one host can do: `capabilities.toml` binds every neutral capability to a host mechanism, `coordination.toml` orders the coordination strategies that host supports, `layout.toml` says where each component lands in its packages and what the two Claude placeholders a kernel may write (`${CLAUDE_PLUGIN_ROOT}`, `$ARGUMENTS`) become on that host, `templates/` holds the harness wrappers, `policies/` holds this host's implementation of a neutral policy, and `overrides/` holds fingerprinted semantic divergences.

**Everything under `exports/` and every root marketplace manifest is generated.** `scripts/daodan_build.py` compiles kernels plus adapters into `exports/claude/`, `exports/copilot/`, `exports/codex/`, `exports/pi/` and `exports/opencode/`, and into `.claude-plugin/marketplace.json`, `.github/plugin/marketplace.json`, `.agents/plugins/marketplace.json`, the root `package.json` and `exports/opencode/package.json`. The last two are the odd members and neither is a Node project. Pi has no marketplace, it installs a package and reads the manifest at that package's root, so the repository root is where its catalog has to live. OpenCode V2 has none either: a package reaches it only as a plugin, so its catalog is that plugin's own manifest, whose `daodan` key lists every skill, agent, command and MCP server, and the package carries `index.js`, a fixed loader copied verbatim from `adapters/opencode/templates/` that registers them from that key. It is the one runtime JavaScript this repository ships, it imports nothing outside Node's standard library, and its tests run under `node --test` from the Python suite. Never hand-edit any of them; edit the kernel and rebuild.

`AGENTS.md` and the four repository workflow skills under `.agents/skills/` are native Codex adaptations of this file and `.agents/skills/`. Generate them with `python scripts/sync_codex_instructions.py`; `--check` is the parity gate. Edit the Claude-side canonical copies, then run the synchronizer. The transformation is deliberately limited to instruction paths, cache paths, install commands and the host-relative downstream description.

A kernel can export canonical contract files through `[contracts].exports`. Workflow `contract.shared_schemas` names a required provider and its exported `contracts/` path; schemas stay in one source location and are rendered by the compiler. Cross-plugin phase roles use `plugin/role` and are validated against the kernel registry. A composed method's additional workers are declared in `[dispatch].roles` rather than fabricated scheduling phases. `isolated` declares context requirements; `inline_workers` explicitly permits task-specific work through project-protocol's isolated-worker. Dispatch references require declared providers and actual roles. Inline adapters receive generated unregistered dispatch bodies from the canonical owner; named-agent adapters use owner-qualified IDs. `invoke` is rejected until an executor is implemented and proved.

The compiler is `scripts/daodan/`: `model.py` and `load.py` (strict TOML loading), `validate.py` and `trust.py` (semantic and secret validation), `adapter.py` (capability parity and strategy selection), `overrides.py` (the fingerprint gate), `render.py`, `templates.py`, `provenance.py`, `catalogs.py` and `report.py`. Standard library only, no third-party dependency anywhere in the toolchain.

`codebase-xray` was named `deep-dive-analysis` until marketplace 14.0.0, and its analysis artifact directory kept the old name, `.deep-dive/`, until marketplace 27.0.0. It is now `.codebase-xray/`, matching the plugin. That directory is the stable downstream contract, declared as the plugin's `write-confinement` policy: every consumer reads it by that path, so a rename is a marketplace-wide change and never a local one. There is no fallback to the old path, by decision: a reader that silently accepted both would leave two contracts alive and nothing would ever name which one it read.

The X-ray is static analysis and stays so: runtime evidence counts only when the user supplies it. Marketplace 28.3.0 drew the consequence after a Phazly incident of 2026-09-14: a global dark-theme rule in a `.css` file overrode a consent screen's positioning and locked users out on mobile, and the X-ray run that had the component in its inventory could not have cited the rule, because `snapshot.py` inventoried only parsed source and configuration and dropped every stylesheet. Presentation files now enter the manifest, paths that gate entry into the product are mandatory critical paths traced with their effective style cascade, `Usability-blocking` is a risk category, and the final report states three coverage figures: files in inventory, files read in depth, files exercised at runtime, the last always none. A file count is never coverage. Marketplace 28.4.0 made CSS, SCSS and LESS a parsed language, one symbol per applied rule, and added `cascade_scan.py`, which lists every rule whose selector reaches the document root or its untargeted children and sets a property that decides layout, with the rules it can override and what decides it. Its output is leads: whether two selectors match the same element is confirmed by reading, in Phase 5. Its Tailwind `@apply` expansion is load-bearing: on the incident's own stylesheets 90% of the applied rules used `@apply`, the consent modal's `fixed` included, and without it the scan found the culprit and missed the victim. Exercising those paths in a browser belongs to the project's own tests or to `frontend-review`; do not add a browser step to the X-ray on a later pass.

## Conventions

- Agent names: kebab-case matching the filename (e.g. `quick-searcher.md`)
- No name is shared across component kinds inside a plugin. `validate_component_kinds` fails the build when a skill, role or workflow repeats a name: OpenCode lists skills and agents in one `@` menu, and a name meaning two things in one plugin is ambiguous to every body that cites it. A role beside a same-topic skill takes `-agent` (`abstraction-architect-agent`), a skill beside a same-topic workflow takes `-method` (`brand-naming-method`, after `codebase-xray`'s `xray-method`). Marketplace 29.0.0 renamed the five components that broke this rule.
- Plugin names: kebab-case directory names
- Default model: `inherit` (agents follow the session model instead of pinning one); exceptions noted per-agent (e.g. `quick-searcher` uses `sonnet`)
- Agent `color` must be one of: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`
- Agent body style: terse keyword lists, imperative tone, structured with markdown headers; simple agents ~50-200 lines, complex agents up to ~700 lines
- Long `description` frontmatter values use the YAML multiline `>` form
- Skills supplementary subdirs: `references/`, `scripts/`, `templates/`, `assets/`, `lib/` as needed
- No build step or runtime framework - plugins are markdown with optional helper scripts (Python, JS) in skills' `scripts/` subdirs
- Avoid the dash-aside construct anywhere (code, comments, commit messages, documentation). The rule targets the *rhetorical pattern* of bracketing a clause between dashes, in any form: `—` (em dash), `--` (double hyphen), or ` - ` (spaced hyphen). All three are banned when used to wrap a parenthetical aside (e.g., "lorem ipsum -- lorem ipsum -- lorem ipsum"). Substituting `--` for `—` is **not** the fix. Rewrite into separate sentences, parentheses, colons, or just delete the aside. Hyphenated compounds (`file-ownership`, `multi-agent`) are unrelated and fine.
- **AGENTS.md never records transient, runtime, or temporary state.** Never. This file states durable facts: structure, conventions, policies, workflows, and the reasoning behind them. It is not a status board. Nothing goes in here that is true only until the next run, the next commit, or the next session: in-progress task lists, "currently", "pending", "as of today" notes, open branches, scratch paths, session findings, backlog items, or anything that would need editing merely because time passed. If a fact has an expiry, it belongs in the commit message, an issue, a design doc under `docs/`, or session memory. A stale claim in this file is worse than no claim, because everything here is read as ground truth.

## Marketplace update workflow

When changes modify a plugin kernel, update the marketplace **before committing**:

1. **Bump the plugin version** - increment `version` in that plugin's `plugins/<name>/plugin.toml`
2. **Bump the marketplace version** - increment `metadata.version` in `.claude-plugin/marketplace.json`
3. **Rebuild** - `python scripts/daodan_build.py`, then `python scripts/daodan_build.py --check`
4. **Commit together** - stage the kernel files and everything the build regenerated under `exports/` and the root manifests, in one commit
5. **Push to remote** - `git push` to `master`

There is no hand-mirroring step any more, and no per-host obligation to remember: the compiler writes every host, and `--check` fails the build when a committed package no longer reproduces from its kernel.

## Adding a new plugin

1. Create `plugins/<name>/plugin.toml` declaring `schema = "daodan/v1"`, identity, `[capabilities]`, `[dependencies]` and `[components]`
2. Add the component bodies: `roles/<role>.md`, `workflows/<workflow>.md` with a `workflows/<workflow>.toml` sidecar, `skills/<skill>/SKILL.md`, and any `contracts/` or `policies/`
3. Declare capabilities from the closed registry in `scripts/daodan/validate.py`. A capability outside it fails the build rather than being guessed at by an adapter. Local dependencies go in `[dependencies].required`, always: see the dependency policy below
4. Build every host, bump `metadata.version`, and commit the kernel plus the generated output together

## Git workflow

- Single branch: `master`
- Commit style: imperative, descriptive (e.g. "Add high-value keywords to prompt-engineer agent")
- Primary workflow: direct push to master (PRs used occasionally)

## Build / CI

The build is `python scripts/daodan_build.py`. It loads every kernel, validates it, binds it to each adapter, renders every package into a temporary tree, and replaces the live output only after every validator passes. `--check` renders the same tree and reports drift instead of writing, and it is the gate CI runs. Exit codes: 0 clean, 1 drift or validation failure, 2 invocation error. Publication always builds every host; `--host` narrows the run and is accepted only under `--check`, because a marketplace where one host is a commit ahead of the others is the drift this compiler exists to prevent.

`.github/workflows/consistency.yml` runs on push to `master` and on PRs. Its checks, all stdlib-only Python from the repository root:

1. `python scripts/lint_dependency_graph.py` — the dependency-graph linter. Extracts runtime cross-plugin references (agent spawns, skill loads) from plugin bodies and enforces: every runtime reference is declared in `dependencies`; bare dependency names must exist in this marketplace (cross-marketplace deps use the qualified `name@marketplace` form); the forbidden edge `codebase-xray → senior-review` never reappears; **no plugin in this marketplace appears in another's `optionalDependencies`**; and **no plugin body makes something conditional on a hard local dependency being installed, or names a fallback for one**. Those two passes are the two halves of the dependency policy below, over declarations and over prose. A further pass enforces that **no hard local dependency goes unused**, which is the only check that notices a dependency silently reintroduced by a concurrent writer.
2. `python scripts/lint_bundled_paths.py` — the bundled-path linter. A body that says to read `plugins/<name>/skills/x/references/y.md` names a path that exists only in a checkout of this repo, so for an installed user that read silently fails. Self-references must use `${CLAUDE_PLUGIN_ROOT}/...` or a skill-relative `references/...` path inside that same skill, and no plugin may reach into another plugin's files by path. Its `GRANDFATHERED` map is empty: its first run found 40 such references across 26 files and they were fixed rather than baselined. Fix a reference, delete its entry; never add one to make a build pass. Its third pass, `shipped refs`, resolves every `${CLAUDE_PLUGIN_ROOT}/...` reference against the generated Claude package and fails the ones no package contains, because a well-formed path to a file the compiler never copies fails at runtime exactly as silently as a checkout path. Its motivating case was `ai-tooling`, whose reasoning-patterns reference sat at the kernel root, unshipped on every host, from the kernel neutralization until marketplace 27.1.0. Its `UNSHIPPED` baseline is empty too: its first run found 23 such references, `peer-review`'s protocol documents and MCP server and `research`'s two search scripts, all at kernel roots the compiler never copies, and marketplace 27.2.0 moved every one under its plugin's skill rather than baselining it. Move the file under a skill, fix the reference, never add an entry. Its fourth pass, `skill refs`, covers what the third cannot see: a role or workflow sits outside every skill, so a bare `references/<file>.md` in its body must name a file under a skill of its own plugin or of a local plugin it declares. Its motivating case was `app-analyzer`, whose role read `references/report-templates.md` from an `agents/` directory at the kernel root, unshipped on every host until marketplace 28.6.1.
3. `python scripts/lint_plugin_registration.py` — the registration linter. A component present in a package but missing from that plugin's catalog entry does not exist at runtime, so a spawn fails with "Agent type not found" and takes its phase down. It runs both directions over all three content kinds, against the **generated package** named by each catalog `source`. A neutral kernel is skipped as a package root on purpose: its bodies live under `roles/` and `workflows/` and the compiler decides their installed paths. A third pass covers Pi, whose catalog registers nothing by name and globs the tree instead: there the same invariant inverts into whether every generated component of a registered kind falls inside a declared glob, and whether every glob reaches anything at all. A fourth covers OpenCode, whose loader registers what the `daodan` key of `exports/opencode/package.json` names: every `file` there exists, and every rendered skill, agent and command is named by one.
4. `python scripts/lint_fact_anchors.py` — the fact-anchor linter. A knowledge plugin states the same load-bearing fact in several artifacts on purpose, because each is loaded on its own. The redundancy is correct; what it costs is that a correction must land in every copy at once, so the linter compares them and fails the build naming both files. Its motivating case: a Web API rate limit sat wrong in one file for months because every copy was internally plausible and no two were ever compared. Add an anchor the second time you correct a fact; never delete one to go green.
5. `python -m unittest discover -s tests` — the compiler's own suite plus the port and parity contract tests: the neutral model, validation, adapter parity, the override fingerprint gate, deterministic rendering and transactional replacement, catalogs, the CLI, both canary ports, universal catalog parity, the publication workflow contract, the cutover identity gate, what each host package must say (`test_daodan_host_rendering.py`, on the real `codebase-xray` and `senior-review` kernels) and the X-ray script suites (`test_xray_scripts.py`, `test_xray_snapshot.py`, `test_xray_stylesheet.py`), and the OpenCode loader's `node --test` suite through `test_opencode_loader.py`, which both workflows give a Node runtime so it runs rather than skips.
6. `python scripts/daodan_build.py --check --support` — the drift gate. Every committed package and catalog must reproduce byte-for-byte from the kernels and adapters in the same commit.
7. `python adapters/copilot/policies/xray-guard/test_xray_guard.py` — the Copilot write-confinement policy implementation, 36 cases.
8. `python scripts/check_version_bumps.py <base-rev> [<head-rev>]` — over the pushed or PR range, a change under `plugins/<name>/` or under `adapters/<host>/overrides/<name>/` must come with a bump of that plugin's version and of `metadata.version`. Generated packages under `exports/` never count: they are compiler output, and a rebuild is not a plugin change.
9. `python scripts/lint_host_vocabulary.py` rejects host-specific team primitives in neutral behavior. Kernels state delivery/ownership/barrier obligations and adapter wrappers supply their mechanisms. Neutralize a file and remove its grandfathered count, never increase one. Marketplace operations and SDK knowledge retain host vocabulary when tooling is their subject; instruction examples belong to the knowledge owner's skill.

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

`docs/plugins/` contains per-plugin documentation. `docs/references/` holds cross-cutting knowledge bases that inform changes across multiple plugins — notably [`agent-teams-best-practices.md`](docs/references/agent-teams-best-practices.md), the source of truth when restructuring any plugin that spawns multi-agent teams or pipeline reviewers (`senior-review`, `project-knowledge`, `research`, `codebase-xray`). `evals/` holds eval harnesses: development assets, never shipped, not registered in `marketplace.json`. `evals/senior-review/` measures review recall against ground-truth bugs (cases plus scoring protocol). `evals/ai-tooling/` is a different shape, because that plugin has no bugs to recall: its 15 cases assert **behavioral invariants** (the frontier is never auto-picked, a contract survives optimization, an installed SDK outranks a bundled reference, an every-call rule uses a `PreToolUse` hook) so that a later edit cannot quietly remove one. Assertions target the philosophy, never the wording, and a case that fails once keeps its case forever. `evals/research/` follows the `ai-tooling` shape for the deep-research pipeline (marketplace 25.0.0). `evals/codebase-xray/` does the same for the X-ray pipeline (marketplace 26.4.0): eleven behavioural-invariant cases (Phase 0 at every depth, run isolation, parsers over hand reading, forbidden files never quoted, claims cite evidence and carry a status, partition ownership, scope authorization and mapper scope in team mode, incremental runs carry unaffected claims forward and re-derive only what changed, declared coverage with stylesheets parsed and scanned), the first nine written after the 2026-09-03 review; `evals/codebase-xray/RESULTS.md` records which have run. The script half of that plugin is pinned mechanically instead: `tests/test_xray_scripts.py` runs the regex fallback on CI and the tree-sitter path wherever it is installed, `tests/test_xray_snapshot.py` pins the incremental snapshot, and `tests/test_xray_stylesheet.py` the stylesheet adapter and the cascade scan.

The senior-review entries are thin pointers to canonical review-method, review-preparation and review-consolidation skills. Agent prompts, fix-loop and native output references remain under review-quality-gates. application-cleanup-method is the named Step 7c method and carries severity acceptance, exclusive-workspace/clean-tree prerequisites and snapshot-bound gates. --fix edits and verifies without committing; --commit additionally authorizes commits and is required for bulk application subtraction.

## Research technique: when a direct fetch is blocked, drive a browser

Many vendor documentation sites (IBKR's `interactivebrokers.com/docs/` among them) return **HTTP 403 to WebFetch** while serving the same pages fine to a real browser. A 403 is a bot-detection result, not evidence that the page is gone or that the fact is unverifiable. Never downgrade a claim to "unverified" on a 403 alone.

The escalation path, in order:

1. `WebFetch`. If it returns 403 or empty content, do not retry it and do not conclude anything from the failure.
2. **Drive a real browser with the Playwright MCP tools** of the `playwright` plugin (`playwright@claude-plugins-official`, Microsoft's Playwright MCP server, a hard dependency of `app-analyzer`, `digital-marketing`, `grabber-development` and `pwa-expert`; install with `codex plugin install playwright@claude-plugins-official`). `browser_navigate` opens a visible browser, which also passes bot detection that headless does not; `browser_snapshot` reads the page and `browser_run_code_unsafe` runs any Playwright extraction code.
3. Check whether the site publishes an **LLM-friendly index**. IBKR's docs expose `/llms.txt` at the root and serve clean Markdown for any page by appending `.md` to its URL, which is faster and cleaner than scraping rendered HTML. Look for that before writing extraction logic.

This is how the five "unverifiable" IBKR facts in the 2026-08-09 `ibkr-trading` refresh were actually resolved, one of which (a plugin claim that error code 10167 exists) turned out to be false rather than merely unconfirmed.

On this machine there is also a standing local install: IB Gateway/TWS under `D:\Software\Jts` (ibgateway build directory `1045`) and IBC 3.23.0 under `D:\Software\IBC`. That is the production deployment's install: its `config.ini` and settings are live configuration, so the `ibkr` skill's verification work may reuse those *binaries* but must never launch or edit that configuration. Its `ibkr_gateway.py` provisions its own disposable paper install under `%LOCALAPPDATA%\ibkr-verify` instead, which is the preferred route for probes.

## The characteristic defect here is cross-file contradiction

Almost nothing in this repository is stated once. A plugin's behaviour is described by its own kernel files, compiled into five host packages, summarized in `docs/plugins/`, asserted by an eval, and ruled on here. That redundancy is deliberate and mostly correct, since each artifact is loaded on its own. What it costs is that **the failure mode is almost never a broken file; it is two files that no longer agree**, and every mechanical guard this repo has grew from one instance of it: the fact-anchor linter, the registration linter, the version-bump check, and the drift gate that replaced hand-mirroring outright.

The compiler removed one whole class of it. A host package can no longer disagree with its source, because it is not written by hand: `--check` fails the build the moment a committed package stops reproducing from its kernel. What it cannot check is prose that describes behaviour, which is why the fact-anchor linter still earns its place.

The `research` 6.0.0 release is the worked example, and the lesson is about how to review rather than what to write. It ran as ten tasks under subagent-driven development, each with a fresh reviewer against its own diff, and **all ten came back clean**. The final whole-branch review then found one Critical and three Important, and every one of them was a cross-file contradiction: an export frontmatter broken in a way its own task's review had no reason to parse, and three tracked files elsewhere in the repo still describing the contract that branch had just replaced. A per-task review verifies the diff it is given; only a whole-branch pass asks what the diff invalidated somewhere else. Budget for that pass, and point it at the files the change makes stale rather than only at the files the change touched.

## Repo workflows

Four maintenance workflows live in `.agents/skills/` so they load only when the task calls for them. Load the matching skill before starting; do not improvise these from memory.

| Skill | Load it when |
|---|---|
| `external-repo-intake` | Importing, vendoring, or cherry-picking from an external GitHub repo for the FIRST time. Covers classification, the license gate, convention adaptation, and the commit shape. |
| `upstream-sync` | Re-syncing a plugin already ported from an upstream repo, or answering "which plugins are upstream-synced". Holds the sync table, the merge strategy, and the per-plugin sync notes. |
| `custom-plugin-refresh` | Refreshing a hand-authored plugin that has no upstream. Holds the freshness risk classes, cadences, and the re-research protocol. |
| `downstream-exports` | Changing how a host package is shaped: an adapter layout, a harness template, a capability binding, a policy implementation, or a semantic override. Holds what each host expects, what the compiler generates for it, and the content that deliberately keeps host-as-subject vocabulary. Nothing under `exports/` is ever edited by hand. |

## Broker knowledge lives in one plugin

All broker and trading-platform knowledge lives in a single plugin, `trading-broker-integration`, with one skill per vendor (`ibkr`, `mt5`) alongside the vendor-neutral `broker-vocabulary` skill that supplies the shared terms every vendor skill is written in: the five archetypes, the single-broker/multi-broker-platform axis, the reference order-lifecycle model, and the evidence ladder.

That shape replaced one plugin per broker (`ibkr-trading`, `mt5-trading`, `trading-broker-connectivity`) in this consolidation. The reason is what research into a third broker, WH SelfInvest, established: the durable unit of knowledge is the platform, not the broker. WH SelfInvest's main account is contractually an Interactive Brokers account, its NanoTrader platform is a Fipertec product, and its futures run over CQG. A broker reselling three platforms does not produce one plugin, it touches three that already exist for other reasons. If the unit is not the broker, one plugin per broker was the wrong partition to begin with, and it is what made a per-plugin conformance contract look necessary: a contract exists to police a boundary, and the boundary here was drawn in the wrong place.

A two-level conformance contract (`base` and `verified`, each with its own declaration lines) and a linter enforcing it (`scripts/lint_broker_plugins.py`) existed for that old partition and were deliberately removed in this consolidation, along with `.agents/skills/broker-plugin-contract/`. This is recorded so nobody reintroduces them believing their absence was an oversight. A future broker or platform gets a new skill under `trading-broker-integration`, not a new plugin and not a revived contract.

## Deliberately not vendored

Ten areas were removed and delegated to their upstreams because maintaining the local copy cost more than it returned (most were vendored copies handed back; `git-worktrees` was locally authored content retired in favor of equivalent upstream coverage; `prompt-improver` was a local JS re-port handed back to its upstream in 17.0.0; `codebase-cleanup` was retired outright because its verified content defects made delegation undesirable). Do NOT re-import or re-create them, and do not add rows for them to the sync table in the `upstream-sync` skill on a future "upstream updates" pass. The delegation table below records their owners and retirement history.

Standing policy since 2026-08-04: this repository no longer maintains vendored copies of external repositories. New capability never gets vendored in; it gets delegated with a declared dependency. The remaining sync-table rows in the `upstream-sync` skill are scheduled for a dedicated de-vendoring pass (delegate, adopt as local, or delete, decided per plugin) that will also retire that skill.

| Area | Upstream | Removed in |
|---|---|---|
| Frontend and design (`frontend` plugin: 3 agents, 5 skills, 1 command) | `pbakaus/impeccable`, `nextlevelbuilder/ui-ux-pro-max-skill`, `paulirish/dotfiles` | marketplace 7.0.0 |
| Brainstorming, planning, execution (`ai-tooling` skills `brainstorming`, `writing-plans`, `executing-plans`) | `obra/superpowers` | marketplace 8.0.0, ai-tooling 3.0.0 |
| Multi-agent generic core (`agent-teams` plugin: 6 commands, 4 agents, 6 skills) | `wshobson/agents` | marketplace 9.0.0 |
| Browser automation (`playwright-skill` plugin: 1 skill) | `lackeyjb/playwright-skill` | marketplace 11.0.0 |
| Binary reverse engineering (`reverse-engineering` plugin: 3 agents, 4 skills) | `wshobson/agents` | marketplace 12.0.0 |
| Git worktree parallel development (`git-worktrees` plugin: 1 agent, 1 skill, 1 command) | `obra/superpowers` (`using-git-worktrees` skill) | marketplace 13.0.0 |
| Prompt-improver hook (`prompt-improver` plugin: 1 skill, 4 hook handlers) | `severity1/claude-code-prompt-improver` | marketplace 17.0.0 |
| Language-agnostic TDD knowledge base (`testing` skill `tdd`) | `mattpocock/skills` | marketplace 18.0.0 |
| Browser E2E patterns (`testing` skill `e2e-testing-patterns`) | `wshobson/agents` | marketplace 18.0.0 |
| Cleanup command trio (`codebase-cleanup` plugin: 3 commands) | `wshobson/agents` | marketplace 19.0.0 |

As of marketplace 8.2.0, superpowers is a declared hard dependency of `ai-tooling` (`dependencies: ["superpowers@claude-plugins-official"]` in `marketplace.json`; cross-marketplace dependencies MUST use the qualified `name@marketplace` form, because a bare name resolves against this marketplace and fails the whole plugin load, which is what silently broke `ai-tooling` until marketplace 12.0.2). Any place that points at the superpowers planning skills says so unconditionally: load the skills, and if they are unavailable stop and tell the user to install superpowers (`codex plugin install superpowers@claude-plugins-official`). This supersedes the earlier rule that kept superpowers references conditional; do not reintroduce conditional phrasing.

The scoped exception that used to sit here is closed. From 2026-07-30 until the universal cutover, `exports/vscode/` vendored 14 superpowers skills and the 6 agents that served them, because there was no Copilot install path for superpowers and the extension shipped them or nothing did. The extension is gone, so the copy is gone with it, and the delegation is now unconditional again on every host: `ai-tooling` hard-depends on `superpowers@claude-plugins-official`, and nothing anywhere may re-import those skills. Superpowers publishes its own marketplace (`obra/superpowers-marketplace`), which is the install path to point users at.

The universal cutover also retired the whole hand-mirroring apparatus it depended on: the per-bundle catalog, the extension manifest generator, the export structural checker, the mirror workflow and the release workflow. Do not rebuild any of them. A host that needs a different shape gets an adapter; a host that needs different meaning gets a fingerprinted override; nothing gets a second hand-maintained copy of a plugin.

**`marketplace-ops` and `ai-tooling/agent-sdk-builder` keep their host-as-subject vocabulary.** Their subject matter *is* the agent tooling, so their tool names and trigger labels are content rather than accidental host coupling. Never de-brand or tool-rename them.

Team scheduling is adapter-owned in senior-review, codebase-xray and
project-knowledge. These project pipelines do not depend on agent-teams for host
coordination. Generic team methods remain delegated upstream when a plugin actually
uses them. The host-vocabulary linter rejects tool primitives in neutral bodies.

## Dependency policy: every internal dependency is mandatory

Every runtime dependency on a local plugin is declared in [dependencies].required.
Never add a local optional dependency, a not-installed skip, or a fallback reviewer.
A missing required component is a broken installation, reported as failure rather
than silently reduced coverage. Cross-marketplace dependencies remain qualified
name@marketplace and mandatory for their consumers.

A prose pointer is not a runtime dependency. Suggestions, routing hints and related
reading do not justify an installation edge. Spawning a role, loading a method or
consuming its runtime artifact does. No hard local dependency goes unused.

When installation cost is unwanted, separate the capability and its orchestration.
review-plus is the explicit specialist consumer; senior-review retains universal
correctness. Do not turn those specialist dependencies into optional edges or
reintroduce them into knowledge through an unrelated pointer.

| Owner | Direct required local dependencies |
|---|---|
| project-protocol | none |
| codebase-xray | none |
| repo-hygiene | none |
| abstraction-architect | codebase-xray |
| testing | project-protocol |
| senior-review | project-protocol, repo-hygiene, codebase-xray, abstraction-architect, testing |
| review-plus | senior-review, react-development, typescript-development, platform-engineering |
| project-knowledge | project-protocol, codebase-xray, senior-review, text-humanizer |
| project-lifecycle | project-protocol, project-knowledge, senior-review, testing, abstraction-architect, codebase-xray, repo-hygiene, clean-code |
| clean-code | project-protocol |
| python-development | testing, project-protocol |

The manifests are the control plane; this table records the architectural boundary.
The dependency linter fails unresolved, undeclared and unused runtime edges.

codebase-xray never calls senior-review at runtime. Context assets belong to their
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
removals are quarantined, never deleted. C5 protects .daodan/, .codebase-xray/ and
sentinel-marked run roots by name/presence, without interpreting protocol state.

Lifecycle consolidation manages only its own run's concluded artifacts, with
verified summaries, retained evidence, unchanged fingerprints and explicit purge
permission. It does not widen repo-hygiene or system-utils into arbitrary project
deletion. system-utils organizes personal folders and inactive archives.

research remains web-only and dependency-free. Its deep pipeline plans subquestions,
dispatches native isolated researchers, verifies contradictions and cites sources
actually read. A one-fact question uses quick-searcher and writes no report. Local
experiments belong to consolidate. The research depth bands and backend/key rules
are load-bearing in its design and evals: no key in prompts, auto backend needs no
key, preflight never spends a search credit.

Browser-facing app-analyzer, digital-marketing, grabber-development and pwa-expert
declare Playwright MCP, not the retired playwright-skill CLI. A missing required
browser is an install failure, never a browserless successful audit. On hosts
without that marketplace server, register the same Microsoft MCP server through
the host's native configuration. Preserve concrete install instructions in the
consumer. Grabber's separately scoped Patchright technique remains local.

testing delegates TDD to mattpocock-skills@mattpocock and browser E2E mechanics to
developer-essentials@claude-code-workflows. project-lifecycle, ai-tooling and
peer-review delegate development methods to superpowers@claude-plugins-official.
Do not vendor those upstream methods, revive the retired generic worktree plugin
or restore the flawed codebase-cleanup trio. Dependency audit is a separately
maintained tool-first capability, not forced package remediation.
