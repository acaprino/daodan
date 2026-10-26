## Step 1: Preconditions and baseline

1. Load the `test-hygiene` skill of this plugin for placement/prevention and `testing:test-remediation-method` for the canonical consolidation contract.
2. Use protocol execution preflight. An inventory or dry run is read-only; mutation requires explicit inventory acceptance and an owned recovery point preserving preexisting edits.
3. Resolve the test set: every test file resolving to `<module-path>` (imports plus naming convention), wherever it lives, INCLUDING matching entries under `tests/_quarantine/` and their ledger rows.
4. Detect the runner (`--runner` overrides), configuration and collection. Absent runner or suite yields an explicit diagnosis with inspected signals; retain a static inventory instead of claiming no findings. When required checks cannot execute locally, record why and require a remote baseline for the exact starting snapshot and a remote candidate gate before closure.
5. Inventory behavioral protection, distinct failure modes and bugfix provenance. Record coverage as supporting evidence when configured. Missing coverage tooling does not change the proof to a count: each protected inventory row needs an independently justified oracle and mapped surviving check.
