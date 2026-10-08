# Scope-aware skill catalog

The user approved a shared skill selector and implementation on 7 October 2026.
Senior-review keeps its canonical methods, isolated workers, evidence verification,
required specialist bindings and single report. Knowledge is selected for each
affected scope from the skills actually available to the host, including project
and external skills. Adding a knowledge skill changes its metadata, not the reviewer.

## Boundary

The new leaf plugin `skill-catalog` owns metadata discovery, search, selection and
content fingerprints. `SKILL.toml` beside a registered `SKILL.md` declares kind,
operations, languages, frameworks, topics and review dimensions. Missing metadata
means unknown kind. Methods and workflows are never automatic review knowledge.
The compiler validates sidecars and generates a compact metadata index inside the
catalog skill on every host. A generated declaration is not installation evidence.

Adapters explain how to normalize their actual skill inventory into explicit
provider roots, IDs and versions. Only those roots are inspected; no home-directory
crawl, automatic installation or network retrieval. External/project skills use
the same sidecar. Unclassified matches remain visible gaps. All runtime helpers
use Python standard library and return JSON to stdout; run records are persisted
through project-protocol inside the identified project.

## Selection and delivery

The coordinator derives scope paths, language/framework/topic signals and their
evidence from the exact candidate. Metadata filters exclude unrelated scopes and
wrong operations. Search returns bounded candidate pages; automatic selection has
no arbitrary top-K coverage cutoff. Only selected bodies are read and hashed at
preparation. A selection binds project, run, snapshot, provider version, metadata,
content hash, scope, dimensions and activation evidence. Supplementary references
are loaded on demand, confined to the selected skill's `references` directory.

Auditors receive relevant knowledge bindings with their existing briefs. Several
skills can support one auditor. A task-specific domain lens uses only the already
declared isolated-worker if no existing selected lens owns that scope/question.
Knowledge supplies hypotheses; findings still require code evidence and falsifiable
premises. One ledger accounts for all selected workers and their knowledge usage.
Missing, stale or unread knowledge blocks completion for its selected coverage.
An empty inventory, ambiguous metadata or unmatched scope is an explicit gap.

Static methods/roles/providers remain mandatory dependencies. Resolved knowledge
is an explicit, fingerprinted per-run input through the required catalog provider,
not an optional runtime method or role. This distinction is recorded in repository
policy and contracts. Existing React/TypeScript/platform role dependencies stay.

## Verification

Exercise Kotlin selection among 2500 irrelevant skills without reading their bodies;
mixed Python/React/SQL scopes; a newly added language without reviewer edits; wrong
operations; unknown kinds; duplicate IDs; ambiguous/missing inventory; missing or
changed selected bodies and metadata; reference traversal and links; and missing
knowledge deliveries. Verify deterministic indexes and inventory instructions on
all five exports, dependency integrity, documentation parity and the full suite.
Compiler/fixture checks are not an installed-host runtime probe.
