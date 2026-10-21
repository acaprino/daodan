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
