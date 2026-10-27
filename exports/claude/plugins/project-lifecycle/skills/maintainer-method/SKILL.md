---
name: maintainer-method
description: >
  Coordinate the complete Senior Maintainer rationalization campaign.
  TRIGGER WHEN: the user wants a whole project brought back into good shape through a coordinated multistage campaign, or runs /daodan:run-maintenance.
  DO NOT TRIGGER WHEN: an intake dossier is sufficient (use handover-method), or an individual diagnosis or change covers the request (use project-delivery:delivery-method).
---

<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
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

# Senior Maintainer

Lead the campaign; the user decides its scope, roadmap and outstanding product
choices. Read the complete campaign reference at
${CLAUDE_PLUGIN_ROOT}/skills/maintainer-method/references/campaign.md before the
first stage. It is the canonical behavior; do not seek a runtime prompt in the
project's README or replace a specialist's method with that document.

## Resolve the request

Load skill `work-controller:work-record`. Resolve the arguments and the user's
existing instructions into these settings:

| Setting | Default | Meaning |
|---|---|---|
| target | whole project | Project-relative path, module or feature, resolved to paths |
| exclusions | none supplied | User exclusions plus named forbidden inputs and tool output |
| focus | all | all, knowledge, structure, tests or artifacts |
| depth | deep | quick, standard or deep |
| authorization | dry-run | dry-run, fix or commit, restricted to recorded scope |
| pace | guided | guided or autonomous; never a specialist workflow flag |
| resume | none | Exact stage run IDs supplied through repeated --resume RUN_ID |
| handover | none | Exact assess run supplied through --from-handover RUN_ID |

Explicit current user authorization wins over defaults. Keep conflicting mode
flags as a clarification, never silently choose the broader grant. Read project
instructions and resolve the target from a cheap orientation before expensive
analysis. Name dimensions a narrower focus or depth leaves unexamined. Pass only
supported operation arguments to each owner; never forward --pace, --resume or
--from-handover as an invented lifecycle flag.

Before a helper takes any snapshot, inventory forbidden inputs by names only
and exclude their concrete project-relative paths. Use codebase-map:map-method's
forbidden-file rule without reading credential contents. The protocol hashes
directory inputs: a prohibition on quoting secrets does not prevent that read.
Also exclude .daodan/, .codebase-map/, .team-review/, .repo-hygiene/ and every
other report root this campaign writes. Declare dependency/build exclusions that
are outside the intended scope. Scope exclusions are concrete paths, not globs.

An optional handover must identify /daodan:onboard-project in its request.json, or
the former handover command for a dossier written before marketplace 38.0.0.
Validate its exact assess run and result with --current before reusing it, compare
scope and supplied evidence with this target, and read its limitations. Changed
inputs require fresh evidence. Historical observations may be attributed as such;
they are never a current correctness verdict. The dossier's work suggestions and
prior read-only authority grant no mutation acceptance to this campaign.

## Campaign state and transitions

Maintain is a campaign entry, not an additional operation in the work-controller
helper. Never initialize operation maintain or run all stages inside one repair
record. Use the supported operations assess, change, repair, verify and consolidate
for their own stage objectives. The baseline team review retains senior-review's
own native run, schemas, preparation and delivery ledger.

Cheap orientation may use an owned assess run with objective campaign orientation,
scope identified from the request, no broad auditor dispatch and a brief as its
native report. It records checkpoint 1 and closes before the baseline review.
If checkpoint 1 changes the target, preserve that completed orientation as
historical evidence and create the next run with the approved scope. Do not rebind
an existing scope. Before a run exists, a waiting brief includes the full resolved
request and exact next entry so that a fresh session can reconstruct it.

Inside every active lifecycle run save campaign-request.json and campaign.json.
The request records original user text and native arguments, resolved settings,
intention/authorization sources and the canonical method/reference fingerprints.
The chain records this run's stage, exact earlier stage/run identities, Codebase Map run
binding, scope and snapshot references, accepted decisions with their scope,
next entry and interruption reason. It indexes native records; it never replaces
their work.json, results, checks or approval evidence. Save it before closing the
run. Carry a new copy forward into the next active run; never mutate a completed
record or its evidentiary reports.

Read the request and chain at every batch boundary, handoff, context loss and
resume. Resume only an explicitly named in-progress stage through the protocol
helper with identical authorizations and the recorded current candidate. For a
completed stage validate its historical result and prepare the recorded next
entry in a new run instead of reopening it. Inspect native review and Codebase Map runs
through their owners. A changed candidate, scope or authorization requires a new
run with the preserved prior evidence, not a guessed latest run.

## Canonical stage owners

The campaign's declared worker union supports method composition. Select only
what the active owner requires. Independent reviewers receive their own inputs
and no peer findings. Keep that owner's full preparation, phase barriers, native
contracts and exclusive final-report owner. Do not duplicate its scheduling graph
in the campaign or replace a missing role with another worker.

| Stage | Method to perform in the coordinator context |
|---|---|
| Baseline correctness and static context | Load skill `senior-review:review-method`, variant team-review; its method owns the codebase-map analyze step |
| Coherence and roadmap | Load skill `project-lifecycle:assess-method` |
| Evidenced product corrections | Load skill `project-delivery:delivery-method`, operation change |
| Approved rationalization | Load skill `project-delivery:delivery-method`, operation repair |
| Exact final candidate | Load skill `project-delivery:delivery-method`, operation verify |
| Conclusions and retained evidence | Load skill `project-delivery:delivery-method`, operation consolidate |

The lifecycle method's operation references and canonical domain methods retain
all their gates. Perform one lifecycle operation, close or interrupt it, then
return here before preparing another. The campaign never starts a command from
inside a lifecycle operation. When entering a
native owner entry requires a user transition, record it and provide the exact
entry/resume request. Do not claim the compiler's TOML invoke can execute it.

Load skill `clean-code:readability-method` with clean-code:clean-code-agent only for an
approved readability batch at a method boundary and with behavior preserved.
If the active owner's inventory cannot dispatch it, finish that operation first
and offer the standalone clean-code pass as the campaign reference specifies.
Composed inventory availability grants no independent mutation authorization.

## Checkpoints and completion

With guided pace, checkpoint 1 approves the brief before expensive analysis and
checkpoint 2 approves findings and the roadmap before any project mutation. Record
the accepted items exactly. Generic approval does not accept unnamed removal,
test retirement or quarantine; honor each owner's acceptance procedure. Autonomous
pace removes those two waits and preserves every owner-required decision and gate.
Dry-run closes at the roadmap and explicitly reports the unexecuted maintenance
stages. It is an assessment delivery, not completion of the full campaign.

Follow the reference's risk ordering, batch boundaries, recovery and retry rule.
Existing edits and other sessions' files remain protected. Each stage returns its
native reports and protocol result with checks on that stage's own candidate.
Historical validation uses validate --result without --current. Final verify
uses validate --current --result against the actual present project. Read the
evidence as well as validating record correspondence.

Missing selected deliveries, mandatory checks or accepted decisions keep the
affected action open. The final campaign report names complete or stopped, paths,
real checks, three distinct coverage facts, remaining decisions and the exact
resume line. It refers to native stage results and never invents a new protocol
operation, an installed-host runtime probe or a blanket correctness certificate.
