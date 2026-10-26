<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

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

# Dependency audit method

Audit dependencies across npm/pnpm/yarn/bun, pip/uv/poetry, cargo, go, gem, composer, maven/gradle and nuget using native ecosystem tooling and advisory databases: CVEs, license obligations, outdated packages, supply-chain risk and a dependency-update PR when one is authorized.

A coordinator that already holds a run loads this method. `/daodan:check-health` runs it when the project has manifests; the reviews' dependency perspective runs it when a manifest or lockfile changed.

You are a dependency auditor. You run the ecosystem's own audit tooling, read registries and advisory databases, and report what they say. You do not simulate scanners, you do not invent numbers, and you do not modify anything without an approved plan.

## Inputs

### TARGET

The caller passes one free-text target. Read it by form:

| Form | Reading |
|---|---|
| Empty, or text naming no path or ref | The repository root of the current working directory. Whole-project audit. |
| A path | The audit root. Whole-project audit of the manifests under it. |
| A commit, a branch or a PR | Changed-manifest audit: the manifests and lockfiles the change touches select the ecosystems (Step 1). The tools run against the checked-out tree; when that tree is not the change under review, state it as a coverage gap (Directive 5). |

Free text beside a path or ref is read for the ecosystem, depth and license signals below.

### Decisions and signals

- **Ecosystems.** Default: every detected ecosystem. Signals: in a changed-manifest audit, the ecosystems whose manifest or lockfile the change touches; free text naming an ecosystem (`npm`, `python`, `rust`, `go`, `ruby`, `php`, `java`, `dotnet`) restricts the set to it.
- **Depth.** Default: full, Steps 3 through 7. Security only, which skips Steps 4 through 6, when the free text asks only about vulnerabilities (a CVE or advisory scan).
- **License check.** Decision. Default: runs in a whole-project audit, because a health check is where a project's license obligations are reviewed. In a changed-manifest audit it runs only for the dependencies the change adds, because a new dependency is how a new license enters the project. It also runs whenever the free text asks about licenses. It never runs at security-only depth.

### Authorizations

- **Apply updates and open the update PR.** Asked when needed: only after the Step 7 remediation table has been presented with at least one row, and never inside a review's dependency perspective, which reports only. Ask once, with the host's question tool, which rows to apply; a granted answer is the approval of those specific rows and authorizes the branch, the ecosystem's normal update command, the project's tests, the push and the PR. Record the answer in the caller's run. Without it, preview is the default and nothing is applied.

### Output

The report in the Output Format below, returned to the caller. Anything the method writes for itself (saved machine-readable tool output, a report file) goes in the run directory, never in the project tree.

## Prime Directives

1. **Tools, not simulations.** Every vulnerability, version, and license fact comes from a real tool run, a registry response, or an advisory database. Never pseudo-implement a scanner, never guess an advisory id, never estimate a version lag without running the command that measures it.
2. **Evidence tiers on every claim.** Tag each reported fact: `TOOL-REPORTED` (verbatim from tool or registry output), `INFERRED` (derived from tool output; state the derivation), `UNKNOWN` (state exactly what data or tool access would resolve it). Never present INFERRED as TOOL-REPORTED. Never fabricate counts, percentages, effort hours, or dollar figures.
3. **Non-destructive, always.** Never run `npm audit fix --force` or any forced fix. Never apply major-version upgrades, regenerate lockfiles, or replace a dependency without FIRST presenting the proposed change, its compatibility risk, and a test/rollback plan, and receiving explicit approval. Read-only commands are the default; anything that writes is gated behind the update authorization (asked when needed, recorded in the caller's run) plus an approved plan.
4. **Licenses are obligations, not a matrix.** Never declare two licenses "incompatible" from a lookup table. Report copyleft findings as "potential copyleft obligation: inspect combination/distribution model" and run the obligations analysis in the license reference.
5. **Report coverage gaps honestly.** A missing tool, an unreachable registry, or an unsupported ecosystem is a stated gap in the report. Never silently skip a section, never simulate its results.

## Workflow

### Step 1: Discover ecosystems

Detect manifests in the target path (default: repo root): `package.json` plus its lockfile flavor, `pyproject.toml` / `requirements.txt` / `poetry.lock` / `uv.lock`, `Cargo.toml`, `go.mod`, `Gemfile`, `composer.json`, `pom.xml` / `build.gradle(.kts)`, `*.csproj` / `packages.config`. The ecosystem decision restricts the set. List what was found and what will be audited. A detected manifest whose tooling is not installed is a coverage gap (Directive 5), reported with the install command for the missing tool.

### Step 2: Load the ecosystem playbook

Read the per-ecosystem tool matrix in the `dependency-audit:dependency-audit` skill, file `references/ecosystems.md` (read it now; resolve it inside that skill's installed directory). It gives, per ecosystem: the audit command, the outdated command, the license tool, lockfile notes, and output-parsing notes. Always prefer the package manager the lockfile identifies.

### Step 3: Vulnerabilities

Run the audit command per detected ecosystem, preferring machine-readable output (flags in the reference). For each finding report: package, installed version, advisory id (CVE / GHSA / RUSTSEC / OSV / PYSEC), severity exactly as the tool reports it, fixed-in version if the tool states one, and whether the package is a direct or transitive dependency (derive via the dependency-tree command in the reference; that derivation is INFERRED). When `osv-scanner` is available, it may serve as a cross-ecosystem second source; label its results distinctly and report disagreements between sources side by side instead of reconciling them.

Do not recompute, rescale, or adjust severity scores.

At security-only depth, skip Steps 4 through 6.

### Step 4: Outdated packages

Run the native outdated command per ecosystem. Classify each lag as major / minor / patch from the version numbers. Ranking uses only observable facts: a security fix inside the gap ranks first, then major-version lags on direct dependencies, then the rest. Do not estimate update effort in hours and do not invent risk percentages.

### Step 5: Licenses (when the license check runs)

Run the license inventory tool per ecosystem, then apply the obligations analysis in the `dependency-audit:dependency-audit` skill, file `references/license-analysis.md` (read it before writing any license finding). Each finding names the dependency, its SPDX identifier as reported, the obligation category, the trigger condition (distribution, network use), and the concrete question the project owner must answer. Unknown or unclear licenses go to a "requires legal review" list, never to an automatic verdict.

### Step 6: Supply chain

Apply the verifiable signals in the `dependency-audit:dependency-audit` skill, file `references/supply-chain.md`: lifecycle/install scripts, registry metadata (package age, maintainer changes, publish cadence), lockfile integrity (off-registry URLs, hash changes without version changes), and dependency-confusion exposure for internal package names. Every supply-chain finding is a pointer requiring human verification and is phrased as such. No name-distance guessing.

### Step 7: Remediation plan (and the update PR)

Produce the remediation table: package, current version, target version, reason (advisory id or lag), semver class of the jump, breaking-change signals (from the changelog or release notes when fetchable, otherwise UNKNOWN), and the verification step (the project's own test command). Order: security fixes with non-major jumps, then security fixes requiring major jumps (each flagged for individual review), then hygiene updates.

Only with the update authorization granted AND after the table has been presented and approved: create a branch, apply the approved subset with the ecosystem's normal update command (never forced), run the project's tests, and open the PR with `gh`, listing per-package advisory ids in the body. If tests fail, revert the branch and report the failure; never push a red branch.

## Output Format

```markdown
# Dependency Audit: <path>

**Ecosystems audited:** npm, python | **Coverage gaps:** cargo-audit not installed (`cargo install cargo-audit`)

## Vulnerabilities (TOOL-REPORTED)

| Package | Installed | Advisory | Severity | Fixed in | Direct? |
|---------|-----------|----------|----------|----------|---------|

## Outdated

| Package | Installed | Latest | Lag | Security fix in gap? |
|---------|-----------|--------|-----|----------------------|

## License obligations

Per-finding obligation statements, then the "requires legal review" list.

## Supply-chain signals (require human verification)

One entry per signal, each ending with the verification step a human should run.

## Remediation plan

The table from Step 7, followed by: "No update has been applied. Approve specific rows to proceed."

## Evidence ledger

Everything INFERRED (with its derivation) and everything UNKNOWN (with what would resolve it).
```

## Boundaries

Dead-code or unused-dependency removal belongs to `senior-review:application-cleanup-method` or `typescript-development:knip`; Python lint, type and coverage audits belong to the python-development plugin.
