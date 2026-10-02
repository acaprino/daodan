# Migrating from `claude-code-daodan` to `daodan`

The repository is now one marketplace with five native front ends. The same 40 plugins are compiled
from one set of content kernels into Claude Code, GitHub Copilot, Codex, Pi and OpenCode packages, at one
identical version everywhere. Two things changed for existing users: the repository name, and the
removal of the VS Code extension. Pi arrived later, in marketplace 28.0.0, and OpenCode in 29.0.0;
neither host changed anything for anyone already installed. Marketplace 29.0.0 did rename five
components on every host, listed below.

## What replaced what

| Before | After |
|---|---|
| `acaprino/claude-code-daodan` | `acaprino/daodan` |
| Claude packages under `plugins/<name>` | compiled packages under `exports/claude/plugins/<name>` |
| A VS Code extension built from `exports/vscode` | a native Copilot marketplace at `.github/plugin/marketplace.json` |
| No Codex distribution | a native Codex marketplace at `.agents/plugins/marketplace.json` |
| No Pi distribution | a package installed from git, catalogued by the root `package.json` |
| No OpenCode distribution | a V2 plugin package at `exports/opencode/`, installed with `opencode plugin add` |

Plugin names did not change. Command, agent and skill names did not change on Claude Code.

## One-time migration

### Claude Code

```bash
claude plugin marketplace remove claude-code-daodan
claude plugin marketplace add acaprino/daodan
claude plugin install <plugin>@daodan
```

Start a fresh session afterwards and check that no plugin name appears twice: a stale marketplace left
registered is the only way to end up with two copies of the same plugin.

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
