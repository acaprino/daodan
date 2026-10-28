---
description: 'Route any Office request from one intake into the requested document, deck, workbook, theme, verification or repair methods with shared content/design.'
---

<daodan_host_binding host="claude">
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

Claude binding: repository read, file discovery and content search use Read, Glob
and Grep; repository write and repository edit use Write and Edit; shell execution
uses Bash; network fetch uses WebFetch and network search uses WebSearch; a user
question uses AskUserQuestion. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

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

# start

<!-- Generated by the Daodan compiler for claude. Edit the kernel, never this file. -->

## Execution harness

Selected topology: **serial-isolated**. Use native Agent Teams when they are enabled in this session;
otherwise dispatch the same roles as isolated subagents. Both paths satisfy the same contract, and
which one answered changes nothing a reader of the report can observe.
Declared worker isolation: **required**.

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
  Independent reviewers never read peer results before their own delivery; no worker runs in the coordinator's context.
- Follow the dispatch plan below in phase order. A phase starts only after every phase it needs has
  closed, and a phase closes only when every worker it dispatched is recorded `delivered` or
  `failed`. A missing result is a recorded failure, never a silently shorter report.
- Dispatch only roles from this set, as the phase graph or loaded method requires: `office:content-strategist`, `office:document-designer`, `office:document-reviewer`, `office:presentation-designer`, `office:presentation-reviewer`
- A worker writes only what the coordinator assigned to it: its intermediate report and, when its
  task authorizes edits, its assigned files. It never reverts preexisting or foreign changes.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `run`: runs in the orchestrating context; produces `artifact:route-map`, `artifact:office-result`.

Role bindings:

- `office:content-strategist`: dispatch the installed `office:content-strategist` agent by its qualified identity.
- `office:document-designer`: dispatch the installed `office:document-designer` agent by its qualified identity.
- `office:document-reviewer`: dispatch the installed `office:document-reviewer` agent by its qualified identity.
- `office:presentation-designer`: dispatch the installed `office:presentation-designer` agent by its qualified identity.
- `office:presentation-reviewer`: dispatch the installed `office:presentation-reviewer` agent by its qualified identity.

The phase graph, the isolation and join policies and the record schemas are in
`contracts/start.workflow.toml`, which ships with this package.

## Method

Handle the Office request in: $ARGUMENTS

Load `office:intake` and `work-controller:work-record`, then follow intake's
`references/routing.md`: read/classify inputs, name destinations, record
phase-specific dependencies, settle inherited decisions and ask remaining
material choices once through the existing question contract.

Run routed methods here in order; do not start nested coordinators. This entry
declares every Office role and supplies their generated isolated bindings:

- `document`: `office:docx`; dispatch `office:content-strategist` for full/delta
  content, `office:document-designer` for scoped layout and
  `office:document-reviewer` for exact saved-render review.
- `presentation`: `office:pptx`; dispatch the same strategist when needed,
  `office:presentation-designer` and `office:presentation-reviewer`.
- `theme`: `office:design` and the requested reusable-template procedure, using
  the same declared format designers/reviewers for native proof and final review.
- `workbook`: `office:xlsx`; `verify` and `fix`: `office:integrity`.

For a DOCX/PPTX bundle prepare shared editorial data once and select one DESIGN.md
after `office:design`'s reviewed native proposals and v2 gallery; preserve one
content/design identity/revision and only requested projections. Finalize PPTX
display values and canonical binding after visual
selection, then validate/load the actual CONTENT.md/plan and DESIGN.md before
final composition. Proposal working bindings follow design's art-direction
contract. Reuse accepted records for the next format instead of repeating
strategy or selection. Layout and native review remain format-specific.

Only the operation's necessary phases run. Pass outputs forward, preserve
supplied files and separate candidates, and verify expected reports/coverage.
Missing capability blocks dependent delivery; a worker stop is not success.
Deliver each destination with its review/report, final recorded decisions and
checks that remain unavailable.
