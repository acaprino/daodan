<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
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

# Refactoring Summary

**File:** `path/to/file.ext`
**Date:** YYYY-MM-DD
**Refactored By:** [Your Name]
**Duration:** [Time Spent]
**Risk Level:** [Low/Medium/High]

---

## Overview

[2-3 sentence summary of what was refactored and why]

---

## Changes Made

### 1. [Change Category - e.g., "Extracted Methods for Complexity Reduction"]

**Lines Affected:** XXX-YYY

**Description:**
[Detailed description of what was changed and why]

**Rationale:**
[Business/technical justification for this change]

**Pattern Applied:**
[Reference to pattern from patterns.md]

**Risk Level:** Low/Medium/High

**Before:**
```language
[Code snippet before refactoring]
```

**After:**
```language
[Code snippet after refactoring]
```

---

### 2. [Change Category]

**Lines Affected:** XXX-YYY

**Description:**
[Detailed description]

**Rationale:**
[Justification]

**Pattern Applied:**
[Pattern reference]

**Risk Level:** Low/Medium/High

**Before:**
```language
[Code snippet before]
```

**After:**
```language
[Code snippet after]
```

---

### 3. [Change Category]

**Lines Affected:** XXX-YYY

**Description:**
[Detailed description]

**Rationale:**
[Justification]

**Pattern Applied:**
[Pattern reference]

**Risk Level:** Low/Medium/High

---

## Metrics Improvement

### Complexity Metrics

| Metric | Before | After | Change | Status |
|--------|--------|-------|--------|--------|
| Avg Cyclomatic Complexity | XX.X | Y.Y | -Z.Z (-W%) | ✓ |
| Max Cyclomatic Complexity | XX | Y | -Z (-W%) | ✓ |
| Avg Function Length (lines) | XX | Y | -Z (-W%) | ✓ |
| Max Function Length (lines) | XX | Y | -Z (-W%) | ✓ |
| Avg Nesting Depth | X.X | Y.Y | -Z.Z (-W%) | ✓ |
| Max Nesting Depth | X | Y | -Z (-W%) | ✓ |
| Total Functions | X | Y | +Z (+W%) | Note: More but simpler |

### Documentation Metrics

| Metric | Before | After | Change | Status |
|--------|--------|-------|--------|--------|
| Module Docstring | No/Yes | Yes | Added | ✓ |
| Docstring Coverage | XX% | YY% | +Z% | ✓ |
| Type Hint Coverage | XX% | YY% | +Z% | ✓ |
| Documented Functions | X/Y | Z/Z | All documented | ✓ |

### Code Size Metrics

| Metric | Before | After | Change | Note |
|--------|--------|-------|--------|------|
| Total Lines of Code | XXX | YYY | +ZZ | More verbose but clearer |
| Blank Lines | XX | YY | +Z | Improved readability |
| Comment Lines | XX | YY | +Z | Better documentation |

---

## Validation Results

### Test Results

**Test Suite:** [Name]
**Tests Run:** XXX
**Tests Passed:** XXX ✓
**Tests Failed:** 0
**Test Coverage:** XX% (unchanged/improved)

**Details:**
- All existing tests pass without modification ✓
- No regression detected ✓
- Test execution time: [Duration] (±X% change)

### Performance Validation

**Benchmark Results:**

| Function | Before | After | Change | Status |
|----------|--------|-------|--------|--------|
| `function_name()` | X.XX ms | Y.YY ms | +Z% | ✓ Within threshold |
| `another_function()` | X.XX ms | Y.YY ms | -Z% | ✓ Faster |

**Performance Assessment:**
- No function shows >10% regression ✓
- Overall performance impact: [Negligible/Positive/Within acceptable range]

### Code Quality Validation

**Linter Results:**
- Warnings Before: XX
- Warnings After: Y
- Reduction: Z warnings fixed

**Type Checker Results:**
- Type Errors Before: XX
- Type Errors After: 0 ✓
- New Type Coverage: YY%

---

## Risk Assessment

### Overall Risk: [Low/Medium/High]

**Risk Factors:**

✓ **Low Risk Factors:**
- All tests passing
- No public API changes
- Performance within acceptable range
- Changes are mechanical refactorings
- Full test coverage maintained

⚠ **Medium Risk Factors:**
- [If any, list here]

✗ **High Risk Factors:**
- [If any, list here]

### Risk Mitigation

[If medium/high risk, describe mitigation steps taken]

---

## Human Review Recommendations

**Review Required:** [Yes/No]

**Review Focus Areas:**
1. [Specific area if review needed - e.g., "Verify business logic in extracted payment_calculator() function"]
2. [Another area if applicable]
3. [Another area if applicable]

**Review Checklist:**
- [ ] Verify all tests pass
- [ ] Review extracted functions for correctness
- [ ] Confirm no unintended behavior changes
- [ ] Validate performance is acceptable
- [ ] Check documentation accuracy
- [ ] Verify error handling remains robust

---

## Breaking Changes

**API Changes:** [None/Listed Below]

[If any breaking changes, list them here with migration guide]

**Migration Guide:**
[If applicable, provide guidance for updating calling code]

---

## Lessons Learned

### What Went Well
1. [Positive outcome or discovery]
2. [Another positive aspect]

### Challenges Encountered
1. [Challenge faced and how it was resolved]
2. [Another challenge]

### Recommendations for Future
1. [Suggestion for similar refactorings]
2. [Process improvement suggestion]

---

## Related Refactorings

### Recommended Follow-Ups

Based on this refactoring, these related improvements are recommended:

1. **[Related File/Function]**
   - Issue: [Similar problem]
   - Estimated Effort: [Duration]
   - Priority: [Low/Medium/High]

2. **[Another Related Area]**
   - Issue: [Description]
   - Estimated Effort: [Duration]
   - Priority: [Low/Medium/High]

---

## Commit Information

**Branch:** `feature/refactor-[description]`
**Commits:** X commit(s)

**Commit Messages:**
- `[commit-hash]` - [Commit message]
- `[commit-hash]` - [Commit message]

**Pull Request:** #XXX (if applicable)

---

## Sign-Off

**Refactored By:** [Your Name]
**Date:** YYYY-MM-DD

**Reviewed By:** [Reviewer Name] (if applicable)
**Review Date:** YYYY-MM-DD

**Approved For Merge:** [Yes/Pending/No]

---

## Appendix

### Files Modified
- `path/to/file1.ext` - [Description of changes]
- `path/to/file2.ext` - [Description of changes]

### References
- [Link to relevant documentation]
- [Link to related issues/PRs]
- [Link to patterns used]

### Additional Notes
[Any other relevant information, context, or observations]
