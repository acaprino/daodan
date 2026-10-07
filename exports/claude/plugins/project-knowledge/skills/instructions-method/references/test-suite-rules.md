# Condensed test-suite rules

Locally authored policy distilled from this marketplace's testing methods.
This block is self-contained for the target project. Procedure, runner choices,
quarantine and consolidation belong to testing, rather than instruction files.

Offer the block when tests exist or are explicitly planned. Preserve equivalent
project rules and flag inverted or weakened obligations. A project without tests
does not receive a finding solely because this block is absent.

```markdown
## Test-Suite Rules

Test ownership: source at unit; behavior at integration, contract and e2e.

1. Search before writing: find the existing owner for the intended layer and behavioral scope, and extend it. A parallel file for the same owner requires a justified scope split.
2. Unit tests mirror source ownership (for example `src/foo/bar.py` maps to `tests/unit/foo/test_bar.py`), following this project's convention. Integration, contract and e2e tests belong to a flow, endpoint or contract and may span several source modules.
3. Keep test layers explicit (unit, integration, e2e), each in its own directory with a runtime budget. A new test goes in the lowest layer that can express the behavior.
4. Test behavior through public interfaces, never implementation details. A refactor that preserves behavior must not break tests.
5. Never mark a test skipped (`.skip`, `xfail`, `@Disabled`, or equivalent) to make CI pass. Fix it, or quarantine it with a tracked reason.
6. Never weaken an assertion to make a failing test pass. A failing assertion is a signal about the code, not an obstacle in the test.
7. Retire tests only with retired behavior, in the same commit. Refactors, renames and migrations preserve and retarget meaningful protection.
```
