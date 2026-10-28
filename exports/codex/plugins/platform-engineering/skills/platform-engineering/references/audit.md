<daodan_host_binding host="codex">
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

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. Network search and network fetch
use the runtime's registered web search tool when the Codex configuration enables
it. A user question uses the runtime's registered question tool when one exists;
otherwise ask it in the reply and wait for the answer. In particular, a shell example's
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

# Platform audit

The platform portion of `/daodan:check-health` verifies supported browser, PWA,
mobile, Electron and Tauri mechanisms. The same `platform-reviewer` participates
in senior-review with its prepared inputs; never run both paths for one assignment.

## Input and scope

Use the caller's target, snapshot, declared platforms/versions, required behavior
and run directory. A file, directory or diff retains that scope. Detect platforms
from the relevant manifests, configuration and runtime entrypoints when the caller
has not named them; distinguish installed dependencies from mechanisms actually
used. Unknown support targets remain gaps.

A security, architecture or performance focus narrows platform-specific concerns.
Generic security, performance and operational coverage belongs to the caller's
other review dimensions; report adjacent leads without claiming their completion.

## Execute

1. Inspect effective platform configuration, native interfaces, packaging and
   lifecycle paths. Read only reference sections required by those mechanisms;
   verify historical advice against actual requirements and target versions.
2. Dispatch `platform-engineering:platform-reviewer` in an isolated context through
   the caller's declared host harness. Supply target/snapshot, detected or declared
   platform scope, instructions, evidence, permissions and
   `<run>/platform-review/REPORT.md`. Multiple platforms can share one assignment
   when their implementation is shared; each supported target must be accounted for.
3. Preserve application files. Supplied browser/device results count only for their
   recorded build and conditions. Running a new app, device or probe requires the
   caller's corresponding authorization and an owned disposable environment.
4. Verify the assigned report exists and identifies examined targets, findings,
   evidence, gaps and assigned knowledge usage. Missing delivery or required input
   is failure, not a clean audit.

## Output

Use the reviewer's compact native report at `<run>/platform-review/REPORT.md`.
Include supported target/version, required operation, effective mechanism, source
location, observable impact, counterevidence and correction for each finding.
Separate static reasoning from measured behavior. Add a concise coverage/gap list
and the actual commands/results of any authorized probes. Do not manufacture a
compliance certificate or mandatory hardening checklist.

A report grants no fix, installation, signing, deployment or publication authority.
The caller consolidates platform findings with other dimensions once.
