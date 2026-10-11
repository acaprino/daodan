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

# Instruction loading and authority

Use this preflight within instruction preparation, proportional to the requested
scope. Record its evidence in the owned run. Do not copy a universal precedence
table into project instructions or inspect unrelated private host configuration.

1. Identify the active host and installed version when observable, the project
   root/worktree, working directory and relevant configured instruction mechanism.
   Read applicable project configuration within the authorized scope. Use the
   installed host's documentation or official documentation for its version to
   verify discovery and precedence; missing evidence remains UNVERIFIED.
2. Map the selected root and nested instruction paths, their scope, canonical
   owner and any generated destinations or synchronization command. Distinguish
   files that exist from files selected by the configuration and files actually
   loaded. A conventional filename alone does not establish any of those claims.
3. Follow imports only according to the host's supported mechanism and the
   project's trust rules. Distinguish automatic imports from ordinary Markdown
   links: a pointer to a guide is discoverable detail, not proof that its contents
   enter every session. Check referenced paths and imports for broken targets or
   conflicting obligations; do not silently flatten separate scopes.
4. Verify loading with available host diagnostics or an observed session read,
   preserving what that evidence covers. File discovery, generated-copy parity
   and model compliance are different facts. Do not resolve conflicting rules by
   inventing a cross-host ordering; identify the applicable source and unresolved
   conflict before a dependent action.
5. After an authorized edit, regenerate from the canonical owner, check parity and
   determine whether the host needs a supported reload or a new session. Record
   activation evidence or the open check. Do not assume the current context has
   discarded an older instruction because the file changed on disk.
6. Distinguish guidance from enforcement. A written prohibition does not establish
   a sandbox, permission restriction, hook or CI gate. Verify the guard's actual
   configuration and relevant runtime evidence before calling it enforced; keep
   untested or unavailable enforcement claims UNVERIFIED.

Keep only stable, project-relevant loading and synchronization guidance in durable
instructions. Host probe output, session identity, temporary paths and reload
status remain operational evidence. An unavailable loading or enforcement check
must be visible in the result; it cannot be converted into a successful gate.
