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

# Project run report view

Only the coordinator loads this reference when HTML is requested or navigation
and comparison materially help the final report. Workers deliver their native
reports. Load the `report-rendering:report-renderer` skill by its registered identity and
resolve the helper from that installed provider.

## Source and ownership

Use the reviewed `handover.md`, the final `campaign-final.md`, or the operation's
completed human-readable Markdown report in its exact owned run. When an
operation has no such report, persist its existing final summary once as
`run-summary.md` inside the run. Derive it from the native deliveries and actual
run/result records, linking details rather than copying specialist reports.
The JSON envelope and stage records retain their authority; never pass JSON to
the Markdown renderer or infer completion from a summary.

Preserve scope/snapshot bindings, finding provenance, accepted decisions,
outstanding actions, authorization, unavailable gates and the resume line.
Keep inventory, files read and runtime exercise separate. For a campaign, label
earlier stage checks historical and identify the final current verification.
Dry-run and stopped outcomes retain that status and their unexecuted work.
For handover, retain observed versus exercised commands and the absence of
maintenance authorization.

## Render and close

Set `$RUN_DIR` to the existing dedicated project-contained run directory,
`$REPORT_MD` to that final Markdown file and `$REPORT_HTML` to its same-stem
HTML path inside `$RUN_DIR`. The repository root, a shared directory and an
earlier stage's closed run are not output roots. Run:

```bash
python "<resolved-report-renderer-helper>" --input "$REPORT_MD" --output "$REPORT_HTML" --profile report --root "$RUN_DIR"
```

Follow the provider's verification and intentional-overwrite contract. Render
after native report review and before closing the owning run. Record Markdown
and HTML paths in that run's outputs, then validate its envelope and required
gates. An explicitly requested missing or failed HTML delivery keeps the run
open; preserve completed earlier stages and the available native report.

Navigation, filters and task checkboxes affect only the local view. They neither
approve a roadmap nor change deliveries, gate results, dispositions or run state.
The provider needs no browser for structural verification. Rendering adds no
product-runtime coverage, instruction activation proof or token-saving claim.
