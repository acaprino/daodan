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

# Specialist review conventions

Load once per assignment, including compositions. Roles supply domain checks;
briefs supply target, snapshot, scope, permissions and delivery. Providers receive
these conventions in the brief. Reuse existing contracts and native report formats.

## Establish evidence

- Confirm candidate, required inputs and review basis. Changesets compare base and
  candidate; distinguish introduced, exposed and preexisting defects under the
  caller's policy. Content audits admit evidenced preexisting defects in scope.
  Judge plans/specs/documents against their claims; absent implementation alone
  is not a plan defect.
- Keep conclusions within the assigned perimeter. Read relevant requirements,
  effective configuration, callers, consumers and guards within admitted read/impact
  scope. Request missing scope or inputs; an unknown prerequisite remains a gap,
  never proof of inapplicability.
- Preserve source and configuration; write only the assigned report. Run checks
  only with permission in the assigned disposable environment. Record actual
  command, candidate and outcome. A tool/input/delivery failure is a review gap,
  not evidence of a product defect.
- Maps, comments, names and searches supply leads. Read source establishing the
  premise; seek guards, alternate paths and configurations that refute it. Check
  multiplicity, ownership and reachable state transitions where relevant.
  Do not consume peer findings before independent delivery. Cite used map anchors
  and preserve causal provenance.
- Establish a reachable trigger, violated requirement and observable consequence.
  A pattern or missing preferred technique alone proves nothing. Calibrate severity
  to impact; invent no percentages, loads, timings, costs, universal thresholds
  or finding quotas. Route overlaps by the violated mechanism or contract.

## Context economy and coverage

Search narrowly; expand reading as evidence requires. Load applicable references
and assigned knowledge through exact catalog bindings, once per distinct binding.
Knowledge is read-only input, not permission to execute workflows. Missing/stale
assigned knowledge fails coverage. Return existing `knowledge_usage` records with
selection, worker/scope, body/reference hashes, loaded/failed status and application;
use `[]` when unassigned. Shared worker identity does not merge assignments/scopes.

Finish assigned checks or name unchecked scope and cause. Read counts, budget
exhaustion and absence of findings never prove completion. Preserve evidence in
one report; the coordinator routes concise cross-reviewer notes after independent
delivery. Static inspection and runtime exercise are distinct coverage facts.

## Deliver once

Use the native report and existing reviewer-result envelope: `dimension`,
`reviewer`, `status` (`delivered` or `failed`), `findings`, `gaps`,
`output_path`, `knowledge_usage`. Persist at the assigned path; return that path
and a short result. Without an assigned path, deliver inline.

Each finding supplies `file`, `line`, `evidence`, `severity`, numeric
`confidence` (0–100, supported by evidence), `premise`, `premise_provenance`,
`trigger`, `counterevidence_checked`, `evidence_class` and a concrete fix direction;
include `introduced_by_candidate` when comparing candidates. Confidence describes
support, not impact or measured probability; preserve native strength labels
separately. Provenance is `independent`, `shared-context` or `mixed` according to
premise origin, not citations alone. Evidence is `derived`, `tool-reported`,
`measured` or `reproduced`; source reading proves no execution. A derived number
alone cannot justify Critical severity.

Report examined scope, completed applicable checks and gaps compactly. A complete
no-findings result has `findings: []` and that coverage account; silence is missing
delivery. A missing required input or unfinished required check makes the assignment failed (`status: failed`); preserve
partial findings and name the missing evidence/check. The coordinator checks
coverage before acceptance. Apply the working discipline supplied in the required brief. These are agent obligations; only exercised gates
prove mechanical enforcement.
Generate no score, inventory, repeated source listing or action quota unless the
native report requires it.
