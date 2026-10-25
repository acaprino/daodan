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

# Map consumption

Use this path for read-only evidence consumption during ordinary project work
and inside analyze or other composed workflows, with or without a Daodan command.
This unit grants no root migration, run creation, snapshot refresh, card
deepening or publication. Standalone consumption never performs them; a composed
workflow performs only operations already authorized by its own method.

1. **Locate existing evidence.** With MCP, call `codebase_map_runs`, then
   `codebase_map_status` for the selected completed run. Without MCP, inspect
   `.codebase-map/runs.json`, the published `state.json` and the root mirror.
   Latest-state questions may use the mirror; work bound to an invocation keeps
   that exact run directory. Do not select a partial run as a completed analysis.
2. **Navigate before scanning.** Use the task table in `reading.md`, section
   `Task views`. Query `codebase_map_outline`, `codebase_map_graph`,
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
