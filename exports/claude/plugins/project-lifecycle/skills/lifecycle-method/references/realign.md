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
before the first phase, and stop with that command when a required one is off.
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

# Realign

When commits land on the base branch, through a finish or a sync, the
knowledge that describes the project follows them, in this order. Run alone
after a merge made outside the cycle, it realigns the current head.

1. **Records.** Load `project-knowledge:adr-method`. A finish runs `promote`
   for its run's proposed record with `merged_sha`, and the helper marks the
   superseded records in the same transaction. A sync promotes the proposed
   record of every agenda task whose branch the incoming range merged, and
   lists to the user the active records whose cited symbols the range
   changed. A range without records says so.
2. **Map.** Load `codebase-map:map-method` and run the incremental update of
   the bound run against the new head: changed files and symbols re-derived,
   unaffected claims carried. Then the concept index of
   `abstraction-architect`, through its skill, for the changed scope. Cards
   turn stale by themselves and are rewritten only when an area is deepened.
3. **Documentation.** Run the `project-knowledge:project-knowledge` drift
   audit on the documents that cite the changed paths and symbols, and apply
   the authorized corrections; `project-knowledge:readme-craft` when the
   README cites them.
4. **Instructions.** Run `project-knowledge:instructions-method` to
   regenerate the loop block from the run and the record index: commands,
   active records, workspace convention. Nothing outside the markers changes.
5. **Head.** Record `last_synced` in the run and compare it with `HEAD`: a
   commit that landed meanwhile gets one more map update before the run
   closes.

A step that cannot run, for a missing runner or an unauthorized edit, stays
open with its reason; the run never closes on it silently.
