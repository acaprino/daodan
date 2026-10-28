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

<!--
Portions of this file are derived from Jeffallan/claude-skills
(https://github.com/Jeffallan/claude-skills), MIT License.
Snapshot 2026-05-12.
-->

# Android & Jetpack Compose

## Compose Basics

```kotlin
import androidx.compose.runtime.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun UserProfile(user: User, onEdit: () -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = user.name,
                style = MaterialTheme.typography.headlineMedium
            )
            Text(
                text = user.email,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(modifier = Modifier.height(8.dp))
            Button(onClick = onEdit) {
                Text("Edit Profile")
            }
        }
    }
}
```

## State Management

```kotlin
// ViewModel with StateFlow
class UserViewModel(
    private val repository: UserRepository
) : ViewModel() {
    private val _uiState = MutableStateFlow(UserUiState())
    val uiState: StateFlow<UserUiState> = _uiState.asStateFlow()

    fun loadUser(userId: String) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            try {
                val user = repository.getUser(userId)
                _uiState.update { it.copy(user = user, isLoading = false) }
            } catch (e: Exception) {
                _uiState.update { it.copy(error = e.message, isLoading = false) }
            }
        }
    }
}

data class UserUiState(
    val user: User? = null,
    val isLoading: Boolean = false,
    val error: String? = null
)

// Composable using ViewModel
@Composable
fun UserScreen(
    viewModel: UserViewModel = hiltViewModel(),
    userId: String
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    LaunchedEffect(userId) {
        viewModel.loadUser(userId)
    }

    when {
        uiState.isLoading -> LoadingIndicator()
        uiState.error != null -> ErrorMessage(uiState.error!!)
        uiState.user != null -> UserProfile(uiState.user!!)
    }
}
```

## Material 3 Theme

```kotlin
@Composable
fun AppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) {
        darkColorScheme(
            primary = Purple80,
            secondary = PurpleGrey80,
            tertiary = Pink80
        )
    } else {
        lightColorScheme(
            primary = Purple40,
            secondary = PurpleGrey40,
            tertiary = Pink40
        )
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
```

## Navigation

```kotlin
import androidx.navigation.compose.*

@Composable
fun AppNavigation() {
    val navController = rememberNavController()

    NavHost(
        navController = navController,
        startDestination = "home"
    ) {
        composable("home") {
            HomeScreen(
                onNavigateToProfile = { userId ->
                    navController.navigate("profile/$userId")
                }
            )
        }

        composable(
            route = "profile/{userId}",
            arguments = listOf(navArgument("userId") { type = NavType.StringType })
        ) { backStackEntry ->
            val userId = backStackEntry.arguments?.getString("userId")
            ProfileScreen(
                userId = userId ?: "",
                onBack = { navController.popBackStack() }
            )
        }

        composable("settings") {
            SettingsScreen()
        }
    }
}
```

## LazyColumn (Lists)

```kotlin
@Composable
fun UserList(
    users: List<User>,
    onUserClick: (User) -> Unit
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(users, key = { it.id }) { user ->
            UserCard(
                user = user,
                onClick = { onUserClick(user) }
            )
        }
    }
}

// Pagination with LazyColumn
@Composable
fun PaginatedList(viewModel: ListViewModel = hiltViewModel()) {
    val items by viewModel.items.collectAsStateWithLifecycle()
    val isLoading by viewModel.isLoading.collectAsStateWithLifecycle()

    LazyColumn {
        items(items, key = { it.id }) { item ->
            ItemCard(item)
        }

        if (isLoading) {
            item {
                CircularProgressIndicator(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp)
                )
            }
        }

        // Load more trigger
        item {
            LaunchedEffect(Unit) {
                viewModel.loadMore()
            }
        }
    }
}
```

## Side Effects

```kotlin
@Composable
fun UserScreen(userId: String) {
    // Run once when userId changes
    LaunchedEffect(userId) {
        loadUser(userId)
    }

    // Run on every recomposition
    SideEffect {
        analyticsService.trackScreen("UserScreen")
    }

    // Cleanup when leaving composition
    DisposableEffect(Unit) {
        val listener = setupListener()
        onDispose {
            listener.cleanup()
        }
    }

    // Remember value across recompositions
    val scrollState = rememberScrollState()

    // Derived state
    val isScrolled by remember {
        derivedStateOf { scrollState.value > 0 }
    }
}
```

## Dependency Injection (Hilt)

```kotlin
// Application class
@HiltAndroidApp
class MyApplication : Application()

// Module
@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    @Provides
    @Singleton
    fun provideApiService(): ApiService = ApiServiceImpl()

    @Provides
    @Singleton
    fun provideUserRepository(api: ApiService): UserRepository =
        UserRepositoryImpl(api)
}

// ViewModel with injection
@HiltViewModel
class UserViewModel @Inject constructor(
    private val repository: UserRepository,
    private val savedStateHandle: SavedStateHandle
) : ViewModel() {
    private val userId: String = savedStateHandle["userId"] ?: ""

    val user: StateFlow<User?> = repository
        .getUserFlow(userId)
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = null
        )
}

// Activity
@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            AppTheme {
                AppNavigation()
            }
        }
    }
}
```

## Remember & State

```kotlin
@Composable
fun SearchScreen() {
    // State hoisting
    var query by remember { mutableStateOf("") }
    var results by remember { mutableStateOf<List<Result>>(emptyList()) }

    Column {
        SearchBar(
            query = query,
            onQueryChange = { query = it },
            onSearch = {
                // Trigger search
            }
        )

        ResultsList(results)
    }
}

// Remember with keys
@Composable
fun UserDetail(userId: String) {
    val user = remember(userId) {
        loadUser(userId)
    }

    // rememberSaveable survives process death
    var expanded by rememberSaveable { mutableStateOf(false) }
}
```

## Animation

```kotlin
import androidx.compose.animation.*
import androidx.compose.animation.core.*

@Composable
fun AnimatedContent() {
    var visible by remember { mutableStateOf(false) }

    // Simple fade
    AnimatedVisibility(visible) {
        Text("Hello World")
    }

    // Custom animation
    val alpha by animateFloatAsState(
        targetValue = if (visible) 1f else 0f,
        animationSpec = tween(durationMillis = 300)
    )

    // Animated content
    AnimatedContent(
        targetState = selectedTab,
        transitionSpec = {
            fadeIn() + slideInVertically() togetherWith
                    fadeOut() + slideOutVertically()
        }
    ) { tab ->
        when (tab) {
            0 -> HomeContent()
            1 -> ProfileContent()
        }
    }
}
```

## Performance Optimization

```kotlin
// Stability annotations
@Immutable
data class User(val id: String, val name: String)

@Stable
class UserState(private val repository: UserRepository) {
    val users: StateFlow<List<User>> = repository.users
}

// Key for recomposition optimization
@Composable
fun ItemList(items: List<Item>) {
    LazyColumn {
        items(items, key = { it.id }) { item ->
            ItemCard(item)
        }
    }
}

// derivedStateOf for expensive calculations
@Composable
fun FilteredList(items: List<Item>, filter: String) {
    val filtered by remember(items, filter) {
        derivedStateOf {
            items.filter { it.name.contains(filter, ignoreCase = true) }
        }
    }

    LazyColumn {
        items(filtered) { item ->
            ItemCard(item)
        }
    }
}
```

## Quick Reference

| Composable | Purpose |
|------------|---------|
| `remember` | Retain value across recompositions |
| `rememberSaveable` | Survive process death |
| `LaunchedEffect` | Run suspend functions |
| `DisposableEffect` | Cleanup when leaving |
| `SideEffect` | Non-suspend effects |
| `derivedStateOf` | Computed state |
| `collectAsStateWithLifecycle` | Flow to State (lifecycle-aware) |
| `animateFloatAsState` | Animate value changes |
| `LazyColumn` | Scrollable list |
| `Scaffold` | Material 3 layout structure |
| `viewModelScope` | ViewModel coroutine scope |
| `@HiltViewModel` | Hilt dependency injection |
