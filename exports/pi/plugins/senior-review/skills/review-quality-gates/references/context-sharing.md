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

# Context sharing, anchor routing and metrics

Preparation/dispatch unit of `senior-review:review-quality-gates`; its provenance
rule applies throughout.

## Context Sharing Pattern

Supply only admitted, actually produced/bound artifacts. Availability never changes
the computed roster or required gates:

1. **Codebase Map**: `$XRAY_RUN_DIR` if this command started it, otherwise the
   `.codebase-map/` mirror, never both. Read `01-structure.md`,
   `02-interfaces.md`, `05-risks.md`; optionally `03-flows.md`,
   `04-semantics.md`, `06-documentation.md`, `07-final-report.md`.
2. **Interconnect map**: `.team-review/02-interconnect.md`, produced by
   `codebase-map:semantic-interconnect-mapper`: contracts, invariants, domain
   rules, assumptions, integration hot-spots and change impact.
3. **Knowledge provenance**: `.team-review/01-knowledge-provenance.md`, Phase 1d:
   concepts found by either discovery branch, neither, or disputed.

Required blind derivation produces `.team-review/01b-independent-claims.md`
through `senior-review:premise-auditor` in Phase 1c. Phase 1d compares it only
with an actual shared derivation. No flag removes the required independent delivery.

### Scoped semantic context and visibility

Without an interconnect map, supply scoped semantic context: Code Graph
`symbols-at`/`edit-impact`/`stale-callers` rows carrying snapshot, symbol,
locator and freshness; scope-linked records/documents and cards with provenance.
Route contract/invariant/rule/assumption rows below. Missing provenance/freshness
makes a row a lead. This enables lite logic review; neither context available means
a missing prerequisite, never a silent pass.

Premise-auditor Mode 1 receives no shared artifacts, map output or peer findings,
including earlier exposure in that worker context. Lens 0 (Mode 2) receives its
assigned claim and admitted evidence separately. Other reviewers receive scoped
admitted inputs only.

### Default anchor routing

Read relevant anchors in `.team-review/02-interconnect.md`; brief template:
`references/panel-and-critic-prompts.md`.

| Dimension | Anchors and focus |
|---|---|
| security | Integration Hot-Spots: inbound; Assumptions: unverified; Contracts: input validation |
| architecture/code | Invariants; Contracts: structural/implicit; Call Graph |
| logic-integrity | Contracts: implicit/unverified; Invariants; Assumptions; Domain Rules |
| distributed-flows | Integration Hot-Spots: HTTP/queue/IPC; Call Graph: cross-service |
| chicken-egg | Assumptions: initialization; Integration Hot-Spots: Env/config; Invariants |
| ui-races | Invariants: temporal; Integration Hot-Spots: UI state |
| temporal-resilience | Invariants: liveness; Assumptions: timing/retry; Integration Hot-Spots: loops |
| data-integrity | Invariants: uniqueness/exclusivity/balances; Contracts: persistence; Assumptions: isolation/consistency |
| resource-lifecycle | Assumptions: pool bounds/reuse; Integration Hot-Spots: connections/processes/handles |
| api-contracts | Contracts: formal |
| structural entropy (diff) | No anchors: `$XRAY_RUN_DIR/01-structure.md`, `02-interfaces.md`, concept index |

### Metrics

Map utilization: anchor-citing findings, operational only, no target.

Quality signals:
- Independent premise reconstruction: premises obtained without exposure; Phase 1c
  or unprimed re-derivation, excluding primed Lens 0.
- Premise challenge: eligible shared/mixed/universal/negative premises attacked by Lens 0.
- Map challenge: consumed rows tested.
- Map gap: `[MAP-GAP]` findings / total findings.
- Cross-source corroboration: evidence across code, tests and docs.

### Withholding shared context (`--no-context`)

Withhold optional shared analysis; retain target, snapshot, run binding and source
evidence. Roster, required blind derivation and gates remain. Logic may use
source-derived scoped context; missing required inputs leave delivery incomplete.

Provenance reflects actual exposure, including earlier map/peer material; flags
cannot confer independence. Use a fresh unprimed blind context; record contamination.
Lens 0 still checks eligible shared/mixed and universal/negative premises at any
provenance with admitted evidence. Missing evidence means a gap/uncertain verdict,
never a passed gate.
