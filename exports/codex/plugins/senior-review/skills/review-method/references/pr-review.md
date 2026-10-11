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

## Phase 2: Risk & Architecture Assessment

Run the two core agents below and any selected stack specialists in the same
parallel batch. Agent A carries the lite codebase-hygiene pass. Stack bindings and
inputs come from review-preparation's `references/stack-dimensions.md`; use their
canonical role definitions with the prepared scope and premise-provenance rules.
Read the Shared Instructions for All Agents section of `references/code-review.md`
inside this skill and apply it to both core and stack workers, using this PR's
prepared target, intent and diff. Unknown intent stays declared as unknown. Include
the evidenced-finding requirements from review-consolidation's stack-findings
reference, including confidence and the normalized review severity; preserve each
specialist's native report and labels. Do not run the code-review dispatch table.
Account for every selected delivery before producing the risk assessment or PR
description; a missing specialist result remains a coverage gap.

### Agent A: Architecture, Risk & Hygiene Assessment

```
Isolated worker brief:
  role: "senior-review:code-auditor"
  description: "Architecture and risk assessment for PR"
  prompt: |
    Analyze the following code changes for architectural soundness and risk.

    ## Changed Files
    [list with categories and line counts]

    ## Diff
    [git diff output]

    ## Instructions
    Assess:
    1. **Change type**: Feature, bugfix, refactor, dependency update, config change
    2. **Architectural impact**: Does this change boundaries, contracts, or data models?
    3. **Risk factors**:
       - Size risk: >500 lines = high, 200-500 = medium, <200 = low
       - Complexity risk: new abstractions, changed interfaces, database migrations
       - Test risk: test coverage of changed code paths
       - Dependency risk: new or updated packages
       - Security risk: auth, input handling, crypto, secrets
    4. **Breaking changes**: Any API contract changes, removed exports, schema changes
    5. **PR split opportunities**: If >500 lines, suggest logical split points
    6. **Lite hygiene pass**: dead code (D1) plus the `repo-hygiene:repo-hygiene`
       skill's VCS checks at its lite profile, scoped to the changed files. Load
       that skill rather than restating its patterns: the full and lite passes
       share one set of check definitions and differ only in perimeter.
       This is the same perimeter /senior-review:code-review runs. Do not widen
       it to orphan assets, dependency hygiene, or stale docs: those belong to
       the full pass in /senior-review:team-review.

       **D1, dead code introduced or exposed by the diff.** Run the tool that
       matches the changed files and report only findings on lines the diff
       touched:

       ```bash
       # Python
       ruff check --select F401,F811,F841,ARG <changed .py files>
       vulture --min-confidence 80 <changed .py files>   # if available
       # TS/JS
       npx knip --include files,exports,dependencies --no-progress
       # fallback when knip is absent
       npx tsc --noEmit --noUnusedLocals --noUnusedParameters
       ```

       Skip a tool that is not installed rather than installing it; note the
       skip. Do not flag framework conventions (route decorators, pytest
       fixtures, signal handlers, Django views), symbols in `__all__` or
       reached dynamically, dunder methods, or parameters prefixed with `_`.

       **D3, artifacts that should not be in the commit.** Check files the diff
       ADDS for build output and caches (`dist/`, `build/`, `out/`, `.next/`,
       `target/`, `__pycache__/`, `coverage/`), compiled or generated files
       (`*.pyc`, `*.class`, `*.map`, `*.tsbuildinfo`), OS and editor metadata
       (`.DS_Store`, `Thumbs.db`), and filesystem garbage (`nul`, `*.bak`,
       `*.orig`, `*.swp`). For each hit, run `git check-ignore -v <path>` to
       tell a missing `.gitignore` pattern apart from a file committed before
       the pattern existed.

    Report hygiene findings in their own section, each with the path and the
    owner-qualified phase that would resolve it: `/senior-review:code-review
    --commit` phase `exports` for dead code, `/repo-hygiene:tidy` phase
    `garbage` or `gitignore` for what the filesystem and git decide. A bare
    phase name is ambiguous now that two commands own disjoint phase sets.
    Never remove anything: this command only describes the PR.

    Output a structured risk assessment with an overall risk level (Low/Medium/High/Critical).
```

### Agent B: Security & Dependency Check

```
Isolated worker brief:
  role: "senior-review:security-auditor"
  description: "Security review for PR changes"
  prompt: |
    Review the following code changes for security concerns relevant to a PR.

    ## Changed Files
    [list of changed code files]

    ## Diff
    [git diff output]

    ## Instructions
    Check for:
    1. Secrets or credentials in the diff (API keys, tokens, passwords)
    2. New dependencies -- are they trustworthy? Known vulnerabilities?
    3. Input validation gaps in new/modified code
    4. Auth/authorization changes -- are they correct?
    5. Insecure defaults introduced (debug mode, verbose errors, permissive CORS)

    If no security issues, say so clearly.
    For each finding: severity, file, issue, fix.
```

---
