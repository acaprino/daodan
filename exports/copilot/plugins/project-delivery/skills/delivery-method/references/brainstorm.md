<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
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

# Brainstorm

Explore an idea with the user before a task exists. It reads the project,
writes no code, decision record or implementation plan; its `brainstorm` run holds the conversation. Scientific publication follows the bounded exception below.

## Ground first

1. Load `codebase-map:map-method` and deepen the idea's area as its
   `references/deepen.md` directs. Name the code the idea would touch and the
   existing code that already does part of it, with the concept index of
   `abstraction-architect` when present.
2. Load `project-delivery:adr-method` and run `resolve` on that area: the
   active records are constraints, and a record the idea contradicts is said
   at once.
3. Read what the project's instructions say about the area.
4. Load `research:science-based-approach`, automatic checkpoint entry, before comparing alternatives. Reuse the caller's context and run. Read mode first; OFF skips scientific archive/network work. Read-only brainstorming keeps results in the authorized run or chat. Research publication under its canonical docs destination is permitted only when the caller already grants documented research; it does not authorize product edits or a second interview.

## Talk

Ask by the work record's question rule, one per turn, anchored to code
("today `path:line` does X; should the idea change that?"): purpose, users,
constraints, success, never what the code settles. Once the idea is clear,
ask which of two or three alternatives to take, each costed in modules and
files, records extended or superseded, tests, risks and waves; name one that
gives a concept a second owner.

## Close with the user's choice

- **Do it.** Write the brief into the run (objective, chosen alternative,
  examples, constraints, rejected alternatives with their reasons) for the
  change cycle's interview to start from.
- **Keep it.** With the user's agreement, write
  `docs/ideas/<YYYY-MM-DD>-<slug>.md`: the idea, the code and records it
  touches, the alternatives with their costs, and the open questions. It is
  the idea document a brainstorm writes. The scientific-publication exception above remains bound to the caller's existing grants.
- **Drop it.** Nothing further is written outside the run; preserve any scientific research already published within its grant.
