# Prevention Rules

The full protocol behind each binding rule in SKILL.md. These rules are written for the agent creating tests, and every one of them is checkable at review time.

## 1. Search before writing (the protocol)

Before creating ANY test file, identify its layer and behavioral owner. For unit tests use the source-file search below. For integration, contract and e2e tests search for the intended flow, endpoint or contract; a source module already covered at another layer does not prevent a justified new behavioral scope.

1. **Derive the expected test path** from the source path using the project's convention (see rule 2). If a file exists there, extend it. Done.
2. **Glob for name variants** of the target source file `<name>` across the test tree: `test_<name>*`, `<name>.test.*`, `<name>.spec.*`, `<name>_test.*`.
3. **Grep the test tree for imports** of the target module (its module path, not just the basename) to catch tests that cover it from a misplaced file.
4. **Zero hits on all three** is the only situation in which creating a new test file is legitimate. State the evidence when creating it: what was searched, what was found.

Preference order when a hit exists:

1. Add a case to an existing test group (describe block, test class, parametrize list) covering the same behavior area.
2. Add a new test group to the existing file for the module.
3. Create a new unit file only when that source owner has no unit file. Higher-layer files require an uncovered behavioral scope, not a source module without tests anywhere.

Creating `test_foo_extra.py` next to `test_foo.py` is never acceptable. If the existing file is misplaced relative to the convention, move it as part of the same change instead of forking it.

## 2. Mirror-the-source placement (unit layer)

One deterministic location per source file. If there is exactly one plausible place where a test can live, the agent finds it with a single Glob instead of a semantic search that fails. Source-path mirroring binds the unit layer; integration, contract, and e2e files mirror a behavioral scope instead (rule 3), and their deterministic location is the layer directory plus the flow, endpoint, or contract name.

| Ecosystem | Source | Test |
|---|---|---|
| Python | `src/pkg/auth/login.py` | `tests/unit/pkg/auth/test_login.py` |
| JS/TS (separate tree) | `src/auth/login.ts` | `tests/unit/auth/login.test.ts` |
| JS/TS (colocated) | `src/auth/login.ts` | `src/auth/login.test.ts` |
| Go | `pkg/auth/login.go` | `pkg/auth/login_test.go` (same package) |
| Rust | `src/auth/login.rs` | Inline `#[cfg(test)]` module; `tests/` only for integration |
| JVM | `src/main/java/x/y/Z.java` | `src/test/java/x/y/ZTest.java` |

The project's established convention wins over this table. What is non-negotiable is that the convention is deterministic and that there is one location per source file.

## 3. One test file per source file (unit layer)

At the unit layer the inverse also holds: a test file covers exactly one source file. Integration, contract, and e2e tests are owned by a BEHAVIOR, not a source file: a checkout flow test that exercises the service, the repository, and the payment gateway together is structurally correct, not suspect. What stays forbidden at every layer is the unexplained parallel file: two files owning the same source file at unit, or the same behavioral scope above it. Shared setup goes in fixture files (`conftest.py`, `fixtures.ts`, test helpers), never in a grab-bag test file that covers "miscellaneous" behavior. Grab-bag files are where duplicates hide, because no search for a specific module ever surfaces them.

## 4. Explicit layers with budgets

Directory structure separates `unit`, `integration`, and `e2e` (or the project's equivalents). Assignment rule: a new test goes in the LOWEST layer that can express the behavior. Consequences:

- A "unit" test that needs a real database, network, or filesystem is an integration test in the wrong directory. Move it; do not mock the database to keep it in unit.
- A behavior's primary proof lives at ONE layer. Re-asserting the same failure mode through the same observable contract at another layer (a validation rule checked in a unit test, re-checked through the API, re-checked through the UI) is the most toxic duplication a suite can carry, because one behavior change breaks three tests in three places. Cross-layer overlap that protects DIFFERENT failure modes (the calculation at unit, the transaction persisting it at integration, the wire format at contract, the user completing the flow at e2e) is defense in depth, not duplication.
- Budgets (SKILL.md table) are project-tunable defaults. A layer over budget is an audit finding, not background noise.

## 5. Behavior, not implementation

The full treatment lives in the `mattpocock-skills:tdd` skill (behavior-first design, what to mock and what never to mock). The binding consequences enforced here:

- Do not mock modules internal to the project. Needing to is a design signal, not a testing technique.
- Do not test private functions, private attributes, or call sequences (`toHaveBeenCalledWith` chains that restate the implementation line by line).
- A behavior-preserving refactor must leave every test green. A test that breaks on a pure refactor is implementation-coupled and gets rewritten against the public behavior, not patched to track the new internals.

## 6. No skip markers to get green

| Ecosystem | Markers |
|---|---|
| pytest | `@pytest.mark.skip`, `@pytest.mark.xfail`, commented-out test bodies |
| Jest/Vitest/Mocha | `.skip`, `.only` left behind, `xit`, `xdescribe` |
| JUnit | `@Disabled`, `@Ignore` |
| Go | `t.Skip` outside platform guards |
| Rust | `#[ignore]` |
| .NET | `[Skip]`, `Skip = "..."` |

A skip needs a justified condition, owner and visible limitation. Supported-platform
guards and explicitly tracked expected failures can be legitimate; age alone is
not a quarantine verdict. `.only` that unintentionally suppresses the suite is a
defect. Classify underlying failures before any temporary quarantine.

## 7. Never weaken an assertion

Do not weaken tolerances, assertions or failure handling simply to get green.
Load the `testing:test-remediation-method` skill for the canonical classification before
changing or quarantining a red test. A wrong oracle can be corrected with independent
evidence; a true product regression stays active. Unknown cause remains open.

## 8. Retire tests with retired behavior

Remove a test only when its behavior is explicitly retired or its exact failure
mode has justified replacement protection in the same candidate. Moving a module,
migrating storage, renaming an endpoint or refactoring implementation does not
retire the contract. Follow usages and bugfix history before calling a test orphan;
retarget the existing protection instead of silently deleting it.
