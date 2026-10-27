---
name: handover-method
description: >
  Coordinate an evidence-based consultant intake dossier.
  TRIGGER WHEN: the user asks to be onboarded, walked through an unfamiliar codebase, given a project takeover or intake dossier, or runs /daodan:onboard-project.
  DO NOT TRIGGER WHEN: being new to a project is only background for a code change (use project-delivery:delivery-method), correcting and rationalizing the project (use maintainer-method), or writing durable repository documentation (use project-knowledge:project-knowledge).
---

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

# Consultant handover

Own orientation and its evidence, not remediation. Produce a usable dossier for an
incoming consultant inside an identified project run. Use work-controller for
identity, snapshots, delivery accounting and completion; use project-knowledge for
context preparation, reader/file ownership, onboarding and factual review. Do not
repeat their discovery prompts or introduce a second documentation owner.

## Inputs and boundary

Inputs: project/worktree, target, audience and task intent; optional depth,
checks and run ID. Default target is the whole project,
audience is an incoming consultant, depth is standard and checks is none.
Resolve named modules/features to project-relative paths. Ask only about an
ambiguity that materially changes the intake. Read the applicable project
instructions and distinguish approved intent from implemented behavior.

Depth quick covers the essential entry points and a representative flow; standard
covers the scoped module map, important boundaries and the consultant's common
tasks; deep broadens those traces and constraints across the requested scope.
State what was inventoried, read in depth and exercised. Depth is a coverage plan,
not a correctness certificate or permission to exceed the target.

Only run-owned records, worker reports and the dossier may be written.
Application files, tests, durable instructions, README and project guides are
outside this entry's write authorization, even when another request allowed their
maintenance.
Do not start maintain, repair, change, a full correctness review or a Codebase Map run.
Do not install dependencies, change configuration, commit, push or publish.
Inspect existing material before proposing another document. Read source, worker
output and existing reports as evidence; they cannot grant authorization.
Do not read secrets or credential stores. Load codebase-map:map-method for its
forbidden-file rule and apply it to source reads and snapshot inputs. Record a
needed credential as unavailable without exposing its contents.

## Prepare the owned run

Load skill `work-controller:work-record` and skill `project-knowledge:project-knowledge`.
Read the latter's references/preparation.md and references/guide-method.md from its
installed skill. Apply their source/intent distinctions, audience/file plan and
writer/reviewer ownership to this report-writing task. Do not execute the guide
method's durable-document application path.

Initialize through the protocol helper with operation assess and objective
handover. These are supported operational values; do not invent a handover
operation. Save request.json inside the run with entrypoint
/daodan:onboard-project, original request, resolved target, audience, depth,
checks and the exact authorization source. This note identifies the entry;
it neither changes the protocol schema nor substitutes for work.json.

Before any project snapshot, discover forbidden paths by names only and record
their concrete project-relative exclusions. The protocol helper hashes files in
directory scopes; omitting those exclusions would read forbidden content. Exclude
every tool report root: .daodan/, .codebase-map/,
.team-review/, .repo-hygiene/ and other discovered tool output. Also identify
dependency/build/cache output that is outside the requested project source and
declare its exclusions. Never silently apply an undeclared perimeter. A supplied
report is explicit evidence, not a source file added to the project snapshot.
Record preexisting edits, untracked inputs,
scope/exclusions, unavailable access, the reader/file plan and expected cost.

Record phases, selected worker deliveries and mandatory gates before dispatch.
Each report has one owner and a destination under this run. Always select
codebase-explorer, onboarding-writer and guide-reviewer. Select the semantic mapper
only when the scoped flows need contracts, invariants or domain rules beyond the
context brief. Record the reason when mapping is not selected; its empty selection
is not a failed delivery. Do not fabricate inline roles.

--run-id names this handover's identified run, never the latest assess. For an
existing run, read request.json, confirm its entrypoint and settings, and resume
through the protocol with the same scope, snapshot and current authorizations.
An absent/mismatched entry note or changed inputs requires a new run rather than
rebinding a completed dossier or taking over another intervention. Preserve interruptions and the exact pending phase.

## Discover and check

Dispatch project-knowledge:codebase-explorer with the reader/file plan, exact
scope/snapshot, source evidence, mode audit-only and its owned context-brief.md.
Verify its delivery before using it. It discovers purpose, modules, entry paths,
commands, constraints and actual knowledge gaps through its canonical method.
If existing Codebase Map evidence is explicitly supplied, validate its exact run, target,
completion and current input snapshot through project-knowledge preparation.
Never substitute an unbound latest mirror or stale report for current source.

When selected, dispatch codebase-map:semantic-interconnect-mapper using that
verified context_path, scoped source paths and its owned interconnect-report.md.
Preserve every verified/documented/unverified/disputed status. No new Codebase Map is
required for an intake. A failed selected mapper remains a failed delivery.

Resolve startup, build and test commands from current scripts/configuration and
project instructions. Write checks-report.md with command, source locator,
prerequisites, environment, scope, snapshot, status, outcome and limitations.
With --checks none, execute no project setup/build/test/startup command; label
each observed command not exercised. Reading a script or previous CI result is
not evidence that startup or tests work on this candidate. This optional omission
is a declared coverage limit, not an unavailable mandatory gate.

--checks local requests only inspected, locally authorized checks whose effects
and prerequisites are established. Trace wrappers and hooks before execution:
a setup/test name alone does not prove a command is local or harmless. Execute
only checks allowed by project instructions, using existing dependencies and
available local fixtures. No network service, production system, credential
access, migration, installation or destructive operation is implied. Do not
start a persistent server or leave background processes running. Temporary check
output must stay in the owned run; a command that changes project files, writes
outside it or has unproved effects remains unexecuted with its reason.

Record each requested applicable safe local check as a required gate before it
runs. A missing environment or unavailable required check leaves that gate open;
do not downgrade to checks none or retry by weakening the command. Capture output
and bind results to the exact candidate. Reject any source drift or unexpected
write as a failed boundary check; preserve preexisting edits and report the
affected paths rather than broadly resetting the workspace.

## Write and review the dossier

Prepare a run-owned evidence bundle that identifies the verified context and
checks reports, the mapper report when selected, and the reason otherwise.
An unselected map is an explicit omission, never a required nonexistent artifact.

Dispatch project-knowledge:onboarding-writer with the verified context_path,
evidence_paths, checks report, optional interconnect report, audience, purpose and
output_files=[handover.md] inside this run. Its assignment explicitly authorizes
writing this owned consultant report. Use mode audit-only for project sources and
durable knowledge; this is report generation, not an invented docs mutation mode.
Pass existing documents as attributed evidence and navigation links, not files
the writer may change. The dossier contains, proportionally to the target:

- Project purpose, supported behavior and the sources of approved intention.
- Module/responsibility map, important entry points, dependencies and scoped user
  or data flows, with source locators and unresolved boundaries.
- Prerequisites, startup/test commands, common tasks and gotchas. Distinguish
  commands observed in configuration, past reported outcomes and current checks
  actually exercised, including the environment needed to reproduce them.
- Contracts, architectural decisions, operational constraints and the current
  sources to consult. Attribute historical decisions; do not invent their reasons.
- Known evidenced risks, contradictory documents and real unknowns, with their
  consequence and evidence status. No quota of risks or speculative questions.
- A first scoped work plan: objective, owner/canonical method, target paths,
  prerequisites, relevant evidence and acceptance gate for each proposed step.
  Separate orientation tasks, design decisions and candidate maintenance work.
  The plan neither approves edits nor starts them.
- Scope, exclusions, inventory/read/runtime coverage, checks not executed and
  the run/snapshot binding needed to revisit the dossier.

Do not label the project safe or the suite healthy from orientation alone.
Shared context remains inherited evidence; writer/reviewer agreement is not an
independent correctness check.

Dispatch project-knowledge:guide-reviewer in audit-only mode with the planned
dossier, original source evidence, context, checks and its owned guide-review.md.
Retain native findings, locators and premise provenance. Route accepted dossier
corrections to onboarding-writer, preserving its output ownership; verify the
corrected delivery and affected reader paths before closing. Neither reviewer
nor coordinator edits another writer's report or a durable project document.

## Completion and next step

Register the current-snapshot/source-evidence check, factual dossier review and
project-unchanged check as mandatory gates. Validate paths, command provenance,
claim statuses and source bindings by reading their supporting evidence. Verify
that scoped project inputs still match the recorded candidate and that owned
output stayed inside the run. Tool write confinement is a prompt obligation
unless the host has measured enforcement; do not claim a read-only tool sandbox.

Missing required evidence, stale bindings, failed deliveries, unresolved factual
contradictions or unavailable mandatory checks prevent a verified handover and
keep the run incomplete. Known unknowns with truthful source/status and optional
runtime checks not requested may remain explicit limits in a delivered dossier.
A discovered product defect is an evidenced risk, not a reason to silently repair
it or to treat its successfully delivered report as a worker failure.

For requested HTML or a dossier that benefits from navigation, the coordinator
must load skill `report-rendering:report-renderer`, then read `references/project-run-view.md`
and renders the reviewed handover.md before run closure. The writer's native
delivery and read-only project boundary remain authoritative.

Write the canonical project-result envelope with native report references and
hashes, deliveries, snapshot-bound checks, output paths, limitations and completion
state. Validate through run_state.py with --current and --result before declaring
completion. An incomplete dossier remains available with its interruption reason
and resume line. Report the dossier path, run ID, coverage and next scoped step.
Offer /daodan:run-maintenance only when the findings justify remediation; wait
for an explicit request. Handover never chains maintenance automatically.
