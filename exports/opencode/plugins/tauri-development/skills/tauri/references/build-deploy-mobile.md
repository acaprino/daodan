<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
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

# Mobile Build and Deploy

Android (AAB/APK) + iOS (IPA) builds, store submission, and the Windows-specific build trail (16KB page size, symlink workaround, dev-mode `.so` stale assets, RustWebViewClient.kt patch). The Windows trail is gold local know-how -- nowhere upstream.

## When to use

Building signed `.aab`/`.apk` for Google Play, `.ipa` for the App Store, or just sideloading debug builds to a device. For desktop builds, see `build-deploy-desktop.md`. For toolchain prerequisites, see `setup-mobile.md`.

## Build commands

### Android
```bash
cargo tauri android build --apk                                    # debug APK (sideload)
cargo tauri android build --aab                                    # release AAB (Play Store)
cargo tauri android build --aab --target aarch64 --target armv7    # specific archs
cargo tauri android build --debug                                  # debug build
```

Output: APK in `src-tauri/gen/android/app/build/outputs/apk/`, AAB in `.../bundle/release/`.

### iOS
```bash
cargo tauri ios build --export-method app-store-connect            # App Store
cargo tauri ios build --export-method ad-hoc                       # Ad Hoc (registered devices)
cargo tauri ios build --export-method development                  # Dev
cargo tauri ios build --open                                       # Open in Xcode
```

Output: `src-tauri/gen/apple/build/`.

## Stale embedded frontend (THE pitfall)

Before any other Android debugging: if your APK shows old UI even after `vite build`, the `.so` is stale. This is a known structural gap in `tauri-build`'s `cargo:rerun-if-changed` tracking, not a Cargo bug or a "clean and retry" issue. The fix lives in your `build.rs`. See `mobile-stale-builds.md` for the full architecture, the three-tier solution (`build.rs` walk + Gradle safety net), and the cache-reset playbook.

The Windows-only "Dev-mode `.so` stale-asset deep-dive" section below is a separate (additional) failure mode where cross-compilation fails on the host and a fresh `.so` cannot be produced. The two problems compound on Windows.

## Gotchas

- **16KB page size (Google Play deadline 2026-05-31)**: Google Play started enforcing 16-KB alignment on Android 15+ uploads in November 2025, with a community extension to 2026-05-31. Two paths:
  - **NDK 28+**: produces 16-KB-aligned shared libraries by default, no rustflags needed. Recommended for new projects.
  - **NDK 27 (LTS)**: keep the explicit linker flag in `.cargo/config.toml`:
    ```toml
    [target.aarch64-linux-android]
    rustflags = ["-C", "link-arg=-Wl,-z,max-page-size=16384"]
    [target.armv7-linux-androideabi]
    rustflags = ["-C", "link-arg=-Wl,-z,max-page-size=16384"]
    ```
  Symptom on store upload: "App is not 16 KB aligned." Either upgrade to NDK 28+ or apply this rustflag.
- **iOS local development**: open `src-tauri/gen/apple/[App].xcodeproj` in Xcode → Signing & Capabilities → "Automatically manage signing" → select team. CI uses App Store Connect API key (`APPLE_API_ISSUER`/`APPLE_API_KEY`/`APPLE_API_KEY_PATH`/`APPLE_DEVELOPMENT_TEAM` env vars).
- **iOS upload from CLI**:
  ```bash
  xcrun altool --upload-app --type ios \
    --file "src-tauri/gen/apple/build/arm64/App.ipa" \
    --apiKey $APPLE_API_KEY_ID --apiIssuer $APPLE_API_ISSUER
  ```
- **Android version code format**: `MAJOR * 1000000 + MINOR * 1000 + PATCH` (override in `tauri.android.conf.json` if not auto-derived).
- **`cargo tauri icon ./app-icon.png`** generates all icon sizes. Source must be **1024x1024 PNG**. Outputs land in `src-tauri/icons/`.

## Windows-only build trail (the gold local know-how)

### `--apk` flag syntax bug

Use `--apk true` (not just `--apk`):
```bash
cargo tauri android build --apk true     # works on Windows
cargo tauri android build --apk          # may fail on Windows
```

### Symlink failure without Developer Mode

Windows requires elevated privileges to create symlinks; Tauri/Gradle creates them for `.so` native libraries. Without Developer Mode, build fails:
```
java.nio.file.FileSystemException: ...\libtauri_app.so:
A required privilege is not held by the client
```

**Fix 1 (recommended)**: Settings → For developers → **Developer Mode → On**, restart build.

**Fix 2 (manual jniLib copy workaround)** when Developer Mode isn't available:
```powershell
$jniLibs = "src-tauri\gen\android\app\src\main\jniLibs"
$arches = "arm64-v8a","armeabi-v7a","x86","x86_64"
$arches | ForEach-Object { New-Item -ItemType Directory -Force -Path "$jniLibs\$_" | Out-Null }

$buildOut = "src-tauri\gen\android\app\build\intermediates\tauri"
foreach ($a in $arches) {
  Copy-Item "$buildOut\$a\release\libtauri_app.so" "$jniLibs\$a\"
}

cd src-tauri\gen\android
.\gradlew assembleRelease
```

### Path-length limit

Windows default is 260 chars; Tauri Android builds easily exceed:
- Keep project in a short path (e.g. `C:\dev\myapp`)
- `git config --system core.longpaths true`
- Enable LongPathsEnabled in registry (admin)

## Dev-mode `.so` stale-asset deep-dive (Windows)

This section covers the Windows-host cross-compilation chain that prevents a fresh `.so` from being produced at all (Strawberry Perl + OpenSSL). For the general stale-`.so` problem (Cargo cache misses frontend changes on every platform), see `mobile-stale-builds.md` first; this section is for what happens AFTER you fixed Cargo's tracking and the build still fails on Windows.

### Symptom
App shows months-old frontend content when launched from Android Studio, even though Gradle rebuilds the frontend.

### Root cause
The Rust `.so` was compiled with `tauri android dev`. In dev mode the .so is configured differently:

| Setting | Dev | Build |
|---------|-----|-------|
| `withAssetLoader()` | `false` | `true` |
| `assetLoaderDomain()` | `"wry.assets"` | `"tauri.localhost"` |
| Asset source | Rust handler serves embedded assets | Android `WebViewAssetLoader` serves APK assets |

The WebView navigates to `http://tauri.localhost/` but with `withAssetLoader()=false` the Rust handler intercepts everything and serves assets embedded in the .so at compile time. Fresh assets in the APK are ignored.

### Cross-compilation blockers (sequential)

| # | Problem | Cause | Fix |
|---|---------|-------|-----|
| 1 | `cargo` not found in bash PATH | Rust toolchain not on PATH | Add `~/.rustup/toolchains/stable-x86_64-pc-windows-msvc/bin` to PATH |
| 2 | OpenSSL not found for `x86_64-linux-android` | `reqwest` + `native-tls` requires OpenSSL headers | No pre-built; vendored build (next row) |
| 3 | Vendored OpenSSL build fails | `openssl-src` needs full Perl; Git Bash's Perl is too minimal (missing `Locale::Maketext::Simple`) | **Install Strawberry Perl** |

### Kotlin workaround (`RustWebViewClient.kt` 4-step patch)

If cross-compilation is blocked, patch `src-tauri/gen/android/.../RustWebViewClient.kt` to force the `WebViewAssetLoader` path. **This file is gitignored / auto-generated by Tauri** -- changes are local only and lost on `tauri android init`.

| # | Problem | Symptom | Fix |
|---|---------|---------|-----|
| 1 | `.so` in dev mode | `withAssetLoader()=false`, Rust serves stale assets | Bypass: call `assetLoader.shouldInterceptRequest()` directly instead of delegating to Rust |
| 2 | HTTP vs HTTPS | Dev WebView navigates to `http://`, asset loader only intercepts HTTPS | Add `.setHttpAllowed(true)` to `WebViewAssetLoader.Builder` |
| 3 | Root path `/` returns null | `AssetsPathHandler` doesn't serve `index.html` for bare `/` | Rewrite URL: if path is `/`, change to `/index.html` before asset loader |
| 4 | Domain mismatch | `.so` returns `"wry.assets"`, WebView requests `"tauri.localhost"` | Hardcode `.setDomain("tauri.localhost")` in builder |

### Permanent fix
Install [Strawberry Perl](https://strawberryperl.com/), then:
```bash
npx tauri android build --debug --target x86_64
```
Recompiles the .so with `withAssetLoader()=true` and `assetLoaderDomain()="tauri.localhost"`, killing the Kotlin workaround.

### Collateral build fixes (you may also hit)

| Problem | Fix |
|---------|-----|
| NDK version mismatch | Update NDK path in `.cargo/config.toml` to match installed version |
| Java source/target 1.8 deprecated | `build.gradle.kts`: `sourceCompatibility = JavaVersion.VERSION_11`, same for target, `jvmTarget = "11"` |
| `java {}` toolchain block in root `build.gradle.kts` | Remove it -- doesn't work without the `java` plugin applied |

## Code signing summary

### Android keystore
```bash
keytool -genkey -v -keystore upload-keystore.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias upload -storepass YOUR_PASSWORD
```
Then `src-tauri/gen/android/keystore.properties` with `password=...`, `keyAlias=upload`, `storeFile=...`. Modify `build.gradle.kts` to use `signingConfig` in release type. **Add `*.jks`, `*.keystore`, `keystore.properties` to `.gitignore`.**

### iOS
- Local: Xcode Signing & Capabilities, automatic management.
- CI: App Store Connect API key (`.p8` file) + team ID.

## Cargo.toml release profile (mobile-optimized)

```toml
[profile.release]
lto = true
opt-level = "s"             # mobile: optimize for size
codegen-units = 1
strip = true
panic = "abort"

[profile.release.package.tauri]
opt-level = 3               # but Tauri core full-speed
```

## Official docs

- Tauri Android distribution: https://v2.tauri.app/distribute/google-play/
- Tauri iOS distribution: https://v2.tauri.app/distribute/app-store/
- 16KB page size (Android): https://developer.android.com/guide/practices/page-sizes
- App Store Connect API keys: https://developer.apple.com/documentation/appstoreconnectapi/creating_api_keys_for_app_store_connect_api
- `xcrun altool` reference: https://developer.apple.com/documentation/xcode/altool
- Strawberry Perl (Windows): https://strawberryperl.com/
- Android keytool: https://docs.oracle.com/javase/8/docs/technotes/tools/unix/keytool.html
- Tauri icon generator (`cargo tauri icon`): https://v2.tauri.app/reference/cli/#icon

## Related

- `mobile-stale-builds.md` -- the cross-platform stale-bundle bug (Cargo `rerun-if-changed` gap), Gradle safety net, cache reset playbook. **Read this first if your APK shows old UI after a frontend change.**
- `setup-mobile.md` -- toolchain prerequisites (Strawberry Perl, NDK, Vite mobile config)
- `build-deploy-desktop.md` -- desktop signing/notarization, updater
- `ci-cd-mobile.md` -- mobile CI signing + store upload
- `testing.md` -- emulator, ADB, logcat for debugging the build artifact
