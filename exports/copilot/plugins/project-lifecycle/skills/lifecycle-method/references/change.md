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

# Change

Own the complete requested development outcome: bootstrap, feature, bugfix, refactor
or migration. Discover code, tests, decisions, instructions and constraints first.
Look for a useful implementation before adding another representation.

For a requested project-wide architectural refactor or deep rationalization, first
obtain full static context through codebase-xray:analyze. Reuse an existing run only
after validating its source snapshot, requested scope, depth and completion; bind
that exact run in the ledger. An ordinary scoped change uses the context it needs.
Inventory, deep reading and runtime exercise remain separate coverage facts.
Prioritize evidenced severe defects and broken product entry paths before cosmetic
cleanup; preserve the approved contract and regression protection while fixing them.

Use superpowers:brainstorming and superpowers:writing-plans when design or impact
requires them. Keep planning proportional; direct authorized small changes do not
need a ceremonial project audit. Reuse upstream execution via
superpowers:executing-plans or superpowers:subagent-driven-development. Its own
ledger is referenced from the run rather than copied into a second live state store.

Define intended behavior and source of authority. Conflicting requirements become
concrete alternatives; do not promote the current code into the requirement.
Bootstrap includes a minimal structure and project-knowledge instructions, chosen
build/test commands and a short explanation of the project. Do not scaffold every
framework or document template.

The base developer context implements the plan. Specialist extras remain available
as independent commands/results; automatic extra dispatch requires a consumer's
declared mandatory dependency. Do not invent a dynamic optional-plugin registry.

Delegate meaningful test authoring to testing:test-writer with explicit behavior,
oracle/source, existing test inventory, runner and layer. Search before writing.
When suite rationalization is requested, use testing:test-preparation and the
testing:test-suite-auditor across the declared suite in bounded batches, accounting
for every selected layer and uncovered portion. Use testing:test-remediation-method
for accepted repairs or consolidation. Preserve independent failure modes and
verified replacement protection in the same candidate; a green count is no oracle.
Use clean-code:readability-method only for readability with behavior preserved. Structural
refactors use abstraction diagnosis and concept/owner criteria; application
subtraction uses its separate canonical method when authorized.

Use project-protocol baseline and candidate checks. Preserve preexisting edits and
work belonging to other sessions. Implement incrementally, run meaningful local or
revision-correlated remote checks, then review the full consequence set: stale
documents/instructions, retired exports/config, tests that lost purpose and outputs
produced during work.

Use project-knowledge:instructions-method for instruction consequences when changing
architecture, test policy, commands, setup or instruction loading. Review applicable
root and nested instructions, canonical owners and generated copies using that
method's loading evidence and project-derived test policy. Apply accepted corrections
to the canonical source, regenerate derivatives and verify parity. Preserve decisions
and record unknown loading or required session reloads in the run, outside durable
instructions. Guide and README consequences use project-knowledge's own methods.

Review the candidate through senior-review:review-method using the code-review
variant and this run's output root, following the verify reference. Applicable
stack specialists join the same review selection, ledger and report; do not ask
the user to select another review plugin.

Integrate durable findings through project-knowledge and consolidate owned
experimental outputs through the consolidate reference. Update result.json with
delivered behavior, protection preserved, changed paths, exact checks and limits.
Account for suite audit coverage, instruction synchronization and loading evidence
when selected. A required runtime or loading check that could not run remains a gap.
A plan or generated diff without verification is not completed development.
