---
name: lifecycle-method
description: >
  Coordinate complete AI development work across code, tests, project knowledge and artifacts.
  TRIGGER WHEN: running project-lifecycle assess, repair, change, verify or consolidate, or explicitly taking responsibility for project coherence.
  DO NOT TRIGGER WHEN: an isolated specialist audit suffices (use senior-review, codebase-map or testing directly).
---

# Project lifecycle

Own the requested outcome and its consequences, in proportion to risk, scope
and authorization. Load `project-protocol:project-protocol` first: it owns run
records, snapshots, verification and recovery. This skill owns decisions and
dispatch, never detection prompts.

## Load map

Read one unit per step, in this skill, when the step starts.

| Operation or step | Read |
|---|---|
| assess, including `--init` | `references/assess.md` |
| change, phase 1 | `references/preflight.md` |
| change, phases 2 and 3 | `references/interview.md` |
| change, phases 4 and 5 | `references/waves.md`, then `references/worker-brief.md` before each dispatch |
| change, overview of all seven phases | `references/change.md` |
| repair | `references/repair.md`, then preflight and waves as it directs |
| verify | `references/verify.md` |
| consolidate | `references/consolidate.md` |
| converting a native report | `references/native-reports.md` |
| a requested HTML view | `references/human-view.md` |

## Run record

Inputs: operation, project root, objective and its source; optional target,
focus, depth, run and plan identities, output root, prior evidence. Initialize
through the protocol helper with operation, objective, scope, authorizations,
budget, phases, plan, deliveries and required gates; the loop sections
(`workspace`, `preflight`, `adr`, `waves`, `rulings`) are added as the phases
produce them, and a draft plan passes `plan-check` before it enters the run.
Resume only an exact run with current authorizations; the latest report of
another session is never a resume target. Preview is the default; `--fix`
authorizes in-scope edits, `--commit` adds commits, neither authorizes a push
or a permanent deletion.

## Canonical methods

Load only what the step needs, by name, never by path into another plugin.

| Need | Load or dispatch |
|---|---|
| Static context, impact packets, exact run binding | `codebase-map:map-method`; dispatch `codebase-map:map-analyst` in an isolated context for an analysis |
| Decisions governing a scope, a proposed record, promotion at merge | `project-knowledge:adr-method` |
| Candidate review at any stage, any target kind, shape `light` or `branch` | `senior-review:review-method`, through `senior-review:review-preparation` |
| Application subtraction | `senior-review:application-cleanup-method` |
| Suite preparation and remediation | `testing:test-preparation`, `testing:test-remediation-method` |
| Test authoring | dispatch `testing:test-writer` |
| Writing Python or TypeScript in a wave | dispatch `python-development:python-engineer` or `typescript-development:typescript-engineer`; other stacks use the isolated worker with the knowledge `skill-catalog:skill-catalog` selects |
| Readability with behavior preserved | `clean-code:readability-method` |
| Structural diagnosis | `abstraction-architect:abstraction-architect` and its auditor |
| Durable instructions, guides, README | `project-knowledge:instructions-method`, `project-knowledge:project-knowledge`, `project-knowledge:readme-craft` |
| Workspace detection and reversible operations | `repo-hygiene:repo-hygiene` |
| Challenge of a proposed record or plan by another model, on request | dispatch `peer-review:packet-builder` and `peer-review:respondent` through `peer-review:cross-model-peer-review` |
| Second opinion on a decision, on request | load the `moe:multi-model-deliberation` skill |

For a Codebase Map, execute the analyze entry's preflight, checkpoints,
delivery check and publication decision here and dispatch the analyst for the
phases; loading a role as a skill runs nothing. Never launch a lifecycle
workflow from inside a lifecycle operation.

## Delivery and closure

Keep every specialist's native report, hashes, scope, status, evidence and
declared gaps. A missing delivery stays missing; a failed worker is not an
empty result. Deduplicate findings by behavior or concept, keep contradictions,
and treat two reviewers with one inherited premise as one observation.

For a requested HTML view, or a final report that benefits from navigation
or comparison, the coordinator reads `references/human-view.md` before
closing the run; workers keep their native deliveries.

`result.json` follows the protocol's envelope and references each native
report. Validate it with the helper before claiming completion; a validated
record is not read evidence. Reports state inventory, read and runtime
coverage separately, the exact candidate of every check, decisions, changes,
remaining limits and next actions. Never claim runtime coverage from source
inspection, correctness from self-generated tests, or disk recovery from a
quarantine move.
