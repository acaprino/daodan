---
name: delivery-method
description: >
  Coordinate analysis, debugging, features and complete documentation through grounded specifications, adversarial plans, verified commits and authorized merge.
  TRIGGER WHEN: the user wants to brainstorm or design a project, define specifications or implementation plans, investigate or debug, build or refactor code, produce project documentation, resume work, or finish a delivery. Route design conversations to the owned brainstorm without requiring an explicit command.
  DO NOT TRIGGER WHEN: diagnosing project health without implementing (use project-lifecycle:assess-method), requesting code explanation, or requesting one isolated specialist audit without delivery coordination.
---

# Project delivery

Load `work-controller:work-record` for grants/snapshots/delivery/recovery.
Own design-to-delivery; compose methods, never competing workflows.

## Load map

Load by step:

- First use: `references/first-use.md`.
- Initialization/ADR/FRD bootstrap: `references/init.md`; `project-delivery:project-bootstrap`.
- Change overview: `references/change.md`.
- Preflight: `references/preflight.md`, `references/context-cycle.md`.
- Interview/specification: `references/interview.md`.
- Plan/execution: `references/waves.md`; dispatch: `references/worker-brief.md`.
- Specifications/approval/handoff: `references/specification.md`.
- Brainstorm: `references/brainstorm.md`.
- Load skills: `references/investigate.md`.
- Documentation: `references/document.md`.
- Repair/refactor: `references/repair.md`, `references/refactor.md`.
- Resume/status: `references/continue.md`, `references/status.md`.
- Verification: `references/verify.md`.
- Integration: `references/finish.md`, `references/realign.md`.
- Sync: `references/sync.md`, `references/realign.md`.
- Consolidation: `references/realign.md`, `references/retention.md`.

## Run record

Initialize operation/root/objective/source/scope.
Resume with current grants and session; preview is default. Specifications live
in `docs/specs/`; `intent.md` binds approval. ADRs retain separate technical decisions.

New execution runs set `process_required: true`; follow work-record's
`references/process-runtime.md` to admit approved YAML and bind workers before
dispatch. Preserve legacy unbound runs. Require process/delivery/domain gates;
commit through the reviewed workflow.

## Canonical methods

- Maps: `codebase-map:map-method`; dispatch isolated `codebase-map:map-analyst`.
  Own analyze preflight/checkpoints/delivery/publication; loading is not dispatch.
- Load skills: `project-delivery:adr-method`.
- Load skills: `senior-review:investigation-method`.
- Load skills: `senior-review:review-method`; branches: `senior-review:review-preparation`.
- Load skills: `senior-review:application-cleanup-method`.
- Tests: `testing:test-preparation`, `testing:test-remediation-method`; dispatch `testing:test-writer`.
- Load skills: `clean-code:readability-method`.
- Load skills: `abstraction-architect:abstraction-architect` and its auditor.
- Load skills: `project-knowledge:instructions-method`, `project-knowledge:project-knowledge`, `project-knowledge:readme-craft`.
- Load skills: `repo-hygiene:repo-hygiene`.
- Task workspaces/catalog: load skill `worktree-manager:worktree-method`.
- Requested challenge: `peer-review:cross-model-peer-review`; dispatch `peer-review:packet-builder`,
  `peer-review:respondent`. Requested opinion: `moe:multi-model-deliberation`.
- HTML: the coordinator must load skill `report-rendering:report-renderer` and read `references/project-run-view.md` before closure when requested/useful.

The worktree method owns workspace creation/resumption and catalog annotations;
Work Controller owns agenda/grants. Status and brainstorming create no worktree.
Missing Worktrunk blocks dependent operations with its recovery path.

## Delivery and closure

Validate the protocol's `result.json`, retaining native reports, hashes, gaps
and contradictory/shared-premise findings. Missing deliveries block completion.
Report inventory/reading/runtime separately, with exact candidates/limits.
Static checks prove no runtime execution; self-checks no independent correctness;
quarantine moves no recovered disk space.
