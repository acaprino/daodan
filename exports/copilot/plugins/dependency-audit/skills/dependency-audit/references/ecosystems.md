<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. fetch
retrieves a known URL and does not search: network search needs a search tool
registered in this session. A user question is asked in the reply, and the run
waits for the answer. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
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

# Per-ecosystem tool matrix

Commands for vulnerability audit, outdated detection, license inventory, and dependency-tree queries, per ecosystem. Two rules apply everywhere:

- **Flags drift across tool versions.** If a listed flag errors, drop to the tool's default output and parse the text. Never fake machine-readable output that a tool did not produce.
- **Prefer the package manager the lockfile identifies.** Running a different manager's audit against someone else's lockfile produces incomplete or misleading results.

## Summary

| Ecosystem | Detect via | Audit | Outdated | Licenses |
|---|---|---|---|---|
| npm | `package-lock.json` | `npm audit --json` | `npm outdated --json` | `license-checker` |
| pnpm | `pnpm-lock.yaml` | `pnpm audit --json` | `pnpm outdated` | `pnpm licenses list` |
| yarn | `yarn.lock` | `yarn audit --json` (classic) / `yarn npm audit --json` (berry) | `yarn outdated` (classic) | `license-checker` |
| bun | `bun.lock` / `bun.lockb` | `bun audit` | `bun outdated` | `license-checker` |
| Python | `pyproject.toml`, `requirements.txt`, `uv.lock`, `poetry.lock` | `pip-audit -f json` | `pip list --outdated --format json` | `pip-licenses --format=json` |
| Rust | `Cargo.toml` / `Cargo.lock` | `cargo audit --json` | `cargo outdated` | `cargo license` |
| Go | `go.mod` / `go.sum` | `govulncheck -json ./...` | `go list -u -m -json all` | `go-licenses report ./...` |
| Ruby | `Gemfile` / `Gemfile.lock` | `bundler-audit check --update` | `bundle outdated` | `license_finder` |
| PHP | `composer.json` / `composer.lock` | `composer audit --format=json` | `composer outdated --format=json` | `composer licenses` |
| Java | `pom.xml`, `build.gradle(.kts)` | OWASP dependency-check plugin | `mvn versions:display-dependency-updates` / versions plugin | license-maven-plugin |
| .NET | `*.csproj`, `packages.config` | `dotnet list package --vulnerable --include-transitive` | `dotnet list package --outdated` | `nuget-license` |
| Any | lockfiles | `osv-scanner --recursive .` | - | - |

## JavaScript / TypeScript (npm, pnpm, yarn, bun)

- Identify the manager from the lockfile before running anything. Mixed lockfiles (two managers' lockfiles side by side) are themselves a hygiene finding; report them.
- `npm audit --json` (registry advisory data; requires a lockfile). Parse the `vulnerabilities` map: entries carry `severity`, `via` (chain to the advisory), `range`, `fixAvailable`. `fixAvailable: { isSemVerMajor: true }` marks fixes that need a major jump: those go to the individual-review bucket, never auto-applied.
- Yarn classic `yarn audit --json` emits NDJSON (one JSON object per line); berry uses `yarn npm audit --json`.
- Direct vs transitive: `npm ls <pkg> --all`, `pnpm why <pkg>`, `yarn why <pkg>`.
- Licenses: `npx license-checker --json` (or the maintained `license-checker-rseidelsohn` fork); both read installed `node_modules`, so install first. pnpm ships `pnpm licenses list` natively.
- Registry metadata (supply-chain steps): `npm view <pkg> time --json`, `npm view <pkg> maintainers`.

## Python

- `pip-audit` (PyPA; sources: PyPI advisory db + OSV). Modes: `pip-audit` against the active environment, `pip-audit -r requirements.txt` against a requirements file.
- uv projects: `uv export --format requirements-txt > /tmp/req.txt` then `pip-audit -r /tmp/req.txt`, or `uvx pip-audit` inside the project environment.
- Poetry: `poetry show --outdated` for lag; export for pip-audit: `poetry export -f requirements.txt`.
- Licenses: `pip-licenses --format=json` reads installed metadata; run in the project environment.

## Rust

- `cargo audit --json` (RustSec advisory db; install: `cargo install cargo-audit`). Reads `Cargo.lock`.
- Outdated: `cargo outdated` (install: `cargo install cargo-outdated`).
- Licenses: `cargo license` (install: `cargo install cargo-license`); when the project carries a `deny.toml`, prefer `cargo deny check licenses` since it evaluates the project's own policy.
- Reverse tree: `cargo tree -i <crate>`.

## Go

- `govulncheck -json ./...` (install: `go install golang.org/x/vuln/cmd/govulncheck@latest`). Call-graph aware: it distinguishes vulnerabilities in *called* code from merely *imported* modules. Report the distinction verbatim; it is the tool's headline feature and materially changes priority.
- Outdated: `go list -u -m -json all` (entries with an `Update` field lag).
- Licenses: `go-licenses report ./...` (install: `go install github.com/google/go-licenses@latest`).
- Why is it here: `go mod why <module>`, full graph: `go mod graph`.

## Ruby

- `bundler-audit check --update` (`--update` refreshes the local ruby-advisory-db copy first; that flag updates the advisory database, not the project).
- Outdated: `bundle outdated`.
- Licenses: `license_finder` (multi-ecosystem, works for Ruby when Bundler is present).

## PHP

- `composer audit --format=json` (Composer >= 2.4; sources: Packagist security advisories).
- Outdated: `composer outdated --format=json` (`--direct` limits to direct deps).
- Licenses: `composer licenses`.

## Java (Maven / Gradle)

- Vulnerabilities: OWASP dependency-check (`mvn org.owasp:dependency-check-maven:check`, or the `dependency-check-gradle` plugin). It downloads NVD data on first run, which is slow and may need an NVD API key; if the project has not configured it, report the gap and offer `osv-scanner` against the build files as the lighter alternative rather than injecting build plugins uninvited.
- Outdated: `mvn versions:display-dependency-updates`; Gradle: the ben-manes `versions` plugin (`gradle dependencyUpdates`) when applied.
- Licenses: `license-maven-plugin` when configured; otherwise report the gap.

## .NET

- `dotnet list package --vulnerable --include-transitive` (advisory source: GitHub Advisory Database via NuGet).
- Outdated: `dotnet list package --outdated`.
- Licenses: `nuget-license` dotnet tool when installed; otherwise report the gap.

## Cross-ecosystem second source: osv-scanner

`osv-scanner --recursive <path>` scans lockfiles across all of the above against OSV.dev. Use it (a) as the fallback when an ecosystem's native tool is missing, (b) as a second opinion beside native results. Label its findings as osv-scanner output and report source disagreements side by side; do not merge them into one deduplicated list silently.
