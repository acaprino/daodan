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

Use the resolved target, relevant package configuration and exact candidate
snapshot. Inspect the affected package in a monorepo; unrelated root dependencies
are not an activation signal. Add these bindings to the native reviewer selection
alongside the other dimensions. There is one dispatch round and one delivery ledger.

| Dimension ID | Automatic activation evidence | Canonical role |
|---|---|---|
| react | React in the relevant package and target includes JSX/TSX or affected React runtime | `react-development:react-performance-optimizer` |
| typescript | Relevant TypeScript configuration and target includes TS/TSX/type contracts | `typescript-development:type-safety-auditor` |
| platform | At least two verified frontend, backend, API-route, multiple-service or desktop-shell integration signals relevant to the target | `platform-engineering:platform-reviewer` |
| python | Target includes `.py` or `.pyi` files, or the relevant package declares `pyproject.toml`, `setup.py`, `uv.lock` or `requirements*.txt` | `project-protocol:isolated-worker`. Its brief says: load the `python-development:python-refactor-method` skill and load the `python-development:python-dead-code` skill in audit-only mode; read the Python tool results of the evidence pack (`references/candidate-grounding.md`); report what the tools cannot see (semantic misuse, behavior-changing complexity, idiom violations) and never restate a tool line |
| dependencies | The candidate changes a manifest or lockfile: `pyproject.toml`, `uv.lock`, `poetry.lock`, `requirements*.txt`, `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lock`, `Cargo.toml`, `Cargo.lock`, `go.mod`, `go.sum`, `Gemfile.lock`, `composer.lock`, `pom.xml`, `build.gradle*`, `*.csproj` | `project-protocol:isolated-worker`. Its brief says: load the `dependency-audit:dependency-audit` skill read-only; run the ecosystem's own audit, outdated and license tooling on the candidate; report `TOOL-REPORTED`, `INFERRED` and `UNKNOWN` facts, never a remediation |

The two rows above bind a method through the declared isolated worker rather
than a named role, because those providers ship no review role: their value is
the method and the tooling it names. The worker's brief carries the skill
identities, audit-only mode, the evidence pack paths and the report path, like
any other inline lens.

Select each dimension once. A false signal records a code-based skip reason. An
unreadable or ambiguous signal records a coverage gap; it is not evidence of
inapplicability. Required provider dependencies supply the roles regardless of
selection. A matched role that cannot run is a failed delivery, never a clean skip
or a generic substitute.

Respect team review's explicit --reviewers selection and --all override. Record
manual selection as activation evidence, including the lack of an automatic
signal when appropriate. Normalize legacy selectors before applying that scope:
react-perf/react-performance select react, and ts-safety/type-safety select
typescript. An explicit performance selector resolves to react when the relevant
React signal is verified; otherwise it selects the existing general-performance
dimension, with a React coverage gap if applicability is unknown. Do not dispatch
both performance bindings for that one selector. Architecture review remains a
separate dimension even when it shares the general code-auditor role. Record the
requested spelling and resolved dimension in the plan.

--no-context removes shared context from these workers
as it does from other reviewers; it does not remove the dimensions. --fast changes
verification cost, not which applicable specialists are selected.

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

Dispatch these reviewers with the other selected dimensions in isolated contexts.
Do not run their standalone workflows, repeat preparation or publish another
report. Consolidation waits for every selected reviewer to deliver or fail, and
preserves source role, severity, evidence and premise provenance in the same native
finding set. Independent reviewers do not receive peer findings before delivery.
