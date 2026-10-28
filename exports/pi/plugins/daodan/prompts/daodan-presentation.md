---
description: 'Create, derive, revise, review or export an editable PowerPoint presentation through shared Office content/design, native DeckCraft and independent review.'
---

<daodan_host_binding host="pi">
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

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi has no network tool: network fetch and network search run as shell
commands, and a user question is asked in the reply while the run waits for the
answer.
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

# presentation

<!-- Generated by the Daodan compiler for pi. Edit the kernel, never this file. -->

## Execution harness

Selected topology: **serial-isolated**, with role delivery by **inline-prompt**, and declared
isolation **required**. Dispatch one worker per entry in the plan below with the `subagent`
tool supplied by the `pi-subagents` package, each in its own context. Role delivery here is
`inline-prompt`: paste that role's Markdown body into the dispatch prompt verbatim, because the
worker must receive the whole role rather than a summary of it.

Pi's core ships no subagent tool. Apply the availability check when the selected task
requires a dispatched worker. If the method explicitly permits a worker-free path
(for example, read-only inspection or a narrow edit), record why no worker is needed
and continue that path without this companion. Do not waive a required worker.
If a worker is needed and no subagent tool is available, the declared isolation
above decides what happens, and the two cases are not interchangeable:

- **`required`**: stop the dependent dispatch, and tell the user to run `pi install npm:pi-subagents`. Running the phases
  serially in this one context is the loss of isolation rather than a lesser form of it, so a
  report produced that way would claim a contract it did not meet.
- **`shared`**: run the phases in order in this context, and say in the report that no worker was
  isolated.

Coordinator completion ownership: keep the method's owned run and delivery ledger,
including each expected worker, attempt, report path and required check evidence.
Validate report artifacts before recording delivered. An empty final message or
worker stop remains missing delivery: inspect or resume when permitted, otherwise
record failed with the uncovered scope. Follow the declared join and phase gates;
a recorded failure is accounted for, never converted into a successful delivery.
Continue authorized work and recovery until the requested result and its checks
exist or a concrete blocker is recorded. Preserve the exclusive final report owner
and the ledger schema; a tool exit or a promise cannot satisfy completion.

Harness obligations, none of them optional:

- Every dispatched worker runs in its own context and reads only coordinator-declared inputs.
  Independent reviewers never read peer results before their own delivery.
- Follow the dispatch plan below in phase order. A phase starts only after every phase it needs has
  closed, and a phase closes only when every worker it dispatched is recorded `delivered` or
  `failed`. A worker reports delivered or failed in its final message; there is no shared task
  list, so the coordinator keeps that record itself.
- Dispatch only roles from this set, as the phase graph or loaded method requires: `office:content-strategist`, `office:presentation-designer`, `office:presentation-reviewer`
- A worker writes only what the coordinator assigned to it: its intermediate report and, when its
  task authorizes edits, its assigned files. It never reverts preexisting or foreign changes.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `run`: runs in the orchestrating context; produces `artifact:presentation-result`, `artifact:presentation-review`.

Role body bindings (load the complete body only for the selected worker):

- `office:content-strategist`: read `contracts/dispatch/office/content-strategist.md` inside this package and pass its complete role body verbatim.
- `office:presentation-designer`: read `contracts/dispatch/office/presentation-designer.md` inside this package and pass its complete role body verbatim.
- `office:presentation-reviewer`: read `contracts/dispatch/office/presentation-reviewer.md` inside this package and pass its complete role body verbatim.

The phase graph and record-schema references are in `contracts/presentation.workflow.toml`.

## Method

Handle the presentation task requested in: $ARGUMENTS

Load `office:intake` first, then follow `office:pptx` for its operation matrix,
shared-record finalization, native object/image contracts and specialist delivery.
Inspect supplied files and settle inherited decisions/dependencies once.

Full/delta content uses `office:content` and declared `office:content-strategist`;
restyle/edit/review/export does not reopen global content. Reuse a shared bundle
delivery. `office:design` owns the new-look Taste input/output contract, reviewed
native proposals, v2 gallery and explicit DESIGN.md selection. Then finalize the
existing plan's display direction from
the selected theme, recompute its canonical binding and freeze/validate CONTENT.md
with that actual plan before native pattern/capacity validation. This derived
binding changes no claims or content revision; editorial changes return to content.

For final construction, dispatch declared isolated `office:presentation-designer`
in `final` mode for scoped composition and `office:presentation-reviewer` in
`final` mode for exact saved-render review. Load only their
targeted contracts in workers; a skill load is not a worker dispatch. The
coordinator alone writes native files through `office:deckcraft` and owns image
calls, candidate identity and repairs. Separate POTX is optional unless requested.
Preserve sources, round trips, approved cuts, coverage, native editability,
font/embedding order and independent target-application evidence. Narrow edits
retain the look; read-only work never writes to the source.

Inspect workbook sources through `office:xlsx`, Word through `office:docx`, and
preserve source conditions and uncertainty. Continue authorized corrections;
missing runtime, isolation, image or render evidence blocks only its dependent
delivery and remains explicit. A stopped worker is not a delivery.

Deliver the requested editable PPTX, findings or export with a concise review:
exact identity, inspected slides, native preservation/editability, verdict and
limits. Printing means a printable PDF unless a real printer action is requested.
