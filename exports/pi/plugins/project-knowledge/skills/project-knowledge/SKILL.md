---
name: project-knowledge
description: >
  Prepare, audit and maintain durable project documentation with a file/audience plan. Load when writing guides, reconciling document drift or coordinating knowledge work.
---

<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
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

# Project knowledge method

## Common contract

Load `project-protocol:project-protocol` for operational records and gates.
Receive or initialize an owned run before dispatch. A caller's existing run is
reused; do not create a competing run or choose an unrelated latest report.
Inputs: project/worktree identity, target scope, snapshot, task intent, existing
documents, evidence paths, audiences, authorized mode, budget and output root.
Modes: audit-only/dry-run, plan-only, fix and commit. Audit-only may write only
the owned run report, never project source or durable knowledge. A requested
missing path is an explicit gap; no automatic broadening of scope.

The coordinator alone may perform the project-bound Codebase Map preflight
before dispatch: move an idle legacy archive intact and write only bound
relocation metadata. This bounded exception authorizes no application changes,
analysis run, worker migration or generic filesystem move.

Operational records remain in the run. Durable documents describe verified
implementation or attributed approved intent, with unknowns labelled. They do
not accumulate progress, branch names, one-run measurements or session status.

Read `references/preparation.md` before dispatch and
`references/documentation-audit.md` for the twenty drift dimensions. For guide
writing read `references/guide-method.md`; for authorized changes read
`references/apply-method.md`. Writer briefs also load
`references/writing-guidelines.md`, `references/audience-adaptation.md` and
`references/diagram-patterns.md` according to the task.

## Reusable dispatch

- Discovery: `codebase-explorer`, with the exact scope and owned context output.
- Documentation drift: `documentation-engineer`, explicitly audit-only until
  application is authorized.
- Cross-document evidence review: `guide-reviewer`, explicitly audit-only.
- Structured writing: overview-writer, tech-writer, flow-writer,
  onboarding-writer and ops-writer, only for their assigned files.
- Existing document structure: doc-humanizer. It changes form, not facts.
- Instruction claims: load `instructions-method` and dispatch instructions-auditor.
- README: load `readme-craft` and execute its audit/apply method in context.

No detector prompt is repeated in this entry method. Every writer receives a
file/audience plan and cannot invent additional files to satisfy a template.
Dispatch and delivery barriers use the host harness. Do not spawn a fixed number
of writers or require a team-only API.

## Result

Preserve native findings and locators. Record changes by owned file, retained or
migrated information, unresolved intent, stale inputs, checks run and checks not
available. A missing reviewer or changed snapshot blocks successful completion.
For requested HTML or useful comparison/navigation, the coordinator reads
`references/human-view.md` before closing the run.
Validate and close the operational result with the project-protocol method.
