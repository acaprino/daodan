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
  A pattern or missing preferred technique alone proves nothing. Where the
  project configures a linter or formatter, style and formatting are its job,
  not findings; report only what those tools cannot see. Calibrate severity
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

A job with `paths` concludes on those files and reads whatever else they need.
Its one result is the JSON reviewer-result at `output_path`: the fields above,
the job's `job_id`, `reviewer` (its role), `specialist_ids`, `scope_id`,
`candidate` and `body_sha256`, `member_results`, `read` (assigned files read in
full) and `partial` (file → why its reading or checks are incomplete, even after
a full reading). A file in `partial` neither fails the result nor makes a member
incomplete; `failed` and `incomplete` mean the job or member could not conclude
its other assigned files. Write no second report.

A finding is a hypothesis the verification panel tries to falsify. Each supplies
`file`, `line`, `evidence`, `severity`, numeric `confidence` (0-100: support by
evidence, not impact or measured probability; keep native strength labels
separately), a concrete fix direction and:

- `premise`: the single proposition whose falsity collapses the finding; minimal,
  falsifiable and scoped. Not a paraphrase of the finding ("heartbeat handling is
  incorrect") but a proposition ("no credential-bearing response path exists after
  registration").
- `premise_provenance`: `independent`, `shared-context` or `mixed` by causal
  dependence, not citation. A premise absorbed from Codebase Map output or the
  interconnect map is `shared-context` even without a cited anchor; `mixed` when
  part of it rests on shared context; `independent` only when the whole premise
  was re-derived from code, tests or documents the reviewer read.
- `trigger`: the concrete input, state or timing under which the defect
  manifests; "could fail" without a trigger is not a finding.
- `counterevidence_checked`: what was looked for that would refute the finding
  (guards, validations, callers, tests, configuration) and not found.
- `introduced_by_candidate`: true only when the candidate change causes the
  defect; applies to changeset basis and never excludes an eligible content or
  claims finding.
- `evidence_class`: `reproduced` (a test or run showed it), `tool-reported` (a tool
  in the evidence pack reported it), `measured` or `derived`; source reading proves
  no execution, and a derived number alone cannot justify Critical severity.

Report examined scope, completed applicable checks and gaps compactly. A complete
no-findings result has `findings: []` and that coverage account; silence is missing
delivery. A missing required input or unfinished required check outside `partial` makes the assignment failed (`status: failed`); preserve
partial findings and name the missing evidence/check. The coordinator checks
coverage before acceptance. Apply the working discipline supplied in the required brief. These are agent obligations; only exercised gates
prove mechanical enforcement.
Generate no score, inventory, repeated source listing or action quota unless the
native report requires it.
