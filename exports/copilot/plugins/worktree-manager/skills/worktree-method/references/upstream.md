> `${PLUGIN_ROOT}` is this plugin's install directory, the one that holds its `plugin.json`. If the host has not expanded it, resolve it from where this file was loaded.

<daodan_host_binding host="copilot">
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

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. fetch
retrieves a known URL and does not search: network search needs a search tool
registered in this session. A user question is asked in the reply, and the run
waits for the answer. Custom
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

# Worktrunk runtime and upstream updates

Canonical provider: [max-sixty/worktrunk](https://github.com/max-sixty/worktrunk).
Worktrunk is dual licensed **MIT OR Apache-2.0**, at the recipient's choice.
Daodan's adapter is original code and delegates to the external executable.
No upstream Rust source, plugin bodies or binary is shipped in this kernel.
The machine-readable compatibility record is `upstream.json` beside this file.

## Availability

Run the bundled boundary first:

```text
python "${PLUGIN_ROOT}/skills/worktree-method/scripts/worktrunk_runtime.py" probe --project ROOT
python "${PLUGIN_ROOT}/skills/worktree-method/scripts/worktrunk_runtime.py" upstream-check
```

The main checkout's `.daodan/tools/worktrunk/<version>/` is checked before PATH.
Automatic discovery requires an ignored, untracked executable in the owned
`.daodan` home without links. Repository-tracked executables are refused before
they can run. PATH fallback inspects only absolute directory entries and rejects
executables in the invoking checkout, the target checkout or any of their
registered linked worktrees, including paths that resolve into those trees.
Empty and relative PATH entries and implicit current-directory lookup are
excluded without changing the process environment. Outside Git, an executable
directly in the invoking directory is excluded; a user installation in one of
its child directories remains eligible through an absolute PATH entry.
On Windows, fallback accepts
only `git-wt.exe`, never batch files or `wt.exe`.
The installation step verifies the official archive checksum;
later probes check availability/version, not a universal binary security audit.
An explicitly supplied executable may be used for another authorized install.
The boundary checks the actual binary identity and supported version. On Windows,
`wt.exe` can be Windows Terminal; use Worktrunk's `git-wt.exe` or an explicit
verified path. Do not launch the unrelated program as a probe.

If absent, report the required release from the compatibility record and use
the provider's [installation documentation](https://worktrunk.dev/install/).
Prefer its released binary for the current OS/architecture, verify its published
checksum before execution, and keep a portable install in the project's
`.daodan/tools/worktrunk/<version>/` when no existing authorized installation
fits. System-wide/package-manager changes need their applicable authorization.
Do not run a downloaded installer script blindly. Do not install upstream agent
plugins or shell profile hooks as a prerequisite of Daodan's adapter.

Core commands support Windows; upstream shell hooks require Git Bash. Daodan
creation disables Worktrunk hooks and uses an invocation-only `core.hooksPath`
override pointing at the bundled empty hook directory. Native checkout hooks
therefore cannot run setup implicitly; persistent Git configuration is unchanged.
Run explicitly authorized setup separately.
Supply a working directory and argument array through the actual host execution
mechanism. Registration or generated instructions do not prove that a host can
execute or bind a workspace.

## Update procedure

1. On a requested upstream update, run `upstream-check`. Keep its checked and
   supported versions distinct. Network/rate-limit failure is unavailable
   evidence, not proof of being current. This command changes no installation,
   pin, project configuration or catalog.
2. Read the candidate release notes, license and relevant CLI/schema changes at
   its exact tag/commit. Assess hook execution, path handling, staging, merge,
   cleanup, supported OS and security changes. The absence of an advisory is
   not a security audit. Preserve the previous known-compatible installation.
3. Test the candidate in an isolated temporary repository with a separate
   candidate copy of the adapter's compatibility record. Verify executable
   identity, structured output, creation/resume under the main `.daodan`, dirty
   and ignored file preservation, candidate review boundaries, interrupted
   cleanup and the active host's execution binding. Keep broader host checks
   explicitly unverified until exercised.
4. Advance `upstream.json` only with the source commit, version, asset provenance
   and successful compatibility evidence. Update the original adapter only for
   demonstrated contract changes. Bump its plugin version, regenerate all host
   packages and run the repository checks. Failed probes keep the old pin and
   describe the incompatible behavior.
5. Activate the tested binary under the user's update authorization. Verify its
   version from the actual invocation path and retain the previous version for
   recovery. Report separately release discovery, adapter support, installation
   and host execution. Do not mark a downloaded release as an adopted update.

This is versioned external dependency maintenance, not vendored source syncing.
It adds no copied-source sync target and schedules no background polling.
