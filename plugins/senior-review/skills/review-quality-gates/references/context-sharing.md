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
