---
name: test-preparation
description: >
  Prepare existing test-auditor inputs, runner/configuration diagnosis and snapshot-bound baseline evidence.
---

# Test preparation

Input: `mode=audit|consolidate`, target, runner override, scope, output root and
run permission. Output: runner/configuration diagnosis, native metrics with source
and snapshot, test inventory, baseline evidence, source intent and missing inputs.

Load the `testing:test-hygiene` skill for its runner playbook and prevention rules. Load
`project-protocol:project-protocol` for execution preflight, exact snapshot and
confined output. Read `references/<mode>.md` inside this skill. Reuse these steps
without adding another detection prompt. Caller-provided measurements must carry
source, time and snapshot; stale metrics are diagnostic evidence only.

Missing runner, disabled discovery/configuration, absent suite and unresolved
detection are distinct diagnoses. Inspect manifests, configuration, exclusions,
test paths and intended product behavior. Continue static auditing when execution
is unavailable; never report an unexecuted suite as healthy. Return the same inputs
the existing `testing:test-suite-auditor` requires and its explicit limitations.
