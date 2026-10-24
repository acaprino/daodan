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
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
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
