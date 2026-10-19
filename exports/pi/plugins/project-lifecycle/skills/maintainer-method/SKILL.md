---
name: maintainer-method
description: >
  Coordinate the complete Senior Maintainer rationalization campaign.
  TRIGGER WHEN: the user wants a whole project brought back into good shape through a coordinated multistage campaign, or runs /daodan:run-maintenance.
  DO NOT TRIGGER WHEN: an intake dossier is sufficient (use handover-method), or an individual diagnosis or change covers the request (use lifecycle-method).
---

> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/` and `prompts/`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

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

# Senior Maintainer

Lead the campaign; the user decides its scope, roadmap and outstanding product
choices. Read the complete campaign reference at
<plugin-root>/skills/maintainer-method/references/campaign.md before the
first stage. It is the canonical behavior; do not seek a runtime prompt in the
project's README or replace a specialist's method with that document.

## Resolve the request

Load project-protocol:project-protocol. Resolve the arguments and the user's
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
| output root | protocol default | Project-contained alternative selected with --out |

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
Also exclude .daodan/, .codebase-map/, .codebase-xray/, .team-review/, .repo-hygiene/ and every
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

Maintain is a campaign entry, not an additional operation in the project-protocol
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
| Baseline correctness and static context | senior-review:review-method, variant team-review; its method owns the codebase-map analyze step |
| Coherence and roadmap | project-lifecycle:lifecycle-method, operation assess |
| Evidenced product corrections | project-lifecycle:lifecycle-method, operation change |
| Approved rationalization | project-lifecycle:lifecycle-method, operation repair |
| Exact final candidate | project-lifecycle:lifecycle-method, operation verify |
| Conclusions and retained evidence | project-lifecycle:lifecycle-method, operation consolidate |

The lifecycle method's operation references and canonical domain methods retain
all their gates. Perform one lifecycle operation, close or interrupt it, then
return here before preparing another. The campaign never starts a command from
inside a lifecycle operation. When entering a
native owner entry requires a user transition, record it and provide the exact
entry/resume request. Do not claim the compiler's TOML invoke can execute it.

Use clean-code:readability-method with clean-code:clean-code-agent only for an
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
