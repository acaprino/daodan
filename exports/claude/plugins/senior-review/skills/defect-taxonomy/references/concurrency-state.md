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

# Concurrency & Parallelism Errors + Variable & State Errors

Reference for defect taxonomy categories 1 and 2.

---

## Category 1: Concurrency and Parallelism Errors

### 1.1 Race Conditions / Data Races
- **CWE**: 362
- **Pattern**: Multiple threads access shared data, at least one writes, no synchronization
- **Detection**: ThreadSanitizer (C/C++/Go), Go `-race`, RacerD/Infer (Java), Helgrind
- **Fix**: Mutexes, `synchronized`, atomic operations, thread-safe collections, channels
- **Difficulty**: Hard
- **Signature**: Shared mutable field accessed from multiple goroutines/threads without lock

### 1.2 TOCTOU (Time-of-Check to Time-of-Use)
- **CWE**: 367
- **Pattern**: Check condition, then act on it -- state changes between check and use
- **Detection**: Polyspace, Coverity, Flawfinder
- **Fix**: Atomic ops combining check+use, file descriptors over paths, `O_CREAT|O_EXCL`
- **Difficulty**: Hard
- **Signature**: `if (file.exists()) { file.open() }`, `access()` then `open()`

### 1.3 Deadlocks
- **CWE**: 833
- **Pattern**: Coffman conditions met -- mutual exclusion, hold-and-wait, no preemption, circular wait
- **Detection**: Lock-order analysis, `jstack`, Go deadlock detector, Valgrind DRD
- **Fix**: Consistent global lock ordering, `tryLock` with timeouts, `std::scoped_lock`, lock-free structures
- **Difficulty**: Medium-Hard
- **Signature**: Two+ locks acquired in different orders across code paths

### 1.4 Livelocks / Starvation
- **CWE**: 400 (related)
- **Pattern**: Threads actively executing but making no progress; low-priority threads never scheduled
- **Detection**: Thread profiling, watchdog timers, CPU profiling showing spinning
- **Fix**: Randomized backoff, fair locks (`ReentrantLock(true)`), priority inheritance protocols
- **Difficulty**: Very Hard
- **Signature**: High CPU with no throughput, repeated retry loops without progress

### 1.5 Atomicity Violations
- **CWE**: 362 (subtype)
- **Pattern**: Check-then-act sequence assumed atomic but interleaved by other threads
- **Detection**: AVIO, CTrigger, CodeGuru Reviewer
- **Fix**: Single atomic API calls, `synchronized` blocks covering full operation, CAS loops
- **Difficulty**: Hard
- **Signature**: `if (map.containsKey(k)) { map.get(k) }` -- use `computeIfAbsent`

### 1.6 Thread-Safety Violations
- **CWE**: 567
- **Pattern**: Non-thread-safe class (HashMap, ArrayList, SimpleDateFormat) used in concurrent context
- **Detection**: SpotBugs, Clang Thread Safety Analysis, `@ThreadSafe` annotations
- **Fix**: `ConcurrentHashMap`, `Collections.synchronizedList()`, `ThreadLocal`, immutable types
- **Difficulty**: Medium-High
- **Signature**: Shared `HashMap`/`ArrayList`/`StringBuilder` without synchronization

### 1.7 Incorrect Synchronization
- **CWE**: 820, 662, 667
- **Pattern**: Wrong lock scope, wrong lock identity, broken double-checked locking (CWE-609)
- **Detection**: Coverity, Infer, SpotBugs `IS2_INCONSISTENT_SYNC`
- **Fix**: Same lock for same data, `@GuardedBy` annotations, channels/actors over shared state
- **Difficulty**: Medium
- **Signature**: Lock on local variable, lock on mutable field, DCL without `volatile`

### 1.8 Volatile / Memory Ordering Errors
- **CWE**: 667
- **Pattern**: C++ `volatile` != atomicity, wrong `memory_order` on atomics, JVM field visibility
- **Detection**: CppMem, CDSChecker, LLVM ThreadSanitizer
- **Fix**: `std::atomic` with `seq_cst` default, `volatile` keyword in Java for visibility
- **Difficulty**: Very Hard
- **Signature**: `volatile int` in C++ used for synchronization, relaxed ordering on flag variables

### 1.9 Async/Await Anti-Patterns
- **CWE**: N/A (emerging)
- **Pattern**: Unhandled promise rejections, missing `await`, `async void` fire-and-forget
- **Detection**: ESLint `no-floating-promises`, `@typescript-eslint/no-misused-promises`, asyncio debug mode
- **Fix**: Always `await` or `.catch()`, `run_in_executor` for blocking, `TaskGroup` for structured concurrency
- **Difficulty**: Medium
- **Signature**: `async function f() { doAsync(); }` -- missing `await`

### 1.10 Actor Model Errors
- **CWE**: N/A
- **Pattern**: Mailbox overflow, supervision restart storms, blocking calls inside actors
- **Detection**: Dead letter monitoring, actor metrics, mailbox size alerts
- **Fix**: Back-pressure (`BoundedMailbox`), circuit-break supervision, dedicated dispatchers for blocking
- **Difficulty**: Medium-High
- **Signature**: Unbounded mailbox with slow consumer, `Thread.sleep` in actor receive

---

## Category 2: Variable and State Errors

### 2.1 Stale Variables / Stale Reads
- **CWE**: N/A
- **Pattern**: React stale closures capturing old state, Python late-binding closures in loops
- **Detection**: ESLint `react-hooks/exhaustive-deps`, manual closure analysis
- **Fix**: Functional updates `setState(prev => ...)`, `useRef` for mutable current, default argument binding `lambda x=x:`
- **Difficulty**: Hard
- **Signature**: `useEffect(() => { use(count) }, [])` -- missing `count` in deps

### 2.2 Uninitialized Variables
- **CWE**: 457
- **Pattern**: Reading variable before assignment -- junk data in C/C++, undefined behavior
- **Detection**: `-Wuninitialized`, `-Wmaybe-uninitialized`, Coverity, MSan, Clang-Tidy
- **Fix**: Initialize at declaration, use constructors, enable compiler warnings as errors
- **Difficulty**: Low-Medium
- **Signature**: `int x; if (cond) x = 5; return x;`

### 2.3 Variable Shadowing
- **CWE**: N/A
- **Pattern**: Inner scope variable hides outer scope variable with same name
- **Detection**: `-Wshadow` (GCC/Clang), ESLint `no-shadow`, `go vet` (`:=` shadowing)
- **Fix**: Unique names, avoid `:=` in inner scopes in Go, enable lint rules
- **Difficulty**: Low
- **Signature**: `err := ...; if cond { err := other() }` -- outer `err` unchanged

### 2.4 Null / Undefined References
- **CWE**: 476
- **Pattern**: Dereferencing null/nil/None/undefined -- "billion-dollar mistake"
- **Detection**: Kotlin null safety, TypeScript `strictNullChecks`, NullAway, Infer
- **Fix**: `Optional` types, `?.` optional chaining, `??` nullish coalescing, non-nullable by default
- **Difficulty**: Medium
- **Signature**: `user.getAddress().getCity()` -- any link can be null

### 2.5 Off-by-One Indexing
- **CWE**: 193
- **Pattern**: Loop boundary errors, fence-post problems, array index +/-1
- **Detection**: Boundary-value unit tests, array bounds sanitizers
- **Fix**: Range-based iteration (`for...of`, `for item in list`), half-open intervals `[start, end)`, boundary-specific tests
- **Difficulty**: Medium
- **Signature**: `for (i = 0; i <= arr.length; i++)` -- should be `<`

### 2.6 Incorrect Variable Scope
- **CWE**: N/A
- **Pattern**: JS `var` hoisting, Python loop variable leaking, Go `:=` creating new var vs assigning
- **Detection**: ESLint `no-var`, pylint `redefined-outer-name`
- **Fix**: `let`/`const` over `var`, list comprehensions, explicit scope management
- **Difficulty**: Low-Medium
- **Signature**: `for (var i ...) { setTimeout(() => use(i)) }` -- all callbacks see final `i`

### 2.7 Mutable State Leakage
- **CWE**: N/A
- **Pattern**: Returning mutable internal state, Python mutable default arguments, aliased collections
- **Detection**: SpotBugs `EI_EXPOSE_REP`, `EI_EXPOSE_REP2`
- **Fix**: Defensive copies, `Collections.unmodifiableList()`, `tuple()` over `list`, `None` sentinel for defaults
- **Difficulty**: Medium
- **Signature**: `def __init__(self, items=[]):` -- shared default list across instances

### 2.8 Per-Instance State Divergence (Phantom Singleton)
- **CWE**: N/A
- **Pattern**: Stateful hook/composable/mixin instantiated by N components; each instance owns a private copy of state the design assumes is shared, so a write in one instance never reaches the others
- **Detection**: Grep call sites of custom hooks that own `useState`/`useRef` (or framework equivalents); flag any with more than one instantiating component whose state models an app-global fact (update availability, auth/session, connectivity, feature flags). Runtime fingerprint: mount effects logged once per instance, and actions that succeed in the logs with no visible UI change
- **Fix**: Lift the state into a shared store (module-level store, context, Zustand/Redux/Jotai slice); keep non-serializable handles in a module-level ref; run mount-time checks once through the store instead of per instance
- **Difficulty**: Medium
- **Signature**: `useThing()` with internal `useState` called from both ComponentA and ComponentB; A's handler updates A's copy while B renders its own never-updated copy
