# repo-hygiene

Workspace tidying decided by the filesystem and git alone. Committed build output,
`.gitignore` gaps and stale rules, filesystem garbage, scratch directories, orphan
doc-assets, and stale git state.

**Install:** ships with the marketplace. No dependencies: it is a leaf by rule.

| | |
|---|---|
| **Entry** | `/daodan:tidy-repo`, which follows the skill's `references/tidy.md` |
| **Agent** | `repo-hygiene:workspace-auditor` |
| **Skill** | `repo-hygiene:repo-hygiene` |
| **Dependencies** | none |

Command examples and named tools in this guide use Claude notation. For other
hosts, use the entry points and bindings in the source-derived reference below
and [host setup](../hosts.md).

## What decides the boundary

One question separates this plugin from `senior-review`: **what kind of evidence
answers the check?**

`git ls-files`, `git check-ignore`, `git stash list`, a directory listing. No source
file is read and no symbol is understood. That is this plugin.

What a symbol is for, whether a reference reaches it, whether removing it changes
behavior. Dynamic imports, decorators, framework conventions, module augmentation. That
is `senior-review:cleanup-auditor`, and this plugin never reaches for it.

The split is not about risk or size. A tracked `dist/` directory can be larger and more
consequential than a dead export, and it still belongs here, because deciding it needs
`git ls-files` and not a parser.

## The seven checks

| | Check | Full | Lite |
|---|---|---|---|
| C1 | Filesystem garbage: `nul`, `.DS_Store`, `Thumbs.db`, shell-redirection artifacts | yes | yes |
| C2 | Generated artifacts tracked in git, checked against publication conventions first | yes | yes |
| C3 | `.gitignore` completeness, per detected ecosystem | yes | partial |
| C4 | `.gitignore` archaeology: stale rules, overly-broad rules, with `git check-ignore -v` provenance | yes | no |
| C5 | Scratch and pipeline-output directories | yes | no |
| C6 | Orphan doc-assets, widened past literal Markdown links | yes | no |
| C7 | Git auxiliary state: stale stashes, orphan worktrees, gone-upstream and merged branches | yes | no |

C5 protects `.daodan/` and `.codebase-map/` by name, plus any directory containing
a `.daodan-root` sentinel and its ancestors. It never proposes removing these
roots and does not interpret protocol states. Classifying run evidence, resume
data and concluded output belongs to [project-lifecycle](project-lifecycle.md)'s retention
method (`references/retention.md` of `project-delivery:delivery-method`).

**Two profiles, one set of definitions.** The full profile runs over the working tree.
The lite profile runs over the files a diff adds, and is what the inline hygiene pass
of the code-review and pr-review variants of `senior-review:review-method` loads. C4 through C7 are
absent from the lite profile on purpose: they are repository-historical, so a diff under
review cannot have caused them, and reporting them there attributes old debt to an
innocent change.

## Three things it refuses to do

**It will not untrack a build output that is published on purpose.** A tracked `dist/`
reads exactly like an accident, and sometimes GitHub Pages serves from it or a generated
SDK ships to package consumers. C2 checks `.nojekyll`, `CNAME`, Pages workflows, and the
`files` allowlist in `package.json` before proposing anything. When a convention claims
the path, the finding is KEEP with the convention quoted, which also stops the next
audit from re-raising it.

**It will not delete a doc-asset on the strength of a basename Grep.** An image reaches
the rendered site through a `mkdocs.yml` value, a `url()` in a stylesheet, a generated
navigation entry, or a path composed in a template, none of which a Markdown search
sees. C6 widens to configs, stylesheets and templates, and removal still requires
item-level approval showing both searches that found nothing.

**It will never drop a stash, remove a worktree, or delete a branch.** C7 is
detection-only, permanently, and the reason is structural rather than cautious. Every
other check mutates tracked content, so a commit records the change and reverting
restores it. A dropped stash produces no diff for any commit to hold, a removed worktree
takes its uncommitted files with it, and a deleted branch survives only in a reflog that
expires. The rollback mechanism the command promises does not reach that far, so the
command does not go there. The findings carry the commands; the user runs them.

## `/daodan:tidy-repo`

The plugin has no command of its own. `/daodan:tidy-repo` loads `repo-hygiene:repo-hygiene`
and follows its `references/tidy.md`, beside the other owners' detections, in one
preview. The target is the repository root or a path; text naming phases restricts
them.

Detects and reports by default. Applying is one question asked after the report:
applied without commits, the working tree is left modified with no commits; applied
with commits, one commit per phase is added. The two answers mean exactly what
applying and committing mean in `senior-review:review-method`.

Four phases, run in order: `garbage`, `gitignore`, `scratch`, `git-state`.

**There is no build-and-test gate between phases**, because nothing applied here is
code. For `gitignore`, the protection that matters is the per-item confirmation on
`git rm --cached`, not a test suite that passes because the untracked files are still
sitting on disk.

**Untracked removals go to quarantine**, at `.repo-hygiene/quarantine/<timestamp>/`,
preserving relative paths. Git holds no copy of an untracked file, so deletion would be
the one irreversible operation in the command, and it is not taken. This is what makes
applying without commits safe: everything it does is undoable by hand.

**Applying with commits requires a clean tree** because its per-phase commits are its
revert mechanism and an unrelated modified file would be swept into one. Applying
without commits has no such requirement: it stages nothing and keeps untracked removals in quarantine. The
accepted item list still bounds its changes. Staging is always by explicit path,
never `git add -A`.

## Inside a team review

The branch review of `/daodan:review-branch` spawns `repo-hygiene:workspace-auditor` as an always-on
dimension alongside `senior-review:cleanup-auditor`. The two perimeters are disjoint by
construction, so consolidation has nothing to deduplicate between them. **A finding
appearing in both reports is a boundary violation to investigate, not an `echo` to
fold.**

## Related

- [senior-review](senior-review.md): everything hygiene-adjacent that needs source
  comprehension, plus Step 7c, which removes application code in five gated phases.
- [testing](testing.md): `testing:test-remediation-method` in mode `consolidate`, run by
  `/daodan:tidy-repo`, owns bulk removal of test files.
- [dependency-audit](dependency-audit.md): CVEs, licenses and version drift from each
  ecosystem's own tooling, which is a different question from whether a dependency is
  used.

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `2.2.1`. **Source:** [plugin.toml](<../../plugins/repo-hygiene/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | None |
| Direct external | None |
| Local closure (1) | [repo-hygiene](<repo-hygiene.md>) |
| External closure (0) | None |

External bundles are separate upstream installations, not copied local skills.
See [host setup](<../hosts.md>) for selection and availability requirements.

**Required capabilities:** `repository.read`, `shell.execute`, `repository.write`, `contexts.isolate`, `roles.dispatch`.
**Optional capabilities:** None.
Optional capabilities are host mechanisms, not optional local plugin dependencies.

### Registered components

Names below are kernel IDs. Host entry points and paths follow the adapter
mapping in [the host reference](<../hosts.md>).
The source links carry the complete instructions and accepted arguments.

| Kind | ID | Purpose and trigger | Source |
|---|---|---|---|
| Skill | `repo-hygiene:repo-hygiene` | Check catalog for workspace tidying: filesystem garbage, tracked build artifacts, .gitignore gaps, scratch directories, orphan doc-assets and git auxiliary state. TRIGGER WHEN: running the tidy method (references/tidy.md) behind /daodan:tidy-repo or a lifecycle plan's workspace operations, or the repo-hygiene dimension of a review pipeline. DO NOT TRIGGER WHEN: source-level dead code or unused dependencies (use senior-review), or test consolidation (use testing:test-remediation-method). | [repo-hygiene](<../../plugins/repo-hygiene/skills/repo-hygiene/SKILL.md>) |
| Role | `repo-hygiene:workspace-auditor` | Workspace-hygiene auditor for filesystem garbage, tracked build artifacts, .gitignore gaps, scratch directories, orphan doc-assets and git auxiliary state. TRIGGER WHEN: dispatched by the tidy method of repo-hygiene:repo-hygiene behind /daodan:tidy-repo, or spawned in review pipelines, for tidying a repository, finding committed build output, auditing .gitignore, locating scratch directories, or listing stale stashes/worktrees/branches. DO NOT TRIGGER WHEN: source-level dead code or unused dependencies (use senior-review:cleanup-auditor), or applying removals (the tidy method applies them after its authorization, through /daodan:tidy-repo). | [workspace-auditor](<../../plugins/repo-hygiene/roles/workspace-auditor.md>) |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/repo-hygiene](<../../exports/claude/plugins/repo-hygiene>) | `native` | No workflow entry points |
| copilot | [exports/copilot/plugins/repo-hygiene](<../../exports/copilot/plugins/repo-hygiene>) | `native` | No workflow entry points |
| codex | [exports/codex/plugins/repo-hygiene](<../../exports/codex/plugins/repo-hygiene>) | `adapted` | No workflow entry points |
| pi | [exports/pi/plugins/repo-hygiene](<../../exports/pi/plugins/repo-hygiene>) | `adapted` | No workflow entry points |
| opencode | [exports/opencode/plugins/repo-hygiene](<../../exports/opencode/plugins/repo-hygiene>) | `native` | No workflow entry points |

<!-- daodan:reference:end -->
