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

# Context sharing, anchor routing and metrics

On-demand unit of `senior-review:review-quality-gates`, read when preparing or
dispatching reviewers that build shared context. The skill's provenance rule
governs everything here.

## Context Sharing Pattern

When `team-review` runs in pipeline mode (no `--no-context`), reviewers receive three context artifacts produced in Phase 1:

1. **Codebase Map output** at `$XRAY_RUN_DIR` for a run this command started, else the `.codebase-map/` mirror (never both). Files: `01-structure.md`, `02-interfaces.md`, `05-risks.md`, and optionally `03-flows.md`, `04-semantics.md`, `06-documentation.md`, `07-final-report.md`.
2. **Interconnect map** at `.team-review/02-interconnect.md` (from `codebase-map:semantic-interconnect-mapper`): contracts, invariants, domain rules, assumptions, integration hot-spots, change impact radius.
3. **Knowledge provenance** at `.team-review/01-knowledge-provenance.md` (Phase 1d): concepts found by each discovery branch, by neither, and disputed.

A fourth artifact, `.team-review/01b-independent-claims.md`, is derived in Phase 1c by `senior-review:premise-auditor`, blind to the above, and joined into `01-knowledge-provenance.md` in Phase 1d (`disputed` rows).

### Scoped semantic context and visibility

With no interconnect map, preparation may supply a **scoped semantic context**: Code Graph rows (`symbols-at`, `edit-impact`, `stale-callers`) with snapshot, symbol, locator and freshness; records and documents citing the scope; and cards, each with provenance. Its contract, invariant, rule and assumption rows route through the table below. A row without provenance or freshness is a lead. This context lets `logic-integrity-auditor` run in lite reviews; with neither input it reports the missing prerequisite, never a silent pass.

Premise-auditor Mode 1 receives no shared artifacts, map output or peer findings. Lens 0 (Mode 2) and ordinary reviewers receive the full admitted context.

### Default anchor routing

Reviewers read only their dimension's anchors from `.team-review/02-interconnect.md` (spawn template: `references/panel-and-critic-prompts.md`):

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

**Map utilization rate** (operational only): findings citing an interconnect anchor. No target.

Quality signals:
- **Independent premise reconstruction rate**: premises obtained without exposure to them (Phase 1c or re-derivation; Lens 0 excluded, Mode 2 is primed).
- **Premise challenge rate**: eligible premises (`shared-context`, `mixed`, universal/negative) attacked by Lens 0.
- **Map challenge rate**: consumed rows tested, not assumed.
- **Map gap rate**: `[MAP-GAP]` findings over total findings.
- **Cross-source corroboration rate**: findings corroborated across code, tests and docs.

### Fallback: raw mode (`--no-context`)

With `--no-context`, reviewers receive only target + diff: `premise-auditor`, Phase 0c and Lens 0 do not run, and `logic-integrity-auditor` reports its missing prerequisite instead of running. All findings are `independent`; no map or run references appear in prompts.
