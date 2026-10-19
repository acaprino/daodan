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

# Context sharing, anchor routing and metrics

On-demand unit of `senior-review:review-quality-gates`. Read it when preparing or
dispatching reviewers of a review that builds shared context (the team variant,
or a lifecycle review with shape `branch`). The provenance rule in the skill's
core governs everything here.

## Context Sharing Pattern

When `/team-review` runs in pipeline mode (no `--no-context`), reviewers receive three context artifacts produced in Phase 1:

1. **Codebase Map output** (from `codebase-map`) at `$XRAY_RUN_DIR` when the command started the run itself (`/team-review` Phase 1a), or the `.codebase-map/` mirror when consuming an existing analysis (`/code-review` Step 2). A command that started a run never reads the mirror. Files: `01-structure.md`, `02-interfaces.md`, `05-risks.md`, and optionally `03-flows.md`, `04-semantics.md`, `06-documentation.md`, `07-final-report.md`.
2. **Interconnect map** at `.team-review/02-interconnect.md` (from `codebase-map:semantic-interconnect-mapper`): contracts (formal / structural / implicit), invariants, domain rules, assumptions (verified / documented / unverified), integration hot-spots, change impact radius.
3. **Knowledge provenance** at `.team-review/01-knowledge-provenance.md` (from `/team-review` Phase 1d): which concepts each discovery branch found, which neither found, and which they disagree about.

A fourth artifact, `.team-review/01b-independent-claims.md`, is derived in Phase 1c by `senior-review:premise-auditor` while blind to both of the above, and joined into `01-knowledge-provenance.md` in Phase 1d (contradictions become `disputed` rows).

### Default anchor routing

Reviewers Grep or read only the anchors relevant to their dimension from `.team-review/02-interconnect.md` (see `references/panel-and-critic-prompts.md` for the context-aware spawn template):

| Reviewer dimension | Primary anchors in interconnect map |
|---|---|
| security | `## Integration Hot-Spots` (inbound), `## Assumptions` (unverified), `## Contracts` (implicit, input validation) |
| architecture (code-auditor) | `## Invariants`, `## Contracts` (structural + implicit), `## Call Graph` |
| logic-integrity | `## Contracts` (implicit, unverified), `## Invariants`, `## Assumptions` (unverified), `## Domain Rules` |
| distributed-flows | `## Integration Hot-Spots` (HTTP / queue / IPC), `## Call Graph` (cross-service) |
| chicken-egg | `## Assumptions` (initialization order), `## Integration Hot-Spots` (Env / config), `## Invariants` (cross-component) |
| ui-races | `## Invariants` (temporal), `## Integration Hot-Spots` (UI state) |
| temporal-resilience | `## Invariants` (temporal, liveness), `## Assumptions` (unverified, timing/retry), `## Integration Hot-Spots` (queues, timers, network loops) |
| data-integrity | `## Invariants` (uniqueness, state exclusivity, balances), `## Contracts` (structural, persistence shapes), `## Assumptions` (unverified, isolation/consistency) |
| resource-lifecycle | `## Assumptions` (pool bounds, connection reuse), `## Integration Hot-Spots` (connections, subprocesses, long-lived handles) |
| api-contracts | `## Contracts` (formal) -> `senior-review:api-contract-auditor` |
| structural entropy (diff mode) | none (reads `$XRAY_RUN_DIR/01-structure.md` + `02-interfaces.md` + concept index) |

### Metrics

**Map utilization rate** (operational, not a quality signal): fraction of findings citing an interconnect anchor. Do not set a target for it.

Quality signals:
- **Independent premise reconstruction rate**: fraction of findings whose load-bearing premise was obtained without exposure to that premise (Phase 1c Premise Auditor or independent reviewer re-derivation; **Lens 0 does not count** because Mode 2 is primed).
- **Premise challenge rate**: fraction of eligible premises (`shared-context`, `mixed`, or universal/negative quantifier) attacked by Lens 0.
- **Map challenge rate**: fraction of consumed map rows explicitly tested rather than assumed.
- **Map gap rate**: `[MAP-GAP]` findings over total findings.
- **Cross-source corroboration rate**: diagnostic over findings corroborated across code, tests, and docs.

### Fallback: raw mode (`--no-context`)

When `--no-context` is set, reviewers receive only target + diff: `logic-integrity-auditor`, `premise-auditor`, Phase 0c, and Lens 0 do not run; all findings are `independent` by construction; no `.codebase-map/`, `$XRAY_RUN_DIR`, or `.team-review/02-interconnect.md` references appear in reviewer prompts.
