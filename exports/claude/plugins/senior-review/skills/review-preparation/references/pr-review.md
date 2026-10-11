<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

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

# PR Enhancement Pipeline

## CRITICAL BEHAVIORAL RULES

You MUST follow these rules exactly. Violating any of them is a failure.

1. **Execute phases in order.** Do NOT skip ahead, reorder, or merge phases.
2. **Start from git diff.** All analysis comes from `git diff` and `git log` -- the actual changes are ground truth.
3. **Run agents in parallel where marked.** Fire parallel agents in a single response.
4. **Confirm before creating PR.** If `--create` flag is set, show the full PR description for approval before running `gh pr create`.
5. **Never enter plan mode.** Execute immediately.
6. **Never push without permission.** If the branch hasn't been pushed, ask the user before pushing.

## Phase 1: Analyze Changes

### Step 1A: Identify the diff

```bash
# Detect base branch with fallback
BASE_BRANCH="${BASE_ARG:-main}"
if ! git show-ref --verify --quiet "refs/heads/$BASE_BRANCH" && \
   ! git show-ref --verify --quiet "refs/remotes/origin/$BASE_BRANCH"; then
  BASE_BRANCH="master"  # Fallback if main doesn't exist
fi
git fetch origin "$BASE_BRANCH" 2>/dev/null || true
MERGE_BASE=$(git merge-base HEAD "origin/$BASE_BRANCH")
git log --oneline "$MERGE_BASE"..HEAD
git diff "$MERGE_BASE"...HEAD --stat
git diff "$MERGE_BASE"...HEAD --name-status
```

If `--base` flag provides a different base branch, use that as `BASE_ARG`.

If no commits diverge from base, check for uncommitted changes:
```bash
git diff --name-only
git diff --cached --name-only
```

If nothing to analyze, say so and stop.

### Step 1B: Categorize changed files

Group files by type:
- **Source code**: `.py`, `.js`, `.ts`, `.tsx`, `.rs`, `.go`, `.java`, etc.
- **Tests**: files matching `test_*`, `*_test.*`, `*.spec.*`, `*.test.*`
- **Config**: `.json`, `.yaml`, `.yml`, `.toml`, `Dockerfile`, `Makefile`
- **Docs**: `.md`, `.txt`, `.rst`
- **Styles**: `.css`, `.scss`, `.less`
- **Build/CI**: `.github/`, `Jenkinsfile`, CI configs

### Step 1C: Compute statistics

```bash
git diff main...HEAD --shortstat
```

Present change summary:
```
Branch: [branch name]
Base: [base branch]
Commits: [count]
Files changed: [count] ([source] source, [test] test, [config] config, [docs] docs)
Lines: +[insertions] / -[deletions] (net: [net change])
```

---
