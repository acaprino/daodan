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

# Memory Management + Error Handling & Resources + Performance

Reference for defect taxonomy categories 5, 7, and 13.

---

## Category 5: Memory Management Errors

### 5.1 Memory Leaks
- **CWE**: 401
- **Pattern**: `malloc` without `free`, classloader leaks (JVM), JS event listener / closure leaks, Go goroutine leaks
- **Detection**: Valgrind (Memcheck), ASan, heap profilers (VisualVM, Chrome DevTools), `pprof`
- **Fix**: RAII / smart pointers (`unique_ptr`, `shared_ptr`), `removeEventListener`, `WeakReference`, context cancellation
- **Difficulty**: Medium-Hard
- **Signature**: Growing RSS over time, OOM after hours/days of operation

### 5.2 Buffer Overflow / Underflow
- **CWE**: 119 (general), 787 (out-of-bounds write), 125 (out-of-bounds read)
- **Pattern**: Stack-based or heap-based buffer overrun -- #1 cause of security vulns in C/C++
- **Detection**: ASan, Valgrind, Coverity, fuzzing (AFL, libFuzzer), `-fstack-protector`
- **Fix**: Bounds-checked functions (`strncpy`, `snprintf`), `std::vector`/`std::string`, stack canaries
- **Difficulty**: Medium
- **Signature**: `strcpy(buf, input)`, `memcpy` without size validation, array indexing without bounds check

### 5.3 Stack Overflow
- **CWE**: 674
- **Pattern**: Uncontrolled recursion, adversary-controlled nested data (JSON, XML)
- **Detection**: Recursion depth monitoring, stack size profiling
- **Fix**: Depth limits, iterative conversion with explicit stack, trampolining, tail-call optimization
- **Difficulty**: Medium
- **Signature**: Recursive function without base case guard on depth, parsing deeply nested input

### 5.4 Use-After-Free
- **CWE**: 416 (Top 25 #7)
- **Pattern**: Dereferencing pointer to freed memory -- arbitrary code execution, data corruption
- **Detection**: ASan, Valgrind, fuzzing, MiraclePtr (Chrome)
- **Fix**: Nullify after free, smart pointers, ownership semantics (Rust), arena allocation
- **Difficulty**: Hard
- **Signature**: `free(ptr); ... ptr->field = x;`, returning pointer to freed local

### 5.5 Double Free
- **CWE**: 415
- **Pattern**: Freeing same allocation twice -- heap corruption, exploitable
- **Detection**: ASan, Valgrind, heap debugging (`MALLOC_CHECK_`)
- **Fix**: Set pointer to NULL after free, smart pointers, RAII, single-owner semantics
- **Difficulty**: Medium-Hard
- **Signature**: Error path frees, then cleanup path frees again

### 5.6 Dangling Pointers / References
- **CWE**: 825
- **Pattern**: Returning reference to local variable, iterator invalidation after container mutation
- **Detection**: ASan, `-Wreturn-local-addr`, Rust borrow checker (compile-time), lifetime analysis
- **Fix**: Return by value, `std::move`, stable iterators, Rust lifetimes
- **Difficulty**: Hard
- **Signature**: `return &localVar;`, `vec.push_back()` then using old iterator

### 5.7 Memory Fragmentation
- **CWE**: N/A
- **Pattern**: Varied-size alloc/dealloc cycles -- free memory exists but not contiguous
- **Detection**: Memory allocator stats, fragmentation metrics, long-running system monitoring
- **Fix**: Memory pools, slab allocators, arena allocators, fixed-size allocation classes
- **Difficulty**: Hard
- **Signature**: Allocation failures despite free memory, embedded/real-time systems degradation

### 5.8 GC Pressure / Object Churn
- **CWE**: N/A
- **Pattern**: Rapid allocation of short-lived objects, autoboxing, temporary collections
- **Detection**: GC logs (`-Xlog:gc*`), allocation profilers (JFR, async-profiler), GC pause metrics
- **Fix**: Object pooling, avoid autoboxing (`IntStream` not `Stream<Integer>`), pre-size collections, reuse buffers
- **Difficulty**: Medium
- **Signature**: High minor GC frequency, `Integer.valueOf()` in tight loops

---

## Category 7: Error Handling and Resource Management

### 7.1 Swallowed / Empty Catch Blocks
- **CWE**: 390
- **Pattern**: `catch (Exception e) { }` -- silently discards errors, masks bugs
- **Detection**: ESLint `no-empty`, SonarQube, PMD `EmptyCatchBlock`, Clippy
- **Fix**: Log at minimum, rethrow if unrecoverable, add explicit comment if intentionally swallowed
- **Difficulty**: Low

### 7.2 Overly Broad Exception Catching
- **CWE**: 396
- **Pattern**: `catch (Exception e)`, `catch (Throwable t)`, bare `except:` in Python
- **Detection**: SonarQube, PMD, pylint `bare-except`, Clippy `match` exhaustiveness
- **Fix**: Catch specific types, multi-catch syntax, let unexpected errors propagate
- **Difficulty**: Low

### 7.3 Resource Leaks
- **CWE**: 404
- **Pattern**: Unclosed streams, DB connections, file handles, sockets -- one of most common production outage causes
- **Detection**: SpotBugs `OBL_UNSATISFIED_OBLIGATION`, Coverity `RESOURCE_LEAK`, ESLint
- **Fix**: `try-with-resources` (Java), `with` statement (Python), `defer` (Go), RAII/`Drop` (Rust/C++)
- **Difficulty**: Medium
- **Signature**: `new FileInputStream(f)` not in try-with-resources, `open()` without corresponding `close()`

### 7.4 Missing Cleanup Patterns
- **CWE**: 404, 459
- **Pattern**: `AutoCloseable` not used in try-with-resources, missing `defer`, no `finally` block
- **Detection**: SpotBugs, Coverity, IDE inspections
- **Fix**: Wrap all closeable resources in language-idiomatic cleanup pattern
- **Difficulty**: Low-Medium

### 7.5 Unchecked Error Codes
- **CWE**: 252
- **Pattern**: Go `err` ignored (`val, _ := f()`), C return codes unchecked, `Result` discarded
- **Detection**: `errcheck`, `staticcheck` (Go), SpotBugs `RV_RETURN_VALUE_IGNORED`, `#[must_use]` (Rust)
- **Fix**: Check every error, use `must_use` attributes, linter enforcement
- **Difficulty**: Low-Medium
- **Signature**: `f()` in Go without `if err != nil`, ignoring `fclose()` return

### 7.6 Incorrect Error Propagation
- **CWE**: 755
- **Pattern**: Losing stack traces when wrapping errors, swallowing cause chain
- **Detection**: Code review, logging analysis (missing root cause in error messages)
- **Fix**: Chain causes (`new Exception("msg", cause)`), `%w` not `%v` in Go, `raise X from original` in Python
- **Difficulty**: Medium
- **Signature**: `catch (e) { throw new CustomException(e.getMessage()) }` -- cause lost

### 7.7 Panic / Abort Misuse
- **CWE**: 382, 617
- **Pattern**: Go `panic()` in libraries (should return error), Rust `.unwrap()` in production code
- **Detection**: Clippy `unwrap_used`/`expect_used`, `go vet`, custom lint for `panic` in library packages
- **Fix**: Return errors, `?` operator (Rust), `log.Fatal` only in `main()`, `expect()` with context message
- **Difficulty**: Low

---

## Category 13: Performance and Resource Errors

### 13.1 Algorithmic Complexity Bugs
- **CWE**: N/A
- **Pattern**: Accidental O(n^2) -- nested iteration, `String` concatenation in loops, `List.contains()` in loops
- **Detection**: CPU profiling, benchmark tests, Big-O review
- **Fix**: `HashMap`/`HashSet` for lookups, `StringBuilder`/`join()`, streaming/pagination
- **Difficulty**: Easy
- **Signature**: `for x in list: if x in other_list:` where `other_list` is large

### 13.2 Unbounded Collection Growth
- **CWE**: N/A
- **Pattern**: Maps/lists grow without eviction -- slow memory leak over days/weeks
- **Detection**: Heap dumps, memory trend monitoring, collection size metrics
- **Fix**: Bounded caches (LRU via `LinkedHashMap`, Guava Cache, `@lru_cache(maxsize=)`), TTL-based expiry
- **Difficulty**: Medium
- **Signature**: `static Map<K,V> cache = new HashMap<>()` without size limits

### 13.3 Thread Pool Exhaustion
- **CWE**: N/A
- **Pattern**: All threads blocked on slow I/O, downstream timeout cascading
- **Detection**: Thread dumps (`jstack`), pool utilization metrics, active thread count alerts
- **Fix**: Timeouts on all blocking calls, separate pools per concern (bulkhead pattern), async I/O
- **Difficulty**: Medium
- **Signature**: Default `Executors.newFixedThreadPool()` shared across features, no call timeouts

### 13.4 Connection Pool Starvation
- **CWE**: N/A
- **Pattern**: All DB/HTTP connections checked out, new requests queue or fail
- **Detection**: Pool metrics (HikariCP `activeConnections`), leak detection (`leakDetectionThreshold`)
- **Fix**: `try-with-resources` for connections, `maxLifetime` settings, connection leak detection enabled
- **Difficulty**: Easy
- **Signature**: `getConnection()` without corresponding `close()` in finally/try-with-resources

### 13.5 Excessive Logging in Hot Paths
- **CWE**: N/A
- **Pattern**: Even disabled log levels incur formatting/allocation cost in tight loops
- **Detection**: CPU profiling showing time in logging framework, allocation profiling
- **Fix**: Guarded logging (`if (log.isDebugEnabled())`), parameterized messages (`log.debug("x={}", x)`), sampling
- **Difficulty**: Easy
- **Signature**: `log.debug("Processing: " + obj.toString())` in per-request loop

### 13.6 Blocking in Async / Reactive Contexts
- **CWE**: N/A
- **Pattern**: JDBC calls in WebFlux, `Thread.sleep` on event loop, synchronous I/O in Vert.x
- **Detection**: BlockHound (Java), Node.js `--trace-sync-io`, Vert.x blocked thread checker
- **Fix**: `subscribeOn(Schedulers.boundedElastic())`, R2DBC, `setImmediate`, never `.block()` on event loop
- **Difficulty**: Medium
- **Signature**: `repository.findAll()` (JDBC) inside `Mono.map()`

### 13.7 GC Thrashing
- **CWE**: N/A
- **Pattern**: Autoboxing primitives, creating temporary collections, excessive finalization
- **Detection**: GC logs, JFR allocation profiling, GC pause duration metrics
- **Fix**: Object pooling, primitive-specialized collections (Eclipse Collections, fastutil), pre-sized collections, avoid finalizers
- **Difficulty**: Medium
- **Signature**: `Map<Integer, Integer>` with millions of entries (autoboxing), `new ArrayList<>()` per iteration
