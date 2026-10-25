# Complete documentation activity

Inventory existing ADR, FRD, README, guides, instructions and their intended
readers before writing. Reuse `codebase-map:map-method` for discovery and impact;
when no current map exists, search and read the source directly. Documentation is
evidence with provenance, never automatic truth: verify behavioral claims against
current code and mark contradictions, unavailable runtime checks and uncovered
scope.

Load `project-knowledge:project-knowledge` for guides and drift,
`project-knowledge:instructions-method` for instructions and
`project-knowledge:readme-craft` for README. Preserve approved intent separately
from observed behavior. Resolve ADR through `project-delivery:adr-method`; new
records remain Proposed until approved.

Plan documentation in bounded jobs when it spans multiple documents or audiences.
Run the requested document review, verify links and generated parity, then use the
same candidate, commit, resume and final-merge gates as a code change. Do not claim
complete documentation when required sources or audiences remain unexamined.
