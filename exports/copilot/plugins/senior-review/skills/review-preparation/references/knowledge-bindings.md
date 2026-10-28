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

# Knowledge bindings

Use skill-catalog's canonical inventory, selection and loading method once, inside
this review's output root. Keep the same candidate snapshot, project/worktree and
run identity. The generated registry is not installation evidence. Normalize the
actual host/project inventory with the catalog's adapter instructions and preserve
its availability provenance. Methods, workflow wrappers and role wrappers are not
automatic review knowledge. An unclassified relevant match is a classification gap.

Derive one scope per affected package/behavior boundary. Record exact target paths,
languages, used frameworks, topics and code/configuration activation evidence.
Include relevant embedded SQL or cross-language calls when the actual candidate
shows them. Root dependencies from unrelated monorepo packages do not activate
knowledge. Search metadata as needed to discover useful labels, then refine the
evidence-backed scope signals. Search ranking is a lead, not a coverage gate.

Map knowledge dimensions to the existing selected native delivery IDs in each
scope's `workers` field: correctness to the code lens, security to security,
performance to the applicable performance lens, data-integrity to persistence,
resource-lifecycle to ownership, test-quality to the test lens, and other dimensions
to their actual owner. The mapping is about review risks, never a language registry.
Assign every selected dimension explicitly, including several dimensions owned by
one lens. Preparation preserves `dimension_workers`; an unassigned dimension is
failed coverage and cannot be hidden by another assigned dimension.
Use the full existing role brief. Where no selected lens owns a relevant domain
question, add one task-specific lens through the already declared
`work-controller:isolated-worker`, with its scope, budget and assigned report path.
That worker applies selected knowledge; it never substitutes for a failed mandatory
canonical specialist or dispatches a new undeclared role. Respect explicit reviewer
selection and budgets; declare excluded coverage rather than silently expanding it.

Run catalog `prepare` with operation=review after assigning all selected knowledge
to worker delivery IDs. Persist its exact result as `knowledge/selection.json` in
this run. `knowledge_selection` carries that path and selection fingerprint in the
native brief/selection. Each native reviewer binding records `knowledge_ids` (empty
when none) for its own scope/lens. A knowledge input is selected once, with one or
more scoped worker assignments. Preparation hashing does not prove worker reading.
Do not create one reviewer per skill, repeat preparation or run specialist workflows.

The existing React/TypeScript/platform role table remains the canonical role-binding
contract. This knowledge selection extends its coverage to other available stacks
through the general review lenses. Their required role providers remain mandatory.
Keep automatic activation, explicit overrides, independent inputs and report rules.

Before dispatch, validate target and knowledge bindings together. A selected load
failure is failed coverage; any candidate gate requiring it cannot pass. Unmatched,
unknown or unresolved scope signals remain declared gaps. A report may deliver that
degraded coverage but must not claim those domains were verified. Use the same
selection through lifecycle change/repair/verify, never a branch substitute.
