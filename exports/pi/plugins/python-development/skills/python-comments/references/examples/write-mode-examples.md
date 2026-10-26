<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
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

# Write Mode Examples

Before/after examples for each positive comment type (1-6) and fixes for negative types (7-9).

---

## Type 1: Function Comment

### Before (missing docstring)

```python
def calculate_compound_interest(principal, rate, periods, contributions=0):
    if rate == 0:
        return principal + contributions * periods
    factor = (1 + rate) ** periods
    base = principal * factor
    annuity = contributions * (factor - 1) / rate
    return base + annuity
```

### After

```python
def calculate_compound_interest(
    principal: float,
    rate: float,
    periods: int,
    contributions: float = 0,
) -> float:
    """Calculate future value with compound interest and regular contributions.

    Uses the standard compound interest formula with an optional annuity
    component for periodic contributions.

    Args:
        principal: Initial investment amount. Must be non-negative.
        rate: Interest rate per period as a decimal (e.g., 0.05 for 5%).
            Use 0 for simple accumulation without interest.
        periods: Number of compounding periods. Must be positive.
        contributions: Fixed amount added at the end of each period.

    Returns:
        Total future value including compounded principal and contributions.
    """
    if rate == 0:
        return principal + contributions * periods
    factor = (1 + rate) ** periods
    base = principal * factor
    annuity = contributions * (factor - 1) / rate
    return base + annuity
```

**What makes this correct:** Explains the financial concept (annuity component), documents semantic meaning of `rate` (per-period decimal, not percentage), and notes the edge case (rate=0).

---

## Type 2: Design Comment

### Before (missing rationale)

```python
class EventBus:
    def __init__(self):
        self._handlers = defaultdict(list)
        self._queue = deque()
        self._processing = False

    def emit(self, event_type, data):
        self._queue.append((event_type, data))
        if not self._processing:
            self._drain_queue()
```

### After

```python
class EventBus:
    """In-process event bus with queued dispatch.

    Events are queued rather than dispatched inline to prevent re-entrancy
    issues. If handler A emits event B during processing, B is queued and
    processed after A's handler completes. This avoids stack overflow from
    circular event chains and ensures handlers see consistent state.

    Alternative considered: async dispatch with asyncio.Queue. Rejected
    because most consumers are synchronous and adding async would force
    the entire call chain to be async.
    """

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)
        self._queue: deque[tuple[str, Any]] = deque()
        self._processing: bool = False

    def emit(self, event_type: str, data: Any) -> None:
        """Queue an event for dispatch.

        Args:
            event_type: Event name. Handlers registered for this type
                will be called in registration order.
            data: Arbitrary payload passed to handlers.
        """
        self._queue.append((event_type, data))
        if not self._processing:
            self._drain_queue()
```

**What makes this correct:** Explains the queuing design choice, names the problem it solves (re-entrancy), and documents the rejected alternative.

---

## Type 3: Why Comment

### Before (no explanation for non-obvious code)

```python
def parse_csv_record(line: str) -> list[str]:
    fields = line.split(",")
    if len(fields) > 0 and fields[-1].endswith("\r"):
        fields[-1] = fields[-1][:-1]
    return fields
```

### After

```python
def parse_csv_record(line: str) -> list[str]:
    fields = line.split(",")
    # Strip trailing \r because files transferred from Windows retain CRLF
    # line endings even after Python's universal newline mode strips \n.
    # Without this, the last field silently carries a \r that breaks
    # downstream string comparisons.
    if len(fields) > 0 and fields[-1].endswith("\r"):
        fields[-1] = fields[-1][:-1]
    return fields
```

**What makes this correct:** Explains the *reason* (Windows CRLF transfer issue), the *mechanism* (universal newlines strips \n but not \r), and the *consequence* if removed (broken string comparisons).

---

## Type 4: Teacher Comment

### Before (algorithm without context)

```python
def find_closest_points(points: list[tuple[float, float]], k: int) -> list:
    heap = []
    for x, y in points:
        dist = -(x * x + y * y)
        if len(heap) < k:
            heapq.heappush(heap, (dist, (x, y)))
        elif dist > heap[0][0]:
            heapq.heapreplace(heap, (dist, (x, y)))
    return [p for _, p in heap]
```

### After

```python
def find_closest_points(
    points: list[tuple[float, float]], k: int
) -> list[tuple[float, float]]:
    """Return the k points closest to the origin.

    Uses a max-heap of size k for O(n log k) time, which is more
    efficient than sorting all points (O(n log n)) when k << n.

    Args:
        points: 2D points as (x, y) tuples.
        k: Number of closest points to return. Must be <= len(points).

    Returns:
        The k closest points in arbitrary order.
    """
    # Max-heap trick: Python's heapq is a min-heap, so we negate distances
    # to get max-heap behavior. This lets us efficiently evict the farthest
    # point in our k-sized candidate set.
    heap: list[tuple[float, tuple[float, float]]] = []
    for x, y in points:
        dist = -(x * x + y * y)
        if len(heap) < k:
            heapq.heappush(heap, (dist, (x, y)))
        elif dist > heap[0][0]:
            heapq.heapreplace(heap, (dist, (x, y)))
    return [p for _, p in heap]
```

**What makes this correct:** Teaches the max-heap-via-negation trick that a reader unfamiliar with Python's heapq would not know. The docstring adds complexity context (O(n log k) vs O(n log n)).

---

## Type 5: Checklist Comment

### Before (multi-step process without order markers)

```python
def rotate_api_key(service: str) -> str:
    new_key = generate_api_key()
    store_key(service, new_key, status="pending")
    update_service_config(service, new_key)
    health_check(service)
    mark_key_active(service, new_key)
    revoke_old_keys(service, except_key=new_key)
    return new_key
```

### After

```python
def rotate_api_key(service: str) -> str:
    """Rotate the API key for a service with zero-downtime rollover.

    Args:
        service: Service identifier whose key is being rotated.

    Returns:
        The new active API key.
    """
    # 1. Generate new key (does not affect running service)
    new_key = generate_api_key()

    # 2. Store as "pending" - both old and new keys are valid at this point
    store_key(service, new_key, status="pending")

    # 3. Push new key to service config (service now accepts both keys)
    update_service_config(service, new_key)

    # 4. Health check MUST pass before proceeding - if the service can't
    #    use the new key, we abort and the old key remains active
    health_check(service)

    # 5. Mark new key active only after health check confirms it works
    mark_key_active(service, new_key)

    # 6. Revoke old keys LAST - revoking before step 4-5 would cause outage
    revoke_old_keys(service, except_key=new_key)

    return new_key
```

**What makes this correct:** Numbers each step, explains why ordering matters (steps 4-5 before 6), and notes the consequence of misordering (outage).

---

## Type 6: Guide Comment

### Before (long module without navigation)

```python
import os
import json
from dataclasses import dataclass
from enum import Enum

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

@dataclass
class Task:
    title: str
    priority: Priority
    done: bool = False

class TaskRepository:
    def __init__(self, path: str):
        self._path = path
    def load(self) -> list[Task]: ...
    def save(self, tasks: list[Task]) -> None: ...

class TaskService:
    def __init__(self, repo: TaskRepository):
        self._repo = repo
    def add(self, title: str, priority: Priority) -> Task: ...
    def complete(self, title: str) -> None: ...
    def list_pending(self) -> list[Task]: ...

class TaskCLI:
    def __init__(self, service: TaskService):
        self._service = service
    def run(self, args: list[str]) -> None: ...
```

### After

```python
"""Task management module with CLI interface.

Provides CRUD operations for tasks with file-based persistence
and a command-line interface.
"""

import os
import json
from dataclasses import dataclass
from enum import Enum

# --- Domain Models ---

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

@dataclass
class Task:
    title: str
    priority: Priority
    done: bool = False

# --- Persistence ---

class TaskRepository:
    def __init__(self, path: str):
        self._path = path
    def load(self) -> list[Task]: ...
    def save(self, tasks: list[Task]) -> None: ...

# --- Business Logic ---

class TaskService:
    def __init__(self, repo: TaskRepository):
        self._repo = repo
    def add(self, title: str, priority: Priority) -> Task: ...
    def complete(self, title: str) -> None: ...
    def list_pending(self) -> list[Task]: ...

# --- CLI Interface ---

class TaskCLI:
    def __init__(self, service: TaskService):
        self._service = service
    def run(self, args: list[str]) -> None: ...
```

**What makes this correct:** Consistent `# --- Section ---` format. Sections match the actual code organization. Module docstring added for context.

---

## Fixing Negative Types

### Type 7 Fix: Delete Trivial Comments

```python
# BEFORE
# Initialize the cache
cache = {}

# Get the user from the database
user = db.get_user(user_id)

# Check if user exists
if user is None:
    # Return None
    return None

# AFTER (comments deleted, code is self-explanatory)
cache = {}
user = db.get_user(user_id)
if user is None:
    return None
```

### Type 8 Fix: Resolve or Track Debt

```python
# BEFORE
# TODO: handle edge case
if len(items) > 0:
    process(items)

# AFTER (option A: resolve the debt)
if not items:
    return ProcessResult.empty()
process(items)

# AFTER (option B: track with ticket if can't resolve now)
# TODO(alice): Handle empty items list - currently skips silently [PROJ-892]
if len(items) > 0:
    process(items)
```

### Type 9 Fix: Delete Backup Code

```python
# BEFORE
def process(data):
    # result = old_process(data)
    # if result.status == "error":
    #     result = fallback_process(data)
    return new_process(data)

# AFTER (backup code deleted - git history preserves it)
def process(data):
    return new_process(data)
```
