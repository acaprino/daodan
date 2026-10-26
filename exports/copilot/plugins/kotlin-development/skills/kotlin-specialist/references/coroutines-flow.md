<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

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

<!--
Portions of this file are derived from Jeffallan/claude-skills
(https://github.com/Jeffallan/claude-skills), MIT License.
Snapshot 2026-05-12.
-->

# Coroutines & Flow API

## Structured Concurrency

```kotlin
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*

class UserRepository(
    private val api: ApiService,
    private val scope: CoroutineScope
) {
    // CORRECT: Structured concurrency with supervisor
    suspend fun fetchUsers(): Result<List<User>> = coroutineScope {
        supervisorScope {
            try {
                val users = async { api.getUsers() }
                val profiles = async { api.getProfiles() }
                Result.success(users.await() + profiles.await())
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }

    // WRONG: GlobalScope bypasses structured concurrency
    // fun fetchUsersWrong() = GlobalScope.launch { ... }
}
```

## Coroutine Scopes & Dispatchers

```kotlin
class ViewModel : CoroutineScope {
    override val coroutineContext = SupervisorJob() + Dispatchers.Main

    fun loadData() {
        launch {
            val data = withContext(Dispatchers.IO) {
                // I/O operations on IO dispatcher
                repository.fetchData()
            }
            // Back to Main dispatcher automatically
            updateUI(data)
        }
    }

    fun cleanup() {
        coroutineContext.cancelChildren()
    }
}

// Android ViewModel - use viewModelScope
class AndroidViewModel : ViewModel() {
    fun loadUsers() {
        viewModelScope.launch {
            userRepository.getUsers().collect { users ->
                _uiState.update { it.copy(users = users) }
            }
        }
    }
}
```

## Flow Basics

```kotlin
// Cold flow - starts on collection
fun getUsers(): Flow<List<User>> = flow {
    val users = api.fetchUsers()
    emit(users)
    delay(1000)
    emit(users + api.fetchNewUsers())
}.flowOn(Dispatchers.IO)

// Hot flow - StateFlow (always has value)
class UserStore {
    private val _users = MutableStateFlow<List<User>>(emptyList())
    val users: StateFlow<List<User>> = _users.asStateFlow()

    suspend fun loadUsers() {
        api.getUsers().collect { userList ->
            _users.update { userList }
        }
    }
}

// Hot flow - SharedFlow (events, no initial value)
class EventBus {
    private val _events = MutableSharedFlow<Event>(
        replay = 0,
        extraBufferCapacity = 10,
        onBufferOverflow = BufferOverflow.DROP_OLDEST
    )
    val events: SharedFlow<Event> = _events.asSharedFlow()

    suspend fun emit(event: Event) {
        _events.emit(event)
    }
}
```

## Flow Operators

```kotlin
fun getUsersWithPosts(): Flow<UserWithPosts> = flow {
    userRepository.getUsers()
        .map { user -> UserWithPosts(user, getPosts(user.id)) }
        .filter { it.posts.isNotEmpty() }
        .catch { e -> emit(UserWithPosts.Error(e)) }
        .onEach { delay(100) } // Throttle
        .distinctUntilChanged()
        .collect { emit(it) }
}

// Combining flows
fun getCombinedData(): Flow<UiState> = combine(
    userFlow,
    settingsFlow,
    notificationsFlow
) { user, settings, notifications ->
    UiState(user, settings, notifications)
}

// Flattening flows
fun searchUsers(query: String): Flow<List<User>> =
    queryFlow
        .debounce(300)
        .filter { it.length >= 3 }
        .distinctUntilChanged()
        .flatMapLatest { query ->
            repository.search(query)
        }
```

## Exception Handling

```kotlin
suspend fun loadDataSafely(): Result<Data> =
    supervisorScope {
        try {
            val result = async {
                api.getData()
            }
            Result.success(result.await())
        } catch (e: CancellationException) {
            // Don't catch cancellation - rethrow
            throw e
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

// Flow error handling
fun getDataFlow(): Flow<Data> = flow {
    emit(api.getData())
}.retry(3) { cause ->
    cause is IOException
}.catch { e ->
    emit(Data.Error(e))
}

// Supervisor scope for independent children
suspend fun loadMultiple() = supervisorScope {
    val job1 = launch { task1() } // Failure won't affect job2
    val job2 = launch { task2() }
    joinAll(job1, job2)
}
```

## Cancellation

```kotlin
suspend fun cancellableWork() {
    withTimeout(5000) {
        while (isActive) { // Check for cancellation
            doWork()
            yield() // Cooperation point
        }
    }
}

// Cleanup with finally
suspend fun withCleanup() {
    try {
        longRunningTask()
    } finally {
        withContext(NonCancellable) {
            cleanup() // Always runs even if cancelled
        }
    }
}
```

## Testing Coroutines

```kotlin
import kotlinx.coroutines.test.*

class UserViewModelTest {
    @Test
    fun testLoadUsers() = runTest {
        val viewModel = UserViewModel(fakeRepository)

        viewModel.loadUsers()
        advanceUntilIdle() // Run all pending coroutines

        assertEquals(expectedUsers, viewModel.users.value)
    }

    @Test
    fun testFlow() = runTest {
        val flow = repository.getUsersFlow()
        val results = flow.take(3).toList()

        assertEquals(3, results.size)
    }

    // Testing with Turbine
    @Test
    fun testFlowWithTurbine() = runTest {
        repository.getUsersFlow().test {
            assertEquals(Loading, awaitItem())
            assertEquals(Success(users), awaitItem())
            awaitComplete()
        }
    }
}
```

## Performance Patterns

```kotlin
// Use sequence for lazy evaluation
fun processLargeList(items: List<Item>): List<Result> =
    items.asSequence()
        .filter { it.isValid }
        .map { transform(it) }
        .take(100)
        .toList() // Only processes first 100 valid items

// Channel for producer-consumer
fun produceNumbers() = produce {
    repeat(10) {
        send(it)
        delay(100)
    }
}

// Parallel processing with async
suspend fun processInParallel(items: List<Item>): List<Result> =
    coroutineScope {
        items.map { item ->
            async { process(item) }
        }.awaitAll()
    }
```

## Quick Reference

| Pattern | Use Case |
|---------|----------|
| `launch` | Fire-and-forget coroutine |
| `async/await` | Parallel computation with result |
| `flow { }` | Cold stream of values |
| `StateFlow` | Hot flow with current state |
| `SharedFlow` | Hot flow for events |
| `withContext` | Switch dispatcher |
| `supervisorScope` | Independent child failures |
| `coroutineScope` | All children must succeed |
| `flowOn` | Change flow dispatcher |
| `catch` | Handle flow errors |
| `retry` | Retry on failure |
| `debounce` | Rate limiting |
| `distinctUntilChanged` | Skip duplicates |
| `combine` | Merge multiple flows |
