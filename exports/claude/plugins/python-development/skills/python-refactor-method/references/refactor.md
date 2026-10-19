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

# Python Refactoring

Measure, rewrite, verify against the tests, then report the delta. This is the run procedure of `python-development:python-refactor-method` for a coordinator that already holds a run: `/daodan:refactor-code` on Python code. Use it to refactor Python code, reduce cyclomatic complexity, or restructure modules with measured before/after metrics.

Not for renaming or simplifying for readability only (`clean-code:readability-method`), or for removing dead code (`senior-review:application-cleanup-method`).

## Inputs

- **TARGET**: what the caller passes. Read it as:
  - a path to a file or directory: refactor it as given;
  - a commit, PR or branch: the Python files it changes that exist in the working tree;
  - free text naming a module, class or function: resolve it to its project-relative file path.

  In the commands below, `TARGET` stands for the resolved path or paths, each quoted.
- **RUN_DIR**: the caller's run directory. The session state and every phase output file go there, never in the project.
- **Strict mode**: a method decision. Default: off. On when the caller's request asks for caution (strict, careful or step-by-step execution). It changes the recommendation at the phase checkpoint only.
- **Executing the plan**: an authorization asked at the phase checkpoint, once, with the host's question tool, and recorded in the run (`project-protocol:project-protocol`). Committing needs its own authorization (Phase 3).

## CRITICAL RULES

1. **Execute phases in order.** Analysis -> Planning -> Approval -> Execution -> Validation.
2. **Write output files.** Each phase writes to `RUN_DIR/` for persistence and context.
3. **Stop at checkpoint.** Get user approval of the refactoring plan BEFORE making any code changes.
4. **Run tests after every change.** Never proceed if tests fail.
5. **Never enter plan mode.** Execute immediately.
6. **One pattern at a time.** Don't combine multiple refactorings in a single edit.

## Operational preflight

Apply this skill's `SKILL.md` (`python-development:python-refactor-method`) with this
reference, and load `project-protocol:project-protocol` before mutation. Existing plan authorization
can satisfy the approval checkpoint; do not ask again for the same accepted scope.
All checkpoints and native reports are bound to the same current snapshot.
Required unavailable local checks need an authorized same-snapshot remote gate.
Recover only this phase's edits from preserved pre-edit content; hard reset requires
an exclusively owned clean isolated worktree and the captured `pre_phase_sha`.

## Pre-flight

### 1. Check for existing session

Check if `RUN_DIR/state.json` exists:
- If in progress: offer to resume or start fresh
- If complete: offer to archive and start fresh

### 2. Initialize state

Create `RUN_DIR/state.json`:

```json
{
  "target": "TARGET",
  "status": "in_progress",
  "decisions": {
    "strict_mode": false
  },
  "current_phase": 1,
  "completed_phases": [],
  "files_created": [],
  "started_at": "ISO_TIMESTAMP"
}
```

`strict_mode` records the strict mode decision of the Inputs.

## Phase 1: Analysis

1. **Read the target code** to understand current structure
2. **Run complexity metrics** (if available):
   ```bash
   uv run python "${CLAUDE_PLUGIN_ROOT}/skills/python-refactor-method/scripts/measure_complexity.py" TARGET 2>/dev/null
   uv run python "${CLAUDE_PLUGIN_ROOT}/skills/python-refactor-method/scripts/analyze_with_flake8.py" TARGET 2>/dev/null
   ```
   If scripts aren't available, analyze manually by reading the code.

3. **Identify issues** against thresholds:
   - Cyclomatic complexity: >10 per function (high priority)
   - Cognitive complexity: >15 per function (high priority)
   - Function length: >30 lines (medium priority)
   - Nesting depth: >3 levels (medium priority)

4. **Establish test baseline**:
   ```bash
   pytest [test files] -v 2>/dev/null || python -m pytest -v 2>/dev/null
   ```
   Record which tests exist and their pass/fail status.

**Output file:** `RUN_DIR/01-analysis.md`

```markdown
# Phase 1: Analysis

## Target
[file/directory path]

## Current Metrics
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Cyclomatic Complexity (avg) | X | <10 | PASS/FAIL |
| Cognitive Complexity (max) | X | <15 | PASS/FAIL |
| Max Function Length | X lines | <30 | PASS/FAIL |
| Max Nesting Depth | X | <=3 | PASS/FAIL |

## Issues Found
[Ordered by severity: HIGH, MEDIUM, LOW]

## Test Baseline
- Tests found: [count]
- Passing: [count]
- Failing: [count]
```

## Phase 2: Planning

Read `RUN_DIR/01-analysis.md` for context.

1. **Prioritize issues** by impact
2. **Select refactoring patterns** for each issue:
   - Guard clauses for nested conditionals
   - Extract method for long functions
   - Replace magic numbers with named constants
   - Rename for clarity
   - Decompose god functions
3. **Assess risk** for each change (Low / Medium / High)
4. **Create ordered plan** with atomic steps

**Output file:** `RUN_DIR/02-plan.md`

```markdown
# Phase 2: Refactoring Plan

## Refactoring Steps (ordered)

### Step 1: [pattern] on [target]
- Risk: [Low/Medium/High]
- File: [path:line]
- What: [description of change]
- Why: [rationale]

### Step 2: ...
[Continue for all planned changes]

## Estimated Impact
- Complexity reduction: ~X%
- Functions affected: [count]
- Risk level: [overall Low/Medium/High]
```

---

## PHASE CHECKPOINT -- User Approval Required

Ask with the host's question tool and record the answer in the run.

```
Analysis and planning complete.

Issues found: [count] ([X high, Y medium, Z low])
Refactoring steps planned: [count]
Overall risk: [Low/Medium/High]
Test baseline: [X] tests passing

Please review:
- RUN_DIR/01-analysis.md
- RUN_DIR/02-plan.md

1. Execute the plan -- apply all refactorings with test validation
2. Execute partial -- I'll tell you which steps to apply
3. Revise plan -- adjust before executing
4. Cancel -- stop here with the analysis only
```

If strict mode is on and there are High risk changes, recommend option 2 (partial execution).

Do NOT proceed to Phase 3 until the user approves.

---

## Phase 3: Execution

Read `RUN_DIR/02-plan.md` for the approved plan.

For each refactoring step:

1. Apply the single refactoring pattern
2. Run tests immediately:
   ```bash
   pytest [test files] -v
   ```
3. If required candidate gates pass: commit only when authorized, then continue;
   otherwise deliver the verified owned edits without committing
4. If tests fail: REVERT the change, report the failure, ask the user how to proceed

Log each step to `RUN_DIR/03-execution.md`:

```markdown
# Phase 3: Execution Log

## Step 1: [pattern]
- Status: [completed/failed/reverted]
- File: [path]
- Tests: [all passing / X failures]
- Commit: [hash]

## Step 2: ...
```

## Phase 4: Validation

After all steps executed:

1. **Run full test suite** -- zero failures required
2. **Compare metrics** (if scripts available):
   ```bash
   uv run python "${CLAUDE_PLUGIN_ROOT}/skills/python-refactor-method/scripts/compare_metrics.py" [before] [after] 2>/dev/null
   ```
3. **Manual comparison** -- re-read the code and compare complexity

**Output file:** `RUN_DIR/04-validation.md`

```markdown
# Phase 4: Validation

## Metrics Comparison
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Cyclomatic Complexity (avg) | X | Y | -Z% |
| Cognitive Complexity (max) | X | Y | -Z% |
| Max Function Length | X | Y | -Z lines |
| Max Nesting Depth | X | Y | -Z |

## Test Results
- Tests run: [count]
- Passing: [count]
- Failing: [count]

## Refactoring Summary
- Steps executed: [X/Y]
- Steps reverted: [count]
- Files changed: [count]
- Commits: [count]
```

---

## Completion

```
Python refactoring complete for: TARGET

Output Files:
- Analysis: RUN_DIR/01-analysis.md
- Plan: RUN_DIR/02-plan.md
- Execution Log: RUN_DIR/03-execution.md
- Validation: RUN_DIR/04-validation.md

Summary:
- Refactorings applied: [X/Y]
- Tests: [all passing / X failures]
- Complexity reduction: ~[Z]%

Next steps:
1. Review changes with /daodan:review-changes
2. Run the full test suite to confirm
3. Commit remaining changes if needed
```

## Related Skills

- `pytest-patterns` -- Set up tests before refactoring
- `python-performance-optimization` -- Profile if performance-critical
- `async-python-patterns` -- For async code refactoring
