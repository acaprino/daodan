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

# Comment Taxonomy Reference

Based on antirez's "Writing system software: code comments" (9 types), adapted for Python.

---

## Type 1: Function Comments

**Purpose:** Describe what a function, class, or module does.

**Python scope:** Docstrings on modules, classes, functions, methods.

**Quality markers:**
- Imperative mood ("Return", "Calculate", not "Returns", "Calculates" for summary line)
- Covers: purpose, args (semantics, not types if hints exist), returns, raises, side effects
- First line stands alone as summary
- Does not duplicate type hints

**Example:**
```python
def retry_with_backoff(func: Callable, max_retries: int = 3) -> Any:
    """Execute a function with exponential backoff on failure.

    Retries on any exception, doubling the wait time between attempts.
    Useful for flaky network calls where transient failures are expected.

    Args:
        func: Callable to execute. Must take no arguments.
        max_retries: Maximum retry attempts before re-raising.

    Returns:
        The return value of func on success.

    Raises:
        Exception: The last exception if all retries are exhausted.
    """
```

**Bad example (placeholder):**
```python
def retry_with_backoff(func, max_retries=3):
    """Retry with backoff."""  # Adds nothing useful
```

---

## Type 2: Design Comments

**Purpose:** Explain architectural decisions and design rationale.

**Python scope:** Module-level docstrings, class-level docstrings, or inline `#` above complex structures.

**Quality markers:**
- Explains *why this design* over alternatives
- References constraints that drove the decision
- May reference external design docs or ADRs

**Example:**
```python
class ConnectionPool:
    """Thread-safe database connection pool.

    Uses a bounded semaphore rather than a queue to manage connections.
    A queue approach was considered but rejected because it doesn't
    provide backpressure when all connections are in use - callers
    would block indefinitely. The semaphore raises after timeout,
    letting callers handle congestion explicitly.
    """
```

**Example (inline):**
```python
# Store sessions in Redis rather than DB to avoid write amplification
# on every request. Accept the trade-off of losing sessions on Redis restart
# since users can re-authenticate cheaply.
session_store = RedisSessionStore(ttl=3600)
```

---

## Type 3: Why Comments

**Purpose:** Explain non-obvious reasoning behind a specific code decision.

**Python scope:** Inline `#` comments, one line above or at end of the relevant line.

**Quality markers:**
- Answers "why?", not "what?"
- Would not be obvious to a competent developer reading the code
- References the constraint, bug, or requirement that caused the decision

**Example:**
```python
# Use <= instead of < because sensor readings are inclusive on both ends,
# per the hardware spec (Section 4.2.1)
if reading <= threshold:
    trigger_alert(reading)
```

```python
# Sleep before retry to avoid overwhelming the rate-limited API.
# 429 responses include Retry-After but we add jitter to prevent
# thundering herd when multiple workers hit the limit simultaneously.
time.sleep(base_delay * (2 ** attempt) + random.uniform(0, 0.5))
```

**Bad example (restates code):**
```python
# Check if reading is less than or equal to threshold
if reading <= threshold:
```

---

## Type 4: Teacher Comments

**Purpose:** Explain domain knowledge, algorithms, or concepts the reader may not know.

**Python scope:** Inline `#` comments, sometimes multi-line blocks above complex code.

**Quality markers:**
- Teaches a concept, not just labels it
- Accurate domain explanation
- Links to external references when applicable (papers, RFCs, specs)

**Example:**
```python
# Levenshtein distance: minimum single-character edits (insert, delete,
# substitute) to transform one string into another. Used here for
# fuzzy matching user input against known command names.
# Reference: https://en.wikipedia.org/wiki/Levenshtein_distance
def fuzzy_match(input_str: str, candidates: list[str]) -> str | None:
```

```python
# Bloom filter: probabilistic set membership test. False positives possible,
# false negatives impossible. We use it as a fast pre-filter before the
# expensive database lookup - if the filter says "not present", we skip
# the DB query entirely.
if not bloom_filter.might_contain(key):
    return None
```

---

## Type 5: Checklist Comments

**Purpose:** Mark steps in a sequence that must not be skipped or reordered.

**Python scope:** Numbered inline `#` comments within a multi-step procedure.

**Quality markers:**
- Steps are numbered
- Order dependency is explicit
- Consequences of skipping/reordering are noted where non-obvious

**Example:**
```python
def deploy_schema_migration(migration: Migration) -> None:
    # 1. Acquire advisory lock to prevent concurrent migrations
    lock = acquire_migration_lock(timeout=30)

    # 2. Validate migration hasn't already been applied (idempotency check)
    if is_already_applied(migration.version):
        release_lock(lock)
        return

    # 3. Apply migration in a transaction
    # MUST be after lock acquisition - concurrent apply causes partial schema
    with db.transaction():
        migration.apply()

    # 4. Record migration version BEFORE releasing lock
    # If we release first, another process could re-apply
    record_applied(migration.version)

    # 5. Release lock last
    release_lock(lock)
```

---

## Type 6: Guide Comments

**Purpose:** Help readers navigate long files by marking logical sections.

**Python scope:** `#` section dividers in long modules or complex functions.

**Quality markers:**
- Consistent formatting throughout file
- Matches actual code sections (not outdated)
- Used only when file is long enough to warrant navigation (>100 lines typically)

**Example:**
```python
# --- Configuration ---

DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
BATCH_SIZE = 100

# --- Data Models ---

@dataclass
class Task:
    id: str
    status: TaskStatus
    created_at: datetime

# --- Repository Layer ---

class TaskRepository:
    ...

# --- Service Layer ---

class TaskService:
    ...
```

---

## Type 7: Trivial Comments (NEGATIVE)

**Purpose:** None. Restates what the code already says.

**Detection heuristics:**
- Comment is a direct English translation of the code
- Removing the comment loses zero information
- Comment uses the same words as the code identifiers

**Examples to delete:**
```python
# Initialize the counter
counter = 0

# Get the user
user = get_user(user_id)

# Return the result
return result

# Loop through items
for item in items:

# Check if valid
if is_valid(data):
```

**Fix:** Delete. If the code needs explanation, rename variables or extract functions instead.

---

## Type 8: Debt Comments (NEGATIVE)

**Purpose:** Mark known issues. Not inherently bad, but problematic when they accumulate.

**Detection heuristics:**
- Contains `TODO`, `FIXME`, `HACK`, `XXX`, `WORKAROUND`
- References a ticket number (good) or is vague (bad)
- Has been in codebase for >6 months without resolution

**Examples:**
```python
# TODO: This should use batch processing for performance  (vague, no owner)
# FIXME: Race condition when multiple workers process same job  (critical, no ticket)
# HACK: Workaround for upstream bug in requests 2.28  (may be resolved by now)
# TODO(alice): Migrate to v2 API before Q3 deprecation [PROJ-1234]  (good: owner + ticket)
```

**Fix strategies:**
- If actionable: Create issue/ticket, add reference to comment, set deadline
- If vague: Clarify the problem and required fix, or delete if no longer relevant
- If stale (>6 months): Investigate if still relevant. Delete or resolve

---

## Type 9: Backup Comments (NEGATIVE)

**Purpose:** None. Preserves old code "just in case."

**Detection heuristics:**
- Commented-out code blocks (not example code in docstrings)
- `# old version:`, `# was:`, `# previously:`
- Entire functions or class methods commented out

**Examples to delete:**
```python
# def process_v1(data):
#     return data.strip().lower()

# result = expensive_computation(data)
# if result > threshold:
#     notify_admin(result)
```

**Fix:** Delete unconditionally. Git history preserves all previous versions. If the code might be needed again, the commit message or a type 8 (debt) comment with a ticket reference is the right way to track it.

---

## Quick Reference Table

| Type | Name | Python Form | Trigger | Quality Test |
|------|------|-------------|---------|-------------|
| 1 | Function | Docstring | New/missing docstring | Covers purpose, args, returns? |
| 2 | Design | Docstring / `#` | Architecture decision | Explains *why this approach*? |
| 3 | Why | Inline `#` | Non-obvious code | Answers "why?", not "what?"? |
| 4 | Teacher | Inline `#` | Domain/algorithm concept | Teaches something new? |
| 5 | Checklist | Numbered `#` | Multi-step procedure | Steps numbered, order enforced? |
| 6 | Guide | Section `#` | Long file (>100 LOC) | Matches actual sections? |
| 7 | Trivial | Any | Restates code | **DELETE** |
| 8 | Debt | `TODO`/`FIXME` | Known issue | Has ticket + owner? |
| 9 | Backup | Commented code | Old code preserved | **DELETE** (git has history) |
