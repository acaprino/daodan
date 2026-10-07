# Migrating from `claude-code-daodan` to `daodan`

Daodan is a development harness with five host front ends. Its active kernels are
compiled into Claude Code, GitHub Copilot, Codex, Pi and OpenCode packages, with
identical plugin identities and versions across hosts. The original universal
migration changed the repository name and removed the VS Code extension. Pi
arrived in marketplace 28.0.0, OpenCode in 29.0.0, and the coherent lifecycle in
30.0.0.

This guide covers migration from the old repository and distribution. For the
30.0.0 ownership and command changes, follow
[Migrating to the coherent development harness](migration-to-coherent-harness.md).
For active installation, command mappings, required dependencies and environment
limits, see [Hosts, exports and runtime requirements](hosts.md).

## What replaced what

| Before | After |
|---|---|
| `acaprino/claude-code-daodan` | `acaprino/daodan` |
| Claude packages under `plugins/<name>` | compiled packages under `exports/claude/plugins/<name>` |
| A VS Code extension built from `exports/vscode` | a native Copilot marketplace at `.github/plugin/marketplace.json` |
| No Codex distribution | a native Codex marketplace at `.agents/plugins/marketplace.json` |
| No Pi distribution | a package installed from git, catalogued by the root `package.json` |
| No OpenCode distribution | a V2 plugin package at `exports/opencode/`, installed with `opencode plugin add` |

The original universal migration preserved plugin names and Claude component
names. Marketplace 29.0.0 later renamed five components, listed below. Marketplace
30.0.0 retires `project-setup`, `codebase-mapper` and `docs` in favor of
`project-knowledge`, and adds `project-lifecycle`, `project-protocol` and
`review-plus`. Install the new owners and update stored invocations using the
[lifecycle migration table](migration-to-coherent-harness.md); the retired IDs
have no compatibility aliases.

## One-time migration

### Claude Code

```bash
claude plugin marketplace remove claude-code-daodan
claude plugin marketplace add acaprino/daodan
claude plugin install <plugin>@daodan
```

Start a fresh session afterwards and remove stale installations or loose copied
skills that would expose the same content twice. Registration of a new marketplace
does not remove an old independently installed copy.

### GitHub Copilot

Uninstall the old extension first. It is no longer built, and leaving it installed keeps a second copy
of every skill in `~/.copilot/skills/`:

```bash
code --uninstall-extension acaprino.claude-code-daodan
```

Then register the repository as a marketplace and install what you want:

```bash
copilot plugin marketplace add acaprino/daodan
copilot plugin install <plugin>@daodan
```

### Codex

```bash
codex plugin marketplace add acaprino/daodan
codex plugin install <plugin>@daodan
```

### Pi

Pi has no marketplace or per-plugin installation. Install the repository at a
released tag:

```bash
pi install git:github.com/acaprino/daodan@v<metadata.version>
```

Select prompts and skills through package settings, retaining each chosen
plugin's mandatory local providers. Isolated workflows need `pi-subagents`;
MCP use needs `pi-mcp-adapter` and server registration. Qualified external plugin
dependencies are not automatically installed by the package.

### OpenCode V2

OpenCode also installs one package, with its generated loader:

```bash
opencode plugin add 'github:acaprino/daodan#v<metadata.version>::path:exports/opencode'
```

Selection uses the loader's `options.plugins` and `options.exclude`. A selected
plugin brings its transitive local dependency closure; an exclusion cannot remove
a required provider. External marketplace dependencies still need separate
provisioning. The package targets V2 and serves its CLI and Desktop service; no V1
adapter or separate Desktop bundle is shipped.

### Required providers after an upgrade

Generated marketplace catalogs declare required dependencies and their foreign
marketplace trust list. Every local provider is mandatory, even when a particular
run selects fewer dimensions. Before running a migrated entry, provide the
complete dependency closure and any qualified external skills. Package rendering
does not establish their availability in the installed host. The
[host guide](hosts.md#required-dependency-behavior) explains selection differences
between the three marketplace hosts, Pi and OpenCode.

## Renamed in marketplace 29.0.0

No name may now be shared by two kinds of component inside one plugin, because OpenCode lists skills
and agents in one menu. Five components were renamed on every host; the commands kept their names.

| Plugin | Before | After |
|---|---|---|
| abstraction-architect | agent `abstraction-architect` | agent `abstraction-architect-agent` |
| browser-extensions | agent `firefox-extension-dev` | agent `firefox-extension-dev-agent` |
| digital-marketing | skill `brand-naming` | skill `brand-naming-method` |
| digital-marketing | skill `reply-to-customer-review` | skill `review-reply-method` |
| python-development | skill `python-refactor` | skill `python-refactor-method` |

Anything that spawns or loads one of these by its old name needs the new one. `/digital-marketing:brand-naming`,
`/digital-marketing:reply-to-customer-review` and `/python-development:python-refactor` are unchanged.

## The VS Code extension is not coming back

The `.vsix` was a distribution workaround from before Copilot read plugin marketplaces. It shipped one
bundle per plugin plus a JavaScript lifecycle that copied skill directories into `~/.copilot/skills/`,
and it had no auto-update path: every upgrade meant downloading an asset and running
`code --install-extension`. The native Copilot marketplace replaces all of it.

Historical GitHub Release assets are left untouched, and they are unsupported. They install content
from before the universal migration, they will never be rebuilt, and nothing checks them.

## Rollback

Roll back with a Git revert and a **new** patch marketplace version. Published versions are never
reused: a consumer that already installed `26.0.0` must be able to tell a rollback from the original
by its version alone.

```bash
git revert <cutover-sha>
# bump metadata.version in .claude-plugin/marketplace.json to the next patch
python scripts/daodan_build.py
python scripts/daodan_build.py --check
```

The repository name is not part of rollback. GitHub keeps redirecting the old name, renaming back
would break the redirect in both directions, and the marketplace identity (`daodan`) is what consumers
actually resolve.

## Curated host directories

A future submission to any curated directory references an immutable release tag or SHA. Each published
marketplace version now has one: `publish-marketplaces.yml` tags it `v<metadata.version>` on the commit it
published from, with no asset attached. That is independent of publication from this repository:
registering `acaprino/daodan` as a marketplace installs from `master`, and a directory listing installs
from whatever revision it pinned.
