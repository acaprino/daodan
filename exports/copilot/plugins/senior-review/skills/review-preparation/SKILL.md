---
name: review-preparation
description: >
  Prepare the existing code, team or PR review inputs without writing another detection prompt. Load before dispatching reviewers in senior-review or project-lifecycle.
---

<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

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

# Review preparation

Branch input: `variant=code-review|team-review|pr-review`, target, flags, output,
optional bound scope/baseline/candidate. Output: snapshot, brief, context,
selection, run and evidence. Light loads only `references/composition.md` here;
its own method prepares inputs.

Load `project-protocol:project-protocol` for preflight and confined run records. Read-only reviews may use a dirty workspace: capture its complete snapshot and
preserve edits. Review grants no mutation.

The coordinator alone may perform the project-bound Codebase Map preflight
before dispatch: move an idle legacy archive intact and write only bound
relocation metadata. This bounded exception authorizes no application changes,
analysis run, worker migration or generic filesystem move.

A caller-bound candidate is authoritative. Validate its project/worktree, run,
scope and current snapshot through project-protocol before deriving review inputs.
Use its captured baseline and exact candidate content, including scoped untracked
files and their full contents. Exclude the run's output root. Never replace that
target with a branch comparison or the previous commit. Missing baseline content
is a declared comparison gap, not permission to invent a before-state; preserve
the actual candidate and leave any gate needing that comparison unavailable.

## Load map

| Step | Read inside this skill |
|---|---|
| Always, before the variant | `references/candidate-grounding.md`: target kind/basis, governing snapshot policy, ground-truth gate, evidence pack, budget and roster by kind |
| Then | `references/<variant>.md` |
| Reviewer selection | `references/stack-dimensions.md`, then `references/knowledge-bindings.md` |
| Reviewer catalog | `references/reviewer-catalog.json` (compiled): reviewer identities, triggers, prerequisites, host bindings. Never scan role kernels at runtime |
| Always, after the roster | `references/composition.md`: bind and validate specialist jobs before recording the complete review or dispatching |

Execute preparation once under the computed roster and support requirements.
For team review Phase 1a, when selected, the
coordinator executes the `codebase-map:map-method` analyze entry's preflight,
answerable checkpoints, delivery check and publication decision, dispatching
`codebase-map:map-analyst` in one isolated context through the consuming
workflow's declared host harness. Loading either body alone executes nothing;
the analyst is a role, while analyze remains the entry. This step introduces no
second review preparation or final report owner. Required workers retain
isolated contexts. Resolve the exact run in runs.json and never
substitute a mirror for a missing run.

Reports use the explicit review output root; lifecycle runs keep scratch/context
in their run root. Record the same
snapshot and run identity. Return missing evidence as degraded coverage.

Read `references/stack-dimensions.md` to include React, TypeScript and platform
bindings in the same reviewer selection. For team review this is part of Phase 0b,
before presenting the plan; for code and PR review it follows scope resolution.
Preparation never dispatches. Record the activation
evidence or skip reason for each dimension, then pass the complete selection to
review-method. A prepared bundle cannot imply that any selected reviewer ran.

Load the `skill-catalog:skill-catalog` skill. Read `references/knowledge-bindings.md`
inside this skill after resolving scope and the native reviewer selection. Prepare
one `knowledge_selection` against the same candidate snapshot and actual available
skill inventory. Add scope/lens assignments and content fingerprints to this brief;
knowledge selection is open to every classified available stack, not a fixed
language list. Return inventory/classification/match gaps and failed selected loads
explicitly. Reuse the exact prepared record until any of its bindings changes.
