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
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
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

# Setup and Tooling

Project generation, build system, language choice, IDE configuration, and libGDX 1.14.0 changes.

## Project Generation with gdx-liftoff

`gdx-liftoff` is the official project generator maintained under the `libgdx` GitHub org. It replaced the legacy `gdx-setup.jar` and is the only generator recommended for new projects.

### Get the generator
- Latest release: https://github.com/libgdx/gdx-liftoff/releases
- Download the `gdx-liftoff-*.jar` runnable JAR
- Requires JDK 17 minimum, Java 21 recommended

### Run the generator
```bash
java -jar gdx-liftoff-<version>.jar
```
Opens a Swing GUI with these decision panels:
- **Basic**: project name, package, main class, output directory, libGDX version
- **Platforms**: Core (always), LWJGL3 (desktop), Android, iOS, HTML
- **Languages**: Java, Kotlin, Groovy, Scala, Clojure (Java and Kotlin are by far the most common)
- **Extensions**: Box2D, Box2DLights, Ashley, FreeType, Controllers, ai, gdx-vfx
- **Third-party extensions**: bundled curated list (gdx-pay, gdx-fireapp, regexodus, etc.)
- **Templates**: Empty, ApplicationListener, ApplicationAdapter, Game (Screens), Scene2D demo

### Generated layout
A multi-module Gradle project:
```
my-game/
  build.gradle          # root config, shared dependencies, version coordinates
  settings.gradle       # module list
  gradle.properties
  core/                 # platform-independent game code
    src/main/java/...
  lwjgl3/               # Desktop launcher (LWJGL3 backend)
    src/main/java/.../lwjgl3/Lwjgl3Launcher.java
  android/              # Android launcher + AndroidManifest.xml + res/
  ios/                  # iOS launcher (RoboVM)
  html/                 # GWT module + html descriptor
```

### Baseline versions in gdx-liftoff (as of 2025)
- libGDX target: 1.14.0
- Kotlin: 2.3.21
- Gradle: 9.5.0
- Java toolchain: 21 (with 17 minimum)
- LWJGL3: 3.4.1

## Language Choice

| Target set | Language |
|------------|----------|
| Desktop + Android only | Kotlin (recommended) |
| Desktop + Android + iOS | Kotlin works (RoboVM compiles Kotlin bytecode), but iOS source level is Java 8 |
| Any setup including HTML5 (GWT) | **Java only**. Kotlin is incompatible with GWT |
| HTML5 with Kotlin | Use TeaVM backend instead (work-in-progress libGDX support) |

Kotlin benefits in libGDX (from community experience, Unciv project):
- ~20% smaller code base
- Compile-time null safety eliminates a class of NPEs
- Extension functions clean up Vector2/Matrix4 math
- No measurable runtime performance penalty (JVM bytecode is the same)

Kotlin caveats:
- GWT/HTML backend will not compile Kotlin
- Coroutines work on Desktop/Android/iOS but be careful with the render thread
- KTX library (https://github.com/libktx/ktx) provides idiomatic Kotlin wrappers for libGDX

## Build System: Gradle

libGDX only officially supports Gradle. Maven is not supported by gdx-liftoff and the wiki has not maintained Maven instructions in years.

### Common Gradle tasks
| Task | What it does |
|------|--------------|
| `:lwjgl3:run` | Run the desktop module |
| `:lwjgl3:dist` | Build a runnable fat JAR |
| `:android:installDebug` | Install on connected Android device or emulator |
| `:android:bundleRelease` | Build signed AAB for Play Store |
| `:ios:launchIPhoneSimulator` | Launch in iOS simulator (macOS only) |
| `:html:dist` | Build production GWT bundle to `html/build/dist/` |
| `:html:superDev` | GWT super dev mode for HTML iteration |

### Multi-module Gradle setup
- Core module has no Android/iOS/Desktop dependencies; pure libGDX API
- Platform modules depend on core and add backend libraries
- Shared assets typically live in `android/assets/` and are symlinked or copied to other modules
- Do NOT add Android-specific dependencies to core; they will break Desktop and iOS

## JDK Selection

- **Build JDK**: 21 (gdx-liftoff default), 17 minimum
- **Source compatibility for core/desktop/Android**: Java 17+ (or 21)
- **Source compatibility for iOS**: capped at Java 8 by RoboVM. iOS-targeting projects must keep the core module at Java 8 source level
- **JDK 25 support**: LWJGL3 3.4.1 (default in libGDX 1.14.0) supports JDK 25

If iOS is a target, set `sourceCompatibility = 1.8` and `targetCompatibility = 1.8` in the core module and avoid:
- Java 9+ syntax: `var`, records, switch expressions, sealed classes, text blocks
- Java 9+ APIs: `List.of()`, `Optional#orElseThrow()` overloads, HTTP client, etc.

## IDE Setup

- **IntelliJ IDEA** (community or ultimate): primary recommendation, best Gradle support
- **Android Studio**: required for Android development, works fine for Desktop too
- **Eclipse**: legacy, not recommended for modern libGDX
- **VSCode**: works with Java/Kotlin extensions but Gradle integration is weaker

Import as Gradle project. Let the IDE download dependencies. First import can take several minutes.

## libGDX 1.14.0 Breaking Changes (Released 2025-10-20)

Released after libGDX 1.13.5 (2025-05). The framework is actively maintained; 5-month release cadence.

### Pools API deprecation
The 1.13.x `Pools` API was reverted and is now deprecated. Migrate to the new `PoolManager`:
```java
// Before
MyComponent c = Pools.obtain(MyComponent.class);
Pools.free(c);

// After
MyComponent c = PoolManager.get().obtain(MyComponent.class);
PoolManager.get().free(c);
```
The old `Pools` methods still work but are marked deprecated and will be removed in a future major version.

### JsonValue case sensitivity
`JsonValue#get(String)` no longer matches case-insensitively. Audit JSON loading code; keys must now match exactly. If your assets have mixed-case keys you previously relied on, normalize them in the JSON files.

### Tiled map loader unification
`TmxMapLoader` and `AtlasTmxMapLoader` now share a common base. Class objects and template objects are supported in Tiled `.tmx` files. If you wrote a custom Tiled loader, check the parent-class signatures.

### LWJGL3 upgraded to 3.4.1
Supports Java 25 and later runtimes. No application-level changes typically required, but `Lwjgl3ApplicationConfiguration` API surface is unchanged.

### Other notable changes
See https://libgdx.com/news/2025/10/gdx-1-14-0 for the full annotated changelog.

## Helpful Tools and Libraries

| Tool | Purpose |
|------|---------|
| **TexturePacker** | Pack sprites into atlas. Bundled with libGDX, run via gradle task or standalone JAR |
| **Skin Composer** | GUI tool to author Scene2D Skin JSON files; https://github.com/raeleus/skin-composer |
| **Tiled** | Industry-standard 2D map editor; libGDX has native `.tmx` loader |
| **Spine** | Skeletal animation; libGDX runtime via `com.esotericsoftware.spine` |
| **KTX** | Kotlin extensions for libGDX; https://github.com/libktx/ktx |
| **gdx-vfx** | Post-processing effects (bloom, blur, vignette); https://github.com/crashinvaders/gdx-vfx |
| **gdx-controllers** | Gamepad support |
| **gdx-pay** | In-app purchase abstraction for Android/iOS |

## Source References

- https://libgdx.com/wiki/start/setup
- https://libgdx.com/wiki/start/project-generation
- https://github.com/libgdx/gdx-liftoff
- https://github.com/libgdx/gdx-liftoff/blob/master/Guide.md
- https://libgdx.com/news/2025/10/gdx-1-14-0
- https://libgdx.com/news/all/
