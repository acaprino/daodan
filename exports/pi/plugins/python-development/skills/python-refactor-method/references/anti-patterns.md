<daodan_host_binding host="pi">
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

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi has no network tool: network fetch and network search run as shell
commands, and a user question is asked in the reply while the run waits for the
answer.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

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

# Code Anti-Patterns Reference

This document catalogs investigation leads for readability and maintainability. Promote only evidenced comprehension or behavioral cost under the project’s requirements. Line counts, missing classes, annotations and docstring percentages are not standalone defects; pure modules and small CLIs can be the simplest correct design. Review bindings consume this knowledge read-only.

## Table of Contents

1. [High-Priority Anti-Patterns](#high-priority-anti-patterns)
2. [Medium-Priority Anti-Patterns](#medium-priority-anti-patterns)
3. [Low-Priority Anti-Patterns](#low-priority-anti-patterns)

---

## High-Priority Anti-Patterns

These anti-patterns significantly harm code comprehension and should be fixed first.

### 1. Script-Like / Procedural Code (Spaghetti Code)

**Problem:** Shared mutable state or unrelated responsibilities obscure ownership and cause demonstrated coupling. Procedural code alone is not a defect.

**Detection:**
- Global variables for state management
- Functions scattered without cohesion
- State ownership obscured by poorly chosen modules or classes
- Unrelated responsibilities sharing mutable state
- No clear separation of concerns
- Direct dependencies instead of dependency injection

**Impact:**
- Impossible to test in isolation
- Global state causes unpredictable behavior
- Difficult to reuse components
- No clear boundaries or responsibilities
- Changes in one area break unrelated functionality
- Cannot scale or extend easily

**Example:**
```python
# BAD: Script-like code with global state
users_cache = {}  # Global state!
API_URL = "https://api.example.com"

def fetch_user(user_id):
    global users_cache  # Modifying global state
    if user_id in users_cache:
        return users_cache[user_id]

    response = requests.get(f"{API_URL}/users/{user_id}")
    data = response.json()
    users_cache[user_id] = data
    return data

def process_user(user_id):
    user = fetch_user(user_id)
    # ... scattered processing logic
    return processed_data

# Executing at module level
if __name__ == "__main__":
    result = process_user(123)
```

**Fix:** Clarify ownership using existing modules or classes; use oop_principles.md when state encapsulation is justified.

**Good Example:**
```python
# GOOD: OOP-based with clear structure
# models/user.py
@dataclass
class User:
    id: int
    name: str
    email: str

# repositories/user_repository.py
class UserRepository:
    def __init__(self, api_client: APIClient):
        self._api_client = api_client
        self._cache: dict[int, User] = {}

    def get_by_id(self, user_id: int) -> Optional[User]:
        if user_id in self._cache:
            return self._cache[user_id]

        data = self._api_client.get(f"/users/{user_id}")
        if data:
            user = User(**data)
            self._cache[user_id] = user
            return user
        return None

# services/user_service.py
class UserService:
    def __init__(self, user_repository: UserRepository):
        self._user_repo = user_repository

    def process_user(self, user_id: int) -> dict:
        user = self._user_repo.get_by_id(user_id)
        if not user:
            return {'error': 'User not found'}
        return self._process(user)

    def _process(self, user: User) -> dict:
        # Processing logic
        pass
```

**Related Patterns:** Repository Pattern, Service Layer, Dependency Injection
**Related Reference:** See `references/oop_principles.md` for complete guide

---

### 2. God Object / God Class

**Problem:** One class responsible for too many unrelated things.

**Detection:**
- Class > 500 lines
- Class has > 10 public methods
- Class name contains "Manager", "Helper", "Utility", "Handler"
- Methods handle unrelated responsibilities
- Difficult to describe class purpose in one sentence

**Impact:**
- Violates Single Responsibility Principle
- Impossible to maintain
- Changes risk breaking everything
- Cannot test in isolation
- Poor reusability

**Example:**
```python
# BAD: God Object
class ApplicationManager:
    def __init__(self):
        self.users = []
        self.products = []
        self.orders = []

    def add_user(self): pass
    def delete_user(self): pass
    def validate_user(self): pass
    def send_email(self): pass
    def process_payment(self): pass
    def generate_report(self): pass
    def backup_database(self): pass
    def log_activity(self): pass
    def manage_sessions(self): pass
    # ... 50 more methods
```

**Fix:** Split into focused classes with single responsibilities

**Good Example:**
```python
# GOOD: Separated responsibilities
class UserManager:
    """Manages user operations only."""
    pass

class EmailService:
    """Handles email operations only."""
    pass

class PaymentService:
    """Handles payment operations only."""
    pass

class ReportService:
    """Handles report generation only."""
    pass
```

**Related Patterns:** Single Responsibility Principle, Service Layer
**Related Reference:** See `references/oop_principles.md`

---

### 3. Complex Nested Conditionals (Arrow Anti-Pattern)

**Problem:** Deeply nested if/else blocks create "arrow" shape that's hard to follow.

**Detection:**
- Nesting depth > 3 levels
- Visual "arrow" pointing to right edge of screen

**Impact:**
- High cognitive load to understand control flow
- Difficult to test all branches
- Easy to introduce bugs when modifying

**Example:**
```python
# BAD: Arrow anti-pattern
def process_request(user, data, permissions):
    if user:
        if user.is_active:
            if data:
                if data.is_valid():
                    if permissions:
                        if 'write' in permissions:
                            # Finally do something
                            return save_data(data)
```

**Fix:** Use guard clauses (early returns) - see patterns.md

**Related Patterns:** Guard Clauses, Extract Method

---

### 4. God Functions (Too Long, Too Complex)

**Problem:** Single function doing too many unrelated things.

**Detection:**
- Function length > 50 lines
- Cyclomatic complexity > 15
- Function name contains "and" or multiple verbs
- Multiple levels of abstraction mixed

**Impact:**
- Impossible to understand without reading entire function
- Difficult to test individual logic pieces
- Changes risk breaking unrelated functionality
- Often violates Single Responsibility Principle

**Example:**
```python
# BAD: God function
def process_user_and_save_to_database_and_send_email(user_data):
    # 20 lines of validation
    # 15 lines of data transformation
    # 10 lines of database logic
    # 12 lines of email composition
    # 8 lines of error handling
    # Total: 65 lines of mixed concerns
```

**Fix:** Extract Method - break into focused functions (see patterns.md)

**Related Patterns:** Extract Method, Separate Concerns

---

### 5. Magic Numbers and Strings

**Problem:** Unexplained literal values scattered through code.

**Detection:**
- Numeric literals (except 0, 1, -1) without explanation
- String literals used multiple times
- Hardcoded thresholds, limits, or configuration

**Impact:**
- Meaning unclear without context
- Changes require finding all occurrences
- Easy to use wrong value by mistake
- Difficult to configure or test with different values

**Example:**
```python
# BAD: Magic numbers everywhere
def calculate_price(base_price, quantity):
    if quantity > 10:
        discount = 0.15
    elif quantity > 5:
        discount = 0.10
    else:
        discount = 0

    price = base_price * quantity * (1 - discount)

    if price > 100:
        price *= 1.08  # ???
    else:
        price += 5  # ???

    return price
```

**Fix:** Extract to named constants (see patterns.md)

**Related Patterns:** Extract Magic Numbers to Named Constants

---

### 6. Cryptic Variable Names

**Problem:** Single-letter or abbreviated names that don't convey meaning.

**Detection:**
- Single letters (except i, j, k for simple loops)
- Abbreviations without obvious meaning (tmp, d, val, obj, mgr)
- Generic names (data, info, item, thing)

**Impact:**
- Requires reading surrounding code to understand purpose
- Increases cognitive load
- Makes code review difficult
- Confusing months after writing

**Example:**
```python
# BAD: Cryptic names
def calc(d, r, t, m):
    p = d
    for i in range(t * m):
        p = p * (1 + r/m)
    return p
```

**Fix:** Use meaningful names (see patterns.md)

**Related Patterns:** Meaningful Variable Names

---

### 7. Missing Type Hints (Python)

**Problem:** Function signatures without type information.

**Detection:**
- Function parameters without type annotations
- Return types not specified
- Generic types (dict, list) without element types

**Impact:**
- Unclear what types function expects/returns
- No IDE autocomplete or type checking
- Runtime type errors not caught early
- Difficult to refactor safely

**Example:**
```python
# BAD: No type hints
def process_orders(orders, user):
    results = []
    for order in orders:
        if check_permission(user, order):
            result = process(order)
            results.append(result)
    return results
```

**Fix:** Add comprehensive type hints

```python
# GOOD: Clear type hints
from typing import List

def process_orders(
    orders: List[Order],
    user: User
) -> List[ProcessResult]:
    results: List[ProcessResult] = []
    for order in orders:
        if check_permission(user, order):
            result = process(order)
            results.append(result)
    return results
```

---

### 8. Missing or Inadequate Docstrings

**Problem:** Functions without documentation of purpose, parameters, or behavior.

**Detection:**
- Public functions without docstrings
- Docstrings that just repeat function name
- Missing parameter descriptions
- Missing return value descriptions
- No exception documentation

**Impact:**
- Unclear how to use function correctly
- Users must read implementation to understand behavior
- Edge cases and exceptions not documented
- Difficult for new team members

**Example:**
```python
# BAD: No docstring
def calculate_discount(user, order):
    if user.tier == 'gold':
        return order.total * 0.2
    elif user.tier == 'silver':
        return order.total * 0.1
    return 0

# BAD: Useless docstring
def calculate_discount(user, order):
    """Calculate discount."""  # Adds nothing!
    # ... implementation
```

**Fix:** Write comprehensive docstrings (see patterns.md)

**Related Patterns:** Comprehensive Function Docstrings

---

### 9. Unclear Error Handling

**Problem:** Errors silently swallowed or handled unclearly.

**Detection:**
- Bare `except:` clauses
- Empty exception handlers
- Generic exception catching without re-raising
- Errors converted to None without logging

**Impact:**
- Bugs hide silently
- Difficult to debug failures
- Unclear what errors can occur
- May mask serious problems

**Example:**
```python
# BAD: Silent failure
def load_config():
    try:
        with open('config.json') as f:
            return json.load(f)
    except:  # What errors? Why silent?
        return {}

# BAD: Too broad
def process_data(data):
    try:
        # 50 lines of code
        return result
    except Exception:  # Catches everything!
        return None
```

**Fix:** Handle specific exceptions, log errors, provide context

```python
# GOOD: Clear error handling
def load_config(config_path: str = 'config.json') -> Dict[str, Any]:
    """Load configuration from JSON file.

    Args:
        config_path: Path to config file

    Returns:
        Configuration dictionary

    Raises:
        ConfigNotFoundError: If config file doesn't exist
        ConfigParseError: If config file is invalid JSON
    """
    try:
        with open(config_path) as f:
            return json.load(f)
    except FileNotFoundError:
        log.error(f"Config file not found: {config_path}")
        raise ConfigNotFoundError(f"No config file at {config_path}")
    except json.JSONDecodeError as e:
        log.error(f"Invalid JSON in config: {e}")
        raise ConfigParseError(f"Config file has invalid JSON: {e}")
```

---

### 10. Mixed Abstraction Levels

**Problem:** High-level and low-level operations mixed in same function.

**Detection:**
- Function has both business logic and implementation details
- Some lines are conceptual, others are mechanical
- Reading requires switching between abstraction levels

**Impact:**
- Difficult to understand function purpose
- Can't see the big picture
- Implementation details obscure logic
- Hard to modify without affecting unrelated parts

**Example:**
```python
# BAD: Mixed levels
def process_order(order):
    # High-level
    customer = get_customer(order.customer_id)

    # Low-level detail
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("UPDATE inventory SET stock = stock - %s WHERE id = %s",
                   (order.quantity, order.product_id))

    # High-level
    send_confirmation(customer.email)

    # Low-level detail
    cursor.execute("INSERT INTO logs (message) VALUES (%s)", ("Order processed",))
    conn.commit()
```

**Fix:** Consistent Abstraction Levels (see patterns.md)

**Related Patterns:** Consistent Abstraction Levels, Separate Concerns

---

## Medium-Priority Anti-Patterns

These anti-patterns harm maintainability but are less critical than high-priority ones.

### 11. Duplicate Code (DRY Violations)

**Problem:** Same or similar code repeated multiple times.

**Detection:**
- Identical code blocks in multiple places
- Similar logic with minor variations
- Copy-pasted functions with small changes

**Impact:**
- Bug fixes must be applied in multiple places
- Inconsistencies introduced over time
- Increased code size and maintenance burden
- Changes are error-prone

**Fix:** Extract common logic to shared function

---

### 12. Primitive Obsession

**Problem:** Using primitive types (string, int, dict) instead of domain objects.

**Detection:**
- Dictionaries with fixed keys used as objects
- String constants representing enumerations
- Multiple primitive parameters that logically go together
- Validation logic scattered across codebase

**Impact:**
- No type safety
- Easy to pass wrong values
- Validation logic duplicated
- Domain concepts not explicitly modeled

**Example:**
```python
# BAD: Primitives everywhere
def create_user(name: str, email: str, role: str, status: str):
    if '@' not in email:  # Validation scattered
        raise ValueError()
    if role not in ['admin', 'user', 'guest']:  # Validation scattered
        raise ValueError()
    return {'name': name, 'email': email, 'role': role, 'status': status}

# GOOD: Domain objects
@dataclass
class Email:
    """Value object for email addresses."""
    address: str

    def __post_init__(self):
        if '@' not in self.address:
            raise ValueError(f"Invalid email: {self.address}")

class UserRole(Enum):
    """User role enumeration."""
    ADMIN = 'admin'
    USER = 'user'
    GUEST = 'guest'

@dataclass
class User:
    """User entity."""
    name: str
    email: Email
    role: UserRole
    status: str
```

---

### 13. Long Parameter Lists

**Problem:** Functions with too many parameters.

**Detection:**
- > 5 parameters
- Many boolean flags
- Parameters that always passed together

**Impact:**
- Easy to pass arguments in wrong order
- Difficult to remember parameter order
- Function signature changes affect many callers
- Often indicates function does too much

**Fix:**
- Group related parameters into objects
- Use builder pattern for complex construction
- Split function if doing too much

**Example:**
```python
# BAD: Too many parameters
def create_report(user_id, start_date, end_date, include_details,
                  include_summary, format, timezone, currency,
                  filter_by_status, filter_by_type):
    pass

# GOOD: Parameter object
@dataclass
class ReportOptions:
    """Configuration for report generation."""
    start_date: date
    end_date: date
    include_details: bool = True
    include_summary: bool = True
    format: str = 'pdf'
    timezone: str = 'UTC'
    currency: str = 'USD'
    filter_by_status: Optional[str] = None
    filter_by_type: Optional[str] = None

def create_report(user_id: int, options: ReportOptions):
    pass
```

---

### 14. Comments Explaining What Instead of Why

**Problem:** Comments that describe what code does instead of why it does it.

**Detection:**
- Comment restates code in English
- Comment documents obvious operation
- Comment becomes outdated when code changes
- Code needs comment to be understood

**Impact:**
- Comments add noise without value
- Comments become outdated and misleading
- Indicates code should be clearer
- Maintenance burden keeping comments synchronized

**Example:**
```python
# BAD: Obvious comments
# Increment counter by 1
counter += 1

# Get user by ID
user = get_user(user_id)

# Check if user is active
if user.is_active:
    # Do something
    pass

# GOOD: Comments explain WHY
# Force cache clear to ensure fresh data after schema migration
cache.clear()

# Use exponential backoff to avoid overwhelming API during outages
time.sleep(2 ** retry_count)
```

**Fix:**
- Make code self-documenting through naming
- Only comment non-obvious reasoning
- Move "what" explanations to docstrings

---

## Low-Priority Anti-Patterns

These anti-patterns are minor annoyances but should still be addressed.

### 15. Inconsistent Naming Conventions

**Problem:** Mixed naming styles within codebase.

**Detection:**
- camelCase mixed with snake_case
- Inconsistent capitalization
- Some booleans use is_/has_, others don't

**Impact:**
- Looks unprofessional
- Harder to search and navigate
- Cognitive load from switching conventions

**Fix:** Follow language conventions consistently

---

### 16. Redundant Comments

**Problem:** Comments that add no information beyond code itself.

**Detection:**
- Comment is exact translation of code
- Comment just repeats function name
- Outdated comments that don't match code

**Example:**
```python
# BAD: Redundant
# Create a new user
create_user()

# Validate the email
if not is_valid_email(email):
    raise ValueError()

# GOOD: Only when adding value
# Bypass cache to ensure consistency after database migration
user = get_user(user_id, use_cache=False)
```

**Fix:** Delete redundant comments, keep only valuable ones

---

### 17. Unused Code

**Problem:** Commented-out code, unused imports, unused variables.

**Detection:**
- Code blocks commented out
- Imports not used in file
- Variables assigned but never read
- Functions never called

**Impact:**
- Clutter and noise
- Confusion about whether code should be there
- Maintenance burden
- Git history preserves old code better than comments

**Fix:** Delete completely (git history preserves it if needed)

---

## Anti-Pattern Priority Matrix

Use this matrix to prioritize refactoring efforts:

| Anti-Pattern | Impact | Effort | Priority |
|-------------|--------|--------|----------|
| #1. Script-Like Code | **Critical** | High | **HIGHEST** |
| #2. God Object/Class | **Critical** | High | **HIGHEST** |
| #3. Complex Nested Conditionals | High | Low | **High** |
| #4. God Functions | High | Medium | **High** |
| #5. Magic Numbers | Medium | Low | **High** |
| #6. Cryptic Names | Medium | Low | **High** |
| #7. Missing Type Hints | Medium | Low | **High** |
| #8. Missing Docstrings | Medium | Low | **High** |
| #9. Unclear Error Handling | High | Medium | **High** |
| #10. Mixed Abstraction Levels | High | Medium | **High** |
| #11. Duplicate Code | Medium | Medium | Medium |
| #12. Primitive Obsession | Medium | High | Medium |
| #13. Long Parameter Lists | Medium | Medium | Medium |
| #14. Misleading Comments | Low | Low | Low |
| #15. Inconsistent Naming | Low | Low | Low |
| #16. Redundant Comments | Low | Low | Low |
| #17. Unused Code | Low | Low | Low |

**Priority Formula:** (Impact × 2 + Maintainability × 2 - Effort) = Priority Score

Focus refactoring on high-priority anti-patterns first for maximum improvement with minimal effort.

---

## Detection Checklist

Use this checklist to scan code for anti-patterns:

### Function-Level Checks
- [ ] Function > 30 lines? → Extract Method
- [ ] Nesting > 3 levels? → Guard Clauses
- [ ] Complexity > 10? → Simplify or Extract
- [ ] > 5 parameters? → Parameter Object
- [ ] No docstring? → Add Documentation
- [ ] No type hints? → Add Type Hints
- [ ] Cryptic names? → Rename
- [ ] Magic numbers? → Extract Constants

### File-Level Checks
- [ ] No module docstring? → Add Documentation
- [ ] Mixed abstraction levels? → Separate Concerns
- [ ] Duplicate code? → Extract Common Logic
- [ ] Unused imports? → Remove
- [ ] Inconsistent naming? → Standardize

### Architecture-Level Checks
- [ ] God classes (>500 lines)? → Split Responsibilities
- [ ] Mixed concerns? → Separate Layers
- [ ] Primitive obsession? → Domain Objects
- [ ] Unclear error handling? → Explicit Exceptions

Run this checklist systematically to identify refactoring opportunities across the codebase.
