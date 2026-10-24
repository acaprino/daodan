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

# Stack dimensions

Use candidate-grounding's basis, scope and evidence rules. Inspect the affected
package/configuration at the candidate snapshot; unrelated monorepo dependencies
do not activate dimensions. Resolve computed identities through these bindings:
one dispatch round and ledger, no extra roles or clean skips for unknown signals.

| Dimension ID | Automatic activation evidence | Role to dispatch |
|---|---|---|
| react | React in the relevant package and target includes JSX/TSX or affected React runtime | `react-development:react-performance-optimizer` |
| typescript | Relevant TypeScript configuration and target includes TS/TSX/type contracts | `typescript-development:type-safety-auditor` |
| platform | Roster evidence for browser/PWA storage, service workers, client security policy, mobile capabilities or Electron/Tauri shell integration | `platform-engineering:platform-reviewer` |
| python | Target includes `.py` or `.pyi` files, or the relevant package declares `pyproject.toml`, `setup.py`, `uv.lock` or `requirements*.txt` | `work-controller:isolated-worker`. Its brief says: load the `python-development:python-refactor-method` skill and load the `python-development:python-dead-code` skill in audit-only mode; read the Python tool results of the evidence pack (`references/candidate-grounding.md`); report what the tools cannot see (semantic misuse, behavior-changing complexity, idiom violations) and never restate a tool line |
| dependencies | The candidate changes a manifest or lockfile: `pyproject.toml`, `uv.lock`, `poetry.lock`, `requirements*.txt`, `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lock`, `Cargo.toml`, `Cargo.lock`, `go.mod`, `go.sum`, `Gemfile.lock`, `composer.lock`, `pom.xml`, `build.gradle*`, `*.csproj` | `work-controller:isolated-worker`. Its brief says: load the `dependency-audit:dependency-audit` skill read-only; run the ecosystem's own audit, outdated and license tooling on the candidate; report `TOOL-REPORTED`, `INFERRED` and `UNKNOWN` facts, never a remediation |

Python/dependencies bind their methods through the declared isolated worker.
Carry skill identities, audit-only mode, evidence-pack paths and the report
path in its brief, as for other inline lenses.

Select each dimension once. False signals need code-based skip reasons;
unreadable/ambiguous signals remain gaps. Required providers supply roles
regardless of selection. An unavailable selected role is a failed delivery,
never a skip or generic substitute.

Composition uses the existing catalog and `required_specialists`
with scope/evidence. Merge identical member/scope obligations only. Requirements
and sources identify canonical specialists; unknown applicability, missing
prerequisites and graph omissions remain gaps. Light permits one discovery;
obligations that cannot fit stay incomplete and require branch review.

Record explicit specialist requests and compare them with the computed roster;
requests cannot remove its floor or bypass allowed dispatch. Normalize legacy
`react-perf`/`react-performance` to `react` and `ts-safety`/`type-safety` to
`typescript`. General performance belongs to `senior-review:performance-auditor`,
including query and algorithm cost in a React application. React's optimizer
retains component/render work; both may run when each is selected. Platform
reviews client capabilities and cross-platform behavior. Service operation,
deployment and recovery belong to `senior-review:operability-auditor`.

--no-context removes shared context from these workers
as it does from other reviewers; it does not remove the dimensions. --fast can reduce optional verification work, never the required roster or gates.

The canonical roles retain their own knowledge, analysis method and native output.
Before dispatch, load review-consolidation's `references/stack-findings.md` inside
that skill. Include its native review field requirements and severity mapping in
the brief, alongside the role's own report format. Preserve the original report;
the existing evidenced-finding envelope carries the fields required by this review.
Supply the prepared target, diff, intent, project instructions, run identity,
snapshot and assigned intermediate report path. Add the variant's shared scope
and premise-provenance instructions from review-method and review-quality-gates;
include context paths only when context is enabled. Quantitative performance
claims need the evidence required by review-quality-gates. Missing runtime
measurements remain gaps, not invented results.

Include these members in the validated jobs with the other selected dimensions.
Dispatch each job once in its isolated context, preserving each member's native method.
Do not run their standalone workflows, repeat preparation or publish another
report. Consolidation waits for every selected reviewer to deliver or fail, and
preserves source role, severity, evidence and premise provenance in the same native
finding set. Independent reviewers do not receive peer findings before delivery.
