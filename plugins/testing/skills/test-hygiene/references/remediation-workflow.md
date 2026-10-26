# Remediation Workflow

Mechanics for bonifying an already-degraded suite. The ladder is: measure, quarantine, consolidate, verify. Never "grand refactor of the suite": that loses the real coverage buried in the mess and blocks development for weeks. Remediation runs opportunistically, per module, alongside normal work.

## 1. Measure first: the TEST_AUDIT.md contract

`/testing:test-audit` maintains a `TEST_AUDIT.md` at the audited root. Format:

- Each run PREPENDS a `## Audit <ISO date>` section, newest first, so the file reads as its own history in addition to git's.
- The section carries a metrics table with a delta column against the previous audit section when one exists:

| Metric | Value | Delta |
|---|---|---|
| Test files | | |
| Test cases | | |
| Total runtime | | |
| Skipped/disabled | | |
| Failing | | |
| Flaky (rerun disagreement) | | |
| Orphan test files | | |
| Layer distribution (unit/integration/e2e) | | |
| Top-10 slowest (list) | | |
| Per-module coverage (when tooling exists) | | |

- Below the table: the audit findings summary from the test-suite-auditor (by severity, with file:line evidence) and the recommended remediation order.
- The file can be versioned in git as the native audit history. Commit only under
  explicit authorization; an audit request alone does not authorize a commit.

## 2. Canonical remediation

Load the `testing:test-remediation-method` skill for cause classification, quarantine,
behavior/failure-mode inventory, approval, replacement and snapshot-bound gates.
Its references contain the audit and consolidation procedures. This skill owns
placement/prevention rules and the native audit format, not a second fix loop.

## 5. Mutation testing (guidance only)

Mutation testing supplies additional evidence by mutating code and recording which tests detect changes. Equivalent, unreachable or invalid mutants require analysis; a surviving mutant alone cannot justify deletion. Configuration guidance, not a shipped runner:

| Stack | Tool |
|---|---|
| JS/TS | Stryker |
| Python | mutmut |
| JVM | PIT |
| Rust | cargo-mutants |
| .NET | Stryker.NET |

Choose a project-approved scope and cadence from measured cost, risk and CI budget;
fast changed-code runs can be commit gates while costly full-suite runs can be
scheduled. The audit consumes available reports without launching a new mutation
job. Feed valid, non-equivalent reachable survivors into investigation of missing
behavioral protection, not automatic pruning. Classify existing failures and
establish a comparable baseline before treating mutation results as gate evidence.
