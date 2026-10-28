<daodan_host_binding host="codex">
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

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. Network search and network fetch
use the runtime's registered web search tool when the Codex configuration enables
it. A user question uses the runtime's registered question tool when one exists;
otherwise ask it in the reply and wait for the answer. In particular, a shell example's
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

# Flake8 Code Quality Report

**Target:** `path/to/code`
**Date:** YYYY-MM-DD
**Analysis Type:** [Before Refactoring / After Refactoring]

---

## Executive Summary

**Status:** [PASSED / FAILED]
**Total Issues:** XXX
**Risk Level:** [Low / Medium / High]

[2-3 sentence summary of overall code quality based on flake8 analysis]

---

## Installed Plugins

### ESSENTIAL (Must-Have - Highest Impact)
✓/✗ **flake8-bugbear**: Finds likely bugs and design problems (B codes)
✓/✗ **flake8-simplify**: Suggests simpler, clearer code (SIM codes)
✓/✗ **flake8-cognitive-complexity**: Measures cognitive load (CCR codes)
✓/✗ **pep8-naming**: Enforces clear naming conventions (N codes)
✓/✗ **flake8-docstrings**: Ensures documentation (D codes)

### RECOMMENDED (Strong Readability Impact)
✓/✗ **flake8-comprehensions**: Cleaner comprehensions (C4 codes)
✓/✗ **flake8-expression-complexity**: Prevents complex expressions (ECE codes)
✓/✗ **flake8-functions**: Simpler function signatures (CFQ codes)
✓/✗ **flake8-variables-names**: Better variable naming (VNE codes)
✓/✗ **tryceratops**: Clean exception handling (TC codes)

### OPTIONAL (Nice to Have)
✓/✗ **flake8-builtins**: Prevents shadowing built-ins (A codes)
✓/✗ **flake8-eradicate**: Finds commented-out code (E800 codes)
✓/✗ **flake8-unused-arguments**: Flags unused parameters (U codes)
✓/✗ **flake8-annotations**: Validates type hints (ANN codes)
✓/✗ **pydoclint**: Complete docstrings (DOC codes)
✓/✗ **flake8-spellcheck**: Catches typos (SC codes)

### Missing Plugins

**Missing ESSENTIAL plugins (install these first):**
[List missing essential plugins]

**Installation Command:**
```bash
pip install flake8 [missing-essential-plugins]
```

**Missing RECOMMENDED plugins:**
[List missing recommended plugins]

**Installation Command:**
```bash
pip install [missing-recommended-plugins]
```

**Install all 16 plugins (full suite):**
```bash
pip install flake8 flake8-bugbear flake8-simplify \
    flake8-cognitive-complexity pep8-naming flake8-docstrings \
    flake8-comprehensions flake8-expression-complexity \
    flake8-functions flake8-variables-names tryceratops \
    flake8-builtins flake8-eradicate flake8-unused-arguments \
    flake8-annotations pydoclint flake8-spellcheck
```

---

## Issues by Severity

| Severity | Count | Percentage |
|----------|-------|------------|
| High     | XX    | XX%        |
| Medium   | XX    | XX%        |
| Low      | XX    | XX%        |
| **Total**| **XXX** | **100%** |

### Severity Distribution

```
High   [████████░░] XX%
Medium [██████░░░░] XX%
Low    [███░░░░░░░] XX%
```

---

## Issues by Category

| Category | Count | Description |
|----------|-------|-------------|
| Style Error (PEP 8) | XX | Code style violations |
| Style Warning (PEP 8) | XX | Code style warnings |
| PyFlakes Error | XX | Code logic errors |
| Complexity | XX | High complexity violations |
| Bugbear (Likely Bug) | XX | Potential bugs identified |
| Naming Convention | XX | PEP 8 naming violations |
| Docstring | XX | Missing or malformed docstrings |
| Annotations | XX | Missing type annotations |
| Simplification | XX | Code can be simplified |

---

## Top Issue Types

| Code | Count | Description | Severity |
|------|-------|-------------|----------|
| EXXX | XXX   | [Description of error code] | High/Med/Low |
| EXXX | XXX   | [Description] | High/Med/Low |
| EXXX | XXX   | [Description] | High/Med/Low |
| ... |

---

## Files with Most Issues

| File | Issue Count | Primary Issues |
|------|-------------|----------------|
| path/to/file1.py | XXX | E501, C901, D103 |
| path/to/file2.py | XXX | F401, N803, B008 |
| path/to/file3.py | XXX | E302, W503, D100 |
| ... |

---

## High Severity Issues

### Potential Bugs (Bugbear - B codes)

**B001** - Line XXX: Do not use bare `except:`
```python
# File: path/to/file.py:XXX
try:
    dangerous_operation()
except:  # Too broad!
    pass
```
**Impact:** May catch and hide critical errors like KeyboardInterrupt
**Fix:** Catch specific exceptions or use `except Exception:`

---

**B006** - Line XXX: Do not use mutable data structures as default arguments
```python
# File: path/to/file.py:XXX
def append_to_list(item, lst=[]):  # Dangerous!
    lst.append(item)
    return lst
```
**Impact:** Shared mutable default causes unexpected behavior
**Fix:** Use `lst=None` and initialize inside function

---

### PyFlakes Errors (F codes)

**F401** - Lines XXX, YYY, ZZZ: Module imported but unused
**Impact:** Clutters namespace, suggests dead code
**Fix:** Remove unused imports or add to `__all__`

**F841** - Lines XXX, YYY: Local variable assigned but never used
**Impact:** Dead code, possible logic error
**Fix:** Remove assignment or use the variable

---

### Runtime Errors (E9 codes)

[List any E9xx codes - these are critical syntax/runtime errors]

---

## Medium Severity Issues

### Complexity (C codes)

**C901** - Function too complex
```
Function: complex_function() (Line XXX)
Cyclomatic Complexity: XX (threshold: 10)
```
**Impact:** Hard to understand and test
**Recommendation:** Apply Extract Method pattern (see patterns.md)

---

### Naming Conventions (N codes)

**N802** - Lines XXX, YYY: Function name should be lowercase
```python
def CalculateTotal():  # Should be: calculate_total()
    pass
```

**N803** - Lines XXX: Argument name should be lowercase
**N806** - Lines XXX: Variable should be lowercase

---

### Annotations (A codes)

**ANN201** - Lines XXX, YYY, ZZZ: Missing return type annotation
```python
def process_data(data: str):  # Missing -> ReturnType
    return data.upper()
```
**Impact:** Reduced type safety, no IDE support
**Fix:** Add return type annotation

---

## Low Severity Issues

### Style Errors (E/W codes)

**E501** - Line too long (XX > 88 characters)
**E302** - Expected 2 blank lines, found 1
**E303** - Too many blank lines
**W503** - Line break before binary operator

[List most common style violations with counts]

---

### Docstring Issues (D codes)

**D100** - Missing docstring in public module
**D103** - Missing docstring in public function
**D107** - Missing docstring in __init__

**Functions Missing Docstrings:**
1. `function_name()` - Line XXX
2. `another_function()` - Line YYY
3. [...]

---

### Simplification Opportunities (S codes)

**SIM105** - Lines XXX: Use `contextlib.suppress()` instead of try/except/pass
**SIM108** - Lines XXX: Use ternary operator instead of if/else
**SIM118** - Lines XXX: Use `key in dict` instead of `key in dict.keys()`

---

## Detailed Issue List

### Critical Issues (Must Fix)

1. **File:** `path/to/file.py:XXX`
   **Code:** BXXX
   **Severity:** High
   **Message:** [Full error message]
   **Recommendation:** [How to fix]

2. [Continue with all high severity issues...]

---

### Important Issues (Should Fix)

[Medium severity issues with line numbers and recommendations]

---

### Minor Issues (Nice to Fix)

[Low severity issues - can list first 50]

---

## Recommendations

### Immediate Actions (High Priority)

1. **Fix all Bugbear issues (B codes)** - These indicate likely bugs
   - Estimated effort: [Duration]
   - Files affected: [X files]

2. **Address PyFlakes errors (F codes)** - Dead code and logic issues
   - Estimated effort: [Duration]
   - Files affected: [X files]

3. **Reduce function complexity (C901)** - Apply Extract Method pattern
   - Estimated effort: [Duration]
   - Functions affected: [X functions]

### Short-Term Actions (Medium Priority)

4. **Add missing docstrings (D codes)** - Improve documentation
   - Target: >80% coverage
   - Estimated effort: [Duration]

5. **Add type annotations (ANN codes)** - Improve type safety
   - Target: >90% coverage
   - Estimated effort: [Duration]

6. **Fix naming conventions (N codes)** - Follow PEP 8
   - Estimated effort: [Duration]

### Long-Term Actions (Low Priority)

7. **Address style violations (E/W codes)** - Improve consistency
   - Consider using Black formatter
   - Estimated effort: [Duration]

8. **Apply simplifications (S codes)** - Make code more Pythonic
   - Estimated effort: [Duration]

---

## Comparison with Targets

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Total Issues | XXX | 0 | ⚠ |
| High Severity | XX | 0 | ⚠/✓ |
| Medium Severity | XX | <10 | ⚠/✓ |
| Complexity Violations | XX | 0 | ⚠/✓ |
| Docstring Coverage | XX% | >80% | ⚠/✓ |
| Type Hint Coverage | XX% | >90% | ⚠/✓ |

---

## Integration with Refactoring Workflow

### Issues Aligned with Anti-Patterns

[Map flake8 issues to anti-patterns.md categories]

**Complex Nested Conditionals** ← C901 (High complexity)
**God Functions** ← C901 (Complexity), E501 (Too long)
**Magic Numbers** ← No direct flake8 code (manual review needed)
**Cryptic Names** ← N803, N806 (Naming violations)
**Missing Docstrings** ← D100-D107 (Docstring codes)
**Missing Type Hints** ← ANN* codes
**Unclear Error Handling** ← B001 (Bare except)

### Recommended Patterns to Apply

Based on flake8 results, apply these patterns from patterns.md:

1. **Extract Method** - For C901 complexity violations
2. **Guard Clauses** - For deeply nested code (manual + C901)
3. **Add Documentation** - For D codes
4. **Add Type Hints** - For ANN codes
5. **Improve Naming** - For N codes
6. **Simplify Code** - For S codes

---

## Next Steps

1. **Review High Severity Issues** - Fix all B, F, and E9 codes first
2. **Run Refactoring Workflow** - Use patterns from patterns.md
3. **Re-run flake8** - Measure improvements
4. **Compare Reports** - Use compare_flake8_reports.py

**Command to Re-run:**
```bash
python scripts/analyze_with_flake8.py <target> --output after_flake8.json --html after_flake8.html
```

**Command to Compare:**
```bash
python scripts/compare_flake8_reports.py before_flake8.json after_flake8.json --html comparison.html
```

---

## Configuration Used

```ini
[flake8]
max-line-length = 88
max-complexity = 10
max-cognitive-complexity = 10
max-expression-complexity = 7
docstring-convention = google
```

**Configuration File:** `assets/.flake8`
[Copy this file to your project root for consistent analysis]

---

## Additional Resources

- **Flake8 Documentation:** https://flake8.pycqa.org/
- **Plugin Documentation:**
  - flake8-bugbear: https://github.com/PyCQA/flake8-bugbear
  - flake8-docstrings: https://github.com/PyCQA/flake8-docstrings
  - flake8-simplify: https://github.com/MartinThoma/flake8-simplify
- **Anti-Patterns Reference:** `references/anti-patterns.md`
- **Refactoring Patterns:** `references/patterns.md`

---

## Report Metadata

**Generated By:** python-refactor-method skill
**Skill Version:** 1.1.0
**Timestamp:** YYYY-MM-DD HH:MM:SS
**Flake8 Version:** [Version from --version]
**Python Version:** [Version]

---

## Notes

[Any additional observations, context, or recommendations specific to this codebase]
