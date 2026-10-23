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
Outline inspired by dchuk/claude-code-tauri-skills (tauri-android-distribution),
which has no license. No upstream text reused. Content written fresh against
Tauri v2 documentation, Google Play Console guides, and Android Developer docs.
-->

# Android Distribution (Google Play)

End-to-end workflow for shipping a Tauri 2 Android build to Google Play: keystore setup, `build.gradle.kts` wiring, AAB upload, Play App Signing handoff, and the rejection patterns that bite first-time submitters.

## When to use

You have a working `cargo tauri android build --aab` output and need to get it onto the Play Console. For the build command surface, NDK / 16KB / Windows trail, and the dev-mode stale-`.so` problem, see `build-deploy-mobile.md` first. For CI signing, see `ci-cd-mobile.md`.

## Prerequisites

| Item | Where |
|---|---|
| Google Play developer account ($25 one-off) | https://play.google.com/console/signup |
| Tauri Android initialised | `cargo tauri android init` |
| Signed release AAB | this doc, plus `build-deploy-mobile.md` for commands |
| Privacy policy URL | required for any app handling user data, location, ads, or contacts |
| Content rating questionnaire | filled inside Play Console |
| Store assets | feature graphic, icon 512x512, 2-8 screenshots per form factor |

## `tauri.conf.json` Android knobs

```json
{
  "bundle": {
    "android": {
      "minSdkVersion": 24,
      "versionCode": 1
    }
  }
}
```

| Key | Default | Notes |
|---|---|---|
| `minSdkVersion` | 24 (Android 7.0) | Raise only if you depend on an API level above the floor; lower is rarely worth the back-compat tax. |
| `versionCode` | auto from `version` | Must strictly increase on every Play upload, even for staged rollouts. |

### Version code formula

When `versionCode` is omitted, Tauri derives it from the semver `version` field:

```
versionCode = MAJOR * 1_000_000 + MINOR * 1_000 + PATCH
```

`1.4.7` becomes `1004007`. Override the auto value when you need a monotonic build counter independent of marketing version (most teams do this for CI):

```json
{
  "version": "1.4.7",
  "bundle": { "android": { "versionCode": 142 } }
}
```

### Min SDK ladder

| SDK | Android release |
|---|---|
| 24 | 7.0 Nougat |
| 26 | 8.0 Oreo |
| 28 | 9.0 Pie |
| 29 | 10 |
| 30 | 11 |
| 31 | 12 |
| 33 | 13 |
| 34 | 14 |
| 35 | 15 (16KB page size enforced for new uploads, see `build-deploy-mobile.md`) |

## Keystore creation

Play App Signing is mandatory for new apps, but you still own the **upload key**. Generate it once and back it up; if you lose it you cannot push updates without going through Google's manual recovery.

```bash
keytool -genkeypair -v \
  -keystore upload-keystore.jks \
  -alias upload \
  -keyalg RSA -keysize 2048 \
  -validity 10000 \
  -storetype JKS
```

Store the resulting `upload-keystore.jks` outside the repo. Add to `.gitignore`:

```
*.jks
*.keystore
keystore.properties
**/gen/android/keystore.properties
```

## Wire the keystore into Gradle

Create `src-tauri/gen/android/keystore.properties` (gitignored):

```properties
storeFile=/absolute/path/to/upload-keystore.jks
storePassword=...
keyAlias=upload
keyPassword=...
```

Then edit `src-tauri/gen/android/app/build.gradle.kts` so the release build type pulls those values. Tauri regenerates this file on `tauri android init`, so commit the patch as a kept-local change or apply it post-init.

```kotlin
import java.util.Properties
import java.io.FileInputStream

val keystoreProps = Properties().apply {
    val f = rootProject.file("keystore.properties")
    if (f.exists()) load(FileInputStream(f))
}

android {
    signingConfigs {
        create("release") {
            storeFile = keystoreProps["storeFile"]?.let { file(it as String) }
            storePassword = keystoreProps["storePassword"] as String?
            keyAlias = keystoreProps["keyAlias"] as String?
            keyPassword = keystoreProps["keyPassword"] as String?
        }
    }
    buildTypes {
        getByName("release") {
            signingConfig = signingConfigs.getByName("release")
            isMinifyEnabled = true
            isShrinkResources = true
        }
    }
}
```

### CI signing without a file on disk

In CI, prefer env vars over a checked-in `keystore.properties`. Base64-encode the JKS, decode at runtime, then read from env:

```kotlin
signingConfigs {
    create("release") {
        storeFile = System.getenv("ANDROID_KEYSTORE_PATH")?.let { file(it) }
        storePassword = System.getenv("ANDROID_STORE_PASSWORD")
        keyAlias = System.getenv("ANDROID_KEY_ALIAS")
        keyPassword = System.getenv("ANDROID_KEY_PASSWORD")
    }
}
```

CI step that materialises the keystore from a secret:

```yaml
- name: Restore keystore
  run: |
    echo "$ANDROID_KEYSTORE_BASE64" | base64 -d > "$RUNNER_TEMP/upload.jks"
    echo "ANDROID_KEYSTORE_PATH=$RUNNER_TEMP/upload.jks" >> $GITHUB_ENV
```

## Build artefact locations

After `cargo tauri android build --aab --target aarch64`:

| Artefact | Path |
|---|---|
| Universal AAB (Play Store upload) | `src-tauri/gen/android/app/build/outputs/bundle/universalRelease/app-universal-release.aab` |
| Per-arch AAB | `.../bundle/<arch>Release/app-<arch>-release.aab` |
| Release APK (sideload / alt stores) | `src-tauri/gen/android/app/build/outputs/apk/universal/release/app-universal-release.apk` |
| Mapping for crash de-obfuscation | `src-tauri/gen/android/app/build/outputs/mapping/release/mapping.txt` |

## Play Console upload (first release)

1. **Create app**: All apps -> Create app. Pick default language, app name, free/paid, declare it as App (not Game) if appropriate.
2. **Set up your app** checklist on the dashboard. Burn down every required item before the upload UI unlocks:
   - App access (login credentials for review)
   - Ads declaration
   - Content rating questionnaire
   - Target audience
   - News app declaration
   - COVID-19 contact-tracing declaration
   - Data safety form (must mirror your actual data flows)
   - Government app declaration
   - Privacy policy URL
3. **Production -> Create new release**. Upload the universal AAB.
4. **Play App Signing**: on the first upload Google prompts you to opt in. Accept. From here on, your upload key signs the AAB you submit, then Google re-signs the artefact served to devices with the app-signing key it manages.
5. **Release name and notes**: name defaults to `versionName (versionCode)`; release notes per locale.
6. **Review and rollout**: pick staged percentage or full rollout, then Send for review.

Initial review for a new account commonly takes several days. Subsequent reviews are typically hours to a day.

## Updates after the first release

- Bump `versionCode` (strictly increasing) and usually `version` (semver) in `tauri.conf.json`.
- Sign with the same upload keystore. Losing it requires Google's upload-key reset flow (multi-day, identity verification).
- For staged rollouts, watch the Pre-launch report and ANR / crash dashboards before raising the percentage.

## Internal testing track

Skip the public store for early builds:

1. Testing -> Internal testing -> Create new release.
2. Upload the AAB (same signing rules).
3. Add testers by Google account email (max 100). Optionally set up a Google Group.
4. Share the opt-in link with testers.

No content review for internal testing. Builds become available within minutes.

## Pre-submission self-check

| Check | Why it fails review |
|---|---|
| Privacy policy URL reachable from a fresh browser session | Reviewers hit dead links and reject for "Privacy policy unavailable". |
| Data safety form matches what the app actually does | Mismatched declarations of network access, location, contacts -> policy strike. |
| Permissions in `AndroidManifest.xml` justified | Camera/location/contacts requested but never used trigger Policy 4.8 rejection. |
| Icon and screenshots locale-consistent | Mixed-language screenshots get flagged. |
| `targetSdkVersion` meets Play's annual floor | Each August Google raises the floor; check the current minimum on the developer site. |
| `applicationId` matches the Play Console listing | Mismatch fails the upload check immediately. |
| Crash-reproducible flow for reviewer | "App crashed on launch" rejections happen when the dev account login is gated by your own backend. Provide credentials in App access. |

## Common rejections and fixes

| Symptom | Root cause | Fix |
|---|---|---|
| "Upload failed: APK signed with debug key" | `--debug` build, or release build but signingConfig not wired | Confirm `keystore.properties` is on disk in CI and `build.gradle.kts` reads it. |
| "Version code N has already been used" | You forgot to bump `versionCode` | Increment and rebuild. |
| "App is not 16 KB aligned" | NDK older than 28 without rustflag | See `build-deploy-mobile.md` 16KB section. |
| "We found an issue with your declared permissions" | Manifest auto-merger pulled an unused permission from a plugin | Audit `gen/android/app/src/main/AndroidManifest.xml` and add `<uses-permission ... tools:node="remove" />` for the ones you do not need. |
| Pre-launch report shows TLS errors on Android 7 | App used a network plugin that ships without an updated trust store | Bundle a trust store or raise `minSdkVersion`. |

## Local sideload check before upload

```bash
adb install -r src-tauri/gen/android/app/build/outputs/apk/universal/release/app-universal-release.apk
adb shell pm grant <package> android.permission.POST_NOTIFICATIONS  # if your app needs it on Android 13+
adb logcat -s RustStdoutStderr WindowManager Tauri
```

If the install fails with `INSTALL_PARSE_FAILED_NO_CERTIFICATES`, the APK is unsigned (debug-only build). If it fails with `INSTALL_FAILED_UPDATE_INCOMPATIBLE`, uninstall the previous build first (signing identity changed).

## Resources

- Tauri Android distribution: https://v2.tauri.app/distribute/google-play/
- Play Console: https://play.google.com/console
- Play App Signing: https://support.google.com/googleplay/android-developer/answer/9842756
- App bundle (AAB) format: https://developer.android.com/guide/app-bundle
- Target API level policy timeline: https://support.google.com/googleplay/android-developer/answer/11926878
- ProGuard / R8 (used when `isMinifyEnabled = true`): https://developer.android.com/build/shrink-code

## Related local references

- `build-deploy-mobile.md` -- build commands, 16KB rustflag, NDK guidance, Windows trail
- `ci-cd-mobile.md` -- env-var-driven keystore in CI, store-upload steps
- `setup-mobile.md` -- toolchain prerequisites
- `mobile-stale-builds.md` -- stale frontend in APK pitfall (read before debugging "wrong UI in release build")
- `plugins-mobile.md` -- permission impact of common plugins
