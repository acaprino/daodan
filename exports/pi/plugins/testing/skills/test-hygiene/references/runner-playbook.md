<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

# Runner Playbook

Detection signals and measurement commands per test runner. Used by `/testing:test-audit`, `/testing:test-consolidate`, and the test-suite-auditor. Every command here is read-only with respect to the code; commands that RUN the suite are marked, and the caller decides whether running is permitted (`--no-run`).

## Detection

Check in this order; the first match wins unless the project visibly uses several stacks (then report each).

| Runner | Detection signal |
|---|---|
| pytest | `pytest.ini`, `[tool.pytest.ini_options]` in `pyproject.toml`, `conftest.py`, `setup.cfg [tool:pytest]` |
| Vitest | `vitest.config.*`, `"vitest"` in package.json devDependencies |
| Jest | `jest.config.*`, `"jest"` key or devDependency in package.json |
| Mocha | `.mocharc.*`, `"mocha"` devDependency |
| go test | `go.mod` plus any `*_test.go` |
| cargo test | `Cargo.toml` plus `#[test]` or `tests/` dir |
| JUnit (Gradle) | `build.gradle(.kts)` with `test` task, `src/test/java` or `src/test/kotlin` |
| JUnit (Maven) | `pom.xml` with surefire, `src/test/java` |
| dotnet test | `*.csproj` with xunit/nunit/mstest package refs |
| RSpec | `.rspec`, `spec/` dir, `rspec` in Gemfile |
| PHPUnit | `phpunit.xml(.dist)`, `phpunit` in composer.json |

## Measurement commands

| Runner | List tests (no run) | Run with timing (RUNS) | Count skipped | Coverage (RUNS) |
|---|---|---|---|---|
| pytest | `pytest --collect-only -q` | `pytest -q --durations=20` | grep `skip\|xfail` markers; `pytest -rs` summary | `pytest --cov=<pkg> --cov-report=term-missing` (pytest-cov) |
| Vitest | `vitest list` | `vitest run --reporter=verbose` | grep `\.skip\|\.todo`; reporter summary | `vitest run --coverage` |
| Jest | `jest --listTests` | `jest --verbose` | grep `\.skip\|xit\|xdescribe`; reporter summary | `jest --coverage` |
| Mocha | `mocha --dry-run` (10+) | `mocha --reporter spec` | grep `\.skip`; pending count in output | via nyc: `nyc mocha` |
| go test | `go test -list '.*' ./...` | `go test -v ./...` (per-test timing in output) | grep `t\.Skip`; `--- SKIP` lines | `go test -coverprofile=cover.out ./...` then `go tool cover -func=cover.out` |
| cargo test | `cargo test -- --list` | `cargo test -- --nocapture` (use `cargo nextest run` for per-test timing when available) | grep `#\[ignore\]`; `ignored` count in output | `cargo llvm-cov` or `cargo tarpaulin` when configured |
| Gradle | `gradle test --dry-run` (approx) | `gradle test` then read `build/test-results/test/*.xml` (has per-test `time`) | `@Disabled\|@Ignore` grep; `skipped` attr in XML | JaCoCo report when the plugin is applied |
| Maven | n/a; read surefire reports after run | `mvn test` then `target/surefire-reports/*.xml` | `skipped` attr in XML | JaCoCo when configured |
| dotnet | `dotnet test --list-tests` | `dotnet test --logger "trx"` (per-test times in trx) | `Skip=` grep; `skipped` in summary | `dotnet test --collect:"XPlat Code Coverage"` |
| RSpec | `rspec --dry-run -f doc` | `rspec --profile 20` | grep `skip\|pending\|xit`; pending count | SimpleCov when configured |
| PHPUnit | `phpunit --list-tests` | `phpunit --log-junit report.xml` (per-test times) | `markTestSkipped` grep; summary | `phpunit --coverage-text` (xdebug/pcov) |

Notes:

- **Per-module coverage** means the report broken down by source path, not the aggregate percentage. pytest-cov `term-missing`, `go tool cover -func`, JaCoCo XML, and lcov reports all provide it; the aggregate number alone is not a usable audit metric.
- When a command above is missing from the project (no coverage plugin, no nextest), report the metric as "tooling absent" rather than improvising an install. Installing tooling is a user decision.

## Flaky detection

Intermittence is demonstrated by disagreement under comparable recorded conditions,
never inferred from style alone. It is an observation: a product race, environment
failure or test isolation defect still needs classification before quarantine.

1. Preferred: rerun the suite (or the suspect subset) 3-5 times and diff the outcomes. `pytest -p no:randomly --lf`, `vitest run --retry=0` repeated, `go test -count=5 ./pkg/...`, `cargo test` repeated.
2. Where CI history is accessible (`gh run list` / `gh api`), compare attempts of the same candidate, command/configuration and service lane. Preserve job/attempt identities; changed environments cannot be treated as identical runs merely because the commit matches.
3. Static signatures justify SUSPICION only (report as candidates, not findings): real timestamps or `sleep` in tests, shared mutable module state, order-dependent fixtures, unmocked network calls, port or tmpdir collisions.
4. Randomized-order plugins (`pytest-randomly`, Jest `--randomize`) convert order-dependence into reproducible failures; note their absence in the audit when order-coupling is suspected.
5. Apply prevention rule 9 to state/resource leads. Keep seeds, ordering, clock and service state with the attempt evidence. Record all outcomes; retries cannot hide a failing required gate. An evidenced product race keeps active regression protection.
