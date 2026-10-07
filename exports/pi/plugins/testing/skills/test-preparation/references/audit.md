## Step 0: Pre-flight

1. Load the `test-hygiene` skill of this plugin. Its `references/runner-playbook.md` drives Steps 1 and 2; its `references/remediation-workflow.md` defines the `TEST_AUDIT.md` format and the quarantine protocol used below.
2. Under `--fix`, use the protocol execution preflight: isolated exclusive workspace, preserved starting snapshot, explicit category/scope and commit authorization. Audit reports remain read-only except for their confined output.

## Step 1: Runner detection

Detect the runner(s) per the playbook's detection table; `--runner` overrides. Multiple stacks detected: audit each, one section per runner. No runner detected: inspect configuration, source intent and discovery exclusions. Record one of `runner-missing`, `configuration-disabled`, `suite-absent` or `detection-unresolved` with inspected signals and impact. Continue static source/test discovery and dispatch the auditor with execution unavailable; this is a finding/input limitation, not a reason to skip the audit. Never claim a test passed when it was not run.

## Step 2: Mechanical measurement

Collect through the host shell, using the playbook's per-runner commands:

1. Test file list and per-layer counts (list-tests command; no execution).
2. Skip/disable marker counts (grep table from the skill's `prevention-rules.md` section 6).
3. Unless `--no-run`: one timed full run (pass/fail/skip counts, total runtime, top-10 slowest), plus 2 to 4 reruns of the failing set for flaky classification, plus per-module coverage when tooling is configured.
4. Under `--no-run`: pull the same numbers from CI (`gh run list` / `gh api`) or the newest local report artifacts (junit XML, coverage files); mark every reused number `stale` with its source and date.
