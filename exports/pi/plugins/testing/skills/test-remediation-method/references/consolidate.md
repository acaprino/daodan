## Step 2: Behavior inventory (always, before any code)

Read every test in scope and produce the inventory table. Track behavior and observable contract together with the distinct failure mode, oracle source and bugfix history. Similar test names and equal counts do not establish duplication.

| Behavior / contract | Failure mode | Oracle source | Bugfix provenance | file:line | Duplicate of | Value (high/low/none) | Reason |
|---|---|---|---|---|---|---|---|

Flag separately, each with evidence:

- **Contradictory pairs**: tests asserting incompatible outcomes for the same input/state.
- **Implementation-coupling candidates**: internal mocks, call-echo asserts, private access. Confirm the actual boundary or diagnostic purpose before declaring these defects; preserve justified protection.
- **Never-failing**: no asserts, tautologies, everything mocked.
- **Quarantined entries** for this module, each with a keep (behavior worth preserving in the rewrite) or drop proposal. A drop proposal cites evidence beyond age: feature removed, replacement coverage, temporary origin, no bug-fix provenance.

Under `--dry-run`, print the inventory and stop.

## Step 3: Safety-net check

Determine critical flows and failure modes from the project contract and existing evidence. Where meaningful protection is missing, use `testing:test-writer` to add the justified checks at the lowest sufficient layer before deletion. No fixed test quota or universal e2e prerequisite proves safety. Browser checks use the `developer-essentials:e2e-testing-patterns` skill, a required upstream dependency; check that the current host can load it before accepting a browser lane. Missing upstream capability leaves that lane open, without substituting an improvised method or forcing browser tests for non-browser behavior.

## Step 4: Approval gate

Present the inventory through the host question mechanism, grouped per owner (source file for unit tests, behavioral scope above that layer): the keep-list (behaviors the rewrite will cover) and the delete-list (duplicates, never-failing, dropped quarantine entries). Unanswered rows default to KEEP. No flag bypasses this gate. Contradictory pairs need an explicit ruling: which behavior is the correct one (check the authorized product contract, historical bugfix evidence and independent oracle before proposing; the current implementation cannot declare itself correct).

## Step 5: Rewrite

One primary file per owner at the correct layer, covering exactly the approved behaviors plus any evident gaps the user approved, with justified scope splits documented. Follow the established mirrored or colocated convention at unit; use behavioral ownership at integration, contract, and e2e. Follow the prevention rules of the test-hygiene skill; write test content behavior-first per the `mattpocock-skills:tdd` skill (upstream mattpocock/skills, a hard dependency of this plugin; if unavailable, stop and tell the user to install it: `claude plugin marketplace add mattpocock/skills`, then `claude plugin install mattpocock-skills@mattpocock`).

## Step 6: Replace originals atomically

Capture `pre_phase_sha` and the owned file snapshot before rewriting/removing any
original. Preserve bugfix provenance in the inventory. Rewrite and remove only
approved duplicate/retired files in the same candidate; do not leave parallel
suites. Do not erase unresolved ledger entries or historical proof before the
replacement has been validated. Both changes belong to the same authorized commit.

## Step 7: Verify before commit

Use `project-protocol:project-protocol` to bind the required checks to the exact
candidate snapshot, required command/configuration and job identity. Map each
approved protected behavior and distinct failure mode to a surviving check with
an independent oracle. A bugfix regression survives unless its behavior is
explicitly retired or its exact failure mode has justified replacement protection.
Coverage and test counts are descriptive supporting evidence, never the gate.
Required lanes that cannot execute locally await authorized same-snapshot remote
results; an old green job, different configuration or collection-only run is open.

On a failed gate restore the owned pre-edit snapshot or `pre_phase_sha` through the
protocol, verify originals and earlier successful phases survive, then halt.
Hard reset is available only in an exclusively owned clean isolated worktree.
After successful gate commit only with authorization. If an already published
owned commit needs recovery, use an authorized revert rather than rewriting shared
history, and gate the recovery snapshot too.

## Step 8: Report

- Before/after table: files, test cases, runtime, coverage.
- Behaviors dropped, each with the user's recorded reason from Step 4.
- Quarantine entries processed and entries remaining for other modules.
- Suggested next module by `/testing:test-audit`'s latest remediation ranking, when a `TEST_AUDIT.md` exists.
