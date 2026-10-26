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

# Condensed test-suite rules

Locally authored policy distilled from this marketplace's testing methods.
This block is self-contained for the target project. Procedure, runner choices,
quarantine and consolidation belong to testing, rather than instruction files.

Offer the block when tests exist or are explicitly planned. Preserve equivalent
project rules and flag inverted or weakened obligations. A project without tests
does not receive a finding solely because this block is absent.

## Project-derived policy completeness

Before publishing test guidance, confirm these facts from the project's approved
decisions, configured tooling and observed checks. Keep detailed procedures in the
existing testing guide and reference its actual owner. Missing information is a
gap to resolve, not permission to invent a default.

- Exact permitted commands, working directories, runner/configuration and required
  runtime versions; identify which are local checks and which are CI gates.
- Prerequisites for each lane: services, fixtures, migrations, browser/application
  startup and approved credentials. A local integration environment and production
  schema verification are distinct checks; inaccessible production remains open.
- Established test layers and placement conventions, behavior/oracle authority,
  boundary-double policy and the lanes that exercise real persistence or protocols.
- Isolation and cleanup obligations for resource-dependent tests, including clocks,
  randomness, environment, filesystem/database state and async work where relevant.
  Keep the detailed checklist and failure procedure with testing's canonical owner.
- Failure classification, approved quarantine/skip conditions, retained regression
  protection and verified equivalent replacement before consolidation or retirement.
- Measured runtime or coverage/mutation targets and their configured enforcement,
  when the project has approved them. Counts and a template threshold do not prove
  meaningful protection. Record commands not run and prerequisites not available.

## Reusable instruction block

```markdown
## Test-Suite Rules

Test ownership: source at unit; behavior at integration, contract and e2e.
Assertion protection: Preserve assertions for approved behavior; correct a wrong oracle only with independent authority and evidence, while keeping valid product protection active.
Test retirement: Retire tests only for retired behavior or verified equivalent replacement protection in the same candidate; counts, coverage, age and refactoring alone are insufficient.

1. Search before writing: find the existing owner for the intended layer and behavioral scope, and extend it. A parallel file for the same owner requires a justified scope split.
2. Unit tests mirror source ownership (for example `src/foo/bar.py` maps to `tests/unit/foo/test_bar.py`), following this project's convention. Integration, contract and e2e tests belong to a flow, endpoint or contract and may span several source modules.
3. Keep layers explicit through established directories, colocated paths or runner markers. Use measured runtime budgets. Choose the lowest layer that protects the required behavior; unit coverage does not replace a distinct integration or contract check.
4. Prefer observable contracts. Internal access, interaction/order assertions and boundary doubles require a meaningful boundary or diagnostic regression purpose; a repository-owned IO adapter may be such a boundary. A mocked adapter does not verify real persistence or wire behavior.
5. Classify product defects, wrong oracles, environment failures and intermittence before suppressing a test. Do not skip or weaken checks to make CI pass. Legitimate platform/feature conditions and quarantine follow the project's tracked policy, with active protection and restoration obligations preserved.
6. Derive expected results from independent approved authority. Follow Assertion protection when correcting an expectation; changing code and its oracle together cannot establish correctness.
7. Follow Test retirement before consolidation or removal. Refactors, renames and migrations preserve and retarget meaningful outcomes and independent failure modes.
8. Resource-dependent tests control incidental time, randomness and environment, isolate mutable filesystem/database state and release fixtures, async work and handles on every exit. The project's testing guide records permitted real services, setup and cleanup.
```
