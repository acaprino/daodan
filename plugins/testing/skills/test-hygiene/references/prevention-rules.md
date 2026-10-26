# Prevention Rules

The full protocol behind each binding rule in SKILL.md. These rules are written for the agent creating tests, and every one of them is checkable at review time.

## 1. Search before writing (the protocol)

Before creating ANY test file, identify its layer and behavioral owner. For unit tests use the source-file search below. For integration, contract and e2e tests search for the intended flow, endpoint or contract; a source module already covered at another layer does not prevent a justified new behavioral scope.

1. **Derive the expected test path** from the source path using the project's convention (see rule 2). If a file exists there, extend it. Done.
2. **Glob for name variants** of the target source file `<name>` across the test tree: `test_<name>*`, `<name>.test.*`, `<name>.spec.*`, `<name>_test.*`.
3. **Grep the test tree for imports** of the target module (its module path, not just the basename) to catch tests that cover it from a misplaced file.
4. **Resolve the intended owner at the intended layer.** A hit for that owner normally means extend it. Source imports at another layer do not prevent a new flow, endpoint or contract test. A new file requires evidence of an absent owner or a justified split with distinct scope, placement and fixture/lifecycle needs; state the searches and why extending the existing owner would be unsuitable.

Preference order when a hit exists:

1. Add a case to an existing test group (describe block, test class, parametrize list) covering the same behavior area.
2. Add a new test group to the existing file for the module.
3. Create a new unit file when that source owner has no unit file or a documented scope split is justified. Higher-layer files require an uncovered behavioral scope or justified split, not a source module without tests anywhere.

Creating `test_foo_extra.py` next to `test_foo.py` simply to avoid reading the owner is unacceptable. A deliberate split needs discoverable scope names and recorded ownership, rather than an unexplained suffix. If an existing file violates the established project convention, propose an owned move that preserves collection instead of forking it; colocated layouts are legitimate conventions.

## 2. Mirror-the-source placement (unit layer)

One deterministic primary location per source file, with any justified splits discoverable by scope. Source-path mirroring binds the unit layer under the project's convention; integration, contract, and e2e files mirror a behavioral scope instead (rule 3). Their deterministic location follows the project's layer layout and flow, endpoint, or contract names.

| Ecosystem | Source | Test |
|---|---|---|
| Python | `src/pkg/auth/login.py` | `tests/unit/pkg/auth/test_login.py` |
| JS/TS (separate tree) | `src/auth/login.ts` | `tests/unit/auth/login.test.ts` |
| JS/TS (colocated) | `src/auth/login.ts` | `src/auth/login.test.ts` |
| Go | `pkg/auth/login.go` | `pkg/auth/login_test.go` (same package) |
| Rust | `src/auth/login.rs` | Inline `#[cfg(test)]` module; `tests/` only for integration |
| JVM | `src/main/java/x/y/Z.java` | `src/test/java/x/y/ZTest.java` |

The project's established convention wins over this table. Ownership and justified splits must remain deterministic and discoverable.

## 3. One test file per source file (unit layer)

At the unit layer one source file is the primary subject of a test file; invoking its real collaborators or shared helpers does not create extra owners. Document any justified scope split. Integration, contract, and e2e tests are owned by a BEHAVIOR, not a source file: a checkout flow test that exercises the service, the repository, and the payment gateway together is structurally correct, not suspect. What stays forbidden at every layer is the unexplained parallel file: two files owning the same source file at unit, or the same behavioral scope above it. Shared setup goes in fixture files (`conftest.py`, `fixtures.ts`, test helpers), never in a grab-bag test file that covers "miscellaneous" behavior. Grab-bag files are where duplicates hide, because no search for a specific module ever surfaces them.

## 4. Explicit layers with budgets

Identify `unit`, `integration`, `contract`, and `e2e` (or project equivalents) through established directories, colocated paths, runner projects or explicit markers. Do not relocate a healthy suite just to impose a universal directory template. Assignment rule: a new test goes in the LOWEST layer that can prove the required contract without hiding its relevant boundary. Consequences:

- A test crossing a real database, network or filesystem boundary belongs in integration. Identify and collect it under the project's appropriate lane. An isolated service test can use a controlled boundary double; that does not establish SQL, transaction, wire or persistence correctness. Preserve real-boundary integration protection for those contracts.
- A behavior's primary proof lives at ONE layer. Re-asserting the same failure mode through the same observable contract at another layer (a validation rule checked in a unit test, re-checked through the API, re-checked through the UI) is the most toxic duplication a suite can carry, because one behavior change breaks three tests in three places. Cross-layer overlap that protects DIFFERENT failure modes (the calculation at unit, the transaction persisting it at integration, the wire format at contract, the user completing the flow at e2e) is defense in depth, not duplication.
- Budgets (SKILL.md table) are project-tunable defaults. A layer over budget is an audit finding, not background noise.

## 5. Behavior, not implementation

The full treatment lives in the `mattpocock-skills:tdd` skill (behavior-first design, what to mock and what never to mock). The binding consequences enforced here:

- Prefer real production collaborators within the behavior under test. Mock a justified architectural boundary when isolation or controlled failure injection requires it, including a project-owned adapter for real I/O. Record which contract is controlled and which real-boundary lane verifies the adapter; an internal module path alone does not determine whether a double is legitimate.
- Prefer observable outcomes over private functions, attributes or call echoes. An ordering assertion can protect an explicit protocol contract; targeted internal access can preserve an evidenced diagnostic regression. Name that purpose and assess whether a public check can replace it before proposing a rewrite. Echoing incidental implementation steps has no independent oracle.
- A failure after a claimed behavior-preserving refactor is a lead, not proof that the test is wrong. Confirm preserved behavior and the independent contract first. Rewrite incidental coupling while retaining equivalent protection; keep a true product regression active.

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

## 7. Preserve assertion protection

Assertion protection: Preserve assertions for approved behavior; correct a wrong oracle only with independent authority and evidence, while keeping valid product protection active.

Do not weaken tolerances, assertions or failure handling simply to get green.
Load the `testing:test-remediation-method` skill for the canonical classification before
changing or quarantining a red test. A wrong oracle can be corrected with independent
evidence; a true product regression stays active. Unknown cause remains open.

## 8. Retire only with evidence

Test retirement: Retire tests only for retired behavior or verified equivalent replacement protection in the same candidate; counts, coverage, age and refactoring alone are insufficient.

Remove a test only when its behavior is explicitly retired or its exact failure
mode has justified replacement protection in the same candidate. Moving a module,
migrating storage, renaming an endpoint or refactoring implementation does not
retire the contract. Follow usages and bugfix history before calling a test orphan;
retarget the existing protection instead of silently deleting it.

## 9. Isolate resources and preserve reproduction evidence

Apply the relevant items when a test uses process state, external resources or async work:

- Control clocks, timezone, randomness and scheduling where incidental. Record seeds, simulated time or synchronization conditions needed to reproduce a failure. When real time or concurrency is the contract, use bounded waits and observable synchronization rather than arbitrary sleeps.
- Restore changed environment variables, module state, patched functions and boundary doubles after each test, including failure paths. Test independence must survive reordered or repeated execution.
- Give files, temporary directories, database rows/schemas and network ports distinct ownership. Prepare known fixture state and clean up or roll back owned resources in teardown; avoid collisions between workers and runs. A real integration lane records the required service/version/configuration and checks readiness.
- Await, cancel and join tasks, streams, subscriptions and background processes on success, failure and cancellation. Assert relevant cleanup behavior through its contract; do not leave work that can alter the next test.
- Record runner command, candidate identity, configuration, service state and attempt outcomes for intermittent failures. Separate test isolation defects, environment failures and product races before disposition. Retries can gather evidence, but cannot silently replace a failing required gate with a green attempt.
