<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
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

# Guide method

Start with input preparation and the file/audience plan. A small project may
need an existing README update and no new guide directory. A comprehensive
multi-document set is allowed only when requested or justified in the authorized
plan; numbered files are a naming choice, never a required package or quota.

Resolve the mode before dispatch. Audit-only reviews existing documentation with
documentation-engineer and guide-reviewer, then returns native findings through
the protocol, writing only their owned reports. Plan-only delivers the
file/audience plan and returns without starting writers. A request to
create or update the guide authorizes the planned document edits; otherwise use
plan-only. Explicit audit/plan/fix/commit arguments and caller authorizations take
precedence, and a commit still requires commit authorization.

For writing, dispatch codebase-explorer to prepare the assigned context brief in
the owned run. Pass the scoped source/intent evidence and planned readers rather
than requiring a whole-project rescan. Verify that delivery before giving its
context_path to writers or the semantic mapper.

Load `codebase-map:map-method` for a bound analysis. Dispatch its
`codebase-map:semantic-interconnect-mapper` when contracts, invariants and domain
rules are needed, with the scoped context and an owned report destination. Each
row retains its evidence status. Failure is a failed delivery; do not silently
proceed as if that dimension were covered.

Assign each file to exactly one writer and pass context_path, evidence_paths,
output_files, readers, document purposes, existing content, boundaries and mode.
Writers share verified context but their agreement is inherited evidence unless
they derive the premise themselves. Dispatch only the needed writers using the
host's supported strategy. Check every delivery before cross-document review.

Dispatch guide-reviewer in audit-only mode with the planned file set. A review
may request corrections or a navigation index when the plan calls for one; it
does not create a fixed glossary/index package or edit another writer's files.
Apply accepted corrections through the owning writer. Load
`text-humanizer:anti-ai-writing-patterns` and dispatch
`text-humanizer:text-humanizer` for a proportional docs-register voice pass when
the requested writing needs it. Preserve factual content, citations, tables,
diagrams and the author's intentional voice. No automatic second pass is needed
when the draft already satisfies the register.

Finish through apply-method: inspect downstream links, retained facts and the
current snapshot. Claimed runtime setup remains unexercised unless an allowed
project check actually ran.
