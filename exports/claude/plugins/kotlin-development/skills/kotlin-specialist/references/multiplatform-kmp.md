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

<!--
Portions of this file are derived from Jeffallan/claude-skills
(https://github.com/Jeffallan/claude-skills), MIT License.
Snapshot 2026-05-12.
-->

# Kotlin Multiplatform (KMP)

## Project Structure

```
project/
├── commonMain/
│   ├── kotlin/
│   │   ├── data/
│   │   │   └── User.kt
│   │   ├── repository/
│   │   │   └── UserRepository.kt
│   │   └── Platform.kt (expect)
│   └── resources/
├── androidMain/
│   └── kotlin/
│       └── Platform.android.kt (actual)
├── iosMain/
│   └── kotlin/
│       └── Platform.ios.kt (actual)
└── jvmMain/
    └── kotlin/
        └── Platform.jvm.kt (actual)
```

## Gradle Configuration

```kotlin
// build.gradle.kts
plugins {
    kotlin("multiplatform") version "1.9.22"
    kotlin("plugin.serialization") version "1.9.22"
}

kotlin {
    // JVM target
    jvm {
        compilations.all {
            kotlinOptions.jvmTarget = "17"
        }
    }

    // Android target
    androidTarget {
        compilations.all {
            kotlinOptions.jvmTarget = "17"
        }
    }

    // iOS targets
    listOf(
        iosX64(),
        iosArm64(),
        iosSimulatorArm64()
    ).forEach { iosTarget ->
        iosTarget.binaries.framework {
            baseName = "shared"
            isStatic = true
        }
    }

    // JS target
    js(IR) {
        browser()
        nodejs()
    }

    sourceSets {
        val commonMain by getting {
            dependencies {
                implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
                implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.2")
                implementation("io.ktor:ktor-client-core:2.3.7")
            }
        }

        val commonTest by getting {
            dependencies {
                implementation(kotlin("test"))
                implementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.7.3")
            }
        }

        val androidMain by getting {
            dependencies {
                implementation("io.ktor:ktor-client-okhttp:2.3.7")
            }
        }

        val iosMain by getting {
            dependencies {
                implementation("io.ktor:ktor-client-darwin:2.3.7")
            }
        }

        val jvmMain by getting {
            dependencies {
                implementation("io.ktor:ktor-client-cio:2.3.7")
            }
        }
    }
}
```

## Expect/Actual Pattern

```kotlin
// commonMain/kotlin/Platform.kt
expect class Platform() {
    val name: String
    fun currentTimeMillis(): Long
}

expect fun getPlatform(): Platform

// androidMain/kotlin/Platform.android.kt
import android.os.Build

actual class Platform {
    actual val name: String = "Android ${Build.VERSION.SDK_INT}"

    actual fun currentTimeMillis(): Long =
        System.currentTimeMillis()
}

actual fun getPlatform(): Platform = Platform()

// iosMain/kotlin/Platform.ios.kt
import platform.UIKit.UIDevice
import platform.Foundation.NSDate

actual class Platform {
    actual val name: String =
        UIDevice.currentDevice.systemName() + " " + UIDevice.currentDevice.systemVersion

    actual fun currentTimeMillis(): Long =
        (NSDate().timeIntervalSince1970 * 1000).toLong()
}

actual fun getPlatform(): Platform = Platform()
```

## Common Code Patterns

```kotlin
// commonMain - Shared business logic
class UserRepository(private val api: ApiService) {
    private val _users = MutableStateFlow<List<User>>(emptyList())
    val users: StateFlow<List<User>> = _users.asStateFlow()

    suspend fun loadUsers() {
        try {
            val result = api.getUsers()
            _users.value = result
        } catch (e: Exception) {
            // Handle error
        }
    }
}

// Shared models
@Serializable
data class User(
    val id: String,
    val name: String,
    val email: String,
    val createdAt: Long
)

// Sealed class for platform-agnostic results
sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val exception: Exception) : Result<Nothing>()
    object Loading : Result<Nothing>()
}
```

## Platform-Specific Implementations

```kotlin
// commonMain
expect class DatabaseDriver()

expect suspend fun DatabaseDriver.query(sql: String): List<Map<String, Any>>

// androidMain
import android.content.Context
import androidx.sqlite.db.SupportSQLiteDatabase

actual class DatabaseDriver(private val context: Context) {
    private val db: SupportSQLiteDatabase = // Initialize Android SQLite
}

actual suspend fun DatabaseDriver.query(sql: String): List<Map<String, Any>> =
    withContext(Dispatchers.IO) {
        // Android-specific query execution
    }

// iosMain
import platform.Foundation.NSFileManager

actual class DatabaseDriver() {
    private val db = // Initialize iOS SQLite
}

actual suspend fun DatabaseDriver.query(sql: String): List<Map<String, Any>> =
    withContext(Dispatchers.Default) {
        // iOS-specific query execution
    }
```

## Ktor Client Multiplatform

```kotlin
// commonMain
class ApiClient {
    private val client = HttpClient {
        install(ContentNegotiation) {
            json(Json {
                prettyPrint = true
                isLenient = true
                ignoreUnknownKeys = true
            })
        }
        install(Logging) {
            level = LogLevel.INFO
        }
    }

    suspend fun getUsers(): List<User> =
        client.get("https://api.example.com/users").body()

    suspend fun createUser(user: User): User =
        client.post("https://api.example.com/users") {
            contentType(ContentType.Application.Json)
            setBody(user)
        }.body()
}
```

## Source Set Hierarchy

```kotlin
// Intermediate source sets for iOS
kotlin {
    sourceSets {
        val commonMain by getting
        val commonTest by getting

        val iosMain by creating {
            dependsOn(commonMain)
        }

        val iosX64Main by getting {
            dependsOn(iosMain)
        }

        val iosArm64Main by getting {
            dependsOn(iosMain)
        }

        val iosSimulatorArm64Main by getting {
            dependsOn(iosMain)
        }
    }
}
```

## Native Interop (iOS)

```kotlin
// iosMain - Calling Objective-C/Swift
import platform.Foundation.NSBundle
import platform.UIKit.UIApplication

fun getAppVersion(): String =
    NSBundle.mainBundle.objectForInfoDictionaryKey("CFBundleShortVersionString") as? String
        ?: "Unknown"

fun openURL(url: String) {
    val nsUrl = NSURL.URLWithString(url)
    UIApplication.sharedApplication.openURL(nsUrl ?: return)
}

// Freezing for thread safety (Kotlin/Native memory model)
class IosViewModel {
    private val scope = MainScope()

    fun loadData() {
        scope.launch {
            val data = api.getData().freeze() // Freeze for iOS
            updateUI(data)
        }
    }
}
```

## Testing Multiplatform Code

```kotlin
// commonTest
class UserRepositoryTest {
    private lateinit var repository: UserRepository

    @BeforeTest
    fun setup() {
        repository = UserRepository(FakeApiService())
    }

    @Test
    fun testLoadUsers() = runTest {
        repository.loadUsers()

        val users = repository.users.value
        assertEquals(2, users.size)
    }
}

// Platform-specific tests
// androidTest
class AndroidUserRepositoryTest {
    @Test
    fun testAndroidSpecific() {
        // Android-only test
    }
}

// iosTest
class IosUserRepositoryTest {
    @Test
    fun testIosSpecific() {
        // iOS-only test
    }
}
```

## Publishing KMP Library

```kotlin
// build.gradle.kts
plugins {
    `maven-publish`
}

publishing {
    publications {
        create<MavenPublication>("kotlinMultiplatform") {
            groupId = "com.example"
            artifactId = "shared"
            version = "1.0.0"
        }
    }

    repositories {
        maven {
            url = uri("https://maven.pkg.github.com/user/repo")
            credentials {
                username = System.getenv("GITHUB_ACTOR")
                password = System.getenv("GITHUB_TOKEN")
            }
        }
    }
}
```

## Quick Reference

| Pattern | Purpose |
|---------|---------|
| `expect class` | Declare platform-specific type in common |
| `actual class` | Implement platform-specific type |
| `commonMain` | Shared code across all platforms |
| `androidMain` | Android-specific implementations |
| `iosMain` | iOS-specific implementations (all targets) |
| `jvmMain` | JVM/Desktop-specific code |
| `jsMain` | JavaScript-specific code |
| `*Test` | Platform-specific tests |
| `dependsOn` | Source set hierarchy |
| `.freeze()` | iOS memory model (legacy) |
| `kotlin("multiplatform")` | KMP Gradle plugin |
