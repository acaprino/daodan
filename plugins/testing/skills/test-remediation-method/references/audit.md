## Step 3: Qualitative audit (agent)

Dispatch `testing:test-suite-auditor` through the caller's declared isolated host harness using its actual rendered role. Supply the prepared target/snapshot, global D1/D9 metrics and provenance, runner diagnosis/configuration, requirements, scope, run permission (`--no-run` propagates), working discipline, provider root, assigned knowledge and `<output-root>/findings.md`. Canonical members own the checks; do not recreate a dimension checklist in the worker prompt. It is report-only; nothing moves in this step.

Supply the native conventions below once in the assignment. Findings require current evidence and an independent behavioral oracle, causal impact/counterevidence, confidence, cause classification and owner. Unknown causes and missing runtime evidence stay explicit. Account for every assigned member through its findings or coverage/gaps, including `member_results` when the rendered composition requires it, and return assigned knowledge usage. A missing/failed member or input blocks completion; a clean finding list does not close missing coverage. The coordinator verifies the intermediate delivery before writing the one audit history.

```markdown
### Test-Suite Audit

**Scope:** [whole suite | modules | diff range]
**Runner(s):** [detected]
**Execution:** [full run | reruns N | no-run (reasons)]
**Runner diagnosis:** [available | runner-missing | configuration-disabled | suite-absent | detection-unresolved]
**Dimensions scanned:** D1 inventory | D2 orphans | D3 skipped | D4 failing/flaky | D5 duplicates | D6 contradictions | D7 impl-coupled | D8 never-failing | D9 runtime/coverage

---

### Findings

**[CRITICAL] [Title]**
- **Location:** `file:line`
- **Evidence:** [command output line, git log line, or the pair of asserts]
- **Impact:** [one sentence]
- **Confidence:** [0-100, with unresolved premises stated]
- **Cause:** [product-defect | wrong-oracle | environment | test-isolation | intermittent | unknown]
- **Fix path / owner:** [implementation owner | testing:test-writer oracle/authoring | environment/configuration owner | consolidation | eligible quarantine]
- **Protected behavior / failure mode / bugfix provenance:** [evidence or explicitly unknown]

*(continue by severity)*

---

### False-Positive Candidates (require confirmation)

| Item | Why flagged | Why likely FP |
|------|-------------|---------------|
| `tests/unit/api/test_routes.py` | 40 near-identical cases | Parametrized table; one behavior per row |

---

### Statistics

| Dimension | Findings | Affected files | Wasted runtime (est.) |
|-----------|----------|----------------|------------------------|
| D1 .. D9 | N | N | Xs |

---

### Recommended Remediation Order

1. Resolve product/oracle/environment diagnoses and missing runner/configuration/absent-suite findings; keep unresolved protection visible
2. `/daodan:maintain-tests` consolidation for the worst modules by D5/D7 density: [ranked list]
3. [Coverage-absence modules worth new tests, if D9 found any]
```

## Step 4: Write TEST_AUDIT.md

Prepend a `## Audit <ISO date>` section to `<path>/TEST_AUDIT.md` (create the file when absent) in the format defined by `remediation-workflow.md` section 1: the metrics table with deltas against the previous audit section, then the findings summary by severity from Step 3, then the recommended remediation order.

Without `--fix`, print the report path, the metrics table, and the top findings.
For requested HTML or useful navigation/comparison, the coordinator reads
`references/human-view.md` in this skill and renders the completed native audit
before normal delivery and run closure. Do not proceed to quarantine.

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
5. Gate failed: use `work-controller:work-record` recovery for the captured `pre_phase_sha` or exact owned pre-edit snapshot. Restore only owned changes and verified newly created artifacts; verify restoration and halt. No broad cleanup of the quarantine directory, and no deletion of artifacts created by another run.
6. Gate passed: commit the exact accepted batch only when authorized, with the candidate gate identity in its ledger.

### 5d: Refresh the audit

Refresh the current `## Audit <date>` section of `TEST_AUDIT.md` with the measured
post-quarantine numbers and remaining protection. Include the per-batch table,
suite status and Step 5e next steps in that native section. Finalize owned audit/ledger edits
before capturing their candidate snapshot and gating an authorized commit. If the
last batch is already committed, treat this refresh as a separate owned candidate
with the protocol's required gate, not an ungated trailing commit. Run-envelope
results can record gate outcomes without changing the gated source snapshot.

### 5e: Report

Per-batch table (category, files, commit sha, gate result), the new suite status, and next steps:

- Consolidation of each module (mode `consolidate`, through `/daodan:tidy-repo`) for the modules ranked worst by duplicate/implementation-coupling density in Step 3.
- The quarantine lifecycle reminder from the skill: entries are processed when their module is next touched; entries older than 3 months become investigation candidates. Retirement still requires accepted inventory and evidence of retired behavior or verified equivalent replacement beyond age.

For requested HTML or useful navigation/comparison, the coordinator reads
`references/human-view.md` in this skill after the refreshed native audit and
required gates are final, before run closure. Render no intermediate audit that
later quarantine batches or refreshes would invalidate.

## Output locations

- `<path>/TEST_AUDIT.md`: the native audit history (committed only when authorized).
- `<output-root>/findings.md`: the full auditor report backing the latest audit section.
- `tests/_quarantine/` plus its `README.md` ledger: only under `--fix`.
