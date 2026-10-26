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
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
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

# Cognitive Complexity: Complete Guide

> Cognitive complexity measures how **difficult code is to understand**, not how many execution paths exist.

---

## Calculation Rules

### Rule 1: Base Increments (+1)

Every **break in linear flow** adds +1:

```python
def example():
    if condition:        # +1
        pass
    for item in items:   # +1
        pass
    while running:       # +1
        pass
    try:                 # +0 (try does not increment)
        pass
    except Error:        # +1
        pass
    condition and do()   # +1 (logical operator as branch)
```

**Structures that increment:**
- `if`, `elif`, `else`
- `for`, `while`
- `except`, `with`
- `and`, `or` (when they change flow)
- Recursion (+1 per recursive call)
- `break`, `continue` with label

**Structures that do NOT increment:**
- `try` (only `except` increments)
- `finally`
- Simple lambdas
- Top-level ternary operator

---

### Rule 2: Nesting Penalty (additive by depth)

Each nested structure adds **+1 per nesting level**:

```python
def nested_example():
    if a:                    # +1 (nesting=0)
        if b:                # +2 (1 base + 1 nesting)
            if c:            # +3 (1 base + 2 nesting)
                if d:        # +4 (1 base + 3 nesting)
                    pass
# Total: 1+2+3+4 = 10 for just 4 ifs!
```

**Impact of nesting:**

| Levels | Formula | Total Complexity |
|--------|---------|-----------------|
| 1 if | 1 | 1 |
| 2 nested ifs | 1+2 | 3 |
| 3 nested ifs | 1+2+3 | 6 |
| 4 nested ifs | 1+2+3+4 | 10 |
| 5 nested ifs | 1+2+3+4+5 | 15 |

A single chain sums 1 + 2 + … + n = n(n+1)/2: quadratic, not exponential. This structural metric does not itself measure comprehension or runtime cost.

---

### Rule 3: Boolean Sequences

**Same operator in sequence = FREE:**
```python
# Complexity +1 (counts as a single break)
if a and b and c and d:
    pass
```

**Operator change = +1 per change:**
```python
# Complexity +3 (each and->or or or->and change = +1)
if a and b or c and d:
    #       ^       ^
    #      +1      +1 (plus the +1 base = 3)
    pass
```

**Best practice:** Extract complex conditions into named variables:
```python
# BEFORE: Complexity +3
if user.active and user.verified or user.is_admin and not user.banned:
    ...

# AFTER: Complexity +1 (single condition)
is_regular_authorized = user.active and user.verified
is_admin_authorized = user.is_admin and not user.banned
if is_regular_authorized or is_admin_authorized:
    ...
```

---

### Rule 4: Switch/Match Counts ONCE

**if-elif chain = +1 per branch:**
```python
# Complexity = 4
def get_word(n):
    if n == 1:           # +1
        return "one"
    elif n == 2:         # +1
        return "couple"
    elif n == 3:         # +1
        return "few"
    else:                # +1
        return "lots"
```

**match/switch = +1 TOTAL:**
```python
# Complexity = 1 (!)
def get_word(n):
    match n:             # +1 for the entire switch
        case 1: return "one"
        case 2: return "couple"
        case 3: return "few"
        case _: return "lots"
```

**Use `match` (Python 3.10+) to drastically reduce complexity.**

---

### Rule 5: Extract Method RESETS Nesting

**The most powerful pattern for reducing complexity:**

```python
# BEFORE: Complexity = 6
def process_items(items):
    for item in items:           # +1, nesting +1
        if item.valid:           # +2 (1 + nesting 1)
            if item.ready:       # +3 (1 + nesting 2)
                handle(item)
# Total: 1+2+3 = 6

# AFTER: Complexity = 3 (split across 2 functions)
def process_items(items):
    for item in items:           # +1
        process_single_item(item)
# Function 1 complexity: 1

def process_single_item(item):   # NESTING RESET TO 0!
    if not item.valid:           # +1 (nesting 0)
        return
    if not item.ready:           # +1 (nesting 0)
        return
    handle(item)
# Function 2 complexity: 2

# Total: 1 + 2 = 3 (50% reduction!)
```

---

## Tools: Ruff + Complexipy

### Recommended Stack

| Tool | Cyclomatic (CC) | Cognitive (CoC) | Speed |
|------|-----------------|-----------------|-------|
| **Ruff** | C901 | - | Rust, very fast |
| **Complexipy** | - | Yes | Rust, very fast |
| flake8 + plugin | Yes | Yes (inactive) | Python, slow |

**Ruff + Complexipy** is the recommended stack: both written in Rust, actively maintained, modern ecosystem.

### Setup

```bash
pip install ruff complexipy radon wily
```

### Complexipy: Dedicated Cognitive Complexity Tool

Features:
- Written in Rust (very fast)
- Actively maintained (v5.1.0, December 2025)
- Configuration via pyproject.toml
- Snapshot for legacy code (gradual adoption)
- Pre-commit hook, GitHub Action, VSCode extension

#### Installation

```bash
pip install complexipy
```

#### CLI

```bash
# Basic analysis
complexipy src/

# Custom threshold (default: 15, same as SonarQube)
complexipy src/ --max-complexity-allowed 15

# JSON output for CI
complexipy src/ --output-json

# Show all functions (ignore threshold)
complexipy src/ --ignore-complexity

# Sort by complexity
complexipy src/ --sort desc
```

#### Configuration (pyproject.toml)

```toml
[tool.complexipy]
paths = ["src"]
max-complexity-allowed = 15    # SonarQube default
exclude = ["tests", "migrations", "vendor"]
quiet = false
output-json = false
```

#### Python API

```python
from complexipy import file_complexity, code_complexity

# Analyze file
result = file_complexity("src/user_service.py")
print(f"File: {result.path}")
print(f"Total complexity: {result.complexity}")

for func in result.functions:
    status = "WARNING" if func.complexity > 15 else "OK"
    print(f"  {status} {func.name}: {func.complexity} (lines {func.line_start}-{func.line_end})")

# Analyze code string
code = """
def example(x):
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                print(i)
"""
result = code_complexity(code)
print(f"Complexity: {result.complexity}")
```

#### Snapshot for Legacy Code

Key feature for gradual adoption on existing codebases:

```bash
# 1. Create snapshot of current state
complexipy src/ --snapshot-create --max-complexity-allowed 15
# Creates: complexipy-snapshot.json

# 2. In CI: block only REGRESSIONS (new complex functions)
complexipy src/ --max-complexity-allowed 15
# Passes if no new functions exceed threshold
# Fails if NEW functions exceed threshold
# Existing functions in snapshot are "grandfathered"

# 3. When you fix a function, it is automatically removed from the snapshot
```

#### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/rohaquinlop/complexipy-pre-commit
    rev: v3.0.0
    hooks:
      - id: complexipy
        args: [--max-complexity-allowed, "15"]
```

#### GitHub Action

```yaml
- uses: rohaquinlop/complexipy-action@v2
  with:
    paths: src/
    max_complexity_allowed: 15
    output_json: true
```

#### VSCode Extension

Install "Complexipy" from the marketplace for real-time analysis with visual indicators.

### Ruff Configuration (for cyclomatic + linting)

```toml
# pyproject.toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E", "W",     # pycodestyle
    "F",          # Pyflakes
    "C90",        # McCabe cyclomatic complexity
    "B",          # flake8-bugbear
    "SIM",        # flake8-simplify
    "N",          # pep8-naming
    "UP",         # pyupgrade
    "I",          # isort
]

[tool.ruff.lint.mccabe]
max-complexity = 10  # Cyclomatic complexity
```

### Complete Workflow

```bash
# 1. Fast linting
ruff check src/ --fix

# 2. Cognitive complexity
complexipy src/ --max-complexity-allowed 15

# 3. Maintainability Index
radon mi src/ -s

# 4. Historical trend (optional)
wily build src/ && wily report src/
```

---

## Combining Metrics

**Do not rely on a single metric.**

| Metric | Measures | Best Use |
|--------|----------|----------|
| **Cognitive Complexity** | Difficulty of understanding | Code review, maintainability |
| **Cyclomatic Complexity** | Execution paths | Test planning (min test cases) |
| **Maintainability Index** | Overall health | Dashboard, trends |

### Combined Setup

```bash
# Install all tools
pip install flake8 flake8-cognitive-complexity radon wily

# Combined analysis
flake8 src/ --max-cognitive-complexity=15 --max-complexity=10
radon cc src/ -a -s  # Cyclomatic + Average
radon mi src/ -s     # Maintainability Index
```

### Recommended Targets

| Metric | Conservative | Moderate | Permissive |
|--------|-------------|----------|------------|
| Cognitive | <= 10 | <= 15 | <= 25 |
| Cyclomatic | <= 5 | <= 10 | <= 20 |
| MI (Maintainability) | >= 80 | >= 65 | >= 50 |

---

## Progressive Thresholds for Legacy Code

**Do not apply strict thresholds to legacy code immediately.**

### Ratcheting Strategy

```yaml
# .github/workflows/quality.yml
- name: Quality Gate (Ratcheting)
  run: |
    # Save baseline if it doesn't exist
    if [ ! -f .quality-baseline.json ]; then
      python scripts/measure_all_metrics.py > .quality-baseline.json
    fi

    # Compare against baseline
    python scripts/compare_to_baseline.py .quality-baseline.json

    # Fail if WORSE, pass if equal or better
```

### Changed Files Only Strategy

```bash
# Apply strict thresholds ONLY to files modified in the PR
CHANGED_FILES=$(git diff --name-only origin/main...HEAD -- '*.py')

for file in $CHANGED_FILES; do
    flake8 "$file" --max-cognitive-complexity=10  # Strict for new code
done

# Permissive threshold for everything else
flake8 src/ --max-cognitive-complexity=25  # Lenient for legacy
```

### Adoption Phases

```ini
# Phase 1: Baseline (month 1-2)
max-cognitive-complexity = 30  # Permissive, block only extreme cases

# Phase 2: Reduction (month 3-6)
max-cognitive-complexity = 20  # Moderate

# Phase 3: Target (month 6+)
max-cognitive-complexity = 15  # SonarQube standard

# Phase 4: Strict (new code only)
max-cognitive-complexity = 10  # For greenfield code
```

---

## Historical Tracking with Wily

**Monitor trends over time, not just thresholds.**

### Setup

```bash
pip install wily

# Build cache (once)
wily build src/ -n 100  # Last 100 commits

# Report per file
wily report src/module.py

# Diff between commits
wily diff src/ -r HEAD~10..HEAD

# Trend graph
wily graph src/module.py complexity  # Opens browser

# Rank most complex files
wily rank src/ complexity
```

### CI Integration

```yaml
# .github/workflows/wily.yml
name: Complexity Trend

on:
  push:
    branches: [main]

jobs:
  wily:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 50  # Wily needs history

      - name: Setup
        run: pip install wily

      - name: Build Wily Cache
        run: wily build src/ -n 50

      - name: Check for Regression
        run: |
          # Fail if complexity INCREASED compared to previous commit
          wily diff src/ -r HEAD~1..HEAD --exit-zero
          if wily diff src/ -r HEAD~1..HEAD | grep -q "increased"; then
            echo "Complexity increased!"
            exit 1
          fi
```

### Dashboard Output

```
+--------------------------------------------------------------+
|                    COMPLEXITY TREND                            |
+--------------------------------------------------------------+
| File: src/services/user_service.py                            |
|                                                                |
| Commit    Date       CC    MI    CoC                          |
| -------------------------------------------                   |
| abc123    2024-01-01  12    75    18                           |
| def456    2024-01-15  10    78    15                           |
| ghi789    2024-02-01   8    82    12                           |
| jkl012    2024-02-15   6    85     9                           |
|                                                                |
| TREND: Improving (-50% complexity in 6 weeks)                 |
+--------------------------------------------------------------+
```

---

## High-Impact Refactoring Patterns

### Pattern 1: Dictionary Dispatch (eliminates if-elif chains)

```python
# BEFORE: Cognitive Complexity = 8
def process_action(action, data):
    if action == "create":           # +1
        return create_item(data)
    elif action == "read":           # +1
        return read_item(data)
    elif action == "update":         # +1
        return update_item(data)
    elif action == "delete":         # +1
        return delete_item(data)
    elif action == "archive":        # +1
        return archive_item(data)
    elif action == "restore":        # +1
        return restore_item(data)
    elif action == "clone":          # +1
        return clone_item(data)
    else:                            # +1
        raise ValueError(f"Unknown action: {action}")

# AFTER: Cognitive Complexity = 1
ACTION_HANDLERS = {
    "create": create_item,
    "read": read_item,
    "update": update_item,
    "delete": delete_item,
    "archive": archive_item,
    "restore": restore_item,
    "clone": clone_item,
}

def process_action(action, data):
    handler = ACTION_HANDLERS.get(action)
    if handler is None:              # +1 (single branch)
        raise ValueError(f"Unknown action: {action}")
    return handler(data)

# Reduction: 87.5%!
```

### Pattern 2: Guard Clauses (eliminates nesting)

```python
# BEFORE: Cognitive Complexity = 10
def process_order(order):
    if order:                           # +1
        if order.is_valid():            # +2 (nesting)
            if order.has_items():       # +3 (nesting)
                if order.payment_ok():  # +4 (nesting)
                    return fulfill(order)
    return OrderResult.failed()

# AFTER: Cognitive Complexity = 4
def process_order(order):
    if not order:                   # +1
        return OrderResult.failed()
    if not order.is_valid():        # +1
        return OrderResult.failed()
    if not order.has_items():       # +1
        return OrderResult.failed()
    if not order.payment_ok():      # +1
        return OrderResult.failed()
    return fulfill(order)

# Reduction: 60%!
```

### Pattern 3: Extract + Compose (breaks apart monster functions)

```python
# BEFORE: Single function with Cognitive Complexity = 25
def process_user_registration(data):
    # 20 lines of validation
    # 15 lines of normalization
    # 10 lines of saving
    # 10 lines of notification
    # 15 lines of logging
    pass  # 70+ lines, CC=25

# AFTER: Composition of simple functions
def process_user_registration(data):
    validated = validate_registration(data)      # CC=4
    normalized = normalize_user_data(validated)  # CC=2
    user = save_user(normalized)                 # CC=3
    send_welcome_email(user)                     # CC=2
    log_registration(user)                       # CC=1
    return user
# Main function: CC=0 (no branches!)
# Total distributed: 4+2+3+2+1 = 12 (but never >4 in a single function)
```

---

## Quick Reference

```
+-------------------------------------------------------------+
|              COGNITIVE COMPLEXITY CHEAT SHEET                 |
+-------------------------------------------------------------+
| INCREMENTS (+1):                                              |
|   if, elif, else, for, while, except, and, or, recursion    |
|                                                               |
| NESTING PENALTY (+1 per level):                              |
|   Each structure inside another adds a level                 |
|   4 nested ifs = 1+2+3+4 = 10 (not 4!)                      |
|                                                               |
| DOES NOT INCREMENT:                                           |
|   try (only except), finally, simple lambdas, switch/case    |
|                                                               |
| BOOLEAN SEQUENCES:                                            |
|   a and b and c = +1 (same operator)                         |
|   a and b or c  = +2 (operator change)                       |
+-------------------------------------------------------------+
| HIGH-IMPACT PATTERNS:                                         |
|   1. Guard clauses      - eliminates nesting penalty         |
|   2. Extract method     - resets nesting to 0                |
|   3. Dictionary dispatch - if-elif chain to O(1) lookup      |
|   4. match/switch       - n branches = +1 total              |
+-------------------------------------------------------------+
| RECOMMENDED THRESHOLDS:                                       |
|   Strict (new code):  <= 10                                  |
|   Standard (SonarQube): <= 15                                |
|   Legacy (initial):   <= 25                                  |
+-------------------------------------------------------------+
```
