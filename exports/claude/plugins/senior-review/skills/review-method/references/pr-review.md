## Phase 2: Risk & Architecture Assessment (2 agents in parallel)

Run both agents **in parallel** in a single response. Agent A also carries the lite codebase-hygiene pass, so the phase stays at two spawns.

### Agent A: Architecture, Risk & Hygiene Assessment

```
Task:
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
Task:
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
