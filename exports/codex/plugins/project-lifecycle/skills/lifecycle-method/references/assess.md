# Assess

Load the canonical methods before preparing inputs. Diagnosis does not modify
application files, test files or durable instructions. Run-owned reports and the
explicit X-ray run are the allowed audit outputs.

## Focus selection and inputs

| Focus | Dimensions | Native inputs and preparation |
|---|---|---|
| knowledge | instructions and documentation | instructions-method audit-only; project-knowledge inventory and documentation/README audit; authoritative intent, existing file plan, output paths |
| structure | cleanup and abstraction | cleanup-auditor scoped target; abstraction auditor codebase_path, mode, xray_path, scope, changed_files for diff, report_path, concept_index_path=none |
| tests | suite health | test-preparation determines runner/configuration/source mapping; test-suite-auditor receives paths, runner, layers, measurements and output path |
| artifacts | workspace | workspace-auditor profile full, explicit scope, output path; filesystem/Git evidence only |
| all | union above | no duplicate worker or second detection prompt |

Prepare selections cleanup, tests, structure, instructions and workspace with zero
or one binding each for the sidecar phases. A binding records role, native inputs,
run output path, expected deliverable and input hash. Empty selection means not
requested; selected workers that fail remain failed. Documentary audit is performed
through the knowledge method and accounted for in the same total worker budget.
Count documentation-engineer and guide-reviewer before dispatch. If the quick
budget cannot cover the requested union, show the selected priorities and remaining
dimensions; do not silently dispatch extra contexts or imply complete coverage.

For abstraction context, invoke codebase-xray:analyze in this coordinator context
only when required by the requested scope. Bind the exact new or validated X-ray
run ID, source snapshot, depth and directory. Quick uses lite context and states
missing flows/semantics; deep can request full context. Diff mode receives actual
changed_files. The concept index is a lead, never proof; disable its writes for this
read-only assessment. An interrupted X-ray is not the active completed mirror.

Use the native auditor inputs and boundaries. Missing runner/config or no test
suite produces evidence and an authoring/configuration remedy, not quarantine.
Audit instructions explicitly in audit-only mode. Compare declared intention with
implementation and documents, retaining uncertain authority as a decision.

## Build the plan

Hold all selected deliveries before consolidation; failed workers produce gaps.
Use senior-review:review-consolidation's evidence and provenance rules, without
turning a coherence assessment into a correctness verdict.

Route native findings: docs/instructions/README to project-knowledge; test oracle,
suite configuration, authoring, quarantine or consolidation to testing; reversible
filesystem operations to repo-hygiene; confirmed application subtraction to the
application-cleanup-method; known semantic refactors to change with abstraction
audit before/after. Unknown design intent remains clarify with explicit alternatives.

For every action record dependencies, scope/snapshot, evidence, cost, method, owner
and gate. Cleanup requiring --commit is disclosed here; repair --fix leaves that
action open. Missing credentials/build access need a runnable alternative or an
explicit non-executable action. They never become a green check.

Write plan.json, native reports and result.json under this run. Show executable
actions separately from design decisions, failed dimensions and uncovered scope.
A no-findings report includes what was examined, not a blanket project certificate.

