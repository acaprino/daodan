# Context sharing and metrics

Preparation/dispatch unit of `senior-review:review-quality-gates`; its provenance
rule applies throughout.

## Context Sharing Pattern

Supply only admitted, actually produced/bound artifacts. Availability never changes
the computed roster or required gates:

1. **Codebase Map**: the tools of the complete run named in the context
   (`codebase_map_search`, `_read`, `_outline`, `_edit_impact`, `_graph`,
   `_symbols_at`), never a new analysis. Reviewers query them for anything the
   context does not cover.
2. **Review context**: `.team-review/01-context.md` (the object and its source
   references) and `.team-review/02-selection.md` (the selected reviewers and why),
   written by the coordinator in Phase 1. Leads, not ground truth.

Independent premise derivation (`senior-review:premise-auditor` Mode 1) is not part
of the branch flow: it runs on explicit request, with no shared artifacts, map
output or peer findings, including earlier exposure in that worker context. Lens 0
(Mode 2) receives its assigned claim and admitted evidence separately. Other
reviewers receive scoped admitted inputs only.

### Scoped semantic context and visibility

Without `01-context.md`, supply scoped semantic context: Code Graph
`symbols-at`/`edit-impact`/`stale-callers` rows carrying snapshot, symbol,
locator and freshness; scope-linked records/documents and cards with provenance.
Missing provenance/freshness makes a row a lead. This enables lite logic review;
neither context available means a missing prerequisite, never a silent pass.

### Metrics

Quality signals:
- Premise challenge: eligible shared/mixed/universal/negative premises attacked by Lens 0.
- Map challenge: consumed rows tested.
- Map gap: `[MAP-GAP]` findings / total findings.
- Cross-source corroboration: evidence across code, tests and docs.

### Withholding shared context (`--no-context`)

Withhold `01-context.md`; retain target, snapshot, run binding and source evidence.
Roster and gates remain. Logic may use source-derived scoped context; missing
required inputs leave delivery incomplete.

Provenance reflects actual exposure, including earlier map/peer material; flags
cannot confer independence. Record contamination. Lens 0 still checks eligible
shared/mixed and universal/negative premises at any provenance with admitted
evidence. Missing evidence means a gap/uncertain verdict, never a passed gate.
