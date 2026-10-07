# Daodan coherent harness implementation plan

> **For agentic workers:** Execute by independent subsystem in the current shared checkout. Read the design first. No worker rebuilds generated exports or edits another subsystem. The root owns integration, release and whole-change review.

**Goal:** Restructure the marketplace into complete AI development paths while preserving useful specialist products.

**Architecture:** A project-lifecycle coordinator uses canonical domain methods, a leaf project-protocol owns operational records, and project-knowledge owns durable project information. Universal review and specialist review are separate mandatory dependency closures.

**Tech Stack:** Markdown, strict TOML, stdlib Python, the existing five host adapters.

**Spec:** [Architecture](../specs/2026-10-07-daodan-coherent-harness-design.md)

## Global constraints

- Hand-authored kernels and adapters only; generated catalogs and exports are rebuilt together.
- No optional local dependencies, runtime fallback for a required dependency, or duplicate component names.
- repo-hygiene remains a leaf; its Git auxiliary state is detection-only.
- X-ray remains static and confined to .codebase-xray/.
- Preserve meaningful behavioral protection; no test or coverage quotas.
- Operational state lives in .daodan/runs/<id>/, never in durable instructions.
- Runtime host probes and deterministic package tests are reported separately.
- Marketplace major release 30.0.0; modified existing kernels get an appropriate version bump; new kernels start at 1.0.0.

## Review focus

- Existing dirty worktrees and files from another session must survive failures.
- Missing workers, missing test runners and old remote CI successes must not produce false completion.
- Shared premises must not be counted as independent corroboration.
- Permanent retention must reject changed artifacts, symlinks and unresolved evidence.
- Retired IDs must disappear from live consumers, while migrations and historical specs remain readable.

## Subsystem A: compiler and protocol

**Files:** scripts/daodan/model.py, load.py, validate.py, render.py, build.py and relevant adapter templates; new plugins/project-protocol/{plugin.toml,contracts/,skills/project-protocol/}; tests/test_daodan_*.py and tests/test_project_protocol.py.

- [x] Add exported contract paths to the neutral plugin model and strict manifest loader. Validate paths under contracts/, existence and declared cross-plugin schema providers. Support contract.shared_schemas without copying canonical schemas.
- [x] Reject nonempty PhaseSpec.invoke with unsupported-workflow-invoke; test loading a valid-looking invocation fails semantically.
- [x] Pass the kernel registry to validation/render. Resolve plugin/role against actual declared roles and hard dependencies. Render adapter-native role IDs and correct installed body paths for inline dispatch.
- [x] Add two-kernel fixtures exercising missing roles, undeclared provider, wrong contract paths and cross-plugin dispatch on all five hosts.
- [x] Create project-protocol contracts/work.toml and project-result.toml. Keep the seven senior review contracts domain-owned.
- [x] Implement skills/project-protocol/scripts/run_state.py with init, show, update, validate and resume commands, JSON payload files, expected-revision checks and atomic updates. Records identify project, workspace, snapshot, scope, authorizations, budget, plan, deliveries and interruption. Validate exact run IDs, confined output roots and sentinel.
- [x] Define canonical baseline, candidate gate, pre-phase SHA and rollback behavior in the protocol skill. Helpers mechanically confine their own writes; other tool obligations remain prompt-level.
- [x] Test atomic revisions, path traversal/symlinks, interruption, stale snapshots, missing deliveries and required gate accounting.

## Subsystem B: review and tests

**Files:** plugins/senior-review/, new plugins/review-plus/, plugins/testing/, plugins/python-development/, plugins/clean-code/; tests and evals for these methods.

- [x] Extract canonical review preparation/consolidation and named application-cleanup method from existing skill references. Keep prerequisites and provenance rules, fixing rollback to the captured pre-phase SHA.
- [x] Remove React/TypeScript/platform dispatch and hard dependencies from senior-review. Add review-plus code-review, team-review and pr-review entries that load senior canonical methods and dispatch those three mandatory specialists. No copied prompts or review engine.
- [x] Make existing auditor input preparation and test remediation methods callable. Add runner/configuration/absent-suite findings instead of aborting silently.
- [x] Distinguish product defect, wrong oracle, environment, flaky or unknown before quarantine. Preserve independent failure modes and bugfix provenance before consolidation; replace coverage/count equivalence claims.
- [x] Retire python-test-engineer; transform python-tdd into pytest-patterns, retaining Python techniques and removing quotas and derived/tautological oracle guidance. Python depends on testing; testing does not depend on Python.
- [x] Make readability and refactor failure recovery preserve existing edits and use the common gate procedure.
- [x] Run relevant compiler/content contracts and add behavioral eval cases for false oracle, real product bug, distinct failures and failed cleanup phases.

## Subsystem C: knowledge migration

**Files:** new plugins/project-knowledge/, removed plugins/codebase-mapper/, project-setup/, docs/; live consumers, linter entries, fact anchors, docs/plugins/ and knowledge evals.

- [x] Move source material directly into its final owner. Expose instructions, guide, maintain and readme with common input and outcome conventions.
- [x] Rename claude-md-auditor to instructions-auditor and support explicit read-only audit. Select durable instruction destinations from the target project/host.
- [x] Prefer existing documents and a reviewed file/audience plan; full numbered guide set only when requested. Absorb config-writer into ops-writer while preserving how-to/reference techniques.
- [x] Remove duplicated voice rules from doc-humanizer and route voice to text-humanizer. Preserve evidence-aware guide review.
- [x] Extract knowledge preparation/audit/apply methods under skills. Remove the old three kernels atomically.
- [x] Update runtime references, linter exemptions/baselines, fact anchors and per-plugin documentation without increasing grandfathered counts.
- [x] Check no retired runtime ID remains and generated installed paths will contain every referenced resource.

## Subsystem D: lifecycle and retention

**Files:** new plugins/project-lifecycle/{plugin.toml,workflows/,skills/lifecycle-method/}; plugins/repo-hygiene/; tests/test_lifecycle_artifacts.py; evals/project-lifecycle/.

- [x] Implement assess, repair, change, verify and consolidate as thin entries to lifecycle-method. Sidecars declare conditional fanout phases with explicit cross-plugin roles and all-delivered barriers.
- [x] Define focus-to-dimension/input table, one initial pass, budget and coverage reporting, exact snapshot binding and verified result reuse.
- [x] Normalize native reports as provenance-preserving wrappers, retaining missing fields and native dispositions; build a DAG plan with owner, method, authorization and gate for each action.
- [x] Repair consumes an identified plan. Invalid scope/revision requires reassessment; known semantic refactors use authoring then abstraction audit. Commit-only cleanup is disclosed in assess.
- [x] Change integrates upstream planning/execution, discovery before writing and complete consequences; verify correlates local or remote evidence to the candidate revision.
- [x] Consolidate preserves experiment conditions/results/errors/limits before knowledge integration and retention. Add skills/lifecycle-method/scripts/artifacts.py with plan/apply, owned manifests, exact hashes, unresolved-reference checks, report verification and explicit purge.
- [x] Protect .daodan and sentinel roots in repo-hygiene without interpreting work.json. Contract-test the native tidy converter.
- [x] Test retention path confinement, changed artifacts, links, missing reports, interruption/reapply and byte accounting. Add behavioral eval cases including stale gates and missing workers.

## Subsystem E: integration and publication

**Files:** plugins/codebase-xray/, plugins/marketplace-ops/, plugins/system-utils/, README.md, CLAUDE.md, docs/plugins/, docs/migration-*.md, scripts/lint_*.py where live ID migration requires it; generated exports/catalogs/instructions.

- [x] Remove X-ray quick-fix application while retaining diagnostic recommendations.
- [x] Align marketplace-ops with neutral kernels, adapter-owned tooling and generated catalogs. Keep system-utils out of active repository cleanup.
- [x] Publish a compact front door with five lifecycle commands, knowledge/review owners and independently useful extras. Record all retired IDs and changed review coverage.
- [x] Recalculate dependency closures from manifests. Update durable instruction facts; regenerate AGENTS and native skills.
- [x] Bump release to 30.0.0, rebuild every host, run all required linters, unit suites, Copilot guard and deterministic drift/sync checks.
- [x] Fresh reviewers examine the whole migration and stale untouched consumers. Fix findings, rerun only affected checks plus final release gate.
- [x] Record compiler/eval/installed-host evidence honestly. Remove only owned scratch artifacts after preserving validation results.
Publication follows the repository workflow: commit the synchronized source and generated packages together, then push without rewriting remote history. The delivery message records the observed commit, remote and release status.

