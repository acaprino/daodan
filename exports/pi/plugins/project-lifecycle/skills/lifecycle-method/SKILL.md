---
name: lifecycle-method
description: >
  Coordinate complete AI development work across code, tests, project knowledge and artifacts.
  TRIGGER WHEN: running project-lifecycle assess, repair, change, verify or consolidate, or explicitly taking responsibility for project coherence.
  DO NOT TRIGGER WHEN: an isolated specialist audit or a single factual answer is sufficient.
---

> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/` and `prompts/`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

# Project lifecycle

Own the requested outcome and its consequences. Keep the work proportional to risk,
scope and authorization. Load the project-protocol:project-protocol skill first; it owns run
records, snapshots, verification and recovery. This skill owns decisions and dispatch,
not a second set of specialist detection prompts.

## Entry and state

Inputs: operation, project root, objective and intention source; optional target,
focus, depth, run ID, plan ID, output root and prior evidence. Detect existing material
before proposing new files. Read project instructions and distinguish approved intent
from implemented behavior. Code alone cannot settle contradictory requirements.

Use the installed project-protocol run_state.py helper through that skill. Its CLI:
init --project ROOT --payload INPUT.json [--run-id ID] [--out INTERNAL_ROOT];
show or validate --project ROOT --run-id ID [--out INTERNAL_ROOT];
update --project ROOT --run-id ID --expected-revision N --payload PATCH.json;
resume --project ROOT --run-id ID --payload CONTEXT.json [--out INTERNAL_ROOT].
Payload files are run-owned inputs. Never guess a cache path to another plugin.

Initialization payload: operation, objective, scope {paths, focus}, authorizations,
budget, phases, plan, deliveries and required_gates. Preserve the helper's exact
project identity and snapshot. Save the authoritative work.json inside the run.
On resume, supply current authorizations and validate the exact run, workspace,
scope and snapshot. The latest completed X-ray or another session's report is not a
resume target.

Preview is the default for assess/repair/retention. --fix authorizes in-scope edits;
--commit additionally authorizes commits. Neither authorizes a push or permanent
artifact deletion by itself. Existing human authorization persists in its scope.
State missing permissions and actual design ambiguities against a concrete plan.

Default assessment depth is quick, one initial audit round, at most five selected workers
in total, including documentary workers from reused methods. Selection is a
budgeted coverage plan; a broad focus does not bypass that cap. Declare unexamined
dimensions and offer a larger explicitly selected depth when needed.
Before dispatch, show scope, selected dimensions, likely expensive steps and gaps.
--depth standard broadens evidence, --depth deep requests comprehensive work.
Prompt budgets are instructions; do not claim the host enforces tokens. Unknown
consumption is unknown. Reuse a delivery only when role version, input fingerprints,
scope and dependencies remain valid.

## Canonical methods

Load the selected skills before their operation: project-knowledge:project-knowledge,
project-knowledge:instructions-method and project-knowledge:readme-craft for knowledge;
senior-review:review-preparation and senior-review:review-consolidation for assessment
evidence; senior-review:review-method for candidate correctness review;
testing:test-preparation and testing:test-remediation-method for suite operations;
abstraction-architect:abstraction-architect for structural diagnosis;
Load the codebase-xray:xray-method skill for static context.
Load the repo-hygiene:repo-hygiene skill for workspace operations.
Load the clean-code:readability-method skill for readability. Load only methods required
by the requested scope, never a second detector prompt.

| Need | Load or dispatch |
|---|---|
| Static context and exact X-ray run binding | codebase-xray:analyze, in coordinator context |
| Candidate correctness, including applicable stack specialists | senior-review:review-method |
| Assessment provenance consolidation | senior-review:review-preparation and senior-review:review-consolidation |
| Application subtraction | senior-review:application-cleanup-method |
| Suite preparation and remediation | testing:test-preparation and testing:test-remediation-method |
| Test authoring | testing:test-writer |
| Structural diagnosis | abstraction-architect:abstraction-architect and its auditor |
| Durable instructions | project-knowledge:instructions-method |
| Guide/documentation preparation, audit and apply | project-knowledge:project-knowledge |
| README | project-knowledge:readme-craft |
| Workspace detection and reversible application | repo-hygiene:repo-hygiene |
| Readability | clean-code:readability-method |
| General development planning/execution | superpowers:brainstorming, superpowers:writing-plans, superpowers:executing-plans or superpowers:subagent-driven-development |

The X-ray is the single declared workflow-in-context exception. Do not recursively
launch lifecycle workflows or pretend TOML invoke executes a workflow. Load the
operation reference below; perform its methods in this context.

## Operation references

- assess: read <plugin-root>/skills/lifecycle-method/references/assess.md.
- repair: read <plugin-root>/skills/lifecycle-method/references/repair.md.
- change: read <plugin-root>/skills/lifecycle-method/references/change.md.
- verify: read <plugin-root>/skills/lifecycle-method/references/verify.md.
- consolidate: read <plugin-root>/skills/lifecycle-method/references/consolidate.md.
- Native report conversion: read <plugin-root>/skills/lifecycle-method/references/native-reports.md.

## Delivery and closure

Keep raw specialist payloads, role/version/input/output hashes, scope, status,
evidence and declared gaps. Schema-valid means structurally valid. Missing evidence
does not become an empty no-findings result. Missing delivery remains missing.
Use native_reports.py to wrap payload provenance; it does not validate their meaning.

Each plan action identifies finding IDs, disposition (retain, correct, merge, retire
or clarify), owner, canonical method, prerequisites, authorization, target paths and
gate. Native seven-way workspace dispositions remain present. Deduplicate by
behavior/concept, retain contradictions, and distinguish corroboration from shared
premise echo. Two reviewers with one inherited premise are not two confirmations.

result.json follows project-protocol's project-result envelope. Reference each
specialist's native report, declared limitations, outstanding actions and evidence
of checks. Account for every expected delivery and required gate before marking the
run complete. Preserve a failed or interrupted state when requirements remain unmet.

Validate the final result with run_state.py validate --project ROOT --run-id ID
--result RESULT_PATH. Its record correspondence check is distinct from reading and
verifying the specialist evidence. Add newly discovered mandatory gates to the
append-only required_gates list before executing them; never remove a failed gate.

Reports include requested/read/runtime-exercised coverage separately, checks with
their exact candidate snapshot, decisions, changes, remaining limits and next
actions. Consolidation adds bytes moved and bytes deleted. Never claim runtime
coverage from source inspection, correctness from passing self-generated tests, or
disk recovery from a quarantine move.

