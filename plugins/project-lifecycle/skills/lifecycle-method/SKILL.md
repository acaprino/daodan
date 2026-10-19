---
name: lifecycle-method
description: >
  Coordinate complete AI development work across code, tests, project knowledge and artifacts.
  TRIGGER WHEN: the user wants to brainstorm or explore an idea before building, initialize or set up a project, diagnose project health or technical debt, build a feature, fix a bug, refactor code, check task status, continue an open task, finish and merge a task, sync upstream, or run a daodan lifecycle command.
  DO NOT TRIGGER WHEN: the user requests code explanation without investigation or changes, wants an isolated specialist audit (use senior-review, codebase-map or testing directly), or only needs a problem investigated without fixing it (use senior-review:investigation-method).
---

# Project lifecycle

Own the requested outcome and its consequences, in proportion to risk, scope
and authorization. Load the skill `project-protocol:project-protocol` first: it owns run
records, snapshots, verification and recovery. This skill owns decisions and
dispatch, never detection prompts.

## Load map

Read one unit per step, in this skill, at its start.

| Operation or step | Read |
|---|---|
| initialization | `references/init.md` |
| assess, the diagnosis | `references/assess.md` |
| change, phase 1 | `references/preflight.md` |
| change, phases 2 and 3 | `references/interview.md` |
| change, phases 4 and 5 | `references/waves.md`, then `references/worker-brief.md` before each dispatch |
| change, overview | `references/change.md` |
| repair, refactor | `references/repair.md`, `references/refactor.md`, then the change phases they name |
| continue a task | `references/continue.md` |
| status | `references/status.md` |
| verify | `references/verify.md` |
| brainstorm | `references/brainstorm.md` |
| finish, phase 7 | `references/finish.md`, then `references/realign.md` |
| sync | `references/sync.md`, then `references/realign.md` |
| consolidate | `references/realign.md`; a run's output, `references/retention.md` |
| converting a native report | `references/native-reports.md` |
| a requested HTML view | `references/human-view.md` |

## Run record

Inputs: operation, project root, objective and its source; optional target,
run identity and prior evidence. Initialize
through the protocol helper with operation, objective, scope, authorizations,
budget, phases, plan, deliveries and required gates; the loop sections are
added as the phases produce them, and a draft plan passes `plan-check` before
it enters the run. Resume the branch's task from the agenda with current
authorizations and this session's id; a task another session holds is taken
over only after the user confirms it is closed. Preview is the default; an
authorization is asked when a step needs it and recorded in the run: `fix` for
in-scope edits, `commit` for commits, neither a push or a permanent deletion.

## Canonical methods

Load only what the step needs, by name, never by path.

| Need | Load or dispatch |
|---|---|
| Static context, impact packets, exact run binding | `codebase-map:map-method`; dispatch `codebase-map:map-analyst` in an isolated context for an analysis |
| Decisions governing a scope, a proposed record, promotion at merge | `project-knowledge:adr-method` |
| Review at any stage and of any kind, shape `light` or `branch` | `senior-review:review-method`; shape `branch` through `senior-review:review-preparation` |
| Application subtraction | `senior-review:application-cleanup-method` |
| Suite preparation and remediation | `testing:test-preparation`, `testing:test-remediation-method` |
| Test authoring | dispatch `testing:test-writer` |
| Readability with behavior preserved | `clean-code:readability-method` |
| Structural diagnosis | `abstraction-architect:abstraction-architect` and its auditor |
| Durable instructions, guides, README | `project-knowledge:instructions-method`, `project-knowledge:project-knowledge`, `project-knowledge:readme-craft` |
| Workspace detection and reversible operations | `repo-hygiene:repo-hygiene` |
| Another model's challenge of a record or plan, on request | `peer-review:cross-model-peer-review`, dispatching `peer-review:packet-builder` and `peer-review:respondent`; a question goes to `moe:multi-model-deliberation` |

For a Codebase Map, execute the analyze entry's preflight, checkpoints,
delivery check and publication decision here and dispatch the analyst for the
phases; loading a role as a skill runs nothing. Never start a command from
inside another.

## Delivery and closure

Keep every specialist's native report, hashes, scope, status, evidence and
declared gaps. A missing delivery stays missing; a failed worker is not an
empty result. Deduplicate findings by behavior or concept, keep contradictions,
and treat two reviewers with one inherited premise as one observation.

For an HTML view, requested or useful for navigation, the coordinator reads
`references/human-view.md` before closing; workers keep native deliveries.

`result.json` follows the protocol's envelope and references each native
report. Validate it with the helper before claiming completion; a validated
record is not read evidence. Reports state inventory, read and runtime
coverage separately, the exact candidate of every check, decisions, changes,
remaining limits and next actions. Never claim runtime coverage from source
inspection, correctness from self-generated tests, or disk recovery from a
quarantine move.
