<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
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

# Assess

Load the canonical methods before preparing inputs. Diagnosis does not modify
application files, test files or durable instructions. Run-owned reports and the
explicit Codebase Map run are the allowed audit outputs.

## Focus selection and inputs

| Focus | Dimensions | Native inputs and preparation |
|---|---|---|
| knowledge | instructions and documentation | instructions-method audit-only; project-knowledge inventory and documentation/README audit; authoritative intent, existing file plan, output paths |
| structure | cleanup and abstraction | Dispatch `senior-review:cleanup-auditor` and `abstraction-architect:abstraction-architect-agent` with codebase_path, mode, xray_path, scope, changed_files for diff, report_path, concept_index_path=none |
| tests | suite health | Load skill `testing:test-preparation`; dispatch `testing:test-suite-auditor` with paths, runner, layers, measurements and output path |
| artifacts | workspace | Dispatch `repo-hygiene:workspace-auditor` with profile full, explicit scope and output path; filesystem/Git evidence only |
| stack | each stack the snapshot shows | load each owner's audit skill on the whole project: `python-development:python-audit-method`; `references/audit.md` of `react-development:react-best-practices`, `typescript-development:type-safety-rules`, `platform-engineering:platform-engineering`, and of `dependency-audit:dependency-audit` when manifests exist |
| all | union above | no duplicate worker or second detection prompt |

Prepare selections cleanup, tests, structure, instructions and workspace with zero
or one binding each for the sidecar phases. A binding records role, native inputs,
run output path, expected deliverable and input hash. Empty selection means not
requested; selected workers that fail remain failed. Documentary audit is performed
through the knowledge method and accounted for in the same total worker budget.
Count documentation-engineer and guide-reviewer before dispatch. If the quick
budget cannot cover the requested union, show the selected priorities and remaining
dimensions; do not silently dispatch extra contexts or imply complete coverage.

For abstraction context, execute the canonical preflight and delivery/publication
steps of the analyze entry of codebase-map:map-method only when required by the
requested scope.
Dispatch codebase-map:map-analyst in one isolated context through the consuming
workflow's declared host harness. Bind the exact new or validated Codebase Map
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
and gate. Cleanup that needs a `commit` grant is disclosed here; a `fix` grant
alone leaves that action open. Missing credentials/build access need a runnable alternative or an
explicit non-executable action. They never become a green check.

Write plan.json, native reports and result.json under this run. Show executable
actions separately from design decisions, failed dimensions and uncovered scope.
A no-findings report includes what was examined, not a blanket project certificate.
