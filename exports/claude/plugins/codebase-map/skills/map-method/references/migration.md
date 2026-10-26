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

# Output-root compatibility

Coordinators run preflight before root lookup, writer confinement and dispatch.
Workers only resolve supplied bindings afterward. Resolve the project root
independently of the analysis target. The owning method supplies this helper:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/migrate_root.py" --project <project-root>
```

Inspect its JSON and exit code. `absent`, `current`, `migrated` or `recovered` permit
continuation under `.codebase-map/`. `blocked` stops the dependent operation:
finish or explicitly conclude active legacy runs, or reconcile conflicting roots
without overwriting either. Never fall back to starting a fresh analysis because
the new root was absent before preflight. `--check` inspects without writing.

For a caller-supplied legacy `xray_path` or retained run binding, resolve it after
preflight and propagate the returned `path` to every helper and consumer:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/migrate_root.py" resolve --project <project-root> <bound-analysis-path>
```

Preserve run IDs, lineage, manifests, blobs, reports and historical citations.
The helper moves bytes intact and records the relocation. Translate a historical
analysis-root prefix through this resolver; never rewrite stored evidence or
translate source-file paths. An immutable run binding remains that same run.
The legacy directory contains only relocation metadata afterward. Legacy tools
must use updated compatibility entries and never write a second archive.
Original cache executables are not public APIs; locate helpers through the method.
