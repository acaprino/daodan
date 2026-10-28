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

# Mobile Plugins and Patterns

Mobile-only Tauri plugins (biometric, barcode, haptics, NFC, geolocation) plus mobile deep-link configuration and the Android safe-area workaround.

## When to use

Adding a capability that only exists on Android/iOS, or hitting one of the mobile-specific quirks below. For universal plugins (fs, http, store, sql, etc.), see `plugins-core.md`.

## Mobile-only plugin matrix

| Plugin | Platforms | Use for |
|--------|-----------|---------|
| `biometric` | Android, iOS | Fingerprint / Face ID auth |
| `barcode-scanner` | Android, iOS | QR / EAN / Code128 scanning |
| `haptics` | Android, iOS | Tap / impact / notification feedback |
| `nfc` | Android, iOS | NFC tag read/write |
| `geolocation` | Android, iOS | GPS position + watch |

Universal plugins that also work on mobile: `fs`, `http`, `notification`, `store`, `sql`, `deep-link`, `opener`, `os`.

## Gotchas

- **`#[cfg(mobile)]` on every mobile-only plugin registration.** Without the gate, `cargo tauri build` fails on desktop targets. Missing-cfg is the #1 mobile build error.
- **Android `safe-area-inset-*` does not work** out of the box on Tauri's WebView. Pure CSS `env(safe-area-inset-top)` returns 0 on Android. The fix is to detect platform once at app boot and inject explicit pixel values via CSS custom properties (snippet below).
- **iOS biometric "fallback to password" requires `allowDeviceCredential: true`** -- without it, users with no biometrics enrolled get a hard error instead of a passcode prompt.
- **`barcode-scanner` opens a full-screen camera view** that takes over the WebView; design for the disappear/reappear lifecycle. Use `windowed: true` only for prototypes -- on iOS the windowed view has known z-order bugs.
- **`geolocation` `enableHighAccuracy: true` drains battery fast** -- only enable on the active screen, never in a background subscription.
- **NFC writes are platform-different.** Android works in foreground only (no background dispatch via Tauri's plugin); iOS prompts user every read/write -- there is no "always-on" NFC.
- **Mobile capabilities live in their own file.** Create `src-tauri/capabilities/mobile.json` with `"platforms": ["iOS", "android"]` -- mixing into `default.json` makes desktop fail capability checks.

## Android safe-area workaround (the one composite pattern worth keeping local)

CSS `env(safe-area-inset-*)` works on iOS but returns 0 on Android WebView. Detect Android and inject explicit values:

```typescript
import { platform } from '@tauri-apps/plugin-os';

export async function setupMobileSafeAreas(): Promise<void> {
  if ((await platform()) === 'android') {
    document.documentElement.style.setProperty('--safe-area-top', '48px');
    document.documentElement.style.setProperty('--safe-area-bottom', '24px');
  }
}
```

```css
:root {
  --safe-area-top: env(safe-area-inset-top, 0px);     /* iOS native; Android 0 -> overridden by JS */
  --safe-area-bottom: env(safe-area-inset-bottom, 0px);
}
.header { padding-top: var(--safe-area-top); }
.bottom-nav { padding-bottom: var(--safe-area-bottom); }
```

Typical values: Android top ~48px, bottom ~24px. iOS varies 44-59px top, 0-34px bottom (home indicator).

## Mobile capabilities file

```json
// src-tauri/capabilities/mobile.json
{
  "identifier": "mobile",
  "windows": ["main"],
  "platforms": ["iOS", "android"],
  "permissions": [
    "biometric:allow-authenticate",
    "geolocation:allow-get-current-position",
    "haptics:default"
  ]
}
```

## Mobile deep-link snippets

Android `AndroidManifest.xml` Intent Filter for Universal Links:

```xml
<intent-filter android:autoVerify="true">
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="https" android:host="app.example.com" />
</intent-filter>
```

iOS Associated Domains (Xcode → Signing & Capabilities):
```
applinks:app.example.com
```

## Official docs

- Mobile plugins index: https://v2.tauri.app/plugin/ (each plugin page lists its mobile support)
- Biometric: https://v2.tauri.app/plugin/biometric/
- Barcode scanner: https://v2.tauri.app/plugin/barcode-scanner/
- NFC: https://v2.tauri.app/plugin/nfc/
- Haptics: https://v2.tauri.app/plugin/haptics/
- Geolocation: https://v2.tauri.app/plugin/geolocation/
- Deep links (mobile sections): https://v2.tauri.app/plugin/deep-link/

## Community plugins

- `tauri-plugin-iap` -- in-app purchases (see `iap.md`)
- `tauri-plugin-keep-screen-on`, `tauri-plugin-camera`, `tauri-plugin-share`
- Index: https://github.com/tauri-apps/awesome-tauri

## Related

- `plugins-core.md` -- universal plugins
- `iap.md` -- the IAP plugin in detail
- `setup-mobile.md` -- toolchain prerequisites
- `authentication-mobile.md` -- mobile OAuth + Apple Sign-In
