---
name: review-quality-gates
description: >
  Verification panel, completeness critic, pipeline conventions and shared-context provenance rules for multi-reviewer consolidation.
  TRIGGER WHEN: running /senior-review:team-review or /senior-review:code-review quality gates, or consolidating findings from parallel reviewers.
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
before the first phase, and stop with that command when a required one is off.
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

## Existing analysis compatibility

Coordinators load `codebase-map:map-method` and apply `references/migration.md`
before root lookup or dispatch. Workers never migrate roots: use only its
`migrate_root.py resolve` for supplied bindings. Propagate returned paths.
Failed migration/resolution or a still-legacy `.codebase-xray` path blocks the
dependent operation; preserve archives and run IDs.

# Review Quality Gates

Gates and consolidation rules shared by every review variant. This core holds
what every consumer needs; the two procedures that only one step uses are units
loaded by that step.

## Load map

| Step | Read inside this skill |
|---|---|
| Any review, any role | this file: provenance rule, reviewer conventions, evidence classes, delivery gate |
| Preparing or dispatching reviewers with shared context | `references/context-sharing.md`: context artifacts, anchor routing per dimension, metrics, raw mode |
| Consolidation | `references/verification-panel.md`: the four lenses, their gating, the cost guard and the completeness critic |
| Writing a lens, critic or reviewer brief | `references/panel-and-critic-prompts.md` |
| `/code-review` agent dispatch templates and Codebase Map context injection | `references/code-review-agents.md` |
| `/code-review` native output and optional HTML view | `references/code-review-output.md` |
| `/code-review --fix` and `--commit` remediation loop | `references/code-review-fix-loop.md` |

Lens 0 uses the declared `senior-review:premise-auditor` binding. Lenses 1 to 3,
the critic and any inline brief use only the declared
`project-protocol:isolated-worker` binding through the consuming workflow's host
harness, inheriting the session model.

## Shared-Context Provenance Rule

> **Evidence derived from a shared artifact cannot independently corroborate the claims contained in that same artifact. N reviewers agreeing on a premise they were all given is one observation, not N.**

Three consequences bind every gate below:
1. A reviewer that consumed a claim from the Codebase Map output or the interconnect map has not verified that claim. It must re-derive the claim independently before standing a finding on it.
2. Concordance between reviewers who share a premise is an **echo**. It raises no confidence and no severity. Consolidation reports it as such.
3. No metric may reward agreement with a shared artifact. Utilization of the map is an operational number, never a quality signal.

## Reviewer Pipeline Conventions

Every Phase 2 reviewer carries four rules in its system prompt:
- **Scope budget**: stop after ~15 file reads without a finding and return a "scope-off-topic" report.
- **No-findings protocol**: "examined X, Y, Z: no issues" is a valid Phase 3 input, not a failure.
- **Cross-Reviewer Notes**: observations belonging to other dimensions go in `## Cross-Reviewer Notes` for Phase 3 routing.
- **Interconnect anchor citation**: reviewers cite map anchors when applicable. Findings that cite map anchors feed the map utilization rate, an operational measure of map consumption, not a quality signal. The quality signals that matter are in `references/context-sharing.md`, section `### Metrics`.

## Evidence Classes

Every finding labels how its decisive evidence was obtained, strongest first:
- **`reproduced`**: a test or run showed the defect, passing on the base and failing on the candidate, or the reverse for a fix (state the command and the scratch path).
- **`tool-reported`**: a tool in the evidence pack reported it verbatim (`references/candidate-grounding.md` in `senior-review:review-preparation`).
- **`measured`**: obtained from a harness, simulation or real logs/metrics (state method in one line; build any harness outside the work tree and delete afterwards).
- **`derived`**: computed by reading code (a hypothesis, not a fact; an unlabeled finding defaults to `derived`).

Consequences:
1. A `derived` number alone cannot justify **Critical** severity (measure it or cap at High).
2. A finding cannot be closed as acceptable ("bounded", "low traffic") on a `derived` number alone, nor without answering **what the user or operator sees, and when** ("None (silent)" is a severity escalator, never a mitigation).
3. Lens 2 actively checks whether claimed rates/costs survive actual control flow (deduplication, caps, phase transitions).
4. Lens 1 may reproduce. When the brief grants a disposable workspace owned by the run and names a test runner, the lens writes a minimal test at the scratch path the brief names, runs it on the base and on the candidate, records both outcomes, and removes the file unless the caller adopts it as regression protection. A reproduction that fails to show the defect is counterevidence, recorded as such. Without that grant, the lens reads and reasons, and the class stays as the reviewer declared it.

## Delivery Gate

1. **Every reviewer delivers or declares:** Consolidation does not start until every spawned reviewer has produced either its findings file or an explicit no-findings report. An idle reviewer receives one nudge; if still silent, salvage partial output as `[undelivered -- collected by orchestrator]` and mark the dimension **degraded** (or **not delivered** if empty), never clean.
2. **The work tree is left as found:** Compare the complete pre-review workspace snapshot with the final state. A new file in status is not proof the review owns it. Workers keep an explicit manifest of files they created, with original absence and final hashes; foreign or changed files are preserved and reported. Keep probes inside the owned run root. Before removing an unchanged owned temporary artifact, preserve its conditions, commands, outcomes, errors and limitations in the native report and verify every remaining evidence reference still resolves. Preserve unresolved evidence and resume data. Broad cleanup or Git clean is forbidden. Persistent run retention belongs to the caller's consolidate path; the review returns the owned manifest and report, rather than deleting arbitrary repository residue on status alone.
