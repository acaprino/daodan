<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

### 7c. Cleanup Phases

Run this sub-step only when the accepted findings include codebase-hygiene items (dead code, orphan assets, unused or phantom deps, stale docs). Skip it entirely otherwise. Workspace hygiene that the filesystem and git decide alone (generated artifacts tracked in VCS, `.gitignore`, scratch directories, git auxiliary state) is applied by the tidy entry of `repo-hygiene:repo-hygiene`, never here. This is the only place in the marketplace that performs bulk removal of application code (test-file bulk removal is owned by the `testing` plugin's gated `testing:test-remediation-method`, mode `consolidate`); detection lives in `senior-review:cleanup-auditor` and in Agent B2 above, and neither of them deletes anything.

#### Critical rules

These are non-negotiable. Removal at this scale is safe only because of them.

1. **A `commit` grant and accepted severities required.** Reuse the accepted finding list from 7a or the identified lifecycle plan. Fixes from 7b must have completed and been committed when needed; otherwise record the step as not applicable. Announce in assess when this method is unavailable under a `fix` grant alone.
2. **Execution preflight.** Load the `project-protocol:project-protocol` skill. Require an exclusively owned isolated Git worktree with a clean tree, explicit scope and commit authorization. A shared checkout or dirty worktree is not eligible for hard reset.
3. **Pre-phase recovery point.** Immediately before each phase capture `pre_phase_sha` and its owned file manifest. Successful prior phases belong to this recovery point and must survive.
4. **Candidate gate before commit.** Run the project's recorded build and meaningful tests for the candidate snapshot. A remote gate must identify this exact snapshot, required command/configuration, job and successful result. Old green CI or collection alone cannot pass it. On failure use the common protocol's owned recovery to `pre_phase_sha`, verify restoration and halt. No commit exists for the failed candidate yet.
5. **Grep-before-delete.** For every asset, export, or dependency candidate, run a final confirmation Grep and proceed only on zero results. Skip any item with matches and log it separately.
6. **Never remove what is used through side effects.** Dynamic imports, decorators, framework conventions (Next.js `pages/` and `app/`, Django views, pytest fixtures), and module augmentation in `*.d.ts` with `declare module`.
7. **Python functions and classes require explicit approval.** vulture's false-positive rate is high; present them separately and wait for user confirmation.

#### Baseline

Before the first phase, record the starting commit (`git rev-parse HEAD`), run the build, and run the required checks to capture outcomes, protected behaviors, distinct failure modes and bugfix provenance. Counts are descriptive and never prove behavioral equivalence. Resolve `BUILD_CMD` and `TEST_CMD` from the project (`package.json` scripts, `pyproject.toml`, or the project equivalent), including the meaningful checks required for the affected behavior, not silently substituting unit tests for a required remote or end-to-end lane. If the baseline build or tests already fail, halt: the branch must be stable before subtraction.

#### Phase order

Lowest risk first, stopping at the first gate failure. Run only the phases the accepted findings actually require.

1. `brand` -- rebrand residue. Requires the user to confirm the old brand name first.
2. `assets` -- orphan static files. Watch for dynamic references built from template literals, so Grep partial basenames too. For eager `import.meta.glob` bloat, switch to `{ eager: false }` with lazy resolution rather than removing the glob, unless every file in it is provably unused; removing the glob needs user sign-off.
3. `deps` -- unused and phantom dependencies. Move phantom deps to the correct workspace's manifest instead of deleting them unless confirmed unused everywhere. Re-install after editing and commit the manifest together with the lockfile. Never touch implicitly-used devDependencies (`prettier`, `eslint`, `typescript`, `@types/*` matching runtime deps) without grepping config files first.
4. `exports`: dead exports, types, files, and unused Python symbols, in ascending risk order: ruff `F401` and `F841` auto-fix, then Knip unused exports and types verified by Grep across all workspaces, then Knip unused files verified against dynamic require and framework-convention paths, then vulture functions and classes under rule 7.
5. `docs` -- stale documentation and historical artifacts. Last on purpose, so it also catches doc references made stale by the `exports` phase. Detection-only unless the user explicitly opts into removal.

#### Per-phase template

For every phase `P`:

- **P.1 Confirm zero references.** Grep each candidate across source and docs, excluding the file being removed. Skip anything with a match.
- **P.2 Apply removals in reviewable batches** sized by risk and the affected behavior. Delete files or edit export lines for code, `git rm` for assets, manifest edit plus re-install for deps, line-level edits for stale doc references.
- **P.3 Gate.** Run `BUILD_CMD` then `TEST_CMD`. On failure, use the protocol recovery for the captured `pre_phase_sha`, verify restoration, report the failed candidate snapshot and halt. Hard reset is permitted only in the clean, exclusively owned isolated worktree; preserve all earlier successful phases and all external edits.
- **P.4 Commit.** One commit per phase: `chore(cleanup): <phase> -- <count> items removed`, with a short summary of what went in the body.
- **P.5 Proceed** to the next phase, or halt if the gate failed.

#### The docs phase

Highest false-positive rate of the five, so removal is opt-in and gated per item.

- Without an explicit opt-in, output the categorized report and stop.
- Plans, ADRs, and archive folders need per-item confirmation. A stale plan is indistinguishable from an active one to a tool. Show path, last-modified date, checklist completion percentage, and the first few lines of the body.
- Stale doc references are edits, not deletions. Rewrite the paragraph or strike the bullet; never delete a whole document over one stale link. If a document ends up effectively empty, propose its deletion as a separate confirmed item.
- Orphan doc-assets follow the same Grep-before-delete rule, searching only `*.md`, `*.mdx`, `*.rst`, `*.adoc`. Watch for inline base64 images that reference no filename.
- ADRs are historical record. The default action for `Status: Superseded` is to move them under a `superseded/` subfolder, not to delete them.

#### Cleanup report

After the last phase, or at the first gate failure, present one row per phase with status, items removed, and the commit sha, plus the behavior/failure-mode gate evidence and descriptive before-and-after test counts and the reverted phase if any. Then run the alignment check: Grep the removed symbols, paths, and dependency names against `CLAUDE.md` and propose updates for any hit, since a cleanup that leaves the project instructions describing deleted code has only moved the problem.

Four phase names that used to live here now belong to the tidy entry of `repo-hygiene:repo-hygiene`: `garbage`, `gitignore`, `scratch` and `git-state`. They left because the filesystem and git decide them without reading a symbol, so the build-and-test gate above protects nothing there. A hygiene finding naming one of those is not this loop's to apply.

This step is pure subtraction. It does not refactor architecture, does not touch test files unless they reference removed symbols, and does not run a bundle analyzer.
