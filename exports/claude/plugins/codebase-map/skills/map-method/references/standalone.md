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

# Map consumption

Use this path for read-only evidence consumption during ordinary project work
and inside analyze or other composed workflows, with or without a Daodan command.
This unit grants no run creation, snapshot refresh, card
deepening or publication. Standalone consumption never performs them; a composed
workflow performs only operations already authorized by its own method.

1. **Locate existing evidence.** With MCP, call `codebase_map_runs`, then
   `codebase_map_status` for the selected completed run. Without MCP, inspect
   `.codebase-map/runs.json`, the published `state.json` and the root mirror.
   Latest-state questions may use the mirror; work bound to an invocation keeps
   that exact run directory. Do not select a partial run as a completed analysis.
2. **Navigate before scanning.** Use the task table in `reading.md`, section
   `Task views`. To find the code a request is about, follow `locate.md`:
   `codebase_map_search` with the names in the request, then
   `codebase_map_outline` and `codebase_map_graph` on the hits. Query
   `codebase_map_meta_query` and `codebase_map_artifact` as pertinent, or search
   the run's Markdown and the project with ordinary tools. Locate symbols,
   contracts, flows and documentation leads before broadly reading source.
3. **Verify and bound the work.** Before editing, call
   `codebase_map_edit_impact` on affected symbols when available. Read exact
   target and neighbor source with `codebase_map_read` or ordinary file tools
   only when the consumer may read source; artifact-only consumers stay within
   their declared inputs. The map supplies leads, not verdicts; verify material
   behavior and business rules against current source. Static evidence
   establishes no runtime behavior.
4. **Recover by consumer role.** `codebase_map_diff` compares a bound snapshot
   with current source. A newer snapshot does not refresh an older report or
   card. A read-only consumer discloses absent, incomplete, inaccessible or
   drifting evidence and continues with ordinary repository exploration, never
   starting analysis, update or deepening implicitly. A composed producer
   instead follows its authorized refresh, re-derivation or blocking procedure;
   this unit never replaces those obligations.
