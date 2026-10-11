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

# Mobile Environment Setup

Android SDK + iOS Xcode tooling on top of the base prerequisites in `setup.md`.

## When to use

Adding Android or iOS targets to an existing Tauri 2 project, or setting up a new dev machine for mobile builds. Pure desktop projects can skip this entirely.

## Rust targets (the one thing easy to forget)

```bash
# Android
rustup target add aarch64-linux-android armv7-linux-androideabi i686-linux-android x86_64-linux-android

# iOS (macOS only)
rustup target add aarch64-apple-ios x86_64-apple-ios aarch64-apple-ios-sim
```

`tauri android init` / `tauri ios init` won't add these for you -- the build will fail late with cryptic linker errors if they're missing.

## Gotchas

- **Strawberry Perl on Windows.** If your Rust deps include `reqwest` with `native-tls`, cross-compiling for Android pulls in the vendored `openssl-src` crate, which needs a full Perl install. Git Bash's bundled Perl is **not** sufficient. Install [Strawberry Perl](https://strawberryperl.com/) and put it on PATH before `tauri android build`. The error message ("Could not find Perl") doesn't make this obvious.
- **`TAURI_DEV_HOST` is set automatically** by `tauri android dev` / `tauri ios dev` -- your `vite.config.ts` should read it and bind `server.host` + HMR to it. If you hardcode `localhost`, the device can't reach the dev server.
- **Vite build target.** Mobile WebViews lag desktop -- target `chrome105` for Android WebView (matches Tauri 2's WebView2 floor) and `safari14` for iOS WKWebView. `esnext` will silently produce code the device WebView can't parse.
- **iOS needs the full Xcode**, not just CLI tools. CocoaPods via `brew install cocoapods` -- the gem version drifts.
- **Android NDK version**: install **NDK 28+** if you can. NDK 28 produces 16-KB-aligned shared libraries by default, which Google Play requires (deadline extended to 2026-05-31). NDK 27 is the LTS line and works fine, but you must add the `-Wl,-z,max-page-size=16384` rustflag (see `build-deploy-mobile.md`). Set `NDK_HOME` dynamically (e.g. `$ANDROID_HOME/ndk/$(ls -1 $ANDROID_HOME/ndk | tail -1)`); pinning a specific version path breaks across machines.

## Toolchain versions pinned by `tauri android init` (May 2026)

The current Tauri 2.x template (verified against `dev` branch on 2026-05-08, shipped in tauri-cli 2.11.1) generates an Android project pinned to:

| Component | Version | Source |
|---|---|---|
| `tauri` / `tauri-cli` / `tauri-build` | 2.11.1 / 2.11.1 / 2.6.1 | crates.io, released 2026-05-06 |
| Android Gradle Plugin (AGP) | 8.11.0 | `build.gradle.kts` template |
| Gradle wrapper | 8.14.3 | `gradle-wrapper.properties` template |
| Kotlin | 1.9.25 | `build.gradle.kts` template |
| `compileSdk` / `targetSdk` | 36 / 36 | `app/build.gradle.kts` template |
| `jvmTarget` (deprecated form) | `"1.8"` | `app/build.gradle.kts` template |

`targetSdk = 36` is forward-compatible with the Google Play API requirement (currently API 35 since 2025-08-31; no API 36 deadline announced as of May 2026).

### Gradle 9.0 readiness

Builds on the shipped template emit "Deprecated Gradle features were used in this build, making it incompatible with Gradle 9.0." The known-deprecated bits in the Tauri Android template:

- `kotlinOptions { jvmTarget = "1.8" }` is deprecated in favour of the `jvmToolchain { ... }` block in modern AGP/Kotlin.
- A few other AGP 8.x diagnostics that get loud when you run with Gradle 8.13+.

Tracking issue: [tauri-apps/tauri#13858](https://github.com/tauri-apps/tauri/issues/13858). PR [#14984](https://github.com/tauri-apps/tauri/pull/14984) proposed bumping the template to AGP 9.0.1 / Gradle 9.3.1 / Kotlin 2.3.10 / JVM 24 but was closed without merging as of 2026-05-08, so the warnings remain in shipped projects. Builds still succeed on Gradle 8.14.3; treat the warnings as a future-compat heads-up, not a blocker. If you want to silence them locally, you can override the toolchain with a `jvmToolchain(17)` block in `app/build.gradle.kts` and bump the wrapper, but that is a manual maintenance burden until the upstream template moves.

## Vite config snippet (the parts that matter)

```typescript
export default defineConfig({
  server: {
    host: process.env.TAURI_DEV_HOST || 'localhost',
    port: 5173,
    strictPort: true,
    hmr: process.env.TAURI_DEV_HOST
      ? { protocol: 'ws', host: process.env.TAURI_DEV_HOST, port: 5174 }
      : undefined,
  },
  clearScreen: false,
  envPrefix: ['VITE_', 'TAURI_'],
  build: {
    target: process.env.TAURI_ENV_PLATFORM === 'windows' ? 'chrome105' : 'safari14',
  },
});
```

## Official docs

- Mobile prerequisites: https://v2.tauri.app/start/prerequisites/#mobile-targets
- Android setup: https://v2.tauri.app/develop/#android
- iOS setup: https://v2.tauri.app/develop/#ios
- Android permissions reference: https://developer.android.com/reference/android/Manifest.permission
- iOS Info.plist usage descriptions: https://developer.apple.com/documentation/bundleresources/information_property_list

## Related

- `setup.md` -- base prerequisites
- `build-deploy-mobile.md` -- store builds, signing, the full Android/iOS gotcha trail
- `mobile-stale-builds.md` -- the Cargo `rerun-if-changed` gap that produces stale APKs (read before debugging "frontend changes don't appear")
- `testing.md` -- emulator + ADB + WebView debugging
- `ci-cd-mobile.md` -- CI build matrix for mobile
