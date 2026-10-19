<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when a required one is off.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

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

# TypeScript Type-Safety Audit

Audit a codebase for type-system erosion and write a markdown report: `any` leakage, unsound casts, tsconfig strictness, exhaustiveness, generics soundness, and missing runtime validation at boundaries. Shape: detect scope, run the compiler and linter, dispatch the plugin's reviewer in an isolated context, write the report.

Caller: `/daodan:check-health`, which runs this audit when the project has TypeScript. Inside `/daodan:review-changes` and `/daodan:review-branch`, senior-review dispatches `typescript-development:type-safety-auditor` with inputs it prepares, not through this procedure: never run both on the same target.

Not this audit: style review (`typescript-write`), React performance (the React audit of the react-development plugin), dead-code detection (`knip`).

Act as a senior TypeScript type-safety auditor. Review TypeScript code for type-system erosion: any leakage, unsound casts, missing boundary validation, assertion abuse, configuration drift, exhaustiveness gaps, and unsound generics.

## Inputs

- **TARGET**: what the caller passes.
  - The project, or nothing: full mode over the default source roots.
  - A path (file or directory): full mode restricted to that path.
  - A diff (uncommitted changes, or a commit, range or branch the caller resolved to a revision range): diff mode over the TypeScript files it changes.
  - Free text that names no path and no diff: full mode over the default source roots.
- **Mode**: method decision. Full mode when called by `/daodan:check-health`; diff mode only when the caller passes a diff.
- **Run directory**: the caller's run directory, written `<run>` below. Everything this audit writes goes under `<run>/ts-review/`; it edits no project file.

## CRITICAL RULES

1. **Type-safety-only scope.** Ignore style, naming, formatting, performance, and dead code. Focus on where the type system stops telling the truth.
2. **Run the declared reviewer.** Dispatch `typescript-development:type-safety-auditor` in its required isolated context through the host harness with the full prepared scope.
3. **Write markdown report.** Output is `<run>/ts-review/report.md`: an actionable checklist with scores, findings, and fix instructions.
4. **Never enter plan mode.** Execute immediately.

## Step 1: Detect Scope

### Decision tree

**Full mode** (the default; the caller passes no diff, as `/daodan:check-health` does):
- Scan the whole source tree: `src/`, `app/`, `lib/`, `packages/`, or the TARGET path

**Diff mode** (the caller passes a diff):
- Review only the changed TypeScript files
- Get the diff: `git diff HEAD -- <ts files>` for uncommitted changes, `git diff <range> -- <ts files>` for a revision range

### Check for TypeScript files (diff mode only)

For uncommitted changes:

```bash
git diff HEAD --name-only | grep -E '\.tsx?$' || true
git diff --name-only | grep -E '\.tsx?$' || true
git diff --cached --name-only | grep -E '\.tsx?$' || true
```

For a revision range: `git diff <range> --name-only | grep -E '\.tsx?$' || true`.

### Discover TypeScript files (full mode only)

```bash
find src -type f \( -name "*.ts" -o -name "*.tsx" \) | head -80
```

Or use the TARGET path in place of `src` when the caller names one.

If no TypeScript files are found, stop and say so.

## Step 1.5: Run Deterministic Ground Truth (if available)

```bash
npx tsc --noEmit --pretty false 2>/dev/null || true
npx eslint --format json "src/**/*.{ts,tsx}" 2>/dev/null || true
```

Pass both outputs to the agent. If the tools are unavailable, proceed without them and note it in the report.

## Step 2: Sample Key Files & Gather Context

Read a representative cross-section:
- `tsconfig.json` and every config it extends (always)
- Boundary modules: API clients, route handlers, queue consumers, storage access, env/config access
- 3-5 core domain modules with exported types
- Any first-party `.d.ts` files

## Step 3: Run Review Agent

The host harness binds the declared `typescript-development:type-safety-auditor` role. Give it the
following task, the exact scope, relevant files, authorization and an owned
intermediate report path `<run>/ts-review/worker-findings.md`. The reviewer
returns its findings and a delivered or failed outcome; it does not write
the final report. Record that outcome before the report phase. A failed or
missing delivery leaves the review incomplete and must be reported.

````text
Audit the type safety of this TypeScript codebase.

## Scope
[list of key files sampled]

## File Contents
[paste tsconfig.json, boundary modules, and sampled core modules]

## Compiler Output (if available)
[paste tsc --noEmit output, or "No compiler output available"]

## Linter Output (if available)
[paste ESLint JSON report, or "No linter output available"]

## Type-Safety Rules Checklist (20 rules; flag violations by id)

**1. Any Erosion (CRITICAL):** any-explicit (unknown plus narrowing over any), any-implicit-boundary (type JSON.parse and response.json() immediately), any-generic-default (never <T = any>)
**2. Unsound Casts (CRITICAL):** cast-as-unsound (shape-changing as needs a runtime check), cast-double (as unknown as X is a bypass), cast-const-assertion (as const over widening annotations)
**3. Boundary Validation (CRITICAL):** boundary-http (schema-parse payloads at the edge), boundary-queue (validate messages on receipt), boundary-storage (validate and version storage reads), boundary-env (one validated config module)
**4. Assertion Abuse (HIGH):** assert-non-null (! needs justification or a fail-fast check), assert-ts-expect-error (@ts-expect-error with reason, never @ts-ignore)
**5. Compiler Configuration (HIGH):** config-strict (strict true baseline), config-unchecked-index (noUncheckedIndexedAccess), config-exact-optional (exactOptionalPropertyTypes), config-skiplibcheck (never hide first-party errors)
**6. Exhaustiveness (MEDIUM-HIGH):** exhaust-switch-never (never assertion in default), exhaust-satisfies-record (satisfies Record for lookup tables)
**7. Generics Soundness (MEDIUM):** generics-constraint (constrain public type parameters), generics-type-guards (predicates verify the whole shape)

## Instructions
Use the checklist as your primary audit framework. Cite rule ids in every finding (e.g. "Violates boundary-http"). Cross-check candidates against the compiler output: a tsc error near a grep hit raises confidence.

For each finding: rule id, severity (Critical/High/Medium/Low), file + line, confidence (0-100), what breaks at runtime, concrete fix with a code example.
Note what is done well.

Return the structured JSON block from your output format at the end.
````

## Step 4: Generate Markdown Report

After the agent completes, create the `<run>/ts-review/` directory and write `report.md`.

Order findings by severity, then file name.

**Output file:** `<run>/ts-review/report.md`

```markdown
# TypeScript Type-Safety Review: [date]

[Diff mode: N changed files | Full mode: N files sampled]

## Ground Truth

[tsc error count and eslint summary, or "Compiler and linter unavailable: review is heuristic only."]

## Scores

| Category | Score |
|----------|-------|
| Any Hygiene | X/10 |
| Cast Discipline | X/10 |
| Config Strictness | X/10 |
| Boundary Validation | X/10 |
| **Overall** | **X/10** |

Critical: X | High: X | Medium: X | Low: X

## Files Audited

- `tsconfig.json`, `api/client.ts`, ...

---

## Critical & High Issues

### [rule-id]

#### `file.ts:42` [issue title]
- **Severity**: Critical
- **Confidence**: 90
- **Issue**: [what breaks at runtime]
- **Fix**: [fix instruction with code]
- [ ] Fixed

## Medium & Low Issues

[same structure, compact]

## Positives

- [what is done well]
```

Present the report summary to the user with the top findings and the report path.
