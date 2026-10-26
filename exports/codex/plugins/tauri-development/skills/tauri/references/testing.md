<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
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

# Testing with Emulator and ADB

Practical recipes for testing Tauri 2 mobile apps on an Android emulator. iOS simulator is mostly Xcode-driven and doesn't need a separate guide.

## When to use

Iterating on Android in `tauri android dev`, debugging WebView issues, scripting install/log/screenshot/restart cycles, or tracking down "works on the emulator, breaks on a real device" issues.

## Emulator + ADB sanity checklist

1. AVD created in Android Studio (Pixel 7 Pro, API 34, x86_64 + Google Play, 4GB RAM is the safe default).
2. `adb devices -l` lists it.
3. `cargo tauri android dev` finds it without `--device`.
4. If not: `adb kill-server && adb start-server` and retry.

## Gotchas

- **`--force-ip-prompt` and pick the LAN IP, not 127.0.0.1.** Tauri offers a list of network interfaces; selecting localhost makes the emulator reach itself, not your dev server, and the WebView shows blank. The LAN IP (`192.168.x.x`) is what you want even on the emulator.
- **Vite must print `Network: http://192.168.x.x:5173/`.** If you only see `Local`, you forgot to honour `TAURI_DEV_HOST` in `vite.config.ts` (see `setup-mobile.md`). The emulator can't reach `localhost`.
- **HMR not working on the device?** `adb reverse tcp:5174 tcp:5174` exposes the WebSocket port back. If still broken, full restart: emulator → Vite → `adb kill-server` → start emulator → `cargo tauri android dev`.
- **Logcat is noisy.** Tauri-relevant filter: `adb logcat | grep -iE "(tauri|RustStdout|WebView)"`. Just Rust prints: `adb logcat | grep "RustStdout"`. With timestamps: `-v time`.
- **`adb install` after a previous install fails with `INSTALL_FAILED_ALREADY_EXISTS`.** Use `-r -d` (reinstall, allow downgrade) or `adb uninstall com.your.app.identifier` first.
- **IAP doesn't work on emulators without Google Play.** The "Google APIs" image is not enough -- pick "Google Play" explicitly when creating the AVD. Verify with `adb shell pm list packages | grep vending`.
- **Hardware virtualization missing = 5x slower.** Linux: `egrep -c '(vmx|svm)' /proc/cpuinfo` must be > 0, install `qemu-kvm`. Windows: enable Hyper-V or HAXM in BIOS.
- **Slow Rust builds**: `cargo tauri android build --target aarch64` skips the x86 / armv7 builds; combine with `sccache` for ~50% speedup on incremental rebuilds.
- **WebView DevTools**: open Chrome → `chrome://inspect/#devices` → click "inspect" on your app's WebView. The standard Chrome inspector attaches.

## The five commands worth aliasing

```bash
# Start dev cycle
cargo tauri android dev

# Tail Tauri-only logs
adb logcat -c && adb logcat | grep -iE "(tauri|RustStdout)"

# Reinstall debug APK without uninstalling
adb install -r src-tauri/gen/android/app/build/outputs/apk/universal/debug/app-universal-debug.apk

# Force restart the app (faster than reinstall)
adb shell am force-stop com.your.app.identifier && \
  adb shell am start -n com.your.app.identifier/.MainActivity

# Test deep link
adb shell am start -W -a android.intent.action.VIEW -d "myapp://open/screen" com.your.app.identifier
```

## Permissions during dev

```bash
adb shell pm grant com.your.app.identifier android.permission.CAMERA
adb shell pm revoke com.your.app.identifier android.permission.CAMERA   # to test request flow
```

## Official docs

- Android emulator CLI: https://developer.android.com/studio/run/emulator-commandline
- ADB reference: https://developer.android.com/tools/adb
- WebView debugging in Chrome DevTools: https://developer.chrome.com/docs/devtools/remote-debugging/webviews
- pidcat (better logcat with colors): https://github.com/JakeWharton/pidcat
- Tauri Android dev guide: https://v2.tauri.app/develop/#android

## Related

- `setup-mobile.md` -- the toolchain underneath this
- `build-deploy-mobile.md` -- moving from emulator to real device + signing
- `plugins-mobile.md` -- the plugins you're testing on the emulator
