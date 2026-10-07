## Step 3: Qualitative audit (agent)

Spawn this plugin's `test-suite-auditor` agent with: the target path, the Step 2 metrics, the scope, run permission (`--no-run` propagates), and an output path of `<output-root>/findings.md`. The agent covers the judgment dimensions (orphans, duplicates, contradictions, implementation-coupling, never-failing tests) and returns the findings report. It is report-only; nothing moves in this step.

## Step 4: Write TEST_AUDIT.md

Prepend a `## Audit <ISO date>` section to `<path>/TEST_AUDIT.md` (create the file when absent) in the format defined by `remediation-workflow.md` section 1: the metrics table with deltas against the previous audit section, then the findings summary by severity from Step 3, then the recommended remediation order.

Without `--fix`, print the report path, the metrics table, and the top findings, and stop here.

## Step 5: Quarantine (only with `--fix`)

Use this method's accepted category inventory and the common project protocol: baseline, candidate gate, owned phase recovery and authorized commit. No external review fix loop is executed.

### 5a: Category acceptance gate

Build candidate batches only after the canonical cause classification below.
Removed source alone is not a confirmed orphan: follow renames/migrations and
verify the behavior was retired. Age of a skip and a red baseline are investigation
signals. Product defects and unknown causes stay active and block the affected
change; wrong oracles are repaired, environment failures route to environment/
configuration owners. Only confirmed ineligible/obsolete, unresolved environment
limitations or evidenced intermittent tests may be proposed for temporary
quarantine with remaining protection, owner, return condition and explicit acceptance.

Present the non-empty categories through the host question mechanism with multiple category choices (label: category and file count; description: sample paths). Only accepted categories proceed. This gate is never bypassed: `--yes` affects only the per-batch re-confirmation below.

### 5b: Baseline

Record the exact starting snapshot, native test results and meaningful behavior
protection. Under `--no-run`, historical metrics remain stale diagnostic evidence.
Mutation needs an executable local gate or a remote gate for this exact candidate
snapshot, with required command/configuration and job identity. A collect-only
check is structural evidence and cannot satisfy a behavior gate.

### 5c: Batch execution

Process accepted categories in fixed order, lowest ambiguity first: `orphan`, `skipped`, `failing`, `flaky`. Per batch, first capture `pre_phase_sha`, owned paths and required gate configuration:

1. Preview the exact file list and target paths (`tests/_quarantine/<original relative path>`). Confirm the batch unless `--yes`.
2. First batch only: add the runner's CI exclusion from this skill's `references/quarantine-layout.md` and create its native README ledger, preserving existing runner exclusions.
3. `git mv` each file to its mirrored quarantine path; append one ledger row per file (original path, date, category, cause, reason, evidence, owner, return condition, preserved protection and candidate gate identity).
4. Record the candidate snapshot and run its required checks. Preserve every approved behavior, distinct failure mode and bugfix regression. Neither pass counts nor line coverage establish equivalence; report unresolved or unexercised protection explicitly. Under `--no-run`, await authorized same-snapshot remote evidence instead of using collection or old CI as a pass.
5. Gate failed: use `project-protocol:project-protocol` recovery for the captured `pre_phase_sha` or exact owned pre-edit snapshot. Restore only owned changes and verified newly created artifacts; verify restoration and halt. No broad cleanup of the quarantine directory, and no deletion of artifacts created by another run.
6. Gate passed: commit the exact accepted batch only when authorized, with the candidate gate identity in its ledger.

### 5d: Refresh the audit

Refresh the current `## Audit <date>` section of `TEST_AUDIT.md` with the measured
post-quarantine numbers and remaining protection. Finalize owned audit/ledger edits
before capturing their candidate snapshot and gating an authorized commit. If the
last batch is already committed, treat this refresh as a separate owned candidate
with the protocol's required gate, not an ungated trailing commit. Run-envelope
results can record gate outcomes without changing the gated source snapshot.

### 5e: Report

Per-batch table (category, files, commit sha, gate result), the new suite status, and next steps:

- `/testing:test-consolidate <module>` for the modules ranked worst by duplicate/implementation-coupling density in Step 3.
- The quarantine lifecycle reminder from the skill: entries are processed when their module is next touched; entries older than 3 months become deletion candidates, dropped only through the consolidation approval gate with evidence beyond age.

## Output locations

- `<path>/TEST_AUDIT.md`: the native audit history (committed only when authorized).
- `<output-root>/findings.md`: the full auditor report backing the latest audit section.
- `tests/_quarantine/` plus its `README.md` ledger: only under `--fix`.
