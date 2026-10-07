# repo-hygiene

Workspace tidying decided by the filesystem and git alone. Committed build output,
`.gitignore` gaps and stale rules, filesystem garbage, scratch directories, orphan
doc-assets, and stale git state.

**Install:** ships with the marketplace. No dependencies: it is a leaf by rule.

| | |
|---|---|
| **Command** | `/repo-hygiene:tidy` |
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

C5 protects `.daodan/` and `.codebase-xray/` by name, plus any directory containing
a `.daodan-root` sentinel and its ancestors. It never proposes removing these
roots and does not interpret protocol states. Classifying run evidence, resume
data and concluded output belongs to [project-lifecycle:consolidate](project-lifecycle.md).

**Two profiles, one set of definitions.** The full profile runs over the working tree.
The lite profile runs over the files a diff adds, and is what the inline hygiene pass
of `/senior-review:code-review` and `/senior-review:pr-review` loads. C4 through C7 are
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

## `/repo-hygiene:tidy`

```
/repo-hygiene:tidy [path] [--fix] [--commit] [--phases=garbage,gitignore,scratch,git-state]
```

Detects and reports by default. `--fix` applies and leaves the working tree modified
with no commits. `--commit` implies `--fix` and adds one commit per phase. The flags
mean exactly what they mean in `/senior-review:code-review`.

Four phases, run in order: `garbage`, `gitignore`, `scratch`, `git-state`.

**There is no build-and-test gate between phases**, because nothing applied here is
code. For `gitignore`, the protection that matters is the per-item confirmation on
`git rm --cached`, not a test suite that passes because the untracked files are still
sitting on disk.

**Untracked removals go to quarantine**, at `.repo-hygiene/quarantine/<timestamp>/`,
preserving relative paths. Git holds no copy of an untracked file, so deletion would be
the one irreversible operation in the command, and it is not taken. This is what makes
`--fix` safe without commits: everything it does is undoable by hand.

**`--commit` requires a clean tree** because its per-phase commits are its revert
mechanism and an unrelated modified file would be swept into one. `--fix` has no such
requirement: it stages nothing and keeps untracked removals in quarantine. The
accepted item list still bounds its changes. Staging is always by explicit path,
never `git add -A`.

## Inside a team review

`/senior-review:team-review` spawns `repo-hygiene:workspace-auditor` as an always-on
dimension alongside `senior-review:cleanup-auditor`. The two perimeters are disjoint by
construction, so consolidation has nothing to deduplicate between them. **A finding
appearing in both reports is a boundary violation to investigate, not an `echo` to
fold.**

## Related

- [senior-review](senior-review.md): everything hygiene-adjacent that needs source
  comprehension, plus Step 7c, which removes application code in five gated phases.
- [testing](testing.md): `/testing:test-consolidate` owns bulk removal of test files.
- [dependency-audit](dependency-audit.md): CVEs, licenses and version drift from each
  ecosystem's own tooling, which is a different question from whether a dependency is
  used.

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `1.3.0`. **Source:** [plugin.toml](<../../plugins/repo-hygiene/plugin.toml>).

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
| Skill | `repo-hygiene:repo-hygiene` | The check catalog for workspace tidying: filesystem garbage, generated artifacts tracked in git, `.gitignore` completeness and archaeology, scratch directories, orphan doc-assets, and git auxiliary state. Two profiles, full and lite, over one set of check definitions. TRIGGER WHEN: running `/repo-hygiene:tidy`, spawned as the repo-hygiene dimension of a review pipeline, or running the diff-scoped VCS check inside a code or PR review. DO NOT TRIGGER WHEN: the question needs source comprehension (dead exports, unused dependencies, orphan application assets, rebrand residue), which belongs to `senior-review`. | [repo-hygiene](<../../plugins/repo-hygiene/skills/repo-hygiene/SKILL.md>) |
| Role | `repo-hygiene:workspace-auditor` | Adversarial workspace-hygiene auditor: filesystem garbage, generated artifacts tracked in git, `.gitignore` completeness and archaeology, scratch and pipeline-output directories, orphan doc-assets, and git auxiliary state. Report-only, no edits. TRIGGER WHEN: the user asks to tidy a repository, find committed build output, audit or repair `.gitignore`, locate scratch directories or leftover pipeline output, or list stale stashes, orphan worktrees and gone-upstream branches. Spawned as the repo-hygiene dimension of a review pipeline. DO NOT TRIGGER WHEN: the finding would need source comprehension (dead code, unused exports, unused dependencies, orphan application assets, rebrand residue), which belongs to `senior-review:cleanup-auditor`; or the user wants the removal applied, which belongs to `/repo-hygiene:tidy`. | [workspace-auditor](<../../plugins/repo-hygiene/roles/workspace-auditor.md>) |
| Workflow | `repo-hygiene:tidy` | Tidy the workspace: filesystem garbage, generated artifacts tracked in git, `.gitignore` gaps and stale rules, scratch directories, orphan doc-assets, and git auxiliary state. Detects by default; applies with --fix or --commit. TRIGGER WHEN: the user asks to clean up a repository, remove committed build output, fix or audit `.gitignore`, clear scratch and pipeline-output directories, or list stale stashes, orphan worktrees and gone-upstream branches. DO NOT TRIGGER WHEN: the target needs source comprehension (dead code, unused exports, unused dependencies, orphan application assets), which belongs to `/senior-review:code-review`; or the target is test files, which belongs to `/testing:test-consolidate`. | [tidy](<../../plugins/repo-hygiene/workflows/tidy.md>) |

### Workflow contracts

Contracts describe observable outputs; Markdown bodies define decisions,
flags, safety gates and execution. Declared `invoke` execution is unsupported.

#### `repo-hygiene:tidy`

**Arguments:** `[path] [--fix] [--commit] [--phases=garbage,gitignore,scratch,git-state]`

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `tidy-completed` |
| Artifacts | `tidy-report` |
| Schemas | None declared |
| Declared workers | `repo-hygiene/workspace-auditor` |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [tidy.toml](<../../plugins/repo-hygiene/workflows/tidy.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `scope` | None | None | `shared` | None declared | `preferred` |
| `review` | `scope` | `workspace-auditor` | `required` | None declared | `preferred` |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/repo-hygiene](<../../exports/claude/plugins/repo-hygiene>) | `native` | `tidy: native-team` |
| copilot | [exports/copilot/plugins/repo-hygiene](<../../exports/copilot/plugins/repo-hygiene>) | `native` | `tidy: parallel-subagents` |
| codex | [exports/codex/plugins/repo-hygiene](<../../exports/codex/plugins/repo-hygiene>) | `adapted` | `tidy: parallel-subagents` |
| pi | [exports/pi/plugins/repo-hygiene](<../../exports/pi/plugins/repo-hygiene>) | `adapted` | `tidy: parallel-subagents` |
| opencode | [exports/opencode/plugins/repo-hygiene](<../../exports/opencode/plugins/repo-hygiene>) | `native` | `tidy: parallel-subagents` |

<!-- daodan:reference:end -->
