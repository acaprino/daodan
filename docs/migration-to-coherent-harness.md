# Migration to the coherent development harness

Marketplace 30 reorganized project work around five project-lifecycle entries
while preserving domain specialists. This is a breaking catalog and review-coverage
change. Install the new owners and update prompts, saved commands and integrations.
The first published release of this organization is 30.0.1. Marketplace 31 unifies
correctness review under senior-review and retires the review-plus bundle.

| Retired entry/component | Replacement |
|---|---|
| codebase-mapper:map-codebase and team-codebase-map | project-knowledge:guide; coordination follows the host adapter |
| codebase-mapper:docs-create | project-knowledge:guide with the requested audience/file plan |
| codebase-mapper:docs-maintain | project-knowledge:maintain |
| codebase-mapper:humanize-docs | project-knowledge:guide with an existing-file structure plan; text-humanizer for voice |
| project-setup:create-claude-md | project-knowledge:instructions --create |
| project-setup:maintain-claude-md | project-knowledge:instructions --audit-only or --fix |
| docs:maintain-readme | project-knowledge:readme |
| docs:readme-craft | project-knowledge:readme-craft |
| codebase-mapper:codebase-mapper | project-knowledge:project-knowledge |
| codebase-mapper:config-writer | project-knowledge:ops-writer |
| project-setup:claude-md-auditor | project-knowledge:instructions-auditor, audit-only supported |
| python-development:python-test-engineer | testing:test-writer, with Python test context |
| python-development:python-tdd | python-development:pytest-patterns for Python techniques; upstream TDD through testing |
| review-plus:code-review | senior-review:code-review |
| review-plus:team-review | senior-review:team-review |
| review-plus:pr-review | senior-review:pr-review |
| review-plus:extended-review-method | senior-review:review-method |

The codebase-mapper, project-setup and docs packages are removed. No permanent
alias kernels preserve a second source of behavior. Historical design/research
documents still use the original IDs when discussing past decisions.

Marketplace 30 temporarily placed React, TypeScript and platform dispatch in
review-plus. Marketplace 31 brings those dimensions into senior-review's existing
preparation, selection, delivery ledger, verification panel and report. Update
stored review-plus invocations to the same senior-review variant and uninstall the
retired bundle; there are no compatibility aliases. Start a fresh host session to
avoid retaining old commands or copied workflow skills. Specialist roles and
standalone commands retain their original IDs.

The three specialist providers are mandatory senior-review dependencies. A false
target signal skips execution with a recorded code-based reason; missing matched
workers remain failed deliveries. The larger mandatory installation closure also
applies to project-knowledge and project-lifecycle through senior-review. Their
source-derived references show the complete cost. Lifecycle change, repair and
verify use the same candidate review, without another plugin choice.

The lifecycle uses canonical methods instead of executing arbitrary nested
workflows. Sidecar invoke is rejected. X-ray analysis in coordinator context is
the explicit existing exception. Cross-plugin role bindings are compiled to the
host's mechanism; inline body resources are generated from the canonical owner.
The sidecar's dispatch table declares every role a loaded method can select,
independently of phase scheduling. Providers are required dependencies. Generic
isolated tasks use project-protocol:isolated-worker when inline_workers is declared;
the coordinator assigns their inputs, scope and intermediate report paths. Final
report ownership stays with its declaring phase.

Records live in .daodan/runs/<id>/ with a .daodan-root sentinel. Resume the exact run,
not the latest report. Alternative run roots must remain dedicated directories
inside the project. Tri-Tech private storage requires a separate permission
integration; it is not implicitly allowed by an installed plugin cache allowance.

Repair --fix cannot run commit-only bulk application subtraction. The assessment
plan reports this prerequisite before repair. Gate failures restore the owned
pre-phase state; old remote CI results do not validate a dirty candidate.

Consolidation verifies experiment outcomes and preserves evidence before retention.
Quarantine moves delete zero content bytes. Permanent purge requires an explicit
scoped grant and unchanged owned artifacts. Deleted content-byte totals and actual
filesystem free-space changes are different measurements.

Review installed-host compatibility separately from compiler/package checks.
See the [architecture](superpowers/specs/2026-10-07-daodan-coherent-harness-design.md)
and [validation record](superpowers/reports/2026-10-07-daodan-harness-validation.md).

