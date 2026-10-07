# Quarantine layout and lifecycle

Move only explicitly accepted files, retaining their relative paths:
`tests/unit/auth/test_login.py` becomes
`tests/_quarantine/unit/auth/test_login.py`. No renames obscure provenance.
For runners whose collection cannot exclude this path, choose a verified
non-collected project location and record it before moving files.

The native ledger is `tests/_quarantine/README.md`:

| Original path | Date | Category | Cause | Reason | Evidence | Owner | Return condition | Remaining protection | Gate identity |
|---|---|---|---|---|---|---|---|---|---|

Categories retain the native `orphan`, `failing`, `flaky`, `skipped` labels.
Category is the observed symptom; cause classification in the method determines
whether quarantine is eligible. Product defects and unknown causes remain active.

Configure and verify exclusion once, preserving the runner's existing settings:

| Runner | Exclusion |
|---|---|
| pytest | `norecursedirs = tests/_quarantine` or `--ignore=tests/_quarantine` |
| Vitest | Add `tests/_quarantine/**` to the existing `exclude` array |
| Jest | Add `<rootDir>/tests/_quarantine/` to `testPathIgnorePatterns` |
| Go | A non-collected directory or explicit quarantine build tag, verified with package discovery |
| Cargo | Outside the collected `tests/` and `src` trees |
| JUnit | Excluded source set in the project's build configuration |

Collection validates the layout only; it never passes the behavioral candidate gate.
An entry is processed when its module is touched. Age greater than three months
is a reason to investigate, never to delete. Retirement requires explicit inventory
acceptance plus evidence that behavior was retired or its exact failure mode has
replacement protection. Preserve real bugfix provenance and unresolved ledger rows.
Quarantine does not prove the remaining suite trustworthy or settle an unknown defect.
