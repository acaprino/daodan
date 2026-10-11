---
name: kotlin-specialist
description: >
  Idiomatic patterns for concurrent, shared-code, and UI-layer work.
  TRIGGER WHEN: building, writing, or reviewing Kotlin code using coroutines / Flow / StateFlow / SharedFlow / suspend functions, Kotlin Multiplatform (KMP) and expect/actual, Compose composables / ViewModels, Ktor routing with JWT auth and Exposed, sealed-class state modeling, scope functions, or DSL builders.
  DO NOT TRIGGER WHEN: libGDX game work (use libgdx-development), or Android Java without Kotlin.
---

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

<!--
Portions of this file are derived from Jeffallan/claude-skills
(https://github.com/Jeffallan/claude-skills), MIT License.
Snapshot 2026-05-12.
-->

# Kotlin Specialist

Senior Kotlin developer with deep expertise in coroutines, Kotlin Multiplatform (KMP), and modern Kotlin 1.9+ patterns.

## Core Workflow

1. **Analyze architecture** - Identify platform targets, coroutine patterns, shared code strategy
2. **Design models** - Create sealed classes, data classes, type hierarchies
3. **Implement** - Write idiomatic Kotlin with coroutines, Flow, extension functions
   - *Checkpoint:* Verify coroutine cancellation is handled (parent scope cancelled on teardown) and null safety is enforced before proceeding
4. **Validate** - Run `detekt` and `ktlint`; verify coroutine cancellation handling and null safety
   - *If detekt/ktlint fails:* Fix all reported issues and re-run both tools before proceeding to step 5
5. **Optimize** - Apply inline classes, sequence operations, compilation strategies
6. **Test** - Write multiplatform tests with coroutine test support (`runTest`, Turbine)

## Reference Guide

Load detailed guidance based on context:

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Coroutines & Flow | `references/coroutines-flow.md` | Async operations, structured concurrency, Flow API |
| Multiplatform | `references/multiplatform-kmp.md` | Shared code, expect/actual, platform setup |
| Android & Compose | `references/android-compose.md` | Jetpack Compose, ViewModel, Material3, navigation |
| Ktor Server | `references/ktor-server.md` | Routing, plugins, authentication, serialization |
| DSL & Idioms | `references/dsl-idioms.md` | Type-safe builders, scope functions, delegates |

## Key Patterns

### Sealed Classes for State Modeling

```kotlin
sealed class UiState<out T> {
    data object Loading : UiState<Nothing>()
    data class Success<T>(val data: T) : UiState<T>()
    data class Error(val message: String, val cause: Throwable? = null) : UiState<Nothing>()
}

// Consume exhaustively — compiler enforces all branches
fun render(state: UiState<User>) = when (state) {
    is UiState.Loading  -> showSpinner()
    is UiState.Success  -> showUser(state.data)
    is UiState.Error    -> showError(state.message)
}
```

### Coroutines & Flow

```kotlin
// Use structured concurrency — never GlobalScope
class UserRepository(private val api: UserApi, private val scope: CoroutineScope) {

    fun userUpdates(id: String): Flow<UiState<User>> = flow {
        emit(UiState.Loading)
        try {
            emit(UiState.Success(api.fetchUser(id)))
        } catch (e: IOException) {
            emit(UiState.Error("Network error", e))
        }
    }.flowOn(Dispatchers.IO)

    private val _user = MutableStateFlow<UiState<User>>(UiState.Loading)
    val user: StateFlow<UiState<User>> = _user.asStateFlow()
}

// Anti-pattern — blocks the calling thread; avoid in production
// runBlocking { api.fetchUser(id) }
```

### Null Safety

```kotlin
// Prefer safe calls and elvis operator
val displayName = user?.profile?.name ?: "Anonymous"

// Use let to scope nullable operations
user?.email?.let { email -> sendNotification(email) }

// !! only when the null case is a true contract violation and documented
val config = requireNotNull(System.getenv("APP_CONFIG")) { "APP_CONFIG must be set" }
```

### Scope Functions

```kotlin
// apply — configure an object, returns receiver
val request = HttpRequest().apply {
    url = "https://api.example.com/users"
    headers["Authorization"] = "Bearer $token"
}

// let — transform nullable / introduce a local scope
val length = name?.let { it.trim().length } ?: 0

// also — side-effects without changing the chain
val user = createUser(form).also { logger.info("Created user ${it.id}") }
```

## Constraints

### MUST DO
- Use null safety (`?`, `?.`, `?:`, `!!` only when contract guarantees non-null)
- Prefer `sealed class` for state modeling
- Use `suspend` functions for async operations
- Leverage type inference but be explicit when needed
- Use `Flow` for reactive streams
- Apply scope functions appropriately (`let`, `run`, `apply`, `also`, `with`)
- Document public APIs with KDoc
- Use explicit API mode for libraries
- Run `detekt` and `ktlint` before committing
- Verify coroutine cancellation is handled (cancel parent scope on teardown)

### MUST NOT DO
- Block coroutines with `runBlocking` in production code
- Use `!!` without documented justification
- Mix platform-specific code in common modules
- Skip null safety checks
- Use `GlobalScope.launch` (use structured concurrency)
- Ignore coroutine cancellation
- Create memory leaks with coroutine scopes

## Output Templates

When implementing Kotlin features, provide:
1. Data models (sealed classes, data classes)
2. Implementation file (extension functions, suspend functions)
3. Test file with coroutine test support
4. Brief explanation of Kotlin-specific patterns used

## Knowledge Reference

Kotlin 1.9+, Coroutines, Flow API, StateFlow/SharedFlow, Kotlin Multiplatform, Jetpack Compose, Ktor, Arrow.kt, kotlinx.serialization, Detekt, ktlint, Gradle Kotlin DSL, JUnit 5, MockK, Turbine
