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

# Quarantine layout and lifecycle

Move only explicitly accepted files, retaining their relative paths:
`tests/unit/auth/test_login.py` becomes
`tests/_quarantine/unit/auth/test_login.py`. No renames obscure provenance.
For runners whose collection cannot exclude this path, choose a verified
non-collected project location and record it before moving files.

The native ledger is `tests/_quarantine/README.md`:

| Original path | Date | Category | Cause | Reason | Evidence | Owner | Return condition | Remaining protection | Gate identity |
|---|---|---|---|---|---|---|---|---|---|

Categories retain the native `orphan`, `failing`, `flaky`, `skipped` labels.
Category is the observed symptom; cause classification in the method determines
whether quarantine is eligible. Product defects and unknown causes remain active.

Configure and verify exclusion once, preserving the runner's existing settings:

| Runner | Exclusion |
|---|---|
| pytest | `norecursedirs = tests/_quarantine` or `--ignore=tests/_quarantine` |
| Vitest | Add `tests/_quarantine/**` to the existing `exclude` array |
| Jest | Add `<rootDir>/tests/_quarantine/` to `testPathIgnorePatterns` |
| Go | A non-collected directory or explicit quarantine build tag, verified with package discovery |
| Cargo | Outside the collected `tests/` and `src` trees |
| JUnit | Excluded source set in the project's build configuration |

Collection validates the layout only; it never passes the behavioral candidate gate.
An entry is processed when its module is touched. Age greater than three months
is a reason to investigate, never to delete. Retirement requires explicit inventory
acceptance plus evidence that behavior was retired or its exact failure mode has
replacement protection. Preserve real bugfix provenance and unresolved ledger rows.
Quarantine does not prove the remaining suite trustworthy or settle an unknown defect.
