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



## Existing analysis compatibility

Coordinators load `codebase-map:map-method` and apply `references/migration.md`
before root lookup or dispatch. Workers never migrate roots: use only its
`migrate_root.py resolve` for supplied bindings. Propagate returned paths.
Failed migration/resolution or a still-legacy `.codebase-xray` path blocks the
dependent operation; preserve archives and run IDs.

# Assess

Load the canonical methods before preparing inputs. Diagnosis does not modify
application files, test files or durable instructions. Run-owned reports and the
explicit Codebase Map run are the allowed audit outputs.

## Focus selection and inputs

| Focus | Dimensions | Native inputs and preparation |
|---|---|---|
| knowledge | instructions and documentation | instructions-method audit-only; project-knowledge inventory and documentation/README audit; authoritative intent, existing file plan, output paths |
| structure | cleanup and abstraction | cleanup-auditor scoped target; abstraction auditor codebase_path, mode, xray_path, scope, changed_files for diff, report_path, concept_index_path=none |
| tests | suite health | test-preparation determines runner/configuration/source mapping; test-suite-auditor receives paths, runner, layers, measurements and output path |
| artifacts | workspace | workspace-auditor profile full, explicit scope, output path; filesystem/Git evidence only |
| all | union above | no duplicate worker or second detection prompt |

Prepare selections cleanup, tests, structure, instructions and workspace with zero
or one binding each for the sidecar phases. A binding records role, native inputs,
run output path, expected deliverable and input hash. Empty selection means not
requested; selected workers that fail remain failed. Documentary audit is performed
through the knowledge method and accounted for in the same total worker budget.
Count documentation-engineer and guide-reviewer before dispatch. If the quick
budget cannot cover the requested union, show the selected priorities and remaining
dimensions; do not silently dispatch extra contexts or imply complete coverage.

For abstraction context, invoke codebase-map:analyze in this coordinator context
only when required by the requested scope. Bind the exact new or validated Codebase Map
run ID, source snapshot, depth and directory. Quick uses lite context and states
missing flows/semantics; deep can request full context. Diff mode receives actual
changed_files. The concept index is a lead, never proof; disable its writes for this
read-only assessment. An interrupted Codebase Map is not the active completed mirror.

Use the native auditor inputs and boundaries. Missing runner/config or no test
suite produces evidence and an authoring/configuration remedy, not quarantine.
Audit instructions explicitly in audit-only mode. Compare declared intention with
implementation and documents, retaining uncertain authority as a decision.

## Build the plan

Hold all selected deliveries before consolidation; failed workers produce gaps.
Use senior-review:review-consolidation's evidence and provenance rules, without
turning a coherence assessment into a correctness verdict.

Route native findings: docs/instructions/README to project-knowledge; test oracle,
suite configuration, authoring, quarantine or consolidation to testing; reversible
filesystem operations to repo-hygiene; confirmed application subtraction to the
application-cleanup-method; known semantic refactors to change with abstraction
audit before/after. Unknown design intent remains clarify with explicit alternatives.

For every action record dependencies, scope/snapshot, evidence, cost, method, owner
and gate. Cleanup requiring --commit is disclosed here; repair --fix leaves that
action open. Missing credentials/build access need a runnable alternative or an
explicit non-executable action. They never become a green check.

Write plan.json, native reports and result.json under this run. Show executable
actions separately from design decisions, failed dimensions and uncovered scope.
A no-findings report includes what was examined, not a blanket project certificate.
