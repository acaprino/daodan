<daodan_host_binding host="opencode">
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

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network fetch uses webfetch, network search uses
websearch, and a user question uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
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

<!--
Portions of this file are derived from Jeffallan/claude-skills
(https://github.com/Jeffallan/claude-skills), MIT License.
Snapshot 2026-05-12.
-->

# Ktor Server

## Application Setup

```kotlin
import io.ktor.server.application.*
import io.ktor.server.engine.*
import io.ktor.server.netty.*
import io.ktor.server.plugins.contentnegotiation.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.serialization.json.Json

fun main() {
    embeddedServer(Netty, port = 8080, host = "0.0.0.0") {
        configureRouting()
        configureSerialization()
        configureAuth()
        configureMonitoring()
    }.start(wait = true)
}

fun Application.configureSerialization() {
    install(ContentNegotiation) {
        json(Json {
            prettyPrint = true
            isLenient = true
            ignoreUnknownKeys = true
        })
    }
}
```

## Routing

```kotlin
import io.ktor.server.routing.*
import io.ktor.server.response.*
import io.ktor.server.request.*
import io.ktor.http.*

fun Application.configureRouting() {
    routing {
        route("/api/v1") {
            userRoutes()
            postRoutes()
        }
    }
}

fun Route.userRoutes() {
    route("/users") {
        get {
            val users = userService.getAllUsers()
            call.respond(HttpStatusCode.OK, users)
        }

        get("/{id}") {
            val id = call.parameters["id"]
                ?: return@get call.respond(HttpStatusCode.BadRequest, "Missing ID")

            val user = userService.getUser(id)
                ?: return@get call.respond(HttpStatusCode.NotFound, "User not found")

            call.respond(HttpStatusCode.OK, user)
        }

        post {
            val userRequest = call.receive<CreateUserRequest>()
            val user = userService.createUser(userRequest)
            call.respond(HttpStatusCode.Created, user)
        }

        put("/{id}") {
            val id = call.parameters["id"]
                ?: return@put call.respond(HttpStatusCode.BadRequest, "Missing ID")

            val updateRequest = call.receive<UpdateUserRequest>()
            val user = userService.updateUser(id, updateRequest)
                ?: return@put call.respond(HttpStatusCode.NotFound, "User not found")

            call.respond(HttpStatusCode.OK, user)
        }

        delete("/{id}") {
            val id = call.parameters["id"]
                ?: return@delete call.respond(HttpStatusCode.BadRequest, "Missing ID")

            val deleted = userService.deleteUser(id)
            if (deleted) {
                call.respond(HttpStatusCode.NoContent)
            } else {
                call.respond(HttpStatusCode.NotFound, "User not found")
            }
        }
    }
}
```

## Models & Serialization

```kotlin
import kotlinx.serialization.Serializable

@Serializable
data class User(
    val id: String,
    val email: String,
    val name: String,
    val createdAt: Long
)

@Serializable
data class CreateUserRequest(
    val email: String,
    val name: String,
    val password: String
)

@Serializable
data class UpdateUserRequest(
    val email: String? = null,
    val name: String? = null
)

@Serializable
data class ApiResponse<T>(
    val success: Boolean,
    val data: T? = null,
    val error: String? = null
)
```

## Authentication (JWT)

```kotlin
import io.ktor.server.auth.*
import io.ktor.server.auth.jwt.*
import com.auth0.jwt.JWT
import com.auth0.jwt.algorithms.Algorithm

fun Application.configureAuth() {
    val secret = environment.config.property("jwt.secret").getString()
    val issuer = environment.config.property("jwt.issuer").getString()
    val audience = environment.config.property("jwt.audience").getString()

    install(Authentication) {
        jwt("auth-jwt") {
            realm = "Ktor Server"
            verifier(
                JWT
                    .require(Algorithm.HMAC256(secret))
                    .withIssuer(issuer)
                    .withAudience(audience)
                    .build()
            )
            validate { credential ->
                if (credential.payload.audience.contains(audience)) {
                    JWTPrincipal(credential.payload)
                } else {
                    null
                }
            }
            challenge { _, _ ->
                call.respond(HttpStatusCode.Unauthorized, "Token is not valid or has expired")
            }
        }
    }
}

// Protected routes
fun Route.protectedRoutes() {
    authenticate("auth-jwt") {
        get("/profile") {
            val principal = call.principal<JWTPrincipal>()
            val userId = principal?.payload?.getClaim("userId")?.asString()
            val user = userService.getUser(userId ?: "")
            call.respond(user ?: HttpStatusCode.NotFound)
        }
    }
}

// Token generation
fun generateToken(userId: String): String {
    return JWT.create()
        .withAudience(audience)
        .withIssuer(issuer)
        .withClaim("userId", userId)
        .withExpiresAt(Date(System.currentTimeMillis() + 60000 * 60 * 24)) // 24h
        .sign(Algorithm.HMAC256(secret))
}
```

## Database Integration (Exposed)

```kotlin
import org.jetbrains.exposed.sql.*
import org.jetbrains.exposed.sql.transactions.experimental.newSuspendedTransaction
import org.jetbrains.exposed.sql.transactions.transaction

object Users : Table() {
    val id = varchar("id", 36)
    val email = varchar("email", 255).uniqueIndex()
    val name = varchar("name", 255)
    val passwordHash = varchar("password_hash", 255)
    val createdAt = long("created_at")

    override val primaryKey = PrimaryKey(id)
}

class UserService(private val database: Database) {
    suspend fun <T> dbQuery(block: suspend () -> T): T =
        newSuspendedTransaction(Dispatchers.IO) { block() }

    suspend fun getAllUsers(): List<User> = dbQuery {
        Users.selectAll().map { toUser(it) }
    }

    suspend fun getUser(id: String): User? = dbQuery {
        Users.select { Users.id eq id }
            .mapNotNull { toUser(it) }
            .singleOrNull()
    }

    suspend fun createUser(request: CreateUserRequest): User = dbQuery {
        val id = UUID.randomUUID().toString()
        val passwordHash = hashPassword(request.password)

        Users.insert {
            it[Users.id] = id
            it[email] = request.email
            it[name] = request.name
            it[Users.passwordHash] = passwordHash
            it[createdAt] = System.currentTimeMillis()
        }

        User(id, request.email, request.name, System.currentTimeMillis())
    }

    private fun toUser(row: ResultRow): User =
        User(
            id = row[Users.id],
            email = row[Users.email],
            name = row[Users.name],
            createdAt = row[Users.createdAt]
        )
}
```

## Error Handling

```kotlin
import io.ktor.server.plugins.statuspages.*

fun Application.configureErrorHandling() {
    install(StatusPages) {
        exception<Throwable> { call, cause ->
            when (cause) {
                is IllegalArgumentException -> {
                    call.respond(
                        HttpStatusCode.BadRequest,
                        ApiResponse<Nothing>(success = false, error = cause.message)
                    )
                }
                is NotFoundException -> {
                    call.respond(
                        HttpStatusCode.NotFound,
                        ApiResponse<Nothing>(success = false, error = cause.message)
                    )
                }
                else -> {
                    call.respond(
                        HttpStatusCode.InternalServerError,
                        ApiResponse<Nothing>(success = false, error = "Internal server error")
                    )
                }
            }
        }

        status(HttpStatusCode.NotFound) { call, status ->
            call.respond(
                status,
                ApiResponse<Nothing>(success = false, error = "Resource not found")
            )
        }
    }
}

class NotFoundException(message: String) : Exception(message)
```

## CORS Configuration

```kotlin
import io.ktor.server.plugins.cors.routing.*

fun Application.configureCORS() {
    install(CORS) {
        allowMethod(HttpMethod.Options)
        allowMethod(HttpMethod.Put)
        allowMethod(HttpMethod.Delete)
        allowMethod(HttpMethod.Patch)
        allowHeader(HttpHeaders.Authorization)
        allowHeader(HttpHeaders.ContentType)
        allowCredentials = true
        allowNonSimpleContentTypes = true

        anyHost() // Development only
        // allowHost("client-host", schemes = listOf("http", "https"))
    }
}
```

## WebSockets

```kotlin
import io.ktor.websocket.*
import io.ktor.server.websocket.WebSockets
import io.ktor.server.websocket.webSocket
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.receiveAsFlow

fun Application.configureWebSockets() {
    install(WebSockets) {
        pingPeriod = Duration.ofSeconds(15)
        timeout = Duration.ofSeconds(15)
        maxFrameSize = Long.MAX_VALUE
        masking = false
    }

    routing {
        webSocket("/chat") {
            val session = ChatSession(this)
            chatService.addSession(session)

            try {
                for (frame in incoming) {
                    when (frame) {
                        is Frame.Text -> {
                            val message = frame.readText()
                            chatService.broadcast(message)
                        }
                        else -> {}
                    }
                }
            } finally {
                chatService.removeSession(session)
            }
        }
    }
}
```

## Testing

```kotlin
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.server.testing.*
import kotlin.test.*

class ApplicationTest {
    @Test
    fun testGetUsers() = testApplication {
        application {
            configureRouting()
            configureSerialization()
        }

        val response = client.get("/api/v1/users")
        assertEquals(HttpStatusCode.OK, response.status)
    }

    @Test
    fun testCreateUser() = testApplication {
        application {
            configureRouting()
            configureSerialization()
        }

        val response = client.post("/api/v1/users") {
            contentType(ContentType.Application.Json)
            setBody(CreateUserRequest("test@example.com", "Test User", "password123"))
        }

        assertEquals(HttpStatusCode.Created, response.status)
    }

    @Test
    fun testAuthenticatedRoute() = testApplication {
        application {
            configureAuth()
            configureRouting()
        }

        val token = generateToken("user123")

        val response = client.get("/api/v1/profile") {
            header(HttpHeaders.Authorization, "Bearer $token")
        }

        assertEquals(HttpStatusCode.OK, response.status)
    }
}
```

## Quick Reference

| Plugin | Purpose |
|--------|---------|
| `ContentNegotiation` | JSON serialization |
| `Authentication` | JWT/OAuth2 auth |
| `CORS` | Cross-origin requests |
| `StatusPages` | Error handling |
| `CallLogging` | Request logging |
| `WebSockets` | WebSocket support |
| `RateLimit` | Rate limiting |
| `Compression` | Response compression |

| Function | Purpose |
|----------|---------|
| `call.receive<T>()` | Parse request body |
| `call.respond()` | Send response |
| `call.parameters` | Query/path params |
| `call.principal()` | Get authenticated user |
| `authenticate { }` | Protect routes |
| `route("/path") { }` | Group routes |
