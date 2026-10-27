---
name: delivery-method
description: >
  Coordinate analysis, debugging, features and complete documentation through grounded specifications, adversarial plans, verified commits and authorized merge.
  TRIGGER WHEN: the user wants to investigate or debug a problem, build or refactor code, produce complete project documentation, define specifications or implementation plans, resume work, or finish and merge a delivery.
  DO NOT TRIGGER WHEN: diagnosing project health without implementing (use project-lifecycle:assess-method), requesting code explanation, or requesting one isolated specialist audit without delivery coordination.
---

# Project delivery

Load `work-controller:work-record` for records, snapshots, verification and recovery.
Coordinate authorized outcomes within scope; reuse detection owners.

## Load map

Read each step's units at its start.

| Operation or step | Read |
|---|---|
| first use | `references/first-use.md` |
| initialization or missing ADR/FRD | `references/init.md`; `project-delivery:project-bootstrap` |
| change, phase 1 | `references/preflight.md`, `references/context-cycle.md` |
| change, phases 2 and 3 | `references/interview.md` |
| change, phases 4 and 5 | `references/waves.md`, then `references/worker-brief.md` before each dispatch |
| change, overview | `references/change.md` |
| investigate, debug | `references/investigate.md` |
| complete documentation | `references/document.md` |
| repair, refactor | `references/repair.md`, `references/refactor.md`, then the change phases they name |
| continue a task | `references/continue.md` |
| status | `references/status.md` |
| verify | `references/verify.md` |
| brainstorm | `references/brainstorm.md` |
| finish, phase 7 | `references/finish.md`, then `references/realign.md` |
| sync | `references/sync.md`, then `references/realign.md` |
| consolidate | `references/realign.md`; a run's output, `references/retention.md` |
| a requested HTML view | the project-run view of `report-rendering:report-renderer` |

## Run record

Inputs: operation, root, objective and source; optional target, run and evidence.
Initialize through the protocol helper. Resume the agenda's branch task with
current authorizations and this session. Preview is the default; `fix` and
`commit` grants are recorded separately, never push or permanent deletion.
Without `docs/adr/README.md`, the run's `intent.md` replaces records.

New execution runs set `process_required: true`; read Work Controller's
`references/process-runtime.md` to admit approved YAML and bind worker outputs
before dispatch. Legacy runs retain their recorded method. Graph, native ledger
and domain reviews must succeed; commits remain in the reviewed workflow.

## Canonical methods

Load owners by name, never by path.

| Need | Load or dispatch |
|---|---|
| Static context, packets, run binding | `codebase-map:map-method`; dispatch isolated `codebase-map:map-analyst` for analysis |
| Scientific grounding before substantive decisions | Load `research:science-based-approach`, automatic checkpoint entry; reuse the caller run and grants |
| Decisions and record lifecycle | `project-delivery:adr-method` |
| Root-cause investigation | `senior-review:investigation-method` |
| Any review, `light` or `branch` | `senior-review:review-method`; `branch` through `senior-review:review-preparation` |
| Application subtraction | `senior-review:application-cleanup-method` |
| Suite preparation and remediation | `testing:test-preparation`, `testing:test-remediation-method` |
| Test authoring | dispatch `testing:test-writer` |
| Behavior-preserving readability | `clean-code:readability-method` |
| Structural diagnosis | `abstraction-architect:abstraction-architect` and its auditor |
| Durable instructions, guides, README | `project-knowledge:instructions-method`, `project-knowledge:project-knowledge`, `project-knowledge:readme-craft` |
| Workspace detection and reversible operations | `repo-hygiene:repo-hygiene` |
| Task workspaces and catalog | `worktree-manager:worktree-method` |
| Requested model challenge | `peer-review:cross-model-peer-review`, dispatching `peer-review:packet-builder` and `peer-review:respondent`; questions use `moe:multi-model-deliberation` |

For a Codebase Map, execute the analyze entry's preflight, checkpoints,
delivery check and publication decision here and dispatch the analyst for the
phases; loading a role as a skill runs nothing. Never start a command from
inside another.

The worktree method owns workspace creation/resumption and catalog annotations;
Work Controller owns agenda and grants. Status and brainstorming create no
worktree. Missing Worktrunk blocks dependent operations with its recovery path.

## Delivery and closure

Keep native reports, hashes, scope, status, evidence and gaps. Missing/failed
deliveries stay visible. Deduplicate by behavior, retain contradictions and
count shared-premise reviewers as one observation.

For an HTML view, requested or useful for navigation, the coordinator must
load skill `report-rendering:report-renderer` and read `references/project-run-view.md`
before closing; workers keep native deliveries.

Use the protocol envelope for `result.json`, referencing each native report.
Validate before claiming completion; validation alone is no reading evidence.
Report inventory, reading and runtime coverage separately, each check's exact
candidate, decisions, changes, limits and next actions. Source inspection proves
no runtime coverage; self-generated tests prove no correctness; quarantine moves
prove no recovered disk space.
