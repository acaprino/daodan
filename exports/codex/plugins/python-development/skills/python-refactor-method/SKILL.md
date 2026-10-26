---
name: python-refactor-method
description: >
  Restructure tangled code into a clear equivalent, preserving behavior.
  TRIGGER WHEN: the user asks for "readable", "maintainable" or "clean" code, a review flags comprehension issues, the task is legacy modernization or onboarding cleanup, or `/daodan:refactor-code` runs on Python code.
---

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

# Python Refactor

Transform complex Python into clear, maintainable code while preserving correctness. Phased workflow with safety-by-design and continuous validation. For deep references (anti-patterns, OOP principles, cognitive complexity, regression prevention), see the `references/` directory.

## Load map

| Reference | Read when |
|---|---|
| `references/refactor.md` | A coordinator runs a refactor on Python code (`/daodan:refactor-code`): target reading, strict mode, session state and phase files in the run directory, the approval checkpoint and the completion report |
| `references/REGRESSION_PREVENTION.md` | Before any session |
| `references/anti-patterns.md` | Phase 1, identifying readability issues |
| `references/oop_principles.md` | Phase 1, assessing architecture |
| `references/patterns.md` | Selecting a refactoring pattern |
| `references/cognitive_complexity_guide.md` | Cognitive complexity rules, tool configuration and Wily tracking |
| `references/flake8_plugins_guide.md` | Projects already on flake8 |
| `references/examples/` | Worked transformations |

## When to invoke

- Explicit "human", "readable", "maintainable", "clean", or "refactor" request
- Code review flags comprehension or maintainability issues
- Legacy code modernization
- Onboarding / educational contexts
- Complexity metrics exceed thresholds
- **Red flags**: file > 500 lines with scattered functions and global state, multiple `global` statements, no clear module/class organization, configuration mixed with business logic

## Do NOT invoke when

- Code is performance-critical and profiling shows perf optimization is needed first
- Code is scheduled for deletion or replacement
- External dependencies require upstream contributions instead
- User explicitly requested perf optimization over readability

## Core principles (priority order)

1. **Prefer structured OOP for complex code** -- shared state, multiple concerns, scattered globals = restructure into classes/modules. (But: simple modules with pure functions, click/argparse CLIs, and functional pipelines DON'T need to be forced into classes.)
2. **Clarity over cleverness** -- explicit beats implicit
3. **Preserve correctness** -- all tests pass, behavior identical
4. **Single Responsibility** -- one thing per class/function (SOLID)
5. **Self-documenting structure** -- code = what, comments = why
6. **Progressive disclosure** -- reveal complexity in layers
7. **Required performance**: preserve the approved workload budget; compare like-for-like measurements and record unavailable evidence

## Hard constraints

- **SAFETY BY DESIGN** -- mandatory migration checklists for destructive changes. CREATE → SEARCH → MIGRATE → VERIFY → only then REMOVE. NEVER remove before 100% migration verified.
- **STATIC ANALYSIS FIRST** -- `flake8 --select=F821,E0602` (or `ruff check --select=F821`) BEFORE tests. Catches NameErrors immediately.
- **PRESERVE BEHAVIOR** -- all existing tests pass after.
- **PERFORMANCE CONTRACT**: a measured violation of the approved budget requires a decision before accepting the refactor; no universal 2× or percentage threshold.
- **NO API CHANGES** -- public APIs unchanged unless explicitly requested + documented.
- **NO OVER-ENGINEERING** -- simple stays simple.
- **NO MAGIC** -- no framework magic, no metaprogramming unless absolutely necessary.
- **VALIDATE CONTINUOUSLY** -- static analysis + tests after each logical change.

## Operational preflight and recovery

Load the `work-controller:work-record` skill before execution. Reuse an authorized
plan only for its current scope/snapshot. Record existing tracked/untracked edits,
owned files, baseline and required commands/configurations; capture `pre_phase_sha`
and pre-edit contents immediately before each phase. A remote gate must match
the exact candidate snapshot and required lane/job, not merely the current branch.
Path-scoped recovery restores saved pre-edit content and preserves unrelated edits.
Hard reset is available only in an exclusively owned clean isolated worktree.
If another writer changed an owned file, halt with the conflict instead of overwriting.

## Regression prevention (MANDATORY)

**Refactoring must NEVER introduce regressions.** Read `references/REGRESSION_PREVENTION.md` before any session.

Before each session:
- Required baseline checks pass for the exact starting snapshot, or the affected phase remains open
- Protected behaviors, independent failure modes and bugfix regressions inventoried; fill relevant gaps before the affected transformation, without a coverage quota
- Characterization outputs captured for critical edge cases and checked against the authorized contract; observed behavior does not make a known bug correct
- Static analysis baseline saved

After EACH micro-change (not at the end -- every single one):
- `flake8 --select=F821,E999` → 0 errors
- `pytest -x` → all passing
- Spot check 1 edge case for unchanged behavior

If a required check fails, stop and use the common protocol to restore the exact owned pre-phase state. Preserve preceding successful work and all preexisting edits; analyze before a new candidate.

ANY REGRESSION = TOTAL FAILURE.

## Workflow (4 phases)

### Phase 1: Analysis

1. Read the entire codebase section.
2. Identify readability issues using `references/anti-patterns.md` (script-like/global-state, God Objects, nested conditionals, long functions, magic numbers, cryptic names).
3. Assess architecture against `references/oop_principles.md` (proper classes/modules, encapsulated state, separated responsibilities, SOLID, DI vs hard-coded deps).
4. Measure current metrics with `scripts/measure_complexity.py` or `scripts/analyze_multi_metrics.py`.
5. Run linting analysis (see Tooling below).
6. Check test coverage; identify gaps to fill BEFORE refactoring.
7. Document with `assets/templates/analysis_template.md`.

**Output**: prioritized list of issues by impact and risk.

### Phase 2: Planning

1. **Classify each change**:
   - **Non-destructive** (rename, docs, type hints) → low risk
   - **Destructive** (remove globals, delete functions, replace APIs) → high risk
2. **For DESTRUCTIVE changes -- migration plan is MANDATORY**:
   - Search ALL usages of each element to be removed
   - Document every usage (file, line, type)
   - **No complete migration plan = cannot proceed with the destructive change**
3. Risk assessment per change (Low/Medium/High)
4. Dependency map -- what depends on this code?
5. Test strategy -- what tests are needed? what might break?
6. Order changes safest → riskiest
7. Document expected metric improvements

**Output**: refactoring plan, sequenced changes, migration plans, test strategy, rollback plan.

### Phase 3: Execution

#### Non-destructive (safe anytime)
1. Rename for clarity
2. Extract magic numbers/strings to named constants
3. Add/improve docs and type hints
4. Add guard clauses to reduce nesting

#### Destructive (STRICT PROTOCOL)
1. **CREATE** new structure (no removal) -- write new classes/functions + tests
2. **SEARCH** for ALL usages of the element being removed
3. **CREATE** migration checklist documenting every found usage
4. **MIGRATE** one usage at a time, checking off the list, running static analysis + tests after each
5. **VERIFY** complete migration -- re-run searches, should find zero old references
6. **REMOVE** old code only after 100% migration verified

#### Execution rules
- NEVER skip the migration checklist for destructive changes
- Run static analysis BEFORE tests
- One pattern at a time -- never mix multiple refactoring patterns in a single change
- Atomic candidates; commit each migration step only when explicitly authorized and its candidate gate passed
- Stop on ANY error (static analysis OR test failure) → immediate fix/revert

#### Recommended order
1. Transform script-like code to proper architecture (`references/examples/script_to_oop_transformation.md`)
2. Rename for clarity
3. Extract magic numbers/strings to constants/enums
4. Improve docs + type hints
5. Extract methods to reduce function length
6. Simplify conditionals with guard clauses
7. Reduce nesting depth
8. Final review: separation of concerns

### Phase 4: Validation

1. **Static analysis FIRST**:
   ```bash
   flake8 <file> --select=F821,E0602          # undefined names/variables -- MUST be 0
   flake8 <file> --select=F401                # unused imports
   flake8 <file>                              # full quality check
   ```
2. **Full test suite** → 100% pass required.
3. **Architecture validation**: global state eliminated/encapsulated, proper modules/classes, separated responsibilities, SOLID compliance.
4. **Before/after metrics** with `scripts/measure_complexity.py` or `scripts/analyze_multi_metrics.py`.
5. **Performance regression check** with `scripts/benchmark_changes.py` for hot paths.
6. **Summary report** using `assets/templates/summary_template.md`.
7. **Flag for human review** if: the agreed performance budget is violated or cannot be verified, public API signatures changed, test coverage decreased, significant architectural changes.

## Refactoring patterns (catalog summary)

Full catalog with examples in `references/patterns.md`. Key patterns:

- **Guard Clauses** -- early returns instead of nested conditionals
- **Extract Method** -- split large functions into focused units (resets the nesting counter -- most powerful for cognitive complexity)
- **Dictionary Dispatch** -- replace if-elif chains with lookup tables
- **Match Statement** (Py 3.10+) -- counts as +1 total, not per branch
- **Named Boolean Conditions** -- extract complex booleans into named variables
- **Encapsulate Global State** -- move globals into classes with proper encapsulation
- **Group Related Functions** -- organize scattered functions into classes by responsibility
- **Create Domain Models** -- replace primitive dicts with dataclasses + enums
- **Apply Dependency Injection** -- replace hard-coded deps with injected ones

For cognitive complexity calculation rules and reduction strategies, see `references/cognitive_complexity_guide.md`.

### Naming conventions

- **Variables**: descriptive, booleans as `is_active` / `has_permission` / `can_edit`, collections as plurals
- **Functions**: verb + object (`calculate_total`, `validate_email`); boolean queries as `is_valid()` / `has_items()`
- **Constants**: `UPPERCASE_WITH_UNDERSCORES`; replace magic numbers/strings
- **Classes**: PascalCase nouns (`UserAccount`, `PaymentProcessor`)

## Anti-patterns to investigate (priority order)

Full catalog: `references/anti-patterns.md`. The numeric and structural signals below are leads; confirm actual cost before proposing changes.

- **Critical**: script-like / procedural code with global state; God Object / God Class
- **High**: complex nested conditionals (> 3 levels), long functions (> 30 lines), magic numbers, cryptic names, missing type hints, missing docstrings
- **Medium**: duplicate code, primitive obsession, long parameter lists (> 5)
- **Low**: inconsistent naming, redundant comments, unused imports

## Tooling

### Primary stack: Ruff + Complexipy (recommended for new projects)

```bash
uv tool install ruff complexipy radon wily

ruff check src/                                 # fast linting (Rust, replaces flake8+plugins)
complexipy src/ --max-complexity-allowed 15     # cognitive complexity (Rust)
radon mi src/ -s                                # maintainability index
```

Full configuration (pyproject.toml, pre-commit, GitHub Actions): `references/cognitive_complexity_guide.md`.

### Alternative: flake8 + curated plugins

For projects already on flake8, see `references/flake8_plugins_guide.md` (curated 16-plugin selector list).

### Multi-metric analysis

`scripts/analyze_multi_metrics.py` combines complexipy + radon + maintainability index in a single report.

| Metric | Tool | Use |
|--------|------|-----|
| Cognitive complexity | **complexipy** | Human comprehension |
| Cyclomatic complexity | **ruff** (C901), radon | Test planning |
| Maintainability index | radon | Overall code health |

### Metric targets

- Cyclomatic complexity: < 10 per function (warning 15, error 20)
- Cognitive complexity: < 15 per function (SonarQube default; warning 20)
- Function length: < 30 lines (warning 50)
- Nesting depth: ≤ 3 levels
- Docstring coverage: > 80% for public functions
- Type-hint coverage: > 90% for public APIs

### Historical tracking with Wily

Trends matter, not just thresholds. Setup + CI integration: `references/cognitive_complexity_guide.md`.

## Common refactoring mistakes

Full guide: `references/REGRESSION_PREVENTION.md`. Key traps:

1. **Incomplete migration** -- removing old code before ALL usages migrated (causes NameErrors).
2. **Partial pattern application** -- applying refactoring to some functions but not others.
3. **Breaking public APIs** -- changing signatures used by external code.
4. **Assuming tests cover everything** -- tests pass but runtime errors occur (run static analysis!).

## When to reach for which tool

- **clean-code** (cross-language plugin) -- multi-language cosmetic cleanup; renames local vars, improves comments, simplifies structure. Lowest regression risk. Use for "make this readable", "clean up naming."
- **python-refactor-method** (this skill) -- Python-only deep restructuring. OOP transformation, SOLID, complexity metrics, migration checklists, benchmark validation. Use for "refactor this module", "reduce complexity", "transform to OOP."

**Escalation path**: clean-code → python-refactor-method (safest to most thorough).

## Integration

- Load the `testing:test-hygiene` skill and use `testing:test-writer` for needed behavior checks; `pytest-patterns` supplies Python mechanics
- **python-performance-optimization** -- deep profiling before/after
- **python-packaging** -- handle pyproject.toml + distribution if refactoring a library
- **uv-package-manager** -- `uv run ruff`, `uv run complexipy` for tool execution
- **async-python-patterns** -- reference async patterns when refactoring async code

## When NOT to refactor

Perf-critical optimized code (profile first), code scheduled for deletion, external deps (contribute upstream), stable legacy code nobody needs to modify.

## Limitations

Cannot improve algorithmic complexity (that's an algorithm change). Cannot add domain knowledge not in code/comments. Cannot guarantee correctness without tests. Style preferences vary -- adjust to team conventions.

## Examples

`references/examples/`:
- `script_to_oop_transformation.md` -- script → clean OOP architecture (flagship case study)
- `python_complexity_reduction.md` -- nested conditionals and long functions
- `typescript_naming_improvements.md` -- naming patterns (cross-language reference)

## Success criteria

1. **Zero regressions** -- all tests pass, behavior unchanged
2. Golden master match for documented critical cases
3. Complexity metrics improved (documented in summary)
4. Approved performance budget preserved on comparable measurements, or an explicit authorized change
5. Documentation coverage improved
6. Code easier for humans to understand
7. No new security vulnerabilities
8. Atomic, well-documented git history
9. Wily trend -- complexity not increased vs previous commit
10. Static analysis shows improvement
