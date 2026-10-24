---
name: review-quality-gates
description: >
  Verification panel, completeness critic, pipeline conventions and shared-context provenance rules for multi-reviewer consolidation.
  TRIGGER WHEN: running team-review (/daodan:review-branch) or code-review quality gates, or consolidating findings from parallel reviewers.
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

Shared obligations below; load step-specific procedures only when needed.

## Load map

| Step | Read inside this skill |
|---|---|
| Any review | this file: provenance, conventions, evidence, delivery |
| Shared-context preparation/dispatch | `references/context-sharing.md`: artifacts, anchors, metrics, raw mode |
| Consolidation | `references/verification-panel.md`: lenses, gating, cost guard, critic |
| Lens, critic or reviewer briefs | `references/panel-and-critic-prompts.md` |
| code-review dispatch and map injection | `references/code-review-agents.md` |
| code-review output and optional HTML | `references/code-review-output.md` |
| code-review `fix`/`commit` remediation | `references/code-review-fix-loop.md` |

Lens 0 uses declared `senior-review:premise-auditor`. Lenses 1-3, critic and
inline briefs use declared `project-protocol:isolated-worker` through the
consuming workflow's host harness, inheriting the session model.

## Shared-Context Provenance Rule

> **Evidence derived from a shared artifact cannot independently corroborate the claims contained in that same artifact. N reviewers agreeing on a premise they were all given is one observation, not N.**

1. Consuming a Codebase Map or interconnect claim does not verify it. Re-derive
   its support from evidence before basing a finding on it; preserve prior exposure.
2. Agreement on a shared premise is an **echo**, raising neither confidence nor
   severity. Consolidation labels it accordingly.
3. No metric rewards agreement with shared context. Map utilization measures
   consumption, never quality.

## Reviewer Pipeline Conventions

Discovery reviewers read `references/reviewer-common.md` for evidence, coverage,
knowledge accounting and compact delivery; roles own domain methods. Provider
reviewers receive these conventions through their briefs:

- **Scope budget**: complete assigned checks or name unchecked scope and cause.
  Read count and absence of findings never prove irrelevance or completion.
- **No-findings protocol**: "examined X, Y, Z: no issues" is valid Phase 3 input.
- **Cross-Reviewer Notes**: route other dimensions' observations through
  `## Cross-Reviewer Notes` in Phase 3.
- **Interconnect anchor citation**: cite applicable anchors. Findings that cite map anchors feed the map utilization rate, an operational measure of map consumption, not a quality signal.
  Quality metrics: `references/context-sharing.md`, `### Metrics`.

## Evidence Classes

Label each finding's decisive evidence, strongest first:

- **`reproduced`**: test/run fails on candidate and passes on base (reverse for a
  fix); record command, scratch path and both outcomes.
- **`tool-reported`**: verbatim evidence-pack tool result; see
  `references/candidate-grounding.md` in `senior-review:review-preparation`.
- **`measured`**: harness, simulation or real logs/metrics; state method. Keep
  temporary harnesses outside the work tree, removing them under the Delivery Gate.
- **`derived`**: inferred from code, not execution; default for unlabeled evidence.

1. A `derived` number alone cannot justify **Critical** severity: measure it or cap at High.
2. Neither a derived number nor "bounded"/"low traffic" alone justifies accepting
   a finding. Establish **what the user or operator sees, and when**.
   "None (silent)" escalates consequential harm; it never mitigates it.
3. Lens 2 checks rates/costs against actual deduplication, caps and phase transitions.
4. Lens 1 may reproduce only when its brief grants a run-owned disposable workspace
   and names the runner and scratch path. Write a minimal test there, run base and
   candidate, record both outcomes; remove it unless adopted as regression protection.
   Failure to reproduce is counterevidence. Without the grant, read and reason;
   retain the reviewer's evidence class.

## Delivery Gate

1. **Every reviewer delivers or declares:** before consolidation, collect each
   spawned reviewer's findings file or explicit no-findings report. Nudge an idle
   reviewer once. Continued silence: salvage partial output as
   `[undelivered -- collected by orchestrator]`, marking the dimension **degraded**
   or **not delivered** when empty, never clean. Missing required deliveries/checks
   remain incomplete regardless of flags.
2. **The work tree is left as found:** compare complete pre-review and final
   workspace snapshots. New status entries do not prove ownership. Workers record
   created files, original absence and final hashes in an explicit manifest;
   preserve/report foreign or changed files. Keep probes in the owned run root.
   Before removing an unchanged owned temporary artifact, preserve its conditions,
   commands, outcomes, errors and limitations in the native report; verify remaining
   evidence links resolve. Preserve unresolved evidence and resume data. Broad
   cleanup or Git clean is forbidden. Return manifest and report; persistent
   retention belongs to the caller's consolidate path, never status-based deletion.
