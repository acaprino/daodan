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

# Mobile CI/CD

Mobile-specific signing, store upload, and gotchas on top of the base pipeline patterns in `ci-cd.md`.

## When to use

CI that produces signed `.aab`/`.apk` for Google Play or `.ipa` for the App Store. Internal/test builds can skip most of this.

## Required runner OS

- **Android**: Linux (cheapest, fastest). Java 17+, Android SDK + NDK, Rust targets `aarch64-linux-android` and `armv7-linux-androideabi`.
- **iOS**: macOS only -- Apple toolchains do not run elsewhere. Full Xcode (not CLI tools), Rust targets `aarch64-apple-ios` and `aarch64-apple-ios-sim`.

Run them in parallel jobs.

## Gotchas

- **16KB page size for Google Play.** Builds with NDK < 28 may fail Play Console's page-size check. Either upgrade NDK or add `RUSTFLAGS="-C link-arg=-Wl,-z,max-page-size=16384"` for affected `.so` libs. Symptom: store upload rejected with "App is not 16 KB aligned."
- **Android keystore as base64.** Generate with `base64 -i upload-keystore.jks | tr -d '\n'` and store as `ANDROID_KEYSTORE_BASE64`. Decode at build time:
  ```bash
  echo "$ANDROID_KEYSTORE_BASE64" | base64 -d > /tmp/keystore.jks
  ```
  Then write `keystore.properties` with alias/password/path. Required secrets: `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD`, `ANDROID_KEYSTORE_BASE64`.
- **iOS: App Store Connect API key, not Apple ID.** Headless CI cannot do interactive 2FA. Generate a `.p8` key in App Store Connect and store as `APPLE_API_KEY_CONTENT` (raw .p8 contents) plus `APPLE_API_ISSUER`, `APPLE_API_KEY` (the key ID), `APPLE_TEAM_ID`.
- **Cache Gradle and CocoaPods.** Without it, Android builds add 5-10 min and iOS adds 3-5 min.
  - Gradle: `~/.gradle/caches/` keyed on `gradle-wrapper.properties` hash
  - CocoaPods: `Pods/` and `~/Library/Caches/CocoaPods/` keyed on `Podfile.lock`
- **Dev builds vs store builds use different artifact paths.** AABs land in `src-tauri/gen/android/app/build/outputs/bundle/`, APKs in `.../apk/`. iOS `.ipa` ends up under `src-tauri/gen/apple/build/`.

## Store upload

- **Google Play**: Fastlane or the Play Developer API. Tracks: `internal`, `alpha`, `beta`, `production`. Requires a service account JSON with the `Release Manager` role.
- **App Store**: `xcrun altool --upload-app` or Fastlane `pilot`/`deliver`. Uses the same App Store Connect API key as signing.

## Official docs

- Tauri Android distribution: https://v2.tauri.app/distribute/google-play/
- Tauri iOS distribution: https://v2.tauri.app/distribute/app-store/
- App Store Connect API keys: https://developer.apple.com/documentation/appstoreconnectapi/creating_api_keys_for_app_store_connect_api
- 16KB page size requirement: https://developer.android.com/guide/practices/page-sizes
- Fastlane: https://docs.fastlane.tools/

## Related

- `ci-cd.md` -- base pipeline patterns, caching, OS matrix
- `build-deploy-mobile.md` -- the mobile bundle gotchas (NDK, symlinks, RustWebViewClient) that CI inherits
- `setup-mobile.md` -- the toolchain CI mirrors
