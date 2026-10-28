---
name: worktree-method
description: >
  Manage Git task workspaces through the external Worktrunk CLI: create or resume
  under .daodan, list every worktree, annotate descriptions and tags, prepare safe
  lifecycle handoffs and check supported upstream releases.
  TRIGGER WHEN: starting or resuming an isolated task, listing or annotating worktrees,
  preparing their integration or cleanup, or updating Worktrunk compatibility.
  DO NOT TRIGGER WHEN: reviewing code correctness or deciding whether a task is complete;
  those decisions remain with the existing review and delivery owners.
---

> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/` and `prompts/`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi has no network tool: network fetch and network search run as shell
commands, and a user question is asked in the reply while the run waits for the
answer.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
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

# Task workspaces

Load skill `work-controller:work-record` for working discipline, task identity, grants,
questions and evidence. Git owns actual branches, commits and worktree paths;
this method owns workspace annotations and the external CLI boundary. It does
not introduce another scheduler, reviewer or completion gate owner.

Worktrunk is a separately installed executable. Its source and host plugins are
not copied into this package. Read `references/upstream.md` before provisioning
or updating it; `references/upstream.json` records the supported release.

## Entry and outputs

Interpret the caller's free text as list, annotate, create/resume, lifecycle
handoff or upstream update. A plain inventory is read-only and opens no task.
Use the owning helper with an explicit project directory:

```text
python "<plugin-root>/skills/worktree-method/scripts/workspaces.py" --project ROOT list
python "<plugin-root>/skills/worktree-method/scripts/workspaces.py" --project ROOT annotate --path PATH --description TEXT --tag TAG
python "<plugin-root>/skills/worktree-method/scripts/workspaces.py" --project ROOT create --task-id ID --kind fix --slug login-timeout --base REV --prefix codex --description TEXT
```

Check the helper's help for optional arguments. Pass values as separate process
arguments; never interpolate free text into shell commands. Its JSON output is
the data contract, not text to execute. Preserve errors and incomplete creation.

Display at most the useful inventory columns: description, tags, branch, task
and path. Join the existing agenda when task phase/holder is needed; do not
infer completion from a clean checkout. Include external and detached worktrees.
Missing catalog entries remain unannotated, not hidden. Metadata for a removed
checkout remains visible as stale information rather than silently recreated.
Descriptions describe the task; a generated diff summary must not replace them.
Tags are labels, not Git tags. For additions or removals, use repeated
`--add-tag` or `--remove-tag` arguments; the helper applies those changes to the
latest set under its catalog lock. Repeated `--tag` arguments explicitly replace
the whole set; `--clear-tags` clears it. Do not combine replacement or clearing
with additions/removals. Report unavailable remote status as unknown.

## Create or resume

1. Resolve the user's task, approved workspace mode, base revision and naming
   policy. Default branch prefix is `task`; an active host or project may require
   another prefix (for example `codex`). Use a stable task ID and a short slug;
   changing a description never renames a branch or checkout.
2. Resolve the main checkout through Git's common directory. New worktrees live
   only in its `.daodan/worktrees/`; annotations live in `.daodan/worktrees.json`.
   Require `.daodan` to be ignored before creation. If it is not, prepare the
   scoped ignore change under the current task grant and recheck. Never create
   nested homes from a linked worktree. Bare repositories without a main checkout
   need a separately specified home and are unsupported by this helper.
3. Probe the supported executable before creation. The helper reserves the task
   identity and invokes Worktrunk with its lifecycle hooks and native checkout
   hooks disabled for that invocation. A retry reconciles
   the actual checkout's repository, worktree registration, branch and HEAD;
   mismatches stop without deleting or overwriting.
   Existing foreign worktrees may be listed/annotated; annotation is not ownership
   and does not authorize their reuse, mutation or removal.
4. Bind the host's actual execution directory and permitted workspace to the
   returned path before dispatch. A successful shell `cd` is not proof of session
   binding. If the host cannot use the requested checkout, keep it recoverable
   and report that capability gap. Never silently work in the main checkout.
5. Execute only the task's trusted, authorized setup. Record setup separately
   from checkout creation and wait for required setup to finish. Do not copy all
   ignored files, secrets, dependency environments or mutable caches implicitly.

The helper confines its own catalog and creation paths; it does not enforce
every later agent tool operation. Do not claim a host sandbox from this check.
Main-home discovery and Git metadata are shared; Worktrunk's internal logs and
state can live in the shared Git directory, outside `.daodan`.

## Integration and cleanup

Read `references/lifecycle.md` when the delivery owner requests these phases.
Return paths, source/target identities and metadata to the caller. The caller
keeps its existing authorizations, candidate-bound review and result protocol.
Never call bare `wt merge`, install global lifecycle hooks or remove a checkout
on agent/session exit. Preserve original task commits and the run's immutable
review receipts across squash and cleanup.

## Upstream updates

Read `references/upstream.md`. A release check is read-only; installation,
compatibility testing and adoption are distinct outcomes. Unsupported binaries
fail with an explicit recovery path rather than falling back to unrelated tools.
