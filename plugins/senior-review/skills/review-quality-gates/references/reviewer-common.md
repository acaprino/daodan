# Specialist review conventions

Load once per assignment, including compositions. Roles supply domain checks;
briefs supply target, snapshot, scope, permissions and delivery. Providers receive
these conventions in the brief. Reuse existing contracts and native report formats.

## Establish evidence

- Confirm candidate, required inputs and review basis. Changesets compare base and
  candidate; distinguish introduced, exposed and preexisting defects under the
  caller's policy. Content audits admit evidenced preexisting defects in scope.
  Judge plans/specs/documents against their claims; absent implementation alone
  is not a plan defect.
- Keep conclusions within the assigned perimeter. Read relevant requirements,
  effective configuration, callers, consumers and guards within admitted read/impact
  scope. Request missing scope or inputs; an unknown prerequisite remains a gap,
  never proof of inapplicability.
- Preserve source and configuration; write only the assigned report. Run checks
  only with permission in the assigned disposable environment. Record actual
  command, candidate and outcome. A tool/input/delivery failure is a review gap,
  not evidence of a product defect.
- Maps, comments, names and searches supply leads. Read source establishing the
  premise; seek guards, alternate paths and configurations that refute it. Check
  multiplicity, ownership and reachable state transitions where relevant.
  Do not consume peer findings before independent delivery. Cite used map anchors
  and preserve causal provenance.
- Establish a reachable trigger, violated requirement and observable consequence.
  A pattern or missing preferred technique alone proves nothing. Calibrate severity
  to impact; invent no percentages, loads, timings, costs, universal thresholds
  or finding quotas. Route overlaps by the violated mechanism or contract.

## Context economy and coverage

Search narrowly; expand reading as evidence requires. Load applicable references
and assigned knowledge through exact catalog bindings, once per distinct binding.
Knowledge is read-only input, not permission to execute workflows. Missing/stale
assigned knowledge fails coverage. Return existing `knowledge_usage` records with
selection, worker/scope, body/reference hashes, loaded/failed status and application;
use `[]` when unassigned. Shared worker identity does not merge assignments/scopes.

Finish assigned checks or name unchecked scope and cause. Read counts, budget
exhaustion and absence of findings never prove completion. Preserve evidence in
one report; the coordinator routes concise cross-reviewer notes after independent
delivery. Static inspection and runtime exercise are distinct coverage facts.

## Deliver once

Use the native report and existing reviewer-result envelope: `dimension`,
`reviewer`, `status` (`delivered` or `failed`), `findings`, `gaps`,
`output_path`, `knowledge_usage`. Persist at the assigned path; return that path
and a short result. Without an assigned path, deliver inline.

Each finding supplies `file`, `line`, `evidence`, `severity`, numeric
`confidence` (0–100, supported by evidence), `premise`, `premise_provenance`,
`trigger`, `counterevidence_checked`, `evidence_class` and a concrete fix direction;
include `introduced_by_candidate` when comparing candidates. Confidence describes
support, not impact or measured probability; preserve native strength labels
separately. Provenance is `independent`, `shared-context` or `mixed` according to
premise origin, not citations alone. Evidence is `derived`, `tool-reported`,
`measured` or `reproduced`; source reading proves no execution. A derived number
alone cannot justify Critical severity.

Report examined scope, completed applicable checks and gaps compactly. A complete
no-findings result has `findings: []` and that coverage account; silence is missing
delivery. A missing required input or unfinished required check makes the assignment failed (`status: failed`); preserve
partial findings and name the missing evidence/check. The coordinator checks
coverage before acceptance. Apply the working discipline supplied in the required brief. These are agent obligations; only exercised gates
prove mechanical enforcement.
Generate no score, inventory, repeated source listing or action quota unless the
native report requires it.
