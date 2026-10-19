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

# Refactoring Analysis

**File:** `path/to/file.ext`
**Date:** YYYY-MM-DD
**Analyst:** [Your Name/Tool]

---

## Executive Summary

[Brief 2-3 sentence overview of the code quality and recommended refactoring approach]

---

## Current State Metrics

### Complexity Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Avg Cyclomatic Complexity | X.X | <10 | ⚠/✓ |
| Max Cyclomatic Complexity | XX | <15 | ⚠/✓ |
| Avg Function Length | XX lines | <30 | ⚠/✓ |
| Max Function Length | XX lines | <50 | ⚠/✓ |
| Avg Nesting Depth | X.X | ≤3 | ⚠/✓ |
| Max Nesting Depth | X | ≤3 | ⚠/✓ |

### Documentation Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Module Docstring | Yes/No | Yes | ⚠/✓ |
| Docstring Coverage | XX% | >80% | ⚠/✓ |
| Type Hint Coverage | XX% | >90% | ⚠/✓ |
| Public Functions Documented | X/Y | Y/Y | ⚠/✓ |

---

## Identified Issues

### High Priority

1. **[Issue Name]** - Line XXX
   - **Anti-Pattern:** [Name from anti-patterns.md]
   - **Impact:** [Readability/Maintainability/Performance]
   - **Description:** [What makes this problematic]
   - **Recommended Fix:** [Pattern from patterns.md]

2. **[Issue Name]** - Line XXX
   - **Anti-Pattern:** [Name]
   - **Impact:** [Impact type]
   - **Description:** [Details]
   - **Recommended Fix:** [Pattern]

### Medium Priority

3. **[Issue Name]** - Line XXX
   - **Anti-Pattern:** [Name]
   - **Impact:** [Impact type]
   - **Description:** [Details]
   - **Recommended Fix:** [Pattern]

### Low Priority

4. **[Issue Name]** - Line XXX
   - **Anti-Pattern:** [Name]
   - **Impact:** [Impact type]
   - **Description:** [Details]
   - **Recommended Fix:** [Pattern]

---

## Risk Assessment

### Refactoring Complexity: [Low/Medium/High]

**Factors:**
- **Test Coverage:** [Percentage] - [Good/Poor]
- **Dependencies:** [Number] external dependencies affected
- **Public API Changes:** [None/Minor/Major]
- **Business Logic Complexity:** [Low/Medium/High]

### Risk Level by Issue

| Issue | Current Risk | Refactoring Risk | Net Risk |
|-------|--------------|------------------|----------|
| Issue 1 | High | Low | Worth it |
| Issue 2 | Medium | Medium | Evaluate |
| Issue 3 | Low | High | Skip |

---

## Recommended Refactoring Plan

### Phase 1: Safe Changes (Low Risk)
**Estimated Time:** [Duration]

1. **Rename variables and functions** for clarity
   - Lines: XXX, YYY, ZZZ
   - Risk: Very Low
   - Impact: Readability improved

2. **Extract magic numbers to constants**
   - Lines: XXX, YYY
   - Risk: Very Low
   - Impact: Maintainability improved

3. **Add/improve documentation**
   - All public functions
   - Risk: None
   - Impact: Documentation coverage to >80%

### Phase 2: Structural Changes (Medium Risk)
**Estimated Time:** [Duration]

4. **Apply guard clauses** to reduce nesting
   - Function: `function_name()` (Line XXX)
   - Risk: Low (preserves behavior)
   - Impact: Nesting reduced from X to Y levels

5. **Extract methods** to reduce function length
   - Function: `long_function()` (Line XXX)
   - Extract: 3-4 helper functions
   - Risk: Medium (requires careful testing)
   - Impact: Complexity reduced from XX to Y

### Phase 3: Advanced Refactoring (Higher Risk)
**Estimated Time:** [Duration]

6. **Separate concerns** into distinct layers
   - Mixed data/logic/presentation
   - Risk: Medium-High
   - Impact: Major architectural improvement

7. **Replace primitive obsession** with domain objects
   - Risk: High (API changes)
   - Impact: Type safety and validation improved

---

## Expected Outcomes

### Metrics Improvement Projections

| Metric | Current | Projected | Improvement |
|--------|---------|-----------|-------------|
| Avg Complexity | XX | Y | Z% ↓ |
| Avg Function Length | XX | Y | Z% ↓ |
| Max Nesting | X | Y | Z% ↓ |
| Docstring Coverage | XX% | Y% | Z% ↑ |
| Type Hint Coverage | XX% | Y% | Z% ↑ |

### Qualitative Improvements

- **Readability:** [Description of improvement]
- **Maintainability:** [Description of improvement]
- **Testability:** [Description of improvement]
- **Onboarding:** [Description of improvement]

---

## Test Coverage Assessment

### Current Coverage

- **Overall Coverage:** XX%
- **Critical Paths Covered:** Yes/No
- **Edge Cases Tested:** Yes/No
- **Integration Tests:** Yes/No

### Recommended Test Additions

Before refactoring, add tests for:

1. **[Test Description]** - Current gap in coverage
2. **[Test Description]** - Needed before structural changes
3. **[Test Description]** - Critical path not tested

---

## Dependencies Analysis

### Internal Dependencies

Functions/modules that depend on code being refactored:

1. **[Module/Function Name]** - [Dependency Type]
   - Impact: [Low/Medium/High]
   - Required Changes: [Description]

### External Dependencies

Third-party code or APIs affected:

1. **[Library/API Name]**
   - Impact: [Low/Medium/High]
   - Required Changes: [Description]

---

## Alternatives Considered

### Option A: [Approach Name]
- **Pros:** [List]
- **Cons:** [List]
- **Effort:** [Low/Medium/High]
- **Recommendation:** [Chosen/Not Chosen - Why]

### Option B: [Approach Name]
- **Pros:** [List]
- **Cons:** [List]
- **Effort:** [Low/Medium/High]
- **Recommendation:** [Chosen/Not Chosen - Why]

---

## Sign-Off Checklist

Before proceeding with refactoring:

- [ ] All high-priority issues identified
- [ ] Risk assessment completed
- [ ] Observable contracts, independent failure modes and bugfix regressions have justified surviving protection
- [ ] Refactoring plan reviewed by team
- [ ] Time estimate approved
- [ ] Dependencies documented
- [ ] Rollback plan defined

---

## Next Steps

1. **Immediate:** [Action item]
2. **Short-term:** [Action item]
3. **Long-term:** [Action item]

---

## Notes

[Any additional context, concerns, or observations]
