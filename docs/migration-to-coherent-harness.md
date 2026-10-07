# Migration to the coherent development harness

Marketplace 30.0.0 reorganizes project work around five project-lifecycle entries
while preserving domain specialists. This is a breaking catalog and review-coverage
change. Install the new owners and update prompts, saved commands and integrations.

| Retired entry/component | Replacement |
|---|---|
| codebase-mapper:map-codebase and team-codebase-map | project-knowledge:guide; coordination follows the host adapter |
| codebase-mapper:docs-create | project-knowledge:guide with the requested audience/file plan |
| codebase-mapper:docs-maintain | project-knowledge:maintain |
| codebase-mapper:humanize-docs | project-knowledge:maintain for structure; text-humanizer for voice |
| project-setup:create-claude-md | project-knowledge:instructions --create |
| project-setup:maintain-claude-md | project-knowledge:instructions --audit or --fix |
| docs:maintain-readme | project-knowledge:readme |
| codebase-mapper:config-writer | project-knowledge:ops-writer |
| project-setup:claude-md-auditor | project-knowledge:instructions-auditor, audit-only supported |
| python-development:python-test-engineer | testing:test-writer, with Python test context |
| python-development:python-tdd | python-development:pytest-patterns for Python techniques; upstream TDD through testing |

The codebase-mapper, project-setup and docs packages are removed. No permanent
alias kernels preserve a second source of behavior. Historical design/research
documents still use the original IDs when discussing past decisions.

senior-review now covers universal correctness and its existing source/workspace/
testing/abstraction dimensions. React, TypeScript and platform dispatch is owned by
review-plus. Use review-plus:code-review, team-review or pr-review for the previous
extended dimension coverage. Specialist roles themselves retain their original IDs.

The lifecycle uses canonical methods instead of executing arbitrary nested
workflows. Sidecar invoke is rejected. X-ray analysis in coordinator context is
the explicit existing exception. Cross-plugin role bindings are compiled to the
host's mechanism; inline body resources are generated from the canonical owner.

Records live in .daodan/runs/<id>/ with a .daodan-root sentinel. Resume the exact run,
not the latest report. Alternative run roots must remain dedicated directories
inside the project. Tri-Tech private storage requires a separate permission
integration; it is not implicitly allowed by an installed plugin cache allowance.

Repair --fix cannot run commit-only bulk application subtraction. The assessment
plan reports this prerequisite before repair. Gate failures restore the owned
pre-phase state; old remote CI results do not validate a dirty candidate.

Consolidation verifies experiment outcomes and preserves evidence before retention.
Quarantine moves recover zero content bytes. Permanent purge requires an explicit
scoped grant and unchanged owned artifacts. Deleted content-byte totals and actual
filesystem free-space changes are different measurements.

Review installed-host compatibility separately from compiler/package checks.
See the [architecture](superpowers/specs/2026-10-07-daodan-coherent-harness-design.md)
and [validation record](superpowers/reports/2026-10-07-daodan-harness-validation.md).

